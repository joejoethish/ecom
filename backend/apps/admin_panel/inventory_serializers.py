"""
Advanced Inventory Management System serializers for comprehensive admin panel.
"""
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from apps.products.models import Product
from .inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization,
    InventoryOptimizationItem, InventoryReport
)
from .models import AdminUser


class InventoryLocationSerializer(serializers.ModelSerializer):
    """Serializer for inventory locations with capacity tracking."""
    
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    utilization_percentage = serializers.ReadOnlyField()
    current_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryLocation
        fields = [
            'id', 'warehouse', 'warehouse_name', 'zone', 'aisle', 'shelf', 'bin',
            'location_code', 'capacity', 'current_utilization', 'utilization_percentage',
            'location_type', 'temperature_range', 'humidity_range', 'is_active',
            'is_blocked', 'blocked_reason', 'current_items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'location_code', 'created_at', 'updated_at']
    
    def get_current_items_count(self, obj):
        """Get count of items currently in this location."""
        return obj.items.filter(is_available=True).count()
    
    def create(self, validated_data):
        """Create location with auto-generated location code."""
        warehouse = validated_data['warehouse']
        zone = validated_data['zone']
        aisle = validated_data['aisle']
        shelf = validated_data['shelf']
        bin_code = validated_data.get('bin', '')
        
        # Generate location code
        location_code = f"{warehouse.code}-{zone}-{aisle}-{shelf}"
        if bin_code:
            location_code += f"-{bin_code}"
        
        validated_data['location_code'] = location_code
        return super().create(validated_data)


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for individual inventory items with serialization."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_code = serializers.CharField(source='location.location_code', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    available_quantity = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location', 'location_code',
            'serial_number', 'lot_number', 'batch_number', 'quantity', 'reserved_quantity',
            'available_quantity', 'condition', 'quality_grade', 'manufactured_date',
            'expiry_date', 'received_date', 'unit_cost', 'landed_cost', 'supplier',
            'supplier_name', 'purchase_order_reference', 'is_available', 'is_quarantined',
            'quarantine_reason', 'is_expired', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'received_date', 'created_at', 'updated_at']


