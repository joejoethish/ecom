from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)


class DataImportJobSerializer(serializers.ModelSerializer):
    """Serializer for data import jobs"""
    
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DataImportJob
        fields = [
            'id', 'name', 'description', 'file_path', 'file_format', 'file_size',
            'target_model', 'content_type', 'content_type_name', 'mapping_config',
            'validation_rules', 'transformation_rules', 'status', 'progress_percentage',
            'total_records', 'processed_records', 'successful_records', 'failed_records',
            'error_log', 'validation_errors', 'processing_log', 'created_by',
            'created_by_name', 'created_at', 'started_at', 'completed_at',
            'skip_duplicates', 'update_existing', 'batch_size', 'duration'
        ]
        read_only_fields = [
            'id', 'status', 'progress_percentage', 'total_records', 'processed_records',
            'successful_records', 'failed_records', 'error_log', 'validation_errors',
            'processing_log', 'created_by', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class DataExportJobSerializer(serializers.ModelSerializer):
    """Serializer for data export jobs"""
    
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DataExportJob
        fields = [
            'id', 'name', 'description', 'source_model', 'content_type',
            'content_type_name', 'export_format', 'field_mapping', 'filter_criteria',
            'sort_criteria', 'file_path', 'file_size', 'status', 'progress_percentage',
            'total_records', 'exported_records', 'error_log', 'processing_log',
            'created_by', 'created_by_name', 'created_at', 'started_at',
            'completed_at', 'expires_at', 'include_headers', 'compress_output',
            'encrypt_output', 'duration'
        ]
        read_only_fields = [
            'id', 'file_path', 'file_size', 'status', 'progress_percentage',
            'total_records', 'exported_records', 'error_log', 'processing_log',
            'created_by', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class DataMappingSerializer(serializers.ModelSerializer):
    """Serializer for data mappings"""
    
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataMapping
        fields = [
            'id', 'name', 'description', 'target_model', 'content_type',
            'content_type_name', 'field_mappings', 'default_values',
            'transformation_rules', 'validation_rules', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DataSyncJobSerializer(serializers.ModelSerializer):
    """Serializer for data sync jobs"""
    
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataSyncJob
        fields = [
            'id', 'name', 'description', 'source_type', 'source_config',
            'target_model', 'content_type', 'content_type_name', 'frequency',
            'schedule_config', 'mapping_config', 'sync_mode', 'status',
            'last_run_at', 'next_run_at', 'last_run_status', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_run_at', 'next_run_at', 'last_run_status',
            'created_by', 'created_at', 'updated_at'
        ]


class DataBackupSerializer(serializers.ModelSerializer):
    """Serializer for data backups"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DataBackup
        fields = [
            'id', 'name', 'description', 'backup_type', 'models_to_backup',
            'backup_path', 'status', 'progress_percentage', 'file_size',
            'created_by', 'created_by_name', 'created_at', 'started_at',
            'completed_at', 'compress_backup', 'encrypt_backup',
            'retention_days', 'duration'
        ]
        read_only_fields = [
            'id', 'backup_path', 'status', 'progress_percentage', 'file_size',
            'created_by', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class DataAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for data audit logs"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = DataAuditLog
        fields = [
            'id', 'action', 'operation_id', 'content_type', 'content_type_name',
            'object_id', 'changes', 'old_values', 'new_values', 'user',
            'user_name', 'timestamp', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'timestamp']


class DataQualityRuleSerializer(serializers.ModelSerializer):
    """Serializer for data quality rules"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataQualityRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'target_model',
            'target_field', 'rule_config', 'is_active', 'severity',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DataLineageSerializer(serializers.ModelSerializer):
    """Serializer for data lineage"""
    
    class Meta:
        model = DataLineage
        fields = [
            'id', 'source_type', 'source_name', 'source_field',
            'target_type', 'target_name', 'target_field',
            'transformation_type', 'transformation_config',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ImportJobCreateSerializer(serializers.Serializer):
    """Serializer for creating import jobs"""
    
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    target_model = serializers.CharField(max_length=100)
    file_format = serializers.ChoiceField(choices=DataImportJob.FORMAT_CHOICES)
    mapping_config = serializers.JSONField(default=dict)
    validation_rules = serializers.JSONField(default=dict)
    transformation_rules = serializers.JSONField(default=dict)
    skip_duplicates = serializers.BooleanField(default=True)
    update_existing = serializers.BooleanField(default=False)
    batch_size = serializers.IntegerField(default=1000, min_value=1, max_value=10000)


class ExportJobCreateSerializer(serializers.Serializer):
    """Serializer for creating export jobs"""
    
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    source_model = serializers.CharField(max_length=100)
    export_format = serializers.ChoiceField(choices=DataExportJob.FORMAT_CHOICES)
    field_mapping = serializers.JSONField(default=dict)
    filter_criteria = serializers.JSONField(default=dict)
    sort_criteria = serializers.JSONField(default=list)
    include_headers = serializers.BooleanField(default=True)
    compress_output = serializers.BooleanField(default=False)
    encrypt_output = serializers.BooleanField(default=False)


class DataValidationResultSerializer(serializers.Serializer):
    """Serializer for data validation results"""
    
    is_valid = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.DictField())
    warnings = serializers.ListField(child=serializers.DictField())
    total_records = serializers.IntegerField()
    valid_records = serializers.IntegerField()
    invalid_records = serializers.IntegerField()


class DataTransformationSerializer(serializers.Serializer):
    """Serializer for data transformation configuration"""
    
    field_name = serializers.CharField()
    transformation_type = serializers.ChoiceField(choices=[
        ('uppercase', 'Uppercase'),
        ('lowercase', 'Lowercase'),
        ('trim', 'Trim Whitespace'),
        ('format_date', 'Format Date'),
        ('format_number', 'Format Number'),
        ('replace', 'Replace Text'),
        ('custom', 'Custom Function'),
    ])
    parameters = serializers.JSONField(default=dict)


class BulkOperationSerializer(serializers.Serializer):
    """Serializer for bulk operations"""
    
    operation = serializers.ChoiceField(choices=[
        ('delete', 'Delete'),
        ('cancel', 'Cancel'),
        ('retry', 'Retry'),
        ('archive', 'Archive'),
    ])
    job_ids = serializers.ListField(child=serializers.UUIDField())