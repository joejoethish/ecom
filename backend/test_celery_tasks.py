#!/usr/bin/env python
"""
Standalone test script for Celery tasks.
This script tests the task functions directly without Django's test framework.
"""
import os
import sys
import django
from unittest.mock import patch, MagicMock

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

def test_email_task():
    """Test email sending task."""
    from tasks.tasks import send_email_task
    
    print("Testing email task...")
    
    with patch('tasks.tasks.send_mail') as mock_send_mail:
        result = send_email_task(
            subject='Test Subject',
            message='Test message',
            recipient_list=['test@example.com']
        )
        
        assert result['status'] == 'success'
        assert result['recipients'] == ['test@example.com']
        mock_send_mail.assert_called_once()
        print("✓ Email task test passed")

def test_sms_task():
    """Test SMS sending task."""
    from tasks.tasks import send_sms_task
    
    print("Testing SMS task...")
    
    result = send_sms_task(
        phone_number='+1234567890',
        message='Test SMS message'
    )
    
    assert result['status'] == 'success'
    assert result['phone_number'] == '+1234567890'
    print("✓ SMS task test passed")

def test_inventory_check_task():
    """Test inventory checking task."""
    from tasks.tasks import check_inventory_levels_task
    from apps.products.models import Product, Category
    from apps.inventory.models import Inventory
    from django.contrib.auth import get_user_model
    
    print("Testing inventory check task...")
    
    User = get_user_model()
    
    # Create test data
    user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        is_staff=True
    )
    
    category = Category.objects.create(name='Electronics')
    product = Product.objects.create(
        name='Test Product',
        slug='test-product',
        category=category,
        price=99.99,
        sku='TEST001'
    )
    
    inventory = Inventory.objects.create(
        product=product,
        quantity=5,  # Below minimum level
        minimum_stock_level=10,
        reorder_point=15,
        cost_price=50.00
    )
    
    with patch('tasks.tasks.send_email_task.delay') as mock_email_task:
        result = check_inventory_levels_task()
        
        assert result['status'] == 'success'
        assert result['low_stock_count'] == 1
        assert len(result['items']) == 1
        assert result['items'][0]['product_name'] == 'Test Product'
        print("✓ Inventory check task test passed")

def test_inventory_transaction_task():
    """Test inventory transaction processing task."""
    from tasks.tasks import process_inventory_transaction
    from apps.products.models import Product, Category
    from apps.inventory.models import Inventory
    from django.contrib.auth import get_user_model
    
    print("Testing inventory transaction task...")
    
    User = get_user_model()
    
    # Create test data
    user = User.objects.create_user(
        username='admin2',
        email='admin2@example.com'
    )
    
    category = Category.objects.create(name='Books')
    product = Product.objects.create(
        name='Test Book',
        slug='test-book',
        category=category,
        price=29.99,
        sku='BOOK001'
    )
    
    inventory = Inventory.objects.create(
        product=product,
        quantity=10,
        minimum_stock_level=5,
        reorder_point=8,
        cost_price=15.00
    )
    
    result = process_inventory_transaction(
        inventory_id=inventory.id,
        transaction_type='IN',
        quantity=20,
        reference_number='PO-001',
        notes='Purchase order received',
        user_id=user.id
    )
    
    assert result['status'] == 'success'
    assert result['new_quantity'] == 30  # 10 + 20
    print("✓ Inventory transaction task test passed")

