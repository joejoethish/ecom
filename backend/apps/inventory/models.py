from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.products.models import Product


class Supplier(models.Model):
    """
    Model for managing product suppliers with contact information and performance metrics.
    """
    name = models.CharField(_("Supplier Name"), max_length=255)
    code = models.CharField(_("Supplier Code"), max_length=50, unique=True)
    contact_person = models.CharField(_("Contact Person"), max_length=255, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    
    # Performance metrics
    lead_time_days = models.PositiveIntegerField(_("Lead Time (days)"), default=7)
    reliability_rating = models.DecimalField(
        _("Reliability Rating"), 
        max_digits=3, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=5.00
    )
    
    # Financial information
    payment_terms = models.CharField(_("Payment Terms"), max_length=255, blank=True)
    currency = models.CharField(_("Currency"), max_length=3, default="USD")
    
    # Status and timestamps
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """
    Model for managing multiple warehouses for inventory storage.
    """
    name = models.CharField(_("Warehouse Name"), max_length=255)
    code = models.CharField(_("Warehouse Code"), max_length=50, unique=True)
    location = models.CharField(_("Location"), max_length=255)
    address = models.TextField(_("Address"))
    contact_person = models.CharField(_("Contact Person"), max_length=255, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    
    # Capacity and status
    capacity = models.PositiveIntegerField(_("Capacity (units)"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Warehouse")
        verbose_name_plural = _("Warehouses")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Inventory(models.Model):
    """
    Model for tracking product inventory levels across warehouses.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="inventories",
        verbose_name=_("Product")
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="inventories",
        verbose_name=_("Warehouse")
    )
    quantity = models.PositiveIntegerField(_("Available Quantity"), default=0)
    reserved_quantity = models.PositiveIntegerField(_("Reserved Quantity"), default=0)
    
    # Stock level thresholds
    minimum_stock_level = models.PositiveIntegerField(_("Minimum Stock Level"), default=10)
    maximum_stock_level = models.PositiveIntegerField(_("Maximum Stock Level"), default=1000)
    reorder_point = models.PositiveIntegerField(_("Reorder Point"), default=20)
    
    # Cost information
    cost_price = models.DecimalField(_("Cost Price"), max_digits=10, decimal_places=2)
    
    # Supplier information
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supplied_inventories",
        verbose_name=_("Supplier")
    )
    
    # Status and timestamps
    last_restocked = models.DateTimeField(_("Last Restocked"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Inventory")
        verbose_name_plural = _("Inventories")
        unique_together = ["product", "warehouse"]
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name} ({self.quantity})"
    
    @property
    def available_quantity(self):
        """Returns the quantity available for sale (total - reserved)"""
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def needs_reordering(self):
        """Checks if the inventory needs reordering"""
        return self.quantity <= self.reorder_point
    
    @property
    def stock_status(self):
        """Returns the stock status based on current levels"""
        if self.quantity <= 0:
            return "OUT_OF_STOCK"
        elif self.quantity <= self.reorder_point:
            return "LOW_STOCK"
        elif self.quantity >= self.maximum_stock_level:
            return "OVERSTOCK"
        else:
            return "IN_STOCK"


class InventoryTransaction(models.Model):
    """
    Model for tracking all inventory movements with complete audit trail.
    """
    TRANSACTION_TYPES = [
        ("PURCHASE", _("Purchase")),
        ("SALE", _("Sale")),
        ("RETURN", _("Return")),
        ("ADJUSTMENT", _("Adjustment")),
        ("TRANSFER", _("Transfer")),
        ("DAMAGED", _("Damaged/Lost")),
        ("EXPIRED", _("Expired")),
    ]
    
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Inventory")
    )
    transaction_type = models.CharField(_("Transaction Type"), max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(_("Quantity Change"))
    reference_number = models.CharField(_("Reference Number"), max_length=100, blank=True)
    
    # Related entities
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_transactions",
        verbose_name=_("Order")
    )
    
    # Transfer information (for warehouse transfers)
    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outgoing_transfers",
        verbose_name=_("Source Warehouse")
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_transfers",
        verbose_name=_("Destination Warehouse")
    )
    
    # Batch and lot tracking
    batch_number = models.CharField(_("Batch Number"), max_length=100, blank=True)
    expiry_date = models.DateField(_("Expiry Date"), null=True, blank=True)
    
    # Cost information
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(_("Total Cost"), max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Notes and audit information
    notes = models.TextField(_("Notes"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventory_transactions",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Inventory Transaction")
        verbose_name_plural = _("Inventory Transactions")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.inventory.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total cost if unit cost is provided"""
        if self.unit_cost and self.quantity:
            self.total_cost = self.unit_cost * abs(self.quantity)
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """
    Model for managing purchase orders to suppliers.
    """
    STATUS_CHOICES = [
        ("DRAFT", _("Draft")),
        ("SUBMITTED", _("Submitted")),
        ("CONFIRMED", _("Confirmed")),
        ("PARTIAL", _("Partially Received")),
        ("RECEIVED", _("Received")),
        ("CANCELLED", _("Cancelled")),
    ]
    
    po_number = models.CharField(_("PO Number"), max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Supplier")
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Warehouse")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    
    # Dates
    order_date = models.DateField(_("Order Date"), auto_now_add=True)
    expected_delivery_date = models.DateField(_("Expected Delivery Date"), null=True, blank=True)
    actual_delivery_date = models.DateField(_("Actual Delivery Date"), null=True, blank=True)
    
    # Financial information
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_("Shipping Cost"), max_digits=10, decimal_places=2, default=0)
    
    # Notes and audit information
    notes = models.TextField(_("Notes"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_purchase_orders",
        verbose_name=_("Created By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_purchase_orders",
        verbose_name=_("Approved By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-order_date"]
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    """
    Model for individual items in a purchase order.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Purchase Order")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="purchase_order_items",
        verbose_name=_("Product")
    )
    quantity_ordered = models.PositiveIntegerField(_("Quantity Ordered"))
    quantity_received = models.PositiveIntegerField(_("Quantity Received"), default=0)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2)
    
    # Status
    is_completed = models.BooleanField(_("Completed"), default=False)
    
    class Meta:
        verbose_name = _("Purchase Order Item")
        verbose_name_plural = _("Purchase Order Items")
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_ordered} units"
    
    @property
    def total_price(self):
        """Calculate the total price for this item"""
        return self.quantity_ordered * self.unit_price
    
    @property
    def remaining_quantity(self):
        """Calculate the remaining quantity to be received"""
        return max(0, self.quantity_ordered - self.quantity_received)