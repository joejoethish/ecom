"""
Chart models for advanced data visualization
"""
from django.db import models
from django.contrib.auth import get_user_model
# JSONSchemaValidator not available in this Django version
# from django.core.validators import JSONSchemaValidator
import uuid
import json

User = get_user_model()

class ChartTemplate(models.Model):
    """Predefined chart templates for common use cases"""
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('heatmap', 'Heatmap'),
        ('gauge', 'Gauge Chart'),
        ('funnel', 'Funnel Chart'),
        ('treemap', 'Treemap'),
        ('radar', 'Radar Chart'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES)
    category = models.CharField(max_length=100)  # sales, inventory, customer, financial
    config = models.JSONField(default=dict)  # Chart configuration
    data_source = models.CharField(max_length=200)  # API endpoint or query
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_chart_templates'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.chart_type})"

class Chart(models.Model):
    """Individual chart instances"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    chart_type = models.CharField(max_length=50, choices=ChartTemplate.CHART_TYPES)
    template = models.ForeignKey(ChartTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Chart Configuration
    config = models.JSONField(default=dict)
    data_source = models.CharField(max_length=200)
    refresh_interval = models.IntegerField(default=300)  # seconds
    
    # Customization
    theme = models.CharField(max_length=50, default='default')
    colors = models.JSONField(default=list)
    custom_css = models.TextField(blank=True)
    
    # Access Control
    is_public = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User, blank=True)
    allowed_roles = models.JSONField(default=list)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_real_time = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_charts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'admin_charts'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ChartVersion(models.Model):
    """Chart version history for change tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    title = models.CharField(max_length=200)
    config = models.JSONField()
    changes_summary = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_versions'
        unique_together = ['chart', 'version_number']
        ordering = ['-version_number']

class ChartAnnotation(models.Model):
    """Chart annotations and markup"""
    ANNOTATION_TYPES = [
        ('note', 'Note'),
        ('highlight', 'Highlight'),
        ('trend_line', 'Trend Line'),
        ('threshold', 'Threshold'),
        ('event', 'Event Marker'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='annotations')
    annotation_type = models.CharField(max_length=50, choices=ANNOTATION_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    position = models.JSONField()  # x, y coordinates or data point
    style = models.JSONField(default=dict)  # color, size, etc.
    is_visible = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_annotations'

class ChartComment(models.Model):
    """Chart collaboration and commenting"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    position = models.JSONField(null=True, blank=True)  # Optional position on chart
    is_resolved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_chart_comments'
        ordering = ['created_at']

class ChartShare(models.Model):
    """Chart sharing and embedding"""
    SHARE_TYPES = [
        ('public_link', 'Public Link'),
        ('embed_code', 'Embed Code'),
        ('api_access', 'API Access'),
        ('email', 'Email Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='shares')
    share_type = models.CharField(max_length=50, choices=SHARE_TYPES)
    share_token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    access_count = models.IntegerField(default=0)
    settings = models.JSONField(default=dict)  # Share-specific settings
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_shares'

class ChartPerformanceMetric(models.Model):
    """Chart performance monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='performance_metrics')
    load_time = models.FloatField()  # milliseconds
    data_size = models.IntegerField()  # bytes
    render_time = models.FloatField()  # milliseconds
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_performance'
        indexes = [
            models.Index(fields=['chart', 'timestamp']),
        ]

class ChartDataCache(models.Model):
    """Chart data caching for performance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='data_cache')
    cache_key = models.CharField(max_length=200, unique=True)
    data = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_data_cache'
        indexes = [
            models.Index(fields=['cache_key', 'expires_at']),
        ]

class ChartExport(models.Model):
    """Chart export history and tracking"""
    EXPORT_FORMATS = [
        ('png', 'PNG Image'),
        ('pdf', 'PDF Document'),
        ('svg', 'SVG Vector'),
        ('excel', 'Excel Spreadsheet'),
        ('csv', 'CSV Data'),
        ('json', 'JSON Data'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=20, choices=EXPORT_FORMATS)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField()
    export_settings = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_chart_exports'