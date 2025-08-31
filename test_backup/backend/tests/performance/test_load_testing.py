# Performance and load testing
import pytest
import time
import threading
import concurrent.futures
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import connection
from django.test.utils import override_settings
from unittest.mock import patch
import statistics
from decimal import Decimal

User = get_user_model()

class BasePerformanceTestCase(APITestCase):
    """Base class for performance tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin_perf',
            email='admin@perf.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.authenticate()
        
        # Create test data
        self.create_test_data()
    
    def authenticate(self):
        """Authenticate the client"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def create_test_data(self):
        """Create test data for performance testing"""
        # Create products
        from apps.products.models import Product
        products = []
        for i in range(100):
            products.append(Product(
                name=f'Performance Test Product {i}',
                description=f'Description for product {i}',
                price=Decimal(f'{10 + i}.99'),
                sku=f'PERF-{i:04d}',
                stock_quantity=100 + i
            ))
        Product.objects.bulk_create(products)
        
        # Create orders
        from apps.orders.models import Order
        orders = []
        for i in range(50):
            orders.append(Order(
                customer=self.admin_user,
                order_number=f'ORD-PERF-{i:04d}',
                total_amount=Decimal(f'{100 + i}.00'),
                status='pending'
            ))
        Order.objects.bulk_create(orders)
    
    def measure_response_time(self, func, *args, **kwargs):
        """Measure response time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def measure_multiple_requests(self, func, num_requests=10, *args, **kwargs):
        """Measure response time for multiple requests"""
        response_times = []
        for _ in range(num_requests):
            _, response_time = self.measure_response_time(func, *args, **kwargs)
            response_times.append(response_time)
        
        return {
            'min': min(response_times),
            'max': max(response_times),
            'avg': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }

class APIPerformanceTest(BasePerformanceTestCase):
    """Test API endpoint performance"""
    
    def test_product_list_performance(self):
        """Test product list endpoint performance"""
        def make_request():
            return self.client.get('/api/admin/products/')
        
        stats = self.measure_multiple_requests(make_request, 20)
        
        # Assert performance requirements
        self.assertLess(stats['avg'], 1.0, f"Average response time too slow: {stats['avg']:.3f}s")
        self.assertLess(stats['max'], 2.0, f"Max response time too slow: {stats['max']:.3f}s")
        
        print(f"Product List Performance Stats: {stats}")
    
    def test_product_detail_performance(self):
        """Test product detail endpoint performance"""
        from apps.products.models import Product
        product = Product.objects.first()
        
        def make_request():
            return self.client.get(f'/api/admin/products/{product.id}/')
        
        stats = self.measure_multiple_requests(make_request, 20)
        
        self.assertLess(stats['avg'], 0.5, f"Average response time too slow: {stats['avg']:.3f}s")
        print(f"Product Detail Performance Stats: {stats}")
    
    def test_dashboard_stats_performance(self):
        """Test dashboard stats endpoint performance"""
        def make_request():
            return self.client.get('/api/admin/dashboard/stats/')
        
        stats = self.measure_multiple_requests(make_request, 10)
        
        self.assertLess(stats['avg'], 2.0, f"Dashboard stats too slow: {stats['avg']:.3f}s")
        print(f"Dashboard Stats Performance Stats: {stats}")
    
    def test_order_list_performance(self):
        """Test order list endpoint performance"""
        def make_request():
            return self.client.get('/api/admin/orders/')
        
        stats = self.measure_multiple_requests(make_request, 15)
        
        self.assertLess(stats['avg'], 1.5, f"Order list too slow: {stats['avg']:.3f}s")
        print(f"Order List Performance Stats: {stats}")
    
    def test_search_performance(self):
        """Test search endpoint performance"""
        def make_request():
            return self.client.get('/api/admin/products/?search=test')
        
        stats = self.measure_multiple_requests(make_request, 10)
        
        self.assertLess(stats['avg'], 1.0, f"Search too slow: {stats['avg']:.3f}s")
        print(f"Search Performance Stats: {stats}")

class DatabasePerformanceTest(BasePerformanceTestCase):
    """Test database query performance"""
    
    def test_query_count_optimization(self):
        """Test that endpoints don't have N+1 query problems"""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Test product list with related data
        with self.assertNumQueries(5):  # Should be optimized with select_related/prefetch_related
            response = self.client.get('/api/admin/products/')
            self.assertEqual(response.status_code, 200)
    
    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        from apps.products.models import Product
        
        # Test bulk create
        start_time = time.time()
        products = []
        for i in range(1000):
            products.append(Product(
                name=f'Bulk Product {i}',
                price=Decimal('10.00'),
                sku=f'BULK-{i:05d}'
            ))
        Product.objects.bulk_create(products)
        bulk_create_time = time.time() - start_time
        
        self.assertLess(bulk_create_time, 5.0, f"Bulk create too slow: {bulk_create_time:.3f}s")
        
        # Test bulk update
        products_to_update = Product.objects.filter(sku__startswith='BULK-')[:500]
        start_time = time.time()
        for product in products_to_update:
            product.price = Decimal('15.00')
        Product.objects.bulk_update(products_to_update, ['price'])
        bulk_update_time = time.time() - start_time
        
        self.assertLess(bulk_update_time, 3.0, f"Bulk update too slow: {bulk_update_time:.3f}s")
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Test first page
        start_time = time.time()
        response = self.client.get('/api/admin/products/?page=1&page_size=50')
        first_page_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(first_page_time, 1.0, f"First page too slow: {first_page_time:.3f}s")
        
        # Test middle page
        start_time = time.time()
        response = self.client.get('/api/admin/products/?page=2&page_size=50')
        middle_page_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(middle_page_time, 1.0, f"Middle page too slow: {middle_page_time:.3f}s")
    
    def test_complex_query_performance(self):
        """Test complex queries with joins and filters"""
        # Test complex filter query
        start_time = time.time()
        response = self.client.get('/api/admin/products/?category=1&price_min=10&price_max=100&in_stock=true')
        complex_query_time = time.time() - start_time
        
        self.assertLess(complex_query_time, 2.0, f"Complex query too slow: {complex_query_time:.3f}s")

