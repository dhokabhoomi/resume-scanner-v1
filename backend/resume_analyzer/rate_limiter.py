"""
Rate limiting and API throttling for Resume Analyzer
"""

import time
import asyncio
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, Request
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    burst: int = 0 # Burst allowance (extra requests)
    
    def __str__(self):
        return f"{self.requests} requests per {self.window}s" + (f" (burst: {self.burst})" if self.burst else "")

@dataclass
class ClientRecord:
    """Track client request history"""
    requests: List[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    violation_count: int = 0
    first_seen: float = field(default_factory=time.time)
    
    def is_blocked(self) -> bool:
        """Check if client is currently blocked"""
        if self.blocked_until is None:
            return False
        return time.time() < self.blocked_until
    
    def add_violation(self, block_duration: int = 300):  # 5 minutes default
        """Record a rate limit violation and apply block"""
        self.violation_count += 1
        # Progressive blocking: 5min, 15min, 60min, 24hr
        durations = [300, 900, 3600, 86400]
        duration = durations[min(self.violation_count - 1, len(durations) - 1)]
        self.blocked_until = time.time() + duration
        logger.warning(f"Client blocked for {duration}s (violation #{self.violation_count})")

class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self):
        self.clients: Dict[str, ClientRecord] = {}
        self.global_stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'unique_clients': 0,
            'start_time': time.time()
        }
        
        # Rate limiting rules for different endpoints
        self.rules = {
            # General API limits
            'default': RateLimitRule(requests=100, window=3600, burst=10),  # 100/hour + 10 burst
            
            # Analysis endpoints (more restrictive)
            'analyze': RateLimitRule(requests=20, window=3600, burst=5),    # 20/hour + 5 burst
            'bulk_analyze': RateLimitRule(requests=5, window=3600, burst=2), # 5/hour + 2 burst
            
            # Export endpoints
            'export': RateLimitRule(requests=10, window=3600, burst=3),     # 10/hour + 3 burst
            
            # Health/info endpoints (lenient)
            'health': RateLimitRule(requests=1000, window=3600, burst=50),  # 1000/hour + 50 burst
            
            # Per-minute limits for rapid requests
            'rapid': RateLimitRule(requests=10, window=60, burst=5),        # 10/minute + 5 burst
        }
        
        # Global system limits
        self.global_limits = {
            'max_concurrent': 50,      # Max concurrent requests
            'max_clients_per_minute': 100,  # Max new clients per minute
        }
        
        self.concurrent_requests = 0
        self.new_clients_window = []
        
    def _get_client_id(self, request: Request) -> str:
        """Generate unique client identifier"""
        # Priority order: authenticated user > forwarded IP > direct IP
        client_ip = None
        
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        # Check for real IP header
        if not client_ip:
            real_ip = request.headers.get('X-Real-IP')
            if real_ip:
                client_ip = real_ip.strip()
        
        # Fall back to direct client IP
        if not client_ip and request.client:
            client_ip = request.client.host
        
        if not client_ip:
            client_ip = "unknown"
        
        # Include User-Agent for more specific identification
        user_agent = request.headers.get('User-Agent', 'unknown')[:100]  # Limit length
        
        # Create hash of IP + partial UA for privacy
        client_data = f"{client_ip}:{user_agent}"
        client_id = hashlib.sha256(client_data.encode()).hexdigest()[:16]
        
        return client_id
    
    def _get_endpoint_category(self, path: str, method: str) -> str:
        """Categorize endpoint for appropriate rate limiting"""
        path_lower = path.lower()
        
        if '/health' in path_lower or '/metrics' in path_lower or path_lower == '/':
            return 'health'
        elif '/analyze_resume' in path_lower:
            return 'analyze'
        elif '/bulk_analyze' in path_lower:
            return 'bulk_analyze' 
        elif '/export' in path_lower:
            return 'export'
        else:
            return 'default'
    
    def _cleanup_old_records(self):
        """Clean up old client records to prevent memory leaks"""
        current_time = time.time()
        cutoff = current_time - 86400  # 24 hours
        
        # Clean up clients not seen for 24 hours
        to_remove = []
        for client_id, record in self.clients.items():
            if record.first_seen < cutoff and (not record.requests or max(record.requests) < cutoff):
                to_remove.append(client_id)
        
        for client_id in to_remove:
            del self.clients[client_id]
        
        # Clean up new clients window
        minute_ago = current_time - 60
        self.new_clients_window = [t for t in self.new_clients_window if t > minute_ago]
    
    def _check_global_limits(self) -> Optional[str]:
        """Check global system limits"""
        # Check concurrent requests
        if self.concurrent_requests >= self.global_limits['max_concurrent']:
            return f"System at capacity ({self.concurrent_requests} concurrent requests)"
        
        # Check new clients per minute
        if len(self.new_clients_window) >= self.global_limits['max_clients_per_minute']:
            return f"Too many new clients ({len(self.new_clients_window)}/minute)"
        
        return None
    
    async def check_rate_limit(self, request: Request) -> Optional[Dict]:
        """
        Check if request should be rate limited
        
        Returns:
            None if allowed, Dict with error info if blocked
        """
        current_time = time.time()
        client_id = self._get_client_id(request)
        endpoint_category = self._get_endpoint_category(request.url.path, request.method)
        
        # Periodic cleanup
        if current_time % 300 < 1:  # Every 5 minutes
            self._cleanup_old_records()
        
        # Check global limits first
        global_error = self._check_global_limits()
        if global_error:
            self.global_stats['blocked_requests'] += 1
            logger.warning(f"Global limit hit: {global_error}")
            return {
                'error': 'rate_limit_exceeded',
                'message': 'System temporarily unavailable due to high load',
                'retry_after': 60
            }
        
        # Get or create client record
        if client_id not in self.clients:
            self.clients[client_id] = ClientRecord()
            self.new_clients_window.append(current_time)
            self.global_stats['unique_clients'] += 1
        
        client = self.clients[client_id]
        
        # Check if client is blocked
        if client.is_blocked():
            self.global_stats['blocked_requests'] += 1
            remaining_block = int(client.blocked_until - current_time)
            logger.debug(f"Blocked client {client_id} attempted request (blocked for {remaining_block}s more)")
            return {
                'error': 'client_blocked',
                'message': f'Client temporarily blocked due to rate limit violations',
                'retry_after': remaining_block
            }
        
        # Get applicable rate limit rules
        rules_to_check = [
            ('rapid', self.rules['rapid']),           # Per-minute limit
            (endpoint_category, self.rules[endpoint_category])  # Endpoint-specific limit
        ]
        
        # If endpoint category is default, also check it
        if endpoint_category != 'default':
            rules_to_check.append(('default', self.rules['default']))
        
        # Check each applicable rule
        for rule_name, rule in rules_to_check:
            # Clean old requests outside the window
            window_start = current_time - rule.window
            client.requests = [req_time for req_time in client.requests if req_time > window_start]
            
            # Count requests in window
            requests_in_window = len(client.requests)
            allowed_requests = rule.requests + rule.burst
            
            if requests_in_window >= allowed_requests:
                # Rate limit exceeded
                client.add_violation()
                self.global_stats['blocked_requests'] += 1
                
                logger.warning(
                    f"Rate limit exceeded for client {client_id}: "
                    f"{requests_in_window}/{allowed_requests} ({rule_name}: {rule})"
                )
                
                return {
                    'error': 'rate_limit_exceeded',
                    'message': f'Rate limit exceeded: {rule}',
                    'retry_after': int(rule.window / 4),  # Suggest retry after 1/4 window
                    'limit': allowed_requests,
                    'window': rule.window,
                    'remaining': max(0, allowed_requests - requests_in_window)
                }
        
        # Request is allowed - record it
        client.requests.append(current_time)
        self.global_stats['total_requests'] += 1
        
        return None  # Allow request
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        current_time = time.time()
        uptime = current_time - self.global_stats['start_time']
        
        # Count active clients (seen in last hour)
        hour_ago = current_time - 3600
        active_clients = sum(
            1 for record in self.clients.values() 
            if record.requests and max(record.requests) > hour_ago
        )
        
        # Count blocked clients
        blocked_clients = sum(
            1 for record in self.clients.values()
            if record.is_blocked()
        )
        
        return {
            'total_requests': self.global_stats['total_requests'],
            'blocked_requests': self.global_stats['blocked_requests'],
            'unique_clients': self.global_stats['unique_clients'],
            'active_clients_1h': active_clients,
            'blocked_clients': blocked_clients,
            'concurrent_requests': self.concurrent_requests,
            'uptime_seconds': uptime,
            'requests_per_minute': self.global_stats['total_requests'] / (uptime / 60) if uptime > 60 else 0,
            'block_rate': (self.global_stats['blocked_requests'] / max(self.global_stats['total_requests'], 1)) * 100,
            'rules': {name: str(rule) for name, rule in self.rules.items()}
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for FastAPI"""
    # Skip rate limiting for health checks in development
    if request.url.path in ['/health', '/'] and request.method == 'GET':
        # Still count for stats but don't block
        pass
    else:
        # Check rate limits
        limit_result = await rate_limiter.check_rate_limit(request)
        if limit_result:
            raise HTTPException(
                status_code=429,
                detail=limit_result['message'],
                headers={'Retry-After': str(limit_result['retry_after'])}
            )
    
    # Track concurrent requests
    rate_limiter.concurrent_requests += 1
    
    try:
        response = await call_next(request)
        return response
    finally:
        rate_limiter.concurrent_requests -= 1

# Rate limiting decorator for individual endpoints
def rate_limit(category: str = 'default', requests: int = None, window: int = None):
    """
    Decorator for endpoint-specific rate limiting
    
    Args:
        category: Rate limit category to use
        requests: Override requests limit
        window: Override time window
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Create custom rule if parameters provided
            if requests is not None and window is not None:
                custom_rule = RateLimitRule(requests=requests, window=window)
                # Temporarily override rule
                original_rule = rate_limiter.rules.get(category)
                rate_limiter.rules[category] = custom_rule
                
                try:
                    limit_result = await rate_limiter.check_rate_limit(request)
                    if limit_result:
                        raise HTTPException(
                            status_code=429,
                            detail=limit_result['message'],
                            headers={'Retry-After': str(limit_result['retry_after'])}
                        )
                finally:
                    # Restore original rule
                    if original_rule:
                        rate_limiter.rules[category] = original_rule
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator