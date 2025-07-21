import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from ecommerce_project.asgi import application
from apps.inventory.models import Inventory, InventoryTransaction
from apps.products.models import Product, Category

User = get_user_model()

class InventoryUpdateConsumerTest(TransactionTestCase):
    """
    Test case for the InventoryUpdateConsumer WebSocket consumer.
    """
    
    async def test_inventory_update_consumer_connection(self):
        """Test connecting to the inventory update consumer."""
        # Create test admin user
        admin = await database_sync_to_async(User.objects.create_user)(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        
        # Connect to the WebSocket with admin authentication
        communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        
        # Add authentication to the scope
        communicator.scope['user'] = admin
        communicator.scope['user'].is_authenticated = True
        
        connected, _ = await communicator.connect()
        
        # Test connection established
        self.assertTrue(connected)
        
        # Create test product and inventory
        category = await database_sync_to_async(Category.objects.create)(
            name='Test Category'
        )
        
        product = await database_sync_to_async(Product.objects.create)(
            name='Test Product',
            category=category,
            price=99.99,
            sku='TEST001'
        )
        
        inventory = await database_sync_to_async(Inventory.objects.create)(
            product=product,
            quantity=100,
            minimum_stock_level=10,
            reorder_point=20,
            maximum_stock_level=200,
            cost_price=50.00
        )
        
        # Send an inventory update through the channel layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'inventory_updates',
            {
                'type': 'inventory_update',
                'update_type': 'stock_change',
                'product_id': str(product.id),
                'data': {
                    'product_name': product.name,
                    'sku': product.sku,
                    'previous_quantity': 100,
                    'current_quantity': 90,
                    'transaction_type': 'OUT',
                    'reference': 'ORD12345',
                    'notes': 'Order fulfillment'
                },
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Receive the update
        update_response = await communicator.receive_json_from()
        
        # Verify the update
        self.assertEqual(update_response['type'], 'stock_change')
        self.assertEqual(update_response['product_id'], str(product.id))
        self.assertEqual(update_response['data']['product_name'], 'Test Product')
        self.assertEqual(update_response['data']['current_quantity'], 90)
        
        # Send a low stock alert
        await channel_layer.group_send(
            'inventory_updates',
            {
                'type': 'low_stock_alert',
                'product_id': str(product.id),
                'product_name': 'Test Product',
                'current_stock': 5,
                'threshold': 10,
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Receive the alert
        alert_response = await communicator.receive_json_from()
        
        # Verify the alert
        self.assertEqual(alert_response['type'], 'low_stock_alert')
        self.assertEqual(alert_response['product_id'], str(product.id))
        self.assertEqual(alert_response['product_name'], 'Test Product')
        self.assertEqual(alert_response['current_stock'], 5)
        self.assertEqual(alert_response['threshold'], 10)
        
        # Close the connection
        await communicator.disconnect()
    
    async def test_inventory_update_permission_check(self):
        """Test that only authorized users can connect to inventory updates."""
        # Create test users
        admin = await database_sync_to_async(User.objects.create_user)(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        
        regular_user = await database_sync_to_async(User.objects.create_user)(
            username='regular',
            email='regular@example.com',
            password='password123'
        )
        
        # Connect as admin (should succeed)
        admin_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        admin_communicator.scope['user'] = admin
        admin_communicator.scope['user'].is_authenticated = True
        
        admin_connected, _ = await admin_communicator.connect()
        self.assertTrue(admin_connected)
        await admin_communicator.disconnect()
        
        # Connect as regular user (should fail)
        user_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        user_communicator.scope['user'] = regular_user
        user_communicator.scope['user'].is_authenticated = True
        
        user_connected, _ = await user_communicator.connect()
        self.assertFalse(user_connected)
        
        # Connect as unauthenticated user (should fail)
        anon_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        
        anon_connected, _ = await anon_communicator.connect()
        self.assertFalse(anon_connected)