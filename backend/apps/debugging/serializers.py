from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold,
    FrontendRoute, APICallDiscovery, RouteDiscoverySession, RouteDependency
)


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for debugging context"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TraceStepSerializer(serializers.ModelSerializer):
    """Serializer for individual trace steps"""
    class Meta:
        model = TraceStep
        fields = [
            'id', 'layer', 'component', 'operation', 'start_time', 
            'end_time', 'status', 'duration_ms', 'metadata'
        ]
        read_only_fields = ['id']


class WorkflowSessionSerializer(serializers.ModelSerializer):
    """Serializer for workflow sessions with nested trace steps"""
    user = UserSerializer(read_only=True)
    trace_steps = TraceStepSerializer(many=True, read_only=True)
    duration_ms = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowSession
        fields = [
            'id', 'correlation_id', 'workflow_type', 'user', 'session_key',
            'start_time', 'end_time', 'status', 'duration_ms', 'metadata', 'trace_steps'
        ]
        read_only_fields = ['id', 'correlation_id']
    
    def get_duration_ms(self, obj):
        """Calculate workflow duration in milliseconds"""
        if obj.end_time and obj.start_time:
            delta = obj.end_time - obj.start_time
            return int(delta.total_seconds() * 1000)
        return None


class WorkflowSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workflow sessions"""
    class Meta:
        model = WorkflowSession
        fields = ['workflow_type', 'user', 'session_key', 'metadata']


class PerformanceSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for performance metrics"""
    is_warning = serializers.SerializerMethodField()
    is_critical = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceSnapshot
        fields = [
            'id', 'correlation_id', 'timestamp', 'layer', 'component',
            'metric_name', 'metric_value', 'threshold_warning', 'threshold_critical',
            'is_warning', 'is_critical', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_is_warning(self, obj):
        """Check if metric value exceeds warning threshold"""
        if obj.threshold_warning is not None:
            return obj.metric_value >= obj.threshold_warning
        return False
    
    def get_is_critical(self, obj):
        """Check if metric value exceeds critical threshold"""
        if obj.threshold_critical is not None:
            return obj.metric_value >= obj.threshold_critical
        return False


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for error logs"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'correlation_id', 'timestamp', 'layer', 'component', 'severity',
            'error_type', 'error_message', 'stack_trace', 'user', 'request_path',
            'request_method', 'user_agent', 'ip_address', 'resolved', 'resolution_notes', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class ErrorLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating error logs"""
    class Meta:
        model = ErrorLog
        fields = [
            'correlation_id', 'layer', 'component', 'severity', 'error_type',
            'error_message', 'stack_trace', 'user', 'request_path', 'request_method',
            'user_agent', 'ip_address', 'metadata'
        ]


class DebugConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for debug configuration"""
    class Meta:
        model = DebugConfiguration
        fields = [
            'id', 'name', 'config_type', 'enabled', 'config_data',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PerformanceThresholdSerializer(serializers.ModelSerializer):
    """Serializer for performance thresholds"""
    class Meta:
        model = PerformanceThreshold
        fields = [
            'id', 'metric_name', 'layer', 'component', 'warning_threshold',
            'critical_threshold', 'enabled', 'alert_on_warning', 'alert_on_critical',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health overview"""
    overall_status = serializers.CharField()
    active_workflows = serializers.IntegerField()
    recent_errors = serializers.IntegerField()
    performance_alerts = serializers.IntegerField()
    layers = serializers.DictField()
    timestamp = serializers.DateTimeField()


class WorkflowStatsSerializer(serializers.Serializer):
    """Serializer for workflow statistics"""
    total_workflows = serializers.IntegerField()
    completed_workflows = serializers.IntegerField()
    failed_workflows = serializers.IntegerField()
    average_duration_ms = serializers.FloatField()
    workflow_types = serializers.DictField()
    recent_activity = serializers.ListField()


class APICallDiscoverySerializer(serializers.ModelSerializer):
    """Serializer for discovered API calls"""
    class Meta:
        model = APICallDiscovery
        fields = [
            'id', 'method', 'endpoint', 'component_file', 'line_number',
            'function_name', 'requires_authentication', 'payload_schema',
            'headers', 'query_params', 'discovered_at', 'last_validated',
            'is_valid', 'validation_error'
        ]
        read_only_fields = ['id', 'discovered_at']


class FrontendRouteSerializer(serializers.ModelSerializer):
    """Serializer for frontend routes with nested API calls"""
    api_calls = APICallDiscoverySerializer(many=True, read_only=True)
    
    class Meta:
        model = FrontendRoute
        fields = [
            'id', 'path', 'route_type', 'component_path', 'component_name',
            'is_dynamic', 'dynamic_segments', 'metadata', 'discovered_at',
            'last_validated', 'is_valid', 'api_calls'
        ]
        read_only_fields = ['id', 'discovered_at']


class RouteDiscoverySessionSerializer(serializers.ModelSerializer):
    """Serializer for route discovery sessions"""
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = RouteDiscoverySession
        fields = [
            'id', 'session_id', 'start_time', 'end_time', 'status',
            'routes_discovered', 'api_calls_discovered', 'errors_encountered',
            'scan_duration_ms', 'duration_seconds', 'metadata', 'error_log'
        ]
        read_only_fields = ['id', 'session_id', 'start_time']
    
    def get_duration_seconds(self, obj):
        """Calculate session duration in seconds"""
        if obj.scan_duration_ms:
            return round(obj.scan_duration_ms / 1000, 2)
        return None


class RouteDependencySerializer(serializers.ModelSerializer):
    """Serializer for route dependencies"""
    frontend_route = FrontendRouteSerializer(read_only=True)
    api_call = APICallDiscoverySerializer(read_only=True)
    
    class Meta:
        model = RouteDependency
        fields = [
            'id', 'frontend_route', 'api_call', 'dependency_type',
            'is_critical', 'load_order', 'conditions', 'discovered_at'
        ]
        read_only_fields = ['id', 'discovered_at']


class RouteDiscoveryResultSerializer(serializers.Serializer):
    """Serializer for route discovery results"""
    routes = serializers.ListField(child=serializers.DictField())
    totalRoutes = serializers.IntegerField()
    apiCallsCount = serializers.IntegerField()
    lastScanned = serializers.CharField(allow_null=True)
    scanDuration = serializers.IntegerField()


class DependencyMapSerializer(serializers.Serializer):
    """Serializer for dependency mapping"""
    frontend_routes = FrontendRouteSerializer(many=True)
    api_endpoints = serializers.ListField(child=serializers.CharField())
    dependencies = serializers.ListField(child=serializers.DictField())


class RouteValidationResultSerializer(serializers.Serializer):
    """Serializer for route validation results"""
    totalRoutes = serializers.IntegerField()
    validRoutes = serializers.IntegerField()
    invalidRoutes = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())