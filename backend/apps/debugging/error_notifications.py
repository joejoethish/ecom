"""
Error Notification and Alerting System

This module provides notification handlers for error escalation,
including email, webhook, and dashboard notifications.
"""

import json
import logging
import smtplib
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.cache import cache
import requests

from .models import ErrorLog, DebugConfiguration
from .error_handling import ErrorContext, ErrorClassification

logger = logging.getLogger(__name__)


class NotificationThrottler:
    """Throttles notifications to prevent spam"""
    
    def __init__(self, default_window_minutes: int = 15, default_max_notifications: int = 5):
        self.default_window_minutes = default_window_minutes
        self.default_max_notifications = default_max_notifications
    
    def should_send_notification(self, notification_key: str, 
                               window_minutes: Optional[int] = None,
                               max_notifications: Optional[int] = None) -> bool:
        """Check if notification should be sent based on throttling rules"""
        window_minutes = window_minutes or self.default_window_minutes
        max_notifications = max_notifications or self.default_max_notifications
        
        cache_key = f"notification_throttle:{notification_key}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= max_notifications:
            logger.debug(f"Notification throttled for {notification_key}: {current_count}/{max_notifications}")
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window_minutes * 60)
        return True
    
    def reset_throttle(self, notification_key: str):
        """Reset throttle counter for a notification key"""
        cache_key = f"notification_throttle:{notification_key}"
        cache.delete(cache_key)


class EmailNotificationHandler:
    """Handles email notifications for error escalation"""
    
    def __init__(self):
        self.throttler = NotificationThrottler()
    
    def send_error_notification(self, escalation_data: Dict[str, Any]):
        """Send email notification for error escalation"""
        error_log = escalation_data['error_log']
        classification = escalation_data['classification']
        escalation_level = escalation_data['escalation_level']
        
        # Create notification key for throttling
        notification_key = f"email:{error_log.layer}:{error_log.component}:{error_log.error_type}"
        
        # Check throttling
        if not self.throttler.should_send_notification(notification_key):
            return
        
        # Get email configuration
        email_config = self._get_email_config(escalation_level)
        if not email_config or not email_config.get('enabled', False):
            return
        
        recipients = email_config.get('recipients', [])
        if not recipients:
            logger.warning("No email recipients configured for error notifications")
            return
        
        # Prepare email content
        subject = self._generate_subject(error_log, escalation_level)
        html_content = self._generate_html_content(escalation_data)
        text_content = self._generate_text_content(escalation_data)
        
        try:
            # Send email using Django's email system
            from django.core.mail import EmailMultiAlternatives
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Error notification email sent to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send error notification email: {e}")
    
    def _get_email_config(self, escalation_level: str) -> Optional[Dict[str, Any]]:
        """Get email configuration for escalation level"""
        try:
            config = DebugConfiguration.objects.get(
                name=f"email_notifications_{escalation_level}",
                enabled=True
            )
            return config.config_data
        except DebugConfiguration.DoesNotExist:
            # Try default configuration
            try:
                config = DebugConfiguration.objects.get(
                    name="email_notifications_default",
                    enabled=True
                )
                return config.config_data
            except DebugConfiguration.DoesNotExist:
                return None
    
    def _generate_subject(self, error_log: ErrorLog, escalation_level: str) -> str:
        """Generate email subject"""
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️'
        }
        
        emoji = severity_emoji.get(escalation_level, '❗')
        
        return (
            f"{emoji} [{escalation_level.upper()}] Error in {error_log.layer}.{error_log.component}: "
            f"{error_log.error_type}"
        )
    
    def _generate_html_content(self, escalation_data: Dict[str, Any]) -> str:
        """Generate HTML email content"""
        try:
            return render_to_string('debugging/error_notification_email.html', {
                'escalation_data': escalation_data,
                'error_log': escalation_data['error_log'],
                'classification': escalation_data['classification'],
                'escalation_level': escalation_data['escalation_level'],
                'timestamp': escalation_data['timestamp']
            })
        except Exception as e:
            logger.error(f"Failed to render HTML email template: {e}")
            return self._generate_text_content(escalation_data)
    
    def _generate_text_content(self, escalation_data: Dict[str, Any]) -> str:
        """Generate plain text email content"""
        error_log = escalation_data['error_log']
        classification = escalation_data['classification']
        escalation_level = escalation_data['escalation_level']
        timestamp = escalation_data['timestamp']
        
        content = f"""
ERROR ESCALATION NOTIFICATION

Escalation Level: {escalation_level.upper()}
Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

ERROR DETAILS:
- Layer: {error_log.layer}
- Component: {error_log.component}
- Error Type: {error_log.error_type}
- Severity: {error_log.severity}
- Message: {error_log.error_message}

CLASSIFICATION:
- Category: {classification.category.value if hasattr(classification, 'category') else 'Unknown'}
- Recoverable: {classification.is_recoverable if hasattr(classification, 'is_recoverable') else 'Unknown'}
- Recovery Strategy: {classification.recovery_strategy.value if hasattr(classification, 'recovery_strategy') else 'Unknown'}

CONTEXT:
- Correlation ID: {error_log.correlation_id or 'None'}
- User: {error_log.user.username if error_log.user else 'Anonymous'}
- Request Path: {error_log.request_path or 'N/A'}
- Request Method: {error_log.request_method or 'N/A'}
- IP Address: {error_log.ip_address or 'N/A'}

STACK TRACE:
{error_log.stack_trace or 'No stack trace available'}

---
This is an automated notification from the E2E Workflow Debugging System.
"""
        return content.strip()


