"""
Comprehensive tests for the workflow tracing engine

These tests validate the complete workflow tracing functionality including
session management, step recording, timing analysis, and error tracking.
"""

import uuid
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from ..models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, PerformanceThreshold
)
from ..services import (
    WorkflowSessionManager, TraceStepRecorder, TimingAnalyzer,
    ErrorTracker, WorkflowTracingEngine, WorkflowStepContext
)
from ..database_monitor import (
    DatabaseQueryMonitor, DatabaseOperationTracer, 
    DatabaseHealthMonitor
)


class WorkflowSessionManagerTests(TestCase):
    """Test workflow session management"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.correlation_id = uuid.uuid4()
        self.session_manager = WorkflowSessionManager(self.correlation_id)
    
    def test_start_session(self):
        """Test starting a new workflow session"""
        session = self.session_manager.start_session(
            workflow_type='login',
            user=self.user,
            metadata={'test': 'data'}
        )
        
        self.assertEqual(session.correlation_id, self.correlation_id)
        self.assertEqual(session.workflow_type, 'login')
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.status, 'in_progress')
        self.assertEqual(session.metadata['test'], 'data')
        
        # Verify session is stored in database
        db_session = WorkflowSession.objects.get(correlation_id=self.correlation_id)
        self.assertEqual(db_session.workflow_type, 'login')
    
    def test_get_session(self):
        """Test retrieving an existing session"""
        # Create session first
        original_session = self.session_manager.start_session('product_fetch')
        
        # Create new manager with same correlation ID
        new_manager = WorkflowSessionManager(self.correlation_id)
        retrieved_session = new_manager.get_session()
        
        self.assertEqual(retrieved_session.id, original_session.id)
        self.assertEqual(retrieved_session.correlation_id, self.correlation_id)
    
    def test_complete_session(self):
        """Test completing a workflow session"""
        session = self.session_manager.start_session('checkout')
        
        completed_session = self.session_manager.complete_session(
            metadata={'items': 3, 'total': 99.99}
        )
        
        self.assertEqual(completed_session.status, 'completed')
        self.assertIsNotNone(completed_session.end_time)
        self.assertEqual(completed_session.metadata['items'], 3)
        self.assertEqual(completed_session.metadata['total'], 99.99)
    
    def test_fail_session(self):
        """Test failing a workflow session"""
        session = self.session_manager.start_session('cart_update')
        
        failed_session = self.session_manager.fail_session(
            'Payment processing failed',
            metadata={'error_code': 'PAYMENT_DECLINED'}
        )
        
        self.assertEqual(failed_session.status, 'failed')
        self.assertIsNotNone(failed_session.end_time)
        self.assertEqual(failed_session.metadata['error_message'], 'Payment processing failed')
        self.assertEqual(failed_session.metadata['error_code'], 'PAYMENT_DECLINED')


class TraceStepRecorderTests(TestCase):
    """Test trace step recording functionality"""
    
    def setUp(self):
        self.correlation_id = uuid.uuid4()
        self.session_manager = WorkflowSessionManager(self.correlation_id)
        self.session = self.session_manager.start_session('test_workflow')
        self.step_recorder = TraceStepRecorder(self.session_manager)
    
    def test_start_step(self):
        """Test starting a trace step"""
        step = self.step_recorder.start_step(
            layer='api',
            component='ProductView',
            operation='list_products',
            metadata={'page': 1, 'limit': 20}
        )
        
        self.assertEqual(step.workflow_session, self.session)
        self.assertEqual(step.layer, 'api')
        self.assertEqual(step.component, 'ProductView')
        self.assertEqual(step.operation, 'list_products')
        self.assertEqual(step.status, 'started')
        self.assertEqual(step.metadata['page'], 1)
        self.assertIsNotNone(step.start_time)
    
    def test_complete_step(self):
        """Test completing a trace step"""
        step = self.step_recorder.start_step('database', 'Product', 'query')
        
        # Simulate some processing time
        time.sleep(0.01)
        
        completed_step = self.step_recorder.complete_step(
            'database', 'Product', 'query',
            metadata={'result_count': 50}
        )
        
        self.assertEqual(completed_step.status, 'completed')
        self.assertIsNotNone(completed_step.end_time)
        self.assertIsNotNone(completed_step.duration_ms)
        self.assertGreater(completed_step.duration_ms, 0)
        self.assertEqual(completed_step.metadata['result_count'], 50)
    
    def test_fail_step(self):
        """Test failing a trace step"""
        step = self.step_recorder.start_step('api', 'AuthView', 'authenticate')
        
        failed_step = self.step_recorder.fail_step(
            'api', 'AuthView', 'authenticate',
            'Invalid credentials',
            metadata={'username': 'testuser'}
        )
        
        self.assertEqual(failed_step.status, 'failed')
        self.assertIsNotNone(failed_step.end_time)
        self.assertEqual(failed_step.metadata['error_message'], 'Invalid credentials')
        self.assertEqual(failed_step.metadata['username'], 'testuser')
    
    def test_step_context_manager(self):
        """Test using step as context manager"""
        with self.step_recorder.session_manager.session_manager.trace_step(
            'frontend', 'LoginForm', 'submit'
        ) as step_context:
            # Simulate some work
            time.sleep(0.01)
            step_context.add_metadata({'form_valid': True})
        
        # Verify step was completed
        steps = TraceStep.objects.filter(
            workflow_session=self.session,
            component='LoginForm'
        )
        self.assertEqual(steps.count(), 1)
        
        step = steps.first()
        self.assertEqual(step.status, 'completed')
        self.assertEqual(step.metadata['form_valid'], True)


class TimingAnalyzerTests(TestCase):
    """Test timing analysis functionality"""
    
    def setUp(self):
        self.correlation_id = uuid.uuid4()
        self.session_manager = WorkflowSessionManager(self.correlation_id)
        self.session = self.session_manager.start_session('test_workflow')
        self.timing_analyzer = TimingAnalyzer(self.correlation_id)
        
        # Create some test performance thresholds
        PerformanceThreshold.objects.create(
            metric_name='response_time',
            layer='api',
            warning_threshold=100,
            critical_threshold=500
        )
    
    def test_analyze_workflow_timing_empty(self):
        """Test timing analysis with no steps"""
        analysis = self.timing_analyzer.analyze_workflow_timing()
        
        self.assertEqual(analysis['step_count'], 0)
        self.assertEqual(analysis['workflow_type'], 'test_workflow')
        self.assertIn('layers', analysis)
    
    def test_analyze_workflow_timing_with_steps(self):
        """Test timing analysis with multiple steps"""
        # Create test steps with different durations
        step1 = TraceStep.objects.create(
            workflow_session=self.session,
            layer='frontend',
            component='LoginForm',
            operation='render',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(milliseconds=50),
            duration_ms=50,
            status='completed'
        )
        
        step2 = TraceStep.objects.create(
            workflow_session=self.session,
            layer='api',
            component='AuthView',
            operation='authenticate',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(milliseconds=200),
            duration_ms=200,
            status='completed'
        )
        
        step3 = TraceStep.objects.create(
            workflow_session=self.session,
            layer='database',
            component='User',
            operation='lookup',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(milliseconds=30),
            duration_ms=30,
            status='completed'
        )
        
        analysis = self.timing_analyzer.analyze_workflow_timing()
        
        self.assertEqual(analysis['step_count'], 3)
        self.assertIn('frontend', analysis['layers'])
        self.assertIn('api', analysis['layers'])
        self.assertIn('database', analysis['layers'])
        
        # Check layer statistics
        frontend_stats = analysis['layers']['frontend']
        self.assertEqual(frontend_stats['step_count'], 1)
        self.assertEqual(frontend_stats['total_duration_ms'], 50)
        
        api_stats = analysis['layers']['api']
        self.assertEqual(api_stats['step_count'], 1)
        self.assertEqual(api_stats['total_duration_ms'], 200)
    
    def test_identify_performance_issues(self):
        """Test identification of performance issues"""
        # Create a slow step that exceeds threshold
        TraceStep.objects.create(
            workflow_session=self.session,
            layer='api',
            component='SlowView',
            operation='process',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(milliseconds=600),
            duration_ms=600,
            status='completed'
        )
        
        analysis = self.timing_analyzer.analyze_workflow_timing()
        
        self.assertGreater(len(analysis['performance_issues']), 0)
        
        issue = analysis['performance_issues'][0]
        self.assertEqual(issue['type'], 'critical_threshold_exceeded')
        self.assertEqual(issue['layer'], 'api')
        self.assertEqual(issue['component'], 'SlowView')
        self.assertEqual(issue['duration_ms'], 600)
        self.assertEqual(issue['severity'], 'critical')


class ErrorTrackerTests(TestCase):
    """Test error tracking and correlation"""
    
    def setUp(self):
        self.correlation_id = uuid.uuid4()
        self.error_tracker = ErrorTracker(self.correlation_id)
    
    def test_track_error(self):
        """Test tracking an error"""
        error_log = self.error_tracker.track_error(
            layer='frontend',
            component='LoginForm',
            error_type='ValidationError',
            error_message='Username is required',
            severity='warning',
            metadata={'field': 'username'}
        )
        
        self.assertEqual(error_log.correlation_id, self.correlation_id)
        self.assertEqual(error_log.layer, 'frontend')
        self.assertEqual(error_log.component, 'LoginForm')
        self.assertEqual(error_log.error_type, 'ValidationError')
        self.assertEqual(error_log.severity, 'warning')
        self.assertEqual(error_log.metadata['field'], 'username')
    
    def test_get_correlated_errors(self):
        """Test retrieving correlated errors"""
        # Create multiple errors with same correlation ID
        self.error_tracker.track_error('frontend', 'Form', 'ValidationError', 'Error 1')
        self.error_tracker.track_error('api', 'View', 'AuthError', 'Error 2')
        self.error_tracker.track_error('database', 'Model', 'IntegrityError', 'Error 3')
        
        # Create error with different correlation ID
        other_tracker = ErrorTracker(uuid.uuid4())
        other_tracker.track_error('api', 'View', 'NotFound', 'Other error')
        
        correlated_errors = self.error_tracker.get_correlated_errors()
        
        self.assertEqual(len(correlated_errors), 3)
        for error in correlated_errors:
            self.assertEqual(error.correlation_id, self.correlation_id)
    
    def test_analyze_error_patterns(self):
        """Test error pattern analysis"""
        # Create errors that demonstrate patterns
        self.error_tracker.track_error('frontend', 'Form', 'ValidationError', 'Error 1')
        self.error_tracker.track_error('api', 'View', 'ValidationError', 'Error 2')
        self.error_tracker.track_error('database', 'Model', 'IntegrityError', 'Error 3')
        self.error_tracker.track_error('api', 'View', 'ValidationError', 'Error 4')
        
        analysis = self.error_tracker.analyze_error_patterns()
        
        self.assertEqual(analysis['error_count'], 4)
        self.assertEqual(len(analysis['layers_affected']), 3)
        self.assertIn('frontend', analysis['layers_affected'])
        self.assertIn('api', analysis['layers_affected'])
        self.assertIn('database', analysis['layers_affected'])
        
        # Check error type distribution
        self.assertEqual(analysis['error_types']['ValidationError'], 3)
        self.assertEqual(analysis['error_types']['IntegrityError'], 1)
        
        # Check for patterns
        patterns = analysis['patterns']
        self.assertGreater(len(patterns), 0)
        
        # Should detect cascading errors
        cascading_pattern = next((p for p in patterns if p['type'] == 'cascading_errors'), None)
        self.assertIsNotNone(cascading_pattern)
        
        # Should detect repeated errors
        repeated_pattern = next((p for p in patterns if p['type'] == 'repeated_error'), None)
        self.assertIsNotNone(repeated_pattern)


class WorkflowTracingEngineTests(TestCase):
    """Test the complete workflow tracing engine"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    def test_complete_workflow_trace(self):
        """Test a complete workflow trace from start to finish"""
        engine = WorkflowTracingEngine()
        
        # Start workflow
        session = engine.start_workflow(
            'user_login',
            user=self.user,
            metadata={'ip_address': '127.0.0.1'}
        )
        
        # Trace multiple steps
        with engine.trace_step('frontend', 'LoginForm', 'render') as step1:
            time.sleep(0.01)
            step1.add_metadata({'form_fields': ['username', 'password']})
        
        with engine.trace_step('api', 'AuthView', 'authenticate') as step2:
            time.sleep(0.02)
            step2.add_metadata({'auth_method': 'password'})
        
        with engine.trace_step('database', 'User', 'lookup') as step3:
            time.sleep(0.01)
            step3.add_metadata({'query_type': 'SELECT'})
        
        # Complete workflow
        analysis = engine.complete_workflow(metadata={'login_successful': True})
        
        # Verify analysis structure
        self.assertIn('session', analysis)
        self.assertIn('timing_analysis', analysis)
        self.assertIn('error_analysis', analysis)
        self.assertIn('summary', analysis)
        
        # Verify session data
        session_data = analysis['session']
        self.assertEqual(session_data['workflow_type'], 'user_login')
        self.assertEqual(session_data['status'], 'completed')
        self.assertEqual(session_data['metadata']['login_successful'], True)
        
        # Verify timing analysis
        timing = analysis['timing_analysis']
        self.assertEqual(timing['step_count'], 3)
        self.assertIn('frontend', timing['layers'])
        self.assertIn('api', timing['layers'])
        self.assertIn('database', timing['layers'])
        
        # Verify summary
        summary = analysis['summary']
        self.assertEqual(summary['total_steps'], 3)
        self.assertEqual(summary['failed_steps'], 0)
    
    def test_failed_workflow_trace(self):
        """Test a workflow trace that fails"""
        engine = WorkflowTracingEngine()
        
        # Start workflow
        session = engine.start_workflow('checkout_process')
        
        # Trace some successful steps
        with engine.trace_step('frontend', 'CheckoutForm', 'validate'):
            time.sleep(0.01)
        
        # Simulate an error
        engine.error_tracker.track_error(
            'api', 'PaymentView', 'PaymentError', 
            'Credit card declined'
        )
        
        # Fail workflow
        analysis = engine.fail_workflow(
            'Payment processing failed',
            metadata={'payment_method': 'credit_card'}
        )
        
        # Verify failure analysis
        self.assertEqual(analysis['session']['status'], 'failed')
        self.assertIn('failure_summary', analysis)
        
        failure_summary = analysis['failure_summary']
        self.assertEqual(failure_summary['error_message'], 'Payment processing failed')
        self.assertEqual(failure_summary['total_errors'], 1)


