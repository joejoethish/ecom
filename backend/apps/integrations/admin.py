from django.contrib import admin
from .models import (
    IntegrationCategory, IntegrationProvider, Integration,
    IntegrationLog, IntegrationMapping, IntegrationWebhook,
    IntegrationSync, IntegrationTemplate
)


@admin.register(IntegrationCategory)
class IntegrationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(IntegrationProvider)
class IntegrationProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'is_popular', 'created_at']
    list_filter = ['category', 'status', 'is_popular']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'status', 'environment', 'created_by', 'created_at']
    list_filter = ['status', 'environment', 'provider__category', 'auto_sync']
    search_fields = ['name', 'provider__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_sync_at', 'error_count']
    raw_id_fields = ['provider', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider', 'status', 'environment')
        }),
        ('Configuration', {
            'fields': ('configuration', 'webhook_url', 'webhook_secret'),
            'classes': ('collapse',)
        }),
        ('Authentication', {
            'fields': ('api_key', 'api_secret', 'access_token', 'refresh_token', 'token_expires_at'),
            'classes': ('collapse',)
        }),
        ('Sync Settings', {
            'fields': ('auto_sync', 'sync_frequency', 'last_sync_at')
        }),
        ('Error Tracking', {
            'fields': ('error_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ['integration', 'level', 'action_type', 'message', 'created_at']
    list_filter = ['level', 'action_type', 'created_at']
    search_fields = ['integration__name', 'message']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['integration']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(IntegrationMapping)
class IntegrationMappingAdmin(admin.ModelAdmin):
    list_display = ['integration', 'mapping_type', 'source_field', 'target_field', 'is_required']
    list_filter = ['mapping_type', 'is_required']
    search_fields = ['integration__name', 'source_field', 'target_field']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['integration']


@admin.register(IntegrationWebhook)
class IntegrationWebhookAdmin(admin.ModelAdmin):
    list_display = ['integration', 'event_type', 'is_active', 'success_count', 'failure_count']
    list_filter = ['event_type', 'is_active']
    search_fields = ['integration__name', 'event_type']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_triggered_at', 'success_count', 'failure_count']
    raw_id_fields = ['integration']


@admin.register(IntegrationSync)
class IntegrationSyncAdmin(admin.ModelAdmin):
    list_display = ['integration', 'sync_type', 'status', 'records_processed', 'created_at']
    list_filter = ['sync_type', 'status', 'created_at']
    search_fields = ['integration__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['integration', 'created_by']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(IntegrationTemplate)
class IntegrationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'is_official', 'usage_count', 'rating', 'created_at']
    list_filter = ['is_official', 'provider__category']
    search_fields = ['name', 'description', 'provider__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'usage_count']
    raw_id_fields = ['provider', 'created_by']