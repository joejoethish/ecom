from django.core.management.base import BaseCommand
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Clean up old notifications to manage database size'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Age of notifications to clean up (in days)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        if dry_run:
            from django.utils import timezone
            from datetime import timedelta
            from apps.notifications.models import Notification
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            old_notifications = Notification.objects.filter(
                created_at__lt=cutoff_date
            ).exclude(
                channel='IN_APP',
                status__in=['PENDING', 'SENT', 'DELIVERED']
            )
            
            count = old_notifications.count()
            
            self.stdout.write(
                self.style.SUCCESS(f'Would delete {count} old notifications (older than {days} days)')
            )
            return
        
        service = NotificationService()
        service.cleanup_old_notifications(days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up old notifications (older than {days} days)')
        )