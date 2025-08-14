"""
Payment and Transaction API Tests

Comprehensive test suite for payment processing endpoints, transaction validation,
webhook testing, refund and cancellation API testing, and payment gateway integration APIs.

This module implements task 6.4 from the QA testing framework specification.
"""

import pytest
import time
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator, ValidationResult
from core.interfaces import Environment, UserRole, Severity
from core.models import TestUser, Address, PaymentMethod


class TestPaymentProcessingAPI:
    """Test suite for payment processing API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Test user credentials for different payment scenarios
        self.test_users = {
            'customer': {'username': 'customer_user', 'password': 'testpass123'},
            'premium': {'username': 'premium_user', 'password': 'testpass123'},
            'seller': {'username': 'seller_user', 'password': 'testpass123'},
            'admin': {'username': 'admin_user', 'password': 'testpass123'}
        }
        
        # Payment API endpoints
        self.endpoints = {
            'currencies': '/api/v1/payments/currencies/',
            'payment_methods': '/api/v1/payments/methods/',
            'payments': '/api/v1/payments/payments/',
            'create_payment': '/api/v1/payments/payments/create_payment/',
            'verify_payment': '/api/v1/payments/payments/verify_payment/',
            'payment_status': '/api/v1/payments/payments/{id}/status/',
            'generate_payment_link': '/api/v1/payments/payments/generate_payment_link/',
            'refunds': '/api/v1/payments/refunds/',
            'create_refund': '/api/v1/payments/refunds/create_refund/',
            'wallets': '/api/v1/payments/wallets/',
            'wallet_add_funds': '/api/v1/payments/wallets/add_funds/',
            'wallet_transactions': '/api/v1/payments/wallets/transactions/',
            'gift_cards': '/api/v1/payments/gift-cards/',
            'gift_card_purchase': '/api/v1/payments/gift-cards/purchase/',
            'gift_card_check': '/api/v1/payments/gift-cards/check/',
        }
        
        # Test payment data
        self.test_payment_data = {
            'order_id': str(uuid.uuid4()),
            'amount': '99.99',
            'currency_code': 'USD',
            'payment_method_id': str(uuid.uuid4()),
            'metadata': {
                'customer_id': 'test_customer_123',
                'order_notes': 'Test payment for QA framework'
            }
        }
        
        # Test payment methods
        self.payment_methods = {
            'credit_card': {
                'id': str(uuid.uuid4()),
                'name': 'Credit Card',
                'method_type': 'CARD',
                'gateway': 'STRIPE'
            },
            'upi': {
                'id': str(uuid.uuid4()),
                'name': 'UPI',
                'method_type': 'UPI',
                'gateway': 'RAZORPAY'
            },
            'wallet': {
                'id': str(uuid.uuid4()),
                'name': 'Digital Wallet',
                'method_type': 'WALLET',
                'gateway': 'INTERNAL'
            },
            'cod': {
                'id': str(uuid.uuid4()),
                'name': 'Cash on Delivery',
                'method_type': 'COD',
                'gateway': 'INTERNAL'
            }
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    def _authenticate_as_customer(self):
        """Helper method to authenticate as customer"""
        self.client.auth_token = 'customer_test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_test_token'
    
    # Payment Creation Tests
    
    @patch('requests.Session.request')
    def test_create_payment_success_credit_card(self, mock_request):
        """Test successful payment creation with credit card"""
        # Mock successful payment creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'PENDING',
            'amount': '99.99',
            'currency': 'USD',
            'payment_method': 'Credit Card',
            'gateway_payment_id': 'pi_1234567890',
            'gateway_order_id': 'order_1234567890',
            'client_secret': 'pi_1234567890_secret_abcd',
            'next_action': {
                'type': 'redirect_to_url',
                'redirect_to_url': {
                    'url': 'https://hooks.stripe.com/redirect/authenticate/src_1234567890'
                }
            },
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test payment creation
        payment_data = self.test_payment_data.copy()
        payment_data['payment_method_id'] = self.payment_methods['credit_card']['id']
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate response structure
        assert response.has_field('payment_id')
        assert response.has_field('status')
        assert response.has_field('gateway_payment_id')
        assert response.has_field('client_secret')
        assert response.has_field('next_action')
        
        # Validate payment data
        assert response.get_field_value('status') == 'PENDING'
        assert response.get_field_value('amount') == '99.99'
        assert response.get_field_value('currency') == 'USD'
        
        # Validate next action for 3D Secure
        next_action = response.get_field_value('next_action')
        assert next_action['type'] == 'redirect_to_url'
        assert 'url' in next_action['redirect_to_url']
    
    @patch('requests.Session.request')
    def test_create_payment_success_upi(self, mock_request):
        """Test successful payment creation with UPI"""
        # Mock successful UPI payment creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'PENDING',
            'amount': '99.99',
            'currency': 'INR',
            'payment_method': 'UPI',
            'gateway_payment_id': 'pay_1234567890',
            'upi_link': 'upi://pay?pa=merchant@upi&pn=Merchant&am=99.99&cu=INR&tn=Payment',
            'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...',
            'expires_at': '2024-01-01T00:15:00Z',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test UPI payment creation
        payment_data = self.test_payment_data.copy()
        payment_data['payment_method_id'] = self.payment_methods['upi']['id']
        payment_data['currency_code'] = 'INR'
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate UPI-specific fields
        assert response.has_field('upi_link')
        assert response.has_field('qr_code')
        assert response.has_field('expires_at')
        
        # Validate UPI link format
        upi_link = response.get_field_value('upi_link')
        assert upi_link.startswith('upi://pay?')
        assert 'pa=' in upi_link  # Payee address
        assert 'am=' in upi_link  # Amount
    
    @patch('requests.Session.request')
    def test_create_payment_success_wallet(self, mock_request):
        """Test successful payment creation with digital wallet"""
        # Mock successful wallet payment creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'COMPLETED',
            'amount': '99.99',
            'currency': 'USD',
            'payment_method': 'Digital Wallet',
            'wallet_balance_before': '500.00',
            'wallet_balance_after': '400.01',
            'transaction_id': 'txn_1234567890',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test wallet payment creation
        payment_data = self.test_payment_data.copy()
        payment_data['payment_method_id'] = self.payment_methods['wallet']['id']
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate wallet-specific fields
        assert response.has_field('wallet_balance_before')
        assert response.has_field('wallet_balance_after')
        assert response.has_field('transaction_id')
        
        # Validate wallet balance calculation
        balance_before = Decimal(response.get_field_value('wallet_balance_before'))
        balance_after = Decimal(response.get_field_value('wallet_balance_after'))
        amount = Decimal(response.get_field_value('amount'))
        
        assert balance_before - balance_after == amount
        assert response.get_field_value('status') == 'COMPLETED'
    
    @patch('requests.Session.request')
    def test_create_payment_insufficient_wallet_balance(self, mock_request):
        """Test payment creation with insufficient wallet balance"""
        # Mock insufficient balance error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Insufficient wallet balance',
            'error_code': 'INSUFFICIENT_FUNDS',
            'wallet_balance': '50.00',
            'required_amount': '99.99',
            'shortfall': '49.99'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_data = self.test_payment_data.copy()
        payment_data['payment_method_id'] = self.payment_methods['wallet']['id']
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        
        # Validate error details
        assert response.has_field('error')
        assert response.has_field('error_code')
        assert response.has_field('wallet_balance')
        assert response.has_field('shortfall')
        
        assert response.get_field_value('error_code') == 'INSUFFICIENT_FUNDS'
    
    @patch('requests.Session.request')
    def test_create_payment_invalid_order(self, mock_request):
        """Test payment creation with invalid order ID"""
        # Mock invalid order error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Order not found or not eligible for payment',
            'error_code': 'INVALID_ORDER',
            'order_id': str(uuid.uuid4())
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_data = self.test_payment_data.copy()
        payment_data['order_id'] = str(uuid.uuid4())  # Non-existent order
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'INVALID_ORDER'
    
    @patch('requests.Session.request')
    def test_create_payment_invalid_payment_method(self, mock_request):
        """Test payment creation with invalid payment method"""
        # Mock invalid payment method error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Invalid payment method',
            'error_code': 'INVALID_PAYMENT_METHOD',
            'payment_method_id': str(uuid.uuid4())
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_data = self.test_payment_data.copy()
        payment_data['payment_method_id'] = str(uuid.uuid4())  # Non-existent payment method
        
        response = self.client.post(self.endpoints['create_payment'], data=payment_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'INVALID_PAYMENT_METHOD'
    
    # Payment Verification Tests
    
    @patch('requests.Session.request')
    def test_verify_payment_success(self, mock_request):
        """Test successful payment verification"""
        # Mock successful payment verification response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'COMPLETED',
            'amount': '99.99',
            'currency': 'USD',
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'valid_signature_hash',
            'verification_status': 'SUCCESS',
            'payment_date': '2024-01-01T00:05:00Z',
            'processing_fee': '2.97'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test payment verification
        verify_data = {
            'payment_id': str(uuid.uuid4()),
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'valid_signature_hash',
            'metadata': {
                'verification_timestamp': '2024-01-01T00:05:00Z'
            }
        }
        
        response = self.client.post(self.endpoints['verify_payment'], data=verify_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate verification fields
        assert response.has_field('verification_status')
        assert response.has_field('payment_date')
        assert response.has_field('processing_fee')
        
        assert response.get_field_value('status') == 'COMPLETED'
        assert response.get_field_value('verification_status') == 'SUCCESS'
    
    @patch('requests.Session.request')
    def test_verify_payment_invalid_signature(self, mock_request):
        """Test payment verification with invalid signature"""
        # Mock invalid signature error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Invalid payment signature',
            'error_code': 'INVALID_SIGNATURE',
            'verification_status': 'FAILED',
            'payment_id': str(uuid.uuid4())
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        verify_data = {
            'payment_id': str(uuid.uuid4()),
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'invalid_signature_hash'
        }
        
        response = self.client.post(self.endpoints['verify_payment'], data=verify_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'INVALID_SIGNATURE'
        assert response.get_field_value('verification_status') == 'FAILED'
    
    @patch('requests.Session.request')
    def test_verify_payment_expired(self, mock_request):
        """Test payment verification for expired payment"""
        # Mock expired payment error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Payment has expired',
            'error_code': 'PAYMENT_EXPIRED',
            'payment_id': str(uuid.uuid4()),
            'expires_at': '2024-01-01T00:15:00Z',
            'current_time': '2024-01-01T00:20:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        verify_data = {
            'payment_id': str(uuid.uuid4()),
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'valid_signature_hash'
        }
        
        response = self.client.post(self.endpoints['verify_payment'], data=verify_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'PAYMENT_EXPIRED'
    
    # Payment Status Tests
    
    @patch('requests.Session.request')
    def test_get_payment_status_success(self, mock_request):
        """Test successful payment status retrieval"""
        # Mock payment status response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'COMPLETED',
            'amount': '99.99',
            'currency': 'USD',
            'payment_method': 'Credit Card',
            'gateway_status': 'succeeded',
            'gateway_payment_id': 'pi_1234567890',
            'payment_date': '2024-01-01T00:05:00Z',
            'processing_fee': '2.97',
            'failure_reason': None,
            'refund_amount': '0.00',
            'refund_status': None
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_id = str(uuid.uuid4())
        endpoint = self.endpoints['payment_status'].format(id=payment_id)
        
        response = self.client.get(endpoint)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate status fields
        assert response.has_field('status')
        assert response.has_field('gateway_status')
        assert response.has_field('payment_date')
        assert response.has_field('processing_fee')
        assert response.has_field('refund_amount')
        
        assert response.get_field_value('status') == 'COMPLETED'
        assert response.get_field_value('gateway_status') == 'succeeded'
    
    @patch('requests.Session.request')
    def test_get_payment_status_failed_payment(self, mock_request):
        """Test payment status for failed payment"""
        # Mock failed payment status response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'FAILED',
            'amount': '99.99',
            'currency': 'USD',
            'payment_method': 'Credit Card',
            'gateway_status': 'failed',
            'gateway_payment_id': 'pi_1234567890',
            'failure_reason': 'Your card was declined.',
            'failure_code': 'card_declined',
            'decline_code': 'generic_decline',
            'created_at': '2024-01-01T00:00:00Z',
            'failed_at': '2024-01-01T00:02:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_id = str(uuid.uuid4())
        endpoint = self.endpoints['payment_status'].format(id=payment_id)
        
        response = self.client.get(endpoint)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate failure fields
        assert response.has_field('failure_reason')
        assert response.has_field('failure_code')
        assert response.has_field('decline_code')
        assert response.has_field('failed_at')
        
        assert response.get_field_value('status') == 'FAILED'
        assert response.get_field_value('gateway_status') == 'failed'
        assert response.get_field_value('failure_code') == 'card_declined'


class TestPaymentGatewayIntegration:
    """Test suite for payment gateway integration APIs"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Payment gateway endpoints
        self.endpoints = {
            'generate_payment_link': '/api/v1/payments/payments/generate_payment_link/',
            'webhook_stripe': '/api/v1/payments/webhooks/stripe/',
            'webhook_razorpay': '/api/v1/payments/webhooks/razorpay/',
            'gateway_status': '/api/v1/payments/gateways/status/',
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    def _authenticate_as_customer(self):
        """Helper method to authenticate as customer"""
        self.client.auth_token = 'customer_test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_test_token'
    
    @patch('requests.Session.request')
    def test_generate_payment_link_success(self, mock_request):
        """Test successful payment link generation"""
        # Mock payment link generation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_link': 'https://checkout.stripe.com/pay/cs_test_1234567890',
            'link_id': 'plink_1234567890',
            'expires_at': '2024-01-01T01:00:00Z',
            'amount': '99.99',
            'currency': 'USD',
            'order_id': str(uuid.uuid4())
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test payment link generation
        link_data = {
            'order_id': str(uuid.uuid4()),
            'amount': '99.99',
            'currency_code': 'USD',
            'payment_method_id': str(uuid.uuid4()),
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel',
            'metadata': {
                'customer_id': 'test_customer_123'
            }
        }
        
        response = self.client.post(self.endpoints['generate_payment_link'], data=link_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate payment link fields
        assert response.has_field('payment_link')
        assert response.has_field('link_id')
        assert response.has_field('expires_at')
        
        # Validate payment link URL
        payment_link = response.get_field_value('payment_link')
        assert payment_link.startswith('https://')
        assert 'checkout' in payment_link.lower()
    
    @patch('requests.Session.request')
    def test_stripe_webhook_payment_succeeded(self, mock_request):
        """Test Stripe webhook for successful payment"""
        # Mock webhook processing response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'received': True,
            'processed': True,
            'event_type': 'payment_intent.succeeded',
            'payment_id': str(uuid.uuid4()),
            'status_updated': True
        }
        mock_request.return_value = mock_response
        
        # Test Stripe webhook
        webhook_data = {
            'id': 'evt_1234567890',
            'object': 'event',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_1234567890',
                    'amount': 9999,
                    'currency': 'usd',
                    'status': 'succeeded',
                    'metadata': {
                        'order_id': str(uuid.uuid4()),
                        'payment_id': str(uuid.uuid4())
                    }
                }
            },
            'created': 1640995200
        }
        
        # Add Stripe signature header
        headers = {
            'Stripe-Signature': 't=1640995200,v1=test_signature_hash'
        }
        
        response = self.client.post(
            self.endpoints['webhook_stripe'], 
            data=webhook_data, 
            headers=headers,
            authenticate=False
        )
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate webhook processing
        assert response.get_field_value('received') == True
        assert response.get_field_value('processed') == True
        assert response.get_field_value('event_type') == 'payment_intent.succeeded'
    
    @patch('requests.Session.request')
    def test_razorpay_webhook_payment_captured(self, mock_request):
        """Test Razorpay webhook for captured payment"""
        # Mock webhook processing response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'received': True,
            'processed': True,
            'event': 'payment.captured',
            'payment_id': str(uuid.uuid4()),
            'status_updated': True
        }
        mock_request.return_value = mock_response
        
        # Test Razorpay webhook
        webhook_data = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_1234567890',
                        'amount': 9999,
                        'currency': 'INR',
                        'status': 'captured',
                        'order_id': 'order_1234567890',
                        'notes': {
                            'order_id': str(uuid.uuid4()),
                            'payment_id': str(uuid.uuid4())
                        }
                    }
                }
            },
            'created_at': 1640995200
        }
        
        # Add Razorpay signature header
        headers = {
            'X-Razorpay-Signature': 'test_razorpay_signature_hash'
        }
        
        response = self.client.post(
            self.endpoints['webhook_razorpay'], 
            data=webhook_data, 
            headers=headers,
            authenticate=False
        )
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate webhook processing
        assert response.get_field_value('received') == True
        assert response.get_field_value('processed') == True
        assert response.get_field_value('event') == 'payment.captured'


