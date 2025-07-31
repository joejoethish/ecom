#!/usr/bin/env python
"""
Test script for the simple database performance benchmarker
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

from core.simple_performance_benchmarker import simple_benchmarker, run_basic_benchmark


def test_connection_benchmark():
    """Test connection performance benchmark"""
    print("Testing connection benchmark...")
    try:
        suite = simple_benchmarker.benchmark_connection_performance(
            database_alias='default', 
            iterations=5
        )
        
        report = simple_benchmarker.generate_performance_report(suite)
        
        print(f"✓ Connection benchmark completed")
        print(f"  - Total tests: {report['performance_metrics']['total_tests']}")
        print(f"  - Success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"  - Average time: {report['performance_metrics']['average_execution_time']:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection benchmark failed: {e}")
        return False


def test_simple_queries_benchmark():
    """Test simple queries benchmark"""
    print("\nTesting simple queries benchmark...")
    try:
        suite = simple_benchmarker.benchmark_simple_queries(
            database_alias='default', 
            iterations=9  # 3 queries * 3 iterations each
        )
        
        report = simple_benchmarker.generate_performance_report(suite)
        
        print(f"✓ Simple queries benchmark completed")
        print(f"  - Total tests: {report['performance_metrics']['total_tests']}")
        print(f"  - Success rate: {report['performance_metrics']['success_rate']:.1f}%")
        print(f"  - Average time: {report['performance_metrics']['average_execution_time']:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Simple queries benchmark failed: {e}")
        return False


def test_basic_benchmark():
    """Test basic benchmark functionality"""
    print("\nTesting basic benchmark...")
    try:
        results = run_basic_benchmark('default')
        
        print(f"✓ Basic benchmark completed")
        print(f"  - Database: {results['database_alias']}")
        print(f"  - Benchmarks run: {len(results.get('benchmarks', {}))}")
        
        # Show some details
        for bench_name, bench_data in results.get('benchmarks', {}).items():
            metrics = bench_data.get('performance_metrics', {})
            print(f"  - {bench_name}: {metrics.get('success_rate', 0):.1f}% success rate")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic benchmark failed: {e}")
        return False


def main():
    """Run all benchmark tests"""
    print("="*60)
    print("SIMPLE DATABASE PERFORMANCE BENCHMARKER TESTS")
    print("="*60)
    
    tests = [
        test_connection_benchmark,
        test_simple_queries_benchmark,
        test_basic_benchmark
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Simple performance benchmarker is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())