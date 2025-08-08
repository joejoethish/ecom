"""
Initial migration for admin panel with comprehensive schema.
"""
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.auth.models
import django.utils.timezone
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Create AdminUser table
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('manager', 'Manager'), ('analyst', 'Analyst'), ('support', 'Support'), ('viewer', 'Viewer')], default='viewer', max_length=20)),
                ('department', models.CharField(blank=True, choices=[('it', 'IT Department'), ('sales', 'Sales Department'), ('marketing', 'Marketing Department'), ('customer_service', 'Customer Service'), ('finance', 'Finance Department'), ('operations', 'Operations'), ('hr', 'Human Resources'), ('management', 'Management')], max_length=50)),
                ('phone', models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='admin_avatars/')),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('failed_login_attempts', models.IntegerField(default=0)),
                ('account_locked_until', models.DateTimeField(blank=True, null=True)),
                ('password_changed_at', models.DateTimeField(auto_now_add=True)),
                ('must_change_password', models.BooleanField(default=False)),
                ('two_factor_enabled', models.BooleanField(default=False)),
                ('two_factor_secret', models.CharField(blank=True, max_length=32)),
                ('backup_codes', models.JSONField(blank=True, default=list)),
                ('max_concurrent_sessions', models.IntegerField(default=3)),
                ('session_timeout_minutes', models.IntegerField(default=60)),
                ('is_admin_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_admins', to='admin_panel.adminuser')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='admin_user_set', related_query_name='admin_user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='admin_user_set', related_query_name='admin_user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Admin User',
                'verbose_name_plural': 'Admin Users',
                'db_table': 'admin_users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        
        # Create AdminPermission table
        migrations.CreateModel(
            name='AdminPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('codename', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('module', models.CharField(choices=[('dashboard', 'Dashboard'), ('products', 'Products'), ('orders', 'Orders'), ('customers', 'Customers'), ('inventory', 'Inventory'), ('analytics', 'Analytics'), ('reports', 'Reports'), ('settings', 'Settings'), ('users', 'User Management'), ('content', 'Content Management'), ('promotions', 'Promotions'), ('shipping', 'Shipping'), ('payments', 'Payments'), ('notifications', 'Notifications'), ('system', 'System Administration')], max_length=50)),
                ('action', models.CharField(choices=[('view', 'View'), ('create', 'Create'), ('edit', 'Edit'), ('delete', 'Delete'), ('export', 'Export'), ('import', 'Import'), ('approve', 'Approve'), ('publish', 'Publish'), ('manage', 'Manage'), ('configure', 'Configure')], max_length=20)),
                ('resource', models.CharField(blank=True, max_length=100)),
                ('is_sensitive', models.BooleanField(default=False)),
                ('requires_mfa', models.BooleanField(default=False)),
                ('ip_restricted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_system_permission', models.BooleanField(default=False)),
                ('depends_on', models.ManyToManyField(blank=True, related_name='dependents', to='admin_panel.adminpermission')),
            ],
            options={
                'verbose_name': 'Admin Permission',
                'verbose_name_plural': 'Admin Permissions',
                'db_table': 'admin_permissions',
                'ordering': ['module', 'action', 'resource'],
            },
        ),
        
        # Create AdminRole table
        migrations.CreateModel(
            name='AdminRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('level', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_system_role', models.BooleanField(default=False)),
                ('parent_role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_roles', to='admin_panel.adminrole')),
                ('permissions', models.ManyToManyField(blank=True, related_name='roles', to='admin_panel.adminpermission')),
            ],
            options={
                'verbose_name': 'Admin Role',
                'verbose_name_plural': 'Admin Roles',
                'db_table': 'admin_roles',
                'ordering': ['level', 'name'],
            },
        ),
        
        # Create SystemSettings table
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('key', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('value', models.TextField()),
                ('default_value', models.TextField(blank=True)),
                ('setting_type', models.CharField(choices=[('string', 'String'), ('integer', 'Integer'), ('float', 'Float'), ('boolean', 'Boolean'), ('json', 'JSON'), ('text', 'Text'), ('email', 'Email'), ('url', 'URL'), ('password', 'Password'), ('file', 'File')], default='string', max_length=20)),
                ('category', models.CharField(choices=[('general', 'General Settings'), ('email', 'Email Configuration'), ('sms', 'SMS Configuration'), ('payment', 'Payment Settings'), ('shipping', 'Shipping Settings'), ('tax', 'Tax Configuration'), ('security', 'Security Settings'), ('performance', 'Performance Settings'), ('seo', 'SEO Settings'), ('social', 'Social Media'), ('analytics', 'Analytics'), ('backup', 'Backup Settings'), ('maintenance', 'Maintenance'), ('api', 'API Configuration'), ('integration', 'Third-party Integrations')], max_length=50)),
                ('subcategory', models.CharField(blank=True, max_length=100)),
                ('validation_rules', models.JSONField(blank=True, default=dict)),
                ('options', models.JSONField(blank=True, default=list)),
                ('is_public', models.BooleanField(default=False)),
                ('is_encrypted', models.BooleanField(default=False)),
                ('requires_restart', models.BooleanField(default=False)),
                ('is_system_setting', models.BooleanField(default=False)),
                ('version', models.IntegerField(default=1)),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'System Setting',
                'verbose_name_plural': 'System Settings',
                'db_table': 'system_settings',
                'ordering': ['category', 'subcategory', 'name'],
            },
        ),
        
        # Create ActivityLog table
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session_key', models.CharField(blank=True, max_length=40)),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('view', 'View'), ('login', 'Login'), ('logout', 'Logout'), ('export', 'Export'), ('import', 'Import'), ('approve', 'Approve'), ('reject', 'Reject'), ('publish', 'Publish'), ('unpublish', 'Unpublish'), ('error', 'Error'), ('security', 'Security Event')], max_length=20)),
                ('description', models.TextField()),
                ('object_id', models.CharField(blank=True, max_length=100)),
                ('changes', models.JSONField(blank=True, default=dict)),
                ('additional_data', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('request_method', models.CharField(blank=True, max_length=10)),
                ('request_path', models.CharField(blank=True, max_length=500)),
                ('module', models.CharField(blank=True, max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', max_length=10)),
                ('is_successful', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
                ('admin_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.adminuser')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Activity Log',
                'verbose_name_plural': 'Activity Logs',
                'db_table': 'activity_logs',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create AdminSession table
        migrations.CreateModel(
            name='AdminSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session_key', models.CharField(max_length=40, unique=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('device_type', models.CharField(blank=True, max_length=50)),
                ('browser', models.CharField(blank=True, max_length=100)),
                ('os', models.CharField(blank=True, max_length=100)),
                ('location', models.CharField(blank=True, max_length=200)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('is_trusted_device', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('is_suspicious', models.BooleanField(default=False)),
                ('security_score', models.IntegerField(default=100)),
                ('admin_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_sessions', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Admin Session',
                'verbose_name_plural': 'Admin Sessions',
                'db_table': 'admin_sessions',
                'ordering': ['-last_activity'],
            },
        ),
        
        # Create AdminNotification table
        migrations.CreateModel(
            name='AdminNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('error', 'Error'), ('success', 'Success'), ('security', 'Security Alert'), ('system', 'System Notification'), ('task', 'Task Notification'), ('reminder', 'Reminder')], default='info', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=10)),
                ('object_id', models.CharField(blank=True, max_length=100)),
                ('action_url', models.CharField(blank=True, max_length=500)),
                ('action_label', models.CharField(blank=True, max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('is_dismissed', models.BooleanField(default=False)),
                ('dismissed_at', models.DateTimeField(blank=True, null=True)),
                ('scheduled_for', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='admin_panel.adminuser')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_notifications', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Admin Notification',
                'verbose_name_plural': 'Admin Notifications',
                'db_table': 'admin_notifications',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create AdminLoginAttempt table
        migrations.CreateModel(
            name='AdminLoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(max_length=150)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField()),
                ('is_successful', models.BooleanField(default=False)),
                ('failure_reason', models.CharField(blank=True, max_length=100)),
                ('is_suspicious', models.BooleanField(default=False)),
                ('risk_score', models.IntegerField(default=0)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('admin_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='login_attempts', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Admin Login Attempt',
                'verbose_name_plural': 'Admin Login Attempts',
                'db_table': 'admin_login_attempts',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create AdminReport table
        migrations.CreateModel(
            name='AdminReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('report_type', models.CharField(choices=[('sales', 'Sales Report'), ('inventory', 'Inventory Report'), ('customer', 'Customer Report'), ('financial', 'Financial Report'), ('activity', 'Activity Report'), ('security', 'Security Report'), ('performance', 'Performance Report'), ('custom', 'Custom Report')], max_length=20)),
                ('query_config', models.JSONField(default=dict)),
                ('format', models.CharField(choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV'), ('json', 'JSON')], default='pdf', max_length=10)),
                ('schedule_type', models.CharField(choices=[('once', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], default='once', max_length=20)),
                ('schedule_config', models.JSONField(default=dict)),
                ('next_run', models.DateTimeField(blank=True, null=True)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('email_recipients', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('total_runs', models.IntegerField(default=0)),
                ('successful_runs', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_reports', to='admin_panel.adminuser')),
                ('recipients', models.ManyToManyField(blank=True, related_name='subscribed_reports', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Admin Report',
                'verbose_name_plural': 'Admin Reports',
                'db_table': 'admin_reports',
                'ordering': ['name'],
            },
        ),
        
        # Add AdminUser permissions relationship
        migrations.AddField(
            model_name='adminuser',
            name='permissions',
            field=models.ManyToManyField(blank=True, related_name='admin_users', to='admin_panel.adminpermission'),
        ),
    ]