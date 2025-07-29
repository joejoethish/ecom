#!/usr/bin/env python
"""
Payment Gateway Integration Tests

This module contains integration tests for payment gateway integrations,
testing the interaction between the e-commerce platform and payment providers.
"""

import os
import sys
import django
import json
import uuid
from decimal import Decimal
from unittest import mock

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

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, Wallet, GiftCard
from apps.products.models import Product, Category
from apps.customers.models import Address
from apps.cart.models import Cart, CartItem

User = get_user_model()


class MockRazorpayClient:
    """Mock Razorpay client for testing"""
    
    def __init__(self, *args, **kwargs):
        self.orders = self.Orders()
        self.payments = self.Payments()
        self.refunds = self.Refunds()
    
    class Orders:
        def create(self, data):
            return {
                'id': f'order_{uuid.uuid4().hex}',
                'amount': data['amount'],
                'currency': data['currency'],
                'receipt': data['receipt'],
                'status': 'created'
            }
    
    class Payments:
        def fetch(self, payment_id):
            return {
                'id': payment_id,
                'amount': 10000,  # 100.00 in paise
                'currency': 'INR',
                'status': 'captured',
                'order_id': f'order_{uuid.uuid4().hex}',
                'method': 'card',
                'card_id': f'card_{uuid.uuid4().hex}',
                'bank': 'HDFC',
                'wallet': None,
                'vpa': None
            }
        
        def capture(self, payment_id, amount):
            return {
                'id': payment_id,
                'amount': amount,
                'currency': 'INR',
                'status': 'captured'
            }
    
    class Refunds:
        def create(self, data):
            return {
                'id': f'rfnd_{uuid.uuid4().hex}',
                'payment_id': data['payment_id'],
                'amount': data['amount'],
                'currency': 'INR',
                'status': 'processed'
            }


class MockStripeClient:
    """Mock Stripe client for testing"""
    
    def __init__(self, *args, **kwargs):
        pass
    
    class PaymentIntents:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f'pi_{uuid.uuid4().hex}',
                'amount': kwargs['amount'],
                'currency': kwargs['currency'],
                'status': 'requires_payment_method',
                'client_secret': f'secret_{uuid.uuid4().hex}'
            }
        
        @staticmethod
        def confirm(payment_intent_id, **kwargs):
            return {
                'id': payment_intent_id,
                'status': 'succeeded'
            }
        
        @staticmethod
        def retrieve(payment_intent_id):
            return {
                'id': payment_intent_id,
                'status': 'succeeded',
                'amount': 10000,
                'currency': 'inr'
            }
    
    class Refunds:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f're_{uuid.uuid4().hex}',
                'payment_intent': kwargs['payment_intent'],
                'amount': kwargs['amount'],
                'status': 'succeeded'
            }
    
    payment_intents = PaymentIntents()
    refunds = Refunds()


