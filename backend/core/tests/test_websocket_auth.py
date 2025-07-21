import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from ecommerce_project.asgi import application

User = get_user_model()

class WebSocketAuthTest(TransactionTestCase):
    """
    Test case for WebSocket authentication middleware.
    """
    
    async def test_auth_middleware(self):
        """Test that authentication middleware properly handles user authentication."""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test admin
        admin = await database_sync_to_async(User.objects.create_user)(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        
        # Test unauthenticated connection to protected endpoint
        unauthenticated_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        unauthenticated_connected, _ = await unauthenticated_communicator.connect()
        self.assertFalse(unauthenticated_connected)
        
        # Test authenticated connection with insufficient permissions
        user_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        user_communicator.scope['user'] = user
        user_communicator.scope['user'].is_authenticated = True
        user_connected, _ = await user_communicator.connect()
        self.assertFalse(user_connected)
        
        # Test authenticated connection with sufficient permissions
        admin_communicator = WebsocketCommunicator(
            application,
            "/ws/inventory/updates/"
        )
        admin_communicator.scope['user'] = admin
        admin_communicator.scope['user'].is_authenticated = True
        admin_connected, _ = await admin_communicator.connect()
        self.assertTrue(admin_connected)
        await admin_communicator.disconnect()