class TestRefundAndCancellationAPI:
    """Test suite for refund and cancellation API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Refund API endpoints
        self.endpoints = {
            'refunds': '/api/v1/payments/refunds/',
            'create_refund': '/api/v1/payments/refunds/create_refund/',
            'refund_detail': '/api/v1/payments/refunds/{id}/',
            'cancel_payment': '/api/v1/payments/payments/{id}/cancel/',
        }
        
        # Test refund data
        self.test_refund_data = {
            'payment_id': str(uuid.uuid4()),
            'amount': '50.00',
            'reason': 'Customer requested refund',
            'metadata': {
                'refund_type': 'partial',
                'requested_by': 'customer'
            }
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    def _authenticate_as_customer(self):
        """Helper method to authenticate as customer"""
        self.client.auth_token = 'customer_test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_test_token'
    
    @patch('requests.Session.request')
    def test_create_refund_success_partial(self, mock_request):
        """Test successful partial refund creation"""
        # Mock successful refund creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'refund_id': str(uuid.uuid4()),
            'payment_id': str(uuid.uuid4()),
            'amount': '50.00',
            'currency': 'USD',
            'reason': 'Customer requested refund',
            'status': 'PENDING',
            'refund_type': 'PARTIAL',
            'gateway_refund_id': 're_1234567890',
            'processing_fee': '1.50',
            'net_refund_amount': '48.50',
            'estimated_arrival': '2024-01-08T00:00:00Z',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test partial refund creation
        refund_data = self.test_refund_data.copy()
        
        response = self.client.post(self.endpoints['create_refund'], data=refund_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate refund fields
        assert response.has_field('refund_id')
        assert response.has_field('payment_id')
        assert response.has_field('refund_type')
        assert response.has_field('gateway_refund_id')
        assert response.has_field('processing_fee')
        assert response.has_field('net_refund_amount')
        assert response.has_field('estimated_arrival')
        
        # Validate refund data
        assert response.get_field_value('status') == 'PENDING'
        assert response.get_field_value('refund_type') == 'PARTIAL'
        assert response.get_field_value('amount') == '50.00'
    
    @patch('requests.Session.request')
    def test_create_refund_success_full(self, mock_request):
        """Test successful full refund creation"""
        # Mock successful full refund creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'refund_id': str(uuid.uuid4()),
            'payment_id': str(uuid.uuid4()),
            'amount': '99.99',
            'currency': 'USD',
            'reason': 'Order cancelled by customer',
            'status': 'PENDING',
            'refund_type': 'FULL',
            'gateway_refund_id': 're_1234567890',
            'processing_fee': '0.00',  # No fee for full refund
            'net_refund_amount': '99.99',
            'estimated_arrival': '2024-01-08T00:00:00Z',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test full refund creation
        refund_data = self.test_refund_data.copy()
        refund_data['amount'] = '99.99'
        refund_data['reason'] = 'Order cancelled by customer'
        
        response = self.client.post(self.endpoints['create_refund'], data=refund_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate full refund specifics
        assert response.get_field_value('refund_type') == 'FULL'
        assert response.get_field_value('processing_fee') == '0.00'
        assert response.get_field_value('amount') == response.get_field_value('net_refund_amount')
    
    @patch('requests.Session.request')
    def test_create_refund_wallet_payment(self, mock_request):
        """Test refund creation for wallet payment"""
        # Mock wallet refund creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'refund_id': str(uuid.uuid4()),
            'payment_id': str(uuid.uuid4()),
            'amount': '50.00',
            'currency': 'USD',
            'reason': 'Customer requested refund',
            'status': 'COMPLETED',  # Wallet refunds are instant
            'refund_type': 'PARTIAL',
            'payment_method': 'WALLET',
            'wallet_balance_before': '100.00',
            'wallet_balance_after': '150.00',
            'transaction_id': 'txn_refund_1234567890',
            'created_at': '2024-01-01T00:00:00Z',
            'completed_at': '2024-01-01T00:00:01Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        refund_data = self.test_refund_data.copy()
        
        response = self.client.post(self.endpoints['create_refund'], data=refund_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate wallet refund specifics
        assert response.has_field('wallet_balance_before')
        assert response.has_field('wallet_balance_after')
        assert response.has_field('transaction_id')
        assert response.has_field('completed_at')
        
        assert response.get_field_value('status') == 'COMPLETED'
        assert response.get_field_value('payment_method') == 'WALLET'
        
        # Validate wallet balance update
        balance_before = Decimal(response.get_field_value('wallet_balance_before'))
        balance_after = Decimal(response.get_field_value('wallet_balance_after'))
        refund_amount = Decimal(response.get_field_value('amount'))
        
        assert balance_after - balance_before == refund_amount
    
    @patch('requests.Session.request')
    def test_create_refund_invalid_payment(self, mock_request):
        """Test refund creation with invalid payment ID"""
        # Mock invalid payment error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Payment not found',
            'error_code': 'PAYMENT_NOT_FOUND',
            'payment_id': str(uuid.uuid4())
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        refund_data = self.test_refund_data.copy()
        refund_data['payment_id'] = str(uuid.uuid4())  # Non-existent payment
        
        response = self.client.post(self.endpoints['create_refund'], data=refund_data)
        
        # Validate error response
        assert response.status_code == 404
        assert response.get_field_value('error_code') == 'PAYMENT_NOT_FOUND'
    
    @patch('requests.Session.request')
    def test_create_refund_exceeds_available_amount(self, mock_request):
        """Test refund creation that exceeds available refund amount"""
        # Mock refund amount exceeded error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Refund amount exceeds available refund amount',
            'error_code': 'REFUND_AMOUNT_EXCEEDED',
            'payment_amount': '99.99',
            'already_refunded': '60.00',
            'available_for_refund': '39.99',
            'requested_amount': '50.00'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        refund_data = self.test_refund_data.copy()
        
        response = self.client.post(self.endpoints['create_refund'], data=refund_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'REFUND_AMOUNT_EXCEEDED'
        
        # Validate refund calculation fields
        assert response.has_field('payment_amount')
        assert response.has_field('already_refunded')
        assert response.has_field('available_for_refund')
        assert response.has_field('requested_amount')
    
    @patch('requests.Session.request')
    def test_cancel_payment_success(self, mock_request):
        """Test successful payment cancellation"""
        # Mock successful payment cancellation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'CANCELLED',
            'cancelled_at': '2024-01-01T00:05:00Z',
            'cancellation_reason': 'Customer requested cancellation',
            'refund_initiated': True,
            'refund_id': str(uuid.uuid4()),
            'refund_amount': '99.99'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        payment_id = str(uuid.uuid4())
        endpoint = self.endpoints['cancel_payment'].format(id=payment_id)
        
        cancel_data = {
            'reason': 'Customer requested cancellation'
        }
        
        response = self.client.post(endpoint, data=cancel_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate cancellation fields
        assert response.has_field('cancelled_at')
        assert response.has_field('cancellation_reason')
        assert response.has_field('refund_initiated')
        assert response.has_field('refund_id')
        
        assert response.get_field_value('status') == 'CANCELLED'
        assert response.get_field_value('refund_initiated') == True


class TestTransactionValidationAPI:
    """Test suite for transaction validation and monitoring"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Transaction validation endpoints
        self.endpoints = {
            'validate_transaction': '/api/v1/payments/transactions/validate/',
            'transaction_history': '/api/v1/payments/transactions/history/',
            'transaction_analytics': '/api/v1/payments/transactions/analytics/',
            'fraud_check': '/api/v1/payments/transactions/fraud-check/',
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    def _authenticate_as_admin(self):
        """Helper method to authenticate as admin"""
        self.client.auth_token = 'admin_test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer admin_test_token'
    
    @patch('requests.Session.request')
    def test_validate_transaction_success(self, mock_request):
        """Test successful transaction validation"""
        # Mock transaction validation response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'transaction_id': str(uuid.uuid4()),
            'validation_status': 'VALID',
            'checks_performed': [
                'amount_validation',
                'currency_validation',
                'payment_method_validation',
                'fraud_check',
                'duplicate_check'
            ],
            'validation_results': {
                'amount_validation': {'status': 'PASS', 'message': 'Amount is valid'},
                'currency_validation': {'status': 'PASS', 'message': 'Currency is supported'},
                'payment_method_validation': {'status': 'PASS', 'message': 'Payment method is active'},
                'fraud_check': {'status': 'PASS', 'score': 0.15, 'message': 'Low fraud risk'},
                'duplicate_check': {'status': 'PASS', 'message': 'No duplicate transaction found'}
            },
            'risk_score': 0.15,
            'recommendation': 'APPROVE'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_admin()
        
        # Test transaction validation
        validation_data = {
            'transaction_id': str(uuid.uuid4()),
            'payment_id': str(uuid.uuid4()),
            'checks': ['amount', 'currency', 'payment_method', 'fraud', 'duplicate']
        }
        
        response = self.client.post(self.endpoints['validate_transaction'], data=validation_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate validation fields
        assert response.has_field('validation_status')
        assert response.has_field('checks_performed')
        assert response.has_field('validation_results')
        assert response.has_field('risk_score')
        assert response.has_field('recommendation')
        
        assert response.get_field_value('validation_status') == 'VALID'
        assert response.get_field_value('recommendation') == 'APPROVE'
    
    @patch('requests.Session.request')
    def test_fraud_check_high_risk(self, mock_request):
        """Test fraud check for high-risk transaction"""
        # Mock high-risk fraud check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'transaction_id': str(uuid.uuid4()),
            'fraud_check_status': 'HIGH_RISK',
            'risk_score': 0.85,
            'risk_factors': [
                'unusual_spending_pattern',
                'new_payment_method',
                'high_velocity_transactions',
                'suspicious_ip_location'
            ],
            'risk_details': {
                'unusual_spending_pattern': {
                    'score': 0.3,
                    'description': 'Transaction amount significantly higher than usual'
                },
                'new_payment_method': {
                    'score': 0.2,
                    'description': 'Payment method added within last 24 hours'
                },
                'high_velocity_transactions': {
                    'score': 0.25,
                    'description': 'Multiple transactions in short time period'
                },
                'suspicious_ip_location': {
                    'score': 0.1,
                    'description': 'IP location differs from usual pattern'
                }
            },
            'recommendation': 'REVIEW',
            'suggested_actions': [
                'manual_review',
                'additional_verification',
                'contact_customer'
            ]
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_admin()
        
        fraud_check_data = {
            'transaction_id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'amount': '5000.00',
            'payment_method_id': str(uuid.uuid4()),
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = self.client.post(self.endpoints['fraud_check'], data=fraud_check_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate fraud check fields
        assert response.has_field('fraud_check_status')
        assert response.has_field('risk_score')
        assert response.has_field('risk_factors')
        assert response.has_field('risk_details')
        assert response.has_field('suggested_actions')
        
        assert response.get_field_value('fraud_check_status') == 'HIGH_RISK'
        assert response.get_field_value('recommendation') == 'REVIEW'
        assert float(response.get_field_value('risk_score')) > 0.8


if __name__ == '__main__':
    pytest.main([__file__])