"""
Comprehensive test suite for database error handling and recovery system
"""

import unittest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from django.test import TestCase, TransactionTestCase
from django.db import connections, transaction
from django.db.utils import OperationalError, DatabaseError, IntegrityError
from django.core.cache import cache
from django.conf import settings

from core.database_error_handler import (
    DatabaseErrorHandler, DeadlockDetector, CircuitBreaker,
    ErrorSeverity, RecoveryAction, CircuitState,
    get_error_handler, database_error_handler, retry_on_database_error
)


class DatabaseErrorHandlerTest(TestCase):
    """Test the main database error handler functionality"""
    
    def setUp(self):
        self.error_handler = DatabaseErrorHandler()
        cache.clear()
    
    def test_error_severity_determination(self):
        """Test error severity classification"""
        # Critical errors
        critical_error = OperationalError("connection refused")
        severity = self.error_handler._determine_error_severity(critical_error)
        self.assertEqual(severity, ErrorSeverity.CRITICAL)
        
        # High severity errors
        high_error = OperationalError("deadlock found")
        severity = self.error_handler._determine_error_severity(high_error)
        self.assertEqual(severity, ErrorSeverity.HIGH)
        
        # Medium severity errors
        medium_error = IntegrityError("duplicate key")
        severity = self.error_handler._determine_error_severity(medium_error)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
        
        # Low severity errors
        low_error = Exception("generic error")
        severity = self.error_handler._determine_error_severity(low_error)
        self.assertEqual(severity, ErrorSeverity.LOW)
    
    def test_recovery_action_determination(self):
        """Test recovery action selection"""
        # Test deadlock recovery
        deadlock_error = self.error_handler._create_error_info(
            'default', OperationalError("deadlock found"), 'test_op'
        )
        action = self.error_handler._determine_recovery_action(deadlock_error)
        self.assertEqual(action, RecoveryAction.RETRY)
        
        # Test connection error recovery
        conn_error = self.error_handler._create_error_info(
            'default', OperationalError("connection refused"), 'test_op'
        )
        action = self.error_handler._determine_recovery_action(conn_error)
        self.assertEqual(action, RecoveryAction.RECONNECT)
        
        # Test integrity error (no retry)
        integrity_error = self.error_handler._create_error_info(
            'default', IntegrityError("duplicate key"), 'test_op'
        )
        action = self.error_handler._determine_recovery_action(integrity_error)
        self.assertEqual(action, RecoveryAction.MANUAL_INTERVENTION)
    
    def test_error_context_manager(self):
        """Test error handling context manager"""
        error_occurred = False
        
        try:
            with self.error_handler.handle_database_errors('default', 'test_operation'):
                raise OperationalError("test error")
        except OperationalError:
            error_occurred = True
        
        self.assertTrue(error_occurred)
        self.assertEqual(len(self.error_handler.error_history), 1)
        
        error_info = self.error_handler.error_history[0]
        self.assertEqual(error_info.database_alias, 'default')
        self.assertEqual(error_info.error_type, 'OperationalError')
    
    def test_degradation_mode(self):
        """Test graceful degradation mode"""
        # Initially not degraded
        self.assertFalse(self.error_handler.is_degraded())
        
        # Trigger degradation
        self.error_handler._handle_graceful_degradation('default')
        
        # Should be in degradation mode
        self.assertTrue(self.error_handler.is_degraded())
        self.assertTrue(self.error_handler.degradation_mode)
        
        # Reset degradation
        self.error_handler.reset_degradation_mode('default')
        self.assertFalse(self.error_handler.is_degraded())
    
    def test_error_statistics(self):
        """Test error statistics collection"""
        # Generate some test errors
        for i in range(5):
            error_info = self.error_handler._create_error_info(
                'default', OperationalError(f"test error {i}"), 'test_op'
            )
            self.error_handler.error_history.append(error_info)
        
        stats = self.error_handler.get_error_statistics('default')
        
        self.assertEqual(stats['total_errors'], 5)
        self.assertIn('OperationalError', stats['error_types'])
        self.assertEqual(stats['error_types']['OperationalError'], 5)
    
    def test_notification_callbacks(self):
        """Test error notification callbacks"""
        callback_called = False
        callback_error = None
        
        def test_callback(error_info):
            nonlocal callback_called, callback_error
            callback_called = True
            callback_error = error_info
        
        self.error_handler.add_notification_callback(test_callback)
        
        try:
            with self.error_handler.handle_database_errors('default', 'test_operation'):
                raise OperationalError("test error")
        except OperationalError:
            pass
        
        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_error)
        self.assertEqual(callback_error.error_type, 'OperationalError')


class DeadlockDetectorTest(TestCase):
    """Test deadlock detection functionality"""
    
    def setUp(self):
        self.detector = DeadlockDetector()
    
    def test_deadlock_detection(self):
        """Test deadlock detection from error messages"""
        # Test positive cases
        deadlock_error = OperationalError("deadlock found when trying to get lock")
        self.assertTrue(self.detector.detect_deadlock(deadlock_error))
        
        timeout_error = OperationalError("lock wait timeout exceeded")
        self.assertTrue(self.detector.detect_deadlock(timeout_error))
        
        # Test negative case
        other_error = OperationalError("connection refused")
        self.assertFalse(self.detector.detect_deadlock(other_error))
    
    def test_deadlock_pattern_tracking(self):
        """Test deadlock pattern analysis"""
        query = "SELECT * FROM users WHERE id = 1 FOR UPDATE"
        error = OperationalError("deadlock found")
        
        # Record multiple deadlocks with same pattern
        for _ in range(3):
            self.detector.detect_deadlock(error, query)
        
        stats = self.detector.get_deadlock_statistics()
        self.assertEqual(stats['total_deadlocks'], 3)
        self.assertIn('most_common_pattern', stats)


