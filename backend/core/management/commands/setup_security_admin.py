"""
Django management command to set up the security admin interface.

This command:
- Registers the security admin models
- Creates necessary database tables
- Sets up initial security configuration
- Configures admin permissions

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to set up security admin interface."""
    
    help = 'Set up the database security admin interface and permissions'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--create-tables',
            action='store_true',
            help='Create security-related database tables',
        )
        parser.add_argument(
            '--setup-permissions',
            action='store_true',
            help='Set up security admin permissions and groups',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test database security configuration',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all setup tasks',
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(
            self.style.SUCCESS('Setting up Database Security Admin Interface...')
        )
        
        try:
            if options['all']:
                self.create_security_tables()
                self.setup_security_permissions()
                self.test_security_configuration()
            else:
                if options['create_tables']:
                    self.create_security_tables()
                
                if options['setup_permissions']:
                    self.setup_security_permissions()
                
                if options['test_connection']:
                    self.test_security_configuration()
            
            self.stdout.write(
                self.style.SUCCESS('Security admin interface setup completed successfully!')
            )
            
        except Exception as e:
            raise CommandError(f'Setup failed: {e}')
    
    def create_security_tables(self):
        """Create security-related database tables."""
        self.stdout.write('Creating security tables...')
        
        try:
            with connection.cursor() as cursor:
                # Create audit log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS db_audit_log (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME(6) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        user VARCHAR(100) NOT NULL,
                        source_ip VARCHAR(45),
                        database_name VARCHAR(100),
                        table_name VARCHAR(100),
                        operation VARCHAR(50),
                        affected_rows INT DEFAULT 0,
                        query_hash VARCHAR(64),
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        additional_data JSON,
                        INDEX idx_audit_timestamp (timestamp),
                        INDEX idx_audit_user (user),
                        INDEX idx_audit_event_type (event_type),
                        INDEX idx_audit_source_ip (source_ip),
                        INDEX idx_audit_success (success)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                
                # Create security events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS db_security_events (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME(6) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        user VARCHAR(100),
                        source_ip VARCHAR(45),
                        description TEXT NOT NULL,
                        details JSON,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at DATETIME(6),
                        resolved_by VARCHAR(100),
                        INDEX idx_security_timestamp (timestamp),
                        INDEX idx_security_severity (severity),
                        INDEX idx_security_resolved (resolved),
                        INDEX idx_security_event_type (event_type)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                
                # Create security metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS db_security_metrics (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME(6) NOT NULL,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15,4) NOT NULL,
                        metric_unit VARCHAR(20),
                        additional_info JSON,
                        INDEX idx_metrics_timestamp (timestamp),
                        INDEX idx_metrics_name (metric_name)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                
                # Create failed login attempts tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS db_failed_login_attempts (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        user_identifier VARCHAR(150) NOT NULL,
                        source_ip VARCHAR(45) NOT NULL,
                        attempt_timestamp DATETIME(6) NOT NULL,
                        user_agent TEXT,
                        INDEX idx_failed_login_user (user_identifier),
                        INDEX idx_failed_login_ip (source_ip),
                        INDEX idx_failed_login_timestamp (attempt_timestamp)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('✓ Security tables created successfully')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to create security tables: {e}')
            )
            raise
    
    def setup_security_permissions(self):
        """Set up security admin permissions and groups."""
        self.stdout.write('Setting up security permissions...')
        
        try:
            # Create Security Administrators group
            security_admin_group, created = Group.objects.get_or_create(
                name='Security Administrators'
            )
            
            if created:
                self.stdout.write('✓ Created Security Administrators group')
            else:
                self.stdout.write('✓ Security Administrators group already exists')
            
            # Create Security Auditors group (read-only access)
            security_auditor_group, created = Group.objects.get_or_create(
                name='Security Auditors'
            )
            
            if created:
                self.stdout.write('✓ Created Security Auditors group')
            else:
                self.stdout.write('✓ Security Auditors group already exists')
            
            # Get or create custom permissions
            from django.contrib.auth.models import User
            user_content_type = ContentType.objects.get_for_model(User)
            
            # Custom permissions for security management
            security_permissions = [
                ('view_audit_logs', 'Can view audit logs'),
                ('export_audit_logs', 'Can export audit logs'),
                ('view_security_events', 'Can view security events'),
                ('resolve_security_events', 'Can resolve security events'),
                ('run_security_scans', 'Can run security scans'),
                ('manage_database_security', 'Can manage database security'),
                ('view_security_dashboard', 'Can view security dashboard'),
            ]
            
            created_permissions = []
            for codename, name in security_permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    name=name,
                    content_type=user_content_type,
                )
                created_permissions.append(permission)
                
                if created:
                    self.stdout.write(f'✓ Created permission: {name}')
            
            # Assign permissions to groups
            # Security Administrators get all permissions
            security_admin_group.permissions.set(created_permissions)
            
            # Security Auditors get read-only permissions
            auditor_permissions = [p for p in created_permissions 
                                 if 'view' in p.codename or 'export' in p.codename]
            security_auditor_group.permissions.set(auditor_permissions)
            
            self.stdout.write(
                self.style.SUCCESS('✓ Security permissions configured successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to setup permissions: {e}')
            )
            raise
    
    def test_security_configuration(self):
        """Test database security configuration."""
        self.stdout.write('Testing security configuration...')
        
        try:
            from core.database_security import DatabaseSecurityManager
            
            # Initialize security manager
            security_manager = DatabaseSecurityManager()
            
            # Test SSL configuration
            self.stdout.write('Testing SSL encryption...')
            ssl_result = security_manager.setup_ssl_encryption()
            if ssl_result:
                self.stdout.write(self.style.SUCCESS('✓ SSL encryption is configured'))
            else:
                self.stdout.write(self.style.WARNING('⚠ SSL encryption test failed'))
            
            # Test audit logging
            self.stdout.write('Testing audit logging...')
            with connection.cursor() as cursor:
                cursor.execute("SHOW VARIABLES LIKE 'general_log'")
                result = cursor.fetchone()
                
                if result and result[1] == 'ON':
                    self.stdout.write(self.style.SUCCESS('✓ Audit logging is enabled'))
                else:
                    self.stdout.write(self.style.WARNING('⚠ Audit logging is not enabled'))
                
                # Test security tables
                cursor.execute("SHOW TABLES LIKE 'db_%'")
                security_tables = cursor.fetchall()
                
                expected_tables = ['db_audit_log', 'db_security_events', 'db_security_metrics']
                found_tables = [table[0] for table in security_tables]
                
                for table in expected_tables:
                    if table in found_tables:
                        self.stdout.write(self.style.SUCCESS(f'✓ Table {table} exists'))
                    else:
                        self.stdout.write(self.style.ERROR(f'✗ Table {table} missing'))
            
            # Test threat detection
            self.stdout.write('Testing threat detection...')
            test_query = "SELECT * FROM auth_user WHERE id = 1"
            threats_detected, threat_details = security_manager.detect_threats(
                test_query, 'test_user', '127.0.0.1'
            )
            
            if not threats_detected:
                self.stdout.write(self.style.SUCCESS('✓ Threat detection is working'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Threat detection flagged test query: {threat_details}')
                )
            
            self.stdout.write(
                self.style.SUCCESS('✓ Security configuration test completed')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Security configuration test failed: {e}')
            )
            raise
    
    def create_sample_data(self):
        """Create sample security data for testing."""
        self.stdout.write('Creating sample security data...')
        
        try:
            from core.database_security import database_security_manager, AuditEventType
            from datetime import datetime, timedelta
            import random
            
            # Create sample audit log entries
            sample_events = [
                (AuditEventType.LOGIN_SUCCESS, 'admin', '192.168.1.100', True),
                (AuditEventType.DATA_ACCESS, 'user1', '192.168.1.101', True),
                (AuditEventType.LOGIN_FAILURE, 'hacker', '10.0.0.1', False),
                (AuditEventType.SUSPICIOUS_ACTIVITY, 'user2', '192.168.1.102', False),
            ]
            
            for event_type, user, ip, success in sample_events:
                database_security_manager.log_audit_event(
                    event_type=event_type,
                    user=user,
                    source_ip=ip,
                    database='ecommerce_db',
                    table='test_table',
                    operation='TEST',
                    affected_rows=random.randint(0, 10),
                    query_hash=f'test_{random.randint(1000, 9999)}',
                    success=success,
                    additional_data={'test': True}
                )
            
            self.stdout.write(
                self.style.SUCCESS('✓ Sample security data created')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠ Failed to create sample data: {e}')
            )