def test_notification_cleanup_task():
    """Test notification cleanup task."""
    from tasks.tasks import cleanup_old_notifications
    from apps.notifications.models import Notification
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    
    print("Testing notification cleanup task...")
    
    User = get_user_model()
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com'
    )
    
    # Create old read notifications
    old_date = timezone.now() - timedelta(days=35)
    for i in range(3):
        notification = Notification.objects.create(
            user=user,
            title=f'Old Notification {i}',
            message='This is an old notification',
            is_read=True
        )
        # Manually set the created_at to simulate old notifications
        notification.created_at = old_date
        notification.save()
    
    # Create recent notifications
    for i in range(2):
        Notification.objects.create(
            user=user,
            title=f'Recent Notification {i}',
            message='This is a recent notification',
            is_read=False
        )
    
    initial_count = Notification.objects.count()
    assert initial_count == 5  # 3 old + 2 recent
    
    result = cleanup_old_notifications(days_old=30)
    
    assert result['status'] == 'success'
    assert result['deleted_count'] == 3  # Only old read notifications
    
    # Verify only recent notifications remain
    remaining_count = Notification.objects.count()
    assert remaining_count == 2
    print("✓ Notification cleanup task test passed")

def test_payment_sync_task():
    """Test payment status sync task."""
    from tasks.tasks import sync_payment_status_task
    from apps.payments.models import Payment, PaymentMethod
    from apps.orders.models import Order
    from django.contrib.auth import get_user_model
    
    print("Testing payment sync task...")
    
    User = get_user_model()
    
    # Create test data
    user = User.objects.create_user(
        username='customer',
        email='customer@example.com'
    )
    
    order = Order.objects.create(
        user=user,
        order_number='ORD-001',
        status='CONFIRMED',
        total_amount=99.99,
        shipping_address={'street': '123 Test St', 'city': 'Test City'},
        billing_address={'street': '123 Test St', 'city': 'Test City'},
        payment_method='credit_card'
    )
    
    payment_method = PaymentMethod.objects.create(
        name='Credit Card',
        gateway='STRIPE',
        is_active=True
    )
    
    payment = Payment.objects.create(
        order=order,
        user=user,
        payment_method=payment_method,
        amount=99.99,
        currency='USD',
        status='PENDING',
        gateway_payment_id='pi_123456789'
    )
    
    with patch('tasks.tasks.sync_stripe_payment_status') as mock_sync:
        # Mock the Stripe sync function to return a completed status
        mock_sync.return_value = {
            "status": "COMPLETED",
            "gateway_payment_id": payment.gateway_payment_id,
            "synced_at": timezone.now().isoformat()
        }
        
        result = sync_payment_status_task(payment.id)
        
        assert result['status'] == 'success'
        assert result['synced_count'] == 1
        
        # Refresh payment from database
        payment.refresh_from_db()
        assert payment.status == 'COMPLETED'
        
        print("✓ Payment sync task test passed")

def test_abandoned_cart_reminder_task():
    """Test abandoned cart reminder task."""
    from tasks.tasks import send_abandoned_cart_reminders
    from apps.cart.models import Cart, CartItem
    from apps.products.models import Product, Category
    from django.contrib.auth import get_user_model
    
    print("Testing abandoned cart reminder task...")
    
    User = get_user_model()
    
    # Create test data
    user = User.objects.create_user(
        username='shopper',
        email='shopper@example.com'
    )
    
    category = Category.objects.create(name='Electronics')
    product = Product.objects.create(
        name='Test Product',
        slug='test-product',
        category=category,
        price=99.99,
        sku='TEST001'
    )
    
    cart = Cart.objects.create(user=user)
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )
    
    # Set cart updated_at to 25 hours ago
    cart.updated_at = timezone.now() - timedelta(hours=25)
    cart.save(update_fields=['updated_at'])
    
    with patch('tasks.tasks.send_email_task.delay') as mock_email_task:
        result = send_abandoned_cart_reminders()
        
        assert result['status'] == 'success'
        assert result['reminder_count'] >= 1
        mock_email_task.assert_called()
        
        print("✓ Abandoned cart reminder task test passed")

def main():
    """Run all tests."""
    print("Running Celery task tests...")
    print("=" * 50)
    
    try:
        test_email_task()
        test_sms_task()
        test_inventory_check_task()
        test_inventory_transaction_task()
        test_notification_cleanup_task()
        test_payment_sync_task()
        test_abandoned_cart_reminder_task()
        
        print("=" * 50)
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()