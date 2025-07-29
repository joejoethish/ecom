#!/usr/bin/env python
"""
Notification System Integration Tests

This module contains integration tests for the notification system,
testing the flow of notifications across different channels and events.
"""

import os
import sys
import django
import json
import uuid
from decimal import Decimal
from unittest import mock
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.notifications.models import (
    NotificationTemplate, NotificationPreference, Notification
)
from apps.notifications.services import NotificationService
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category
from apps.customers.models import Address
from apps.cart.models import Cart, CartItem

User = get_user_model()


class MockEmailService:
    """Mock email service for testing"""
    
    def __init__(self):
        self.sent_emails = []
    
    def send_email(self, to_email, subject, message, html_message=None, from_email=None):
        self.sent_emails.append({
            'to_email': to_email,
            'subject': subject,
            'message': message,
            'html_message': html_message,
            'from_email': from_email
        })
        return True, 'Email sent successfully'


class MockSMSService:
    """Mock SMS service for testing"""
    
    def __init__(self):
        self.sent_sms = []
    
    def send_sms(self, to_phone, message):
        self.sent_sms.append({
            'to_phone': to_phone,
            'message': message
        })
        return True, 'SMS sent successfully'


class MockPushNotificationService:
    """Mock push notification service for testing"""
    
    def __init__(self):
        self.sent_notifications = []
    
    def send_push_notification(self, user_id, title, message, data=None):
        self.sent_notifications.append({
            'user_id': user_id,
            'title': title,
            'message': message,
            'data': data
        })
        return True, 'Push notification sent successfully'


