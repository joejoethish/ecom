from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    ShippingPartner, 
    ServiceableArea, 
    DeliverySlot, 
    Shipment, 
    ShipmentTracking,
    ShippingRate
)


class ShippingPartnerSerializer(serializers.ModelSerializer):
    """Serializer for shipping partners"""
    
    class Meta:
        model = ShippingPartner
        fields = [
            'id', 'name', 'code', 'partner_type', 'base_url',
            'is_active', 'supports_cod', 'supports_prepaid',
            'supports_international', 'supports_return',
            'contact_person', 'contact_email', 'contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceableAreaSerializer(serializers.ModelSerializer):
    """Serializer for serviceable areas"""
    
    class Meta:
        model = ServiceableArea
        fields = [
            'id', 'shipping_partner', 'pin_code', 'city', 'state',
            'country', 'min_delivery_days', 'max_delivery_days',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DeliverySlotSerializer(serializers.ModelSerializer):
    """Serializer for delivery slots"""
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DeliverySlot
        fields = [
            'id', 'name', 'start_time', 'end_time', 'day_of_week',
            'day_of_week_display', 'additional_fee', 'max_orders',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    """Serializer for shipment tracking updates"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShipmentTracking
        fields = [
            'id', 'shipment', 'status', 'status_display', 'description',
            'location', 'timestamp', 'created_at'
        ]
        read_only_fields = ['created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer for shipments"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tracking_updates = ShipmentTrackingSerializer(many=True, read_only=True)
    shipping_partner_name = serializers.CharField(source='shipping_partner.name', read_only=True)
    delivery_slot_display = serializers.CharField(source='delivery_slot.__str__', read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'order', 'shipping_partner', 'shipping_partner_name',
            'tracking_number', 'shipping_label_url', 'partner_order_id',
            'partner_shipment_id', 'status', 'status_display',
            'estimated_delivery_date', 'delivery_slot', 'delivery_slot_display',
            'shipping_address', 'weight', 'dimensions', 'shipping_cost',
            'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'tracking_updates'
        ]
        read_only_fields = ['created_at', 'updated_at', 'shipped_at', 'delivered_at']


class ShippingRateSerializer(serializers.ModelSerializer):
    """Serializer for shipping rates"""
    shipping_partner_name = serializers.CharField(source='shipping_partner.name', read_only=True)
    
    class Meta:
        model = ShippingRate
        fields = [
            'id', 'shipping_partner', 'shipping_partner_name',
            'source_pin_code', 'destination_pin_code',
            'min_weight', 'max_weight', 'min_distance', 'max_distance',
            'base_rate', 'per_kg_rate', 'per_km_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ShippingRateCalculationSerializer(serializers.Serializer):
    """Serializer for shipping rate calculation requests"""
    source_pin_code = serializers.CharField(max_length=6)
    destination_pin_code = serializers.CharField(max_length=6)
    weight = serializers.DecimalField(max_digits=8, decimal_places=2)
    dimensions = serializers.JSONField(required=False)
    shipping_partner_id = serializers.IntegerField(required=False)


class DeliverySlotAvailabilitySerializer(serializers.Serializer):
    """Serializer for checking delivery slot availability"""
    delivery_date = serializers.DateField()
    pin_code = serializers.CharField(max_length=6)


class TrackingWebhookSerializer(serializers.Serializer):
    """Serializer for tracking update webhooks"""
    tracking_number = serializers.CharField(max_length=100)
    status = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField()
    partner_data = serializers.JSONField(required=False, default=dict)
    
    def validate_tracking_number(self, value):
        """Validate tracking number format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Tracking number cannot be empty")
        return value.strip()
    
    def validate_status(self, value):
        """Validate status value"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Status cannot be empty")
        return value.strip().upper()


class BulkShipmentUpdateSerializer(serializers.Serializer):
    """Serializer for bulk shipment status updates"""
    shipment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    status = serializers.CharField(max_length=20)
    description = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status against available choices"""
        from .models import Shipment
        valid_statuses = [choice[0] for choice in Shipment.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value


class ShipmentAnalyticsSerializer(serializers.Serializer):
    """Serializer for shipment analytics data"""
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    shipping_partner_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    
    def validate(self, data):
        """Validate date range"""
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("date_from must be before date_to")
        return data