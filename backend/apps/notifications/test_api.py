from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    NotificationTemplate, NotificationPreference, Notification,
    NotificationBatch, NotificationAnalytics
)

User = get_user_model()


class NotificationAPITestCase(APITestCase):
    """
    Base test case for notification API tests
    """
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Create test template
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Order Confirmation - {{ order_number }}',
            body_template='Hello {{ user_name }}, your order {{ order_number }} has been confirmed.',
            is_active=True
        )
        
        # Create test preference
        self.preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='EMAIL',
            is_enabled=True
        )
        
        # Create test notification
        self.notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Notification',
            message='Test message',
            recipient_email=self.user.email,
            priority='NORMAL'
        )


class NotificationTemplateAPITests(NotificationAPITestCase):
    """
    Test cases for notification template API endpoints
    """
    
    def test_list_templates_as_admin(self):
        """Test listing templates as admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:template-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Template')
    
    def test_list_templates_as_regular_user(self):
        """Test listing templates as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:template-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_template_as_admin(self):
        """Test creating template as admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:template-list-create')
        
        data = {
            'name': 'New Template',
            'template_type': 'PAYMENT_SUCCESS',
            'channel': 'EMAIL',
            'subject_template': 'Payment Successful',
            'body_template': 'Your payment has been processed.',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Template')
        self.assertTrue(NotificationTemplate.objects.filter(name='New Template').exists())
    
    def test_create_duplicate_template(self):
        """Test creating duplicate template (should fail)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:template-list-create')
        
        data = {
            'name': 'Duplicate Template',
            'template_type': 'ORDER_CONFIRMATION',  # Same as existing
            'channel': 'EMAIL',  # Same as existing
            'subject_template': 'Duplicate',
            'body_template': 'Duplicate message',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_template_detail(self):
        """Test getting template detail"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:template-detail', kwargs={'pk': self.template.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Template')
    
    def test_update_template(self):
        """Test updating template"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:template-detail', kwargs={'pk': self.template.pk})
        
        data = {
            'name': 'Updated Template',
            'template_type': 'ORDER_CONFIRMATION',
            'channel': 'EMAIL',
            'subject_template': 'Updated Subject',
            'body_template': 'Updated message',
            'is_active': True
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Template')
        
        # Verify in database
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, 'Updated Template')


class NotificationPreferenceAPITests(NotificationAPITestCase):
    """
    Test cases for notification preference API endpoints
    """
    
    def test_list_user_preferences(self):
        """Test listing user's preferences"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:preference-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['notification_type'], 'ORDER_UPDATES')
    
    def test_bulk_update_preferences(self):
        """Test bulk updating preferences"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:preference-update')
        
        data = {
            'preferences': [
                {
                    'notification_type': 'ORDER_UPDATES',
                    'channel': 'EMAIL',
                    'is_enabled': False
                },
                {
                    'notification_type': 'PAYMENT_UPDATES',
                    'channel': 'SMS',
                    'is_enabled': True
                }
            ]
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('updated_count', response.data)
        self.assertIn('created_count', response.data)
        
        # Verify preferences were updated/created
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.is_enabled)
        
        new_preference = NotificationPreference.objects.get(
            user=self.user,
            notification_type='PAYMENT_UPDATES',
            channel='SMS'
        )
        self.assertTrue(new_preference.is_enabled)
    
    def test_get_preference_detail(self):
        """Test getting preference detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:preference-detail', kwargs={'pk': self.preference.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notification_type'], 'ORDER_UPDATES')
    
    def test_update_preference(self):
        """Test updating individual preference"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:preference-detail', kwargs={'pk': self.preference.pk})
        
        data = {
            'notification_type': 'ORDER_UPDATES',
            'channel': 'EMAIL',
            'is_enabled': False
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_enabled'])
        
        # Verify in database
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.is_enabled)


class NotificationAPITests(NotificationAPITestCase):
    """
    Test cases for notification API endpoints
    """
    
    def test_list_user_notifications(self):
        """Test listing user's notifications"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['subject'], 'Test Notification')
    
    def test_filter_notifications_by_status(self):
        """Test filtering notifications by status"""
        # Create additional notification with different status
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Read Notification',
            message='Read message',
            recipient_email=self.user.email,
            status='READ'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-list')
        
        # Filter by PENDING status
        response = self.client.get(url, {'status': 'PENDING'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'PENDING')
        
        # Filter by READ status
        response = self.client.get(url, {'status': 'READ'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'READ')
    
    def test_filter_notifications_unread_only(self):
        """Test filtering unread notifications only"""
        # Create read notification
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Read Notification',
            message='Read message',
            recipient_email=self.user.email,
            status='READ'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-list')
        response = self.client.get(url, {'unread_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'PENDING')
    
    def test_get_notification_detail(self):
        """Test getting notification detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-detail', kwargs={'pk': self.notification.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subject'], 'Test Notification')
    
    def test_get_in_app_notification_marks_as_read(self):
        """Test that getting in-app notification marks it as read"""
        # Create in-app notification
        in_app_notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='IN_APP',
            subject='In-App Notification',
            message='In-app message',
            recipient_email=self.user.email,
            status='SENT'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-detail', kwargs={'pk': in_app_notification.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify notification was marked as read
        in_app_notification.refresh_from_db()
        self.assertEqual(in_app_notification.status, 'READ')
        self.assertIsNotNone(in_app_notification.read_at)
    
    def test_create_notification_as_admin(self):
        """Test creating notification as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:notification-create')
        
        data = {
            'user_id': self.user.id,
            'template_type': 'ORDER_CONFIRMATION',
            'channels': ['EMAIL'],
            'context_data': {
                'user_name': 'Test User',
                'order_number': 'ORD-12345'
            },
            'priority': 'HIGH'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 1)  # One notification created
        self.assertEqual(response.data[0]['priority'], 'HIGH')
    
    def test_create_notification_as_regular_user(self):
        """Test creating notification as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-create')
        
        data = {
            'user_id': self.user.id,
            'template_type': 'ORDER_CONFIRMATION',
            'channels': ['EMAIL']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_mark_notifications_as_read(self):
        """Test marking specific notifications as read"""
        # Create additional notification
        notification2 = Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Notification 2',
            message='Test message 2',
            recipient_email=self.user.email
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-mark-as-read')
        
        data = {
            'notification_ids': [str(self.notification.id), str(notification2.id)]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)
        
        # Verify notifications were marked as read
        self.notification.refresh_from_db()
        notification2.refresh_from_db()
        self.assertEqual(self.notification.status, 'READ')
        self.assertEqual(notification2.status, 'READ')
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        # Create additional notifications
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='EMAIL',
            subject='Test Notification 2',
            message='Test message 2',
            recipient_email=self.user.email
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-mark-all-as-read')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)
        
        # Verify all notifications were marked as read
        unread_count = Notification.objects.filter(
            user=self.user
        ).exclude(status='READ').count()
        self.assertEqual(unread_count, 0)
    
    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        # Create notifications with different statuses
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='SMS',
            subject='SMS Notification',
            message='SMS message',
            recipient_phone='1234567890',
            status='READ'
        )
        
        Notification.objects.create(
            user=self.user,
            template=self.template,
            channel='IN_APP',
            subject='In-App Notification',
            message='In-app message',
            status='FAILED'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats = response.data
        self.assertEqual(stats['total_notifications'], 3)
        self.assertEqual(stats['unread_count'], 2)  # PENDING and FAILED
        self.assertEqual(stats['read_count'], 1)
        self.assertEqual(stats['failed_count'], 1)
        self.assertEqual(stats['email_count'], 1)
        self.assertEqual(stats['sms_count'], 1)
        self.assertEqual(stats['in_app_count'], 1)
    
    def test_get_notification_settings(self):
        """Test getting notification settings"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-settings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        settings = response.data
        self.assertIn('user_preferences', settings)
        self.assertIn('available_types', settings)
        self.assertIn('available_channels', settings)
        self.assertEqual(len(settings['user_preferences']), 1)


class NotificationBatchAPITests(NotificationAPITestCase):
    """
    Test cases for notification batch API endpoints
    """
    
    def test_list_batches_as_admin(self):
        """Test listing batches as admin"""
        # Create test batch
        batch = NotificationBatch.objects.create(
            name='Test Batch',
            template=self.template,
            created_by=self.admin_user,
            total_recipients=10
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:batch-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Batch')
    
    def test_list_batches_as_regular_user(self):
        """Test listing batches as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:batch-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_batch_detail(self):
        """Test getting batch detail"""
        batch = NotificationBatch.objects.create(
            name='Test Batch',
            template=self.template,
            created_by=self.admin_user,
            total_recipients=10,
            sent_count=8,
            failed_count=2
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:batch-detail', kwargs={'pk': batch.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Batch')
        self.assertEqual(response.data['success_rate'], 80.0)  # 8/10 * 100


class NotificationAnalyticsAPITests(NotificationAPITestCase):
    """
    Test cases for notification analytics API endpoints
    """
    
    def test_list_analytics_as_admin(self):
        """Test listing analytics as admin"""
        # Create test analytics
        today = timezone.now().date()
        NotificationAnalytics.objects.create(
            date=today,
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            sent_count=100,
            delivered_count=95,
            read_count=80,
            failed_count=5,
            delivery_rate=95.0,
            read_rate=84.21,
            failure_rate=5.0
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:analytics-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sent_count'], 100)
    
    def test_list_analytics_as_regular_user(self):
        """Test listing analytics as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:analytics-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_analytics_summary(self):
        """Test getting analytics summary"""
        # Create test analytics
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        NotificationAnalytics.objects.create(
            date=today,
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            sent_count=50,
            delivered_count=45,
            read_count=40,
            failed_count=5
        )
        
        NotificationAnalytics.objects.create(
            date=yesterday,
            template_type='PAYMENT_SUCCESS',
            channel='SMS',
            sent_count=30,
            delivered_count=28,
            read_count=25,
            failed_count=2
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:analytics-summary')
        
        # Test with date range
        response = self.client.get(url, {
            'date_from': yesterday.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        summary = response.data
        self.assertEqual(summary['total_sent'], 80)
        self.assertEqual(summary['total_delivered'], 73)
        self.assertEqual(summary['total_failed'], 7)


class NotificationUtilityAPITests(NotificationAPITestCase):
    """
    Test cases for notification utility API endpoints
    """
    
    def test_get_notification_types(self):
        """Test getting notification types and options"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:notification-types')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('notification_types', data)
        self.assertIn('channels', data)
        self.assertIn('template_types', data)
        self.assertIn('priorities', data)
        self.assertIn('statuses', data)
        
        # Verify structure
        self.assertTrue(len(data['notification_types']) > 0)
        self.assertTrue(len(data['channels']) > 0)
        
        # Check first item structure
        first_type = data['notification_types'][0]
        self.assertIn('value', first_type)
        self.assertIn('label', first_type)
    
    def test_retry_failed_notifications_as_admin(self):
        """Test retrying failed notifications as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:retry-failed')
        
        data = {'max_age_hours': 48}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_retry_failed_notifications_as_regular_user(self):
        """Test retrying failed notifications as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notifications:retry-failed')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_analytics_as_admin(self):
        """Test updating analytics as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:update-analytics')
        
        today = timezone.now().date()
        data = {'date': today.strftime('%Y-%m-%d')}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_update_analytics_invalid_date(self):
        """Test updating analytics with invalid date"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('notifications:update-analytics')
        
        data = {'date': 'invalid-date'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)