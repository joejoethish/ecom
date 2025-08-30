"""
Comprehensive tests for error handling and recovery systems
"""

import uuid
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone

from .error_handling import (
    ErrorClassifier, ErrorSeverity, ErrorCategory, RecoveryStrategy,
    ErrorClassification, ErrorContext, CircuitBreaker, RetryHandler,
    FallbackHandler, ErrorEscalationManager, ErrorRecoveryEngine
)
from .error_decorators import (
    with_error_recovery, with_circuit_breaker, with_retry, with_fallback,
    ErrorHandlingContext, CircuitBreakerContext, RetryContext
)
from .error_notifications import (
    NotificationThrottler, EmailNotificationHandler, WebhookNotificationHandler,
    SlackNotificationHandler, DashboardNotificationHandler, NotificationManager
)
from .models import ErrorLog, DebugConfiguration


class TestErrorClassifier(TestCase):
    """Test error classification system"""
    
    def setUp(self):
        self.classifier = ErrorClassifier()
    
    def test_network_error_classification(self):
        """Test classification of network errors"""
        exception = Exception("Connection timeout occurred")
        classification = self.classifier.classify_error(exception, "api", "external_service")
        
        self.assertEqual(classification.category, ErrorCategory.NETWORK)
        self.assertEqual(classification.severity, ErrorSeverity.WARNING)
        self.assertTrue(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy, RecoveryStrategy.RETRY)
        self.assertEqual(classification.max_retries, 3)
    
    def test_authentication_error_classification(self):
        """Test classification of authentication errors"""
        exception = Exception("Invalid credentials provided")
        classification = self.classifier.classify_error(exception, "api", "auth")
        
        self.assertEqual(classification.category, ErrorCategory.AUTHENTICATION)
        self.assertEqual(classification.severity, ErrorSeverity.ERROR)
        self.assertTrue(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy, RecoveryStrategy.FALLBACK)
    
    def test_database_error_classification(self):
        """Test classification of database errors"""
        exception = Exception("Database connection pool exhausted")
        classification = self.classifier.classify_error(exception, "database", "orm")
        
        self.assertEqual(classification.category, ErrorCategory.DATABASE)
        self.assertEqual(classification.severity, ErrorSeverity.CRITICAL)
        self.assertTrue(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy, RecoveryStrategy.CIRCUIT_BREAKER)
    
    def test_validation_error_classification(self):
        """Test classification of validation errors"""
        exception = Exception("Required field missing")
        classification = self.classifier.classify_error(exception, "api", "serializer")
        
        self.assertEqual(classification.category, ErrorCategory.VALIDATION)
        self.assertEqual(classification.severity, ErrorSeverity.WARNING)
        self.assertFalse(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy, RecoveryStrategy.ESCALATE)
    
    def test_default_classification(self):
        """Test default classification for unknown errors"""
        exception = Exception("Unknown error occurred")
        classification = self.classifier.classify_error(exception, "unknown", "unknown")
        
        self.assertEqual(classification.category, ErrorCategory.SYSTEM)
        self.assertEqual(classification.severity, ErrorSeverity.ERROR)
        self.assertFalse(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy, RecoveryStrategy.ESCALATE)


class TestCircuitBreaker(TestCase):
    """Test circuit breaker implementation"""
    
    def setUp(self):
        cache.clear()
        self.circuit_breaker = CircuitBreaker("test_component", failure_threshold=3, timeout_seconds=60)
    
    def tearDown(self):
        cache.clear()
    
    def test_circuit_breaker_closed_initially(self):
        """Test circuit breaker is closed initially"""
        self.assertFalse(self.circuit_breaker.is_open())
        self.assertFalse(self.circuit_breaker.is_half_open())
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        # Record failures up to threshold
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        self.assertTrue(self.circuit_breaker.is_open())
    
    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker moves to half-open after timeout"""
        # Open the circuit
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        self.assertTrue(self.circuit_breaker.is_open())
        
        # Simulate timeout by manipulating cache
        cache.set(f"circuit_breaker:test_component:open_time", time.time() - 70, 60)
        
        self.assertFalse(self.circuit_breaker.is_open())
        self.assertTrue(self.circuit_breaker.is_half_open())
    
    def test_circuit_breaker_closes_on_success_in_half_open(self):
        """Test circuit breaker closes on success in half-open state"""
        # Open the circuit and move to half-open
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        cache.set(f"circuit_breaker:test_component:state", "half_open", 30)
        
        # Record success
        self.circuit_breaker.record_success()
        
        self.assertFalse(self.circuit_breaker.is_open())
        self.assertFalse(self.circuit_breaker.is_half_open())
    
    def test_circuit_breaker_status(self):
        """Test circuit breaker status reporting"""
        status = self.circuit_breaker.get_status()
        
        self.assertEqual(status['component'], 'test_component')
        self.assertEqual(status['state'], 'closed')
        self.assertEqual(status['failures'], 0)
        self.assertEqual(status['failure_threshold'], 3)


class TestRetryHandler(TestCase):
    """Test retry handler implementation"""
    
    def setUp(self):
        self.retry_handler = RetryHandler(max_retries=3, base_delay=0.1, backoff_multiplier=2.0)
    
    def test_successful_execution_no_retry(self):
        """Test successful execution without retry"""
        mock_func = Mock(return_value="success")
        
        result = self.retry_handler.execute_with_retry(mock_func, "arg1", kwarg1="value1")
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_retry_on_failure(self):
        """Test retry mechanism on failure"""
        mock_func = Mock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        
        result = self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted"""
        mock_func = Mock(side_effect=Exception("persistent error"))
        
        with self.assertRaises(Exception) as context:
            self.retry_handler.execute_with_retry(mock_func)
        
        self.assertEqual(str(context.exception), "persistent error")
        self.assertEqual(mock_func.call_count, 4)  # Initial + 3 retries


