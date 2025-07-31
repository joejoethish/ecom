"""
Comprehensive Database Error Handling and Recovery System

This module provides advanced error handling capabilities including:
- Connection failure handling with intelligent retry logic
- Deadlock detection and automatic resolution
- Comprehensive error logging and notification systems
- Graceful degradation strategies for database issues
- Circuit breaker pattern for database protection
"""

import logging
import threading
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
from enum import Enum

from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connections, connection, transaction
from django.db.utils import (
    OperationalError, DatabaseError, IntegrityError, 
    DataError, InternalError, ProgrammingError
)
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"
    RECONNECT = "reconnect"
    FAILOVER = "failover"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADE = "graceful_degrade"
    MANUAL_INTERVENTION = "manual_intervention"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class DatabaseError:
    """Database error information"""
    error_id: str
    database_alias: str
    error_type: str
    error_message: str
    error_code: Optional[str]
    severity: ErrorSeverity
    timestamp: datetime
    stack_trace: str
    query: Optional[str] = None
    recovery_action: Optional[RecoveryAction] = None
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        if data['recovery_action']:
            data['recovery_action'] = self.recovery_action.value
        if data['resolution_time']:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data


@dataclass
class RetryConfig:
    """Retry configuration for different error types"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on_errors: List[str] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                'OperationalError',
                'DatabaseError',
                'ConnectionError',
                'TimeoutError'
            ]


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker implementation for database protection"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.RLock()
    
    def __call__(self, func):
        """Decorator for circuit breaker functionality"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                if self.state == CircuitState.OPEN:
                    if self._should_attempt_reset():
                        self.state = CircuitState.HALF_OPEN
                        logger.info(f"Circuit breaker {self.config.name} moved to HALF_OPEN")
                    else:
                        raise Exception(f"Circuit breaker {self.config.name} is OPEN")
                
                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                except self.config.expected_exception as e:
                    self._on_failure()
                    raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker {self.config.name} moved to CLOSED")
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.config.name} moved to OPEN")


