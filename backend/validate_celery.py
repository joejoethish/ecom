#!/usr/bin/env python
"""
Validation script for Celery infrastructure implementation.
This script validates that all required components are in place.
"""
import os
import sys

def validate_file_structure():
    """Validate that all required files exist."""
    print("Validating file structure...")
    
    required_files = [
        'tasks/__init__.py',
        'tasks/tasks.py',
        'tasks/schedules.py',
        'tasks/tests.py',
        'tasks/management/__init__.py',
        'tasks/management/commands/__init__.py',
        'tasks/management/commands/test_celery.py',
        'templates/emails/base.html',
        'templates/emails/order_confirmation.html',
        'templates/emails/order_status_update.html',
        'templates/emails/welcome.html',
        'templates/emails/inventory_alert.html',
        'templates/emails/daily_inventory_report.html',
        'templates/emails/abandoned_cart_reminder.html',
        'ecommerce_project/celery.py',
        'ecommerce_project/settings/testing.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files exist")
        return True

def validate_task_definitions():
    """Validate task function definitions."""
    print("Validating task definitions...")
    
    try:
        # Read tasks.py file
        with open('tasks/tasks.py', 'r') as f:
            content = f.read()
        
        required_tasks = [
            'send_email_task',
            'send_sms_task',
            'check_inventory_levels_task',
            'send_order_confirmation_email',
            'send_order_status_update_notification',
            'send_welcome_email',
            'process_inventory_transaction',
            'cleanup_old_notifications',
            'send_daily_inventory_report',
            'sync_payment_status_task',
            'send_abandoned_cart_reminders'
        ]
        
        missing_tasks = []
        for task in required_tasks:
            if f'def {task}(' not in content:
                missing_tasks.append(task)
        
        if missing_tasks:
            print(f"✗ Missing task definitions: {missing_tasks}")
            return False
        else:
            print("✓ All required tasks are defined")
            return True
            
    except Exception as e:
        print(f"✗ Error reading tasks.py: {str(e)}")
        return False

def validate_celery_configuration():
    """Validate Celery configuration."""
    print("Validating Celery configuration...")
    
    try:
        # Read schedules.py file
        with open('tasks/schedules.py', 'r') as f:
            content = f.read()
        
        required_configs = [
            'CELERY_BEAT_SCHEDULE',
            'CELERY_TASK_ROUTES',
            'CELERY_TASK_QUEUES'
        ]
        
        missing_configs = []
        for config in required_configs:
            if config not in content:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"✗ Missing Celery configurations: {missing_configs}")
            return False
        else:
            print("✓ Celery configuration is complete")
            return True
            
    except Exception as e:
        print(f"✗ Error reading schedules.py: {str(e)}")
        return False

def validate_email_templates():
    """Validate email template structure."""
    print("Validating email templates...")
    
    try:
        # Check base template
        with open('templates/emails/base.html', 'r') as f:
            base_content = f.read()
        
        if '{% block content %}' not in base_content:
            print("✗ Base template missing content block")
            return False
        
        # Check that other templates extend base
        template_files = [
            'templates/emails/order_confirmation.html',
            'templates/emails/welcome.html',
            'templates/emails/inventory_alert.html'
        ]
        
        for template_file in template_files:
            with open(template_file, 'r') as f:
                content = f.read()
            
            if '{% extends "emails/base.html" %}' not in content:
                print(f"✗ Template {template_file} doesn't extend base template")
                return False
        
        print("✓ Email templates are properly structured")
        return True
        
    except Exception as e:
        print(f"✗ Error validating templates: {str(e)}")
        return False

def validate_django_integration():
    """Validate Django integration."""
    print("Validating Django integration...")
    
    try:
        # Check celery.py configuration
        with open('ecommerce_project/celery.py', 'r') as f:
            celery_content = f.read()
        
        required_celery_configs = [
            'from tasks.schedules import',
            'app.conf.beat_schedule',
            'app.conf.task_routes'
        ]
        
        for config in required_celery_configs:
            if config not in celery_content:
                print(f"✗ Missing Celery configuration: {config}")
                return False
        
        # Check settings integration
        with open('ecommerce_project/settings/base.py', 'r') as f:
            settings_content = f.read()
        
        if "'tasks'," not in settings_content:
            print("✗ Tasks app not registered in Django settings")
            return False
        
        if 'CELERY_BROKER_URL' not in settings_content:
            print("✗ Celery broker configuration missing")
            return False
        
        print("✓ Django integration is complete")
        return True
        
    except Exception as e:
        print(f"✗ Error validating Django integration: {str(e)}")
        return False

def validate_task_features():
    """Validate task features and capabilities."""
    print("Validating task features...")
    
    try:
        with open('tasks/tasks.py', 'r') as f:
            content = f.read()
        
        required_features = [
            '@shared_task',  # Celery task decorator
            'bind=True',     # Task binding for retry
            'max_retries',   # Retry configuration
            'self.retry',    # Retry mechanism
            'logger.',       # Logging
            'render_to_string',  # Template rendering
            'send_mail',     # Email sending
            'EmailMultiAlternatives'  # HTML email support
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"✗ Missing task features: {missing_features}")
            return False
        else:
            print("✓ All required task features are implemented")
            return True
            
    except Exception as e:
        print(f"✗ Error validating task features: {str(e)}")
        return False

def main():
    """Run all validations."""
    print("Celery Infrastructure Validation")
    print("=" * 50)
    
    validations = [
        validate_file_structure,
        validate_task_definitions,
        validate_celery_configuration,
        validate_email_templates,
        validate_django_integration,
        validate_task_features
    ]
    
    passed = 0
    failed = 0
    
    for validation in validations:
        try:
            if validation():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Validation {validation.__name__} failed: {str(e)}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ Celery infrastructure implementation is complete!")
        print("\nNext steps:")
        print("1. Start Redis server: redis-server")
        print("2. Start Celery worker: celery -A ecommerce_project worker -l info")
        print("3. Start Celery beat: celery -A ecommerce_project beat -l info")
        print("4. Test tasks using the management command")
        return True
    else:
        print(f"✗ {failed} validations failed. Please fix the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)