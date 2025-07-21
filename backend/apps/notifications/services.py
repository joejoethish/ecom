from django.conf import settings
from django.template import Template, Context
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from typing import Dict, List, Optional, Any
import logging
import json
import requests
from datetime import datetime, timedelta

from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, NotificationBatch, NotificationAnalytics
)

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main service for handling all notification operations
    """
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.sms_service = SMSNotificationService()
        self.push_service = PushNotificationService()
        self.in_app_service = InAppNotificationService()
    
    def send_notification(
        self, 
        user: User, 
        template_type: str, 
        context_data: Dict[str, Any] = None,
        channels: List[str] = None,
        priority: str = 'NORMAL',
        scheduled_at: datetime = None,
        expires_at: datetime = None,
        related_object: Any = None
    ) -> List[Notification]:
        """
        Send notification to user across specified channels
        """
        context_data = context_data or {}
        notifications = []
        
        # Get user preferences if channels not specified
        if not channels:
            channels = self._get_preferred_channels(user, template_type)
        
        for channel in channels:
            try:
                # Check if user has enabled this channel for this type
                if not self._is_channel_enabled(user, template_type, channel):
                    logger.info(f"Channel {channel} disabled for user {user.id} and type {template_type}")
                    continue
                
                # Get template for this channel
                template = self._get_template(template_type, channel)
                if not template:
                    logger.warning(f"No template found for {template_type} - {channel}")
                    continue
                
                # Create notification
                notification = self._create_notification(
                    user=user,
                    template=template,
                    channel=channel,
                    context_data=context_data,
                    priority=priority,
                    scheduled_at=scheduled_at,
                    expires_at=expires_at,
                    related_object=related_object
                )
                
                notifications.append(notification)
                
                # Send immediately if not scheduled
                if not scheduled_at:
                    self._send_notification(notification)
                
            except Exception as e:
                logger.error(f"Error creating notification for {user.id} on {channel}: {str(e)}")
        
        return notifications
    
    def send_bulk_notification(
        self,
        template_type: str,
        context_data: Dict[str, Any] = None,
        user_criteria: Dict[str, Any] = None,
        channels: List[str] = None,
        priority: str = 'NORMAL',
        scheduled_at: datetime = None,
        created_by: User = None,
        batch_name: str = None
    ) -> NotificationBatch:
        """
        Send bulk notifications to multiple users
        """
        # Create notification batch
        batch = NotificationBatch.objects.create(
            name=batch_name or f"Bulk {template_type} - {timezone.now()}",
            template=self._get_template(template_type, channels[0] if channels else 'EMAIL'),
            scheduled_at=scheduled_at,
            created_by=created_by,
            target_criteria=user_criteria or {}
        )
        
        # Get target users
        users = self._get_users_by_criteria(user_criteria)
        batch.target_users.set(users)
        batch.total_recipients = users.count()
        batch.save()
        
        # Process batch
        if not scheduled_at:
            self._process_notification_batch(batch, context_data, channels, priority)
        
        return batch
    
    def _send_notification(self, notification: Notification):
        """
        Send individual notification based on channel
        """
        try:
            if notification.is_expired():
                notification.status = 'CANCELLED'
                notification.save()
                return
            
            service_map = {
                'EMAIL': self.email_service,
                'SMS': self.sms_service,
                'PUSH': self.push_service,
                'IN_APP': self.in_app_service,
            }
            
            service = service_map.get(notification.channel)
            if service:
                success = service.send(notification)
                if success:
                    notification.mark_as_sent()
                    self._log_notification_action(notification, 'sent')
                else:
                    notification.mark_as_failed('Service send failed')
                    self._log_notification_action(notification, 'failed')
            else:
                notification.mark_as_failed(f'Unknown channel: {notification.channel}')
                
        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {str(e)}")
            notification.mark_as_failed(str(e))
            self._log_notification_action(notification, 'failed', {'error': str(e)})
    
    def _create_notification(
        self,
        user: User,
        template: NotificationTemplate,
        channel: str,
        context_data: Dict[str, Any],
        priority: str,
        scheduled_at: datetime,
        expires_at: datetime,
        related_object: Any
    ) -> Notification:
        """
        Create notification instance with rendered content
        """
        # Render template content
        subject = self._render_template(template.subject_template, context_data)
        message = self._render_template(template.body_template, context_data)
        html_content = self._render_template(template.html_template, context_data) if template.html_template else ''
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            template=template,
            channel=channel,
            priority=priority,
            subject=subject,
            message=message,
            html_content=html_content,
            recipient_email=user.email,
            recipient_phone=getattr(user, 'phone', ''),
            scheduled_at=scheduled_at,
            expires_at=expires_at,
            metadata=context_data
        )
        
        # Link to related object if provided
        if related_object:
            from django.contrib.contenttypes.models import ContentType
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.pk
            notification.save()
        
        self._log_notification_action(notification, 'created')
        return notification
    
    def _get_template(self, template_type: str, channel: str) -> Optional[NotificationTemplate]:
        """
        Get notification template for type and channel
        """
        try:
            return NotificationTemplate.objects.get(
                template_type=template_type,
                channel=channel,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
    
    def _render_template(self, template_string: str, context_data: Dict[str, Any]) -> str:
        """
        Render Django template with context data
        """
        if not template_string:
            return ''
        
        template = Template(template_string)
        context = Context(context_data)
        return template.render(context)
    
    def _is_channel_enabled(self, user: User, template_type: str, channel: str) -> bool:
        """
        Check if user has enabled this channel for this notification type
        """
        # Map template types to preference types
        type_mapping = {
            'ORDER_CONFIRMATION': 'ORDER_UPDATES',
            'ORDER_STATUS_UPDATE': 'ORDER_UPDATES',
            'PAYMENT_SUCCESS': 'PAYMENT_UPDATES',
            'PAYMENT_FAILED': 'PAYMENT_UPDATES',
            'SHIPPING_UPDATE': 'SHIPPING_UPDATES',
            'DELIVERY_CONFIRMATION': 'SHIPPING_UPDATES',
            'PROMOTIONAL': 'PROMOTIONAL',
            'SECURITY_ALERT': 'SECURITY',
            'ACCOUNT_UPDATE': 'ACCOUNT',
            'INVENTORY_LOW': 'INVENTORY',
            'REVIEW_REQUEST': 'REVIEWS',
            'SELLER_VERIFICATION': 'SELLER_UPDATES',
            'SELLER_PAYOUT': 'SELLER_UPDATES',
        }
        
        preference_type = type_mapping.get(template_type, 'GENERAL')
        
        try:
            preference = NotificationPreference.objects.get(
                user=user,
                notification_type=preference_type,
                channel=channel
            )
            return preference.is_enabled
        except NotificationPreference.DoesNotExist:
            # Default to enabled if no preference set
            return True
    
    def _get_preferred_channels(self, user: User, template_type: str) -> List[str]:
        """
        Get user's preferred channels for a notification type
        """
        # Default channels based on template type
        default_channels = {
            'ORDER_CONFIRMATION': ['EMAIL', 'IN_APP'],
            'ORDER_STATUS_UPDATE': ['EMAIL', 'SMS', 'IN_APP'],
            'PAYMENT_SUCCESS': ['EMAIL', 'IN_APP'],
            'PAYMENT_FAILED': ['EMAIL', 'SMS', 'IN_APP'],
            'SHIPPING_UPDATE': ['EMAIL', 'SMS', 'IN_APP'],
            'SECURITY_ALERT': ['EMAIL', 'SMS', 'IN_APP'],
            'PROMOTIONAL': ['EMAIL', 'PUSH'],
            'WELCOME': ['EMAIL'],
        }
        
        return default_channels.get(template_type, ['EMAIL', 'IN_APP'])
    
    def _get_users_by_criteria(self, criteria: Dict[str, Any]) -> Any:
        """
        Get users based on criteria for bulk notifications
        """
        queryset = User.objects.all()
        
        if criteria:
            if 'is_active' in criteria:
                queryset = queryset.filter(is_active=criteria['is_active'])
            if 'date_joined_after' in criteria:
                queryset = queryset.filter(date_joined__gte=criteria['date_joined_after'])
            if 'has_orders' in criteria and criteria['has_orders']:
                queryset = queryset.filter(orders__isnull=False).distinct()
            # Add more criteria as needed
        
        return queryset
    
    def _process_notification_batch(
        self,
        batch: NotificationBatch,
        context_data: Dict[str, Any],
        channels: List[str],
        priority: str
    ):
        """
        Process notification batch
        """
        batch.status = 'PROCESSING'
        batch.started_at = timezone.now()
        batch.save()
        
        try:
            for user in batch.target_users.all():
                notifications = self.send_notification(
                    user=user,
                    template_type=batch.template.template_type,
                    context_data=context_data,
                    channels=channels,
                    priority=priority
                )
                
                # Update batch statistics
                for notification in notifications:
                    if notification.status == 'SENT':
                        batch.sent_count += 1
                    elif notification.status == 'FAILED':
                        batch.failed_count += 1
            
            batch.status = 'COMPLETED'
            batch.completed_at = timezone.now()
            
        except Exception as e:
            logger.error(f"Error processing batch {batch.id}: {str(e)}")
            batch.status = 'FAILED'
        
        batch.save()
    
    def _log_notification_action(self, notification: Notification, action: str, details: Dict[str, Any] = None):
        """
        Log notification action for analytics
        """
        NotificationLog.objects.create(
            notification=notification,
            action=action,
            details=details or {}
        )
    
    def retry_failed_notifications(self, max_age_hours: int = 24):
        """
        Retry failed notifications that can be retried
        """
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        failed_notifications = Notification.objects.filter(
            status='FAILED',
            created_at__gte=cutoff_time
        )
        
        for notification in failed_notifications:
            if notification.can_retry():
                self._send_notification(notification)
    
    def cleanup_old_notifications(self, days: int = 90):
        """
        Clean up old notifications to manage database size
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old notifications except unread in-app notifications
        Notification.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(
            channel='IN_APP',
            status__in=['PENDING', 'SENT', 'DELIVERED']
        ).delete()


