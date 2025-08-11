from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.performance.models import PerformanceMetric, DatabasePerformanceLog, ApplicationPerformanceMonitor
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old performance monitoring data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--metrics-days',
            type=int,
            default=30,
            help='Keep performance metrics for N days (default: 30)'
        )
        parser.add_argument(
            '--db-logs-days',
            type=int,
            default=7,
            help='Keep database logs for N days (default: 7)'
        )
        parser.add_argument(
            '--apm-days',
            type=int,
            default=14,
            help='Keep APM data for N days (default: 14)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        metrics_days = options['metrics_days']
        db_logs_days = options['db_logs_days']
        apm_days = options['apm_days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))
        
        self.stdout.write('Starting performance data cleanup...')
        
        try:
            # Clean up performance metrics
            metrics_cutoff = timezone.now() - timedelta(days=metrics_days)
            old_metrics = PerformanceMetric.objects.filter(
                timestamp__lt=metrics_cutoff
            ).exclude(severity='critical')  # Keep critical metrics longer
            
            metrics_count = old_metrics.count()
            self.stdout.write(f'Found {metrics_count} old performance metrics to delete')
            
            if not dry_run and metrics_count > 0:
                old_metrics.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {metrics_count} performance metrics')
                )
            
            # Clean up database logs
            db_cutoff = timezone.now() - timedelta(days=db_logs_days)
            old_db_logs = DatabasePerformanceLog.objects.filter(
                timestamp__lt=db_cutoff
            ).exclude(is_slow_query=True)  # Keep slow queries longer
            
            db_count = old_db_logs.count()
            self.stdout.write(f'Found {db_count} old database logs to delete')
            
            if not dry_run and db_count > 0:
                old_db_logs.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {db_count} database logs')
                )
            
            # Clean up APM data
            apm_cutoff = timezone.now() - timedelta(days=apm_days)
            old_apm = ApplicationPerformanceMonitor.objects.filter(
                start_time__lt=apm_cutoff
            ).exclude(status_code__gte=400)  # Keep error transactions longer
            
            apm_count = old_apm.count()
            self.stdout.write(f'Found {apm_count} old APM records to delete')
            
            if not dry_run and apm_count > 0:
                old_apm.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {apm_count} APM records')
                )
            
            # Summary
            total_deleted = metrics_count + db_count + apm_count
            if dry_run:
                self.stdout.write(f'Would delete {total_deleted} total records')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Cleanup completed. Deleted {total_deleted} total records')
                )
                
        except Exception as e:
            logger.error(f'Error during performance data cleanup: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {e}')
            )