"""
Advanced Customer Management System models for the admin panel.
"""
import uuid
import json
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import TimestampedModel
from apps.customers.models import CustomerProfile
from apps.orders.models import Order

User = get_user_model()


class CustomerSegment(TimestampedModel):
    """
    Dynamic customer segmentation for targeted marketing.
    """
    SEGMENT_TYPE_CHOICES = [
        ('demographic', 'Demographic'),
        ('behavioral', 'Behavioral'),
        ('geographic', 'Geographic'),
        ('psychographic', 'Psychographic'),
        ('transactional', 'Transactional'),
        ('lifecycle', 'Lifecycle'),
        ('value_based', 'Value Based'),
        ('custom', 'Custom'),
    ]
    
    # Segment identification
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPE_CHOICES)
    
    # Segmentation criteria (stored as JSON for flexibility)
    criteria = models.JSONField(default=dict, help_text="Segmentation rules and conditions")
    
    # Segment properties
    is_active = models.BooleanField(default=True)
    is_dynamic = models.BooleanField(default=True, help_text="Auto-update membership based on criteria")
    priority = models.IntegerField(default=0, help_text="Higher priority segments take precedence")
    
    # Analytics
    customer_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'customer_segments'
        verbose_name = 'Customer Segment'
        verbose_name_plural = 'Customer Segments'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['segment_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['priority']),
            models.Index(fields=['last_calculated']),
        ]

    def __str__(self):
        return f"{self.name} ({self.customer_count} customers)"

    def calculate_membership(self):
        """Calculate and update segment membership based on criteria."""
        # This would contain complex logic to evaluate criteria against customer data
        # For now, we'll implement a basic structure
        pass


class CustomerSegmentMembership(TimestampedModel):
    """
    Track customer membership in segments.
    """
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='segment_memberships')
    segment = models.ForeignKey(CustomerSegment, on_delete=models.CASCADE, related_name='memberships')
    
    # Membership details
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    confidence_score = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Metadata
    auto_assigned = models.BooleanField(default=True)
    assigned_by = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'customer_segment_memberships'
        verbose_name = 'Customer Segment Membership'
        verbose_name_plural = 'Customer Segment Memberships'
        unique_together = ('customer', 'segment')
        indexes = [
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['segment', 'is_active']),
            models.Index(fields=['joined_at']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} in {self.segment.name}"


class CustomerLifecycleStage(TimestampedModel):
    """
    Track customer lifecycle stages (prospect, active, inactive, churned).
    """
    STAGE_CHOICES = [
        ('prospect', 'Prospect'),
        ('new_customer', 'New Customer'),
        ('active', 'Active Customer'),
        ('at_risk', 'At Risk'),
        ('inactive', 'Inactive'),
        ('churned', 'Churned'),
        ('win_back', 'Win Back'),
        ('loyal', 'Loyal Customer'),
        ('champion', 'Champion'),
    ]
    
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='lifecycle_stage')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospect')
    previous_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, blank=True)
    
    # Stage metrics
    stage_entry_date = models.DateTimeField(auto_now_add=True)
    days_in_current_stage = models.IntegerField(default=0)
    total_stage_changes = models.IntegerField(default=0)
    
    # Predictive scores
    churn_probability = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    engagement_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    loyalty_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    # Automation
    auto_calculated = models.BooleanField(default=True)
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_lifecycle_stages'
        verbose_name = 'Customer Lifecycle Stage'
        verbose_name_plural = 'Customer Lifecycle Stages'
        indexes = [
            models.Index(fields=['current_stage']),
            models.Index(fields=['churn_probability']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['stage_entry_date']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_current_stage_display()}"

    def update_stage(self, new_stage, reason=""):
        """Update customer lifecycle stage."""
        if new_stage != self.current_stage:
            self.previous_stage = self.current_stage
            self.current_stage = new_stage
            self.stage_entry_date = timezone.now()
            self.total_stage_changes += 1
            self.save()
            
            # Log the stage change
            CustomerLifecycleHistory.objects.create(
                customer=self.customer,
                from_stage=self.previous_stage,
                to_stage=new_stage,
                reason=reason
            )


class CustomerLifecycleHistory(TimestampedModel):
    """
    Track customer lifecycle stage changes over time.
    """
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='lifecycle_history')
    from_stage = models.CharField(max_length=20, choices=CustomerLifecycleStage.STAGE_CHOICES)
    to_stage = models.CharField(max_length=20, choices=CustomerLifecycleStage.STAGE_CHOICES)
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'customer_lifecycle_history'
        verbose_name = 'Customer Lifecycle History'
        verbose_name_plural = 'Customer Lifecycle History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['to_stage', 'created_at']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()}: {self.from_stage} → {self.to_stage}"


