"""
Management command to clean up old logs from the database.
"""
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.logs.models import SystemLog, SecurityEvent, PerformanceMetric, BusinessMetric


class Command(BaseCommand):
    help = 'Clean up old logs from the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete logs older than this many days'
        )
        parser.add_argument(
            '--log-type',
            type=str,
            choices=['system', 'security', 'performance', 'business', 'all'],
            default='all',
            help='Type of logs to clean up'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        log_type = options['log_type']
        dry_run = options['dry_run']
        
        # Calculate the cutoff date
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        self.stdout.write(f"Cleaning up logs older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No logs will be deleted"))
        
        # Clean up the requested log types
        if log_type in ['system', 'all']:
            count = self.cleanup_logs(SystemLog, cutoff_date, dry_run)
            self.stdout.write(f"System logs: {count} deleted")
        
        if log_type in ['security', 'all']:
            count = self.cleanup_logs(SecurityEvent, cutoff_date, dry_run)
            self.stdout.write(f"Security events: {count} deleted")
        
        if log_type in ['performance', 'all']:
            count = self.cleanup_logs(PerformanceMetric, cutoff_date, dry_run)
            self.stdout.write(f"Performance metrics: {count} deleted")
        
        if log_type in ['business', 'all']:
            count = self.cleanup_logs(BusinessMetric, cutoff_date, dry_run)
            self.stdout.write(f"Business metrics: {count} deleted")
        
        self.stdout.write(self.style.SUCCESS('Log cleanup complete!'))
    
    def cleanup_logs(self, model, cutoff_date, dry_run):
        """
        Clean up logs of a specific type older than the cutoff date.
        
        Args:
            model: The model class to clean up
            cutoff_date: Delete logs older than this date
            dry_run: If True, don't actually delete anything
        
        Returns:
            The number of logs that were (or would be) deleted
        """
        # Get the count of logs to delete
        count = model.objects.filter(timestamp__lt=cutoff_date).count()
        
        if not dry_run and count > 0:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                model.objects.filter(timestamp__lt=cutoff_date).delete()
        
        return count