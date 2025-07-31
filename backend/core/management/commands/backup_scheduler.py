"""
Django management command for backup scheduler control

This command provides control over the backup scheduler service including:
- Starting and stopping the scheduler
- Getting scheduler status
- Force running specific backup operations

Usage:
    python manage.py backup_scheduler start
    python manage.py backup_scheduler stop
    python manage.py backup_scheduler status
    python manage.py backup_scheduler force_full
    python manage.py backup_scheduler force_incremental
    python manage.py backup_scheduler force_cleanup
"""

import time
import signal
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.backup_scheduler import (
    get_backup_scheduler, 
    initialize_backup_scheduler,
    start_backup_scheduler,
    stop_backup_scheduler
)


class Command(BaseCommand):
    help = 'Control the backup scheduler service'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Scheduler actions')
        
        # Start scheduler
        start_parser = subparsers.add_parser('start', help='Start the backup scheduler')
        start_parser.add_argument(
            '--foreground',
            action='store_true',
            help='Run scheduler in foreground (blocks until stopped)'
        )
        
        # Stop scheduler
        stop_parser = subparsers.add_parser('stop', help='Stop the backup scheduler')
        
        # Status
        status_parser = subparsers.add_parser('status', help='Show scheduler status')
        
        # Force operations
        force_full_parser = subparsers.add_parser('force_full', help='Force immediate full backup')
        force_incr_parser = subparsers.add_parser('force_incremental', help='Force immediate incremental backup')
        force_cleanup_parser = subparsers.add_parser('force_cleanup', help='Force immediate cleanup')
        
        # Test scheduler
        test_parser = subparsers.add_parser('test', help='Test scheduler functionality')

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'backup_scheduler')
            return
        
        try:
            if action == 'start':
                self.handle_start(options)
            elif action == 'stop':
                self.handle_stop(options)
            elif action == 'status':
                self.handle_status(options)
            elif action == 'force_full':
                self.handle_force_full(options)
            elif action == 'force_incremental':
                self.handle_force_incremental(options)
            elif action == 'force_cleanup':
                self.handle_force_cleanup(options)
            elif action == 'test':
                self.handle_test(options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            raise CommandError(f"Scheduler operation failed: {e}")

    def handle_start(self, options):
        """Start the backup scheduler"""
        foreground = options.get('foreground', False)
        
        # Check if scheduler is enabled
        if not getattr(settings, 'BACKUP_SCHEDULER_ENABLED', True):
            raise CommandError("Backup scheduler is disabled in settings")
        
        # Initialize and start scheduler
        scheduler = get_backup_scheduler()
        if not scheduler:
            scheduler = initialize_backup_scheduler()
        
        if not scheduler:
            raise CommandError("Failed to initialize backup scheduler")
        
        if scheduler.running:
            self.stdout.write(
                self.style.WARNING("Backup scheduler is already running")
            )
            return
        
        scheduler.start()
        self.stdout.write(
            self.style.SUCCESS("Backup scheduler started successfully")
        )
        
        if foreground:
            self.stdout.write("Running in foreground mode. Press Ctrl+C to stop.")
            
            def signal_handler(signum, frame):
                self.stdout.write("\nStopping backup scheduler...")
                scheduler.stop()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            try:
                while scheduler.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write("\nStopping backup scheduler...")
                scheduler.stop()

    def handle_stop(self, options):
        """Stop the backup scheduler"""
        scheduler = get_backup_scheduler()
        
        if not scheduler:
            self.stdout.write(
                self.style.WARNING("Backup scheduler is not initialized")
            )
            return
        
        if not scheduler.running:
            self.stdout.write(
                self.style.WARNING("Backup scheduler is not running")
            )
            return
        
        scheduler.stop()
        self.stdout.write(
            self.style.SUCCESS("Backup scheduler stopped successfully")
        )

    def handle_status(self, options):
        """Show scheduler status"""
        scheduler = get_backup_scheduler()
        
        if not scheduler:
            self.stdout.write("Backup scheduler: Not initialized")
            return
        
        status = scheduler.get_scheduler_status()
        
        self.stdout.write("Backup Scheduler Status:")
        self.stdout.write(f"  Running: {'Yes' if status['running'] else 'No'}")
        
        # Show schedule configuration
        schedule = status['schedule_config']
        self.stdout.write(f"  Full Backup Time: {schedule['full_backup_time']}")
        self.stdout.write(f"  Incremental Interval: {schedule['incremental_interval_hours']} hours")
        self.stdout.write(f"  Cleanup Time: {schedule['cleanup_time']}")
        self.stdout.write(f"  Health Check Interval: {schedule['health_check_interval_minutes']} minutes")
        
        # Show last operations
        self.stdout.write("\nLast Operations:")
        for operation, timestamp in status['last_operations'].items():
            if timestamp:
                self.stdout.write(f"  {operation.replace('_', ' ').title()}: {timestamp}")
            else:
                self.stdout.write(f"  {operation.replace('_', ' ').title()}: Never")
        
        # Show failure counts
        self.stdout.write("\nFailure Counts:")
        for operation, count in status['failure_counts'].items():
            if count > 0:
                style = self.style.ERROR if count >= 3 else self.style.WARNING
                self.stdout.write(style(f"  {operation.replace('_', ' ').title()}: {count}"))
            else:
                self.stdout.write(f"  {operation.replace('_', ' ').title()}: {count}")
        
        # Get backup system status
        try:
            backup_status = scheduler.backup_manager.get_backup_status()
            self.stdout.write("\nBackup System Status:")
            self.stdout.write(f"  Total Backups: {backup_status['total_backups']}")
            self.stdout.write(f"  Storage Used: {backup_status['total_size_gb']} GB")
            
            if backup_status.get('recent_full_backup'):
                self.stdout.write(self.style.SUCCESS("  ✓ Recent full backup available"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ No recent full backup"))
            
            if backup_status.get('recent_incremental_backup'):
                self.stdout.write(self.style.SUCCESS("  ✓ Recent incremental backup available"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ No recent incremental backup"))
                
        except Exception as e:
            self.stdout.write(f"  Error getting backup status: {e}")

    def handle_force_full(self, options):
        """Force immediate full backup"""
        scheduler = get_backup_scheduler()
        
        if not scheduler:
            raise CommandError("Backup scheduler is not initialized")
        
        self.stdout.write("Starting forced full backup...")
        
        success = scheduler.force_full_backup()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Full backup completed successfully")
            )
        else:
            raise CommandError("Full backup failed")

    def handle_force_incremental(self, options):
        """Force immediate incremental backup"""
        scheduler = get_backup_scheduler()
        
        if not scheduler:
            raise CommandError("Backup scheduler is not initialized")
        
        self.stdout.write("Starting forced incremental backup...")
        
        success = scheduler.force_incremental_backup()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Incremental backup completed successfully")
            )
        else:
            raise CommandError("Incremental backup failed")

    def handle_force_cleanup(self, options):
        """Force immediate cleanup"""
        scheduler = get_backup_scheduler()
        
        if not scheduler:
            raise CommandError("Backup scheduler is not initialized")
        
        self.stdout.write("Starting forced cleanup...")
        
        success = scheduler.force_cleanup()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Cleanup completed successfully")
            )
        else:
            raise CommandError("Cleanup failed")

    def handle_test(self, options):
        """Test scheduler functionality"""
        self.stdout.write("Testing backup scheduler functionality...")
        
        try:
            # Initialize scheduler
            scheduler = initialize_backup_scheduler()
            if not scheduler:
                raise Exception("Failed to initialize scheduler")
            
            self.stdout.write("✓ Scheduler initialization: OK")
            
            # Test configuration
            status = scheduler.get_scheduler_status()
            if 'running' not in status:
                raise Exception("Invalid scheduler status")
            
            self.stdout.write("✓ Status reporting: OK")
            
            # Test backup manager
            backup_status = scheduler.backup_manager.get_backup_status()
            if 'total_backups' not in backup_status:
                raise Exception("Invalid backup status")
            
            self.stdout.write("✓ Backup manager: OK")
            
            self.stdout.write(
                self.style.SUCCESS("All scheduler tests passed!")
            )
            
        except Exception as e:
            raise CommandError(f"Scheduler test failed: {e}")