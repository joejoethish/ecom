from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from .models import (
    NotificationTemplate, NotificationPreference, Notification,
    NotificationLog, NotificationBatch, NotificationAnalytics
)
from .services import (
    NotificationService, EmailNotificationService, SMSNotificationService,
    PushNotificationService, InAppNotificationService, NotificationAnalyticsService
)

User = get_user_model()


class NotificationModelTests(TestCase):
    """
    Test cases for notification models
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Order Confirmation - {{ order_number }}',
            body_template='Hello {{ user_name }}, your order {{ order_number }} has been confirmed.',
            is_active=True
        )
    
    def test_notification_template_creation(self):
        """Test notification template creation"""
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.template_type, 'ORDER_CONFIRMATION')
        self.assertEqual(self.template.channel, 'EMAIL')
        self.assertTrue(self.template.is_active)
    
    def test_notification_template_str(self):
        """Test notification template string representation"""
        expected = f"{self.template.name} - {self.template.get_channel_display()}"
        self.assertEqual(str(self.template), expected)
    
    def test_notification_preference_creation(self):
        """Test notification preference creation"""
        preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='EMAIL',
            is_enabled=True
        )
        
        self.assertEqual(preference.user, self.user)
        self.assertEqual(preference.notification_type, 'ORDER_UPDATES')
        self.assertEqual(preference.channel, 'EMAIL')
        self.assertTrue(preference.is_enabled)
    
    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email,
            priority='NORMAL'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.template, self.template)
        self.assertEqual(notification.channel, 'EMAIL')
        self.assertEqual(notification.status, 'PENDING')
        self.assertEqual(notification.priority, 'NORMAL')
    
    def test_notification_mark_as_sent(self):
        """Test marking notification as sent"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email
        )
        
        notification.mark_as_sent()
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'SENT')
        self.assertIsNotNone(notification.sent_at)
    
    def test_notification_mark_as_delivered(self):
        """Test marking notification as delivered"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email
        )
        
        notification.mark_as_delivered()
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'DELIVERED')
        self.assertIsNotNone(notification.delivered_at)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email
        )
        
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'READ')
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_mark_as_failed(self):
        """Test marking notification as failed"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email
        )
        
        error_message = 'Test error'
        notification.mark_as_failed(error_message)
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'FAILED')
        self.assertEqual(notification.error_message, error_message)
        self.assertEqual(notification.retry_count, 1)
    
    def test_notification_can_retry(self):
        """Test notification retry logic"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email,
            max_retries=3
        )
        
        # Initially can't retry (not failed)
        self.assertFalse(notification.can_retry())
        
        # After marking as failed, can retry
        notification.mark_as_failed()
        self.assertTrue(notification.can_retry())
        
        # After max retries, can't retry
        notification.retry_count = 3
        notification.save()
        self.assertFalse(notification.can_retry())
    
    def test_notification_is_expired(self):
        """Test notification expiry logic"""
        # Not expired notification
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertFalse(notification.is_expired())
        
        # Expired notification
        notification.expires_at = timezone.now() - timedelta(hours=1)
        notification.save()
        
        self.assertTrue(notification.is_expired())


class NotificationServiceTests(TestCase):
    """
    Test cases for notification services
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Order Confirmation - {{ order_number }}',
            body_template='Hello {{ user_name }}, your order {{ order_number }} has been confirmed.',
            is_active=True
        )
        
        # Create default preferences
        NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='EMAIL',
            is_enabled=True
        )
        
        self.service = NotificationService()
    
    def test_send_notification_single_channel(self):
        """Test sending notification to single channel"""
        context_data = {
            'user_name': 'Test User',
            'order_number': 'ORD-12345'
        }
        
        notifications = self.service.send_notification(
            user=self.user,
            template_type='ORDER_CONFIRMATION',
            context_data=context_data,
            channels=['EMAIL']
        )
        
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.channel, 'EMAIL')
        self.assertEqual(notification.subject, 'Order Confirmation - ORD-12345')
        self.assertIn('Hello Test User', notification.message)
        self.assertIn('ORD-12345', notification.message)
    
    def test_send_notification_multiple_channels(self):
        """Test sending notification to multiple channels"""
        # Create templates for multiple channels
        NotificationTemplate.objects.create(
            name='SMS Template',
            template_type='ORDER_CONFIRMATION',
            channel='SMS',
            subject_template='Order Confirmation',
            body_template='Order {{ order_number }} confirmed.',
            is_active=True
        )
        
        # Create preferences for SMS
        NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='SMS',
            is_enabled=True
        )
        
        context_data = {
            'user_name': 'Test User',
            'order_number': 'ORD-12345'
        }
        
        notifications = self.service.send_notification(
            user=self.user,
            template_type='ORDER_CONFIRMATION',
            context_data=context_data,
            channels=['EMAIL', 'SMS']
        )
        
        self.assertEqual(len(notifications), 2)
        channels = [n.channel for n in notifications]
        self.assertIn('EMAIL', channels)
        self.assertIn('SMS', channels)
    
    def test_send_notification_disabled_channel(self):
        """Test sending notification when channel is disabled"""
        # Disable email notifications
        preference = NotificationPreference.objects.get(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='EMAIL'
        )
        preference.is_enabled = False
        preference.save()
        
        context_data = {
            'user_name': 'Test User',
            'order_number': 'ORD-12345'
        }
        
        notifications = self.service.send_notification(
            user=self.user,
            template_type='ORDER_CONFIRMATION',
            context_data=context_data,
            channels=['EMAIL']
        )
        
        self.assertEqual(len(notifications), 0)
    
    def test_send_notification_scheduled(self):
        """Test sending scheduled notification"""
        scheduled_time = timezone.now() + timedelta(hours=1)
        context_data = {
            'user_name': 'Test User',
            'order_number': 'ORD-12345'
        }
        
        notifications = self.service.send_notification(
            user=self.user,
            template_type='ORDER_CONFIRMATION',
            context_data=context_data,
            channels=['EMAIL'],
            scheduled_at=scheduled_time
        )
        
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        
        self.assertEqual(notification.status, 'PENDING')
        self.assertEqual(notification.scheduled_at, scheduled_time)
    
    @patch('apps.notifications.services.EmailNotificationService.send')
    def test_send_notification_with_mock_email(self, mock_send):
        """Test sending notification with mocked email service"""
        mock_send.return_value = True
        
        context_data = {
            'user_name': 'Test User',
            'order_number': 'ORD-12345'
        }
        
        notifications = self.service.send_notification(
            user=self.user,
            template_type='ORDER_CONFIRMATION',
            context_data=context_data,
            channels=['EMAIL']
        )
        
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        
        # Check that email service was called
        mock_send.assert_called_once_with(notification)
        
        # Check notification status
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'SENT')
    
    def test_bulk_notification(self):
        """Test bulk notification sending"""
        # Create additional users
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        
        context_data = {
            'promotion_title': 'Special Offer',
            'discount_percent': '20'
        }
        
        # Create promotional template
        NotificationTemplate.objects.create(
            name='Promotional Template',
            template_type='PROMOTIONAL',
            channel='EMAIL',
            subject_template='{{ promotion_title }} - {{ discount_percent }}% Off!',
            body_template='Don\'t miss our {{ promotion_title }} with {{ discount_percent }}% discount!',
            is_active=True
        )
        
        batch = self.service.send_bulk_notification(
            template_type='PROMOTIONAL',
            context_data=context_data,
            channels=['EMAIL'],
            batch_name='Test Promotional Campaign',
            created_by=self.user
        )
        
        self.assertIsInstance(batch, NotificationBatch)
        self.assertEqual(batch.name, 'Test Promotional Campaign')
        self.assertEqual(batch.total_recipients, 3)  # All 3 users


