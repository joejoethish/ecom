"""
Order models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import BaseModel


class Order(BaseModel):
    """
    Order model.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
        ('partially_returned', 'Partially Returned'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.JSONField(null=True, blank=True)
    billing_address = models.JSONField(null=True, blank=True)
    shipping_method = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"
    
    def get_total_items(self):
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items.all())
    
    def get_order_timeline(self):
        """Get the order timeline events."""
        return self.timeline_events.all().order_by('created_at')
    
    def add_timeline_event(self, status, description, user=None):
        """Add a new timeline event to the order."""
        return OrderTracking.objects.create(
            order=self,
            status=status,
            description=description,
            created_by=user
        )
    
    def can_cancel(self):
        """Check if the order can be cancelled."""
        non_cancellable_statuses = ['shipped', 'out_for_delivery', 'delivered', 'returned', 'refunded']
        return self.status not in non_cancellable_statuses
    
    def can_return(self):
        """Check if the order can be returned."""
        return self.status == 'delivered' and (timezone.now().date() - self.actual_delivery_date).days <= 30


class OrderItem(BaseModel):
    """
    Order item model.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_gift = models.BooleanField(default=False)
    gift_message = models.TextField(blank=True)
    returned_quantity = models.PositiveIntegerField(default=0)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def can_return(self):
        """Check if the item can be returned."""
        return (
            self.status == 'delivered' and 
            self.returned_quantity < self.quantity and
            self.order.can_return()
        )


class OrderTracking(BaseModel):
    """
    Order tracking model for maintaining status timeline.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='timeline_events')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='order_tracking_events'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.created_at}"


class ReturnRequest(BaseModel):
    """
    Return request model for handling order returns.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    RETURN_REASON_CHOICES = [
        ('damaged', 'Product Damaged'),
        ('defective', 'Product Defective'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not As Described'),
        ('unwanted', 'No Longer Wanted'),
        ('size_issue', 'Size/Fit Issue'),
        ('quality_issue', 'Quality Issue'),
        ('other', 'Other'),
    ]
    
    REFUND_METHOD_CHOICES = [
        ('original', 'Original Payment Method'),
        ('wallet', 'Store Wallet'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_requests')
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=50, choices=RETURN_REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES, default='original')
    return_tracking_number = models.CharField(max_length=100, blank=True)
    return_received_date = models.DateField(null=True, blank=True)
    refund_processed_date = models.DateField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_returns'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return {self.id} for Order {self.order.order_number}"


class Replacement(BaseModel):
    """
    Replacement model for handling product replacements.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    return_request = models.OneToOneField(
        ReturnRequest, 
        on_delete=models.CASCADE, 
        related_name='replacement',
        null=True,
        blank=True
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='replacements')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='replacements')
    replacement_product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.JSONField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_replacements'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Replacement {self.id} for Order {self.order.order_number}"


class Invoice(BaseModel):
    """
    Invoice model for order invoices.
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    billing_address = models.JSONField()
    shipping_address = models.JSONField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    file_path = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number}"