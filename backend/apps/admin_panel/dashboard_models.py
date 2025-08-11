"""
Advanced Dashboard System Models for comprehensive admin panel.
"""
import uuid
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from core.models import TimestampedModel
from .models import AdminUser


class DashboardWidget(TimestampedModel):
    """
    Customizable dashboard widgets with drag-and-drop functionality.
    """
    WIDGET_TYPE_CHOICES = [
        ('metric', 'Metric Card'),
        ('chart', 'Chart Widget'),
        ('table', 'Data Table'),
        ('list', 'List Widget'),
        ('calendar', 'Calendar Widget'),
        ('map', 'Map Widget'),
        ('iframe', 'External Content'),
        ('custom', 'Custom Widget'),
    ]
    
    CHART_TYPE_CHOICES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('radar', 'Radar Chart'),
        ('gauge', 'Gauge Chart'),
    ]
    
    SIZE_CHOICES = [
        ('small', 'Small (1x1)'),
        ('medium', 'Medium (2x1)'),
        ('large', 'Large (2x2)'),
        ('wide', 'Wide (3x1)'),
        ('tall', 'Tall (1x3)'),
        ('extra_large', 'Extra Large (3x2)'),
    ]
    
    # Widget identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Widget type and configuration
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES, blank=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='medium')
    
    # Data source configuration
    data_source = models.CharField(max_length=100)  # API endpoint or query name
    data_config = models.JSONField(default=dict)  # Parameters for data fetching
    refresh_interval = models.IntegerField(default=300)  # Seconds
    
    # Display configuration
    display_config = models.JSONField(default=dict)  # Colors, formatting, etc.
    chart_config = models.JSONField(default=dict)  # Chart-specific options
    
    # Permissions and access
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(default=list)  # List of role names
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='created_widgets')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_system_widget = models.BooleanField(default=False)  # Cannot be deleted
    
    class Meta:
        db_table = 'dashboard_widgets'
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['name']
        indexes = [
            models.Index(fields=['widget_type']),
            models.Index(fields=['data_source']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"


class DashboardLayout(TimestampedModel):
    """
    Dashboard layout configurations for different users and roles.
    """
    # Layout identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Owner and sharing
    owner = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='dashboard_layouts')
    is_shared = models.BooleanField(default=False)
    shared_with_roles = models.JSONField(default=list)  # List of role names
    shared_with_users = models.ManyToManyField(AdminUser, blank=True, related_name='shared_layouts')
    
    # Layout configuration
    layout_config = models.JSONField(default=dict)  # Grid layout positions
    widgets = models.ManyToManyField(DashboardWidget, through='DashboardWidgetPosition')
    
    # Template and defaults
    is_template = models.BooleanField(default=False)
    is_default_for_role = models.CharField(max_length=50, blank=True)  # Role name
    
    # Status
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'dashboard_layouts'
        verbose_name = 'Dashboard Layout'
        verbose_name_plural = 'Dashboard Layouts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_template']),
            models.Index(fields=['is_default_for_role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


class DashboardWidgetPosition(TimestampedModel):
    """
    Widget positions within dashboard layouts.
    """
    layout = models.ForeignKey(DashboardLayout, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    
    # Grid position
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    width = models.IntegerField(default=2)
    height = models.IntegerField(default=2)
    
    # Widget-specific configuration
    widget_config = models.JSONField(default=dict)  # Override widget settings
    
    # Status
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'dashboard_widget_positions'
        verbose_name = 'Dashboard Widget Position'
        verbose_name_plural = 'Dashboard Widget Positions'
        unique_together = ['layout', 'widget']
        ordering = ['order']


class DashboardTemplate(TimestampedModel):
    """
    Pre-built dashboard templates for different user roles.
    """
    TEMPLATE_TYPE_CHOICES = [
        ('executive', 'Executive Dashboard'),
        ('sales', 'Sales Dashboard'),
        ('inventory', 'Inventory Dashboard'),
        ('customer', 'Customer Dashboard'),
        ('financial', 'Financial Dashboard'),
        ('operational', 'Operational Dashboard'),
        ('marketing', 'Marketing Dashboard'),
        ('support', 'Support Dashboard'),
    ]
    
    # Template identification
    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    # Template configuration
    layout_config = models.JSONField(default=dict)
    widgets_config = models.JSONField(default=list)  # List of widget configurations
    
    # Target roles
    target_roles = models.JSONField(default=list)  # List of role names
    
    # Metadata
    preview_image = models.ImageField(upload_to='dashboard_templates/', blank=True)
    tags = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'dashboard_templates'
        verbose_name = 'Dashboard Template'
        verbose_name_plural = 'Dashboard Templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class DashboardUserPreference(TimestampedModel):
    """
    User-specific dashboard preferences and personalization.
    """
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'Auto (System)'),
    ]
    
    # User identification
    user = models.OneToOneField(AdminUser, on_delete=models.CASCADE, related_name='dashboard_preferences')
    
    # Layout preferences
    default_layout = models.ForeignKey(DashboardLayout, on_delete=models.SET_NULL, null=True, blank=True)
    grid_size = models.IntegerField(default=12)  # Grid columns
    compact_mode = models.BooleanField(default=False)
    
    # Display preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    show_animations = models.BooleanField(default=True)
    auto_refresh = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=300)  # Seconds
    
    # Notification preferences
    show_notifications = models.BooleanField(default=True)
    notification_position = models.CharField(max_length=20, default='top-right')
    
    # Data preferences
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    time_format = models.CharField(max_length=20, default='HH:mm:ss')
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=10, default='USD')
    
    # Advanced preferences
    preferences = models.JSONField(default=dict)  # Additional custom preferences
    
    class Meta:
        db_table = 'dashboard_user_preferences'
        verbose_name = 'Dashboard User Preference'
        verbose_name_plural = 'Dashboard User Preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"


