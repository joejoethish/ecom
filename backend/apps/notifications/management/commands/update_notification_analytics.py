from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.notifications.services import NotificationAnalyticsService


class Command(BaseCommand):
    help = 'Update notification analytics for specified date range'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to update analytics for (YYYY-MM-DD format)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to update analytics for',
        )
    
    def handle(self, *args, **options):
        service = NotificationAnalyticsService()
        
        if options['date']:
            # Update for specific date
            try:
                date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                service.update_daily_analytics(date)
                self.stdout.write(
                    self.style.SUCCESS(f'Updated analytics for {date}')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            # Update for last N days
            days_back = options['days_back']
            today = timezone.now().date()
            
            for i in range(days_back):
                date = today - timedelta(days=i)
                service.update_daily_analytics(date)
                self.stdout.write(f'Updated analytics for {date}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated analytics for last {days_back} days')
            )