class CustomerCommunicationHistory(TimestampedModel):
    """
    Track all customer communications (email, SMS, calls).
    """
    COMMUNICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone_call', 'Phone Call'),
        ('chat', 'Live Chat'),
        ('push_notification', 'Push Notification'),
        ('in_app_message', 'In-App Message'),
        ('postal_mail', 'Postal Mail'),
        ('social_media', 'Social Media'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('replied', 'Replied'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='communication_history')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    
    # Communication details
    subject = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    
    # Metadata
    campaign_id = models.CharField(max_length=100, blank=True)
    template_id = models.CharField(max_length=100, blank=True)
    sender = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'customer_communication_history'
        verbose_name = 'Customer Communication History'
        verbose_name_plural = 'Customer Communication History'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['customer', 'sent_at']),
            models.Index(fields=['communication_type', 'sent_at']),
            models.Index(fields=['status']),
            models.Index(fields=['campaign_id']),
        ]

    def __str__(self):
        return f"{self.get_communication_type_display()} to {self.customer.get_full_name()}"


class CustomerSupportTicket(TimestampedModel):
    """
    Customer support ticket integration with case management.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending_customer', 'Pending Customer Response'),
        ('pending_internal', 'Pending Internal Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    
    CATEGORY_CHOICES = [
        ('general_inquiry', 'General Inquiry'),
        ('order_issue', 'Order Issue'),
        ('product_issue', 'Product Issue'),
        ('payment_issue', 'Payment Issue'),
        ('shipping_issue', 'Shipping Issue'),
        ('return_refund', 'Return/Refund'),
        ('account_issue', 'Account Issue'),
        ('technical_issue', 'Technical Issue'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
    ]
    
    # Ticket identification
    ticket_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket details
    subject = models.CharField(max_length=500)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Assignment
    assigned_to = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    department = models.CharField(max_length=50, blank=True)
    
    # Related objects
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    related_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timing
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_due_date = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    
    # Customer satisfaction
    satisfaction_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    satisfaction_feedback = models.TextField(blank=True)
    
    # Metadata
    source = models.CharField(max_length=50, default='web', help_text="Source of the ticket (web, email, phone, etc.)")
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'customer_support_tickets'
        verbose_name = 'Customer Support Ticket'
        verbose_name_plural = 'Customer Support Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['sla_due_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate unique ticket number
            import random
            import string
            self.ticket_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)


class CustomerSupportTicketResponse(TimestampedModel):
    """
    Responses/messages within support tickets.
    """
    ticket = models.ForeignKey(CustomerSupportTicket, on_delete=models.CASCADE, related_name='responses')
    
    # Response details
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to customer")
    
    # Author
    admin_user = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    # Tracking
    is_read_by_customer = models.BooleanField(default=False)
    read_by_customer_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'customer_support_ticket_responses'
        verbose_name = 'Support Ticket Response'
        verbose_name_plural = 'Support Ticket Responses'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['is_internal']),
        ]

    def __str__(self):
        author = self.admin_user.username if self.admin_user else self.customer.get_full_name()
        return f"Response by {author} on {self.ticket.ticket_number}"


class CustomerAnalytics(TimestampedModel):
    """
    Customer analytics with lifetime value, purchase patterns, and behavior analysis.
    """
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='admin_analytics')
    
    # Lifetime Value Metrics
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    predicted_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Purchase Behavior
    total_orders = models.IntegerField(default=0)
    total_items_purchased = models.IntegerField(default=0)
    favorite_category = models.CharField(max_length=100, blank=True)
    favorite_brand = models.CharField(max_length=100, blank=True)
    
    # Frequency Metrics
    purchase_frequency = models.FloatField(default=0.0, help_text="Orders per month")
    days_since_last_order = models.IntegerField(default=0)
    average_days_between_orders = models.FloatField(default=0.0)
    
    # Engagement Metrics
    website_visits = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)
    time_on_site = models.IntegerField(default=0, help_text="Total time in minutes")
    email_open_rate = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    email_click_rate = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Behavioral Scores
    engagement_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    loyalty_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    satisfaction_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    # Risk Assessment
    churn_risk_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    fraud_risk_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    credit_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(300), MaxValueValidator(850)])
    
    # Preferences
    preferred_communication_channel = models.CharField(max_length=50, blank=True)
    preferred_shopping_time = models.CharField(max_length=50, blank=True)
    price_sensitivity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    
    # Last calculation
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_analytics'
        verbose_name = 'Customer Analytics'
        verbose_name_plural = 'Customer Analytics'
        indexes = [
            models.Index(fields=['lifetime_value']),
            models.Index(fields=['churn_risk_score']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['loyalty_score']),
            models.Index(fields=['last_calculated']),
        ]

    def __str__(self):
        return f"Analytics for {self.customer.get_full_name()}"

    def calculate_metrics(self):
        """Calculate and update customer analytics metrics."""
        # This would contain complex analytics calculations
        # For now, we'll implement basic structure
        orders = Order.objects.filter(customer=self.customer.user)
        
        self.total_orders = orders.count()
        if orders.exists():
            self.lifetime_value = sum(order.total_amount for order in orders)
            self.average_order_value = self.lifetime_value / self.total_orders if self.total_orders > 0 else 0
        
        self.save()


class CustomerPaymentMethod(TimestampedModel):
    """
    Secure customer payment method management.
    """
    PAYMENT_TYPE_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_account', 'Bank Account'),
        ('digital_wallet', 'Digital Wallet'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Encrypted/Tokenized payment details
    token = models.CharField(max_length=255, help_text="Tokenized payment method identifier")
    last_four_digits = models.CharField(max_length=4, blank=True)
    expiry_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    expiry_year = models.IntegerField(null=True, blank=True)
    
    # Card/Account details
    brand = models.CharField(max_length=50, blank=True, help_text="Visa, MasterCard, etc.")
    bank_name = models.CharField(max_length=100, blank=True)
    account_holder_name = models.CharField(max_length=200, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Security
    added_ip = models.GenericIPAddressField(null=True, blank=True)
    verification_attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'customer_payment_methods'
        verbose_name = 'Customer Payment Method'
        verbose_name_plural = 'Customer Payment Methods'
        indexes = [
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['token']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.get_payment_type_display()} ending in {self.last_four_digits}"


class CustomerLoyaltyProgram(TimestampedModel):
    """
    Customer loyalty program management with points, tiers, and rewards.
    """
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]
    
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='loyalty_program')
    
    # Points and Tier
    current_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    current_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    
    # Tier progression
    points_to_next_tier = models.IntegerField(default=0)
    tier_expiry_date = models.DateField(null=True, blank=True)
    
    # Program status
    is_active = models.BooleanField(default=True)
    enrolled_date = models.DateField(auto_now_add=True)
    
    # Rewards tracking
    total_rewards_earned = models.IntegerField(default=0)
    total_rewards_redeemed = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'customer_loyalty_programs'
        verbose_name = 'Customer Loyalty Program'
        verbose_name_plural = 'Customer Loyalty Programs'
        indexes = [
            models.Index(fields=['current_tier']),
            models.Index(fields=['current_points']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_current_tier_display()} ({self.current_points} points)"

    def add_points(self, points, reason=""):
        """Add loyalty points."""
        self.current_points += points
        self.lifetime_points += points
        self.save()
        
        # Log the transaction
        CustomerLoyaltyTransaction.objects.create(
            loyalty_program=self,
            transaction_type='earned',
            points=points,
            reason=reason
        )

    def redeem_points(self, points, reason=""):
        """Redeem loyalty points."""
        if self.current_points >= points:
            self.current_points -= points
            self.total_rewards_redeemed += 1
            self.save()
            
            # Log the transaction
            CustomerLoyaltyTransaction.objects.create(
                loyalty_program=self,
                transaction_type='redeemed',
                points=-points,
                reason=reason
            )
            return True
        return False


class CustomerLoyaltyTransaction(TimestampedModel):
    """
    Track loyalty points transactions.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('adjusted', 'Points Adjusted'),
    ]
    
    loyalty_program = models.ForeignKey(CustomerLoyaltyProgram, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()
    reason = models.CharField(max_length=500, blank=True)
    
    # Related objects
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    processed_by = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'customer_loyalty_transactions'
        verbose_name = 'Customer Loyalty Transaction'
        verbose_name_plural = 'Customer Loyalty Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loyalty_program', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.points} points"


