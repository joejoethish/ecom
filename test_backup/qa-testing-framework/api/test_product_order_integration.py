"""
Product and Order Management Integration Tests

End-to-end integration tests for product catalog and order processing workflows.
Tests complete user journeys and cross-module interactions.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator
from api.product_order_test_data import ProductTestDataFactory, OrderTestDataFactory
from core.interfaces import Environment, UserRole


class TestProductOrderIntegration:
    """Integration tests for complete product and order workflows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.product_factory = ProductTestDataFactory(Environment.DEVELOPMENT)
        self.order_factory = OrderTestDataFactory(Environment.DEVELOPMENT)
        self.endpoints = self.product_factory.get_api_endpoints()
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_complete_product_lifecycle(self, mock_request):
        """Test complete product lifecycle from creation to sale"""
        # Mock responses for product lifecycle
        responses = [
            # Create product
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 201,
                    'name': 'Lifecycle Test Product',
                    'sku': 'LIFECYCLE001',
                    'price': 99.99,
                    'stock_quantity': 100,
                    'is_active': True,
                    'seller_id': 1,
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ),
            # Update product
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 201,
                    'name': 'Updated Lifecycle Product',
                    'sku': 'LIFECYCLE001',
                    'price': 89.99,
                    'stock_quantity': 100,
                    'is_active': True,
                    'updated_at': '2024-01-01T01:00:00Z'
                }
            ),
            # Create order with product
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 301,
                    'order_number': 'ORD000301',
                    'status': 'pending',
                    'items': [
                        {
                            'product_id': 201,
                            'product_name': 'Updated Lifecycle Product',
                            'quantity': 2,
                            'unit_price': 89.99,
                            'total_price': 179.98
                        }
                    ],
                    'total_amount': 199.98,
                    'created_at': '2024-01-01T02:00:00Z'
                }
            ),
            # Check inventory after order
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'product_id': 201,
                    'current_stock': 98,  # Reduced by 2
                    'reserved_stock': 2,
                    'available_stock': 96,
                    'last_updated': '2024-01-01T02:00:00Z'
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Setup seller authentication
        self.client.auth_token = 'seller_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer seller_token_123'
        
        # Step 1: Create product
        product_data = {
            'name': 'Lifecycle Test Product',
            'description': 'Product for lifecycle testing',
            'category': 'Electronics',
            'brand': 'TestBrand',
            'sku': 'LIFECYCLE001',
            'price': 99.99,
            'stock_quantity': 100,
            'is_active': True
        }
        
        create_response = self.client.post(self.endpoints['products'], data=product_data)
        
        assert create_response.is_success
        assert create_response.status_code == 201
        
        product_id = create_response.get_field_value('id')
        
        # Step 2: Update product price
        update_data = {
            'name': 'Updated Lifecycle Product',
            'price': 89.99
        }
        
        product_endpoint = self.endpoints['product_detail'].format(id=product_id)
        update_response = self.client.patch(product_endpoint, data=update_data)
        
        assert update_response.is_success
        assert update_response.status_code == 200
        assert update_response.get_field_value('price') == 89.99
        
        # Step 3: Switch to customer and create order
        self.client.auth_token = 'customer_token_123'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
        
        order_data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': product_id,
                    'quantity': 2,
                    'unit_price': 89.99
                }
            ],
            'shipping_address': {
                'street': '123 Test St',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'payment_method': 'credit_card'
        }
        
        order_response = self.client.post(self.endpoints['orders'], data=order_data)
        
        assert order_response.is_success
        assert order_response.status_code == 201
        
        # Step 4: Check inventory impact
        inventory_endpoint = self.endpoints['inventory_detail'].format(product_id=product_id)
        inventory_response = self.client.get(inventory_endpoint, authenticate=False)
        
        assert inventory_response.is_success
        assert inventory_response.get_field_value('current_stock') == 98
        
        # Validate complete workflow
        assert len(self.client.request_history) == 4
        
        for response in self.client.request_history:
            validation_result = self.validator.validate_full_response(response)
            assert validation_result.is_valid or len(validation_result.errors) == 0
    
    @patch('requests.Session.request')
    def test_order_fulfillment_workflow(self, mock_request):
        """Test complete order fulfillment workflow"""
        # Mock responses for order fulfillment
        responses = [
            # Create order
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 401,
                    'order_number': 'ORD000401',
                    'status': 'pending',
                    'payment_status': 'pending',
                    'total_amount': 149.99,
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ),
            # Confirm order
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 401,
                    'status': 'confirmed',
                    'payment_status': 'paid',
                    'updated_at': '2024-01-01T01:00:00Z'
                }
            ),
            # Process order
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 401,
                    'status': 'processing',
                    'updated_at': '2024-01-01T02:00:00Z'
                }
            ),
            # Ship order
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 401,
                    'status': 'shipped',
                    'tracking_number': 'TRACK00000401',
                    'updated_at': '2024-01-01T03:00:00Z'
                }
            ),
            # Deliver order
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 401,
                    'status': 'delivered',
                    'delivered_at': '2024-01-05T10:00:00Z',
                    'updated_at': '2024-01-05T10:00:00Z'
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Setup customer authentication
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
        
        # Step 1: Create order
        order_data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,
                    'quantity': 1,
                    'unit_price': 149.99
                }
            ],
            'shipping_address': {
                'street': '123 Fulfillment St',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'payment_method': 'credit_card'
        }
        
        create_response = self.client.post(self.endpoints['orders'], data=order_data)
        
        assert create_response.is_success
        assert create_response.status_code == 201
        
        order_id = create_response.get_field_value('id')
        status_endpoint = self.endpoints['order_status'].format(id=order_id)
        
        # Step 2: Confirm order (payment processed)
        confirm_data = {'status': 'confirmed'}
        confirm_response = self.client.patch(status_endpoint, data=confirm_data)
        
        assert confirm_response.is_success
        assert confirm_response.get_field_value('status') == 'confirmed'
        
        # Step 3: Process order
        process_data = {'status': 'processing'}
        process_response = self.client.patch(status_endpoint, data=process_data)
        
        assert process_response.is_success
        assert process_response.get_field_value('status') == 'processing'
        
        # Step 4: Ship order
        ship_data = {'status': 'shipped'}
        ship_response = self.client.patch(status_endpoint, data=ship_data)
        
        assert ship_response.is_success
        assert ship_response.get_field_value('status') == 'shipped'
        assert ship_response.has_field('tracking_number')
        
        # Step 5: Deliver order
        deliver_data = {'status': 'delivered'}
        deliver_response = self.client.patch(status_endpoint, data=deliver_data)
        
        assert deliver_response.is_success
        assert deliver_response.get_field_value('status') == 'delivered'
        
        # Validate complete fulfillment workflow
        assert len(self.client.request_history) == 5
        
        # Check status progression
        statuses = [
            'pending', 'confirmed', 'processing', 'shipped', 'delivered'
        ]
        
        for i, response in enumerate(self.client.request_history):
            if i > 0:  # Skip creation response
                expected_status = statuses[i]
                if response.has_field('status'):
                    assert response.get_field_value('status') == expected_status
    
    @patch('requests.Session.request')
    def test_multi_vendor_order_processing(self, mock_request):
        """Test order processing with products from multiple vendors"""
        # Mock responses for multi-vendor order
        responses = [
            # Create order with items from different sellers
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 501,
                    'order_number': 'ORD000501',
                    'status': 'pending',
                    'items': [
                        {
                            'id': '501_item_1',
                            'product_id': 1,
                            'seller_id': 1,
                            'product_name': 'Seller 1 Product',
                            'quantity': 1,
                            'unit_price': 50.0,
                            'total_price': 50.0
                        },
                        {
                            'id': '501_item_2',
                            'product_id': 2,
                            'seller_id': 2,
                            'product_name': 'Seller 2 Product',
                            'quantity': 2,
                            'unit_price': 75.0,
                            'total_price': 150.0
                        }
                    ],
                    'total_amount': 220.0,  # Including tax and shipping
                    'seller_orders': [
                        {
                            'seller_id': 1,
                            'items_count': 1,
                            'subtotal': 50.0,
                            'status': 'pending'
                        },
                        {
                            'seller_id': 2,
                            'items_count': 1,
                            'subtotal': 150.0,
                            'status': 'pending'
                        }
                    ],
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ),
            # Get seller 1 orders
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'count': 1,
                    'results': [
                        {
                            'id': 501,
                            'order_number': 'ORD000501',
                            'customer_name': 'Test Customer',
                            'status': 'confirmed',
                            'items': [
                                {
                                    'product_name': 'Seller 1 Product',
                                    'quantity': 1,
                                    'unit_price': 50.0
                                }
                            ],
                            'commission_amount': 7.50,  # 15% commission
                            'created_at': '2024-01-01T00:00:00Z'
                        }
                    ]
                }
            ),
            # Get seller 2 orders
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'count': 1,
                    'results': [
                        {
                            'id': 501,
                            'order_number': 'ORD000501',
                            'customer_name': 'Test Customer',
                            'status': 'confirmed',
                            'items': [
                                {
                                    'product_name': 'Seller 2 Product',
                                    'quantity': 2,
                                    'unit_price': 75.0
                                }
                            ],
                            'commission_amount': 22.50,  # 15% commission
                            'created_at': '2024-01-01T00:00:00Z'
                        }
                    ]
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Setup customer authentication
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
        
        # Step 1: Create multi-vendor order
        order_data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,  # Seller 1 product
                    'quantity': 1,
                    'unit_price': 50.0
                },
                {
                    'product_id': 2,  # Seller 2 product
                    'quantity': 2,
                    'unit_price': 75.0
                }
            ],
            'shipping_address': {
                'street': '123 Multi Vendor St',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'payment_method': 'credit_card'
        }
        
        create_response = self.client.post(self.endpoints['orders'], data=order_data)
        
        assert create_response.is_success
        assert create_response.status_code == 201
        
        # Validate multi-vendor order structure
        assert create_response.has_field('seller_orders')
        seller_orders = create_response.get_field_value('seller_orders')
        assert len(seller_orders) == 2
        
        # Step 2: Check seller 1 orders
        self.client.auth_token = 'seller1_token_123'
        self.client.session.headers['Authorization'] = 'Bearer seller1_token_123'
        
        seller1_response = self.client.get(self.endpoints['seller_orders'])
        
        assert seller1_response.is_success
        results = seller1_response.get_field_value('results')
        assert len(results) == 1
        assert results[0]['commission_amount'] == 7.50
        
        # Step 3: Check seller 2 orders
        self.client.auth_token = 'seller2_token_123'
        self.client.session.headers['Authorization'] = 'Bearer seller2_token_123'
        
        seller2_response = self.client.get(self.endpoints['seller_orders'])
        
        assert seller2_response.is_success
        results = seller2_response.get_field_value('results')
        assert len(results) == 1
        assert results[0]['commission_amount'] == 22.50
    
    @patch('requests.Session.request')
    def test_inventory_management_integration(self, mock_request):
        """Test inventory management across product and order operations"""
        # Mock responses for inventory management
        responses = [
            # Initial inventory check
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'product_id': 1,
                    'current_stock': 100,
                    'reserved_stock': 0,
                    'available_stock': 100,
                    'reorder_level': 10
                }
            ),
            # Create order (reserves stock)
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 601,
                    'order_number': 'ORD000601',
                    'status': 'pending',
                    'items': [
                        {
                            'product_id': 1,
                            'quantity': 5,
                            'unit_price': 50.0
                        }
                    ],
                    'total_amount': 275.0
                }
            ),
            # Inventory after order creation
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'product_id': 1,
                    'current_stock': 100,
                    'reserved_stock': 5,
                    'available_stock': 95,
                    'reorder_level': 10,
                    'stock_movements': [
                        {
                            'type': 'reservation',
                            'quantity': -5,
                            'reference': 'ORD000601',
                            'timestamp': '2024-01-01T00:00:00Z'
                        }
                    ]
                }
            ),
            # Confirm order (commits stock)
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 601,
                    'status': 'confirmed',
                    'updated_at': '2024-01-01T01:00:00Z'
                }
            ),
            # Final inventory after confirmation
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'product_id': 1,
                    'current_stock': 95,
                    'reserved_stock': 0,
                    'available_stock': 95,
                    'reorder_level': 10,
                    'stock_movements': [
                        {
                            'type': 'sale',
                            'quantity': -5,
                            'reference': 'ORD000601',
                            'timestamp': '2024-01-01T01:00:00Z'
                        }
                    ]
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Setup authentication
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
        
        # Step 1: Check initial inventory
        inventory_endpoint = self.endpoints['inventory_detail'].format(product_id=1)
        initial_inventory = self.client.get(inventory_endpoint, authenticate=False)
        
        assert initial_inventory.is_success
        assert initial_inventory.get_field_value('available_stock') == 100
        
        # Step 2: Create order (should reserve stock)
        order_data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,
                    'quantity': 5,
                    'unit_price': 50.0
                }
            ],
            'shipping_address': {
                'street': '123 Inventory St',
                'city': 'Test City',
                'state': 'TS',
                'postal_code': '12345',
                'country': 'US'
            },
            'payment_method': 'credit_card'
        }
        
        order_response = self.client.post(self.endpoints['orders'], data=order_data)
        
        assert order_response.is_success
        order_id = order_response.get_field_value('id')
        
        # Step 3: Check inventory after order (stock should be reserved)
        reserved_inventory = self.client.get(inventory_endpoint, authenticate=False)
        
        assert reserved_inventory.is_success
        assert reserved_inventory.get_field_value('reserved_stock') == 5
        assert reserved_inventory.get_field_value('available_stock') == 95
        
        # Step 4: Confirm order (should commit stock)
        status_endpoint = self.endpoints['order_status'].format(id=order_id)
        confirm_data = {'status': 'confirmed'}
        confirm_response = self.client.patch(status_endpoint, data=confirm_data)
        
        assert confirm_response.is_success
        
        # Step 5: Check final inventory (stock should be committed)
        final_inventory = self.client.get(inventory_endpoint, authenticate=False)
        
        assert final_inventory.is_success
        assert final_inventory.get_field_value('current_stock') == 95
        assert final_inventory.get_field_value('reserved_stock') == 0
        assert final_inventory.get_field_value('available_stock') == 95
        
        # Validate inventory tracking
        stock_movements = final_inventory.get_field_value('stock_movements')
        assert isinstance(stock_movements, list)
        assert len(stock_movements) > 0
        assert stock_movements[0]['type'] == 'sale'
        assert stock_movements[0]['quantity'] == -5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])