from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class ShippingPartner(models.Model):
    """
    Model for shipping partners like Shiprocket, Delhivery, etc.
    """
    PARTNER_CHOICES = [
        ('SHIPROCKET', 'Shiprocket'),
        ('DELHIVERY', 'Delhivery'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(_('Partner Name'), max_length=100)
    code = models.CharField(_('Partner Code'), max_length=50, unique=True)
    partner_type = models.CharField(_('Partner Type'), max_length=20, choices=PARTNER_CHOICES)
    api_key = models.CharField(_('API Key'), max_length=255)
    api_secret = models.CharField(_('API Secret'), max_length=255, blank=True)
    base_url = models.URLField(_('API Base URL'))
    is_active = models.BooleanField(_('Active'), default=True)
    
    # Partner-specific configuration stored as JSON
    configuration = models.JSONField(_('Configuration'), default=dict, blank=True)
    
    # Service areas and capabilities
    supports_cod = models.BooleanField(_('Supports COD'), default=True)
    supports_prepaid = models.BooleanField(_('Supports Prepaid'), default=True)
    supports_international = models.BooleanField(_('Supports International'), default=False)
    supports_return = models.BooleanField(_('Supports Returns'), default=True)
    
    # Contact information
    contact_person = models.CharField(_('Contact Person'), max_length=100, blank=True)
    contact_email = models.EmailField(_('Contact Email'), blank=True)
    contact_phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Shipping Partner')
        verbose_name_plural = _('Shipping Partners')
    
    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class ServiceableArea(models.Model):
    """
    Model to store pin codes/areas serviced by shipping partners
    """
    shipping_partner = models.ForeignKey(
        ShippingPartner, 
        on_delete=models.CASCADE,
        related_name='serviceable_areas'
    )
    
    # Pin code validation (6 digits for India)
    pin_code_validator = RegexValidator(
        regex=r'^\d{6}$',
        message=_('Pin code must be 6 digits')
    )
    pin_code = models.CharField(
        _('Pin Code'), 
        max_length=6, 
        validators=[pin_code_validator]
    )
    
    city = models.CharField(_('City'), max_length=100)
    state = models.CharField(_('State'), max_length=100)
    country = models.CharField(_('Country'), max_length=100, default='India')
    
    # Delivery timeframe in days
    min_delivery_days = models.PositiveSmallIntegerField(_('Minimum Delivery Days'), default=1)
    max_delivery_days = models.PositiveSmallIntegerField(_('Maximum Delivery Days'), default=3)
    
    is_active = models.BooleanField(_('Active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Serviceable Area')
        verbose_name_plural = _('Serviceable Areas')
        unique_together = ('shipping_partner', 'pin_code')
    
    def __str__(self):
        return f"{self.pin_code} - {self.city}, {self.state}"


class DeliverySlot(models.Model):
    """
    Model for delivery time slots
    """
    name = models.CharField(_('Slot Name'), max_length=100)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    
    # Days of week this slot is available (0-6, Monday is 0)
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    day_of_week = models.IntegerField(_('Day of Week'), choices=DAYS_OF_WEEK)
    
    # Additional fee for this slot (if any)
    additional_fee = models.DecimalField(
        _('Additional Fee'), 
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    # Maximum orders that can be delivered in this slot
    max_orders = models.PositiveIntegerField(_('Maximum Orders'), default=50)
    
    is_active = models.BooleanField(_('Active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Delivery Slot')
        verbose_name_plural = _('Delivery Slots')
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        day = self.get_day_of_week_display()
        return f"{day} {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Shipment(models.Model):
    """
    Model for tracking shipments
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('SHIPPED', _('Shipped')),
        ('IN_TRANSIT', _('In Transit')),
        ('OUT_FOR_DELIVERY', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')),
        ('FAILED_DELIVERY', _('Failed Delivery')),
        ('RETURNED', _('Returned')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    # Order reference (using string to avoid circular imports)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='shipments'
    )
    
    shipping_partner = models.ForeignKey(
        ShippingPartner,
        on_delete=models.PROTECT,
        related_name='shipments'
    )
    
    # Shipping details
    tracking_number = models.CharField(_('Tracking Number'), max_length=100, unique=True)
    shipping_label_url = models.URLField(_('Shipping Label URL'), blank=True)
    
    # Partner reference IDs
    partner_order_id = models.CharField(_('Partner Order ID'), max_length=100, blank=True)
    partner_shipment_id = models.CharField(_('Partner Shipment ID'), max_length=100, blank=True)
    
    # Status and timestamps
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    estimated_delivery_date = models.DateField(_('Estimated Delivery Date'), null=True, blank=True)
    
    # Selected delivery slot (if applicable)
    delivery_slot = models.ForeignKey(
        DeliverySlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments'
    )
    
    # Shipping address details
    shipping_address = models.JSONField(_('Shipping Address'))
    
    # Package details
    weight = models.DecimalField(_('Weight (kg)'), max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(_('Dimensions'), default=dict, blank=True)
    
    # Shipping costs
    shipping_cost = models.DecimalField(_('Shipping Cost'), max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    shipped_at = models.DateTimeField(_('Shipped At'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('Delivered At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Shipment')
        verbose_name_plural = _('Shipments')
    
    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.get_status_display()}"


class ShipmentTracking(models.Model):
    """
    Model for tracking shipment status updates
    """
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_updates'
    )
    
    status = models.CharField(_('Status'), max_length=20, choices=Shipment.STATUS_CHOICES)
    description = models.TextField(_('Description'))
    location = models.CharField(_('Location'), max_length=255, blank=True)
    
    # Raw response from shipping partner
    raw_response = models.JSONField(_('Raw Response'), default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(_('Timestamp'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Shipment Tracking')
        verbose_name_plural = _('Shipment Tracking')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.get_status_display()} at {self.timestamp}"


class ShippingRate(models.Model):
    """
    Model for storing shipping rates by weight, distance, and partner
    """
    shipping_partner = models.ForeignKey(
        ShippingPartner,
        on_delete=models.CASCADE,
        related_name='shipping_rates'
    )
    
    # Source and destination
    source_pin_code = models.CharField(_('Source Pin Code'), max_length=6, blank=True)
    destination_pin_code = models.CharField(_('Destination Pin Code'), max_length=6, blank=True)
    
    # Weight range
    min_weight = models.DecimalField(_('Minimum Weight (kg)'), max_digits=8, decimal_places=2)
    max_weight = models.DecimalField(_('Maximum Weight (kg)'), max_digits=8, decimal_places=2)
    
    # Distance range (in km)
    min_distance = models.DecimalField(_('Minimum Distance (km)'), max_digits=10, decimal_places=2, null=True, blank=True)
    max_distance = models.DecimalField(_('Maximum Distance (km)'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Rate details
    base_rate = models.DecimalField(_('Base Rate'), max_digits=10, decimal_places=2)
    per_kg_rate = models.DecimalField(_('Per Kg Rate'), max_digits=10, decimal_places=2, default=0.00)
    per_km_rate = models.DecimalField(_('Per Km Rate'), max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Shipping Rate')
        verbose_name_plural = _('Shipping Rates')
    
    def __str__(self):
        return f"{self.shipping_partner.name} - {self.min_weight}kg to {self.max_weight}kg"