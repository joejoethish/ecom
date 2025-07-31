#!/usr/bin/env python
"""
Test script for connection pooling and optimization functionality
"""
import os
import sys
import django
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from django.db import connections
from django.conf import settings
from core.connection_pool import get_pool_manager, initialize_connection_pools
from core.connection_monitor import get_connection_monitor, initialize_monitoring
from core.database_router import DatabaseRouter, get_router_stats


def test_basic_connection():
    """Test basic database connection"""
    print("Testing basic database connection...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✓ Basic connection test passed: {result}")
            return True
    except Exception as e:
        print(f"✗ Basic connection test failed: {e}")
        return False


def test_connection_pool_manager():
    """Test connection pool manager functionality"""
    print("\nTesting Connection Pool Manager...")
    
    try:
        # Initialize connection pools
        pool_manager = initialize_connection_pools()
        print("✓ Connection pools initialized")
        
        # Test getting connection from pool
        with pool_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✓ Pool connection test passed: {result}")
        
        # Get pool status
        status = pool_manager.get_pool_status()
        print(f"✓ Pool status retrieved: {len(status)} pools")
        
        for pool_name, pool_info in status.items():
            print(f"  Pool '{pool_name}': {pool_info['pool_size']} connections, "
                  f"{pool_info['total_requests']} requests")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection pool test failed: {e}")
        return False


def test_database_router():
    """Test database router functionality"""
    print("\nTesting Database Router...")
    
    try:
        router = DatabaseRouter()
        
        # Test router stats
        stats = get_router_stats()
        print(f"✓ Router stats retrieved")
        print(f"  Read databases: {stats['read_databases']}")
        print(f"  Write database: {stats['write_database']}")
        print(f"  Replica lag threshold: {stats['replica_lag_threshold']}s")
        
        # Test database health
        for db_alias, health in stats['database_health'].items():
            status_icon = '✓' if health.get('healthy', False) else '✗'
            print(f"  {db_alias}: {status_icon}")
            if 'error' in health:
                print(f"    Error: {health['error']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Database router test failed: {e}")
        return False


def test_connection_monitoring():
    """Test connection monitoring functionality"""
    print("\nTesting Connection Monitoring...")
    
    try:
        # Initialize monitoring
        monitor = initialize_monitoring(10)  # 10 second interval for testing
        print("✓ Connection monitoring initialized")
        
        # Wait for some metrics to be collected
        print("  Waiting for metrics collection...")
        time.sleep(12)  # Wait for at least one monitoring cycle
        
        # Get current metrics
        metrics = monitor.get_current_metrics()
        print(f"✓ Current metrics retrieved for {len(metrics)} databases")
        
        for db_alias, db_metrics in metrics.items():
            if db_metrics:
                print(f"  {db_alias}:")
                print(f"    Active connections: {db_metrics.get('active_connections', 0)}")
                print(f"    Queries/sec: {db_metrics.get('queries_per_second', 0):.2f}")
                print(f"    Avg query time: {db_metrics.get('average_query_time', 0):.3f}s")
        
        # Get health summary
        health = monitor.get_health_summary()
        print(f"✓ Health summary: {health['overall_status']}")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("✓ Monitoring stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection monitoring test failed: {e}")
        return False


def test_concurrent_connections():
    """Test concurrent database connections"""
    print("\nTesting Concurrent Connections...")
    
    def worker(worker_id):
        """Worker function for concurrent testing"""
        results = {'success': 0, 'failed': 0, 'total_time': 0}
        
        for i in range(10):  # 10 queries per worker
            try:
                start_time = time.time()
                
                # Use Django ORM connection
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT %s, %s", [worker_id, i])
                    result = cursor.fetchone()
                
                query_time = time.time() - start_time
                results['success'] += 1
                results['total_time'] += query_time
                
                time.sleep(0.1)  # Small delay between queries
                
            except Exception as e:
                results['failed'] += 1
                print(f"  Worker {worker_id} query {i} failed: {e}")
        
        return results
    
    try:
        # Test with multiple concurrent workers
        num_workers = 5
        print(f"  Starting {num_workers} concurrent workers...")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker, i) for i in range(num_workers)]
            
            total_success = 0
            total_failed = 0
            total_time = 0
            
            for future in as_completed(futures):
                result = future.result()
                total_success += result['success']
                total_failed += result['failed']
                total_time += result['total_time']
        
        test_duration = time.time() - start_time
        
        print(f"✓ Concurrent test completed in {test_duration:.2f}s")
        print(f"  Total queries: {total_success + total_failed}")
        print(f"  Successful: {total_success}")
        print(f"  Failed: {total_failed}")
        
        if total_success > 0:
            avg_query_time = total_time / total_success
            qps = total_success / test_duration
            print(f"  Average query time: {avg_query_time:.3f}s")
            print(f"  Queries per second: {qps:.2f}")
        
        return total_failed == 0
        
    except Exception as e:
        print(f"✗ Concurrent connection test failed: {e}")
        return False


def test_connection_recovery():
    """Test connection recovery functionality"""
    print("\nTesting Connection Recovery...")
    
    try:
        # Get connection monitor
        monitor = get_connection_monitor()
        
        # Simulate connection failure by closing connection
        connection = connections['default']
        connection.close()
        print("  Simulated connection failure")
        
        # Try to use connection - should trigger recovery
        time.sleep(1)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print(f"✓ Connection recovery successful: {result}")
        return True
        
    except Exception as e:
        print(f"✗ Connection recovery test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Connection Pooling and Optimization Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Connection Pool Manager", test_connection_pool_manager),
        ("Database Router", test_database_router),
        ("Connection Monitoring", test_connection_monitoring),
        ("Concurrent Connections", test_concurrent_connections),
        ("Connection Recovery", test_connection_recovery),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {test_name}")
        print(f"{'-' * 40}")
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())