class NotificationFlowIntegrationTest(TestCase):
    """Test notification system flows"""
    
    def setUp(self):
        """Set up test data for notification flow tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='notifyuser',
            email='notify@example.com',
            password='testpass123',
            first_name='Notify',
            last_name='User',
            phone='9876543210'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.login(username='notifyuser', password='testpass123')
        
        # Create notification templates
        self.order_confirmation_email_template = NotificationTemplate.objects.create(
            name='Order Confirmation Email',
            template_type='ORDER_CONFIRMATION',
            channel='EMAIL',
            subject_template='Order Confirmation - {{ order_number }}',
            body_template='Hello {{ user_name }}, your order {{ order_number }} has been confirmed.',
            is_active=True
        )
        
        self.order_confirmation_sms_template = NotificationTemplate.objects.create(
            name='Order Confirmation SMS',
            template_type='ORDER_CONFIRMATION',
            channel='SMS',
            subject_template='',
            body_template='Your order {{ order_number }} has been confirmed. Thank you for shopping with us!',
            is_active=True
        )
        
        self.order_shipped_email_template = NotificationTemplate.objects.create(
            name='Order Shipped Email',
            template_type='ORDER_SHIPPED',
            channel='EMAIL',
            subject_template='Your Order {{ order_number }} Has Been Shipped',
            body_template='Hello {{ user_name }}, your order {{ order_number }} has been shipped. Track your order with tracking number {{ tracking_number }}.',
            is_active=True
        )
        
        self.order_delivered_push_template = NotificationTemplate.objects.create(
            name='Order Delivered Push',
            template_type='ORDER_DELIVERED',
            channel='PUSH',
            subject_template='Order Delivered',
            body_template='Your order {{ order_number }} has been delivered. Enjoy your purchase!',
            is_active=True
        )
        
        self.price_drop_email_template = NotificationTemplate.objects.create(
            name='Price Drop Email',
            template_type='PRICE_DROP',
            channel='EMAIL',
            subject_template='Price Drop Alert for {{ product_name }}',
            body_template='Hello {{ user_name }}, the price of {{ product_name }} has dropped to {{ new_price }}!',
            is_active=True
        )
        
        # Create notification preferences
        self.email_preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='EMAIL',
            is_enabled=True
        )
        
        self.sms_preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='SMS',
            is_enabled=True
        )
        
        self.push_preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='ORDER_UPDATES',
            channel='PUSH',
            is_enabled=True
        )
        
        self.price_drop_preference = NotificationPreference.objects.create(
            user=self.user,
            notification_type='PRICE_ALERTS',
            channel='EMAIL',
            is_enabled=True
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            short_description='Test product',
            category=self.category,
            brand='TestBrand',
            sku='TEST001',
            price=Decimal('100.00'),
            is_active=True
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Notify',
            last_name='User',
            address_line_1='123 Notify Street',
            city='Notify City',
            state='Notify State',
            postal_code='12345',
            country='India',
            phone='9876543210',
            is_default=True
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.user,
            order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
            status='PENDING',
            total_amount=Decimal('100.00'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            shipping_address={
                'first_name': 'Notify',
                'last_name': 'User',
                'address_line_1': '123 Notify Street',
                'city': 'Notify City',
                'state': 'Notify State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '9876543210'
            },
            billing_address={
                'first_name': 'Notify',
                'last_name': 'User',
                'address_line_1': '123 Notify Street',
                'city': 'Notify City',
                'state': 'Notify State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '9876543210'
            },
            payment_method='PREPAID',
            payment_status='PENDING'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Create mock services
        self.mock_email_service = MockEmailService()
        self.mock_sms_service = MockSMSService()
        self.mock_push_service = MockPushNotificationService()

    @mock.patch('apps.notifications.services.email_service.send_email')
    @mock.patch('apps.notifications.services.sms_service.send_sms')
    def test_order_confirmation_notifications(self, mock_send_sms, mock_send_email):
        """Test order confirmation notification flow"""
        print("\nTesting order confirmation notification flow...")
        
        # Setup mocks
        mock_send_email.side_effect = self.mock_email_service.send_email
        mock_send_sms.side_effect = self.mock_sms_service.send_sms
        
        # Step 1: Confirm order and trigger notifications
        self.order.status = 'CONFIRMED'
        self.order.payment_status = 'PAID'
        self.order.save()
        
        # Step 2: Manually trigger notifications (in real system, this would be done by signals)
        notification_service = NotificationService()
        context = {
            'user_name': f"{self.user.first_name} {self.user.last_name}",
            'order_number': self.order.order_number,
            'order_date': self.order.created_at.strftime('%Y-%m-%d'),
            'order_total': str(self.order.total_amount),
            'shipping_address': self.order.shipping_address
        }
        
        # Send email notification
        notification_service.send_notification(
            user=self.user,
            notification_type='ORDER_CONFIRMATION',
            context=context,
            channel='EMAIL'
        )
        
        # Send SMS notification
        notification_service.send_notification(
            user=self.user,
            notification_type='ORDER_CONFIRMATION',
            context=context,
            channel='SMS'
        )
        
        # Step 3: Verify email notification was sent
        self.assertEqual(len(self.mock_email_service.sent_emails), 1)
        email = self.mock_email_service.sent_emails[0]
        self.assertEqual(email['to_email'], self.user.email)
        self.assertIn(self.order.order_number, email['subject'])
        self.assertIn(self.user.first_name, email['message'])
        self.assertIn(self.order.order_number, email['message'])
        print("✓ Order confirmation email sent successfully")
        
        # Step 4: Verify SMS notification was sent
        self.assertEqual(len(self.mock_sms_service.sent_sms), 1)
        sms = self.mock_sms_service.sent_sms[0]
        self.assertEqual(sms['to_phone'], self.user.phone)
        self.assertIn(self.order.order_number, sms['message'])
        print("✓ Order confirmation SMS sent successfully")
        
        # Step 5: Verify notifications were recorded in database
        email_notifications = Notification.objects.filter(
            user=self.user,
            template=self.order_confirmation_email_template
        )
        self.assertEqual(email_notifications.count(), 1)
        self.assertEqual(email_notifications.first().status, 'SENT')
        
        sms_notifications = Notification.objects.filter(
            user=self.user,
            template=self.order_confirmation_sms_template
        )
        self.assertEqual(sms_notifications.count(), 1)
        self.assertEqual(sms_notifications.first().status, 'SENT')
        print("✓ Notifications recorded in database")
        
        print("✓ Order confirmation notification flow test passed!")

    @mock.patch('apps.notifications.services.email_service.send_email')
    def test_order_shipped_notification(self, mock_send_email):
        """Test order shipped notification flow"""
        print("\nTesting order shipped notification flow...")
        
        # Setup mock
        mock_send_email.side_effect = self.mock_email_service.send_email
        
        # Step 1: Update order status to shipped
        self.order.status = 'SHIPPED'
        self.order.save()
        
        # Create shipment tracking info
        tracking_number = f'TRACK-{uuid.uuid4().hex[:8].upper()}'
        
        # Step 2: Manually trigger notification
        notification_service = NotificationService()
        context = {
            'user_name': f"{self.user.first_name} {self.user.last_name}",
            'order_number': self.order.order_number,
            'tracking_number': tracking_number,
            'carrier': 'Test Carrier',
            'estimated_delivery': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        notification_service.send_notification(
            user=self.user,
            notification_type='ORDER_SHIPPED',
            context=context,
            channel='EMAIL'
        )
        
        # Step 3: Verify email notification was sent
        self.assertEqual(len(self.mock_email_service.sent_emails), 1)
        email = self.mock_email_service.sent_emails[0]
        self.assertEqual(email['to_email'], self.user.email)
        self.assertIn(self.order.order_number, email['subject'])
        self.assertIn('shipped', email['subject'].lower())
        self.assertIn(tracking_number, email['message'])
        print("✓ Order shipped email sent successfully")
        
        # Step 4: Verify notification was recorded in database
        notifications = Notification.objects.filter(
            user=self.user,
            template=self.order_shipped_email_template
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().status, 'SENT')
        print("✓ Notification recorded in database")
        
        print("✓ Order shipped notification flow test passed!")

    @mock.patch('apps.notifications.services.push_service.send_push_notification')
    def test_order_delivered_notification(self, mock_send_push):
        """Test order delivered notification flow"""
        print("\nTesting order delivered notification flow...")
        
        # Setup mock
        mock_send_push.side_effect = self.mock_push_service.send_push_notification
        
        # Step 1: Update order status to delivered
        self.order.status = 'DELIVERED'
        self.order.save()
        
        # Step 2: Manually trigger notification
        notification_service = NotificationService()
        context = {
            'user_name': f"{self.user.first_name} {self.user.last_name}",
            'order_number': self.order.order_number,
            'delivery_date': timezone.now().strftime('%Y-%m-%d')
        }
        
        notification_service.send_notification(
            user=self.user,
            notification_type='ORDER_DELIVERED',
            context=context,
            channel='PUSH'
        )
        
        # Step 3: Verify push notification was sent
        self.assertEqual(len(self.mock_push_service.sent_notifications), 1)
        push = self.mock_push_service.sent_notifications[0]
        self.assertEqual(push['user_id'], self.user.id)
        self.assertEqual(push['title'], 'Order Delivered')
        self.assertIn(self.order.order_number, push['message'])
        print("✓ Order delivered push notification sent successfully")
        
        # Step 4: Verify notification was recorded in database
        notifications = Notification.objects.filter(
            user=self.user,
            template=self.order_delivered_push_template
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().status, 'SENT')
        print("✓ Notification recorded in database")
        
        print("✓ Order delivered notification flow test passed!")

    @mock.patch('apps.notifications.services.email_service.send_email')
    def test_price_drop_notification(self, mock_send_email):
        """Test price drop notification flow"""
        print("\nTesting price drop notification flow...")
        
        # Setup mock
        mock_send_email.side_effect = self.mock_email_service.send_email
        
        # Step 1: Update product price
        old_price = self.product.price
        new_price = Decimal('80.00')  # 20% discount
        self.product.price = new_price
        self.product.save()
        
        # Step 2: Manually trigger notification
        notification_service = NotificationService()
        context = {
            'user_name': f"{self.user.first_name} {self.user.last_name}",
            'product_name': self.product.name,
            'product_slug': self.product.slug,
            'old_price': str(old_price),
            'new_price': str(new_price),
            'discount_percentage': '20%'
        }
        
        notification_service.send_notification(
            user=self.user,
            notification_type='PRICE_DROP',
            context=context,
            channel='EMAIL'
        )
        
        # Step 3: Verify email notification was sent
        self.assertEqual(len(self.mock_email_service.sent_emails), 1)
        email = self.mock_email_service.sent_emails[0]
        self.assertEqual(email['to_email'], self.user.email)
        self.assertIn(self.product.name, email['subject'])
        self.assertIn('Price Drop', email['subject'])
        self.assertIn(str(new_price), email['message'])
        print("✓ Price drop email sent successfully")
        
        # Step 4: Verify notification was recorded in database
        notifications = Notification.objects.filter(
            user=self.user,
            template=self.price_drop_email_template
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().status, 'SENT')
        print("✓ Notification recorded in database")
        
        print("✓ Price drop notification flow test passed!")

    def test_notification_preferences(self):
        """Test notification preferences management"""
        print("\nTesting notification preferences management...")
        
        # Step 1: Update notification preferences via API
        response = self.client.patch('/api/v1/notifications/preferences/', {
            'ORDER_UPDATES': {
                'EMAIL': False,
                'SMS': True,
                'PUSH': True
            },
            'PRICE_ALERTS': {
                'EMAIL': True,
                'SMS': False,
                'PUSH': True
            }
        }, format='json')
        self.assertEqual(response.status_code, 200)
        print("✓ Notification preferences updated successfully")
        
        # Step 2: Verify preferences were updated in database
        self.email_preference.refresh_from_db()
        self.assertFalse(self.email_preference.is_enabled)
        
        self.sms_preference.refresh_from_db()
        self.assertTrue(self.sms_preference.is_enabled)
        
        # Check if new preference was created
        price_alerts_push = NotificationPreference.objects.get(
            user=self.user,
            notification_type='PRICE_ALERTS',
            channel='PUSH'
        )
        self.assertTrue(price_alerts_push.is_enabled)
        print("✓ Notification preferences updated in database")
        
        # Step 3: Test notification delivery respects preferences
        notification_service = NotificationService()
        
        # This should not send (email preference disabled)
        with mock.patch('apps.notifications.services.email_service.send_email') as mock_send_email:
            mock_send_email.side_effect = self.mock_email_service.send_email
            
            notification_service.send_notification(
                user=self.user,
                notification_type='ORDER_UPDATES',
                context={'order_number': self.order.order_number},
                channel='EMAIL'
            )
            
            self.assertEqual(len(self.mock_email_service.sent_emails), 0)
            print("✓ Email notification correctly blocked by preference")
        
        # This should send (SMS preference enabled)
        with mock.patch('apps.notifications.services.sms_service.send_sms') as mock_send_sms:
            mock_send_sms.side_effect = self.mock_sms_service.send_sms
            
            notification_service.send_notification(
                user=self.user,
                notification_type='ORDER_UPDATES',
                context={'order_number': self.order.order_number},
                channel='SMS'
            )
            
            self.assertEqual(len(self.mock_sms_service.sent_sms), 1)
            print("✓ SMS notification correctly sent based on preference")
        
        print("✓ Notification preferences test passed!")

    def test_notification_history(self):
        """Test notification history retrieval"""
        print("\nTesting notification history retrieval...")
        
        # Step 1: Create some notifications in the database
        notification1 = Notification.objects.create(
            user=self.user,
            template=self.order_confirmation_email_template,
            channel='EMAIL',
            subject='Order Confirmation - ORD123',
            message='Your order ORD123 has been confirmed.',
            recipient_email=self.user.email,
            status='DELIVERED',
            read_at=timezone.now()
        )
        
        notification2 = Notification.objects.create(
            user=self.user,
            template=self.order_shipped_email_template,
            channel='EMAIL',
            subject='Your Order ORD123 Has Been Shipped',
            message='Your order ORD123 has been shipped with tracking number TRACK123.',
            recipient_email=self.user.email,
            status='DELIVERED'
        )
        
        notification3 = Notification.objects.create(
            user=self.user,
            template=self.order_confirmation_sms_template,
            channel='SMS',
            message='Your order ORD456 has been confirmed.',
            recipient_phone=self.user.phone,
            status='SENT'
        )
        
        # Step 2: Retrieve notification history via API
        response = self.client.get('/api/v1/notifications/history/')
        self.assertEqual(response.status_code, 200)
        history_data = response.json()
        self.assertEqual(len(history_data['results']), 3)
        print(f"✓ Retrieved {len(history_data['results'])} notifications from history")
        
        # Step 3: Test filtering by channel
        response = self.client.get('/api/v1/notifications/history/?channel=EMAIL')
        self.assertEqual(response.status_code, 200)
        email_history = response.json()
        self.assertEqual(len(email_history['results']), 2)
        print(f"✓ Filtered history by channel successfully")
        
        # Step 4: Test filtering by read status
        response = self.client.get('/api/v1/notifications/history/?read=true')
        self.assertEqual(response.status_code, 200)
        read_history = response.json()
        self.assertEqual(len(read_history['results']), 1)
        print(f"✓ Filtered history by read status successfully")
        
        # Step 5: Mark notification as read
        response = self.client.post(f'/api/v1/notifications/{notification2.id}/mark-read/')
        self.assertEqual(response.status_code, 200)
        
        # Verify notification was marked as read
        notification2.refresh_from_db()
        self.assertIsNotNone(notification2.read_at)
        print("✓ Notification marked as read successfully")
        
        # Step 6: Test bulk mark as read
        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, 200)
        
        # Verify all notifications are marked as read
        unread_count = Notification.objects.filter(user=self.user, read_at__isnull=True).count()
        self.assertEqual(unread_count, 0)
        print("✓ All notifications marked as read successfully")
        
        print("✓ Notification history test passed!")


def main():
    """Run the notification flow integration tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_notification_flows'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()