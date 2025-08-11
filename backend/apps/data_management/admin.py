from django.contrib import admin
from .models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)


@admin.register(DataImportJob)
class DataImportJobAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'target_model', 'file_format', 'status',
        'progress_percentage', 'total_records', 'successful_records',
        'failed_records', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'file_format', 'target_model', 'created_at']
    search_fields = ['name', 'description', 'target_model']
    readonly_fields = [
        'id', 'file_size', 'status', 'progress_percentage',
        'total_records', 'processed_records', 'successful_records',
        'failed_records', 'error_log', 'validation_errors',
        'processing_log', 'created_at', 'started_at', 'completed_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_format', 'file_size')
        }),
        ('Target Configuration', {
            'fields': ('target_model', 'content_type')
        }),
        ('Processing Configuration', {
            'fields': (
                'mapping_config', 'validation_rules', 'transformation_rules',
                'skip_duplicates', 'update_existing', 'batch_size'
            )
        }),
        ('Status and Progress', {
            'fields': (
                'status', 'progress_percentage', 'total_records',
                'processed_records', 'successful_records', 'failed_records'
            )
        }),
        ('Logs and Errors', {
            'fields': ('error_log', 'validation_errors', 'processing_log'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DataExportJob)
class DataExportJobAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'source_model', 'export_format', 'status',
        'progress_percentage', 'total_records', 'exported_records',
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'export_format', 'source_model', 'created_at']
    search_fields = ['name', 'description', 'source_model']
    readonly_fields = [
        'id', 'file_path', 'file_size', 'status', 'progress_percentage',
        'total_records', 'exported_records', 'error_log', 'processing_log',
        'created_at', 'started_at', 'completed_at'
    ]


@admin.register(DataMapping)
class DataMappingAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'target_model', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['target_model', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'target_model']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DataSyncJob)
class DataSyncJobAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'target_model', 'frequency', 'status',
        'last_run_at', 'next_run_at', 'created_by'
    ]
    list_filter = ['status', 'frequency', 'target_model', 'created_at']
    search_fields = ['name', 'description', 'target_model']
    readonly_fields = [
        'id', 'last_run_at', 'next_run_at', 'last_run_status',
        'created_at', 'updated_at'
    ]


@admin.register(DataBackup)
class DataBackupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'backup_type', 'status', 'progress_percentage',
        'file_size', 'created_by', 'created_at'
    ]
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'id', 'backup_path', 'status', 'progress_percentage',
        'file_size', 'created_at', 'started_at', 'completed_at'
    ]


@admin.register(DataAuditLog)
class DataAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'action', 'user', 'content_type', 'object_id', 'timestamp'
    ]
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['user__username', 'object_id']
    readonly_fields = ['id', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DataQualityRule)
class DataQualityRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'rule_type', 'target_model', 'target_field',
        'severity', 'is_active', 'created_by'
    ]
    list_filter = ['rule_type', 'target_model', 'severity', 'is_active']
    search_fields = ['name', 'description', 'target_model', 'target_field']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DataLineage)
class DataLineageAdmin(admin.ModelAdmin):
    list_display = [
        'source_name', 'source_field', 'target_name', 'target_field',
        'transformation_type', 'is_active'
    ]
    list_filter = ['source_type', 'target_type', 'transformation_type', 'is_active']
    search_fields = ['source_name', 'target_name']
    readonly_fields = ['id', 'created_at', 'updated_at']