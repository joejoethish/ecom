"""
Tests for background tasks.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.inventory.models import Inventory, InventoryTransaction
from apps.notifications.models import Notification

from .tasks import (
    send_email_task,
    send_sms_task,
    check_inventory_levels_task,
    send_order_confirmation_email,
    send_order_status_update_notification,
    send_welcome_email,
    process_inventory_transaction,
    cleanup_old_notifications
)

User = get_user_model()


class EmailTaskTests(TestCase):
    """Test email sending tasks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_email_task_success(self):
        """Test successful email sending."""
        result = send_email_task(
            subject='Test Subject',
            message='Test message',
            recipient_list=['test@example.com']
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')
        self.assertEqual(mail.outbox[0].body, 'Test message')
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_email_task_with_html(self):
        """Test email sending with HTML content."""
        result = send_email_task(
            subject='Test Subject',
            message='Test message',
            recipient_list=['test@example.com'],
            html_message='<h1>Test HTML</h1>'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        # Check that HTML alternative was attached
        self.assertTrue(hasattr(mail.outbox[0], 'alternatives'))
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_welcome_email(self):
        """Test welcome email sending."""
        result = send_welcome_email(self.user.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['user_id'], self.user.id)
    
    def test_send_welcome_email_user_not_found(self):
        """Test welcome email with non-existent user."""
        result = send_welcome_email(99999)
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'User not found')


class SMSTaskTests(TestCase):
    """Test SMS sending tasks."""
    
    @patch('tasks.tasks.logger')
    def test_send_sms_task_success(self, mock_logger):
        """Test successful SMS sending (mocked)."""
        result = send_sms_task(
            phone_number='+1234567890',
            message='Test SMS message'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['phone_number'], '+1234567890')
        mock_logger.info.assert_called()
    
    @patch('tasks.tasks.logger')
    def test_send_sms_task_with_template(self, mock_logger):
        """Test SMS sending with template rendering."""
        # This would require actual template rendering in a real scenario
        result = send_sms_task(
            phone_number='+1234567890',
            message='Test SMS message',
            template_name='sms/test.txt',
            context={'name': 'Test User'}
        )
        
        self.assertEqual(result['status'], 'success')


class InventoryTaskTests(TestCase):
    """Test inventory-related tasks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=5,  # Below minimum level
            minimum_stock_level=10,
            reorder_point=15,
            cost_price=50.00
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_check_inventory_levels_task(self):
        """Test inventory level checking task."""
        result = check_inventory_levels_task()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['low_stock_count'], 1)
        self.assertIn('items', result)
        self.assertEqual(len(result['items']), 1)
        
        # Check that alert email was queued (we can't easily test the actual sending in this context)
        item = result['items'][0]
        self.assertEqual(item['product_name'], 'Test Product')
        self.assertEqual(item['current_stock'], 5)
        self.assertEqual(item['minimum_level'], 10)
    
    def test_process_inventory_transaction_stock_in(self):
        """Test processing stock-in transaction."""
        initial_quantity = self.inventory.quantity
        
        result = process_inventory_transaction(
            inventory_id=self.inventory.id,
            transaction_type='IN',
            quantity=20,
            reference_number='PO-001',
            notes='Purchase order received',
            user_id=self.user.id
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['new_quantity'], initial_quantity + 20)
        
        # Verify transaction was created
        transaction = InventoryTransaction.objects.get(id=result['transaction_id'])
        self.assertEqual(transaction.transaction_type, 'IN')
        self.assertEqual(transaction.quantity, 20)
        self.assertEqual(transaction.reference_number, 'PO-001')
        self.assertEqual(transaction.created_by, self.user)
    
    def test_process_inventory_transaction_stock_out(self):
        """Test processing stock-out transaction."""
        initial_quantity = self.inventory.quantity
        
        result = process_inventory_transaction(
            inventory_id=self.inventory.id,
            transaction_type='OUT',
            quantity=3,
            reference_number='ORDER-001',
            notes='Order fulfillment',
            user_id=self.user.id
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['new_quantity'], initial_quantity - 3)
    
    def test_process_inventory_transaction_adjustment(self):
        """Test processing inventory adjustment."""
        result = process_inventory_transaction(
            inventory_id=self.inventory.id,
            transaction_type='ADJUSTMENT',
            quantity=15,  # Set to exact quantity
            reference_number='ADJ-001',
            notes='Physical count adjustment',
            user_id=self.user.id
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['new_quantity'], 15)
    
    def test_process_inventory_transaction_not_found(self):
        """Test processing transaction for non-existent inventory."""
        result = process_inventory_transaction(
            inventory_id=99999,
            transaction_type='IN',
            quantity=10,
            user_id=self.user.id
        )
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'Inventory not found')


class OrderTaskTests(TestCase):
    """Test order-related tasks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customerpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            order_number='ORD-001',
            status='CONFIRMED',
            total_amount=99.99,
            shipping_address={'street': '123 Test St', 'city': 'Test City'},
            billing_address={'street': '123 Test St', 'city': 'Test City'},
            payment_method='credit_card'
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=99.99,
            total_price=99.99
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_order_confirmation_email(self):
        """Test order confirmation email sending."""
        result = send_order_confirmation_email(self.order.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_id'], self.order.id)
    
    def test_send_order_confirmation_email_not_found(self):
        """Test order confirmation email for non-existent order."""
        result = send_order_confirmation_email(99999)
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'Order not found')
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_order_status_update_notification(self):
        """Test order status update notification."""
        result = send_order_status_update_notification(
            order_id=self.order.id,
            status='SHIPPED'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_id'], self.order.id)
        self.assertEqual(result['new_status'], 'SHIPPED')


class NotificationCleanupTests(TestCase):
    """Test notification cleanup tasks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create old read notifications
        old_date = timezone.now() - timedelta(days=35)
        for i in range(5):
            notification = Notification.objects.create(
                user=self.user,
                title=f'Old Notification {i}',
                message='This is an old notification',
                is_read=True
            )
            # Manually set the created_at to simulate old notifications
            notification.created_at = old_date
            notification.save()
        
        # Create recent notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                title=f'Recent Notification {i}',
                message='This is a recent notification',
                is_read=False
            )
    
    def test_cleanup_old_notifications(self):
        """Test cleanup of old notifications."""
        initial_count = Notification.objects.count()
        self.assertEqual(initial_count, 8)  # 5 old + 3 recent
        
        result = cleanup_old_notifications(days_old=30)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['deleted_count'], 5)  # Only old read notifications
        
        # Verify only recent notifications remain
        remaining_count = Notification.objects.count()
        self.assertEqual(remaining_count, 3)


class TaskRetryTests(TestCase):
    """Test task retry mechanisms."""
    
    @patch('tasks.tasks.send_mail')
    def test_email_task_retry_on_failure(self, mock_send_mail):
        """Test email task retry mechanism."""
        # Mock send_mail to raise an exception
        mock_send_mail.side_effect = Exception('SMTP server error')
        
        # Create a mock task instance
        mock_task = MagicMock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3
        mock_task.default_retry_delay = 60
        
        # This would normally test the retry mechanism, but requires more complex mocking
        # In a real scenario, you'd use celery's test utilities
        pass


class TaskQueueTests(TestCase):
    """Test task queue routing and configuration."""
    
    def test_task_routing_configuration(self):
        """Test that task routing is properly configured."""
        from tasks.schedules import CELERY_TASK_ROUTES
        
        # Verify email tasks are routed to email queue
        self.assertEqual(CELERY_TASK_ROUTES['tasks.tasks.send_email_task']['queue'], 'emails')
        self.assertEqual(CELERY_TASK_ROUTES['tasks.tasks.send_sms_task']['queue'], 'sms')
        self.assertEqual(CELERY_TASK_ROUTES['tasks.tasks.check_inventory_levels_task']['queue'], 'inventory')
    
    def test_periodic_task_schedule(self):
        """Test that periodic tasks are properly scheduled."""
        from tasks.schedules import CELERY_BEAT_SCHEDULE
        
        # Verify inventory check is scheduled
        self.assertIn('check-inventory-levels', CELERY_BEAT_SCHEDULE)
        self.assertEqual(
            CELERY_BEAT_SCHEDULE['check-inventory-levels']['task'],
            'tasks.tasks.check_inventory_levels_task'
        )
        
        # Verify cleanup task is scheduled
        self.assertIn('cleanup-old-notifications', CELERY_BEAT_SCHEDULE)
        self.assertEqual(
            CELERY_BEAT_SCHEDULE['cleanup-old-notifications']['task'],
            'tasks.tasks.cleanup_old_notifications'
        )