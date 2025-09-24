"""
Performance optimization utilities for Resume Analyzer
"""

import asyncio
import time
import weakref
from typing import Dict, Any, Optional, List, Tuple, Callable, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import queue
import logging
from functools import wraps, lru_cache
import json
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization"""
    total_requests: int = 0
    avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    concurrent_requests: int = 0
    peak_concurrent: int = 0
    cpu_intensive_tasks: int = 0
    io_intensive_tasks: int = 0
    failed_tasks: int = 0
    start_time: float = field(default_factory=time.time)
    
    def update_response_time(self, new_time: float):
        """Update average response time with new measurement"""
        self.total_requests += 1
        self.avg_response_time = (
            (self.avg_response_time * (self.total_requests - 1) + new_time) 
            / self.total_requests
        )

class OptimizedCache:
    """High-performance cache with intelligent eviction"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
    
    def _generate_key(self, text: str, priorities: Optional[List[str]] = None) -> str:
        """Generate cache key from resume text and priorities"""
        # Use hash of text + priorities for consistent keys
        content = text.strip()
        priority_str = ",".join(sorted(priorities)) if priorities else ""
        key_content = f"{content}:{priority_str}"
        return hashlib.sha256(key_content.encode()).hexdigest()[:32]
    
    def _evict_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time - data.get('cached_at', 0) > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Remove least recently used entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove 20% of least recently used items
            num_to_remove = max(1, int(self.max_size * 0.2))
            lru_keys = sorted(
                self.access_times.items(), 
                key=lambda x: x[1]
            )[:num_to_remove]
            
            for key, _ in lru_keys:
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
    
    def get(self, text: str, priorities: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        key = self._generate_key(text, priorities)
        
        with self._lock:
            self._evict_expired()
            
            if key in self.cache:
                self.access_times[key] = time.time()
                self.hit_count += 1
                logger.debug(f"Cache hit for key {key[:8]}...")
                return self.cache[key]['data']
            else:
                self.miss_count += 1
                logger.debug(f"Cache miss for key {key[:8]}...")
                return None
    
    def set(self, text: str, data: Dict[str, Any], priorities: Optional[List[str]] = None):
        """Cache result"""
        key = self._generate_key(text, priorities)
        
        with self._lock:
            self._evict_lru()
            
            self.cache[key] = {
                'data': data,
                'cached_at': time.time()
            }
            self.access_times[key] = time.time()
            
            logger.debug(f"Cached result for key {key[:8]}... (cache size: {len(self.cache)})")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': round(hit_rate, 2),
            'ttl_seconds': self.ttl_seconds
        }
    
    def clear(self):
        """Clear all cached data"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Cache cleared")

class TaskBatcher:
    """Batch similar tasks for more efficient processing"""
    
    def __init__(self, batch_size: int = 5, max_wait_time: float = 2.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_tasks: Dict[str, List] = {}
        self._locks: Dict[str, threading.Lock] = {}
    
    async def add_task(self, task_type: str, task_data: Dict[str, Any], processor: Callable) -> Any:
        """Add task to batch processing queue"""
        if task_type not in self._locks:
            self._locks[task_type] = threading.Lock()
            self.pending_tasks[task_type] = []
        
        # Add task to pending queue
        task_item = {
            'data': task_data,
            'timestamp': time.time(),
            'future': asyncio.Future()
        }
        
        with self._locks[task_type]:
            self.pending_tasks[task_type].append(task_item)
        
        # Check if we should process batch
        should_process = (
            len(self.pending_tasks[task_type]) >= self.batch_size or
            (self.pending_tasks[task_type] and 
             time.time() - self.pending_tasks[task_type][0]['timestamp'] > self.max_wait_time)
        )
        
        if should_process:
            asyncio.create_task(self._process_batch(task_type, processor))
        
        return await task_item['future']
    
    async def _process_batch(self, task_type: str, processor: Callable):
        """Process a batch of similar tasks"""
        with self._locks[task_type]:
            batch = self.pending_tasks[task_type][:self.batch_size]
            self.pending_tasks[task_type] = self.pending_tasks[task_type][self.batch_size:]
        
        if not batch:
            return
        
        logger.info(f"Processing batch of {len(batch)} {task_type} tasks")
        
        try:
            # Extract task data
            batch_data = [item['data'] for item in batch]
            
            # Process batch
            results = await processor(batch_data)
            
            # Set results for individual futures
            for item, result in zip(batch, results):
                if not item['future'].done():
                    item['future'].set_result(result)
        
        except Exception as e:
            logger.error(f"Batch processing failed for {task_type}: {e}")
            for item in batch:
                if not item['future'].done():
                    item['future'].set_exception(e)

class OptimizedAsyncProcessor:
    """Enhanced async processor with advanced optimizations"""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=max_workers, 
            thread_name_prefix="CPU"
        )
        self.io_executor = ThreadPoolExecutor(
            max_workers=max_workers * 2,  # More threads for I/O
            thread_name_prefix="IO"
        )
        
        self.cache = OptimizedCache(max_size=2000, ttl_seconds=7200)  # 2 hour TTL
        self.metrics = PerformanceMetrics()
        self.task_batcher = TaskBatcher(batch_size=3, max_wait_time=1.5)
        
        # Connection pooling for external services
        self._connection_pools = {}
        
        # Task prioritization queue
        self.high_priority_queue = asyncio.PriorityQueue()
        self.normal_priority_queue = asyncio.PriorityQueue()
        
    async def process_resume_optimized(
        self,
        resume_text: str,
        pdf_processor,
        rule_validator, 
        ai_analyzer,
        score_enforcer,
        priorities: Optional[List[str]] = None,
        priority_level: int = 1  # 0=high, 1=normal
    ) -> Dict[str, Any]:
        """
        Optimized parallel processing with caching and batching
        """
        start_time = time.time()
        self.metrics.concurrent_requests += 1
        self.metrics.peak_concurrent = max(
            self.metrics.peak_concurrent, 
            self.metrics.concurrent_requests
        )
        
        try:
            # Check cache first
            cached_result = self.cache.get(resume_text, priorities)
            if cached_result:
                self.metrics.cache_hit_rate = (
                    self.cache.hit_count / 
                    (self.cache.hit_count + self.cache.miss_count)
                )
                logger.info("Returning cached analysis result")
                return cached_result
            
            # Create optimized task pipeline
            pipeline_tasks = []
            
            # Stage 1: Fast preprocessing (parallel)
            preprocessing_tasks = [
                self._run_cpu_task(
                    self._preprocess_text_sections,
                    resume_text
                ),
                self._run_cpu_task(
                    self._extract_metadata_fast,
                    resume_text
                )
            ]
            
            preprocess_results = await asyncio.gather(*preprocessing_tasks)
            processed_sections = preprocess_results[0]
            metadata = preprocess_results[1]
            
            # Stage 2: Main analysis (parallel with priorities)
            analysis_tasks = []
            
            # High-priority: Critical validations
            if priority_level == 0:  # High priority
                analysis_tasks.extend([
                    self._run_cpu_task_prioritized(
                        rule_validator.run_all_checks,
                        resume_text,
                        priority=0
                    ),
                    self._run_io_task_prioritized(
                        ai_analyzer.analyze_resume,
                        resume_text, priorities, None, True,
                        priority=0
                    )
                ])
            else:  # Normal priority  
                analysis_tasks.extend([
                    self._run_cpu_task(
                        rule_validator.run_all_checks,
                        resume_text
                    ),
                    self._run_io_task(
                        ai_analyzer.analyze_resume,
                        resume_text, priorities, None, True
                    )
                ])
            
            # Wait for main analysis
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Handle results and exceptions
            rule_result = analysis_results[0] if not isinstance(analysis_results[0], Exception) else {"error": str(analysis_results[0])}
            ai_result = analysis_results[1] if not isinstance(analysis_results[1], Exception) else {"error": str(analysis_results[1])}
            
            # Stage 3: Post-processing (optimized)
            if "error" not in rule_result and "error" not in ai_result:
                enforced_analysis = await self._run_cpu_task(
                    score_enforcer.enforce_scores_with_facts,
                    ai_result, rule_result, priorities
                )
                
                enforced_analysis = await self._run_cpu_task(
                    score_enforcer.enforce_headshot_rule,
                    enforced_analysis
                )
                
                # Construct complete response with all required fields
                final_result = {
                    **enforced_analysis,  # Contains the main analysis
                    "rule_based_findings": rule_result.get("rule_based_findings", rule_result),
                    "fact_sheet": enforced_analysis.get("fact_sheet", {}),
                    "priority_analysis": None  # Will be handled by main endpoint if needed
                }
            else:
                # Fallback result
                final_result = {
                    "error": "Analysis failed",
                    "rule_result": rule_result,
                    "ai_result": ai_result
                }
            
            # Add metadata
            final_result["processing_metadata"] = {
                **metadata,
                "processing_time": time.time() - start_time,
                "cache_used": False,
                "priority_level": priority_level
            }
            
            # Cache successful results
            if "error" not in final_result:
                self.cache.set(resume_text, final_result, priorities)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Optimized processing failed: {e}")
            self.metrics.failed_tasks += 1
            return {
                "error": f"Processing failed: {str(e)}",
                "processing_metadata": {
                    "processing_time": time.time() - start_time,
                    "cache_used": False,
                    "priority_level": priority_level
                }
            }
        finally:
            self.metrics.concurrent_requests -= 1
            duration = time.time() - start_time
            self.metrics.update_response_time(duration)
    
    async def _run_cpu_task(self, func: Callable, *args, **kwargs):
        """Run CPU-intensive task in optimized thread pool"""
        self.metrics.cpu_intensive_tasks += 1
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.cpu_executor, func, *args, **kwargs)
    
    async def _run_io_task(self, func: Callable, *args, **kwargs):
        """Run I/O-intensive task in optimized thread pool"""
        self.metrics.io_intensive_tasks += 1
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.io_executor, func, *args, **kwargs)
    
    async def _run_cpu_task_prioritized(self, func: Callable, *args, priority: int = 1, **kwargs):
        """Run CPU task with priority"""
        task_item = (priority, time.time(), func, args, kwargs)
        if priority == 0:
            await self.high_priority_queue.put(task_item)
        else:
            await self.normal_priority_queue.put(task_item)
        return await self._run_cpu_task(func, *args, **kwargs)
    
    async def _run_io_task_prioritized(self, func: Callable, *args, priority: int = 1, **kwargs):
        """Run I/O task with priority"""
        return await self._run_io_task(func, *args, **kwargs)
    
    @lru_cache(maxsize=500)
    def _preprocess_text_sections(self, text: str) -> Dict[str, str]:
        """Fast preprocessing with caching for repeated patterns"""
        sections = {
            'education': '',
            'experience': '',
            'skills': '',
            'projects': '',
            'personal': ''
        }
        
        # Fast regex-based section extraction
        import re
        
        # Common section patterns
        patterns = {
            'education': r'(education|academic|qualification|degree|university|college).*?(?=experience|skills|projects|$)',
            'experience': r'(experience|work|employment|career|job).*?(?=education|skills|projects|$)',
            'skills': r'(skills|technical|technologies|programming|tools).*?(?=education|experience|projects|$)',
            'projects': r'(projects|portfolio|work).*?(?=education|experience|skills|$)',
        }
        
        text_lower = text.lower()
        for section, pattern in patterns.items():
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(0)
        
        return sections
    
    def _extract_metadata_fast(self, text: str) -> Dict[str, Any]:
        """Fast metadata extraction"""
        return {
            'text_length': len(text),
            'word_count': len(text.split()),
            'estimated_sections': len([s for s in ['education', 'experience', 'skills', 'projects'] if s.lower() in text.lower()]),
            'has_contact_info': any(pattern in text.lower() for pattern in ['@', 'phone', 'email', 'linkedin'])
        }
    
    async def bulk_process_optimized(
        self, 
        resume_data_list: List[Tuple[str, str]], # (text, filename)
        processors: Dict[str, Any],
        priorities: Optional[List[str]] = None,
        max_concurrent: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Optimized bulk processing with streaming results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(text: str, filename: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.process_resume_optimized(
                        text,
                        processors['pdf_processor'],
                        processors['rule_validator'],
                        processors['ai_analyzer'], 
                        processors['score_enforcer'],
                        priorities=priorities
                    )
                    result['filename'] = filename
                    return result
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {e}")
                    return {
                        'filename': filename,
                        'error': str(e),
                        'processing_metadata': {
                            'processing_time': 0,
                            'cache_used': False
                        }
                    }
        
        # Process in controlled batches
        for i in range(0, len(resume_data_list), max_concurrent):
            batch = resume_data_list[i:i + max_concurrent]
            
            # Create tasks for this batch
            tasks = [
                process_single(text, filename) 
                for text, filename in batch
            ]
            
            # Yield results as they complete
            for future in asyncio.as_completed(tasks):
                result = await future
                yield result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.cache.get_stats()
        
        return {
            "processing": {
                "total_requests": self.metrics.total_requests,
                "avg_response_time_ms": round(self.metrics.avg_response_time * 1000, 2),
                "current_concurrent": self.metrics.concurrent_requests,
                "peak_concurrent": self.metrics.peak_concurrent,
                "cpu_tasks": self.metrics.cpu_intensive_tasks,
                "io_tasks": self.metrics.io_intensive_tasks,
                "failed_tasks": self.metrics.failed_tasks,
                "uptime_hours": round((time.time() - self.metrics.start_time) / 3600, 2)
            },
            "cache": cache_stats,
            "thread_pools": {
                "cpu_pool_size": self.cpu_executor._max_workers,
                "io_pool_size": self.io_executor._max_workers,
                "cpu_active_threads": len(self.cpu_executor._threads),
                "io_active_threads": len(self.io_executor._threads)
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.cpu_executor.shutdown(wait=True)
        self.io_executor.shutdown(wait=True)
        self.cache.clear()

# Global optimized processor instance
optimized_processor = OptimizedAsyncProcessor(max_workers=6)