class CustomerRiskAssessment(TimestampedModel):
    """
    Customer risk assessment with fraud detection and credit scoring.
    """
    RISK_LEVEL_CHOICES = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='risk_assessment')
    
    # Overall risk scores
    overall_risk_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    fraud_risk_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    credit_risk_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    # Risk levels
    overall_risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    fraud_risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    credit_risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    
    # Risk factors
    risk_factors = models.JSONField(default=list, blank=True)
    
    # Fraud indicators
    suspicious_activities = models.JSONField(default=list, blank=True)
    failed_payment_attempts = models.IntegerField(default=0)
    chargebacks = models.IntegerField(default=0)
    
    # Account security
    account_takeover_risk = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    identity_verification_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('manual_review', 'Manual Review Required'),
    ], default='pending')
    
    # Assessment metadata
    last_assessed = models.DateTimeField(auto_now=True)
    assessed_by = models.CharField(max_length=50, default='system')
    
    # Actions taken
    restrictions_applied = models.JSONField(default=list, blank=True)
    manual_review_required = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'customer_risk_assessments'
        verbose_name = 'Customer Risk Assessment'
        verbose_name_plural = 'Customer Risk Assessments'
        indexes = [
            models.Index(fields=['overall_risk_level']),
            models.Index(fields=['fraud_risk_score']),
            models.Index(fields=['manual_review_required']),
            models.Index(fields=['last_assessed']),
        ]

    def __str__(self):
        return f"Risk Assessment for {self.customer.get_full_name()} - {self.overall_risk_level}"


