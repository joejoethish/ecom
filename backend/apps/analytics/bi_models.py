"""
Advanced Business Intelligence Models for comprehensive analytics platform.
"""
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json
import uuid


class BIDashboard(models.Model):
    """Executive BI Dashboard configurations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(max_length=50, choices=[
        ('executive', 'Executive Summary'),
        ('sales', 'Sales Analytics'),
        ('financial', 'Financial Analytics'),
        ('operational', 'Operational Analytics'),
        ('customer', 'Customer Analytics'),
        ('product', 'Product Analytics'),
        ('custom', 'Custom Dashboard')
    ])
    layout_config = models.JSONField(default=dict)  # Widget positions and sizes
    filters_config = models.JSONField(default=dict)  # Default filters
    refresh_interval = models.IntegerField(default=300)  # Seconds
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_dashboards', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.dashboard_type})"


class BIWidget(models.Model):
    """BI Dashboard Widgets"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(BIDashboard, on_delete=models.CASCADE, related_name='widgets')
    name = models.CharField(max_length=200)
    widget_type = models.CharField(max_length=50, choices=[
        ('metric', 'Key Metric'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('gauge', 'Gauge'),
        ('map', 'Geographic Map'),
        ('funnel', 'Funnel Chart'),
        ('heatmap', 'Heat Map'),
        ('treemap', 'Tree Map'),
        ('scatter', 'Scatter Plot'),
        ('timeline', 'Timeline'),
        ('custom', 'Custom Widget')
    ])
    data_source = models.CharField(max_length=100)  # API endpoint or query identifier
    query_config = models.JSONField(default=dict)  # Query parameters and filters
    visualization_config = models.JSONField(default=dict)  # Chart/display settings
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4)
    height = models.IntegerField(default=3)
    refresh_interval = models.IntegerField(default=300)  # Seconds
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return f"{self.name} ({self.widget_type})"


class BIDataSource(models.Model):
    """BI Data Sources configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=50, choices=[
        ('database', 'Database Query'),
        ('api', 'API Endpoint'),
        ('file', 'File Upload'),
        ('external', 'External Service'),
        ('realtime', 'Real-time Stream')
    ])
    connection_config = models.JSONField(default=dict)  # Connection parameters
    query_template = models.TextField(blank=True)  # SQL or query template
    schema_definition = models.JSONField(default=dict)  # Data schema
    refresh_schedule = models.CharField(max_length=50, choices=[
        ('realtime', 'Real-time'),
        ('1min', 'Every Minute'),
        ('5min', 'Every 5 Minutes'),
        ('15min', 'Every 15 Minutes'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('manual', 'Manual Only')
    ], default='hourly')
    last_refresh = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class BIReport(models.Model):
    """BI Reports and Analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=[
        ('executive_summary', 'Executive Summary'),
        ('sales_performance', 'Sales Performance'),
        ('financial_analysis', 'Financial Analysis'),
        ('customer_insights', 'Customer Insights'),
        ('product_analysis', 'Product Analysis'),
        ('operational_metrics', 'Operational Metrics'),
        ('predictive_analytics', 'Predictive Analytics'),
        ('custom_report', 'Custom Report')
    ])
    data_sources = models.ManyToManyField(BIDataSource, related_name='reports')
    query_config = models.JSONField(default=dict)  # Report query configuration
    visualization_config = models.JSONField(default=dict)  # Report layout and charts
    filters_config = models.JSONField(default=dict)  # Available filters
    schedule_config = models.JSONField(default=dict)  # Automated scheduling
    export_formats = models.JSONField(default=list)  # Supported export formats
    recipients = models.JSONField(default=list)  # Email recipients for scheduled reports
    is_scheduled = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_reports', blank=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.report_type})"


