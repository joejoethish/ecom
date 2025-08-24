"""
Correlation ID Middleware for Django

This middleware assigns unique correlation IDs to all incoming requests
and ensures they are propagated throughout the request lifecycle.
"""
import uuid
import logging
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import threading

logger = logging.getLogger(__name__)

# Thread-local storage for correlation ID
_correlation_id_storage = threading.local()


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Middleware that assigns a unique correlation ID to each request.
    
    The correlation ID can be:
    1. Provided by the client via X-Correlation-ID header
    2. Auto-generated if not provided
    
    The correlation ID is:
    - Added to the request object
    - Added to response headers
    - Made available to logging throughout the request
    - Stored in thread-local storage for access anywhere in the request cycle
    """
    
    CORRELATION_ID_HEADER = 'X-Correlation-ID'
    CORRELATION_ID_RESPONSE_HEADER = 'X-Correlation-ID'
    
    def process_request(self, request: HttpRequest) -> None:
        """
        Process incoming request and assign correlation ID.
        
        Args:
            request: The incoming HTTP request
        """
        # Try to get correlation ID from request headers
        correlation_id = request.META.get(
            f'HTTP_{self.CORRELATION_ID_HEADER.upper().replace("-", "_")}'
        )
        
        # Generate new correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Validate correlation ID format (should be UUID-like)
        if not self._is_valid_correlation_id(correlation_id):
            logger.warning(
                f"Invalid correlation ID format received: {correlation_id}. "
                f"Generating new one."
            )
            correlation_id = str(uuid.uuid4())
        
        # Store correlation ID in request
        request.correlation_id = correlation_id
        
        # Store in thread-local storage for global access
        _correlation_id_storage.correlation_id = correlation_id
        
        # Log request start with correlation ID
        user_info = 'Anonymous'
        if hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_info = str(request.user.id)
        
        logger.info(
            f"Request started - Correlation ID: {correlation_id}, "
            f"Method: {request.method}, Path: {request.path}, "
            f"User: {user_info}"
        )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process response and add correlation ID to headers.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            Modified HTTP response with correlation ID header
        """
        correlation_id = getattr(request, 'correlation_id', None)
        
        if correlation_id:
            # Add correlation ID to response headers
            response[self.CORRELATION_ID_RESPONSE_HEADER] = correlation_id
            
            # Log request completion
            logger.info(
                f"Request completed - Correlation ID: {correlation_id}, "
                f"Status: {response.status_code}, "
                f"Method: {request.method}, Path: {request.path}"
            )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """
        Process exceptions and log with correlation ID.
        
        Args:
            request: The HTTP request
            exception: The exception that occurred
        """
        correlation_id = getattr(request, 'correlation_id', None)
        
        if correlation_id:
            logger.error(
                f"Request failed - Correlation ID: {correlation_id}, "
                f"Method: {request.method}, Path: {request.path}, "
                f"Exception: {type(exception).__name__}: {str(exception)}"
            )
    
    def _is_valid_correlation_id(self, correlation_id: str) -> bool:
        """
        Validate correlation ID format.
        
        Args:
            correlation_id: The correlation ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not correlation_id or not isinstance(correlation_id, str):
            return False
        
        # Check length (UUID is 36 characters with hyphens)
        if len(correlation_id) < 8 or len(correlation_id) > 64:
            return False
        
        # Check for basic UUID format (optional - can be any string)
        try:
            uuid.UUID(correlation_id)
            return True
        except ValueError:
            # Allow non-UUID formats but with reasonable constraints
            return correlation_id.replace('-', '').replace('_', '').isalnum()


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from thread-local storage.
    
    Returns:
        The current correlation ID or None if not set
    """
    return getattr(_correlation_id_storage, 'correlation_id', None)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in thread-local storage.
    
    Args:
        correlation_id: The correlation ID to set
    """
    _correlation_id_storage.correlation_id = correlation_id


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to log record.
        
        Args:
            record: The log record to modify
            
        Returns:
            True to allow the record to be logged
        """
        correlation_id = get_correlation_id()
        record.correlation_id = correlation_id or 'N/A'
        return True


# Utility functions for correlation ID management
class CorrelationIdManager:
    """
    Utility class for managing correlation IDs throughout the application.
    """
    
    @staticmethod
    def generate_correlation_id() -> str:
        """
        Generate a new correlation ID.
        
        Returns:
            A new UUID-based correlation ID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def get_current_correlation_id() -> Optional[str]:
        """
        Get the current correlation ID.
        
        Returns:
            The current correlation ID or None if not set
        """
        return get_correlation_id()
    
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
            # Log the parent-child relationship
            logger.debug(
                f"Created child correlation ID: {child_id} "
                f"for parent: {parent_id}"
            )
        
        return child_id
    
    @staticmethod
    def log_with_correlation_id(level: str, message: str, **kwargs) -> None:
        """
        Log a message with correlation ID context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: The message to log
            **kwargs: Additional context to include
        """
        correlation_id = get_correlation_id()
        
        # Add correlation ID to the message
        if correlation_id:
            message = f"[{correlation_id}] {message}"
        
        # Get logger and log at appropriate level
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, extra=kwargs)