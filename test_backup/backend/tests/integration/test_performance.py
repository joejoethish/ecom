#!/usr/bin/env python
"""
Performance and Load Testing

This module contains integration tests for performance and load testing
of the e-commerce platform, measuring response times, throughput, and
system behavior under various load conditions.
"""

import os
import sys
import django
import json
import time
import uuid
import threading
import statistics
from decimal import Decimal
from unittest import mock
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection, reset_queries
from django.conf import settings
from rest_framework.test import APIClient

from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.customers.models import Address
from apps.cart.models import Cart, CartItem
from apps.inventory.models import Inventory, InventoryTransaction

User = get_user_model()


class PerformanceTestCase(TestCase):
    """Base class for performance tests with utility methods"""
    
    def setUp(self):
        """Set up test data for performance tests"""
        # Enable query counting for database performance tests
        settings.DEBUG = True
        
        # Create test user
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123',
            first_name='Performance',
            last_name='User'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.login(username='perfuser', password='testpass123')
        
        # Create categories
        self.categories = []
        for i in range(5):
            category = Category.objects.create(
                name=f'Category {i}',
                slug=f'category-{i}',
                is_active=True
            )
            self.categories.append(category)
        
        # Create products
        self.products = []
        for i in range(50):
            category_index = i % len(self.categories)
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Description for Product {i}',
                short_description=f'Short description for Product {i}',
                category=self.categories[category_index],
                brand=f'Brand {i % 10}',
                sku=f'SKU{i:03d}',
                price=Decimal(f'{(i % 10) * 10 + 50}.99'),
                is_active=True
            )
            self.products.append(product)
            
            # Create inventory for each product
            inventory = Inventory.objects.create(
                product=product,
                quantity=100,
                reserved_quantity=0,
                minimum_stock_level=10,
                cost_price=Decimal(f'{(i % 10) * 5 + 25}.00')
            )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Performance',
            last_name='User',
            address_line_1='123 Performance Street',
            city='Performance City',
            state='Performance State',
            postal_code='12345',
            country='India',
            phone='1234567890',
            is_default=True
        )
        
        # Create cart
        self.cart = Cart.objects.create(user=self.user)
        
        # Add items to cart
        for i in range(5):
            CartItem.objects.create(
                cart=self.cart,
                product=self.products[i],
                quantity=1
            )
    
    def tearDown(self):
        """Clean up after tests"""
        settings.DEBUG = False
    
    def count_queries(self, func, *args, **kwargs):
        """Count the number of database queries executed by a function"""
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        return result, query_count
    
    def measure_response_time(self, url, method='get', data=None, repeat=1):
        """Measure response time for a URL"""
        client_method = getattr(self.client, method.lower())
        
        response_times = []
        status_codes = []
        query_counts = []
        
        for _ in range(repeat):
            reset_queries()
            start_time = time.time()
            
            if data and method.lower() != 'get':
                response = client_method(url, data, format='json')
            elif data and method.lower() == 'get':
                response = client_method(f"{url}?{data}")
            else:
                response = client_method(url)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            response_times.append(response_time)
            status_codes.append(response.status_code)
            query_counts.append(len(connection.queries))
        
        return {
            'min_time': min(response_times),
            'max_time': max(response_times),
            'avg_time': statistics.mean(response_times),
            'median_time': statistics.median(response_times),
            'status_codes': status_codes,
            'avg_query_count': statistics.mean(query_counts)
        }
    
    def concurrent_requests(self, url, method='get', data=None, num_requests=10, max_workers=5):
        """Execute concurrent requests and measure performance"""
        client_method = getattr(Client(), method.lower())
        
        def make_request():
            start_time = time.time()
            
            if data and method.lower() != 'get':
                response = client_method(url, data=data, content_type='application/json')
            elif data and method.lower() == 'get':
                response = client_method(f"{url}?{data}")
            else:
                response = client_method(url)
            
            end_time = time.time()
            return {
                'time': (end_time - start_time) * 1000,  # Convert to milliseconds
                'status_code': response.status_code
            }
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_request = {executor.submit(make_request): i for i in range(num_requests)}
            for future in as_completed(future_to_request):
                results.append(future.result())
        
        response_times = [result['time'] for result in results]
        status_codes = [result['status_code'] for result in results]
        
        return {
            'min_time': min(response_times),
            'max_time': max(response_times),
            'avg_time': statistics.mean(response_times),
            'median_time': statistics.median(response_times),
            'status_codes': status_codes,
            'throughput': num_requests / (sum(response_times) / 1000)  # Requests per second
        }


