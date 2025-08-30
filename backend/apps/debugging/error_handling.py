"""
Comprehensive Error Handling and Recovery System

This module provides error classification, recovery strategies, circuit breakers,
fallback mechanisms, and error escalation for the debugging system.
"""

import uuid
import time
import logging
import traceback
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User

from .models import ErrorLog, WorkflowSession, TraceStep
from .utils import ErrorLogger

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    correlation_id: Optional[uuid.UUID] = None
    user: Optional[User] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorClassification:
    """Classification result for an error"""
    category: ErrorCategory
    severity: ErrorSeverity
    is_recoverable: bool
    recovery_strategy: RecoveryStrategy
    retry_count: int = 0
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    base_delay_seconds: float = 1.0
    timeout_seconds: Optional[float] = None
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


class ErrorClassifier:
    """Classifies errors and determines appropriate handling strategies"""
    
    def __init__(self):
        self._classification_rules = self._build_classification_rules()
    
    def classify_error(self, exception: Exception, layer: str, component: str, 
                      context: Optional[ErrorContext] = None) -> ErrorClassification:
        """Classify an error and determine handling strategy"""
        
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Check specific classification rules
        for rule in self._classification_rules:
            if rule['matcher'](exception, layer, component, error_message):
                return ErrorClassification(**rule['classification'])
        
        # Default classification for unmatched errors
        return ErrorClassification(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            is_recoverable=False,
            recovery_strategy=RecoveryStrategy.ESCALATE
        )
    
    def _build_classification_rules(self) -> List[Dict[str, Any]]:
        """Build error classification rules"""
        return [
            # Network errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['connection', 'timeout', 'network', 'unreachable', 'dns']
                ),
                'classification': {
                    'category': ErrorCategory.NETWORK,
                    'severity': ErrorSeverity.WARNING,
                    'is_recoverable': True,
                    'recovery_strategy': RecoveryStrategy.RETRY,
                    'max_retries': 3,
                    'base_delay_seconds': 2.0
                }
            },
            
            # Authentication errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['authentication', 'login', 'token', 'unauthorized', 'invalid credentials']
                ),
                'classification': {
                    'category': ErrorCategory.AUTHENTICATION,
                    'severity': ErrorSeverity.ERROR,
                    'is_recoverable': True,
                    'recovery_strategy': RecoveryStrategy.FALLBACK,
                    'max_retries': 1
                }
            },
            
            # Authorization errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['permission', 'forbidden', 'access denied', 'authorization']
                ),
                'classification': {
                    'category': ErrorCategory.AUTHORIZATION,
                    'severity': ErrorSeverity.ERROR,
                    'is_recoverable': False,
                    'recovery_strategy': RecoveryStrategy.ESCALATE
                }
            },
            
            # Validation errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['validation', 'invalid', 'required field', 'format error']
                ),
                'classification': {
                    'category': ErrorCategory.VALIDATION,
                    'severity': ErrorSeverity.WARNING,
                    'is_recoverable': False,
                    'recovery_strategy': RecoveryStrategy.ESCALATE
                }
            },
            
            # Database errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['database', 'sql', 'connection pool', 'deadlock', 'constraint']
                ) or layer == 'database',
                'classification': {
                    'category': ErrorCategory.DATABASE,
                    'severity': ErrorSeverity.CRITICAL,
                    'is_recoverable': True,
                    'recovery_strategy': RecoveryStrategy.CIRCUIT_BREAKER,
                    'max_retries': 2,
                    'circuit_breaker_threshold': 3,
                    'circuit_breaker_timeout': 30
                }
            },
            
            # External service errors
            {
                'matcher': lambda exc, layer, comp, msg: (
                    layer == 'external' or 
                    any(keyword in comp.lower() for keyword in ['api', 'service', 'client'])
                ),
                'classification': {
                    'category': ErrorCategory.EXTERNAL_SERVICE,
                    'severity': ErrorSeverity.ERROR,
                    'is_recoverable': True,
                    'recovery_strategy': RecoveryStrategy.CIRCUIT_BREAKER,
                    'max_retries': 3,
                    'circuit_breaker_threshold': 5,
                    'circuit_breaker_timeout': 60
                }
            },
            
            # Resource errors (memory, disk, etc.)
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['memory', 'disk', 'resource', 'quota', 'limit exceeded']
                ),
                'classification': {
                    'category': ErrorCategory.RESOURCE,
                    'severity': ErrorSeverity.CRITICAL,
                    'is_recoverable': False,
                    'recovery_strategy': RecoveryStrategy.MANUAL_INTERVENTION
                }
            },
            
            # Configuration errors
            {
                'matcher': lambda exc, layer, comp, msg: any(
                    keyword in msg.lower() for keyword in 
                    ['configuration', 'setting', 'environment', 'missing key']
                ),
                'classification': {
                    'category': ErrorCategory.CONFIGURATION,
                    'severity': ErrorSeverity.ERROR,
                    'is_recoverable': False,
                    'recovery_strategy': RecoveryStrategy.MANUAL_INTERVENTION
                }
            }
        ]