class EmailNotificationServiceTests(TestCase):
    """
    Test cases for email notification service
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Test Subject',
            body_template='Test Message',
            is_active=True
        )
        
        self.service = EmailNotificationService()
    
    def test_send_plain_text_email(self):
        """Test sending plain text email"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            recipient_email=self.user.email
        )
        
        result = self.service.send(notification)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Test Subject')
        self.assertEqual(sent_email.body, 'Test Message')
        self.assertEqual(sent_email.to, [self.user.email])
    
    def test_send_html_email(self):
        """Test sending HTML email"""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Subject',
            message='Test Message',
            html_content='<h1>Test HTML Message</h1>',
            recipient_email=self.user.email
        )
        
        result = self.service.send(notification)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Test Subject')
        self.assertEqual(sent_email.body, 'Test Message')
        self.assertIn('<h1>Test HTML Message</h1>', sent_email.alternatives[0][0])


class SMSNotificationServiceTests(TestCase):
    """
    Test cases for SMS notification service
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.phone = '+1234567890'
        self.user.save()
        
        self.service = SMSNotificationService()
    
    @patch('requests.post')
    def test_send_sms_success(self, mock_post):
        """Test successful SMS sending"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'message_id': 'SMS123456'
        }
        mock_post.return_value = mock_response
        
        notification = Notification.objects.create(
            user=self.user,
            channel='SMS',
            subject='Test SMS',
            message='Test SMS Message',
            recipient_phone=self.user.phone
        )
        
        result = self.service.send(notification)
        
        self.assertTrue(result)
        notification.refresh_from_db()
        self.assertEqual(notification.external_id, 'SMS123456')
    
    @patch('requests.post')
    def test_send_sms_failure(self, mock_post):
        """Test SMS sending failure"""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        notification = Notification.objects.create(
            user=self.user,
            channel='SMS',
            subject='Test SMS',
            message='Test SMS Message',
            recipient_phone=self.user.phone
        )
        
        result = self.service.send(notification)
        
        self.assertFalse(result)