class DatabaseMonitoringTests(TransactionTestCase):
    """Test database monitoring functionality"""
    
    def test_database_query_monitor(self):
        """Test database query monitoring"""
        correlation_id = str(uuid.uuid4())
        monitor = DatabaseQueryMonitor(correlation_id)
        
        # Start monitoring a query
        query_key = monitor.start_query_monitoring('SELECT', 'auth_user', 'lookup')
        
        # Simulate query execution
        time.sleep(0.01)
        
        # End monitoring
        monitor.end_query_monitoring(
            query_key,
            query_sql='SELECT * FROM auth_user WHERE username = %s',
            result_count=1
        )
        
        # Verify performance metric was recorded
        metrics = PerformanceSnapshot.objects.filter(
            correlation_id=correlation_id,
            layer='database',
            component='auth_user'
        )
        
        self.assertEqual(metrics.count(), 1)
        metric = metrics.first()
        self.assertEqual(metric.metric_name, 'query_time')
        self.assertGreater(metric.metric_value, 0)
    
    def test_database_health_monitor(self):
        """Test database health monitoring"""
        health_monitor = DatabaseHealthMonitor()
        
        health_status = health_monitor.check_database_health()
        
        self.assertIn('status', health_status)
        self.assertIn('checks', health_status)
        self.assertIn('connectivity', health_status['checks'])
        
        # Should pass connectivity check in test environment
        self.assertEqual(health_status['checks']['connectivity'], 'pass')
    
    def test_database_operation_tracer(self):
        """Test database operation tracing"""
        engine = WorkflowTracingEngine()
        session = engine.start_workflow('database_test')
        
        tracer = DatabaseOperationTracer(engine)
        
        # Test model operation tracing
        with tracer.trace_model_operation('User', 'create', instance_id=1):
            # Simulate model operation
            time.sleep(0.01)
        
        # Verify trace step was created
        steps = TraceStep.objects.filter(
            workflow_session=session,
            layer='database',
            component='User',
            operation='create'
        )
        
        self.assertEqual(steps.count(), 1)
        step = steps.first()
        self.assertEqual(step.status, 'completed')
        self.assertEqual(step.metadata['model_name'], 'User')
        self.assertEqual(step.metadata['instance_id'], 1)