class ProductAPIPerformanceTest(PerformanceTestCase):
    """Test performance of product-related API endpoints"""
    
    def test_product_list_performance(self):
        """Test performance of product listing API"""
        print("\nTesting product list API performance...")
        
        # Test basic product listing
        url = '/api/v1/products/'
        result = self.measure_response_time(url, repeat=5)
        
        print(f"Product list API (no filters):")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 500, "Average response time should be less than 500ms")
        
        # Test with category filter
        category_id = self.categories[0].id
        result = self.measure_response_time(f"{url}?category={category_id}", repeat=5)
        
        print(f"Product list API (with category filter):")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 500, "Average response time should be less than 500ms")
        
        # Test with price filter
        result = self.measure_response_time(f"{url}?min_price=50&max_price=100", repeat=5)
        
        print(f"Product list API (with price filter):")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 500, "Average response time should be less than 500ms")
        
        # Test with search query
        result = self.measure_response_time(f"{url}?search=Product", repeat=5)
        
        print(f"Product list API (with search query):")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 1000, "Average response time should be less than 1000ms")
        
        print("✓ Product list API performance test passed!")
    
    def test_product_detail_performance(self):
        """Test performance of product detail API"""
        print("\nTesting product detail API performance...")
        
        # Test product detail endpoint
        product_id = self.products[0].id
        url = f'/api/v1/products/{product_id}/'
        result = self.measure_response_time(url, repeat=5)
        
        print(f"Product detail API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 300, "Average response time should be less than 300ms")
        self.assertLess(result['avg_query_count'], 10, "Average query count should be less than 10")
        
        print("✓ Product detail API performance test passed!")
    
    def test_category_list_performance(self):
        """Test performance of category listing API"""
        print("\nTesting category list API performance...")
        
        url = '/api/v1/categories/'
        result = self.measure_response_time(url, repeat=5)
        
        print(f"Category list API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 200, "Average response time should be less than 200ms")
        self.assertLess(result['avg_query_count'], 5, "Average query count should be less than 5")
        
        print("✓ Category list API performance test passed!")


class CartAPIPerformanceTest(PerformanceTestCase):
    """Test performance of cart-related API endpoints"""
    
    def test_cart_operations_performance(self):
        """Test performance of cart operations"""
        print("\nTesting cart operations performance...")
        
        # Test get cart
        url = '/api/v1/cart/'
        result = self.measure_response_time(url, repeat=5)
        
        print(f"Get cart API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 300, "Average response time should be less than 300ms")
        
        # Test add to cart
        url = '/api/v1/cart/items/'
        data = {
            'product_id': self.products[10].id,
            'quantity': 1
        }
        result = self.measure_response_time(url, method='post', data=data, repeat=5)
        
        print(f"Add to cart API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 201 for code in result['status_codes']), "All requests should return 201")
        self.assertLess(result['avg_time'], 500, "Average response time should be less than 500ms")
        
        # Test update cart item
        cart_item = CartItem.objects.filter(cart=self.cart).first()
        url = f'/api/v1/cart/items/{cart_item.id}/'
        data = {
            'quantity': 3
        }
        result = self.measure_response_time(url, method='patch', data=data, repeat=5)
        
        print(f"Update cart item API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 400, "Average response time should be less than 400ms")
        
        # Test remove from cart
        url = f'/api/v1/cart/items/{cart_item.id}/'
        result = self.measure_response_time(url, method='delete', repeat=5)
        
        print(f"Remove from cart API:")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Average query count: {result['avg_query_count']:.1f}")
        
        self.assertTrue(all(code == 204 for code in result['status_codes']), "All requests should return 204")
        self.assertLess(result['avg_time'], 300, "Average response time should be less than 300ms")
        
        print("✓ Cart operations performance test passed!")


class CheckoutPerformanceTest(PerformanceTestCase):
    """Test performance of checkout process"""
    
    def test_checkout_performance(self):
        """Test performance of checkout process"""
        print("\nTesting checkout process performance...")
        
        # Add items to cart if empty
        if CartItem.objects.filter(cart=self.cart).count() == 0:
            for i in range(3):
                CartItem.objects.create(
                    cart=self.cart,
                    product=self.products[i],
                    quantity=1
                )
        
        # Test checkout process
        url = '/api/v1/orders/checkout/'
        data = {
            'shipping_address': {
                'first_name': 'Performance',
                'last_name': 'User',
                'address_line_1': '123 Performance Street',
                'city': 'Performance City',
                'state': 'Performance State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'billing_address': {
                'first_name': 'Performance',
                'last_name': 'User',
                'address_line_1': '123 Performance Street',
                'city': 'Performance City',
                'state': 'Performance State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'payment_method': 'PREPAID',
            'shipping_method': 'STANDARD'
        }
        
        # Measure checkout performance
        reset_queries()
        start_time = time.time()
        response = self.client.post(url, data, format='json')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        query_count = len(connection.queries)
        
        print(f"Checkout API:")
        print(f"  Response time: {response_time:.2f} ms")
        print(f"  Query count: {query_count}")
        print(f"  Status code: {response.status_code}")
        
        self.assertEqual(response.status_code, 201, "Checkout should return 201 Created")
        self.assertLess(response_time, 1000, "Checkout response time should be less than 1000ms")
        
        # Verify order was created
        order_data = response.json()
        self.assertIn('id', order_data)
        self.assertIn('order_number', order_data)
        
        # Verify inventory was updated
        for item in CartItem.objects.filter(cart=self.cart):
            inventory = Inventory.objects.get(product=item.product)
            self.assertEqual(inventory.reserved_quantity, item.quantity)
        
        print("✓ Checkout performance test passed!")


class ConcurrentRequestsTest(PerformanceTestCase):
    """Test system behavior under concurrent requests"""
    
    def test_concurrent_product_listing(self):
        """Test performance with concurrent product listing requests"""
        print("\nTesting concurrent product listing requests...")
        
        url = '/api/v1/products/'
        result = self.concurrent_requests(url, num_requests=20, max_workers=10)
        
        print(f"Concurrent product listing ({len(result['status_codes'])} requests):")
        print(f"  Min response time: {result['min_time']:.2f} ms")
        print(f"  Max response time: {result['max_time']:.2f} ms")
        print(f"  Average response time: {result['avg_time']:.2f} ms")
        print(f"  Median response time: {result['median_time']:.2f} ms")
        print(f"  Throughput: {result['throughput']:.2f} requests/second")
        
        self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        self.assertLess(result['avg_time'], 1000, "Average response time should be less than 1000ms under load")
        
        print("✓ Concurrent product listing test passed!")
    
    def test_concurrent_product_detail(self):
        """Test performance with concurrent product detail requests"""
        print("\nTesting concurrent product detail requests...")
        
        # Get multiple product IDs
        product_ids = [p.id for p in self.products[:5]]
        results = []
        
        for product_id in product_ids:
            url = f'/api/v1/products/{product_id}/'
            result = self.concurrent_requests(url, num_requests=10, max_workers=5)
            results.append(result)
        
        # Calculate average metrics across all products
        avg_response_time = statistics.mean([r['avg_time'] for r in results])
        avg_throughput = statistics.mean([r['throughput'] for r in results])
        
        print(f"Concurrent product detail ({len(product_ids)} products, 10 requests each):")
        print(f"  Average response time: {avg_response_time:.2f} ms")
        print(f"  Average throughput: {avg_throughput:.2f} requests/second")
        
        for result in results:
            self.assertTrue(all(code == 200 for code in result['status_codes']), "All requests should return 200")
        
        self.assertLess(avg_response_time, 800, "Average response time should be less than 800ms under load")
        
        print("✓ Concurrent product detail test passed!")
    
    def test_concurrent_cart_operations(self):
        """Test performance with concurrent cart operations"""
        print("\nTesting concurrent cart operations...")
        
        # Create multiple test users with carts
        test_users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'loaduser{i}',
                email=f'load{i}@example.com',
                password='testpass123'
            )
            cart = Cart.objects.create(user=user)
            test_users.append((user, cart))
        
        # Function to perform cart operations for a user
        def cart_operations(user_cart):
            user, cart = user_cart
            client = APIClient()
            client.login(username=user.username, password='testpass123')
            
            # Add to cart
            add_url = '/api/v1/cart/items/'
            add_data = {
                'product_id': self.products[0].id,
                'quantity': 1
            }
            add_response = client.post(add_url, add_data, format='json')
            
            # Get cart
            get_url = '/api/v1/cart/'
            get_response = client.get(get_url)
            
            # Update cart item
            if add_response.status_code == 201:
                item_id = add_response.json()['id']
                update_url = f'/api/v1/cart/items/{item_id}/'
                update_data = {'quantity': 2}
                update_response = client.patch(update_url, update_data, format='json')
                
                # Remove from cart
                delete_response = client.delete(update_url)
                
                return all([
                    add_response.status_code == 201,
                    get_response.status_code == 200,
                    update_response.status_code == 200,
                    delete_response.status_code == 204
                ])
            
            return False
        
        # Execute cart operations concurrently
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(cart_operations, test_users))
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        operations_per_second = len(test_users) * 4 / (total_time / 1000)  # 4 operations per user
        
        print(f"Concurrent cart operations ({len(test_users)} users, 4 operations each):")
        print(f"  Total time: {total_time:.2f} ms")
        print(f"  Operations per second: {operations_per_second:.2f}")
        
        self.assertTrue(all(results), "All cart operations should succeed")
        
        print("✓ Concurrent cart operations test passed!")


class DatabasePerformanceTest(PerformanceTestCase):
    """Test database query performance"""
    
    def test_query_optimization(self):
        """Test database query optimization"""
        print("\nTesting database query optimization...")
        
        # Test product listing with select_related and prefetch_related
        def get_products_optimized():
            return list(Product.objects.select_related('category').all()[:20])
        
        def get_products_unoptimized():
            products = list(Product.objects.all()[:20])
            # Force category access to trigger additional queries
            for product in products:
                _ = product.category.name
            return products
        
        # Measure optimized query
        reset_queries()
        start_time = time.time()
        optimized_products = get_products_optimized()
        optimized_time = (time.time() - start_time) * 1000
        optimized_queries = len(connection.queries)
        
        # Measure unoptimized query
        reset_queries()
        start_time = time.time()
        unoptimized_products = get_products_unoptimized()
        unoptimized_time = (time.time() - start_time) * 1000
        unoptimized_queries = len(connection.queries)
        
        print(f"Product listing query optimization:")
        print(f"  Optimized: {optimized_time:.2f} ms, {optimized_queries} queries")
        print(f"  Unoptimized: {unoptimized_time:.2f} ms, {unoptimized_queries} queries")
        print(f"  Improvement: {unoptimized_queries - optimized_queries} fewer queries")
        
        self.assertLess(optimized_queries, unoptimized_queries, "Optimized query should use fewer database queries")
        
        # Test order listing with select_related and prefetch_related
        # Create some test orders first
        for i in range(5):
            order = Order.objects.create(
                user=self.user,
                order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
                status='CONFIRMED',
                total_amount=Decimal('100.00'),
                shipping_amount=Decimal('10.00'),
                tax_amount=Decimal('5.00'),
                shipping_address={},
                billing_address={},
                payment_method='PREPAID',
                payment_status='PAID'
            )
            
            # Add order items
            for j in range(3):
                OrderItem.objects.create(
                    order=order,
                    product=self.products[j],
                    quantity=1,
                    unit_price=self.products[j].price,
                    total_price=self.products[j].price
                )
        
        def get_orders_optimized():
            return list(Order.objects.select_related('user').prefetch_related('items__product').all())
        
        def get_orders_unoptimized():
            orders = list(Order.objects.all())
            # Force related object access to trigger additional queries
            for order in orders:
                _ = order.user.username
                for item in order.items.all():
                    _ = item.product.name
            return orders
        
        # Measure optimized query
        reset_queries()
        start_time = time.time()
        optimized_orders = get_orders_optimized()
        optimized_time = (time.time() - start_time) * 1000
        optimized_queries = len(connection.queries)
        
        # Measure unoptimized query
        reset_queries()
        start_time = time.time()
        unoptimized_orders = get_orders_unoptimized()
        unoptimized_time = (time.time() - start_time) * 1000
        unoptimized_queries = len(connection.queries)
        
        print(f"Order listing query optimization:")
        print(f"  Optimized: {optimized_time:.2f} ms, {optimized_queries} queries")
        print(f"  Unoptimized: {unoptimized_time:.2f} ms, {unoptimized_queries} queries")
        print(f"  Improvement: {unoptimized_queries - optimized_queries} fewer queries")
        
        self.assertLess(optimized_queries, unoptimized_queries, "Optimized query should use fewer database queries")
        
        print("✓ Database query optimization test passed!")


def main():
    """Run the performance and load tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_performance'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()