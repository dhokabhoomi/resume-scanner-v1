"""
Enhanced caching system with persistent storage and intelligent prefetching
"""

import os
import json
import pickle
import sqlite3
import threading
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached resume analysis result"""
    key: str
    data: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int
    priority_hash: str
    text_hash: str
    file_size: int
    ttl: float = 7200  # 2 hours default
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl
    
    def should_evict(self, max_idle_time: float = 3600) -> bool:
        """Check if entry should be evicted due to inactivity"""
        return time.time() - self.last_accessed > max_idle_time

class PersistentCache:
    """Persistent cache with SQLite backend for resume analysis"""
    
    def __init__(self, db_path: str = "cache/resume_cache.db", max_memory_entries: int = 1000):
        self.db_path = db_path
        self.max_memory_entries = max_memory_entries
        self.memory_cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Cache")
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'disk_hits': 0,
            'evictions': 0,
            'errors': 0
        }
        
        # Initialize database
        self._init_database()
        
        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _init_database(self):
        """Initialize SQLite database for persistent cache"""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        data BLOB,
                        created_at REAL,
                        last_accessed REAL,
                        access_count INTEGER,
                        priority_hash TEXT,
                        text_hash TEXT,
                        file_size INTEGER,
                        ttl REAL
                    )
                ''')
                
                # Create indexes for better query performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_text_hash ON cache_entries(text_hash)')
                
                conn.commit()
                logger.info(f"Initialized persistent cache database at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
            self.stats['errors'] += 1
    
    def _generate_cache_key(self, text: str, priorities: Optional[List[str]] = None) -> Tuple[str, str, str]:
        """Generate cache key and hashes"""
        # Normalize text
        text_normalized = ' '.join(text.strip().split())
        text_hash = hashlib.sha256(text_normalized.encode()).hexdigest()
        
        # Generate priority hash
        priority_str = ','.join(sorted(priorities)) if priorities else ''
        priority_hash = hashlib.sha256(priority_str.encode()).hexdigest()
        
        # Combine for cache key
        cache_key = f"{text_hash[:16]}_{priority_hash[:8]}"
        
        return cache_key, text_hash, priority_hash
    
    async def get(self, text: str, priorities: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get cached result with async database fallback"""
        cache_key, text_hash, priority_hash = self._generate_cache_key(text, priorities)
        
        # Check memory cache first
        with self._lock:
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if not entry.is_expired():
                    entry.last_accessed = time.time()
                    entry.access_count += 1
                    self.stats['hits'] += 1
                    self.stats['memory_hits'] += 1
                    logger.debug(f"Memory cache hit for {cache_key}")
                    return entry.data
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
        
        # Check persistent cache
        try:
            loop = asyncio.get_event_loop()
            entry = await loop.run_in_executor(
                self._executor, 
                self._get_from_disk, 
                cache_key, text_hash, priority_hash
            )
            
            if entry:
                # Add to memory cache
                with self._lock:
                    if len(self.memory_cache) >= self.max_memory_entries:
                        self._evict_lru_memory()
                    self.memory_cache[cache_key] = entry
                
                self.stats['hits'] += 1
                self.stats['disk_hits'] += 1
                logger.debug(f"Disk cache hit for {cache_key}")
                return entry.data
        except Exception as e:
            logger.error(f"Error reading from disk cache: {e}")
            self.stats['errors'] += 1
        
        self.stats['misses'] += 1
        return None
    
    def _get_from_disk(self, cache_key: str, text_hash: str, priority_hash: str) -> Optional[CacheEntry]:
        """Get entry from disk cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT * FROM cache_entries WHERE key = ? AND text_hash = ? AND priority_hash = ?',
                    (cache_key, text_hash, priority_hash)
                )
                row = cursor.fetchone()
                
                if row:
                    key, data_blob, created_at, last_accessed, access_count, p_hash, t_hash, file_size, ttl = row
                    
                    # Check if expired
                    if time.time() - created_at > ttl:
                        # Remove expired entry
                        conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                        conn.commit()
                        return None
                    
                    # Deserialize data
                    data = pickle.loads(data_blob)
                    
                    # Update access info
                    new_access_time = time.time()
                    conn.execute(
                        'UPDATE cache_entries SET last_accessed = ?, access_count = ? WHERE key = ?',
                        (new_access_time, access_count + 1, key)
                    )
                    conn.commit()
                    
                    return CacheEntry(
                        key=key,
                        data=data,
                        created_at=created_at,
                        last_accessed=new_access_time,
                        access_count=access_count + 1,
                        priority_hash=p_hash,
                        text_hash=t_hash,
                        file_size=file_size,
                        ttl=ttl
                    )
        except Exception as e:
            logger.error(f"Error reading from disk: {e}")
        
        return None
    
    async def set(self, text: str, data: Dict[str, Any], priorities: Optional[List[str]] = None, ttl: float = 7200):
        """Set cached result with async database persistence"""
        cache_key, text_hash, priority_hash = self._generate_cache_key(text, priorities)
        
        current_time = time.time()
        entry = CacheEntry(
            key=cache_key,
            data=data,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            priority_hash=priority_hash,
            text_hash=text_hash,
            file_size=len(text),
            ttl=ttl
        )
        
        # Add to memory cache
        with self._lock:
            if len(self.memory_cache) >= self.max_memory_entries:
                self._evict_lru_memory()
            self.memory_cache[cache_key] = entry
        
        # Persist to disk asynchronously
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self._save_to_disk, entry)
            logger.debug(f"Cached result for {cache_key} (size: {len(self.memory_cache)})")
        except Exception as e:
            logger.error(f"Error saving to disk cache: {e}")
            self.stats['errors'] += 1
    
    def _save_to_disk(self, entry: CacheEntry):
        """Save entry to disk cache"""
        try:
            data_blob = pickle.dumps(entry.data)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (key, data, created_at, last_accessed, access_count, priority_hash, text_hash, file_size, ttl)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.key, data_blob, entry.created_at, entry.last_accessed,
                    entry.access_count, entry.priority_hash, entry.text_hash, entry.file_size, entry.ttl
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving to disk: {e}")
    
    def _evict_lru_memory(self):
        """Evict least recently used entries from memory cache"""
        if not self.memory_cache:
            return
        
        # Remove 20% of least recently used entries
        num_to_remove = max(1, int(self.max_memory_entries * 0.2))
        lru_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )[:num_to_remove]
        
        for key, _ in lru_entries:
            del self.memory_cache[key]
            self.stats['evictions'] += 1
        
        logger.debug(f"Evicted {num_to_remove} entries from memory cache")
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._cleanup_expired()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running, cleanup will be manual
            pass
    
    async def _cleanup_expired(self):
        """Clean up expired entries from both memory and disk"""
        current_time = time.time()
        
        # Clean memory cache
        with self._lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired() or entry.should_evict()
            ]
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats['evictions'] += 1
        
        # Clean disk cache
        try:
            loop = asyncio.get_event_loop()
            removed_count = await loop.run_in_executor(
                self._executor, 
                self._cleanup_disk_expired, 
                current_time
            )
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired disk cache entries")
        except Exception as e:
            logger.error(f"Error cleaning disk cache: {e}")
    
    def _cleanup_disk_expired(self, current_time: float) -> int:
        """Clean up expired entries from disk"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove entries older than their TTL
                cursor = conn.execute(
                    'DELETE FROM cache_entries WHERE ? - created_at > ttl',
                    (current_time,)
                )
                removed_count = cursor.rowcount
                
                # Also remove entries not accessed for a long time (7 days)
                cursor = conn.execute(
                    'DELETE FROM cache_entries WHERE ? - last_accessed > 604800',
                    (current_time,)
                )
                removed_count += cursor.rowcount
                
                conn.commit()
                return removed_count
        except Exception as e:
            logger.error(f"Error cleaning disk cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Get disk cache info
        disk_stats = self._get_disk_stats()
        
        return {
            'memory_cache': {
                'size': len(self.memory_cache),
                'max_size': self.max_memory_entries,
                'hit_rate_percent': round(hit_rate, 2),
                'memory_hits': self.stats['memory_hits'],
                'disk_hits': self.stats['disk_hits']
            },
            'disk_cache': disk_stats,
            'performance': {
                'total_hits': self.stats['hits'],
                'total_misses': self.stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self.stats['evictions'],
                'errors': self.stats['errors']
            }
        }
    
    def _get_disk_stats(self) -> Dict[str, Any]:
        """Get disk cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total entries
                cursor = conn.execute('SELECT COUNT(*) FROM cache_entries')
                total_entries = cursor.fetchone()[0]
                
                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # Count expired entries
                cursor = conn.execute(
                    'SELECT COUNT(*) FROM cache_entries WHERE ? - created_at > ttl',
                    (time.time(),)
                )
                expired_entries = cursor.fetchone()[0]
                
                return {
                    'total_entries': total_entries,
                    'expired_entries': expired_entries,
                    'db_size_mb': round(db_size / (1024 * 1024), 2),
                    'db_path': self.db_path
                }
        except Exception as e:
            logger.error(f"Error getting disk stats: {e}")
            return {'error': str(e)}
    
    async def clear(self, keep_recent: bool = False):
        """Clear cache data"""
        with self._lock:
            if keep_recent:
                # Keep entries accessed in last hour
                recent_time = time.time() - 3600
                recent_entries = {
                    key: entry for key, entry in self.memory_cache.items()
                    if entry.last_accessed > recent_time
                }
                self.memory_cache = recent_entries
            else:
                self.memory_cache.clear()
        
        # Clear disk cache
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self._clear_disk, keep_recent)
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")
    
    def _clear_disk(self, keep_recent: bool = False):
        """Clear disk cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if keep_recent:
                    recent_time = time.time() - 3600
                    conn.execute(
                        'DELETE FROM cache_entries WHERE last_accessed <= ?',
                        (recent_time,)
                    )
                else:
                    conn.execute('DELETE FROM cache_entries')
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        self._executor.shutdown(wait=True)

# Global enhanced cache instance
enhanced_cache = PersistentCache(
    db_path="cache/resume_analysis.db",
    max_memory_entries=1500
)