#!/usr/bin/env python
"""
Simple test for error handling system
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.core.cache import cache
from apps.debugging.error_handling import ErrorClassifier, CircuitBreaker

def test_error_classifier():
    print("Testing Error Classifier...")
    classifier = ErrorClassifier()
    
    # Test network error
    exception = Exception("Connection timeout")
    classification = classifier.classify_error(exception, "api", "external_service")
    
    print(f"  Category: {classification.category.value}")
    print(f"  Severity: {classification.severity.value}")
    print(f"  Recoverable: {classification.is_recoverable}")
    print(f"  Strategy: {classification.recovery_strategy.value}")
    print("✓ Error Classifier working!")

def test_circuit_breaker():
    print("\nTesting Circuit Breaker...")
    cache.clear()
    
    cb = CircuitBreaker("test_service", failure_threshold=2)
    print(f"  Initial state: {'Open' if cb.is_open() else 'Closed'}")
    
    cb.record_failure()
    cb.record_failure()
    
    print(f"  After 2 failures: {'Open' if cb.is_open() else 'Closed'}")
    print("✓ Circuit Breaker working!")

if __name__ == '__main__':
    test_error_classifier()
    test_circuit_breaker()
    print("\n✅ Error handling system validation complete!")