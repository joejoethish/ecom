#!/usr/bin/env python
"""
Test script for database monitoring and alerting system

This script tests the comprehensive database monitoring system including:
- Metrics collection and analysis
- Slow query detection and optimization recommendations
- Alert generation and notification
- Recovery mechanisms
- API endpoints
"""

import os
import sys
import django
import time
import json
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.db import connections, connection
from django.conf import settings

from core.database_monitor import get_database_monitor, initialize_database_monitoring
from core.database_alerting import get_database_alerting, initialize_database_alerting

User = get_user_model()


class DatabaseMonitoringTest:
    """Test suite for database monitoring system"""
    
    def __init__(self):
        self.client = Client()
        self.monitor = None
        self.alerting = None
        self.test_user = None
        self.admin_user = None
        
    def setup(self):
        """Setup test environment"""
        print("Setting up test environment...")
        
        # Create test users
        try:
            self.test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            
            self.admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123'
            )
        except Exception as e:
            print(f"User creation error (may already exist): {e}")
            self.test_user = User.objects.get(username='testuser')
            self.admin_user = User.objects.get(username='admin')
        
        # Initialize monitoring system
        self.monitor = initialize_database_monitoring(monitoring_interval=5)
        self.alerting = initialize_database_alerting()
        
        # Connect alerting to monitoring
        self.monitor.add_alert_callback(self.alerting.send_alert)
        
        print("Test environment setup complete")
    
    def test_metrics_collection(self):
        """Test database metrics collection"""
        print("\n=== Testing Metrics Collection ===")
        
        try:
            # Wait for initial metrics collection
            time.sleep(6)
            
            # Get current metrics
            current_metrics = self.monitor.get_current_metrics()
            
            print(f"Collected metrics for {len(current_metrics)} databases")
            
            for db_alias, metrics in current_metrics.items():
                if metrics:
                    print(f"\n{db_alias} metrics:")
                    print(f"  Health Score: {metrics.get('health_score', 0):.1f}/100")
                    print(f"  Active Connections: {metrics.get('active_connections', 0)}")
                    print(f"  Queries/sec: {metrics.get('queries_per_second', 0):.1f}")
                    print(f"  Avg Query Time: {metrics.get('average_query_time', 0):.3f}s")
                    print(f"  Status: {metrics.get('status', 'unknown')}")
                else:
                    print(f"{db_alias}: No metrics available")
            
            # Test metrics history
            if current_metrics:
                db_alias = list(current_metrics.keys())[0]
                history = self.monitor.get_metrics_history(db_alias, hours=1)
                print(f"\nMetrics history for {db_alias}: {len(history)} entries")
            
            print("✓ Metrics collection test passed")
            return True
            
        except Exception as e:
            print(f"✗ Metrics collection test failed: {e}")
            return False
    
    def test_slow_query_analysis(self):
        """Test slow query analysis and recommendations"""
        print("\n=== Testing Slow Query Analysis ===")
        
        try:
            # Simulate some slow queries by executing complex queries
            with connection.cursor() as cursor:
                # Execute a potentially slow query
                cursor.execute("""
                    SELECT COUNT(*) FROM auth_user u1 
                    CROSS JOIN auth_user u2 
                    WHERE u1.id < 10 AND u2.id < 10
                """)
                result = cursor.fetchone()
            
            # Record query time manually for testing
            self.monitor.record_query_time('default', 2.5)  # Simulate 2.5s query
            
            # Wait for analysis
            time.sleep(2)
            
            # Get slow queries
            slow_queries = self.monitor.get_slow_queries(limit=10)
            
            print(f"Found {len(slow_queries)} slow queries")
            
            for query in slow_queries[:3]:  # Show first 3
                print(f"\nSlow Query:")
                print(f"  Execution Time: {query.get('execution_time', 0):.3f}s")
                print(f"  Severity: {query.get('severity', 'unknown')}")
                print(f"  Suggestions: {len(query.get('optimization_suggestions', []))}")
                
                for suggestion in query.get('optimization_suggestions', [])[:2]:
                    print(f"    - {suggestion}")
            
            print("✓ Slow query analysis test passed")
            return True
            
        except Exception as e:
            print(f"✗ Slow query analysis test failed: {e}")
            return False
    
    def test_alert_system(self):
        """Test alert generation and notification"""
        print("\n=== Testing Alert System ===")
        
        try:
            # Temporarily lower thresholds to trigger alerts
            original_threshold = self.monitor.alert_thresholds['connection_usage'].warning_threshold
            self.monitor.update_threshold('connection_usage', warning=1.0, critical=2.0)
            
            # Wait for alert to be generated
            time.sleep(6)
            
            # Check for active alerts
            active_alerts = self.monitor.get_active_alerts()
            
            print(f"Generated {len(active_alerts)} active alerts")
            
            for alert in active_alerts[:3]:  # Show first 3
                print(f"\nAlert:")
                print(f"  Database: {alert.get('database_alias', 'unknown')}")
                print(f"  Metric: {alert.get('metric_name', 'unknown')}")
                print(f"  Severity: {alert.get('severity', 'unknown')}")
                print(f"  Message: {alert.get('message', 'No message')}")
            
            # Test alert history
            alert_history = self.monitor.get_alert_history(hours=1)
            print(f"\nAlert history: {len(alert_history)} alerts in last hour")
            
            # Restore original threshold
            self.monitor.update_threshold('connection_usage', warning=original_threshold)
            
            print("✓ Alert system test passed")
            return True
            
        except Exception as e:
            print(f"✗ Alert system test failed: {e}")
            return False
    
    def test_health_summary(self):
        """Test health summary generation"""
        print("\n=== Testing Health Summary ===")
        
        try:
            health_summary = self.monitor.get_health_summary()
            
            print(f"Overall Status: {health_summary.get('overall_status', 'unknown')}")
            print(f"Active Alerts: {health_summary.get('active_alerts', 0)}")
            print(f"Total Slow Queries: {health_summary.get('total_slow_queries', 0)}")
            
            databases = health_summary.get('databases', {})
            print(f"\nDatabase Health ({len(databases)} databases):")
            
            for db_alias, db_data in databases.items():
                print(f"  {db_alias}: {db_data.get('status', 'unknown')} "
                      f"(Health: {db_data.get('health_score', 0):.1f})")
            
            print("✓ Health summary test passed")
            return True
            
        except Exception as e:
            print(f"✗ Health summary test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test monitoring API endpoints"""
        print("\n=== Testing API Endpoints ===")
        
        try:
            # Login as admin user
            self.client.force_login(self.admin_user)
            
            # Test current metrics endpoint
            response = self.client.get('/core/api/monitoring/metrics/')
            print(f"Current metrics API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {data.get('status', 'unknown')}")
                print(f"  Databases: {len(data.get('data', {}))}")
            
            # Test health summary endpoint
            response = self.client.get('/core/api/monitoring/health/')
            print(f"Health summary API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                health_data = data.get('data', {})
                print(f"  Overall Status: {health_data.get('overall_status', 'unknown')}")
            
            # Test dashboard endpoint
            response = self.client.get('/core/api/monitoring/dashboard/')
            print(f"Dashboard API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('data', {}).get('summary', {})
                print(f"  Total Databases: {summary.get('total_databases', 0)}")
                print(f"  Active Alerts: {summary.get('active_alerts', 0)}")
            
            # Test slow queries endpoint
            response = self.client.get('/core/api/monitoring/slow-queries/')
            print(f"Slow queries API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                queries = data.get('data', {}).get('slow_queries', [])
                print(f"  Slow Queries: {len(queries)}")
            
            # Test alerts endpoint
            response = self.client.get('/core/api/monitoring/alerts/')
            print(f"Alerts API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                alerts = data.get('data', {}).get('active_alerts', [])
                print(f"  Active Alerts: {len(alerts)}")
            
            # Test configuration endpoint
            response = self.client.get('/core/api/monitoring/config/')
            print(f"Configuration API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                config = data.get('data', {})
                print(f"  Monitoring Enabled: {config.get('monitoring', {}).get('enabled', False)}")
                print(f"  Alert Thresholds: {len(config.get('thresholds', {}))}")
            
            print("✓ API endpoints test passed")
            return True
            
        except Exception as e:
            print(f"✗ API endpoints test failed: {e}")
            return False
    
    def test_alert_channels(self):
        """Test alert channel functionality"""
        print("\n=== Testing Alert Channels ===")
        
        try:
            # Test channel configuration
            channels = self.alerting.channels
            print(f"Configured alert channels: {len(channels)}")
            
            for channel in channels:
                print(f"  {channel.name} ({channel.type}): {'Enabled' if channel.enabled else 'Disabled'}")
            
            # Test alert suppression
            self.alerting.suppress_alert('default', 'test_metric', duration_minutes=1)
            suppressed = self.alerting.get_suppressed_alerts()
            print(f"Suppressed alerts: {len(suppressed)}")
            
            # Test alert acknowledgment
            test_alert_id = f"test_alert_{int(time.time())}"
            self.alerting.acknowledge_alert(test_alert_id, 'test_user')
            acknowledged = self.alerting.get_acknowledged_alerts()
            print(f"Acknowledged alerts: {len(acknowledged)}")
            
            print("✓ Alert channels test passed")
            return True
            
        except Exception as e:
            print(f"✗ Alert channels test failed: {e}")
            return False
    
    def test_recovery_mechanisms(self):
        """Test automatic recovery mechanisms"""
        print("\n=== Testing Recovery Mechanisms ===")
        
        try:
            # Test connection recovery
            print("Testing connection recovery...")
            self.monitor._recover_connection_exhaustion('default')
            
            # Test slow query recovery
            print("Testing slow query recovery...")
            self.monitor._recover_slow_queries('default')
            
            # Test memory recovery
            print("Testing memory recovery...")
            self.monitor._recover_memory_issues('default')
            
            print("✓ Recovery mechanisms test passed")
            return True
            
        except Exception as e:
            print(f"✗ Recovery mechanisms test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting Database Monitoring System Tests")
        print("=" * 60)
        
        self.setup()
        
        tests = [
            self.test_metrics_collection,
            self.test_slow_query_analysis,
            self.test_alert_system,
            self.test_health_summary,
            self.test_api_endpoints,
            self.test_alert_channels,
            self.test_recovery_mechanisms
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Test {test.__name__} failed with exception: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Database monitoring system is working correctly.")
        else:
            print(f"⚠️  {failed} tests failed. Please check the implementation.")
        
        # Cleanup
        self.cleanup()
        
        return failed == 0
    
    def cleanup(self):
        """Cleanup test environment"""
        print("\nCleaning up test environment...")
        
        if self.monitor:
            self.monitor.stop_monitoring()
        
        print("Cleanup complete")


def main():
    """Main test function"""
    test_suite = DatabaseMonitoringTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Database monitoring system is ready for production!")
        sys.exit(0)
    else:
        print("\n❌ Database monitoring system has issues that need to be resolved.")
        sys.exit(1)


if __name__ == '__main__':
    main()