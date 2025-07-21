import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from ecommerce_project.asgi import application
from apps.notifications.models import Notification

User = get_user_model()

class NotificationConsumerTest(TransactionTestCase):
    """
    Test case for the NotificationConsumer WebSocket consumer.
    """
    
    async def test_notification_consumer_connection(self):
        """Test connecting to the notification consumer."""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a notification for the user
        notification = await database_sync_to_async(Notification.objects.create)(
            user=user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='TEST',
            reference_id='123'
        )
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/{user.id}/"
        )
        
        # Add authentication to the scope
        communicator.scope['user'] = user
        communicator.scope['user'].is_authenticated = True
        
        connected, _ = await communicator.connect()
        
        # Test connection established
        self.assertTrue(connected)
        
        # Send a notification through the channel layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'notifications_{user.id}',
            {
                'type': 'notification_message',
                'notification_type': 'ORDER_UPDATE',
                'message': 'Your order has been shipped',
                'data': {
                    'order_id': '12345',
                    'order_number': 'ORD12345',
                    'status': 'SHIPPED'
                },
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Receive the notification
        response = await communicator.receive_json_from()
        
        # Verify the notification
        self.assertEqual(response['type'], 'ORDER_UPDATE')
        self.assertEqual(response['message'], 'Your order has been shipped')
        self.assertEqual(response['data']['order_number'], 'ORD12345')
        
        # Send a mark_read message
        await communicator.send_json_to({
            'type': 'mark_read',
            'notification_id': str(notification.id)
        })
        
        # Close the connection
        await communicator.disconnect()
        
        # Verify notification was marked as read
        updated_notification = await database_sync_to_async(Notification.objects.get)(id=notification.id)
        self.assertTrue(await database_sync_to_async(getattr)(updated_notification, 'is_read'))
    
    async def test_multiple_notifications(self):
        """Test receiving multiple notifications."""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/{user.id}/"
        )
        
        # Add authentication to the scope
        communicator.scope['user'] = user
        communicator.scope['user'].is_authenticated = True
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send multiple notifications through the channel layer
        channel_layer = get_channel_layer()
        
        # First notification
        await channel_layer.group_send(
            f'notifications_{user.id}',
            {
                'type': 'notification_message',
                'notification_type': 'ORDER_UPDATE',
                'message': 'Your order has been shipped',
                'data': {'order_number': 'ORD12345'},
                'timestamp': '2023-01-01T12:00:00Z'
            }
        )
        
        # Second notification
        await channel_layer.group_send(
            f'notifications_{user.id}',
            {
                'type': 'notification_message',
                'notification_type': 'PAYMENT_CONFIRMATION',
                'message': 'Payment received',
                'data': {'amount': 99.99},
                'timestamp': '2023-01-01T12:05:00Z'
            }
        )
        
        # Receive the first notification
        response1 = await communicator.receive_json_from()
        self.assertEqual(response1['type'], 'ORDER_UPDATE')
        
        # Receive the second notification
        response2 = await communicator.receive_json_from()
        self.assertEqual(response2['type'], 'PAYMENT_CONFIRMATION')
        
        # Close the connection
        await communicator.disconnect()