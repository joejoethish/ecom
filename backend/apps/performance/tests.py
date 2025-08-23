from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json
import uuid

from .models import (
    PerformanceMetric, ApplicationPerformanceMonitor, DatabasePerformanceLog,
    ServerMetrics, UserExperienceMetrics, PerformanceAlert, PerformanceBenchmark,
    PerformanceReport, PerformanceIncident
)
from .utils import (
    PerformanceAnalyzer, PerformanceOptimizer, AlertManager, CapacityPlanner,
    get_client_ip, generate_transaction_id, calculate_percentile
)

User = get_user_model()
class PerformanceMetricModelTest(TestCase):
    """Test PerformanceMetric model"""
    
    def setUp(self):
        self.metric_data = {
            'metric_type': 'response_time',
            'name': 'API Response Time',
            'value': 150.5,
            'unit': 'ms',
            'source': 'web_server',
            'endpoint': '/api/products/',
            'severity': 'low'
        }
    
    def test_create_performance_metric(self):
        """Test creating a performance metric"""
        metric = PerformanceMetric.objects.create(**self.metric_data)
        
        self.assertEqual(metric.metric_type, 'response_time')
        self.assertEqual(metric.name, 'API Response Time')
        self.assertEqual(metric.value, 150.5)
        self.assertEqual(metric.unit, 'ms')
        self.assertEqual(metric.source, 'web_server')
        self.assertEqual(metric.endpoint, '/api/products/')
        self.assertEqual(metric.severity, 'low')
        self.assertIsNotNone(metric.id)
        self.assertIsNotNone(metric.timestamp)
        self.assertIsNotNone(metric.created_at)
    
    def test_metric_type_choices(self):
        """Test metric type choices validation"""
        valid_types = [
            'response_time', 'cpu_usage', 'memory_usage', 'disk_usage',
            'network_io', 'database_query', 'api_endpoint', 'user_experience',
            'error_rate', 'throughput'
        ]
        
        for metric_type in valid_types:
            metric = PerformanceMetric.objects.create(
                metric_type=metric_type,
                name=f'Test {metric_type}',
                value=100.0,
                unit='ms'
            )
            self.assertEqual(metric.metric_type, metric_type)
    
    def test_severity_levels(self):
        """Test severity level choices"""
        severity_levels = ['low', 'medium', 'high', 'critical']
        
        for severity in severity_levels:
            metric = PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Test Metric',
                value=100.0,
                unit='ms',
                severity=severity
            )
            self.assertEqual(metric.severity, severity)
    
    def test_metadata_field(self):
        """Test JSON metadata field"""
        metadata = {
            'user_agent': 'Mozilla/5.0',
            'request_size': 1024,
            'response_size': 2048
        }
        
        metric = PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Test Metric',
            value=100.0,
            unit='ms',
            metadata=metadata
        )
        
        self.assertEqual(metric.metadata, metadata)
        self.assertEqual(metric.metadata['user_agent'], 'Mozilla/5.0')
        self.assertEqual(metric.metadata['request_size'], 1024)


class DatabasePerformanceLogModelTest(TestCase):
    """Test DatabasePerformanceLog model"""
    
    def setUp(self):
        self.log_data = {
            'query': 'SELECT * FROM products WHERE category_id = 1',
            'query_hash': 'abc123def456',
            'execution_time': 250.5,
            'rows_examined': 1000,
            'rows_returned': 50,
            'database_name': 'ecommerce',
            'table_names': ['products', 'categories'],
            'query_type': 'SELECT',
            'is_slow_query': True
        }
    
    def test_create_database_log(self):
        """Test creating a database performance log"""
        log = DatabasePerformanceLog.objects.create(**self.log_data)
        
        self.assertEqual(log.query, 'SELECT * FROM products WHERE category_id = 1')
        self.assertEqual(log.query_hash, 'abc123def456')
        self.assertEqual(log.execution_time, 250.5)
        self.assertEqual(log.rows_examined, 1000)
        self.assertEqual(log.rows_returned, 50)
        self.assertEqual(log.database_name, 'ecommerce')
        self.assertEqual(log.table_names, ['products', 'categories'])
        self.assertEqual(log.query_type, 'SELECT')
        self.assertTrue(log.is_slow_query)
        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.timestamp)
    
    def test_explain_plan_json_field(self):
        """Test explain plan JSON field"""
        explain_plan = {
            'select_type': 'SIMPLE',
            'table': 'products',
            'type': 'ref',
            'key': 'idx_category_id',
            'rows': 1000
        }
        
        log = DatabasePerformanceLog.objects.create(
            query='SELECT * FROM products',
            query_hash='test123',
            execution_time=100.0,
            database_name='test',
            query_type='SELECT',
            explain_plan=explain_plan
        )
        
        self.assertEqual(log.explain_plan, explain_plan)
        self.assertEqual(log.explain_plan['select_type'], 'SIMPLE')


class ApplicationPerformanceMonitorModelTest(TestCase):
    """Test ApplicationPerformanceMonitor model"""
    
    def setUp(self):
        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(milliseconds=500)
        
        self.apm_data = {
            'transaction_id': 'txn_123456',
            'transaction_type': 'web_request',
            'name': 'GET /api/products/',
            'duration': 500.0,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status_code': 200
        }
    
    def test_create_apm_record(self):
        """Test creating an APM record"""
        apm = ApplicationPerformanceMonitor.objects.create(**self.apm_data)
        
        self.assertEqual(apm.transaction_id, 'txn_123456')
        self.assertEqual(apm.transaction_type, 'web_request')
        self.assertEqual(apm.name, 'GET /api/products/')
        self.assertEqual(apm.duration, 500.0)
        self.assertEqual(apm.start_time, self.start_time)
        self.assertEqual(apm.end_time, self.end_time)
        self.assertEqual(apm.status_code, 200)
        self.assertIsNotNone(apm.id)
    
    def test_transaction_types(self):
        """Test transaction type choices"""
        transaction_types = [
            'web_request', 'background_job', 'database_operation',
            'external_api', 'file_operation'
        ]
        
        for tx_type in transaction_types:
            apm = ApplicationPerformanceMonitor.objects.create(
                transaction_id=f'txn_{tx_type}',
                transaction_type=tx_type,
                name=f'Test {tx_type}',
                duration=100.0,
                start_time=timezone.now(),
                end_time=timezone.now()
            )
            self.assertEqual(apm.transaction_type, tx_type)
    
    def test_spans_and_tags_json_fields(self):
        """Test spans and tags JSON fields"""
        spans = [
            {'name': 'database_query', 'duration': 50.0},
            {'name': 'external_api_call', 'duration': 100.0}
        ]
        
        tags = {
            'environment': 'production',
            'service': 'api',
            'version': '1.0.0'
        }
        
        apm = ApplicationPerformanceMonitor.objects.create(
            transaction_id='txn_test',
            transaction_type='web_request',
            name='Test Transaction',
            duration=200.0,
            start_time=timezone.now(),
            end_time=timezone.now(),
            spans=spans,
            tags=tags
        )
        
        self.assertEqual(apm.spans, spans)
        self.assertEqual(apm.tags, tags)
        self.assertEqual(len(apm.spans), 2)
        self.assertEqual(apm.tags['environment'], 'production')


