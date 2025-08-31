"""
Product and Order Management API Tests

Comprehensive test suite for product catalog management, order processing,
inventory management, and seller/vendor API endpoints.

This module implements task 6.3 from the QA testing framework specification.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator, ValidationResult
from api.product_order_test_data import ProductTestDataFactory, OrderTestDataFactory
from core.interfaces import Environment, UserRole, Severity
from core.models import TestUser


class TestProductManagementAPI:
    """Test suite for product management API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.product_factory = ProductTestDataFactory(Environment.DEVELOPMENT)
        self.test_products = self.product_factory.generate_test_products()
        self.endpoints = self.product_factory.get_api_endpoints()
        
        # Setup authenticated seller user for product management
        self.client.auth_token = 'seller_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer seller_token_123'
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    # Product CRUD Operations Tests
    
    @patch('requests.Session.request')
    def test_create_product_success(self, mock_request):
        """Test successful product creation"""
        # Mock successful product creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 101,
            'name': 'New Test Product',
            'description': 'A new product for testing',
            'category': 'Electronics',
            'brand': 'TestBrand A',
            'sku': 'NEWSKU001',
            'price': 99.99,
            'stock_quantity': 50,
            'is_active': True,
            'weight': 1.5,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'seller_id': 1
        }
        mock_request.return_value = mock_response
        
        # Test data
        product_data = {
            'name': 'New Test Product',
            'description': 'A new product for testing',
            'category': 'Electronics',
            'brand': 'TestBrand A',
            'sku': 'NEWSKU001',
            'price': 99.99,
            'stock_quantity': 50,
            'is_active': True,
            'weight': 1.5
        }
        
        # Make product creation request
        response = self.client.post(self.endpoints['products'], data=product_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate response content
        validation_result = self.validator.response_validator.validate_success_response(response, 'product')
        assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
        
        # Check required fields
        assert response.has_field('id')
        assert response.has_field('name')
        assert response.has_field('sku')
        assert response.get_field_value('name') == 'New Test Product'
        assert response.get_field_value('price') == 99.99
    
    @patch('requests.Session.request')
    def test_create_product_validation_errors(self, mock_request):
        """Test product creation with validation errors"""
        # Mock validation error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'name': ['This field is required.'],
            'price': ['Price must be greater than 0.'],
            'sku': ['This field is required.']
        }
        mock_request.return_value = mock_response
        
        # Test data with validation errors
        product_data = {
            'description': 'Product without required fields',
            'price': -10.0,  # Invalid price
            'stock_quantity': 10
        }
        
        # Make product creation request
        response = self.client.post(self.endpoints['products'], data=product_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        
        validation_result = self.validator.response_validator.validate_error_response(response)
        assert validation_result.is_valid
        
        # Check error structure
        assert isinstance(response.content, dict)
        assert 'name' in response.content
        assert 'price' in response.content
        assert 'sku' in response.content
    
    @patch('requests.Session.request')
    def test_get_product_list_success(self, mock_request):
        """Test successful product list retrieval"""
        # Mock product list response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 50,
            'next': 'http://localhost:8000/api/v1/products/?page=2',
            'previous': None,
            'results': [
                {
                    'id': i,
                    'name': f'Test Product {i}',
                    'category': 'Electronics',
                    'brand': 'TestBrand A',
                    'sku': f'SKU{i:03d}',
                    'price': 99.99 + i,
                    'stock_quantity': 50 - i,
                    'is_active': True,
                    'rating': 4.5,
                    'review_count': 10
                } for i in range(1, 21)  # 20 products per page
            ]
        }
        mock_request.return_value = mock_response
        
        # Make product list request
        response = self.client.get(self.endpoints['products'])
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate pagination schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'list')
        assert validation_result.is_valid
        
        # Check pagination fields
        assert response.has_field('count')
        assert response.has_field('results')
        assert isinstance(response.get_field_value('results'), list)
        assert len(response.get_field_value('results')) == 20
    
    @patch('requests.Session.request')
    def test_get_product_detail_success(self, mock_request):
        """Test successful product detail retrieval"""
        # Mock product detail response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Test Product 1',
            'description': 'This is a test product for electronics category.',
            'category': 'Electronics',
            'brand': 'TestBrand A',
            'sku': 'SKU001',
            'price': 99.99,
            'sale_price': 79.99,
            'stock_quantity': 50,
            'is_active': True,
            'is_featured': False,
            'weight': 1.5,
            'dimensions': {
                'length': 10.0,
                'width': 8.0,
                'height': 3.0
            },
            'images': [
                'https://testcdn.example.com/products/1/image1.jpg',
                'https://testcdn.example.com/products/1/image2.jpg'
            ],
            'variants': [
                {
                    'id': '1_variant_1',
                    'sku': 'SKU001V1',
                    'color': 'Red',
                    'price': 99.99,
                    'stock_quantity': 25
                }
            ],
            'rating': 4.5,
            'review_count': 15,
            'seller_id': 1,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        product_id = 1
        endpoint = self.endpoints['product_detail'].format(id=product_id)
        response = self.client.get(endpoint)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate product schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'product')
        assert validation_result.is_valid
        
        # Check product details
        assert response.get_field_value('id') == 1
        assert response.has_field('variants')
        assert response.has_field('images')
        assert isinstance(response.get_field_value('variants'), list)
    
    @patch('requests.Session.request')
    def test_update_product_success(self, mock_request):
        """Test successful product update"""
        # Mock product update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Updated Test Product',
            'description': 'Updated description',
            'category': 'Electronics',
            'brand': 'TestBrand A',
            'sku': 'SKU001',
            'price': 129.99,
            'stock_quantity': 75,
            'is_active': True,
            'updated_at': '2024-01-02T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        product_id = 1
        endpoint = self.endpoints['product_detail'].format(id=product_id)
        
        update_data = {
            'name': 'Updated Test Product',
            'description': 'Updated description',
            'price': 129.99,
            'stock_quantity': 75
        }
        
        response = self.client.patch(endpoint, data=update_data)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate CRUD response
        validation_result = self.validator.response_validator.validate_crud_response(response, 'UPDATE')
        assert validation_result.is_valid
        
        assert response.get_field_value('name') == 'Updated Test Product'
        assert response.get_field_value('price') == 129.99
    
    @patch('requests.Session.request')
    def test_delete_product_success(self, mock_request):
        """Test successful product deletion"""
        # Mock product deletion response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ''
        mock_request.return_value = mock_response
        
        product_id = 1
        endpoint = self.endpoints['product_detail'].format(id=product_id)
        
        response = self.client.delete(endpoint)
        
        assert response.is_success
        assert response.status_code == 204
        
        # Validate CRUD response
        validation_result = self.validator.response_validator.validate_crud_response(response, 'DELETE')
        assert validation_result.is_valid
    
    # Product Search and Filtering Tests
    
    @patch('requests.Session.request')
    def test_product_search_by_name(self, mock_request):
        """Test product search by name"""
        # Mock search response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 5,
            'results': [
                {
                    'id': i,
                    'name': f'Test Product {i}',
                    'category': 'Electronics',
                    'price': 99.99 + i,
                    'is_active': True
                } for i in range(1, 6)
            ]
        }
        mock_request.return_value = mock_response
        
        search_params = {'search': 'Test Product'}
        response = self.client.get(self.endpoints['products'], params=search_params)
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        assert len(results) == 5
        
        # Verify search results contain search term
        for result in results:
            assert 'Test Product' in result['name']
    
    @patch('requests.Session.request')
    def test_product_filter_by_category(self, mock_request):
        """Test product filtering by category"""
        # Mock filter response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 10,
            'results': [
                {
                    'id': i,
                    'name': f'Electronics Product {i}',
                    'category': 'Electronics',
                    'price': 99.99 + i,
                    'is_active': True
                } for i in range(1, 11)
            ]
        }
        mock_request.return_value = mock_response
        
        filter_params = {'category': 'Electronics'}
        response = self.client.get(self.endpoints['products'], params=filter_params)
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        
        # Verify all results are in Electronics category
        for result in results:
            assert result['category'] == 'Electronics'
    
    @patch('requests.Session.request')
    def test_product_filter_by_price_range(self, mock_request):
        """Test product filtering by price range"""
        # Mock price filter response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 8,
            'results': [
                {
                    'id': i,
                    'name': f'Product {i}',
                    'category': 'Electronics',
                    'price': 50.0 + (i * 10),
                    'is_active': True
                } for i in range(1, 9)
            ]
        }
        mock_request.return_value = mock_response
        
        filter_params = {'min_price': 50, 'max_price': 150}
        response = self.client.get(self.endpoints['products'], params=filter_params)
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        
        # Verify all results are within price range
        for result in results:
            assert 50 <= result['price'] <= 150


