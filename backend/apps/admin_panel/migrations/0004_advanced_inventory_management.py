"""
Migration for Advanced Inventory Management System models.
"""
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0003_comprehensive_order_management'),
        ('products', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        # Warehouse model
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('location', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('contact_person', models.CharField(blank=True, max_length=255)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('capacity', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Warehouse',
                'verbose_name_plural': 'Warehouses',
                'db_table': 'warehouses',
                'ordering': ['name'],
            },
        ),

        # Supplier model
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('contact_person', models.CharField(blank=True, max_length=255)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('lead_time_days', models.PositiveIntegerField(default=7)),
                ('reliability_rating', models.DecimalField(decimal_places=2, default=5.0, max_digits=3)),
                ('payment_terms', models.CharField(blank=True, max_length=255)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Supplier',
                'verbose_name_plural': 'Suppliers',
                'db_table': 'suppliers',
                'ordering': ['name'],
            },
        ),

        # InventoryLocation model
        migrations.CreateModel(
            name='InventoryLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('zone', models.CharField(max_length=50)),
                ('aisle', models.CharField(max_length=50)),
                ('shelf', models.CharField(max_length=50)),
                ('bin', models.CharField(blank=True, max_length=50)),
                ('location_code', models.CharField(max_length=100, unique=True)),
                ('capacity', models.PositiveIntegerField(default=100)),
                ('current_utilization', models.PositiveIntegerField(default=0)),
                ('location_type', models.CharField(choices=[('standard', 'Standard'), ('cold_storage', 'Cold Storage'), ('hazardous', 'Hazardous Materials'), ('high_value', 'High Value Items'), ('bulk', 'Bulk Storage'), ('picking', 'Picking Location'), ('receiving', 'Receiving Area'), ('shipping', 'Shipping Area'), ('quarantine', 'Quarantine')], default='standard', max_length=50)),
                ('temperature_range', models.JSONField(blank=True, default=dict)),
                ('humidity_range', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_blocked', models.BooleanField(default=False)),
                ('blocked_reason', models.TextField(blank=True)),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='admin_panel.warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Location',
                'verbose_name_plural': 'Inventory Locations',
                'db_table': 'inventory_locations',
            },
        ),

        # InventoryItem model
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('serial_number', models.CharField(blank=True, max_length=100, unique=True)),
                ('lot_number', models.CharField(blank=True, max_length=100)),
                ('batch_number', models.CharField(blank=True, max_length=100)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('reserved_quantity', models.PositiveIntegerField(default=0)),
                ('condition', models.CharField(choices=[('new', 'New'), ('good', 'Good'), ('fair', 'Fair'), ('damaged', 'Damaged'), ('defective', 'Defective'), ('expired', 'Expired'), ('quarantined', 'Quarantined')], default='new', max_length=50)),
                ('quality_grade', models.CharField(choices=[('A', 'Grade A'), ('B', 'Grade B'), ('C', 'Grade C'), ('D', 'Grade D')], default='A', max_length=10)),
                ('manufactured_date', models.DateField(blank=True, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('received_date', models.DateField(auto_now_add=True)),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('landed_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('purchase_order_reference', models.CharField(blank=True, max_length=100)),
                ('is_available', models.BooleanField(default=True)),
                ('is_quarantined', models.BooleanField(default=False)),
                ('quarantine_reason', models.TextField(blank=True)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='products.product')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.supplier')),
            ],
            options={
                'verbose_name': 'Inventory Item',
                'verbose_name_plural': 'Inventory Items',
                'db_table': 'inventory_items',
            },
        ),

        # InventoryValuation model
        migrations.CreateModel(
            name='InventoryValuation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('costing_method', models.CharField(choices=[('fifo', 'First In, First Out'), ('lifo', 'Last In, First Out'), ('weighted_average', 'Weighted Average'), ('standard_cost', 'Standard Cost'), ('specific_identification', 'Specific Identification')], max_length=50)),
                ('valuation_date', models.DateField()),
                ('total_quantity', models.PositiveIntegerField()),
                ('available_quantity', models.PositiveIntegerField()),
                ('reserved_quantity', models.PositiveIntegerField()),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('average_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('material_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('labor_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('overhead_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('landed_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('calculation_method', models.TextField(blank=True)),
                ('calculated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.adminuser')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='valuations', to='products.product')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='valuations', to='admin_panel.warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Valuation',
                'verbose_name_plural': 'Inventory Valuations',
                'db_table': 'inventory_valuations',
            },
        ),

        # InventoryAdjustment model
        migrations.CreateModel(
            name='InventoryAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('adjustment_number', models.CharField(max_length=50, unique=True)),
                ('adjustment_type', models.CharField(choices=[('increase', 'Increase'), ('decrease', 'Decrease'), ('correction', 'Correction'), ('write_off', 'Write Off'), ('found', 'Found Stock'), ('damaged', 'Damaged'), ('expired', 'Expired'), ('stolen', 'Stolen/Lost'), ('cycle_count', 'Cycle Count'), ('physical_count', 'Physical Count')], max_length=50)),
                ('quantity_before', models.IntegerField()),
                ('quantity_after', models.IntegerField()),
                ('adjustment_quantity', models.IntegerField()),
                ('reason_code', models.CharField(max_length=50)),
                ('reason_description', models.TextField()),
                ('supporting_documents', models.JSONField(blank=True, default=list)),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_cost_impact', models.DecimalField(decimal_places=2, max_digits=15)),
                ('status', models.CharField(choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('applied', 'Applied'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approved_date', models.DateTimeField(blank=True, null=True)),
                ('applied_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('reference_number', models.CharField(blank=True, max_length=100)),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_adjustments', to='admin_panel.adminuser')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_adjustments', to='admin_panel.adminuser')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='products.product')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_adjustments', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Inventory Adjustment',
                'verbose_name_plural': 'Inventory Adjustments',
                'db_table': 'inventory_adjustments',
            },
        ),

        # InventoryTransfer model
        migrations.CreateModel(
            name='InventoryTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('transfer_number', models.CharField(max_length=50, unique=True)),
                ('quantity_requested', models.PositiveIntegerField()),
                ('quantity_shipped', models.PositiveIntegerField(default=0)),
                ('quantity_received', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_transit', 'In Transit'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('partial', 'Partially Completed')], default='pending', max_length=20)),
                ('tracking_number', models.CharField(blank=True, max_length=100)),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('shipped_date', models.DateTimeField(blank=True, null=True)),
                ('expected_arrival_date', models.DateTimeField(blank=True, null=True)),
                ('received_date', models.DateTimeField(blank=True, null=True)),
                ('reason', models.TextField()),
                ('notes', models.TextField(blank=True)),
                ('cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('destination_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transfers', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='products.product')),
                ('received_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_transfers', to='admin_panel.adminuser')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_transfers', to='admin_panel.adminuser')),
                ('shipped_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shipped_transfers', to='admin_panel.adminuser')),
                ('source_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_transfers', to='admin_panel.inventorylocation')),
            ],
            options={
                'verbose_name': 'Inventory Transfer',
                'verbose_name_plural': 'Inventory Transfers',
                'db_table': 'inventory_transfers',
            },
        ),

        # InventoryReservation model
        migrations.CreateModel(
            name='InventoryReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reservation_number', models.CharField(max_length=50, unique=True)),
                ('reservation_type', models.CharField(choices=[('order', 'Order Reservation'), ('quote', 'Quote Reservation'), ('promotion', 'Promotion Reservation'), ('manual', 'Manual Reservation'), ('system', 'System Reservation')], max_length=20)),
                ('quantity_reserved', models.PositiveIntegerField()),
                ('quantity_fulfilled', models.PositiveIntegerField(default=0)),
                ('object_id', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('active', 'Active'), ('fulfilled', 'Fulfilled'), ('expired', 'Expired'), ('cancelled', 'Cancelled'), ('partial', 'Partially Fulfilled')], default='active', max_length=20)),
                ('reserved_date', models.DateTimeField(auto_now_add=True)),
                ('expiry_date', models.DateTimeField()),
                ('fulfilled_date', models.DateTimeField(blank=True, null=True)),
                ('priority', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('notes', models.TextField(blank=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='products.product')),
                ('reserved_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Inventory Reservation',
                'verbose_name_plural': 'Inventory Reservations',
                'db_table': 'inventory_reservations',
            },
        ),

        # InventoryAlert model
        migrations.CreateModel(
            name='InventoryAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alert_number', models.CharField(max_length=50, unique=True)),
                ('alert_type', models.CharField(choices=[('low_stock', 'Low Stock'), ('out_of_stock', 'Out of Stock'), ('overstock', 'Overstock'), ('expiring_soon', 'Expiring Soon'), ('expired', 'Expired'), ('damaged', 'Damaged Items'), ('slow_moving', 'Slow Moving'), ('fast_moving', 'Fast Moving'), ('reorder_point', 'Reorder Point Reached'), ('quality_issue', 'Quality Issue')], max_length=20)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=10)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('current_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('threshold_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('status', models.CharField(choices=[('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved'), ('dismissed', 'Dismissed')], default='active', max_length=20)),
                ('triggered_date', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_date', models.DateTimeField(blank=True, null=True)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('auto_actions_taken', models.JSONField(blank=True, default=list)),
                ('notifications_sent', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('notes', models.TextField(blank=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_alerts', to='admin_panel.adminuser')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_alerts', to='products.product')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_alerts', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Inventory Alert',
                'verbose_name_plural': 'Inventory Alerts',
                'db_table': 'inventory_alerts',
            },
        ),

        # InventoryAudit model
        migrations.CreateModel(
            name='InventoryAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('audit_number', models.CharField(max_length=50, unique=True)),
                ('audit_type', models.CharField(choices=[('cycle_count', 'Cycle Count'), ('physical_count', 'Physical Count'), ('spot_check', 'Spot Check'), ('annual_audit', 'Annual Audit'), ('quality_audit', 'Quality Audit'), ('compliance_audit', 'Compliance Audit')], max_length=20)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('on_hold', 'On Hold')], default='planned', max_length=20)),
                ('planned_date', models.DateField()),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('total_items_counted', models.PositiveIntegerField(default=0)),
                ('items_with_variances', models.PositiveIntegerField(default=0)),
                ('total_variance_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('accuracy_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('notes', models.TextField(blank=True)),
                ('findings', models.TextField(blank=True)),
                ('recommendations', models.TextField(blank=True)),
                ('audit_team', models.ManyToManyField(related_name='audits', to='admin_panel.adminuser')),
                ('locations', models.ManyToManyField(blank=True, related_name='audits', to='admin_panel.inventorylocation')),
                ('products', models.ManyToManyField(blank=True, related_name='audits', to='products.product')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervised_audits', to='admin_panel.adminuser')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audits', to='admin_panel.warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Audit',
                'verbose_name_plural': 'Inventory Audits',
                'db_table': 'inventory_audits',
            },
        ),

        # InventoryAuditItem model
        migrations.CreateModel(
            name='InventoryAuditItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('system_quantity', models.IntegerField()),
                ('counted_quantity', models.IntegerField()),
                ('variance_quantity', models.IntegerField()),
                ('variance_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('variance_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('count_date', models.DateTimeField()),
                ('recount_required', models.BooleanField(default=False)),
                ('recount_completed', models.BooleanField(default=False)),
                ('condition_notes', models.TextField(blank=True)),
                ('discrepancy_reason', models.TextField(blank=True)),
                ('audit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_items', to='admin_panel.inventoryaudit')),
                ('counted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='counted_items', to='admin_panel.adminuser')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_items', to='admin_panel.inventorylocation')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_items', to='products.product')),
            ],
            options={
                'verbose_name': 'Inventory Audit Item',
                'verbose_name_plural': 'Inventory Audit Items',
                'db_table': 'inventory_audit_items',
            },
        ),

        # InventoryForecast model
        migrations.CreateModel(
            name='InventoryForecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('forecast_number', models.CharField(max_length=50, unique=True)),
                ('forecast_type', models.CharField(choices=[('demand', 'Demand Forecast'), ('supply', 'Supply Forecast'), ('reorder', 'Reorder Forecast'), ('seasonal', 'Seasonal Forecast'), ('promotional', 'Promotional Forecast')], max_length=20)),
                ('forecast_date', models.DateField()),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('predicted_demand', models.PositiveIntegerField()),
                ('confidence_level', models.DecimalField(decimal_places=2, max_digits=5)),
                ('recommended_order_quantity', models.PositiveIntegerField()),
                ('recommended_reorder_point', models.PositiveIntegerField()),
                ('recommended_safety_stock', models.PositiveIntegerField()),
                ('forecasting_model', models.CharField(max_length=100)),
                ('model_parameters', models.JSONField(blank=True, default=dict)),
                ('historical_data_points', models.PositiveIntegerField()),
                ('actual_demand', models.PositiveIntegerField(blank=True, null=True)),
                ('forecast_accuracy', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('notes', models.TextField(blank=True)),
                ('external_factors', models.JSONField(blank=True, default=list)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to='admin_panel.adminuser')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to='products.product')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to='admin_panel.warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Forecast',
                'verbose_name_plural': 'Inventory Forecasts',
                'db_table': 'inventory_forecasts',
            },
        ),

        # InventoryOptimization model
        migrations.CreateModel(
            name='InventoryOptimization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('analysis_number', models.CharField(max_length=50, unique=True)),
                ('analysis_type', models.CharField(choices=[('abc', 'ABC Analysis'), ('xyz', 'XYZ Analysis'), ('slow_moving', 'Slow Moving Analysis'), ('fast_moving', 'Fast Moving Analysis'), ('dead_stock', 'Dead Stock Analysis'), ('turnover', 'Turnover Analysis')], max_length=20)),
                ('analysis_date', models.DateField()),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('total_products_analyzed', models.PositiveIntegerField()),
                ('total_value_analyzed', models.DecimalField(decimal_places=2, max_digits=15)),
                ('category_a_count', models.PositiveIntegerField(default=0)),
                ('category_b_count', models.PositiveIntegerField(default=0)),
                ('category_c_count', models.PositiveIntegerField(default=0)),
                ('category_a_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('category_b_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('category_c_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('recommendations', models.TextField(blank=True)),
                ('action_items', models.JSONField(blank=True, default=list)),
                ('methodology', models.TextField(blank=True)),
                ('parameters', models.JSONField(blank=True, default=dict)),
                ('analyzed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='optimizations', to='admin_panel.adminuser')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='optimizations', to='admin_panel.warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Optimization',
                'verbose_name_plural': 'Inventory Optimizations',
                'db_table': 'inventory_optimizations',
            },
        ),

        # InventoryOptimizationItem model
        migrations.CreateModel(
            name='InventoryOptimizationItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('abc_category', models.CharField(blank=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], max_length=1)),
                ('xyz_category', models.CharField(blank=True, choices=[('X', 'X'), ('Y', 'Y'), ('Z', 'Z')], max_length=1)),
                ('annual_usage_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('annual_usage_quantity', models.PositiveIntegerField()),
                ('turnover_rate', models.DecimalField(decimal_places=2, max_digits=8)),
                ('days_of_supply', models.DecimalField(decimal_places=2, max_digits=8)),
                ('current_stock_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('current_stock_quantity', models.PositiveIntegerField()),
                ('last_movement_date', models.DateField(blank=True, null=True)),
                ('days_since_last_movement', models.PositiveIntegerField(blank=True, null=True)),
                ('recommended_action', models.CharField(blank=True, max_length=100)),
                ('recommended_stock_level', models.PositiveIntegerField(blank=True, null=True)),
                ('potential_savings', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('is_slow_moving', models.BooleanField(default=False)),
                ('is_dead_stock', models.BooleanField(default=False)),
                ('is_overstocked', models.BooleanField(default=False)),
                ('is_understocked', models.BooleanField(default=False)),
                ('optimization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='optimization_items', to='admin_panel.inventoryoptimization')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='optimization_items', to='products.product')),
            ],
            options={
                'verbose_name': 'Inventory Optimization Item',
                'verbose_name_plural': 'Inventory Optimization Items',
                'db_table': 'inventory_optimization_items',
            },
        ),

        # InventoryReport model
        migrations.CreateModel(
            name='InventoryReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_number', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('report_type', models.CharField(choices=[('stock_levels', 'Stock Levels Report'), ('valuation', 'Inventory Valuation Report'), ('movement', 'Inventory Movement Report'), ('aging', 'Inventory Aging Report'), ('turnover', 'Inventory Turnover Report'), ('variance', 'Inventory Variance Report'), ('forecast', 'Inventory Forecast Report'), ('optimization', 'Inventory Optimization Report'), ('alerts', 'Inventory Alerts Report'), ('audit', 'Inventory Audit Report')], max_length=20)),
                ('parameters', models.JSONField(blank=True, default=dict)),
                ('filters', models.JSONField(blank=True, default=dict)),
                ('format', models.CharField(choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV'), ('json', 'JSON')], default='pdf', max_length=10)),
                ('schedule_type', models.CharField(choices=[('once', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], default='once', max_length=20)),
                ('schedule_config', models.JSONField(blank=True, default=dict)),
                ('next_run', models.DateTimeField(blank=True, null=True)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('email_recipients', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('total_runs', models.PositiveIntegerField(default=0)),
                ('successful_runs', models.PositiveIntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_inventory_reports', to='admin_panel.adminuser')),
                ('recipients', models.ManyToManyField(blank=True, related_name='inventory_reports', to='admin_panel.adminuser')),
            ],
            options={
                'verbose_name': 'Inventory Report',
                'verbose_name_plural': 'Inventory Reports',
                'db_table': 'inventory_reports',
            },
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='inventorylocation',
            index=models.Index(fields=['warehouse', 'location_code'], name='inventory_locations_warehouse_location_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorylocation',
            index=models.Index(fields=['location_type'], name='inventory_locations_type_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorylocation',
            index=models.Index(fields=['is_active', 'is_blocked'], name='inventory_locations_status_idx'),
        ),

        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['product', 'location'], name='inventory_items_product_location_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['serial_number'], name='inventory_items_serial_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['lot_number'], name='inventory_items_lot_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['batch_number'], name='inventory_items_batch_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['condition'], name='inventory_items_condition_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['expiry_date'], name='inventory_items_expiry_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['is_available'], name='inventory_items_available_idx'),
        ),

        migrations.AddIndex(
            model_name='inventoryvaluation',
            index=models.Index(fields=['product', 'warehouse'], name='inventory_valuations_product_warehouse_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryvaluation',
            index=models.Index(fields=['valuation_date'], name='inventory_valuations_date_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryvaluation',
            index=models.Index(fields=['costing_method'], name='inventory_valuations_method_idx'),
        ),

        migrations.AddIndex(
            model_name='inventoryadjustment',
            index=models.Index(fields=['adjustment_number'], name='inventory_adjustments_number_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryadjustment',
            index=models.Index(fields=['product', 'location'], name='inventory_adjustments_product_location_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryadjustment',
            index=models.Index(fields=['status'], name='inventory_adjustments_status_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryadjustment',
            index=models.Index(fields=['requested_date'], name='inventory_adjustments_date_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryadjustment',
            index=models.Index(fields=['adjustment_type'], name='inventory_adjustments_type_idx'),
        ),

        migrations.AddIndex(
            model_name='inventorytransfer',
            index=models.Index(fields=['transfer_number'], name='inventory_transfers_number_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorytransfer',
            index=models.Index(fields=['source_location', 'destination_location'], name='inventory_transfers_locations_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorytransfer',
            index=models.Index(fields=['status'], name='inventory_transfers_status_idx'),
        ),
        migrations.AddIndex(
            model_name='inventorytransfer',
            index=models.Index(fields=['requested_date'], name='inventory_transfers_date_idx'),
        ),

        migrations.AddIndex(
            model_name='inventoryreservation',
            index=models.Index(fields=['reservation_number'], name='inventory_reservations_number_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryreservation',
            index=models.Index(fields=['product', 'location'], name='inventory_reservations_product_location_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryreservation',
            index=models.Index(fields=['status'], name='inventory_reservations_status_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryreservation',
            index=models.Index(fields=['expiry_date'], name='inventory_reservations_expiry_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryreservation',
            index=models.Index(fields=['priority'], name='inventory_reservations_priority_idx'),
        ),

        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['alert_number'], name='inventory_alerts_number_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['product', 'location'], name='inventory_alerts_product_location_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['alert_type'], name='inventory_alerts_type_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['severity'], name='inventory_alerts_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['status'], name='inventory_alerts_status_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryalert',
            index=models.Index(fields=['triggered_date'], name='inventory_alerts_date_idx'),
        ),

        # Add unique constraints
        migrations.AddConstraint(
            model_name='inventorylocation',
            constraint=models.UniqueConstraint(fields=['warehouse', 'zone', 'aisle', 'shelf', 'bin'], name='unique_location_per_warehouse'),
        ),

        migrations.AddConstraint(
            model_name='inventoryvaluation',
            constraint=models.UniqueConstraint(fields=['product', 'warehouse', 'valuation_date', 'costing_method'], name='unique_valuation_per_product_date_method'),
        ),

        migrations.AddConstraint(
            model_name='inventoryaudititem',
            constraint=models.UniqueConstraint(fields=['audit', 'product', 'location'], name='unique_audit_item_per_product_location'),
        ),

        migrations.AddConstraint(
            model_name='inventoryforecast',
            constraint=models.UniqueConstraint(fields=['product', 'warehouse', 'forecast_date', 'forecast_type'], name='unique_forecast_per_product_date_type'),
        ),

        migrations.AddConstraint(
            model_name='inventoryoptimizationitem',
            constraint=models.UniqueConstraint(fields=['optimization', 'product'], name='unique_optimization_item_per_product'),
        ),
    ]