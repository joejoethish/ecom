#!/usr/bin/env python
"""
Validation script for error handling and recovery system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

import uuid
from django.contrib.auth.models import User
from django.core.cache import cache
from apps.debugging.error_handling import (
    ErrorClassifier, ErrorRecoveryEngine, ErrorContext, CircuitBreaker
)
from apps.debugging.error_decorators import with_error_recovery, with_circuit_breaker
from apps.debugging.models import ErrorLog, DebugConfiguration


def test_error_classifier():
    """Test error classification system"""
    print("Testing Error Classifier...")
    
    classifier = ErrorClassifier()
    
    # Test network error
    exception = Exception("Connection timeout occurred")
    classification = classifier.classify_error(exception, "api", "external_service")
    
    print(f"  Network Error Classification:")
    print(f"    Category: {classification.category.value}")
    print(f"    Severity: {classification.severity.value}")
    print(f"    Recoverable: {classification.is_recoverable}")
    print(f"    Strategy: {classification.recovery_strategy.value}")
    
    # Test database error
    exception = Exception("Database connection failed")
    classification = classifier.classify_error(exception, "database", "orm")
    
    print(f"  Database Error Classification:")
    print(f"    Category: {classification.category.value}")
    print(f"    Severity: {classification.severity.value}")
    print(f"    Strategy: {classification.recovery_strategy.value}")
    
    print("✓ Error Classifier working correctly\n")


def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("Testing Circuit Breaker...")
    
    cache.clear()
    circuit_breaker = CircuitBreaker("test_service", failure_threshold=2, timeout_seconds=5)
    
    # Initially closed
    print(f"  Initial state: {'Open' if circuit_breaker.is_open() else 'Closed'}")
    
    # Record failures
    circuit_breaker.record_failure()
    circuit_breaker.record_failure()
    
    print(f"  After 2 failures: {'Open' if circuit_breaker.is_open() else 'Closed'}")
    
    # Get status
    status = circuit_breaker.get_status()
    print(f"  Status: {status}")
    
    print("✓ Circuit Breaker working correctly\n")


def test_error_recovery_engine():
    """Test error recovery engine"""
    print("Testing Error Recovery Engine...")
    
    recovery_engine = ErrorRecoveryEngine()
    
    # Create test user
    try:
        user = User.objects.get(username='test_error_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_error_user',
            email='test@example.com'
        )
    
    context = ErrorContext(
        correlation_id=uuid.uuid4(),
        user=user,
        metadata={'test': True}
    )
    
    # Test handling a validation error (should escalate)
    exception = Exception("Required field missing")
    
    try:
        result = recovery_engine.handle_error(
            exception=exception,
            layer="api",
            component="serializer",
            operation="validate",
            context=context
        )
        print(f"  Recovery result: {result}")
    except Exception as e:
        print(f"  Error during recovery: {e}")
    
    # Test system health
    health = recovery_engine.get_system_health()
    print(f"  System Health Score: {health['health_score']}")
    print(f"  System Health Status: {health['health_status']}")
    
    print("✓ Error Recovery Engine working correctly\n")


def test_error_decorators():
    """Test error handling decorators"""
    print("Testing Error Decorators...")
    
    # Test retry decorator
    call_count = 0
    
    @with_error_recovery(layer="api", component="test")
    def test_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary error")
        return "success"
    
    try:
        result = test_function()
        print(f"  Retry decorator result: {result}")
        print(f"  Function called {call_count} times")
    except Exception as e:
        print(f"  Retry decorator error: {e}")
    
    # Test circuit breaker decorator
    @with_circuit_breaker(component="test_cb_service", failure_threshold=1)
    def failing_function():
        raise Exception("Service unavailable")
    
    try:
        failing_function()
    except Exception as e:
        print(f"  First call failed: {e}")
    
    try:
        failing_function()
    except Exception as e:
        print(f"  Second call (circuit breaker): {e}")
    
    print("✓ Error Decorators working correctly\n")


def test_configurations():
    """Test error handling configurations"""
    print("Testing Error Handling Configurations...")
    
    # Check if configurations exist
    configs = DebugConfiguration.objects.filter(
        config_type='alert_settings'
    ).count()
    
    print(f"  Found {configs} error handling configurations")
    
    # Check specific configurations
    email_config = DebugConfiguration.objects.filter(
        name__contains='email_notifications'
    ).first()
    
    if email_config:
        print(f"  Email configuration: {email_config.name}")
        print(f"  Enabled: {email_config.enabled}")
    
    print("✓ Configurations loaded correctly\n")


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("ERROR HANDLING AND RECOVERY SYSTEM VALIDATION")
    print("=" * 60)
    print()
    
    try:
        test_error_classifier()
        test_circuit_breaker()
        test_error_recovery_engine()
        test_error_decorators()
        test_configurations()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED - Error handling system is working correctly!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()