import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class InventoryUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated and has permission
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        # For inventory updates, we might want to restrict to staff/admin or specific roles
        has_permission = await self.check_inventory_permission(user.id)
        if not has_permission:
            await self.close()
            return
        
        # Join inventory updates group
        self.inventory_group_name = 'inventory_updates'
        await self.channel_layer.group_add(
            self.inventory_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave inventory group
        await self.channel_layer.group_discard(
            self.inventory_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket (not typically used for inventory updates)
    async def receive(self, text_data):
        # This consumer primarily sends updates, but could handle specific client requests
        pass
    
    # Send inventory update to WebSocket
    async def inventory_update(self, event):
        update_type = event['update_type']
        product_id = event.get('product_id')
        data = event.get('data', {})
        
        # Send update to WebSocket
        await self.send(text_data=json.dumps({
            'type': update_type,
            'product_id': product_id,
            'data': data,
            'timestamp': event.get('timestamp')
        }))
    
    # Send low stock alert to WebSocket
    async def low_stock_alert(self, event):
        product_id = event.get('product_id')
        product_name = event.get('product_name')
        current_stock = event.get('current_stock')
        threshold = event.get('threshold')
        
        # Send alert to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'low_stock_alert',
            'product_id': product_id,
            'product_name': product_name,
            'current_stock': current_stock,
            'threshold': threshold,
            'timestamp': event.get('timestamp')
        }))
    
    @database_sync_to_async
    def check_inventory_permission(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            # Allow staff, admins, and users with specific permissions
            if user.is_staff or user.is_superuser:
                return True
                
            # Check for specific permission
            if user.has_perm('inventory.view_inventory'):
                return True
                
            # Check if user is a seller (for their own products)
            if hasattr(user, 'seller_profile'):
                return True
                
            return False
        except User.DoesNotExist:
            return False