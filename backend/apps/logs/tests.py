"""
Tests for the logging and monitoring functionality.
"""
import json
import logging
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from backend.logs.middleware import (
    RequestLoggingMiddleware,
    SecurityAuditMiddleware,
    PerformanceMonitoringMiddleware
)
from backend.logs.handlers import (
    JsonFormatter,
    SecurityRotatingFileHandler,
    BusinessMetricsHandler,
    DatabaseLogHandler,
    SlackHandler
)
from backend.logs.formatters import (
    VerboseFormatter,
    SimpleFormatter,
    ColoredConsoleFormatter,
    StructuredFormatter,
    SecurityFormatter,
    BusinessMetricsFormatter
)
from backend.logs.filters import (
    RequireDebugTrue,
    RequireDebugFalse,
    IgnoreHealthChecks,
    SensitiveDataFilter,
    RateLimitFilter,
    EnvironmentFilter,
    UserFilter
)
from backend.logs.security import (
    log_login_attempt,
    log_password_change,
    log_permission_change,
    log_access_violation,
    log_admin_action,
    log_api_key_usage,
    log_data_export,
    log_payment_action,
    log_suspicious_activity,
    log_brute_force_attempt,
    log_csrf_failure,
    log_rate_limit_exceeded
)
from backend.logs.metrics import (
    log_order_placed,
    log_product_view,
    log_cart_action,
    log_search,
    log_checkout_step,
    log_user_registration,
    log_revenue,
    log_inventory_change,
    log_page_view,
    log_api_request
)
from backend.logs.monitoring import (
    SystemMonitor,
    BusinessMetricsMonitor
)
from apps.logs.models import (
    SystemLog,
    BusinessMetric,
    PerformanceMetric,
    SecurityEvent
)

User = get_user_model()


