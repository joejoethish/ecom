"""
Tests for the interactive debugging dashboard backend API.

This module contains comprehensive tests for all dashboard API endpoints,
including data retrieval, real-time updates, report generation, and manual testing tools.
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold,
    FrontendRoute, APICallDiscovery, RouteDiscoverySession
)
from .dashboard_views import (
    DashboardDataViewSet, ReportGenerationViewSet, 
    ManualAPITestingViewSet, DashboardConfigurationViewSet
)


User = get_user_model()


class DashboardAPITestCase(APITestCase):
    """Base test case for dashboard API tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set up API client with authentication
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test data
        self.create_test_data()
    
    def create_test_data(self):
        """Create test data for dashboard tests"""
        # Create workflow sessions
        self.workflow1 = WorkflowSession.objects.create(
            workflow_type='login',
            user=self.user,
            status='completed',
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() - timedelta(minutes=50)
        )
        
        self.workflow2 = WorkflowSession.objects.create(
            workflow_type='product_fetch',
            user=self.user,
            status='in_progress',
            start_time=timezone.now() - timedelta(minutes=30)
        )
        
        self.workflow3 = WorkflowSession.objects.create(
            workflow_type='cart_update',
            user=self.user,
            status='failed',
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=2) + timedelta(minutes=5)
        )
        
        # Create trace steps
        TraceStep.objects.create(
            workflow_session=self.workflow1,
            layer='frontend',
            component='LoginForm',
            operation='submit_form',
            start_time=self.workflow1.start_time,
            end_time=self.workflow1.start_time + timedelta(seconds=1),
            status='completed',
            duration_ms=1000
        )
        
        TraceStep.objects.create(
            workflow_session=self.workflow1,
            layer='api',
            component='AuthenticationView',
            operation='authenticate_user',
            start_time=self.workflow1.start_time + timedelta(seconds=1),
            end_time=self.workflow1.start_time + timedelta(seconds=3),
            status='completed',
            duration_ms=2000
        )
        
        # Create error logs
        ErrorLog.objects.create(
            correlation_id=self.workflow3.correlation_id,
            layer='api',
            component='CartView',
            severity='error',
            error_type='ValidationError',
            error_message='Invalid product ID',
            user=self.user
        )
        
        ErrorLog.objects.create(
            layer='database',
            component='ProductModel',
            severity='critical',
            error_type='DatabaseError',
            error_message='Connection timeout',
            timestamp=timezone.now() - timedelta(minutes=15)
        )
        
        # Create performance snapshots
        PerformanceSnapshot.objects.create(
            correlation_id=self.workflow1.correlation_id,
            layer='api',
            component='AuthenticationView',
            metric_name='response_time',
            metric_value=250.0,
            threshold_warning=500.0,
            threshold_critical=1000.0
        )
        
        PerformanceSnapshot.objects.create(
            layer='database',
            component='UserModel',
            metric_name='query_count',
            metric_value=5.0,
            threshold_warning=10.0,
            threshold_critical=20.0
        )
        
        # Create performance threshold exceeding metric
        PerformanceSnapshot.objects.create(
            layer='api',
            component='SlowEndpoint',
            metric_name='response_time',
            metric_value=1500.0,
            threshold_warning=500.0,
            threshold_critical=1000.0
        )
        
        # Create frontend routes
        self.route1 = FrontendRoute.objects.create(
            path='/login',
            route_type='page',
            component_path='app/login/page.tsx',
            component_name='LoginPage'
        )
        
        # Create API call discovery
        APICallDiscovery.objects.create(
            frontend_route=self.route1,
            method='POST',
            endpoint='/api/v1/auth/login/',
            component_file='components/LoginForm.tsx',
            requires_authentication=False,
            is_valid=True
        )
        
        # Create route discovery session
        RouteDiscoverySession.objects.create(
            status='completed',
            routes_discovered=10,
            api_calls_discovered=25,
            scan_duration_ms=5000
        )
        
        # Create debug configuration
        DebugConfiguration.objects.create(
            name='dashboard_settings',
            config_type='dashboard_settings',
            enabled=True,
            config_data={
                'refresh_interval': 30,
                'max_workflow_display': 10,
                'enable_realtime_updates': True
            }
        )