class EmailNotificationService:
    """
    Service for sending email notifications
    """
    
    def send(self, notification: Notification) -> bool:
        """
        Send email notification
        """
        try:
            if notification.html_content:
                # Send HTML email
                msg = EmailMultiAlternatives(
                    subject=notification.subject,
                    body=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.recipient_email]
                )
                msg.attach_alternative(notification.html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient_email],
                    fail_silently=False
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification {notification.id}: {str(e)}")
            return False


class SMSNotificationService:
    """
    Service for sending SMS notifications
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.api_url = getattr(settings, 'SMS_API_URL', '')
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'ECOMMERCE')
    
    def send(self, notification: Notification) -> bool:
        """
        Send SMS notification
        """
        if not self.api_key or not notification.recipient_phone:
            return False
        
        try:
            # Example SMS API integration (adjust based on your SMS provider)
            payload = {
                'apikey': self.api_key,
                'numbers': notification.recipient_phone,
                'message': notification.message,
                'sender': self.sender_id
            }
            
            response = requests.post(self.api_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    notification.external_id = result.get('message_id', '')
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending SMS notification {notification.id}: {str(e)}")
            return False


class PushNotificationService:
    """
    Service for sending push notifications
    """
    
    def __init__(self):
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', '')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
    
    def send(self, notification: Notification) -> bool:
        """
        Send push notification via Firebase Cloud Messaging
        """
        if not self.fcm_server_key:
            return False
        
        try:
            # Get user's FCM token (you'll need to store this when user registers for push notifications)
            fcm_token = self._get_user_fcm_token(notification.user)
            if not fcm_token:
                return False
            
            headers = {
                'Authorization': f'key={self.fcm_server_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': fcm_token,
                'notification': {
                    'title': notification.subject,
                    'body': notification.message,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                },
                'data': {
                    'notification_id': str(notification.id),
                    'type': notification.template.template_type if notification.template else 'GENERAL'
                }
            }
            
            response = requests.post(self.fcm_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', 0) > 0:
                    notification.external_id = result.get('multicast_id', '')
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending push notification {notification.id}: {str(e)}")
            return False
    
    def _get_user_fcm_token(self, user: User) -> Optional[str]:
        """
        Get user's FCM token for push notifications
        This would typically be stored in a UserDevice model
        """
        # Placeholder - implement based on your user device tracking
        return None


class InAppNotificationService:
    """
    Service for in-app notifications (stored in database)
    """
    
    def send(self, notification: Notification) -> bool:
        """
        In-app notifications are just stored in database
        """
        # For in-app notifications, just marking as sent is enough
        # The frontend will fetch these via API
        return True


class NotificationAnalyticsService:
    """
    Service for notification analytics and reporting
    """
    
    def update_daily_analytics(self, date: datetime.date = None):
        """
        Update daily analytics for notifications
        """
        if not date:
            date = timezone.now().date()
        
        # Get all template types and channels
        templates = NotificationTemplate.objects.values_list('template_type', 'channel').distinct()
        
        for template_type, channel in templates:
            notifications = Notification.objects.filter(
                created_at__date=date,
                template__template_type=template_type,
                channel=channel
            )
            
            sent_count = notifications.filter(status__in=['SENT', 'DELIVERED', 'READ']).count()
            delivered_count = notifications.filter(status__in=['DELIVERED', 'READ']).count()
            read_count = notifications.filter(status='READ').count()
            failed_count = notifications.filter(status='FAILED').count()
            
            # Calculate rates
            delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
            read_rate = (read_count / delivered_count * 100) if delivered_count > 0 else 0
            failure_rate = (failed_count / (sent_count + failed_count) * 100) if (sent_count + failed_count) > 0 else 0
            
            # Update or create analytics record
            analytics, created = NotificationAnalytics.objects.update_or_create(
                date=date,
                template_type=template_type,
                channel=channel,
                defaults={
                    'sent_count': sent_count,
                    'delivered_count': delivered_count,
                    'read_count': read_count,
                    'failed_count': failed_count,
                    'delivery_rate': round(delivery_rate, 2),
                    'read_rate': round(read_rate, 2),
                    'failure_rate': round(failure_rate, 2),
                }
            )
    
    def get_analytics_summary(self, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """
        Get analytics summary for date range
        """
        analytics = NotificationAnalytics.objects.filter(
            date__range=[start_date, end_date]
        )
        
        summary = {
            'total_sent': analytics.aggregate(total=models.Sum('sent_count'))['total'] or 0,
            'total_delivered': analytics.aggregate(total=models.Sum('delivered_count'))['total'] or 0,
            'total_read': analytics.aggregate(total=models.Sum('read_count'))['total'] or 0,
            'total_failed': analytics.aggregate(total=models.Sum('failed_count'))['total'] or 0,
        }
        
        # Calculate overall rates
        if summary['total_sent'] > 0:
            summary['overall_delivery_rate'] = round(summary['total_delivered'] / summary['total_sent'] * 100, 2)
        else:
            summary['overall_delivery_rate'] = 0
        
        if summary['total_delivered'] > 0:
            summary['overall_read_rate'] = round(summary['total_read'] / summary['total_delivered'] * 100, 2)
        else:
            summary['overall_read_rate'] = 0
        
        return summary