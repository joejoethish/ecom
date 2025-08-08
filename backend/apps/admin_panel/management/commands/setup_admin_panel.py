"""
Management command to set up initial admin panel data.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.admin_panel.models import (
    AdminUser, AdminRole, AdminPermission, SystemSettings
)


class Command(BaseCommand):
    help = 'Set up initial admin panel data including roles, permissions, and settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a default super admin user',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up admin panel...')
        
        with transaction.atomic():
            # Create permissions
            self.create_permissions()
            
            # Create roles
            self.create_roles()
            
            # Create system settings
            self.create_system_settings()
            
            # Create super admin user if requested
            if options['create_superuser']:
                self.create_superuser()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up admin panel!')
        )

    def create_permissions(self):
        """Create all admin permissions."""
        self.stdout.write('Creating admin permissions...')
        
        permissions_data = [
            # Dashboard permissions
            ('dashboard.view.all', 'View Dashboard', 'dashboard', 'view', ''),
            ('dashboard.view.stats', 'View Dashboard Stats', 'dashboard', 'view', 'stats'),
            
            # Product permissions
            ('products.view.all', 'View Products', 'products', 'view', ''),
            ('products.create.all', 'Create Products', 'products', 'create', ''),
            ('products.edit.all', 'Edit Products', 'products', 'edit', ''),
            ('products.delete.all', 'Delete Products', 'products', 'delete', ''),
            ('products.export.all', 'Export Products', 'products', 'export', ''),
            ('products.import.all', 'Import Products', 'products', 'import', ''),
            
            # Order permissions
            ('orders.view.all', 'View Orders', 'orders', 'view', ''),
            ('orders.edit.all', 'Edit Orders', 'orders', 'edit', ''),
            ('orders.delete.all', 'Delete Orders', 'orders', 'delete', ''),
            ('orders.export.all', 'Export Orders', 'orders', 'export', ''),
            
            # Customer permissions
            ('customers.view.all', 'View Customers', 'customers', 'view', ''),
            ('customers.edit.all', 'Edit Customers', 'customers', 'edit', ''),
            ('customers.delete.all', 'Delete Customers', 'customers', 'delete', ''),
            ('customers.export.all', 'Export Customers', 'customers', 'export', ''),
            
            # Inventory permissions
            ('inventory.view.all', 'View Inventory', 'inventory', 'view', ''),
            ('inventory.edit.all', 'Edit Inventory', 'inventory', 'edit', ''),
            ('inventory.manage.all', 'Manage Inventory', 'inventory', 'manage', ''),
            
            # Analytics permissions
            ('analytics.view.all', 'View Analytics', 'analytics', 'view', ''),
            ('analytics.export.all', 'Export Analytics', 'analytics', 'export', ''),
            
            # Reports permissions
            ('reports.view.all', 'View Reports', 'reports', 'view', ''),
            ('reports.create.all', 'Create Reports', 'reports', 'create', ''),
            ('reports.export.all', 'Export Reports', 'reports', 'export', ''),
            
            # Settings permissions (sensitive)
            ('settings.view.all', 'View Settings', 'settings', 'view', ''),
            ('settings.edit.all', 'Edit Settings', 'settings', 'edit', ''),
            ('settings.configure.all', 'Configure Settings', 'settings', 'configure', ''),
            
            # User management permissions (sensitive)
            ('users.view.all', 'View Users', 'users', 'view', ''),
            ('users.create.all', 'Create Users', 'users', 'create', ''),
            ('users.edit.all', 'Edit Users', 'users', 'edit', ''),
            ('users.delete.all', 'Delete Users', 'users', 'delete', ''),
            
            # System administration (critical)
            ('system.manage.all', 'System Administration', 'system', 'manage', ''),
            ('system.configure.all', 'System Configuration', 'system', 'configure', ''),
        ]
        
        for codename, name, module, action, resource in permissions_data:
            permission, created = AdminPermission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'module': module,
                    'action': action,
                    'resource': resource,
                    'is_sensitive': module in ['settings', 'users', 'system'],
                    'requires_mfa': module == 'system',
                    'is_system_permission': True,
                }
            )
            if created:
                self.stdout.write(f'  Created permission: {codename}')

    def create_roles(self):
        """Create admin roles with hierarchical structure."""
        self.stdout.write('Creating admin roles...')
        
        # Create Super Admin role (level 0)
        super_admin_role, created = AdminRole.objects.get_or_create(
            name='super_admin',
            defaults={
                'display_name': 'Super Administrator',
                'description': 'Full system access with all permissions',
                'level': 0,
                'is_system_role': True,
            }
        )
        if created:
            # Assign all permissions to super admin
            super_admin_role.permissions.set(AdminPermission.objects.all())
            self.stdout.write('  Created Super Admin role')
        
        # Create Admin role (level 1)
        admin_role, created = AdminRole.objects.get_or_create(
            name='admin',
            defaults={
                'display_name': 'Administrator',
                'description': 'Administrative access with most permissions',
                'level': 1,
                'parent_role': super_admin_role,
                'is_system_role': True,
            }
        )
        if created:
            # Assign most permissions except system administration
            permissions = AdminPermission.objects.exclude(module='system')
            admin_role.permissions.set(permissions)
            self.stdout.write('  Created Admin role')
        
        # Create Manager role (level 2)
        manager_role, created = AdminRole.objects.get_or_create(
            name='manager',
            defaults={
                'display_name': 'Manager',
                'description': 'Management access for business operations',
                'level': 2,
                'parent_role': admin_role,
                'is_system_role': True,
            }
        )
        if created:
            # Assign business-related permissions
            permissions = AdminPermission.objects.filter(
                module__in=['dashboard', 'products', 'orders', 'customers', 'inventory', 'analytics', 'reports']
            ).exclude(action='delete')
            manager_role.permissions.set(permissions)
            self.stdout.write('  Created Manager role')
        
        # Create Analyst role (level 3)
        analyst_role, created = AdminRole.objects.get_or_create(
            name='analyst',
            defaults={
                'display_name': 'Analyst',
                'description': 'Read-only access for analysis and reporting',
                'level': 3,
                'parent_role': manager_role,
                'is_system_role': True,
            }
        )
        if created:
            # Assign view and export permissions
            permissions = AdminPermission.objects.filter(
                action__in=['view', 'export']
            )
            analyst_role.permissions.set(permissions)
            self.stdout.write('  Created Analyst role')

    def create_system_settings(self):
        """Create initial system settings."""
        self.stdout.write('Creating system settings...')
        
        settings_data = [
            # General settings
            ('site_name', 'Site Name', 'E-Commerce Admin Panel', 'string', 'general'),
            ('site_description', 'Site Description', 'Comprehensive admin panel for e-commerce management', 'text', 'general'),
            ('admin_email', 'Admin Email', 'admin@example.com', 'email', 'general'),
            ('timezone', 'Timezone', 'UTC', 'string', 'general'),
            
            # Security settings
            ('session_timeout', 'Session Timeout (minutes)', '60', 'integer', 'security'),
            ('max_login_attempts', 'Max Login Attempts', '5', 'integer', 'security'),
            ('lockout_duration', 'Account Lockout Duration (minutes)', '60', 'integer', 'security'),
            ('require_2fa', 'Require Two-Factor Authentication', 'false', 'boolean', 'security'),
            ('password_min_length', 'Minimum Password Length', '8', 'integer', 'security'),
            
            # Performance settings
            ('cache_timeout', 'Cache Timeout (seconds)', '3600', 'integer', 'performance'),
            ('page_size', 'Default Page Size', '20', 'integer', 'performance'),
            ('max_export_records', 'Max Export Records', '10000', 'integer', 'performance'),
            
            # Email settings
            ('email_enabled', 'Email Notifications Enabled', 'true', 'boolean', 'email'),
            ('smtp_host', 'SMTP Host', 'localhost', 'string', 'email'),
            ('smtp_port', 'SMTP Port', '587', 'integer', 'email'),
            ('smtp_use_tls', 'SMTP Use TLS', 'true', 'boolean', 'email'),
            
            # Backup settings
            ('backup_enabled', 'Backup Enabled', 'true', 'boolean', 'backup'),
            ('backup_retention_days', 'Backup Retention (days)', '30', 'integer', 'backup'),
            ('backup_schedule', 'Backup Schedule', 'daily', 'string', 'backup'),
        ]
        
        for key, name, value, setting_type, category in settings_data:
            setting, created = SystemSettings.objects.get_or_create(
                key=key,
                defaults={
                    'name': name,
                    'value': value,
                    'default_value': value,
                    'setting_type': setting_type,
                    'category': category,
                    'is_system_setting': True,
                }
            )
            if created:
                self.stdout.write(f'  Created setting: {key}')

    def create_superuser(self):
        """Create a default super admin user."""
        self.stdout.write('Creating super admin user...')
        
        if not AdminUser.objects.filter(username='superadmin').exists():
            super_admin = AdminUser.objects.create_user(
                username='superadmin',
                email='admin@example.com',
                password='admin123',  # Should be changed immediately
                role='super_admin',
                department='management',
                is_staff=True,
                is_superuser=True,
                must_change_password=True,
            )
            
            # Assign super admin role permissions
            try:
                super_admin_role = AdminRole.objects.get(name='super_admin')
                super_admin.permissions.set(super_admin_role.permissions.all())
            except AdminRole.DoesNotExist:
                pass
            
            self.stdout.write(
                self.style.WARNING(
                    'Created super admin user: superadmin / admin123 '
                    '(CHANGE PASSWORD IMMEDIATELY!)'
                )
            )
        else:
            self.stdout.write('Super admin user already exists')