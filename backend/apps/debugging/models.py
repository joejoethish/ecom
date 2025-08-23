from django.db import models
from django.conf import settings
import uuid


class WorkflowSession(models.Model):
    """Track complete user workflows across the system"""
    WORKFLOW_TYPES = [
        ('login', 'User Login'),
        ('product_fetch', 'Product Catalog Access'),
        ('cart_update', 'Cart Operations'),
        ('checkout', 'Checkout Process'),
        ('order_management', 'Order Management'),
        ('seller_operations', 'Seller Operations'),
        ('admin_operations', 'Admin Operations'),
        ('api_call', 'Generic API Call'),
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    correlation_id = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True, db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'debugging_workflow_session'
        indexes = [
            models.Index(fields=['correlation_id', 'start_time']),
            models.Index(fields=['workflow_type', 'status']),
            models.Index(fields=['user', 'start_time']),
        ]
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.workflow_type} - {self.correlation_id}"


class TraceStep(models.Model):
    """Individual steps within a workflow trace"""
    LAYER_CHOICES = [
        ('frontend', 'Frontend'),
        ('api', 'API'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('external', 'External Service'),
    ]
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    workflow_session = models.ForeignKey(WorkflowSession, on_delete=models.CASCADE, related_name='trace_steps')
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, db_index=True)
    component = models.CharField(max_length=100, db_index=True)
    operation = models.CharField(max_length=100)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started', db_index=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'debugging_trace_step'
        indexes = [
            models.Index(fields=['workflow_session', 'start_time']),
            models.Index(fields=['layer', 'component']),
            models.Index(fields=['status', 'duration_ms']),
        ]
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.layer}.{self.component} - {self.operation}"


class PerformanceSnapshot(models.Model):
    """Performance metrics collected from different system layers"""
    LAYER_CHOICES = [
        ('frontend', 'Frontend'),
        ('api', 'API'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('system', 'System'),
    ]
    
    METRIC_TYPES = [
        ('response_time', 'Response Time (ms)'),
        ('memory_usage', 'Memory Usage (MB)'),
        ('cpu_usage', 'CPU Usage (%)'),
        ('query_count', 'Query Count'),
        ('cache_hit_rate', 'Cache Hit Rate (%)'),
        ('error_rate', 'Error Rate (%)'),
        ('throughput', 'Throughput (req/sec)'),
        ('connection_pool', 'Connection Pool Usage'),
    ]
    
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, db_index=True)
    component = models.CharField(max_length=100, db_index=True)
    metric_name = models.CharField(max_length=50, choices=METRIC_TYPES, db_index=True)
    metric_value = models.FloatField()
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'debugging_performance_snapshot'
        indexes = [
            models.Index(fields=['timestamp', 'layer']),
            models.Index(fields=['metric_name', 'component']),
            models.Index(fields=['correlation_id', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.layer}.{self.component} - {self.metric_name}: {self.metric_value}"


class ErrorLog(models.Model):
    """Comprehensive error logging across all system layers"""
    LAYER_CHOICES = [
        ('frontend', 'Frontend'),
        ('api', 'API'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('external', 'External Service'),
        ('system', 'System'),
    ]
    
    SEVERITY_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, db_index=True)
    component = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='error', db_index=True)
    error_type = models.CharField(max_length=100, db_index=True)
    error_message = models.TextField()
    stack_trace = models.TextField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    request_path = models.CharField(max_length=500, null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    resolved = models.BooleanField(default=False, db_index=True)
    resolution_notes = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'debugging_error_log'
        indexes = [
            models.Index(fields=['correlation_id', 'timestamp']),
            models.Index(fields=['layer', 'severity']),
            models.Index(fields=['error_type', 'resolved']),
            models.Index(fields=['timestamp', 'severity']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.layer}.{self.component} - {self.error_type}: {self.error_message[:50]}"


class DebugConfiguration(models.Model):
    """Configuration settings for the debugging system"""
    CONFIG_TYPES = [
        ('performance_threshold', 'Performance Threshold'),
        ('logging_level', 'Logging Level'),
        ('tracing_enabled', 'Tracing Enabled'),
        ('dashboard_settings', 'Dashboard Settings'),
        ('alert_settings', 'Alert Settings'),
    ]
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    config_type = models.CharField(max_length=50, choices=CONFIG_TYPES, db_index=True)
    enabled = models.BooleanField(default=True)
    config_data = models.JSONField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'debugging_configuration'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.config_type})"


class PerformanceThreshold(models.Model):
    """Performance thresholds for monitoring and alerting"""
    METRIC_TYPES = [
        ('response_time', 'Response Time (ms)'),
        ('memory_usage', 'Memory Usage (MB)'),
        ('cpu_usage', 'CPU Usage (%)'),
        ('query_count', 'Query Count'),
        ('cache_hit_rate', 'Cache Hit Rate (%)'),
        ('error_rate', 'Error Rate (%)'),
        ('throughput', 'Throughput (req/sec)'),
    ]
    
    LAYER_CHOICES = [
        ('frontend', 'Frontend'),
        ('api', 'API'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('system', 'System'),
    ]
    
    metric_name = models.CharField(max_length=50, choices=METRIC_TYPES, db_index=True)
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, db_index=True)
    component = models.CharField(max_length=100, null=True, blank=True)
    warning_threshold = models.FloatField()
    critical_threshold = models.FloatField()
    enabled = models.BooleanField(default=True)
    alert_on_warning = models.BooleanField(default=True)
    alert_on_critical = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'debugging_performance_threshold'
        unique_together = ['metric_name', 'layer', 'component']
        indexes = [
            models.Index(fields=['metric_name', 'layer']),
            models.Index(fields=['enabled', 'layer']),
        ]
        ordering = ['layer', 'metric_name']
    
    def __str__(self):
        component_str = f".{self.component}" if self.component else ""
        return f"{self.layer}{component_str} - {self.metric_name}"
