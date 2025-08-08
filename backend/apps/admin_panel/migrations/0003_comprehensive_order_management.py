# Generated migration for comprehensive order management system

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_simple_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderSearchFilter',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('filters', models.JSONField(help_text='Saved filter criteria')),
                ('is_public', models.BooleanField(default=False, help_text='Available to all admin users')),
                ('admin_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_order_filters', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='OrderWorkflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('from_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('returned', 'Returned')], max_length=20)),
                ('to_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('returned', 'Returned')], max_length=20)),
                ('conditions', models.JSONField(help_text='Conditions that must be met for this workflow')),
                ('actions', models.JSONField(help_text='Actions to perform when workflow is triggered')),
                ('is_automatic', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.IntegerField(default=0, help_text='Higher priority workflows are processed first')),
            ],
            options={
                'ordering': ['-priority', 'name'],
            },
        ),
        migrations.CreateModel(
            name='OrderFraudScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('score', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('risk_level', models.CharField(choices=[('low', 'Low Risk'), ('medium', 'Medium Risk'), ('high', 'High Risk'), ('critical', 'Critical Risk')], max_length=20)),
                ('risk_factors', models.JSONField(help_text='List of identified risk factors')),
                ('is_flagged', models.BooleanField(default=False)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_fraud_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-score', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note_type', models.CharField(choices=[('internal', 'Internal Note'), ('customer', 'Customer Communication'), ('system', 'System Generated'), ('escalation', 'Escalation Note')], default='internal', max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('is_important', models.BooleanField(default=False)),
                ('is_customer_visible', models.BooleanField(default=False)),
                ('attachments', models.JSONField(blank=True, default=list, help_text='List of attachment file paths')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_notes', to=settings.AUTH_USER_MODEL)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderEscalation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('escalation_type', models.CharField(choices=[('payment_issue', 'Payment Issue'), ('inventory_shortage', 'Inventory Shortage'), ('shipping_delay', 'Shipping Delay'), ('customer_complaint', 'Customer Complaint'), ('fraud_alert', 'Fraud Alert'), ('system_error', 'System Error'), ('manual_review', 'Manual Review Required'), ('other', 'Other')], max_length=30)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='open', max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('sla_deadline', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_escalations', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_escalations', to=settings.AUTH_USER_MODEL)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_escalations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-priority', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderSLA',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processing_deadline', models.DateTimeField(blank=True, null=True)),
                ('shipping_deadline', models.DateTimeField(blank=True, null=True)),
                ('delivery_deadline', models.DateTimeField(blank=True, null=True)),
                ('processing_completed_at', models.DateTimeField(blank=True, null=True)),
                ('shipping_completed_at', models.DateTimeField(blank=True, null=True)),
                ('delivery_completed_at', models.DateTimeField(blank=True, null=True)),
                ('processing_sla_met', models.BooleanField(blank=True, null=True)),
                ('shipping_sla_met', models.BooleanField(blank=True, null=True)),
                ('delivery_sla_met', models.BooleanField(blank=True, null=True)),
                ('overall_sla_met', models.BooleanField(blank=True, null=True)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'verbose_name': 'Order SLA',
                'verbose_name_plural': 'Order SLAs',
            },
        ),
        migrations.CreateModel(
            name='OrderAllocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('allocated', 'Allocated'), ('partially_allocated', 'Partially Allocated'), ('failed', 'Failed'), ('released', 'Released')], default='pending', max_length=30)),
                ('allocated_at', models.DateTimeField(blank=True, null=True)),
                ('allocation_details', models.JSONField(default=dict, help_text='Details of inventory allocation per item')),
                ('reservation_expires_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('allocated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_allocations', to=settings.AUTH_USER_MODEL)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderProfitability',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gross_revenue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('net_revenue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('product_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('payment_processing_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('packaging_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('handling_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('marketing_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('other_costs', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('gross_profit', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('net_profit', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('profit_margin_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('cost_breakdown', models.JSONField(default=dict, help_text='Detailed cost breakdown')),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'verbose_name_plural': 'Order Profitabilities',
            },
        ),
        migrations.CreateModel(
            name='OrderDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_type', models.CharField(choices=[('invoice', 'Invoice'), ('receipt', 'Receipt'), ('shipping_label', 'Shipping Label'), ('packing_slip', 'Packing Slip'), ('return_label', 'Return Label'), ('customs_declaration', 'Customs Declaration'), ('delivery_confirmation', 'Delivery Confirmation'), ('other', 'Other')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('file_path', models.CharField(max_length=500)),
                ('file_size', models.PositiveIntegerField(help_text='File size in bytes')),
                ('mime_type', models.CharField(max_length=100)),
                ('is_customer_accessible', models.BooleanField(default=False)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('last_downloaded_at', models.DateTimeField(blank=True, null=True)),
                ('generated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_documents', to=settings.AUTH_USER_MODEL)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderQualityControl',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending Inspection'), ('in_progress', 'In Progress'), ('passed', 'Passed'), ('failed', 'Failed'), ('conditional_pass', 'Conditional Pass')], default='pending', max_length=20)),
                ('inspection_date', models.DateTimeField(blank=True, null=True)),
                ('checklist', models.JSONField(default=dict, help_text='Quality control checklist items')),
                ('issues_found', models.JSONField(default=list, help_text='List of issues found during inspection')),
                ('corrective_actions', models.JSONField(default=list, help_text='Corrective actions taken')),
                ('notes', models.TextField(blank=True)),
                ('requires_reinspection', models.BooleanField(default=False)),
                ('inspector', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qc_inspections', to=settings.AUTH_USER_MODEL)),
                ('order_id', models.UUIDField(help_text='Reference to order ID')),
            ],
            options={
                'verbose_name': 'Order Quality Control',
                'verbose_name_plural': 'Order Quality Controls',
            },
        ),
        migrations.CreateModel(
            name='OrderSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('frequency', models.CharField(choices=[('weekly', 'Weekly'), ('biweekly', 'Bi-weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='active', max_length=20)),
                ('next_order_date', models.DateField()),
                ('last_order_date', models.DateField(blank=True, null=True)),
                ('total_orders_generated', models.PositiveIntegerField(default=0)),
                ('max_orders', models.PositiveIntegerField(blank=True, help_text='Maximum number of orders to generate', null=True)),
                ('subscription_start_date', models.DateField()),
                ('subscription_end_date', models.DateField(blank=True, null=True)),
                ('items_config', models.JSONField(help_text='Configuration for subscription items')),
                ('shipping_address', models.JSONField()),
                ('billing_address', models.JSONField()),
                ('payment_method', models.CharField(max_length=50)),
                ('paused_at', models.DateTimeField(blank=True, null=True)),
                ('pause_reason', models.TextField(blank=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_subscriptions', to=settings.AUTH_USER_MODEL)),
                ('original_order_id', models.UUIDField(help_text='Reference to original order ID')),
                ('paused_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paused_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='ordersearchfilter',
            unique_together={('name', 'admin_user')},
        ),

    ]