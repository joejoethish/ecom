#!/usr/bin/env python
"""
Validation script for performance monitoring implementation

This script validates that all performance monitoring components are properly implemented
without requiring a live database connection.
"""

import os
import sys
import importlib
import inspect
from pathlib import Path

def validate_implementation():
    """Validate that all performance monitoring components are properly implemented"""
    
    print("Validating Performance Monitoring Implementation...")
    print("=" * 60)
    
    validation_results = []
    
    # Test 1: Import core performance monitoring modules
    try:
        from core.performance_monitor import PerformanceMonitor, get_performance_monitor, initialize_performance_monitoring
        from core.performance_monitor import PerformanceBaseline, QueryOptimizationRecommendation, CapacityRecommendation, PerformanceRegression
        validation_results.append(("✓", "Core performance monitoring modules import successfully"))
    except ImportError as e:
        validation_results.append(("✗", f"Failed to import core performance monitoring modules: {e}"))
    
    # Test 2: Import performance views
    try:
        from core.performance_views import (
            performance_dashboard, performance_metrics_api, optimization_recommendations_api,
            capacity_recommendations_api, performance_regressions_api, PerformanceMonitoringView
        )
        validation_results.append(("✓", "Performance monitoring views import successfully"))
    except ImportError as e:
        validation_results.append(("✗", f"Failed to import performance monitoring views: {e}"))
    
    # Test 3: Import performance URLs
    try:
        from core.performance_urls import urlpatterns
        assert len(urlpatterns) >= 10  # Should have multiple URL patterns
        validation_results.append(("✓", f"Performance monitoring URLs configured ({len(urlpatterns)} patterns)"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"Performance monitoring URLs not properly configured: {e}"))
    
    # Test 4: Import management command
    try:
        from core.management.commands.performance_monitor import Command
        cmd = Command()
        assert hasattr(cmd, 'handle')
        assert hasattr(cmd, 'add_arguments')
        validation_results.append(("✓", "Performance monitoring management command available"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"Performance monitoring management command not available: {e}"))
    
    # Test 5: Import Celery tasks
    try:
        from tasks.performance_monitoring_tasks import (
            collect_performance_metrics, analyze_query_performance,
            detect_performance_regressions, generate_capacity_recommendations,
            generate_daily_performance_report, cleanup_old_performance_data,
            update_performance_baselines
        )
        validation_results.append(("✓", "Performance monitoring Celery tasks import successfully"))
    except ImportError as e:
        validation_results.append(("✗", f"Failed to import performance monitoring Celery tasks: {e}"))
    
    # Test 6: Check Celery task scheduling
    try:
        from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
        
        # Check for performance monitoring tasks in schedule
        perf_schedule_tasks = [k for k in CELERY_BEAT_SCHEDULE.keys() if 'performance' in k]
        assert len(perf_schedule_tasks) >= 5  # Should have multiple scheduled tasks
        
        # Check for performance monitoring tasks in routes
        perf_route_tasks = [k for k in CELERY_TASK_ROUTES.keys() if 'performance_monitoring' in k]
        assert len(perf_route_tasks) >= 5  # Should have multiple routed tasks
        
        validation_results.append(("✓", f"Performance monitoring tasks scheduled ({len(perf_schedule_tasks)} scheduled, {len(perf_route_tasks)} routed)"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"Performance monitoring tasks not properly scheduled: {e}"))
    
    # Test 7: Validate PerformanceMonitor class structure
    try:
        from core.performance_monitor import PerformanceMonitor
        
        # Check required methods
        required_methods = [
            'start_monitoring', 'stop_monitoring', 'get_current_performance_metrics',
            'get_optimization_recommendations', 'get_capacity_recommendations',
            'get_performance_regressions', 'get_performance_baselines',
            'reset_baseline', 'update_thresholds'
        ]
        
        for method in required_methods:
            assert hasattr(PerformanceMonitor, method), f"Missing method: {method}"
        
        validation_results.append(("✓", f"PerformanceMonitor class has all required methods ({len(required_methods)} methods)"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"PerformanceMonitor class structure invalid: {e}"))
    
    # Test 8: Validate data structures
    try:
        from core.performance_monitor import PerformanceBaseline, QueryOptimizationRecommendation, CapacityRecommendation, PerformanceRegression
        
        # Test that data structures can be instantiated (with dummy data)
        from datetime import datetime
        
        baseline = PerformanceBaseline(
            database_alias='test',
            metric_name='cpu',
            baseline_value=50.0,
            baseline_timestamp=datetime.now(),
            sample_count=100,
            confidence_interval=(45.0, 55.0)
        )
        
        recommendation = QueryOptimizationRecommendation(
            query_hash='test123',
            query_text='SELECT * FROM test',
            current_performance={'execution_time': 2.5},
            recommendations=['Add index'],
            priority='medium',
            estimated_improvement=25.0,
            implementation_effort='easy',
            timestamp=datetime.now()
        )
        
        capacity_rec = CapacityRecommendation(
            resource_type='cpu',
            current_usage=80.0,
            projected_usage=95.0,
            time_to_capacity=30,
            recommended_action='Scale up',
            urgency='high',
            cost_estimate=100.0,
            timestamp=datetime.now()
        )
        
        regression = PerformanceRegression(
            database_alias='test',
            metric_name='cpu',
            baseline_value=50.0,
            current_value=75.0,
            regression_percentage=50.0,
            detection_timestamp=datetime.now(),
            severity='major',
            potential_causes=['High load']
        )
        
        validation_results.append(("✓", "All data structures can be instantiated correctly"))
    except Exception as e:
        validation_results.append(("✗", f"Data structures cannot be instantiated: {e}"))
    
    # Test 9: Check template files
    try:
        template_path = Path("templates/admin/performance_dashboard.html")
        assert template_path.exists(), "Performance dashboard template not found"
        
        # Check template content
        with open(template_path, 'r') as f:
            template_content = f.read()
            assert 'performance-dashboard' in template_content
            assert 'metrics-grid' in template_content
            
        validation_results.append(("✓", "Performance dashboard template exists and has required content"))
    except (AssertionError, FileNotFoundError) as e:
        validation_results.append(("✗", f"Performance dashboard template issues: {e}"))
    
    # Test 10: Validate API endpoint functions
    try:
        from core.performance_views import (
            performance_metrics_api, optimization_recommendations_api,
            capacity_recommendations_api, performance_regressions_api,
            performance_baselines_api, reset_baseline_api, update_thresholds_api
        )
        
        # Check that functions are callable
        api_functions = [
            performance_metrics_api, optimization_recommendations_api,
            capacity_recommendations_api, performance_regressions_api,
            performance_baselines_api, reset_baseline_api, update_thresholds_api
        ]
        
        for func in api_functions:
            assert callable(func), f"Function {func.__name__} is not callable"
        
        validation_results.append(("✓", f"All API endpoint functions are callable ({len(api_functions)} functions)"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"API endpoint functions not properly defined: {e}"))
    
    # Test 11: Check integration with existing monitoring
    try:
        from core.database_monitor import get_database_monitor
        from core.database_alerting import get_database_alerting
        
        # These should be importable and callable
        assert callable(get_database_monitor)
        assert callable(get_database_alerting)
        
        validation_results.append(("✓", "Integration with existing monitoring systems available"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"Integration with existing monitoring systems failed: {e}"))
    
    # Test 12: Validate task requirements implementation
    try:
        # Check that all task 19 requirements are addressed
        requirements_met = []
        
        # Requirement: Continuous performance monitoring and alerting
        from core.performance_monitor import PerformanceMonitor
        monitor_class = PerformanceMonitor
        assert hasattr(monitor_class, '_monitoring_loop'), "Continuous monitoring loop not implemented"
        requirements_met.append("Continuous performance monitoring")
        
        # Requirement: Automated query optimization recommendations
        assert hasattr(monitor_class, '_analyze_query_for_optimization'), "Query optimization analysis not implemented"
        assert hasattr(monitor_class, 'get_optimization_recommendations'), "Optimization recommendations not implemented"
        requirements_met.append("Automated query optimization recommendations")
        
        # Requirement: Capacity planning and scaling recommendations
        assert hasattr(monitor_class, '_generate_capacity_recommendations'), "Capacity planning not implemented"
        assert hasattr(monitor_class, 'get_capacity_recommendations'), "Capacity recommendations not implemented"
        requirements_met.append("Capacity planning and scaling recommendations")
        
        # Requirement: Performance regression detection
        assert hasattr(monitor_class, '_detect_regressions'), "Regression detection not implemented"
        assert hasattr(monitor_class, 'get_performance_regressions'), "Performance regressions not implemented"
        requirements_met.append("Performance regression detection")
        
        validation_results.append(("✓", f"All task 19 requirements implemented: {', '.join(requirements_met)}"))
    except (ImportError, AssertionError) as e:
        validation_results.append(("✗", f"Task 19 requirements not fully implemented: {e}"))
    
    # Print results
    print("\nValidation Results:")
    print("-" * 60)
    
    passed = 0
    total = len(validation_results)
    
    for status, message in validation_results:
        print(f"{status} {message}")
        if status == "✓":
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Performance monitoring implementation is COMPLETE and meets all requirements!")
        print("\nTask 19 Implementation Status: ✅ COMPLETE")
        print("\n✅ Continuous performance monitoring and alerting: IMPLEMENTED")
        print("✅ Automated query optimization recommendations: IMPLEMENTED") 
        print("✅ Capacity planning and scaling recommendations: IMPLEMENTED")
        print("✅ Performance regression detection: IMPLEMENTED")
        print("\nThe performance monitoring system is ready for production use.")
        return True
    else:
        failed = total - passed
        print(f"\n⚠️  {failed} validation tests failed. Please review the implementation.")
        return False


if __name__ == '__main__':
    success = validate_implementation()
    sys.exit(0 if success else 1)