class BIInsight(models.Model):
    """Automated insights and anomaly detection"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    insight_type = models.CharField(max_length=50, choices=[
        ('anomaly', 'Anomaly Detection'),
        ('trend', 'Trend Analysis'),
        ('correlation', 'Correlation Discovery'),
        ('forecast', 'Forecast Alert'),
        ('threshold', 'Threshold Breach'),
        ('pattern', 'Pattern Recognition'),
        ('recommendation', 'Recommendation'),
        ('alert', 'Business Alert')
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    data_source = models.ForeignKey(BIDataSource, on_delete=models.CASCADE)
    metric_name = models.CharField(max_length=100)
    current_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    expected_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    deviation_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    metadata = models.JSONField(default=dict)  # Additional insight data
    action_items = models.JSONField(default=list)  # Recommended actions
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_insights')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-severity']

    def __str__(self):
        return f"{self.title} ({self.insight_type})"


class BIMLModel(models.Model):
    """Machine Learning Models for BI"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    model_type = models.CharField(max_length=50, choices=[
        ('forecasting', 'Sales Forecasting'),
        ('classification', 'Customer Classification'),
        ('clustering', 'Customer Segmentation'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('recommendation', 'Recommendation Engine'),
        ('churn_prediction', 'Churn Prediction'),
        ('price_optimization', 'Price Optimization'),
        ('demand_planning', 'Demand Planning')
    ])
    algorithm = models.CharField(max_length=100)  # Algorithm used
    training_data_source = models.ForeignKey(BIDataSource, on_delete=models.CASCADE, related_name='ml_models')
    feature_config = models.JSONField(default=dict)  # Feature engineering configuration
    hyperparameters = models.JSONField(default=dict)  # Model hyperparameters
    performance_metrics = models.JSONField(default=dict)  # Model performance scores
    model_file_path = models.CharField(max_length=500, blank=True)  # Path to saved model
    version = models.CharField(max_length=50, default='1.0')
    is_deployed = models.BooleanField(default=False)
    deployment_config = models.JSONField(default=dict)  # Deployment settings
    last_trained = models.DateTimeField(null=True, blank=True)
    last_prediction = models.DateTimeField(null=True, blank=True)
    training_schedule = models.CharField(max_length=50, choices=[
        ('manual', 'Manual'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], default='manual')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"


class BIDataCatalog(models.Model):
    """Data catalog and metadata management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=50, choices=[
        ('table', 'Database Table'),
        ('view', 'Database View'),
        ('api', 'API Endpoint'),
        ('file', 'Data File'),
        ('stream', 'Data Stream')
    ])
    schema_name = models.CharField(max_length=100, blank=True)
    table_name = models.CharField(max_length=100, blank=True)
    columns_metadata = models.JSONField(default=dict)  # Column definitions and types
    data_quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_lineage = models.JSONField(default=dict)  # Data lineage information
    business_glossary = models.JSONField(default=dict)  # Business terms and definitions
    tags = models.JSONField(default=list)  # Searchable tags
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_data_assets')
    stewards = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='stewarded_data_assets', blank=True)
    access_level = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('confidential', 'Confidential')
    ], default='internal')
    last_updated = models.DateTimeField(null=True, blank=True)
    update_frequency = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.data_type})"


class BIAnalyticsSession(models.Model):
    """Self-service analytics sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data_sources = models.ManyToManyField(BIDataSource, related_name='analytics_sessions')
    query_history = models.JSONField(default=list)  # History of queries executed
    visualizations = models.JSONField(default=list)  # Created visualizations
    insights_discovered = models.JSONField(default=list)  # User-discovered insights
    bookmarks = models.JSONField(default=list)  # Bookmarked views
    collaboration_notes = models.TextField(blank=True)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_analytics_sessions', blank=True)
    is_public = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.name} by {self.user.username}"


class BIPerformanceMetric(models.Model):
    """BI system performance and optimization metrics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=50, choices=[
        ('query_performance', 'Query Performance'),
        ('dashboard_load_time', 'Dashboard Load Time'),
        ('data_freshness', 'Data Freshness'),
        ('user_engagement', 'User Engagement'),
        ('system_resource', 'System Resource Usage'),
        ('error_rate', 'Error Rate')
    ])
    value = models.DecimalField(max_digits=15, decimal_places=4)
    unit = models.CharField(max_length=50)  # seconds, percentage, count, etc.
    dashboard = models.ForeignKey(BIDashboard, on_delete=models.CASCADE, null=True, blank=True)
    widget = models.ForeignKey(BIWidget, on_delete=models.CASCADE, null=True, blank=True)
    data_source = models.ForeignKey(BIDataSource, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    metadata = models.JSONField(default=dict)  # Additional metric context
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"


class BIAlert(models.Model):
    """BI alerts and notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    alert_type = models.CharField(max_length=50, choices=[
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Alert'),
        ('data_quality', 'Data Quality Alert'),
        ('performance', 'Performance Alert'),
        ('schedule', 'Scheduled Alert')
    ])
    data_source = models.ForeignKey(BIDataSource, on_delete=models.CASCADE)
    condition_config = models.JSONField(default=dict)  # Alert conditions
    notification_config = models.JSONField(default=dict)  # Notification settings
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='bi_alerts')
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.alert_type})"