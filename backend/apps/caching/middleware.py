import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from .models import CacheMetrics
from .cache_manager import cache_manager
import threading
import json

logger = logging.getLogger(__name__)


class CacheMetricsMiddleware(MiddlewareMixin):
    """Middleware to collect cache performance metrics"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.metrics_lock = threading.Lock()
        self.metrics_buffer = []
        self.buffer_size = 100
        
    def process_request(self, request):
        """Start timing the request"""
        request._cache_start_time = time.time()
        request._cache_operations = {
            'get': 0,
            'set': 0,
            'delete': 0,
            'hit': 0,
            'miss': 0
        }
        return None
    
    def process_response(self, request, response):
        """Record cache metrics after response"""
        try:
            if hasattr(request, '_cache_start_time'):
                response_time = (time.time() - request._cache_start_time) * 1000
                
                # Collect metrics asynchronously
                threading.Thread(
                    target=self._collect_metrics,
                    args=(request, response, response_time),
                    daemon=True
                ).start()
                
        except Exception as e:
            logger.error(f"Cache metrics collection failed: {e}")
        
        return response
    
    def _collect_metrics(self, request, response, response_time):
        """Collect and buffer cache metrics"""
        try:
            # Get cache operations from request
            operations = getattr(request, '_cache_operations', {})
            
            # Create metrics entry
            metrics_data = {
                'timestamp': timezone.now(),
                'response_time_ms': response_time,
                'operations': operations,
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request)
            }
            
            # Buffer metrics
            with self.metrics_lock:
                self.metrics_buffer.append(metrics_data)
                
                # Flush buffer if it's full
                if len(self.metrics_buffer) >= self.buffer_size:
                    self._flush_metrics_buffer()
                    
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
    
    def _flush_metrics_buffer(self):
        """Flush metrics buffer to database"""
        try:
            if not self.metrics_buffer:
                return
            
            # Process buffered metrics
            buffer_copy = self.metrics_buffer.copy()
            self.metrics_buffer.clear()
            
            # Aggregate metrics by cache name
            cache_metrics = {}
            
            for metrics_data in buffer_copy:
                # This would typically involve more sophisticated cache name detection
                cache_name = 'default'  # Simplified for now
                
                if cache_name not in cache_metrics:
                    cache_metrics[cache_name] = {
                        'cache_name': cache_name,
                        'cache_type': 'redis',  # Would be detected dynamically
                        'timestamp': metrics_data['timestamp'],
                        'hit_count': 0,
                        'miss_count': 0,
                        'get_operations': 0,
                        'set_operations': 0,
                        'delete_operations': 0,
                        'response_times': [],
                        'error_count': 0
                    }
                
                # Aggregate operations
                ops = metrics_data['operations']
                cache_metrics[cache_name]['hit_count'] += ops.get('hit', 0)
                cache_metrics[cache_name]['miss_count'] += ops.get('miss', 0)
                cache_metrics[cache_name]['get_operations'] += ops.get('get', 0)
                cache_metrics[cache_name]['set_operations'] += ops.get('set', 0)
                cache_metrics[cache_name]['delete_operations'] += ops.get('delete', 0)
                cache_metrics[cache_name]['response_times'].append(metrics_data['response_time_ms'])
                
                if metrics_data['status_code'] >= 400:
                    cache_metrics[cache_name]['error_count'] += 1
            
            # Save aggregated metrics
            for cache_name, metrics in cache_metrics.items():
                try:
                    response_times = metrics['response_times']
                    total_operations = (
                        metrics['hit_count'] + metrics['miss_count']
                    )
                    
                    CacheMetrics.objects.create(
                        cache_name=cache_name,
                        cache_type=metrics['cache_type'],
                        timestamp=metrics['timestamp'],
                        hit_count=metrics['hit_count'],
                        miss_count=metrics['miss_count'],
                        hit_ratio=metrics['hit_count'] / max(total_operations, 1),
                        avg_response_time_ms=sum(response_times) / max(len(response_times), 1),
                        max_response_time_ms=max(response_times) if response_times else 0,
                        min_response_time_ms=min(response_times) if response_times else 0,
                        get_operations=metrics['get_operations'],
                        set_operations=metrics['set_operations'],
                        delete_operations=metrics['delete_operations'],
                        error_count=metrics['error_count']
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to save metrics for {cache_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Metrics buffer flush failed: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CacheHeadersMiddleware(MiddlewareMixin):
    """Middleware to add cache headers to responses"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache_rules = self._load_cache_rules()
    
    def process_response(self, request, response):
        """Add cache headers to response"""
        try:
            # Skip for admin and API endpoints
            if request.path.startswith('/admin/') or request.path.startswith('/api/'):
                return response
            
            # Get cache rule for this path
            cache_rule = self._get_cache_rule(request.path, response.get('Content-Type', ''))
            
            if cache_rule:
                # Add cache headers
                response['Cache-Control'] = cache_rule['cache_control']
                response['Expires'] = cache_rule.get('expires', '')
                
                if cache_rule.get('etag_enabled', False):
                    # Generate ETag based on content
                    import hashlib
                    content_hash = hashlib.md5(response.content).hexdigest()
                    response['ETag'] = f'"{content_hash}"'
                
                if cache_rule.get('vary_headers'):
                    response['Vary'] = ', '.join(cache_rule['vary_headers'])
                
                # Add security headers
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                response['X-XSS-Protection'] = '1; mode=block'
                
        except Exception as e:
            logger.error(f"Cache headers middleware failed: {e}")
        
        return response
    
    def _load_cache_rules(self):
        """Load cache rules configuration"""
        return {
            'static': {
                'extensions': ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'],
                'cache_control': 'public, max-age=31536000, immutable',
                'etag_enabled': True
            },
            'images': {
                'extensions': ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif'],
                'cache_control': 'public, max-age=2592000',
                'etag_enabled': True
            },
            'html': {
                'content_types': ['text/html'],
                'cache_control': 'public, max-age=3600',
                'etag_enabled': True,
                'vary_headers': ['Accept-Encoding', 'Cookie']
            },
            'api': {
                'paths': ['/api/'],
                'cache_control': 'no-cache, no-store, must-revalidate',
                'etag_enabled': False
            }
        }
    
    def _get_cache_rule(self, path, content_type):
        """Get cache rule for path and content type"""
        try:
            # Check for API paths
            for rule_name, rule in self.cache_rules.items():
                if 'paths' in rule:
                    for rule_path in rule['paths']:
                        if path.startswith(rule_path):
                            return rule
            
            # Check by file extension
            for rule_name, rule in self.cache_rules.items():
                if 'extensions' in rule:
                    for ext in rule['extensions']:
                        if path.endswith(ext):
                            return rule
            
            # Check by content type
            for rule_name, rule in self.cache_rules.items():
                if 'content_types' in rule:
                    for ct in rule['content_types']:
                        if content_type.startswith(ct):
                            return rule
            
            return None
            
        except Exception as e:
            logger.error(f"Cache rule lookup failed: {e}")
            return None


