from rest_framework import serializers
from django.db.models import Sum, F
from .models import Inventory, InventoryTransaction, Supplier, Warehouse, PurchaseOrder, PurchaseOrderItem
from .analytics_models import (
    InventoryAnalytics, InventoryKPI, InventoryForecast, 
    InventoryAlert, CycleCount, CycleCountItem
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'email', 'phone', 
            'address', 'website', 'lead_time_days', 'reliability_rating',
            'payment_terms', 'currency', 'is_active', 'created_at', 'updated_at'
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'location', 'address', 'contact_person',
            'email', 'phone', 'capacity', 'is_active', 'created_at', 'updated_at'
        ]


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_name', 'warehouse', 'warehouse_name',
            'quantity', 'reserved_quantity', 'available_quantity', 'stock_status',
            'minimum_stock_level', 'maximum_stock_level', 'reorder_point',
            'cost_price', 'supplier', 'supplier_name', 'last_restocked',
            'created_at', 'updated_at'
        ]


class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    warehouse_name = serializers.CharField(source='inventory.warehouse.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'inventory', 'product_name', 'warehouse_name', 'transaction_type',
            'transaction_type_display', 'quantity', 'reference_number', 'order',
            'source_warehouse', 'destination_warehouse', 'batch_number',
            'expiry_date', 'unit_cost', 'total_cost', 'notes', 'created_by',
            'created_by_username', 'created_at'
        ]
        read_only_fields = ['total_cost', 'created_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'product', 'product_name', 'quantity_ordered',
            'quantity_received', 'unit_price', 'total_price', 'remaining_quantity',
            'is_completed'
        ]
        read_only_fields = ['is_completed']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name', 'warehouse',
            'warehouse_name', 'status', 'status_display', 'order_date',
            'expected_delivery_date', 'actual_delivery_date', 'total_amount',
            'tax_amount', 'shipping_cost', 'notes', 'created_by',
            'created_by_username', 'approved_by', 'approved_by_username',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['po_number', 'order_date', 'created_at', 'updated_at']


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.Field(),
            allow_empty=False
        ),
        allow_empty=False
    )
    
    def validate_items(self, items):
        """Validate that each item has the required fields with valid values"""
        for i, item in enumerate(items):
            if not all(key in item for key in ['product_id', 'quantity', 'unit_price']):
                raise serializers.ValidationError(f"Item {i+1} is missing required fields")
            
            if not isinstance(item['product_id'], int) or item['product_id'] <= 0:
                raise serializers.ValidationError(f"Item {i+1} has invalid product_id")
            
            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                raise serializers.ValidationError(f"Item {i+1} has invalid quantity")
            
            try:
                float_price = float(item['unit_price'])
                if float_price <= 0:
                    raise serializers.ValidationError(f"Item {i+1} has invalid unit_price")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Item {i+1} has invalid unit_price")
        
        return items


class PurchaseOrderReceiveSerializer(serializers.Serializer):
    received_items = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        allow_empty=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class InventoryAdjustmentSerializer(serializers.Serializer):
    inventory_id = serializers.IntegerField()
    adjustment_quantity = serializers.IntegerField()
    reason = serializers.CharField()
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class InventoryTransferSerializer(serializers.Serializer):
    source_inventory_id = serializers.IntegerField()
    destination_inventory_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class BulkInventoryUpdateSerializer(serializers.Serializer):
    """Serializer for bulk inventory updates."""
    inventory_updates = serializers.ListField(
        child=serializers.DictField(
            child=serializers.Field(),
            allow_empty=False
        ),
        allow_empty=False
    )
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_inventory_updates(self, updates):
        """Validate that each update has the required fields with valid values"""
        for i, update in enumerate(updates):
            if not all(key in update for key in ['inventory_id', 'quantity']):
                raise serializers.ValidationError(f"Update {i+1} is missing required fields")
            
            if not isinstance(update['inventory_id'], int) or update['inventory_id'] <= 0:
                raise serializers.ValidationError(f"Update {i+1} has invalid inventory_id")
            
            if not isinstance(update['quantity'], int):
                raise serializers.ValidationError(f"Update {i+1} has invalid quantity")
        
        return updates


