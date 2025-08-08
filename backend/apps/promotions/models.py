"""
Comprehensive Promotion and Coupon Management Models
"""
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

User = get_user_model()


class PromotionType(models.TextChoices):
    """Types of promotions available"""
    PERCENTAGE = 'percentage', 'Percentage Discount'
    FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount Discount'
    BOGO = 'bogo', 'Buy One Get One'
    FREE_SHIPPING = 'free_shipping', 'Free Shipping'
    BUNDLE = 'bundle', 'Bundle Discount'
    TIERED = 'tiered', 'Tiered Discount'
    DYNAMIC = 'dynamic', 'Dynamic Pricing'


class PromotionStatus(models.TextChoices):
    """Status of promotions"""
    DRAFT = 'draft', 'Draft'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'


class TargetType(models.TextChoices):
    """Types of promotion targets"""
    ALL_CUSTOMERS = 'all_customers', 'All Customers'
    CUSTOMER_SEGMENT = 'customer_segment', 'Customer Segment'
    SPECIFIC_CUSTOMERS = 'specific_customers', 'Specific Customers'
    NEW_CUSTOMERS = 'new_customers', 'New Customers'
    RETURNING_CUSTOMERS = 'returning_customers', 'Returning Customers'
    VIP_CUSTOMERS = 'vip_customers', 'VIP Customers'


class PromotionChannel(models.TextChoices):
    """Channels where promotions can be applied"""
    WEBSITE = 'website', 'Website'
    MOBILE_APP = 'mobile_app', 'Mobile App'
    EMAIL = 'email', 'Email Campaign'
    SMS = 'sms', 'SMS Campaign'
    SOCIAL_MEDIA = 'social_media', 'Social Media'
    AFFILIATE = 'affiliate', 'Affiliate'
    IN_STORE = 'in_store', 'In Store'


class Promotion(models.Model):
    """Main promotion model with comprehensive features"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=200)
    description = models.TextField()
    internal_notes = models.TextField(blank=True)
    
    # Promotion Configuration
    promotion_type = models.CharField(max_length=20, choices=PromotionType.choices)
    status = models.CharField(max_length=20, choices=PromotionStatus.choices, default=PromotionStatus.DRAFT)
    
    # Discount Configuration
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum discount amount for percentage discounts"
    )
    
    # BOGO Configuration
    buy_quantity = models.PositiveIntegerField(default=1, help_text="Buy X items")
    get_quantity = models.PositiveIntegerField(default=1, help_text="Get Y items")
    get_discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage for 'get' items (100% = free)"
    )
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Usage Limits
    usage_limit_total = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Total number of times this promotion can be used"
    )
    usage_limit_per_customer = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Number of times each customer can use this promotion"
    )
    usage_count = models.PositiveIntegerField(default=0)
    
    # Minimum Requirements
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    minimum_quantity = models.PositiveIntegerField(null=True, blank=True)
    
    # Targeting
    target_type = models.CharField(max_length=20, choices=TargetType.choices)
    target_customer_segments = models.JSONField(default=list, blank=True)
    target_customer_ids = models.JSONField(default=list, blank=True)
    
    # Channels
    allowed_channels = models.JSONField(default=list, blank=True)
    
    # Stacking Rules
    can_stack_with_other_promotions = models.BooleanField(default=False)
    stackable_promotion_types = models.JSONField(default=list, blank=True)
    excluded_promotion_ids = models.JSONField(default=list, blank=True)
    
    # Priority and Ordering
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Higher numbers have higher priority"
    )
    
    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_group = models.CharField(max_length=10, blank=True)
    ab_test_traffic_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Approval Workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_promotions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Budget Management
    budget_limit = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    budget_spent = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    
    # Performance Tracking
    conversion_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Conversion rate percentage"
    )
    roi = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Return on Investment"
    )
    
    # Fraud Detection
    fraud_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_flagged_for_review = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_promotions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'promotions_promotion'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date', 'end_date']),
            models.Index(fields=['promotion_type']),
            models.Index(fields=['target_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_promotion_type_display()})"
    
    @property
    def is_active(self):
        """Check if promotion is currently active"""
        now = timezone.now()
        return (
            self.status == PromotionStatus.ACTIVE and
            self.start_date <= now <= self.end_date and
            (self.usage_limit_total is None or self.usage_count < self.usage_limit_total) and
            (self.budget_limit is None or self.budget_spent < self.budget_limit)
        )
    
    @property
    def days_remaining(self):
        """Calculate days remaining for the promotion"""
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return None
    
    def can_be_used_by_customer(self, customer):
        """Check if promotion can be used by a specific customer"""
        if not self.is_active:
            return False
        
        # Check customer targeting
        if self.target_type == TargetType.SPECIFIC_CUSTOMERS:
            return str(customer.id) in self.target_customer_ids
        elif self.target_type == TargetType.CUSTOMER_SEGMENT:
            # This would need to be implemented based on customer segmentation logic
            pass
        
        # Check usage limit per customer
        if self.usage_limit_per_customer:
            usage_count = PromotionUsage.objects.filter(
                promotion=self,
                customer=customer
            ).count()
            if usage_count >= self.usage_limit_per_customer:
                return False
        
        return True


class PromotionProduct(models.Model):
    """Products included in or excluded from promotions"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='promotion_products')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    is_included = models.BooleanField(default=True, help_text="True for included, False for excluded")
    
    class Meta:
        db_table = 'promotions_promotion_product'
        unique_together = ['promotion', 'product']


