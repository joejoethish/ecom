from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Retry failed notifications that can be retried'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Maximum age of failed notifications to retry (in hours)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be retried without actually retrying',
        )
    
    def handle(self, *args, **options):
        max_age_hours = options['max_age_hours']
        dry_run = options['dry_run']
        
        service = NotificationService()
        
        if dry_run:
            cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
            from apps.notifications.models import Notification
            
            failed_notifications = Notification.objects.filter(
                status='FAILED',
                created_at__gte=cutoff_time
            )
            
            retryable_count = sum(1 for n in failed_notifications if n.can_retry())
            
            self.stdout.write(
                self.style.SUCCESS(f'Would retry {retryable_count} failed notifications')
            )
            
            for notification in failed_notifications:
                if notification.can_retry():
                    self.stdout.write(
                        f'  - {notification.user.username}: {notification.subject} '
                        f'({notification.channel}) - Retry {notification.retry_count + 1}'
                    )
            return
        
        # Actually retry failed notifications
        initial_count = service.retry_failed_notifications(max_age_hours)
        
        self.stdout.write(
            self.style.SUCCESS(f'Retried failed notifications (max age: {max_age_hours} hours)')
        )