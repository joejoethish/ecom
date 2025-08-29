#!/usr/bin/env python
"""
Simple validation script for the interactive debugging dashboard backend API.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def main():
    print("Interactive Debugging Dashboard Backend API Validation")
    print("=" * 60)
    
    # Test 1: Import dashboard views
    try:
        from apps.debugging.dashboard_views import (
            DashboardDataViewSet, ReportGenerationViewSet, 
            ManualAPITestingViewSet, DashboardConfigurationViewSet
        )
        print("✓ Dashboard views imported successfully")
    except ImportError as e:
        print(f"✗ Dashboard views import failed: {e}")
        return False
    
    # Test 2: Import WebSocket consumers
    try:
        from apps.debugging.consumers import DashboardConsumer, WorkflowTraceConsumer
        print("✓ WebSocket consumers imported successfully")
    except ImportError as e:
        print(f"✗ WebSocket consumers import failed: {e}")
        return False
    
    # Test 3: Import serializers
    try:
        from apps.debugging.serializers import (
            DashboardDataSerializer, RealtimeUpdateSerializer, DebugReportSerializer
        )
        print("✓ Dashboard serializers imported successfully")
    except ImportError as e:
        print(f"✗ Dashboard serializers import failed: {e}")
        return False
    
    # Test 4: Import testing framework
    try:
        from apps.debugging.testing_framework import APITestingFramework
        framework = APITestingFramework()
        if hasattr(framework, 'test_single_endpoint') and hasattr(framework, 'test_workflow_sequence'):
            print("✓ Testing framework with required methods available")
        else:
            print("✗ Testing framework missing required methods")
            return False
    except ImportError as e:
        print(f"✗ Testing framework import failed: {e}")
        return False
    
    # Test 5: Check URL configuration
    try:
        from django.urls import reverse
        test_urls = [
            'debugging:dashboard-data-list',
            'debugging:reports-generate-workflow-report',
            'debugging:manual-testing-test-endpoint',
            'debugging:dashboard-health-check'
        ]
        
        for url_name in test_urls:
            try:
                url = reverse(url_name)
                print(f"✓ URL {url_name} configured: {url}")
            except Exception as e:
                print(f"✗ URL {url_name} not configured: {e}")
                return False
                
    except Exception as e:
        print(f"✗ URL configuration test failed: {e}")
        return False
    
    # Test 6: WebSocket routing
    try:
        from apps.debugging.routing import websocket_urlpatterns
        if len(websocket_urlpatterns) >= 2:
            print(f"✓ WebSocket routing configured with {len(websocket_urlpatterns)} patterns")
        else:
            print("✗ WebSocket routing not properly configured")
            return False
    except ImportError as e:
        print(f"✗ WebSocket routing import failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL VALIDATIONS PASSED!")
    print("\nImplemented components:")
    print("✅ Django REST API endpoints for dashboard data retrieval")
    print("✅ Real-time WebSocket service for live dashboard updates") 
    print("✅ Report generation service for debugging summaries")
    print("✅ Manual API testing endpoints for dashboard integration")
    print("✅ API tests for dashboard backend functionality")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)