class CustomerGDPRCompliance(TimestampedModel):
    """
    GDPR compliance tools with data export and deletion capabilities.
    """
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='gdpr_compliance')
    
    # Consent management
    marketing_consent = models.BooleanField(default=False)
    marketing_consent_date = models.DateTimeField(null=True, blank=True)
    analytics_consent = models.BooleanField(default=False)
    analytics_consent_date = models.DateTimeField(null=True, blank=True)
    
    # Data processing
    data_processing_consent = models.BooleanField(default=True)
    data_processing_consent_date = models.DateTimeField(auto_now_add=True)
    
    # Right to be forgotten
    deletion_requested = models.BooleanField(default=False)
    deletion_request_date = models.DateTimeField(null=True, blank=True)
    deletion_processed = models.BooleanField(default=False)
    deletion_processed_date = models.DateTimeField(null=True, blank=True)
    
    # Data export requests
    data_export_requested = models.BooleanField(default=False)
    data_export_request_date = models.DateTimeField(null=True, blank=True)
    data_export_completed = models.BooleanField(default=False)
    data_export_completed_date = models.DateTimeField(null=True, blank=True)
    data_export_file_path = models.CharField(max_length=500, blank=True)
    
    # Compliance tracking
    last_consent_update = models.DateTimeField(auto_now=True)
    consent_version = models.CharField(max_length=20, default='1.0')
    
    class Meta:
        db_table = 'customer_gdpr_compliance'
        verbose_name = 'Customer GDPR Compliance'
        verbose_name_plural = 'Customer GDPR Compliance'
        indexes = [
            models.Index(fields=['deletion_requested']),
            models.Index(fields=['data_export_requested']),
            models.Index(fields=['marketing_consent']),
        ]

    def __str__(self):
        return f"GDPR Compliance for {self.customer.get_full_name()}"

    def request_data_export(self):
        """Request customer data export."""
        self.data_export_requested = True
        self.data_export_request_date = timezone.now()
        self.save()

    def request_deletion(self):
        """Request customer data deletion."""
        self.deletion_requested = True
        self.deletion_request_date = timezone.now()
        self.save()


