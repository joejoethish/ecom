"""
Enterprise Email and Communication Management models.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import BaseModel
import json

User = get_user_model()


class EmailTemplate(BaseModel):
    """
    Email template model for reusable email designs.
    """
    TEMPLATE_TYPES = [
        ('marketing', 'Marketing Email'),
        ('transactional', 'Transactional Email'),
        ('newsletter', 'Newsletter'),
        ('notification', 'Notification'),
        ('welcome', 'Welcome Email'),
        ('order_confirmation', 'Order Confirmation'),
        ('password_reset', 'Password Reset'),
        ('invoice', 'Invoice'),
        ('custom', 'Custom Template'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=500)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Template variables
    variables = models.JSONField(
        default=list,
        blank=True,
        help_text="List of template variables like {{name}}, {{email}}, etc."
    )
    
    # Design settings
    design_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Design configuration for drag-and-drop editor"
    )
    
    # Status and usage
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Preview settings
    preview_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sample data for template preview"
    )

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
            models.Index(fields=['is_system_template']),
        ]

    def __str__(self):
        return f"{self.name} ({self.template_type})"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class EmailCampaign(BaseModel):
    """
    Email campaign model for managing email marketing campaigns.
    """
    CAMPAIGN_TYPES = [
        ('one_time', 'One-time Campaign'),
        ('recurring', 'Recurring Campaign'),
        ('automated', 'Automated Campaign'),
        ('drip', 'Drip Campaign'),
        ('a_b_test', 'A/B Test Campaign'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Email content
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=500)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Sender information
    from_name = models.CharField(max_length=200)
    from_email = models.EmailField()
    reply_to = models.EmailField(blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Targeting and segmentation
    target_segments = models.JSONField(
        default=list,
        blank=True,
        help_text="List of customer segments to target"
    )
    recipient_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filters for selecting recipients"
    )
    
    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="A/B test configuration"
    )
    
    # Analytics
    total_recipients = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    bounced_count = models.PositiveIntegerField(default=0)
    unsubscribed_count = models.PositiveIntegerField(default=0)
    
    # Settings
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign_type', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.campaign_type})"

    @property
    def open_rate(self):
        """Calculate open rate percentage."""
        if self.delivered_count == 0:
            return 0
        return round((self.opened_count / self.delivered_count) * 100, 2)

    @property
    def click_rate(self):
        """Calculate click rate percentage."""
        if self.delivered_count == 0:
            return 0
        return round((self.clicked_count / self.delivered_count) * 100, 2)

    @property
    def bounce_rate(self):
        """Calculate bounce rate percentage."""
        if self.total_recipients == 0:
            return 0
        return round((self.bounced_count / self.total_recipients) * 100, 2)


class EmailRecipient(BaseModel):
    """
    Email recipient model for tracking individual email sends.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('unsubscribed', 'Unsubscribed'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer reference
    customer_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    
    # Personalization data
    personalization_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data for personalizing email content"
    )
    
    # Error tracking
    error_message = models.TextField(blank=True)
    bounce_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['campaign', 'email']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['customer_id']),
        ]

    def __str__(self):
        return f"{self.email} - {self.campaign.name}"


