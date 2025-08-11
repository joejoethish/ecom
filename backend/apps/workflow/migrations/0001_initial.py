# Generated manually for workflow app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('approval', 'Approval Process'), ('notification', 'Notification'), ('data_processing', 'Data Processing'), ('integration', 'System Integration'), ('customer_journey', 'Customer Journey'), ('supply_chain', 'Supply Chain'), ('financial', 'Financial Process'), ('custom', 'Custom')], max_length=50)),
                ('version', models.CharField(default='1.0.0', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_system_template', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'workflow_templates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('paused', 'Paused'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('trigger_type', models.CharField(choices=[('manual', 'Manual'), ('scheduled', 'Scheduled'), ('event', 'Event-based'), ('webhook', 'Webhook'), ('api', 'API Call')], default='manual', max_length=20)),
                ('trigger_config', models.JSONField(default=dict)),
                ('workflow_definition', models.JSONField(default=dict)),
                ('variables', models.JSONField(default=dict)),
                ('settings', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow.workflowtemplate')),
            ],
            options={
                'db_table': 'workflows',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowIntegration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('integration_type', models.CharField(choices=[('api', 'REST API'), ('webhook', 'Webhook'), ('email', 'Email'), ('sms', 'SMS'), ('database', 'Database'), ('file', 'File System'), ('ftp', 'FTP/SFTP'), ('cloud', 'Cloud Service')], max_length=20)),
                ('endpoint_url', models.URLField(blank=True)),
                ('authentication', models.JSONField(default=dict)),
                ('configuration', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'workflow_integrations',
            },
        ),
    ]