"""
Simple integration tests for the E2E Workflow Debugging System.
"""
import json
import time
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog,
    DebugConfiguration, PerformanceThreshold, FrontendRoute, APICallDiscovery
)
from .config import DebuggingConfig, FeatureFlags, ConfigValidator
from .database_integration import DatabaseMonitor, database_monitor
from .utils import PerformanceMonitor, ErrorLogger, WorkflowTracer
from .middleware import CorrelationIdMiddleware, DebuggingMiddleware


User = get_user_model()


class SimpleIntegrationTestCase(TransactionTestCase):
    """Base test case for simple integration tests"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test configuration
        self.debug_config = DebugConfiguration.objects.create(
            name='test_config',
            config_type='performance_threshold',
            enabled=True,
            config_data={
                'api_response_time_warning': 500,
                'api_response_time_critical': 2000,
                'database_query_time_warning': 100,
                'database_query_time_critical': 1000,
            }
        )
        
        # Create performance thresholds
        self.performance_threshold = PerformanceThreshold.objects.create(
            metric_name='response_time',
            layer='api',
            warning_threshold=500.0,
            critical_threshold=2000.0,
            enabled=True
        )
    
    def tearDown(self):
        # Clean up test data
        WorkflowSession.objects.all().delete()
        TraceStep.objects.all().delete()
        PerformanceSnapshot.objects.all().delete()
        ErrorLog.objects.all().delete()


@override_settings(DEBUGGING_SYSTEM={'ENABLED': True})
class ConfigurationIntegrationTest(SimpleIntegrationTestCase):
    """Test configuration management integration"""
    
    def test_configuration_loading(self):
        """Test that configuration is loaded correctly from settings and database"""
        config = DebuggingConfig()
        
        # Test settings loading
        self.assertTrue(config.get('debugging_system', 'ENABLED'))
        
        # Test database configuration override
        DebugConfiguration.objects.create(
            name='debugging_system',
            config_type='runtime_setting',
            enabled=True,
            config_data={'ENABLED': False, 'TEST_SETTING': True}
        )
        
        # Reload configuration
        config.reload()
        
        # Should now reflect database settings
        self.assertFalse(config.get('debugging_system', 'ENABLED'))
        self.assertTrue(config.get('debugging_system', 'TEST_SETTING'))
    
    def test_feature_flags(self):
        """Test feature flag functionality"""
        # Test default feature flags
        with override_settings(DEBUGGING_SYSTEM={'PERFORMANCE_MONITORING_ENABLED': True}):
            self.assertTrue(FeatureFlags.is_performance_monitoring_enabled())
        
        # Test configuration override
        config = DebuggingConfig()
        config.set('debugging_system', 'PERFORMANCE_MONITORING_ENABLED', False)
        
        # Feature flag should reflect the change
        self.assertFalse(FeatureFlags.is_performance_monitoring_enabled())
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        validator = ConfigValidator()
        results = validator.validate_configuration()
        
        self.assertIsInstance(results, dict)
        self.assertIn('valid', results)
        self.assertIn('errors', results)
        self.assertIn('warnings', results)
        self.assertIn('recommendations', results)


@override_settings(DEBUGGING_SYSTEM={'ENABLED': True})
class DatabaseIntegrationTest(SimpleIntegrationTestCase):
    """Test database monitoring and integration"""
    
    def test_database_health_check(self):
        """Test database health monitoring"""
        health_info = database_monitor.check_database_health()
        
        self.assertIn('status', health_info)
        self.assertEqual(health_info['status'], 'healthy')
        self.assertIn('connection_time_ms', health_info)
        self.assertIsInstance(health_info['connection_time_ms'], float)
    
    def test_migration_status_check(self):
        """Test migration status validation"""
        migration_status = database_monitor.check_migration_status()
        
        self.assertIn('status', migration_status)
        self.assertIn('pending_migrations', migration_status)
        self.assertIsInstance(migration_status['pending_migrations'], int)
    
    def test_database_integrity_validation(self):
        """Test database integrity checks"""
        integrity_results = database_monitor.validate_database_integrity()
        
        self.assertIn('status', integrity_results)
        self.assertIn('foreign_key_violations', integrity_results)
        self.assertIn('constraint_violations', integrity_results)
    
    def test_database_statistics(self):
        """Test database statistics collection"""
        stats = database_monitor.get_database_statistics()
        
        self.assertIn('connection_info', stats)
        self.assertIn('table_statistics', stats)
        self.assertIsInstance(stats['table_statistics'], list)


@override_settings(DEBUGGING_SYSTEM={'ENABLED': True})
class WorkflowTracingIntegrationTest(SimpleIntegrationTestCase):
    """Test workflow tracing integration"""
    
    def test_workflow_session_creation(self):
        """Test workflow session creation and management"""
        correlation_id = str(uuid.uuid4())
        
        # Start a workflow session
        session = WorkflowTracer.start_workflow(
            workflow_type='login',
            correlation_id=correlation_id,
            user=self.user
        )
        
        self.assertIsInstance(session, WorkflowSession)
        self.assertEqual(str(session.correlation_id), correlation_id)
        self.assertEqual(session.workflow_type, 'login')
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.status, 'in_progress')
    
    def test_trace_step_recording(self):
        """Test trace step recording"""
        correlation_id = str(uuid.uuid4())
        
        # Start workflow and add trace steps
        session = WorkflowTracer.start_workflow(
            workflow_type='product_fetch',
            correlation_id=correlation_id
        )
        
        # Add trace steps
        WorkflowTracer.add_trace_step(
            correlation_id=correlation_id,
            layer='frontend',
            component='ProductList',
            operation='render',
            metadata={'page': 1}
        )
        
        WorkflowTracer.add_trace_step(
            correlation_id=correlation_id,
            layer='api',
            component='ProductViewSet',
            operation='list',
            metadata={'filters': {'category': 'electronics'}}
        )
        
        # Complete workflow
        WorkflowTracer.complete_workflow(correlation_id)
        
        # Verify trace steps were recorded
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertEqual(session.trace_steps.count(), 2)
        
        # Verify trace step details
        frontend_step = session.trace_steps.filter(layer='frontend').first()
        self.assertEqual(frontend_step.component, 'ProductList')
        self.assertEqual(frontend_step.operation, 'render')
        self.assertEqual(frontend_step.metadata['page'], 1)


@override_settings(DEBUGGING_SYSTEM={'ENABLED': True})
class PerformanceMonitoringIntegrationTest(SimpleIntegrationTestCase):
    """Test performance monitoring integration"""
    
    def test_performance_metric_recording(self):
        """Test performance metric recording"""
        correlation_id = str(uuid.uuid4())
        
        # Record performance metrics
        PerformanceMonitor.record_metric(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=250.5,
            correlation_id=correlation_id,
            metadata={'endpoint': '/api/products/'}
        )
        
        # Verify metric was recorded
        metrics = PerformanceSnapshot.objects.filter(
            correlation_id=correlation_id,
            layer='api',
            component='ProductViewSet',
            metric_name='response_time'
        )
        
        self.assertEqual(metrics.count(), 1)
        metric = metrics.first()
        self.assertEqual(metric.metric_value, 250.5)
        self.assertEqual(metric.metadata['endpoint'], '/api/products/')
    
    def test_performance_threshold_alerts(self):
        """Test performance threshold alerting"""
        correlation_id = str(uuid.uuid4())
        
        # Record metric that exceeds warning threshold
        PerformanceMonitor.record_metric(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=750.0,  # Exceeds 500ms warning threshold
            correlation_id=correlation_id
        )
        
        # Check if alert was generated
        alerts = PerformanceMonitor.check_thresholds()
        
        # Should have at least one alert
        self.assertGreater(len(alerts), 0)
        
        # Verify alert details
        alert = alerts[0]
        self.assertEqual(alert['level'], 'warning')
        self.assertEqual(alert['metric_name'], 'response_time')
        self.assertEqual(alert['layer'], 'api')


@override_settings(DEBUGGING_SYSTEM={'ENABLED': True})
class ErrorTrackingIntegrationTest(SimpleIntegrationTestCase):
    """Test error tracking integration"""
    
    def test_error_logging(self):
        """Test error logging functionality"""
        correlation_id = str(uuid.uuid4())
        
        # Log an error
        ErrorLogger.log_error(
            layer='api',
            component='ProductViewSet',
            error_type='ValidationError',
            error_message='Invalid product data',
            correlation_id=correlation_id,
            severity='error',
            metadata={'field': 'price', 'value': 'invalid'}
        )
        
        # Verify error was logged
        error_logs = ErrorLog.objects.filter(
            correlation_id=correlation_id,
            layer='api',
            component='ProductViewSet'
        )
        
        self.assertEqual(error_logs.count(), 1)
        error_log = error_logs.first()
        self.assertEqual(error_log.error_type, 'ValidationError')
        self.assertEqual(error_log.error_message, 'Invalid product data')
        self.assertEqual(error_log.severity, 'error')
    
    def test_exception_logging(self):
        """Test exception logging with stack trace"""
        correlation_id = str(uuid.uuid4())
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            ErrorLogger.log_exception(
                exception=e,
                layer='api',
                component='TestComponent',
                correlation_id=correlation_id,
                metadata={'test': True}
            )
        
        # Verify exception was logged
        error_logs = ErrorLog.objects.filter(
            correlation_id=correlation_id,
            error_type='ValueError'
        )
        
        self.assertEqual(error_logs.count(), 1)
        error_log = error_logs.first()
        self.assertEqual(error_log.error_message, 'Test exception')
        self.assertIsNotNone(error_log.stack_trace)
        self.assertIn('ValueError', error_log.stack_trace)


class EndToEndIntegrationTest(SimpleIntegrationTestCase):
    """End-to-end integration tests"""
    
    def test_complete_workflow_tracing(self):
        """Test complete workflow from frontend to database"""
        correlation_id = str(uuid.uuid4())
        
        # Simulate a complete user workflow
        # 1. Start workflow
        session = WorkflowTracer.start_workflow(
            workflow_type='product_fetch',
            correlation_id=correlation_id,
            user=self.user
        )
        
        # 2. Frontend step
        WorkflowTracer.add_trace_step(
            correlation_id=correlation_id,
            layer='frontend',
            component='ProductList',
            operation='componentDidMount',
            metadata={'route': '/products'}
        )
        
        # 3. API step
        WorkflowTracer.add_trace_step(
            correlation_id=correlation_id,
            layer='api',
            component='ProductViewSet',
            operation='list',
            metadata={'query_params': {'page': 1}}
        )
        
        # 4. Database step
        WorkflowTracer.add_trace_step(
            correlation_id=correlation_id,
            layer='database',
            component='ProductModel',
            operation='select',
            metadata={'query': 'SELECT * FROM products LIMIT 20'}
        )
        
        # 5. Record performance metrics
        PerformanceMonitor.record_metric(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=150.0,
            correlation_id=correlation_id
        )
        
        # 6. Complete workflow
        WorkflowTracer.complete_workflow(correlation_id)
        
        # Verify complete workflow
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertEqual(session.trace_steps.count(), 3)
        
        # Verify performance metrics
        metrics = PerformanceSnapshot.objects.filter(correlation_id=correlation_id)
        self.assertEqual(metrics.count(), 1)
    
    def test_error_correlation_across_layers(self):
        """Test error correlation across different system layers"""
        correlation_id = str(uuid.uuid4())
        
        # Start workflow
        session = WorkflowTracer.start_workflow(
            workflow_type='checkout',
            correlation_id=correlation_id,
            user=self.user
        )
        
        # Log errors at different layers
        ErrorLogger.log_error(
            layer='frontend',
            component='CheckoutForm',
            error_type='ValidationError',
            error_message='Invalid credit card number',
            correlation_id=correlation_id,
            severity='error'
        )
        
        ErrorLogger.log_error(
            layer='api',
            component='PaymentProcessor',
            error_type='PaymentError',
            error_message='Payment gateway timeout',
            correlation_id=correlation_id,
            severity='critical'
        )
        
        ErrorLogger.log_error(
            layer='database',
            component='OrderModel',
            error_type='DatabaseError',
            error_message='Transaction rollback',
            correlation_id=correlation_id,
            severity='error'
        )
        
        # Mark workflow as failed
        WorkflowTracer.fail_workflow(correlation_id, 'Payment processing failed')
        
        # Verify error correlation
        error_logs = ErrorLog.objects.filter(correlation_id=correlation_id)
        self.assertEqual(error_logs.count(), 3)
        
        # Verify workflow status
        session.refresh_from_db()
        self.assertEqual(session.status, 'failed')
        
        # Verify errors are properly correlated
        correlation_ids = [str(error.correlation_id) for error in error_logs]
        self.assertTrue(all(cid == correlation_id for cid in correlation_ids))
    
    def test_performance_monitoring_with_alerts(self):
        """Test performance monitoring with threshold alerts"""
        correlation_id = str(uuid.uuid4())
        
        # Record metrics that exceed thresholds
        PerformanceMonitor.record_metric(
            layer='api',
            component='ProductViewSet',
            metric_name='response_time',
            metric_value=2500.0,  # Exceeds critical threshold
            correlation_id=correlation_id
        )
        
        PerformanceMonitor.record_metric(
            layer='database',
            component='ProductModel',
            metric_name='query_time',
            metric_value=1200.0,  # Exceeds critical threshold
            correlation_id=correlation_id
        )
        
        # Check for threshold violations
        alerts = PerformanceMonitor.check_thresholds()
        
        # Should have alerts for both metrics
        self.assertGreaterEqual(len(alerts), 2)
        
        # Verify alert details
        api_alerts = [a for a in alerts if a['layer'] == 'api']
        db_alerts = [a for a in alerts if a['layer'] == 'database']
        
        self.assertGreater(len(api_alerts), 0)
        self.assertGreater(len(db_alerts), 0)