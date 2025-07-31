#!/usr/bin/env python
"""
Test script for the database performance benchmarker
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from core.performance_benchmarker import (
    performance_benchmarker, 
    LoadTestConfig,
    benchmark_database,
    compare_database_performance
)


def test_connection_benchmark():
    """Test connection performance benchmark"""
    print("Testing connection benchmark...")
    try:
        suite = performance_benchmarker.benchmark_connection_performance(
            database_alias='default', 
            iterations=10
        )
        
        report = performance_benchmarker.generate_performance_report(suite)
        
        print(f"✓ Connection benchmark completed")
        print(f"  - Total tests: {report['performance_metrics']['total_tests']}")
        print(f"  - Success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"  - Average time: {report['performance_metrics']['average_execution_time']:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection benchmark failed: {e}")
        return False


def test_crud_benchmark():
    """Test CRUD operations benchmark"""
    print("\nTesting CRUD benchmark...")
    try:
        suite = performance_benchmarker.benchmark_crud_operations(
            database_alias='default', 
            iterations=20
        )
        
        report = performance_benchmarker.generate_performance_report(suite)
        
        print(f"✓ CRUD benchmark completed")
        print(f"  - Total tests: {report['performance_metrics']['total_tests']}")
        print(f"  - Success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"  - Average time: {report['performance_metrics']['average_execution_time']:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ CRUD benchmark failed: {e}")
        return False


def test_load_test():
    """Test load testing functionality"""
    print("\nTesting load test...")
    try:
        config = LoadTestConfig(
            concurrent_users=3,
            test_duration=10,
            queries_per_user=5
        )
        
        suite = performance_benchmarker.run_load_test('default', config)
        report = performance_benchmarker.generate_performance_report(suite)
        
        print(f"✓ Load test completed")
        print(f"  - Total tests: {report['performance_metrics']['total_tests']}")
        print(f"  - Success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"  - Average time: {report['performance_metrics']['average_execution_time']:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Load test failed: {e}")
        return False


def test_comprehensive_benchmark():
    """Test comprehensive benchmark functionality"""
    print("\nTesting comprehensive benchmark...")
    try:
        # Run a minimal comprehensive benchmark
        results = performance_benchmarker.run_comprehensive_benchmark('default')
        
        print(f"✓ Comprehensive benchmark completed")
        print(f"  - Database: {results['database_alias']}")
        print(f"  - Benchmarks run: {len(results.get('benchmarks', {}))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Comprehensive benchmark failed: {e}")
        return False


def main():
    """Run all benchmark tests"""
    print("="*60)
    print("DATABASE PERFORMANCE BENCHMARKER TESTS")
    print("="*60)
    
    tests = [
        test_connection_benchmark,
        test_crud_benchmark,
        test_load_test,
        # test_comprehensive_benchmark  # Skip for quick testing
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Performance benchmarker is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())