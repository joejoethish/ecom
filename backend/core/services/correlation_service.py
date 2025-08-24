"""
Correlation ID Service for Backend Operations

This service provides utilities for propagating correlation IDs
across all backend operations including database queries, 
external API calls, and background tasks.
"""
import logging
import uuid
from typing import Optional, Dict, Any, Callable
from functools import wraps
from django.db import connection
from django.core.cache import cache
from core.middleware.correlation_id_middleware import get_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)


class CorrelationIdService:
    """
    Service for managing correlation IDs across backend operations.
    """
    
    CACHE_PREFIX = 'correlation_id'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_current_correlation_id() -> Optional[str]:
        """
        Get the current correlation ID from thread-local storage.
        
        Returns:
            The current correlation ID or None if not set
        """
        return get_correlation_id()
    
    @staticmethod
    def set_current_correlation_id(correlation_id: str) -> None:
        """
        Set the current correlation ID in thread-local storage.
        
        Args:
            correlation_id: The correlation ID to set
        """
        set_correlation_id(correlation_id)
    
    @staticmethod
    def generate_correlation_id() -> str:
        """
        Generate a new correlation ID.
        
        Returns:
            A new UUID-based correlation ID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def create_child_correlation_id(parent_id: Optional[str] = None) -> str:
        """
        Create a child correlation ID for sub-operations.
        
        Args:
            parent_id: The parent correlation ID (uses current if not provided)
            
        Returns:
            A new child correlation ID
        """
        if not parent_id:
            parent_id = get_correlation_id()
        
        child_id = str(uuid.uuid4())
        
        if parent_id:
            logger.debug(
                f"Created child correlation ID: {child_id} for parent: {parent_id}"
            )
        
        return child_id
    
    @staticmethod
    def store_correlation_context(correlation_id: str, context: Dict[str, Any]) -> None:
        """
        Store correlation context in cache for later retrieval.
        
        Args:
            correlation_id: The correlation ID
            context: Context data to store
        """
        cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
        cache.set(cache_key, context, CorrelationIdService.CACHE_TIMEOUT)
        
        logger.debug(f"Stored correlation context for ID: {correlation_id}")
    
    @staticmethod
    def get_correlation_context(correlation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve correlation context from cache.
        
        Args:
            correlation_id: The correlation ID
            
        Returns:
            The stored context or None if not found
        """
        cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
        context = cache.get(cache_key)
        
        if context:
            logger.debug(f"Retrieved correlation context for ID: {correlation_id}")
        
        return context
    
    @staticmethod
    def clear_correlation_context(correlation_id: str) -> None:
        """
        Clear correlation context from cache.
        
        Args:
            correlation_id: The correlation ID
        """
        cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
        cache.delete(cache_key)
        
        logger.debug(f"Cleared correlation context for ID: {correlation_id}")


def with_correlation_id(func: Callable) -> Callable:
    """
    Decorator to ensure correlation ID is available in function execution.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        correlation_id = get_correlation_id()
        
        if not correlation_id:
            correlation_id = CorrelationIdService.generate_correlation_id()
            set_correlation_id(correlation_id)
            logger.debug(f"Generated correlation ID for function {func.__name__}: {correlation_id}")
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Function {func.__name__} failed with correlation ID {correlation_id}: {str(e)}"
            )
            raise
    
    return wrapper


def log_database_operation(operation: str, table: str, correlation_id: Optional[str] = None) -> None:
    """
    Log database operations with correlation ID.
    
    Args:
        operation: The database operation (SELECT, INSERT, UPDATE, DELETE)
        table: The table name
        correlation_id: The correlation ID (uses current if not provided)
    """
    if not correlation_id:
        correlation_id = get_correlation_id()
    
    logger.info(
        f"Database operation - Correlation ID: {correlation_id}, "
        f"Operation: {operation}, Table: {table}"
    )


class DatabaseCorrelationMixin:
    """
    Mixin for Django models to add correlation ID tracking to database operations.
    """
    
    def save(self, *args, **kwargs):
        """Override save to log with correlation ID."""
        correlation_id = get_correlation_id()
        
        if correlation_id:
            operation = "INSERT" if self.pk is None else "UPDATE"
            log_database_operation(operation, self._meta.db_table, correlation_id)
        
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to log with correlation ID."""
        correlation_id = get_correlation_id()
        
        if correlation_id:
            log_database_operation("DELETE", self._meta.db_table, correlation_id)
        
        return super().delete(*args, **kwargs)


