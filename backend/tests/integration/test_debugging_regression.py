"""
Automated Regression Testing for System Health Monitoring

This module contains automated regression tests to ensure the debugging system
maintains functionality and performance over time.

Requirements: 7.1, 7.2, 7.3
"""

import pytest
import uuid
import time
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.test.utils import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from apps.debugging.models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold,
    FrontendRoute, APICallDiscovery
)
from apps.debugging.services import WorkflowTracingEngine
from apps.debugging.route_discovery import RouteDiscoveryService
from apps.products.models import Product, Category


User = get_user_model()


class SystemHealthRegressionTestCase(TransactionTestCase):
    """Base test case for system health regression testing"""
    
    def setUp(self):
        """Set up test environment for regression testing"""
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            price=99.99,
            category=self.category,
            stock_quantity=10
        )
        
        # Set up baseline performance thresholds
        self.setup_baseline_thresholds()
    
    def setup_baseline_thresholds(self):
        """Set up baseline performance thresholds for regression testing"""
        baseline_thresholds = [
            # API Response Time Baselines
            ('response_time', 'api', 'WorkflowSessionViewSet', 150.0, 300.0),
            ('response_time', 'api', 'ErrorLogViewSet', 100.0, 200.0),
            ('response_time', 'api', 'SystemHealthViewSet', 50.0, 100.0),
            
            # Database Performance Baselines
            ('query_count', 'database', 'WorkflowSession', 3.0, 6.0),
            ('response_time', 'database', 'TraceStep', 25.0, 50.0),
            
            # System Resource Baselines
            ('memory_usage', 'system', 'WorkflowTracing', 50.0, 100.0),
            ('cpu_usage', 'system', 'DebuggingSystem', 20.0, 40.0),
        ]
        
        for metric_name, layer, component, warning, critical in baseline_thresholds:
            PerformanceThreshold.objects.get_or_create(
                metric_name=metric_name,
                layer=layer,
                component=component,
                defaults={
                    'warning_threshold': warning,
                    'critical_threshold': critical,
                    'enabled': True
                }
            )
    
    def create_baseline_data(self):
        """Create baseline data for regression testing"""
        # Create workflow sessions
        for i in range(20):
            session = WorkflowSession.objects.create(
                workflow_type='login' if i % 2 == 0 else 'product_fetch',
                user=self.regular_user,
                status='completed',
                metadata={'baseline_data': True, 'session_id': i}
            )
            
            # Add trace steps
            for j in range(5):
                TraceStep.objects.create(
                    workflow_session=session,
                    layer='api' if j % 2 == 0 else 'database',
                    component=f'Component{j}',
                    operation=f'operation_{j}',
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration_ms=50 + j * 10,
                    status='completed'
                )
        
        # Create error logs
        for i in range(10):
            ErrorLog.objects.create(
                layer='api',
                component='TestComponent',
                error_type='TestError',
                error_message=f'Baseline test error {i}',
                severity='warning' if i % 2 == 0 else 'error'
            )
        
        # Create performance snapshots
        for i in range(30):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='TestComponent',
                metric_name='response_time',
                metric_value=100 + i * 5
            )
    
    def measure_api_performance(self, url, method='GET', data=None):
        """Measure API endpoint performance"""
        start_time = time.perf_counter()
        
        if method == 'GET':
            response = self.client.get(url)
        elif method == 'POST':
            response = self.client.post(url, data or {})
        elif method == 'PUT':
            response = self.client.put(url, data or {})
        elif method == 'DELETE':
            response = self.client.delete(url)
        
        end_time = time.perf_counter()
        response_time = (end_time - start_time) * 1000  # ms
        
        return response, response_time
    
    def assert_no_performance_regression(self, current_value, baseline_value, metric_name, tolerance=20):
        """Assert that performance hasn't regressed beyond tolerance"""
        if baseline_value == 0:
            return  # Skip if no baseline
        
        regression_percent = ((current_value - baseline_value) / baseline_value) * 100
        
        self.assertLessEqual(
            regression_percent,
            tolerance,
            f"{metric_name} performance regression detected: "
            f"{regression_percent:.2f}% increase (current: {current_value}, baseline: {baseline_value})"
        )
    
    def get_baseline_performance(self, metric_name, layer, component):
        """Get baseline performance for comparison"""
        threshold = PerformanceThreshold.objects.filter(
            metric_name=metric_name,
            layer=layer,
            component=component
        ).first()
        
        if threshold:
            # Use warning threshold as baseline
            return threshold.warning_threshold
        
        return None


