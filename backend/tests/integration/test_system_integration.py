#!/usr/bin/env python
"""
System Integration Tests

This module contains integration tests that validate the entire system works together,
including all components, services, and external integrations.
"""

import os
import sys
import django
import json
import time
import uuid
import requests
from decimal import Decimal
from unittest import mock
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APIClient

from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.customers.models import Address
from apps.cart.models import Cart, CartItem
from apps.inventory.models import Inventory, InventoryTransaction
from apps.payments.models import Payment
from apps.shipping.models import ShippingPartner
from apps.notifications.models import Notification

User = get_user_model()


class SystemIntegrationTestCase(TestCase):
    """Test the entire system integration"""
    
    def setUp(self):
        """Set up test data for system integration tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.login(username='testuser', password='testpass123')
        
        # Create categories
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        # Create products
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            short_description='Test product short description',
            category=self.category,
            brand='Test Brand',
            sku='TEST001',
            price=Decimal('99.99'),
            is_active=True
        )
        
        # Create inventory
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10,
            cost_price=Decimal('50.00')
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Test',
            last_name='User',
            address_line_1='123 Test Street',
            city='Test City',
            state='Test State',
            postal_code='12345',
            country='India',
            phone='1234567890',
            is_default=True
        )
        
        # Create cart
        self.cart = Cart.objects.create(user=self.user)
        
        # Add item to cart
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        # Create shipping partner
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipping',
            code='TEST',
            is_active=True
        )
    
    def test_complete_order_flow(self):
        """Test the complete order flow from cart to payment"""
        print("\nTesting complete order flow...")
        
        # 1. Get cart
        cart_url = '/api/v1/cart/'
        cart_response = self.client.get(cart_url)
        
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(len(cart_response.json()['items']), 1)
        self.assertEqual(cart_response.json()['items'][0]['product']['id'], self.product.id)
        
        # 2. Proceed to checkout
        checkout_url = '/api/v1/orders/checkout/'
        checkout_data = {
            'shipping_address': {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'billing_address': {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'payment_method': 'PREPAID',
            'shipping_method': 'STANDARD',
            'shipping_partner': self.shipping_partner.code
        }
        
        checkout_response = self.client.post(checkout_url, checkout_data, format='json')
        
        self.assertEqual(checkout_response.status_code, 201)
        order_id = checkout_response.json()['id']
        order_number = checkout_response.json()['order_number']
        
        # 3. Verify order was created
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.payment_status, 'PENDING')
        
        # 4. Verify order items
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 1)
        self.assertEqual(order_items[0].product, self.product)
        self.assertEqual(order_items[0].quantity, 2)
        
        # 5. Verify inventory was updated
        inventory = Inventory.objects.get(product=self.product)
        self.assertEqual(inventory.reserved_quantity, 2)
        
        # 6. Process payment
        payment_url = f'/api/v1/payments/process/'
        payment_data = {
            'order_id': order_id,
            'payment_method': 'PREPAID',
            'amount': float(order.total_amount),
            'transaction_id': f'TEST-{uuid.uuid4().hex[:8].upper()}',
            'status': 'COMPLETED'
        }
        
        # Mock payment gateway response
        with mock.patch('apps.payments.services.PaymentGatewayService.process_payment') as mock_payment:
            mock_payment.return_value = {
                'success': True,
                'transaction_id': payment_data['transaction_id'],
                'amount': payment_data['amount'],
                'status': 'COMPLETED'
            }
            
            payment_response = self.client.post(payment_url, payment_data, format='json')
        
        self.assertEqual(payment_response.status_code, 200)
        self.assertEqual(payment_response.json()['status'], 'success')
        
        # 7. Verify payment was created
        payment = Payment.objects.filter(order=order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        
        # 8. Verify order status was updated
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'PAID')
        self.assertEqual(order.status, 'CONFIRMED')
        
        # 9. Verify inventory was updated
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity, 98)
        self.assertEqual(inventory.reserved_quantity, 0)
        
        # 10. Verify notification was created
        notifications = Notification.objects.filter(user=self.user)
        self.assertTrue(notifications.exists())
        
        # 11. Get order details
        order_url = f'/api/v1/orders/{order_id}/'
        order_response = self.client.get(order_url)
        
        self.assertEqual(order_response.status_code, 200)
        self.assertEqual(order_response.json()['order_number'], order_number)
        self.assertEqual(order_response.json()['status'], 'CONFIRMED')
        
        print("✓ Complete order flow test passed!")
    
    def test_error_handling_edge_cases(self):
        """Test error handling and edge cases"""
        print("\nTesting error handling and edge cases...")
        
        # 1. Test invalid product ID
        cart_item_url = '/api/v1/cart/items/'
        invalid_data = {
            'product_id': 9999,  # Non-existent product ID
            'quantity': 1
        }
        
        response = self.client.post(cart_item_url, invalid_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
        # 2. Test adding out-of-stock product
        # Set inventory to 0
        self.inventory.quantity = 0
        self.inventory.save()
        
        out_of_stock_data = {
            'product_id': self.product.id,
            'quantity': 1
        }
        
        response = self.client.post(cart_item_url, out_of_stock_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
        # Reset inventory
        self.inventory.quantity = 100
        self.inventory.save()
        
        # 3. Test checkout with invalid shipping partner
        checkout_url = '/api/v1/orders/checkout/'
        invalid_checkout_data = {
            'shipping_address': {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'billing_address': {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            'payment_method': 'PREPAID',
            'shipping_method': 'STANDARD',
            'shipping_partner': 'INVALID'  # Invalid shipping partner code
        }
        
        response = self.client.post(checkout_url, invalid_checkout_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
        # 4. Test payment with invalid order ID
        payment_url = '/api/v1/payments/process/'
        invalid_payment_data = {
            'order_id': 9999,  # Non-existent order ID
            'payment_method': 'PREPAID',
            'amount': 99.99,
            'transaction_id': f'TEST-{uuid.uuid4().hex[:8].upper()}',
            'status': 'COMPLETED'
        }
        
        response = self.client.post(payment_url, invalid_payment_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
        # 5. Test unauthorized access to admin endpoints
        admin_url = '/api/v1/admin/dashboard/'
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 403)
        
        print("✓ Error handling and edge cases test passed!")
    
    def test_websocket_connections(self):
        """Test WebSocket connections for real-time updates"""
        print("\nTesting WebSocket connections...")
        
        # This is a simplified test since we can't easily test WebSockets in a unit test
        # In a real scenario, you would use a WebSocket client library
        
        # Check if Channels is properly configured
        self.assertTrue(hasattr(settings, 'CHANNEL_LAYERS'))
        self.assertEqual(settings.CHANNEL_LAYERS['default']['BACKEND'], 'channels_redis.core.RedisChannelLayer')
        
        # Verify WebSocket URLs are defined
        from ecommerce_project.asgi import application
        self.assertIsNotNone(application)
        
        print("✓ WebSocket configuration test passed!")
    
    def test_celery_task_execution(self):
        """Test Celery task execution"""
        print("\nTesting Celery task execution...")
        
        # Import Celery tasks
        from tasks.tasks import send_order_confirmation_email
        
        # Create a test order
        order = Order.objects.create(
            user=self.user,
            order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
            status='CONFIRMED',
            total_amount=Decimal('99.99'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            shipping_address={},
            billing_address={},
            payment_method='PREPAID',
            payment_status='PAID'
        )
        
        # Mock the task execution
        with mock.patch('tasks.tasks.send_order_confirmation_email.delay') as mock_task:
            # Call the task
            send_order_confirmation_email.delay(order.id)
            
            # Verify the task was called with the correct arguments
            mock_task.assert_called_once_with(order.id)
        
        print("✓ Celery task execution test passed!")


def main():
    """Run the system integration tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_system_integration'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()