class CustomerJourneyMapping(TimestampedModel):
    """
    Customer journey mapping and analytics.
    """
    TOUCHPOINT_CHOICES = [
        ('website_visit', 'Website Visit'),
        ('product_view', 'Product View'),
        ('category_browse', 'Category Browse'),
        ('search', 'Search'),
        ('cart_add', 'Add to Cart'),
        ('cart_abandon', 'Cart Abandonment'),
        ('checkout_start', 'Checkout Started'),
        ('order_placed', 'Order Placed'),
        ('email_open', 'Email Opened'),
        ('email_click', 'Email Clicked'),
        ('support_contact', 'Support Contact'),
        ('review_left', 'Review Left'),
        ('social_media', 'Social Media Interaction'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='journey_touchpoints')
    touchpoint = models.CharField(max_length=30, choices=TOUCHPOINT_CHOICES)
    
    # Touchpoint details
    page_url = models.URLField(blank=True)
    referrer = models.URLField(blank=True)
    campaign_source = models.CharField(max_length=100, blank=True)
    campaign_medium = models.CharField(max_length=100, blank=True)
    campaign_name = models.CharField(max_length=100, blank=True)
    
    # Session information
    session_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    
    # Engagement metrics
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    interaction_count = models.IntegerField(default=1)
    
    # Conversion tracking
    led_to_conversion = models.BooleanField(default=False)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'customer_journey_mapping'
        verbose_name = 'Customer Journey Touchpoint'
        verbose_name_plural = 'Customer Journey Touchpoints'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['touchpoint', 'created_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['led_to_conversion']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_touchpoint_display()}"


class CustomerSatisfactionSurvey(TimestampedModel):
    """
    Customer satisfaction tracking with NPS and surveys.
    """
    SURVEY_TYPE_CHOICES = [
        ('nps', 'Net Promoter Score'),
        ('csat', 'Customer Satisfaction'),
        ('ces', 'Customer Effort Score'),
        ('custom', 'Custom Survey'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='satisfaction_surveys')
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES)
    
    # Survey details
    survey_name = models.CharField(max_length=200)
    questions = models.JSONField(default=list)
    responses = models.JSONField(default=dict)
    
    # Scores
    nps_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    csat_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    ces_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(7)])
    
    # Survey metadata
    sent_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Related objects
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    related_ticket = models.ForeignKey(CustomerSupportTicket, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'customer_satisfaction_surveys'
        verbose_name = 'Customer Satisfaction Survey'
        verbose_name_plural = 'Customer Satisfaction Surveys'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['customer', 'survey_type']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['nps_score']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.survey_name} - {self.customer.get_full_name()}"