class WebhookNotificationHandler:
    """Handles webhook notifications for error escalation"""
    
    def __init__(self):
        self.throttler = NotificationThrottler()
    
    def send_webhook_notification(self, escalation_data: Dict[str, Any]):
        """Send webhook notification for error escalation"""
        error_log = escalation_data['error_log']
        escalation_level = escalation_data['escalation_level']
        
        # Create notification key for throttling
        notification_key = f"webhook:{error_log.layer}:{error_log.component}:{error_log.error_type}"
        
        # Check throttling
        if not self.throttler.should_send_notification(notification_key):
            return
        
        # Get webhook configuration
        webhook_config = self._get_webhook_config(escalation_level)
        if not webhook_config or not webhook_config.get('enabled', False):
            return
        
        webhooks = webhook_config.get('webhooks', [])
        if not webhooks:
            logger.warning("No webhooks configured for error notifications")
            return
        
        # Prepare webhook payload
        payload = self._generate_webhook_payload(escalation_data)
        
        # Send to all configured webhooks
        for webhook in webhooks:
            self._send_to_webhook(webhook, payload)
    
    def _get_webhook_config(self, escalation_level: str) -> Optional[Dict[str, Any]]:
        """Get webhook configuration for escalation level"""
        try:
            config = DebugConfiguration.objects.get(
                name=f"webhook_notifications_{escalation_level}",
                enabled=True
            )
            return config.config_data
        except DebugConfiguration.DoesNotExist:
            # Try default configuration
            try:
                config = DebugConfiguration.objects.get(
                    name="webhook_notifications_default",
                    enabled=True
                )
                return config.config_data
            except DebugConfiguration.DoesNotExist:
                return None
    
    def _generate_webhook_payload(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate webhook payload"""
        error_log = escalation_data['error_log']
        classification = escalation_data['classification']
        escalation_level = escalation_data['escalation_level']
        timestamp = escalation_data['timestamp']
        
        return {
            'event_type': 'error_escalation',
            'escalation_level': escalation_level,
            'timestamp': timestamp.isoformat(),
            'error': {
                'id': error_log.id,
                'correlation_id': str(error_log.correlation_id) if error_log.correlation_id else None,
                'layer': error_log.layer,
                'component': error_log.component,
                'error_type': error_log.error_type,
                'error_message': error_log.error_message,
                'severity': error_log.severity,
                'timestamp': error_log.timestamp.isoformat(),
                'user': error_log.user.username if error_log.user else None,
                'request_path': error_log.request_path,
                'request_method': error_log.request_method,
                'ip_address': error_log.ip_address,
                'resolved': error_log.resolved,
                'metadata': error_log.metadata
            },
            'classification': {
                'category': classification.category.value if hasattr(classification, 'category') else None,
                'severity': classification.severity.value if hasattr(classification, 'severity') else None,
                'is_recoverable': classification.is_recoverable if hasattr(classification, 'is_recoverable') else None,
                'recovery_strategy': classification.recovery_strategy.value if hasattr(classification, 'recovery_strategy') else None
            },
            'system_info': {
                'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                'service': 'e2e-workflow-debugging'
            }
        }
    
    def _send_to_webhook(self, webhook_config: Dict[str, Any], payload: Dict[str, Any]):
        """Send payload to a specific webhook"""
        url = webhook_config.get('url')
        if not url:
            logger.error("Webhook URL not configured")
            return
        
        headers = webhook_config.get('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        
        timeout = webhook_config.get('timeout', 30)
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent successfully to {url}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook notification to {url}: {e}")


class SlackNotificationHandler:
    """Handles Slack notifications for error escalation"""
    
    def __init__(self):
        self.throttler = NotificationThrottler()
    
    def send_slack_notification(self, escalation_data: Dict[str, Any]):
        """Send Slack notification for error escalation"""
        error_log = escalation_data['error_log']
        escalation_level = escalation_data['escalation_level']
        
        # Create notification key for throttling
        notification_key = f"slack:{error_log.layer}:{error_log.component}:{error_log.error_type}"
        
        # Check throttling
        if not self.throttler.should_send_notification(notification_key):
            return
        
        # Get Slack configuration
        slack_config = self._get_slack_config(escalation_level)
        if not slack_config or not slack_config.get('enabled', False):
            return
        
        webhook_url = slack_config.get('webhook_url')
        if not webhook_url:
            logger.warning("No Slack webhook URL configured")
            return
        
        # Prepare Slack message
        message = self._generate_slack_message(escalation_data)
        
        try:
            response = requests.post(
                webhook_url,
                json=message,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info("Slack notification sent successfully")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def _get_slack_config(self, escalation_level: str) -> Optional[Dict[str, Any]]:
        """Get Slack configuration for escalation level"""
        try:
            config = DebugConfiguration.objects.get(
                name=f"slack_notifications_{escalation_level}",
                enabled=True
            )
            return config.config_data
        except DebugConfiguration.DoesNotExist:
            # Try default configuration
            try:
                config = DebugConfiguration.objects.get(
                    name="slack_notifications_default",
                    enabled=True
                )
                return config.config_data
            except DebugConfiguration.DoesNotExist:
                return None
    
    def _generate_slack_message(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Slack message payload"""
        error_log = escalation_data['error_log']
        escalation_level = escalation_data['escalation_level']
        timestamp = escalation_data['timestamp']
        
        # Color based on escalation level
        color_map = {
            'critical': '#FF0000',  # Red
            'high': '#FF8C00',      # Orange
            'medium': '#FFD700',    # Gold
            'low': '#32CD32'        # Green
        }
        color = color_map.get(escalation_level, '#808080')
        
        # Emoji based on escalation level
        emoji_map = {
            'critical': ':rotating_light:',
            'high': ':warning:',
            'medium': ':zap:',
            'low': ':information_source:'
        }
        emoji = emoji_map.get(escalation_level, ':exclamation:')
        
        return {
            'text': f"{emoji} Error Escalation - {escalation_level.upper()}",
            'attachments': [
                {
                    'color': color,
                    'title': f"Error in {error_log.layer}.{error_log.component}",
                    'title_link': f"/admin/debugging/errorlog/{error_log.id}/change/",
                    'fields': [
                        {
                            'title': 'Error Type',
                            'value': error_log.error_type,
                            'short': True
                        },
                        {
                            'title': 'Severity',
                            'value': error_log.severity.upper(),
                            'short': True
                        },
                        {
                            'title': 'Layer',
                            'value': error_log.layer,
                            'short': True
                        },
                        {
                            'title': 'Component',
                            'value': error_log.component,
                            'short': True
                        },
                        {
                            'title': 'Message',
                            'value': error_log.error_message[:200] + ('...' if len(error_log.error_message) > 200 else ''),
                            'short': False
                        },
                        {
                            'title': 'Correlation ID',
                            'value': str(error_log.correlation_id) if error_log.correlation_id else 'None',
                            'short': True
                        },
                        {
                            'title': 'User',
                            'value': error_log.user.username if error_log.user else 'Anonymous',
                            'short': True
                        }
                    ],
                    'footer': 'E2E Workflow Debugging System',
                    'ts': int(timestamp.timestamp())
                }
            ]
        }


class DashboardNotificationHandler:
    """Handles real-time dashboard notifications"""
    
    def __init__(self):
        self.throttler = NotificationThrottler(default_window_minutes=5, default_max_notifications=10)
    
    def send_dashboard_notification(self, escalation_data: Dict[str, Any]):
        """Send real-time notification to dashboard"""
        error_log = escalation_data['error_log']
        escalation_level = escalation_data['escalation_level']
        
        # Create notification key for throttling
        notification_key = f"dashboard:{error_log.layer}:{error_log.component}"
        
        # Check throttling (more lenient for dashboard)
        if not self.throttler.should_send_notification(notification_key, window_minutes=2, max_notifications=20):
            return
        
        # Prepare dashboard notification
        notification = self._generate_dashboard_notification(escalation_data)
        
        # Send via WebSocket (if available)
        self._send_websocket_notification(notification)
        
        # Store in cache for dashboard polling
        self._store_notification_in_cache(notification)
    
    def _generate_dashboard_notification(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard notification payload"""
        error_log = escalation_data['error_log']
        escalation_level = escalation_data['escalation_level']
        timestamp = escalation_data['timestamp']
        
        return {
            'id': f"error_{error_log.id}_{int(timestamp.timestamp())}",
            'type': 'error_escalation',
            'escalation_level': escalation_level,
            'timestamp': timestamp.isoformat(),
            'title': f"Error in {error_log.layer}.{error_log.component}",
            'message': error_log.error_message[:100] + ('...' if len(error_log.error_message) > 100 else ''),
            'data': {
                'error_id': error_log.id,
                'layer': error_log.layer,
                'component': error_log.component,
                'error_type': error_log.error_type,
                'severity': error_log.severity,
                'correlation_id': str(error_log.correlation_id) if error_log.correlation_id else None,
                'user': error_log.user.username if error_log.user else None
            },
            'actions': [
                {
                    'label': 'View Details',
                    'url': f"/admin/debugging/errorlog/{error_log.id}/change/"
                },
                {
                    'label': 'Mark Resolved',
                    'action': 'resolve_error',
                    'error_id': error_log.id
                }
            ]
        }
    
    def _send_websocket_notification(self, notification: Dict[str, Any]):
        """Send notification via WebSocket"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'debugging_dashboard',
                    {
                        'type': 'error_notification',
                        'notification': notification
                    }
                )
                logger.debug("Dashboard WebSocket notification sent")
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
    
    def _store_notification_in_cache(self, notification: Dict[str, Any]):
        """Store notification in cache for dashboard polling"""
        cache_key = "dashboard_notifications"
        notifications = cache.get(cache_key, [])
        
        # Add new notification
        notifications.append(notification)
        
        # Keep only last 50 notifications
        notifications = notifications[-50:]
        
        # Store for 1 hour
        cache.set(cache_key, notifications, 3600)


class NotificationManager:
    """Manages all notification handlers"""
    
    def __init__(self):
        self.handlers = {
            'email': EmailNotificationHandler(),
            'webhook': WebhookNotificationHandler(),
            'slack': SlackNotificationHandler(),
            'dashboard': DashboardNotificationHandler()
        }
    
    def send_notifications(self, escalation_data: Dict[str, Any]):
        """Send notifications through all configured handlers"""
        escalation_level = escalation_data['escalation_level']
        
        # Get notification configuration
        notification_config = self._get_notification_config(escalation_level)
        
        # Send through enabled handlers
        for handler_name, handler in self.handlers.items():
            if notification_config.get(handler_name, {}).get('enabled', False):
                try:
                    method_name = f"send_{handler_name}_notification"
                    if hasattr(handler, method_name):
                        getattr(handler, method_name)(escalation_data)
                except Exception as e:
                    logger.error(f"Failed to send {handler_name} notification: {e}")
    
    def _get_notification_config(self, escalation_level: str) -> Dict[str, Any]:
        """Get notification configuration for escalation level"""
        try:
            config = DebugConfiguration.objects.get(
                name=f"notifications_{escalation_level}",
                enabled=True
            )
            return config.config_data
        except DebugConfiguration.DoesNotExist:
            # Default configuration
            return {
                'email': {'enabled': True},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'dashboard': {'enabled': True}
            }
    
    def register_custom_handler(self, name: str, handler: Any):
        """Register a custom notification handler"""
        self.handlers[name] = handler
    
    def get_notification_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get notification history from cache"""
        # This would typically query a notification log table
        # For now, return dashboard notifications from cache
        return cache.get("dashboard_notifications", [])


# Global notification manager instance
notification_manager = NotificationManager()    