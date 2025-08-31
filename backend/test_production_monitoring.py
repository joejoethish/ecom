#!/usr/bin/env python
"""
Simple test script for production monitoring system
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

import time
import logging
from datetime import datetime
from apps.debugging.production_monitoring import (
    ProductionLogger,
    AlertingSystem,
    HealthCheckService,
    ProductionMonitoringDashboard,
    start_production_monitoring,
    stop_production_monitoring
)

def test_production_logger():
    """Test production logging functionality"""
    print("Testing Production Logger...")
    
    logger = ProductionLogger()
    
    # Test logging
    logging.info("Test info message")
    logging.warning("Test warning message")
    logging.error("Test error message")
    
    # Test log files info
    log_files = logger.get_log_files_info()
    print(f"Log files: {list(log_files.keys())}")
    
    print("✓ Production Logger test completed")


def test_health_checks():
    """Test health check functionality"""
    print("Testing Health Checks...")
    
    health_service = HealthCheckService()
    
    # Run all health checks
    results = health_service.run_all_health_checks()
    
    print(f"Health check results:")
    for result in results:
        status_symbol = "✓" if result.status == 'healthy' else \
                       "⚠" if result.status == 'degraded' else "✗"
        print(f"  {status_symbol} {result.service}: {result.status} "
              f"({result.response_time_ms:.1f}ms)")
        
        if result.error_message:
            print(f"    Error: {result.error_message}")
    
    print("✓ Health Checks test completed")


def test_alerting_system():
    """Test alerting system functionality"""
    print("Testing Alerting System...")
    
    alerting = AlertingSystem()
    
    # Create a test alert
    alerting._create_alert(
        alert_type='test',
        severity='medium',
        title='Test Alert',
        message='This is a test alert for system validation',
        component='test_component',
        layer='test_layer',
        metric_name='test_metric',
        current_value=100.0,
        threshold_value=80.0
    )
    
    # Get active alerts
    active_alerts = alerting.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    
    for alert in active_alerts:
        print(f"  - {alert.severity.upper()}: {alert.title}")
    
    # Resolve test alert
    if active_alerts:
        test_alert = active_alerts[0]
        alerting.resolve_alert(test_alert.alert_id, "test_script")
        print(f"  Resolved alert: {test_alert.alert_id}")
    
    print("✓ Alerting System test completed")


def test_monitoring_dashboard():
    """Test monitoring dashboard functionality"""
    print("Testing Monitoring Dashboard...")
    
    dashboard = ProductionMonitoringDashboard()
    
    # Get system status
    system_status = dashboard.get_system_status()
    
    print(f"System Status: {system_status.status}")
    print(f"Timestamp: {system_status.timestamp}")
    print(f"Uptime: {system_status.uptime_seconds:.1f} seconds")
    print(f"Health Checks: {len(system_status.health_checks)}")
    print(f"Active Alerts: {len(system_status.active_alerts)}")
    
    # Performance summary
    if system_status.performance_summary:
        print("Performance Summary:")
        for metric, data in system_status.performance_summary.items():
            if isinstance(data, dict) and 'avg' in data:
                print(f"  {metric}: avg={data['avg']}, max={data['max']}")
            else:
                print(f"  {metric}: {data}")
    
    print("✓ Monitoring Dashboard test completed")


def test_production_monitoring_lifecycle():
    """Test complete production monitoring lifecycle"""
    print("Testing Production Monitoring Lifecycle...")
    
    # Start monitoring
    print("  Starting monitoring...")
    success = start_production_monitoring()
    if success:
        print("  ✓ Monitoring started")
    else:
        print("  ✗ Failed to start monitoring")
        return
    
    # Wait a moment
    time.sleep(2)
    
    # Check status
    dashboard = ProductionMonitoringDashboard()
    status = dashboard.get_system_status()
    print(f"  System status: {status.status}")
    
    # Stop monitoring
    print("  Stopping monitoring...")
    success = stop_production_monitoring()
    if success:
        print("  ✓ Monitoring stopped")
    else:
        print("  ✗ Failed to stop monitoring")
    
    print("✓ Production Monitoring Lifecycle test completed")


def main():
    """Run all production monitoring tests"""
    print("Production Monitoring System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Run individual tests
        test_production_logger()
        print()
        
        test_health_checks()
        print()
        
        test_alerting_system()
        print()
        
        test_monitoring_dashboard()
        print()
        
        test_production_monitoring_lifecycle()
        print()
        
        print("=" * 50)
        print("✓ All production monitoring tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()