class InventoryValuationSerializer(serializers.ModelSerializer):
    """Serializer for inventory valuation with different costing methods."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    calculated_by_name = serializers.CharField(source='calculated_by.username', read_only=True)
    
    class Meta:
        model = InventoryValuation
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'warehouse', 'warehouse_name',
            'costing_method', 'valuation_date', 'total_quantity', 'available_quantity',
            'reserved_quantity', 'unit_cost', 'total_value', 'average_cost',
            'material_cost', 'labor_cost', 'overhead_cost', 'landed_cost',
            'calculated_by', 'calculated_by_name', 'calculation_method',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    """Serializer for inventory adjustments with approval workflow."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_code = serializers.CharField(source='location.location_code', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.username', read_only=True)
    
    class Meta:
        model = InventoryAdjustment
        fields = [
            'id', 'adjustment_number', 'product', 'product_name', 'product_sku',
            'location', 'location_code', 'adjustment_type', 'quantity_before',
            'quantity_after', 'adjustment_quantity', 'reason_code', 'reason_description',
            'supporting_documents', 'unit_cost', 'total_cost_impact', 'status',
            'requested_by', 'requested_by_name', 'approved_by', 'approved_by_name',
            'applied_by', 'applied_by_name', 'requested_date', 'approved_date',
            'applied_date', 'notes', 'reference_number', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'adjustment_number', 'requested_date', 'approved_date',
            'applied_date', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create adjustment with auto-generated adjustment number."""
        # Generate adjustment number
        import uuid
        adjustment_number = f"ADJ-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['adjustment_number'] = adjustment_number
        
        # Calculate adjustment quantity
        validated_data['adjustment_quantity'] = (
            validated_data['quantity_after'] - validated_data['quantity_before']
        )
        
        # Calculate cost impact
        validated_data['total_cost_impact'] = (
            validated_data['adjustment_quantity'] * validated_data['unit_cost']
        )
        
        return super().create(validated_data)


class InventoryTransferSerializer(serializers.ModelSerializer):
    """Serializer for inventory transfers between locations."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    source_location_code = serializers.CharField(source='source_location.location_code', read_only=True)
    destination_location_code = serializers.CharField(source='destination_location.location_code', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    shipped_by_name = serializers.CharField(source='shipped_by.username', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)
    is_complete = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryTransfer
        fields = [
            'id', 'transfer_number', 'source_location', 'source_location_code',
            'destination_location', 'destination_location_code', 'product',
            'product_name', 'product_sku', 'quantity_requested', 'quantity_shipped',
            'quantity_received', 'status', 'tracking_number', 'requested_date',
            'shipped_date', 'expected_arrival_date', 'received_date',
            'requested_by', 'requested_by_name', 'shipped_by', 'shipped_by_name',
            'received_by', 'received_by_name', 'reason', 'notes', 'cost',
            'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transfer_number', 'requested_date', 'shipped_date',
            'received_date', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create transfer with auto-generated transfer number."""
        import uuid
        transfer_number = f"TRF-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['transfer_number'] = transfer_number
        return super().create(validated_data)


class InventoryReservationSerializer(serializers.ModelSerializer):
    """Serializer for inventory reservations."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_code = serializers.CharField(source='location.location_code', read_only=True)
    reserved_by_name = serializers.CharField(source='reserved_by.username', read_only=True)
    remaining_quantity = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryReservation
        fields = [
            'id', 'reservation_number', 'product', 'product_name', 'product_sku',
            'location', 'location_code', 'reservation_type', 'quantity_reserved',
            'quantity_fulfilled', 'remaining_quantity', 'content_type', 'object_id',
            'status', 'reserved_date', 'expiry_date', 'fulfilled_date',
            'reserved_by', 'reserved_by_name', 'priority', 'notes',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reservation_number', 'reserved_date', 'fulfilled_date',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create reservation with auto-generated reservation number."""
        import uuid
        reservation_number = f"RSV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['reservation_number'] = reservation_number
        return super().create(validated_data)


class InventoryAlertSerializer(serializers.ModelSerializer):
    """Serializer for inventory alerts and notifications."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_code = serializers.CharField(source='location.location_code', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = InventoryAlert
        fields = [
            'id', 'alert_number', 'product', 'product_name', 'product_sku',
            'location', 'location_code', 'alert_type', 'severity', 'title',
            'description', 'current_value', 'threshold_value', 'status',
            'triggered_date', 'acknowledged_date', 'resolved_date',
            'acknowledged_by', 'acknowledged_by_name', 'resolved_by',
            'resolved_by_name', 'auto_actions_taken', 'notifications_sent',
            'metadata', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'alert_number', 'triggered_date', 'acknowledged_date',
            'resolved_date', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create alert with auto-generated alert number."""
        import uuid
        alert_number = f"ALT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['alert_number'] = alert_number
        return super().create(validated_data)


class InventoryAuditItemSerializer(serializers.ModelSerializer):
    """Serializer for individual audit items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_code = serializers.CharField(source='location.location_code', read_only=True)
    counted_by_name = serializers.CharField(source='counted_by.username', read_only=True)
    
    class Meta:
        model = InventoryAuditItem
        fields = [
            'id', 'audit', 'product', 'product_name', 'product_sku',
            'location', 'location_code', 'system_quantity', 'counted_quantity',
            'variance_quantity', 'variance_percentage', 'unit_cost', 'variance_value',
            'counted_by', 'counted_by_name', 'count_date', 'recount_required',
            'recount_completed', 'condition_notes', 'discrepancy_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'variance_quantity', 'variance_percentage', 'variance_value', 'created_at', 'updated_at']
    
    def save(self, **kwargs):
        """Calculate variance when saving."""
        if self.instance:
            # Update case
            self.instance.variance_quantity = self.validated_data.get('counted_quantity', self.instance.counted_quantity) - self.instance.system_quantity
        else:
            # Create case
            system_qty = self.validated_data['system_quantity']
            counted_qty = self.validated_data['counted_quantity']
            self.validated_data['variance_quantity'] = counted_qty - system_qty
            
            # Calculate variance percentage
            if system_qty > 0:
                self.validated_data['variance_percentage'] = ((counted_qty - system_qty) / system_qty) * 100
            else:
                self.validated_data['variance_percentage'] = 0
            
            # Calculate variance value
            unit_cost = self.validated_data.get('unit_cost', 0)
            self.validated_data['variance_value'] = self.validated_data['variance_quantity'] * unit_cost
        
        return super().save(**kwargs)


class InventoryAuditSerializer(serializers.ModelSerializer):
    """Serializer for inventory audits with cycle counting."""
    
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.username', read_only=True)
    audit_team_names = serializers.SerializerMethodField()
    audit_items = InventoryAuditItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryAudit
        fields = [
            'id', 'audit_number', 'audit_type', 'warehouse', 'warehouse_name',
            'locations', 'products', 'status', 'planned_date', 'start_date',
            'end_date', 'audit_team', 'audit_team_names', 'supervisor',
            'supervisor_name', 'total_items_counted', 'items_with_variances',
            'total_variance_value', 'accuracy_percentage', 'notes', 'findings',
            'recommendations', 'audit_items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'audit_number', 'start_date', 'end_date', 'total_items_counted',
            'items_with_variances', 'total_variance_value', 'accuracy_percentage',
            'created_at', 'updated_at'
        ]
    
    def get_audit_team_names(self, obj):
        """Get names of audit team members."""
        return [user.username for user in obj.audit_team.all()]
    
    def create(self, validated_data):
        """Create audit with auto-generated audit number."""
        import uuid
        audit_number = f"AUD-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['audit_number'] = audit_number
        return super().create(validated_data)


class InventoryForecastSerializer(serializers.ModelSerializer):
    """Serializer for inventory forecasting."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = InventoryForecast
        fields = [
            'id', 'forecast_number', 'forecast_type', 'product', 'product_name',
            'product_sku', 'warehouse', 'warehouse_name', 'forecast_date',
            'period_start', 'period_end', 'predicted_demand', 'confidence_level',
            'recommended_order_quantity', 'recommended_reorder_point',
            'recommended_safety_stock', 'forecasting_model', 'model_parameters',
            'historical_data_points', 'actual_demand', 'forecast_accuracy',
            'created_by', 'created_by_name', 'notes', 'external_factors',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'forecast_number', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create forecast with auto-generated forecast number."""
        import uuid
        forecast_number = f"FCT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['forecast_number'] = forecast_number
        return super().create(validated_data)


class InventoryOptimizationItemSerializer(serializers.ModelSerializer):
    """Serializer for optimization analysis items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = InventoryOptimizationItem
        fields = [
            'id', 'optimization', 'product', 'product_name', 'product_sku',
            'abc_category', 'xyz_category', 'annual_usage_value',
            'annual_usage_quantity', 'turnover_rate', 'days_of_supply',
            'current_stock_value', 'current_stock_quantity', 'last_movement_date',
            'days_since_last_movement', 'recommended_action',
            'recommended_stock_level', 'potential_savings', 'is_slow_moving',
            'is_dead_stock', 'is_overstocked', 'is_understocked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InventoryOptimizationSerializer(serializers.ModelSerializer):
    """Serializer for inventory optimization analysis."""
    
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    analyzed_by_name = serializers.CharField(source='analyzed_by.username', read_only=True)
    optimization_items = InventoryOptimizationItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryOptimization
        fields = [
            'id', 'analysis_number', 'analysis_type', 'warehouse', 'warehouse_name',
            'analysis_date', 'period_start', 'period_end', 'total_products_analyzed',
            'total_value_analyzed', 'category_a_count', 'category_b_count',
            'category_c_count', 'category_a_value', 'category_b_value',
            'category_c_value', 'recommendations', 'action_items',
            'analyzed_by', 'analyzed_by_name', 'methodology', 'parameters',
            'optimization_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'analysis_number', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create optimization with auto-generated analysis number."""
        import uuid
        analysis_number = f"OPT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['analysis_number'] = analysis_number
        return super().create(validated_data)


class InventoryReportSerializer(serializers.ModelSerializer):
    """Serializer for inventory reports."""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    recipients_names = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryReport
        fields = [
            'id', 'report_number', 'name', 'description', 'report_type',
            'parameters', 'filters', 'format', 'schedule_type', 'schedule_config',
            'next_run', 'last_run', 'recipients', 'recipients_names',
            'email_recipients', 'is_active', 'created_by', 'created_by_name',
            'total_runs', 'successful_runs', 'last_error', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'report_number', 'last_run', 'total_runs', 'successful_runs',
            'created_at', 'updated_at'
        ]
    
    def get_recipients_names(self, obj):
        """Get names of report recipients."""
        return [user.username for user in obj.recipients.all()]
    
    def create(self, validated_data):
        """Create report with auto-generated report number."""
        import uuid
        report_number = f"RPT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        validated_data['report_number'] = report_number
        return super().create(validated_data)


class InventoryDashboardSerializer(serializers.Serializer):
    """Serializer for inventory dashboard data."""
    
    total_products = serializers.IntegerField()
    total_locations = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_items = serializers.IntegerField()
    out_of_stock_items = serializers.IntegerField()
    overstock_items = serializers.IntegerField()
    expired_items = serializers.IntegerField()
    expiring_soon_items = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    pending_adjustments = serializers.IntegerField()
    active_transfers = serializers.IntegerField()
    active_reservations = serializers.IntegerField()
    
    # Turnover metrics
    average_turnover_rate = serializers.DecimalField(max_digits=8, decimal_places=2)
    slow_moving_items = serializers.IntegerField()
    dead_stock_items = serializers.IntegerField()
    
    # Recent activity
    recent_adjustments = InventoryAdjustmentSerializer(many=True)
    recent_transfers = InventoryTransferSerializer(many=True)
    recent_alerts = InventoryAlertSerializer(many=True)


class BulkInventoryActionSerializer(serializers.Serializer):
    """Serializer for bulk inventory operations."""
    
    action = serializers.ChoiceField(choices=[
        ('adjust_stock', 'Adjust Stock'),
        ('transfer_items', 'Transfer Items'),
        ('create_reservations', 'Create Reservations'),
        ('update_locations', 'Update Locations'),
        ('mark_expired', 'Mark as Expired'),
        ('quarantine_items', 'Quarantine Items'),
        ('generate_alerts', 'Generate Alerts'),
    ])
    items = serializers.ListField(child=serializers.DictField())
    parameters = serializers.DictField(default=dict)
    notes = serializers.CharField(max_length=1000, required=False)
    
    def validate_items(self, value):
        """Validate items list."""
        if not value:
            raise serializers.ValidationError("Items list cannot be empty.")
        
        if len(value) > 1000:
            raise serializers.ValidationError("Cannot process more than 1000 items at once.")
        
        return value


class InventoryImportSerializer(serializers.Serializer):
    """Serializer for inventory data import."""
    
    file = serializers.FileField()
    import_type = serializers.ChoiceField(choices=[
        ('locations', 'Locations'),
        ('items', 'Items'),
        ('adjustments', 'Adjustments'),
        ('transfers', 'Transfers'),
        ('valuations', 'Valuations'),
    ])
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    validate_only = serializers.BooleanField(default=False)
    update_existing = serializers.BooleanField(default=False)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        if not value.name.endswith(('.csv', '.xlsx', '.xls')):
            raise serializers.ValidationError("Only CSV and Excel files are supported.")
        
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        return value


class InventoryExportSerializer(serializers.Serializer):
    """Serializer for inventory data export."""
    
    export_type = serializers.ChoiceField(choices=[
        ('stock_levels', 'Stock Levels'),
        ('valuations', 'Valuations'),
        ('movements', 'Movements'),
        ('alerts', 'Alerts'),
        ('audit_results', 'Audit Results'),
        ('optimization_results', 'Optimization Results'),
    ])
    format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ], default='csv')
    filters = serializers.DictField(default=dict)
    date_range = serializers.DictField(default=dict)
    warehouses = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all()),
        required=False
    )
    products = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all()),
        required=False
    )