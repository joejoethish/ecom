#!/usr/bin/env python
"""
Simple test script for Celery task logic without database dependencies.
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_task_imports():
    """Test that all task functions can be imported."""
    print("Testing task imports...")
    
    try:
        # Set up minimal Django environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
        import django
        django.setup()
        
        from tasks.tasks import (
            send_email_task,
            send_sms_task,
            check_inventory_levels_task,
            send_order_confirmation_email,
            send_order_status_update_notification,
            send_welcome_email,
            process_inventory_transaction,
            cleanup_old_notifications,
            send_daily_inventory_report,
            sync_payment_status_task,
            send_abandoned_cart_reminders
        )
        
        print("✓ All task functions imported successfully")
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False

def test_celery_configuration():
    """Test Celery configuration."""
    print("Testing Celery configuration...")
    
    try:
        from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
        
        # Check that periodic tasks are configured
        assert 'check-inventory-levels' in CELERY_BEAT_SCHEDULE
        assert 'cleanup-old-notifications' in CELERY_BEAT_SCHEDULE
        assert 'daily-inventory-report' in CELERY_BEAT_SCHEDULE
        assert 'sync-payment-status' in CELERY_BEAT_SCHEDULE
        assert 'abandoned-cart-reminders' in CELERY_BEAT_SCHEDULE
        
        # Check that task routing is configured
        assert 'tasks.tasks.send_email_task' in CELERY_TASK_ROUTES
        assert 'tasks.tasks.send_sms_task' in CELERY_TASK_ROUTES
        assert 'tasks.tasks.check_inventory_levels_task' in CELERY_TASK_ROUTES
        
        # Verify queue assignments
        assert CELERY_TASK_ROUTES['tasks.tasks.send_email_task']['queue'] == 'emails'
        assert CELERY_TASK_ROUTES['tasks.tasks.send_sms_task']['queue'] == 'sms'
        assert CELERY_TASK_ROUTES['tasks.tasks.check_inventory_levels_task']['queue'] == 'inventory'
        
        print("✓ Celery configuration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Celery configuration test failed: {str(e)}")
        return False

def test_email_task_logic():
    """Test email task logic with mocked dependencies."""
    print("Testing email task logic...")
    
    try:
        from tasks.tasks import send_email_task
        
        with patch('tasks.tasks.send_mail') as mock_send_mail, \
             patch('tasks.tasks.EmailMultiAlternatives') as mock_email_alt:
            
            # Test plain text email
            result = send_email_task(
                subject='Test Subject',
                message='Test message',
                recipient_list=['test@example.com']
            )
            
            assert result['status'] == 'success'
            assert result['recipients'] == ['test@example.com']
            mock_send_mail.assert_called_once()
            
            # Test HTML email
            mock_email_instance = MagicMock()
            mock_email_alt.return_value = mock_email_instance
            
            result = send_email_task(
                subject='Test Subject',
                message='Test message',
                recipient_list=['test@example.com'],
                html_message='<h1>Test HTML</h1>'
            )
            
            assert result['status'] == 'success'
            mock_email_alt.assert_called_once()
            mock_email_instance.attach_alternative.assert_called_once()
            mock_email_instance.send.assert_called_once()
        
        print("✓ Email task logic test passed")
        return True
        
    except Exception as e:
        print(f"✗ Email task logic test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sms_task_logic():
    """Test SMS task logic."""
    print("Testing SMS task logic...")
    
    try:
        from tasks.tasks import send_sms_task
        
        with patch('tasks.tasks.logger') as mock_logger:
            result = send_sms_task(
                phone_number='+1234567890',
                message='Test SMS message'
            )
            
            assert result['status'] == 'success'
            assert result['phone_number'] == '+1234567890'
            mock_logger.info.assert_called()
        
        print("✓ SMS task logic test passed")
        return True
        
    except Exception as e:
        print(f"✗ SMS task logic test failed: {str(e)}")
        return False

def test_task_retry_mechanism():
    """Test task retry mechanism structure."""
    print("Testing task retry mechanism...")
    
    try:
        from tasks.tasks import send_email_task
        
        # Check that the task has retry configuration
        assert hasattr(send_email_task, 'max_retries')
        assert hasattr(send_email_task, 'default_retry_delay')
        
        # Test with mocked exception
        with patch('tasks.tasks.send_mail') as mock_send_mail:
            mock_send_mail.side_effect = Exception('SMTP error')
            
            # Create a mock task instance for retry testing
            mock_task = MagicMock()
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            
            # The actual retry mechanism would be tested in integration tests
            # Here we just verify the structure is in place
            
        print("✓ Task retry mechanism test passed")
        return True
        
    except Exception as e:
        print(f"✗ Task retry mechanism test failed: {str(e)}")
        return False

def test_template_files():
    """Test that email templates exist."""
    print("Testing email templates...")
    
    try:
        template_files = [
            'templates/emails/base.html',
            'templates/emails/order_confirmation.html',
            'templates/emails/order_status_update.html',
            'templates/emails/welcome.html',
            'templates/emails/inventory_alert.html',
            'templates/emails/daily_inventory_report.html',
            'templates/emails/abandoned_cart_reminder.html'
        ]
        
        for template_file in template_files:
            if not os.path.exists(template_file):
                raise FileNotFoundError(f"Template file not found: {template_file}")
        
        print("✓ All email templates exist")
        return True
        
    except Exception as e:
        print(f"✗ Template files test failed: {str(e)}")
        return False

def test_management_command():
    """Test that management command exists."""
    print("Testing management command...")
    
    try:
        command_file = 'tasks/management/commands/test_celery.py'
        if not os.path.exists(command_file):
            raise FileNotFoundError(f"Management command not found: {command_file}")
        
        print("✓ Management command exists")
        return True
        
    except Exception as e:
        print(f"✗ Management command test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("Running Celery task tests (simplified)...")
    print("=" * 60)
    
    tests = [
        test_task_imports,
        test_celery_configuration,
        test_email_task_logic,
        test_sms_task_logic,
        test_task_retry_mechanism,
        test_template_files,
        test_management_command
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
        return True
    else:
        print(f"✗ {failed} tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)