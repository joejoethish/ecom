#!/usr/bin/env python
"""
Simple test script for the logging system without Django test framework
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.logs.aggregation import (
    LogAggregationService, 
    AggregatedLogEntry, 
    LogLevel, 
    LogSource,
    log_frontend_entry,
    log_backend_entry,
    log_database_entry
)
from datetime import datetime
from django.core.cache import cache

def test_log_aggregation_service():
    """Test the log aggregation service"""
    print("Testing Log Aggregation Service...")
    
    # Clear cache
    cache.clear()
    
    service = LogAggregationService()
    correlation_id = 'test-correlation-123'
    
    # Test adding a log entry
    entry = AggregatedLogEntry(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message='Test message',
        source=LogSource.FRONTEND,
        correlation_id=correlation_id,
        user_id='user123'
    )
    
    service.add_log_entry(entry)
    print("✓ Added log entry")
    
    # Test retrieving logs
    logs = service.get_logs_by_correlation_id(correlation_id)
    assert len(logs) == 1
    assert logs[0]['message'] == 'Test message'
    assert logs[0]['source'] == 'frontend'
    print("✓ Retrieved logs by correlation ID")
    
    # Test workflow trace
    trace = service.get_workflow_trace(correlation_id)
    assert trace['correlation_id'] == correlation_id
    assert len(trace['entries']) == 1
    print("✓ Generated workflow trace")
    
    print("Log Aggregation Service tests passed!\n")

def test_helper_functions():
    """Test the helper functions"""
    print("Testing Helper Functions...")
    
    cache.clear()
    service = LogAggregationService()
    correlation_id = 'test-helper-123'
    
    # Test frontend logging
    log_frontend_entry(
        correlation_id=correlation_id,
        level='info',
        message='Frontend test',
        user_id='user123',
        user_action='click',
        component='button'
    )
    
    logs = service.get_logs_by_correlation_id(correlation_id)
    assert len(logs) == 1
    assert logs[0]['source'] == 'frontend'
    assert logs[0]['user_action'] == 'click'
    print("✓ Frontend logging helper works")
    
    # Test backend logging
    log_backend_entry(
        correlation_id=correlation_id,
        level='info',
        message='Backend test',
        request_method='GET',
        request_url='/api/test/',
        response_status=200
    )
    
    logs = service.get_logs_by_correlation_id(correlation_id)
    assert len(logs) == 2
    backend_log = next(log for log in logs if log['source'] == 'backend')
    assert backend_log['request_method'] == 'GET'
    print("✓ Backend logging helper works")
    
    # Test database logging
    log_database_entry(
        correlation_id=correlation_id,
        level='info',
        message='Database test',
        sql_query='SELECT * FROM test',
        query_duration=25.5
    )
    
    logs = service.get_logs_by_correlation_id(correlation_id)
    assert len(logs) == 3
    db_log = next(log for log in logs if log['source'] == 'database')
    assert db_log['sql_query'] == 'SELECT * FROM test'
    assert db_log['query_duration'] == 25.5
    print("✓ Database logging helper works")
    
    print("Helper Functions tests passed!\n")

def test_performance_analysis():
    """Test performance issue detection"""
    print("Testing Performance Analysis...")
    
    cache.clear()
    service = LogAggregationService()
    correlation_id = 'test-performance-123'
    
    # Add slow query
    log_database_entry(
        correlation_id=correlation_id,
        level='warn',
        message='Slow database query',
        sql_query='SELECT * FROM large_table',
        query_duration=500  # 500ms - slow
    )
    
    # Add slow API call
    log_backend_entry(
        correlation_id=correlation_id,
        level='warn',
        message='Slow API response',
        request_method='GET',  # Add request method
        request_url='/api/slow/',
        response_time=2000  # 2 seconds - slow
    )
    
    # Get workflow trace with performance analysis
    trace = service.get_workflow_trace(correlation_id)
    performance_issues = trace['analysis']['performance_issues']
    
    print(f"Debug: Found {len(performance_issues)} performance issues")
    print(f"Debug: Performance issues: {performance_issues}")
    
    assert len(performance_issues) == 2
    print("✓ Detected performance issues")
    
    # Check for slow query issue
    slow_query_issue = next(
        (issue for issue in performance_issues if issue['type'] == 'slow_query'), 
        None
    )
    assert slow_query_issue is not None
    assert slow_query_issue['duration'] == 500
    print("✓ Detected slow query")
    
    # Check for slow API call issue
    slow_api_issue = next(
        (issue for issue in performance_issues if issue['type'] == 'slow_api_call'), 
        None
    )
    assert slow_api_issue is not None
    assert slow_api_issue['duration'] == 2000
    print("✓ Detected slow API call")
    
    print("Performance Analysis tests passed!\n")

def test_error_patterns():
    """Test error pattern detection"""
    print("Testing Error Pattern Detection...")
    
    cache.clear()
    service = LogAggregationService()
    
    # Add error entries
    log_backend_entry(
        correlation_id='error-1',
        level='error',
        message='Database connection failed'
    )
    
    log_backend_entry(
        correlation_id='error-2',
        level='error',
        message='Database connection failed'
    )
    
    log_backend_entry(
        correlation_id='error-3',
        level='error',
        message='API timeout'
    )
    
    # Get error patterns
    patterns = service.get_error_patterns(hours=1)
    
    print(f"Debug: Found {patterns['total_errors']} total errors")
    print(f"Debug: Found {patterns['unique_patterns']} unique patterns")
    
    assert patterns['total_errors'] == 3
    assert patterns['unique_patterns'] > 0
    print("✓ Error pattern detection works")
    
    print("Error Pattern Detection tests passed!\n")

if __name__ == '__main__':
    print("Running Logging System Tests...\n")
    
    try:
        test_log_aggregation_service()
        test_helper_functions()
        test_performance_analysis()
        test_error_patterns()
        
        print("🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)