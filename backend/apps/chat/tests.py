import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from ecommerce_project.asgi import application
from .models import ChatRoom, Message

User = get_user_model()

class ChatConsumerTest(TransactionTestCase):
    """
    Test case for the ChatConsumer WebSocket consumer.
    """
    
    async def test_chat_consumer_connection(self):
        """Test connecting to the chat consumer."""
        # Create test user and chat room
        user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        room = await database_sync_to_async(ChatRoom.objects.create)(
            name='Test Room',
            room_type='CUSTOMER_SUPPORT'
        )
        await database_sync_to_async(room.participants.add)(user)
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{room.id}/"
        )
        connected, _ = await communicator.connect()
        
        # Test connection established
        self.assertTrue(connected)
        
        # Send a message
        await communicator.send_json_to({
            'message': 'Hello, this is a test message',
            'user_id': str(user.id),
            'timestamp': '2023-01-01T12:00:00Z'
        })
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Verify the response
        self.assertEqual(response['message'], 'Hello, this is a test message')
        self.assertEqual(response['user_id'], str(user.id))
        
        # Close the connection
        await communicator.disconnect()
        
        # Verify message was saved to database
        message_count = await database_sync_to_async(Message.objects.filter(
            room=room,
            user=user,
            content='Hello, this is a test message'
        ).count)()
        
        self.assertEqual(message_count, 1)
    
    async def test_chat_consumer_group_message(self):
        """Test that messages are broadcast to all users in the chat room."""
        # Create test users and chat room
        user1 = await database_sync_to_async(User.objects.create_user)(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        
        user2 = await database_sync_to_async(User.objects.create_user)(
            username='user2',
            email='user2@example.com',
            password='password123'
        )
        
        room = await database_sync_to_async(ChatRoom.objects.create)(
            name='Group Test Room',
            room_type='CUSTOMER_SUPPORT'
        )
        await database_sync_to_async(room.participants.add)(user1, user2)
        
        # Connect two communicators to the same room
        communicator1 = WebsocketCommunicator(
            application,
            f"/ws/chat/{room.id}/"
        )
        connected1, _ = await communicator1.connect()
        self.assertTrue(connected1)
        
        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/chat/{room.id}/"
        )
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)
        
        # Send a message from user1
        await communicator1.send_json_to({
            'message': 'Hello from user1',
            'user_id': str(user1.id),
            'timestamp': '2023-01-01T12:00:00Z'
        })
        
        # Both users should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        # Verify responses
        self.assertEqual(response1['message'], 'Hello from user1')
        self.assertEqual(response1['user_id'], str(user1.id))
        
        self.assertEqual(response2['message'], 'Hello from user1')
        self.assertEqual(response2['user_id'], str(user1.id))
        
        # Close connections
        await communicator1.disconnect()
        await communicator2.disconnect()