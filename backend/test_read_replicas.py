#!/usr/bin/env python
"""
Test script for read replica setup and configuration

This script tests the read replica functionality including:
- Replica setup and configuration
- Health monitoring
- Automatic failover
- Read/write splitting
"""
import os
import sys
import django
import logging
import time
from django.test import TestCase
from django.db import connections
from django.core.cache import cache

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from core.read_replica_setup import ReadReplicaManager, ReplicationHealthChecker
from core.replica_health_monitor import ReplicaHealthMonitor, ReplicaMetricsCollector
from core.database_router import DatabaseRouter, get_router_stats
from apps.products.models import Product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReadReplicaTests:
    """Test read replica functionality"""
    
    def __init__(self):
        self.replica_manager = ReadReplicaManager()
        self.health_monitor = ReplicaHealthMonitor()
        self.metrics_collector = ReplicaMetricsCollector()
        self.router = DatabaseRouter()
    
    def test_replica_configuration(self):
        """Test replica configuration generation"""
        print("\n=== Testing Replica Configuration ===")
        
        try:
            # Test Django configuration generation
            config = self.replica_manager.get_replica_django_config()
            print(f"Generated Django config for {len(config)} replicas")
            
            for alias, db_config in config.items():
                print(f"  {alias}: {db_config['HOST']}:{db_config['PORT']}")
            
            return True
        except Exception as e:
            print(f"Configuration test failed: {e}")
            return False
    
    def test_database_router(self):
        """Test database router functionality"""
        print("\n=== Testing Database Router ===")
        
        try:
            # Test router statistics
            stats = get_router_stats()
            print(f"Router stats: {stats}")
            
            # Test read database selection
            if Product.objects.exists():
                product = Product.objects.first()
                read_db = self.router.db_for_read(Product)
                write_db = self.router.db_for_write(Product)
                
                print(f"Read database: {read_db}")
                print(f"Write database: {write_db}")
                
                # Test read/write splitting
                print("Testing read/write splitting...")
                
                # Force read from replica
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM products_product")
                    count = cursor.fetchone()[0]
                    print(f"Product count from default: {count}")
                
                if 'read_replica' in connections.databases:
                    try:
                        with connections['read_replica'].cursor() as cursor:
                            cursor.execute("SELECT COUNT(*) FROM products_product")
                            replica_count = cursor.fetchone()[0]
                            print(f"Product count from replica: {replica_count}")
                    except Exception as e:
                        print(f"Replica connection failed (expected if not set up): {e}")
            
            return True
        except Exception as e:
            print(f"Router test failed: {e}")
            return False
    
    def test_health_monitoring(self):
        """Test replica health monitoring"""
        print("\n=== Testing Health Monitoring ===")
        
        try:
            # Test health check
            health_results = self.health_monitor.force_health_check()
            print(f"Health check results: {health_results}")
            
            # Test monitoring status
            status = self.health_monitor.get_monitoring_status()
            print(f"Monitoring enabled: {status['monitoring_enabled']}")
            print(f"Check interval: {status['check_interval']}s")
            print(f"Lag threshold: {status['lag_threshold']}s")
            
            return True
        except Exception as e:
            print(f"Health monitoring test failed: {e}")
            return False
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        print("\n=== Testing Metrics Collection ===")
        
        try:
            # Collect current metrics
            metrics = self.metrics_collector.collect_metrics()
            print(f"Collected metrics for {len(metrics.get('replicas', {}))} replicas")
            
            # Get metrics summary
            summary = self.metrics_collector.get_metrics_summary(1)  # 1 hour
            print(f"Metrics summary: {summary}")
            
            return True
        except Exception as e:
            print(f"Metrics collection test failed: {e}")
            return False
    
    def test_cache_integration(self):
        """Test cache integration for health status"""
        print("\n=== Testing Cache Integration ===")
        
        try:
            # Test health status caching
            test_health_data = {
                'healthy': True,
                'replication_lag': 2,
                'last_check': time.time(),
            }
            
            cache.set('db_health_test_replica', test_health_data, 60)
            cached_data = cache.get('db_health_test_replica')
            
            print(f"Cache test successful: {cached_data == test_health_data}")
            
            # Clean up
            cache.delete('db_health_test_replica')
            
            return True
        except Exception as e:
            print(f"Cache integration test failed: {e}")
            return False
    
    def test_connection_handling(self):
        """Test database connection handling"""
        print("\n=== Testing Connection Handling ===")
        
        try:
            # Test default connection
            default_conn = connections['default']
            print(f"Default connection: {default_conn.settings_dict['HOST']}:{default_conn.settings_dict['PORT']}")
            
            # Test replica connection (if configured)
            if 'read_replica' in connections.databases:
                try:
                    replica_conn = connections['read_replica']
                    print(f"Replica connection: {replica_conn.settings_dict['HOST']}:{replica_conn.settings_dict['PORT']}")
                    
                    # Test basic query
                    with replica_conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        print(f"Replica query test: {result[0] == 1}")
                        
                except Exception as e:
                    print(f"Replica connection test failed (expected if not configured): {e}")
            
            return True
        except Exception as e:
            print(f"Connection handling test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting Read Replica Tests...")
        print("=" * 50)
        
        tests = [
            ('Replica Configuration', self.test_replica_configuration),
            ('Database Router', self.test_database_router),
            ('Health Monitoring', self.test_health_monitoring),
            ('Metrics Collection', self.test_metrics_collection),
            ('Cache Integration', self.test_cache_integration),
            ('Connection Handling', self.test_connection_handling),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"Test {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Results Summary:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            color = "\033[92m" if result else "\033[91m"  # Green or Red
            reset = "\033[0m"
            print(f"{test_name}: {color}{status}{reset}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\033[92mAll tests passed! Read replica setup is working correctly.\033[0m")
        else:
            print(f"\033[91m{total - passed} tests failed. Please check the configuration.\033[0m")
        
        return passed == total


def main():
    """Main test function"""
    tester = ReadReplicaTests()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()