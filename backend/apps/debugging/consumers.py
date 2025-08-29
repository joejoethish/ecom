"""
WebSocket consumers for real-time debugging dashboard updates.

This module provides WebSocket consumers that enable real-time communication
between the debugging dashboard frontend and backend, delivering live updates
for system health, workflow traces, errors, and performance metrics.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration
)
from .serializers import (
    WorkflowSessionSerializer, TraceStepSerializer, 
    PerformanceSnapshotSerializer, ErrorLogSerializer,
    WebSocketMessageSerializer
)


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    
    Handles connections from dashboard clients and provides real-time updates
    for system health, workflow traces, errors, and performance metrics.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = "dashboard_updates"
        self.user = None
        self.last_update_time = None
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Check authentication
        self.user = self.scope["user"]
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)  # Unauthorized
            return
        
        # Join dashboard updates group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        await self.send_initial_data()
        
        # Set last update time
        self.last_update_time = timezone.now()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave dashboard updates group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self.handle_subscription(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(data)
            elif message_type == 'request_update':
                await self.handle_update_request(data)
            elif message_type == 'ping':
                await self.send_pong()
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_subscription(self, data: Dict[str, Any]):
        """Handle subscription to specific update types"""
        subscription_types = data.get('subscription_types', [])
        
        # Store subscription preferences (could be stored in database)
        # For now, we'll just acknowledge the subscription
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscription_types': subscription_types,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_unsubscription(self, data: Dict[str, Any]):
        """Handle unsubscription from specific update types"""
        subscription_types = data.get('subscription_types', [])
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscription_types': subscription_types,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_update_request(self, data: Dict[str, Any]):
        """Handle manual update requests"""
        update_type = data.get('update_type', 'all')
        
        if update_type == 'system_health':
            await self.send_system_health_update()
        elif update_type == 'workflows':
            await self.send_workflow_updates()
        elif update_type == 'errors':
            await self.send_error_updates()
        elif update_type == 'performance':
            await self.send_performance_updates()
        else:
            await self.send_all_updates()
    
    async def send_pong(self):
        """Send pong response to ping"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_initial_data(self):
        """Send initial dashboard data to newly connected client"""
        try:
            # Get initial system health
            system_health = await self.get_system_health()
            
            # Get recent workflows
            recent_workflows = await self.get_recent_workflows(limit=5)
            
            # Get recent errors
            recent_errors = await self.get_recent_errors(limit=10)
            
            # Get performance summary
            performance_summary = await self.get_performance_summary()
            
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': {
                    'system_health': system_health,
                    'recent_workflows': recent_workflows,
                    'recent_errors': recent_errors,
                    'performance_summary': performance_summary
                },
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            await self.send_error(f"Failed to send initial data: {str(e)}")
    
    async def send_all_updates(self):
        """Send all types of updates"""
        await self.send_system_health_update()
        await self.send_workflow_updates()
        await self.send_error_updates()
        await self.send_performance_updates()
    
    async def send_system_health_update(self):
        """Send system health update"""
        try:
            system_health = await self.get_system_health()
            
            await self.send(text_data=json.dumps({
                'type': 'system_health_update',
                'data': system_health,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            await self.send_error(f"Failed to send system health update: {str(e)}")
    
    async def send_workflow_updates(self):
        """Send workflow updates"""
        try:
            since = self.last_update_time or (timezone.now() - timedelta(minutes=5))
            new_workflows = await self.get_workflows_since(since)
            
            if new_workflows:
                await self.send(text_data=json.dumps({
                    'type': 'workflow_update',
                    'data': new_workflows,
                    'timestamp': timezone.now().isoformat()
                }))
            
        except Exception as e:
            await self.send_error(f"Failed to send workflow updates: {str(e)}")
    
    async def send_error_updates(self):
        """Send error updates"""
        try:
            since = self.last_update_time or (timezone.now() - timedelta(minutes=5))
            new_errors = await self.get_errors_since(since)
            
            if new_errors:
                await self.send(text_data=json.dumps({
                    'type': 'error_update',
                    'data': new_errors,
                    'timestamp': timezone.now().isoformat()
                }))
            
        except Exception as e:
            await self.send_error(f"Failed to send error updates: {str(e)}")
    
    async def send_performance_updates(self):
        """Send performance metric updates"""
        try:
            since = self.last_update_time or (timezone.now() - timedelta(minutes=5))
            new_metrics = await self.get_metrics_since(since)
            
            if new_metrics:
                await self.send(text_data=json.dumps({
                    'type': 'performance_update',
                    'data': new_metrics,
                    'timestamp': timezone.now().isoformat()
                }))
            
        except Exception as e:
            await self.send_error(f"Failed to send performance updates: {str(e)}")
    
    # Group message handlers
    async def dashboard_update(self, event):
        """Handle dashboard update messages from group"""
        await self.send(text_data=json.dumps({
            'type': event['update_type'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def workflow_created(self, event):
        """Handle new workflow creation"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_created',
            'data': event['workflow_data'],
            'timestamp': event['timestamp']
        }))
    
    async def workflow_completed(self, event):
        """Handle workflow completion"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_completed',
            'data': event['workflow_data'],
            'timestamp': event['timestamp']
        }))
    
    async def workflow_failed(self, event):
        """Handle workflow failure"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_failed',
            'data': event['workflow_data'],
            'timestamp': event['timestamp']
        }))
    
    async def error_logged(self, event):
        """Handle new error logging"""
        await self.send(text_data=json.dumps({
            'type': 'error_logged',
            'data': event['error_data'],
            'timestamp': event['timestamp']
        }))
    
    async def performance_alert(self, event):
        """Handle performance alerts"""
        await self.send(text_data=json.dumps({
            'type': 'performance_alert',
            'data': event['alert_data'],
            'timestamp': event['timestamp']
        }))
    
    # Database query methods (async)
    @database_sync_to_async
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # Active workflows
        active_workflows = WorkflowSession.objects.filter(
            status='in_progress'
        ).count()
        
        # Recent errors
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=last_hour,
            severity__in=['error', 'critical']
        ).count()
        
        # Performance alerts
        performance_alerts = PerformanceSnapshot.objects.filter(
            timestamp__gte=last_hour,
            metric_value__gte=models.F('threshold_warning')
        ).count()
        
        # Overall status
        overall_status = 'healthy'
        if recent_errors > 0 or performance_alerts > 0:
            overall_status = 'degraded'
        if recent_errors > 10 or performance_alerts > 5:
            overall_status = 'critical'
        
        return {
            'overall_status': overall_status,
            'active_workflows': active_workflows,
            'recent_errors': recent_errors,
            'performance_alerts': performance_alerts,
            'timestamp': now.isoformat()
        }
    
    @database_sync_to_async
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflows"""
        workflows = WorkflowSession.objects.select_related('user').order_by('-start_time')[:limit]
        return WorkflowSessionSerializer(workflows, many=True).data
    
    @database_sync_to_async
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent errors"""
        errors = ErrorLog.objects.select_related('user').order_by('-timestamp')[:limit]
        return ErrorLogSerializer(errors, many=True).data
    
    @database_sync_to_async
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        last_hour = timezone.now() - timedelta(hours=1)
        
        metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=last_hour
        ).values('layer', 'metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value'),
            count=models.Count('id')
        )
        
        # Group by layer
        layer_metrics = {}
        for metric in metrics:
            layer = metric['layer']
            if layer not in layer_metrics:
                layer_metrics[layer] = {}
            
            layer_metrics[layer][metric['metric_name']] = {
                'average': round(metric['avg_value'], 2),
                'maximum': round(metric['max_value'], 2),
                'count': metric['count']
            }
        
        return layer_metrics
    
    @database_sync_to_async
    def get_workflows_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get workflows created since timestamp"""
        workflows = WorkflowSession.objects.filter(
            start_time__gte=since
        ).select_related('user').order_by('-start_time')[:10]
        
        return WorkflowSessionSerializer(workflows, many=True).data
    
    @database_sync_to_async
    def get_errors_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get errors logged since timestamp"""
        errors = ErrorLog.objects.filter(
            timestamp__gte=since
        ).select_related('user').order_by('-timestamp')[:20]
        
        return ErrorLogSerializer(errors, many=True).data
    
    @database_sync_to_async
    def get_metrics_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get performance metrics since timestamp"""
        metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=since
        ).order_by('-timestamp')[:50]
        
        return PerformanceSnapshotSerializer(metrics, many=True).data


class WorkflowTraceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time workflow trace updates.
    
    Provides detailed real-time updates for specific workflow traces,
    including trace steps, timing information, and error details.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correlation_id = None
        self.room_group_name = None
        self.user = None
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Check authentication
        self.user = self.scope["user"]
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)  # Unauthorized
            return
        
        # Get correlation ID from URL
        self.correlation_id = self.scope['url_route']['kwargs']['correlation_id']
        self.room_group_name = f"workflow_trace_{self.correlation_id}"
        
        # Join workflow trace group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial workflow data
        await self.send_initial_workflow_data()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave workflow trace group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                await self.send_workflow_update()
            elif message_type == 'ping':
                await self.send_pong()
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def send_pong(self):
        """Send pong response to ping"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_initial_workflow_data(self):
        """Send initial workflow data to newly connected client"""
        try:
            workflow_data = await self.get_workflow_data()
            
            if workflow_data:
                await self.send(text_data=json.dumps({
                    'type': 'initial_workflow_data',
                    'data': workflow_data,
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                await self.send_error(f"Workflow not found: {self.correlation_id}")
                
        except Exception as e:
            await self.send_error(f"Failed to send initial workflow data: {str(e)}")
    
    async def send_workflow_update(self):
        """Send workflow update"""
        try:
            workflow_data = await self.get_workflow_data()
            
            if workflow_data:
                await self.send(text_data=json.dumps({
                    'type': 'workflow_update',
                    'data': workflow_data,
                    'timestamp': timezone.now().isoformat()
                }))
                
        except Exception as e:
            await self.send_error(f"Failed to send workflow update: {str(e)}")
    
    # Group message handlers
    async def trace_step_added(self, event):
        """Handle new trace step"""
        await self.send(text_data=json.dumps({
            'type': 'trace_step_added',
            'data': event['step_data'],
            'timestamp': event['timestamp']
        }))
    
    async def trace_step_completed(self, event):
        """Handle trace step completion"""
        await self.send(text_data=json.dumps({
            'type': 'trace_step_completed',
            'data': event['step_data'],
            'timestamp': event['timestamp']
        }))
    
    async def workflow_error(self, event):
        """Handle workflow error"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_error',
            'data': event['error_data'],
            'timestamp': event['timestamp']
        }))
    
    # Database query methods (async)
    @database_sync_to_async
    def get_workflow_data(self) -> Dict[str, Any]:
        """Get complete workflow data including trace steps"""
        try:
            workflow = WorkflowSession.objects.get(correlation_id=self.correlation_id)
            
            # Get trace steps
            trace_steps = workflow.trace_steps.all().order_by('start_time')
            
            # Get related errors
            errors = ErrorLog.objects.filter(
                correlation_id=self.correlation_id
            ).order_by('timestamp')
            
            # Get performance metrics
            metrics = PerformanceSnapshot.objects.filter(
                correlation_id=self.correlation_id
            ).order_by('timestamp')
            
            return {
                'workflow': WorkflowSessionSerializer(workflow).data,
                'trace_steps': TraceStepSerializer(trace_steps, many=True).data,
                'errors': ErrorLogSerializer(errors, many=True).data,
                'performance_metrics': PerformanceSnapshotSerializer(metrics, many=True).data
            }
            
        except WorkflowSession.DoesNotExist:
            return None