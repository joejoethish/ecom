from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    ShippingPartner,
    ServiceableArea,
    DeliverySlot,
    Shipment,
    ShipmentTracking,
    ShippingRate
)

@admin.register(ShippingPartner)
class ShippingPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'partner_type', 'is_active')
    list_filter = ('partner_type', 'is_active', 'supports_cod', 'supports_international')
    search_fields = ('name', 'code')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'partner_type', 'is_active')
        }),
        (_('API Configuration'), {
            'fields': ('api_key', 'api_secret', 'base_url', 'configuration')
        }),
        (_('Capabilities'), {
            'fields': ('supports_cod', 'supports_prepaid', 'supports_international', 'supports_return')
        }),
        (_('Contact Information'), {
            'fields': ('contact_person', 'contact_email', 'contact_phone')
        }),
    )


@admin.register(ServiceableArea)
class ServiceableAreaAdmin(admin.ModelAdmin):
    list_display = ('pin_code', 'city', 'state', 'shipping_partner', 'is_active')
    list_filter = ('shipping_partner', 'state', 'is_active')
    search_fields = ('pin_code', 'city', 'state')
    list_select_related = ('shipping_partner',)


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'day_of_week', 'start_time', 'end_time', 'additional_fee', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('name',)


class ShipmentTrackingInline(admin.TabularInline):
    model = ShipmentTracking
    extra = 0
    readonly_fields = ('timestamp', 'created_at')
    fields = ('status', 'description', 'location', 'timestamp')
    can_delete = False
    max_num = 0


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order', 'shipping_partner', 'status', 'created_at')
    list_filter = ('status', 'shipping_partner', 'created_at')
    search_fields = ('tracking_number', 'order__order_number', 'partner_order_id')
    readonly_fields = ('created_at', 'updated_at', 'shipped_at', 'delivered_at')
    inlines = [ShipmentTrackingInline]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('order', 'shipping_partner', 'status')
        }),
        (_('Tracking Information'), {
            'fields': ('tracking_number', 'partner_order_id', 'partner_shipment_id', 'shipping_label_url')
        }),
        (_('Delivery Details'), {
            'fields': ('estimated_delivery_date', 'delivery_slot', 'shipping_address')
        }),
        (_('Package Information'), {
            'fields': ('weight', 'dimensions', 'shipping_cost')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at')
        }),
    )


@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'description', 'location')
    readonly_fields = ('timestamp', 'created_at')


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ('shipping_partner', 'source_pin_code', 'destination_pin_code', 'min_weight', 'max_weight', 'base_rate')
    list_filter = ('shipping_partner', 'created_at')
    search_fields = ('source_pin_code', 'destination_pin_code')