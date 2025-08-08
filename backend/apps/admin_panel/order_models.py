"""
Enhanced Order models for the admin panel with comprehensive management features.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

# from apps.orders.models import Order, OrderItem, OrderTracking
from core.models import TimestampedModel, UUIDModel

User = get_user_model()


class OrderSearchFilter(UUIDModel, TimestampedModel):
    """
    Model for saving order search filters for quick access.
    """
    name = models.CharField(max_length=100)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_order_filters')
    filters = models.JSONField(help_text="Saved filter criteria")
    is_public = models.BooleanField(default=False, help_text="Available to all admin users")
    
    class Meta:
        unique_together = ['name', 'admin_user']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.admin_user.username}"


class OrderWorkflow(UUIDModel, TimestampedModel):
    """
    Model for defining custom order status workflows and automation rules.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    from_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    to_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    conditions = models.JSONField(help_text="Conditions that must be met for this workflow")
    actions = models.JSONField(help_text="Actions to perform when workflow is triggered")
    is_automatic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority workflows are processed first")
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name}: {self.from_status} -> {self.to_status}"


class OrderFraudScore(UUIDModel, TimestampedModel):
    """
    Model for storing fraud detection scores and risk assessments.
    """
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    risk_factors = models.JSONField(help_text="List of identified risk factors")
    is_flagged = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_fraud_scores')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"Order {self.order_id} - Risk: {self.risk_level} ({self.score})"