class PerformanceAlertModelTest(TestCase):
    """Test PerformanceAlert model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.alert_data = {
            'alert_type': 'threshold',
            'name': 'High Response Time Alert',
            'description': 'Response time exceeded threshold',
            'metric_type': 'response_time',
            'threshold_value': 2000.0,
            'current_value': 2500.0,
            'severity': 'high'
        }
    
    def test_create_alert(self):
        """Test creating a performance alert"""
        alert = PerformanceAlert.objects.create(**self.alert_data)
        
        self.assertEqual(alert.alert_type, 'threshold')
        self.assertEqual(alert.name, 'High Response Time Alert')
        self.assertEqual(alert.description, 'Response time exceeded threshold')
        self.assertEqual(alert.metric_type, 'response_time')
        self.assertEqual(alert.threshold_value, 2000.0)
        self.assertEqual(alert.current_value, 2500.0)
        self.assertEqual(alert.severity, 'high')
        self.assertEqual(alert.status, 'active')  # Default status
        self.assertFalse(alert.notification_sent)  # Default value
        self.assertEqual(alert.escalation_level, 1)  # Default value
        self.assertIsNotNone(alert.triggered_at)
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment"""
        alert = PerformanceAlert.objects.create(**self.alert_data)
        
        # Acknowledge the alert
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = self.user
        alert.save()
        
        self.assertEqual(alert.status, 'acknowledged')
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertEqual(alert.acknowledged_by, self.user)
    
    def test_alert_resolution(self):
        """Test alert resolution"""
        alert = PerformanceAlert.objects.create(**self.alert_data)
        
        # Resolve the alert
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        self.assertEqual(alert.status, 'resolved')
        self.assertIsNotNone(alert.resolved_at)


