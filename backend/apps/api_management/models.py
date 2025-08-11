from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid
import json


class APIVersion(models.Model):
    """API Version management"""
    version = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    is_deprecated = models.BooleanField(default=False)
    deprecation_date = models.DateTimeField(null=True, blank=True)
    sunset_date = models.DateTimeField(null=True, blank=True)
    changelog = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"API v{self.version}"


class APIKey(models.Model):
    """API Key management for authentication"""
    ENVIRONMENT_CHOICES = [
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    secret = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='development')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=1000)
    rate_limit_per_hour = models.IntegerField(default=10000)
    rate_limit_per_day = models.IntegerField(default=100000)
    
    # Permissions
    allowed_endpoints = models.JSONField(default=list, blank=True)
    allowed_methods = models.JSONField(default=list, blank=True)
    ip_whitelist = models.JSONField(default=list, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.environment})"


class APIEndpoint(models.Model):
    """API Endpoint registry"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
        ('HEAD', 'HEAD'),
    ]

    name = models.CharField(max_length=100)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    version = models.ForeignKey(APIVersion, on_delete=models.CASCADE, related_name='endpoints')
    description = models.TextField(blank=True)
    
    # Documentation
    request_schema = models.JSONField(default=dict, blank=True)
    response_schema = models.JSONField(default=dict, blank=True)
    examples = models.JSONField(default=dict, blank=True)
    
    # Configuration
    is_public = models.BooleanField(default=False)
    requires_auth = models.BooleanField(default=True)
    rate_limit_override = models.IntegerField(null=True, blank=True)
    cache_ttl = models.IntegerField(default=0)  # seconds
    
    # Monitoring
    is_monitored = models.BooleanField(default=True)
    alert_threshold = models.FloatField(default=5.0)  # seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['path', 'method', 'version']
        ordering = ['path', 'method']

    def __str__(self):
        return f"{self.method} {self.path} (v{self.version.version})"


class APIUsageLog(models.Model):
    """API Usage logging and analytics"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited'),
        ('unauthorized', 'Unauthorized'),
        ('forbidden', 'Forbidden'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE)
    
    # Request details
    request_id = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.TextField(blank=True)
    
    # Response details
    status_code = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time = models.FloatField()  # milliseconds
    response_size = models.IntegerField(default=0)  # bytes
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'endpoint']),
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.endpoint} - {self.status} ({self.timestamp})"


class APIRateLimit(models.Model):
    """Rate limiting tracking"""
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE)
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, null=True, blank=True)
    
    # Counters
    requests_per_minute = models.IntegerField(default=0)
    requests_per_hour = models.IntegerField(default=0)
    requests_per_day = models.IntegerField(default=0)
    
    # Timestamps
    minute_reset = models.DateTimeField()
    hour_reset = models.DateTimeField()
    day_reset = models.DateTimeField()
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['api_key', 'endpoint']

    def __str__(self):
        return f"{self.api_key} - {self.endpoint or 'Global'}"


class APIWebhook(models.Model):
    """Webhook management"""
    EVENT_CHOICES = [
        ('api.request', 'API Request'),
        ('api.error', 'API Error'),
        ('api.rate_limit', 'Rate Limit Exceeded'),
        ('api.key_created', 'API Key Created'),
        ('api.key_revoked', 'API Key Revoked'),
        ('system.maintenance', 'System Maintenance'),
    ]

    name = models.CharField(max_length=100)
    url = models.URLField()
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    
    # Security
    secret = models.CharField(max_length=128, blank=True)
    
    # Configuration
    timeout = models.IntegerField(default=30)  # seconds
    retry_count = models.IntegerField(default=3)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class APIWebhookDelivery(models.Model):
    """Webhook delivery tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    webhook = models.ForeignKey(APIWebhook, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    
    # Delivery details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Timing
    attempts = models.IntegerField(default=0)
    next_retry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} ({self.status})"


class APIMockService(models.Model):
    """Mock API services for development"""
    name = models.CharField(max_length=100)
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name='mocks')
    
    # Mock configuration
    response_code = models.IntegerField(default=200)
    response_body = models.TextField()
    response_headers = models.JSONField(default=dict, blank=True)
    delay = models.IntegerField(default=0)  # milliseconds
    
    # Conditions
    conditions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mock: {self.name}"


class APIDocumentation(models.Model):
    """API Documentation management"""
    endpoint = models.OneToOneField(APIEndpoint, on_delete=models.CASCADE, related_name='documentation')
    
    # Content
    summary = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=list, blank=True)
    request_examples = models.JSONField(default=list, blank=True)
    response_examples = models.JSONField(default=list, blank=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    deprecated = models.BooleanField(default=False)
    external_docs = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Docs: {self.endpoint}"


class APIPerformanceMetric(models.Model):
    """API Performance metrics"""
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name='metrics')
    
    # Time period
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True)  # 0-23 for hourly metrics
    
    # Metrics
    request_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    min_response_time = models.FloatField(default=0.0)
    max_response_time = models.FloatField(default=0.0)
    error_count = models.IntegerField(default=0)
    error_rate = models.FloatField(default=0.0)
    
    # Status code breakdown
    status_2xx = models.IntegerField(default=0)
    status_3xx = models.IntegerField(default=0)
    status_4xx = models.IntegerField(default=0)
    status_5xx = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['endpoint', 'date', 'hour']
        ordering = ['-date', '-hour']

    def __str__(self):
        period = f"{self.date}"
        if self.hour is not None:
            period += f" {self.hour}:00"
        return f"{self.endpoint} - {period}"