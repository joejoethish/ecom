from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
import uuid

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold
)
from .utils import WorkflowTracer, PerformanceMonitor, ErrorLogger

User = get_user_model()


class DebuggingModelsTestCase(TestCase):
    """Test cases for debugging system models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_workflow_session_creation(self):
        """Test creating a workflow session"""
        workflow = WorkflowSession.objects.create(
            workflow_type='login',
            user=self.user,
            metadata={'test': 'data'}
        )
        
        self.assertIsNotNone(workflow.correlation_id)
        self.assertEqual(workflow.workflow_type, 'login')
        self.assertEqual(workflow.user, self.user)
        self.assertEqual(workflow.status, 'in_progress')
    
    def test_trace_step_creation(self):
        """Test creating trace steps"""
        workflow = WorkflowSession.objects.create(
            workflow_type='product_fetch',
            user=self.user
        )
        
        trace_step = TraceStep.objects.create(
            workflow_session=workflow,
            layer='api',
            component='ProductViewSet',
            operation='list_products',
            start_time=timezone.now()
        )
        
        self.assertEqual(trace_step.workflow_session, workflow)
        self.assertEqual(trace_step.layer, 'api')
        self.assertEqual(trace_step.status, 'started')
    
    def test_performance_snapshot_creation(self):
        """Test creating performance snapshots"""
        snapshot = PerformanceSnapshot.objects.create(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=150.5,
            threshold_warning=200.0,
            threshold_critical=500.0
        )
        
        self.assertEqual(snapshot.layer, 'api')
        self.assertEqual(snapshot.metric_value, 150.5)
        self.assertFalse(snapshot.metric_value >= snapshot.threshold_warning)
    
    def test_error_log_creation(self):
        """Test creating error logs"""
        error_log = ErrorLog.objects.create(
            layer='api',
            component='ProductViewSet',
            severity='error',
            error_type='ValidationError',
            error_message='Invalid product data',
            user=self.user
        )
        
        self.assertEqual(error_log.layer, 'api')
        self.assertEqual(error_log.severity, 'error')
        self.assertFalse(error_log.resolved)


class DebuggingUtilsTestCase(TestCase):
    """Test cases for debugging utility classes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create performance threshold
        PerformanceThreshold.objects.create(
            metric_name='response_time',
            layer='api',
            component='',
            warning_threshold=200.0,
            critical_threshold=500.0
        )
    
    def test_workflow_tracer(self):
        """Test WorkflowTracer utility"""
        tracer = WorkflowTracer()
        
        # Start workflow
        workflow = tracer.start_workflow(
            workflow_type='login',
            user=self.user,
            metadata={'test': 'data'}
        )
        
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.workflow_type, 'login')
        self.assertEqual(workflow.correlation_id, tracer.correlation_id)
        
        # Add trace step
        trace_step = tracer.add_trace_step(
            workflow_session=workflow,
            layer='api',
            component='AuthViewSet',
            operation='login'
        )
        
        self.assertEqual(trace_step.workflow_session, workflow)
        self.assertEqual(trace_step.status, 'started')
        
        # Complete trace step
        completed_step = tracer.complete_trace_step(
            trace_step,
            metadata={'success': True}
        )
        
        self.assertEqual(completed_step.status, 'completed')
        self.assertIsNotNone(completed_step.end_time)
        self.assertIsNotNone(completed_step.duration_ms)
    
    def test_performance_monitor(self):
        """Test PerformanceMonitor utility"""
        correlation_id = uuid.uuid4()
        
        # Record metric
        snapshot = PerformanceMonitor.record_metric(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=150.0,
            correlation_id=correlation_id
        )
        
        self.assertEqual(snapshot.metric_value, 150.0)
        self.assertEqual(snapshot.correlation_id, correlation_id)
        self.assertEqual(snapshot.threshold_warning, 200.0)
        
        # Check thresholds
        threshold_check = PerformanceMonitor.check_thresholds(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=300.0
        )
        
        self.assertEqual(threshold_check['status'], 'warning')
    
    def test_error_logger(self):
        """Test ErrorLogger utility"""
        correlation_id = uuid.uuid4()
        
        # Log error
        error_log = ErrorLogger.log_error(
            layer='api',
            component='ProductViewSet',
            error_type='ValidationError',
            error_message='Invalid product data',
            correlation_id=correlation_id,
            user=self.user
        )
        
        self.assertEqual(error_log.error_type, 'ValidationError')
        self.assertEqual(error_log.correlation_id, correlation_id)
        self.assertEqual(error_log.user, self.user)


class DebuggingAPITestCase(APITestCase):
    """Test cases for debugging API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.workflow = WorkflowSession.objects.create(
            workflow_type='login',
            user=self.user
        )
    
    def test_workflow_session_list(self):
        """Test listing workflow sessions"""
        response = self.client.get('/api/v1/debugging/workflow-sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_workflow_session_stats(self):
        """Test workflow session statistics"""
        response = self.client.get('/api/v1/debugging/workflow-sessions/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_workflows', response.data)
        self.assertIn('workflow_types', response.data)
    
    def test_system_health(self):
        """Test system health endpoint"""
        response = self.client.get('/api/v1/debugging/system-health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_status', response.data[0])
        self.assertIn('layers', response.data[0])
    
    def test_performance_snapshots(self):
        """Test performance snapshots endpoint"""
        # Create test performance snapshot
        PerformanceSnapshot.objects.create(
            layer='api',
            component='TestComponent',
            metric_name='response_time',
            metric_value=150.0
        )
        
        response = self.client.get('/api/v1/debugging/performance-snapshots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_error_logs(self):
        """Test error logs endpoint"""
        # Create test error log
        ErrorLog.objects.create(
            layer='api',
            component='TestComponent',
            error_type='TestError',
            error_message='Test error message',
            user=self.user
        )
        
        response = self.client.get('/api/v1/debugging/error-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test error summary
        response = self.client.get('/api/v1/debugging/error-logs/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_errors', response.data)