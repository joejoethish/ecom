import time
import threading
import psutil
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings
from .models import PerformanceMetric, ApplicationPerformanceMonitor, DatabasePerformanceLog
from .utils import get_client_ip, generate_transaction_id
import uuid

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor application performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Start performance monitoring for request"""
        request.start_time = time.time()
        request.transaction_id = generate_transaction_id()
        request.initial_queries = len(connection.queries)
        
        # Store request context for monitoring
        request.performance_context = {
            'endpoint': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
            'session_id': request.session.session_key if hasattr(request, 'session') else None,
        }
        
        return None
    
    def process_response(self, request, response):
        """End performance monitoring and log metrics"""
        if not hasattr(request, 'start_time'):
            return response
        
        end_time = time.time()
        duration = (end_time - request.start_time) * 1000  # Convert to milliseconds
        
        # Log response time metric
        try:
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name=f"{request.method} {request.path}",
                value=duration,
                unit='ms',
                source='application',
                endpoint=request.path,
                user_agent=request.performance_context.get('user_agent'),
                ip_address=request.performance_context.get('ip_address'),
                session_id=request.performance_context.get('session_id'),
                metadata={
                    'method': request.method,
                    'status_code': response.status_code,
                    'content_length': len(response.content) if hasattr(response, 'content') else 0,
                },
                severity='high' if duration > 5000 else 'medium' if duration > 2000 else 'low'
            )
            
            # Log APM transaction
            ApplicationPerformanceMonitor.objects.create(
                transaction_id=request.transaction_id,
                transaction_type='web_request',
                name=f"{request.method} {request.path}",
                duration=duration,
                start_time=request.start_time,
                end_time=end_time,
                status_code=response.status_code,
                tags={
                    'endpoint': request.path,
                    'method': request.method,
                    'user_agent': request.performance_context.get('user_agent'),
                },
                user_id=str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
                session_id=request.performance_context.get('session_id'),
            )
            
            # Log database queries if any
            if hasattr(request, 'initial_queries'):
                query_count = len(connection.queries) - request.initial_queries
                if query_count > 0:
                    PerformanceMetric.objects.create(
                        metric_type='database_query',
                        name=f"Query count for {request.path}",
                        value=query_count,
                        unit='count',
                        source='database',
                        endpoint=request.path,
                        metadata={'queries': query_count},
                        severity='high' if query_count > 50 else 'medium' if query_count > 20 else 'low'
                    )
        
        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")
        
        return response

class DatabasePerformanceMiddleware:
    """Middleware to monitor database performance"""
    
    def __init__(self):
        self.local = threading.local()
    
    def __call__(self, execute, sql, params, many, context):
        """Monitor database query execution"""
        start_time = time.time()
        
        try:
            result = execute(sql, params, many, context)
            execution_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Log slow queries (configurable threshold)
            slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 1000)
            is_slow = execution_time > slow_query_threshold
            
            # Extract query information
            query_type = sql.strip().split()[0].upper() if sql.strip() else 'UNKNOWN'
            
            # Log database performance
            try:
                DatabasePerformanceLog.objects.create(
                    query=sql[:5000],  # Truncate very long queries
                    query_hash=hash(sql) % (10 ** 8),  # Simple hash for grouping
                    execution_time=execution_time,
                    database_name=context['connection'].alias,
                    query_type=query_type,
                    is_slow_query=is_slow,
                    metadata={
                        'params_count': len(params) if params else 0,
                        'many': many,
                    }
                )
            except Exception as e:
                logger.error(f"Error logging database performance: {e}")
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Log failed query
            try:
                DatabasePerformanceLog.objects.create(
                    query=sql[:5000],
                    query_hash=hash(sql) % (10 ** 8),
                    execution_time=execution_time,
                    database_name=context['connection'].alias,
                    query_type=sql.strip().split()[0].upper() if sql.strip() else 'UNKNOWN',
                    is_slow_query=True,
                    metadata={
                        'error': str(e),
                        'params_count': len(params) if params else 0,
                    }
                )
            except Exception as log_error:
                logger.error(f"Error logging failed query: {log_error}")
            
            raise

class SystemMetricsMiddleware(MiddlewareMixin):
    """Middleware to collect system metrics periodically"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_collection = 0
        self.collection_interval = 60  # seconds
        super().__init__(get_response)
    
    def process_request(self, request):
        """Collect system metrics if interval has passed"""
        current_time = time.time()
        
        if current_time - self.last_collection > self.collection_interval:
            self.collect_system_metrics()
            self.last_collection = current_time
        
        return None
    
    def collect_system_metrics(self):
        """Collect and store system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            PerformanceMetric.objects.create(
                metric_type='cpu_usage',
                name='System CPU Usage',
                value=cpu_percent,
                unit='%',
                source='system',
                severity='high' if cpu_percent > 80 else 'medium' if cpu_percent > 60 else 'low'
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            PerformanceMetric.objects.create(
                metric_type='memory_usage',
                name='System Memory Usage',
                value=memory.percent,
                unit='%',
                source='system',
                metadata={
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                },
                severity='high' if memory.percent > 85 else 'medium' if memory.percent > 70 else 'low'
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            PerformanceMetric.objects.create(
                metric_type='disk_usage',
                name='System Disk Usage',
                value=disk_percent,
                unit='%',
                source='system',
                metadata={
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                },
                severity='high' if disk_percent > 90 else 'medium' if disk_percent > 75 else 'low'
            )
            
            # Network I/O
            network = psutil.net_io_counters()
            PerformanceMetric.objects.create(
                metric_type='network_io',
                name='Network I/O',
                value=network.bytes_sent + network.bytes_recv,
                unit='bytes',
                source='system',
                metadata={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

class ErrorTrackingMiddleware(MiddlewareMixin):
    """Middleware to track and monitor errors"""
    
    def process_exception(self, request, exception):
        """Log exceptions and errors for monitoring"""
        try:
            # Log error metric
            PerformanceMetric.objects.create(
                metric_type='error_rate',
                name=f"Error: {exception.__class__.__name__}",
                value=1,
                unit='count',
                source='application',
                endpoint=request.path if hasattr(request, 'path') else 'unknown',
                metadata={
                    'exception_type': exception.__class__.__name__,
                    'exception_message': str(exception),
                    'method': request.method if hasattr(request, 'method') else 'unknown',
                },
                severity='critical'
            )
            
            # Log APM error transaction
            if hasattr(request, 'transaction_id'):
                ApplicationPerformanceMonitor.objects.create(
                    transaction_id=request.transaction_id,
                    transaction_type='web_request',
                    name=f"ERROR: {request.method} {request.path}",
                    duration=0,
                    start_time=getattr(request, 'start_time', time.time()),
                    end_time=time.time(),
                    status_code=500,
                    error_message=str(exception),
                    stack_trace=str(exception.__traceback__) if hasattr(exception, '__traceback__') else None,
                    tags={
                        'error': True,
                        'exception_type': exception.__class__.__name__,
                    }
                )
        
        except Exception as e:
            logger.error(f"Error logging exception metrics: {e}")
        
        return None