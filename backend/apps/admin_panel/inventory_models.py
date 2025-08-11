"""
Advanced Inventory Management System models for comprehensive admin panel.
"""
import uuid
import json
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from datetime import timedelta, date
from core.models import TimestampedModel
from apps.products.models import Product
from .models import AdminUser


class Warehouse(TimestampedModel):
    """
    Warehouse model for inventory management.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'warehouses'
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(TimestampedModel):
    """
    Supplier model for inventory management.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    lead_time_days = models.PositiveIntegerField(default=7)
    reliability_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    payment_terms = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class InventoryLocation(TimestampedModel):
    """
    Detailed location tracking within warehouses (zones, aisles, shelves).
    """
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    zone = models.CharField(max_length=50)  # e.g., "A", "B", "C"
    aisle = models.CharField(max_length=50)  # e.g., "01", "02", "03"
    shelf = models.CharField(max_length=50)  # e.g., "A", "B", "C"
    bin = models.CharField(max_length=50, blank=True)  # e.g., "01", "02"
    
    # Location properties
    location_code = models.CharField(max_length=100, unique=True)  # e.g., "WH1-A-01-A-01"
    capacity = models.PositiveIntegerField(default=100)
    current_utilization = models.PositiveIntegerField(default=0)
    
    # Location type and restrictions
    location_type = models.CharField(max_length=50, choices=[
        ('standard', 'Standard'),
        ('cold_storage', 'Cold Storage'),
        ('hazardous', 'Hazardous Materials'),
        ('high_value', 'High Value Items'),
        ('bulk', 'Bulk Storage'),
        ('picking', 'Picking Location'),
        ('receiving', 'Receiving Area'),
        ('shipping', 'Shipping Area'),
        ('quarantine', 'Quarantine'),
    ], default='standard')
    
    temperature_range = models.JSONField(default=dict, blank=True)  # min/max temperature
    humidity_range = models.JSONField(default=dict, blank=True)  # min/max humidity
    
    # Status
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_locations'
        verbose_name = 'Inventory Location'
        verbose_name_plural = 'Inventory Locations'
        unique_together = ['warehouse', 'zone', 'aisle', 'shelf', 'bin']
        indexes = [
            models.Index(fields=['warehouse', 'location_code']),
            models.Index(fields=['location_type']),
            models.Index(fields=['is_active', 'is_blocked']),
        ]

    def save(self, *args, **kwargs):
        """Generate location code if not set."""
        if not self.location_code:
            self.location_code = f"{self.warehouse.code}-{self.zone}-{self.aisle}-{self.shelf}-{self.bin}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.location_code

    @property
    def utilization_percentage(self):
        """Calculate location utilization percentage."""
        if self.capacity > 0:
            return (self.current_utilization / self.capacity) * 100
        return 0