class CircuitBreaker:
    """Circuit breaker implementation for error recovery"""
    
    def __init__(self, component_name: str, failure_threshold: int = 5, 
                 timeout_seconds: int = 60, recovery_timeout: int = 30):
        self.component_name = component_name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.recovery_timeout = recovery_timeout
        self._cache_key_prefix = f"circuit_breaker:{component_name}"
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests)"""
        state = cache.get(f"{self._cache_key_prefix}:state", "closed")
        
        if state == "open":
            # Check if timeout has passed
            open_time = cache.get(f"{self._cache_key_prefix}:open_time")
            if open_time and (time.time() - open_time) > self.timeout_seconds:
                # Move to half-open state
                cache.set(f"{self._cache_key_prefix}:state", "half_open", self.recovery_timeout)
                return False
            return True
        
        return False
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is in half-open state"""
        return cache.get(f"{self._cache_key_prefix}:state") == "half_open"
    
    def record_success(self):
        """Record a successful operation"""
        if self.is_half_open():
            # Success in half-open state, close the circuit
            self._close_circuit()
        else:
            # Reset failure count on success
            cache.delete(f"{self._cache_key_prefix}:failures")
    
    def record_failure(self):
        """Record a failed operation"""
        if self.is_half_open():
            # Failure in half-open state, reopen the circuit
            self._open_circuit()
            return
        
        # Increment failure count
        failures = cache.get(f"{self._cache_key_prefix}:failures", 0) + 1
        cache.set(f"{self._cache_key_prefix}:failures", failures, 300)  # 5 minute TTL
        
        # Open circuit if threshold exceeded
        if failures >= self.failure_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit breaker"""
        cache.set(f"{self._cache_key_prefix}:state", "open", self.timeout_seconds)
        cache.set(f"{self._cache_key_prefix}:open_time", time.time(), self.timeout_seconds)
        logger.warning(f"Circuit breaker opened for {self.component_name}")
    
    def _close_circuit(self):
        """Close the circuit breaker"""
        cache.delete(f"{self._cache_key_prefix}:state")
        cache.delete(f"{self._cache_key_prefix}:failures")
        cache.delete(f"{self._cache_key_prefix}:open_time")
        logger.info(f"Circuit breaker closed for {self.component_name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        state = cache.get(f"{self._cache_key_prefix}:state", "closed")
        failures = cache.get(f"{self._cache_key_prefix}:failures", 0)
        open_time = cache.get(f"{self._cache_key_prefix}:open_time")
        
        return {
            'component': self.component_name,
            'state': state,
            'failures': failures,
            'failure_threshold': self.failure_threshold,
            'open_time': open_time,
            'timeout_seconds': self.timeout_seconds
        }


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 backoff_multiplier: float = 2.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.backoff_multiplier ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        # All retries exhausted, raise the last exception
        raise last_exception


class FallbackHandler:
    """Handles fallback mechanisms for failed operations"""
    
    def __init__(self):
        self._fallback_strategies = {}
    
    def register_fallback(self, component: str, operation: str, 
                         fallback_func: Callable, priority: int = 0):
        """Register a fallback function for a component operation"""
        key = f"{component}.{operation}"
        if key not in self._fallback_strategies:
            self._fallback_strategies[key] = []
        
        self._fallback_strategies[key].append({
            'function': fallback_func,
            'priority': priority
        })
        
        # Sort by priority (higher priority first)
        self._fallback_strategies[key].sort(key=lambda x: x['priority'], reverse=True)
    
    def execute_fallback(self, component: str, operation: str, 
                        original_args: tuple = (), original_kwargs: Dict = None,
                        error_context: Optional[ErrorContext] = None) -> Any:
        """Execute fallback for a failed operation"""
        key = f"{component}.{operation}"
        fallbacks = self._fallback_strategies.get(key, [])
        
        if not fallbacks:
            logger.warning(f"No fallback registered for {key}")
            return None
        
        original_kwargs = original_kwargs or {}
        
        for fallback in fallbacks:
            try:
                logger.info(f"Executing fallback for {key}")
                return fallback['function'](*original_args, **original_kwargs)
            except Exception as e:
                logger.error(f"Fallback failed for {key}: {e}")
                continue
        
        logger.error(f"All fallbacks failed for {key}")
        return None


class ErrorEscalationManager:
    """Manages error escalation and notification"""
    
    def __init__(self):
        self._escalation_rules = self._build_escalation_rules()
        self._notification_handlers = []
    
    def register_notification_handler(self, handler: Callable):
        """Register a notification handler"""
        self._notification_handlers.append(handler)
    
    def escalate_error(self, error_log: ErrorLog, classification: ErrorClassification,
                      context: Optional[ErrorContext] = None):
        """Escalate an error based on classification"""
        escalation_level = self._determine_escalation_level(error_log, classification)
        
        if escalation_level == 'none':
            return
        
        escalation_data = {
            'error_log': error_log,
            'classification': classification,
            'escalation_level': escalation_level,
            'context': context,
            'timestamp': timezone.now()
        }
        
        # Send notifications
        for handler in self._notification_handlers:
            try:
                handler(escalation_data)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")
    
    def _determine_escalation_level(self, error_log: ErrorLog, 
                                   classification: ErrorClassification) -> str:
        """Determine escalation level based on error and classification"""
        
        # Critical errors always escalate
        if classification.severity == ErrorSeverity.CRITICAL:
            return 'critical'
        
        # Check for error patterns that require escalation
        recent_errors = ErrorLog.objects.filter(
            layer=error_log.layer,
            component=error_log.component,
            error_type=error_log.error_type,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        if recent_errors >= 5:
            return 'high'
        elif recent_errors >= 3:
            return 'medium'
        elif classification.severity == ErrorSeverity.ERROR:
            return 'low'
        
        return 'none'
    
    def _build_escalation_rules(self) -> List[Dict[str, Any]]:
        """Build escalation rules"""
        return [
            {
                'condition': lambda error, classification: classification.severity == ErrorSeverity.CRITICAL,
                'level': 'critical',
                'actions': ['immediate_notification', 'create_incident', 'page_oncall']
            },
            {
                'condition': lambda error, classification: classification.category == ErrorCategory.DATABASE,
                'level': 'high',
                'actions': ['notification', 'create_incident']
            },
            {
                'condition': lambda error, classification: classification.severity == ErrorSeverity.ERROR,
                'level': 'medium',
                'actions': ['notification']
            }
        ]


class ErrorRecoveryEngine:
    """Main error recovery engine that coordinates all recovery mechanisms"""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.circuit_breakers = {}
        self.retry_handler = RetryHandler()
        self.fallback_handler = FallbackHandler()
        self.escalation_manager = ErrorEscalationManager()
    
    def handle_error(self, exception: Exception, layer: str, component: str,
                    operation: str = "unknown", context: Optional[ErrorContext] = None,
                    original_func: Optional[Callable] = None,
                    original_args: tuple = (), original_kwargs: Dict = None) -> Any:
        """Handle an error with appropriate recovery strategy"""
        
        # Classify the error
        classification = self.classifier.classify_error(exception, layer, component, context)
        
        # Log the error
        error_log = self._log_error(exception, layer, component, classification, context)
        
        # Apply recovery strategy
        recovery_result = None
        
        try:
            if classification.recovery_strategy == RecoveryStrategy.RETRY:
                recovery_result = self._handle_retry(
                    exception, classification, original_func, original_args, original_kwargs
                )
            
            elif classification.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                recovery_result = self._handle_circuit_breaker(
                    exception, layer, component, classification, original_func, 
                    original_args, original_kwargs
                )
            
            elif classification.recovery_strategy == RecoveryStrategy.FALLBACK:
                recovery_result = self._handle_fallback(
                    component, operation, classification, context, 
                    original_args, original_kwargs
                )
            
            elif classification.recovery_strategy == RecoveryStrategy.ESCALATE:
                self._handle_escalation(error_log, classification, context)
            
            elif classification.recovery_strategy == RecoveryStrategy.IGNORE:
                logger.info(f"Ignoring error as per classification: {exception}")
            
            elif classification.recovery_strategy == RecoveryStrategy.MANUAL_INTERVENTION:
                self._handle_manual_intervention(error_log, classification, context)
        
        except Exception as recovery_exception:
            logger.error(f"Error recovery failed: {recovery_exception}")
            # Escalate the recovery failure
            self.escalation_manager.escalate_error(error_log, classification, context)
        
        return recovery_result
    
    def _handle_retry(self, exception: Exception, classification: ErrorClassification,
                     original_func: Optional[Callable], original_args: tuple,
                     original_kwargs: Dict) -> Any:
        """Handle retry recovery strategy"""
        if not original_func:
            logger.warning("No original function provided for retry")
            return None
        
        retry_handler = RetryHandler(
            max_retries=classification.max_retries,
            base_delay=classification.base_delay_seconds,
            backoff_multiplier=classification.backoff_multiplier
        )
        
        return retry_handler.execute_with_retry(original_func, *original_args, **original_kwargs)
    
    def _handle_circuit_breaker(self, exception: Exception, layer: str, component: str,
                               classification: ErrorClassification, original_func: Optional[Callable],
                               original_args: tuple, original_kwargs: Dict) -> Any:
        """Handle circuit breaker recovery strategy"""
        circuit_breaker = self._get_circuit_breaker(component, classification)
        
        if circuit_breaker.is_open():
            logger.warning(f"Circuit breaker is open for {component}, using fallback")
            return self.fallback_handler.execute_fallback(
                component, "circuit_breaker_fallback", original_args, original_kwargs
            )
        
        # Record failure
        circuit_breaker.record_failure()
        
        # Try fallback if available
        return self.fallback_handler.execute_fallback(
            component, "error_fallback", original_args, original_kwargs
        )
    
    def _handle_fallback(self, component: str, operation: str, 
                        classification: ErrorClassification, context: Optional[ErrorContext],
                        original_args: tuple, original_kwargs: Dict) -> Any:
        """Handle fallback recovery strategy"""
        return self.fallback_handler.execute_fallback(
            component, operation, original_args, original_kwargs, context
        )
    
    def _handle_escalation(self, error_log: ErrorLog, classification: ErrorClassification,
                          context: Optional[ErrorContext]):
        """Handle escalation recovery strategy"""
        self.escalation_manager.escalate_error(error_log, classification, context)
    
    def _handle_manual_intervention(self, error_log: ErrorLog, classification: ErrorClassification,
                                   context: Optional[ErrorContext]):
        """Handle manual intervention recovery strategy"""
        # Mark error as requiring manual intervention
        error_log.metadata['requires_manual_intervention'] = True
        error_log.save()
        
        # Escalate with high priority
        self.escalation_manager.escalate_error(error_log, classification, context)
        
        logger.critical(f"Manual intervention required for error: {error_log.error_message}")
    
    def _get_circuit_breaker(self, component: str, classification: ErrorClassification) -> CircuitBreaker:
        """Get or create circuit breaker for component"""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = CircuitBreaker(
                component_name=component,
                failure_threshold=classification.circuit_breaker_threshold,
                timeout_seconds=classification.circuit_breaker_timeout
            )
        return self.circuit_breakers[component]
    
    def _log_error(self, exception: Exception, layer: str, component: str,
                   classification: ErrorClassification, context: Optional[ErrorContext]) -> ErrorLog:
        """Log error to database"""
        return ErrorLogger.log_exception(
            exception=exception,
            layer=layer,
            component=component,
            correlation_id=context.correlation_id if context else None,
            severity=classification.severity.value,
            user=context.user if context else None,
            request_path=context.request_path if context else None,
            request_method=context.request_method if context else None,
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
            metadata={
                'classification': {
                    'category': classification.category.value,
                    'severity': classification.severity.value,
                    'is_recoverable': classification.is_recoverable,
                    'recovery_strategy': classification.recovery_strategy.value
                },
                'context': context.metadata if context else {}
            }
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health based on error patterns"""
        # Get recent errors (last hour)
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        )
        
        # Get circuit breaker statuses
        circuit_breaker_statuses = {}
        for component, breaker in self.circuit_breakers.items():
            circuit_breaker_statuses[component] = breaker.get_status()
        
        # Calculate health metrics
        total_errors = recent_errors.count()
        critical_errors = recent_errors.filter(severity='critical').count()
        error_errors = recent_errors.filter(severity='error').count()
        
        # Determine overall health score (0-100)
        health_score = 100
        if critical_errors > 0:
            health_score -= min(critical_errors * 20, 80)
        if error_errors > 0:
            health_score -= min(error_errors * 5, 20)
        
        health_score = max(health_score, 0)
        
        # Determine health status
        if health_score >= 90:
            health_status = "healthy"
        elif health_score >= 70:
            health_status = "degraded"
        elif health_score >= 50:
            health_status = "unhealthy"
        else:
            health_status = "critical"
        
        return {
            'health_score': health_score,
            'health_status': health_status,
            'recent_errors': {
                'total': total_errors,
                'critical': critical_errors,
                'error': error_errors,
                'warning': recent_errors.filter(severity='warning').count(),
                'by_layer': dict(recent_errors.values_list('layer').annotate(count=models.Count('id')))
            },
            'circuit_breakers': circuit_breaker_statuses,
            'timestamp': timezone.now().isoformat()
        }


# Global error recovery engine instance
error_recovery_engine = ErrorRecoveryEngine()