class NotificationAnalyticsServiceTests(TestCase):
    """
    Test cases for notification analytics service
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Test Subject',
            body_template='Test Message',
            is_active=True
        )
        
        self.service = NotificationAnalyticsService()
    
    def test_update_daily_analytics(self):
        """Test updating daily analytics"""
        today = timezone.now().date()
        
        # Create test notifications
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test 1',
            message='Test Message 1',
            status='SENT'
        )
        
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test 2',
            message='Test Message 2',
            status='DELIVERED'
        )
        
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test 3',
            message='Test Message 3',
            status='FAILED'
        )
        
        # Update analytics
        self.service.update_daily_analytics(today)
        
        # Check analytics record
        analytics = NotificationAnalytics.objects.get(
            date=today,
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL'
        )
        
        self.assertEqual(analytics.sent_count, 2)  # SENT + DELIVERED
        self.assertEqual(analytics.delivered_count, 1)  # DELIVERED only
        self.assertEqual(analytics.failed_count, 1)
        self.assertEqual(analytics.delivery_rate, 50.0)  # 1/2 * 100
    
    def test_get_analytics_summary(self):
        """Test getting analytics summary"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Create analytics records
        NotificationAnalytics.objects.create(
            date=today,
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            sent_count=10,
            delivered_count=8,
            read_count=6,
            failed_count=2
        )
        
        NotificationAnalytics.objects.create(
            date=yesterday,
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            sent_count=5,
            delivered_count=4,
            read_count=3,
            failed_count=1
        )
        
        summary = self.service.get_analytics_summary(yesterday, today)
        
        self.assertEqual(summary['total_sent'], 15)
        self.assertEqual(summary['total_delivered'], 12)
        self.assertEqual(summary['total_read'], 9)
        self.assertEqual(summary['total_failed'], 3)
        self.assertEqual(summary['overall_delivery_rate'], 80.0)  # 12/15 * 100
        self.assertEqual(summary['overall_read_rate'], 75.0)  # 9/12 * 100


class NotificationSignalTests(TestCase):
    """
    Test cases for notification signals
    """
    
    def test_create_default_preferences_on_user_creation(self):
        """Test that default preferences are created when user is created"""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        # Check that preferences were created
        preferences = NotificationPreference.objects.filter(user=user)
        self.assertTrue(preferences.exists())
        
        # Check specific preferences
        email_order_pref = preferences.filter(
            notification_type='ORDER_UPDATES',
            channel='EMAIL'
        ).first()
        
        self.assertIsNotNone(email_order_pref)
        self.assertTrue(email_order_pref.is_enabled)
    
    @patch('apps.notifications.services.NotificationService.send_notification')
    def test_welcome_notification_on_user_creation(self, mock_send):
        """Test that welcome notification is sent when user is created"""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        # Check that send_notification was called
        mock_send.assert_called_once()
        
        # Check the call arguments
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['user'], user)
        self.assertEqual(call_args[1]['template_type'], 'WELCOME')
        self.assertEqual(call_args[1]['channels'], ['EMAIL'])