class ConcurrencyTest(BasePerformanceTestCase):
    """Test concurrent request handling"""
    
    def test_concurrent_read_requests(self):
        """Test handling of concurrent read requests"""
        def make_request():
            response = self.client.get('/api/admin/products/')
            return response.status_code == 200
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        self.assertTrue(all(results), "Some concurrent requests failed")
    
    def test_concurrent_write_requests(self):
        """Test handling of concurrent write requests"""
        def create_product(index):
            data = {
                'name': f'Concurrent Product {index}',
                'price': '99.99',
                'sku': f'CONC-{index:04d}',
                'stock_quantity': 10
            }
            response = self.client.post('/api/admin/products/', data, format='json')
            return response.status_code == 201
        
        # Test with 5 concurrent write requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_product, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        self.assertTrue(all(results), "Some concurrent write requests failed")
    
    def test_read_write_concurrency(self):
        """Test mixed read/write concurrency"""
        def read_products():
            response = self.client.get('/api/admin/products/')
            return response.status_code == 200
        
        def write_product(index):
            data = {
                'name': f'RW Concurrent Product {index}',
                'price': '79.99',
                'sku': f'RW-CONC-{index:04d}',
                'stock_quantity': 5
            }
            response = self.client.post('/api/admin/products/', data, format='json')
            return response.status_code == 201
        
        # Mix of read and write operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            # 5 read operations
            for _ in range(5):
                futures.append(executor.submit(read_products))
            # 3 write operations
            for i in range(3):
                futures.append(executor.submit(write_product, i))
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        self.assertTrue(all(results), "Some concurrent read/write requests failed")