class DashboardDataViewSetTests(DashboardAPITestCase):
    """Tests for DashboardDataViewSet"""
    
    def test_get_dashboard_data(self):
        """Test retrieving comprehensive dashboard data"""
        url = reverse('debugging:dashboard-data-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check required fields
        self.assertIn('timestamp', data)
        self.assertIn('system_health', data)
        self.assertIn('active_workflows', data)
        self.assertIn('recent_errors', data)
        self.assertIn('performance_metrics', data)
        self.assertIn('optimization_recommendations', data)
        self.assertIn('workflow_stats', data)
        self.assertIn('route_discovery_status', data)
        
        # Check system health structure
        system_health = data['system_health']
        self.assertIn('overall_status', system_health)
        self.assertIn('active_workflows', system_health)
        self.assertIn('recent_errors', system_health)
        self.assertIn('performance_alerts', system_health)
        self.assertIn('layers', system_health)
        
        # Check workflow stats
        workflow_stats = data['workflow_stats']
        self.assertIn('total_workflows', workflow_stats)
        self.assertIn('completed_workflows', workflow_stats)
        self.assertIn('failed_workflows', workflow_stats)
        self.assertIn('success_rate', workflow_stats)
    
    def test_get_realtime_updates(self):
        """Test retrieving real-time updates"""
        url = reverse('debugging:dashboard-data-realtime-updates')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('new_workflows', data)
        self.assertIn('new_errors', data)
        self.assertIn('new_metrics', data)
        self.assertIn('has_updates', data)
    
    def test_get_realtime_updates_with_since_parameter(self):
        """Test retrieving real-time updates with since parameter"""
        since_time = (timezone.now() - timedelta(minutes=10)).isoformat()
        url = reverse('debugging:dashboard-data-realtime-updates')
        response = self.client.get(url, {'since': since_time})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('has_updates', data)
    
    def test_dashboard_data_unauthorized(self):
        """Test dashboard data access without authentication"""
        self.client.credentials()  # Remove authentication
        url = reverse('debugging:dashboard-data-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReportGenerationViewSetTests(DashboardAPITestCase):
    """Tests for ReportGenerationViewSet"""
    
    def test_generate_workflow_report(self):
        """Test generating workflow analysis report"""
        url = reverse('debugging:reports-generate-workflow-report')
        data = {'correlation_id': str(self.workflow1.correlation_id)}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_data = response.json()
        
        self.assertEqual(report_data['report_type'], 'workflow_analysis')
        self.assertIn('generated_at', report_data)
        self.assertIn('workflow', report_data)
        self.assertIn('trace_steps', report_data)
        self.assertIn('errors', report_data)
        self.assertIn('performance_metrics', report_data)
        self.assertIn('summary', report_data)
        
        # Check workflow data
        workflow_data = report_data['workflow']
        self.assertEqual(workflow_data['correlation_id'], str(self.workflow1.correlation_id))
        self.assertEqual(workflow_data['workflow_type'], 'login')
        self.assertEqual(workflow_data['status'], 'completed')
    
    def test_generate_workflow_report_not_found(self):
        """Test generating report for non-existent workflow"""
        url = reverse('debugging:reports-generate-workflow-report')
        data = {'correlation_id': str(uuid.uuid4())}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_generate_workflow_report_missing_correlation_id(self):
        """Test generating workflow report without correlation_id"""
        url = reverse('debugging:reports-generate-workflow-report')
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_generate_system_health_report(self):
        """Test generating system health report"""
        url = reverse('debugging:reports-generate-system-health-report')
        data = {'time_range': '24h'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_data = response.json()
        
        self.assertEqual(report_data['report_type'], 'system_health')
        self.assertIn('generated_at', report_data)
        self.assertIn('time_range', report_data)
        self.assertIn('workflow_stats', report_data)
        self.assertIn('error_stats', report_data)
        self.assertIn('performance_stats', report_data)
        self.assertIn('overall_health', report_data)
    
    def test_generate_performance_report(self):
        """Test generating performance analysis report"""
        url = reverse('debugging:reports-generate-performance-report')
        data = {
            'layer': 'api',
            'time_range': '24h'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_data = response.json()
        
        self.assertEqual(report_data['report_type'], 'performance_analysis')
        self.assertIn('generated_at', report_data)
        self.assertIn('filters', report_data)
        self.assertIn('metric_statistics', report_data)
        self.assertIn('total_metrics', report_data)
        self.assertIn('performance_alerts', report_data)
        
        # Check filters
        filters = report_data['filters']
        self.assertEqual(filters['layer'], 'api')


class ManualAPITestingViewSetTests(DashboardAPITestCase):
    """Tests for ManualAPITestingViewSet"""
    
    @patch('apps.debugging.testing_framework.APITestingFramework.test_single_endpoint')
    def test_test_endpoint(self, mock_test_endpoint):
        """Test manual API endpoint testing"""
        # Mock the test result
        mock_test_endpoint.return_value = {
            'success': True,
            'status_code': 200,
            'response_time_ms': 150.0,
            'response_data': {'message': 'success'},
            'headers': {'Content-Type': 'application/json'},
            'error_message': None,
            'status_match': True,
            'expected_status': 200
        }
        
        url = reverse('debugging:manual-testing-test-endpoint')
        data = {
            'method': 'GET',
            'endpoint': '/api/v1/products/',
            'expected_status': 200
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_data = response.json()
        
        self.assertIn('test_id', result_data)
        self.assertIn('timestamp', result_data)
        self.assertIn('request', result_data)
        self.assertIn('response', result_data)
        self.assertIn('success', result_data)
        self.assertTrue(result_data['success'])
        
        # Verify mock was called
        mock_test_endpoint.assert_called_once()
    
    def test_test_endpoint_invalid_data(self):
        """Test manual API testing with invalid data"""
        url = reverse('debugging:manual-testing-test-endpoint')
        data = {
            'method': 'INVALID',
            'endpoint': '/api/v1/products/'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('apps.debugging.testing_framework.APITestingFramework.test_workflow_sequence')
    def test_test_workflow(self, mock_test_workflow):
        """Test manual workflow testing"""
        # Mock the workflow test result
        mock_test_workflow.return_value = {
            'success': True,
            'workflow_type': 'login',
            'total_time_ms': 2500.0,
            'steps': [
                {'step_name': 'login_request', 'success': True},
                {'step_name': 'token_validation', 'success': True}
            ],
            'step_count': 2,
            'failed_steps': [],
            'error_message': None
        }
        
        url = reverse('debugging:manual-testing-test-workflow')
        data = {
            'workflow_type': 'login',
            'test_data': {
                'username': 'testuser',
                'password': 'testpass123'
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_data = response.json()
        
        self.assertIn('test_id', result_data)
        self.assertIn('timestamp', result_data)
        self.assertIn('workflow_type', result_data)
        self.assertIn('result', result_data)
        self.assertIn('success', result_data)
        self.assertTrue(result_data['success'])
        
        # Verify mock was called
        mock_test_workflow.assert_called_once()
    
    def test_test_workflow_missing_type(self):
        """Test workflow testing without workflow_type"""
        url = reverse('debugging:manual-testing-test-workflow')
        data = {'test_data': {}}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_available_endpoints(self):
        """Test retrieving available API endpoints"""
        url = reverse('debugging:manual-testing-available-endpoints')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('endpoints', data)
        self.assertIn('total_count', data)
        
        # Check that our test endpoint is included
        endpoints = data['endpoints']
        self.assertTrue(any(
            endpoint['endpoint'] == '/api/v1/auth/login/' 
            for endpoint in endpoints
        ))
    
    def test_get_test_history(self):
        """Test retrieving test history"""
        url = reverse('debugging:manual-testing-test-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('test_history', data)
        self.assertIn('message', data)


class DashboardConfigurationViewSetTests(DashboardAPITestCase):
    """Tests for DashboardConfigurationViewSet"""
    
    def test_get_dashboard_configuration(self):
        """Test retrieving dashboard configuration"""
        url = reverse('debugging:dashboard-config-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('configuration', data)
        self.assertIn('last_updated', data)
        
        # Check configuration data
        config = data['configuration']
        self.assertIn('refresh_interval', config)
        self.assertIn('max_workflow_display', config)
        self.assertIn('enable_realtime_updates', config)
    
    def test_update_dashboard_configuration(self):
        """Test updating dashboard configuration"""
        url = reverse('debugging:dashboard-config-update-configuration')
        data = {
            'name': 'test_dashboard_settings',
            'config_data': {
                'refresh_interval': 60,
                'max_workflow_display': 20,
                'enable_realtime_updates': False
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_data = response.json()
        
        self.assertIn('success', result_data)
        self.assertIn('config_id', result_data)
        self.assertIn('created', result_data)
        self.assertIn('updated_at', result_data)
        self.assertTrue(result_data['success'])


class DashboardHealthCheckTests(DashboardAPITestCase):
    """Tests for dashboard health check endpoint"""
    
    def test_dashboard_health_check(self):
        """Test dashboard health check endpoint"""
        url = reverse('debugging:dashboard-health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('services', data)
        
        self.assertEqual(data['status'], 'healthy')
        
        # Check services
        services = data['services']
        self.assertIn('database', services)
        self.assertIn('api', services)
        self.assertIn('dashboard', services)
    
    def test_dashboard_health_check_unauthorized(self):
        """Test health check without authentication"""
        self.client.credentials()  # Remove authentication
        url = reverse('debugging:dashboard-health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardIntegrationTests(DashboardAPITestCase):
    """Integration tests for dashboard functionality"""
    
    def test_dashboard_data_consistency(self):
        """Test that dashboard data is consistent across endpoints"""
        # Get dashboard data
        dashboard_url = reverse('debugging:dashboard-data-list')
        dashboard_response = self.client.get(dashboard_url)
        dashboard_data = dashboard_response.json()
        
        # Get system health separately
        health_url = reverse('debugging:system-health-list')
        health_response = self.client.get(health_url)
        health_data = health_response.json()
        
        # Compare system health data
        dashboard_health = dashboard_data['system_health']
        
        # Both should report the same number of active workflows
        self.assertEqual(
            dashboard_health['active_workflows'],
            1  # We have one in_progress workflow
        )
    
    def test_workflow_report_generation_integration(self):
        """Test complete workflow report generation"""
        # Generate workflow report
        report_url = reverse('debugging:reports-generate-workflow-report')
        report_data = {'correlation_id': str(self.workflow1.correlation_id)}
        report_response = self.client.post(report_url, report_data, format='json')
        
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)
        report = report_response.json()
        
        # Verify report contains all expected data
        self.assertEqual(len(report['trace_steps']), 2)  # We created 2 trace steps
        self.assertEqual(len(report['performance_metrics']), 1)  # 1 metric for this workflow
        
        # Check summary calculations
        summary = report['summary']
        self.assertEqual(summary['total_steps'], 2)
        self.assertEqual(summary['completed_steps'], 2)
        self.assertEqual(summary['failed_steps'], 0)
    
    def test_manual_testing_integration(self):
        """Test manual API testing integration"""
        # First, get available endpoints
        endpoints_url = reverse('debugging:manual-testing-available-endpoints')
        endpoints_response = self.client.get(endpoints_url)
        endpoints_data = endpoints_response.json()
        
        self.assertTrue(len(endpoints_data['endpoints']) > 0)
        
        # Find a test endpoint
        test_endpoint = None
        for endpoint in endpoints_data['endpoints']:
            if endpoint['endpoint'] == '/api/v1/auth/login/':
                test_endpoint = endpoint
                break
        
        self.assertIsNotNone(test_endpoint)
        
        # Test the endpoint (this will use the mocked testing framework)
        with patch('apps.debugging.testing_framework.APITestingFramework.test_single_endpoint') as mock_test:
            mock_test.return_value = {
                'success': True,
                'status_code': 200,
                'response_time_ms': 100.0,
                'response_data': {'message': 'test'},
                'headers': {},
                'error_message': None,
                'status_match': True,
                'expected_status': 200
            }
            
            test_url = reverse('debugging:manual-testing-test-endpoint')
            test_data = {
                'method': 'POST',
                'endpoint': test_endpoint['endpoint'],
                'payload': {'username': 'test', 'password': 'test'},
                'expected_status': 200
            }
            test_response = self.client.post(test_url, test_data, format='json')
            
            self.assertEqual(test_response.status_code, status.HTTP_200_OK)
            result = test_response.json()
            self.assertTrue(result['success'])