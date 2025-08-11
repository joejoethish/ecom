# Performance Monitoring Models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
import uuid

User = get_user_model()

class PerformanceMetric(models.Model):
    """Core performance metrics tracking"""
    METRIC_TYPES = [
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('network_io', 'Network I/O'),
        ('database_query', 'Database Query'),
        ('api_endpoint', 'API Endpoint'),
        ('user_experience', 'User Experience'),
        ('error_rate', 'Error Rate'),
        ('throughput', 'Throughput'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    name = models.CharField(max_length=200)
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=100)  # server, database, application, etc.
    endpoint = models.CharField(max_length=500, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='low')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_metrics'
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
        ]

class DatabasePerformanceLog(models.Model):
    """Database performance monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.TextField()
    query_hash = models.CharField(max_length=64)  # MD5 hash of query
    execution_time = models.FloatField()  # in milliseconds
    rows_examined = models.IntegerField(default=0)
    rows_returned = models.IntegerField(default=0)
    database_name = models.CharField(max_length=100)
    table_names = models.JSONField(default=list)
    query_type = models.CharField(max_length=20)  # SELECT, INSERT, UPDATE, DELETE
    is_slow_query = models.BooleanField(default=False)
    explain_plan = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    endpoint = models.CharField(max_length=500, blank=True, null=True)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'database_performance_logs'
        indexes = [
            models.Index(fields=['query_hash', 'timestamp']),
            models.Index(fields=['execution_time', 'timestamp']),
            models.Index(fields=['is_slow_query', 'timestamp']),
        ]

class ApplicationPerformanceMonitor(models.Model):
    """Application Performance Monitoring (APM)"""
    TRANSACTION_TYPES = [
        ('web_request', 'Web Request'),
        ('background_job', 'Background Job'),
        ('database_operation', 'Database Operation'),
        ('external_api', 'External API Call'),
        ('file_operation', 'File Operation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    name = models.CharField(max_length=200)
    duration = models.FloatField()  # in milliseconds
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status_code = models.IntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    stack_trace = models.TextField(blank=True, null=True)
    spans = models.JSONField(default=list)  # Distributed tracing spans
    tags = models.JSONField(default=dict)
    custom_metrics = models.JSONField(default=dict)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'application_performance_monitors'
        indexes = [
            models.Index(fields=['transaction_type', 'start_time']),
            models.Index(fields=['duration', 'start_time']),
            models.Index(fields=['status_code', 'start_time']),
        ]

class ServerMetrics(models.Model):
    """Server and infrastructure monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server_name = models.CharField(max_length=100)
    server_type = models.CharField(max_length=50)  # web, database, cache, etc.
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    memory_total = models.BigIntegerField()
    disk_usage = models.FloatField()
    disk_total = models.BigIntegerField()
    network_in = models.BigIntegerField(default=0)
    network_out = models.BigIntegerField(default=0)
    load_average = models.JSONField(default=list)  # [1min, 5min, 15min]
    active_connections = models.IntegerField(default=0)
    processes_count = models.IntegerField(default=0)
    uptime = models.BigIntegerField(default=0)  # in seconds
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'server_metrics'
        indexes = [
            models.Index(fields=['server_name', 'timestamp']),
            models.Index(fields=['server_type', 'timestamp']),
        ]

class UserExperienceMetrics(models.Model):
    """User experience monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    page_url = models.URLField()
    page_load_time = models.FloatField()  # in milliseconds
    dom_content_loaded = models.FloatField()
    first_contentful_paint = models.FloatField()
    largest_contentful_paint = models.FloatField()
    first_input_delay = models.FloatField()
    cumulative_layout_shift = models.FloatField()
    time_to_interactive = models.FloatField()
    bounce_rate = models.BooleanField(default=False)
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50)
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    screen_resolution = models.CharField(max_length=20)
    connection_type = models.CharField(max_length=50, blank=True, null=True)
    geographic_location = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_experience_metrics'
        indexes = [
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['page_url', 'timestamp']),
            models.Index(fields=['device_type', 'timestamp']),
        ]

class PerformanceAlert(models.Model):
    """Performance alerting system"""
    ALERT_TYPES = [
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Detection'),
        ('trend', 'Trend Alert'),
        ('sla_breach', 'SLA Breach'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('suppressed', 'Suppressed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField()
    metric_type = models.CharField(max_length=50)
    threshold_value = models.FloatField()
    current_value = models.FloatField()
    severity = models.CharField(max_length=20, choices=PerformanceMetric.SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    triggered_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    notification_sent = models.BooleanField(default=False)
    escalation_level = models.IntegerField(default=1)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'performance_alerts'
        indexes = [
            models.Index(fields=['status', 'triggered_at']),
            models.Index(fields=['severity', 'triggered_at']),
            models.Index(fields=['metric_type', 'triggered_at']),
        ]

class PerformanceBenchmark(models.Model):
    """Performance benchmarking and comparison"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    benchmark_type = models.CharField(max_length=50)
    baseline_value = models.FloatField()
    current_value = models.FloatField()
    target_value = models.FloatField()
    unit = models.CharField(max_length=20)
    improvement_percentage = models.FloatField(default=0)
    test_environment = models.CharField(max_length=100)
    test_configuration = models.JSONField(default=dict)
    test_results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'performance_benchmarks'

class PerformanceReport(models.Model):
    """Performance reporting and analytics"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
        ('sla', 'SLA Report'),
        ('capacity', 'Capacity Planning Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    metrics_included = models.JSONField(default=list)
    report_data = models.JSONField(default=dict)
    insights = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_scheduled = models.BooleanField(default=False)
    schedule_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'performance_reports'
        indexes = [
            models.Index(fields=['report_type', 'generated_at']),
            models.Index(fields=['date_range_start', 'date_range_end']),
        ]

class PerformanceIncident(models.Model):
    """Performance incident management"""
    INCIDENT_TYPES = [
        ('outage', 'Service Outage'),
        ('degradation', 'Performance Degradation'),
        ('error_spike', 'Error Rate Spike'),
        ('capacity_issue', 'Capacity Issue'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('identified', 'Identified'),
        ('monitoring', 'Monitoring'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=20, choices=PerformanceMetric.SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    affected_services = models.JSONField(default=list)
    root_cause = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_incidents')
    timeline = models.JSONField(default=list)
    postmortem = models.TextField(blank=True)
    
    class Meta:
        db_table = 'performance_incidents'
        indexes = [
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['severity', 'started_at']),
        ]