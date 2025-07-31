#!/usr/bin/env python
"""
Simple test script for database monitoring system
"""

import os
import sys
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from core.database_monitor import get_database_monitor
from core.database_alerting import get_database_alerting

def test_basic_functionality():
    """Test basic monitoring functionality"""
    print("Testing Database Monitoring System...")
    
    try:
        # Initialize monitoring
        monitor = get_database_monitor()
        alerting = get_database_alerting()
        
        print("✓ Monitor and alerting systems initialized")
        
        # Test metrics collection
        print("Testing metrics collection...")
        time.sleep(2)  # Wait for initial collection
        
        current_metrics = monitor.get_current_metrics()
        print(f"✓ Collected metrics for {len(current_metrics)} databases")
        
        # Test health summary
        health_summary = monitor.get_health_summary()
        print(f"✓ Health summary generated: {health_summary.get('overall_status', 'unknown')}")
        
        # Test slow queries
        slow_queries = monitor.get_slow_queries(limit=5)
        print(f"✓ Slow queries analysis: {len(slow_queries)} queries found")
        
        # Test alerts
        active_alerts = monitor.get_active_alerts()
        print(f"✓ Active alerts: {len(active_alerts)} alerts")
        
        # Test configuration
        config_data = {
            'monitoring_enabled': monitor.monitoring_enabled,
            'alerting_enabled': monitor.alerting_enabled,
            'recovery_enabled': monitor.recovery_enabled,
            'thresholds_count': len(monitor.alert_thresholds),
            'alert_channels': len(alerting.channels)
        }
        
        print("✓ Configuration:")
        for key, value in config_data.items():
            print(f"  {key}: {value}")
        
        print("\n🎉 Database monitoring system is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            monitor.stop_monitoring()
            print("✓ Monitoring stopped")
        except:
            pass

if __name__ == '__main__':
    success = test_basic_functionality()
    sys.exit(0 if success else 1)