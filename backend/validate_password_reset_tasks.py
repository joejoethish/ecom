#!/usr/bin/env python
"""
Validation script to check password reset tasks implementation.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def validate_implementation():
    """Validate the password reset tasks implementation."""
    print("Validating Password Reset Tasks Implementation")
    print("=" * 60)
    
    # Test 1: Import tasks module
    print("1. Testing task imports...")
    try:
        from apps.authentication.tasks import (
            cleanup_expired_password_reset_tokens,
            cleanup_old_password_reset_attempts,
            monitor_password_reset_token_performance,
            send_password_reset_security_alert
        )
        print("   ✓ All task functions imported successfully")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: Import management commands
    print("\n2. Testing management command imports...")
    try:
        from apps.authentication.management.commands.cleanup_password_reset_tokens import Command as CleanupCommand
        from apps.authentication.management.commands.password_reset_stats import Command as StatsCommand
        from apps.authentication.management.commands.invalidate_password_reset_tokens import Command as InvalidateCommand
        print("   ✓ All management commands imported successfully")
    except ImportError as e:
        print(f"   ✗ Management command import error: {e}")
        return False
    
    # Test 3: Check models
    print("\n3. Testing model imports...")
    try:
        from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
        print("   ✓ Password reset models imported successfully")
        
        # Check model fields
        token_fields = [f.name for f in PasswordResetToken._meta.fields]
        required_token_fields = ['user', 'token_hash', 'expires_at', 'is_used', 'ip_address']
        for field in required_token_fields:
            if field in token_fields:
                print(f"   ✓ PasswordResetToken has {field} field")
            else:
                print(f"   ✗ PasswordResetToken missing {field} field")
                return False
        
        attempt_fields = [f.name for f in PasswordResetAttempt._meta.fields]
        required_attempt_fields = ['ip_address', 'email', 'success']
        for field in required_attempt_fields:
            if field in attempt_fields:
                print(f"   ✓ PasswordResetAttempt has {field} field")
            else:
                print(f"   ✗ PasswordResetAttempt missing {field} field")
                return False
                
    except ImportError as e:
        print(f"   ✗ Model import error: {e}")
        return False
    
    # Test 4: Check task schedules
    print("\n4. Testing task schedule configuration...")
    try:
        from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
        
        # Check if our tasks are in the schedule
        expected_scheduled_tasks = [
            'cleanup-password-reset-tokens',
            'cleanup-password-reset-attempts',
            'monitor-password-reset-performance'
        ]
        
        for task_name in expected_scheduled_tasks:
            if task_name in CELERY_BEAT_SCHEDULE:
                print(f"   ✓ {task_name} is scheduled")
            else:
                print(f"   ✗ {task_name} not found in schedule")
                return False
        
        # Check if our tasks are in the routes
        expected_routed_tasks = [
            'apps.authentication.tasks.cleanup_expired_password_reset_tokens',
            'apps.authentication.tasks.cleanup_old_password_reset_attempts',
            'apps.authentication.tasks.monitor_password_reset_token_performance',
            'apps.authentication.tasks.send_password_reset_security_alert'
        ]
        
        for task_name in expected_routed_tasks:
            if task_name in CELERY_TASK_ROUTES:
                print(f"   ✓ {task_name} is routed")
            else:
                print(f"   ✗ {task_name} not found in routes")
                return False
                
    except ImportError as e:
        print(f"   ✗ Schedule import error: {e}")
        return False
    
    # Test 5: Check email template
    print("\n5. Testing email template...")
    try:
        from django.template.loader import get_template
        template = get_template('emails/security_alert.html')
        print("   ✓ Security alert email template exists")
    except Exception as e:
        print(f"   ✗ Email template error: {e}")
        return False
    
    # Test 6: Test task function signatures
    print("\n6. Testing task function signatures...")
    try:
        import inspect
        
        # Check cleanup_expired_password_reset_tokens
        sig = inspect.signature(cleanup_expired_password_reset_tokens)
        # Celery bind=True removes self from signature but adds it at runtime
        if len(sig.parameters) == 0:  # No parameters visible in signature due to bind=True
            print("   ✓ cleanup_expired_password_reset_tokens has correct signature")
        else:
            print("   ✗ cleanup_expired_password_reset_tokens has incorrect signature")
            return False
        
        # Check cleanup_old_password_reset_attempts
        sig = inspect.signature(cleanup_old_password_reset_attempts)
        if 'days_old' in sig.parameters:  # self is hidden by bind=True
            print("   ✓ cleanup_old_password_reset_attempts has correct signature")
        else:
            print("   ✗ cleanup_old_password_reset_attempts has incorrect signature")
            return False
        
        # Check monitor_password_reset_token_performance
        sig = inspect.signature(monitor_password_reset_token_performance)
        if len(sig.parameters) == 0:  # No parameters visible due to bind=True
            print("   ✓ monitor_password_reset_token_performance has correct signature")
        else:
            print("   ✗ monitor_password_reset_token_performance has incorrect signature")
            return False
        
        # Check send_password_reset_security_alert
        sig = inspect.signature(send_password_reset_security_alert)
        if 'alert_type' in sig.parameters and 'details' in sig.parameters:  # self is hidden by bind=True
            print("   ✓ send_password_reset_security_alert has correct signature")
        else:
            print("   ✗ send_password_reset_security_alert has incorrect signature")
            return False
            
    except Exception as e:
        print(f"   ✗ Function signature error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All validation checks passed!")
    print("\nImplementation Summary:")
    print("• 4 Celery tasks created for token cleanup and monitoring")
    print("• 3 management commands created for manual token management")
    print("• Tasks scheduled in Celery beat configuration")
    print("• Email template created for security alerts")
    print("• All tasks properly routed to appropriate queues")
    
    return True

if __name__ == '__main__':
    success = validate_implementation()
    sys.exit(0 if success else 1)