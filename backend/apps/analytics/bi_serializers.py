"""
Advanced Business Intelligence Serializers for comprehensive analytics platform.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .bi_models import (
    BIDashboard, BIWidget, BIDataSource, BIReport, BIInsight, BIMLModel,
    BIDataCatalog, BIAnalyticsSession, BIPerformanceMetric, BIAlert
)


class BIDashboardSerializer(serializers.ModelSerializer):
    """Serializer for BI Dashboard"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    widgets_count = serializers.SerializerMethodField()
    shared_with_users = serializers.SerializerMethodField()

    class Meta:
        model = BIDashboard
        fields = [
            'id', 'name', 'description', 'dashboard_type', 'layout_config',
            'filters_config', 'refresh_interval', 'is_public', 'created_by',
            'created_by_name', 'is_active', 'created_at', 'updated_at',
            'widgets_count', 'shared_with_users'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_widgets_count(self, obj):
        return obj.widgets.filter(is_active=True).count()

    def get_shared_with_users(self, obj):
        return [
            {'id': user.id, 'name': user.get_full_name(), 'email': user.email}
            for user in obj.shared_with.all()
        ]


class BIWidgetSerializer(serializers.ModelSerializer):
    """Serializer for BI Widget"""
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)

    class Meta:
        model = BIWidget
        fields = [
            'id', 'dashboard', 'dashboard_name', 'name', 'widget_type',
            'data_source', 'query_config', 'visualization_config',
            'position_x', 'position_y', 'width', 'height', 'refresh_interval',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BIDataSourceSerializer(serializers.ModelSerializer):
    """Serializer for BI Data Source"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    reports_count = serializers.SerializerMethodField()
    ml_models_count = serializers.SerializerMethodField()

    class Meta:
        model = BIDataSource
        fields = [
            'id', 'name', 'description', 'source_type', 'connection_config',
            'query_template', 'schema_definition', 'refresh_schedule',
            'last_refresh', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'reports_count', 'ml_models_count'
        ]
        read_only_fields = ['id', 'created_by', 'last_refresh', 'created_at', 'updated_at']

    def get_reports_count(self, obj):
        return obj.reports.filter(is_active=True).count()

    def get_ml_models_count(self, obj):
        return obj.ml_models.filter(is_active=True).count()


class BIReportSerializer(serializers.ModelSerializer):
    """Serializer for BI Report"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    data_sources_names = serializers.SerializerMethodField()
    shared_with_users = serializers.SerializerMethodField()

    class Meta:
        model = BIReport
        fields = [
            'id', 'name', 'description', 'report_type', 'query_config',
            'visualization_config', 'filters_config', 'schedule_config',
            'export_formats', 'recipients', 'is_scheduled', 'is_public',
            'created_by', 'created_by_name', 'last_generated', 'is_active',
            'created_at', 'updated_at', 'data_sources_names', 'shared_with_users'
        ]
        read_only_fields = ['id', 'created_by', 'last_generated', 'created_at', 'updated_at']

    def get_data_sources_names(self, obj):
        return [ds.name for ds in obj.data_sources.all()]

    def get_shared_with_users(self, obj):
        return [
            {'id': user.id, 'name': user.get_full_name(), 'email': user.email}
            for user in obj.shared_with.all()
        ]


class BIInsightSerializer(serializers.ModelSerializer):
    """Serializer for BI Insight"""
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    age_hours = serializers.SerializerMethodField()

    class Meta:
        model = BIInsight
        fields = [
            'id', 'title', 'description', 'insight_type', 'severity',
            'data_source', 'data_source_name', 'metric_name', 'current_value',
            'expected_value', 'deviation_percentage', 'confidence_score',
            'metadata', 'action_items', 'is_acknowledged', 'acknowledged_by',
            'acknowledged_by_name', 'acknowledged_at', 'is_resolved',
            'resolution_notes', 'created_at', 'age_hours'
        ]
        read_only_fields = [
            'id', 'acknowledged_by', 'acknowledged_at', 'created_at', 'age_hours'
        ]

    def get_age_hours(self, obj):
        from django.utils import timezone
        age = timezone.now() - obj.created_at
        return round(age.total_seconds() / 3600, 1)


class BIMLModelSerializer(serializers.ModelSerializer):
    """Serializer for BI ML Model"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    training_data_source_name = serializers.CharField(source='training_data_source.name', read_only=True)
    model_status = serializers.SerializerMethodField()

    class Meta:
        model = BIMLModel
        fields = [
            'id', 'name', 'description', 'model_type', 'algorithm',
            'training_data_source', 'training_data_source_name', 'feature_config',
            'hyperparameters', 'performance_metrics', 'model_file_path',
            'version', 'is_deployed', 'deployment_config', 'last_trained',
            'last_prediction', 'training_schedule', 'created_by',
            'created_by_name', 'is_active', 'created_at', 'updated_at',
            'model_status'
        ]
        read_only_fields = [
            'id', 'created_by', 'last_trained', 'last_prediction',
            'created_at', 'updated_at', 'model_status'
        ]

    def get_model_status(self, obj):
        if not obj.last_trained:
            return 'not_trained'
        elif obj.is_deployed:
            return 'deployed'
        else:
            return 'trained'


class BIDataCatalogSerializer(serializers.ModelSerializer):
    """Serializer for BI Data Catalog"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    stewards_names = serializers.SerializerMethodField()

    class Meta:
        model = BIDataCatalog
        fields = [
            'id', 'name', 'description', 'data_type', 'schema_name',
            'table_name', 'columns_metadata', 'data_quality_score',
            'data_lineage', 'business_glossary', 'tags', 'owner',
            'owner_name', 'access_level', 'last_updated', 'update_frequency',
            'is_active', 'created_at', 'stewards_names'
        ]
        read_only_fields = ['id', 'created_at']

    def get_stewards_names(self, obj):
        return [steward.get_full_name() for steward in obj.stewards.all()]


class BIAnalyticsSessionSerializer(serializers.ModelSerializer):
    """Serializer for BI Analytics Session"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    data_sources_names = serializers.SerializerMethodField()
    shared_with_users = serializers.SerializerMethodField()
    session_duration = serializers.SerializerMethodField()

    class Meta:
        model = BIAnalyticsSession
        fields = [
            'id', 'name', 'description', 'user', 'user_name', 'query_history',
            'visualizations', 'insights_discovered', 'bookmarks',
            'collaboration_notes', 'is_public', 'last_accessed', 'created_at',
            'data_sources_names', 'shared_with_users', 'session_duration'
        ]
        read_only_fields = ['id', 'user', 'last_accessed', 'created_at']

    def get_data_sources_names(self, obj):
        return [ds.name for ds in obj.data_sources.all()]

    def get_shared_with_users(self, obj):
        return [
            {'id': user.id, 'name': user.get_full_name(), 'email': user.email}
            for user in obj.shared_with.all()
        ]

    def get_session_duration(self, obj):
        from django.utils import timezone
        duration = obj.last_accessed - obj.created_at
        return round(duration.total_seconds() / 3600, 1)  # Hours


class BIPerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for BI Performance Metric"""
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    widget_name = serializers.CharField(source='widget.name', read_only=True)
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = BIPerformanceMetric
        fields = [
            'id', 'metric_name', 'metric_type', 'value', 'unit',
            'dashboard', 'dashboard_name', 'widget', 'widget_name',
            'data_source', 'data_source_name', 'user', 'user_name',
            'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class BIAlertSerializer(serializers.ModelSerializer):
    """Serializer for BI Alert"""
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    recipients_names = serializers.SerializerMethodField()

    class Meta:
        model = BIAlert
        fields = [
            'id', 'name', 'description', 'alert_type', 'data_source',
            'data_source_name', 'condition_config', 'notification_config',
            'is_active', 'last_triggered', 'trigger_count', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'recipients_names'
        ]
        read_only_fields = [
            'id', 'created_by', 'last_triggered', 'trigger_count',
            'created_at', 'updated_at'
        ]

    def get_recipients_names(self, obj):
        return [recipient.get_full_name() for recipient in obj.recipients.all()]


# Additional specialized serializers for complex data structures

class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data response"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    dashboard_type = serializers.CharField()
    layout_config = serializers.JSONField()
    filters_config = serializers.JSONField()
    widgets = serializers.ListField(child=serializers.JSONField())


class WidgetDataSerializer(serializers.Serializer):
    """Serializer for widget data response"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    widget_type = serializers.CharField()
    position_x = serializers.IntegerField()
    position_y = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    visualization_config = serializers.JSONField()
    data = serializers.JSONField()
    last_updated = serializers.DateTimeField()
    error = serializers.CharField(required=False)


class InsightGenerationSerializer(serializers.Serializer):
    """Serializer for insight generation request"""
    data_source_id = serializers.UUIDField(required=False)
    insight_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['anomaly', 'trend', 'pattern']
    )
    date_range = serializers.CharField(default='30d')
    confidence_threshold = serializers.FloatField(default=70.0)


class MLModelTrainingSerializer(serializers.Serializer):
    """Serializer for ML model training request"""
    model_id = serializers.UUIDField()
    training_config = serializers.JSONField(required=False)
    validation_split = serializers.FloatField(default=0.2)
    cross_validation = serializers.BooleanField(default=True)


class PredictionRequestSerializer(serializers.Serializer):
    """Serializer for prediction request"""
    model_id = serializers.UUIDField()
    prediction_periods = serializers.IntegerField(default=30)
    confidence_level = serializers.FloatField(default=95.0)
    include_intervals = serializers.BooleanField(default=True)


class DataQualityAssessmentSerializer(serializers.Serializer):
    """Serializer for data quality assessment response"""
    data_source_id = serializers.UUIDField()
    data_source_name = serializers.CharField()
    overall_score = serializers.FloatField()
    quality_metrics = serializers.JSONField()
    issues = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.ListField(child=serializers.CharField())
    assessed_at = serializers.DateTimeField()


class DataLineageSerializer(serializers.Serializer):
    """Serializer for data lineage response"""
    source_id = serializers.UUIDField()
    source_name = serializers.CharField()
    upstream_sources = serializers.ListField(child=serializers.JSONField())
    transformations = serializers.ListField(child=serializers.JSONField())
    downstream_consumers = serializers.ListField(child=serializers.JSONField())
    impact_analysis = serializers.JSONField()


class RealtimeMetricsSerializer(serializers.Serializer):
    """Serializer for real-time metrics response"""
    timestamp = serializers.DateTimeField()
    active_users = serializers.IntegerField()
    current_revenue = serializers.FloatField()
    orders_today = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
    cart_abandonment_rate = serializers.FloatField()
    page_views = serializers.IntegerField()
    bounce_rate = serializers.FloatField()
    average_session_duration = serializers.FloatField()
    top_products_realtime = serializers.ListField(child=serializers.JSONField())
    geographic_activity = serializers.ListField(child=serializers.JSONField())


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for export request"""
    dashboard_id = serializers.UUIDField(required=False)
    report_id = serializers.UUIDField(required=False)
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel', 'pdf'],
        default='json'
    )
    filters = serializers.JSONField(required=False)
    date_range = serializers.CharField(required=False)


class StreamingEventSerializer(serializers.Serializer):
    """Serializer for streaming event processing"""
    type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    user_id = serializers.IntegerField(required=False)
    session_id = serializers.CharField(required=False)
    data = serializers.JSONField()
    metadata = serializers.JSONField(required=False)


class GovernanceDashboardSerializer(serializers.Serializer):
    """Serializer for governance dashboard response"""
    data_sources_count = serializers.IntegerField()
    data_quality_average = serializers.FloatField()
    compliance_score = serializers.FloatField()
    active_policies = serializers.IntegerField()
    recent_quality_issues = serializers.ListField(child=serializers.JSONField())
    data_stewards = serializers.IntegerField()
    cataloged_assets = serializers.IntegerField()
    last_audit = serializers.DateTimeField()


class VisualizationSerializer(serializers.Serializer):
    """Serializer for visualization data"""
    id = serializers.UUIDField(required=False)
    name = serializers.CharField()
    type = serializers.CharField()
    config = serializers.JSONField()
    data = serializers.JSONField()
    created_at = serializers.DateTimeField(required=False)


class BookmarkSerializer(serializers.Serializer):
    """Serializer for bookmark data"""
    id = serializers.UUIDField(required=False)
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    url = serializers.CharField()
    filters = serializers.JSONField(required=False)
    created_at = serializers.DateTimeField(required=False)