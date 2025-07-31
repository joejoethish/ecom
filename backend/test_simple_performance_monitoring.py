#!/usr/bin/env python
"""
Simple test for performance monitoring system
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.db import connections
from core.performance_monitor import get_performance_monitor, initialize_performance_monitoring


def test_basic_functionality():
    """Test basic performance monitoring functionality"""
    print("Testing Performance Monitoring System...")
    print("=" * 50)
    
    try:
        # Test database connection first
        print("1. Testing database connection...")
        db_connection = connections['default']
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"   ✓ Database connection successful: {result}")
        
        # Initialize performance monitor
        print("2. Initializing performance monitor...")
        monitor = initialize_performance_monitoring(monitoring_interval=10)
        print(f"   ✓ Performance monitor initialized")
        print(f"   ✓ Monitoring enabled: {monitor.monitoring_enabled}")
        
        # Wait for some data collection
        print("3. Waiting for metrics collection (15 seconds)...")
        time.sleep(15)
        
        # Check metrics
        print("4. Checking collected metrics...")
        metrics = monitor.get_current_performance_metrics('default')
        print(f"   ✓ Metrics collected: {len(metrics)} types")
        
        for metric_name, data in metrics.items():
            print(f"   - {metric_name}: current={data.get('current', 'N/A'):.2f}")
        
        # Check history
        print("5. Checking performance history...")
        history_size = sum(len(h) for h in monitor.performance_history.values())
        print(f"   ✓ History data points: {history_size}")
        
        # Check recommendations
        print("6. Checking optimization recommendations...")
        recommendations = monitor.get_optimization_recommendations(5)
        print(f"   ✓ Optimization recommendations: {len(recommendations)}")
        
        # Check capacity recommendations
        print("7. Checking capacity recommendations...")
        capacity_recs = monitor.get_capacity_recommendations(5)
        print(f"   ✓ Capacity recommendations: {len(capacity_recs)}")
        
        # Check regressions
        print("8. Checking performance regressions...")
        regressions = monitor.get_performance_regressions(5)
        print(f"   ✓ Performance regressions: {len(regressions)}")
        
        print("\n🎉 Performance monitoring system is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_basic_functionality()
    sys.exit(0 if success else 1)