class InventoryAlertSettingsSerializer(serializers.Serializer):
    """Serializer for updating inventory alert settings."""
    inventory_id = serializers.IntegerField()
    minimum_stock_level = serializers.IntegerField(min_value=0, required=False)
    maximum_stock_level = serializers.IntegerField(min_value=0, required=False)
    reorder_point = serializers.IntegerField(min_value=0, required=False)
    
    def validate(self, data):
        """Validate that minimum <= reorder_point <= maximum"""
        minimum = data.get('minimum_stock_level')
        reorder = data.get('reorder_point')
        maximum = data.get('maximum_stock_level')
        
        if minimum is not None and reorder is not None and minimum > reorder:
            raise serializers.ValidationError("Minimum stock level cannot be greater than reorder point")
        
        if reorder is not None and maximum is not None and reorder > maximum:
            raise serializers.ValidationError("Reorder point cannot be greater than maximum stock level")
        
        return data


class InventoryReportSerializer(serializers.Serializer):
    """Serializer for inventory reports."""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    warehouse_id = serializers.IntegerField(required=False)
    product_id = serializers.IntegerField(required=False)
    report_type = serializers.ChoiceField(
        choices=['stock_levels', 'movements', 'valuation', 'turnover'],
        required=True
    )
    
    def validate(self, data):
        """Validate date range if provided"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        return data

# Analytics Serializers

class InventoryAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for inventory analytics data."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    
    class Meta:
        model = InventoryAnalytics
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'warehouse', 'warehouse_name',
            'analysis_type', 'analysis_type_display', 'analysis_date',
            'abc_category', 'revenue_contribution', 'turnover_ratio', 'days_of_supply',
            'forecasted_demand', 'forecast_accuracy', 'shrinkage_quantity', 'shrinkage_value',
            'shrinkage_percentage', 'carrying_cost', 'carrying_cost_percentage',
            'optimal_reorder_point', 'optimal_order_quantity', 'service_level',
            'defect_rate', 'quality_score', 'obsolescence_risk', 'days_since_last_sale',
            'additional_metrics', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InventoryKPISerializer(serializers.ModelSerializer):
    """Serializer for inventory KPIs."""
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    kpi_type_display = serializers.CharField(source='get_kpi_type_display', read_only=True)
    performance_status_display = serializers.CharField(source='get_performance_status_display', read_only=True)
    trend_direction_display = serializers.CharField(source='get_trend_direction_display', read_only=True)
    variance = serializers.SerializerMethodField()
    variance_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryKPI
        fields = [
            'id', 'warehouse', 'warehouse_name', 'kpi_type', 'kpi_type_display',
            'measurement_date', 'value', 'target_value', 'performance_status',
            'performance_status_display', 'previous_value', 'trend_direction',
            'trend_direction_display', 'variance', 'variance_percentage', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_variance(self, obj):
        """Calculate variance from target."""
        if obj.target_value:
            return float(obj.value - obj.target_value)
        return None
    
    def get_variance_percentage(self, obj):
        """Calculate variance percentage from target."""
        if obj.target_value and obj.target_value != 0:
            return float((obj.value - obj.target_value) / obj.target_value * 100)
        return None


class InventoryForecastSerializer(serializers.ModelSerializer):
    """Serializer for inventory forecasts."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    forecast_method_display = serializers.CharField(source='get_forecast_method_display', read_only=True)
    forecast_period_days = serializers.SerializerMethodField()
    accuracy_status = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryForecast
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'warehouse', 'warehouse_name',
            'forecast_date', 'forecast_period_start', 'forecast_period_end', 'forecast_period_days',
            'forecast_method', 'forecast_method_display', 'forecasted_demand',
            'confidence_interval_lower', 'confidence_interval_upper', 'confidence_level',
            'actual_demand', 'forecast_error', 'absolute_percentage_error', 'accuracy_status',
            'model_parameters', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_forecast_period_days(self, obj):
        """Calculate forecast period in days."""
        return (obj.forecast_period_end - obj.forecast_period_start).days + 1
    
    def get_accuracy_status(self, obj):
        """Determine forecast accuracy status."""
        if obj.absolute_percentage_error is None:
            return 'PENDING'
        elif obj.absolute_percentage_error <= 10:
            return 'EXCELLENT'
        elif obj.absolute_percentage_error <= 20:
            return 'GOOD'
        elif obj.absolute_percentage_error <= 30:
            return 'FAIR'
        else:
            return 'POOR'


class InventoryAlertSerializer(serializers.ModelSerializer):
    """Serializer for inventory alerts."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    days_active = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryAlert
        fields = [
            'id', 'alert_type', 'alert_type_display', 'priority', 'priority_display',
            'status', 'status_display', 'product', 'product_name', 'product_sku',
            'warehouse', 'warehouse_name', 'inventory', 'title', 'message',
            'threshold_value', 'current_value', 'recommended_action', 'action_taken',
            'created_by', 'created_by_username', 'acknowledged_by', 'acknowledged_by_username',
            'resolved_by', 'resolved_by_username', 'created_at', 'acknowledged_at',
            'resolved_at', 'days_active'
        ]
        read_only_fields = ['created_at', 'acknowledged_at', 'resolved_at']
    
    def get_days_active(self, obj):
        """Calculate days since alert was created."""
        from django.utils import timezone
        return (timezone.now().date() - obj.created_at.date()).days


class CycleCountItemSerializer(serializers.ModelSerializer):
    """Serializer for cycle count items."""
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    product_sku = serializers.CharField(source='inventory.product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='inventory.warehouse.name', read_only=True)
    counted_by_username = serializers.CharField(source='counted_by.username', read_only=True)
    variance_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CycleCountItem
        fields = [
            'id', 'cycle_count', 'inventory', 'product_name', 'product_sku', 'warehouse_name',
            'system_quantity', 'counted_quantity', 'variance_quantity', 'variance_value',
            'variance_percentage', 'counted_by', 'counted_by_username', 'counted_at',
            'variance_reason', 'adjustment_made', 'adjustment_transaction', 'notes'
        ]
        read_only_fields = ['variance_quantity', 'variance_value']
    
    def get_variance_percentage(self, obj):
        """Calculate variance percentage."""
        if obj.system_quantity != 0:
            return float(obj.variance_quantity / obj.system_quantity * 100)
        return None


class CycleCountSerializer(serializers.ModelSerializer):
    """Serializer for cycle counts."""
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    items = CycleCountItemSerializer(many=True, read_only=True)
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = CycleCount
        fields = [
            'id', 'count_name', 'warehouse', 'warehouse_name', 'status', 'status_display',
            'scheduled_date', 'started_at', 'completed_at', 'duration_days',
            'count_all_products', 'product_categories', 'specific_products',
            'total_items_counted', 'items_with_variances', 'total_variance_value',
            'accuracy_percentage', 'created_by', 'created_by_username',
            'assigned_to', 'assigned_to_username', 'notes', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_duration_days(self, obj):
        """Calculate duration of cycle count."""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at.date() - obj.started_at.date()).days
        return None


class CycleCountCreateSerializer(serializers.Serializer):
    """Serializer for creating cycle counts."""
    count_name = serializers.CharField(max_length=200)
    warehouse_id = serializers.IntegerField()
    scheduled_date = serializers.DateField()
    count_all_products = serializers.BooleanField(default=False)
    product_category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    specific_product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate cycle count creation data."""
        if not data.get('count_all_products'):
            if not data.get('product_category_ids') and not data.get('specific_product_ids'):
                raise serializers.ValidationError(
                    "Either count_all_products must be True or specific categories/products must be selected"
                )
        return data


class InventoryAnalyticsReportSerializer(serializers.Serializer):
    """Serializer for inventory analytics reports."""
    report_type = serializers.ChoiceField(
        choices=[
            ('comprehensive', 'Comprehensive Analytics'),
            ('valuation', 'Inventory Valuation'),
            ('turnover', 'Turnover Analysis'),
            ('abc', 'ABC Analysis'),
            ('slow_moving', 'Slow Moving Analysis'),
            ('aging', 'Aging Analysis'),
            ('forecasting', 'Forecasting Data'),
            ('kpi', 'KPI Dashboard'),
            ('shrinkage', 'Shrinkage Analysis'),
            ('carrying_cost', 'Carrying Cost Analysis'),
            ('reorder_optimization', 'Reorder Optimization'),
            ('supplier_performance', 'Supplier Performance'),
            ('quality_metrics', 'Quality Metrics'),
            ('seasonal', 'Seasonal Analysis'),
            ('obsolescence', 'Obsolescence Analysis'),
            ('location_optimization', 'Location Optimization'),
            ('compliance', 'Compliance Metrics'),
        ],
        required=True
    )
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    export_format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('excel', 'Excel')],
        default='json'
    )
    
    def validate(self, data):
        """Validate report parameters."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        return data