class EmailAutomation(BaseModel):
    """
    Email automation model for triggered and drip campaigns.
    """
    TRIGGER_TYPES = [
        ('user_signup', 'User Signup'),
        ('order_placed', 'Order Placed'),
        ('cart_abandoned', 'Cart Abandoned'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('inactivity', 'User Inactivity'),
        ('custom_event', 'Custom Event'),
        ('date_based', 'Date Based'),
        ('behavior_based', 'Behavior Based'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Trigger configuration
    trigger_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for automation trigger"
    )
    
    # Email sequence
    email_sequence = models.JSONField(
        default=list,
        blank=True,
        help_text="List of emails in the automation sequence"
    )
    
    # Targeting
    target_segments = models.JSONField(
        default=list,
        blank=True,
        help_text="Customer segments for this automation"
    )
    
    # Analytics
    triggered_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trigger_type', 'is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class EmailAutomationInstance(BaseModel):
    """
    Individual instances of email automation for specific users.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    automation = models.ForeignKey(EmailAutomation, on_delete=models.CASCADE, related_name='instances')
    customer_id = models.PositiveIntegerField()
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Progress tracking
    current_step = models.PositiveIntegerField(default=0)
    next_send_at = models.DateTimeField(null=True, blank=True)
    
    # Personalization
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Context data for personalization"
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['automation', 'customer_id']
        indexes = [
            models.Index(fields=['automation', 'status']),
            models.Index(fields=['next_send_at']),
        ]

    def __str__(self):
        return f"{self.automation.name} - {self.email}"


class EmailList(BaseModel):
    """
    Email list model for managing subscriber lists.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # List settings
    double_opt_in = models.BooleanField(default=True)
    send_welcome_email = models.BooleanField(default=True)
    welcome_email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='welcome_lists'
    )
    
    # Analytics
    subscriber_count = models.PositiveIntegerField(default=0)
    active_subscriber_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.name


class EmailSubscriber(BaseModel):
    """
    Email subscriber model for managing list subscriptions.
    """
    STATUS_CHOICES = [
        ('subscribed', 'Subscribed'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('pending', 'Pending Confirmation'),
    ]

    email_list = models.ForeignKey(EmailList, on_delete=models.CASCADE, related_name='subscribers')
    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer reference
    customer_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Subscription tracking
    subscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom subscriber data"
    )
    
    # Source tracking
    source = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['email_list', 'email']
        indexes = [
            models.Index(fields=['email_list', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['customer_id']),
        ]

    def __str__(self):
        return f"{self.email} - {self.email_list.name}"


class EmailAnalytics(BaseModel):
    """
    Email analytics model for tracking email performance metrics.
    """
    METRIC_TYPES = [
        ('sent', 'Emails Sent'),
        ('delivered', 'Emails Delivered'),
        ('opened', 'Emails Opened'),
        ('clicked', 'Links Clicked'),
        ('bounced', 'Emails Bounced'),
        ('unsubscribed', 'Unsubscriptions'),
        ('complained', 'Spam Complaints'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='analytics', null=True, blank=True)
    automation = models.ForeignKey(EmailAutomation, on_delete=models.CASCADE, related_name='analytics', null=True, blank=True)
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_value = models.PositiveIntegerField()
    date = models.DateField()
    
    # Segmentation
    segment = models.CharField(max_length=100, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['campaign', 'date']),
            models.Index(fields=['automation', 'date']),
            models.Index(fields=['metric_type', 'date']),
        ]

    def __str__(self):
        campaign_name = self.campaign.name if self.campaign else self.automation.name
        return f"{campaign_name} - {self.metric_type} ({self.date})"


class EmailDeliverabilitySettings(BaseModel):
    """
    Email deliverability settings and configuration.
    """
    PROVIDER_CHOICES = [
        ('smtp', 'SMTP Server'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('ses', 'Amazon SES'),
        ('mailchimp', 'Mailchimp'),
        ('postmark', 'Postmark'),
        ('sparkpost', 'SparkPost'),
    ]

    name = models.CharField(max_length=200)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Provider configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Provider-specific configuration"
    )
    
    # Sending limits
    daily_limit = models.PositiveIntegerField(null=True, blank=True)
    hourly_limit = models.PositiveIntegerField(null=True, blank=True)
    
    # Reputation tracking
    reputation_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Analytics
    emails_sent_today = models.PositiveIntegerField(default=0)
    emails_sent_this_hour = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider})"


class EmailSuppressionList(BaseModel):
    """
    Email suppression list for managing bounces, complaints, and unsubscribes.
    """
    SUPPRESSION_TYPES = [
        ('bounce', 'Hard Bounce'),
        ('complaint', 'Spam Complaint'),
        ('unsubscribe', 'Unsubscribe'),
        ('manual', 'Manual Suppression'),
    ]

    email = models.EmailField(unique=True)
    suppression_type = models.CharField(max_length=20, choices=SUPPRESSION_TYPES)
    reason = models.TextField(blank=True)
    
    # Source tracking
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    automation = models.ForeignKey(EmailAutomation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    suppressed_at = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-suppressed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['suppression_type']),
        ]

    def __str__(self):
        return f"{self.email} ({self.suppression_type})"