"""
Advanced Caching Manager for MySQL Integration

This module provides intelligent caching strategies for frequently accessed data:
- Multi-level caching (Redis, Memcached, Database)
- Cache invalidation strategies
- Cache warming and preloading
- Performance monitoring and optimization
"""

import logging
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager

from django.core.cache import cache, caches
from django.core.cache.backends.base import BaseCache
from django.conf import settings
from django.db.models import QuerySet, Model
from django.db.models.signals import post_save, post_delete
from django.utils import timezone
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    cache_key: str
    hit_count: int = 0
    miss_count: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    last_accessed: Optional[datetime] = None
    cache_size: int = 0
    ttl: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.hit_count / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if data['last_accessed']:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data


@dataclass
class CacheStrategy:
    """Cache strategy configuration"""
    name: str
    cache_backend: str = 'default'
    default_timeout: int = 300
    max_entries: int = 10000
    compression_enabled: bool = False
    serialization_format: str = 'json'  # json, pickle
    invalidation_strategy: str = 'ttl'  # ttl, manual, signal
    warming_enabled: bool = False
    warming_schedule: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CacheKeyGenerator:
    """Generate consistent cache keys"""
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and parameters"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            elif isinstance(arg, Model):
                key_parts.append(f"{arg._meta.label}_{arg.pk}")
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (str, int, float, bool)):
                key_parts.append(f"{key}_{value}")
            else:
                key_parts.append(f"{key}_{hash(str(value))}")
        
        # Create final key
        cache_key = ":".join(key_parts)
        
        # Ensure key length doesn't exceed limits
        if len(cache_key) > 200:
            # Hash long keys
            hash_suffix = hashlib.md5(cache_key.encode()).hexdigest()[:8]
            cache_key = f"{prefix}:hashed:{hash_suffix}"
        
        return cache_key
    
    @staticmethod
    def generate_model_key(model_class, pk: Any, field: str = None) -> str:
        """Generate cache key for model instance"""
        key_parts = [model_class._meta.label_lower, str(pk)]
        if field:
            key_parts.append(field)
        return ":".join(key_parts)
    
    @staticmethod
    def generate_queryset_key(queryset: QuerySet, extra_params: Dict = None) -> str:
        """Generate cache key for queryset"""
        model_label = queryset.model._meta.label_lower
        query_hash = hashlib.md5(str(queryset.query).encode()).hexdigest()[:16]
        
        key_parts = [model_label, "queryset", query_hash]
        
        if extra_params:
            params_str = json.dumps(extra_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            key_parts.append(params_hash)
        
        return ":".join(key_parts)


class SmartCacheManager:
    """Intelligent cache manager with multiple strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, CacheStrategy] = {}
        self.metrics: Dict[str, CacheMetrics] = {}
        self.key_generator = CacheKeyGenerator()
        self.invalidation_handlers = {}
        
        # Load default strategies
        self._load_default_strategies()
        
        # Setup signal handlers for cache invalidation
        self._setup_signal_handlers()
    
    def _load_default_strategies(self):
        """Load default caching strategies"""
        # Product caching strategy
        self.register_strategy(CacheStrategy(
            name='products',
            cache_backend='default',
            default_timeout=1800,  # 30 minutes
            max_entries=5000,
            compression_enabled=True,
            invalidation_strategy='signal',
            warming_enabled=True
        ))
        
        # Category caching strategy
        self.register_strategy(CacheStrategy(
            name='categories',
            cache_backend='default',
            default_timeout=3600,  # 1 hour
            max_entries=1000,
            invalidation_strategy='signal',
            warming_enabled=True
        ))
        
        # User session caching
        self.register_strategy(CacheStrategy(
            name='user_sessions',
            cache_backend='default',
            default_timeout=900,  # 15 minutes
            max_entries=10000,
            invalidation_strategy='ttl'
        ))
        
        # Search results caching
        self.register_strategy(CacheStrategy(
            name='search_results',
            cache_backend='default',
            default_timeout=600,  # 10 minutes
            max_entries=2000,
            compression_enabled=True,
            invalidation_strategy='ttl'
        ))
        
        # API response caching
        self.register_strategy(CacheStrategy(
            name='api_responses',
            cache_backend='default',
            default_timeout=300,  # 5 minutes
            max_entries=5000,
            compression_enabled=True,
            invalidation_strategy='ttl'
        ))
    
    def register_strategy(self, strategy: CacheStrategy):
        """Register a caching strategy"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Registered cache strategy: {strategy.name}")
    
    def get_cache_backend(self, strategy_name: str) -> BaseCache:
        """Get cache backend for strategy"""
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return cache
        
        return caches[strategy.cache_backend]
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, 
            strategy_name: str = 'default', compress: bool = None) -> bool:
        """Set cache value with strategy"""
        try:
            strategy = self.strategies.get(strategy_name)
            cache_backend = self.get_cache_backend(strategy_name)
            
            # Use strategy timeout if not specified
            if timeout is None and strategy:
                timeout = strategy.default_timeout
            
            # Serialize value if needed
            if strategy and strategy.serialization_format == 'json':
                if not isinstance(value, (str, int, float, bool, type(None))):
                    value = json.dumps(value, cls=DjangoJSONEncoder)
            
            # Compress if enabled
            if compress or (strategy and strategy.compression_enabled):
                value = self._compress_value(value)
            
            # Set cache value
            success = cache_backend.set(key, value, timeout)
            
            # Update metrics
            self._update_metrics(key, 'set', success)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None, strategy_name: str = 'default') -> Any:
        """Get cache value with strategy"""
        start_time = time.time()
        
        try:
            cache_backend = self.get_cache_backend(strategy_name)
            value = cache_backend.get(key, default)
            
            # Track metrics
            hit = value is not default
            response_time = time.time() - start_time
            self._update_metrics(key, 'get', hit, response_time)
            
            # Decompress if needed
            if value is not default and self._is_compressed(value):
                value = self._decompress_value(value)
            
            # Deserialize if needed
            strategy = self.strategies.get(strategy_name)
            if (value is not default and strategy and 
                strategy.serialization_format == 'json' and 
                isinstance(value, str)):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass  # Return as-is if not JSON
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return default
    
    def delete(self, key: str, strategy_name: str = 'default') -> bool:
        """Delete cache value"""
        try:
            cache_backend = self.get_cache_backend(strategy_name)
            success = cache_backend.delete(key)
            self._update_metrics(key, 'delete', success)
            return success
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def get_many(self, keys: List[str], strategy_name: str = 'default') -> Dict[str, Any]:
        """Get multiple cache values"""
        try:
            cache_backend = self.get_cache_backend(strategy_name)
            return cache_backend.get_many(keys)
        except Exception as e:
            logger.error(f"Cache get_many failed: {e}")
            return {}
    
    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = None, 
                 strategy_name: str = 'default') -> bool:
        """Set multiple cache values"""
        try:
            cache_backend = self.get_cache_backend(strategy_name)
            strategy = self.strategies.get(strategy_name)
            
            if timeout is None and strategy:
                timeout = strategy.default_timeout
            
            cache_backend.set_many(data, timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set_many failed: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str, strategy_name: str = 'default'):
        """Invalidate cache keys matching pattern"""
        try:
            cache_backend = self.get_cache_backend(strategy_name)
            
            # This is a simplified implementation
            # In production, you'd want to use Redis SCAN or similar
            if hasattr(cache_backend, 'delete_pattern'):
                cache_backend.delete_pattern(pattern)
            else:
                logger.warning(f"Pattern invalidation not supported for {strategy_name}")
                
        except Exception as e:
            logger.error(f"Cache pattern invalidation failed: {e}")
    
    @contextmanager
    def cached_result(self, key: str, timeout: Optional[int] = None, 
                     strategy_name: str = 'default'):
        """Context manager for caching function results"""
        # Try to get cached result
        cached_value = self.get(key, strategy_name=strategy_name)
        if cached_value is not None:
            yield cached_value
            return
        
        # Execute function and cache result
        result = yield None
        if result is not None:
            self.set(key, result, timeout, strategy_name)
    
    def cache_model_instance(self, instance: Model, timeout: Optional[int] = None, 
                           strategy_name: str = 'default') -> str:
        """Cache a model instance"""
        cache_key = self.key_generator.generate_model_key(
            instance.__class__, instance.pk
        )
        
        # Serialize model instance
        serialized_data = {
            'model': instance._meta.label,
            'pk': instance.pk,
            'fields': {}
        }
        
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            if hasattr(value, 'isoformat'):  # DateTime fields
                value = value.isoformat()
            serialized_data['fields'][field.name] = value
        
        self.set(cache_key, serialized_data, timeout, strategy_name)
        return cache_key
    
    def get_cached_model_instance(self, model_class, pk: Any, 
                                strategy_name: str = 'default') -> Optional[Model]:
        """Get cached model instance"""
        cache_key = self.key_generator.generate_model_key(model_class, pk)
        cached_data = self.get(cache_key, strategy_name=strategy_name)
        
        if not cached_data:
            return None
        
        try:
            # Reconstruct model instance
            instance = model_class()
            for field_name, value in cached_data['fields'].items():
                setattr(instance, field_name, value)
            return instance
        except Exception as e:
            logger.error(f"Failed to reconstruct cached model instance: {e}")
            return None
    
    def cache_queryset_results(self, queryset: QuerySet, timeout: Optional[int] = None,
                             strategy_name: str = 'default') -> str:
        """Cache queryset results"""
        cache_key = self.key_generator.generate_queryset_key(queryset)
        
        # Execute queryset and serialize results
        results = list(queryset.values())
        
        self.set(cache_key, results, timeout, strategy_name)
        return cache_key
    
    def warm_cache(self, strategy_name: str):
        """Warm cache with frequently accessed data"""
        strategy = self.strategies.get(strategy_name)
        if not strategy or not strategy.warming_enabled:
            return
        
        logger.info(f"Warming cache for strategy: {strategy_name}")
        
        try:
            if strategy_name == 'products':
                self._warm_product_cache()
            elif strategy_name == 'categories':
                self._warm_category_cache()
            # Add more warming strategies as needed
                
        except Exception as e:
            logger.error(f"Cache warming failed for {strategy_name}: {e}")
    
    def _warm_product_cache(self):
        """Warm product cache with popular products"""
        from apps.products.models import Product
        
        # Cache featured products
        featured_products = Product.objects.filter(
            is_featured=True, is_active=True
        ).select_related('category')[:50]
        
        for product in featured_products:
            self.cache_model_instance(product, strategy_name='products')
    
    def _warm_category_cache(self):
        """Warm category cache with all active categories"""
        from apps.products.models import Category
        
        categories = Category.objects.filter(is_active=True)
        for category in categories:
            self.cache_model_instance(category, strategy_name='categories')
    
    def _setup_signal_handlers(self):
        """Setup Django signal handlers for cache invalidation"""
        from apps.products.models import Product, Category
        
        # Product cache invalidation
        post_save.connect(
            self._invalidate_product_cache,
            sender=Product,
            dispatch_uid='invalidate_product_cache'
        )
        post_delete.connect(
            self._invalidate_product_cache,
            sender=Product,
            dispatch_uid='invalidate_product_cache_delete'
        )
        
        # Category cache invalidation
        post_save.connect(
            self._invalidate_category_cache,
            sender=Category,
            dispatch_uid='invalidate_category_cache'
        )
        post_delete.connect(
            self._invalidate_category_cache,
            sender=Category,
            dispatch_uid='invalidate_category_cache_delete'
        )
    
    def _invalidate_product_cache(self, sender, instance, **kwargs):
        """Invalidate product-related cache"""
        # Invalidate specific product cache
        cache_key = self.key_generator.generate_model_key(sender, instance.pk)
        self.delete(cache_key, 'products')
        
        # Invalidate related caches
        self.invalidate_pattern(f"products:*", 'products')
        self.invalidate_pattern(f"search_results:*", 'search_results')
    
    def _invalidate_category_cache(self, sender, instance, **kwargs):
        """Invalidate category-related cache"""
        cache_key = self.key_generator.generate_model_key(sender, instance.pk)
        self.delete(cache_key, 'categories')
        
        # Invalidate related caches
        self.invalidate_pattern(f"categories:*", 'categories')
        self.invalidate_pattern(f"products:*", 'products')
    
    def _compress_value(self, value: Any) -> bytes:
        """Compress cache value"""
        import gzip
        if isinstance(value, str):
            value = value.encode('utf-8')
        elif not isinstance(value, bytes):
            value = str(value).encode('utf-8')
        return gzip.compress(value)
    
    def _decompress_value(self, value: bytes) -> str:
        """Decompress cache value"""
        import gzip
        return gzip.decompress(value).decode('utf-8')
    
    def _is_compressed(self, value: Any) -> bool:
        """Check if value is compressed"""
        return isinstance(value, bytes) and value.startswith(b'\x1f\x8b')
    
    def _update_metrics(self, key: str, operation: str, success: bool, 
                       response_time: float = 0.0):
        """Update cache metrics"""
        if key not in self.metrics:
            self.metrics[key] = CacheMetrics(cache_key=key)
        
        metrics = self.metrics[key]
        metrics.last_accessed = datetime.now()
        
        if operation == 'get':
            metrics.total_requests += 1
            if success:
                metrics.hit_count += 1
            else:
                metrics.miss_count += 1
            
            # Update average response time
            if metrics.total_requests > 1:
                metrics.average_response_time = (
                    (metrics.average_response_time * (metrics.total_requests - 1) + response_time) 
                    / metrics.total_requests
                )
            else:
                metrics.average_response_time = response_time
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'strategies': {name: strategy.to_dict() for name, strategy in self.strategies.items()},
            'metrics': {key: metrics.to_dict() for key, metrics in self.metrics.items()},
            'summary': {
                'total_keys': len(self.metrics),
                'average_hit_rate': 0.0,
                'total_requests': 0,
                'total_hits': 0,
                'total_misses': 0
            }
        }
        
        if self.metrics:
            total_requests = sum(m.total_requests for m in self.metrics.values())
            total_hits = sum(m.hit_count for m in self.metrics.values())
            
            stats['summary']['total_requests'] = total_requests
            stats['summary']['total_hits'] = total_hits
            stats['summary']['total_misses'] = total_requests - total_hits
            
            if total_requests > 0:
                stats['summary']['average_hit_rate'] = (total_hits / total_requests) * 100
        
        return stats
    
    def clear_all_caches(self):
        """Clear all caches (use with caution)"""
        for strategy_name in self.strategies:
            try:
                cache_backend = self.get_cache_backend(strategy_name)
                cache_backend.clear()
                logger.info(f"Cleared cache for strategy: {strategy_name}")
            except Exception as e:
                logger.error(f"Failed to clear cache for {strategy_name}: {e}")


# Global cache manager instance
cache_manager = SmartCacheManager()


# Convenience functions
def cached_result(key: str, timeout: Optional[int] = None, strategy_name: str = 'default'):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with cache_manager.cached_result(key, timeout, strategy_name) as cached_value:
                if cached_value is not None:
                    return cached_value
                return func(*args, **kwargs)
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str, strategy_name: str = 'default'):
    """Invalidate cache keys matching pattern"""
    cache_manager.invalidate_pattern(pattern, strategy_name)


def warm_all_caches():
    """Warm all caches that have warming enabled"""
    for strategy_name, strategy in cache_manager.strategies.items():
        if strategy.warming_enabled:
            cache_manager.warm_cache(strategy_name)