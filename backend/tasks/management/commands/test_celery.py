"""
Management command to test Celery task execution.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.tasks import (
    send_email_task,
    send_sms_task,
    check_inventory_levels_task,
    send_welcome_email,
    cleanup_old_notifications
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test Celery task execution'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['email', 'sms', 'inventory', 'welcome', 'cleanup', 'all'],
            default='all',
            help='Specify which task to test'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run tasks asynchronously (requires Celery worker)'
        )
    
    def handle(self, *args, **options):
        task_type = options['task']
        run_async = options['async']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing Celery tasks (async={run_async})')
        )
        
        if task_type in ['email', 'all']:
            self.test_email_task(run_async)
        
        if task_type in ['sms', 'all']:
            self.test_sms_task(run_async)
        
        if task_type in ['inventory', 'all']:
            self.test_inventory_task(run_async)
        
        if task_type in ['welcome', 'all']:
            self.test_welcome_task(run_async)
        
        if task_type in ['cleanup', 'all']:
            self.test_cleanup_task(run_async)
        
        self.stdout.write(
            self.style.SUCCESS('Task testing completed!')
        )
    
    def test_email_task(self, run_async):
        """Test email sending task."""
        self.stdout.write('Testing email task...')
        
        task_func = send_email_task.delay if run_async else send_email_task
        
        result = task_func(
            subject='Test Email from Celery',
            message='This is a test email sent from a Celery task.',
            recipient_list=['test@example.com']
        )
        
        if run_async:
            self.stdout.write(f'Email task queued with ID: {result.id}')
        else:
            self.stdout.write(f'Email task result: {result}')
    
    def test_sms_task(self, run_async):
        """Test SMS sending task."""
        self.stdout.write('Testing SMS task...')
        
        task_func = send_sms_task.delay if run_async else send_sms_task
        
        result = task_func(
            phone_number='+1234567890',
            message='Test SMS from Celery task'
        )
        
        if run_async:
            self.stdout.write(f'SMS task queued with ID: {result.id}')
        else:
            self.stdout.write(f'SMS task result: {result}')
    
    def test_inventory_task(self, run_async):
        """Test inventory checking task."""
        self.stdout.write('Testing inventory task...')
        
        task_func = check_inventory_levels_task.delay if run_async else check_inventory_levels_task
        
        result = task_func()
        
        if run_async:
            self.stdout.write(f'Inventory task queued with ID: {result.id}')
        else:
            self.stdout.write(f'Inventory task result: {result}')
    
    def test_welcome_task(self, run_async):
        """Test welcome email task."""
        self.stdout.write('Testing welcome email task...')
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='celery_test_user',
            defaults={
                'email': 'celery_test@example.com',
                'first_name': 'Celery',
                'last_name': 'Test'
            }
        )
        
        task_func = send_welcome_email.delay if run_async else send_welcome_email
        
        result = task_func(user.id)
        
        if run_async:
            self.stdout.write(f'Welcome email task queued with ID: {result.id}')
        else:
            self.stdout.write(f'Welcome email task result: {result}')
    
    def test_cleanup_task(self, run_async):
        """Test notification cleanup task."""
        self.stdout.write('Testing cleanup task...')
        
        task_func = cleanup_old_notifications.delay if run_async else cleanup_old_notifications
        
        result = task_func(days_old=30)
        
        if run_async:
            self.stdout.write(f'Cleanup task queued with ID: {result.id}')
        else:
            self.stdout.write(f'Cleanup task result: {result}')