class EndToEndWorkflowTests(TransactionTestCase):
    """End-to-end tests for complete workflow scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Create performance thresholds
        PerformanceThreshold.objects.create(
            metric_name='response_time',
            layer='api',
            warning_threshold=100,
            critical_threshold=500
        )
    
    def test_user_login_workflow(self):
        """Test complete user login workflow tracing"""
        engine = WorkflowTracingEngine()
        
        # Start login workflow
        session = engine.start_workflow(
            'user_login',
            user=self.user,
            metadata={'ip_address': '127.0.0.1', 'user_agent': 'TestBrowser'}
        )
        
        # Frontend: Form rendering
        with engine.trace_step('frontend', 'LoginForm', 'render') as step:
            time.sleep(0.005)  # 5ms
            step.add_metadata({'form_fields': ['username', 'password']})
        
        # Frontend: Form submission
        with engine.trace_step('frontend', 'LoginForm', 'submit') as step:
            time.sleep(0.01)  # 10ms
            step.add_metadata({'username': 'testuser'})
        
        # API: Authentication request
        with engine.trace_step('api', 'AuthView', 'authenticate') as step:
            time.sleep(0.02)  # 20ms
            step.add_metadata({'auth_method': 'password'})
        
        # Database: User lookup
        with engine.trace_step('database', 'User', 'lookup') as step:
            time.sleep(0.008)  # 8ms
            step.add_metadata({'query_type': 'SELECT', 'result_count': 1})
        
        # API: JWT token generation
        with engine.trace_step('api', 'JWTAuth', 'generate_token') as step:
            time.sleep(0.003)  # 3ms
            step.add_metadata({'token_type': 'access'})
        
        # Frontend: Token storage
        with engine.trace_step('frontend', 'AuthService', 'store_token') as step:
            time.sleep(0.002)  # 2ms
            step.add_metadata({'storage_type': 'localStorage'})
        
        # Complete workflow
        analysis = engine.complete_workflow(metadata={'login_successful': True})
        
        # Verify comprehensive analysis
        self.assertEqual(analysis['session']['status'], 'completed')
        self.assertEqual(analysis['summary']['total_steps'], 6)
        self.assertEqual(analysis['summary']['failed_steps'], 0)
        
        # Verify timing analysis
        timing = analysis['timing_analysis']
        self.assertEqual(timing['step_count'], 6)
        self.assertIn('frontend', timing['layers'])
        self.assertIn('api', timing['layers'])
        self.assertIn('database', timing['layers'])
        
        # Verify layer statistics
        frontend_stats = timing['layers']['frontend']
        self.assertEqual(frontend_stats['step_count'], 3)
        
        api_stats = timing['layers']['api']
        self.assertEqual(api_stats['step_count'], 2)
        
        database_stats = timing['layers']['database']
        self.assertEqual(database_stats['step_count'], 1)
    
    def test_product_fetch_workflow_with_errors(self):
        """Test product fetch workflow with errors"""
        engine = WorkflowTracingEngine()
        
        # Start product fetch workflow
        session = engine.start_workflow('product_fetch')
        
        # Frontend: Page load
        with engine.trace_step('frontend', 'ProductList', 'load'):
            time.sleep(0.01)
        
        # API: Product fetch (simulate error)
        try:
            with engine.trace_step('api', 'ProductView', 'list') as step:
                time.sleep(0.05)
                # Simulate an error
                raise ValueError("Database connection failed")
        except ValueError:
            # Track the error
            engine.error_tracker.track_error(
                'api', 'ProductView', 'DatabaseError',
                'Database connection failed',
                severity='error'
            )
        
        # Fail the workflow
        analysis = engine.fail_workflow(
            'Product fetch failed due to database error'
        )
        
        # Verify failure analysis
        self.assertEqual(analysis['session']['status'], 'failed')
        self.assertEqual(analysis['failure_summary']['total_errors'], 1)
        self.assertEqual(analysis['failure_summary']['failed_steps'], 1)
        
        # Verify error analysis
        error_analysis = analysis['error_analysis']
        self.assertEqual(error_analysis['error_count'], 1)
        self.assertIn('api', error_analysis['layers_affected'])
    
    def test_cart_operations_workflow(self):
        """Test cart operations workflow with performance monitoring"""
        engine = WorkflowTracingEngine()
        
        # Start cart workflow
        session = engine.start_workflow('cart_operations')
        
        # Add item to cart
        with engine.trace_step('frontend', 'CartComponent', 'add_item'):
            time.sleep(0.01)
        
        with engine.trace_step('api', 'CartView', 'add_item'):
            time.sleep(0.03)
        
        with engine.trace_step('database', 'CartItem', 'create'):
            time.sleep(0.005)
        
        # Update item quantity
        with engine.trace_step('frontend', 'CartComponent', 'update_quantity'):
            time.sleep(0.008)
        
        with engine.trace_step('api', 'CartView', 'update_item'):
            time.sleep(0.025)
        
        with engine.trace_step('database', 'CartItem', 'update'):
            time.sleep(0.004)
        
        # Remove item from cart
        with engine.trace_step('frontend', 'CartComponent', 'remove_item'):
            time.sleep(0.006)
        
        with engine.trace_step('api', 'CartView', 'remove_item'):
            time.sleep(0.02)
        
        with engine.trace_step('database', 'CartItem', 'delete'):
            time.sleep(0.003)
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Verify comprehensive analysis
        self.assertEqual(analysis['summary']['total_steps'], 9)
        self.assertEqual(analysis['summary']['failed_steps'], 0)
        
        # Verify all layers are represented
        timing = analysis['timing_analysis']
        self.assertIn('frontend', timing['layers'])
        self.assertIn('api', timing['layers'])
        self.assertIn('database', timing['layers'])
        
        # Each layer should have 3 operations
        self.assertEqual(timing['layers']['frontend']['step_count'], 3)
        self.assertEqual(timing['layers']['api']['step_count'], 3)
        self.assertEqual(timing['layers']['database']['step_count'], 3)