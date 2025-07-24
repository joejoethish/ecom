"""
Tests for the monitoring dashboard and alerting system.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.logs.models import SystemLog, BusinessMetric, PerformanceMetric, SecurityEvent
from apps.logs.views import (
    MonitoringDashboardView,
    SystemHealthAPIView,
    ErrorMetricsAPIView,
    PerformanceMetricsAPIView,
    SecurityMetricsAPIView,
    AlertAPIView
)
from backend.logs.alerts import (
    AlertManager,
    get_alert_configs,
    update_alert_config
)

User = get_user_model()


class MonitoringDashboardViewTests(TestCase):
    """
    Tests for the monitoring dashboard view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create some test data
        self.create_test_data()
    
    def create_test_data(self):
        """
        Create test data for the dashboard.
        """
        # Create system logs
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            SystemLog.objects.create(
                level=level,
                logger_name='test_logger',
                message=f'Test {level.lower()} message',
                source='test',
                event_type='test_event'
            )
        
        # Create performance metrics
        for i in range(5):
            PerformanceMetric.objects.create(
                name='system_metrics',
                value=25.0 + i * 5,  # CPU usage from 25% to 45%
                endpoint=None,
                method=None,
                response_time=50 + i * 10  # Memory usage from 50% to 90%
            )
            
            PerformanceMetric.objects.create(
                name='request_duration',
                value=100 + i * 50,  # Response time from 100ms to 300ms
                endpoint=f'/api/v1/products/{i}',
                method='GET',
                response_time=100 + i * 50
            )
        
        # Create security events
        for event_type in ['login_success', 'login_failure', 'access_violation']:
            SecurityEvent.objects.create(
                event_type=event_type,
                username='testuser',
                ip_address='127.0.0.1',
                details={'test': 'data'}
            )
        
        # Create business metrics
        for name in ['active_users', 'conversion_rate', 'average_order_value']:
            BusinessMetric.objects.create(
                name=name,
                value=100.0 + name.count('e') * 10,
                dimensions={'test': 'data'}
            )
    
    def test_dashboard_view_requires_admin(self):
        """
        Test that the dashboard view requires admin privileges.
        """
        url = reverse('logs:dashboard')
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/admin/login/'))
    
    def test_dashboard_view_with_admin(self):
        """
        Test that the dashboard view works for admin users.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:dashboard')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the template is used
        self.assertTemplateUsed(response, 'logs/dashboard.html')
        
        # Check that context data is provided
        self.assertIn('system_health', response.context)
        self.assertIn('error_metrics', response.context)
        self.assertIn('performance_metrics', response.context)
        self.assertIn('security_metrics', response.context)
        self.assertIn('business_metrics', response.context)
    
    def test_dashboard_view_with_time_range(self):
        """
        Test that the dashboard view handles time range parameter.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:dashboard') + '?time_range=1h'
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that time range is in context
        self.assertEqual(response.context['time_range'], '1h')


class SystemHealthAPIViewTests(TestCase):
    """
    Tests for the system health API view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create some test data
        PerformanceMetric.objects.create(
            name='system_metrics',
            value=30.0,  # CPU usage
            endpoint=None,
            method=None,
            response_time=60.0  # Memory usage
        )
    
    @patch('backend.logs.monitoring.system_monitor._collect_and_log_metrics')
    def test_system_health_api(self, mock_collect):
        """
        Test that the system health API returns the expected data.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_system_health')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response contains the expected fields
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)
        self.assertIn('cpu_usage', data)
        self.assertIn('memory_usage', data)
        self.assertIn('updated', data)
        
        # Check that the collect_metrics method was called
        mock_collect.assert_called_once()


class ErrorMetricsAPIViewTests(TestCase):
    """
    Tests for the error metrics API view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create some test data
        now = timezone.now()
        for i in range(5):
            SystemLog.objects.create(
                level='ERROR',
                logger_name='test_logger',
                message=f'Test error message {i}',
                source='test',
                event_type='test_event',
                created_at=now - timedelta(hours=i)
            )
            
            if i % 2 == 0:
                SystemLog.objects.create(
                    level='CRITICAL',
                    logger_name='test_logger',
                    message=f'Test critical message {i}',
                    source='test',
                    event_type='test_event',
                    created_at=now - timedelta(hours=i)
                )
    
    def test_error_metrics_api(self):
        """
        Test that the error metrics API returns the expected data.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_error_metrics')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response contains the expected fields
        self.assertEqual(data['status'], 'ok')
        self.assertIn('data', data)
        self.assertIn('updated', data)
        
        # Check that the data contains error counts
        self.assertTrue(len(data['data']) > 0)


