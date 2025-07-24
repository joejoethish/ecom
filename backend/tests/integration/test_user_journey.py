#!/usr/bin/env python
"""
End-to-End User Journey Integration Tests

This module contains comprehensive integration tests that simulate complete user journeys
through the e-commerce platform, testing multiple interconnected components together.
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.products.models import Product, Category
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.customers.models import Address
from apps.inventory.models import Inventory
from apps.payments.models import Payment
from apps.shipping.models import ShippingPartner, Shipment

User = get_user_model()


class UserJourneyIntegrationTest(TestCase):
    """Test complete user journeys through the e-commerce platform"""

    def setUp(self):
        """Set up test data for user journey tests"""
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
        
        # Create categories
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        self.subcategory = Category.objects.create(
            name='Smartphones',
            slug='smartphones',
            parent=self.category,
            is_active=True
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='Test Smartphone 1',
            slug='test-smartphone-1',
            description='A test smartphone with amazing features',
            short_description='Amazing test smartphone',
            category=self.subcategory,
            brand='TestBrand',
            sku='PHONE001',
            price=Decimal('499.99'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Smartphone 2',
            slug='test-smartphone-2',
            description='Another test smartphone with even better features',
            short_description='Better test smartphone',
            category=self.subcategory,
            brand='TestBrand',
            sku='PHONE002',
            price=Decimal('599.99'),
            is_active=True
        )
        
        # Create inventory
        self.inventory1 = Inventory.objects.create(
            product=self.product1,
            quantity=100,
            reserved_quantity=0,
            cost_price=Decimal('300.00')
        )
        
        self.inventory2 = Inventory.objects.create(
            product=self.product2,
            quantity=50,
            reserved_quantity=0,
            cost_price=Decimal('400.00')
        )
        
        # Create shipping partner
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST_SHIPPER',
            partner_type='STANDARD',
            is_active=True,
            supports_cod=True,
            supports_prepaid=True
        )
        
        # Create user address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Test',
            last_name='User',
            address_line_1='123 Test Street',
            city='Test City',
            state='Test State',
            postal_code='12345',
            country='Test Country',
            phone='1234567890',
            is_default=True
        )

    def test_complete_purchase_journey(self):
        """
        Test a complete user journey from login to purchase:
        1. User logs in
        2. User browses products
        3. User adds products to cart
        4. User proceeds to checkout
        5. User places an order
        6. Order is processed and payment is made
        7. Shipping is created
        8. Order status is updated
        """
        print("\nTesting complete purchase journey...")
        
        # Step 1: User logs in
        login_successful = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_successful, "Login failed")
        print("✓ User logged in successfully")
        
        # Step 2: User browses products
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, 200)
        products_data = response.json()
        self.assertGreaterEqual(len(products_data['results']), 2)
        print("✓ User browsed products successfully")
        
        # Step 3: User adds products to cart
        # First, check if user has a cart, create if not
        try:
            cart = Cart.objects.get(user=self.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=self.user)
        
        # Add first product to cart
        response = self.client.post('/api/v1/cart/items/', {
            'product_id': self.product1.id,
            'quantity': 1
        })
        self.assertEqual(response.status_code, 201)
        
        # Add second product to cart
        response = self.client.post('/api/v1/cart/items/', {
            'product_id': self.product2.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 201)
        
        # Verify cart contents
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertEqual(len(cart_data['items']), 2)
        self.assertEqual(Decimal(cart_data['total']), Decimal('499.99') + (Decimal('599.99') * 2))
        print("✓ User added products to cart successfully")
        
        # Step 4: User proceeds to checkout
        # Get shipping options
        response = self.client.get('/api/v1/shipping/rates/', {
            'postal_code': '12345',
            'country': 'Test Country'
        })
        self.assertEqual(response.status_code, 200)
        shipping_options = response.json()
        shipping_option_id = shipping_options[0]['id']
        
        # Get payment methods
        response = self.client.get('/api/v1/payments/methods/')
        self.assertEqual(response.status_code, 200)
        payment_methods = response.json()
        payment_method_id = payment_methods[0]['id']
        
        # Step 5: User places an order
        checkout_data = {
            'shipping_address_id': self.address.id,
            'billing_address_id': self.address.id,
            'shipping_method_id': shipping_option_id,
            'payment_method_id': payment_method_id,
            'notes': 'Please deliver to the front door'
        }
        
        response = self.client.post('/api/v1/orders/checkout/', checkout_data)
        self.assertEqual(response.status_code, 201)
        order_data = response.json()
        order_id = order_data['id']
        order_number = order_data['order_number']
        print(f"✓ User placed order successfully: {order_number}")
        
        # Step 6: Order is processed and payment is made
        # Simulate payment processing
        order = Order.objects.get(id=order_id)
        payment = Payment.objects.create(
            order=order,
            payment_id=f'PAY-{order_number}',
            payment_method='CREDIT_CARD',
            amount=order.total_amount,
            status='COMPLETED'
        )
        
        # Update order payment status
        order.payment_status = 'PAID'
        order.status = 'CONFIRMED'
        order.save()
        
        # Verify order status
        response = self.client.get(f'/api/v1/orders/{order_id}/')
        self.assertEqual(response.status_code, 200)
        updated_order_data = response.json()
        self.assertEqual(updated_order_data['payment_status'], 'PAID')
        self.assertEqual(updated_order_data['status'], 'CONFIRMED')
        print("✓ Payment processed successfully")
        
        # Step 7: Shipping is created
        # Simulate shipping creation
        shipment = Shipment.objects.create(
            order_id=order.id,
            shipping_partner=self.shipping_partner,
            tracking_number=f'TRACK-{order_number}',
            status='PROCESSING',
            shipping_address=order.shipping_address,
            weight=Decimal('1.5'),
            shipping_cost=order.shipping_amount
        )
        
        # Update order status to processing
        order.status = 'PROCESSING'
        order.save()
        
        # Verify order status
        response = self.client.get(f'/api/v1/orders/{order_id}/')
        self.assertEqual(response.status_code, 200)
        updated_order_data = response.json()
        self.assertEqual(updated_order_data['status'], 'PROCESSING')
        print("✓ Shipping created successfully")
        
        # Step 8: Order status is updated to shipped
        # Simulate shipping update
        shipment.status = 'SHIPPED'
        shipment.save()
        
        # Update order status
        order.status = 'SHIPPED'
        order.save()
        
        # Verify order status
        response = self.client.get(f'/api/v1/orders/{order_id}/')
        self.assertEqual(response.status_code, 200)
        updated_order_data = response.json()
        self.assertEqual(updated_order_data['status'], 'SHIPPED')
        print("✓ Order shipped successfully")
        
        # Verify inventory was updated
        inventory1 = Inventory.objects.get(product=self.product1)
        inventory2 = Inventory.objects.get(product=self.product2)
        self.assertEqual(inventory1.quantity, 99)  # 100 - 1
        self.assertEqual(inventory2.quantity, 48)  # 50 - 2
        print("✓ Inventory updated correctly")
        
        print("✓ Complete purchase journey test passed!")

    def test_cart_to_wishlist_journey(self):
        """
        Test user journey for cart and wishlist interactions:
        1. User logs in
        2. User adds products to cart
        3. User moves item from cart to wishlist
        4. User moves item from wishlist back to cart
        """
        print("\nTesting cart to wishlist journey...")
        
        # Step 1: User logs in
        login_successful = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_successful, "Login failed")
        print("✓ User logged in successfully")
        
        # Step 2: User adds products to cart
        # First, check if user has a cart, create if not
        try:
            cart = Cart.objects.get(user=self.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=self.user)
        
        # Add products to cart
        response = self.client.post('/api/v1/cart/items/', {
            'product_id': self.product1.id,
            'quantity': 1
        })
        self.assertEqual(response.status_code, 201)
        cart_item_id = response.json()['id']
        print("✓ User added product to cart successfully")
        
        # Step 3: User moves item from cart to wishlist
        response = self.client.post(f'/api/v1/cart/items/{cart_item_id}/save-for-later/')
        self.assertEqual(response.status_code, 200)
        
        # Verify cart is empty
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertEqual(len(cart_data['items']), 0)
        
        # Verify wishlist has the item
        response = self.client.get('/api/v1/wishlist/')
        self.assertEqual(response.status_code, 200)
        wishlist_data = response.json()
        self.assertEqual(len(wishlist_data['items']), 1)
        self.assertEqual(wishlist_data['items'][0]['product']['id'], self.product1.id)
        wishlist_item_id = wishlist_data['items'][0]['id']
        print("✓ User moved item from cart to wishlist successfully")
        
        # Step 4: User moves item from wishlist back to cart
        response = self.client.post(f'/api/v1/wishlist/items/{wishlist_item_id}/move-to-cart/')
        self.assertEqual(response.status_code, 200)
        
        # Verify wishlist is empty
        response = self.client.get('/api/v1/wishlist/')
        self.assertEqual(response.status_code, 200)
        wishlist_data = response.json()
        self.assertEqual(len(wishlist_data['items']), 0)
        
        # Verify cart has the item
        response = self.client.get('/api/v1/cart/')
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['product']['id'], self.product1.id)
        print("✓ User moved item from wishlist back to cart successfully")
        
        print("✓ Cart to wishlist journey test passed!")

    def test_order_cancellation_journey(self):
        """
        Test user journey for order cancellation:
        1. User logs in
        2. User places an order
        3. User cancels the order
        4. Inventory is restored
        """
        print("\nTesting order cancellation journey...")
        
        # Step 1: User logs in
        login_successful = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_successful, "Login failed")
        print("✓ User logged in successfully")
        
        # Create a cart and add items
        try:
            cart = Cart.objects.get(user=self.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=self.user)
        
        # Add product to cart
        response = self.client.post('/api/v1/cart/items/', {
            'product_id': self.product1.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 201)
        print("✓ User added product to cart successfully")
        
        # Step 2: User places an order
        # Get shipping options
        response = self.client.get('/api/v1/shipping/rates/', {
            'postal_code': '12345',
            'country': 'Test Country'
        })
        self.assertEqual(response.status_code, 200)
        shipping_options = response.json()
        shipping_option_id = shipping_options[0]['id']
        
        # Get payment methods
        response = self.client.get('/api/v1/payments/methods/')
        self.assertEqual(response.status_code, 200)
        payment_methods = response.json()
        payment_method_id = payment_methods[0]['id']
        
        # Place order
        checkout_data = {
            'shipping_address_id': self.address.id,
            'billing_address_id': self.address.id,
            'shipping_method_id': shipping_option_id,
            'payment_method_id': payment_method_id
        }
        
        response = self.client.post('/api/v1/orders/checkout/', checkout_data)
        self.assertEqual(response.status_code, 201)
        order_data = response.json()
        order_id = order_data['id']
        print(f"✓ User placed order successfully: {order_data['order_number']}")
        
        # Check inventory was reduced
        inventory_before = Inventory.objects.get(product=self.product1)
        self.assertEqual(inventory_before.quantity, 98)  # 100 - 2
        print("✓ Inventory was reduced after order placement")
        
        # Step 3: User cancels the order
        response = self.client.post(f'/api/v1/orders/{order_id}/cancel/', {
            'cancellation_reason': 'Changed my mind'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify order status
        response = self.client.get(f'/api/v1/orders/{order_id}/')
        self.assertEqual(response.status_code, 200)
        updated_order_data = response.json()
        self.assertEqual(updated_order_data['status'], 'CANCELLED')
        print("✓ Order cancelled successfully")
        
        # Step 4: Verify inventory was restored
        inventory_after = Inventory.objects.get(product=self.product1)
        self.assertEqual(inventory_after.quantity, 100)  # Back to original
        print("✓ Inventory was restored after cancellation")
        
        print("✓ Order cancellation journey test passed!")


def main():
    """Run the integration tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_user_journey'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()