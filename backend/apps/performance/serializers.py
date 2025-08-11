from rest_framework import serializers
from .models import (
    PerformanceMetric, ApplicationPerformanceMonitor, DatabasePerformanceLog,
    ServerMetrics, UserExperienceMetrics, PerformanceAlert, PerformanceBenchmark,
    PerformanceReport, PerformanceIncident
)

class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class ApplicationPerformanceMonitorSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationPerformanceMonitor
        fields = '__all__'
        read_only_fields = ('id',)
    
    def get_duration_seconds(self, obj):
        return obj.duration / 1000 if obj.duration else 0

class DatabasePerformanceLogSerializer(serializers.ModelSerializer):
    execution_time_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = DatabasePerformanceLog
        fields = '__all__'
        read_only_fields = ('id',)
    
    def get_execution_time_seconds(self, obj):
        return obj.execution_time / 1000 if obj.execution_time else 0

class ServerMetricsSerializer(serializers.ModelSerializer):
    memory_usage_gb = serializers.SerializerMethodField()
    disk_usage_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = ServerMetrics
        fields = '__all__'
        read_only_fields = ('id',)
    
    def get_memory_usage_gb(self, obj):
        return round((obj.memory_total - (obj.memory_total * (1 - obj.memory_usage / 100))) / (1024**3), 2)
    
    def get_disk_usage_gb(self, obj):
        return round((obj.disk_total * obj.disk_usage / 100) / (1024**3), 2)

class UserExperienceMetricsSerializer(serializers.ModelSerializer):
    performance_score = serializers.SerializerMethodField()
    
    class Meta:
        model = UserExperienceMetrics
        fields = '__all__'
        read_only_fields = ('id',)
    
    def get_performance_score(self, obj):
        """Calculate a simple performance score based on Core Web Vitals"""
        score = 100
        
        # Largest Contentful Paint (LCP) - should be < 2.5s
        if obj.largest_contentful_paint > 4000:
            score -= 30
        elif obj.largest_contentful_paint > 2500:
            score -= 15
        
        # First Input Delay (FID) - should be < 100ms
        if obj.first_input_delay > 300:
            score -= 25
        elif obj.first_input_delay > 100:
            score -= 10
        
        # Cumulative Layout Shift (CLS) - should be < 0.1
        if obj.cumulative_layout_shift > 0.25:
            score -= 25
        elif obj.cumulative_layout_shift > 0.1:
            score -= 10
        
        return max(0, score)

class PerformanceAlertSerializer(serializers.ModelSerializer):
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceAlert
        fields = '__all__'
        read_only_fields = ('id', 'triggered_at', 'acknowledged_at', 'resolved_at')
    
    def get_duration(self, obj):
        """Get alert duration in minutes"""
        if obj.resolved_at:
            return int((obj.resolved_at - obj.triggered_at).total_seconds() / 60)
        elif obj.acknowledged_at:
            return int((obj.acknowledged_at - obj.triggered_at).total_seconds() / 60)
        else:
            from django.utils import timezone
            return int((timezone.now() - obj.triggered_at).total_seconds() / 60)

class PerformanceBenchmarkSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    improvement_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceBenchmark
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
    
    def get_improvement_percentage(self, obj):
        """Calculate improvement percentage"""
        if obj.baseline_value and obj.current_value:
            return round(((obj.baseline_value - obj.current_value) / obj.baseline_value) * 100, 2)
        return 0

class PerformanceReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    insights_parsed = serializers.SerializerMethodField()
    recommendations_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceReport
        fields = '__all__'
        read_only_fields = ('id', 'generated_at', 'generated_by')
    
    def get_insights_parsed(self, obj):
        """Parse insights JSON string"""
        try:
            import json
            return json.loads(obj.insights) if obj.insights else []
        except:
            return []
    
    def get_recommendations_parsed(self, obj):
        """Parse recommendations JSON string"""
        try:
            import json
            return json.loads(obj.recommendations) if obj.recommendations else []
        except:
            return []

class PerformanceIncidentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceIncident
        fields = '__all__'
        read_only_fields = ('id', 'incident_id', 'started_at', 'resolved_at', 'created_by')
    
    def get_duration(self, obj):
        """Get incident duration in minutes"""
        if obj.resolved_at:
            return int((obj.resolved_at - obj.started_at).total_seconds() / 60)
        else:
            from django.utils import timezone
            return int((timezone.now() - obj.started_at).total_seconds() / 60)

# Simplified serializers for dashboard/summary views
class PerformanceMetricSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = ('id', 'metric_type', 'name', 'value', 'unit', 'timestamp', 'severity')

class AlertSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceAlert
        fields = ('id', 'name', 'severity', 'status', 'triggered_at', 'current_value')

class IncidentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceIncident
        fields = ('id', 'incident_id', 'title', 'severity', 'status', 'started_at')

# Custom serializers for specific API responses
class DashboardStatsSerializer(serializers.Serializer):
    response_time = serializers.DictField()
    error_rate = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    active_alerts = serializers.IntegerField()
    slow_queries = serializers.IntegerField()
    timestamp = serializers.DateTimeField()

class TimeSeriesDataSerializer(serializers.Serializer):
    timestamp = serializers.CharField()
    value = serializers.FloatField()

class TimeSeriesResponseSerializer(serializers.Serializer):
    metric_type = serializers.CharField()
    interval = serializers.CharField()
    data = TimeSeriesDataSerializer(many=True)

class EndpointStatsSerializer(serializers.Serializer):
    endpoint = serializers.CharField()
    avg_time = serializers.FloatField()
    max_time = serializers.FloatField()
    min_time = serializers.FloatField()
    request_count = serializers.IntegerField()

class AnomalyResponseSerializer(serializers.Serializer):
    metric_type = serializers.CharField()
    anomalies_count = serializers.IntegerField()
    anomalies = PerformanceMetricSerializer(many=True)

class CapacityForecastSerializer(serializers.Serializer):
    historical_data = serializers.ListField(child=serializers.FloatField())
    forecast = serializers.ListField(child=serializers.FloatField())
    trend = serializers.CharField()
    slope = serializers.FloatField()
    confidence = serializers.FloatField()

class CapacityRecommendationSerializer(serializers.Serializer):
    type = serializers.CharField()
    resource = serializers.CharField()
    message = serializers.CharField()
    recommendation = serializers.CharField()
    urgency = serializers.CharField()

class CapacityPlanningResponseSerializer(serializers.Serializer):
    forecasts = serializers.DictField(child=CapacityForecastSerializer())
    recommendations = CapacityRecommendationSerializer(many=True)
    days_ahead = serializers.IntegerField()

class SlowQueryStatsSerializer(serializers.Serializer):
    query_hash = serializers.CharField()
    count = serializers.IntegerField()
    avg_time = serializers.FloatField()
    max_time = serializers.FloatField()
    query_sample = serializers.CharField()

class TransactionStatsSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    avg_duration = serializers.FloatField()
    max_duration = serializers.FloatField()
    error_count = serializers.IntegerField()

class TransactionTypeStatsSerializer(serializers.Serializer):
    transaction_type = serializers.CharField()
    count = serializers.IntegerField()
    avg_duration = serializers.FloatField()

class TransactionStatsResponseSerializer(serializers.Serializer):
    stats = TransactionStatsSerializer()
    transaction_types = TransactionTypeStatsSerializer(many=True)