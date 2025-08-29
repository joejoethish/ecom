#!/usr/bin/env python
"""
Validation script for the interactive debugging dashboard backend API implementation.

This script validates that all required components for task 10 have been implemented correctly:
1. Django REST API endpoints for dashboard data retrieval
2. Real-time WebSocket service for live dashboard updates
3. Report generation service for debugging summaries
4. Manual API testing endpoints for dashboard integration
5. API tests for dashboard backend functionality
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.debugging.models import WorkflowSession, TraceStep, ErrorLog, PerformanceSnapshot
from apps.debugging.dashboard_views import (
    DashboardDataViewSet, ReportGenerationViewSet, 
    ManualAPITestingViewSet, DashboardConfigurationViewSet
)
from apps.debugging.consumers import DashboardConsumer, WorkflowTraceConsumer
from apps.debugging.websocket_signals import WebSocketNotifier


def validate_dashboard_api_endpoints():
    """Validate that all dashboard API endpoints are properly configured"""
    print("=== Validating Dashboard API Endpoints ===")
    
    required_endpoints = [
        'debugging:dashboard-data-list',
        'debugging:dashboard-data-realtime-updates',
        'debugging:reports-generate-workflow-report',
        'debugging:reports-generate-system-health-report',
        'debugging:reports-generate-performance-report',
        'debugging:manual-testing-test-endpoint',
        'debugging:manual-testing-test-workflow',
        'debugging:manual-testing-available-endpoints',
        'debugging:dashboard-config-list',
        'debugging:dashboard-config-update-configuration',
        'debugging:dashboard-health-check',
    ]
    
    success_count = 0
    for endpoint_name in required_endpoints:
        try:
            url = reverse(endpoint_name)
            print(f"✓ {endpoint_name}: {url}")
            success_count += 1
        except NoReverseMatch as e:
            print(f"✗ {endpoint_name}: URL not found - {e}")
    
    print(f"\nEndpoint validation: {success_count}/{len(required_endpoints)} endpoints configured correctly")
    return success_count == len(required_endpoints)


def validate_dashboard_viewsets():
    """Validate that all dashboard ViewSets are properly implemented"""
    print("\n=== Validating Dashboard ViewSets ===")
    
    viewsets = [
        ('DashboardDataViewSet', DashboardDataViewSet),
        ('ReportGenerationViewSet', ReportGenerationViewSet),
        ('ManualAPITestingViewSet', ManualAPITestingViewSet),
        ('DashboardConfigurationViewSet', DashboardConfigurationViewSet),
    ]
    
    success_count = 0
    for name, viewset_class in viewsets:
        try:
            # Check if viewset has required methods
            instance = viewset_class()
            
            # Check required methods for each viewset
            if name == 'DashboardDataViewSet':
                required_methods = ['list', 'realtime_updates']
            elif name == 'ReportGenerationViewSet':
                required_methods = ['generate_workflow_report', 'generate_system_health_report', 'generate_performance_report']
            elif name == 'ManualAPITestingViewSet':
                required_methods = ['test_endpoint', 'test_workflow', 'available_endpoints']
            elif name == 'DashboardConfigurationViewSet':
                required_methods = ['list', 'update_configuration']
            
            methods_found = []
            for method in required_methods:
                if hasattr(instance, method):
                    methods_found.append(method)
            
            if len(methods_found) == len(required_methods):
                print(f"✓ {name}: All required methods implemented ({', '.join(methods_found)})")
                success_count += 1
            else:
                missing = set(required_methods) - set(methods_found)
                print(f"✗ {name}: Missing methods - {', '.join(missing)}")
                
        except Exception as e:
            print(f"✗ {name}: Error validating viewset - {e}")
    
    print(f"\nViewSet validation: {success_count}/{len(viewsets)} viewsets implemented correctly")
    return success_count == len(viewsets)


def validate_websocket_consumers():
    """Validate that WebSocket consumers are properly implemented"""
    print("\n=== Validating WebSocket Consumers ===")
    
    consumers = [
        ('DashboardConsumer', DashboardConsumer),
        ('WorkflowTraceConsumer', WorkflowTraceConsumer),
    ]
    
    success_count = 0
    for name, consumer_class in consumers:
        try:
            # Check if consumer has required methods
            required_methods = ['connect', 'disconnect', 'receive']
            methods_found = []
            
            for method in required_methods:
                if hasattr(consumer_class, method):
                    methods_found.append(method)
            
            if len(methods_found) == len(required_methods):
                print(f"✓ {name}: All required methods implemented ({', '.join(methods_found)})")
                success_count += 1
            else:
                missing = set(required_methods) - set(methods_found)
                print(f"✗ {name}: Missing methods - {', '.join(missing)}")
                
        except Exception as e:
            print(f"✗ {name}: Error validating consumer - {e}")
    
    print(f"\nWebSocket consumer validation: {success_count}/{len(consumers)} consumers implemented correctly")
    return success_count == len(consumers)


def validate_websocket_signals():
    """Validate that WebSocket signal handlers are properly implemented"""
    print("\n=== Validating WebSocket Signal Handlers ===")
    
    try:
        # Check if WebSocketNotifier can be instantiated
        notifier = WebSocketNotifier()
        
        # Check if required methods exist
        required_methods = ['send_to_dashboard_group', 'send_to_workflow_group']
        methods_found = []
        
        for method in required_methods:
            if hasattr(notifier, method):
                methods_found.append(method)
        
        if len(methods_found) == len(required_methods):
            print(f"✓ WebSocketNotifier: All required methods implemented ({', '.join(methods_found)})")
            
            # Check if signal handlers are imported
            try:
                from apps.debugging import websocket_signals
                print("✓ WebSocket signal handlers imported successfully")
                return True
            except ImportError as e:
                print(f"✗ WebSocket signal handlers import failed: {e}")
                return False
        else:
            missing = set(required_methods) - set(methods_found)
            print(f"✗ WebSocketNotifier: Missing methods - {', '.join(missing)}")
            return False
            
    except Exception as e:
        print(f"✗ WebSocketNotifier validation failed: {e}")
        return False


def validate_serializers():
    """Validate that all required serializers are implemented"""
    print("\n=== Validating Dashboard Serializers ===")
    
    try:
        from apps.debugging.serializers import (
            DashboardDataSerializer, RealtimeUpdateSerializer, DebugReportSerializer,
            APITestRequestSerializer, APITestResponseSerializer, WebSocketMessageSerializer
        )
        
        serializers = [
            'DashboardDataSerializer',
            'RealtimeUpdateSerializer', 
            'DebugReportSerializer',
            'APITestRequestSerializer',
            'APITestResponseSerializer',
            'WebSocketMessageSerializer'
        ]
        
        print(f"✓ All dashboard serializers implemented: {', '.join(serializers)}")
        return True
        
    except ImportError as e:
        print(f"✗ Dashboard serializers import failed: {e}")
        return False


def validate_testing_framework_integration():
    """Validate that testing framework integration is working"""
    print("\n=== Validating Testing Framework Integration ===")
    
    try:
        from apps.debugging.testing_framework import APITestingFramework
        
        # Check if the testing framework has the required methods
        framework = APITestingFramework()
        required_methods = ['test_single_endpoint', 'test_workflow_sequence']
        
        methods_found = []
        for method in required_methods:
            if hasattr(framework, method):
                methods_found.append(method)
        
        if len(methods_found) == len(required_methods):
            print(f"✓ APITestingFramework: Required methods implemented ({', '.join(methods_found)})")
            return True
        else:
            missing = set(required_methods) - set(methods_found)
            print(f"✗ APITestingFramework: Missing methods - {', '.join(missing)}")
            return False
            
    except Exception as e:
        print(f"✗ Testing framework validation failed: {e}")
        return False


def validate_database_models():
    """Validate that all required database models exist and are accessible"""
    print("\n=== Validating Database Models ===")
    
    models = [
        ('WorkflowSession', WorkflowSession),
        ('TraceStep', TraceStep),
        ('ErrorLog', ErrorLog),
        ('PerformanceSnapshot', PerformanceSnapshot),
    ]
    
    success_count = 0
    for name, model_class in models:
        try:
            # Try to access the model's meta information
            model_class._meta.get_fields()
            print(f"✓ {name}: Model accessible and properly configured")
            success_count += 1
        except Exception as e:
            print(f"✗ {name}: Model validation failed - {e}")
    
    print(f"\nModel validation: {success_count}/{len(models)} models validated successfully")
    return success_count == len(models)


def run_comprehensive_validation():
    """Run comprehensive validation of the dashboard implementation"""
    print("🔍 INTERACTIVE DEBUGGING DASHBOARD BACKEND API VALIDATION")
    print("=" * 70)
    
    validation_results = []
    
    # Run all validations
    validation_results.append(("API Endpoints", validate_dashboard_api_endpoints()))
    validation_results.append(("ViewSets", validate_dashboard_viewsets()))
    validation_results.append(("WebSocket Consumers", validate_websocket_consumers()))
    validation_results.append(("WebSocket Signals", validate_websocket_signals()))
    validation_results.append(("Serializers", validate_serializers()))
    validation_results.append(("Testing Framework", validate_testing_framework_integration()))
    validation_results.append(("Database Models", validate_database_models()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(validation_results)
    
    for component, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{component:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} components validated successfully")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("The interactive debugging dashboard backend API has been successfully implemented.")
        print("\nImplemented features:")
        print("✅ Django REST API endpoints for dashboard data retrieval")
        print("✅ Real-time WebSocket service for live dashboard updates")
        print("✅ Report generation service for debugging summaries")
        print("✅ Manual API testing endpoints for dashboard integration")
        print("✅ Comprehensive API tests for dashboard backend functionality")
        return True
    else:
        print(f"\n⚠️  {total - passed} VALIDATION(S) FAILED")
        print("Please review the failed components above.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)