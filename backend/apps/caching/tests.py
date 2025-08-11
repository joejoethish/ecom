from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
import time

from .models import (
    CacheConfiguration, CacheMetrics, CacheInvalidation,
    CacheWarming, CacheAlert, CacheOptimization
)
from .cache_manager import MultiLevelCacheManager
from .optimization import CacheOptimizer
from .cdn_integration import CDNManager

User = get_user_model()


class CacheConfigurationModelTest(TestCase):
    """Test CacheConfiguration model"""
    
    def setUp(self):
        self.config = CacheConfiguration.objects.create(
            name='test_cache',
            cache_type='redis',
            strategy='write_through',
            ttl_seconds=3600,
            max_size_mb=100,
            compression_enabled=True,
            is_active=True,
            priority=1
        )
    
    def test_cache_configuration_creation(self):
        """Test cache configuration creation"""
        self.assertEqual(self.config.name, 'test_cache')
        self.assertEqual(self.config.cache_type, 'redis')
        self.assertEqual(self.config.strategy, 'write_through')
        self.assertTrue(self.config.is_active)
    
    def test_cache_configuration_str(self):
        """Test string representation"""
        expected = "test_cache (redis)"
        self.assertEqual(str(self.config), expected)
    
    def test_cache_configuration_ordering(self):
        """Test model ordering"""
        config2 = CacheConfiguration.objects.create(
            name='test_cache_2',
            cache_type='memcached',
            priority=2
        )
        
        configs = list(CacheConfiguration.objects.all())
        self.assertEqual(configs[0], self.config)  # Lower priority first
        self.assertEqual(configs[1], config2)


class CacheMetricsModelTest(TestCase):
    """Test CacheMetrics model"""
    
    def setUp(self):
        self.metrics = CacheMetrics.objects.create(
            cache_name='test_cache',
            cache_type='redis',
            hit_count=100,
            miss_count=20,
            hit_ratio=0.833,
            avg_response_time_ms=15.5,
            memory_used_mb=50.0,
            memory_total_mb=100.0,
            memory_usage_percent=50.0,
            get_operations=120,
            set_operations=80,
            error_count=2
        )
    
    def test_metrics_creation(self):
        """Test metrics creation"""
        self.assertEqual(self.metrics.cache_name, 'test_cache')
        self.assertEqual(self.metrics.hit_count, 100)
        self.assertEqual(self.metrics.miss_count, 20)
        self.assertAlmostEqual(self.metrics.hit_ratio, 0.833, places=3)
    
    def test_metrics_str(self):
        """Test string representation"""
        expected = f"test_cache - {self.metrics.timestamp}"
        self.assertEqual(str(self.metrics), expected)


class MultiLevelCacheManagerTest(TestCase):
    """Test MultiLevelCacheManager"""
    
    def setUp(self):
        self.cache_manager = MultiLevelCacheManager()
        self.config = CacheConfiguration.objects.create(
            name='test_cache',
            cache_type='redis',
            ttl_seconds=3600,
            is_active=True
        )
    
    @patch('apps.caching.cache_manager.redis.from_url')
    def test_cache_manager_initialization(self, mock_redis):
        """Test cache manager initialization"""
        mock_redis.return_value = MagicMock()
        manager = MultiLevelCacheManager()
        self.assertIsNotNone(manager)
    
    @patch('apps.caching.cache_manager.cache')
    def test_cache_get_miss(self, mock_cache):
        """Test cache get operation with miss"""
        mock_cache.get.return_value = None
        
        result = self.cache_manager.get('test_key', 'test_cache')
        self.assertIsNone(result)
    
    @patch('apps.caching.cache_manager.cache')
    def test_cache_set_success(self, mock_cache):
        """Test cache set operation"""
        mock_cache.set.return_value = True
        
        result = self.cache_manager.set('test_key', 'test_value', 'test_cache')
        self.assertTrue(result)
    
    @patch('apps.caching.cache_manager.cache')
    def test_cache_delete_success(self, mock_cache):
        """Test cache delete operation"""
        mock_cache.delete.return_value = True
        
        result = self.cache_manager.delete('test_key', 'test_cache')
        self.assertTrue(result)
    
    def test_cache_warm_functionality(self):
        """Test cache warming functionality"""
        def mock_data_loader(key):
            return f"data_for_{key}"
        
        keys = ['key1', 'key2', 'key3']
        results = self.cache_manager.warm_cache('test_cache', mock_data_loader, keys)
        
        self.assertEqual(len(results), 3)
        self.assertIn('key1', results)
        self.assertIn('key2', results)
        self.assertIn('key3', results)