class MemoryUsageTest(BasePerformanceTestCase):
    """Test memory usage and optimization"""
    
    def test_memory_usage_large_dataset(self):
        """Test memory usage with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make request that processes large dataset
        response = self.client.get('/api/admin/products/?page_size=1000')
        self.assertEqual(response.status_code, 200)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        self.assertLess(memory_increase, 100, f"Memory usage too high: {memory_increase:.2f}MB")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated requests"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many repeated requests
        for _ in range(100):
            response = self.client.get('/api/admin/dashboard/stats/')
            self.assertEqual(response.status_code, 200)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal for repeated identical requests
        self.assertLess(memory_increase, 50, f"Possible memory leak: {memory_increase:.2f}MB increase")

class CachePerformanceTest(BasePerformanceTestCase):
    """Test caching performance"""
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_cache_hit_performance(self):
        """Test performance improvement with caching"""
        from django.core.cache import cache
        
        # Clear cache
        cache.clear()
        
        # First request (cache miss)
        start_time = time.time()
        response1 = self.client.get('/api/admin/dashboard/stats/')
        cache_miss_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = self.client.get('/api/admin/dashboard/stats/')
        cache_hit_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Cache hit should be significantly faster
        self.assertLess(cache_hit_time, cache_miss_time * 0.5, 
                       f"Cache not improving performance: miss={cache_miss_time:.3f}s, hit={cache_hit_time:.3f}s")

class LoadTestingTest(BasePerformanceTestCase):
    """Load testing scenarios"""
    
    def test_sustained_load(self):
        """Test sustained load over time"""
        def make_requests_for_duration(duration_seconds):
            end_time = time.time() + duration_seconds
            request_count = 0
            response_times = []
            
            while time.time() < end_time:
                start_time = time.time()
                response = self.client.get('/api/admin/products/')
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    request_count += 1
                    response_times.append(response_time)
                
                time.sleep(0.1)  # Small delay between requests
            
            return request_count, response_times
        
        # Run sustained load for 30 seconds
        request_count, response_times = make_requests_for_duration(30)
        
        self.assertGreater(request_count, 0, "No successful requests during load test")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            self.assertLess(avg_response_time, 2.0, 
                           f"Average response time degraded under load: {avg_response_time:.3f}s")
    
    def test_spike_load(self):
        """Test handling of sudden load spikes"""
        def burst_requests(num_requests):
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(self.client.get, '/api/admin/products/')
                    for _ in range(num_requests)
                ]
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    response = future.result()
                    results.append(response.status_code == 200)
            
            total_time = time.time() - start_time
            return results, total_time
        
        # Test with 20 simultaneous requests
        results, total_time = burst_requests(20)
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.8, f"Success rate too low under spike load: {success_rate:.2f}")
        self.assertLess(total_time, 10.0, f"Spike load took too long: {total_time:.3f}s")

class ResourceUtilizationTest(BasePerformanceTestCase):
    """Test resource utilization"""
    
    def test_cpu_usage_under_load(self):
        """Test CPU usage under load"""
        import psutil
        
        # Monitor CPU usage during requests
        cpu_percentages = []
        
        def monitor_cpu():
            for _ in range(10):
                cpu_percentages.append(psutil.cpu_percent(interval=0.1))
        
        def make_requests():
            for _ in range(50):
                self.client.get('/api/admin/products/')
        
        # Run monitoring and requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            monitor_future = executor.submit(monitor_cpu)
            request_future = executor.submit(make_requests)
            
            concurrent.futures.wait([monitor_future, request_future])
        
        if cpu_percentages:
            avg_cpu = statistics.mean(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            # CPU usage should be reasonable
            self.assertLess(avg_cpu, 80.0, f"Average CPU usage too high: {avg_cpu:.1f}%")
            self.assertLess(max_cpu, 95.0, f"Peak CPU usage too high: {max_cpu:.1f}%")

@pytest.mark.performance
class PytestPerformanceTest:
    """Pytest-based performance tests"""
    
    @pytest.fixture
    def api_client(self):
        """API client fixture"""
        from rest_framework.test import APIClient
        return APIClient()
    
    @pytest.fixture
    def authenticated_client(self, api_client, admin_user):
        """Authenticated API client"""
        refresh = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return api_client
    
    def test_api_response_time_benchmark(self, authenticated_client):
        """Benchmark API response times"""
        endpoints = [
            '/api/admin/products/',
            '/api/admin/orders/',
            '/api/admin/dashboard/stats/',
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = authenticated_client.get(endpoint)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"{endpoint} too slow: {response_time:.3f}s"
    
    @pytest.mark.slow
    def test_stress_test(self, authenticated_client):
        """Stress test with high load"""
        def make_request():
            return authenticated_client.get('/api/admin/products/')
        
        # Run 100 requests
        start_time = time.time()
        responses = []
        for _ in range(100):
            response = make_request()
            responses.append(response.status_code)
        
        total_time = time.time() - start_time
        success_rate = sum(1 for status in responses if status == 200) / len(responses)
        
        assert success_rate > 0.95, f"Success rate too low: {success_rate:.2f}"
        assert total_time < 60.0, f"Stress test took too long: {total_time:.2f}s"