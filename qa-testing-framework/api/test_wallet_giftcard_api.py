"""
Wallet and Gift Card API Tests

Comprehensive test suite for wallet management, gift card operations,
and related transaction processing APIs.

This module extends task 6.4 from the QA testing framework specification.
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


class TestWalletAPI:
    """Test suite for wallet management API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Wallet API endpoints
        self.endpoints = {
            'my_wallet': '/api/v1/payments/wallets/my_wallet/',
            'wallet_transactions': '/api/v1/payments/wallets/transactions/',
            'add_funds': '/api/v1/payments/wallets/add_funds/',
            'complete_add_funds': '/api/v1/payments/wallets/complete_add_funds/',
            'transfer_funds': '/api/v1/payments/wallets/transfer/',
            'wallet_balance': '/api/v1/payments/wallets/balance/',
        }
        
        # Test wallet data
        self.test_wallet_data = {
            'balance': '500.00',
            'currency': 'USD',
            'is_active': True
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
    def test_get_wallet_success(self, mock_request):
        """Test successful wallet retrieval"""
        # Mock wallet response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'balance': '500.00',
            'currency': {
                'code': 'USD',
                'name': 'US Dollar',
                'symbol': '$'
            },
            'is_active': True,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'last_transaction_at': '2024-01-01T11:30:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        response = self.client.get(self.endpoints['my_wallet'])
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate wallet fields
        assert response.has_field('id')
        assert response.has_field('balance')
        assert response.has_field('currency')
        assert response.has_field('is_active')
        assert response.has_field('last_transaction_at')
        
        # Validate currency details
        currency = response.get_field_value('currency')
        assert currency['code'] == 'USD'
        assert currency['symbol'] == '$'
        
        assert response.get_field_value('balance') == '500.00'
        assert response.get_field_value('is_active') == True
    
    @patch('requests.Session.request')
    def test_get_wallet_transactions_success(self, mock_request):
        """Test successful wallet transactions retrieval"""
        # Mock wallet transactions response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 3,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(uuid.uuid4()),
                    'transaction_type': 'CREDIT',
                    'amount': '100.00',
                    'description': 'Funds added via credit card',
                    'balance_before': '400.00',
                    'balance_after': '500.00',
                    'reference_id': str(uuid.uuid4()),
                    'created_at': '2024-01-01T12:00:00Z'
                },
                {
                    'id': str(uuid.uuid4()),
                    'transaction_type': 'DEBIT',
                    'amount': '50.00',
                    'description': 'Payment for order #12345',
                    'balance_before': '450.00',
                    'balance_after': '400.00',
                    'reference_id': str(uuid.uuid4()),
                    'created_at': '2024-01-01T10:30:00Z'
                },
                {
                    'id': str(uuid.uuid4()),
                    'transaction_type': 'CREDIT',
                    'amount': '25.00',
                    'description': 'Refund for order #12340',
                    'balance_before': '425.00',
                    'balance_after': '450.00',
                    'reference_id': str(uuid.uuid4()),
                    'created_at': '2024-01-01T09:15:00Z'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        response = self.client.get(self.endpoints['wallet_transactions'])
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate pagination structure
        assert response.has_field('count')
        assert response.has_field('results')
        
        # Validate transaction structure
        transactions = response.get_field_value('results')
        assert len(transactions) == 3
        
        for transaction in transactions:
            assert 'id' in transaction
            assert 'transaction_type' in transaction
            assert 'amount' in transaction
            assert 'balance_before' in transaction
            assert 'balance_after' in transaction
            assert 'description' in transaction
            assert 'created_at' in transaction
            
            # Validate transaction types
            assert transaction['transaction_type'] in ['CREDIT', 'DEBIT']
    
    @patch('requests.Session.request')
    def test_add_funds_success(self, mock_request):
        """Test successful funds addition to wallet"""
        # Mock add funds response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'PENDING',
            'amount': '100.00',
            'currency': 'USD',
            'payment_method': 'Credit Card',
            'gateway_payment_id': 'pi_1234567890',
            'client_secret': 'pi_1234567890_secret_abcd',
            'wallet_id': str(uuid.uuid4()),
            'current_balance': '500.00',
            'expected_balance_after': '600.00',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test add funds
        add_funds_data = {
            'amount': '100.00',
            'currency_code': 'USD',
            'payment_method_id': str(uuid.uuid4()),
            'metadata': {
                'source': 'wallet_topup',
                'user_initiated': True
            }
        }
        
        response = self.client.post(self.endpoints['add_funds'], data=add_funds_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate add funds fields
        assert response.has_field('payment_id')
        assert response.has_field('wallet_id')
        assert response.has_field('current_balance')
        assert response.has_field('expected_balance_after')
        assert response.has_field('client_secret')
        
        # Validate balance calculation
        current_balance = Decimal(response.get_field_value('current_balance'))
        expected_balance = Decimal(response.get_field_value('expected_balance_after'))
        amount = Decimal(response.get_field_value('amount'))
        
        assert expected_balance - current_balance == amount
        assert response.get_field_value('status') == 'PENDING'
    
    @patch('requests.Session.request')
    def test_complete_add_funds_success(self, mock_request):
        """Test successful completion of funds addition"""
        # Mock complete add funds response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'status': 'COMPLETED',
            'amount': '100.00',
            'currency': 'USD',
            'wallet_id': str(uuid.uuid4()),
            'balance_before': '500.00',
            'balance_after': '600.00',
            'transaction_id': 'txn_1234567890',
            'gateway_payment_id': 'pi_1234567890',
            'verification_status': 'SUCCESS',
            'completed_at': '2024-01-01T00:05:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test complete add funds
        complete_data = {
            'payment_id': str(uuid.uuid4()),
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'valid_signature_hash'
        }
        
        response = self.client.post(self.endpoints['complete_add_funds'], data=complete_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate completion fields
        assert response.has_field('verification_status')
        assert response.has_field('balance_before')
        assert response.has_field('balance_after')
        assert response.has_field('transaction_id')
        assert response.has_field('completed_at')
        
        assert response.get_field_value('status') == 'COMPLETED'
        assert response.get_field_value('verification_status') == 'SUCCESS'
    
    @patch('requests.Session.request')
    def test_add_funds_insufficient_minimum(self, mock_request):
        """Test add funds with amount below minimum"""
        # Mock minimum amount error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Amount below minimum required',
            'error_code': 'AMOUNT_TOO_LOW',
            'minimum_amount': '10.00',
            'requested_amount': '5.00',
            'currency': 'USD'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        add_funds_data = {
            'amount': '5.00',  # Below minimum
            'currency_code': 'USD',
            'payment_method_id': str(uuid.uuid4())
        }
        
        response = self.client.post(self.endpoints['add_funds'], data=add_funds_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'AMOUNT_TOO_LOW'
        assert response.has_field('minimum_amount')
    
    @patch('requests.Session.request')
    def test_wallet_balance_check(self, mock_request):
        """Test wallet balance check endpoint"""
        # Mock balance check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'wallet_id': str(uuid.uuid4()),
            'balance': '500.00',
            'currency': 'USD',
            'available_balance': '450.00',  # After pending transactions
            'pending_credits': '25.00',
            'pending_debits': '75.00',
            'last_updated': '2024-01-01T12:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        response = self.client.get(self.endpoints['wallet_balance'])
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate balance fields
        assert response.has_field('balance')
        assert response.has_field('available_balance')
        assert response.has_field('pending_credits')
        assert response.has_field('pending_debits')
        
        # Validate balance calculations
        balance = Decimal(response.get_field_value('balance'))
        available = Decimal(response.get_field_value('available_balance'))
        pending_debits = Decimal(response.get_field_value('pending_debits'))
        
        assert balance - pending_debits == available


class TestGiftCardAPI:
    """Test suite for gift card API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Gift card API endpoints
        self.endpoints = {
            'gift_cards': '/api/v1/payments/gift-cards/',
            'gift_card_detail': '/api/v1/payments/gift-cards/{id}/',
            'purchase_gift_card': '/api/v1/payments/gift-cards/purchase/',
            'complete_purchase': '/api/v1/payments/gift-cards/complete_purchase/',
            'check_gift_card': '/api/v1/payments/gift-cards/check/',
            'gift_card_transactions': '/api/v1/payments/gift-cards/{id}/transactions/',
            'redeem_gift_card': '/api/v1/payments/gift-cards/redeem/',
        }
        
        # Test gift card data
        self.test_gift_card_data = {
            'amount': '100.00',
            'currency_code': 'USD',
            'recipient_email': 'recipient@example.com',
            'expiry_days': 365,
            'message': 'Happy Birthday!'
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
    def test_purchase_gift_card_success(self, mock_request):
        """Test successful gift card purchase"""
        # Mock gift card purchase response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'gift_card_id': str(uuid.uuid4()),
            'status': 'PENDING',
            'amount': '100.00',
            'currency': 'USD',
            'recipient_email': 'recipient@example.com',
            'expiry_date': '2025-01-01T00:00:00Z',
            'payment_method': 'Credit Card',
            'gateway_payment_id': 'pi_1234567890',
            'client_secret': 'pi_1234567890_secret_abcd',
            'message': 'Happy Birthday!',
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test gift card purchase
        purchase_data = self.test_gift_card_data.copy()
        purchase_data['payment_method_id'] = str(uuid.uuid4())
        
        response = self.client.post(self.endpoints['purchase_gift_card'], data=purchase_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate gift card purchase fields
        assert response.has_field('payment_id')
        assert response.has_field('gift_card_id')
        assert response.has_field('recipient_email')
        assert response.has_field('expiry_date')
        assert response.has_field('message')
        assert response.has_field('client_secret')
        
        # Validate gift card data
        assert response.get_field_value('amount') == '100.00'
        assert response.get_field_value('recipient_email') == 'recipient@example.com'
        assert response.get_field_value('status') == 'PENDING'
    
    @patch('requests.Session.request')
    def test_complete_gift_card_purchase_success(self, mock_request):
        """Test successful completion of gift card purchase"""
        # Mock complete purchase response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'payment_id': str(uuid.uuid4()),
            'gift_card_id': str(uuid.uuid4()),
            'status': 'COMPLETED',
            'gift_card_code': 'GC-ABCD-1234-EFGH-5678',
            'amount': '100.00',
            'currency': 'USD',
            'recipient_email': 'recipient@example.com',
            'expiry_date': '2025-01-01T00:00:00Z',
            'verification_status': 'SUCCESS',
            'email_sent': True,
            'completed_at': '2024-01-01T00:05:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test complete gift card purchase
        complete_data = {
            'payment_id': str(uuid.uuid4()),
            'gateway_payment_id': 'pi_1234567890',
            'gateway_signature': 'valid_signature_hash'
        }
        
        response = self.client.post(self.endpoints['complete_purchase'], data=complete_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate completion fields
        assert response.has_field('gift_card_code')
        assert response.has_field('verification_status')
        assert response.has_field('email_sent')
        assert response.has_field('completed_at')
        
        # Validate gift card code format
        gift_card_code = response.get_field_value('gift_card_code')
        assert gift_card_code.startswith('GC-')
        assert len(gift_card_code.split('-')) == 5  # GC-XXXX-XXXX-XXXX-XXXX format
        
        assert response.get_field_value('status') == 'COMPLETED'
        assert response.get_field_value('verification_status') == 'SUCCESS'
        assert response.get_field_value('email_sent') == True
    
    @patch('requests.Session.request')
    def test_check_gift_card_valid(self, mock_request):
        """Test checking valid gift card details"""
        # Mock valid gift card check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'gift_card_id': str(uuid.uuid4()),
            'code': 'GC-ABCD-1234-EFGH-5678',
            'status': 'ACTIVE',
            'balance': '75.00',
            'original_amount': '100.00',
            'currency': 'USD',
            'expiry_date': '2025-01-01T00:00:00Z',
            'is_expired': False,
            'issued_to': 'recipient@example.com',
            'issued_at': '2024-01-01T00:00:00Z',
            'last_used_at': '2024-01-15T10:30:00Z',
            'usage_count': 2
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test gift card check
        check_data = {
            'code': 'GC-ABCD-1234-EFGH-5678'
        }
        
        response = self.client.post(self.endpoints['check_gift_card'], data=check_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate gift card details
        assert response.has_field('status')
        assert response.has_field('balance')
        assert response.has_field('original_amount')
        assert response.has_field('expiry_date')
        assert response.has_field('is_expired')
        assert response.has_field('usage_count')
        
        # Validate gift card status
        assert response.get_field_value('status') == 'ACTIVE'
        assert response.get_field_value('is_expired') == False
        assert response.get_field_value('balance') == '75.00'
        assert response.get_field_value('original_amount') == '100.00'
    
    @patch('requests.Session.request')
    def test_check_gift_card_expired(self, mock_request):
        """Test checking expired gift card"""
        # Mock expired gift card check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'gift_card_id': str(uuid.uuid4()),
            'code': 'GC-EXPIRED-1234-EFGH-5678',
            'status': 'EXPIRED',
            'balance': '50.00',
            'original_amount': '100.00',
            'currency': 'USD',
            'expiry_date': '2023-12-31T23:59:59Z',
            'is_expired': True,
            'issued_to': 'recipient@example.com',
            'issued_at': '2023-01-01T00:00:00Z',
            'expired_at': '2023-12-31T23:59:59Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        check_data = {
            'code': 'GC-EXPIRED-1234-EFGH-5678'
        }
        
        response = self.client.post(self.endpoints['check_gift_card'], data=check_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate expired gift card
        assert response.get_field_value('status') == 'EXPIRED'
        assert response.get_field_value('is_expired') == True
        assert response.has_field('expired_at')
    
    @patch('requests.Session.request')
    def test_check_gift_card_invalid(self, mock_request):
        """Test checking invalid gift card code"""
        # Mock invalid gift card error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Gift card not found',
            'error_code': 'GIFT_CARD_NOT_FOUND',
            'code': 'GC-INVALID-1234-EFGH-5678'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        check_data = {
            'code': 'GC-INVALID-1234-EFGH-5678'
        }
        
        response = self.client.post(self.endpoints['check_gift_card'], data=check_data)
        
        # Validate error response
        assert response.status_code == 404
        assert response.get_field_value('error_code') == 'GIFT_CARD_NOT_FOUND'
    
    @patch('requests.Session.request')
    def test_gift_card_transactions_success(self, mock_request):
        """Test successful gift card transactions retrieval"""
        # Mock gift card transactions response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': str(uuid.uuid4()),
                    'transaction_type': 'DEBIT',
                    'amount': '25.00',
                    'description': 'Payment for order #12345',
                    'balance_before': '100.00',
                    'balance_after': '75.00',
                    'order_id': str(uuid.uuid4()),
                    'created_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': str(uuid.uuid4()),
                    'transaction_type': 'ISSUED',
                    'amount': '100.00',
                    'description': 'Gift card issued',
                    'balance_before': '0.00',
                    'balance_after': '100.00',
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        gift_card_id = str(uuid.uuid4())
        endpoint = self.endpoints['gift_card_transactions'].format(id=gift_card_id)
        
        response = self.client.get(endpoint)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate transaction structure
        transactions = response.get_field_value('results')
        assert len(transactions) == 2
        
        for transaction in transactions:
            assert 'transaction_type' in transaction
            assert 'amount' in transaction
            assert 'balance_before' in transaction
            assert 'balance_after' in transaction
            assert 'description' in transaction
            
            # Validate transaction types
            assert transaction['transaction_type'] in ['DEBIT', 'ISSUED', 'REFUND']
    
    @patch('requests.Session.request')
    def test_redeem_gift_card_success(self, mock_request):
        """Test successful gift card redemption"""
        # Mock gift card redemption response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'gift_card_id': str(uuid.uuid4()),
            'code': 'GC-ABCD-1234-EFGH-5678',
            'redemption_amount': '25.00',
            'balance_before': '75.00',
            'balance_after': '50.00',
            'order_id': str(uuid.uuid4()),
            'transaction_id': str(uuid.uuid4()),
            'redeemed_at': '2024-01-20T15:45:00Z'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        # Test gift card redemption
        redeem_data = {
            'code': 'GC-ABCD-1234-EFGH-5678',
            'amount': '25.00',
            'order_id': str(uuid.uuid4())
        }
        
        response = self.client.post(self.endpoints['redeem_gift_card'], data=redeem_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate redemption fields
        assert response.has_field('redemption_amount')
        assert response.has_field('balance_before')
        assert response.has_field('balance_after')
        assert response.has_field('transaction_id')
        assert response.has_field('redeemed_at')
        
        # Validate balance calculation
        balance_before = Decimal(response.get_field_value('balance_before'))
        balance_after = Decimal(response.get_field_value('balance_after'))
        redemption_amount = Decimal(response.get_field_value('redemption_amount'))
        
        assert balance_before - balance_after == redemption_amount
    
    @patch('requests.Session.request')
    def test_redeem_gift_card_insufficient_balance(self, mock_request):
        """Test gift card redemption with insufficient balance"""
        # Mock insufficient balance error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'error': 'Insufficient gift card balance',
            'error_code': 'INSUFFICIENT_GIFT_CARD_BALANCE',
            'available_balance': '25.00',
            'requested_amount': '50.00',
            'shortfall': '25.00'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_customer()
        
        redeem_data = {
            'code': 'GC-ABCD-1234-EFGH-5678',
            'amount': '50.00',  # More than available balance
            'order_id': str(uuid.uuid4())
        }
        
        response = self.client.post(self.endpoints['redeem_gift_card'], data=redeem_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        assert response.get_field_value('error_code') == 'INSUFFICIENT_GIFT_CARD_BALANCE'
        assert response.has_field('available_balance')
        assert response.has_field('shortfall')


if __name__ == '__main__':
    pytest.main([__file__])