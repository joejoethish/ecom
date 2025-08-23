import uuid
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .utils import get_correlation_id_from_request, add_correlation_id_to_response, PerformanceMonitor


class CorrelationIdMiddleware(MiddlewareMixin):
    """Middleware to handle correlation IDs for request tracing"""
    
    def process_request(self, request):
        """Add correlation ID to request"""
        correlation_id = get_correlation_id_from_request(request)
        request.correlation_id = correlation_id
        
        # Store start time for performance monitoring
        request._debug_start_time = time.time()
        
        return None
    
    def process_response(self, request, response):
        """Add correlation ID to response and record performance metrics"""
        correlation_id = getattr(request, 'correlation_id', None)
        
        if correlation_id:
            add_correlation_id_to_response(response, correlation_id)
        
        # Record API response time
        if hasattr(request, '_debug_start_time'):
            duration_ms = (time.time() - request._debug_start_time) * 1000
            
            PerformanceMonitor.record_metric(
                layer='api',
                component=request.resolver_match.view_name if hasattr(request, 'resolver_match') and request.resolver_match else 'unknown',
                metric_name='response_time',
                metric_value=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code
                }
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with correlation ID"""
        from .utils import ErrorLogger
        
        correlation_id = getattr(request, 'correlation_id', None)
        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        
        ErrorLogger.log_exception(
            exception=exception,
            layer='api',
            component=request.resolver_match.view_name if hasattr(request, 'resolver_match') and request.resolver_match else 'unknown',
            correlation_id=correlation_id,
            user=user,
            request=request,
            metadata={
                'path': request.path,
                'method': request.method
            }
        )
        
        return None


class DebuggingMiddleware(MiddlewareMixin):
    """Middleware for comprehensive debugging and monitoring"""
    
    def process_request(self, request):
        """Initialize debugging context for request"""
        # Store request start time
        request._debug_start_time = time.time()
        request._debug_timestamp = timezone.now()
        
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Log view processing start"""
        if hasattr(request, 'correlation_id'):
            from .utils import WorkflowTracer
            
            # You could start a workflow trace here if needed
            # This is optional and can be enabled based on configuration
            pass
        
        return None
    
    def process_response(self, request, response):
        """Process response and log metrics"""
        if hasattr(request, '_debug_start_time'):
            duration_ms = (time.time() - request._debug_start_time) * 1000
            
            # Log slow requests
            if duration_ms > 1000:  # Requests slower than 1 second
                from .utils import ErrorLogger
                
                ErrorLogger.log_error(
                    layer='api',
                    component='middleware',
                    error_type='SlowRequest',
                    error_message=f'Request took {duration_ms:.2f}ms',
                    correlation_id=getattr(request, 'correlation_id', None),
                    severity='warning',
                    metadata={
                        'path': request.path,
                        'method': request.method,
                        'duration_ms': duration_ms,
                        'status_code': response.status_code
                    }
                )
        
        return response