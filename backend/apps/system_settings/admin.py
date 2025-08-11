from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingNotification, SettingAuditLog,
    SettingEnvironmentSync
)


@admin.register(SettingCategory)
class SettingCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'parent', 'order', 'is_active', 'settings_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['order', 'name']
    list_editable = ['order', 'is_active']
    
    def settings_count(self, obj):
        return obj.settings.filter(is_active=True).count()
    settings_count.short_description = 'Active Settings'


class SettingDependencyInline(admin.TabularInline):
    model = SettingDependency
    fk_name = 'setting'
    extra = 0


class SettingNotificationInline(admin.TabularInline):
    model = SettingNotification
    extra = 0


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = [
        'key', 'display_name', 'category', 'data_type', 'environment',
        'is_active', 'is_sensitive', 'requires_restart', 'version', 'last_changed'
    ]
    list_filter = [
        'category', 'data_type', 'environment', 'is_active', 'is_sensitive',
        'requires_restart', 'access_level'
    ]
    search_fields = ['key', 'display_name', 'description']
    readonly_fields = [
        'version', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'typed_value_display', 'validation_status', 'change_history_link'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'display_name', 'description', 'category')
        }),
        ('Value and Type', {
            'fields': ('data_type', 'value', 'default_value', 'typed_value_display')
        }),
        ('Validation Rules', {
            'fields': (
                'min_value', 'max_value', 'min_length', 'max_length',
                'regex_pattern', 'allowed_values', 'validation_status'
            ),
            'classes': ['collapse']
        }),
        ('Security and Access', {
            'fields': ('is_encrypted', 'access_level', 'allowed_roles', 'is_sensitive')
        }),
        ('Metadata', {
            'fields': (
                'is_active', 'is_required', 'requires_restart', 'environment',
                'help_text', 'documentation_url'
            )
        }),
        ('Versioning and Tracking', {
            'fields': (
                'version', 'created_at', 'updated_at', 'created_by', 'updated_by',
                'change_history_link'
            ),
            'classes': ['collapse']
        })
    )
    inlines = [SettingDependencyInline, SettingNotificationInline]
    
    def typed_value_display(self, obj):
        try:
            typed_value = obj.get_typed_value()
            return format_html('<code>{}</code>', typed_value)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    typed_value_display.short_description = 'Typed Value'
    
    def validation_status(self, obj):
        try:
            obj.clean()
            return format_html('<span style="color: green;">✓ Valid</span>')
        except Exception as e:
            return format_html('<span style="color: red;">✗ {}</span>', str(e))
    validation_status.short_description = 'Validation'
    
    def change_history_link(self, obj):
        if obj.pk:
            url = reverse('admin:system_settings_settingchangehistory_changelist')
            return format_html(
                '<a href="{}?setting__id__exact={}">View History ({})</a>',
                url, obj.pk, obj.change_history.count()
            )
        return '-'
    change_history_link.short_description = 'Change History'
    
    def last_changed(self, obj):
        last_change = obj.change_history.first()
        if last_change:
            return last_change.changed_at
        return obj.updated_at
    last_changed.short_description = 'Last Changed'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SettingChangeHistory)
class SettingChangeHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'setting', 'version', 'changed_by', 'changed_at',
        'approval_status', 'approved_by', 'value_preview'
    ]
    list_filter = [
        'approval_status', 'requires_approval', 'changed_at',
        'setting__category', 'setting__environment'
    ]
    search_fields = ['setting__key', 'setting__display_name', 'change_reason']
    readonly_fields = [
        'setting', 'old_value', 'new_value', 'version', 'changed_by',
        'changed_at', 'ip_address', 'user_agent'
    ]
    date_hierarchy = 'changed_at'
    
    def value_preview(self, obj):
        old_preview = (obj.old_value[:50] + '...') if len(obj.old_value) > 50 else obj.old_value
        new_preview = (obj.new_value[:50] + '...') if len(obj.new_value) > 50 else obj.new_value
        return format_html(
            '<div><strong>Old:</strong> <code>{}</code></div>'
            '<div><strong>New:</strong> <code>{}</code></div>',
            old_preview, new_preview
        )
    value_preview.short_description = 'Value Changes'
    
    def has_add_permission(self, request):
        return False  # Changes should only be created through the service


@admin.register(SettingBackup)
class SettingBackupAdmin(admin.ModelAdmin):
    list_display = ['name', 'environment', 'backup_type', 'created_by', 'created_at', 'settings_count']
    list_filter = ['environment', 'backup_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['backup_data', 'created_by', 'created_at', 'settings_count']
    date_hierarchy = 'created_at'
    
    def settings_count(self, obj):
        return len(obj.backup_data.get('settings', []))
    settings_count.short_description = 'Settings Count'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SettingTemplate)
class SettingTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_public', 'created_by', 'usage_count', 'created_at']
    list_filter = ['is_public', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['template_data', 'created_by', 'usage_count', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SettingDependency)
class SettingDependencyAdmin(admin.ModelAdmin):
    list_display = ['setting', 'depends_on', 'dependency_type']
    list_filter = ['dependency_type']
    search_fields = ['setting__key', 'depends_on__key']


@admin.register(SettingNotification)
class SettingNotificationAdmin(admin.ModelAdmin):
    list_display = ['setting', 'notification_type', 'is_active', 'recipients_count']
    list_filter = ['notification_type', 'is_active']
    search_fields = ['setting__key', 'setting__display_name']
    
    def recipients_count(self, obj):
        return len(obj.recipients) if obj.recipients else 0
    recipients_count.short_description = 'Recipients'


@admin.register(SettingAuditLog)
class SettingAuditLogAdmin(admin.ModelAdmin):
    list_display = ['setting', 'action', 'user', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp', 'setting__category', 'setting__environment']
    search_fields = ['setting__key', 'user__username']
    readonly_fields = [
        'setting', 'action', 'user', 'timestamp', 'ip_address',
        'user_agent', 'details', 'compliance_flags'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Audit logs should only be created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should be immutable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs


@admin.register(SettingEnvironmentSync)
class SettingEnvironmentSyncAdmin(admin.ModelAdmin):
    list_display = [
        'setting', 'source_environment', 'target_environment',
        'sync_status', 'last_sync_at'
    ]
    list_filter = ['sync_status', 'source_environment', 'target_environment']
    search_fields = ['setting__key']
    readonly_fields = ['last_sync_at', 'sync_details']