class LoggingMiddlewareTests(TestCase):
    """
    Tests for the logging middleware.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    @patch('backend.logs.middleware.request_logger')
    def test_request_logging_middleware(self, mock_logger):
        """
        Test that RequestLoggingMiddleware logs requests correctly.
        """
        # Create a test request
        request = self.factory.get('/api/v1/products/')
        request.user = self.user
        
        # Create a mock response
        response = MagicMock()
        response.status_code = 200
        response.__setitem__ = MagicMock()
        
        # Create the middleware
        middleware = RequestLoggingMiddleware(lambda r: response)
        
        # Process the request
        result = middleware(request)
        
        # Check that the logger was called
        self.assertTrue(mock_logger.log.called)
        
        # Check that the request ID was added to the response
        response.__setitem__.assert_any_call('X-Request-ID', unittest.mock.ANY)
    
    @patch('backend.logs.middleware.security_logger')
    def test_security_audit_middleware(self, mock_logger):
        """
        Test that SecurityAuditMiddleware logs security-relevant requests.
        """
        # Create a test request to a security-relevant path
        request = self.factory.post('/api/v1/auth/login/')
        request.user = self.user
        
        # Create a mock response
        response = MagicMock()
        response.status_code = 200
        
        # Create the middleware with a test security path
        middleware = SecurityAuditMiddleware(lambda r: response)
        middleware.security_paths = ['/api/v1/auth/']
        
        # Process the request
        result = middleware(request)
        
        # Check that the logger was called
        self.assertTrue(mock_logger.log.called)
    
    @patch('backend.logs.middleware.performance_logger')
    def test_performance_monitoring_middleware_slow_request(self, mock_logger):
        """
        Test that PerformanceMonitoringMiddleware logs slow requests.
        """
        # Create a test request
        request = self.factory.get('/api/v1/products/')
        request.user = self.user
        
        # Create a mock response
        response = MagicMock()
        response.status_code = 200
        response.__setitem__ = MagicMock()
        
        # Create the middleware with a very low threshold
        middleware = PerformanceMonitoringMiddleware(lambda r: response)
        middleware.slow_threshold_ms = 0  # Ensure the request is considered slow
        
        # Process the request
        result = middleware(request)
        
        # Check that the logger was called
        self.assertTrue(mock_logger.log.called)
        
        # Check that the performance header was added to the response
        response.__setitem__.assert_any_call('X-Response-Time-Ms', unittest.mock.ANY)


class LoggingFormattersTests(TestCase):
    """
    Tests for the logging formatters.
    """
    def setUp(self):
        self.record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test_path',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
    
    def test_verbose_formatter(self):
        """
        Test that VerboseFormatter formats log records correctly.
        """
        formatter = VerboseFormatter('%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s')
        result = formatter.format(self.record)
        
        self.assertIn('[INFO]', result)
        self.assertIn('test_logger:42', result)
        self.assertIn('Test message', result)
    
    def test_simple_formatter(self):
        """
        Test that SimpleFormatter formats log records correctly.
        """
        formatter = SimpleFormatter('%(levelname)s %(message)s')
        result = formatter.format(self.record)
        
        self.assertEqual(result, 'INFO Test message')
    
    def test_structured_formatter(self):
        """
        Test that StructuredFormatter formats log records as JSON.
        """
        formatter = StructuredFormatter()
        result = formatter.format(self.record)
        
        # Parse the JSON result
        data = json.loads(result)
        
        self.assertEqual(data['level'], 'INFO')
        self.assertEqual(data['logger'], 'test_logger')
        self.assertEqual(data['message'], 'Test message')
        self.assertEqual(data['line'], 42)
    
    def test_security_formatter(self):
        """
        Test that SecurityFormatter formats security events correctly.
        """
        # Add security-specific attributes
        self.record.event_type = 'login_attempt'
        self.record.username = 'testuser'
        self.record.ip_address = '127.0.0.1'
        
        formatter = SecurityFormatter()
        result = formatter.format(self.record)
        
        # Parse the JSON result
        data = json.loads(result)
        
        self.assertEqual(data['level'], 'INFO')
        self.assertEqual(data['event_type'], 'login_attempt')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['ip_address'], '127.0.0.1')
    
    def test_business_metrics_formatter(self):
        """
        Test that BusinessMetricsFormatter formats metrics correctly.
        """
        # Add metric-specific attributes
        self.record.metric_name = 'order_value'
        self.record.metric_value = 99.99
        self.record.dimensions = {'product_category': 'electronics'}
        
        formatter = BusinessMetricsFormatter()
        result = formatter.format(self.record)
        
        # Parse the JSON result
        data = json.loads(result)
        
        self.assertEqual(data['metric_name'], 'order_value')
        self.assertEqual(data['metric_value'], 99.99)
        self.assertEqual(data['dimensions'], {'product_category': 'electronics'})


class LoggingFiltersTests(TestCase):
    """
    Tests for the logging filters.
    """
    def setUp(self):
        self.record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test_path',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
    
    @patch('backend.logs.filters.settings')
    def test_require_debug_true(self, mock_settings):
        """
        Test that RequireDebugTrue filter works correctly.
        """
        # Test when DEBUG is True
        mock_settings.DEBUG = True
        filter_instance = RequireDebugTrue()
        self.assertTrue(filter_instance.filter(self.record))
        
        # Test when DEBUG is False
        mock_settings.DEBUG = False
        self.assertFalse(filter_instance.filter(self.record))
    
    @patch('backend.logs.filters.settings')
    def test_require_debug_false(self, mock_settings):
        """
        Test that RequireDebugFalse filter works correctly.
        """
        # Test when DEBUG is False
        mock_settings.DEBUG = False
        filter_instance = RequireDebugFalse()
        self.assertTrue(filter_instance.filter(self.record))
        
        # Test when DEBUG is True
        mock_settings.DEBUG = True
        self.assertFalse(filter_instance.filter(self.record))
    
    def test_ignore_health_checks(self):
        """
        Test that IgnoreHealthChecks filter works correctly.
        """
        filter_instance = IgnoreHealthChecks()
        
        # Test with non-health check path
        self.record.request_path = '/api/v1/products/'
        self.assertTrue(filter_instance.filter(self.record))
        
        # Test with health check path
        self.record.request_path = '/api/health/check/'
        self.assertFalse(filter_instance.filter(self.record))
    
    def test_sensitive_data_filter(self):
        """
        Test that SensitiveDataFilter masks sensitive data.
        """
        filter_instance = SensitiveDataFilter()
        
        # Test with sensitive data in message
        self.record.msg = 'Password: "secret123" and credit_card: "4111-1111-1111-1111"'
        filter_instance.filter(self.record)
        
        self.assertIn('Password: "*****"', self.record.msg)
        self.assertIn('credit_card: "*****"', self.record.msg)
        self.assertNotIn('secret123', self.record.msg)
        self.assertNotIn('4111-1111-1111-1111', self.record.msg)
    
    def test_environment_filter(self):
        """
        Test that EnvironmentFilter adds environment information.
        """
        filter_instance = EnvironmentFilter(environment='testing')
        filter_instance.filter(self.record)
        
        self.assertEqual(self.record.environment, 'testing')


class SecurityLoggingTests(TestCase):
    """
    Tests for the security logging functions.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    @patch('backend.logs.security.security_logger')
    def test_log_login_attempt(self, mock_logger):
        """
        Test that log_login_attempt logs correctly.
        """
        # Test successful login
        log_login_attempt('testuser', True, '127.0.0.1', 'Mozilla/5.0')
        mock_logger.info.assert_called_once()
        mock_logger.reset_mock()
        
        # Test failed login
        log_login_attempt('testuser', False, '127.0.0.1', 'Mozilla/5.0')
        mock_logger.warning.assert_called_once()
    
    @patch('backend.logs.security.security_logger')
    def test_log_suspicious_activity(self, mock_logger):
        """
        Test that log_suspicious_activity logs correctly.
        """
        log_suspicious_activity(1, 'testuser', '127.0.0.1', 'multiple_failed_logins')
        mock_logger.warning.assert_called_once()
    
    @patch('backend.logs.security.security_logger')
    @patch('backend.logs.security.SecurityEvent.objects.create')
    def test_log_brute_force_attempt(self, mock_create, mock_logger):
        """
        Test that log_brute_force_attempt logs correctly and creates a database entry.
        """
        log_brute_force_attempt('127.0.0.1', 'testuser', 10, 'Mozilla/5.0')
        mock_logger.error.assert_called_once()
        mock_create.assert_called_once()
    
    @patch('backend.logs.security.security_logger')
    @patch('backend.logs.security.SecurityEvent.objects.create')
    def test_log_csrf_failure(self, mock_create, mock_logger):
        """
        Test that log_csrf_failure logs correctly and creates a database entry.
        """
        request = self.factory.post('/api/v1/products/')
        request.user = self.user
        
        log_csrf_failure(request, 'Token missing')
        mock_logger.warning.assert_called_once()
        mock_create.assert_called_once()


