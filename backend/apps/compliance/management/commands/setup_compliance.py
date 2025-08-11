from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from backend.apps.compliance.models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial compliance system configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Create compliance user groups and permissions',
        )
        parser.add_argument(
            '--create-frameworks',
            action='store_true',
            help='Create default compliance frameworks',
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create compliance admin user',
        )
    
    def handle(self, *args, **options):
        if options['create_groups']:
            self.create_compliance_groups()
        
        if options['create_frameworks']:
            self.create_default_frameworks()
        
        if options['create_admin']:
            self.create_compliance_admin()
        
        self.stdout.write(
            self.style.SUCCESS('Compliance system setup completed successfully!')
        )
    
    def create_compliance_groups(self):
        """Create compliance user groups with appropriate permissions"""
        self.stdout.write('Creating compliance groups and permissions...')
        
        # Define compliance roles and their permissions
        compliance_roles = {
            'Compliance Admin': {
                'permissions': 'all',
                'description': 'Full access to all compliance functions'
            },
            'Compliance Manager': {
                'permissions': [
                    'view', 'add', 'change', 'delete', 'approve', 'assign',
                    'conduct', 'resolve', 'assess', 'mitigate', 'generate'
                ],
                'description': 'Management level access to compliance functions'
            },
            'Compliance Officer': {
                'permissions': [
                    'view', 'add', 'change', 'assign', 'conduct',
                    'resolve', 'assess', 'generate'
                ],
                'description': 'Operational access to compliance functions'
            },
            'Compliance Analyst': {
                'permissions': [
                    'view', 'add', 'change', 'generate'
                ],
                'description': 'Data entry and analysis access'
            },
            'Compliance Viewer': {
                'permissions': ['view'],
                'description': 'Read-only access to compliance data'
            }
        }
        
        # Get all compliance models
        compliance_models = [
            ComplianceFramework, CompliancePolicy, ComplianceControl,
            ComplianceAssessment, ComplianceIncident, ComplianceTraining,
            ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
            ComplianceVendor, ComplianceReport
        ]
        
        for role_name, role_config in compliance_roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                self.stdout.write(f'Created group: {role_name}')
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions based on role configuration
            for model in compliance_models:
                content_type = ContentType.objects.get_for_model(model)
                
                if role_config['permissions'] == 'all':
                    # Add all permissions for this model
                    permissions = Permission.objects.filter(content_type=content_type)
                    group.permissions.add(*permissions)
                else:
                    # Add specific permissions
                    for perm_type in role_config['permissions']:
                        try:
                            permission = Permission.objects.get(
                                content_type=content_type,
                                codename__startswith=perm_type
                            )
                            group.permissions.add(permission)
                        except Permission.DoesNotExist:
                            # Create custom permissions if they don't exist
                            permission, created = Permission.objects.get_or_create(
                                codename=f'{perm_type}_{model._meta.model_name}',
                                name=f'Can {perm_type} {model._meta.verbose_name}',
                                content_type=content_type
                            )
                            group.permissions.add(permission)
            
            self.stdout.write(f'Configured permissions for: {role_name}')
    
    def create_default_frameworks(self):
        """Create default compliance frameworks"""
        self.stdout.write('Creating default compliance frameworks...')
        
        default_frameworks = [
            {
                'name': 'General Data Protection Regulation',
                'framework_type': 'gdpr',
                'description': 'EU regulation on data protection and privacy',
                'version': '2018.1',
                'effective_date': '2018-05-25',
                'requirements': {
                    'data_protection': ['consent', 'data_minimization', 'purpose_limitation'],
                    'rights': ['access', 'rectification', 'erasure', 'portability'],
                    'governance': ['dpo_appointment', 'impact_assessments', 'breach_notification']
                }
            },
            {
                'name': 'California Consumer Privacy Act',
                'framework_type': 'ccpa',
                'description': 'California state statute intended to enhance privacy rights',
                'version': '2020.1',
                'effective_date': '2020-01-01',
                'requirements': {
                    'consumer_rights': ['know', 'delete', 'opt_out', 'non_discrimination'],
                    'business_obligations': ['disclosure', 'deletion', 'opt_out_mechanisms']
                }
            },
            {
                'name': 'Sarbanes-Oxley Act',
                'framework_type': 'sox',
                'description': 'US federal law for corporate financial reporting',
                'version': '2002.1',
                'effective_date': '2002-07-30',
                'requirements': {
                    'financial_reporting': ['internal_controls', 'management_assessment'],
                    'auditing': ['independence', 'audit_committee', 'external_audit']
                }
            },
            {
                'name': 'ISO 27001 Information Security',
                'framework_type': 'iso_27001',
                'description': 'International standard for information security management',
                'version': '2013.1',
                'effective_date': '2013-10-01',
                'requirements': {
                    'isms': ['policy', 'risk_assessment', 'treatment'],
                    'controls': ['access_control', 'cryptography', 'incident_management']
                }
            }
        ]
        
        for framework_data in default_frameworks:
            framework, created = ComplianceFramework.objects.get_or_create(
                name=framework_data['name'],
                defaults=framework_data
            )
            
            if created:
                self.stdout.write(f'Created framework: {framework.name}')
            else:
                self.stdout.write(f'Framework already exists: {framework.name}')
    
    def create_compliance_admin(self):
        """Create a compliance admin user"""
        self.stdout.write('Creating compliance admin user...')
        
        username = 'compliance_admin'
        email = 'compliance@company.com'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'User {username} already exists')
            return
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='CompliantAdmin123!',
            first_name='Compliance',
            last_name='Administrator',
            is_staff=True
        )
        
        # Add to Compliance Admin group
        try:
            admin_group = Group.objects.get(name='Compliance Admin')
            user.groups.add(admin_group)
        except Group.DoesNotExist:
            self.stdout.write('Compliance Admin group not found. Run with --create-groups first.')
        
        self.stdout.write(f'Created compliance admin user: {username}')
        self.stdout.write(f'Default password: CompliantAdmin123!')
        self.stdout.write('Please change the password after first login.')