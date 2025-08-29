"""
WebSocket signal handlers for real-time debugging dashboard updates.

This module provides signal handlers that send real-time updates to WebSocket
clients when debugging events occur (workflows, errors, performance metrics).
"""

import json
from typing import Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import WorkflowSession, TraceStep, ErrorLog, PerformanceSnapshot
from .serializers import (
    WorkflowSessionSerializer, TraceStepSerializer, 
    ErrorLogSerializer, PerformanceSnapshotSerializer
)


class WebSocketNotifier:
    """Helper class for sending WebSocket notifications"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_to_dashboard_group(self, message_type: str, data: Dict[str, Any]):
        """Send message to dashboard group"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                "dashboard_updates",
                {
                    "type": "dashboard_update",
                    "update_type": message_type,
                    "data": data,
                    "timestamp": timezone.now().isoformat()
                }
            )
    
    def send_to_workflow_group(self, correlation_id: str, message_type: str, data: Dict[str, Any]):
        """Send message to specific workflow group"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f"workflow_trace_{correlation_id}",
                {
                    "type": message_type,
                    "data": data,
                    "timestamp": timezone.now().isoformat()
                }
            )


# Initialize notifier
notifier = WebSocketNotifier()


@receiver(post_save, sender=WorkflowSession)
def workflow_session_saved(sender, instance, created, **kwargs):
    """Handle workflow session creation and updates"""
    try:
        serializer = WorkflowSessionSerializer(instance)
        workflow_data = serializer.data
        
        if created:
            # New workflow created
            notifier.send_to_dashboard_group("workflow_created", {
                "workflow_data": workflow_data
            })
            
            # Send to specific workflow group
            notifier.send_to_workflow_group(
                str(instance.correlation_id),
                "workflow_created",
                {"workflow_data": workflow_data}
            )
        else:
            # Workflow updated
            if instance.status == 'completed':
                notifier.send_to_dashboard_group("workflow_completed", {
                    "workflow_data": workflow_data
                })
                
                notifier.send_to_workflow_group(
                    str(instance.correlation_id),
                    "workflow_completed",
                    {"workflow_data": workflow_data}
                )
            elif instance.status == 'failed':
                notifier.send_to_dashboard_group("workflow_failed", {
                    "workflow_data": workflow_data
                })
                
                notifier.send_to_workflow_group(
                    str(instance.correlation_id),
                    "workflow_failed",
                    {"workflow_data": workflow_data}
                )
    except Exception as e:
        # Log error but don't break the workflow
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending workflow WebSocket update: {str(e)}")


@receiver(post_save, sender=TraceStep)
def trace_step_saved(sender, instance, created, **kwargs):
    """Handle trace step creation and updates"""
    try:
        serializer = TraceStepSerializer(instance)
        step_data = serializer.data
        
        correlation_id = str(instance.workflow_session.correlation_id)
        
        if created:
            # New trace step added
            notifier.send_to_workflow_group(
                correlation_id,
                "trace_step_added",
                {"step_data": step_data}
            )
        else:
            # Trace step updated (likely completed)
            if instance.status == 'completed':
                notifier.send_to_workflow_group(
                    correlation_id,
                    "trace_step_completed",
                    {"step_data": step_data}
                )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending trace step WebSocket update: {str(e)}")


@receiver(post_save, sender=ErrorLog)
def error_log_saved(sender, instance, created, **kwargs):
    """Handle error log creation"""
    if not created:
        return
    
    try:
        serializer = ErrorLogSerializer(instance)
        error_data = serializer.data
        
        # Send to dashboard group
        notifier.send_to_dashboard_group("error_logged", {
            "error_data": error_data
        })
        
        # Send to specific workflow group if correlation_id exists
        if instance.correlation_id:
            notifier.send_to_workflow_group(
                str(instance.correlation_id),
                "workflow_error",
                {"error_data": error_data}
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending error log WebSocket update: {str(e)}")


@receiver(post_save, sender=PerformanceSnapshot)
def performance_snapshot_saved(sender, instance, created, **kwargs):
    """Handle performance snapshot creation"""
    if not created:
        return
    
    try:
        serializer = PerformanceSnapshotSerializer(instance)
        metric_data = serializer.data
        
        # Check if this is a performance alert (exceeds thresholds)
        is_alert = False
        if instance.threshold_warning and instance.metric_value >= instance.threshold_warning:
            is_alert = True
        
        if is_alert:
            # Send performance alert
            notifier.send_to_dashboard_group("performance_alert", {
                "alert_data": metric_data,
                "alert_level": "critical" if (
                    instance.threshold_critical and 
                    instance.metric_value >= instance.threshold_critical
                ) else "warning"
            })
        else:
            # Send regular performance update
            notifier.send_to_dashboard_group("performance_update", {
                "metric_data": metric_data
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending performance WebSocket update: {str(e)}")


def send_custom_dashboard_update(update_type: str, data: Dict[str, Any]):
    """
    Send custom dashboard update.
    
    This function can be called from other parts of the application
    to send custom updates to the dashboard.
    """
    try:
        notifier.send_to_dashboard_group(update_type, data)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending custom dashboard update: {str(e)}")


def send_workflow_update(correlation_id: str, update_type: str, data: Dict[str, Any]):
    """
    Send custom workflow update.
    
    This function can be called from other parts of the application
    to send custom updates to specific workflow traces.
    """
    try:
        notifier.send_to_workflow_group(correlation_id, update_type, data)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending workflow update: {str(e)}")