"""
Chart serializers for API responses
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .chart_models import (
    ChartTemplate, Chart, ChartVersion, ChartAnnotation, 
    ChartComment, ChartShare, ChartPerformanceMetric, 
    ChartDataCache, ChartExport
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for chart-related models"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class ChartTemplateSerializer(serializers.ModelSerializer):
    """Chart template serializer"""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChartTemplate
        fields = [
            'id', 'name', 'description', 'chart_type', 'category',
            'config', 'data_source', 'is_public', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class ChartVersionSerializer(serializers.ModelSerializer):
    """Chart version serializer"""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChartVersion
        fields = [
            'id', 'version_number', 'title', 'config', 'changes_summary',
            'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

class ChartAnnotationSerializer(serializers.ModelSerializer):
    """Chart annotation serializer"""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChartAnnotation
        fields = [
            'id', 'annotation_type', 'title', 'content', 'position',
            'style', 'is_visible', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

class ChartCommentSerializer(serializers.ModelSerializer):
    """Chart comment serializer"""
    created_by = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ChartComment
        fields = [
            'id', 'parent', 'content', 'position', 'is_resolved',
            'created_by', 'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.chartcomment_set.all()
            return ChartCommentSerializer(replies, many=True).data
        return []

class ChartShareSerializer(serializers.ModelSerializer):
    """Chart share serializer"""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChartShare
        fields = [
            'id', 'share_type', 'share_token', 'expires_at', 'is_active',
            'access_count', 'settings', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'share_token', 'access_count', 'created_by', 'created_at']

class ChartPerformanceMetricSerializer(serializers.ModelSerializer):
    """Chart performance metric serializer"""
    class Meta:
        model = ChartPerformanceMetric
        fields = [
            'id', 'load_time', 'data_size', 'render_time',
            'user_agent', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class ChartExportSerializer(serializers.ModelSerializer):
    """Chart export serializer"""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChartExport
        fields = [
            'id', 'export_format', 'file_path', 'file_size',
            'export_settings', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'file_path', 'file_size', 'created_by', 'created_at']

class ChartSerializer(serializers.ModelSerializer):
    """Main chart serializer"""
    created_by = UserBasicSerializer(read_only=True)
    template = ChartTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True, required=False)
    annotations = ChartAnnotationSerializer(many=True, read_only=True)
    comments = ChartCommentSerializer(many=True, read_only=True)
    shares = ChartShareSerializer(many=True, read_only=True)
    versions = ChartVersionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chart
        fields = [
            'id', 'title', 'description', 'chart_type', 'template', 'template_id',
            'config', 'data_source', 'refresh_interval', 'theme', 'colors',
            'custom_css', 'is_public', 'allowed_users', 'allowed_roles',
            'status', 'is_real_time', 'created_by', 'created_at', 'updated_at',
            'last_accessed', 'access_count', 'annotations', 'comments',
            'shares', 'versions'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 
            'last_accessed', 'access_count'
        ]
    
    def create(self, validated_data):
        template_id = validated_data.pop('template_id', None)
        if template_id:
            try:
                template = ChartTemplate.objects.get(id=template_id)
                validated_data['template'] = template
                # Initialize config from template if not provided
                if not validated_data.get('config'):
                    validated_data['config'] = template.config
                if not validated_data.get('data_source'):
                    validated_data['data_source'] = template.data_source
            except ChartTemplate.DoesNotExist:
                pass
        
        return super().create(validated_data)

class ChartListSerializer(serializers.ModelSerializer):
    """Simplified chart serializer for list views"""
    created_by = UserBasicSerializer(read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Chart
        fields = [
            'id', 'title', 'chart_type', 'template_name', 'status',
            'is_real_time', 'created_by', 'created_at', 'updated_at',
            'access_count'
        ]

class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data responses"""
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())
    metadata = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField(read_only=True)
    cache_info = serializers.DictField(required=False)

class ChartConfigSerializer(serializers.Serializer):
    """Serializer for chart configuration"""
    type = serializers.CharField()
    data = serializers.DictField()
    options = serializers.DictField()
    plugins = serializers.DictField(required=False)

class ChartExportRequestSerializer(serializers.Serializer):
    """Serializer for chart export requests"""
    format = serializers.ChoiceField(choices=ChartExport.EXPORT_FORMATS)
    width = serializers.IntegerField(default=800)
    height = serializers.IntegerField(default=600)
    quality = serializers.FloatField(default=1.0, min_value=0.1, max_value=1.0)
    background_color = serializers.CharField(default='white')
    include_data = serializers.BooleanField(default=False)
    
class ChartFilterSerializer(serializers.Serializer):
    """Serializer for chart data filtering"""
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    filters = serializers.DictField(required=False)
    group_by = serializers.CharField(required=False)
    aggregation = serializers.ChoiceField(
        choices=['sum', 'avg', 'count', 'min', 'max'],
        required=False
    )

class ChartDrillDownSerializer(serializers.Serializer):
    """Serializer for chart drill-down requests"""
    dimension = serializers.CharField()
    value = serializers.CharField()
    level = serializers.IntegerField(default=1)
    filters = serializers.DictField(required=False)