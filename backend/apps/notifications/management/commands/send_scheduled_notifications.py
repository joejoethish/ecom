from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Send scheduled notifications that are due'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get notifications that are scheduled and due
        now = timezone.now()
        scheduled_notifications = Notification.objects.filter(
            status='PENDING',
            scheduled_at__lte=now,
            scheduled_at__isnull=False
        ).exclude(
            expires_at__lt=now
        )
        
        count = scheduled_notifications.count()
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Would send {count} scheduled notifications')
            )
            for notification in scheduled_notifications:
                self.stdout.write(
                    f'  - {notification.user.username}: {notification.subject} ({notification.channel})'
                )
            return
        
        if count == 0:
            self.stdout.write('No scheduled notifications to send')
            return
        
        service = NotificationService()
        sent_count = 0
        failed_count = 0
        
        for notification in scheduled_notifications:
            try:
                service._send_notification(notification)
                if notification.status == 'SENT':
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error sending notification {notification.id}: {str(e)}')
                )
                failed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processed {count} scheduled notifications: '
                f'{sent_count} sent, {failed_count} failed'
            )
        )