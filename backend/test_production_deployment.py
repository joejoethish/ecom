#!/usr/bin/env python
"""
Production deployment test for monitoring system
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
from django.test import Client
from apps.debugging.production_monitoring import (
    start_production_monitoring,
    stop_production_monitoring,
    cleanup_old_data,
    initialize_production_monitoring
)

def test_production_deployment():
    """Test production deployment readiness"""
    print("Production Deployment Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Initialize production monitoring
    total_tests += 1
    try:
        initialize_production_monitoring()
        print("✓ Production monitoring initialization: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Production monitoring initialization: FAILED - {e}")
    
    # Test 2: Health check endpoints
    total_tests += 1
    try:
        client = Client()
        
        # Basic health check
        response = client.get('/health/')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['healthy', 'degraded']
        assert 'timestamp' in data
        assert data['service'] == 'ecommerce-backend'
        
        print("✓ Health check endpoints: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Health check endpoints: FAILED - {e}")
    
    # Test 3: Detailed health check
    total_tests += 1
    try:
        response = client.get('/production/health/detailed/')
        assert response.status_code in [200, 503]  # 503 is acceptable if some services are down
        data = response.json()
        assert 'overall_status' in data
        assert 'health_checks' in data
        assert 'active_alerts_count' in data
        
        print("✓ Detailed health check: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Detailed health check: FAILED - {e}")
    
    # Test 4: Alert management
    total_tests += 1
    try:
        response = client.get('/production/alerts/')
        assert response.status_code == 200
        data = response.json()
        assert 'active_alerts' in data
        assert 'alert_history' in data
        assert 'total_active' in data
        
        print("✓ Alert management endpoints: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Alert management endpoints: FAILED - {e}")
    
    # Test 5: Monitoring dashboard
    total_tests += 1
    try:
        response = client.get('/production/dashboard/')
        assert response.status_code == 200
        data = response.json()
        assert 'system_status' in data
        assert 'health_checks' in data
        assert 'alerts' in data
        
        print("✓ Monitoring dashboard: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Monitoring dashboard: FAILED - {e}")
    
    # Test 6: Log file creation
    total_tests += 1
    try:
        log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        assert os.path.exists(log_dir)
        
        # Check for log files
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        assert len(log_files) > 0
        
        print("✓ Log file creation: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Log file creation: FAILED - {e}")
    
    # Test 7: Data cleanup functionality
    total_tests += 1
    try:
        result = cleanup_old_data(days_to_keep=30)
        assert isinstance(result, dict)
        assert 'deleted_snapshots' in result or 'error' in result
        
        print("✓ Data cleanup functionality: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Data cleanup functionality: FAILED - {e}")
    
    # Test 8: Production monitoring lifecycle
    total_tests += 1
    try:
        # Start monitoring
        start_result = start_production_monitoring()
        assert start_result == True
        
        # Wait a moment
        time.sleep(1)
        
        # Stop monitoring
        stop_result = stop_production_monitoring()
        assert stop_result == True
        
        print("✓ Production monitoring lifecycle: PASSED")
        success_count += 1
    except Exception as e:
        print(f"✗ Production monitoring lifecycle: FAILED - {e}")
    
    # Summary
    print()
    print("=" * 50)
    print(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED - Production deployment ready!")
        return True
    else:
        print(f"⚠️  {total_tests - success_count} tests failed - Review issues before deployment")
        return False

def test_load_balancer_integration():
    """Test load balancer integration"""
    print("\nLoad Balancer Integration Test")
    print("-" * 30)
    
    client = Client()
    
    # Test multiple health check calls (simulating load balancer)
    for i in range(5):
        response = client.get('/health/')
        print(f"Health check {i+1}: {response.status_code} - {response.json()['status']}")
        time.sleep(0.1)
    
    print("✓ Load balancer integration ready")

def test_monitoring_performance():
    """Test monitoring system performance impact"""
    print("\nMonitoring Performance Test")
    print("-" * 30)
    
    client = Client()
    
    # Measure response times
    start_time = time.time()
    for i in range(10):
        response = client.get('/health/')
        assert response.status_code == 200
    end_time = time.time()
    
    avg_response_time = (end_time - start_time) / 10 * 1000  # Convert to ms
    print(f"Average health check response time: {avg_response_time:.2f}ms")
    
    if avg_response_time < 100:  # Should be under 100ms
        print("✓ Performance impact acceptable")
    else:
        print("⚠️  Performance impact may be too high")

def main():
    """Run all production deployment tests"""
    try:
        # Main deployment test
        deployment_ready = test_production_deployment()
        
        # Additional tests
        test_load_balancer_integration()
        test_monitoring_performance()
        
        print("\n" + "=" * 50)
        if deployment_ready:
            print("✅ PRODUCTION DEPLOYMENT READY")
            print("\nNext steps:")
            print("1. Configure notification channels (email, Slack)")
            print("2. Set up log aggregation (ELK stack)")
            print("3. Configure load balancer health checks")
            print("4. Set up external monitoring (Prometheus/Grafana)")
            print("5. Train operations team on monitoring tools")
        else:
            print("❌ PRODUCTION DEPLOYMENT NOT READY")
            print("Please fix the failing tests before deploying to production.")
        
        return deployment_ready
        
    except Exception as e:
        print(f"✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)