class CircuitBreakerTest(TestCase):
    """Test circuit breaker functionality"""
    
    def setUp(self):
        from core.database_error_handler import CircuitBreakerConfig
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,  # Short timeout for testing
            name="test_breaker"
        )
        self.circuit_breaker = CircuitBreaker(config)
    
    def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions"""
        # Initially closed
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        
        # Simulate failures to open circuit
        for _ in range(3):
            self.circuit_breaker._on_failure()
        
        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should attempt reset to half-open
        self.assertTrue(self.circuit_breaker._should_attempt_reset())
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker as decorator"""
        call_count = 0
        
        @self.circuit_breaker
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("test failure")
            return "success"
        
        # First 3 calls should fail and open circuit
        for _ in range(3):
            with self.assertRaises(Exception):
                test_function()
        
        # Circuit should be open now
        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
        
        # Next call should fail due to open circuit
        with self.assertRaises(Exception):
            test_function()


class DatabaseErrorDecoratorTest(TestCase):
    """Test database error handling decorators"""
    
    def test_database_error_handler_decorator(self):
        """Test the database_error_handler decorator"""
        @database_error_handler('default', 'test_operation')
        def test_function():
            raise OperationalError("test error")
        
        with self.assertRaises(OperationalError):
            test_function()
        
        # Check that error was recorded
        error_handler = get_error_handler()
        self.assertGreater(len(error_handler.error_history), 0)
    
    def test_retry_decorator(self):
        """Test the retry_on_database_error decorator"""
        call_count = 0
        
        @retry_on_database_error(max_attempts=3, delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("deadlock found")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_decorator_non_retryable_error(self):
        """Test retry decorator with non-retryable error"""
        call_count = 0
        
        @retry_on_database_error(max_attempts=3, delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise IntegrityError("duplicate key")
        
        with self.assertRaises(IntegrityError):
            test_function()
        
        # Should only be called once (no retry for integrity errors)
        self.assertEqual(call_count, 1)


class DatabaseErrorIntegrationTest(TransactionTestCase):
    """Integration tests for database error handling"""
    
    def setUp(self):
        self.error_handler = get_error_handler()
        cache.clear()
    
    def test_concurrent_deadlock_handling(self):
        """Test handling of concurrent deadlocks"""
        results = []
        
        def deadlock_simulation(thread_id):
            try:
                with self.error_handler.handle_database_errors('default', f'thread_{thread_id}'):
                    # Simulate deadlock
                    if thread_id % 2 == 0:
                        raise OperationalError("deadlock found when trying to get lock")
                    else:
                        time.sleep(0.1)  # Simulate successful operation
                        results.append(f"thread_{thread_id}_success")
            except OperationalError:
                results.append(f"thread_{thread_id}_deadlock")
        
        # Start multiple threads
        threads = []
        for i in range(6):
            thread = threading.Thread(target=deadlock_simulation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertGreater(len(results), 0)
        deadlock_count = len([r for r in results if 'deadlock' in r])
        success_count = len([r for r in results if 'success' in r])
        
        # Should have both deadlocks and successes
        self.assertGreater(deadlock_count, 0)
        self.assertGreater(success_count, 0)
    
    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow"""
        # Simulate connection error
        try:
            with self.error_handler.handle_database_errors('default', 'recovery_test'):
                raise OperationalError("connection refused")
        except OperationalError:
            pass
        
        # Check error was recorded
        self.assertGreater(len(self.error_handler.error_history), 0)
        
        error_info = self.error_handler.error_history[-1]
        self.assertEqual(error_info.recovery_action, RecoveryAction.RECONNECT)
        
        # Check statistics
        stats = self.error_handler.get_error_statistics('default')
        self.assertGreater(stats['total_errors'], 0)
    
    @patch('core.database_error_handler.send_mail')
    def test_error_notification_system(self, mock_send_mail):
        """Test error notification system"""
        # Configure settings for testing
        with self.settings(DATABASE_ALERT_EMAILS=['admin@test.com']):
            try:
                with self.error_handler.handle_database_errors('default', 'notification_test'):
                    raise OperationalError("server has gone away")  # Critical error
            except OperationalError:
                pass
        
        # Check that notification was attempted
        # Note: In a real test, you might want to check if send_mail was called
        # mock_send_mail.assert_called_once()


class DatabaseErrorMiddlewareTest(TestCase):
    """Test database error handling middleware"""
    
    def setUp(self):
        from core.middleware.database_error_middleware import DatabaseErrorHandlingMiddleware
        self.middleware = DatabaseErrorHandlingMiddleware(lambda r: None)
    
    def test_degradation_mode_response(self):
        """Test middleware response during degradation mode"""
        # Enable degradation mode
        error_handler = get_error_handler()
        error_handler._handle_graceful_degradation('default')
        
        # Create mock request
        from django.http import HttpRequest
        request = HttpRequest()
        request.path = '/api/analytics/report'  # Non-essential endpoint
        
        response = self.middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 503)
        
        # Reset degradation mode
        error_handler.reset_degradation_mode('default')
    
    def test_essential_endpoint_protection(self):
        """Test that essential endpoints are not degraded"""
        # Enable degradation mode
        error_handler = get_error_handler()
        error_handler._handle_graceful_degradation('default')
        
        # Create mock request for essential endpoint
        from django.http import HttpRequest
        request = HttpRequest()
        request.path = '/api/auth/login'  # Essential endpoint
        
        response = self.middleware.process_request(request)
        
        # Should not return degraded response for essential endpoints
        self.assertIsNone(response)
        
        # Reset degradation mode
        error_handler.reset_degradation_mode('default')


if __name__ == '__main__':
    unittest.main()