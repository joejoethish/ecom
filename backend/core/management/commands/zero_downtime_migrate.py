"""
Django management command for zero-downtime database migration.
Provides command-line interface for executing staged migration with monitoring.
"""
import os
import sys
import json
import time
import signal
import threading
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache

from core.zero_downtime_migration import (
    ZeroDowntimeMigrationService,
    MigrationStage,
    MigrationMonitor
)


class Command(BaseCommand):
    """Django management command for zero-downtime migration"""
    
    help = 'Execute zero-downtime migration from SQLite to MySQL'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.migration_service = None
        self.monitoring_thread = None
        self.should_stop = False
    
    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--sqlite-path',
            type=str,
            default=None,
            help='Path to SQLite database file (default: settings.DATABASES default)'
        )
        
        parser.add_argument(
            '--mysql-host',
            type=str,
            default='localhost',
            help='MySQL host (default: localhost)'
        )
        
        parser.add_argument(
            '--mysql-port',
            type=int,
            default=3306,
            help='MySQL port (default: 3306)'
        )
        
        parser.add_argument(
            '--mysql-user',
            type=str,
            required=True,
            help='MySQL username'
        )
        
        parser.add_argument(
            '--mysql-password',
            type=str,
            required=True,
            help='MySQL password'
        )
        
        parser.add_argument(
            '--mysql-database',
            type=str,
            required=True,
            help='MySQL database name'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without actual migration'
        )
        
        parser.add_argument(
            '--monitor-interval',
            type=int,
            default=5,
            help='Progress monitoring interval in seconds (default: 5)'
        )
        
        parser.add_argument(
            '--log-file',
            type=str,
            default=None,
            help='Log file path for detailed progress logging'
        )
        
        parser.add_argument(
            '--web-monitoring',
            action='store_true',
            help='Enable web-based monitoring via Django cache'
        )
        
        parser.add_argument(
            '--max-errors',
            type=int,
            default=5,
            help='Maximum errors before triggering rollback (default: 5)'
        )
        
        parser.add_argument(
            '--max-time-hours',
            type=int,
            default=24,
            help='Maximum migration time in hours before rollback (default: 24)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if validation warnings exist'
        )
        
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show status of running migration'
        )
        
        parser.add_argument(
            '--stop',
            action='store_true',
            help='Stop running migration gracefully'
        )
        
        parser.add_argument(
            '--rollback',
            action='store_true',
            help='Trigger immediate rollback of running migration'
        )
    
    def handle(self, *args, **options):
        """Handle command execution"""
        try:
            # Handle status/control commands first
            if options['status']:
                return self.show_migration_status()
            
            if options['stop']:
                return self.stop_migration()
            
            if options['rollback']:
                return self.trigger_rollback()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Validate arguments
            self.validate_arguments(options)
            
            # Create MySQL configuration
            mysql_config = {
                'host': options['mysql_host'],
                'port': options['mysql_port'],
                'user': options['mysql_user'],
                'password': options['mysql_password'],
                'database': options['mysql_database'],
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False
            }
            
            # Create migration service
            self.migration_service = ZeroDowntimeMigrationService(
                sqlite_path=options['sqlite_path'],
                mysql_config=mysql_config
            )
            
            # Configure rollback triggers
            self.migration_service.rollback_triggers.update({
                'max_errors': options['max_errors'],
                'max_migration_time_hours': options['max_time_hours']
            })
            
            # Setup monitoring
            self.setup_monitoring(options)
            
            # Perform pre-migration validation
            if not options['force']:
                if not self.pre_migration_validation():
                    raise CommandError("Pre-migration validation failed. Use --force to override.")
            
            # Execute migration
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING("DRY RUN MODE - No actual migration will be performed")
                )
                return self.dry_run_migration()
            else:
                return self.execute_migration()
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nMigration interrupted by user"))
            if self.migration_service:
                self.migration_service.stop_migration()
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Migration failed: {e}"))
            raise CommandError(str(e))
        finally:
            self.cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.WARNING(f"\nReceived signal {signum}, stopping migration..."))
        self.should_stop = True
        if self.migration_service:
            self.migration_service.stop_migration()
    
    def validate_arguments(self, options):
        """Validate command line arguments"""
        # Check SQLite path
        sqlite_path = options['sqlite_path']
        if not sqlite_path:
            # Try to get from Django settings
            default_db = settings.DATABASES.get('default', {})
            if default_db.get('ENGINE') == 'django.db.backends.sqlite3':
                sqlite_path = default_db.get('NAME')
            
            if not sqlite_path:
                raise CommandError("SQLite path not specified and cannot be determined from settings")
        
        if not os.path.exists(sqlite_path):
            raise CommandError(f"SQLite database file not found: {sqlite_path}")
        
        # Validate log file path
        if options['log_file']:
            log_dir = os.path.dirname(options['log_file'])
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir)
                except OSError as e:
                    raise CommandError(f"Cannot create log directory: {e}")
    
    def setup_monitoring(self, options):
        """Setup migration monitoring"""
        # Console monitoring (always enabled)
        self.migration_service.add_progress_callback(self.console_progress_callback)
        self.migration_service.add_checkpoint_callback(self.console_checkpoint_callback)
        self.migration_service.add_error_callback(self.console_error_callback)
        
        # File logging
        if options['log_file']:
            file_callback = MigrationMonitor.file_progress_callback(options['log_file'])
            self.migration_service.add_progress_callback(file_callback)
        
        # Web monitoring via cache
        if options['web_monitoring']:
            cache_key = f"migration_progress_{self.migration_service.migration_id}"
            cache_callback = MigrationMonitor.cache_progress_callback(cache_key)
            self.migration_service.add_progress_callback(cache_callback)
            
            self.stdout.write(
                self.style.SUCCESS(f"Web monitoring enabled. Cache key: {cache_key}")
            )
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self.monitoring_loop,
            args=(options['monitor_interval'],)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def console_progress_callback(self, metrics):
        """Console progress callback"""
        stage_name = metrics.stage.value.replace('_', ' ').title()
        progress_bar = self.create_progress_bar(metrics.progress_percentage)
        
        eta_str = "N/A"
        if metrics.estimated_completion:
            eta_str = metrics.estimated_completion.strftime('%H:%M:%S')
        
        # Clear line and write progress
        sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line
        sys.stdout.write(
            f"[{stage_name}] {progress_bar} {metrics.progress_percentage:.1f}% "
            f"({metrics.records_migrated:,}/{metrics.total_records:,}) "
            f"Speed: {metrics.migration_speed:.0f} rec/s "
            f"ETA: {eta_str}"
        )
        sys.stdout.flush()
    
    def console_checkpoint_callback(self, checkpoint):
        """Console checkpoint callback"""
        status_color = self.style.SUCCESS if checkpoint.status == 'passed' else self.style.ERROR
        stage_name = checkpoint.stage.value.replace('_', ' ').title()
        
        # New line for checkpoint
        sys.stdout.write('\n')
        self.stdout.write(
            status_color(f"✓ {stage_name}: {checkpoint.status.upper()}")
        )
        
        if checkpoint.error_message:
            self.stdout.write(self.style.ERROR(f"  Error: {checkpoint.error_message}"))
    
    def console_error_callback(self, error, stage):
        """Console error callback"""
        sys.stdout.write('\n')
        self.stdout.write(
            self.style.ERROR(f"ERROR in {stage.value}: {error}")
        )
    
    def create_progress_bar(self, percentage, width=30):
        """Create ASCII progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"
    
    def monitoring_loop(self, interval):
        """Background monitoring loop"""
        while not self.should_stop and self.migration_service and self.migration_service.is_running:
            time.sleep(interval)
            
            if self.migration_service.metrics:
                # Check for warnings or issues
                if self.migration_service.metrics.error_count > 0:
                    sys.stdout.write('\n')
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  {self.migration_service.metrics.error_count} errors encountered"
                        )
                    )
    
    def pre_migration_validation(self):
        """Perform pre-migration validation"""
        self.stdout.write("Performing pre-migration validation...")
        
        try:
            # Test database connections
            if not self.migration_service.migration_service.connect_databases():
                self.stdout.write(self.style.ERROR("✗ Database connection failed"))
                return False
            
            self.stdout.write(self.style.SUCCESS("✓ Database connections successful"))
            
            # Check table count and data size
            tables = self.migration_service.migration_service.get_sqlite_tables()
            total_records = 0
            
            for table_name in tables:
                cursor = self.migration_service.migration_service.sqlite_conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                total_records += count
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Found {len(tables)} tables with {total_records:,} total records")
            )
            
            # Estimate migration time
            estimated_minutes = total_records / 1000  # Rough estimate: 1000 records per minute
            self.stdout.write(
                f"Estimated migration time: {estimated_minutes:.1f} minutes"
            )
            
            # Check disk space (basic check)
            # TODO: Implement proper disk space validation
            
            self.migration_service.migration_service.disconnect_databases()
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Validation failed: {e}"))
            return False
    
    def dry_run_migration(self):
        """Perform dry run migration"""
        self.stdout.write("Starting dry run migration...")
        
        # Simulate migration stages
        stages = [
            ("Preparation", 2),
            ("Schema Synchronization", 5),
            ("Initial Data Sync", 30),
            ("Validation", 10),
            ("Cutover Preparation", 3),
            ("Cutover", 1),
            ("Post-Cutover Validation", 5),
            ("Cleanup", 2)
        ]
        
        for stage_name, duration in stages:
            self.stdout.write(f"Simulating {stage_name}...")
            
            for i in range(duration):
                if self.should_stop:
                    self.stdout.write(self.style.WARNING("Dry run stopped"))
                    return
                
                progress = (i + 1) / duration * 100
                progress_bar = self.create_progress_bar(progress)
                sys.stdout.write(f'\r  {progress_bar} {progress:.1f}%')
                sys.stdout.flush()
                time.sleep(0.5)
            
            sys.stdout.write('\n')
            self.stdout.write(self.style.SUCCESS(f"✓ {stage_name} completed"))
        
        self.stdout.write(self.style.SUCCESS("✅ Dry run completed successfully"))
    
    def execute_migration(self):
        """Execute actual migration"""
        self.stdout.write("Starting zero-downtime migration...")
        self.stdout.write(f"Migration ID: {self.migration_service.migration_id}")
        
        # Execute migration
        success = self.migration_service.execute_migration()
        
        # Final status
        sys.stdout.write('\n\n')
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Migration completed successfully!"))
            
            # Show final statistics
            if self.migration_service.metrics:
                metrics = self.migration_service.metrics
                self.stdout.write(f"Total records migrated: {metrics.records_migrated:,}")
                self.stdout.write(f"Total time: {metrics.elapsed_time}")
                self.stdout.write(f"Average speed: {metrics.migration_speed:.0f} records/second")
        else:
            self.stdout.write(self.style.ERROR("❌ Migration failed or was rolled back"))
            
            # Show error information
            failed_checkpoints = [
                cp for cp in self.migration_service.checkpoints 
                if cp.status == 'failed'
            ]
            
            if failed_checkpoints:
                self.stdout.write("Failed stages:")
                for cp in failed_checkpoints:
                    stage_name = cp.stage.value.replace('_', ' ').title()
                    self.stdout.write(f"  - {stage_name}: {cp.error_message}")
        
        # Save final report
        self.save_migration_report()
    
    def save_migration_report(self):
        """Save migration report to file"""
        if not self.migration_service:
            return
        
        report_file = Path(settings.BASE_DIR) / 'migration_logs' / f"migration_report_{self.migration_service.migration_id}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        report_data = {
            'migration_id': self.migration_service.migration_id,
            'completion_time': datetime.now().isoformat(),
            'final_stage': self.migration_service.current_stage.value,
            'success': self.migration_service.current_stage == MigrationStage.COMPLETED,
            'rollback_triggered': self.migration_service.rollback_triggered,
            'metrics': self.migration_service.metrics.to_dict() if self.migration_service.metrics else None,
            'checkpoints': [cp.to_dict() for cp in self.migration_service.checkpoints]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.stdout.write(f"Migration report saved to: {report_file}")
    
    def show_migration_status(self):
        """Show status of running migration"""
        # Try to find running migration from cache
        cache_keys = cache.keys("migration_progress_*") if hasattr(cache, 'keys') else []
        
        if not cache_keys:
            self.stdout.write("No running migrations found")
            return
        
        for cache_key in cache_keys:
            status_data = cache.get(cache_key)
            if status_data:
                migration_id = cache_key.replace('migration_progress_', '')
                self.stdout.write(f"Migration ID: {migration_id}")
                self.stdout.write(f"Stage: {status_data.get('stage', 'unknown')}")
                self.stdout.write(f"Progress: {status_data.get('progress_percentage', 0):.1f}%")
                self.stdout.write(f"Records: {status_data.get('records_migrated', 0):,}/{status_data.get('total_records', 0):,}")
                
                if status_data.get('estimated_completion'):
                    eta = datetime.fromisoformat(status_data['estimated_completion'])
                    self.stdout.write(f"ETA: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop_migration(self):
        """Stop running migration"""
        # This would need to be implemented with proper IPC or database coordination
        self.stdout.write("Migration stop requested (implementation depends on deployment)")
        # TODO: Implement proper migration stop mechanism
    
    def trigger_rollback(self):
        """Trigger rollback of running migration"""
        # This would need to be implemented with proper IPC or database coordination
        self.stdout.write("Migration rollback requested (implementation depends on deployment)")
        # TODO: Implement proper rollback trigger mechanism
    
    def cleanup(self):
        """Cleanup resources"""
        self.should_stop = True
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
        
        if self.migration_service:
            self.migration_service.migration_service.disconnect_databases()