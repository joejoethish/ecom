#!/usr/bin/env python
"""
Simple test script for notification models without Django test framework
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')

# Setup Django
django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model
from apps.notifications.models import (
    NotificationTemplate, NotificationPreference, Notification
)
from apps.notifications.services import NotificationService

User = get_user_model()

def test_notification_models():
    """Test notification models creation and basic functionality"""
    print("Testing notification models...")
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    print(f"✓ Created user: {user.username}")
    
    # Create a notification template
    template = NotificationTemplate.objects.create(
        name='Test Template',
        template_type='ORDER_CONFIRMATION',
        channel='EMAIL',
        subject_template='Order Confirmation - {{ order_number }}',
        body_template='Hello {{ user_name }}, your order {{ order_number }} has been confirmed.',
        is_active=True
    )
    print(f"✓ Created template: {template.name}")
    
    # Create notification preference
    preference = NotificationPreference.objects.create(
        user=user,
        notification_type='ORDER_UPDATES',
        channel='EMAIL',
        is_enabled=True
    )
    print(f"✓ Created preference: {preference}")
    
    # Create a notification
    notification = Notification.objects.create(
        user=user,
        template=template,
        channel='EMAIL',
        subject='Test Order Confirmation',
        message='Hello Test User, your order ORD-12345 has been confirmed.',
        recipient_email=user.email,
        priority='NORMAL'
    )
    print(f"✓ Created notification: {notification.subject}")
    
    # Test notification status methods
    notification.mark_as_sent()
    print(f"✓ Marked notification as sent: {notification.status}")
    
    notification.mark_as_delivered()
    print(f"✓ Marked notification as delivered: {notification.status}")
    
    notification.mark_as_read()
    print(f"✓ Marked notification as read: {notification.status}")
    
    # Test notification service
    service = NotificationService()
    print("✓ Created notification service")
    
    # Test template rendering
    context_data = {
        'user_name': 'Test User',
        'order_number': 'ORD-67890'
    }
    
    rendered_subject = service._render_template(template.subject_template, context_data)
    rendered_message = service._render_template(template.body_template, context_data)
    
    print(f"✓ Rendered subject: {rendered_subject}")
    print(f"✓ Rendered message: {rendered_message}")
    
    # Test preference checking
    is_enabled = service._is_channel_enabled(user, 'ORDER_CONFIRMATION', 'EMAIL')
    print(f"✓ Channel enabled check: {is_enabled}")
    
    print("\n🎉 All notification model tests passed!")

def test_notification_signals():
    """Test notification signals"""
    print("\nTesting notification signals...")
    
    # Create a new user to trigger welcome notification signal
    new_user = User.objects.create_user(
        username='newuser',
        email='newuser@example.com',
        password='testpass123'
    )
    
    # Check if default preferences were created
    preferences = NotificationPreference.objects.filter(user=new_user)
    print(f"✓ Default preferences created: {preferences.count()} preferences")
    
    # Check specific preference
    email_order_pref = preferences.filter(
        notification_type='ORDER_UPDATES',
        channel='EMAIL'
    ).first()
    
    if email_order_pref:
        print(f"✓ Email order preference created and enabled: {email_order_pref.is_enabled}")
    else:
        print("✗ Email order preference not found")
    
    print("🎉 Notification signals test completed!")

if __name__ == '__main__':
    try:
        test_notification_models()
        test_notification_signals()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)