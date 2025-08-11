from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.performance.utils import AlertManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check performance thresholds and create alerts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Send notifications for new alerts'
        )
    
    def handle(self, *args, **options):
        send_notifications = options['send_notifications']
        
        self.stdout.write('Checking performance thresholds...')
        
        try:
            # Check thresholds and create alerts
            alerts = AlertManager.check_thresholds()
            
            if alerts:
                self.stdout.write(
                    self.style.SUCCESS(f'Created {len(alerts)} new alerts')
                )
                
                for alert in alerts:
                    self.stdout.write(f'  - {alert.name} ({alert.severity})')
                    
                    # Send notifications if requested
                    if send_notifications:
                        AlertManager.send_alert_notifications(alert)
            else:
                self.stdout.write('No new alerts created')
                
        except Exception as e:
            logger.error(f'Error checking performance alerts: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error checking alerts: {e}')
            )