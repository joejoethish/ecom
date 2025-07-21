import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user_id = text_data_json['user_id']
        
        # Save message to database
        await self.save_message(user_id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'timestamp': text_data_json.get('timestamp', None)
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user_id = event['user_id']
        timestamp = event['timestamp']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,
            'timestamp': timestamp
        }))
    
    @database_sync_to_async
    def save_message(self, user_id, message_text):
        try:
            user = User.objects.get(id=user_id)
            room = ChatRoom.objects.get(id=self.room_id)
            Message.objects.create(
                room=room,
                user=user,
                content=message_text
            )
        except (User.DoesNotExist, ChatRoom.DoesNotExist):
            pass  # Handle error appropriately