class CorrelationIdQuerySet:
    """
    Custom QuerySet that logs database queries with correlation ID.
    """
    
    def _execute_query(self, query_type: str):
        """Log query execution with correlation ID."""
        correlation_id = get_correlation_id()
        
        if correlation_id:
            log_database_operation(query_type, self.model._meta.db_table, correlation_id)
    
    def filter(self, *args, **kwargs):
        """Override filter to log with correlation ID."""
        self._execute_query("SELECT")
        return super().filter(*args, **kwargs)
    
    def create(self, **kwargs):
        """Override create to log with correlation ID."""
        self._execute_query("INSERT")
        return super().create(**kwargs)
    
    def update(self, **kwargs):
        """Override update to log with correlation ID."""
        self._execute_query("UPDATE")
        return super().update(**kwargs)
    
    def delete(self):
        """Override delete to log with correlation ID."""
        self._execute_query("DELETE")
        return super().delete()


class ExternalApiCorrelationMixin:
    """
    Mixin for external API calls to propagate correlation IDs.
    """
    
    def get_correlation_headers(self) -> Dict[str, str]:
        """
        Get headers with correlation ID for external API calls.
        
        Returns:
            Headers dictionary with correlation ID
        """
        correlation_id = get_correlation_id()
        
        if correlation_id:
            return {
                'X-Correlation-ID': correlation_id,
                'X-Request-ID': correlation_id,  # Some APIs use this header
            }
        
        return {}
    
    def log_external_api_call(self, method: str, url: str, correlation_id: Optional[str] = None) -> None:
        """
        Log external API calls with correlation ID.
        
        Args:
            method: HTTP method
            url: API endpoint URL
            correlation_id: The correlation ID (uses current if not provided)
        """
        if not correlation_id:
            correlation_id = get_correlation_id()
        
        logger.info(
            f"External API call - Correlation ID: {correlation_id}, "
            f"Method: {method}, URL: {url}"
        )


class CeleryCorrelationMixin:
    """
    Mixin for Celery tasks to propagate correlation IDs.
    """
    
    def apply_async_with_correlation_id(self, args=None, kwargs=None, correlation_id=None, **options):
        """
        Apply async task with correlation ID propagation.
        
        Args:
            args: Task arguments
            kwargs: Task keyword arguments
            correlation_id: The correlation ID to propagate
            **options: Additional Celery options
            
        Returns:
            AsyncResult object
        """
        if not correlation_id:
            correlation_id = get_correlation_id()
        
        if correlation_id:
            # Add correlation ID to task headers
            headers = options.get('headers', {})
            headers['correlation_id'] = correlation_id
            options['headers'] = headers
            
            logger.info(f"Queuing task with correlation ID: {correlation_id}")
        
        return self.apply_async(args=args, kwargs=kwargs, **options)
    
    def delay_with_correlation_id(self, *args, correlation_id=None, **kwargs):
        """
        Delay task with correlation ID propagation.
        
        Args:
            *args: Task arguments
            correlation_id: The correlation ID to propagate
            **kwargs: Task keyword arguments
            
        Returns:
            AsyncResult object
        """
        if not correlation_id:
            correlation_id = get_correlation_id()
        
        return self.apply_async_with_correlation_id(
            args=args, 
            kwargs=kwargs, 
            correlation_id=correlation_id
        )


# Utility functions for common operations
def execute_with_correlation_id(func: Callable, correlation_id: Optional[str] = None, *args, **kwargs):
    """
    Execute a function with a specific correlation ID.
    
    Args:
        func: The function to execute
        correlation_id: The correlation ID to use (generates new if not provided)
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        The function result
    """
    if not correlation_id:
        correlation_id = CorrelationIdService.generate_correlation_id()
    
    # Store current correlation ID
    current_id = get_correlation_id()
    
    try:
        # Set new correlation ID
        set_correlation_id(correlation_id)
        
        # Execute function
        result = func(*args, **kwargs)
        
        return result
    finally:
        # Restore previous correlation ID
        if current_id:
            set_correlation_id(current_id)
        else:
            # Clear if there was no previous ID
            set_correlation_id(None)


def trace_operation(operation_name: str, correlation_id: Optional[str] = None):
    """
    Decorator to trace operations with correlation ID.
    
    Args:
        operation_name: Name of the operation being traced
        correlation_id: The correlation ID to use
        
    Returns:
        The decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = correlation_id or get_correlation_id()
            
            logger.info(
                f"Operation started - Correlation ID: {trace_id}, "
                f"Operation: {operation_name}, Function: {func.__name__}"
            )
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(
                    f"Operation completed - Correlation ID: {trace_id}, "
                    f"Operation: {operation_name}, Function: {func.__name__}"
                )
                
                return result
            except Exception as e:
                logger.error(
                    f"Operation failed - Correlation ID: {trace_id}, "
                    f"Operation: {operation_name}, Function: {func.__name__}, "
                    f"Error: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator