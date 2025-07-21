from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid

User = get_user_model()


class NotificationTemplate(models.Model):
    """
    Template for different types of notifications with customizable content
    """
    TEMPLATE_TYPES = [
        ('ORDER_CONFIRMATION', 'Order Confirmation'),
        ('ORDER_STATUS_UPDATE', 'Order Status Update'),
        ('PAYMENT_SUCCESS', 'Payment Success'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('SHIPPING_UPDATE', 'Shipping Update'),
        ('DELIVERY_CONFIRMATION', 'Delivery Confirmation'),
        ('RETURN_REQUEST', 'Return Request'),
        ('REFUND_PROCESSED', 'Refund Processed'),
        ('INVENTORY_LOW', 'Low Inventory Alert'),
        ('WELCOME', 'Welcome Message'),
        ('PROMOTIONAL', 'Promotional Offer'),
        ('ACCOUNT_UPDATE', 'Account Update'),
        ('SECURITY_ALERT', 'Security Alert'),
        ('WISHLIST_PRICE_DROP', 'Wishlist Price Drop'),
        ('CART_ABANDONMENT', 'Cart Abandonment'),
        ('REVIEW_REQUEST', 'Review Request'),
        ('SELLER_VERIFICATION', 'Seller Verification'),
        ('SELLER_PAYOUT', 'Seller Payout'),
        ('CUSTOM', 'Custom Template'),
    ]
    
    CHANNELS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App Notification'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    subject_template = models.CharField(max_length=200, help_text="Template for subject/title")
    body_template = models.TextField(help_text="Template for message body with placeholders")
    html_template = models.TextField(blank=True, help_text="HTML template for email")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['template_type', 'channel']
        db_table = 'notification_templates'
    
    def __str__(self):
        return f"{self.name} - {self.get_channel_display()}"


class NotificationPreference(models.Model):
    """
    User preferences for different types of notifications across channels
    """
    NOTIFICATION_TYPES = [
        ('ORDER_UPDATES', 'Order Updates'),
        ('PAYMENT_UPDATES', 'Payment Updates'),
        ('SHIPPING_UPDATES', 'Shipping Updates'),
        ('PROMOTIONAL', 'Promotional Offers'),
        ('SECURITY', 'Security Alerts'),
        ('ACCOUNT', 'Account Updates'),
        ('INVENTORY', 'Inventory Alerts'),
        ('REVIEWS', 'Review Requests'),
        ('SELLER_UPDATES', 'Seller Updates'),
        ('GENERAL', 'General Notifications'),
    ]
    
    CHANNELS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'notification_type', 'channel']
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.get_channel_display()}"


class Notification(models.Model):
    """
    Individual notification instances sent to users
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    CHANNELS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Generic foreign key to link to any model (order, payment, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    channel = models.CharField(max_length=20, choices=CHANNELS)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    
    # Recipient information
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=15, blank=True)
    
    # Tracking information
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text="Additional data for template rendering")
    external_id = models.CharField(max_length=100, blank=True, help_text="External service ID")
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.get_channel_display()})"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.status = 'READ'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_as_failed(self, error_message=''):
        """Mark notification as failed"""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])
    
    def can_retry(self):
        """Check if notification can be retried"""
        return self.retry_count < self.max_retries and self.status == 'FAILED'
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationLog(models.Model):
    """
    Detailed log of notification processing for analytics and debugging
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)  # 'created', 'sent', 'delivered', 'read', 'failed'
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.notification.id} - {self.action} at {self.timestamp}"


class NotificationBatch(models.Model):
    """
    Batch processing for bulk notifications (promotional campaigns, etc.)
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Target criteria
    target_users = models.ManyToManyField(User, blank=True)
    target_criteria = models.JSONField(default=dict, help_text="Criteria for selecting users")
    
    # Batch statistics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_batches'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class NotificationAnalytics(models.Model):
    """
    Analytics data for notification performance tracking
    """
    date = models.DateField()
    template_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=20)
    
    # Metrics
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    read_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Calculated rates
    delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    read_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    failure_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['date', 'template_type', 'channel']
        db_table = 'notification_analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.template_type} - {self.channel}"