import redis
import memcache
import hashlib
import json
import time
import logging
from typing import Any, Optional, Dict, List, Union
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .models import CacheConfiguration, CacheMetrics, CacheInvalidation
import threading
import gzip
import pickle
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class MultiLevelCacheManager:
    """Advanced multi-level caching system with Redis, Memcached, and database support"""
    
    def __init__(self):
        self.redis_client = None
        self.memcached_client = None
        self.encryption_key = None
        self._initialize_clients()
        self._metrics_lock = threading.Lock()
        
    def _initialize_clients(self):
        """Initialize cache clients"""
        try:
            # Redis client
            if hasattr(settings, 'REDIS_URL'):
                self.redis_client = redis.from_url(settings.REDIS_URL)
            else:
                self.redis_client = redis.Redis(
                    host=getattr(settings, 'REDIS_HOST', 'localhost'),
                    port=getattr(settings, 'REDIS_PORT', 6379),
                    db=getattr(settings, 'REDIS_DB', 0),
                    decode_responses=True
                )
            
            # Memcached client
            memcached_servers = getattr(settings, 'MEMCACHED_SERVERS', ['127.0.0.1:11211'])
            self.memcached_client = memcache.Client(memcached_servers)
            
            # Encryption key for sensitive data
            self.encryption_key = getattr(settings, 'CACHE_ENCRYPTION_KEY', None)
            if self.encryption_key:
                self.encryption_key = Fernet(self.encryption_key.encode())
                
        except Exception as e:
            logger.error(f"Failed to initialize cache clients: {e}")
    
    def get(self, key: str, cache_name: str = 'default', use_compression: bool = True) -> Optional[Any]:
        """Get value from cache with multi-level fallback"""
        start_time = time.time()
        
        try:
            config = self._get_cache_config(cache_name)
            if not config or not config.is_active:
                return None
            
            # Try each cache level in order of priority
            cache_levels = self._get_cache_levels(config)
            
            for level_name, client in cache_levels:
                try:
                    value = self._get_from_cache(client, key, config, use_compression)
                    if value is not None:
                        # Record hit
                        self._record_metrics(cache_name, 'hit', time.time() - start_time)
                        
                        # Populate higher priority caches
                        self._populate_higher_caches(cache_levels, level_name, key, value, config)
                        
                        return value
                        
                except Exception as e:
                    logger.warning(f"Cache level {level_name} failed: {e}")
                    continue
            
            # Record miss
            self._record_metrics(cache_name, 'miss', time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, cache_name: str = 'default', 
            ttl: Optional[int] = None, use_compression: bool = True) -> bool:
        """Set value in cache across all configured levels"""
        start_time = time.time()
        
        try:
            config = self._get_cache_config(cache_name)
            if not config or not config.is_active:
                return False
            
            ttl = ttl or config.ttl_seconds
            cache_levels = self._get_cache_levels(config)
            success = False
            
            for level_name, client in cache_levels:
                try:
                    if self._set_to_cache(client, key, value, ttl, config, use_compression):
                        success = True
                except Exception as e:
                    logger.warning(f"Cache level {level_name} set failed: {e}")
            
            if success:
                self._record_metrics(cache_name, 'set', time.time() - start_time)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def delete(self, key: str, cache_name: str = 'default') -> bool:
        """Delete key from all cache levels"""
        try:
            config = self._get_cache_config(cache_name)
            if not config:
                return False
            
            cache_levels = self._get_cache_levels(config)
            success = False
            
            for level_name, client in cache_levels:
                try:
                    if self._delete_from_cache(client, key):
                        success = True
                except Exception as e:
                    logger.warning(f"Cache level {level_name} delete failed: {e}")
            
            # Record invalidation
            CacheInvalidation.objects.create(
                cache_key=key,
                cache_name=cache_name,
                invalidation_type='manual',
                reason='Manual deletion'
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str, cache_name: str = 'default') -> int:
        """Invalidate all keys matching a pattern"""
        try:
            config = self._get_cache_config(cache_name)
            if not config:
                return 0
            
            deleted_count = 0
            cache_levels = self._get_cache_levels(config)
            
            for level_name, client in cache_levels:
                try:
                    if level_name == 'redis' and self.redis_client:
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            deleted_count += self.redis_client.delete(*keys)
                    elif level_name == 'django':
                        # Django cache doesn't support pattern deletion
                        pass
                except Exception as e:
                    logger.warning(f"Pattern invalidation failed for {level_name}: {e}")
            
            # Record invalidation
            CacheInvalidation.objects.create(
                cache_key=pattern,
                cache_name=cache_name,
                invalidation_type='pattern',
                reason=f'Pattern invalidation: {pattern}'
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Pattern invalidation failed: {e}")
            return 0
    
    def warm_cache(self, cache_name: str, data_loader_func, keys: List[str]) -> Dict[str, bool]:
        """Warm cache with preloaded data"""
        results = {}
        
        try:
            for key in keys:
                try:
                    data = data_loader_func(key)
                    if data is not None:
                        results[key] = self.set(key, data, cache_name)
                    else:
                        results[key] = False
                except Exception as e:
                    logger.error(f"Cache warming failed for key {key}: {e}")
                    results[key] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return {key: False for key in keys}
    
    def get_cache_stats(self, cache_name: str) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            config = self._get_cache_config(cache_name)
            if not config:
                return {}
            
            stats = {
                'cache_name': cache_name,
                'cache_type': config.cache_type,
                'is_active': config.is_active,
                'ttl_seconds': config.ttl_seconds,
                'compression_enabled': config.compression_enabled,
            }
            
            # Get Redis stats
            if self.redis_client and config.cache_type == 'redis':
                redis_info = self.redis_client.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                    'redis_hit_ratio': redis_info.get('keyspace_hit_ratio', 0),
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                })
            
            # Get recent metrics
            recent_metrics = CacheMetrics.objects.filter(
                cache_name=cache_name
            ).order_by('-timestamp')[:10]
            
            if recent_metrics:
                latest = recent_metrics[0]
                stats.update({
                    'hit_ratio': latest.hit_ratio,
                    'avg_response_time_ms': latest.avg_response_time_ms,
                    'memory_usage_percent': latest.memory_usage_percent,
                    'error_count': latest.error_count,
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    def _get_cache_config(self, cache_name: str) -> Optional[CacheConfiguration]:
        """Get cache configuration"""
        try:
            return CacheConfiguration.objects.get(name=cache_name, is_active=True)
        except CacheConfiguration.DoesNotExist:
            return None
    
    def _get_cache_levels(self, config: CacheConfiguration) -> List[tuple]:
        """Get ordered list of cache levels based on configuration"""
        levels = []
        
        if config.cache_type == 'redis' and self.redis_client:
            levels.append(('redis', self.redis_client))
        elif config.cache_type == 'memcached' and self.memcached_client:
            levels.append(('memcached', self.memcached_client))
        
        # Always include Django cache as fallback
        levels.append(('django', cache))
        
        return levels
    
    def _get_from_cache(self, client, key: str, config: CacheConfiguration, 
                       use_compression: bool) -> Optional[Any]:
        """Get value from specific cache client"""
        if hasattr(client, 'get'):
            # Redis or Django cache
            value = client.get(key)
        else:
            # Memcached
            value = client.get(key)
        
        if value is None:
            return None
        
        # Decrypt if needed
        if config.encryption_enabled and self.encryption_key:
            try:
                value = self.encryption_key.decrypt(value.encode()).decode()
            except Exception as e:
                logger.warning(f"Decryption failed: {e}")
                return None
        
        # Decompress if needed
        if use_compression and config.compression_enabled:
            try:
                if isinstance(value, str):
                    value = gzip.decompress(value.encode()).decode()
                else:
                    value = pickle.loads(gzip.decompress(value))
            except Exception as e:
                logger.warning(f"Decompression failed: {e}")
                return None
        
        # Deserialize JSON if it's a string
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return value
    
    def _set_to_cache(self, client, key: str, value: Any, ttl: int, 
                     config: CacheConfiguration, use_compression: bool) -> bool:
        """Set value to specific cache client"""
        try:
            # Serialize value
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            # Compress if needed
            if use_compression and config.compression_enabled:
                value = gzip.compress(value.encode()).decode('latin-1')
            
            # Encrypt if needed
            if config.encryption_enabled and self.encryption_key:
                value = self.encryption_key.encrypt(value.encode()).decode()
            
            # Set in cache
            if hasattr(client, 'setex'):
                # Redis
                return client.setex(key, ttl, value)
            elif hasattr(client, 'set'):
                # Django cache or Memcached
                return client.set(key, value, ttl)
            
            return False
            
        except Exception as e:
            logger.error(f"Cache set operation failed: {e}")
            return False
    
    def _delete_from_cache(self, client, key: str) -> bool:
        """Delete key from specific cache client"""
        try:
            if hasattr(client, 'delete'):
                return bool(client.delete(key))
            return False
        except Exception as e:
            logger.error(f"Cache delete operation failed: {e}")
            return False
    
    def _populate_higher_caches(self, cache_levels: List[tuple], found_level: str, 
                               key: str, value: Any, config: CacheConfiguration):
        """Populate higher priority caches when value is found in lower level"""
        try:
            found_index = next(i for i, (name, _) in enumerate(cache_levels) if name == found_level)
            
            for i in range(found_index):
                level_name, client = cache_levels[i]
                try:
                    self._set_to_cache(client, key, value, config.ttl_seconds, config, True)
                except Exception as e:
                    logger.warning(f"Failed to populate {level_name} cache: {e}")
        except Exception as e:
            logger.warning(f"Cache population failed: {e}")
    
    def _record_metrics(self, cache_name: str, operation: str, response_time: float):
        """Record cache metrics asynchronously"""
        try:
            with self._metrics_lock:
                # This would typically be done asynchronously
                # For now, we'll just log the metrics
                logger.info(f"Cache {operation} for {cache_name}: {response_time:.3f}ms")
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")


# Global cache manager instance
cache_manager = MultiLevelCacheManager()