class DashboardAlert(TimestampedModel):
    """
    Dashboard alerts and notifications system.
    """
    ALERT_TYPE_CHOICES = [
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Detection'),
        ('system', 'System Alert'),
        ('business', 'Business Alert'),
        ('security', 'Security Alert'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Alert identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    # Alert configuration
    data_source = models.CharField(max_length=100)
    condition_config = models.JSONField(default=dict)  # Alert conditions
    threshold_config = models.JSONField(default=dict)  # Threshold settings
    
    # Recipients
    recipients = models.ManyToManyField(AdminUser, blank=True, related_name='dashboard_alerts')
    recipient_roles = models.JSONField(default=list)  # List of role names
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    
    # Configuration
    is_enabled = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=60)  # Minimum time between alerts
    
    # Metadata
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='created_alerts')
    
    class Meta:
        db_table = 'dashboard_alerts'
        verbose_name = 'Dashboard Alert'
        verbose_name_plural = 'Dashboard Alerts'
        ordering = ['-last_triggered']
        indexes = [
            models.Index(fields=['alert_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['is_enabled']),
            models.Index(fields=['last_triggered']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class DashboardUsageAnalytics(TimestampedModel):
    """
    Analytics for dashboard usage and performance tracking.
    """
    ACTION_CHOICES = [
        ('view', 'Dashboard View'),
        ('widget_interact', 'Widget Interaction'),
        ('layout_change', 'Layout Change'),
        ('export', 'Data Export'),
        ('filter', 'Filter Applied'),
        ('refresh', 'Data Refresh'),
    ]
    
    # User and session
    user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='dashboard_usage')
    session_id = models.CharField(max_length=40)
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    dashboard_layout = models.ForeignKey(DashboardLayout, on_delete=models.SET_NULL, null=True, blank=True)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)  # Additional action data
    duration_seconds = models.IntegerField(null=True, blank=True)  # Time spent
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'dashboard_usage_analytics'
        verbose_name = 'Dashboard Usage Analytics'
        verbose_name_plural = 'Dashboard Usage Analytics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['dashboard_layout']),
            models.Index(fields=['widget']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


class DashboardExport(TimestampedModel):
    """
    Dashboard export and sharing functionality.
    """
    EXPORT_TYPE_CHOICES = [
        ('pdf', 'PDF Report'),
        ('image', 'Image Export'),
        ('data', 'Data Export'),
        ('link', 'Shareable Link'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('png', 'PNG Image'),
        ('jpg', 'JPEG Image'),
        ('csv', 'CSV Data'),
        ('excel', 'Excel File'),
        ('json', 'JSON Data'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    # Export identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    
    # Export configuration
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    dashboard_layout = models.ForeignKey(DashboardLayout, on_delete=models.CASCADE)
    
    # Export settings
    include_data = models.BooleanField(default=True)
    include_charts = models.BooleanField(default=True)
    date_range = models.JSONField(default=dict)  # Date range for data
    
    # File details
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Access control
    exported_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='dashboard_exports')
    is_public = models.BooleanField(default=False)
    access_token = models.CharField(max_length=64, blank=True)  # For shareable links
    expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'dashboard_exports'
        verbose_name = 'Dashboard Export'
        verbose_name_plural = 'Dashboard Exports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['export_type']),
            models.Index(fields=['status']),
            models.Index(fields=['exported_by']),
            models.Index(fields=['access_token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class DashboardDataSource(TimestampedModel):
    """
    External data source integrations for dashboard widgets.
    """
    SOURCE_TYPE_CHOICES = [
        ('api', 'REST API'),
        ('database', 'Database Query'),
        ('file', 'File Upload'),
        ('webhook', 'Webhook'),
        ('realtime', 'Real-time Stream'),
    ]
    
    AUTH_TYPE_CHOICES = [
        ('none', 'No Authentication'),
        ('basic', 'Basic Auth'),
        ('bearer', 'Bearer Token'),
        ('oauth2', 'OAuth 2.0'),
        ('api_key', 'API Key'),
    ]
    
    # Data source identification
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    
    # Connection configuration
    endpoint_url = models.URLField(blank=True)
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE_CHOICES, default='none')
    auth_config = models.JSONField(default=dict)  # Encrypted auth details
    
    # Data configuration
    data_mapping = models.JSONField(default=dict)  # Field mappings
    refresh_interval = models.IntegerField(default=300)  # Seconds
    cache_duration = models.IntegerField(default=300)  # Seconds
    
    # Status and monitoring
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    # Access control
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='data_sources')
    allowed_users = models.ManyToManyField(AdminUser, blank=True, related_name='accessible_data_sources')
    
    class Meta:
        db_table = 'dashboard_data_sources'
        verbose_name = 'Dashboard Data Source'
        verbose_name_plural = 'Dashboard Data Sources'
        ordering = ['name']
        indexes = [
            models.Index(fields=['source_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_sync']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"