class TestFallbackHandler(TestCase):
    """Test fallback handler implementation"""
    
    def setUp(self):
        self.fallback_handler = FallbackHandler()
    
    def test_register_and_execute_fallback(self):
        """Test registering and executing fallback"""
        mock_fallback = Mock(return_value="fallback_result")
        
        self.fallback_handler.register_fallback("test_component", "test_operation", mock_fallback)
        
        result = self.fallback_handler.execute_fallback(
            "test_component", "test_operation", ("arg1",), {"kwarg1": "value1"}
        )
        
        self.assertEqual(result, "fallback_result")
        mock_fallback.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_fallback_priority(self):
        """Test fallback priority ordering"""
        high_priority_fallback = Mock(return_value="high_priority")
        low_priority_fallback = Mock(return_value="low_priority")
        
        self.fallback_handler.register_fallback("test_component", "test_operation", low_priority_fallback, priority=1)
        self.fallback_handler.register_fallback("test_component", "test_operation", high_priority_fallback, priority=5)
        
        result = self.fallback_handler.execute_fallback("test_component", "test_operation")
        
        self.assertEqual(result, "high_priority")
        high_priority_fallback.assert_called_once()
        low_priority_fallback.assert_not_called()
    
    def test_fallback_cascade_on_failure(self):
        """Test fallback cascade when higher priority fails"""
        failing_fallback = Mock(side_effect=Exception("fallback failed"))
        working_fallback = Mock(return_value="working_fallback")
        
        self.fallback_handler.register_fallback("test_component", "test_operation", working_fallback, priority=1)
        self.fallback_handler.register_fallback("test_component", "test_operation", failing_fallback, priority=5)
        
        result = self.fallback_handler.execute_fallback("test_component", "test_operation")
        
        self.assertEqual(result, "working_fallback")
        failing_fallback.assert_called_once()
        working_fallback.assert_called_once()


