from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.core.validators import URLValidator
import json
import uuid


class IntegrationCategory(models.Model):
    """Categories for different types of integrations"""
    CATEGORY_CHOICES = [
        ('payment', 'Payment Gateways'),
        ('shipping', 'Shipping Carriers'),
        ('crm', 'CRM Systems'),
        ('accounting', 'Accounting Systems'),
        ('marketing', 'Marketing Platforms'),
        ('social', 'Social Media'),
        ('analytics', 'Analytics Platforms'),
        ('inventory', 'Inventory Management'),
        ('erp', 'ERP Systems'),
        ('warehouse', 'Warehouse Management'),
        ('support', 'Customer Service'),
        ('bi', 'Business Intelligence'),
        ('ecommerce', 'E-commerce Platforms'),
        ('marketplace', 'Marketplaces'),
        ('communication', 'Communication'),
        ('document', 'Document Management'),
        ('project', 'Project Management'),
        ('storage', 'Storage Services'),
        ('security', 'Security Services'),
        ('monitoring', 'Monitoring Services'),
        ('compliance', 'Compliance Services'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class IntegrationProvider(models.Model):
    """Third-party service providers"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deprecated', 'Deprecated'),
        ('beta', 'Beta'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(IntegrationCategory, on_delete=models.CASCADE)
    description = models.TextField()
    website_url = models.URLField(validators=[URLValidator()])
    documentation_url = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    api_version = models.CharField(max_length=20, blank=True)
    supported_features = models.JSONField(default=list)
    pricing_model = models.CharField(max_length=100, blank=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_providers'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Integration(models.Model):
    """Active integrations configured by users"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('testing', 'Testing'),
        ('pending', 'Pending Setup'),
    ]
    
    ENVIRONMENT_CHOICES = [
        ('production', 'Production'),
        ('sandbox', 'Sandbox'),
        ('development', 'Development'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='production')
    configuration = models.JSONField(default=dict)  # Encrypted sensitive data
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.IntegerField(default=3600)  # seconds
    auto_sync = models.BooleanField(default=True)
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integrations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.provider.name})"


class IntegrationLog(models.Model):
    """Logs for integration activities"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    ACTION_TYPES = [
        ('sync', 'Data Sync'),
        ('webhook', 'Webhook'),
        ('api_call', 'API Call'),
        ('auth', 'Authentication'),
        ('config', 'Configuration'),
        ('test', 'Test'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict)
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True)  # milliseconds
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'integration_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['integration', '-created_at']),
            models.Index(fields=['level', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.integration.name} - {self.level} - {self.message[:50]}"


class IntegrationMapping(models.Model):
    """Field mappings between systems"""
    MAPPING_TYPES = [
        ('field', 'Field Mapping'),
        ('value', 'Value Mapping'),
        ('transform', 'Data Transform'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    mapping_type = models.CharField(max_length=20, choices=MAPPING_TYPES)
    source_field = models.CharField(max_length=100)
    target_field = models.CharField(max_length=100)
    transformation_rule = models.JSONField(default=dict)
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)
    validation_rule = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_mappings'
        unique_together = ['integration', 'source_field', 'target_field']
    
    def __str__(self):
        return f"{self.integration.name} - {self.source_field} -> {self.target_field}"


class IntegrationWebhook(models.Model):
    """Webhook configurations for integrations"""
    EVENT_TYPES = [
        ('order.created', 'Order Created'),
        ('order.updated', 'Order Updated'),
        ('order.cancelled', 'Order Cancelled'),
        ('payment.completed', 'Payment Completed'),
        ('payment.failed', 'Payment Failed'),
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('inventory.updated', 'Inventory Updated'),
        ('customer.created', 'Customer Created'),
        ('customer.updated', 'Customer Updated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    webhook_url = models.URLField()
    secret_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)  # seconds
    headers = models.JSONField(default=dict)
    payload_template = models.JSONField(default=dict)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_webhooks'
        unique_together = ['integration', 'event_type']
    
    def __str__(self):
        return f"{self.integration.name} - {self.event_type}"


class IntegrationSync(models.Model):
    """Sync jobs and their status"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SYNC_TYPES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
        ('scheduled', 'Scheduled Sync'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    sync_data = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'integration_syncs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.integration.name} - {self.sync_type} - {self.status}"


class IntegrationTemplate(models.Model):
    """Pre-configured integration templates"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE)
    description = models.TextField()
    configuration_template = models.JSONField(default=dict)
    mapping_template = models.JSONField(default=dict)
    webhook_template = models.JSONField(default=dict)
    setup_instructions = models.TextField()
    is_official = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_templates'
        ordering = ['-rating', '-usage_count']
    
    def __str__(self):
        return f"{self.name} - {self.provider.name}"