class CustomerReferralProgram(TimestampedModel):
    """
    Customer referral program management.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rewarded', 'Rewarded'),
        ('expired', 'Expired'),
    ]
    
    referrer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='referrals_made')
    referred_customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='referrals_received')
    
    # Referral details
    referral_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Rewards
    referrer_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    referred_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tracking
    referred_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)
    
    # Related order (that completed the referral)
    completing_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'customer_referral_programs'
        verbose_name = 'Customer Referral'
        verbose_name_plural = 'Customer Referrals'
        ordering = ['-referred_at']
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['referrer', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Referral: {self.referrer.get_full_name()} → {self.referred_customer.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            # Generate unique referral code
            import random
            import string
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)


class CustomerSocialMediaIntegration(TimestampedModel):
    """
    Customer social media integration and monitoring.
    """
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('pinterest', 'Pinterest'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='social_media_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # Account details
    username = models.CharField(max_length=100)
    profile_url = models.URLField()
    profile_id = models.CharField(max_length=100, blank=True)
    
    # Engagement metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    
    # Sentiment analysis
    sentiment_score = models.FloatField(default=0.0, validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)])
    brand_mentions = models.IntegerField(default=0)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_social_media_integrations'
        verbose_name = 'Customer Social Media Account'
        verbose_name_plural = 'Customer Social Media Accounts'
        unique_together = ('customer', 'platform', 'username')
        indexes = [
            models.Index(fields=['platform']),
            models.Index(fields=['customer', 'platform']),
            models.Index(fields=['sentiment_score']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_platform_display()}"


class CustomerWinBackCampaign(TimestampedModel):
    """
    Customer win-back campaigns and automation.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TRIGGER_TYPE_CHOICES = [
        ('churn_risk', 'Churn Risk'),
        ('inactive_period', 'Inactive Period'),
        ('abandoned_cart', 'Abandoned Cart'),
        ('low_engagement', 'Low Engagement'),
        ('manual', 'Manual'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='winback_campaigns')
    
    # Campaign details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Timing
    scheduled_date = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Campaign configuration
    discount_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_shipping = models.BooleanField(default=False)
    
    # Tracking
    emails_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    orders_generated = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Success metrics
    is_successful = models.BooleanField(default=False)
    success_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'customer_winback_campaigns'
        verbose_name = 'Customer Win-Back Campaign'
        verbose_name_plural = 'Customer Win-Back Campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['trigger_type']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"Win-back: {self.name} for {self.customer.get_full_name()}"


class CustomerAccountHealthScore(TimestampedModel):
    """
    Customer account health scoring and monitoring.
    """
    HEALTH_LEVEL_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
    ]
    
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='health_score')
    
    # Overall health score (0-100)
    overall_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    health_level = models.CharField(max_length=20, choices=HEALTH_LEVEL_CHOICES, default='fair')
    
    # Component scores
    engagement_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    satisfaction_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    loyalty_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    payment_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    support_score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    # Risk indicators
    churn_risk = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    fraud_risk = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    payment_risk = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Trends
    score_trend = models.CharField(max_length=20, choices=[
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ], default='stable')
    
    # Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    
    # Calculation metadata
    last_calculated = models.DateTimeField(auto_now=True)
    calculation_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        db_table = 'customer_account_health_scores'
        verbose_name = 'Customer Account Health Score'
        verbose_name_plural = 'Customer Account Health Scores'
        indexes = [
            models.Index(fields=['overall_score']),
            models.Index(fields=['health_level']),
            models.Index(fields=['churn_risk']),
            models.Index(fields=['last_calculated']),
        ]

    def __str__(self):
        return f"Health Score for {self.customer.get_full_name()}: {self.overall_score:.1f}"

    def calculate_health_score(self):
        """Calculate comprehensive health score."""
        # This would contain complex health scoring logic
        # For now, we'll implement basic structure
        
        # Weight different components
        weights = {
            'engagement': 0.25,
            'satisfaction': 0.20,
            'loyalty': 0.20,
            'payment': 0.20,
            'support': 0.15,
        }
        
        self.overall_score = (
            self.engagement_score * weights['engagement'] +
            self.satisfaction_score * weights['satisfaction'] +
            self.loyalty_score * weights['loyalty'] +
            self.payment_score * weights['payment'] +
            self.support_score * weights['support']
        )
        
        # Determine health level
        if self.overall_score >= 80:
            self.health_level = 'excellent'
        elif self.overall_score >= 60:
            self.health_level = 'good'
        elif self.overall_score >= 40:
            self.health_level = 'fair'
        elif self.overall_score >= 20:
            self.health_level = 'poor'
        else:
            self.health_level = 'critical'
        
        self.save()