class PerformanceMetricsAPIViewTests(TestCase):
    """
    Tests for the performance metrics API view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create some test data
        now = timezone.now()
        for i in range(5):
            PerformanceMetric.objects.create(
                name='request_duration',
                value=100 + i * 50,  # Response time from 100ms to 300ms
                endpoint=f'/api/v1/products/{i}',
                method='GET',
                response_time=100 + i * 50,
                timestamp=now - timedelta(hours=i)
            )
    
    def test_performance_metrics_api(self):
        """
        Test that the performance metrics API returns the expected data.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_performance_metrics')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response contains the expected fields
        self.assertEqual(data['status'], 'ok')
        self.assertIn('data', data)
        self.assertIn('updated', data)
        
        # Check that the data contains performance metrics
        self.assertTrue(len(data['data']) > 0)
        self.assertIn('avg_time', data['data'][0])
        self.assertIn('max_time', data['data'][0])
        self.assertIn('count', data['data'][0])


class SecurityMetricsAPIViewTests(TestCase):
    """
    Tests for the security metrics API view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create some test data
        now = timezone.now()
        for i, event_type in enumerate(['login_success', 'login_failure', 'access_violation']):
            for j in range(3):
                SecurityEvent.objects.create(
                    event_type=event_type,
                    username='testuser',
                    ip_address='127.0.0.1',
                    details={'test': 'data'},
                    timestamp=now - timedelta(hours=i + j)
                )
    
    def test_security_metrics_api(self):
        """
        Test that the security metrics API returns the expected data.
        """
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_security_metrics')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response contains the expected fields
        self.assertEqual(data['status'], 'ok')
        self.assertIn('data', data)
        self.assertIn('event_types', data)
        self.assertIn('updated', data)
        
        # Check that the data contains security events
        self.assertTrue(len(data['data']) > 0)
        self.assertTrue(len(data['event_types']) > 0)


class AlertAPIViewTests(TestCase):
    """
    Tests for the alert API view.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
    
    @patch('backend.logs.alerts.get_alert_configs')
    def test_get_alerts(self, mock_get_configs):
        """
        Test that the alert API returns the expected data.
        """
        # Mock the alert configs
        mock_get_configs.return_value = [
            {
                'id': 'test_alert',
                'name': 'Test Alert',
                'description': 'Test alert description',
                'metric': 'test_metric',
                'field': 'test_field',
                'condition': 'gt',
                'threshold': 80,
                'enabled': True,
                'severity': 'warning',
                'channels': ['email', 'slack']
            }
        ]
        
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_alerts')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response contains the expected fields
        self.assertEqual(data['status'], 'ok')
        self.assertIn('alerts', data)
        self.assertIn('updated', data)
        
        # Check that the alerts data is correct
        self.assertEqual(len(data['alerts']), 1)
        self.assertEqual(data['alerts'][0]['id'], 'test_alert')
    
    @patch('backend.logs.alerts.update_alert_config')
    def test_update_alert(self, mock_update_config):
        """
        Test that the alert API can update alert configurations.
        """
        # Mock the update function
        mock_update_config.return_value = True
        
        self.client.login(username='admin', password='adminpassword')
        url = reverse('logs:api_alerts')
        
        # Send a POST request to update an alert
        response = self.client.post(
            url,
            data=json.dumps({
                'id': 'test_alert',
                'enabled': False,
                'threshold': 90
            }),
            content_type='application/json'
        )
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Check that the response indicates success
        self.assertEqual(data['status'], 'ok')
        self.assertIn('message', data)
        
        # Check that the update function was called with the correct parameters
        mock_update_config.assert_called_once_with('test_alert', enabled=False, threshold=90)


