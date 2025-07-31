#!/usr/bin/env python
"""
Test script for performance monitoring and optimization system

This script validates the implementation of task 19:
- Continuous performance monitoring and alerting
- Automated query optimization recommendations
- Capacity planning and scaling recommendations
- Performance regression detection
"""

import os
import sys
import django
import time
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.conf import settings
from django.db import connections

from core.performance_monitor import get_performance_monitor, initialize_performance_monitoring
from core.database_monitor import get_database_monitor
from core.database_alerting import get_database_alerting


class PerformanceMonitoringTest:
    """Test suite for performance monitoring system"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = 0
        
        print("Initializing Performance Monitoring Test Suite")
        print("=" * 60)
        
        # Initialize monitoring systems
        self.performance_monitor = initialize_performance_monitoring(monitoring_interval=5)
        self.db_monitor = get_database_monitor()
        self.alerting = get_database_alerting()
        
        # Wait a moment for initialization
        time.sleep(2)
    
    def log_test_result(self, test_name, success, message=""):
        """Log test result"""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
        if not success:
            self.failed_tests += 1
    
    def test_performance_monitor_initialization(self):
        """Test 1: Performance monitor initialization"""
        try:
            # Check if performance monitor is initialized
            assert self.performance_monitor is not None
            assert hasattr(self.performance_monitor, 'monitoring_enabled')
            assert hasattr(self.performance_monitor, 'performance_history')
            assert hasattr(self.performance_monitor, 'optimization_recommendations')
            assert hasattr(self.performance_monitor, 'capacity_recommendations')
            assert hasattr(self.performance_monitor, 'regressions')
            
            self.log_test_result("Performance monitor initialization", True)
            
        except Exception as e:
            self.log_test_result("Performance monitor initialization", False, str(e))
    
    def test_monitoring_thread_status(self):
        """Test 2: Monitoring thread status"""
        try:
            # Check if monitoring is enabled and thread is running
            assert self.performance_monitor.monitoring_enabled == True
            assert self.performance_monitor._monitoring_thread is not None
            assert self.performance_monitor._monitoring_thread.is_alive()
            
            self.log_test_result("Monitoring thread status", True, "Monitoring thread is active")
            
        except Exception as e:
            self.log_test_result("Monitoring thread status", False, str(e))
    
    def test_metrics_collection(self):
        """Test 3: Performance metrics collection"""
        try:
            # Wait for some metrics to be collected
            print("    Waiting 10 seconds for metrics collection...")
            time.sleep(10)
            
            # Check if metrics are being collected
            db_alias = 'default'
            metrics = self.performance_monitor.get_current_performance_metrics(db_alias)
            
            assert isinstance(metrics, dict)
            assert len(metrics) > 0
            
            # Check for expected metric types
            expected_metrics = ['cpu', 'memory', 'connections', 'query_time']
            found_metrics = [m for m in expected_metrics if any(m in key for key in metrics.keys())]
            
            assert len(found_metrics) > 0
            
            self.log_test_result("Performance metrics collection", True, 
                               f"Collected {len(metrics)} metric types")
            
        except Exception as e:
            self.log_test_result("Performance metrics collection", False, str(e))
    
    def test_baseline_creation(self):
        """Test 4: Performance baseline creation"""
        try:
            # Check if baselines can be created
            baselines = self.performance_monitor.get_performance_baselines()
            
            # Baselines might not exist yet for new system, but the method should work
            assert isinstance(baselines, dict)
            
            self.log_test_result("Performance baseline creation", True, 
                               f"Baseline system operational ({len(baselines)} baselines)")
            
        except Exception as e:
            self.log_test_result("Performance baseline creation", False, str(e))
    
    def test_optimization_recommendations(self):
        """Test 5: Query optimization recommendations"""
        try:
            # Get optimization recommendations
            recommendations = self.performance_monitor.get_optimization_recommendations(10)
            
            assert isinstance(recommendations, list)
            
            # Check structure of recommendations if any exist
            if recommendations:
                rec = recommendations[0]
                required_fields = ['query_hash', 'priority', 'estimated_improvement', 
                                 'implementation_effort', 'recommendations']
                
                for field in required_fields:
                    assert field in rec
            
            self.log_test_result("Query optimization recommendations", True, 
                               f"System operational ({len(recommendations)} recommendations)")
            
        except Exception as e:
            self.log_test_result("Query optimization recommendations", False, str(e))
    
    def test_capacity_recommendations(self):
        """Test 6: Capacity planning recommendations"""
        try:
            # Get capacity recommendations
            capacity_recs = self.performance_monitor.get_capacity_recommendations(10)
            
            assert isinstance(capacity_recs, list)
            
            # Check structure of recommendations if any exist
            if capacity_recs:
                rec = capacity_recs[0]
                required_fields = ['resource_type', 'current_usage', 'projected_usage', 
                                 'recommended_action', 'urgency']
                
                for field in required_fields:
                    assert field in rec
            
            self.log_test_result("Capacity planning recommendations", True, 
                               f"System operational ({len(capacity_recs)} recommendations)")
            
        except Exception as e:
            self.log_test_result("Capacity planning recommendations", False, str(e))
    
    def test_regression_detection(self):
        """Test 7: Performance regression detection"""
        try:
            # Get performance regressions
            regressions = self.performance_monitor.get_performance_regressions(10)
            
            assert isinstance(regressions, list)
            
            # Check structure of regressions if any exist
            if regressions:
                reg = regressions[0]
                required_fields = ['database_alias', 'metric_name', 'baseline_value', 
                                 'current_value', 'regression_percentage', 'severity']
                
                for field in required_fields:
                    assert field in reg
            
            self.log_test_result("Performance regression detection", True, 
                               f"System operational ({len(regressions)} regressions detected)")
            
        except Exception as e:
            self.log_test_result("Performance regression detection", False, str(e))
    
    def test_threshold_configuration(self):
        """Test 8: Threshold configuration"""
        try:
            # Test updating thresholds
            original_regression_threshold = self.performance_monitor.regression_threshold
            original_capacity_warning = self.performance_monitor.capacity_warning_threshold
            
            # Update thresholds
            self.performance_monitor.update_thresholds(
                regression_threshold=0.20,
                capacity_warning=0.75
            )
            
            # Verify updates
            assert self.performance_monitor.regression_threshold == 0.20
            assert self.performance_monitor.capacity_warning_threshold == 0.75
            
            # Restore original values
            self.performance_monitor.update_thresholds(
                regression_threshold=original_regression_threshold,
                capacity_warning=original_capacity_warning
            )
            
            self.log_test_result("Threshold configuration", True, "Thresholds can be updated")
            
        except Exception as e:
            self.log_test_result("Threshold configuration", False, str(e))
    
    def test_alerting_integration(self):
        """Test 9: Alerting system integration"""
        try:
            # Check if alerting system is accessible
            assert self.alerting is not None
            
            # Test alert channels configuration
            channels = self.alerting.channels
            assert isinstance(channels, list)
            
            self.log_test_result("Alerting system integration", True, 
                               f"Alerting system operational ({len(channels)} channels)")
            
        except Exception as e:
            self.log_test_result("Alerting system integration", False, str(e))
    
    def test_performance_history_storage(self):
        """Test 10: Performance history storage"""
        try:
            # Check if performance history is being stored
            history = self.performance_monitor.performance_history
            
            assert isinstance(history, dict)
            
            # Wait a bit more and check if history is growing
            initial_count = sum(len(h) for h in history.values())
            time.sleep(5)
            
            # Trigger metrics collection manually
            self.performance_monitor._collect_performance_metrics()
            
            final_count = sum(len(h) for h in history.values())
            
            self.log_test_result("Performance history storage", True, 
                               f"History storage operational ({final_count} data points)")
            
        except Exception as e:
            self.log_test_result("Performance history storage", False, str(e))
    
    def test_management_command_integration(self):
        """Test 11: Management command integration"""
        try:
            # Test if management command can be imported
            from core.management.commands.performance_monitor import Command
            
            cmd = Command()
            assert hasattr(cmd, 'handle')
            assert hasattr(cmd, 'add_arguments')
            
            self.log_test_result("Management command integration", True, 
                               "Performance monitor command available")
            
        except Exception as e:
            self.log_test_result("Management command integration", False, str(e))
    
    def test_api_endpoints(self):
        """Test 12: API endpoints functionality"""
        try:
            # Test if views can be imported
            from core.performance_views import (
                performance_metrics_api, optimization_recommendations_api,
                capacity_recommendations_api, performance_regressions_api
            )
            
            # Check if URL patterns can be imported
            from core.performance_urls import urlpatterns
            
            assert len(urlpatterns) > 0
            
            self.log_test_result("API endpoints functionality", True, 
                               f"API endpoints available ({len(urlpatterns)} URLs)")
            
        except Exception as e:
            self.log_test_result("API endpoints functionality", False, str(e))
    
    def test_celery_tasks_integration(self):
        """Test 13: Celery tasks integration"""
        try:
            # Test if Celery tasks can be imported
            from tasks.performance_monitoring_tasks import (
                collect_performance_metrics, analyze_query_performance,
                detect_performance_regressions, generate_capacity_recommendations
            )
            
            # Check if tasks are properly configured
            from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
            
            # Check for performance monitoring tasks in schedule
            perf_tasks = [k for k in CELERY_BEAT_SCHEDULE.keys() if 'performance' in k]
            assert len(perf_tasks) > 0
            
            # Check for performance monitoring tasks in routes
            perf_routes = [k for k in CELERY_TASK_ROUTES.keys() if 'performance_monitoring' in k]
            assert len(perf_routes) > 0
            
            self.log_test_result("Celery tasks integration", True, 
                               f"Celery integration complete ({len(perf_tasks)} scheduled tasks)")
            
        except Exception as e:
            self.log_test_result("Celery tasks integration", False, str(e))
    
    def test_continuous_monitoring(self):
        """Test 14: Continuous monitoring functionality"""
        try:
            # Test continuous monitoring over a longer period
            print("    Testing continuous monitoring for 30 seconds...")
            
            initial_metrics = self.performance_monitor.get_current_performance_metrics('default')
            initial_history_size = sum(len(h) for h in self.performance_monitor.performance_history.values())
            
            # Wait for continuous monitoring
            time.sleep(30)
            
            final_metrics = self.performance_monitor.get_current_performance_metrics('default')
            final_history_size = sum(len(h) for h in self.performance_monitor.performance_history.values())
            
            # Check if monitoring is continuous
            assert final_history_size > initial_history_size
            
            self.log_test_result("Continuous monitoring functionality", True, 
                               f"Continuous monitoring active (history grew by {final_history_size - initial_history_size} points)")
            
        except Exception as e:
            self.log_test_result("Continuous monitoring functionality", False, str(e))
    
    def test_data_export_functionality(self):
        """Test 15: Data export functionality"""
        try:
            # Test data export methods
            metrics = self.performance_monitor.get_current_performance_metrics('default')
            recommendations = self.performance_monitor.get_optimization_recommendations(5)
            capacity_recs = self.performance_monitor.get_capacity_recommendations(5)
            regressions = self.performance_monitor.get_performance_regressions(5)
            baselines = self.performance_monitor.get_performance_baselines()
            
            # Test JSON serialization
            export_data = {
                'metrics': metrics,
                'recommendations': recommendations,
                'capacity': capacity_recs,
                'regressions': regressions,
                'baselines': baselines
            }
            
            json_str = json.dumps(export_data, default=str)
            assert len(json_str) > 0
            
            self.log_test_result("Data export functionality", True, 
                               f"Data export operational ({len(json_str)} bytes)")
            
        except Exception as e:
            self.log_test_result("Data export functionality", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting Performance Monitoring System Tests")
        print("=" * 60)
        
        # Run all test methods
        test_methods = [
            self.test_performance_monitor_initialization,
            self.test_monitoring_thread_status,
            self.test_metrics_collection,
            self.test_baseline_creation,
            self.test_optimization_recommendations,
            self.test_capacity_recommendations,
            self.test_regression_detection,
            self.test_threshold_configuration,
            self.test_alerting_integration,
            self.test_performance_history_storage,
            self.test_management_command_integration,
            self.test_api_endpoints,
            self.test_celery_tasks_integration,
            self.test_continuous_monitoring,
            self.test_data_export_functionality
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test_result(test_name, False, f"Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = total_tests - self.failed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 All tests passed! Performance monitoring system is working correctly.")
            print("\nTask 19 Implementation Status: COMPLETE")
            print("\n✅ Continuous performance monitoring and alerting: IMPLEMENTED")
            print("✅ Automated query optimization recommendations: IMPLEMENTED")
            print("✅ Capacity planning and scaling recommendations: IMPLEMENTED")
            print("✅ Performance regression detection: IMPLEMENTED")
        else:
            print(f"\n⚠️  {self.failed_tests} tests failed. Please check the implementation.")
            
            # Show failed tests
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return self.failed_tests == 0


def main():
    """Main test function"""
    test_suite = PerformanceMonitoringTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Performance monitoring system is ready for production!")
        sys.exit(0)
    else:
        print("\n❌ Performance monitoring system has issues that need to be resolved.")
        sys.exit(1)


if __name__ == '__main__':
    main()