"""
Management command to initialize database administration tools.

This command sets up:
- Database monitoring
- Security configurations
- Backup system
- Admin users and permissions
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection

from core.database_monitor import DatabaseMonitor
from core.database_security import DatabaseSecurityManager
from core.backup_manager import MySQLBackupManager, BackupConfig

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize database administration tools and configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-monitoring',
            action='store_true',
            help='Skip database monitoring setup',
        )
        parser.add_argument(
            '--skip-security',
            action='store_true',
            help='Skip security configuration setup',
        )
        parser.add_argument(
            '--skip-backup',
            action='store_true',
            help='Skip backup system setup',
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create database admin user',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Initializing database administration tools...')
        )
        
        try:
            # Initialize database monitoring
            if not options['skip_monitoring']:
                self.setup_monitoring()
            
            # Initialize security configurations
            if not options['skip_security']:
                self.setup_security()
            
            # Initialize backup system
            if not options['skip_backup']:
                self.setup_backup_system()
            
            # Create admin user if requested
            if options['create_admin']:
                self.create_admin_user()
            
            self.stdout.write(
                self.style.SUCCESS('Database administration tools initialized successfully!')
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database administration tools: {e}")
            raise CommandError(f'Initialization failed: {e}')
    
    def setup_monitoring(self):
        """Initialize database monitoring system."""
        self.stdout.write('Setting up database monitoring...')
        
        try:
            # Initialize database monitor
            monitor = DatabaseMonitor()
            
            # Test monitoring functionality
            for db_alias in settings.DATABASES.keys():
                try:
                    metrics = monitor._collect_database_metrics(db_alias)
                    if metrics:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Monitoring configured for {db_alias}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Could not collect metrics for {db_alias}')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Monitoring setup failed for {db_alias}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS('Database monitoring setup completed')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup monitoring: {e}')
            )
            raise
    
    def setup_security(self):
        """Initialize database security configurations."""
        self.stdout.write('Setting up database security...')
        
        try:
            security_manager = DatabaseSecurityManager()
            
            # Setup audit logging
            if security_manager.setup_audit_logging():
                self.stdout.write(
                    self.style.SUCCESS('✓ Audit logging configured')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Audit logging setup had issues')
                )
            
            # Setup SSL encryption
            if security_manager.setup_ssl_encryption():
                self.stdout.write(
                    self.style.SUCCESS('✓ SSL encryption configured')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ SSL encryption not available')
                )
            
            # Create database users
            user_results = security_manager.create_database_users()
            for username, success in user_results.items():
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Database user created: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create user: {username}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS('Database security setup completed')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup security: {e}')
            )
            raise
    
    def setup_backup_system(self):
        """Initialize backup system."""
        self.stdout.write('Setting up backup system...')
        
        try:
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key'),
                retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
            )
            
            backup_manager = MySQLBackupManager(backup_config)
            
            # Test backup system
            backup_status = backup_manager.get_backup_status()
            
            if 'error' not in backup_status:
                self.stdout.write(
                    self.style.SUCCESS('✓ Backup system initialized')
                )
                self.stdout.write(f'  Backup directory: {backup_config.backup_dir}')
                self.stdout.write(f'  Retention period: {backup_config.retention_days} days')
                self.stdout.write(f'  Total backups: {backup_status.get("total_backups", 0)}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Backup system error: {backup_status["error"]}')
                )
            
            self.stdout.write(
                self.style.SUCCESS('Backup system setup completed')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup backup system: {e}')
            )
            raise
    
    def create_admin_user(self):
        """Create database administration user."""
        self.stdout.write('Creating database admin user...')
        
        try:
            username = 'dbadmin'
            email = 'dbadmin@example.com'
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠ User {username} already exists')
                )
                return
            
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='admin123'  # Should be changed in production
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Database admin user created: {username}')
            )
            self.stdout.write(
                self.style.WARNING('⚠ Please change the default password!')
            )
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Password: admin123')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create admin user: {e}')
            )
            raise
    
    def test_database_connections(self):
        """Test all database connections."""
        self.stdout.write('Testing database connections...')
        
        for db_alias in settings.DATABASES.keys():
            try:
                from django.db import connections
                conn = connections[db_alias]
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                if result and result[0] == 1:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Connection successful: {db_alias}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Connection test failed: {db_alias}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Connection failed for {db_alias}: {e}')
                )
    
    def display_access_info(self):
        """Display access information for the admin interface."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('DATABASE ADMINISTRATION ACCESS INFO')
        )
        self.stdout.write('='*60)
        self.stdout.write('Database Admin Interface: http://localhost:8000/db-admin/')
        self.stdout.write('Django Admin Interface: http://localhost:8000/admin/')
        self.stdout.write('')
        self.stdout.write('Available endpoints:')
        self.stdout.write('  - Dashboard: /db-admin/dashboard/')
        self.stdout.write('  - Health Check: /db-admin/health-check/')
        self.stdout.write('  - Backup Management: /db-admin/backup-management/')
        self.stdout.write('  - User Management: /db-admin/user-management/')
        self.stdout.write('  - Performance Report: /db-admin/performance-report/')
        self.stdout.write('='*60)