from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    APIVersion, APIKey, APIEndpoint, APIUsageLog, APIRateLimit,
    APIWebhook, APIWebhookDelivery, APIMockService, APIDocumentation,
    APIPerformanceMetric
)


class APIVersionSerializer(serializers.ModelSerializer):
    endpoint_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIVersion
        fields = '__all__'
    
    def get_endpoint_count(self, obj):
        return obj.endpoints.count()


class APIKeySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = '__all__'
        extra_kwargs = {
            'secret': {'write_only': True},
        }
    
    def get_usage_stats(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        today = now.date()
        
        # Get usage for today
        usage_logs = APIUsageLog.objects.filter(
            api_key=obj,
            timestamp__date=today
        )
        
        return {
            'requests_today': usage_logs.count(),
            'errors_today': usage_logs.filter(status='error').count(),
            'avg_response_time': usage_logs.aggregate(
                avg_time=serializers.models.Avg('response_time')
            )['avg_time'] or 0,
        }


class APIEndpointSerializer(serializers.ModelSerializer):
    version_name = serializers.CharField(source='version.version', read_only=True)
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = APIEndpoint
        fields = '__all__'
    
    def get_usage_stats(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        usage_logs = APIUsageLog.objects.filter(
            endpoint=obj,
            timestamp__gte=last_24h
        )
        
        return {
            'requests_24h': usage_logs.count(),
            'avg_response_time': usage_logs.aggregate(
                avg_time=serializers.models.Avg('response_time')
            )['avg_time'] or 0,
            'error_rate': (
                usage_logs.filter(status='error').count() / max(usage_logs.count(), 1)
            ) * 100,
        }


class APIUsageLogSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    endpoint_method = serializers.CharField(source='endpoint.method', read_only=True)
    
    class Meta:
        model = APIUsageLog
        fields = '__all__'


class APIRateLimitSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    
    class Meta:
        model = APIRateLimit
        fields = '__all__'


class APIWebhookSerializer(serializers.ModelSerializer):
    delivery_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = APIWebhook
        fields = '__all__'
    
    def get_delivery_stats(self, obj):
        deliveries = obj.deliveries.all()
        total = deliveries.count()
        
        if total == 0:
            return {'total': 0, 'success_rate': 0}
        
        successful = deliveries.filter(status='success').count()
        
        return {
            'total': total,
            'successful': successful,
            'failed': deliveries.filter(status='failed').count(),
            'success_rate': (successful / total) * 100,
        }


class APIWebhookDeliverySerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source='webhook.name', read_only=True)
    
    class Meta:
        model = APIWebhookDelivery
        fields = '__all__'


class APIMockServiceSerializer(serializers.ModelSerializer):
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    endpoint_method = serializers.CharField(source='endpoint.method', read_only=True)
    
    class Meta:
        model = APIMockService
        fields = '__all__'


class APIDocumentationSerializer(serializers.ModelSerializer):
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    endpoint_method = serializers.CharField(source='endpoint.method', read_only=True)
    
    class Meta:
        model = APIDocumentation
        fields = '__all__'


class APIPerformanceMetricSerializer(serializers.ModelSerializer):
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    endpoint_method = serializers.CharField(source='endpoint.method', read_only=True)
    
    class Meta:
        model = APIPerformanceMetric
        fields = '__all__'


class APIAnalyticsSerializer(serializers.Serializer):
    """Serializer for API analytics data"""
    total_requests = serializers.IntegerField()
    total_errors = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    top_endpoints = serializers.ListField()
    top_api_keys = serializers.ListField()
    hourly_stats = serializers.ListField()
    daily_stats = serializers.ListField()


class APIHealthSerializer(serializers.Serializer):
    """Serializer for API health status"""
    status = serializers.CharField()
    uptime = serializers.FloatField()
    response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    active_connections = serializers.IntegerField()
    memory_usage = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()


class GraphQLQuerySerializer(serializers.Serializer):
    """Serializer for GraphQL queries"""
    query = serializers.CharField()
    variables = serializers.JSONField(required=False, default=dict)
    operation_name = serializers.CharField(required=False, allow_blank=True)


class APITestCaseSerializer(serializers.Serializer):
    """Serializer for API test cases"""
    name = serializers.CharField()
    endpoint = serializers.CharField()
    method = serializers.CharField()
    headers = serializers.JSONField(default=dict)
    body = serializers.JSONField(required=False)
    expected_status = serializers.IntegerField()
    expected_response = serializers.JSONField(required=False)
    assertions = serializers.ListField(default=list)


class APIBenchmarkSerializer(serializers.Serializer):
    """Serializer for API benchmarking results"""
    endpoint = serializers.CharField()
    concurrent_users = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    duration = serializers.FloatField()
    requests_per_second = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    min_response_time = serializers.FloatField()
    max_response_time = serializers.FloatField()
    error_count = serializers.IntegerField()
    error_rate = serializers.FloatField()
    percentiles = serializers.JSONField()