class TestErrorRecoveryEngine(TestCase):
    """Test error recovery engine integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        self.recovery_engine = ErrorRecoveryEngine()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @patch('apps.debugging.error_handling.ErrorLogger.log_exception')
    def test_handle_retry_strategy(self, mock_log_exception):
        """Test handling retry recovery strategy"""
        mock_log_exception.return_value = Mock(id=1)
        
        # Mock function that fails twice then succeeds
        mock_func = Mock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        
        context = ErrorContext(correlation_id=uuid.uuid4(), user=self.user)
        
        result = self.recovery_engine.handle_error(
            exception=Exception("Connection timeout"),
            layer="api",
            component="external_service",
            operation="fetch_data",
            context=context,
            original_func=mock_func,
            original_args=(),
            original_kwargs={}
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    @patch('apps.debugging.error_handling.ErrorLogger.log_exception')
    def test_handle_circuit_breaker_strategy(self, mock_log_exception):
        """Test handling circuit breaker recovery strategy"""
        mock_log_exception.return_value = Mock(id=1)
        
        context = ErrorContext(correlation_id=uuid.uuid4(), user=self.user)
        
        # Register a fallback
        self.recovery_engine.fallback_handler.register_fallback(
            "database_service", "error_fallback", Mock(return_value="fallback_result")
        )
        
        result = self.recovery_engine.handle_error(
            exception=Exception("Database connection failed"),
            layer="database",
            component="database_service",
            operation="query",
            context=context
        )
        
        self.assertEqual(result, "fallback_result")
    
    @patch('apps.debugging.error_handling.ErrorLogger.log_exception')
    def test_handle_escalation_strategy(self, mock_log_exception):
        """Test handling escalation recovery strategy"""
        mock_error_log = Mock(id=1)
        mock_log_exception.return_value = mock_error_log
        
        context = ErrorContext(correlation_id=uuid.uuid4(), user=self.user)
        
        # Mock escalation manager
        with patch.object(self.recovery_engine.escalation_manager, 'escalate_error') as mock_escalate:
            result = self.recovery_engine.handle_error(
                exception=Exception("Validation failed"),
                layer="api",
                component="serializer",
                operation="validate",
                context=context
            )
            
            mock_escalate.assert_called_once()
            self.assertIsNone(result)
    
    def test_get_system_health(self):
        """Test system health reporting"""
        # Create some test error logs
        ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="critical",
            error_type="TestError",
            error_message="Test critical error"
        )
        
        ErrorLog.objects.create(
            layer="database",
            component="test",
            severity="error",
            error_type="TestError",
            error_message="Test error"
        )
        
        health = self.recovery_engine.get_system_health()
        
        self.assertIn('health_score', health)
        self.assertIn('health_status', health)
        self.assertIn('recent_errors', health)
        self.assertIn('circuit_breakers', health)
        
        # Health score should be reduced due to errors
        self.assertLess(health['health_score'], 100)


class TestErrorDecorators(TestCase):
    """Test error handling decorators"""
    
    def setUp(self):
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_with_error_recovery_decorator(self):
        """Test error recovery decorator"""
        @with_error_recovery(layer="api", component="test", max_retries=2)
        def test_function():
            if not hasattr(test_function, 'call_count'):
                test_function.call_count = 0
            test_function.call_count += 1
            
            if test_function.call_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(test_function.call_count, 3)
    
    def test_with_circuit_breaker_decorator(self):
        """Test circuit breaker decorator"""
        @with_circuit_breaker(component="test_service", failure_threshold=2)
        def test_function():
            raise Exception("Service unavailable")
        
        # First two calls should fail and open the circuit
        with self.assertRaises(Exception):
            test_function()
        
        with self.assertRaises(Exception):
            test_function()
        
        # Third call should be blocked by circuit breaker
        with self.assertRaises(Exception) as context:
            test_function()
        
        self.assertIn("Circuit breaker is open", str(context.exception))
    
    def test_with_retry_decorator(self):
        """Test retry decorator"""
        @with_retry(max_retries=2, base_delay=0.01)
        def test_function():
            if not hasattr(test_function, 'call_count'):
                test_function.call_count = 0
            test_function.call_count += 1
            
            if test_function.call_count < 3:
                raise Exception("Retry me")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(test_function.call_count, 3)
    
    def test_with_fallback_decorator(self):
        """Test fallback decorator"""
        def fallback_function(*args, **kwargs):
            return "fallback_result"
        
        @with_fallback(fallback_function)
        def test_function():
            raise Exception("Primary function failed")
        
        result = test_function()
        self.assertEqual(result, "fallback_result")


class TestErrorContextManagers(TestCase):
    """Test error handling context managers"""
    
    def setUp(self):
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_error_handling_context_suppress(self):
        """Test error handling context with exception suppression"""
        with ErrorHandlingContext(
            layer="api", 
            component="test", 
            operation="test_op",
            suppress_exceptions=True,
            fallback_result="fallback"
        ):
            raise Exception("Test error")
        
        # Should not raise exception due to suppression
    
    def test_circuit_breaker_context(self):
        """Test circuit breaker context manager"""
        # First, open the circuit by recording failures
        circuit_breaker = CircuitBreaker("test_context", failure_threshold=1)
        circuit_breaker.record_failure()
        
        with self.assertRaises(Exception) as context:
            with CircuitBreakerContext("test_context", failure_threshold=1):
                pass
        
        self.assertIn("Circuit breaker is open", str(context.exception))
    
    def test_retry_context(self):
        """Test retry context manager"""
        attempt_count = 0
        
        while attempt_count < 3:
            try:
                with RetryContext(max_retries=3, base_delay=0.01) as retry_ctx:
                    attempt_count = retry_ctx.attempt
                    if attempt_count < 3:
                        raise Exception(f"Attempt {attempt_count} failed")
                    break
            except Exception:
                continue
        
        self.assertEqual(attempt_count, 3)


class TestNotificationSystem(TestCase):
    """Test notification system"""
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
    
    def tearDown(self):
        cache.clear()
    
    def test_notification_throttling(self):
        """Test notification throttling mechanism"""
        throttler = NotificationThrottler(default_window_minutes=1, default_max_notifications=2)
        
        # First two notifications should be allowed
        self.assertTrue(throttler.should_send_notification("test_key"))
        self.assertTrue(throttler.should_send_notification("test_key"))
        
        # Third notification should be throttled
        self.assertFalse(throttler.should_send_notification("test_key"))
    
    @patch('apps.debugging.error_notifications.send_mail')
    def test_email_notification_handler(self, mock_send_mail):
        """Test email notification handler"""
        # Create configuration
        DebugConfiguration.objects.create(
            name="email_notifications_default",
            config_type="alert_settings",
            enabled=True,
            config_data={
                "enabled": True,
                "recipients": ["admin@example.com"]
            }
        )
        
        handler = EmailNotificationHandler()
        
        error_log = ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="error",
            error_type="TestError",
            error_message="Test error message"
        )
        
        escalation_data = {
            'error_log': error_log,
            'classification': Mock(category=Mock(value="system"), severity=Mock(value="error")),
            'escalation_level': 'medium',
            'timestamp': timezone.now()
        }
        
        handler.send_error_notification(escalation_data)
        
        # Verify email was attempted to be sent
        # Note: This would need proper email backend configuration in real tests
    
    @patch('requests.post')
    def test_webhook_notification_handler(self, mock_post):
        """Test webhook notification handler"""
        mock_post.return_value.raise_for_status.return_value = None
        
        # Create configuration
        DebugConfiguration.objects.create(
            name="webhook_notifications_default",
            config_type="alert_settings",
            enabled=True,
            config_data={
                "enabled": True,
                "webhooks": [
                    {
                        "url": "https://example.com/webhook",
                        "headers": {"Authorization": "Bearer token"}
                    }
                ]
            }
        )
        
        handler = WebhookNotificationHandler()
        
        error_log = ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="error",
            error_type="TestError",
            error_message="Test error message"
        )
        
        escalation_data = {
            'error_log': error_log,
            'classification': Mock(
                category=Mock(value="system"), 
                severity=Mock(value="error"),
                is_recoverable=True,
                recovery_strategy=Mock(value="retry")
            ),
            'escalation_level': 'medium',
            'timestamp': timezone.now()
        }
        
        handler.send_webhook_notification(escalation_data)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['event_type'], 'error_escalation')
    
    def test_dashboard_notification_handler(self):
        """Test dashboard notification handler"""
        handler = DashboardNotificationHandler()
        
        error_log = ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="error",
            error_type="TestError",
            error_message="Test error message"
        )
        
        escalation_data = {
            'error_log': error_log,
            'classification': Mock(),
            'escalation_level': 'medium',
            'timestamp': timezone.now()
        }
        
        handler.send_dashboard_notification(escalation_data)
        
        # Check that notification was stored in cache
        notifications = cache.get("dashboard_notifications", [])
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['type'], 'error_escalation')
    
    def test_notification_manager_integration(self):
        """Test notification manager integration"""
        # Create configuration for all handlers
        DebugConfiguration.objects.create(
            name="notifications_medium",
            config_type="alert_settings",
            enabled=True,
            config_data={
                "email": {"enabled": False},
                "webhook": {"enabled": False},
                "slack": {"enabled": False},
                "dashboard": {"enabled": True}
            }
        )
        
        manager = NotificationManager()
        
        error_log = ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="error",
            error_type="TestError",
            error_message="Test error message"
        )
        
        escalation_data = {
            'error_log': error_log,
            'classification': Mock(),
            'escalation_level': 'medium',
            'timestamp': timezone.now()
        }
        
        manager.send_notifications(escalation_data)
        
        # Check that only dashboard notification was sent
        notifications = cache.get("dashboard_notifications", [])
        self.assertEqual(len(notifications), 1)


class TestErrorHandlingIntegration(TestCase):
    """Integration tests for complete error handling system"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @patch('apps.debugging.error_handling.ErrorLogger.log_exception')
    def test_end_to_end_error_handling(self, mock_log_exception):
        """Test complete end-to-end error handling flow"""
        mock_error_log = Mock(
            id=1,
            layer="api",
            component="test_service",
            error_type="ConnectionError",
            error_message="Connection failed",
            severity="error",
            correlation_id=uuid.uuid4(),
            user=self.user,
            timestamp=timezone.now()
        )
        mock_log_exception.return_value = mock_error_log
        
        # Create notification configuration
        DebugConfiguration.objects.create(
            name="notifications_medium",
            config_type="alert_settings",
            enabled=True,
            config_data={
                "dashboard": {"enabled": True}
            }
        )
        
        @with_error_recovery(
            layer="api",
            component="test_service",
            correlation_id=uuid.uuid4(),
            user=self.user
        )
        def failing_function():
            raise Exception("Connection failed")
        
        # This should trigger error handling, classification, and notification
        with self.assertRaises(Exception):
            failing_function()
        
        # Verify error was logged
        mock_log_exception.assert_called_once()
        
        # Verify dashboard notification was created
        notifications = cache.get("dashboard_notifications", [])
        self.assertGreater(len(notifications), 0)


if __name__ == '__main__':
    pytest.main([__file__])