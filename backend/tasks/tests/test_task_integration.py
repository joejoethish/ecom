"""
Integration tests for background tasks.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem, OrderTracking
from apps.inventory.models import Inventory, InventoryTransaction
from apps.payments.models import Payment, PaymentMethod
from apps.notifications.models import Notification
from apps.cart.models import Cart, CartItem

from tasks.tasks import (
    send_email_task,
    send_order_confirmation_email,
    send_order_status_update_notification,
    process_inventory_transaction,
    sync_payment_status_task,
    check_inventory_levels_task,
    send_abandoned_cart_reminders,
    monitor_order_fulfillment_task
)

User = get_user_model()


class OrderEmailTaskIntegrationTests(TestCase):
    """Test integration between order processing and email tasks."""
    
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
        
        self.inventory = Inventory.objects.create(
            product=self.product,
            quantity=10,
            minimum_stock_level=5,
            reorder_point=8,
            cost_price=50.00
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
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=99.99,
            total_price=99.99
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('tasks.tasks.send_email_task.delay')
    def test_order_confirmation_email_flow(self, mock_email_task):
        """Test order confirmation email flow."""
        # Call the task directly
        result = send_order_confirmation_email(self.order.id)
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_id'], self.order.id)
        
        # Verify that send_email_task was called with correct parameters
        mock_email_task.assert_called_once()
        args, kwargs = mock_email_task.call_args
        
        self.assertEqual(kwargs['subject'], f"Order Confirmation - #{self.order.order_number}")
        self.assertIn(self.order.order_number, kwargs['message'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])
        self.assertEqual(kwargs['template_name'], 'emails/order_confirmation.html')
        
        # Verify that notification was created
        notification = Notification.objects.filter(
            user=self.user,
            notification_type="ORDER_CONFIRMATION"
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.order.order_number, notification.title)
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('tasks.tasks.send_email_task.delay')
    @patch('tasks.tasks.send_sms_task.delay')
    def test_order_status_update_notification_flow(self, mock_sms_task, mock_email_task):
        """Test order status update notification flow."""
        # Update order status
        new_status = 'SHIPPED'
        
        # Call the task directly
        result = send_order_status_update_notification(self.order.id, new_status)
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['order_id'], self.order.id)
        self.assertEqual(result['new_status'], new_status)
        
        # Verify that send_email_task was called with correct parameters
        mock_email_task.assert_called_once()
        args, kwargs = mock_email_task.call_args
        
        self.assertEqual(kwargs['subject'], f"Order Update - #{self.order.order_number}")
        self.assertIn(new_status, kwargs['message'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])
        self.assertEqual(kwargs['template_name'], 'emails/order_status_update.html')
        
        # Verify that notification was created
        notification = Notification.objects.filter(
            user=self.user,
            notification_type="ORDER_STATUS_UPDATE"
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.order.order_number, notification.title)
        self.assertIn(new_status, notification.message)


class InventoryTaskIntegrationTests(TestCase):
    """Test integration between inventory operations and background tasks."""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
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
            quantity=10,
            minimum_stock_level=5,
            reorder_point=8,
            cost_price=50.00
        )
    
    @patch('tasks.tasks.send_email_task.delay')
    def test_inventory_transaction_triggers_low_stock_check(self, mock_email_task):
        """Test that inventory transactions trigger low stock checks when appropriate."""
        # Process a transaction that will reduce inventory below minimum level
        with patch('tasks.tasks.check_inventory_levels_task.delay') as mock_check_task:
            result = process_inventory_transaction(
                inventory_id=self.inventory.id,
                transaction_type='OUT',
                quantity=6,  # Reduce from 10 to 4, which is below minimum of 5
                reference_number='ORDER-001',
                notes='Order fulfillment',
                user_id=self.admin_user.id
            )
            
            # Verify transaction result
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['new_quantity'], 4)
            
            # Verify that check_inventory_levels_task was called
            mock_check_task.assert_called_once()
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('tasks.tasks.send_email_task.delay')
    def test_inventory_check_creates_notifications(self, mock_email_task):
        """Test that inventory check creates notifications for low stock items."""
        # Set inventory below minimum level
        self.inventory.quantity = 3  # Below minimum of 5
        self.inventory.save()
        
        # Run inventory check
        result = check_inventory_levels_task()
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['low_stock_count'], 1)
        
        # Verify that email task was called
        mock_email_task.assert_called_once()
        
        # Verify that notification was created for admin
        notification = Notification.objects.filter(
            user=self.admin_user,
            notification_type="INVENTORY_ALERT"
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn("Low Stock Alert", notification.title)


class PaymentTaskIntegrationTests(TestCase):
    """Test integration between payment processing and background tasks."""
    
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
        
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            gateway='STRIPE',
            is_active=True
        )
        
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=99.99,
            currency='USD',
            status='PENDING',
            gateway_payment_id='pi_123456789'
        )
    
    @patch('tasks.tasks.sync_razorpay_payment_status')
    @patch('tasks.tasks.sync_stripe_payment_status')
    def test_payment_sync_task_flow(self, mock_stripe_sync, mock_razorpay_sync):
        """Test payment sync task flow."""
        # Mock the Stripe sync function to return a completed status
        mock_stripe_sync.return_value = {
            "status": "COMPLETED",
            "gateway_payment_id": self.payment.gateway_payment_id,
            "synced_at": timezone.now().isoformat()
        }
        
        # Run payment sync task
        result = sync_payment_status_task(self.payment.id)
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['synced_count'], 1)
        
        # Verify that stripe sync was called
        mock_stripe_sync.assert_called_once()
        mock_razorpay_sync.assert_not_called()
        
        # Refresh payment from database
        self.payment.refresh_from_db()
        
        # Verify payment status was updated
        self.assertEqual(self.payment.status, 'COMPLETED')
        
        # Verify order payment status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        
        # Verify that order tracking event was created
        tracking_event = OrderTracking.objects.filter(
            order=self.order,
            description__contains='Payment'
        ).first()
        
        self.assertIsNotNone(tracking_event)


class CartReminderTaskIntegrationTests(TestCase):
    """Test integration between cart operations and reminder tasks."""
    
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
        
        self.cart = Cart.objects.create(
            user=self.user
        )
        
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        
        # Set cart updated_at to 25 hours ago
        self.cart.updated_at = timezone.now() - timedelta(hours=25)
        self.cart.save(update_fields=['updated_at'])
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('tasks.tasks.send_email_task.delay')
    def test_abandoned_cart_reminder_flow(self, mock_email_task):
        """Test abandoned cart reminder flow."""
        # Run abandoned cart reminder task
        result = send_abandoned_cart_reminders()
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['reminder_count'], 1)
        
        # Verify that email task was called
        mock_email_task.assert_called_once()
        args, kwargs = mock_email_task.call_args
        
        self.assertEqual(kwargs['subject'], "Don't forget your items!")
        self.assertEqual(kwargs['recipient_list'], [self.user.email])
        self.assertEqual(kwargs['template_name'], 'emails/abandoned_cart_reminder.html')
        
        # Verify that notification was created
        notification = Notification.objects.filter(
            user=self.user,
            notification_type="ABANDONED_CART"
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn("Items in Your Cart", notification.title)


class OrderFulfillmentMonitoringTests(TestCase):
    """Test order fulfillment monitoring tasks."""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
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
        
        # Create an order that's been confirmed but not shipped for 4 days
        self.delayed_order = Order.objects.create(
            user=self.user,
            order_number='ORD-001',
            status='CONFIRMED',
            total_amount=99.99,
            shipping_address={'street': '123 Test St', 'city': 'Test City'},
            billing_address={'street': '123 Test St', 'city': 'Test City'},
            payment_method='credit_card'
        )
        
        # Set order updated_at to 4 days ago
        self.delayed_order.updated_at = timezone.now() - timedelta(days=4)
        self.delayed_order.save(update_fields=['updated_at'])
        
        # Create a recent order that shouldn't trigger alerts
        self.recent_order = Order.objects.create(
            user=self.user,
            order_number='ORD-002',
            status='CONFIRMED',
            total_amount=99.99,
            shipping_address={'street': '123 Test St', 'city': 'Test City'},
            billing_address={'street': '123 Test St', 'city': 'Test City'},
            payment_method='credit_card'
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('tasks.tasks.send_email_task.delay')
    def test_order_fulfillment_monitoring(self, mock_email_task):
        """Test order fulfillment monitoring task."""
        # Run order fulfillment monitoring task
        result = monitor_order_fulfillment_task(max_days=3)
        
        # Verify task result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['delayed_count'], 1)
        
        # Verify that email task was called
        mock_email_task.assert_called_once()
        args, kwargs = mock_email_task.call_args
        
        self.assertIn("Order Fulfillment Alert", kwargs['subject'])
        self.assertEqual(kwargs['recipient_list'], [self.admin_user.email])
        self.assertEqual(kwargs['template_name'], 'emails/order_fulfillment_alert.html')
        
        # Verify that notification was created for admin
        notification = Notification.objects.filter(
            user=self.admin_user,
            notification_type="ORDER_FULFILLMENT_DELAY"
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn("Order Fulfillment Alert", notification.title)