class TestOrderManagementAPI:
    """Test suite for order management API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.order_factory = OrderTestDataFactory(Environment.DEVELOPMENT)
        self.test_orders = self.order_factory.generate_test_orders()
        self.endpoints = self.order_factory.get_api_endpoints()
        
        # Setup authenticated customer user for order management
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    # Order CRUD Operations Tests
    
    @patch('requests.Session.request')
    def test_create_order_success(self, mock_request):
        """Test successful order creation"""
        # Mock successful order creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 101,
            'order_number': 'ORD000101',
            'customer_id': 1,
            'status': 'pending',
            'items': [
                {
                    'id': '101_item_1',
                    'product_id': 1,
                    'product_name': 'Test Product 1',
                    'quantity': 2,
                    'unit_price': 50.0,
                    'total_price': 100.0
                },
                {
                    'id': '101_item_2',
                    'product_id': 2,
                    'product_name': 'Test Product 2',
                    'quantity': 1,
                    'unit_price': 75.0,
                    'total_price': 75.0
                }
            ],
            'subtotal': 175.0,
            'tax_amount': 14.0,
            'shipping_cost': 10.0,
            'total_amount': 199.0,
            'currency': 'USD',
            'payment_method': 'credit_card',
            'payment_status': 'pending',
            'shipping_method': 'standard',
            'created_at': '2024-01-01T00:00:00Z',
            'estimated_delivery': '2024-01-08T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        # Test data
        order_data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,
                    'quantity': 2,
                    'unit_price': 50.0
                },
                {
                    'product_id': 2,
                    'quantity': 1,
                    'unit_price': 75.0
                }
            ],
            'shipping_address': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'payment_method': 'credit_card',
            'shipping_method': 'standard'
        }
        
        # Make order creation request
        response = self.client.post(self.endpoints['orders'], data=order_data)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate response content
        validation_result = self.validator.response_validator.validate_success_response(response, 'order')
        assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
        
        # Check required fields
        assert response.has_field('id')
        assert response.has_field('order_number')
        assert response.has_field('total_amount')
        assert response.get_field_value('status') == 'pending'
        assert response.get_field_value('total_amount') == 199.0
    
    @patch('requests.Session.request')
    def test_create_order_validation_errors(self, mock_request):
        """Test order creation with validation errors"""
        # Mock validation error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'customer_id': ['This field is required.'],
            'items': ['This field cannot be empty.'],
            'shipping_address': ['This field is required.']
        }
        mock_request.return_value = mock_response
        
        # Test data with validation errors
        order_data = {
            'items': [],  # Empty items
            'payment_method': 'credit_card'
        }
        
        # Make order creation request
        response = self.client.post(self.endpoints['orders'], data=order_data)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        
        validation_result = self.validator.response_validator.validate_error_response(response)
        assert validation_result.is_valid
        
        # Check error structure
        assert isinstance(response.content, dict)
        assert 'customer_id' in response.content
        assert 'items' in response.content
    
    @patch('requests.Session.request')
    def test_get_order_list_success(self, mock_request):
        """Test successful order list retrieval"""
        # Mock order list response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 30,
            'next': 'http://localhost:8000/api/v1/orders/?page=2',
            'previous': None,
            'results': [
                {
                    'id': i,
                    'order_number': f'ORD{i:06d}',
                    'customer_id': 1,
                    'status': 'pending',
                    'total_amount': 100.0 + i,
                    'currency': 'USD',
                    'created_at': f'2024-01-{i:02d}T00:00:00Z'
                } for i in range(1, 21)  # 20 orders per page
            ]
        }
        mock_request.return_value = mock_response
        
        # Make order list request
        response = self.client.get(self.endpoints['orders'])
        
        # Validate response
        assert response.is_success
        assert response.status_code == 200
        
        # Validate pagination schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'list')
        assert validation_result.is_valid
        
        # Check pagination fields
        assert response.has_field('count')
        assert response.has_field('results')
        assert isinstance(response.get_field_value('results'), list)
        assert len(response.get_field_value('results')) == 20
    
    @patch('requests.Session.request')
    def test_get_order_detail_success(self, mock_request):
        """Test successful order detail retrieval"""
        # Mock order detail response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'order_number': 'ORD000001',
            'customer_id': 1,
            'status': 'confirmed',
            'items': [
                {
                    'id': '1_item_1',
                    'product_id': 1,
                    'product_name': 'Test Product 1',
                    'sku': 'SKU001',
                    'quantity': 2,
                    'unit_price': 50.0,
                    'total_price': 100.0
                }
            ],
            'subtotal': 100.0,
            'tax_amount': 8.0,
            'shipping_cost': 10.0,
            'discount_amount': 0.0,
            'total_amount': 118.0,
            'currency': 'USD',
            'payment_method': 'credit_card',
            'payment_status': 'paid',
            'shipping_method': 'standard',
            'shipping_address': {
                'street': '123 Test Street',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'billing_address': {
                'street': '456 Billing Ave',
                'city': 'Billing City',
                'state': 'BC',
                'postal_code': '67890',
                'country': 'US'
            },
            'tracking_number': 'TRACK00000001',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'estimated_delivery': '2024-01-08T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        order_id = 1
        endpoint = self.endpoints['order_detail'].format(id=order_id)
        response = self.client.get(endpoint)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate order schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'order')
        assert validation_result.is_valid
        
        # Check order details
        assert response.get_field_value('id') == 1
        assert response.has_field('items')
        assert response.has_field('shipping_address')
        assert isinstance(response.get_field_value('items'), list)
    
    # Order Status Management Tests
    
    @patch('requests.Session.request')
    def test_update_order_status_success(self, mock_request):
        """Test successful order status update"""
        # Mock status update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'order_number': 'ORD000001',
            'status': 'processing',
            'status_history': [
                {
                    'status': 'pending',
                    'timestamp': '2024-01-01T00:00:00Z',
                    'notes': 'Order created'
                },
                {
                    'status': 'confirmed',
                    'timestamp': '2024-01-01T01:00:00Z',
                    'notes': 'Payment confirmed'
                },
                {
                    'status': 'processing',
                    'timestamp': '2024-01-01T02:00:00Z',
                    'notes': 'Order is being processed'
                }
            ],
            'updated_at': '2024-01-01T02:00:00Z'
        }
        mock_request.return_value = mock_response
        
        order_id = 1
        endpoint = self.endpoints['order_status'].format(id=order_id)
        
        status_data = {
            'status': 'processing',
            'notes': 'Order is being processed'
        }
        
        response = self.client.patch(endpoint, data=status_data)
        
        assert response.is_success
        assert response.status_code == 200
        
        assert response.get_field_value('status') == 'processing'
        assert response.has_field('status_history')
    
    @patch('requests.Session.request')
    def test_update_order_status_invalid_transition(self, mock_request):
        """Test order status update with invalid transition"""
        # Mock invalid transition response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'status': ['Invalid status transition from delivered to pending']
        }
        mock_request.return_value = mock_response
        
        order_id = 1
        endpoint = self.endpoints['order_status'].format(id=order_id)
        
        status_data = {
            'status': 'pending'  # Invalid transition from delivered
        }
        
        response = self.client.patch(endpoint, data=status_data)
        
        assert response.is_client_error
        assert response.status_code == 400
        assert 'status' in response.content
    
    # Order Search and Filtering Tests
    
    @patch('requests.Session.request')
    def test_order_filter_by_status(self, mock_request):
        """Test order filtering by status"""
        # Mock filter response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 5,
            'results': [
                {
                    'id': i,
                    'order_number': f'ORD{i:06d}',
                    'customer_id': 1,
                    'status': 'pending',
                    'total_amount': 100.0 + i,
                    'created_at': f'2024-01-{i:02d}T00:00:00Z'
                } for i in range(1, 6)
            ]
        }
        mock_request.return_value = mock_response
        
        filter_params = {'status': 'pending'}
        response = self.client.get(self.endpoints['orders'], params=filter_params)
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        
        # Verify all results have pending status
        for result in results:
            assert result['status'] == 'pending'
    
    @patch('requests.Session.request')
    def test_order_filter_by_customer(self, mock_request):
        """Test order filtering by customer"""
        # Mock customer filter response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 8,
            'results': [
                {
                    'id': i,
                    'order_number': f'ORD{i:06d}',
                    'customer_id': 1,
                    'status': 'confirmed',
                    'total_amount': 100.0 + i,
                    'created_at': f'2024-01-{i:02d}T00:00:00Z'
                } for i in range(1, 9)
            ]
        }
        mock_request.return_value = mock_response
        
        filter_params = {'customer_id': 1}
        response = self.client.get(self.endpoints['orders'], params=filter_params)
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        
        # Verify all results belong to customer 1
        for result in results:
            assert result['customer_id'] == 1


class TestInventoryManagementAPI:
    """Test suite for inventory management API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.product_factory = ProductTestDataFactory(Environment.DEVELOPMENT)
        self.endpoints = self.product_factory.get_api_endpoints()
        
        # Setup authenticated seller user for inventory management
        self.client.auth_token = 'seller_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer seller_token_123'
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_get_inventory_status(self, mock_request):
        """Test inventory status retrieval"""
        # Mock inventory response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'product_id': 1,
            'sku': 'SKU001',
            'current_stock': 45,
            'reserved_stock': 5,
            'available_stock': 40,
            'reorder_level': 10,
            'reorder_quantity': 50,
            'last_updated': '2024-01-01T12:00:00Z',
            'stock_movements': [
                {
                    'id': 1,
                    'type': 'sale',
                    'quantity': -2,
                    'timestamp': '2024-01-01T10:00:00Z',
                    'reference': 'ORD000001'
                },
                {
                    'id': 2,
                    'type': 'restock',
                    'quantity': 50,
                    'timestamp': '2023-12-30T14:00:00Z',
                    'reference': 'PO000001'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        product_id = 1
        endpoint = self.endpoints['inventory_detail'].format(product_id=product_id)
        response = self.client.get(endpoint)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate inventory schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'inventory')
        assert validation_result.is_valid
        
        # Check inventory fields
        assert response.has_field('current_stock')
        assert response.has_field('available_stock')
        assert response.has_field('stock_movements')
        assert response.get_field_value('product_id') == 1
    
    @patch('requests.Session.request')
    def test_update_inventory_stock(self, mock_request):
        """Test inventory stock update"""
        # Mock stock update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'product_id': 1,
            'sku': 'SKU001',
            'current_stock': 95,
            'available_stock': 90,
            'last_updated': '2024-01-01T15:00:00Z',
            'movement_id': 123
        }
        mock_request.return_value = mock_response
        
        product_id = 1
        endpoint = self.endpoints['inventory_detail'].format(product_id=product_id)
        
        stock_data = {
            'quantity': 50,
            'type': 'restock',
            'reference': 'PO000002',
            'notes': 'Weekly restock'
        }
        
        response = self.client.patch(endpoint, data=stock_data)
        
        assert response.is_success
        assert response.status_code == 200
        
        assert response.get_field_value('current_stock') == 95
        assert response.has_field('movement_id')


