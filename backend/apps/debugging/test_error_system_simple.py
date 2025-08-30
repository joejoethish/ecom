"""
Simple test to verify error handling system functionality
"""

import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache

from .error_handling import ErrorClassifier, ErrorRecoveryEngine, ErrorContext
from .error_decorators import with_error_recovery, with_circuit_breaker
from .models import ErrorLog


class SimpleErrorHandlingTest(TestCase):
    """Simple tests for error handling system"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_error_classifier(self):
        """Test basic error classification"""
        classifier = ErrorClassifier()
        
        # Test network error
        exception = Exception("Connection timeout")
        classification = classifier.classify_error(exception, "api", "external_service")
        
        self.assertEqual(classification.category.value, "network")
        self.assertEqual(classification.severity.value, "warning")
        self.assertTrue(classification.is_recoverable)
        self.assertEqual(classification.recovery_strategy.value, "retry")
    
    def test_error_recovery_engine(self):
        """Test error recovery engine basic functionality"""
        recovery_engine = ErrorRecoveryEngine()
        
        context = ErrorContext(
            correlation_id=uuid.uuid4(),
            user=self.user
        )
        
        # Test handling a validation error (should escalate)
        exception = Exception("Required field missing")
        
        # This should create an error log and escalate
        result = recovery_engine.handle_error(
            exception=exception,
            layer="api",
            component="serializer",
            operation="validate",
            context=context
        )
        
        # Should return None for escalation strategy
        self.assertIsNone(result)
        
        # Should have created an error log
        error_logs = ErrorLog.objects.filter(error_message="Required field missing")
        self.assertEqual(error_logs.count(), 1)
    
    def test_error_decorator(self):
        """Test error handling decorator"""
        
        @with_error_recovery(layer="api", component="test")
        def test_function():
            raise Exception("Test error")
        
        # This should handle the error and create a log
        try:
            test_function()
        except Exception:
            pass  # Expected to still raise since it's an escalation case
        
        # Should have created an error log
        error_logs = ErrorLog.objects.filter(error_message="Test error")
        self.assertEqual(error_logs.count(), 1)
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator"""
        
        @with_circuit_breaker(component="test_service", failure_threshold=2)
        def failing_function():
            raise Exception("Service unavailable")
        
        # First call should fail
        with self.assertRaises(Exception):
            failing_function()
        
        # Second call should fail and open circuit
        with self.assertRaises(Exception):
            failing_function()
        
        # Third call should be blocked by circuit breaker
        with self.assertRaises(Exception) as context:
            failing_function()
        
        self.assertIn("Circuit breaker is open", str(context.exception))
    
    def test_system_health(self):
        """Test system health reporting"""
        recovery_engine = ErrorRecoveryEngine()
        
        # Create some test errors
        ErrorLog.objects.create(
            layer="api",
            component="test",
            severity="critical",
            error_type="TestError",
            error_message="Test critical error"
        )
        
        health = recovery_engine.get_system_health()
        
        self.assertIn('health_score', health)
        self.assertIn('health_status', health)
        self.assertIn('recent_errors', health)
        
        # Health score should be reduced due to critical error
        self.assertLess(health['health_score'], 100)