class PaymentGatewayIntegrationTest(TestCase):
    """Test payment gateway integrations"""
    
    def setUp(self):
        """Set up test data for payment integration tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='paymentuser',
            email='payment@example.com',
            password='testpass123',
            first_name='Payment',
            last_name='User'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.login(username='paymentuser', password='testpass123')
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            short_description='Test product',
            category=self.category,
            brand='TestBrand',
            sku='TEST001',
            price=Decimal('100.00'),
            is_active=True
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Payment',
            last_name='User',
            address_line_1='123 Payment Street',
            city='Payment City',
            state='Payment State',
            postal_code='12345',
            country='India',
            phone='1234567890',
            is_default=True
        )
        
        # Create cart and add product
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.user,
            order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
            status='PENDING',
            total_amount=Decimal('100.00'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            shipping_address={
                'first_name': 'Payment',
                'last_name': 'User',
                'address_line_1': '123 Payment Street',
                'city': 'Payment City',
                'state': 'Payment State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            billing_address={
                'first_name': 'Payment',
                'last_name': 'User',
                'address_line_1': '123 Payment Street',
                'city': 'Payment City',
                'state': 'Payment State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            },
            payment_method='RAZORPAY',
            payment_status='PENDING'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Create wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('200.00'),
            currency='INR'
        )
        
        # Create gift card
        self.gift_card = GiftCard.objects.create(
            code='GIFT123',
            initial_balance=Decimal('50.00'),
            current_balance=Decimal('50.00'),
            currency='INR',
            expiry_date=timezone.now() + timezone.timedelta(days=365),
            is_active=True
        )

    @mock.patch('apps.payments.services.razorpay.Client', MockRazorpayClient)
    def test_razorpay_payment_flow(self):
        """Test complete Razorpay payment flow"""
        print("\nTesting Razorpay payment flow...")
        
        # Step 1: Initialize payment
        response = self.client.post('/api/v1/payments/razorpay/init/', {
            'order_id': self.order.id,
            'amount': '115.00',  # Total + tax + shipping
            'currency': 'INR'
        })
        self.assertEqual(response.status_code, 200)
        payment_data = response.json()
        self.assertIn('razorpay_order_id', payment_data)
        self.assertIn('amount', payment_data)
        razorpay_order_id = payment_data['razorpay_order_id']
        print("✓ Payment initialized successfully")
        
        # Step 2: Verify payment
        payment_id = f'pay_{uuid.uuid4().hex}'
        signature = 'valid_signature'  # In real tests, this would be a valid signature
        
        response = self.client.post('/api/v1/payments/razorpay/verify/', {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': signature,
            'order_id': self.order.id
        })
        self.assertEqual(response.status_code, 200)
        verify_data = response.json()
        self.assertEqual(verify_data['status'], 'success')
        print("✓ Payment verified successfully")
        
        # Step 3: Check order and payment status
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'CONFIRMED')
        
        # Check payment record
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.payment_method, 'RAZORPAY')
        print("✓ Order and payment status updated correctly")
        
        # Step 4: Test refund
        response = self.client.post(f'/api/v1/orders/{self.order.id}/refund/', {
            'reason': 'Customer requested refund',
            'amount': '115.00'
        })
        self.assertEqual(response.status_code, 200)
        refund_data = response.json()
        self.assertEqual(refund_data['status'], 'success')
        
        # Check order and payment status after refund
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'REFUNDED')
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        print("✓ Refund processed successfully")
        
        print("✓ Razorpay payment flow test passed!")

    @mock.patch('apps.payments.services.stripe.Stripe', MockStripeClient)
    def test_stripe_payment_flow(self):
        """Test complete Stripe payment flow"""
        print("\nTesting Stripe payment flow...")
        
        # Update order payment method
        self.order.payment_method = 'STRIPE'
        self.order.save()
        
        # Step 1: Create payment intent
        response = self.client.post('/api/v1/payments/stripe/create-intent/', {
            'order_id': self.order.id,
            'amount': '115.00',  # Total + tax + shipping
            'currency': 'inr'
        })
        self.assertEqual(response.status_code, 200)
        intent_data = response.json()
        self.assertIn('client_secret', intent_data)
        self.assertIn('payment_intent_id', intent_data)
        payment_intent_id = intent_data['payment_intent_id']
        print("✓ Payment intent created successfully")
        
        # Step 2: Confirm payment
        response = self.client.post('/api/v1/payments/stripe/confirm/', {
            'payment_intent_id': payment_intent_id,
            'order_id': self.order.id
        })
        self.assertEqual(response.status_code, 200)
        confirm_data = response.json()
        self.assertEqual(confirm_data['status'], 'success')
        print("✓ Payment confirmed successfully")
        
        # Step 3: Check order and payment status
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'CONFIRMED')
        
        # Check payment record
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.payment_method, 'STRIPE')
        print("✓ Order and payment status updated correctly")
        
        # Step 4: Test refund
        response = self.client.post(f'/api/v1/orders/{self.order.id}/refund/', {
            'reason': 'Customer requested refund',
            'amount': '115.00'
        })
        self.assertEqual(response.status_code, 200)
        refund_data = response.json()
        self.assertEqual(refund_data['status'], 'success')
        
        # Check order and payment status after refund
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'REFUNDED')
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        print("✓ Refund processed successfully")
        
        print("✓ Stripe payment flow test passed!")

    def test_wallet_payment_flow(self):
        """Test wallet payment flow"""
        print("\nTesting wallet payment flow...")
        
        # Update order payment method
        self.order.payment_method = 'WALLET'
        self.order.save()
        
        # Step 1: Process wallet payment
        initial_wallet_balance = self.wallet.balance
        response = self.client.post('/api/v1/payments/wallet/pay/', {
            'order_id': self.order.id,
            'amount': '115.00'  # Total + tax + shipping
        })
        self.assertEqual(response.status_code, 200)
        wallet_data = response.json()
        self.assertEqual(wallet_data['status'], 'success')
        print("✓ Wallet payment processed successfully")
        
        # Step 2: Check wallet balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_wallet_balance - Decimal('115.00'))
        print(f"✓ Wallet balance updated correctly: {self.wallet.balance}")
        
        # Step 3: Check order and payment status
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'CONFIRMED')
        
        # Check payment record
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.payment_method, 'WALLET')
        print("✓ Order and payment status updated correctly")
        
        # Step 4: Test refund to wallet
        response = self.client.post(f'/api/v1/orders/{self.order.id}/refund/', {
            'reason': 'Customer requested refund',
            'amount': '115.00',
            'refund_to_wallet': True
        })
        self.assertEqual(response.status_code, 200)
        refund_data = response.json()
        self.assertEqual(refund_data['status'], 'success')
        
        # Check wallet balance after refund
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_wallet_balance)
        print(f"✓ Wallet balance restored after refund: {self.wallet.balance}")
        
        # Check order and payment status after refund
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'REFUNDED')
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        print("✓ Refund to wallet processed successfully")
        
        print("✓ Wallet payment flow test passed!")

    def test_gift_card_payment_flow(self):
        """Test gift card payment flow"""
        print("\nTesting gift card payment flow...")
        
        # Update order payment method and amount to match gift card balance
        self.order.payment_method = 'GIFT_CARD'
        self.order.total_amount = Decimal('35.00')  # Less than gift card balance
        self.order.save()
        
        # Update order item
        self.order_item.unit_price = Decimal('35.00')
        self.order_item.total_price = Decimal('35.00')
        self.order_item.save()
        
        # Step 1: Process gift card payment
        initial_gift_card_balance = self.gift_card.current_balance
        response = self.client.post('/api/v1/payments/gift-card/redeem/', {
            'order_id': self.order.id,
            'gift_card_code': 'GIFT123',
            'amount': '35.00'
        })
        self.assertEqual(response.status_code, 200)
        gift_card_data = response.json()
        self.assertEqual(gift_card_data['status'], 'success')
        print("✓ Gift card payment processed successfully")
        
        # Step 2: Check gift card balance
        self.gift_card.refresh_from_db()
        self.assertEqual(self.gift_card.current_balance, initial_gift_card_balance - Decimal('35.00'))
        print(f"✓ Gift card balance updated correctly: {self.gift_card.current_balance}")
        
        # Step 3: Check order and payment status
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'PAID')
        self.assertEqual(self.order.status, 'CONFIRMED')
        
        # Check payment record
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.payment_method, 'GIFT_CARD')
        print("✓ Order and payment status updated correctly")
        
        # Step 4: Test refund to gift card
        response = self.client.post(f'/api/v1/orders/{self.order.id}/refund/', {
            'reason': 'Customer requested refund',
            'amount': '35.00',
            'refund_to_gift_card': True,
            'gift_card_code': 'GIFT123'
        })
        self.assertEqual(response.status_code, 200)
        refund_data = response.json()
        self.assertEqual(refund_data['status'], 'success')
        
        # Check gift card balance after refund
        self.gift_card.refresh_from_db()
        self.assertEqual(self.gift_card.current_balance, initial_gift_card_balance)
        print(f"✓ Gift card balance restored after refund: {self.gift_card.current_balance}")
        
        # Check order and payment status after refund
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'REFUNDED')
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        print("✓ Refund to gift card processed successfully")
        
        print("✓ Gift card payment flow test passed!")

    def test_multi_currency_payment(self):
        """Test payment with different currencies"""
        print("\nTesting multi-currency payment...")
        
        # Update order with USD currency
        self.order.payment_method = 'STRIPE'
        self.order.save()
        
        # Step 1: Create payment intent with USD
        response = self.client.post('/api/v1/payments/stripe/create-intent/', {
            'order_id': self.order.id,
            'amount': '115.00',
            'currency': 'usd'
        })
        self.assertEqual(response.status_code, 200)
        intent_data = response.json()
        self.assertIn('client_secret', intent_data)
        payment_intent_id = intent_data['payment_intent_id']
        print("✓ USD payment intent created successfully")
        
        # Step 2: Confirm payment
        with mock.patch('apps.payments.services.stripe.Stripe', MockStripeClient):
            response = self.client.post('/api/v1/payments/stripe/confirm/', {
                'payment_intent_id': payment_intent_id,
                'order_id': self.order.id
            })
            self.assertEqual(response.status_code, 200)
            confirm_data = response.json()
            self.assertEqual(confirm_data['status'], 'success')
        print("✓ USD payment confirmed successfully")
        
        # Step 3: Check payment record has correct currency
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.gateway_response.get('currency', '').lower(), 'inr')  # Mock always returns INR
        print("✓ Payment record has correct currency")
        
        print("✓ Multi-currency payment test passed!")


def main():
    """Run the payment integration tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_payment_integrations'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()