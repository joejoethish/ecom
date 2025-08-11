"""
Serializers for Advanced Dashboard System.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .dashboard_models import (
    DashboardWidget, DashboardLayout, DashboardWidgetPosition,
    DashboardTemplate, DashboardUserPreference, DashboardAlert,
    DashboardUsageAnalytics, DashboardExport, DashboardDataSource
)
from .models import AdminUser


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer for dashboard widgets."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'name', 'title', 'description', 'widget_type', 'chart_type',
            'size', 'data_source', 'data_config', 'refresh_interval',
            'display_config', 'chart_config', 'is_public', 'allowed_roles',
            'created_by', 'created_by_username', 'is_active', 'is_system_widget',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_data_config(self, value):
        """Validate data configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data config must be a dictionary.")
        return value

    def validate_display_config(self, value):
        """Validate display configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Display config must be a dictionary.")
        return value


class DashboardWidgetPositionSerializer(serializers.ModelSerializer):
    """Serializer for widget positions in layouts."""
    
    widget_details = DashboardWidgetSerializer(source='widget', read_only=True)
    
    class Meta:
        model = DashboardWidgetPosition
        fields = [
            'id', 'layout', 'widget', 'widget_details', 'x', 'y', 'width', 'height',
            'widget_config', 'is_visible', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardLayoutSerializer(serializers.ModelSerializer):
    """Serializer for dashboard layouts."""
    
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    widget_positions = DashboardWidgetPositionSerializer(
        source='dashboardwidgetposition_set', many=True, read_only=True
    )
    widget_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardLayout
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'is_shared', 'shared_with_roles', 'layout_config',
            'widget_positions', 'widget_count', 'is_template',
            'is_default_for_role', 'is_active', 'version',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_widget_count(self, obj):
        """Get the number of widgets in this layout."""
        return obj.dashboardwidgetposition_set.filter(is_visible=True).count()

    def validate_layout_config(self, value):
        """Validate layout configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Layout config must be a dictionary.")
        return value


class DashboardLayoutCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating dashboard layouts with widgets."""
    
    widgets = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = DashboardLayout
        fields = [
            'name', 'description', 'is_shared', 'shared_with_roles',
            'layout_config', 'widgets', 'is_template', 'is_default_for_role'
        ]

    def create(self, validated_data):
        """Create layout with widget positions."""
        widgets_data = validated_data.pop('widgets', [])
        layout = super().create(validated_data)
        
        # Create widget positions
        for widget_data in widgets_data:
            DashboardWidgetPosition.objects.create(
                layout=layout,
                widget_id=widget_data['widget_id'],
                x=widget_data.get('x', 0),
                y=widget_data.get('y', 0),
                width=widget_data.get('width', 2),
                height=widget_data.get('height', 2),
                widget_config=widget_data.get('config', {}),
                order=widget_data.get('order', 0)
            )
        
        return layout


class DashboardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for dashboard templates."""
    
    usage_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DashboardTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'layout_config',
            'widgets_config', 'target_roles', 'preview_image', 'tags',
            'is_active', 'is_featured', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']

    def validate_widgets_config(self, value):
        """Validate widgets configuration."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Widgets config must be a list.")
        return value


class DashboardUserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user dashboard preferences."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    default_layout_name = serializers.CharField(source='default_layout.name', read_only=True)
    
    class Meta:
        model = DashboardUserPreference
        fields = [
            'id', 'user', 'user_username', 'default_layout', 'default_layout_name',
            'grid_size', 'compact_mode', 'theme', 'show_animations',
            'auto_refresh', 'refresh_interval', 'show_notifications',
            'notification_position', 'date_format', 'time_format',
            'timezone', 'currency', 'preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardAlertSerializer(serializers.ModelSerializer):
    """Serializer for dashboard alerts."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    recipient_usernames = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardAlert
        fields = [
            'id', 'name', 'description', 'alert_type', 'severity',
            'data_source', 'condition_config', 'threshold_config',
            'recipients', 'recipient_usernames', 'recipient_roles',
            'status', 'last_triggered', 'trigger_count', 'is_enabled',
            'cooldown_minutes', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_triggered', 'trigger_count', 'created_at', 'updated_at']

    def get_recipient_usernames(self, obj):
        """Get usernames of alert recipients."""
        return [user.username for user in obj.recipients.all()]

    def validate_condition_config(self, value):
        """Validate condition configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Condition config must be a dictionary.")
        return value


class DashboardUsageAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for dashboard usage analytics."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard_layout.name', read_only=True)
    widget_name = serializers.CharField(source='widget.name', read_only=True)
    
    class Meta:
        model = DashboardUsageAnalytics
        fields = [
            'id', 'user', 'user_username', 'session_id', 'action',
            'dashboard_layout', 'dashboard_name', 'widget', 'widget_name',
            'metadata', 'duration_seconds', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DashboardExportSerializer(serializers.ModelSerializer):
    """Serializer for dashboard exports."""
    
    exported_by_username = serializers.CharField(source='exported_by.username', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard_layout.name', read_only=True)
    file_size_human = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardExport
        fields = [
            'id', 'name', 'export_type', 'format', 'dashboard_layout',
            'dashboard_name', 'include_data', 'include_charts', 'date_range',
            'file_path', 'file_size', 'file_size_human', 'status',
            'progress_percentage', 'error_message', 'exported_by',
            'exported_by_username', 'is_public', 'access_token',
            'expires_at', 'is_expired', 'download_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_path', 'file_size', 'status', 'progress_percentage',
            'error_message', 'access_token', 'download_count',
            'created_at', 'updated_at'
        ]

    def get_file_size_human(self, obj):
        """Get human-readable file size."""
        if not obj.file_size:
            return None
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"

    def get_is_expired(self, obj):
        """Check if export has expired."""
        if not obj.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > obj.expires_at


class DashboardDataSourceSerializer(serializers.ModelSerializer):
    """Serializer for dashboard data sources."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DashboardDataSource
        fields = [
            'id', 'name', 'description', 'source_type', 'endpoint_url',
            'auth_type', 'auth_config', 'data_mapping', 'refresh_interval',
            'cache_duration', 'is_active', 'last_sync', 'sync_status',
            'error_count', 'last_error', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_sync', 'sync_status', 'error_count', 'last_error',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'auth_config': {'write_only': True}  # Don't expose auth details
        }

    def validate_data_mapping(self, value):
        """Validate data mapping configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data mapping must be a dictionary.")
        return value


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_dashboards = serializers.IntegerField()
    total_widgets = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_exports = serializers.IntegerField()
    popular_widgets = serializers.ListField(
        child=serializers.DictField()
    )
    usage_by_role = serializers.DictField()
    recent_activity = serializers.ListField(
        child=serializers.DictField()
    )


class WidgetDataSerializer(serializers.Serializer):
    """Serializer for widget data responses."""
    
    widget_id = serializers.UUIDField()
    data = serializers.JSONField()
    last_updated = serializers.DateTimeField()
    cache_expires = serializers.DateTimeField(required=False)
    error = serializers.CharField(required=False)


class DashboardRealTimeUpdateSerializer(serializers.Serializer):
    """Serializer for real-time dashboard updates."""
    
    event_type = serializers.ChoiceField(choices=[
        'widget_update', 'layout_change', 'alert_triggered', 'user_joined', 'user_left'
    ])
    dashboard_id = serializers.UUIDField()
    widget_id = serializers.UUIDField(required=False)
    user_id = serializers.UUIDField(required=False)
    data = serializers.JSONField()
    timestamp = serializers.DateTimeField()