"""
Error Handling Decorators and Context Managers

This module provides decorators and context managers for easy integration
of error handling and recovery mechanisms into existing code.
"""

import functools
import uuid
import logging
from typing import Any, Callable, Optional, Dict, Type, Union
from django.contrib.auth.models import User

from .error_handling import (
    ErrorRecoveryEngine, ErrorContext, error_recovery_engine,
    ErrorSeverity, ErrorCategory, RecoveryStrategy
)

logger = logging.getLogger(__name__)


def with_error_recovery(
    layer: str,
    component: str,
    operation: Optional[str] = None,
    correlation_id: Optional[uuid.UUID] = None,
    user: Optional[User] = None,
    recovery_strategy: Optional[RecoveryStrategy] = None,
    max_retries: Optional[int] = None,
    fallback_func: Optional[Callable] = None,
    ignore_exceptions: Optional[tuple] = None
):
    """
    Decorator for automatic error handling and recovery
    
    Args:
        layer: System layer (frontend, api, database, etc.)
        component: Component name
        operation: Operation name (defaults to function name)
        correlation_id: Correlation ID for tracing
        user: User context
        recovery_strategy: Override recovery strategy
        max_retries: Override max retries
        fallback_func: Fallback function to use
        ignore_exceptions: Tuple of exception types to ignore
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            context = ErrorContext(
                correlation_id=correlation_id,
                user=user,
                metadata={'function': func.__name__, 'module': func.__module__}
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if exception should be ignored
                if ignore_exceptions and isinstance(e, ignore_exceptions):
                    logger.debug(f"Ignoring exception {type(e).__name__} in {component}.{op_name}")
                    raise
                
                # Handle error with recovery engine
                recovery_result = error_recovery_engine.handle_error(
                    exception=e,
                    layer=layer,
                    component=component,
                    operation=op_name,
                    context=context,
                    original_func=func,
                    original_args=args,
                    original_kwargs=kwargs
                )
                
                # If recovery succeeded, return result
                if recovery_result is not None:
                    return recovery_result
                
                # If no recovery or recovery failed, re-raise
                raise
        
        return wrapper
    return decorator


def with_circuit_breaker(
    component: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
    fallback_func: Optional[Callable] = None
):
    """
    Decorator for circuit breaker pattern
    
    Args:
        component: Component name for circuit breaker
        failure_threshold: Number of failures before opening circuit
        timeout_seconds: Timeout before attempting to close circuit
        fallback_func: Fallback function when circuit is open
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .error_handling import CircuitBreaker
            
            circuit_breaker = CircuitBreaker(
                component_name=component,
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds
            )
            
            # Check if circuit is open
            if circuit_breaker.is_open():
                logger.warning(f"Circuit breaker is open for {component}")
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                else:
                    raise Exception(f"Circuit breaker is open for {component}")
            
            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    retry_on: Optional[tuple] = None,
    dont_retry_on: Optional[tuple] = None
):
    """
    Decorator for retry logic with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        backoff_multiplier: Multiplier for exponential backoff
        retry_on: Tuple of exception types to retry on
        dont_retry_on: Tuple of exception types to not retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .error_handling import RetryHandler
            
            retry_handler = RetryHandler(
                max_retries=max_retries,
                base_delay=base_delay,
                backoff_multiplier=backoff_multiplier
            )
            
            def should_retry(exception: Exception) -> bool:
                if dont_retry_on and isinstance(exception, dont_retry_on):
                    return False
                if retry_on and not isinstance(exception, retry_on):
                    return False
                return True
            
            def retry_func():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not should_retry(e):
                        raise
                    raise  # Let retry handler manage the retry
            
            return retry_handler.execute_with_retry(retry_func)
        
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable, fallback_on: Optional[tuple] = None):
    """
    Decorator for fallback mechanism
    
    Args:
        fallback_func: Function to call as fallback
        fallback_on: Tuple of exception types to use fallback for
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if fallback_on and not isinstance(e, fallback_on):
                    raise
                
                logger.warning(f"Using fallback for {func.__name__}: {e}")
                return fallback_func(*args, **kwargs)
        
        return wrapper
    return decorator


class ErrorHandlingContext:
    """Context manager for error handling within a block of code"""
    
    def __init__(self, layer: str, component: str, operation: str,
                 correlation_id: Optional[uuid.UUID] = None,
                 user: Optional[User] = None,
                 suppress_exceptions: bool = False,
                 fallback_result: Any = None):
        self.layer = layer
        self.component = component
        self.operation = operation
        self.correlation_id = correlation_id
        self.user = user
        self.suppress_exceptions = suppress_exceptions
        self.fallback_result = fallback_result
        self.context = ErrorContext(
            correlation_id=correlation_id,
            user=user,
            metadata={'operation': operation}
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # No exception occurred
        
        # Handle the exception
        try:
            recovery_result = error_recovery_engine.handle_error(
                exception=exc_val,
                layer=self.layer,
                component=self.component,
                operation=self.operation,
                context=self.context
            )
            
            # If recovery succeeded and we should suppress exceptions
            if recovery_result is not None and self.suppress_exceptions:
                return True  # Suppress the exception
            
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {recovery_error}")
        
        # If suppression is enabled, return fallback result
        if self.suppress_exceptions:
            return True  # Suppress the exception
        
        return False  # Don't suppress the exception


class CircuitBreakerContext:
    """Context manager for circuit breaker pattern"""
    
    def __init__(self, component: str, failure_threshold: int = 5,
                 timeout_seconds: int = 60, fallback_result: Any = None):
        self.component = component
        self.fallback_result = fallback_result
        
        from .error_handling import CircuitBreaker
        self.circuit_breaker = CircuitBreaker(
            component_name=component,
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds
        )
    
    def __enter__(self):
        if self.circuit_breaker.is_open():
            raise Exception(f"Circuit breaker is open for {self.component}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()
        
        return False  # Don't suppress exceptions


class RetryContext:
    """Context manager for retry logic"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 backoff_multiplier: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.attempt = 0
    
    def __enter__(self):
        self.attempt += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # No exception, don't suppress
        
        if self.attempt <= self.max_retries:
            import time
            delay = self.base_delay * (self.backoff_multiplier ** (self.attempt - 1))
            logger.warning(f"Attempt {self.attempt} failed, retrying in {delay}s: {exc_val}")
            time.sleep(delay)
            return True  # Suppress exception to allow retry
        
        return False  # Max retries reached, don't suppress


# Convenience functions for common error handling patterns

def handle_database_error(func: Callable) -> Callable:
    """Decorator for database error handling"""
    return with_error_recovery(
        layer='database',
        component='orm',
        max_retries=2,
        ignore_exceptions=(ValueError, TypeError)
    )(func)


def handle_api_error(func: Callable) -> Callable:
    """Decorator for API error handling"""
    return with_error_recovery(
        layer='api',
        component='view',
        max_retries=1
    )(func)


def handle_external_service_error(service_name: str) -> Callable:
    """Decorator factory for external service error handling"""
    def decorator(func: Callable) -> Callable:
        return with_circuit_breaker(
            component=service_name,
            failure_threshold=3,
            timeout_seconds=30
        )(with_retry(max_retries=2)(func))
    return decorator


def safe_execute(func: Callable, *args, default_result: Any = None, **kwargs) -> Any:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_result: Default result if function fails
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or default_result if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Safe execution failed for {func.__name__}: {e}")
        return default_result


def with_timeout(timeout_seconds: float):
    """Decorator for function timeout"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            # Set timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel timeout
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator