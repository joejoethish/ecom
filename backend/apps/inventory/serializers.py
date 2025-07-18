from rest_framework import serializers
from django.db.models import Sum, F
from .models import Inventory, InventoryTransaction, Supplier, Warehouse, PurchaseOrder, PurchaseOrderItem


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