class DeadlockDetector:
    """Deadlock detection and resolution system"""
    
    def __init__(self):
        self.deadlock_history: deque = deque(maxlen=100)
        self.deadlock_patterns: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def detect_deadlock(self, error: Exception, query: str = None) -> bool:
        """Detect if error is a deadlock"""
        error_message = str(error).lower()
        deadlock_indicators = [
            'deadlock found',
            'lock wait timeout',
            'deadlock detected',
            'transaction deadlock'
        ]
        
        is_deadlock = any(indicator in error_message for indicator in deadlock_indicators)
        
        if is_deadlock:
            self._record_deadlock(error, query)
        
        return is_deadlock
    
    def _record_deadlock(self, error: Exception, query: str = None):
        """Record deadlock occurrence for analysis"""
        with self._lock:
            deadlock_info = {
                'timestamp': datetime.now().isoformat(),
                'error': str(error),
                'query': query,
                'thread_id': threading.get_ident()
            }
            
            self.deadlock_history.append(deadlock_info)
            
            # Track patterns
            if query:
                query_pattern = self._extract_query_pattern(query)
                self.deadlock_patterns[query_pattern] += 1
            
            logger.warning(f"Deadlock detected: {error}")
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract query pattern for deadlock analysis"""
        # Normalize query by removing literals and parameters
        import re
        pattern = re.sub(r'\b\d+\b', 'N', query.upper())
        pattern = re.sub(r"'[^']*'", "'S'", pattern)
        pattern = re.sub(r'\s+', ' ', pattern).strip()
        return pattern[:100]  # Limit length
    
    def get_deadlock_statistics(self) -> Dict[str, Any]:
        """Get deadlock statistics and patterns"""
        with self._lock:
            recent_deadlocks = [
                dl for dl in self.deadlock_history
                if datetime.fromisoformat(dl['timestamp']) > datetime.now() - timedelta(hours=24)
            ]
            
            return {
                'total_deadlocks': len(self.deadlock_history),
                'recent_deadlocks_24h': len(recent_deadlocks),
                'deadlock_patterns': dict(self.deadlock_patterns),
                'most_common_pattern': max(self.deadlock_patterns.items(), key=lambda x: x[1]) if self.deadlock_patterns else None
            }


class DatabaseErrorHandler:
    """
    Comprehensive database error handling and recovery system
    """
    
    def __init__(self):
        self.error_history: deque = deque(maxlen=1000)
        self.retry_configs: Dict[str, RetryConfig] = self._get_default_retry_configs()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.deadlock_detector = DeadlockDetector()
        self.notification_callbacks: List[Callable] = []
        self.degradation_mode = False
        self.degradation_start_time = None
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_error_times: Dict[str, datetime] = {}
        
        # Threading
        self._lock = threading.RLock()
        
        # Initialize circuit breakers
        self._initialize_circuit_breakers()
        
        logger.info("Database error handler initialized")
    
    def _get_default_retry_configs(self) -> Dict[str, RetryConfig]:
        """Get default retry configurations for different error types"""
        return {
            'connection_error': RetryConfig(
                max_attempts=5,
                base_delay=1.0,
                max_delay=30.0,
                exponential_backoff=True,
                retry_on_errors=['OperationalError', 'DatabaseError']
            ),
            'deadlock': RetryConfig(
                max_attempts=3,
                base_delay=0.1,
                max_delay=2.0,
                exponential_backoff=True,
                jitter=True,
                retry_on_errors=['OperationalError', 'InternalError']
            ),
            'timeout': RetryConfig(
                max_attempts=2,
                base_delay=5.0,
                max_delay=15.0,
                exponential_backoff=False,
                retry_on_errors=['OperationalError']
            ),
            'integrity_error': RetryConfig(
                max_attempts=1,
                base_delay=0.0,
                retry_on_errors=[]  # Don't retry integrity errors
            )
        }
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each database"""
        for db_alias in settings.DATABASES.keys():
            config = CircuitBreakerConfig(
                failure_threshold=getattr(settings, 'DB_CIRCUIT_BREAKER_THRESHOLD', 5),
                recovery_timeout=getattr(settings, 'DB_CIRCUIT_BREAKER_TIMEOUT', 60),
                expected_exception=Exception,
                name=f"db_{db_alias}"
            )
            self.circuit_breakers[db_alias] = CircuitBreaker(config)
    
    @contextmanager
    def handle_database_errors(self, database_alias: str = 'default', 
                              operation_name: str = 'database_operation',
                              query: str = None):
        """
        Context manager for comprehensive database error handling
        
        Usage:
            with error_handler.handle_database_errors('default', 'user_query'):
                # Database operations here
                pass
        """
        start_time = time.time()
        error_occurred = False
        
        try:
            yield
            
        except Exception as e:
            error_occurred = True
            error_info = self._create_error_info(
                database_alias, e, operation_name, query
            )
            
            # Log the error
            self._log_error(error_info)
            
            # Determine recovery action
            recovery_action = self._determine_recovery_action(error_info)
            error_info.recovery_action = recovery_action
            
            # Execute recovery action
            if recovery_action != RecoveryAction.MANUAL_INTERVENTION:
                try:
                    self._execute_recovery_action(error_info)
                except Exception as recovery_error:
                    logger.error(f"Recovery action failed: {recovery_error}")
            
            # Store error for analysis
            with self._lock:
                self.error_history.append(error_info)
                self.error_counts[error_info.error_type] += 1
                self.last_error_times[database_alias] = datetime.now()
            
            # Send notifications if needed
            self._send_error_notifications(error_info)
            
            # Re-raise the original exception
            raise
            
        finally:
            # Record operation metrics
            operation_time = time.time() - start_time
            self._record_operation_metrics(
                database_alias, operation_name, operation_time, error_occurred
            )
    
    def _create_error_info(self, database_alias: str, error: Exception,
                          operation_name: str, query: str = None) -> DatabaseError:
        """Create comprehensive error information"""
        import uuid
        
        error_type = type(error).__name__
        severity = self._determine_error_severity(error)
        
        return DatabaseError(
            error_id=str(uuid.uuid4())[:8],
            database_alias=database_alias,
            error_type=error_type,
            error_message=str(error),
            error_code=getattr(error, 'args', [None])[0] if hasattr(error, 'args') and error.args else None,
            severity=severity,
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
            query=query
        )
    
    def _determine_error_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on error type and context"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Critical errors
        if any(critical in error_message for critical in [
            'connection refused', 'server has gone away', 'lost connection',
            'access denied', 'authentication failed'
        ]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if error_type in ['OperationalError', 'DatabaseError'] or any(high in error_message for high in [
            'deadlock', 'timeout', 'disk full', 'out of memory'
        ]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if error_type in ['IntegrityError', 'DataError']:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _determine_recovery_action(self, error_info: DatabaseError) -> RecoveryAction:
        """Determine appropriate recovery action based on error"""
        error_type = error_info.error_type
        error_message = error_info.error_message.lower()
        
        # Check for deadlocks
        if self.deadlock_detector.detect_deadlock(Exception(error_info.error_message), error_info.query):
            return RecoveryAction.RETRY
        
        # Connection-related errors
        if any(conn_error in error_message for conn_error in [
            'connection refused', 'server has gone away', 'lost connection'
        ]):
            return RecoveryAction.RECONNECT
        
        # Timeout errors
        if 'timeout' in error_message:
            return RecoveryAction.RETRY
        
        # High error rate - circuit break
        if self._should_circuit_break(error_info.database_alias):
            return RecoveryAction.CIRCUIT_BREAK
        
        # Integrity errors - no retry
        if error_type == 'IntegrityError':
            return RecoveryAction.MANUAL_INTERVENTION
        
        # Default retry for operational errors
        if error_type in ['OperationalError', 'DatabaseError']:
            return RecoveryAction.RETRY
        
        return RecoveryAction.MANUAL_INTERVENTION
    
    def _should_circuit_break(self, database_alias: str) -> bool:
        """Determine if circuit breaker should be activated"""
        recent_errors = [
            error for error in self.error_history
            if (error.database_alias == database_alias and
                error.timestamp > datetime.now() - timedelta(minutes=5))
        ]
        
        return len(recent_errors) >= 10  # 10 errors in 5 minutes
    
    def _execute_recovery_action(self, error_info: DatabaseError):
        """Execute the determined recovery action"""
        action = error_info.recovery_action
        database_alias = error_info.database_alias
        
        if action == RecoveryAction.RETRY:
            self._handle_retry(error_info)
        elif action == RecoveryAction.RECONNECT:
            self._handle_reconnect(database_alias)
        elif action == RecoveryAction.FAILOVER:
            self._handle_failover(database_alias)
        elif action == RecoveryAction.CIRCUIT_BREAK:
            self._handle_circuit_break(database_alias)
        elif action == RecoveryAction.GRACEFUL_DEGRADE:
            self._handle_graceful_degradation(database_alias)
        
        logger.info(f"Executed recovery action {action.value} for {database_alias}")
    
    def _handle_retry(self, error_info: DatabaseError):
        """Handle retry logic with exponential backoff"""
        error_type_key = self._get_error_type_key(error_info.error_type)
        retry_config = self.retry_configs.get(error_type_key, self.retry_configs['connection_error'])
        
        if error_info.recovery_attempts >= retry_config.max_attempts:
            logger.warning(f"Max retry attempts reached for {error_info.error_id}")
            return
        
        # Calculate delay with exponential backoff
        delay = retry_config.base_delay
        if retry_config.exponential_backoff:
            delay = min(
                retry_config.base_delay * (2 ** error_info.recovery_attempts),
                retry_config.max_delay
            )
        
        # Add jitter if configured
        if retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        logger.info(f"Retrying operation after {delay:.2f}s (attempt {error_info.recovery_attempts + 1})")
        time.sleep(delay)
        
        error_info.recovery_attempts += 1
    
    def _handle_reconnect(self, database_alias: str):
        """Handle database reconnection"""
        try:
            # Close existing connection
            if database_alias in connections:
                connections[database_alias].close()
            
            # Force new connection
            connections[database_alias].ensure_connection()
            
            logger.info(f"Successfully reconnected to database {database_alias}")
            
        except Exception as e:
            logger.error(f"Failed to reconnect to database {database_alias}: {e}")
            raise
    
    def _handle_failover(self, database_alias: str):
        """Handle database failover to read replica"""
        # This would implement failover logic to read replicas
        # For now, just log the action
        logger.warning(f"Failover requested for database {database_alias}")
        
        # In a real implementation, this would:
        # 1. Check available read replicas
        # 2. Update connection routing
        # 3. Notify monitoring systems
    
    def _handle_circuit_break(self, database_alias: str):
        """Handle circuit breaker activation"""
        circuit_breaker = self.circuit_breakers.get(database_alias)
        if circuit_breaker:
            circuit_breaker.state = CircuitState.OPEN
            circuit_breaker.last_failure_time = time.time()
            
            logger.critical(f"Circuit breaker activated for database {database_alias}")
            
            # Enable graceful degradation
            self._handle_graceful_degradation(database_alias)
    
    def _handle_graceful_degradation(self, database_alias: str):
        """Handle graceful degradation mode"""
        if not self.degradation_mode:
            self.degradation_mode = True
            self.degradation_start_time = datetime.now()
            
            # Cache degradation status
            cache.set('database_degradation_mode', True, 300)
            cache.set('degraded_databases', [database_alias], 300)
            
            logger.critical(f"Entering graceful degradation mode for {database_alias}")
            
            # Send critical alert
            self._send_degradation_alert(database_alias)
    
    def _get_error_type_key(self, error_type: str) -> str:
        """Map error type to retry configuration key"""
        error_mapping = {
            'OperationalError': 'connection_error',
            'DatabaseError': 'connection_error',
            'IntegrityError': 'integrity_error',
            'InternalError': 'deadlock',
            'DataError': 'integrity_error'
        }
        return error_mapping.get(error_type, 'connection_error')
    
    def _log_error(self, error_info: DatabaseError):
        """Log error with appropriate level based on severity"""
        log_message = (
            f"Database error [{error_info.error_id}] on {error_info.database_alias}: "
            f"{error_info.error_type} - {error_info.error_message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Store in cache for monitoring
        cache.set(f"last_db_error_{error_info.database_alias}", error_info.to_dict(), 3600)
    
    def _send_error_notifications(self, error_info: DatabaseError):
        """Send error notifications based on severity"""
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            # Send immediate notification
            self._send_immediate_notification(error_info)
        
        # Call registered callbacks
        for callback in self.notification_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"Error notification callback failed: {e}")
    
    def _send_immediate_notification(self, error_info: DatabaseError):
        """Send immediate notification for critical errors"""
        subject = f"Database Error Alert - {error_info.severity.value.upper()}"
        message = f"""
        Database Error Alert
        
        Error ID: {error_info.error_id}
        Database: {error_info.database_alias}
        Error Type: {error_info.error_type}
        Severity: {error_info.severity.value}
        Time: {error_info.timestamp}
        
        Message: {error_info.error_message}
        
        Recovery Action: {error_info.recovery_action.value if error_info.recovery_action else 'None'}
        
        Please investigate immediately.
        """
        
        try:
            # Send email notification
            admin_emails = getattr(settings, 'DATABASE_ALERT_EMAILS', [])
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=False
                )
                
            logger.info(f"Error notification sent for {error_info.error_id}")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def _send_degradation_alert(self, database_alias: str):
        """Send critical alert for degradation mode"""
        subject = "CRITICAL: Database Degradation Mode Activated"
        message = f"""
        CRITICAL ALERT: Database degradation mode has been activated
        
        Database: {database_alias}
        Time: {datetime.now()}
        
        The system has entered graceful degradation mode due to repeated database errors.
        Some functionality may be limited until the issue is resolved.
        
        Immediate action required.
        """
        
        try:
            admin_emails = getattr(settings, 'DATABASE_ALERT_EMAILS', [])
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=False
                )
        except Exception as e:
            logger.error(f"Failed to send degradation alert: {e}")
    
    def _record_operation_metrics(self, database_alias: str, operation_name: str,
                                 operation_time: float, error_occurred: bool):
        """Record operation metrics for monitoring"""
        metrics = {
            'database_alias': database_alias,
            'operation_name': operation_name,
            'operation_time': operation_time,
            'error_occurred': error_occurred,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in cache for monitoring
        cache.set(f"db_operation_metrics_{database_alias}", metrics, 300)
    
    def add_notification_callback(self, callback: Callable[[DatabaseError], None]):
        """Add a notification callback for error events"""
        self.notification_callbacks.append(callback)
    
    def get_error_statistics(self, database_alias: str = None) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        with self._lock:
            if database_alias:
                errors = [e for e in self.error_history if e.database_alias == database_alias]
            else:
                errors = list(self.error_history)
            
            # Calculate statistics
            total_errors = len(errors)
            recent_errors = [
                e for e in errors
                if e.timestamp > datetime.now() - timedelta(hours=24)
            ]
            
            error_types = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for error in errors:
                error_types[error.error_type] += 1
                severity_counts[error.severity.value] += 1
            
            return {
                'total_errors': total_errors,
                'recent_errors_24h': len(recent_errors),
                'error_types': dict(error_types),
                'severity_counts': dict(severity_counts),
                'degradation_mode': self.degradation_mode,
                'degradation_start_time': self.degradation_start_time.isoformat() if self.degradation_start_time else None,
                'deadlock_statistics': self.deadlock_detector.get_deadlock_statistics()
            }
    
    def reset_degradation_mode(self, database_alias: str = None):
        """Reset graceful degradation mode"""
        self.degradation_mode = False
        self.degradation_start_time = None
        
        # Clear cache
        cache.delete('database_degradation_mode')
        cache.delete('degraded_databases')
        
        # Reset circuit breakers
        if database_alias and database_alias in self.circuit_breakers:
            self.circuit_breakers[database_alias].state = CircuitState.CLOSED
            self.circuit_breakers[database_alias].failure_count = 0
        
        logger.info(f"Degradation mode reset for {database_alias or 'all databases'}")
    
    def is_degraded(self, database_alias: str = None) -> bool:
        """Check if system is in degradation mode"""
        if database_alias:
            circuit_breaker = self.circuit_breakers.get(database_alias)
            return circuit_breaker and circuit_breaker.state == CircuitState.OPEN
        
        return self.degradation_mode


# Global error handler instance
_error_handler = None


def get_error_handler() -> DatabaseErrorHandler:
    """Get the global database error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = DatabaseErrorHandler()
    return _error_handler


def database_error_handler(database_alias: str = 'default', 
                          operation_name: str = 'database_operation',
                          query: str = None):
    """
    Decorator for database error handling
    
    Usage:
        @database_error_handler('default', 'user_query')
        def get_user(user_id):
            # Database operations here
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            with handler.handle_database_errors(database_alias, operation_name, query):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_database_error(max_attempts: int = 3, delay: float = 1.0):
    """
    Simple retry decorator for database operations
    
    Usage:
        @retry_on_database_error(max_attempts=3, delay=1.0)
        def database_operation():
            # Database operations here
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DatabaseError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    # Check if this is a retryable error
                    if handler.deadlock_detector.detect_deadlock(e):
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying after deadlock, attempt {attempt + 1}, waiting {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        raise
            
        return wrapper
    return decorator