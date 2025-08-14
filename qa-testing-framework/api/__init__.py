"""
API Testing Module

Handles Django REST API endpoint testing using REST Assured and custom Python scripts.
Supports authentication testing, request/response validation, and performance testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import (
    ValidationResult, SchemaValidator, ResponseValidator,
    SecurityValidator, PerformanceValidator, APIValidator
)
from api.performance import (
    LoadTestConfig, PerformanceMetrics, LoadTestResults,
    LoadTester, PerformanceMonitor, APIPerformanceTester
)

__all__ = [
    # Client classes
    'APITestClient',
    'APIResponse',
    
    # Validation classes
    'ValidationResult',
    'SchemaValidator',
    'ResponseValidator',
    'SecurityValidator',
    'PerformanceValidator',
    'APIValidator',
    
    # Performance testing classes
    'LoadTestConfig',
    'PerformanceMetrics',
    'LoadTestResults',
    'LoadTester',
    'PerformanceMonitor',
    'APIPerformanceTester',
]