class CompressionMiddleware(MiddlewareMixin):
    """Middleware to handle response compression"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.compressible_types = [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
            'text/xml',
            'image/svg+xml'
        ]
        self.min_size = 1024  # Minimum size to compress (1KB)
    
    def process_response(self, request, response):
        """Compress response if applicable"""
        try:
            # Check if compression is supported
            accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
            
            if 'gzip' not in accept_encoding:
                return response
            
            # Check content type
            content_type = response.get('Content-Type', '').split(';')[0]
            if content_type not in self.compressible_types:
                return response
            
            # Check content size
            if len(response.content) < self.min_size:
                return response
            
            # Check if already compressed
            if response.get('Content-Encoding'):
                return response
            
            # Compress content
            import gzip
            compressed_content = gzip.compress(response.content)
            
            # Only use compressed version if it's actually smaller
            if len(compressed_content) < len(response.content):
                response.content = compressed_content
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = str(len(compressed_content))
                response['Vary'] = response.get('Vary', '') + ', Accept-Encoding'
                
        except Exception as e:
            logger.error(f"Compression middleware failed: {e}")
        
        return response


class CachingMiddleware(MiddlewareMixin):
    """Advanced caching middleware with intelligent cache management"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache_timeout = 300  # 5 minutes default
        self.cache_key_prefix = 'page_cache'
        
    def process_request(self, request):
        """Check if cached response exists"""
        try:
            # Skip caching for certain conditions
            if self._should_skip_cache(request):
                return None
            
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Try to get cached response
            cached_response = cache_manager.get(cache_key, 'page_cache')
            
            if cached_response:
                # Reconstruct HttpResponse from cached data
                response = HttpResponse(
                    content=cached_response['content'],
                    content_type=cached_response['content_type'],
                    status=cached_response['status_code']
                )
                
                # Add cache headers
                for header, value in cached_response.get('headers', {}).items():
                    response[header] = value
                
                response['X-Cache'] = 'HIT'
                return response
                
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        
        return None
    
    def process_response(self, request, response):
        """Cache response if applicable"""
        try:
            # Skip caching for certain conditions
            if self._should_skip_cache(request, response):
                return response
            
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Prepare response data for caching
            cached_data = {
                'content': response.content.decode('utf-8') if response.content else '',
                'content_type': response.get('Content-Type', ''),
                'status_code': response.status_code,
                'headers': dict(response.items())
            }
            
            # Cache the response
            cache_timeout = self._get_cache_timeout(request, response)
            cache_manager.set(cache_key, cached_data, 'page_cache', cache_timeout)
            
            response['X-Cache'] = 'MISS'
            
        except Exception as e:
            logger.error(f"Response caching failed: {e}")
        
        return response
    
    def _should_skip_cache(self, request, response=None):
        """Determine if caching should be skipped"""
        # Skip for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            return True
        
        # Skip for non-GET requests
        if request.method != 'GET':
            return True
        
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return True
        
        # Skip if response has errors (when processing response)
        if response and response.status_code >= 400:
            return True
        
        # Skip if response has cache-control no-cache
        if response and 'no-cache' in response.get('Cache-Control', ''):
            return True
        
        return False
    
    def _generate_cache_key(self, request):
        """Generate cache key for request"""
        import hashlib
        
        key_parts = [
            self.cache_key_prefix,
            request.path,
            request.GET.urlencode(),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', '')
        ]
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_timeout(self, request, response):
        """Get cache timeout for request/response"""
        # Check for cache-control header
        cache_control = response.get('Cache-Control', '')
        
        if 'max-age=' in cache_control:
            try:
                max_age = int(cache_control.split('max-age=')[1].split(',')[0])
                return max_age
            except (ValueError, IndexError):
                pass
        
        # Default timeout based on content type
        content_type = response.get('Content-Type', '').split(';')[0]
        
        timeouts = {
            'text/html': 300,           # 5 minutes
            'application/json': 60,     # 1 minute
            'text/css': 86400,          # 1 day
            'application/javascript': 86400,  # 1 day
            'image/': 3600,             # 1 hour for images
        }
        
        for ct, timeout in timeouts.items():
            if content_type.startswith(ct):
                return timeout
        
        return self.cache_timeout