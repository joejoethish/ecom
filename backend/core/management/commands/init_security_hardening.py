"""
Django management command to initialize database security hardening.

This command sets up:
- Transparent data encryption for sensitive tables
- Enhanced threat detection and monitoring
- Security audit and compliance checking
- Key management and rotation

Usage: python manage.py init_security_hardening
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.encryption_manager import transparent_data_encryption, EncryptionAlgorithm
from core.threat_detection import advanced_threat_detector
from core.security_audit import security_audit_manager, ComplianceFramework
from core.database_security import database_security_manager


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize comprehensive database security hardening'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--encrypt-fields',
            action='store_true',
            help='Configure field-level encryption for sensitive data',
        )
        parser.add_argument(
            '--setup-monitoring',
            action='store_true',
            help='Set up enhanced threat detection and monitoring',
        )
        parser.add_argument(
            '--run-audit',
            action='store_true',
            help='Run initial security audit and compliance check',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all security hardening steps',
        )
        parser.add_argument(
            '--framework',
            type=str,
            choices=['gdpr', 'pci_dss', 'sox', 'iso_27001'],
            help='Specific compliance framework to focus on',
        )
    
    def handle(self, *args, **options):
        """Execute the security hardening initialization."""
        self.stdout.write(
            self.style.SUCCESS('Starting database security hardening initialization...')
        )
        
        try:
            # Determine what to run
            run_all = options['all']
            encrypt_fields = options['encrypt_fields'] or run_all
            setup_monitoring = options['setup_monitoring'] or run_all
            run_audit = options['run_audit'] or run_all
            
            # Step 1: Configure transparent data encryption
            if encrypt_fields:
                self.stdout.write('Configuring transparent data encryption...')
                self._setup_data_encryption()
            
            # Step 2: Set up enhanced monitoring and threat detection
            if setup_monitoring:
                self.stdout.write('Setting up enhanced threat detection...')
                self._setup_threat_detection()
            
            # Step 3: Run security audit and compliance check
            if run_audit:
                self.stdout.write('Running security audit and compliance check...')
                self._run_security_audit(options.get('framework'))
            
            # Step 4: Configure database security settings
            self.stdout.write('Configuring database security settings...')
            self._configure_database_security()
            
            self.stdout.write(
                self.style.SUCCESS('Database security hardening completed successfully!')
            )
            
        except Exception as e:
            logger.error(f"Security hardening failed: {e}")
            raise CommandError(f'Security hardening failed: {e}')
    
    def _setup_data_encryption(self):
        """Set up transparent data encryption for sensitive tables."""
        try:
            # Define sensitive fields that need encryption
            sensitive_fields = [
                # User authentication data
                ('auth_user', 'email', EncryptionAlgorithm.FERNET, False),
                ('auth_user', 'first_name', EncryptionAlgorithm.FERNET, True),
                ('auth_user', 'last_name', EncryptionAlgorithm.FERNET, True),
                
                # Customer personal data
                ('customers_customer', 'email', EncryptionAlgorithm.FERNET, True),
                ('customers_customer', 'phone_number', EncryptionAlgorithm.AES_256_GCM, False),
                ('customers_customer', 'address', EncryptionAlgorithm.AES_256_GCM, False),
                
                # Payment information
                ('payments_payment', 'card_number', EncryptionAlgorithm.AES_256_GCM, False),
                ('payments_payment', 'cardholder_name', EncryptionAlgorithm.FERNET, False),
                
                # Order sensitive data
                ('orders_order', 'billing_address', EncryptionAlgorithm.AES_256_GCM, False),
                ('orders_order', 'shipping_address', EncryptionAlgorithm.AES_256_GCM, False),
            ]
            
            # Configure encryption for each field
            for table_name, field_name, algorithm, is_searchable in sensitive_fields:
                success = transparent_data_encryption.configure_field_encryption(
                    table_name=table_name,
                    field_name=field_name,
                    algorithm=algorithm,
                    is_searchable=is_searchable
                )
                
                if success:
                    self.stdout.write(
                        f'  ✓ Configured encryption for {table_name}.{field_name} ({algorithm.value})'
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Failed to configure encryption for {table_name}.{field_name}')
                    )
            
            # Generate initial encryption keys
            self.stdout.write('Generating encryption keys...')
            
            # Generate master keys for different algorithms
            for algorithm in [EncryptionAlgorithm.FERNET, EncryptionAlgorithm.AES_256_GCM]:
                from core.encryption_manager import KeyType
                key = transparent_data_encryption.generate_encryption_key(
                    key_type=KeyType.DATA_ENCRYPTION_KEY,
                    algorithm=algorithm,
                    expires_days=90
                )
                self.stdout.write(f'  ✓ Generated {algorithm.value} encryption key: {key.key_id}')
            
            # Get encryption status
            status = transparent_data_encryption.get_encryption_status()
            self.stdout.write(
                f'Encryption configured: {status["encrypted_fields"]} fields, '
                f'{status["active_keys"]} active keys'
            )
            
        except Exception as e:
            logger.error(f"Data encryption setup failed: {e}")
            raise CommandError(f'Data encryption setup failed: {e}')
    
    def _setup_threat_detection(self):
        """Set up enhanced threat detection and monitoring."""
        try:
            # Initialize threat detection system
            self.stdout.write('Initializing threat detection system...')
            
            # Get threat detection statistics
            stats = advanced_threat_detector.get_threat_statistics()
            
            self.stdout.write(
                f'  ✓ Threat detection initialized with {stats["active_signatures"]} signatures'
            )
            self.stdout.write(
                f'  ✓ User behavior profiles: {stats["user_profiles"]}'
            )
            
            # Test threat detection with sample queries
            self.stdout.write('Testing threat detection capabilities...')
            
            test_queries = [
                ("SELECT * FROM auth_user", "normal_query"),
                ("SELECT * FROM auth_user WHERE 1=1 OR 1=1", "sql_injection_test"),
                ("SHOW DATABASES", "information_gathering"),
                ("SELECT * FROM information_schema.tables", "schema_enumeration")
            ]
            
            for query, description in test_queries:
                threats_detected, detections = advanced_threat_detector.detect_threats(
                    query=query,
                    user='test_user',
                    source_ip='127.0.0.1',
                    context={'test': True}
                )
                
                if threats_detected:
                    self.stdout.write(
                        f'  ⚠ Detected {len(detections)} threats in {description}: '
                        f'{[d.description for d in detections]}'
                    )
                else:
                    self.stdout.write(f'  ✓ No threats detected in {description}')
            
        except Exception as e:
            logger.error(f"Threat detection setup failed: {e}")
            raise CommandError(f'Threat detection setup failed: {e}')
    
    def _run_security_audit(self, framework_name=None):
        """Run comprehensive security audit."""
        try:
            # Determine framework
            framework = None
            if framework_name:
                framework = ComplianceFramework(framework_name)
                self.stdout.write(f'Running {framework_name.upper()} compliance audit...')
            else:
                self.stdout.write('Running comprehensive security audit...')
            
            # Run the audit
            audit_results = security_audit_manager.run_compliance_audit(framework)
            
            # Display results
            self.stdout.write(
                f'Audit completed: {audit_results["overall_compliance_score"]:.1f}% compliant'
            )
            self.stdout.write(
                f'  ✓ Compliant rules: {audit_results["compliant_rules"]}'
            )
            self.stdout.write(
                f'  ⚠ Non-compliant rules: {audit_results["non_compliant_rules"]}'
            )
            self.stdout.write(
                f'  ⚠ Partially compliant: {audit_results["partially_compliant_rules"]}'
            )
            
            # Show framework-specific results
            if audit_results['summary_by_framework']:
                self.stdout.write('\nCompliance by framework:')
                for fw, summary in audit_results['summary_by_framework'].items():
                    self.stdout.write(
                        f'  {fw.upper()}: {summary["compliance_percentage"]:.1f}% '
                        f'({summary["compliant"]}/{summary["total_rules"]} rules)'
                    )
            
            # Show top recommendations
            if audit_results['recommendations']:
                self.stdout.write('\nTop recommendations:')
                for i, rec in enumerate(audit_results['recommendations'][:5], 1):
                    self.stdout.write(f'  {i}. {rec}')
            
            # Generate detailed report
            report = security_audit_manager.generate_compliance_report(framework)
            self.stdout.write(f'\nDetailed report generated: {report["report_id"]}')
            
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            raise CommandError(f'Security audit failed: {e}')
    
    def _configure_database_security(self):
        """Configure database security settings."""
        try:
            self.stdout.write('Configuring database security settings...')
            
            # Set up SSL encryption
            ssl_success = database_security_manager.setup_ssl_encryption()
            if ssl_success:
                self.stdout.write('  ✓ SSL encryption configured')
            else:
                self.stdout.write(self.style.WARNING('  ⚠ SSL encryption configuration failed'))
            
            # Set up audit logging
            audit_success = database_security_manager.setup_audit_logging()
            if audit_success:
                self.stdout.write('  ✓ Audit logging configured')
            else:
                self.stdout.write(self.style.WARNING('  ⚠ Audit logging configuration failed'))
            
            # Create role-based database users
            self.stdout.write('Creating role-based database users...')
            user_results = database_security_manager.create_database_users()
            
            for username, success in user_results.items():
                if success:
                    self.stdout.write(f'  ✓ Created database user: {username}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Failed to create database user: {username}')
                    )
            
            # Configure field-level encryption for existing data
            self.stdout.write('Encrypting existing sensitive data...')
            
            sensitive_tables = [
                ('auth_user', ['email', 'first_name', 'last_name']),
                ('customers_customer', ['email', 'phone_number']),
            ]
            
            for table_name, fields in sensitive_tables:
                success = database_security_manager.encrypt_sensitive_data(table_name, fields)
                if success:
                    self.stdout.write(f'  ✓ Encrypted data in {table_name}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Failed to encrypt data in {table_name}')
                    )
            
            # Get security metrics
            metrics = database_security_manager.get_security_metrics()
            if metrics:
                self.stdout.write('\nSecurity metrics:')
                for event_type, stats in metrics.get('audit_statistics', [])[:5]:
                    self.stdout.write(
                        f'  {event_type}: {stats["total_count"]} total, '
                        f'{stats["successful"]} successful, {stats["failed"]} failed'
                    )
            
        except Exception as e:
            logger.error(f"Database security configuration failed: {e}")
            raise CommandError(f'Database security configuration failed: {e}')