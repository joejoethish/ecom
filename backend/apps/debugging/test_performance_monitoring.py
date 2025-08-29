"""
Performance Monitoring Service Tests

This module provides comprehensive tests for the performance monitoring service
including metrics collection, threshold management, optimization engine, and trend analysis.
"""

import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import (
    PerformanceSnapshot, PerformanceThreshold, WorkflowSession, 
    TraceStep, ErrorLog
)
from .performance_monitoring import (
    MetricsCollector, ThresholdManager, OptimizationEngine, 
    TrendAnalyzer, PerformanceMonitoringService,
    MetricData, ThresholdAlert, OptimizationRecommendation, TrendAnalysis
)

User = get_user_model()


class MetricsCollectorTestCase(TestCase):
    """Test cases for MetricsCollector"""
    
    def setUp(self):
        self.collector = MetricsCollector()
    
    def test_manual_metric_collection(self):
        """Test manual metric collection"""
        # Create a threshold for testing
        PerformanceThreshold.objects.create(
            metric_name='response_time',
            layer='api',
            component='test_component',
            warning_threshold=200.0,
            critical_threshold=500.0,
            enabled=True
        )
        
        # Collect a metric
        self.collector.collect_manual_metric(
            layer='api',
            component='test_component',
            metric_name='response_time',
            metric_value=150.0,
            correlation_id=str(uuid.uuid4()),
            metadata={'test': 'data'}
        )
        
        # Verify metric was stored
        snapshot = PerformanceSnapshot.objects.filter(
            layer='api',
            component='test_component',
            metric_name='response_time'
        ).first()
        
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.metric_value, 150.0)
        self.assertEqual(snapshot.threshold_warning, 200.0)
        self.assertEqual(snapshot.threshold_critical, 500.0)
        self.assertEqual(snapshot.metadata['test'], 'data')
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_system_metrics_collection(self, mock_net, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 75.5
        mock_memory.return_value = MagicMock(percent=80.2, used=8589934592)  # 8GB
        mock_disk.return_value = MagicMock(used=500000000000, total=1000000000000)  # 50% usage
        mock_net.return_value = MagicMock(bytes_sent=1000000, bytes_recv=2000000)
        
        # Collect system metrics
        timestamp = timezone.now()
        self.collector._collect_system_metrics(timestamp)
        
        # Flush buffer to database
        self.collector._flush_metrics_buffer()
        
        # Verify metrics were collected
        cpu_snapshot = PerformanceSnapshot.objects.filter(
            layer='system',
            component='cpu',
            metric_name='cpu_usage'
        ).first()
        self.assertIsNotNone(cpu_snapshot)
        self.assertEqual(cpu_snapshot.metric_value, 75.5)
        
        memory_snapshot = PerformanceSnapshot.objects.filter(
            layer='system',
            component='memory',
            metric_name='memory_usage'
        ).first()
        self.assertIsNotNone(memory_snapshot)
        self.assertEqual(memory_snapshot.metric_value, 80.2)
    
    def test_metrics_buffer_flush(self):
        """Test metrics buffer flushing"""
        # Add multiple metrics to buffer
        timestamp = timezone.now()
        for i in range(5):
            self.collector._add_metric(
                layer='test',
                component=f'component_{i}',
                metric_name='test_metric',
                metric_value=float(i * 10),
                timestamp=timestamp
            )
        
        # Verify buffer has metrics
        self.assertEqual(len(self.collector._metrics_buffer), 5)
        
        # Flush buffer
        self.collector._flush_metrics_buffer()
        
        # Verify buffer is empty and metrics are in database
        self.assertEqual(len(self.collector._metrics_buffer), 0)
        self.assertEqual(PerformanceSnapshot.objects.count(), 5)


class ThresholdManagerTestCase(TestCase):
    """Test cases for ThresholdManager"""
    
    def setUp(self):
        self.threshold_manager = ThresholdManager()
    
    def test_create_threshold(self):
        """Test threshold creation"""
        threshold = self.threshold_manager.create_threshold(
            metric_name='response_time',
            layer='api',
            component='test_component',
            warning_threshold=200.0,
            critical_threshold=500.0
        )
        
        self.assertIsNotNone(threshold)
        self.assertEqual(threshold.metric_name, 'response_time')
        self.assertEqual(threshold.layer, 'api')
        self.assertEqual(threshold.component, 'test_component')
        self.assertEqual(threshold.warning_threshold, 200.0)
        self.assertEqual(threshold.critical_threshold, 500.0)
        self.assertTrue(threshold.enabled)
    
    def test_update_existing_threshold(self):
        """Test updating existing threshold"""
        # Create initial threshold
        threshold1 = self.threshold_manager.create_threshold(
            metric_name='response_time',
            layer='api',
            component='test_component',
            warning_threshold=200.0,
            critical_threshold=500.0
        )
        
        # Update the same threshold
        threshold2 = self.threshold_manager.create_threshold(
            metric_name='response_time',
            layer='api',
            component='test_component',
            warning_threshold=150.0,
            critical_threshold=400.0
        )
        
        # Should be the same object with updated values
        self.assertEqual(threshold1.id, threshold2.id)
        self.assertEqual(threshold2.warning_threshold, 150.0)
        self.assertEqual(threshold2.critical_threshold, 400.0)
    
    def test_threshold_violation_detection(self):
        """Test threshold violation detection"""
        # Create threshold
        self.threshold_manager.create_threshold(
            metric_name='response_time',
            layer='api',
            component='test_component',
            warning_threshold=200.0,
            critical_threshold=500.0
        )
        
        # Create test metrics
        metrics = [
            MetricData(
                layer='api',
                component='test_component',
                metric_name='response_time',
                metric_value=150.0,  # Normal
                timestamp=timezone.now()
            ),
            MetricData(
                layer='api',
                component='test_component',
                metric_name='response_time',
                metric_value=250.0,  # Warning
                timestamp=timezone.now()
            ),
            MetricData(
                layer='api',
                component='test_component',
                metric_name='response_time',
                metric_value=600.0,  # Critical
                timestamp=timezone.now()
            )
        ]
        
        # Check violations
        alerts = self.threshold_manager.check_threshold_violations(metrics)
        
        # Should have 2 alerts (warning and critical)
        self.assertEqual(len(alerts), 2)
        
        # Check warning alert
        warning_alert = next((a for a in alerts if a.threshold_type == 'warning'), None)
        self.assertIsNotNone(warning_alert)
        self.assertEqual(warning_alert.current_value, 250.0)
        self.assertEqual(warning_alert.threshold_value, 200.0)
        
        # Check critical alert
        critical_alert = next((a for a in alerts if a.threshold_type == 'critical'), None)
        self.assertIsNotNone(critical_alert)
        self.assertEqual(critical_alert.current_value, 600.0)
        self.assertEqual(critical_alert.threshold_value, 500.0)
    
    def test_default_thresholds_initialization(self):
        """Test default thresholds initialization"""
        # Initialize default thresholds
        self.threshold_manager.initialize_default_thresholds()
        
        # Verify some default thresholds were created
        api_response_threshold = PerformanceThreshold.objects.filter(
            metric_name='response_time',
            layer='api',
            component=''
        ).first()
        
        self.assertIsNotNone(api_response_threshold)
        self.assertEqual(api_response_threshold.warning_threshold, 200.0)
        self.assertEqual(api_response_threshold.critical_threshold, 500.0)


class OptimizationEngineTestCase(TestCase):
    """Test cases for OptimizationEngine"""
    
    def setUp(self):
        self.optimization_engine = OptimizationEngine()
        self.base_time = timezone.now()
    
    def test_database_performance_analysis(self):
        """Test database performance analysis"""
        # Create slow query snapshots
        for i in range(5):
            PerformanceSnapshot.objects.create(
                layer='database',
                component='mysql',
                metric_name='avg_query_time',
                metric_value=250.0 + i * 10,  # 250-290ms
                timestamp=self.base_time - timedelta(minutes=i)
            )
        
        # Analyze performance issues
        recommendations = self.optimization_engine.analyze_performance_issues(hours=1)
        
        # Should have database recommendations
        db_recommendations = [r for r in recommendations if r.category == 'database']
        self.assertGreater(len(db_recommendations), 0)
        
        # Check recommendation content
        slow_query_rec = next((r for r in db_recommendations if 'slow queries' in r.title.lower()), None)
        self.assertIsNotNone(slow_query_rec)
        self.assertEqual(slow_query_rec.priority, 'high')
        self.assertIn('mysql', slow_query_rec.affected_components)
    
    def test_api_performance_analysis(self):
        """Test API performance analysis"""
        # Create slow API snapshots
        for i in range(3):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='user_api',
                metric_name='response_time',
                metric_value=600.0 + i * 50,  # 600-700ms
                timestamp=self.base_time - timedelta(minutes=i * 10)
            )
        
        # Create high error rate snapshots
        for i in range(3):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='order_api',
                metric_name='error_rate',
                metric_value=3.0 + i * 0.5,  # 3-4 errors/min
                timestamp=self.base_time - timedelta(minutes=i * 15)
            )
        
        # Analyze performance issues
        recommendations = self.optimization_engine.analyze_performance_issues(hours=2)
        
        # Should have API recommendations
        api_recommendations = [r for r in recommendations if r.category == 'api']
        self.assertGreater(len(api_recommendations), 0)
        
        # Check for slow endpoint recommendation
        slow_api_rec = next((r for r in api_recommendations if 'user_api' in r.affected_components), None)
        self.assertIsNotNone(slow_api_rec)
        self.assertEqual(slow_api_rec.priority, 'high')
        
        # Check for high error rate recommendation
        error_rate_rec = next((r for r in api_recommendations if 'error rate' in r.title.lower()), None)
        self.assertIsNotNone(error_rate_rec)
        self.assertEqual(error_rate_rec.priority, 'high')
    
    def test_system_performance_analysis(self):
        """Test system performance analysis"""
        # Create high CPU usage snapshots
        for i in range(4):
            PerformanceSnapshot.objects.create(
                layer='system',
                component='cpu',
                metric_name='cpu_usage',
                metric_value=85.0 + i * 2,  # 85-91%
                timestamp=self.base_time - timedelta(minutes=i * 5)
            )
        
        # Create high memory usage snapshots
        for i in range(4):
            PerformanceSnapshot.objects.create(
                layer='system',
                component='memory',
                metric_name='memory_usage',
                metric_value=90.0 + i,  # 90-93%
                timestamp=self.base_time - timedelta(minutes=i * 5)
            )
        
        # Analyze performance issues
        recommendations = self.optimization_engine.analyze_performance_issues(hours=1)
        
        # Should have system recommendations
        system_recommendations = [r for r in recommendations if r.category == 'system']
        self.assertGreater(len(system_recommendations), 0)
        
        # Check for CPU recommendation
        cpu_rec = next((r for r in system_recommendations if 'cpu' in r.affected_components), None)
        self.assertIsNotNone(cpu_rec)
        
        # Check for memory recommendation (should be high priority)
        memory_rec = next((r for r in system_recommendations if 'memory' in r.affected_components), None)
        self.assertIsNotNone(memory_rec)
        self.assertEqual(memory_rec.priority, 'high')