class MetricsLoggingTests(TestCase):
    """
    Tests for the metrics logging functions.
    """
    @patch('backend.logs.metrics.metrics_logger')
    def test_log_order_placed(self, mock_logger):
        """
        Test that log_order_placed logs correctly.
        """
        log_order_placed('ORD123', 1, 99.99, 3, 'credit_card')
        mock_logger.info.assert_called_once()
    
    @patch('backend.logs.metrics.metrics_logger')
    def test_log_product_view(self, mock_logger):
        """
        Test that log_product_view logs correctly.
        """
        log_product_view(1, 1, 2, 'search')
        mock_logger.info.assert_called_once()
    
    @patch('backend.logs.metrics.metrics_logger')
    def test_log_cart_action(self, mock_logger):
        """
        Test that log_cart_action logs correctly.
        """
        log_cart_action('add', 1, 2, 1, 99.99)
        mock_logger.info.assert_called_once()
    
    @patch('backend.logs.metrics.metrics_logger')
    def test_log_search(self, mock_logger):
        """
        Test that log_search logs correctly.
        """
        log_search('smartphone', 1, 10, {'price_min': 100})
        mock_logger.info.assert_called_once()


class MonitoringTests(TestCase):
    """
    Tests for the monitoring functionality.
    """
    @patch('backend.logs.monitoring.monitoring_logger')
    @patch('backend.logs.monitoring.psutil.cpu_percent')
    @patch('backend.logs.monitoring.psutil.virtual_memory')
    @patch('backend.logs.monitoring.psutil.disk_usage')
    def test_system_monitor(self, mock_disk, mock_memory, mock_cpu, mock_logger):
        """
        Test that SystemMonitor collects and logs metrics correctly.
        """
        # Mock the psutil functions
        mock_cpu.return_value = 25.0
        mock_memory.return_value = MagicMock(
            percent=50.0,
            available=4 * 1024 * 1024 * 1024,  # 4 GB
            total=8 * 1024 * 1024 * 1024  # 8 GB
        )
        mock_disk.return_value = MagicMock(
            percent=30.0,
            free=70 * 1024 * 1024 * 1024,  # 70 GB
            total=100 * 1024 * 1024 * 1024  # 100 GB
        )
        
        # Create the monitor and collect metrics
        monitor = SystemMonitor()
        monitor._collect_and_log_metrics()
        
        # Check that the logger was called
        self.assertTrue(mock_logger.info.called)
    
    @patch('backend.logs.monitoring.metrics_logger')
    def test_business_metrics_monitor(self, mock_logger):
        """
        Test that BusinessMetricsMonitor logs metrics correctly.
        """
        monitor = BusinessMetricsMonitor()
        
        # Test logging active users
        monitor.log_active_users(100, 'daily')
        mock_logger.info.assert_called_once()
        mock_logger.reset_mock()
        
        # Test logging conversion rate
        monitor.log_conversion_rate(5.5, 'organic', 'daily')
        mock_logger.info.assert_called_once()
        mock_logger.reset_mock()
        
        # Test logging average order value
        monitor.log_average_order_value(75.50, 'daily')
        mock_logger.info.assert_called_once()