class CacheOptimizerTest(TestCase):
    """Test CacheOptimizer"""
    
    def setUp(self):
        self.optimizer = CacheOptimizer()
        self.config = CacheConfiguration.objects.create(
            name='test_cache',
            cache_type='redis',
            ttl_seconds=3600,
            max_size_mb=100,
            is_active=True
        )
        
        # Create test metrics
        for i in range(10):
            CacheMetrics.objects.create(
                cache_name='test_cache',
                cache_type='redis',
                hit_ratio=0.8 - (i * 0.01),  # Declining hit ratio
                avg_response_time_ms=50 + (i * 5),  # Increasing response time
                memory_usage_percent=70 + i,
                hit_count=100 - i,
                miss_count=20 + i,
                get_operations=120,
                set_operations=80,
                timestamp=timezone.now() - timezone.timedelta(hours=i)
            )
    
    def test_analyze_cache_performance(self):
        """Test cache performance analysis"""
        analysis = self.optimizer.analyze_cache_performance('test_cache', days=1)
        
        self.assertIn('cache_name', analysis)
        self.assertIn('performance_summary', analysis)
        self.assertIn('trends', analysis)
        self.assertIn('bottlenecks', analysis)
        self.assertIn('recommendations', analysis)
        self.assertIn('optimization_score', analysis)
        
        self.assertEqual(analysis['cache_name'], 'test_cache')
        self.assertIsInstance(analysis['optimization_score'], (int, float))
    
    def test_optimize_cache_configuration(self):
        """Test cache configuration optimization"""
        optimization = self.optimizer.optimize_cache_configuration('test_cache')
        
        self.assertIn('cache_name', optimization)
        self.assertIn('optimizations_found', optimization)
        self.assertIn('optimizations', optimization)
        
        self.assertEqual(optimization['cache_name'], 'test_cache')
        self.assertIsInstance(optimization['optimizations_found'], int)
    
    def test_monitor_cache_health(self):
        """Test cache health monitoring"""
        with patch.object(self.optimizer, '_get_cache_stats') as mock_stats:
            mock_stats.return_value = {
                'hit_ratio': 0.85,
                'avg_response_time_ms': 45.0,
                'memory_usage_percent': 75.0,
                'error_count': 1
            }
            
            health = self.optimizer.monitor_cache_health('test_cache')
            
            self.assertIn('cache_name', health)
            self.assertIn('health_score', health)
            self.assertIn('status', health)
            self.assertIn('alerts', health)
            
            self.assertEqual(health['cache_name'], 'test_cache')
            self.assertIsInstance(health['health_score'], (int, float))
    
    def test_benchmark_cache_performance(self):
        """Test cache performance benchmarking"""
        with patch.object(self.optimizer, 'cache_manager') as mock_manager:
            mock_manager.set.return_value = True
            mock_manager.get.return_value = 'test_value'
            mock_manager.delete.return_value = True
            
            benchmark = self.optimizer.benchmark_cache_performance('test_cache', test_duration=1)
            
            self.assertIn('cache_name', benchmark)
            self.assertIn('test_duration', benchmark)
            self.assertIn('operations', benchmark)
            self.assertIn('throughput', benchmark)
            
            self.assertEqual(benchmark['cache_name'], 'test_cache')
            self.assertEqual(benchmark['test_duration'], 1)