class PromotionCategory(models.Model):
    """Categories included in or excluded from promotions"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='promotion_categories')
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE)
    is_included = models.BooleanField(default=True, help_text="True for included, False for excluded")
    
    class Meta:
        db_table = 'promotions_promotion_category'
        unique_together = ['promotion', 'category']


class Coupon(models.Model):
    """Coupon codes for promotions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='coupons')
    
    # Coupon Code
    code = models.CharField(max_length=50, unique=True)
    is_single_use = models.BooleanField(default=False)
    
    # Usage Tracking
    usage_count = models.PositiveIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'promotions_coupon'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Coupon: {self.code}"
    
    def can_be_used(self):
        """Check if coupon can be used"""
        return (
            self.is_active and
            self.promotion.is_active and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )


class PromotionUsage(models.Model):
    """Track promotion usage by customers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='usages')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey('customers.CustomerProfile', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    
    # Usage Details
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Context
    channel = models.CharField(max_length=20, choices=PromotionChannel.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Fraud Detection
    is_suspicious = models.BooleanField(default=False)
    fraud_reasons = models.JSONField(default=list, blank=True)
    
    # Metadata
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promotions_usage'
        indexes = [
            models.Index(fields=['promotion', 'customer']),
            models.Index(fields=['used_at']),
            models.Index(fields=['is_suspicious']),
        ]


class PromotionAnalytics(models.Model):
    """Daily analytics for promotions"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Usage Metrics
    total_uses = models.PositiveIntegerField(default=0)
    unique_customers = models.PositiveIntegerField(default=0)
    
    # Financial Metrics
    total_discount_given = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Performance Metrics
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Channel Breakdown
    channel_breakdown = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'promotions_analytics'
        unique_together = ['promotion', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['promotion', 'date']),
        ]


class PromotionApproval(models.Model):
    """Approval workflow for promotions"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Approval Details
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('changes_requested', 'Changes Requested'),
        ]
    )
    comments = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'promotions_approval'
        unique_together = ['promotion', 'approver']


class PromotionAuditLog(models.Model):
    """Audit trail for promotion changes"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Change Details
    action = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('activated', 'Activated'),
            ('deactivated', 'Deactivated'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('deleted', 'Deleted'),
        ]
    )
    changes = models.JSONField(default=dict, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promotions_audit_log'
        indexes = [
            models.Index(fields=['promotion', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
        ]


class PromotionTemplate(models.Model):
    """Templates for quick promotion creation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template Information
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    
    # Template Configuration
    template_data = models.JSONField(help_text="JSON configuration for the promotion")
    
    # Usage Tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'promotions_template'
        ordering = ['-usage_count', 'name']


class PromotionSchedule(models.Model):
    """Scheduled promotion activations and deactivations"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='schedules')
    
    # Schedule Configuration
    action = models.CharField(
        max_length=20,
        choices=[
            ('activate', 'Activate'),
            ('deactivate', 'Deactivate'),
            ('pause', 'Pause'),
            ('resume', 'Resume'),
        ]
    )
    scheduled_time = models.DateTimeField()
    
    # Status
    is_executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    execution_result = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promotions_schedule'
        indexes = [
            models.Index(fields=['scheduled_time', 'is_executed']),
        ]