"""
Comprehensive Order serializers for the admin panel.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from decimal import Decimal

from apps.orders.models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
# from apps.orders.serializers import OrderItemSerializer, OrderTrackingSerializer
from .order_models import (
    OrderSearchFilter, OrderWorkflow, OrderFraudScore, OrderNote, OrderEscalation,
    OrderSLA, OrderAllocation, OrderProfitability, OrderDocument, OrderQualityControl,
    OrderSubscription
)

User = get_user_model()


class OrderSearchFilterSerializer(serializers.ModelSerializer):
    """Serializer for saved order search filters."""
    
    class Meta:
        model = OrderSearchFilter
        fields = ['id', 'name', 'filters', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class OrderWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for order workflows and automation rules."""
    
    class Meta:
        model = OrderWorkflow
        fields = [
            'id', 'name', 'description', 'from_status', 'to_status',
            'conditions', 'actions', 'is_automatic', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderFraudScoreSerializer(serializers.ModelSerializer):
    """Serializer for order fraud scores and risk assessment."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = OrderFraudScore
        fields = [
            'id', 'order', 'order_number', 'score', 'risk_level', 'risk_factors',
            'is_flagged', 'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'review_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderNoteSerializer(serializers.ModelSerializer):
    """Serializer for order notes and communications."""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = OrderNote
        fields = [
            'id', 'order', 'note_type', 'title', 'content', 'created_by',
            'created_by_name', 'is_important', 'is_customer_visible',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderEscalationSerializer(serializers.ModelSerializer):
    """Serializer for order escalations."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderEscalation
        fields = [
            'id', 'order', 'order_number', 'escalation_type', 'priority', 'status',
            'title', 'description', 'created_by', 'created_by_name', 'assigned_to',
            'assigned_to_name', 'resolved_by', 'resolved_by_name', 'resolved_at',
            'resolution_notes', 'sla_deadline', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_overdue']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class OrderSLASerializer(serializers.ModelSerializer):
    """Serializer for order SLA tracking."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = OrderSLA
        fields = [
            'id', 'order', 'order_number', 'processing_deadline', 'shipping_deadline',
            'delivery_deadline', 'processing_completed_at', 'shipping_completed_at',
            'delivery_completed_at', 'processing_sla_met', 'shipping_sla_met',
            'delivery_sla_met', 'overall_sla_met', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderAllocationSerializer(serializers.ModelSerializer):
    """Serializer for order allocation and inventory reservation."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True)
    
    class Meta:
        model = OrderAllocation
        fields = [
            'id', 'order', 'order_number', 'status', 'allocated_at', 'allocated_by',
            'allocated_by_name', 'allocation_details', 'reservation_expires_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderProfitabilitySerializer(serializers.ModelSerializer):
    """Serializer for order profitability analysis."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = OrderProfitability
        fields = [
            'id', 'order', 'order_number', 'gross_revenue', 'net_revenue',
            'product_cost', 'shipping_cost', 'payment_processing_cost',
            'packaging_cost', 'handling_cost', 'marketing_cost', 'other_costs',
            'total_cost', 'gross_profit', 'net_profit', 'profit_margin_percentage',
            'cost_breakdown', 'calculated_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['calculated_at', 'created_at', 'updated_at']


class OrderDocumentSerializer(serializers.ModelSerializer):
    """Serializer for order documents."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = OrderDocument
        fields = [
            'id', 'order', 'order_number', 'document_type', 'title', 'file_path',
            'file_size', 'mime_type', 'generated_by', 'generated_by_name',
            'is_customer_accessible', 'download_count', 'last_downloaded_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderQualityControlSerializer(serializers.ModelSerializer):
    """Serializer for order quality control."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    inspector_name = serializers.CharField(source='inspector.username', read_only=True)
    
    class Meta:
        model = OrderQualityControl
        fields = [
            'id', 'order', 'order_number', 'status', 'inspector', 'inspector_name',
            'inspection_date', 'checklist', 'issues_found', 'corrective_actions',
            'notes', 'requires_reinspection', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for order subscriptions."""
    order_number = serializers.CharField(source='original_order.order_number', read_only=True)
    customer_name = serializers.SerializerMethodField()
    paused_by_name = serializers.CharField(source='paused_by.username', read_only=True)
    
    class Meta:
        model = OrderSubscription
        fields = [
            'id', 'original_order', 'order_number', 'customer', 'customer_name',
            'frequency', 'status', 'next_order_date', 'last_order_date',
            'total_orders_generated', 'max_orders', 'subscription_start_date',
            'subscription_end_date', 'items_config', 'shipping_address',
            'billing_address', 'payment_method', 'paused_at', 'paused_by',
            'paused_by_name', 'pause_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"


class AdminOrderSerializer(serializers.ModelSerializer):
    """Enhanced order serializer for admin panel with comprehensive data."""
    # items = OrderItemSerializer(many=True, read_only=True)
    # timeline = OrderTrackingSerializer(source='get_order_timeline', many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    total_items = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_return = serializers.SerializerMethodField()
    
    # Related data
    fraud_score = OrderFraudScoreSerializer(read_only=True)
    notes = OrderNoteSerializer(source='admin_notes', many=True, read_only=True)
    escalations = OrderEscalationSerializer(many=True, read_only=True)
    sla_tracking = OrderSLASerializer(read_only=True)
    allocation = OrderAllocationSerializer(read_only=True)
    profitability = OrderProfitabilitySerializer(read_only=True)
    documents = OrderDocumentSerializer(many=True, read_only=True)
    quality_control = OrderQualityControlSerializer(read_only=True)
    subscription = OrderSubscriptionSerializer(read_only=True)
    
    # Calculated fields
    days_since_order = serializers.SerializerMethodField()
    processing_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'customer_email',
            'status', 'payment_status', 'total_amount', 'shipping_amount',
            'tax_amount', 'discount_amount', 'shipping_address', 'billing_address',
            'shipping_method', 'payment_method', 'estimated_delivery_date',
            'actual_delivery_date', 'tracking_number', 'invoice_number',
            'notes', 'total_items', 'can_cancel',
            'can_return', 'fraud_score', 'escalations', 'sla_tracking',
            'allocation', 'profitability', 'documents', 'quality_control',
            'subscription', 'days_since_order', 'processing_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'invoice_number', 'customer_name']
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    
    def get_can_cancel(self, obj):
        return obj.can_cancel()
    
    def get_can_return(self, obj):
        return obj.can_return()
    
    def get_days_since_order(self, obj):
        return (timezone.now().date() - obj.created_at.date()).days
    
    def get_processing_time(self, obj):
        """Calculate processing time in hours."""
        if obj.status in ['shipped', 'delivered']:
            shipped_event = obj.timeline_events.filter(status='shipped').first()
            if shipped_event:
                time_diff = shipped_event.created_at - obj.created_at
                return round(time_diff.total_seconds() / 3600, 2)  # Convert to hours
        return None


class OrderAnalyticsSerializer(serializers.Serializer):
    """Serializer for order analytics and performance metrics."""
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_by_status = serializers.DictField()
    orders_by_payment_status = serializers.DictField()
    top_customers = serializers.ListField()
    revenue_trend = serializers.ListField()
    order_volume_trend = serializers.ListField()
    processing_time_avg = serializers.FloatField()
    sla_compliance_rate = serializers.FloatField()
    fraud_detection_stats = serializers.DictField()
    profitability_summary = serializers.DictField()


class OrderBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk order actions."""
    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of order IDs to perform action on"
    )
    action = serializers.ChoiceField(choices=[
        ('update_status', 'Update Status'),
        ('assign_to_user', 'Assign to User'),
        ('add_note', 'Add Note'),
        ('export', 'Export'),
        ('generate_documents', 'Generate Documents'),
        ('allocate_inventory', 'Allocate Inventory'),
        ('calculate_profitability', 'Calculate Profitability'),
    ])
    parameters = serializers.JSONField(
        required=False,
        help_text="Additional parameters for the action"
    )


class OrderModificationSerializer(serializers.Serializer):
    """Serializer for order modifications (add/remove items, change quantities, etc.)."""
    modification_type = serializers.ChoiceField(choices=[
        ('add_item', 'Add Item'),
        ('remove_item', 'Remove Item'),
        ('update_quantity', 'Update Quantity'),
        ('update_address', 'Update Address'),
        ('update_shipping_method', 'Update Shipping Method'),
    ])
    
    # For item modifications
    product_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(required=False, min_value=1)
    order_item_id = serializers.UUIDField(required=False)
    
    # For address modifications
    shipping_address = serializers.JSONField(required=False)
    billing_address = serializers.JSONField(required=False)
    
    # For shipping method modifications
    shipping_method = serializers.CharField(required=False)
    
    # General
    reason = serializers.CharField(help_text="Reason for modification")
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderSplitSerializer(serializers.Serializer):
    """Serializer for order splitting."""
    split_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items to split with their quantities"
    )
    reason = serializers.CharField(help_text="Reason for splitting the order")
    shipping_address = serializers.JSONField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderMergeSerializer(serializers.Serializer):
    """Serializer for order merging."""
    target_order_id = serializers.UUIDField(help_text="Order to merge into")
    source_order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Orders to merge from"
    )
    reason = serializers.CharField(help_text="Reason for merging orders")
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderExportSerializer(serializers.Serializer):
    """Serializer for order export configuration."""
    export_format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('pdf', 'PDF Report'),
    ])
    date_range = serializers.DictField(required=False)
    filters = serializers.DictField(required=False)
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Specific fields to include in export"
    )
    include_items = serializers.BooleanField(default=True)
    include_timeline = serializers.BooleanField(default=False)
    include_notes = serializers.BooleanField(default=False)


class OrderForecastSerializer(serializers.Serializer):
    """Serializer for order forecasting and trend analysis."""
    forecast_period = serializers.ChoiceField(choices=[
        ('7_days', '7 Days'),
        ('30_days', '30 Days'),
        ('90_days', '90 Days'),
        ('1_year', '1 Year'),
    ])
    forecast_type = serializers.ChoiceField(choices=[
        ('volume', 'Order Volume'),
        ('revenue', 'Revenue'),
        ('both', 'Both'),
    ])
    include_seasonality = serializers.BooleanField(default=True)
    confidence_interval = serializers.FloatField(default=0.95, min_value=0.5, max_value=0.99)


class OrderRoutingSerializer(serializers.Serializer):
    """Serializer for order routing optimization."""
    fulfillment_centers = serializers.ListField(
        child=serializers.DictField(),
        help_text="Available fulfillment centers with their capabilities"
    )
    optimization_criteria = serializers.ChoiceField(choices=[
        ('cost', 'Minimize Cost'),
        ('time', 'Minimize Delivery Time'),
        ('distance', 'Minimize Distance'),
        ('balanced', 'Balanced Approach'),
    ])
    constraints = serializers.DictField(
        required=False,
        help_text="Additional constraints for routing"
    )


class OrderComplianceSerializer(serializers.Serializer):
    """Serializer for order compliance tracking."""
    compliance_type = serializers.ChoiceField(choices=[
        ('tax', 'Tax Compliance'),
        ('shipping', 'Shipping Regulations'),
        ('product', 'Product Regulations'),
        ('data_privacy', 'Data Privacy'),
        ('customs', 'Customs Compliance'),
    ])
    region = serializers.CharField(help_text="Geographic region for compliance check")
    requirements = serializers.ListField(
        child=serializers.CharField(),
        help_text="Specific compliance requirements to check"
    )