class WorkflowTracingRegressionTest(SystemHealthRegressionTestCase):
    """Regression tests for workflow tracing functionality"""
    
    def test_workflow_session_creation_regression(self):
        """Test that workflow session creation hasn't regressed
        
        Requirements: 7.1 - Workflow tracing regression testing
        """
        self.client.force_authenticate(user=self.regular_user)
        
        # Measure current performance
        url = reverse('debugging:workflowsession-list')
        response, response_time = self.measure_api_performance(
            url, 'POST', {
                'workflow_type': 'login',
                'metadata': {'regression_test': True}
            }
        )
        
        # Get baseline performance
        baseline = self.get_baseline_performance('response_time', 'api', 'WorkflowSessionViewSet')
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertIn('correlation_id', response.data)
        
        if baseline:
            self.assert_no_performance_regression(
                response_time, baseline, 'workflow_session_creation'
            )
        
        # Verify workflow session was created correctly
        correlation_id = response.data['correlation_id']
        session = WorkflowSession.objects.get(correlation_id=correlation_id)
        self.assertEqual(session.workflow_type, 'login')
        self.assertEqual(session.user, self.regular_user)
    
    def test_trace_step_creation_regression(self):
        """Test that trace step creation hasn't regressed
        
        Requirements: 7.1 - Trace step regression testing
        """
        # Create workflow session
        session = WorkflowSession.objects.create(
            workflow_type='product_fetch',
            user=self.regular_user,
            status='in_progress'
        )
        
        self.client.force_authenticate(user=self.regular_user)
        
        # Measure trace step creation performance
        url = reverse('debugging:tracestep-list')
        response, response_time = self.measure_api_performance(
            url, 'POST', {
                'workflow_session': session.id,
                'layer': 'api',
                'component': 'ProductViewSet',
                'operation': 'list_products',
                'start_time': datetime.now().isoformat(),
                'metadata': {'regression_test': True}
            }
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        
        # Verify trace step was created
        trace_step = TraceStep.objects.get(id=response.data['id'])
        self.assertEqual(trace_step.workflow_session, session)
        self.assertEqual(trace_step.layer, 'api')
        self.assertEqual(trace_step.component, 'ProductViewSet')
    
    def test_workflow_completion_regression(self):
        """Test that workflow completion analysis hasn't regressed
        
        Requirements: 7.1 - Workflow completion regression testing
        """
        # Create workflow with trace steps
        engine = WorkflowTracingEngine()
        session = engine.start_workflow('checkout', user=self.regular_user)
        
        # Add multiple trace steps
        for i in range(5):
            engine.trace_step(
                layer='api',
                component=f'Component{i}',
                operation=f'operation_{i}',
                metadata={'step': i}
            )
        
        # Measure completion performance
        start_time = time.perf_counter()
        analysis = engine.complete_workflow()
        end_time = time.perf_counter()
        
        completion_time = (end_time - start_time) * 1000  # ms
        
        # Assertions
        self.assertIsNotNone(analysis)
        self.assertIn('total_duration_ms', analysis)
        self.assertIn('step_count', analysis)
        self.assertEqual(analysis['step_count'], 5)
        
        # Performance regression check
        baseline = self.get_baseline_performance('response_time', 'api', 'WorkflowTracingEngine')
        if baseline:
            self.assert_no_performance_regression(
                completion_time, baseline, 'workflow_completion'
            )


class APIEndpointRegressionTest(SystemHealthRegressionTestCase):
    """Regression tests for debugging API endpoints"""
    
    def test_system_health_endpoint_regression(self):
        """Test that system health endpoint hasn't regressed
        
        Requirements: 7.2 - System health regression testing
        """
        self.create_baseline_data()
        self.client.force_authenticate(user=self.admin_user)
        
        # Measure system health endpoint performance
        url = reverse('debugging:systemhealth-list')
        response, response_time = self.measure_api_performance(url)
        
        # Get baseline performance
        baseline = self.get_baseline_performance('response_time', 'api', 'SystemHealthViewSet')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('overall_status', response.data)
        self.assertIn('layers', response.data)
        
        # Verify expected data structure
        expected_fields = [
            'overall_status', 'active_workflows', 'recent_errors',
            'performance_alerts', 'layers', 'timestamp'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Performance regression check
        if baseline:
            self.assert_no_performance_regression(
                response_time, baseline, 'system_health_endpoint'
            )
    
    def test_workflow_stats_endpoint_regression(self):
        """Test that workflow stats endpoint hasn't regressed
        
        Requirements: 7.2 - Workflow stats regression testing
        """
        self.create_baseline_data()
        self.client.force_authenticate(user=self.admin_user)
        
        # Measure workflow stats performance
        url = reverse('debugging:workflowsession-stats')
        response, response_time = self.measure_api_performance(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify expected data structure
        expected_fields = [
            'total_workflows', 'completed_workflows', 'failed_workflows',
            'average_duration_ms', 'workflow_types', 'recent_activity'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Verify data accuracy
        self.assertEqual(response.data['total_workflows'], 20)  # From baseline data
        self.assertGreater(response.data['completed_workflows'], 0)
    
    def test_error_log_endpoint_regression(self):
        """Test that error log endpoints haven't regressed
        
        Requirements: 7.2 - Error logging regression testing
        """
        self.create_baseline_data()
        self.client.force_authenticate(user=self.admin_user)
        
        # Test error log list endpoint
        url = reverse('debugging:errorlog-list')
        response, response_time = self.measure_api_performance(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # From baseline data
        
        # Test error log creation
        create_response, create_time = self.measure_api_performance(
            url, 'POST', {
                'layer': 'frontend',
                'component': 'TestComponent',
                'severity': 'error',
                'error_type': 'RegressionTestError',
                'error_message': 'Regression test error message'
            }
        )
        
        self.assertEqual(create_response.status_code, 201)
        
        # Test error summary endpoint
        summary_url = reverse('debugging:errorlog-summary')
        summary_response, summary_time = self.measure_api_performance(summary_url)
        
        self.assertEqual(summary_response.status_code, 200)
        self.assertIn('total_errors', summary_response.data)
        self.assertIn('severity_distribution', summary_response.data)


class DatabaseRegressionTest(SystemHealthRegressionTestCase):
    """Regression tests for database operations"""
    
    def test_database_query_performance_regression(self):
        """Test that database query performance hasn't regressed
        
        Requirements: 7.3 - Database performance regression testing
        """
        self.create_baseline_data()
        
        # Test workflow session queries
        def query_workflow_sessions():
            return list(WorkflowSession.objects.select_related('user').all()[:10])
        
        # Measure query performance
        queries_before = len(connection.queries)
        start_time = time.perf_counter()
        
        results = query_workflow_sessions()
        
        end_time = time.perf_counter()
        queries_after = len(connection.queries)
        
        query_time = (end_time - start_time) * 1000  # ms
        query_count = queries_after - queries_before
        
        # Assertions
        self.assertEqual(len(results), 10)
        self.assertLessEqual(query_count, 2, "Should use select_related to minimize queries")
        
        # Performance regression check
        baseline_time = self.get_baseline_performance('response_time', 'database', 'WorkflowSession')
        baseline_count = self.get_baseline_performance('query_count', 'database', 'WorkflowSession')
        
        if baseline_time:
            self.assert_no_performance_regression(
                query_time, baseline_time, 'database_query_time'
            )
        
        if baseline_count:
            self.assertLessEqual(
                query_count, baseline_count,
                f"Query count regression: {query_count} > {baseline_count}"
            )
    
    def test_database_aggregation_regression(self):
        """Test that database aggregations haven't regressed
        
        Requirements: 7.3 - Database aggregation regression testing
        """
        self.create_baseline_data()
        
        # Test trace step aggregations
        from django.db.models import Avg, Count, Max, Min
        
        def aggregate_trace_steps():
            return TraceStep.objects.aggregate(
                avg_duration=Avg('duration_ms'),
                total_steps=Count('id'),
                max_duration=Max('duration_ms'),
                min_duration=Min('duration_ms')
            )
        
        # Measure aggregation performance
        start_time = time.perf_counter()
        results = aggregate_trace_steps()
        end_time = time.perf_counter()
        
        aggregation_time = (end_time - start_time) * 1000  # ms
        
        # Assertions
        self.assertIsNotNone(results['avg_duration'])
        self.assertGreater(results['total_steps'], 0)
        
        # Performance regression check
        baseline = self.get_baseline_performance('response_time', 'database', 'TraceStep')
        if baseline:
            self.assert_no_performance_regression(
                aggregation_time, baseline, 'database_aggregation'
            )


class RouteDiscoveryRegressionTest(SystemHealthRegressionTestCase):
    """Regression tests for route discovery functionality"""
    
    def test_route_discovery_accuracy_regression(self):
        """Test that route discovery accuracy hasn't regressed
        
        Requirements: 1.1, 1.2 - Route discovery regression testing
        """
        # Create some test routes
        test_routes = [
            {
                'path': '/products',
                'route_type': 'page',
                'component_path': 'app/products/page.tsx',
                'component_name': 'ProductsPage'
            },
            {
                'path': '/api/products',
                'route_type': 'api',
                'component_path': 'app/api/products/route.ts',
                'component_name': 'ProductsAPI'
            }
        ]
        
        for route_data in test_routes:
            FrontendRoute.objects.create(**route_data)
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test route discovery results endpoint
        url = reverse('debugging:routediscovery-results')
        response, response_time = self.measure_api_performance(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('routes', response.data)
        self.assertIn('totalRoutes', response.data)
        
        # Verify route discovery accuracy
        self.assertGreaterEqual(response.data['totalRoutes'], 2)
    
    def test_api_call_discovery_regression(self):
        """Test that API call discovery hasn't regressed
        
        Requirements: 1.2, 1.3 - API call discovery regression testing
        """
        # Create test route with API calls
        route = FrontendRoute.objects.create(
            path='/products',
            route_type='page',
            component_path='app/products/page.tsx',
            component_name='ProductsPage'
        )
        
        # Create test API calls
        api_calls = [
            {
                'frontend_route': route,
                'method': 'GET',
                'endpoint': '/api/products',
                'component_file': 'components/ProductList.tsx',
                'requires_authentication': False
            },
            {
                'frontend_route': route,
                'method': 'POST',
                'endpoint': '/api/cart/add',
                'component_file': 'components/ProductCard.tsx',
                'requires_authentication': True
            }
        ]
        
        for api_call_data in api_calls:
            APICallDiscovery.objects.create(**api_call_data)
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test API call discovery endpoint
        url = reverse('debugging:apicalldiscovery-list')
        response, response_time = self.measure_api_performance(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify API call data structure
        for api_call in response.data['results']:
            required_fields = ['method', 'endpoint', 'component_file', 'requires_authentication']
            for field in required_fields:
                self.assertIn(field, api_call)


class ErrorHandlingRegressionTest(SystemHealthRegressionTestCase):
    """Regression tests for error handling functionality"""
    
    def test_error_correlation_regression(self):
        """Test that error correlation hasn't regressed
        
        Requirements: 6.1, 6.5 - Error correlation regression testing
        """
        # Create workflow with correlation ID
        correlation_id = uuid.uuid4()
        session = WorkflowSession.objects.create(
            correlation_id=correlation_id,
            workflow_type='login',
            user=self.regular_user,
            status='failed'
        )
        
        # Create correlated errors
        error_types = ['ValidationError', 'AuthenticationError', 'DatabaseError']
        for i, error_type in enumerate(error_types):
            ErrorLog.objects.create(
                correlation_id=correlation_id,
                layer='api',
                component=f'Component{i}',
                error_type=error_type,
                error_message=f'Correlated error {i}',
                severity='error'
            )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test error correlation query
        url = reverse('debugging:errorlog-list')
        response = self.client.get(url, {'correlation_id': str(correlation_id)})
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        
        # Verify all errors have the same correlation ID
        for error in response.data['results']:
            self.assertEqual(error['correlation_id'], str(correlation_id))
    
    def test_error_severity_classification_regression(self):
        """Test that error severity classification hasn't regressed
        
        Requirements: 6.2, 6.3 - Error severity regression testing
        """
        # Create errors with different severities
        severities = ['debug', 'info', 'warning', 'error', 'critical']
        for severity in severities:
            ErrorLog.objects.create(
                layer='api',
                component='TestComponent',
                error_type='TestError',
                error_message=f'Test {severity} message',
                severity=severity
            )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test error summary endpoint
        url = reverse('debugging:errorlog-summary')
        response = self.client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('severity_distribution', response.data)
        
        # Verify all severities are represented
        severity_dist = response.data['severity_distribution']
        for severity in severities:
            self.assertIn(severity, severity_dist)
            self.assertGreater(severity_dist[severity], 0)


@pytest.mark.regression
class FullSystemRegressionTest(SystemHealthRegressionTestCase):
    """Comprehensive regression tests for the entire debugging system"""
    
    def test_end_to_end_system_regression(self):
        """Test complete system functionality hasn't regressed
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3 - Full system regression
        """
        self.client.force_authenticate(user=self.regular_user)
        
        # 1. Create workflow session
        workflow_url = reverse('debugging:workflowsession-list')
        workflow_response = self.client.post(workflow_url, {
            'workflow_type': 'checkout',
            'metadata': {'regression_test': 'full_system'}
        })
        
        self.assertEqual(workflow_response.status_code, 201)
        correlation_id = workflow_response.data['correlation_id']
        
        # 2. Add trace steps
        trace_url = reverse('debugging:tracestep-list')
        for i in range(3):
            trace_response = self.client.post(trace_url, {
                'workflow_session': workflow_response.data['id'],
                'layer': 'api',
                'component': f'Component{i}',
                'operation': f'operation_{i}',
                'start_time': datetime.now().isoformat(),
                'metadata': {'step': i}
            })
            self.assertEqual(trace_response.status_code, 201)
        
        # 3. Log performance metrics
        metrics_url = reverse('debugging:performancesnapshot-list')
        metrics_response = self.client.post(metrics_url, {
            'correlation_id': correlation_id,
            'layer': 'api',
            'component': 'TestComponent',
            'metric_name': 'response_time',
            'metric_value': 150.5
        })
        self.assertEqual(metrics_response.status_code, 201)
        
        # 4. Log errors
        error_url = reverse('debugging:errorlog-list')
        error_response = self.client.post(error_url, {
            'correlation_id': correlation_id,
            'layer': 'api',
            'component': 'TestComponent',
            'severity': 'warning',
            'error_type': 'TestWarning',
            'error_message': 'Test warning message'
        })
        self.assertEqual(error_response.status_code, 201)
        
        # 5. Complete workflow
        complete_url = reverse('debugging:workflowsession-complete', kwargs={'pk': workflow_response.data['id']})
        complete_response = self.client.post(complete_url)
        self.assertEqual(complete_response.status_code, 200)
        
        # 6. Verify system health
        health_url = reverse('debugging:systemhealth-list')
        health_response = self.client.get(health_url)
        self.assertEqual(health_response.status_code, 200)
        
        # 7. Verify all data is properly correlated
        session = WorkflowSession.objects.get(correlation_id=correlation_id)
        self.assertEqual(session.status, 'completed')
        
        trace_steps = TraceStep.objects.filter(workflow_session=session)
        self.assertEqual(trace_steps.count(), 3)
        
        metrics = PerformanceSnapshot.objects.filter(correlation_id=correlation_id)
        self.assertEqual(metrics.count(), 1)
        
        errors = ErrorLog.objects.filter(correlation_id=correlation_id)
        self.assertEqual(errors.count(), 1)
        
        # System should be healthy after successful workflow
        self.assertIn(health_response.data['overall_status'], ['healthy', 'degraded'])
    
    def test_system_performance_under_load_regression(self):
        """Test that system performance under load hasn't regressed
        
        Requirements: 7.1, 7.2, 7.3 - Load performance regression
        """
        import concurrent.futures
        
        self.client.force_authenticate(user=self.regular_user)
        
        def create_workflow_with_tracing():
            """Create a complete workflow with tracing"""
            # Create workflow
            workflow_url = reverse('debugging:workflowsession-list')
            workflow_response = self.client.post(workflow_url, {
                'workflow_type': 'product_fetch',
                'metadata': {'load_test': True}
            })
            
            if workflow_response.status_code != 201:
                return False
            
            # Add trace step
            trace_url = reverse('debugging:tracestep-list')
            trace_response = self.client.post(trace_url, {
                'workflow_session': workflow_response.data['id'],
                'layer': 'api',
                'component': 'ProductViewSet',
                'operation': 'list_products',
                'start_time': datetime.now().isoformat()
            })
            
            return trace_response.status_code == 201
        
        # Run concurrent workflows
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(create_workflow_with_tracing) 
                for _ in range(20)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Assertions
        successful_workflows = sum(results)
        self.assertEqual(successful_workflows, 20, "Not all workflows completed successfully")
        
        # Performance assertion - should complete 20 workflows in under 10 seconds
        self.assertLess(total_time, 10, f"Load test took too long: {total_time:.2f}s")
        
        # Verify system health after load test
        health_url = reverse('debugging:systemhealth-list')
        health_response = self.client.get(health_url)
        self.assertEqual(health_response.status_code, 200)
        
        # System should still be responsive after load test
        self.assertIn(health_response.data['overall_status'], ['healthy', 'degraded'])