class TestSellerVendorAPI:
    """Test suite for seller/vendor API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.product_factory = ProductTestDataFactory(Environment.DEVELOPMENT)
        self.order_factory = OrderTestDataFactory(Environment.DEVELOPMENT)
        self.endpoints = self.product_factory.get_api_endpoints()
        
        # Setup authenticated seller user
        self.client.auth_token = 'seller_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer seller_token_123'
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_get_seller_products(self, mock_request):
        """Test seller product list retrieval"""
        # Mock seller products response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 15,
            'results': [
                {
                    'id': i,
                    'name': f'Seller Product {i}',
                    'sku': f'SELLER{i:03d}',
                    'price': 50.0 + i,
                    'stock_quantity': 20 + i,
                    'is_active': True,
                    'sales_count': i * 5,
                    'revenue': (50.0 + i) * (i * 5)
                } for i in range(1, 16)
            ]
        }
        mock_request.return_value = mock_response
        
        response = self.client.get(self.endpoints['seller_products'])
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        assert len(results) == 15
        
        # Verify seller-specific fields
        for result in results:
            assert 'sales_count' in result
            assert 'revenue' in result
    
    @patch('requests.Session.request')
    def test_get_seller_orders(self, mock_request):
        """Test seller order list retrieval"""
        # Mock seller orders response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 12,
            'results': [
                {
                    'id': i,
                    'order_number': f'ORD{i:06d}',
                    'customer_name': f'Customer {i}',
                    'status': 'confirmed',
                    'total_amount': 100.0 + i,
                    'commission_amount': (100.0 + i) * 0.15,
                    'created_at': f'2024-01-{i:02d}T00:00:00Z',
                    'items': [
                        {
                            'product_name': f'Seller Product {i}',
                            'quantity': 1,
                            'unit_price': 100.0 + i
                        }
                    ]
                } for i in range(1, 13)
            ]
        }
        mock_request.return_value = mock_response
        
        response = self.client.get(self.endpoints['seller_orders'])
        
        assert response.is_success
        assert response.status_code == 200
        
        results = response.get_field_value('results')
        assert isinstance(results, list)
        assert len(results) == 12
        
        # Verify seller-specific fields
        for result in results:
            assert 'commission_amount' in result
            assert 'items' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])