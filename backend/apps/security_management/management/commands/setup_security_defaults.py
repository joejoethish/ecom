from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.security_management.models import (
    SecurityPolicy, SecurityTraining, SecurityMonitoringRule,
    SecurityConfiguration, SecurityRiskAssessment
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up default security management configurations'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default security configurations...')
        
        # Create default admin user if not exists
        admin_user, created = User.objects.get_or_create(
            username='security_admin',
            defaults={
                'email': 'security@company.com',
                'first_name': 'Security',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('SecurePass123!')
            admin_user.save()
            self.stdout.write(f'Created security admin user: {admin_user.username}')
        
        # Create default security policies
        self.create_default_policies(admin_user)
        
        # Create default training programs
        self.create_default_training(admin_user)
        
        # Create default monitoring rules
        self.create_default_monitoring_rules(admin_user)
        
        # Create default configurations
        self.create_default_configurations(admin_user)
        
        # Create sample risk assessments
        self.create_sample_risk_assessments(admin_user)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up security management defaults')
        )

    def create_default_policies(self, admin_user):
        """Create default security policies"""
        policies = [
            {
                'policy_name': 'Password Policy',
                'policy_type': 'password',
                'description': 'Corporate password requirements and standards',
                'policy_content': '''
                Password Requirements:
                - Minimum 12 characters
                - Must contain uppercase, lowercase, numbers, and symbols
                - Cannot reuse last 12 passwords
                - Must be changed every 90 days
                - Account lockout after 5 failed attempts
                ''',
                'compliance_requirements': ['ISO 27001', 'NIST'],
                'enforcement_rules': [
                    'Automated password complexity validation',
                    'Password history enforcement',
                    'Regular password expiration notifications'
                ]
            },
            {
                'policy_name': 'Data Classification Policy',
                'policy_type': 'data_classification',
                'description': 'Guidelines for classifying and handling sensitive data',
                'policy_content': '''
                Data Classification Levels:
                - Public: No restrictions
                - Internal: Company employees only
                - Confidential: Authorized personnel only
                - Restricted: Highest security level
                ''',
                'compliance_requirements': ['GDPR', 'SOX'],
                'enforcement_rules': [
                    'Data labeling requirements',
                    'Access control based on classification',
                    'Encryption for confidential data'
                ]
            }
        ]
        
        for policy_data in policies:
            policy, created = SecurityPolicy.objects.get_or_create(
                policy_name=policy_data['policy_name'],
                defaults={
                    **policy_data,
                    'owner': admin_user,
                    'status': 'active',
                    'version': '1.0',
                    'effective_date': timezone.now(),
                    'review_date': timezone.now() + timedelta(days=365)
                }
            )
            if created:
                self.stdout.write(f'Created policy: {policy.policy_name}')

    def create_default_training(self, admin_user):
        """Create default training programs"""
        trainings = [
            {
                'training_name': 'Security Awareness Fundamentals',
                'training_type': 'security_awareness',
                'description': 'Basic security awareness training for all employees',
                'content': '''
                Topics covered:
                - Password security
                - Phishing recognition
                - Social engineering
                - Physical security
                - Incident reporting
                ''',
                'duration_minutes': 45,
                'required_for_roles': ['all_employees'],
                'completion_criteria': {'min_score': 80, 'max_attempts': 3}
            },
            {
                'training_name': 'Phishing Simulation Training',
                'training_type': 'phishing_simulation',
                'description': 'Interactive phishing simulation and training',
                'content': '''
                Simulation scenarios:
                - Email phishing attempts
                - Spear phishing targeting
                - Social media phishing
                - Response procedures
                ''',
                'duration_minutes': 30,
                'required_for_roles': ['all_employees'],
                'completion_criteria': {'min_score': 90, 'max_attempts': 2}
            }
        ]
        
        for training_data in trainings:
            training, created = SecurityTraining.objects.get_or_create(
                training_name=training_data['training_name'],
                defaults={
                    **training_data,
                    'created_by': admin_user,
                    'status': 'published'
                }
            )
            if created:
                self.stdout.write(f'Created training: {training.training_name}')

    def create_default_monitoring_rules(self, admin_user):
        """Create default monitoring rules"""
        rules = [
            {
                'rule_name': 'Failed Login Attempts',
                'rule_type': 'intrusion_detection',
                'description': 'Detect multiple failed login attempts',
                'rule_logic': 'failed_logins > 5 in 10 minutes',
                'conditions': {
                    'event_type': 'login_failure',
                    'threshold': 5,
                    'time_window': 600
                },
                'actions': [
                    'create_alert',
                    'lock_account',
                    'notify_admin'
                ],
                'severity': 'high'
            },
            {
                'rule_name': 'Unusual Data Access',
                'rule_type': 'anomaly_detection',
                'description': 'Detect unusual data access patterns',
                'rule_logic': 'data_access_volume > baseline * 3',
                'conditions': {
                    'metric': 'data_access_volume',
                    'comparison': 'greater_than',
                    'threshold_multiplier': 3
                },
                'actions': [
                    'create_alert',
                    'log_activity',
                    'require_approval'
                ],
                'severity': 'medium'
            }
        ]
        
        for rule_data in rules:
            rule, created = SecurityMonitoringRule.objects.get_or_create(
                rule_name=rule_data['rule_name'],
                defaults={
                    **rule_data,
                    'created_by': admin_user,
                    'status': 'active'
                }
            )
            if created:
                self.stdout.write(f'Created monitoring rule: {rule.rule_name}')

    def create_default_configurations(self, admin_user):
        """Create default security configurations"""
        configs = [
            {
                'config_name': 'Firewall Configuration',
                'config_type': 'firewall',
                'description': 'Main firewall security configuration',
                'configuration_data': {
                    'default_policy': 'deny',
                    'allowed_ports': [80, 443, 22],
                    'blocked_countries': ['CN', 'RU'],
                    'rate_limiting': True
                },
                'compliance_requirements': ['PCI DSS', 'ISO 27001']
            },
            {
                'config_name': 'Encryption Standards',
                'config_type': 'encryption',
                'description': 'Data encryption configuration standards',
                'configuration_data': {
                    'algorithm': 'AES-256',
                    'key_rotation': 90,
                    'tls_version': '1.3',
                    'cipher_suites': ['ECDHE-RSA-AES256-GCM-SHA384']
                },
                'compliance_requirements': ['FIPS 140-2', 'Common Criteria']
            }
        ]
        
        for config_data in configs:
            config, created = SecurityConfiguration.objects.get_or_create(
                config_name=config_data['config_name'],
                defaults={
                    **config_data,
                    'managed_by': admin_user,
                    'status': 'active',
                    'validation_status': 'valid'
                }
            )
            if created:
                self.stdout.write(f'Created configuration: {config.config_name}')

    def create_sample_risk_assessments(self, admin_user):
        """Create sample risk assessments"""
        assessments = [
            {
                'assessment_name': 'Web Application Security Assessment',
                'asset_category': 'Web Application',
                'asset_description': 'Customer-facing e-commerce web application',
                'threat_sources': [
                    'External hackers',
                    'Malicious insiders',
                    'Automated attacks'
                ],
                'vulnerabilities': [
                    'SQL injection potential',
                    'Cross-site scripting',
                    'Weak authentication'
                ],
                'existing_controls': [
                    'Web application firewall',
                    'Input validation',
                    'Regular security testing'
                ],
                'likelihood': 'medium',
                'impact': 'high',
                'risk_level': 'high',
                'risk_score': 12.0,
                'recommended_controls': [
                    'Enhanced input validation',
                    'Multi-factor authentication',
                    'Regular penetration testing'
                ],
                'residual_risk': 'medium'
            }
        ]
        
        for assessment_data in assessments:
            assessment, created = SecurityRiskAssessment.objects.get_or_create(
                assessment_name=assessment_data['assessment_name'],
                defaults={
                    **assessment_data,
                    'assessor': admin_user,
                    'status': 'approved',
                    'review_date': timezone.now() + timedelta(days=180)
                }
            )
            if created:
                self.stdout.write(f'Created risk assessment: {assessment.assessment_name}')