class CDNManagerTest(TestCase):
    """Test CDNManager"""
    
    def setUp(self):
        self.cdn_manager = CDNManager()
    
    @patch('apps.caching.cdn_integration.boto3.client')
    def test_cdn_manager_initialization(self, mock_boto3):
        """Test CDN manager initialization"""
        mock_boto3.return_value = MagicMock()
        manager = CDNManager()
        self.assertIsNotNone(manager)
    
    def test_upload_static_assets(self):
        """Test static asset upload"""
        assets = [
            {'path': 'test.css', 'content_type': 'text/css'},
            {'path': 'test.js', 'content_type': 'application/javascript'}
        ]
        
        with patch.object(self.cdn_manager, '_upload_single_asset') as mock_upload:
            mock_upload.return_value = {
                'success': True,
                'path': 'test.css',
                'original_size': 1000,
                'compressed_size': 800
            }
            
            results = self.cdn_manager.upload_static_assets(assets)
            
            self.assertIn('uploaded', results)
            self.assertIn('failed', results)
            self.assertIn('total_size', results)
            self.assertIn('compressed_size', results)
    
    @patch('apps.caching.cdn_integration.requests.post')
    def test_invalidate_cache(self, mock_post):
        """Test CDN cache invalidation"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'success': True}
        
        paths = ['/static/css/main.css', '/static/js/app.js']
        
        with override_settings(CLOUDFLARE_ZONE_ID='test_zone'):
            results = self.cdn_manager.invalidate_cache(paths)
            
            self.assertIn('cloudflare', results)
            self.assertIn('success', results)


class CacheAPITest(APITestCase):
    """Test Cache API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.config = CacheConfiguration.objects.create(
            name='test_cache',
            cache_type='redis',
            ttl_seconds=3600,
            is_active=True
        )
    
    def test_cache_configuration_list(self):
        """Test cache configuration list endpoint"""
        url = '/api/admin/caching/configurations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'test_cache')
    
    def test_cache_configuration_create(self):
        """Test cache configuration creation"""
        url = '/api/admin/caching/configurations/'
        data = {
            'name': 'new_cache',
            'cache_type': 'memcached',
            'strategy': 'cache_aside',
            'ttl_seconds': 1800,
            'max_size_mb': 50,
            'is_active': True,
            'priority': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_cache')
        self.assertEqual(response.data['cache_type'], 'memcached')
    
    def test_cache_configuration_update(self):
        """Test cache configuration update"""
        url = f'/api/admin/caching/configurations/{self.config.id}/'
        data = {
            'name': 'test_cache',
            'cache_type': 'redis',
            'strategy': 'write_back',
            'ttl_seconds': 7200,
            'max_size_mb': 200,
            'is_active': True,
            'priority': 1
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ttl_seconds'], 7200)
        self.assertEqual(response.data['max_size_mb'], 200)
    
    def test_cache_configuration_delete(self):
        """Test cache configuration deletion"""
        url = f'/api/admin/caching/configurations/{self.config.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CacheConfiguration.objects.filter(id=self.config.id).exists())
    
    @patch('apps.caching.views.cache_manager.get_cache_stats')
    def test_cache_stats_endpoint(self, mock_stats):
        """Test cache stats endpoint"""
        mock_stats.return_value = {
            'cache_name': 'test_cache',
            'hit_ratio': 0.85,
            'avg_response_time_ms': 45.0,
            'memory_usage_percent': 75.0
        }
        
        url = f'/api/admin/caching/configurations/{self.config.id}/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cache_name'], 'test_cache')
        self.assertEqual(response.data['hit_ratio'], 0.85)
    
    @patch('apps.caching.views.cache_manager')
    def test_cache_connection_test(self, mock_manager):
        """Test cache connection test endpoint"""
        mock_manager.set.return_value = True
        mock_manager.get.return_value = 'connection_test'
        mock_manager.delete.return_value = True
        mock_manager.get_cache_stats.return_value = {'status': 'connected'}
        
        url = f'/api/admin/caching/configurations/{self.config.id}/test_connection/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('operations', response.data)
        self.assertIn('stats', response.data)
    
    def test_cache_invalidation_create(self):
        """Test cache invalidation creation"""
        url = '/api/admin/caching/invalidations/invalidate_keys/'
        data = {
            'cache_name': 'test_cache',
            'keys': ['key1', 'key2'],
            'reason': 'Test invalidation'
        }
        
        with patch('apps.caching.views.cache_manager.delete') as mock_delete:
            mock_delete.return_value = True
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(len(response.data['results']), 2)
    
    def test_cache_warming_execute(self):
        """Test cache warming execution"""
        warming = CacheWarming.objects.create(
            name='test_warming',
            cache_name='test_cache',
            warming_type='manual',
            query_pattern='test_pattern',
            is_active=True
        )
        
        url = f'/api/admin/caching/warming/{warming.id}/execute/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('warming_config', response.data)
    
    def test_cache_alert_resolve(self):
        """Test cache alert resolution"""
        alert = CacheAlert.objects.create(
            cache_name='test_cache',
            alert_type='high_miss_ratio',
            severity='high',
            message='Test alert',
            threshold_value=0.8,
            current_value=0.6
        )
        
        url = f'/api/admin/caching/alerts/{alert.id}/resolve/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify alert is resolved
        alert.refresh_from_db()
        self.assertTrue(alert.is_resolved)
        self.assertEqual(alert.resolved_by, self.user)
    
    @patch('apps.caching.views.cache_optimizer.analyze_cache_performance')
    def test_cache_optimization_analyze(self, mock_analyze):
        """Test cache optimization analysis"""
        mock_analyze.return_value = {
            'cache_name': 'test_cache',
            'optimization_score': 75.0,
            'performance_summary': {},
            'trends': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        url = '/api/admin/caching/optimizations/analyze/'
        data = {'cache_name': 'test_cache', 'days': 7}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analysis', response.data)
    
    @patch('apps.caching.views.cache_optimizer.benchmark_cache_performance')
    def test_cache_benchmark(self, mock_benchmark):
        """Test cache benchmarking"""
        mock_benchmark.return_value = {
            'cache_name': 'test_cache',
            'test_duration': 60,
            'operations': {},
            'throughput': {},
            'statistics': {}
        }
        
        url = '/api/admin/caching/optimizations/benchmark/'
        data = {'cache_name': 'test_cache', 'test_duration': 60}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('benchmark', response.data)


class CacheMiddlewareTest(TestCase):
    """Test cache middleware"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cache_metrics_middleware(self):
        """Test cache metrics middleware"""
        from .middleware import CacheMetricsMiddleware
        
        middleware = CacheMetricsMiddleware(lambda request: None)
        self.assertIsNotNone(middleware)
    
    def test_cache_headers_middleware(self):
        """Test cache headers middleware"""
        from .middleware import CacheHeadersMiddleware
        
        middleware = CacheHeadersMiddleware(lambda request: None)
        self.assertIsNotNone(middleware)
    
    def test_compression_middleware(self):
        """Test compression middleware"""
        from .middleware import CompressionMiddleware
        
        middleware = CompressionMiddleware(lambda request: None)
        self.assertIsNotNone(middleware)


class CacheSignalsTest(TestCase):
    """Test cache signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cache_configuration_changed_signal(self):
        """Test cache configuration change signal"""
        # This would test the signal handlers
        # For now, we'll just verify the signal is connected
        from django.db.models.signals import post_save
        from .models import CacheConfiguration
        
        # Check if signal is connected
        receivers = post_save._live_receivers(sender=CacheConfiguration)
        self.assertTrue(len(receivers) > 0)
    
    def test_cache_metrics_saved_signal(self):
        """Test cache metrics saved signal"""
        from django.db.models.signals import post_save
        from .models import CacheMetrics
        
        # Check if signal is connected
        receivers = post_save._live_receivers(sender=CacheMetrics)
        self.assertTrue(len(receivers) > 0)
    
    def test_cache_alert_created_signal(self):
        """Test cache alert created signal"""
        from django.db.models.signals import post_save
        from .models import CacheAlert
        
        # Check if signal is connected
        receivers = post_save._live_receivers(sender=CacheAlert)
        self.assertTrue(len(receivers) > 0)