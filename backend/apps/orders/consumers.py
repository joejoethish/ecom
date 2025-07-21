import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Order, OrderTracking

User = get_user_model()

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.order_group_name = f'order_tracking_{self.order_id}'
        
        # Verify user has permission to access this order
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        has_permission = await self.check_order_permission(user.id, self.order_id)
        if not has_permission:
            await self.close()
            return
        
        # Join order tracking group
        await self.channel_layer.group_add(
            self.order_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Send initial order status
        order_data = await self.get_order_data(self.order_id)
        if order_data:
            await self.send(text_data=json.dumps({
                'type': 'initial_status',
                'order': order_data
            }))
    
    async def disconnect(self, close_code):
        # Leave order tracking group
        await self.channel_layer.group_discard(
            self.order_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket (not typically used for order tracking)
    async def receive(self, text_data):
        # This consumer primarily sends updates, but could handle specific client requests
        pass
    
    # Send order status update to WebSocket
    async def order_update(self, event):
        status = event['status']
        message = event['message']
        tracking_data = event.get('tracking_data', {})
        
        # Send update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': status,
            'message': message,
            'tracking_data': tracking_data,
            'timestamp': event.get('timestamp')
        }))
    
    @database_sync_to_async
    def check_order_permission(self, user_id, order_id):
        try:
            # Check if user is the order owner or an admin/staff
            order = Order.objects.get(id=order_id)
            user = User.objects.get(id=user_id)
            
            if user.is_staff or user.is_superuser:
                return True
                
            if order.user_id == user_id:
                return True
                
            # Check if user is the seller of any items in this order
            if hasattr(user, 'seller_profile'):
                seller_products = order.items.filter(product__seller=user.seller_profile).exists()
                if seller_products:
                    return True
                    
            return False
        except (Order.DoesNotExist, User.DoesNotExist):
            return False
    
    @database_sync_to_async
    def get_order_data(self, order_id):
        try:
            order = Order.objects.get(id=order_id)
            tracking_events = OrderTracking.objects.filter(order=order).order_by('-created_at')
            
            tracking_data = []
            for event in tracking_events:
                tracking_data.append({
                    'status': event.status,
                    'message': event.message,
                    'location': event.location,
                    'timestamp': event.created_at.isoformat()
                })
            
            return {
                'id': str(order.id),
                'order_number': order.order_number,
                'status': order.status,
                'tracking_number': order.tracking_number,
                'tracking_events': tracking_data
            }
        except Order.DoesNotExist:
            return None