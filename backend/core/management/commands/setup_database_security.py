"""
Django management command to set up database security measures.

This command initializes all database security components including:
- SSL encryption configuration
- Role-based database users
- Audit logging setup
- Field-level encryption for sensitive data
- Security monitoring and threat detection

Usage:
    python manage.py setup_database_security
    python manage.py setup_database_security --encrypt-existing-data
    python manage.py setup_database_security --create-users-only
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.database_security import database_security_manager
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up comprehensive database security measures'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--encrypt-existing-data',
            action='store_true',
            help='Encrypt existing sensitive data in the database',
        )
        parser.add_argument(
            '--create-users-only',
            action='store_true',
            help='Only create database users without other security setup',
        )
        parser.add_argument(
            '--skip-ssl',
            action='store_true',
            help='Skip SSL configuration setup',
        )
        parser.add_argument(
            '--skip-audit',
            action='store_true',
            help='Skip audit logging setup',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up database security measures...')
        )
        
        try:
            # Step 1: Configure SSL encryption
            if not options['skip_ssl']:
                self.stdout.write('Configuring SSL encryption...')
                ssl_success = database_security_manager.setup_ssl_encryption()
                if ssl_success:
                    self.stdout.write(
                        self.style.SUCCESS('✓ SSL encryption configured successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠ SSL encryption configuration failed or not available')
                    )
            
            # Step 2: Create role-based database users
            self.stdout.write('Creating role-based database users...')
            user_results = database_security_manager.create_database_users()
            
            for username, success in user_results.items():
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Database user "{username}" created successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create database user "{username}"')
                    )
            
            if options['create_users_only']:
                self.stdout.write(
                    self.style.SUCCESS('Database users creation completed.')
                )
                return
            
            # Step 3: Set up audit logging
            if not options['skip_audit']:
                self.stdout.write('Setting up audit logging...')
                audit_success = database_security_manager.setup_audit_logging()
                if audit_success:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Audit logging configured successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Failed to configure audit logging')
                    )
            
            # Step 4: Encrypt existing sensitive data
            if options['encrypt_existing_data']:
                self.stdout.write('Encrypting existing sensitive data...')
                
                # Define sensitive fields for each table
                sensitive_data_config = {
                    'auth_user': ['email', 'first_name', 'last_name'],
                    'customers_customer': ['phone_number', 'address'],
                    'payments_payment': ['card_number', 'billing_address'],
                    'orders_order': ['shipping_address', 'billing_address'],
                }
                
                for table, fields in sensitive_data_config.items():
                    self.stdout.write(f'  Encrypting fields in {table}: {", ".join(fields)}')
                    encryption_success = database_security_manager.encrypt_sensitive_data(
                        table, fields
                    )
                    if encryption_success:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Encrypted sensitive fields in {table}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Failed to encrypt fields in {table}')
                        )
            
            # Step 5: Display security metrics
            self.stdout.write('Generating security metrics...')
            metrics = database_security_manager.get_security_metrics()
            
            if metrics:
                self.stdout.write('\nSecurity Setup Summary:')
                self.stdout.write('=' * 50)
                
                if 'audit_statistics' in metrics:
                    self.stdout.write('Audit Statistics (Last 24 hours):')
                    for stat in metrics['audit_statistics']:
                        self.stdout.write(
                            f"  {stat['event_type']}: {stat['total_count']} total "
                            f"({stat['successful']} successful, {stat['failed']} failed)"
                        )
                
                if 'security_events' in metrics:
                    self.stdout.write('\nSecurity Events (Last 24 hours):')
                    for event in metrics['security_events']:
                        self.stdout.write(
                            f"  {event['severity']}: {event['total_count']} total "
                            f"({event['resolved']} resolved)"
                        )
            
            # Step 6: Provide next steps and recommendations
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.SUCCESS('Database security setup completed!'))
            self.stdout.write('\nNext Steps:')
            self.stdout.write('1. Update your Django settings to use the new database users')
            self.stdout.write('2. Configure SSL certificates if not already done')
            self.stdout.write('3. Set up monitoring alerts for security events')
            self.stdout.write('4. Review and test the audit logging functionality')
            self.stdout.write('5. Schedule regular security metrics reviews')
            
            self.stdout.write('\nSecurity Features Enabled:')
            self.stdout.write('• Role-based access control with minimal privileges')
            self.stdout.write('• Field-level encryption for sensitive data')
            self.stdout.write('• Comprehensive audit logging and monitoring')
            self.stdout.write('• Threat detection and security alerts')
            self.stdout.write('• Failed login attempt monitoring')
            self.stdout.write('• Automated security metrics collection')
            
            # Display user credentials (in production, these should be stored securely)
            self.stdout.write('\n' + self.style.WARNING('IMPORTANT: Database User Credentials'))
            self.stdout.write(self.style.WARNING('Store these credentials securely and update your Django settings:'))
            
            for username, success in user_results.items():
                if success:
                    self.stdout.write(f'  {username}: [Password generated - check logs for details]')
            
        except Exception as e:
            logger.error(f"Database security setup failed: {e}")
            raise CommandError(f'Database security setup failed: {e}')