class CustomerPreferenceCenter(TimestampedModel):
    """
    Customer preference center for communication and privacy.
    """
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='preference_center')
    
    # Communication preferences
    email_marketing = models.BooleanField(default=True)
    email_transactional = models.BooleanField(default=True)
    email_newsletters = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=True)
    email_product_updates = models.BooleanField(default=True)
    
    sms_marketing = models.BooleanField(default=False)
    sms_transactional = models.BooleanField(default=True)
    sms_promotions = models.BooleanField(default=False)
    sms_order_updates = models.BooleanField(default=True)
    
    push_notifications = models.BooleanField(default=True)
    push_promotions = models.BooleanField(default=True)
    push_order_updates = models.BooleanField(default=True)
    push_abandoned_cart = models.BooleanField(default=True)
    
    # Frequency preferences
    email_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('never', 'Never'),
    ], default='weekly')
    
    # Content preferences
    preferred_categories = models.JSONField(default=list, blank=True)
    preferred_brands = models.JSONField(default=list, blank=True)
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Privacy preferences
    data_sharing_analytics = models.BooleanField(default=True)
    data_sharing_marketing = models.BooleanField(default=True)
    data_sharing_third_party = models.BooleanField(default=False)
    
    # Personalization
    personalized_recommendations = models.BooleanField(default=True)
    personalized_pricing = models.BooleanField(default=True)
    personalized_content = models.BooleanField(default=True)
    
    # Language and locale
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_currency = models.CharField(max_length=3, default='USD')
    preferred_timezone = models.CharField(max_length=50, default='UTC')
    
    # Last updated
    last_updated = models.DateTimeField(auto_now=True)
    updated_by_customer = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'customer_preference_centers'
        verbose_name = 'Customer Preference Center'
        verbose_name_plural = 'Customer Preference Centers'
        indexes = [
            models.Index(fields=['email_marketing']),
            models.Index(fields=['sms_marketing']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"Preferences for {self.customer.get_full_name()}"


class CustomerComplaintManagement(TimestampedModel):
    """
    Customer complaint management and resolution tracking.
    """
    COMPLAINT_TYPE_CHOICES = [
        ('product_quality', 'Product Quality'),
        ('service_quality', 'Service Quality'),
        ('delivery_issue', 'Delivery Issue'),
        ('billing_issue', 'Billing Issue'),
        ('website_issue', 'Website Issue'),
        ('staff_behavior', 'Staff Behavior'),
        ('policy_issue', 'Policy Issue'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='complaints')
    
    # Complaint details
    complaint_number = models.CharField(max_length=50, unique=True)
    complaint_type = models.CharField(max_length=30, choices=COMPLAINT_TYPE_CHOICES)
    subject = models.CharField(max_length=500)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    
    # Related objects
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    related_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assignment and handling
    assigned_to = models.ForeignKey('AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=50, blank=True)
    
    # Resolution
    resolution_description = models.TextField(blank=True)
    compensation_offered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compensation_type = models.CharField(max_length=50, blank=True)
    
    # Timing
    received_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_due_date = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    
    # Customer satisfaction with resolution
    resolution_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    resolution_feedback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'customer_complaint_management'
        verbose_name = 'Customer Complaint'
        verbose_name_plural = 'Customer Complaints'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['complaint_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['sla_due_date']),
        ]

    def __str__(self):
        return f"Complaint #{self.complaint_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # Generate unique complaint number
            import random
            import string
            self.complaint_number = 'COMP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)


class CustomerServiceLevelAgreement(TimestampedModel):
    """
    Customer service level agreement (SLA) tracking.
    """
    SLA_TYPE_CHOICES = [
        ('support_response', 'Support Response Time'),
        ('issue_resolution', 'Issue Resolution Time'),
        ('order_processing', 'Order Processing Time'),
        ('delivery_time', 'Delivery Time'),
        ('refund_processing', 'Refund Processing Time'),
    ]
    
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='sla_tracking')
    sla_type = models.CharField(max_length=30, choices=SLA_TYPE_CHOICES)
    
    # SLA definition
    target_time_hours = models.IntegerField(help_text="Target time in hours")
    warning_threshold_hours = models.IntegerField(help_text="Warning threshold in hours")
    
    # Tracking
    start_time = models.DateTimeField()
    target_time = models.DateTimeField()
    warning_time = models.DateTimeField()
    completion_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_met = models.BooleanField(null=True, blank=True)
    is_breached = models.BooleanField(default=False)
    breach_reason = models.TextField(blank=True)
    
    # Related objects
    related_ticket = models.ForeignKey(CustomerSupportTicket, on_delete=models.CASCADE, null=True, blank=True)
    related_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    related_complaint = models.ForeignKey(CustomerComplaintManagement, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'customer_service_level_agreements'
        verbose_name = 'Customer SLA Tracking'
        verbose_name_plural = 'Customer SLA Tracking'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['customer', 'sla_type']),
            models.Index(fields=['is_breached']),
            models.Index(fields=['target_time']),
            models.Index(fields=['completion_time']),
        ]

    def __str__(self):
        return f"SLA: {self.get_sla_type_display()} for {self.customer.get_full_name()}"

    def check_sla_status(self):
        """Check and update SLA status."""
        now = timezone.now()
        
        if self.completion_time:
            # SLA is completed
            self.is_met = self.completion_time <= self.target_time
            if not self.is_met:
                self.is_breached = True
        elif now > self.target_time:
            # SLA is breached
            self.is_breached = True
            self.is_met = False
        
        self.save()


class CustomerChurnPrediction(TimestampedModel):
    """
    Customer churn prediction with ML algorithms.
    """
    PREDICTION_MODEL_CHOICES = [
        ('logistic_regression', 'Logistic Regression'),
        ('random_forest', 'Random Forest'),
        ('gradient_boosting', 'Gradient Boosting'),
        ('neural_network', 'Neural Network'),
        ('ensemble', 'Ensemble Model'),
    ]
    
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='churn_prediction')
    
    # Prediction results
    churn_probability = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    churn_risk_level = models.CharField(max_length=20, choices=[
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ])
    
    # Model information
    model_used = models.CharField(max_length=30, choices=PREDICTION_MODEL_CHOICES)
    model_version = models.CharField(max_length=20)
    prediction_confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Feature importance
    top_churn_factors = models.JSONField(default=list, blank=True)
    feature_scores = models.JSONField(default=dict, blank=True)
    
    # Timing predictions
    predicted_churn_date = models.DateField(null=True, blank=True)
    days_to_churn = models.IntegerField(null=True, blank=True)
    
    # Intervention recommendations
    recommended_actions = models.JSONField(default=list, blank=True)
    intervention_priority = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Tracking
    prediction_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Validation
    actual_churned = models.BooleanField(null=True, blank=True)
    actual_churn_date = models.DateField(null=True, blank=True)
    prediction_accuracy = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'customer_churn_predictions'
        verbose_name = 'Customer Churn Prediction'
        verbose_name_plural = 'Customer Churn Predictions'
        indexes = [
            models.Index(fields=['churn_probability']),
            models.Index(fields=['churn_risk_level']),
            models.Index(fields=['predicted_churn_date']),
            models.Index(fields=['intervention_priority']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"Churn Prediction for {self.customer.get_full_name()}: {self.churn_probability:.2%}"