class OrderNote(UUIDModel, TimestampedModel):
    """
    Model for internal order notes and communications.
    """
    NOTE_TYPES = [
        ('internal', 'Internal Note'),
        ('customer', 'Customer Communication'),
        ('system', 'System Generated'),
        ('escalation', 'Escalation Note'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='internal')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_notes')
    is_important = models.BooleanField(default=False)
    is_customer_visible = models.BooleanField(default=False)
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment file paths")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_id} - {self.title}"


class OrderEscalation(UUIDModel, TimestampedModel):
    """
    Model for order escalations and exception handling.
    """
    ESCALATION_TYPES = [
        ('payment_issue', 'Payment Issue'),
        ('inventory_shortage', 'Inventory Shortage'),
        ('shipping_delay', 'Shipping Delay'),
        ('customer_complaint', 'Customer Complaint'),
        ('fraud_alert', 'Fraud Alert'),
        ('system_error', 'System Error'),
        ('manual_review', 'Manual Review Required'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    escalation_type = models.CharField(max_length=30, choices=ESCALATION_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_escalations')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_escalations')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_escalations')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Escalation {self.id} - {self.order_id} ({self.priority})"
    
    def is_overdue(self):
        """Check if escalation is overdue based on SLA."""
        if self.sla_deadline and self.status in ['open', 'in_progress']:
            return timezone.now() > self.sla_deadline
        return False


class OrderSLA(UUIDModel, TimestampedModel):
    """
    Model for tracking order SLA (Service Level Agreement) metrics.
    """
    order_id = models.UUIDField(help_text='Reference to order ID')
    processing_deadline = models.DateTimeField(null=True, blank=True)
    shipping_deadline = models.DateTimeField(null=True, blank=True)
    delivery_deadline = models.DateTimeField(null=True, blank=True)
    
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    shipping_completed_at = models.DateTimeField(null=True, blank=True)
    delivery_completed_at = models.DateTimeField(null=True, blank=True)
    
    processing_sla_met = models.BooleanField(null=True, blank=True)
    shipping_sla_met = models.BooleanField(null=True, blank=True)
    delivery_sla_met = models.BooleanField(null=True, blank=True)
    
    overall_sla_met = models.BooleanField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Order SLA"
        verbose_name_plural = "Order SLAs"
    
    def __str__(self):
        return f"SLA for Order {self.order_id}"
    
    def calculate_sla_status(self):
        """Calculate and update SLA status based on current order status."""
        # TODO: Implement when Order model is available
        # This method will need to be updated to work with the actual Order model
        pass


class OrderAllocation(UUIDModel, TimestampedModel):
    """
    Model for order allocation and inventory reservation.
    """
    ALLOCATION_STATUS = [
        ('pending', 'Pending'),
        ('allocated', 'Allocated'),
        ('partially_allocated', 'Partially Allocated'),
        ('failed', 'Failed'),
        ('released', 'Released'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    status = models.CharField(max_length=30, choices=ALLOCATION_STATUS, default='pending')
    allocated_at = models.DateTimeField(null=True, blank=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_allocations')
    allocation_details = models.JSONField(default=dict, help_text="Details of inventory allocation per item")
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Allocation for Order {self.order_id} - {self.status}"


class OrderProfitability(UUIDModel, TimestampedModel):
    """
    Model for tracking order profitability and cost analysis.
    """
    order_id = models.UUIDField(help_text='Reference to order ID')
    
    # Revenue
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Costs
    product_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_processing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    packaging_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    handling_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    marketing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Calculated fields
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Analysis
    cost_breakdown = models.JSONField(default=dict, help_text="Detailed cost breakdown")
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Order Profitabilities"
    
    def __str__(self):
        return f"Profitability for Order {self.order_id}"
    
    def calculate_profitability(self):
        """Calculate profitability metrics."""
        self.total_cost = (
            self.product_cost + self.shipping_cost + self.payment_processing_cost +
            self.packaging_cost + self.handling_cost + self.marketing_cost + self.other_costs
        )
        
        self.gross_profit = self.gross_revenue - self.product_cost
        self.net_profit = self.net_revenue - self.total_cost
        
        if self.net_revenue > 0:
            self.profit_margin_percentage = (self.net_profit / self.net_revenue) * 100
        else:
            self.profit_margin_percentage = 0
        
        self.cost_breakdown = {
            'product_cost': float(self.product_cost),
            'shipping_cost': float(self.shipping_cost),
            'payment_processing_cost': float(self.payment_processing_cost),
            'packaging_cost': float(self.packaging_cost),
            'handling_cost': float(self.handling_cost),
            'marketing_cost': float(self.marketing_cost),
            'other_costs': float(self.other_costs),
        }
        
        self.save()


class OrderDocument(UUIDModel, TimestampedModel):
    """
    Model for managing order-related documents (invoices, receipts, shipping labels, etc.).
    """
    DOCUMENT_TYPES = [
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('shipping_label', 'Shipping Label'),
        ('packing_slip', 'Packing Slip'),
        ('return_label', 'Return Label'),
        ('customs_declaration', 'Customs Declaration'),
        ('delivery_confirmation', 'Delivery Confirmation'),
        ('other', 'Other'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_documents')
    is_customer_accessible = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_type} for Order {self.order_id}"


class OrderQualityControl(UUIDModel, TimestampedModel):
    """
    Model for order quality control and inspection workflows.
    """
    QC_STATUS = [
        ('pending', 'Pending Inspection'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional_pass', 'Conditional Pass'),
    ]
    
    order_id = models.UUIDField(help_text='Reference to order ID')
    status = models.CharField(max_length=20, choices=QC_STATUS, default='pending')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='qc_inspections')
    inspection_date = models.DateTimeField(null=True, blank=True)
    checklist = models.JSONField(default=dict, help_text="Quality control checklist items")
    issues_found = models.JSONField(default=list, help_text="List of issues found during inspection")
    corrective_actions = models.JSONField(default=list, help_text="Corrective actions taken")
    notes = models.TextField(blank=True)
    requires_reinspection = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Order Quality Control"
        verbose_name_plural = "Order Quality Controls"
    
    def __str__(self):
        return f"QC for Order {self.order_id} - {self.status}"


class OrderSubscription(UUIDModel, TimestampedModel):
    """
    Model for handling subscription and recurring orders.
    """
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    original_order_id = models.UUIDField(help_text='Reference to original order ID')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_subscriptions')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    next_order_date = models.DateField()
    last_order_date = models.DateField(null=True, blank=True)
    total_orders_generated = models.PositiveIntegerField(default=0)
    max_orders = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of orders to generate")
    
    subscription_start_date = models.DateField()
    subscription_end_date = models.DateField(null=True, blank=True)
    
    # Subscription details
    items_config = models.JSONField(help_text="Configuration for subscription items")
    shipping_address = models.JSONField()
    billing_address = models.JSONField()
    payment_method = models.CharField(max_length=50)
    
    # Modification tracking
    paused_at = models.DateTimeField(null=True, blank=True)
    paused_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paused_subscriptions')
    pause_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Subscription for Order {self.original_order_id} - {self.frequency}"
    
    def calculate_next_order_date(self):
        """Calculate the next order date based on frequency."""
        from datetime import timedelta
        
        base_date = self.last_order_date or self.subscription_start_date
        
        if self.frequency == 'weekly':
            self.next_order_date = base_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            self.next_order_date = base_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            # Add one month (approximate)
            if base_date.month == 12:
                self.next_order_date = base_date.replace(year=base_date.year + 1, month=1)
            else:
                self.next_order_date = base_date.replace(month=base_date.month + 1)
        elif self.frequency == 'quarterly':
            # Add three months
            month = base_date.month + 3
            year = base_date.year
            if month > 12:
                month -= 12
                year += 1
            self.next_order_date = base_date.replace(year=year, month=month)
        elif self.frequency == 'yearly':
            self.next_order_date = base_date.replace(year=base_date.year + 1)
        
        self.save()