class PerformanceIncidentModelTest(TestCase):
    """Test PerformanceIncident model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.incident_data = {
            'incident_id': 'PERF-0001',
            'title': 'Database Performance Degradation',
            'description': 'Slow database queries causing performance issues',
            'incident_type': 'degradation',
            'severity': 'high',
            'affected_services': ['api', 'web'],
            'created_by': self.user
        }
    
    def test_create_incident(self):
        """Test creating a performance incident"""
        incident = PerformanceIncident.objects.create(**self.incident_data)
        
        self.assertEqual(incident.incident_id, 'PERF-0001')
        self.assertEqual(incident.title, 'Database Performance Degradation')
        self.assertEqual(incident.description, 'Slow database queries causing performance issues')
        self.assertEqual(incident.incident_type, 'degradation')
        self.assertEqual(incident.severity, 'high')
        self.assertEqual(incident.affected_services, ['api', 'web'])
        self.assertEqual(incident.status, 'open')  # Default status
        self.assertEqual(incident.created_by, self.user)
        self.assertIsNotNone(incident.started_at)
        self.assertEqual(incident.timeline, [])  # Default empty list
    
    def test_incident_timeline(self):
        """Test incident timeline functionality"""
        incident = PerformanceIncident.objects.create(**self.incident_data)
        
        # Add timeline entry
        timeline_entry = {
            'timestamp': timezone.now().isoformat(),
            'action': 'status_change',
            'old_status': 'open',
            'new_status': 'investigating',
            'user': 'admin',
            'comment': 'Started investigation'
        }
        
        incident.timeline.append(timeline_entry)
        incident.save()
        
        self.assertEqual(len(incident.timeline), 1)
        self.assertEqual(incident.timeline[0]['action'], 'status_change')
        self.assertEqual(incident.timeline[0]['old_status'], 'open')
        self.assertEqual(incident.timeline[0]['new_status'], 'investigating')


class PerformanceUtilsTest(TestCase):
    """Test performance utility functions"""
    
    def test_generate_transaction_id(self):
        """Test transaction ID generation"""
        tx_id = generate_transaction_id()
        
        self.assertIsInstance(tx_id, str)
        self.assertEqual(len(tx_id), 36)  # UUID4 length
        
        # Test uniqueness
        tx_id2 = generate_transaction_id()
        self.assertNotEqual(tx_id, tx_id2)
    
    def test_calculate_percentile(self):
        """Test percentile calculation"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Test different percentiles
        self.assertEqual(calculate_percentile(values, 50), 5.5)  # Median
        self.assertEqual(calculate_percentile(values, 90), 9.1)
        self.assertEqual(calculate_percentile(values, 95), 9.55)
        
        # Test edge cases
        self.assertEqual(calculate_percentile([], 50), 0)  # Empty list
        self.assertEqual(calculate_percentile([5], 50), 5)  # Single value
    
    def test_get_client_ip(self):
        """Test client IP extraction"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        # Test with X-Forwarded-For header
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test with REMOTE_ADDR
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.2'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.2')


class PerformanceAnalyzerTest(TestCase):
    """Test PerformanceAnalyzer utility class"""
    
    def setUp(self):
        # Create test performance metrics
        base_time = timezone.now() - timedelta(hours=2)
        
        for i in range(10):
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Test Metric',
                value=100 + (i * 10),  # Values from 100 to 190
                unit='ms',
                timestamp=base_time + timedelta(minutes=i * 10)
            )
    
    def test_analyze_response_times(self):
        """Test response time analysis"""
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=3)
        
        analysis = PerformanceAnalyzer.analyze_response_times(start_date, end_date)
        
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis['count'], 10)
        self.assertEqual(analysis['min'], 100)
        self.assertEqual(analysis['max'], 190)
        self.assertEqual(analysis['avg'], 145)  # Average of 100-190
        
        # Test with non-existent endpoint
        analysis = PerformanceAnalyzer.analyze_response_times(
            start_date, end_date, endpoint='/nonexistent/'
        )
        self.assertIsNone(analysis)
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        # Create some anomalous data points
        PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Anomaly',
            value=5000,  # Very high value
            unit='ms',
            timestamp=timezone.now()
        )
        
        anomalies = PerformanceAnalyzer.detect_anomalies('response_time', 24)
        
        self.assertGreater(len(anomalies), 0)
        self.assertTrue(any(anomaly.value == 5000 for anomaly in anomalies))
    
    def test_generate_performance_insights(self):
        """Test performance insights generation"""
        # Create slow response times
        for i in range(5):
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Slow Response',
                value=3000,  # Slow response time
                unit='ms',
                timestamp=timezone.now() - timedelta(minutes=i)
            )
        
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=1)
        
        insights = PerformanceAnalyzer.generate_performance_insights(start_date, end_date)
        
        self.assertIsInstance(insights, list)
        # Should have insight about slow response times
        response_time_insights = [
            insight for insight in insights 
            if insight['category'] == 'response_time'
        ]
        self.assertGreater(len(response_time_insights), 0)


class AlertManagerTest(TestCase):
    """Test AlertManager utility class"""
    
    def setUp(self):
        # Create metrics that exceed thresholds
        PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Slow Response',
            value=3000,  # Exceeds medium threshold (1000)
            unit='ms',
            timestamp=timezone.now()
        )
        
        PerformanceMetric.objects.create(
            metric_type='cpu_usage',
            name='High CPU',
            value=85,  # Exceeds high threshold (80)
            unit='%',
            timestamp=timezone.now()
        )
    
    def test_check_thresholds(self):
        """Test threshold checking"""
        alerts = AlertManager.check_thresholds()
        
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(alerts), 0)
        
        # Check that alerts were created for our test metrics
        alert_types = [alert.metric_type for alert in alerts]
        self.assertIn('response_time', alert_types)
        self.assertIn('cpu_usage', alert_types)
    
    @patch('backend.apps.performance.utils.logger')
    def test_send_alert_notifications(self, mock_logger):
        """Test alert notification sending"""
        alert = PerformanceAlert.objects.create(
            alert_type='threshold',
            name='Test Alert',
            description='Test alert description',
            metric_type='response_time',
            threshold_value=1000,
            current_value=2000,
            severity='high'
        )
        
        AlertManager.send_alert_notifications(alert)
        
        # Check that logger was called
        mock_logger.warning.assert_called_once()
        
        # Check that notification_sent flag was set
        alert.refresh_from_db()
        self.assertTrue(alert.notification_sent)


class CapacityPlannerTest(TestCase):
    """Test CapacityPlanner utility class"""
    
    def setUp(self):
        # Create historical data for forecasting
        base_time = timezone.now() - timedelta(days=30)
        
        for i in range(30):
            # Create increasing CPU usage trend
            PerformanceMetric.objects.create(
                metric_type='cpu_usage',
                name='CPU Usage',
                value=50 + (i * 0.5),  # Gradually increasing from 50% to 64.5%
                unit='%',
                timestamp=base_time + timedelta(days=i)
            )
    
    def test_forecast_resource_usage(self):
        """Test resource usage forecasting"""
        forecast = CapacityPlanner.forecast_resource_usage('cpu_usage', 30)
        
        self.assertIsNotNone(forecast)
        self.assertIn('historical_data', forecast)
        self.assertIn('forecast', forecast)
        self.assertIn('trend', forecast)
        self.assertIn('slope', forecast)
        self.assertIn('confidence', forecast)
        
        self.assertEqual(len(forecast['forecast']), 30)
        self.assertEqual(forecast['trend'], 'increasing')  # Should detect increasing trend
        self.assertGreater(forecast['slope'], 0)  # Positive slope for increasing trend
    
    def test_generate_capacity_recommendations(self):
        """Test capacity recommendations generation"""
        # Create high usage metrics that would trigger recommendations
        for i in range(5):
            PerformanceMetric.objects.create(
                metric_type='memory_usage',
                name='Memory Usage',
                value=90,  # High memory usage
                unit='%',
                timestamp=timezone.now() - timedelta(days=i)
            )
        
        recommendations = CapacityPlanner.generate_capacity_recommendations()
        
        self.assertIsInstance(recommendations, list)
        # Should have recommendations for high resource usage
        if recommendations:
            self.assertIn('type', recommendations[0])
            self.assertIn('resource', recommendations[0])
            self.assertIn('message', recommendations[0])
            self.assertIn('recommendation', recommendations[0])
            self.assertIn('urgency', recommendations[0])

class PerformanceMetricAPITest(APITestCase):
    """Test PerformanceMetric API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test metrics
        self.metric = PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Test Metric',
            value=150.0,
            unit='ms',
            source='web_server',
            endpoint='/api/test/'
        )
    
    def test_list_metrics(self):
        """Test listing performance metrics"""
        url = reverse('performancemetric-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['metric_type'], 'response_time')
    
    def test_create_metric(self):
        """Test creating a performance metric"""
        url = reverse('performancemetric-list')
        data = {
            'metric_type': 'cpu_usage',
            'name': 'CPU Usage Test',
            'value': 75.5,
            'unit': '%',
            'source': 'server'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['metric_type'], 'cpu_usage')
        self.assertEqual(response.data['value'], 75.5)
    
    def test_filter_by_metric_type(self):
        """Test filtering metrics by type"""
        # Create additional metric
        PerformanceMetric.objects.create(
            metric_type='cpu_usage',
            name='CPU Metric',
            value=80.0,
            unit='%'
        )
        
        url = reverse('performancemetric-list')
        response = self.client.get(url, {'metric_type': 'cpu_usage'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['metric_type'], 'cpu_usage')
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard statistics endpoint"""
        url = reverse('performancemetric-dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response_time', response.data)
        self.assertIn('error_rate', response.data)
        self.assertIn('cpu_usage', response.data)
        self.assertIn('memory_usage', response.data)
        self.assertIn('active_alerts', response.data)
    
    def test_time_series_endpoint(self):
        """Test time series data endpoint"""
        url = reverse('performancemetric-time-series')
        response = self.client.get(url, {
            'metric_type': 'response_time',
            'hours': 24,
            'interval': 'hour'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metric_type', response.data)
        self.assertIn('interval', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['metric_type'], 'response_time')
    
    def test_top_endpoints(self):
        """Test top endpoints analysis"""
        url = reverse('performancemetric-top-endpoints')
        response = self.client.get(url, {
            'hours': 24,
            'limit': 10,
            'sort_by': 'slowest'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_anomalies_detection(self):
        """Test anomalies detection endpoint"""
        url = reverse('performancemetric-anomalies')
        response = self.client.get(url, {
            'metric_type': 'response_time',
            'hours': 24
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metric_type', response.data)
        self.assertIn('anomalies_count', response.data)
        self.assertIn('anomalies', response.data)


class PerformanceAlertAPITest(APITestCase):
    """Test PerformanceAlert API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.alert = PerformanceAlert.objects.create(
            alert_type='threshold',
            name='Test Alert',
            description='Test alert description',
            metric_type='response_time',
            threshold_value=1000.0,
            current_value=1500.0,
            severity='medium'
        )
    
    def test_list_alerts(self):
        """Test listing performance alerts"""
        url = reverse('performancealert-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Alert')
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        url = reverse('performancealert-acknowledge', kwargs={'pk': self.alert.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'acknowledged')
        
        # Verify alert was updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'acknowledged')
        self.assertIsNotNone(self.alert.acknowledged_at)
        self.assertEqual(self.alert.acknowledged_by, self.user)
    
    def test_resolve_alert(self):
        """Test resolving an alert"""
        url = reverse('performancealert-resolve', kwargs={'pk': self.alert.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'resolved')
        
        # Verify alert was updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'resolved')
        self.assertIsNotNone(self.alert.resolved_at)
    
    def test_filter_alerts_by_status(self):
        """Test filtering alerts by status"""
        # Create additional alert with different status
        PerformanceAlert.objects.create(
            alert_type='threshold',
            name='Resolved Alert',
            description='Resolved alert',
            metric_type='cpu_usage',
            threshold_value=80.0,
            current_value=85.0,
            severity='high',
            status='resolved'
        )
        
        url = reverse('performancealert-list')
        response = self.client.get(url, {'status': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'active')
    
    def test_check_thresholds_endpoint(self):
        """Test manual threshold checking"""
        url = reverse('performancealert-check-thresholds')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alerts_created', response.data)
        self.assertIn('alerts', response.data)


class DatabasePerformanceLogAPITest(APITestCase):
    """Test DatabasePerformanceLog API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.db_log = DatabasePerformanceLog.objects.create(
            query='SELECT * FROM products',
            query_hash='abc123',
            execution_time=250.0,
            database_name='ecommerce',
            query_type='SELECT',
            is_slow_query=True
        )
    
    def test_list_database_logs(self):
        """Test listing database performance logs"""
        url = reverse('databaseperformancelog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_slow_queries_only(self):
        """Test filtering slow queries only"""
        # Create fast query
        DatabasePerformanceLog.objects.create(
            query='SELECT id FROM products',
            query_hash='def456',
            execution_time=10.0,
            database_name='ecommerce',
            query_type='SELECT',
            is_slow_query=False
        )
        
        url = reverse('databaseperformancelog-list')
        response = self.client.get(url, {'slow_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_slow_query'])
    
    def test_slow_queries_analysis(self):
        """Test slow queries analysis endpoint"""
        url = reverse('databaseperformancelog-slow-queries')
        response = self.client.get(url, {'hours': 24, 'limit': 20})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

class ServerMetricsModelTest(TestCase):
    """Test ServerMetrics model"""
    
    def setUp(self):
        self.server_data = {
            'server_name': 'web-server-01',
            'server_type': 'web',
            'cpu_usage': 45.2,
            'memory_usage': 62.1,
            'memory_total': 8589934592,  # 8GB in bytes
            'disk_usage': 35.5,
            'disk_total': 107374182400,  # 100GB in bytes
            'network_in': 1024000,
            'network_out': 2048000,
            'load_average': [1.2, 1.5, 1.8],
            'active_connections': 150,
            'processes_count': 85,
            'uptime': 86400  # 1 day in seconds
        }
    
    def test_create_server_metrics(self):
        """Test creating server metrics"""
        metrics = ServerMetrics.objects.create(**self.server_data)
        
        self.assertEqual(metrics.server_name, 'web-server-01')
        self.assertEqual(metrics.server_type, 'web')
        self.assertEqual(metrics.cpu_usage, 45.2)
        self.assertEqual(metrics.memory_usage, 62.1)
        self.assertEqual(metrics.memory_total, 8589934592)
        self.assertEqual(metrics.disk_usage, 35.5)
        self.assertEqual(metrics.disk_total, 107374182400)
        self.assertEqual(metrics.network_in, 1024000)
        self.assertEqual(metrics.network_out, 2048000)
        self.assertEqual(metrics.load_average, [1.2, 1.5, 1.8])
        self.assertEqual(metrics.active_connections, 150)
        self.assertEqual(metrics.processes_count, 85)
        self.assertEqual(metrics.uptime, 86400)
        self.assertIsNotNone(metrics.id)
        self.assertIsNotNone(metrics.timestamp)


class UserExperienceMetricsModelTest(TestCase):
    """Test UserExperienceMetrics model"""
    
    def setUp(self):
        self.ux_data = {
            'session_id': 'session_123456',
            'user_id': 'user_789',
            'page_url': 'https://example.com/products',
            'page_load_time': 2500.0,
            'dom_content_loaded': 1800.0,
            'first_contentful_paint': 1200.0,
            'largest_contentful_paint': 2200.0,
            'first_input_delay': 50.0,
            'cumulative_layout_shift': 0.1,
            'time_to_interactive': 3000.0,
            'bounce_rate': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'device_type': 'desktop',
            'browser': 'Chrome',
            'os': 'Windows',
            'screen_resolution': '1920x1080',
            'connection_type': '4g',
            'geographic_location': 'US-CA'
        }
    
    def test_create_ux_metrics(self):
        """Test creating user experience metrics"""
        ux = UserExperienceMetrics.objects.create(**self.ux_data)
        
        self.assertEqual(ux.session_id, 'session_123456')
        self.assertEqual(ux.user_id, 'user_789')
        self.assertEqual(ux.page_url, 'https://example.com/products')
        self.assertEqual(ux.page_load_time, 2500.0)
        self.assertEqual(ux.dom_content_loaded, 1800.0)
        self.assertEqual(ux.first_contentful_paint, 1200.0)
        self.assertEqual(ux.largest_contentful_paint, 2200.0)
        self.assertEqual(ux.first_input_delay, 50.0)
        self.assertEqual(ux.cumulative_layout_shift, 0.1)
        self.assertEqual(ux.time_to_interactive, 3000.0)
        self.assertFalse(ux.bounce_rate)
        self.assertEqual(ux.device_type, 'desktop')
        self.assertEqual(ux.browser, 'Chrome')
        self.assertEqual(ux.os, 'Windows')
        self.assertEqual(ux.screen_resolution, '1920x1080')
        self.assertEqual(ux.connection_type, '4g')
        self.assertEqual(ux.geographic_location, 'US-CA')
        self.assertIsNotNone(ux.id)
        self.assertIsNotNone(ux.timestamp)


class PerformanceBenchmarkModelTest(TestCase):
    """Test PerformanceBenchmark model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.benchmark_data = {
            'name': 'API Response Time Benchmark',
            'description': 'Benchmark for API response times',
            'benchmark_type': 'response_time',
            'baseline_value': 100.0,
            'current_value': 120.0,
            'target_value': 80.0,
            'unit': 'ms',
            'improvement_percentage': -20.0,
            'test_environment': 'staging',
            'test_configuration': {'concurrent_users': 100, 'duration': '5m'},
            'test_results': {'avg': 120.0, 'p95': 200.0, 'p99': 350.0},
            'created_by': self.user
        }
    
    def test_create_benchmark(self):
        """Test creating a performance benchmark"""
        benchmark = PerformanceBenchmark.objects.create(**self.benchmark_data)
        
        self.assertEqual(benchmark.name, 'API Response Time Benchmark')
        self.assertEqual(benchmark.description, 'Benchmark for API response times')
        self.assertEqual(benchmark.benchmark_type, 'response_time')
        self.assertEqual(benchmark.baseline_value, 100.0)
        self.assertEqual(benchmark.current_value, 120.0)
        self.assertEqual(benchmark.target_value, 80.0)
        self.assertEqual(benchmark.unit, 'ms')
        self.assertEqual(benchmark.improvement_percentage, -20.0)
        self.assertEqual(benchmark.test_environment, 'staging')
        self.assertEqual(benchmark.test_configuration, {'concurrent_users': 100, 'duration': '5m'})
        self.assertEqual(benchmark.test_results, {'avg': 120.0, 'p95': 200.0, 'p99': 350.0})
        self.assertEqual(benchmark.created_by, self.user)
        self.assertIsNotNone(benchmark.id)
        self.assertIsNotNone(benchmark.created_at)
        self.assertIsNotNone(benchmark.updated_at)


class PerformanceReportModelTest(TestCase):
    """Test PerformanceReport model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_data = {
            'name': 'Weekly Performance Report',
            'report_type': 'weekly',
            'date_range_start': timezone.now() - timedelta(days=7),
            'date_range_end': timezone.now(),
            'metrics_included': ['response_time', 'cpu_usage', 'memory_usage'],
            'report_data': {
                'response_time': {'avg': 150.0, 'p95': 300.0},
                'cpu_usage': {'avg': 45.2, 'max': 78.5},
                'memory_usage': {'avg': 62.1, 'max': 85.3}
            },
            'insights': 'Performance is within acceptable limits',
            'recommendations': 'Consider optimizing database queries',
            'generated_by': self.user,
            'is_scheduled': True,
            'schedule_config': {'frequency': 'weekly', 'day': 'monday'}
        }
    
    def test_create_report(self):
        """Test creating a performance report"""
        report = PerformanceReport.objects.create(**self.report_data)
        
        self.assertEqual(report.name, 'Weekly Performance Report')
        self.assertEqual(report.report_type, 'weekly')
        self.assertEqual(report.metrics_included, ['response_time', 'cpu_usage', 'memory_usage'])
        self.assertIn('response_time', report.report_data)
        self.assertIn('cpu_usage', report.report_data)
        self.assertIn('memory_usage', report.report_data)
        self.assertEqual(report.insights, 'Performance is within acceptable limits')
        self.assertEqual(report.recommendations, 'Consider optimizing database queries')
        self.assertEqual(report.generated_by, self.user)
        self.assertTrue(report.is_scheduled)
        self.assertEqual(report.schedule_config, {'frequency': 'weekly', 'day': 'monday'})
        self.assertIsNotNone(report.id)
        self.assertIsNotNone(report.generated_at)


class PerformanceMetricAPITest(APITestCase):
    """Test PerformanceMetric API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test metrics
        base_time = timezone.now() - timedelta(hours=2)
        for i in range(5):
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Test Metric',
                value=100 + (i * 20),
                unit='ms',
                source='web_server',
                endpoint='/api/test/',
                timestamp=base_time + timedelta(minutes=i * 10)
            )
    
    def test_list_metrics(self):
        """Test listing performance metrics"""
        url = reverse('performancemetric-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
    
    def test_filter_metrics_by_type(self):
        """Test filtering metrics by type"""
        url = reverse('performancemetric-list')
        response = self.client.get(url, {'metric_type': 'response_time'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        
        for metric in response.data['results']:
            self.assertEqual(metric['metric_type'], 'response_time')
    
    def test_filter_metrics_by_date_range(self):
        """Test filtering metrics by date range"""
        url = reverse('performancemetric-list')
        start_date = (timezone.now() - timedelta(hours=1)).isoformat()
        end_date = timezone.now().isoformat()
        
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return metrics within the date range
        self.assertGreaterEqual(len(response.data['results']), 0)
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard statistics endpoint"""
        url = reverse('performancemetric-dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response_time', response.data)
        self.assertIn('error_rate', response.data)
        self.assertIn('cpu_usage', response.data)
        self.assertIn('memory_usage', response.data)
        self.assertIn('active_alerts', response.data)
        self.assertIn('slow_queries', response.data)
        self.assertIn('timestamp', response.data)
    
    def test_time_series_endpoint(self):
        """Test time series data endpoint"""
        url = reverse('performancemetric-time-series')
        response = self.client.get(url, {
            'metric_type': 'response_time',
            'hours': 24,
            'interval': 'hour'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['metric_type'], 'response_time')
        self.assertEqual(response.data['interval'], 'hour')
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)
    
    def test_top_endpoints_endpoint(self):
        """Test top endpoints analysis"""
        url = reverse('performancemetric-top-endpoints')
        response = self.client.get(url, {
            'hours': 24,
            'limit': 10,
            'sort_by': 'slowest'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        if response.data:
            endpoint_data = response.data[0]
            self.assertIn('endpoint', endpoint_data)
            self.assertIn('avg_time', endpoint_data)
            self.assertIn('max_time', endpoint_data)
            self.assertIn('min_time', endpoint_data)
            self.assertIn('request_count', endpoint_data)
    
    def test_anomalies_endpoint(self):
        """Test anomaly detection endpoint"""
        # Create an anomalous metric
        PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Anomaly',
            value=5000,  # Very high value
            unit='ms',
            source='web_server',
            timestamp=timezone.now()
        )
        
        url = reverse('performancemetric-anomalies')
        response = self.client.get(url, {
            'metric_type': 'response_time',
            'hours': 24
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metric_type', response.data)
        self.assertIn('anomalies_count', response.data)
        self.assertIn('anomalies', response.data)
        self.assertEqual(response.data['metric_type'], 'response_time')
    
    def test_create_metric(self):
        """Test creating a new performance metric"""
        url = reverse('performancemetric-list')
        data = {
            'metric_type': 'cpu_usage',
            'name': 'CPU Usage Test',
            'value': 75.5,
            'unit': '%',
            'source': 'system_monitor',
            'severity': 'medium'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['metric_type'], 'cpu_usage')
        self.assertEqual(response.data['name'], 'CPU Usage Test')
        self.assertEqual(response.data['value'], 75.5)
        self.assertEqual(response.data['unit'], '%')
        self.assertEqual(response.data['source'], 'system_monitor')
        self.assertEqual(response.data['severity'], 'medium')


class PerformanceAlertAPITest(APITestCase):
    """Test PerformanceAlert API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test alert
        self.alert = PerformanceAlert.objects.create(
            alert_type='threshold',
            name='High Response Time Alert',
            description='Response time exceeded threshold',
            metric_type='response_time',
            threshold_value=2000.0,
            current_value=2500.0,
            severity='high'
        )
    
    def test_list_alerts(self):
        """Test listing performance alerts"""
        url = reverse('performancealert-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'High Response Time Alert')
    
    def test_filter_alerts_by_status(self):
        """Test filtering alerts by status"""
        url = reverse('performancealert-list')
        response = self.client.get(url, {'status': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'active')
    
    def test_filter_alerts_by_severity(self):
        """Test filtering alerts by severity"""
        url = reverse('performancealert-list')
        response = self.client.get(url, {'severity': 'high'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['severity'], 'high')
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        url = reverse('performancealert-acknowledge', kwargs={'pk': self.alert.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'acknowledged')
        
        # Verify alert was updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'acknowledged')
        self.assertIsNotNone(self.alert.acknowledged_at)
        self.assertEqual(self.alert.acknowledged_by, self.user)
    
    def test_resolve_alert(self):
        """Test resolving an alert"""
        url = reverse('performancealert-resolve', kwargs={'pk': self.alert.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'resolved')
        
        # Verify alert was updated
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'resolved')
        self.assertIsNotNone(self.alert.resolved_at)
    
    def test_check_thresholds_endpoint(self):
        """Test manual threshold checking"""
        # Create metrics that should trigger alerts
        PerformanceMetric.objects.create(
            metric_type='cpu_usage',
            name='High CPU',
            value=85,  # Exceeds threshold
            unit='%',
            timestamp=timezone.now()
        )
        
        url = reverse('performancealert-check-thresholds')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alerts_created', response.data)
        self.assertIn('alerts', response.data)
        self.assertIsInstance(response.data['alerts_created'], int)
        self.assertIsInstance(response.data['alerts'], list)


class DatabasePerformanceLogAPITest(APITestCase):
    """Test DatabasePerformanceLog API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test database logs
        for i in range(3):
            DatabasePerformanceLog.objects.create(
                query=f'SELECT * FROM products WHERE id = {i}',
                query_hash=f'hash_{i}',
                execution_time=100 + (i * 50),
                rows_examined=1000,
                rows_returned=1,
                database_name='ecommerce',
                table_names=['products'],
                query_type='SELECT',
                is_slow_query=i > 0  # Make some slow queries
            )
    
    def test_list_database_logs(self):
        """Test listing database performance logs"""
        url = reverse('databaseperformancelog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_filter_slow_queries_only(self):
        """Test filtering for slow queries only"""
        url = reverse('databaseperformancelog-list')
        response = self.client.get(url, {'slow_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only slow queries
        
        for log in response.data['results']:
            self.assertTrue(log['is_slow_query'])
    
    def test_slow_queries_analysis(self):
        """Test slow queries analysis endpoint"""
        url = reverse('databaseperformancelog-slow-queries')
        response = self.client.get(url, {
            'hours': 24,
            'limit': 10
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        if response.data:
            query_data = response.data[0]
            self.assertIn('query_hash', query_data)
            self.assertIn('count', query_data)
            self.assertIn('avg_time', query_data)
            self.assertIn('max_time', query_data)
            self.assertIn('query_sample', query_data)


class ApplicationPerformanceMonitorAPITest(APITestCase):
    """Test ApplicationPerformanceMonitor API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test APM records
        base_time = timezone.now() - timedelta(hours=1)
        for i in range(3):
            ApplicationPerformanceMonitor.objects.create(
                transaction_id=f'txn_{i}',
                transaction_type='web_request',
                name=f'GET /api/endpoint/{i}',
                duration=100 + (i * 50),
                start_time=base_time + timedelta(minutes=i * 10),
                end_time=base_time + timedelta(minutes=i * 10, milliseconds=100 + (i * 50)),
                status_code=200 if i < 2 else 500  # Make one error
            )
    
    def test_list_apm_records(self):
        """Test listing APM records"""
        url = reverse('applicationperformancemonitor-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_filter_by_transaction_type(self):
        """Test filtering by transaction type"""
        url = reverse('applicationperformancemonitor-list')
        response = self.client.get(url, {'transaction_type': 'web_request'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        
        for record in response.data['results']:
            self.assertEqual(record['transaction_type'], 'web_request')
    
    def test_transaction_stats_endpoint(self):
        """Test transaction statistics endpoint"""
        url = reverse('applicationperformancemonitor-transaction-stats')
        response = self.client.get(url, {'hours': 24})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)
        self.assertIn('transaction_types', response.data)
        
        stats = response.data['stats']
        self.assertIn('total_transactions', stats)
        self.assertIn('avg_duration', stats)
        self.assertIn('max_duration', stats)
        self.assertIn('error_count', stats)
        
        self.assertEqual(stats['total_transactions'], 3)
        self.assertEqual(stats['error_count'], 1)  # One error record


class PerformanceReportAPITest(APITestCase):
    """Test PerformanceReport API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data for reports
        base_time = timezone.now() - timedelta(days=1)
        for i in range(5):
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Test Metric',
                value=100 + (i * 20),
                unit='ms',
                timestamp=base_time + timedelta(hours=i * 2)
            )
            
            DatabasePerformanceLog.objects.create(
                query=f'SELECT * FROM test WHERE id = {i}',
                query_hash=f'hash_{i}',
                execution_time=50 + (i * 10),
                database_name='test',
                query_type='SELECT',
                is_slow_query=i > 2,
                timestamp=base_time + timedelta(hours=i * 2)
            )
    
    def test_generate_custom_report(self):
        """Test generating a custom performance report"""
        url = reverse('performancereport-generate-report')
        data = {
            'report_type': 'custom',
            'start_date': (timezone.now() - timedelta(days=2)).isoformat(),
            'end_date': timezone.now().isoformat(),
            'metrics_included': ['response_time', 'database']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertIn('report_type', response.data)
        self.assertIn('report_data', response.data)
        self.assertIn('insights', response.data)
        self.assertIn('recommendations', response.data)
        
        # Verify report data structure
        report_data = response.data['report_data']
        self.assertIn('response_time', report_data)
        self.assertIn('database', report_data)
        
        # Verify response time analysis
        response_time_data = report_data['response_time']
        self.assertIn('count', response_time_data)
        self.assertIn('avg', response_time_data)
        self.assertIn('min', response_time_data)
        self.assertIn('max', response_time_data)
        
        # Verify database analysis
        database_data = report_data['database']
        self.assertIn('slow_queries', database_data)
        self.assertIn('total_queries', database_data)
    
    def test_capacity_planning_endpoint(self):
        """Test capacity planning analysis"""
        # Create historical CPU usage data
        base_time = timezone.now() - timedelta(days=30)
        for i in range(30):
            PerformanceMetric.objects.create(
                metric_type='cpu_usage',
                name='CPU Usage',
                value=50 + (i * 0.5),  # Increasing trend
                unit='%',
                timestamp=base_time + timedelta(days=i)
            )
        
        url = reverse('performancereport-capacity-planning')
        response = self.client.get(url, {'days_ahead': 30})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('forecasts', response.data)
        self.assertIn('recommendations', response.data)
        self.assertIn('days_ahead', response.data)
        
        self.assertEqual(response.data['days_ahead'], 30)
        self.assertIsInstance(response.data['forecasts'], dict)
        self.assertIsInstance(response.data['recommendations'], list)


class PerformanceIncidentAPITest(APITestCase):
    """Test PerformanceIncident API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test incident
        self.incident = PerformanceIncident.objects.create(
            incident_id='PERF-0001',
            title='Database Performance Issue',
            description='Slow database queries affecting response times',
            incident_type='degradation',
            severity='high',
            affected_services=['api', 'web'],
            created_by=self.user
        )
    
    def test_list_incidents(self):
        """Test listing performance incidents"""
        url = reverse('performanceincident-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['incident_id'], 'PERF-0001')
    
    def test_create_incident(self):
        """Test creating a new incident"""
        url = reverse('performanceincident-list')
        data = {
            'title': 'High Memory Usage',
            'description': 'Memory usage exceeding 90%',
            'incident_type': 'capacity_issue',
            'severity': 'medium',
            'affected_services': ['web']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'High Memory Usage')
        self.assertEqual(response.data['incident_type'], 'capacity_issue')
        self.assertEqual(response.data['severity'], 'medium')
        self.assertEqual(response.data['affected_services'], ['web'])
        self.assertEqual(response.data['created_by'], self.user.id)
        self.assertIn('incident_id', response.data)
        self.assertTrue(response.data['incident_id'].startswith('PERF-'))
    
    def test_update_incident_status(self):
        """Test updating incident status"""
        url = reverse('performanceincident-update-status', kwargs={'pk': self.incident.pk})
        data = {
            'status': 'investigating',
            'comment': 'Started investigating the issue'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'updated')
        
        # Verify incident was updated
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'investigating')
        self.assertEqual(len(self.incident.timeline), 1)
        
        timeline_entry = self.incident.timeline[0]
        self.assertEqual(timeline_entry['action'], 'status_change')
        self.assertEqual(timeline_entry['old_status'], 'open')
        self.assertEqual(timeline_entry['new_status'], 'investigating')
        self.assertEqual(timeline_entry['user'], self.user.username)
        self.assertEqual(timeline_entry['comment'], 'Started investigating the issue')
    
    def test_add_timeline_entry(self):
        """Test adding timeline entry to incident"""
        url = reverse('performanceincident-add-timeline-entry', kwargs={'pk': self.incident.pk})
        data = {
            'action': 'comment',
            'comment': 'Found root cause in database queries',
            'metadata': {'query_count': 15}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'timeline_updated')
        
        # Verify timeline was updated
        self.incident.refresh_from_db()
        self.assertEqual(len(self.incident.timeline), 1)
        
        timeline_entry = self.incident.timeline[0]
        self.assertEqual(timeline_entry['action'], 'comment')
        self.assertEqual(timeline_entry['comment'], 'Found root cause in database queries')
        self.assertEqual(timeline_entry['metadata'], {'query_count': 15})
        self.assertEqual(timeline_entry['user'], self.user.username)


class PerformanceBenchmarkAPITest(APITestCase):
    """Test PerformanceBenchmark API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_benchmarks(self):
        """Test listing performance benchmarks"""
        # Create test benchmark
        PerformanceBenchmark.objects.create(
            name='API Response Time Benchmark',
            description='Benchmark for API response times',
            benchmark_type='response_time',
            baseline_value=100.0,
            current_value=120.0,
            target_value=80.0,
            unit='ms',
            test_environment='staging',
            created_by=self.user
        )
        
        url = reverse('performancebenchmark-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'API Response Time Benchmark')
    
    def test_run_benchmark(self):
        """Test running a performance benchmark"""
        url = reverse('performancebenchmark-run-benchmark')
        data = {
            'benchmark_type': 'response_time',
            'test_configuration': {
                'concurrent_users': 50,
                'duration': '2m',
                'endpoint': '/api/products/'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertIn('benchmark_type', response.data)
        self.assertIn('test_configuration', response.data)
        self.assertIn('test_results', response.data)
        self.assertEqual(response.data['benchmark_type'], 'response_time')
        self.assertEqual(response.data['created_by'], self.user.id)
        
        # Verify test results structure
        test_results = response.data['test_results']
        self.assertIn('response_time', test_results)
        self.assertIn('throughput', test_results)
        self.assertIn('resource_usage', test_results)


class PerformanceIntegrationTest(TransactionTestCase):
    """Integration tests for performance monitoring system"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_end_to_end_performance_monitoring(self):
        """Test complete performance monitoring workflow"""
        # 1. Create performance metrics
        metric = PerformanceMetric.objects.create(
            metric_type='response_time',
            name='API Response Time',
            value=2500.0,  # High response time
            unit='ms',
            source='web_server',
            endpoint='/api/products/',
            severity='high'
        )
        
        # 2. Check if alerts are triggered
        alerts = AlertManager.check_thresholds()
        self.assertGreater(len(alerts), 0)
        
        # 3. Verify alert was created
        alert = PerformanceAlert.objects.filter(
            metric_type='response_time',
            status='active'
        ).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, 'high')
        
        # 4. Create incident from alert
        incident = PerformanceIncident.objects.create(
            incident_id='PERF-0001',
            title='High Response Time Alert',
            description=f'Response time alert: {alert.description}',
            incident_type='degradation',
            severity=alert.severity,
            affected_services=['api'],
            created_by=self.user
        )
        
        # 5. Update incident status
        incident.status = 'investigating'
        incident.timeline.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'status_change',
            'old_status': 'open',
            'new_status': 'investigating',
            'user': self.user.username,
            'comment': 'Started investigation'
        })
        incident.save()
        
        # 6. Generate performance report
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=1)
        
        insights = PerformanceAnalyzer.generate_performance_insights(start_date, end_date)
        self.assertGreater(len(insights), 0)
        
        # 7. Create performance report
        report = PerformanceReport.objects.create(
            name='Incident Analysis Report',
            report_type='custom',
            date_range_start=start_date,
            date_range_end=end_date,
            metrics_included=['response_time'],
            report_data={'response_time': {'avg': 2500.0, 'max': 2500.0}},
            insights=json.dumps(insights),
            recommendations='Optimize database queries and add caching',
            generated_by=self.user
        )
        
        # 8. Resolve incident
        incident.status = 'resolved'
        incident.resolved_at = timezone.now()
        incident.resolution = 'Optimized database queries and added caching'
        incident.timeline.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'status_change',
            'old_status': 'investigating',
            'new_status': 'resolved',
            'user': self.user.username,
            'comment': 'Issue resolved'
        })
        incident.save()
        
        # 9. Resolve alert
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        # Verify final state
        self.assertEqual(incident.status, 'resolved')
        self.assertEqual(alert.status, 'resolved')
        self.assertIsNotNone(report.id)
        self.assertEqual(len(incident.timeline), 2)
    
    def test_capacity_planning_workflow(self):
        """Test capacity planning workflow"""
        # Create historical data showing increasing trend
        base_time = timezone.now() - timedelta(days=30)
        
        for i in range(30):
            PerformanceMetric.objects.create(
                metric_type='cpu_usage',
                name='CPU Usage',
                value=50 + (i * 1.0),  # Increasing from 50% to 79%
                unit='%',
                timestamp=base_time + timedelta(days=i)
            )
        
        # Generate capacity forecast
        forecast = CapacityPlanner.forecast_resource_usage('cpu_usage', 30)
        
        self.assertIsNotNone(forecast)
        self.assertEqual(forecast['trend'], 'increasing')
        self.assertGreater(forecast['slope'], 0)
        self.assertEqual(len(forecast['forecast']), 30)
        
        # Generate recommendations
        recommendations = CapacityPlanner.generate_capacity_recommendations()
        
        self.assertIsInstance(recommendations, list)
        # Should have CPU recommendation due to increasing trend
        cpu_recommendations = [
            rec for rec in recommendations 
            if rec['resource'] == 'cpu'
        ]
        self.assertGreater(len(cpu_recommendations), 0)
        
        # Create capacity planning report
        report = PerformanceReport.objects.create(
            name='Capacity Planning Report',
            report_type='capacity',
            date_range_start=base_time,
            date_range_end=timezone.now(),
            metrics_included=['cpu_usage'],
            report_data={
                'forecast': forecast,
                'recommendations': recommendations
            },
            insights='CPU usage is trending upward',
            recommendations=json.dumps(recommendations),
            generated_by=self.user
        )
        
        self.assertIsNotNone(report.id)
        self.assertEqual(report.report_type, 'capacity')
class PerformanceReportAPITest(APITestCase):
    """Test PerformanceReport API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test data for reports
        base_time = timezone.now() - timedelta(days=1)
        for i in range(5):
            PerformanceMetric.objects.create(
                metric_type='response_time',
                name='Test Metric',
                value=100 + (i * 10),
                unit='ms',
                timestamp=base_time + timedelta(hours=i)
            )
    
    def test_generate_custom_report(self):
        """Test generating a custom performance report"""
        url = reverse('performancereport-generate-report')
        data = {
            'report_type': 'custom',
            'start_date': (timezone.now() - timedelta(days=2)).isoformat(),
            'end_date': timezone.now().isoformat(),
            'metrics_included': ['response_time', 'database']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertIn('report_type', response.data)
        self.assertIn('report_data', response.data)
        self.assertEqual(response.data['report_type'], 'custom')
    
    def test_capacity_planning_endpoint(self):
        """Test capacity planning analysis"""
        url = reverse('performancereport-capacity-planning')
        response = self.client.get(url, {'days_ahead': 30})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('forecasts', response.data)
        self.assertIn('recommendations', response.data)
        self.assertIn('days_ahead', response.data)
        self.assertEqual(response.data['days_ahead'], 30)


class PerformanceIncidentAPITest(APITestCase):
    """Test PerformanceIncident API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.incident = PerformanceIncident.objects.create(
            incident_id='PERF-0001',
            title='Test Incident',
            description='Test incident description',
            incident_type='degradation',
            severity='medium',
            created_by=self.user
        )
    
    def test_create_incident(self):
        """Test creating a performance incident"""
        url = reverse('performanceincident-list')
        data = {
            'title': 'New Performance Issue',
            'description': 'Database queries are running slowly',
            'incident_type': 'degradation',
            'severity': 'high',
            'affected_services': ['api', 'web']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Performance Issue')
        self.assertIn('incident_id', response.data)
        self.assertTrue(response.data['incident_id'].startswith('PERF-'))
    
    def test_update_incident_status(self):
        """Test updating incident status"""
        url = reverse('performanceincident-update-status', kwargs={'pk': self.incident.pk})
        data = {
            'status': 'investigating',
            'comment': 'Started investigation into the issue'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'updated')
        
        # Verify incident was updated
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'investigating')
        self.assertEqual(len(self.incident.timeline), 1)
        self.assertEqual(self.incident.timeline[0]['action'], 'status_change')
    
    def test_add_timeline_entry(self):
        """Test adding timeline entry to incident"""
        url = reverse('performanceincident-add-timeline-entry', kwargs={'pk': self.incident.pk})
        data = {
            'action': 'comment',
            'comment': 'Found root cause in database queries',
            'metadata': {'query_count': 150}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'timeline_updated')
        
        # Verify timeline was updated
        self.incident.refresh_from_db()
        self.assertEqual(len(self.incident.timeline), 1)
        self.assertEqual(self.incident.timeline[0]['action'], 'comment')
        self.assertEqual(self.incident.timeline[0]['comment'], 'Found root cause in database queries')


class PerformanceBenchmarkAPITest(APITestCase):
    """Test PerformanceBenchmark API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_benchmark(self):
        """Test creating a performance benchmark"""
        url = reverse('performancebenchmark-list')
        data = {
            'name': 'API Response Time Benchmark',
            'description': 'Benchmark for API response times',
            'benchmark_type': 'response_time',
            'baseline_value': 100.0,
            'current_value': 120.0,
            'target_value': 80.0,
            'unit': 'ms'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'API Response Time Benchmark')
        self.assertEqual(response.data['created_by'], self.user.id)
    
    def test_run_benchmark(self):
        """Test running a benchmark test"""
        url = reverse('performancebenchmark-run-benchmark')
        data = {
            'benchmark_type': 'load_test',
            'test_configuration': {
                'concurrent_users': 100,
                'duration': 300,
                'ramp_up': 60
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertIn('test_results', response.data)
        self.assertEqual(response.data['benchmark_type'], 'load_test')


class PerformanceMiddlewareTest(TestCase):
    """Test performance monitoring middleware"""
    
    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()
    
    @patch('backend.apps.performance.middleware.PerformanceMetric.objects.create')
    def test_middleware_records_metrics(self, mock_create):
        """Test that middleware records performance metrics"""
        from backend.apps.performance.middleware import PerformanceMonitoringMiddleware
        
        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse('OK')
        
        middleware = PerformanceMonitoringMiddleware(get_response)
        request = self.factory.get('/api/test/')
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 200)
        # Verify that metric was created
        mock_create.assert_called_once()


class PerformanceSignalsTest(TestCase):
    """Test performance monitoring signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('backend.apps.performance.signals.AlertManager.check_thresholds')
    def test_metric_created_signal(self, mock_check_thresholds):
        """Test signal triggered when metric is created"""
        # Create a metric that should trigger threshold checking
        PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Test Metric',
            value=2500.0,  # High value
            unit='ms'
        )
        
        # Verify that threshold checking was triggered
        mock_check_thresholds.assert_called_once()


class PerformanceManagementCommandsTest(TestCase):
    """Test performance management commands"""
    
    def setUp(self):
        # Create test data
        old_time = timezone.now() - timedelta(days=35)
        PerformanceMetric.objects.create(
            metric_type='response_time',
            name='Old Metric',
            value=100.0,
            unit='ms',
            timestamp=old_time
        )
    
    def test_cleanup_performance_data_command(self):
        """Test cleanup performance data command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('cleanup_performance_data', stdout=out)
        
        # Verify old data was cleaned up
        old_metrics = PerformanceMetric.objects.filter(
            timestamp__lt=timezone.now() - timedelta(days=30)
        )
        self.assertEqual(old_metrics.count(), 0)
    
    @patch('backend.apps.performance.utils.AlertManager.check_thresholds')
    def test_check_performance_alerts_command(self, mock_check_thresholds):
        """Test check performance alerts command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('check_performance_alerts', stdout=out)
        
        # Verify threshold checking was called
        mock_check_thresholds.assert_called_once()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_collect_system_metrics_command(self, mock_memory, mock_cpu):
        """Test collect system metrics command"""
        from django.core.management import call_command
        from io import StringIO
        
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=62.3)
        
        out = StringIO()
        call_command('collect_system_metrics', stdout=out)
        
        # Verify metrics were created
        cpu_metrics = PerformanceMetric.objects.filter(metric_type='cpu_usage')
        memory_metrics = PerformanceMetric.objects.filter(metric_type='memory_usage')
        
        self.assertGreater(cpu_metrics.count(), 0)
        self.assertGreater(memory_metrics.count(), 0)


class PerformanceIntegrationTest(TransactionTestCase):
    """Integration tests for performance monitoring system"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_end_to_end_performance_monitoring(self):
        """Test complete performance monitoring workflow"""
        # 1. Create performance metrics
        metric = PerformanceMetric.objects.create(
            metric_type='response_time',
            name='API Response Time',
            value=2500.0,  # High value to trigger alert
            unit='ms',
            endpoint='/api/products/'
        )
        
        # 2. Check that alert is created
        alerts = AlertManager.check_thresholds()
        self.assertGreater(len(alerts), 0)
        
        # 3. Verify alert exists in database
        alert = PerformanceAlert.objects.filter(
            metric_type='response_time',
            status='active'
        ).first()
        self.assertIsNotNone(alert)
        
        # 4. Acknowledge the alert
        alert.status = 'acknowledged'
        alert.acknowledged_by = self.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        # 5. Generate performance report
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=1)
        
        report = PerformanceReport.objects.create(
            name='Test Report',
            report_type='custom',
            date_range_start=start_date,
            date_range_end=end_date,
            metrics_included=['response_time'],
            report_data={'response_time': {'avg': 2500.0}},
            generated_by=self.user
        )
        
        # 6. Verify complete workflow
        self.assertEqual(PerformanceMetric.objects.count(), 1)
        self.assertEqual(PerformanceAlert.objects.count(), 1)
        self.assertEqual(PerformanceReport.objects.count(), 1)
        self.assertEqual(alert.status, 'acknowledged')
        self.assertEqual(report.generated_by, self.user)
    
    def test_database_performance_monitoring_workflow(self):
        """Test database performance monitoring workflow"""
        # 1. Create slow database query log
        db_log = DatabasePerformanceLog.objects.create(
            query='SELECT * FROM products WHERE name LIKE "%test%"',
            query_hash='slow_query_123',
            execution_time=5000.0,  # Very slow query
            rows_examined=100000,
            rows_returned=10,
            database_name='ecommerce',
            query_type='SELECT',
            is_slow_query=True
        )
        
        # 2. Analyze database performance
        recommendations = PerformanceOptimizer.analyze_database_performance()
        
        # 3. Verify recommendations were generated
        self.assertGreater(len(recommendations), 0)
        db_recommendation = recommendations[0]
        self.assertEqual(db_recommendation['type'], 'database_optimization')
        self.assertEqual(db_recommendation['query_hash'], 'slow_query_123')
        
        # 4. Create performance incident
        incident = PerformanceIncident.objects.create(
            incident_id='PERF-DB-001',
            title='Slow Database Queries',
            description='Multiple slow queries detected',
            incident_type='degradation',
            severity='high',
            affected_services=['api', 'web'],
            created_by=self.user
        )
        
        # 5. Update incident timeline
        timeline_entry = {
            'timestamp': timezone.now().isoformat(),
            'action': 'investigation',
            'user': self.user.username,
            'comment': 'Identified slow query pattern'
        }
        incident.timeline.append(timeline_entry)
        incident.save()
        
        # 6. Verify complete workflow
        self.assertEqual(DatabasePerformanceLog.objects.count(), 1)
        self.assertEqual(PerformanceIncident.objects.count(), 1)
        self.assertEqual(len(incident.timeline), 1)
        self.assertTrue(db_log.is_slow_query)