import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.notification_group_name = f'notifications_{self.user_id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket (not typically used for notifications)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'notification')
        
        if message_type == 'mark_read':
            notification_id = text_data_json.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
    
    # Send notification to WebSocket
    async def notification_message(self, event):
        notification_type = event['notification_type']
        message = event['message']
        data = event.get('data', {})
        
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': notification_type,
            'message': message,
            'data': data,
            'timestamp': event.get('timestamp')
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, user_id=self.user_id)
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False