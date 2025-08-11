from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.caching.models import CacheMetrics, CacheInvalidation, CacheAlert
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old cache data and metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Keep data newer than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--metrics-only',
            action='store_true',
            help='Only clean up metrics data'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        days = options.get('days', 30)
        dry_run = options.get('dry_run', False)
        metrics_only = options.get('metrics_only', False)
        verbose = options.get('verbose', False)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        try:
            total_deleted = 0
            
            # Clean up old metrics
            old_metrics = CacheMetrics.objects.filter(timestamp__lt=cutoff_date)
            metrics_count = old_metrics.count()
            
            if verbose:
                self.stdout.write(f'Found {metrics_count} old metrics records')
            
            if not dry_run:
                deleted_metrics = old_metrics.delete()[0]
                total_deleted += deleted_metrics
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {deleted_metrics} old metrics records')
                )
            else:
                self.stdout.write(f'Would delete {metrics_count} metrics records')
            
            if not metrics_only:
                # Clean up old invalidation records
                old_invalidations = CacheInvalidation.objects.filter(timestamp__lt=cutoff_date)
                invalidations_count = old_invalidations.count()
                
                if verbose:
                    self.stdout.write(f'Found {invalidations_count} old invalidation records')
                
                if not dry_run:
                    deleted_invalidations = old_invalidations.delete()[0]
                    total_deleted += deleted_invalidations
                    self.stdout.write(
                        self.style.SUCCESS(f'Deleted {deleted_invalidations} old invalidation records')
                    )
                else:
                    self.stdout.write(f'Would delete {invalidations_count} invalidation records')
                
                # Clean up resolved alerts older than cutoff
                old_alerts = CacheAlert.objects.filter(
                    created_at__lt=cutoff_date,
                    is_resolved=True
                )
                alerts_count = old_alerts.count()
                
                if verbose:
                    self.stdout.write(f'Found {alerts_count} old resolved alerts')
                
                if not dry_run:
                    deleted_alerts = old_alerts.delete()[0]
                    total_deleted += deleted_alerts
                    self.stdout.write(
                        self.style.SUCCESS(f'Deleted {deleted_alerts} old resolved alerts')
                    )
                else:
                    self.stdout.write(f'Would delete {alerts_count} resolved alerts')
            
            # Summary
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'Dry run completed. Would delete {metrics_count + (invalidations_count if not metrics_only else 0) + (alerts_count if not metrics_only else 0)} total records')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Cleanup completed. Deleted {total_deleted} total records')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Cleanup failed: {e}')
            )
            logger.error(f'Cache cleanup failed: {e}')