class TrendAnalyzerTestCase(TestCase):
    """Test cases for TrendAnalyzer"""
    
    def setUp(self):
        self.trend_analyzer = TrendAnalyzer()
        self.base_time = timezone.now()
    
    def test_improving_trend_detection(self):
        """Test detection of improving performance trends"""
        # Create improving trend data (decreasing response times)
        for i in range(20):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='test_api',
                metric_name='response_time',
                metric_value=500.0 - i * 10,  # 500ms down to 310ms
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(
            metric_name='response_time',
            layer='api',
            component='test_api',
            hours=24
        )
        
        self.assertEqual(len(trends), 1)
        trend = trends[0]
        
        self.assertEqual(trend.trend_direction, 'improving')
        self.assertGreater(trend.trend_strength, 0.8)  # Strong correlation
        self.assertLess(trend.percentage_change, 0)  # Negative change (improvement)
    
    def test_degrading_trend_detection(self):
        """Test detection of degrading performance trends"""
        # Create degrading trend data (increasing response times)
        for i in range(15):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='test_api',
                metric_name='response_time',
                metric_value=200.0 + i * 15,  # 200ms up to 410ms
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(
            metric_name='response_time',
            layer='api',
            component='test_api',
            hours=20
        )
        
        self.assertEqual(len(trends), 1)
        trend = trends[0]
        
        self.assertEqual(trend.trend_direction, 'degrading')
        self.assertGreater(trend.trend_strength, 0.8)  # Strong correlation
        self.assertGreater(trend.percentage_change, 0)  # Positive change (degradation)
    
    def test_stable_trend_detection(self):
        """Test detection of stable performance trends"""
        # Create stable trend data (consistent response times with small variations)
        base_value = 300.0
        for i in range(20):
            # Add small random variation
            variation = (i % 3 - 1) * 5  # -5, 0, or +5
            PerformanceSnapshot.objects.create(
                layer='api',
                component='test_api',
                metric_name='response_time',
                metric_value=base_value + variation,
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(
            metric_name='response_time',
            layer='api',
            component='test_api',
            hours=24
        )
        
        self.assertEqual(len(trends), 1)
        trend = trends[0]
        
        self.assertEqual(trend.trend_direction, 'stable')
        self.assertLess(trend.trend_strength, 0.3)  # Weak correlation
        self.assertLess(abs(trend.percentage_change), 5)  # Small change
    
    def test_trend_summary(self):
        """Test trend summary generation"""
        # Create mixed trend data
        # Improving API response times
        for i in range(15):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='api1',
                metric_name='response_time',
                metric_value=400.0 - i * 10,
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Degrading database query times
        for i in range(15):
            PerformanceSnapshot.objects.create(
                layer='database',
                component='mysql',
                metric_name='avg_query_time',
                metric_value=100.0 + i * 8,
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Stable CPU usage
        for i in range(15):
            PerformanceSnapshot.objects.create(
                layer='system',
                component='cpu',
                metric_name='cpu_usage',
                metric_value=70.0 + (i % 3 - 1) * 2,
                timestamp=self.base_time - timedelta(hours=i)
            )
        
        # Get trend summary
        summary = self.trend_analyzer.get_trend_summary(hours=20)
        
        self.assertEqual(summary['total_metrics'], 3)
        self.assertEqual(summary['improving_trends'], 1)
        self.assertEqual(summary['degrading_trends'], 1)
        self.assertEqual(summary['stable_trends'], 1)


class PerformanceMonitoringServiceTestCase(TestCase):
    """Test cases for PerformanceMonitoringService"""
    
    def setUp(self):
        self.service = PerformanceMonitoringService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        self.assertFalse(self.service._initialized)
        
        # Initialize service
        self.service.initialize()
        
        self.assertTrue(self.service._initialized)
        self.assertTrue(self.service.metrics_collector.is_collecting)
        
        # Verify default thresholds were created
        self.assertGreater(PerformanceThreshold.objects.count(), 0)
    
    def test_service_shutdown(self):
        """Test service shutdown"""
        # Initialize and then shutdown
        self.service.initialize()
        self.assertTrue(self.service._initialized)
        
        self.service.shutdown()
        
        self.assertFalse(self.service._initialized)
        self.assertFalse(self.service.metrics_collector.is_collecting)
    
    def test_system_health_summary(self):
        """Test system health summary generation"""
        # Initialize service
        self.service.initialize()
        
        # Create some test data
        base_time = timezone.now()
        
        # Add some performance snapshots
        PerformanceSnapshot.objects.create(
            layer='api',
            component='test_api',
            metric_name='response_time',
            metric_value=150.0,
            timestamp=base_time - timedelta(minutes=30)
        )
        
        # Add some errors
        ErrorLog.objects.create(
            layer='api',
            component='test_api',
            error_type='ValidationError',
            error_message='Test error',
            severity='error',
            timestamp=base_time - timedelta(minutes=15)
        )
        
        # Get health summary
        summary = self.service.get_system_health_summary()
        
        self.assertIn('timestamp', summary)
        self.assertIn('overall_health', summary)
        self.assertIn('performance_metrics', summary)
        self.assertIn('error_summary', summary)
        self.assertIn('trends', summary)
        self.assertIn('recommendations', summary)
        
        # Check overall health structure
        health = summary['overall_health']
        self.assertIn('score', health)
        self.assertIn('status', health)
        self.assertIn('issues', health)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(health['score'], 0)
        self.assertLessEqual(health['score'], 100)


class PerformanceMonitoringAPITestCase(APITestCase):
    """Test cases for Performance Monitoring API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_system_health_summary_endpoint(self):
        """Test system health summary API endpoint"""
        url = reverse('debugging:performance-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('overall_health', data)
        self.assertIn('performance_metrics', data)
        self.assertIn('error_summary', data)
    
    def test_performance_metrics_endpoint(self):
        """Test performance metrics API endpoint"""
        # Create test data
        PerformanceSnapshot.objects.create(
            layer='api',
            component='test_api',
            metric_name='response_time',
            metric_value=200.0,
            timestamp=timezone.now()
        )
        
        url = reverse('debugging:performance-metrics')
        response = self.client.get(url, {'layer': 'api', 'hours': '1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('metrics', data)
        self.assertIn('pagination', data)
        self.assertIn('filters', data)
        self.assertEqual(len(data['metrics']), 1)
        self.assertEqual(data['metrics'][0]['layer'], 'api')
    
    def test_performance_trends_endpoint(self):
        """Test performance trends API endpoint"""
        # Create trend data
        base_time = timezone.now()
        for i in range(15):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='test_api',
                metric_name='response_time',
                metric_value=200.0 + i * 5,
                timestamp=base_time - timedelta(hours=i)
            )
        
        url = reverse('debugging:performance-trends')
        response = self.client.get(url, {'layer': 'api', 'hours': '20'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('trends', data)
        self.assertIn('summary', data)
        self.assertIn('analysis_parameters', data)
    
    def test_optimization_recommendations_endpoint(self):
        """Test optimization recommendations API endpoint"""
        # Create data that will trigger recommendations
        base_time = timezone.now()
        for i in range(5):
            PerformanceSnapshot.objects.create(
                layer='database',
                component='mysql',
                metric_name='avg_query_time',
                metric_value=300.0 + i * 20,  # Slow queries
                timestamp=base_time - timedelta(minutes=i * 10)
            )
        
        url = reverse('debugging:performance-recommendations')
        response = self.client.get(url, {'hours': '2'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('recommendations', data)
        self.assertIn('total_count', data)
        self.assertIn('filters', data)
    
    def test_collect_manual_metric_endpoint(self):
        """Test manual metric collection API endpoint"""
        url = reverse('debugging:collect-manual-metric')
        data = {
            'layer': 'api',
            'component': 'test_api',
            'metric_name': 'response_time',
            'metric_value': 150.0,
            'metadata': {'test': 'data'}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertIn('message', response_data)
        self.assertIn('metric', response_data)
        
        # Verify metric was stored
        snapshot = PerformanceSnapshot.objects.filter(
            layer='api',
            component='test_api',
            metric_name='response_time'
        ).first()
        
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.metric_value, 150.0)
    
    def test_performance_thresholds_endpoint(self):
        """Test performance thresholds API endpoint"""
        # Test GET
        url = reverse('debugging:performance-thresholds-api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('thresholds', data)
        self.assertIn('total_count', data)
        
        # Test POST
        threshold_data = {
            'metric_name': 'response_time',
            'layer': 'api',
            'component': 'test_api',
            'warning_threshold': 200.0,
            'critical_threshold': 500.0
        }
        
        response = self.client.post(url, threshold_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['metric_name'], 'response_time')
        self.assertEqual(response_data['layer'], 'api')
        self.assertEqual(response_data['warning_threshold'], 200.0)
    
    def test_metrics_summary_endpoint(self):
        """Test metrics summary API endpoint"""
        # Create test data
        base_time = timezone.now()
        PerformanceSnapshot.objects.create(
            layer='api',
            component='test_api',
            metric_name='response_time',
            metric_value=200.0,
            timestamp=base_time
        )
        PerformanceSnapshot.objects.create(
            layer='database',
            component='mysql',
            metric_name='query_time',
            metric_value=50.0,
            timestamp=base_time
        )
        
        url = reverse('debugging:metrics-summary')
        response = self.client.get(url, {'hours': '1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('summary', data)
        self.assertIn('total_layers', data)
        self.assertIn('total_metrics', data)
        self.assertEqual(data['total_layers'], 2)  # api and database
    
    def test_initialize_service_endpoint(self):
        """Test service initialization API endpoint"""
        url = reverse('debugging:initialize-service')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertEqual(data['status'], 'initialized')
    
    def test_shutdown_service_endpoint(self):
        """Test service shutdown API endpoint"""
        url = reverse('debugging:shutdown-service')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertEqual(data['status'], 'shutdown')


class PerformanceMonitoringBenchmarkTestCase(TransactionTestCase):
    """Benchmark tests for performance monitoring service"""
    
    def setUp(self):
        self.service = PerformanceMonitoringService()
        self.service.initialize()
    
    def tearDown(self):
        self.service.shutdown()
    
    def test_metrics_collection_performance(self):
        """Benchmark metrics collection performance"""
        start_time = time.time()
        
        # Collect 1000 metrics
        for i in range(1000):
            self.service.metrics_collector.collect_manual_metric(
                layer='api',
                component=f'component_{i % 10}',
                metric_name='response_time',
                metric_value=float(i % 500),
                correlation_id=str(uuid.uuid4())
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(duration, 10.0, f"Metrics collection took {duration:.2f}s, expected < 10s")
        
        # Verify all metrics were stored
        self.assertEqual(PerformanceSnapshot.objects.count(), 1000)
    
    def test_trend_analysis_performance(self):
        """Benchmark trend analysis performance"""
        # Create large dataset
        base_time = timezone.now()
        snapshots = []
        
        for i in range(1000):
            snapshots.append(PerformanceSnapshot(
                layer='api',
                component='test_api',
                metric_name='response_time',
                metric_value=200.0 + (i % 100),
                timestamp=base_time - timedelta(minutes=i)
            ))
        
        PerformanceSnapshot.objects.bulk_create(snapshots)
        
        # Benchmark trend analysis
        start_time = time.time()
        
        trends = self.service.trend_analyzer.analyze_trends(
            metric_name='response_time',
            layer='api',
            hours=24
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 5.0, f"Trend analysis took {duration:.2f}s, expected < 5s")
        self.assertGreater(len(trends), 0)
    
    def test_optimization_analysis_performance(self):
        """Benchmark optimization analysis performance"""
        # Create diverse performance data
        base_time = timezone.now()
        snapshots = []
        
        # API metrics
        for i in range(200):
            snapshots.append(PerformanceSnapshot(
                layer='api',
                component=f'api_{i % 5}',
                metric_name='response_time',
                metric_value=300.0 + (i % 200),
                timestamp=base_time - timedelta(minutes=i)
            ))
        
        # Database metrics
        for i in range(200):
            snapshots.append(PerformanceSnapshot(
                layer='database',
                component='mysql',
                metric_name='avg_query_time',
                metric_value=150.0 + (i % 100),
                timestamp=base_time - timedelta(minutes=i)
            ))
        
        # System metrics
        for i in range(200):
            snapshots.append(PerformanceSnapshot(
                layer='system',
                component='cpu',
                metric_name='cpu_usage',
                metric_value=70.0 + (i % 30),
                timestamp=base_time - timedelta(minutes=i)
            ))
        
        PerformanceSnapshot.objects.bulk_create(snapshots)
        
        # Benchmark optimization analysis
        start_time = time.time()
        
        recommendations = self.service.optimization_engine.analyze_performance_issues(hours=4)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 10.0, f"Optimization analysis took {duration:.2f}s, expected < 10s")
        self.assertGreaterEqual(len(recommendations), 0)
    
    def test_system_health_summary_performance(self):
        """Benchmark system health summary generation"""
        # Create comprehensive test data
        base_time = timezone.now()
        
        # Performance snapshots
        for i in range(500):
            PerformanceSnapshot.objects.create(
                layer=['api', 'database', 'system', 'cache'][i % 4],
                component=f'component_{i % 10}',
                metric_name=['response_time', 'cpu_usage', 'memory_usage'][i % 3],
                metric_value=float(i % 100),
                timestamp=base_time - timedelta(minutes=i)
            )
        
        # Error logs
        for i in range(50):
            ErrorLog.objects.create(
                layer=['api', 'database', 'system'][i % 3],
                component=f'component_{i % 5}',
                error_type='TestError',
                error_message=f'Test error {i}',
                severity=['warning', 'error', 'critical'][i % 3],
                timestamp=base_time - timedelta(minutes=i * 2)
            )
        
        # Benchmark health summary generation
        start_time = time.time()
        
        summary = self.service.get_system_health_summary()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 5.0, f"Health summary generation took {duration:.2f}s, expected < 5s")
        
        # Verify summary structure
        self.assertIn('overall_health', summary)
        self.assertIn('performance_metrics', summary)
        self.assertIn('error_summary', summary)
        self.assertIn('trends', summary)
        self.assertIn('recommendations', summary)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'apps.debugging',
            ],
            SECRET_KEY='test-secret-key',
            USE_TZ=True,
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['apps.debugging.test_performance_monitoring'])