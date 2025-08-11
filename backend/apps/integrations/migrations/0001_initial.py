# Generated migration for integrations app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IntegrationCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('category', models.CharField(choices=[('payment', 'Payment Gateways'), ('shipping', 'Shipping Carriers'), ('crm', 'CRM Systems'), ('accounting', 'Accounting Systems'), ('marketing', 'Marketing Platforms'), ('social', 'Social Media'), ('analytics', 'Analytics Platforms'), ('inventory', 'Inventory Management'), ('erp', 'ERP Systems'), ('warehouse', 'Warehouse Management'), ('support', 'Customer Service'), ('bi', 'Business Intelligence'), ('ecommerce', 'E-commerce Platforms'), ('marketplace', 'Marketplaces'), ('communication', 'Communication'), ('document', 'Document Management'), ('project', 'Project Management'), ('storage', 'Storage Services'), ('security', 'Security Services'), ('monitoring', 'Monitoring Services'), ('compliance', 'Compliance Services')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'integration_categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='IntegrationProvider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('website_url', models.URLField()),
                ('documentation_url', models.URLField(blank=True)),
                ('logo_url', models.URLField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('deprecated', 'Deprecated'), ('beta', 'Beta')], default='active', max_length=20)),
                ('api_version', models.CharField(blank=True, max_length=20)),
                ('supported_features', models.JSONField(default=list)),
                ('pricing_model', models.CharField(blank=True, max_length=100)),
                ('is_popular', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integrationcategory')),
            ],
            options={
                'db_table': 'integration_providers',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('error', 'Error'), ('testing', 'Testing'), ('pending', 'Pending Setup')], default='pending', max_length=20)),
                ('environment', models.CharField(choices=[('production', 'Production'), ('sandbox', 'Sandbox'), ('development', 'Development')], default='production', max_length=20)),
                ('configuration', models.JSONField(default=dict)),
                ('webhook_url', models.URLField(blank=True)),
                ('webhook_secret', models.CharField(blank=True, max_length=255)),
                ('api_key', models.CharField(blank=True, max_length=255)),
                ('api_secret', models.CharField(blank=True, max_length=255)),
                ('access_token', models.TextField(blank=True)),
                ('refresh_token', models.TextField(blank=True)),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('sync_frequency', models.IntegerField(default=3600)),
                ('auto_sync', models.BooleanField(default=True)),
                ('error_count', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integrationprovider')),
            ],
            options={
                'db_table': 'integrations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='IntegrationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('configuration_template', models.JSONField(default=dict)),
                ('mapping_template', models.JSONField(default=dict)),
                ('webhook_template', models.JSONField(default=dict)),
                ('setup_instructions', models.TextField()),
                ('is_official', models.BooleanField(default=False)),
                ('usage_count', models.IntegerField(default=0)),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integrationprovider')),
            ],
            options={
                'db_table': 'integration_templates',
                'ordering': ['-rating', '-usage_count'],
            },
        ),
        migrations.CreateModel(
            name='IntegrationSync',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sync_type', models.CharField(choices=[('full', 'Full Sync'), ('incremental', 'Incremental Sync'), ('manual', 'Manual Sync'), ('scheduled', 'Scheduled Sync')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('records_processed', models.IntegerField(default=0)),
                ('records_created', models.IntegerField(default=0)),
                ('records_updated', models.IntegerField(default=0)),
                ('records_failed', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('sync_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
            ],
            options={
                'db_table': 'integration_syncs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='IntegrationWebhook',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('order.created', 'Order Created'), ('order.updated', 'Order Updated'), ('order.cancelled', 'Order Cancelled'), ('payment.completed', 'Payment Completed'), ('payment.failed', 'Payment Failed'), ('product.created', 'Product Created'), ('product.updated', 'Product Updated'), ('inventory.updated', 'Inventory Updated'), ('customer.created', 'Customer Created'), ('customer.updated', 'Customer Updated')], max_length=50)),
                ('webhook_url', models.URLField()),
                ('secret_key', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('retry_count', models.IntegerField(default=3)),
                ('timeout', models.IntegerField(default=30)),
                ('headers', models.JSONField(default=dict)),
                ('payload_template', models.JSONField(default=dict)),
                ('last_triggered_at', models.DateTimeField(blank=True, null=True)),
                ('success_count', models.IntegerField(default=0)),
                ('failure_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
            ],
            options={
                'db_table': 'integration_webhooks',
            },
        ),
        migrations.CreateModel(
            name='IntegrationMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mapping_type', models.CharField(choices=[('field', 'Field Mapping'), ('value', 'Value Mapping'), ('transform', 'Data Transform')], max_length=20)),
                ('source_field', models.CharField(max_length=100)),
                ('target_field', models.CharField(max_length=100)),
                ('transformation_rule', models.JSONField(default=dict)),
                ('is_required', models.BooleanField(default=False)),
                ('default_value', models.CharField(blank=True, max_length=255)),
                ('validation_rule', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
            ],
            options={
                'db_table': 'integration_mappings',
            },
        ),
        migrations.CreateModel(
            name='IntegrationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('level', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('debug', 'Debug')], max_length=10)),
                ('action_type', models.CharField(choices=[('sync', 'Data Sync'), ('webhook', 'Webhook'), ('api_call', 'API Call'), ('auth', 'Authentication'), ('config', 'Configuration'), ('test', 'Test')], max_length=20)),
                ('message', models.TextField()),
                ('details', models.JSONField(default=dict)),
                ('request_data', models.JSONField(blank=True, null=True)),
                ('response_data', models.JSONField(blank=True, null=True)),
                ('execution_time', models.FloatField(blank=True, null=True)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
            ],
            options={
                'db_table': 'integration_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='integrationwebhook',
            constraint=models.UniqueConstraint(fields=('integration', 'event_type'), name='unique_integration_event'),
        ),
        migrations.AddConstraint(
            model_name='integrationmapping',
            constraint=models.UniqueConstraint(fields=('integration', 'source_field', 'target_field'), name='unique_integration_mapping'),
        ),
        migrations.AddIndex(
            model_name='integrationlog',
            index=models.Index(fields=['integration', '-created_at'], name='integration_logs_integration_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationlog',
            index=models.Index(fields=['level', '-created_at'], name='integration_logs_level_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationlog',
            index=models.Index(fields=['action_type', '-created_at'], name='integration_logs_action_type_created_at_idx'),
        ),
    ]