class InventoryItem(TimestampedModel):
    """
    Individual inventory items with serialization and lot tracking.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='items')
    
    # Identification
    serial_number = models.CharField(max_length=100, unique=True, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    
    # Quantity and status
    quantity = models.PositiveIntegerField(default=1)
    reserved_quantity = models.PositiveIntegerField(default=0)
    
    # Quality and condition
    condition = models.CharField(max_length=50, choices=[
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
        ('expired', 'Expired'),
        ('quarantined', 'Quarantined'),
    ], default='new')
    
    quality_grade = models.CharField(max_length=10, choices=[
        ('A', 'Grade A'),
        ('B', 'Grade B'),
        ('C', 'Grade C'),
        ('D', 'Grade D'),
    ], default='A')
    
    # Dates
    manufactured_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(auto_now_add=True)
    
    # Cost information
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    landed_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Supplier information
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order_reference = models.CharField(max_length=100, blank=True)
    
    # Status
    is_available = models.BooleanField(default=True)
    is_quarantined = models.BooleanField(default=False)
    quarantine_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_items'
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
        indexes = [
            models.Index(fields=['product', 'location']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['lot_number']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['condition']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['is_available']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.serial_number or self.lot_number or 'Bulk'}"

    @property
    def available_quantity(self):
        """Calculate available quantity."""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def is_expired(self):
        """Check if item is expired."""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        """Calculate days until expiry."""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None


class InventoryValuation(TimestampedModel):
    """
    Inventory valuation with different costing methods.
    """
    COSTING_METHOD_CHOICES = [
        ('fifo', 'First In, First Out'),
        ('lifo', 'Last In, First Out'),
        ('weighted_average', 'Weighted Average'),
        ('standard_cost', 'Standard Cost'),
        ('specific_identification', 'Specific Identification'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='valuations')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='valuations')
    
    # Valuation details
    costing_method = models.CharField(max_length=50, choices=COSTING_METHOD_CHOICES)
    valuation_date = models.DateField(default=date.today)
    
    # Quantities
    total_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    reserved_quantity = models.PositiveIntegerField()
    
    # Values
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    average_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Cost breakdown
    material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    landed_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Metadata
    calculated_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    calculation_method = models.TextField(blank=True)  # Details of calculation
    
    class Meta:
        db_table = 'inventory_valuations'
        verbose_name = 'Inventory Valuation'
        verbose_name_plural = 'Inventory Valuations'
        unique_together = ['product', 'warehouse', 'valuation_date', 'costing_method']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['valuation_date']),
            models.Index(fields=['costing_method']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name} - {self.valuation_date}"


class InventoryAdjustment(TimestampedModel):
    """
    Inventory adjustments with reason codes and approval workflows.
    """
    ADJUSTMENT_TYPE_CHOICES = [
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
        ('correction', 'Correction'),
        ('write_off', 'Write Off'),
        ('found', 'Found Stock'),
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('stolen', 'Stolen/Lost'),
        ('cycle_count', 'Cycle Count'),
        ('physical_count', 'Physical Count'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('applied', 'Applied'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic information
    adjustment_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='adjustments')
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='adjustments')
    
    # Adjustment details
    adjustment_type = models.CharField(max_length=50, choices=ADJUSTMENT_TYPE_CHOICES)
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    adjustment_quantity = models.IntegerField()
    
    # Reason and approval
    reason_code = models.CharField(max_length=50)
    reason_description = models.TextField()
    supporting_documents = models.JSONField(default=list, blank=True)
    
    # Cost impact
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost_impact = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='requested_adjustments')
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_adjustments')
    applied_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_adjustments')
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    applied_date = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'inventory_adjustments'
        verbose_name = 'Inventory Adjustment'
        verbose_name_plural = 'Inventory Adjustments'
        indexes = [
            models.Index(fields=['adjustment_number']),
            models.Index(fields=['product', 'location']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_date']),
            models.Index(fields=['adjustment_type']),
        ]

    def save(self, *args, **kwargs):
        """Generate adjustment number if not set."""
        if not self.adjustment_number:
            # Generate unique adjustment number
            import uuid
            self.adjustment_number = f"ADJ{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate adjustment quantity and cost impact
        self.adjustment_quantity = self.quantity_after - self.quantity_before
        self.total_cost_impact = abs(self.adjustment_quantity) * self.unit_cost
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adjustment_number} - {self.product.name}"


class InventoryTransfer(TimestampedModel):
    """
    Inventory transfers between locations with tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('partial', 'Partially Completed'),
    ]
    
    # Transfer identification
    transfer_number = models.CharField(max_length=50, unique=True)
    
    # Locations
    source_location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='incoming_transfers')
    
    # Transfer details
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transfers')
    quantity_requested = models.PositiveIntegerField()
    quantity_shipped = models.PositiveIntegerField(default=0)
    quantity_received = models.PositiveIntegerField(default=0)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    expected_arrival_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    requested_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='requested_transfers')
    shipped_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipped_transfers')
    received_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')
    
    # Additional information
    reason = models.TextField()
    notes = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'inventory_transfers'
        verbose_name = 'Inventory Transfer'
        verbose_name_plural = 'Inventory Transfers'
        indexes = [
            models.Index(fields=['transfer_number']),
            models.Index(fields=['source_location', 'destination_location']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_date']),
        ]

    def save(self, *args, **kwargs):
        """Generate transfer number if not set."""
        if not self.transfer_number:
            import uuid
            self.transfer_number = f"TRF{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transfer_number} - {self.product.name}"

    @property
    def is_complete(self):
        """Check if transfer is complete."""
        return self.quantity_received >= self.quantity_requested


class InventoryReservation(TimestampedModel):
    """
    Inventory reservation system for pending orders and allocations.
    """
    RESERVATION_TYPE_CHOICES = [
        ('order', 'Order Reservation'),
        ('quote', 'Quote Reservation'),
        ('promotion', 'Promotion Reservation'),
        ('manual', 'Manual Reservation'),
        ('system', 'System Reservation'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('partial', 'Partially Fulfilled'),
    ]
    
    # Reservation identification
    reservation_number = models.CharField(max_length=50, unique=True)
    
    # Product and location
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reservations')
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='reservations')
    
    # Reservation details
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPE_CHOICES)
    quantity_reserved = models.PositiveIntegerField()
    quantity_fulfilled = models.PositiveIntegerField(default=0)
    
    # Related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reserved_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    fulfilled_date = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    reserved_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='reservations')
    
    # Additional information
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_reservations'
        verbose_name = 'Inventory Reservation'
        verbose_name_plural = 'Inventory Reservations'
        indexes = [
            models.Index(fields=['reservation_number']),
            models.Index(fields=['product', 'location']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['priority']),
        ]

    def save(self, *args, **kwargs):
        """Generate reservation number if not set."""
        if not self.reservation_number:
            import uuid
            self.reservation_number = f"RES{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reservation_number} - {self.product.name}"

    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to fulfill."""
        return max(0, self.quantity_reserved - self.quantity_fulfilled)

    @property
    def is_expired(self):
        """Check if reservation is expired."""
        return timezone.now() > self.expiry_date


class InventoryAlert(TimestampedModel):
    """
    Inventory alert system for low stock, overstock, and expiration notifications.
    """
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('damaged', 'Damaged Items'),
        ('slow_moving', 'Slow Moving'),
        ('fast_moving', 'Fast Moving'),
        ('reorder_point', 'Reorder Point Reached'),
        ('quality_issue', 'Quality Issue'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Alert identification
    alert_number = models.CharField(max_length=50, unique=True)
    
    # Product and location
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_alerts')
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Threshold information
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    threshold_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    triggered_date = models.DateTimeField(auto_now_add=True)
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    acknowledged_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    # Actions and notifications
    auto_actions_taken = models.JSONField(default=list, blank=True)
    notifications_sent = models.JSONField(default=list, blank=True)
    
    # Additional information
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_alerts'
        verbose_name = 'Inventory Alert'
        verbose_name_plural = 'Inventory Alerts'
        indexes = [
            models.Index(fields=['alert_number']),
            models.Index(fields=['product', 'location']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['triggered_date']),
        ]

    def save(self, *args, **kwargs):
        """Generate alert number if not set."""
        if not self.alert_number:
            import uuid
            self.alert_number = f"ALT{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alert_number} - {self.title}"


class InventoryAudit(TimestampedModel):
    """
    Inventory audit tools with cycle counting and variance reporting.
    """
    AUDIT_TYPE_CHOICES = [
        ('cycle_count', 'Cycle Count'),
        ('physical_count', 'Physical Count'),
        ('spot_check', 'Spot Check'),
        ('annual_audit', 'Annual Audit'),
        ('quality_audit', 'Quality Audit'),
        ('compliance_audit', 'Compliance Audit'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    # Audit identification
    audit_number = models.CharField(max_length=50, unique=True)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES)
    
    # Scope
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='audits')
    locations = models.ManyToManyField(InventoryLocation, blank=True, related_name='audits')
    products = models.ManyToManyField(Product, blank=True, related_name='audits')
    
    # Audit details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    planned_date = models.DateField()
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Personnel
    audit_team = models.ManyToManyField(AdminUser, related_name='audits')
    supervisor = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='supervised_audits')
    
    # Results summary
    total_items_counted = models.PositiveIntegerField(default=0)
    items_with_variances = models.PositiveIntegerField(default=0)
    total_variance_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    accuracy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Documentation
    notes = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_audits'
        verbose_name = 'Inventory Audit'
        verbose_name_plural = 'Inventory Audits'
        indexes = [
            models.Index(fields=['audit_number']),
            models.Index(fields=['audit_type']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_date']),
            models.Index(fields=['warehouse']),
        ]

    def save(self, *args, **kwargs):
        """Generate audit number if not set."""
        if not self.audit_number:
            import uuid
            self.audit_number = f"AUD{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.audit_number} - {self.get_audit_type_display()}"


class InventoryAuditItem(TimestampedModel):
    """
    Individual items counted during inventory audits.
    """
    audit = models.ForeignKey(InventoryAudit, on_delete=models.CASCADE, related_name='audit_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='audit_items')
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name='audit_items')
    
    # Count information
    system_quantity = models.IntegerField()  # Quantity per system
    counted_quantity = models.IntegerField()  # Actual counted quantity
    variance_quantity = models.IntegerField()  # Difference
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Cost impact
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    variance_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Count details
    counted_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='counted_items')
    count_date = models.DateTimeField()
    recount_required = models.BooleanField(default=False)
    recount_completed = models.BooleanField(default=False)
    
    # Additional information
    condition_notes = models.TextField(blank=True)
    discrepancy_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_audit_items'
        verbose_name = 'Inventory Audit Item'
        verbose_name_plural = 'Inventory Audit Items'
        unique_together = ['audit', 'product', 'location']
        indexes = [
            models.Index(fields=['audit', 'product']),
            models.Index(fields=['variance_quantity']),
            models.Index(fields=['count_date']),
        ]

    def __str__(self):
        return f"{self.audit.audit_number} - {self.product.name}"


class InventoryForecast(TimestampedModel):
    """
    Inventory forecasting with demand planning and reorder point optimization.
    """
    FORECAST_TYPE_CHOICES = [
        ('demand', 'Demand Forecast'),
        ('supply', 'Supply Forecast'),
        ('reorder', 'Reorder Forecast'),
        ('seasonal', 'Seasonal Forecast'),
        ('promotional', 'Promotional Forecast'),
    ]
    
    # Forecast identification
    forecast_number = models.CharField(max_length=50, unique=True)
    forecast_type = models.CharField(max_length=20, choices=FORECAST_TYPE_CHOICES)
    
    # Product and location
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='admin_forecasts')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='admin_forecasts')
    
    # Forecast period
    forecast_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Forecast data
    predicted_demand = models.PositiveIntegerField()
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100%
    
    # Recommendations
    recommended_order_quantity = models.PositiveIntegerField()
    recommended_reorder_point = models.PositiveIntegerField()
    recommended_safety_stock = models.PositiveIntegerField()
    
    # Model information
    forecasting_model = models.CharField(max_length=100)  # e.g., "Linear Regression", "ARIMA"
    model_parameters = models.JSONField(default=dict, blank=True)
    historical_data_points = models.PositiveIntegerField()
    
    # Accuracy tracking
    actual_demand = models.PositiveIntegerField(null=True, blank=True)
    forecast_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Personnel
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='forecasts')
    
    # Additional information
    notes = models.TextField(blank=True)
    external_factors = models.JSONField(default=list, blank=True)  # Seasonality, promotions, etc.
    
    class Meta:
        db_table = 'inventory_forecasts'
        verbose_name = 'Inventory Forecast'
        verbose_name_plural = 'Inventory Forecasts'
        unique_together = ['product', 'warehouse', 'forecast_date', 'forecast_type']
        indexes = [
            models.Index(fields=['forecast_number']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['forecast_date']),
            models.Index(fields=['forecast_type']),
        ]

    def save(self, *args, **kwargs):
        """Generate forecast number if not set."""
        if not self.forecast_number:
            import uuid
            self.forecast_number = f"FOR{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.forecast_number} - {self.product.name}"


class InventoryOptimization(TimestampedModel):
    """
    Inventory optimization with ABC analysis and slow-moving item identification.
    """
    ANALYSIS_TYPE_CHOICES = [
        ('abc', 'ABC Analysis'),
        ('xyz', 'XYZ Analysis'),
        ('slow_moving', 'Slow Moving Analysis'),
        ('fast_moving', 'Fast Moving Analysis'),
        ('dead_stock', 'Dead Stock Analysis'),
        ('turnover', 'Turnover Analysis'),
    ]
    
    # Analysis identification
    analysis_number = models.CharField(max_length=50, unique=True)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES)
    
    # Scope
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='optimizations')
    analysis_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Results summary
    total_products_analyzed = models.PositiveIntegerField()
    total_value_analyzed = models.DecimalField(max_digits=15, decimal_places=2)
    
    # ABC Classification counts
    category_a_count = models.PositiveIntegerField(default=0)
    category_b_count = models.PositiveIntegerField(default=0)
    category_c_count = models.PositiveIntegerField(default=0)
    
    # ABC Classification values
    category_a_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    category_b_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    category_c_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Recommendations
    recommendations = models.TextField(blank=True)
    action_items = models.JSONField(default=list, blank=True)
    
    # Personnel
    analyzed_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='optimizations')
    
    # Additional information
    methodology = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'inventory_optimizations'
        verbose_name = 'Inventory Optimization'
        verbose_name_plural = 'Inventory Optimizations'
        indexes = [
            models.Index(fields=['analysis_number']),
            models.Index(fields=['analysis_type']),
            models.Index(fields=['analysis_date']),
            models.Index(fields=['warehouse']),
        ]

    def save(self, *args, **kwargs):
        """Generate analysis number if not set."""
        if not self.analysis_number:
            import uuid
            self.analysis_number = f"OPT{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.analysis_number} - {self.get_analysis_type_display()}"


class InventoryOptimizationItem(TimestampedModel):
    """
    Individual product results from inventory optimization analysis.
    """
    optimization = models.ForeignKey(InventoryOptimization, on_delete=models.CASCADE, related_name='optimization_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='optimization_items')
    
    # Classification
    abc_category = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], blank=True)
    xyz_category = models.CharField(max_length=1, choices=[('X', 'X'), ('Y', 'Y'), ('Z', 'Z')], blank=True)
    
    # Metrics
    annual_usage_value = models.DecimalField(max_digits=15, decimal_places=2)
    annual_usage_quantity = models.PositiveIntegerField()
    turnover_rate = models.DecimalField(max_digits=8, decimal_places=2)
    days_of_supply = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Current status
    current_stock_value = models.DecimalField(max_digits=15, decimal_places=2)
    current_stock_quantity = models.PositiveIntegerField()
    last_movement_date = models.DateField(null=True, blank=True)
    days_since_last_movement = models.PositiveIntegerField(null=True, blank=True)
    
    # Recommendations
    recommended_action = models.CharField(max_length=100, blank=True)
    recommended_stock_level = models.PositiveIntegerField(null=True, blank=True)
    potential_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Flags
    is_slow_moving = models.BooleanField(default=False)
    is_dead_stock = models.BooleanField(default=False)
    is_overstocked = models.BooleanField(default=False)
    is_understocked = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'inventory_optimization_items'
        verbose_name = 'Inventory Optimization Item'
        verbose_name_plural = 'Inventory Optimization Items'
        unique_together = ['optimization', 'product']
        indexes = [
            models.Index(fields=['optimization', 'abc_category']),
            models.Index(fields=['turnover_rate']),
            models.Index(fields=['is_slow_moving']),
            models.Index(fields=['is_dead_stock']),
        ]

    def __str__(self):
        return f"{self.optimization.analysis_number} - {self.product.name}"


class InventoryReport(TimestampedModel):
    """
    Comprehensive inventory reporting with dashboards and scheduled reports.
    """
    REPORT_TYPE_CHOICES = [
        ('stock_levels', 'Stock Levels Report'),
        ('valuation', 'Inventory Valuation Report'),
        ('movement', 'Inventory Movement Report'),
        ('aging', 'Inventory Aging Report'),
        ('turnover', 'Inventory Turnover Report'),
        ('variance', 'Inventory Variance Report'),
        ('forecast', 'Inventory Forecast Report'),
        ('optimization', 'Inventory Optimization Report'),
        ('alerts', 'Inventory Alerts Report'),
        ('audit', 'Inventory Audit Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    SCHEDULE_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    # Report identification
    report_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    # Configuration
    parameters = models.JSONField(default=dict, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Scheduling
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='once')
    schedule_config = models.JSONField(default=dict, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Recipients
    recipients = models.ManyToManyField(AdminUser, blank=True, related_name='inventory_reports')
    email_recipients = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='created_inventory_reports')
    
    # Execution tracking
    total_runs = models.PositiveIntegerField(default=0)
    successful_runs = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'inventory_reports'
        verbose_name = 'Inventory Report'
        verbose_name_plural = 'Inventory Reports'
        indexes = [
            models.Index(fields=['report_number']),
            models.Index(fields=['report_type']),
            models.Index(fields=['schedule_type']),
            models.Index(fields=['next_run']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.report_number} - {self.name}"