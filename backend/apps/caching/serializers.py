from rest_framework import serializers
from .models import (
    CacheConfiguration, CacheMetrics, CacheInvalidation,
    CacheWarming, CacheAlert, CacheOptimization
)


class CacheConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for cache configuration"""
    
    class Meta:
        model = CacheConfiguration
        fields = [
            'id', 'name', 'cache_type', 'strategy', 'ttl_seconds',
            'max_size_mb', 'compression_enabled', 'encryption_enabled',
            'is_active', 'priority', 'config_json', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_ttl_seconds(self, value):
        if value < 0:
            raise serializers.ValidationError("TTL cannot be negative")
        if value > 31536000:  # 1 year
            raise serializers.ValidationError("TTL cannot exceed 1 year")
        return value
    
    def validate_max_size_mb(self, value):
        if value < 1:
            raise serializers.ValidationError("Cache size must be at least 1MB")
        if value > 10240:  # 10GB
            raise serializers.ValidationError("Cache size cannot exceed 10GB")
        return value


class CacheMetricsSerializer(serializers.ModelSerializer):
    """Serializer for cache metrics"""
    
    hit_ratio_percent = serializers.SerializerMethodField()
    memory_usage_status = serializers.SerializerMethodField()
    performance_grade = serializers.SerializerMethodField()
    
    class Meta:
        model = CacheMetrics
        fields = [
            'id', 'cache_name', 'cache_type', 'timestamp',
            'hit_count', 'miss_count', 'hit_ratio', 'hit_ratio_percent',
            'avg_response_time_ms', 'max_response_time_ms', 'min_response_time_ms',
            'memory_used_mb', 'memory_total_mb', 'memory_usage_percent', 'memory_usage_status',
            'get_operations', 'set_operations', 'delete_operations',
            'network_bytes_in', 'network_bytes_out',
            'error_count', 'timeout_count', 'performance_grade'
        ]
        read_only_fields = ['id']
    
    def get_hit_ratio_percent(self, obj):
        return f"{obj.hit_ratio * 100:.2f}%"
    
    def get_memory_usage_status(self, obj):
        if obj.memory_usage_percent < 50:
            return 'low'
        elif obj.memory_usage_percent < 80:
            return 'normal'
        elif obj.memory_usage_percent < 95:
            return 'high'
        else:
            return 'critical'
    
    def get_performance_grade(self, obj):
        score = 0
        
        # Hit ratio score (40%)
        score += min(40, obj.hit_ratio * 40)
        
        # Response time score (30%)
        if obj.avg_response_time_ms <= 10:
            score += 30
        elif obj.avg_response_time_ms <= 50:
            score += 20
        elif obj.avg_response_time_ms <= 100:
            score += 10
        
        # Memory usage score (20%)
        if obj.memory_usage_percent <= 70:
            score += 20
        elif obj.memory_usage_percent <= 85:
            score += 15
        elif obj.memory_usage_percent <= 95:
            score += 10
        
        # Error rate score (10%)
        total_ops = obj.get_operations + obj.set_operations
        error_rate = obj.error_count / max(total_ops, 1)
        if error_rate <= 0.01:
            score += 10
        elif error_rate <= 0.05:
            score += 5
        
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


class CacheInvalidationSerializer(serializers.ModelSerializer):
    """Serializer for cache invalidation events"""
    
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)
    
    class Meta:
        model = CacheInvalidation
        fields = [
            'id', 'cache_key', 'cache_name', 'invalidation_type',
            'reason', 'triggered_by', 'triggered_by_username',
            'timestamp', 'success', 'error_message'
        ]
        read_only_fields = ['id', 'timestamp', 'triggered_by_username']


class CacheWarmingSerializer(serializers.ModelSerializer):
    """Serializer for cache warming configurations"""
    
    success_rate = serializers.SerializerMethodField()
    next_run_relative = serializers.SerializerMethodField()
    
    class Meta:
        model = CacheWarming
        fields = [
            'id', 'name', 'cache_name', 'warming_type', 'schedule_cron',
            'query_pattern', 'priority', 'is_active', 'last_run', 'next_run',
            'success_count', 'failure_count', 'success_rate', 'next_run_relative',
            'created_at'
        ]
        read_only_fields = ['id', 'last_run', 'success_count', 'failure_count', 'created_at']
    
    def get_success_rate(self, obj):
        total = obj.success_count + obj.failure_count
        if total == 0:
            return None
        return f"{(obj.success_count / total) * 100:.2f}%"
    
    def get_next_run_relative(self, obj):
        if not obj.next_run:
            return None
        
        from django.utils import timezone
        from django.utils.timesince import timeuntil
        
        if obj.next_run > timezone.now():
            return f"in {timeuntil(obj.next_run)}"
        else:
            return "overdue"


class CacheAlertSerializer(serializers.ModelSerializer):
    """Serializer for cache alerts"""
    
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    age = serializers.SerializerMethodField()
    severity_color = serializers.SerializerMethodField()
    
    class Meta:
        model = CacheAlert
        fields = [
            'id', 'cache_name', 'alert_type', 'severity', 'severity_color',
            'message', 'threshold_value', 'current_value',
            'is_resolved', 'resolved_at', 'resolved_by', 'resolved_by_username',
            'created_at', 'age'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_by_username', 'age']
    
    def get_age(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())
    
    def get_severity_color(self, obj):
        colors = {
            'low': '#28a745',      # Green
            'medium': '#ffc107',   # Yellow
            'high': '#fd7e14',     # Orange
            'critical': '#dc3545'  # Red
        }
        return colors.get(obj.severity, '#6c757d')


class CacheOptimizationSerializer(serializers.ModelSerializer):
    """Serializer for cache optimization recommendations"""
    
    applied_by_username = serializers.CharField(source='applied_by.username', read_only=True)
    impact_level = serializers.SerializerMethodField()
    
    class Meta:
        model = CacheOptimization
        fields = [
            'id', 'cache_name', 'optimization_type', 'current_config',
            'recommended_config', 'expected_improvement', 'impact_score', 'impact_level',
            'is_applied', 'applied_at', 'applied_by', 'applied_by_username',
            'results', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'applied_by_username']
    
    def get_impact_level(self, obj):
        if obj.impact_score >= 80:
            return 'high'
        elif obj.impact_score >= 50:
            return 'medium'
        elif obj.impact_score >= 20:
            return 'low'
        else:
            return 'minimal'


class CacheStatsSerializer(serializers.Serializer):
    """Serializer for cache statistics"""
    
    cache_name = serializers.CharField()
    cache_type = serializers.CharField()
    is_active = serializers.BooleanField()
    ttl_seconds = serializers.IntegerField()
    compression_enabled = serializers.BooleanField()
    hit_ratio = serializers.FloatField()
    avg_response_time_ms = serializers.FloatField()
    memory_usage_percent = serializers.FloatField()
    error_count = serializers.IntegerField()
    redis_memory_used = serializers.CharField(required=False)
    redis_hit_ratio = serializers.FloatField(required=False)
    redis_connected_clients = serializers.IntegerField(required=False)


class CacheAnalysisSerializer(serializers.Serializer):
    """Serializer for cache performance analysis"""
    
    cache_name = serializers.CharField()
    analysis_period = serializers.CharField()
    total_metrics = serializers.IntegerField()
    optimization_score = serializers.FloatField()
    
    performance_summary = serializers.DictField()
    trends = serializers.DictField()
    bottlenecks = serializers.ListField()
    recommendations = serializers.ListField()


class CacheBenchmarkSerializer(serializers.Serializer):
    """Serializer for cache benchmark results"""
    
    cache_name = serializers.CharField()
    test_duration = serializers.IntegerField()
    operations = serializers.DictField()
    response_times = serializers.ListField()
    statistics = serializers.DictField(required=False)
    throughput = serializers.DictField()


class CDNAnalyticsSerializer(serializers.Serializer):
    """Serializer for CDN analytics"""
    
    period = serializers.CharField()
    cloudfront = serializers.DictField(required=False, allow_null=True)
    cloudflare = serializers.DictField(required=False, allow_null=True)


class AssetOptimizationSerializer(serializers.Serializer):
    """Serializer for asset optimization results"""
    
    uploaded = serializers.ListField()
    failed = serializers.ListField()
    total_size = serializers.IntegerField()
    compressed_size = serializers.IntegerField()
    compression_ratio = serializers.FloatField(required=False)


class ImageOptimizationSerializer(serializers.Serializer):
    """Serializer for image optimization results"""
    
    optimized = serializers.ListField()
    failed = serializers.ListField()
    total_savings = serializers.IntegerField()


class CacheInvalidationRequestSerializer(serializers.Serializer):
    """Serializer for cache invalidation requests"""
    
    cache_name = serializers.CharField()
    keys = serializers.ListField(child=serializers.CharField(), required=False)
    pattern = serializers.CharField(required=False)
    reason = serializers.CharField(max_length=500)
    
    def validate(self, data):
        if not data.get('keys') and not data.get('pattern'):
            raise serializers.ValidationError(
                "Either 'keys' or 'pattern' must be provided"
            )
        return data


class CacheWarmingRequestSerializer(serializers.Serializer):
    """Serializer for cache warming requests"""
    
    cache_name = serializers.CharField()
    keys = serializers.ListField(child=serializers.CharField())
    data_source = serializers.CharField()  # Function or endpoint to load data
    priority = serializers.IntegerField(default=1, min_value=1, max_value=10)