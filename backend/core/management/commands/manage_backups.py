"""
Django management command for MySQL backup operations

This command provides a CLI interface for managing database backups including:
- Creating full and incremental backups
- Verifying backup integrity
- Restoring from backups
- Point-in-time recovery
- Cleanup operations
- Status reporting

Usage:
    python manage.py manage_backups create_full
    python manage.py manage_backups create_incremental
    python manage.py manage_backups verify <backup_id>
    python manage.py manage_backups restore <backup_id>
    python manage.py manage_backups cleanup
    python manage.py manage_backups status
"""

import os
import sys
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.backup_manager import MySQLBackupManager, BackupConfig


class Command(BaseCommand):
    help = 'Manage MySQL database backups'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Backup actions')
        
        # Create full backup
        create_full_parser = subparsers.add_parser('create_full', help='Create a full backup')
        create_full_parser.add_argument(
            '--database', 
            default='default',
            help='Database alias to backup (default: default)'
        )
        
        # Create incremental backup
        create_incr_parser = subparsers.add_parser('create_incremental', help='Create an incremental backup')
        create_incr_parser.add_argument(
            '--database', 
            default='default',
            help='Database alias to backup (default: default)'
        )
        
        # Verify backup
        verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
        verify_parser.add_argument('backup_id', help='Backup ID to verify')
        
        # Restore backup
        restore_parser = subparsers.add_parser('restore', help='Restore from backup')
        restore_parser.add_argument('backup_id', help='Backup ID to restore')
        restore_parser.add_argument(
            '--database', 
            default='default',
            help='Database alias to restore to (default: default)'
        )
        restore_parser.add_argument(
            '--target-database',
            help='Target database name (if different from source)'
        )
        restore_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the restore operation (required for safety)'
        )
        
        # Point-in-time recovery
        pitr_parser = subparsers.add_parser('pitr', help='Point-in-time recovery')
        pitr_parser.add_argument('backup_id', help='Base backup ID for recovery')
        pitr_parser.add_argument('target_datetime', help='Target datetime (YYYY-MM-DD HH:MM:SS)')
        pitr_parser.add_argument(
            '--database', 
            default='default',
            help='Database alias to restore to (default: default)'
        )
        pitr_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the recovery operation (required for safety)'
        )
        
        # List backups
        list_parser = subparsers.add_parser('list', help='List available backups')
        list_parser.add_argument(
            '--type',
            choices=['full', 'incremental'],
            help='Filter by backup type'
        )
        list_parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of results (default: 20)'
        )
        
        # Cleanup old backups
        cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
        cleanup_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        
        # Status
        status_parser = subparsers.add_parser('status', help='Show backup system status')
        
        # Test backup system
        test_parser = subparsers.add_parser('test', help='Test backup and restore functionality')
        test_parser.add_argument(
            '--database', 
            default='default',
            help='Database alias to test (default: default)'
        )

    def get_backup_config(self):
        """Get backup configuration from Django settings"""
        backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
        encryption_key = getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key-change-in-production')
        
        return BackupConfig(
            backup_dir=backup_dir,
            encryption_key=encryption_key,
            retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
            compression_enabled=getattr(settings, 'BACKUP_COMPRESSION_ENABLED', True),
            verify_backups=getattr(settings, 'BACKUP_VERIFY_ENABLED', True),
        )

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'manage_backups')
            return
        
        try:
            config = self.get_backup_config()
            backup_manager = MySQLBackupManager(config)
            
            if action == 'create_full':
                self.handle_create_full(backup_manager, options)
            elif action == 'create_incremental':
                self.handle_create_incremental(backup_manager, options)
            elif action == 'verify':
                self.handle_verify(backup_manager, options)
            elif action == 'restore':
                self.handle_restore(backup_manager, options)
            elif action == 'pitr':
                self.handle_pitr(backup_manager, options)
            elif action == 'list':
                self.handle_list(backup_manager, options)
            elif action == 'cleanup':
                self.handle_cleanup(backup_manager, options)
            elif action == 'status':
                self.handle_status(backup_manager, options)
            elif action == 'test':
                self.handle_test(backup_manager, options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            raise CommandError(f"Backup operation failed: {e}")

    def handle_create_full(self, backup_manager, options):
        """Handle full backup creation"""
        database = options['database']
        self.stdout.write(f"Creating full backup for database '{database}'...")
        
        try:
            metadata = backup_manager.create_full_backup(database)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Full backup created successfully:\n"
                    f"  Backup ID: {metadata.backup_id}\n"
                    f"  File: {metadata.file_path}\n"
                    f"  Size: {metadata.file_size / (1024*1024):.2f} MB\n"
                    f"  Timestamp: {metadata.timestamp}"
                )
            )
        except Exception as e:
            raise CommandError(f"Failed to create full backup: {e}")

    def handle_create_incremental(self, backup_manager, options):
        """Handle incremental backup creation"""
        database = options['database']
        self.stdout.write(f"Creating incremental backup for database '{database}'...")
        
        try:
            metadata = backup_manager.create_incremental_backup(database)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Incremental backup created successfully:\n"
                    f"  Backup ID: {metadata.backup_id}\n"
                    f"  File: {metadata.file_path}\n"
                    f"  Size: {metadata.file_size / (1024*1024):.2f} MB\n"
                    f"  Parent: {metadata.parent_backup_id}\n"
                    f"  Timestamp: {metadata.timestamp}"
                )
            )
        except Exception as e:
            raise CommandError(f"Failed to create incremental backup: {e}")

    def handle_verify(self, backup_manager, options):
        """Handle backup verification"""
        backup_id = options['backup_id']
        self.stdout.write(f"Verifying backup '{backup_id}'...")
        
        try:
            is_valid = backup_manager.verify_backup_integrity(backup_id)
            if is_valid:
                self.stdout.write(
                    self.style.SUCCESS(f"Backup '{backup_id}' integrity verified successfully")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Backup '{backup_id}' integrity check failed")
                )
                sys.exit(1)
        except Exception as e:
            raise CommandError(f"Failed to verify backup: {e}")

    def handle_restore(self, backup_manager, options):
        """Handle backup restoration"""
        backup_id = options['backup_id']
        database = options['database']
        target_database = options.get('target_database')
        confirm = options.get('confirm', False)
        
        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: This operation will overwrite the target database!\n"
                    "Use --confirm to proceed with the restore operation."
                )
            )
            return
        
        self.stdout.write(f"Restoring backup '{backup_id}' to database '{database}'...")
        
        try:
            success = backup_manager.restore_from_backup(backup_id, database, target_database)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Backup '{backup_id}' restored successfully")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to restore backup '{backup_id}'")
                )
                sys.exit(1)
        except Exception as e:
            raise CommandError(f"Failed to restore backup: {e}")

    def handle_pitr(self, backup_manager, options):
        """Handle point-in-time recovery"""
        backup_id = options['backup_id']
        target_datetime_str = options['target_datetime']
        database = options['database']
        confirm = options.get('confirm', False)
        
        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: This operation will overwrite the target database!\n"
                    "Use --confirm to proceed with the point-in-time recovery."
                )
            )
            return
        
        try:
            target_datetime = datetime.strptime(target_datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise CommandError("Invalid datetime format. Use: YYYY-MM-DD HH:MM:SS")
        
        self.stdout.write(
            f"Performing point-in-time recovery to {target_datetime} "
            f"using backup '{backup_id}'..."
        )
        
        try:
            success = backup_manager.point_in_time_recovery(backup_id, target_datetime, database)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Point-in-time recovery to {target_datetime} completed successfully"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Point-in-time recovery failed")
                )
                sys.exit(1)
        except Exception as e:
            raise CommandError(f"Point-in-time recovery failed: {e}")

    def handle_list(self, backup_manager, options):
        """Handle backup listing"""
        backup_type = options.get('type')
        limit = options['limit']
        
        try:
            backups = backup_manager.storage.list_backups(backup_type)[:limit]
            
            if not backups:
                self.stdout.write("No backups found")
                return
            
            self.stdout.write(f"Found {len(backups)} backup(s):\n")
            
            for backup in backups:
                size_mb = backup.file_size / (1024 * 1024)
                self.stdout.write(
                    f"  {backup.backup_id}\n"
                    f"    Type: {backup.backup_type}\n"
                    f"    Timestamp: {backup.timestamp}\n"
                    f"    Size: {size_mb:.2f} MB\n"
                    f"    Database: {backup.database_name}\n"
                    f"    MySQL Version: {backup.mysql_version}\n"
                    f"    Encrypted: {backup.encrypted}\n"
                    f"    Parent: {backup.parent_backup_id or 'None'}\n"
                )
                
        except Exception as e:
            raise CommandError(f"Failed to list backups: {e}")

    def handle_cleanup(self, backup_manager, options):
        """Handle backup cleanup"""
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write("Dry run mode - showing what would be deleted:")
        
        try:
            if dry_run:
                # Simulate cleanup without actually deleting
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=backup_manager.config.retention_days)
                old_backups = [
                    b for b in backup_manager.storage.list_backups()
                    if b.timestamp < cutoff_date
                ]
                
                if not old_backups:
                    self.stdout.write("No old backups to clean up")
                    return
                
                total_size = sum(b.file_size for b in old_backups)
                self.stdout.write(
                    f"Would delete {len(old_backups)} backup(s) "
                    f"({total_size / (1024*1024):.2f} MB):"
                )
                
                for backup in old_backups:
                    self.stdout.write(f"  - {backup.backup_id} ({backup.timestamp})")
            else:
                removed_backups = backup_manager.cleanup_old_backups()
                
                if not removed_backups:
                    self.stdout.write("No old backups to clean up")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Cleaned up {len(removed_backups)} old backup(s):\n" +
                            "\n".join(f"  - {backup_id}" for backup_id in removed_backups)
                        )
                    )
                    
        except Exception as e:
            raise CommandError(f"Failed to cleanup backups: {e}")

    def handle_status(self, backup_manager, options):
        """Handle status reporting"""
        try:
            status = backup_manager.get_backup_status()
            
            if 'error' in status:
                self.stdout.write(
                    self.style.ERROR(f"Failed to get backup status: {status['error']}")
                )
                return
            
            self.stdout.write("Backup System Status:\n")
            self.stdout.write(f"  Total Backups: {status['total_backups']}")
            self.stdout.write(f"  Full Backups: {status['full_backups']}")
            self.stdout.write(f"  Incremental Backups: {status['incremental_backups']}")
            self.stdout.write(f"  Total Size: {status['total_size_gb']} GB")
            self.stdout.write(f"  Backup Directory: {status['backup_directory']}")
            self.stdout.write(f"  Retention Period: {status['retention_days']} days")
            
            if status['latest_full_backup']:
                self.stdout.write(f"  Latest Full Backup: {status['latest_full_backup']}")
            else:
                self.stdout.write("  Latest Full Backup: None")
            
            if status['latest_incremental_backup']:
                self.stdout.write(f"  Latest Incremental Backup: {status['latest_incremental_backup']}")
            else:
                self.stdout.write("  Latest Incremental Backup: None")
            
            # Health indicators
            if status['recent_full_backup']:
                self.stdout.write(self.style.SUCCESS("  ✓ Recent full backup available"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ No recent full backup (>24h)"))
            
            if status['recent_incremental_backup']:
                self.stdout.write(self.style.SUCCESS("  ✓ Recent incremental backup available"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ No recent incremental backup (>4h)"))
                
        except Exception as e:
            raise CommandError(f"Failed to get backup status: {e}")

    def handle_test(self, backup_manager, options):
        """Handle backup system testing"""
        database = options['database']
        
        self.stdout.write("Testing backup system functionality...")
        
        try:
            # Test full backup creation
            self.stdout.write("1. Testing full backup creation...")
            metadata = backup_manager.create_full_backup(database)
            self.stdout.write(f"   ✓ Full backup created: {metadata.backup_id}")
            
            # Test backup verification
            self.stdout.write("2. Testing backup verification...")
            is_valid = backup_manager.verify_backup_integrity(metadata.backup_id)
            if is_valid:
                self.stdout.write("   ✓ Backup verification passed")
            else:
                raise Exception("Backup verification failed")
            
            # Test incremental backup
            self.stdout.write("3. Testing incremental backup creation...")
            incr_metadata = backup_manager.create_incremental_backup(database)
            self.stdout.write(f"   ✓ Incremental backup created: {incr_metadata.backup_id}")
            
            # Test incremental backup verification
            self.stdout.write("4. Testing incremental backup verification...")
            is_valid = backup_manager.verify_backup_integrity(incr_metadata.backup_id)
            if is_valid:
                self.stdout.write("   ✓ Incremental backup verification passed")
            else:
                raise Exception("Incremental backup verification failed")
            
            # Test status reporting
            self.stdout.write("5. Testing status reporting...")
            status = backup_manager.get_backup_status()
            if 'error' not in status:
                self.stdout.write("   ✓ Status reporting working")
            else:
                raise Exception(f"Status reporting failed: {status['error']}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAll backup system tests passed successfully!\n"
                    f"Created test backups:\n"
                    f"  - Full: {metadata.backup_id}\n"
                    f"  - Incremental: {incr_metadata.backup_id}\n"
                    f"\nYou can clean these up with: python manage.py manage_backups cleanup"
                )
            )
            
        except Exception as e:
            raise CommandError(f"Backup system test failed: {e}")