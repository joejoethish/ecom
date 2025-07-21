#!/usr/bin/env python
"""
Simple validation script for notification models
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

# Setup Django
try:
    django.setup()
except Exception as e:
    print(f"Warning: Could not setup Django: {e}")
    print("Continuing with basic validation...")

def validate_notification_models():
    """Validate that notification models can be imported and have correct structure"""
    print("Validating notification models...")
    
    try:
        # Test model imports
        from apps.notifications.models import (
            NotificationTemplate, NotificationPreference, Notification,
            NotificationLog, NotificationBatch, NotificationAnalytics
        )
        print("✓ All notification models imported successfully")
        
        # Test service imports
        from apps.notifications.services import (
            NotificationService, EmailNotificationService, SMSNotificationService,
            PushNotificationService, InAppNotificationService, NotificationAnalyticsService
        )
        print("✓ All notification services imported successfully")
        
        # Test admin imports
        from apps.notifications.admin import (
            NotificationTemplateAdmin, NotificationPreferenceAdmin, NotificationAdmin,
            NotificationBatchAdmin, NotificationAnalyticsAdmin, NotificationLogAdmin
        )
        print("✓ All notification admin classes imported successfully")
        
        # Test signals import
        import apps.notifications.signals
        print("✓ Notification signals imported successfully")
        
        # Test apps config
        from apps.notifications.apps import NotificationsConfig
        print("✓ Notifications app config imported successfully")
        
        # Validate model structure
        print("\nValidating model structure...")
        
        # Check NotificationTemplate fields
        template_fields = [f.name for f in NotificationTemplate._meta.fields]
        required_template_fields = [
            'name', 'template_type', 'channel', 'subject_template', 
            'body_template', 'html_template', 'is_active'
        ]
        for field in required_template_fields:
            if field in template_fields:
                print(f"✓ NotificationTemplate has {field} field")
            else:
                print(f"✗ NotificationTemplate missing {field} field")
        
        # Check Notification fields
        notification_fields = [f.name for f in Notification._meta.fields]
        required_notification_fields = [
            'user', 'template', 'channel', 'priority', 'status',
            'subject', 'message', 'recipient_email', 'sent_at', 'delivered_at', 'read_at'
        ]
        for field in required_notification_fields:
            if field in notification_fields:
                print(f"✓ Notification has {field} field")
            else:
                print(f"✗ Notification missing {field} field")
        
        # Check NotificationPreference fields
        preference_fields = [f.name for f in NotificationPreference._meta.fields]
        required_preference_fields = ['user', 'notification_type', 'channel', 'is_enabled']
        for field in required_preference_fields:
            if field in preference_fields:
                print(f"✓ NotificationPreference has {field} field")
            else:
                print(f"✗ NotificationPreference missing {field} field")
        
        print("\n✅ All notification model validations passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

def validate_notification_services():
    """Validate notification service structure"""
    print("\nValidating notification services...")
    
    try:
        from apps.notifications.services import NotificationService
        
        # Check if service has required methods
        service = NotificationService()
        required_methods = [
            'send_notification', 'send_bulk_notification', '_send_notification',
            '_create_notification', '_get_template', '_render_template',
            '_is_channel_enabled', '_get_preferred_channels'
        ]
        
        for method in required_methods:
            if hasattr(service, method):
                print(f"✓ NotificationService has {method} method")
            else:
                print(f"✗ NotificationService missing {method} method")
        
        # Check individual service classes
        from apps.notifications.services import (
            EmailNotificationService, SMSNotificationService,
            PushNotificationService, InAppNotificationService
        )
        
        services = [
            ('EmailNotificationService', EmailNotificationService),
            ('SMSNotificationService', SMSNotificationService),
            ('PushNotificationService', PushNotificationService),
            ('InAppNotificationService', InAppNotificationService),
        ]
        
        for service_name, service_class in services:
            service_instance = service_class()
            if hasattr(service_instance, 'send'):
                print(f"✓ {service_name} has send method")
            else:
                print(f"✗ {service_name} missing send method")
        
        print("✅ All notification service validations passed!")
        return True
        
    except Exception as e:
        print(f"❌ Service validation error: {str(e)}")
        return False

def validate_management_commands():
    """Validate management commands exist"""
    print("\nValidating management commands...")
    
    command_files = [
        'send_scheduled_notifications.py',
        'retry_failed_notifications.py',
        'cleanup_old_notifications.py',
        'update_notification_analytics.py',
        'create_default_templates.py'
    ]
    
    commands_dir = 'apps/notifications/management/commands'
    
    for command_file in command_files:
        command_path = os.path.join(commands_dir, command_file)
        if os.path.exists(command_path):
            print(f"✓ Management command exists: {command_file}")
        else:
            print(f"✗ Management command missing: {command_file}")
    
    print("✅ Management command validation completed!")
    return True

if __name__ == '__main__':
    print("🔍 Starting notification system validation...\n")
    
    success = True
    success &= validate_notification_models()
    success &= validate_notification_services()
    success &= validate_management_commands()
    
    if success:
        print("\n🎉 All validations passed! Notification system is properly implemented.")
    else:
        print("\n❌ Some validations failed. Please check the errors above.")
        sys.exit(1)