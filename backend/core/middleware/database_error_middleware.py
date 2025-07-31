"""
Database Error Handling Middleware

This middleware integrates the database error handling system with Django's
request/response cycle, providing automatic error handling and recovery
for database operations during request processing.
"""

import logging
import time
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db import connections
from django.db.utils import OperationalError, DatabaseError
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from ..database_error_handler import get_error_handler, DatabaseError as DBError

logger = logging.getLogger(__name__)


class DatabaseErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for automatic database error handling and recovery
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.error_handler = get_error_handler()
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request and check for degradation mode
        """
        # Check if system is in degradation mode
        if self.error_handler.is_degraded():
            degraded_databases = cache.get('degraded_databases', [])
            
            # Return degraded service response for non-essential endpoints
            if self._is_non_essential_endpoint(request.path):
                return JsonResponse({
                    'error': 'Service temporarily degraded',
                    'message': 'Some features are temporarily unavailable due to database issues',
                    'degraded_databases': degraded_databases,
                    'retry_after': 60
                }, status=503)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process response and handle any database-related issues
        """
        # Check for database connection issues during request processing
        for db_alias in settings.DATABASES.keys():
            try:
                connection = connections[db_alias]
                if hasattr(connection, 'queries') and connection.queries:
                    # Log slow queries for monitoring
                    slow_queries = [
                        q for q in connection.queries
                        if float(q.get('time', 0)) > getattr(settings, 'SLOW_QUERY_THRESHOLD', 2.0)
                    ]
                    
                    for query in slow_queries:
                        logger.warning(
                            f"Slow query detected on {db_alias}: {query['time']}s - {query['sql'][:200]}"
                        )
            except Exception as e:
                logger.error(f"Error checking database queries for {db_alias}: {e}")
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """
        Handle database exceptions during request processing
        """
        if isinstance(exception, (OperationalError, DatabaseError)):
            # Use error handler to process the exception
            try:
                with self.error_handler.handle_database_errors(
                    database_alias='default',
                    operation_name=f"{request.method} {request.path}",
                    query=getattr(exception, 'query', None)
                ):
                    # This will log the error and attempt recovery
                    pass
            except Exception:
                # Error handler processed the exception
                pass
            
            # Return appropriate error response
            if request.content_type == 'application/json' or request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Database error',
                    'message': 'A database error occurred. Please try again.',
                    'type': type(exception).__name__,
                    'retry_after': 5
                }, status=503)
            else:
                # For non-API requests, let Django handle it normally
                return None
        
        return None
    
    def _is_non_essential_endpoint(self, path: str) -> bool:
        """
        Determine if an endpoint is non-essential and can be degraded
        """
        non_essential_patterns = [
            '/api/analytics/',
            '/api/recommendations/',
            '/api/reviews/',
            '/api/search/suggestions/',
            '/api/notifications/',
        ]
        
        essential_patterns = [
            '/api/auth/',
            '/api/users/profile/',
            '/api/orders/',
            '/api/payments/',
            '/admin/',
        ]
        
        # Check if it's an essential endpoint first
        for pattern in essential_patterns:
            if path.startswith(pattern):
                return False
        
        # Check if it's a non-essential endpoint
        for pattern in non_essential_patterns:
            if path.startswith(pattern):
                return True
        
        # Default to essential for unknown endpoints
        return False


class DatabaseConnectionPoolMiddleware(MiddlewareMixin):
    """
    Middleware for managing database connection pool health
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Check connection pool health before processing request
        """
        try:
            from ..connection_pool import get_pool_manager
            pool_manager = get_pool_manager()
            
            # Check pool status
            pool_status = pool_manager.get_pool_status()
            
            for pool_name, status in pool_status.items():
                if not status['healthy']:
                    logger.warning(f"Unhealthy connection pool detected: {pool_name}")
                    
                    # If all pools are unhealthy, return service unavailable
                    if not any(s['healthy'] for s in pool_status.values()):
                        return JsonResponse({
                            'error': 'Service unavailable',
                            'message': 'Database connection pools are unhealthy',
                            'retry_after': 30
                        }, status=503)
        
        except Exception as e:
            logger.error(f"Error checking connection pool health: {e}")
        
        return None


class DatabaseMetricsMiddleware(MiddlewareMixin):
    """
    Middleware for collecting database operation metrics
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest):
        """
        Start timing database operations for this request
        """
        request._db_operation_start = time.time()
        request._db_query_count_start = {}
        
        # Record initial query counts for each database
        for db_alias in settings.DATABASES.keys():
            try:
                connection = connections[db_alias]
                request._db_query_count_start[db_alias] = len(connection.queries)
            except Exception:
                request._db_query_count_start[db_alias] = 0
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Record database operation metrics for this request
        """
        if hasattr(request, '_db_operation_start'):
            operation_time = time.time() - request._db_operation_start
            
            # Calculate query counts for each database
            total_queries = 0
            for db_alias in settings.DATABASES.keys():
                try:
                    connection = connections[db_alias]
                    start_count = request._db_query_count_start.get(db_alias, 0)
                    current_count = len(connection.queries)
                    query_count = current_count - start_count
                    total_queries += query_count
                    
                    # Store metrics in cache for monitoring
                    cache.set(
                        f"db_request_metrics_{db_alias}",
                        {
                            'path': request.path,
                            'method': request.method,
                            'query_count': query_count,
                            'operation_time': operation_time,
                            'timestamp': time.time()
                        },
                        300  # 5 minutes
                    )
                    
                except Exception as e:
                    logger.error(f"Error calculating query metrics for {db_alias}: {e}")
            
            # Log slow requests
            if operation_time > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 5.0):
                logger.warning(
                    f"Slow request: {request.method} {request.path} - "
                    f"{operation_time:.2f}s, {total_queries} queries"
                )
            
            # Add performance headers for debugging
            if getattr(settings, 'DEBUG', False):
                response['X-DB-Queries'] = str(total_queries)
                response['X-DB-Time'] = f"{operation_time:.3f}"
        
        return response


class DatabaseHealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware for periodic database health checks
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.last_health_check = {}
        self.health_check_interval = getattr(settings, 'DB_HEALTH_CHECK_INTERVAL', 60)  # seconds
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Perform periodic health checks on database connections
        """
        current_time = time.time()
        
        for db_alias in settings.DATABASES.keys():
            last_check = self.last_health_check.get(db_alias, 0)
            
            if current_time - last_check > self.health_check_interval:
                try:
                    self._perform_health_check(db_alias)
                    self.last_health_check[db_alias] = current_time
                except Exception as e:
                    logger.error(f"Health check failed for {db_alias}: {e}")
                    
                    # Store health check failure
                    cache.set(f"db_health_check_failed_{db_alias}", True, 300)
        
        return None
    
    def _perform_health_check(self, db_alias: str):
        """
        Perform a simple health check on the database
        """
        connection = connections[db_alias]
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                # Health check passed
                cache.delete(f"db_health_check_failed_{db_alias}")
                cache.set(f"db_health_check_success_{db_alias}", True, 300)
            else:
                raise Exception("Health check query returned unexpected result")