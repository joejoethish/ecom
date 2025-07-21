import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from ecommerce_project.asgi import application
from apps.orders.models import Order, OrderItem, OrderTracking
from apps.products.models import Product, Category

User = get_user_model()

class OrderTrackingConsumerTest(TransactionTestCase):
    """
    Test case for the OrderTrackingConsumer WebSocket consumer.
    """
    
    async def test_order_tracking_consumer_connection(self):
        """Test connecting to the order tracking consumer."""
        # Create test user, product, and order
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        category = await database_sync_to_async(Category.objects.create)(
            name='Test Category'
        )
        
        product = await database_sync_to_async(Product.objects.create)(
            name='Test Product',
            category=category,
            price=99.99,
            sku='TEST001'
        )
        
        order = await database_sync_to_async(Order.objects.create)(
            user=user,
            order_number='ORD12345',
            status='PENDING',
            total_amount=99.99,
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'},
            payment_method='CREDIT_CARD'
        )
        
        order_item = await database_sync_to_async(OrderItem.objects.create)(
            order=order,
            product=product,
            quantity=1,
            unit_price=99.99,
            total_price=99.99
        )
        
        tracking = await database_sync_to_async(OrderTracking.objects.create)(
            order=order,
            status='PENDING',
            description='Order created'
        )
        
        # Connect to the WebSocket with authentication
        communicator = WebsocketCommunicator(
            application,
            f"/ws/orders/tracking/{order.id}/"
        )
        
        # Add authentication to the scope
        communicator.scope['user'] = user
        communicator.scope['user'].is_authenticated = True
        
        connected, _ = await communicator.connect()
        
        # Test connection established
        self.assertTrue(connected)
        
        # Should receive initial order status
        response = await communicator.receive_json_from()
        
        # Verify the response contains order data
        self.assertEqual(response['type'], 'initial_status')
        self.assertEqual(response['order']['order_number'], 'ORD12345')
        self.assertEqual(response['order']['status'], 'PENDING')
        
        # Send an order update through the channel layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'order_tracking_{order.id}',
            {
                'type': 'order_update',
                'status': 'CONFIRMED',
                'message': 'Order has been confirmed',
                'tracking_data': {
                    'status': 'CONFIRMED',
                    'message': 'Order has been confirmed',
                    'timestamp': '2023-01-01T12:00:00Z'
                },
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Receive the update
        update_response = await communicator.receive_json_from()
        
        # Verify the update
        self.assertEqual(update_response['type'], 'status_update')
        self.assertEqual(update_response['status'], 'CONFIRMED')
        self.assertEqual(update_response['message'], 'Order has been confirmed')
        
        # Close the connection
        await communicator.disconnect()
    
    async def test_order_tracking_permission_check(self):
        """Test that only authorized users can connect to order tracking."""
        # Create test users and order
        owner = await database_sync_to_async(User.objects.create_user)(
            username='owner',
            email='owner@example.com',
            password='password123'
        )
        
        other_user = await database_sync_to_async(User.objects.create_user)(
            username='other',
            email='other@example.com',
            password='password123'
        )
        
        category = await database_sync_to_async(Category.objects.create)(
            name='Test Category'
        )
        
        product = await database_sync_to_async(Product.objects.create)(
            name='Test Product',
            category=category,
            price=99.99,
            sku='TEST001'
        )
        
        order = await database_sync_to_async(Order.objects.create)(
            user=owner,
            order_number='ORD12345',
            status='PENDING',
            total_amount=99.99,
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'},
            payment_method='CREDIT_CARD'
        )
        
        # Try connecting as the order owner
        owner_communicator = WebsocketCommunicator(
            application,
            f"/ws/orders/tracking/{order.id}/"
        )
        owner_communicator.scope['user'] = owner
        owner_communicator.scope['user'].is_authenticated = True
        
        owner_connected, _ = await owner_communicator.connect()
        self.assertTrue(owner_connected)
        await owner_communicator.disconnect()
        
        # Try connecting as another user (should fail)
        other_communicator = WebsocketCommunicator(
            application,
            f"/ws/orders/tracking/{order.id}/"
        )
        other_communicator.scope['user'] = other_user
        other_communicator.scope['user'].is_authenticated = True
        
        other_connected, _ = await other_communicator.connect()
        self.assertFalse(other_connected)
        
        # Try connecting as an unauthenticated user (should fail)
        anon_communicator = WebsocketCommunicator(
            application,
            f"/ws/orders/tracking/{order.id}/"
        )
        
        anon_connected, _ = await anon_communicator.connect()
        self.assertFalse(anon_connected)