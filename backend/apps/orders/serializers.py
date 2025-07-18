"""
Order serializers for the ecommerce platform.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.products.serializers import ProductSerializer, ProductMinimalSerializer

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    can_return = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 'unit_price', 'total_price',
            'status', 'is_gift', 'gift_message', 'returned_quantity', 
            'refunded_amount', 'can_return'
        ]
        read_only_fields = ['status', 'returned_quantity', 'refunded_amount']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['can_return'] = instance.can_return()
        return representation


class OrderItemMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for order items (used in nested contexts).
    """
    product = ProductMinimalSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'unit_price', 'total_price',
            'status', 'returned_quantity', 'refunded_amount'
        ]


class OrderTrackingSerializer(serializers.ModelSerializer):
    """
    Serializer for order tracking events.
    """
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'status', 'description', 'location', 
            'created_by', 'created_at'
        ]
    
    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for orders.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    timeline = OrderTrackingSerializer(source='get_order_timeline', many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    can_cancel = serializers.BooleanField(read_only=True)
    can_return = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'status', 
            'payment_status', 'total_amount', 'shipping_amount', 'tax_amount', 
            'discount_amount', 'shipping_address', 'billing_address',
            'shipping_method', 'payment_method', 'estimated_delivery_date',
            'actual_delivery_date', 'tracking_number', 'invoice_number',
            'notes', 'items', 'total_items', 'timeline', 'can_cancel',
            'can_return', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'invoice_number', 'customer_name']
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['can_cancel'] = instance.can_cancel()
        representation['can_return'] = instance.can_return()
        return representation


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating orders.
    """
    cart_items = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of cart item IDs"
    )
    shipping_address = serializers.JSONField()
    billing_address = serializers.JSONField()
    shipping_method = serializers.CharField()
    payment_method = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating order status.
    """
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    description = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)


class OrderCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling orders.
    """
    reason = serializers.CharField()


class ReturnRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for return requests.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    processed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'order', 'order_number', 'order_item', 'product_name',
            'quantity', 'reason', 'description', 'status', 'refund_amount',
            'refund_method', 'return_tracking_number', 'return_received_date',
            'refund_processed_date', 'processed_by', 'processed_by_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['refund_amount', 'return_received_date', 
                           'refund_processed_date', 'processed_by']
    
    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return obj.processed_by.username
        return None


class ReturnRequestCreateSerializer(serializers.Serializer):
    """
    Serializer for creating return requests.
    """
    order_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=ReturnRequest.RETURN_REASON_CHOICES)
    description = serializers.CharField()


class ReturnRequestProcessSerializer(serializers.Serializer):
    """
    Serializer for processing return requests.
    """
    status = serializers.ChoiceField(choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ])
    notes = serializers.CharField(required=False, allow_blank=True)


class ReplacementSerializer(serializers.ModelSerializer):
    """
    Serializer for replacements.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    product_name = serializers.CharField(source='order_item.product.name', read_only=True)
    replacement_product_name = serializers.CharField(source='replacement_product.name', read_only=True)
    processed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Replacement
        fields = [
            'id', 'return_request', 'order', 'order_number', 'order_item',
            'product_name', 'replacement_product', 'replacement_product_name',
            'quantity', 'status', 'shipping_address', 'tracking_number',
            'shipped_date', 'delivered_date', 'processed_by', 'processed_by_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['shipped_date', 'delivered_date', 'processed_by']
    
    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return obj.processed_by.username
        return None


class ReplacementCreateSerializer(serializers.Serializer):
    """
    Serializer for creating replacements.
    """
    return_request_id = serializers.UUIDField()
    replacement_product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReplacementUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating replacements.
    """
    status = serializers.ChoiceField(choices=Replacement.STATUS_CHOICES)
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for orders with all related data.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    timeline = OrderTrackingSerializer(source='get_order_timeline', many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    can_cancel = serializers.BooleanField(read_only=True)
    can_return = serializers.BooleanField(read_only=True)
    return_requests = serializers.SerializerMethodField()
    replacements = serializers.SerializerMethodField()
    has_invoice = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'status', 
            'payment_status', 'total_amount', 'shipping_amount', 'tax_amount', 
            'discount_amount', 'shipping_address', 'billing_address',
            'shipping_method', 'payment_method', 'estimated_delivery_date',
            'actual_delivery_date', 'tracking_number', 'invoice_number',
            'notes', 'items', 'total_items', 'timeline', 'can_cancel',
            'can_return', 'return_requests', 'replacements', 'has_invoice',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'invoice_number', 'customer_name']
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    
    def get_return_requests(self, obj):
        return ReturnRequestSerializer(obj.return_requests.filter(is_deleted=False), many=True).data
    
    def get_replacements(self, obj):
        return ReplacementSerializer(obj.replacements.filter(is_deleted=False), many=True).data
    
    def get_has_invoice(self, obj):
        return hasattr(obj, 'invoice')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['can_cancel'] = instance.can_cancel()
        representation['can_return'] = instance.can_return()
        return representation


class OrderBulkUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk updating orders.
    """
    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of order IDs to update"
    )
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    description = serializers.CharField(required=False, allow_blank=True)


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order items.
    """
    class Meta:
        model = OrderItem
        fields = ['status', 'is_gift', 'gift_message']


class ReturnRequestBulkProcessSerializer(serializers.Serializer):
    """
    Serializer for bulk processing return requests.
    """
    return_request_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of return request IDs to process"
    )
    status = serializers.ChoiceField(choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ])
    notes = serializers.CharField(required=False, allow_blank=True)


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for invoices.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    order_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_number', 'invoice_number', 'invoice_date',
            'due_date', 'billing_address', 'shipping_address', 'subtotal',
            'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount',
            'notes', 'terms_and_conditions', 'file_path', 'order_items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'file_path']
    
    def get_order_items(self, obj):
        return OrderItemMinimalSerializer(obj.order.items.all(), many=True).data