class AlertManagerTests(TestCase):
    """
    Tests for the AlertManager class.
    """
    @patch('backend.logs.alerts.os.path.exists')
    @patch('backend.logs.alerts.open')
    @patch('backend.logs.alerts.json.load')
    def test_load_alert_configs(self, mock_json_load, mock_open, mock_exists):
        """
        Test that the AlertManager loads alert configurations correctly.
        """
        # Mock the file operations
        mock_exists.return_value = True
        mock_json_load.return_value = [
            {
                'id': 'test_alert',
                'name': 'Test Alert',
                'description': 'Test alert description',
                'metric': 'test_metric',
                'field': 'test_field',
                'condition': 'gt',
                'threshold': 80,
                'enabled': True,
                'severity': 'warning',
                'channels': ['email', 'slack']
            }
        ]
        
        # Create an AlertManager instance
        manager = AlertManager()
        
        # Check that the configs were loaded
        self.assertEqual(len(manager.alert_configs), 1)
        self.assertEqual(manager.alert_configs[0]['id'], 'test_alert')
    
    @patch('backend.logs.alerts.os.path.exists')
    @patch('backend.logs.alerts.open')
    @patch('backend.logs.alerts.json.dump')
    def test_save_alert_configs(self, mock_json_dump, mock_open, mock_exists):
        """
        Test that the AlertManager saves alert configurations correctly.
        """
        # Mock the file operations
        mock_exists.return_value = False
        
        # Create an AlertManager instance
        manager = AlertManager()
        
        # Set some test configs
        test_configs = [
            {
                'id': 'test_alert',
                'name': 'Test Alert',
                'description': 'Test alert description',
                'metric': 'test_metric',
                'field': 'test_field',
                'condition': 'gt',
                'threshold': 80,
                'enabled': True,
                'severity': 'warning',
                'channels': ['email', 'slack']
            }
        ]
        
        # Save the configs
        result = manager._save_alert_configs(test_configs)
        
        # Check that the save was successful
        self.assertTrue(result)
        
        # Check that json.dump was called with the correct parameters
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0], test_configs)
    
    @patch('backend.logs.alerts.AlertManager._save_alert_configs')
    def test_update_alert_config(self, mock_save):
        """
        Test that the AlertManager can update alert configurations.
        """
        # Mock the save function
        mock_save.return_value = True
        
        # Create an AlertManager instance
        manager = AlertManager()
        
        # Set some test configs
        manager.alert_configs = [
            {
                'id': 'test_alert',
                'name': 'Test Alert',
                'description': 'Test alert description',
                'metric': 'test_metric',
                'field': 'test_field',
                'condition': 'gt',
                'threshold': 80,
                'enabled': True,
                'severity': 'warning',
                'channels': ['email', 'slack']
            }
        ]
        
        # Update a config
        result = manager.update_alert_config('test_alert', enabled=False, threshold=90)
        
        # Check that the update was successful
        self.assertTrue(result)
        
        # Check that the config was updated
        self.assertFalse(manager.alert_configs[0]['enabled'])
        self.assertEqual(manager.alert_configs[0]['threshold'], 90)
        
        # Check that the save function was called
        mock_save.assert_called_once_with(manager.alert_configs)
    
    @patch('backend.logs.alerts.AlertManager._get_metric_value')
    @patch('backend.logs.alerts.timezone.now')
    def test_check_alert_condition(self, mock_now, mock_get_metric):
        """
        Test that the AlertManager checks alert conditions correctly.
        """
        # Mock the current time and metric value
        mock_now.return_value = timezone.now()
        mock_get_metric.return_value = 85  # Above the threshold
        
        # Create an AlertManager instance
        manager = AlertManager()
        
        # Create a test alert config
        alert_config = {
            'id': 'test_alert',
            'name': 'Test Alert',
            'description': 'Test alert description',
            'metric': 'test_metric',
            'field': 'test_field',
            'condition': 'gt',
            'threshold': 80,
            'duration': 0,  # No duration for testing
            'cooldown': 3600,
            'enabled': True,
            'severity': 'warning',
            'channels': []  # No channels for testing
        }
        
        # Check the alert condition
        manager._check_alert_condition(alert_config)
        
        # Check that the alert state was updated
        self.assertIn('test_alert', manager.alert_state)
        self.assertTrue(manager.alert_state['test_alert']['triggered'])
        
        # Check that the metric value function was called
        mock_get_metric.assert_called_once_with('test_metric', 'test_field')
    
    @patch('backend.logs.alerts.AlertManager._send_email_alert')
    @patch('backend.logs.alerts.AlertManager._send_slack_alert')
    @patch('backend.logs.alerts.AlertManager._store_alert_in_database')
    def test_trigger_alert(self, mock_store, mock_slack, mock_email):
        """
        Test that the AlertManager triggers alerts correctly.
        """
        # Create an AlertManager instance
        manager = AlertManager()
        
        # Create a test alert config
        alert_config = {
            'id': 'test_alert',
            'name': 'Test Alert',
            'description': 'Test alert description',
            'metric': 'test_metric',
            'field': 'test_field',
            'condition': 'gt',
            'threshold': 80,
            'duration': 0,
            'cooldown': 3600,
            'enabled': True,
            'severity': 'warning',
            'channels': ['email', 'slack', 'database']
        }
        
        # Trigger the alert
        manager._trigger_alert(alert_config, 85)
        
        # Check that the alert channels were called
        mock_email.assert_called_once_with(alert_config, 85)
        mock_slack.assert_called_once_with(alert_config, 85)
        mock_store.assert_called_once_with(alert_config, 85)


# Add more tests as needed for other components