class LoggingModelsTests(TestCase):
    """
    Tests for the logging models.
    """
    def test_system_log_creation(self):
        """
        Test creating a SystemLog entry.
        """
        log = SystemLog.objects.create(
            level='INFO',
            logger_name='test_logger',
            message='Test log message',
            source='test',
            event_type='test_event'
        )
        
        self.assertEqual(log.level, 'INFO')
        self.assertEqual(log.message, 'Test log message')
        self.assertEqual(log.source, 'test')
        self.assertEqual(log.event_type, 'test_event')
    
    def test_business_metric_creation(self):
        """
        Test creating a BusinessMetric entry.
        """
        metric = BusinessMetric.objects.create(
            name='test_metric',
            value=42.0,
            dimensions={'category': 'test'}
        )
        
        self.assertEqual(metric.name, 'test_metric')
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.dimensions, {'category': 'test'})
    
    def test_performance_metric_creation(self):
        """
        Test creating a PerformanceMetric entry.
        """
        metric = PerformanceMetric.objects.create(
            name='response_time',
            value=150.0,
            endpoint='/api/v1/products/',
            method='GET',
            response_time=150
        )
        
        self.assertEqual(metric.name, 'response_time')
        self.assertEqual(metric.value, 150.0)
        self.assertEqual(metric.endpoint, '/api/v1/products/')
        self.assertEqual(metric.method, 'GET')
        self.assertEqual(metric.response_time, 150)
    
    def test_security_event_creation(self):
        """
        Test creating a SecurityEvent entry.
        """
        event = SecurityEvent.objects.create(
            event_type='login_failure',
            username='testuser',
            ip_address='127.0.0.1',
            details={'attempt_count': 3}
        )
        
        self.assertEqual(event.event_type, 'login_failure')
        self.assertEqual(event.username, 'testuser')
        self.assertEqual(event.ip_address, '127.0.0.1')
        self.assertEqual(event.details, {'attempt_count': 3})