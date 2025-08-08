"""
Django admin configuration for admin panel models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    AdminUser, AdminRole, AdminPermission, SystemSettings,
    ActivityLog, AdminSession, AdminNotification, AdminLoginAttempt,
    AdminReport
)


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
    """Admin configuration for AdminUser model."""
    list_display = [
        'username', 'email', 'role', 'department', 'is_admin_active',
        'last_login', 'failed_login_attempts', 'account_status'
    ]
    list_filter = [
        'role', 'department', 'is_admin_active', 'two_factor_enabled',
        'created_at', 'last_login'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'last_login_ip', 'failed_login_attempts', 'account_locked_until',
        'password_changed_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('Admin info', {'fields': ('role', 'department', 'notes')}),
        ('Permissions', {'fields': ('is_admin_active', 'is_staff', 'is_superuser', 'permissions')}),
        ('Security', {'fields': (
            'two_factor_enabled', 'max_concurrent_sessions', 'session_timeout_minutes',
            'failed_login_attempts', 'account_locked_until', 'password_changed_at',
            'must_change_password'
        )}),
        ('Important dates', {'fields': ('last_login', 'last_login_ip', 'created_at', 'updated_at')}),
    )
    
    filter_horizontal = ['permissions']
    
    def account_status(self, obj):
        """Display account status with color coding."""
        if obj.is_account_locked:
            return format_html(
                '<span style="color: red;">🔒 Locked until {}</span>',
                obj.account_locked_until.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.is_admin_active:
            return format_html('<span style="color: green;">✅ Active</span>')
        else:
            return format_html('<span style="color: orange;">⏸️ Inactive</span>')
    account_status.short_description = 'Status'


@admin.register(AdminRole)
class AdminRoleAdmin(admin.ModelAdmin):
    """Admin configuration for AdminRole model."""
    list_display = ['display_name', 'name', 'level', 'parent_role', 'is_active', 'permission_count']
    list_filter = ['level', 'is_active', 'is_system_role']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['level', 'name']
    filter_horizontal = ['permissions']
    
    def permission_count(self, obj):
        """Display number of permissions."""
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'


@admin.register(AdminPermission)
class AdminPermissionAdmin(admin.ModelAdmin):
    """Admin configuration for AdminPermission model."""
    list_display = [
        'codename', 'name', 'module', 'action', 'resource',
        'is_sensitive', 'requires_mfa', 'is_active'
    ]
    list_filter = [
        'module', 'action', 'is_sensitive', 'requires_mfa',
        'ip_restricted', 'is_active', 'is_system_permission'
    ]
    search_fields = ['codename', 'name', 'description']
    ordering = ['module', 'action', 'resource']
    filter_horizontal = ['depends_on']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for SystemSettings model."""
    list_display = [
        'key', 'name', 'category', 'setting_type',
        'is_public', 'is_encrypted', 'last_modified_by', 'updated_at'
    ]
    list_filter = [
        'category', 'setting_type', 'is_public', 'is_encrypted',
        'requires_restart', 'is_system_setting'
    ]
    search_fields = ['key', 'name', 'description']
    ordering = ['category', 'key']
    readonly_fields = ['version', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """Set last_modified_by when saving."""
        if hasattr(request.user, 'role'):  # Check if it's an AdminUser
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin configuration for ActivityLog model."""
    list_display = [
        'created_at', 'admin_user', 'action', 'description',
        'module', 'severity', 'is_successful', 'ip_address'
    ]
    list_filter = [
        'action', 'module', 'severity', 'is_successful',
        'created_at', 'content_type'
    ]
    search_fields = [
        'description', 'admin_user__username', 'ip_address',
        'user_agent', 'request_path'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'admin_user', 'session_key', 'action', 'description',
        'content_type', 'object_id', 'changes', 'additional_data',
        'ip_address', 'user_agent', 'request_method', 'request_path',
        'module', 'severity', 'is_successful', 'error_message',
        'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        """Disable adding activity logs manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing activity logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting activity logs."""
        return False


@admin.register(AdminSession)
class AdminSessionAdmin(admin.ModelAdmin):
    """Admin configuration for AdminSession model."""
    list_display = [
        'admin_user', 'ip_address', 'device_type', 'location',
        'is_active', 'is_suspicious', 'security_score', 'last_activity'
    ]
    list_filter = [
        'is_active', 'is_suspicious', 'is_trusted_device',
        'device_type', 'country', 'created_at'
    ]
    search_fields = [
        'admin_user__username', 'ip_address', 'user_agent',
        'location', 'country', 'city'
    ]
    ordering = ['-last_activity']
    readonly_fields = [
        'session_key', 'admin_user', 'ip_address', 'user_agent',
        'device_type', 'browser', 'os', 'location', 'country', 'city',
        'security_score', 'created_at', 'updated_at', 'last_activity'
    ]
    
    def has_add_permission(self, request):
        """Disable adding sessions manually."""
        return False


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    """Admin configuration for AdminNotification model."""
    list_display = [
        'title', 'recipient', 'notification_type', 'priority',
        'is_read', 'created_at', 'scheduled_for'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_dismissed',
        'created_at', 'scheduled_for'
    ]
    search_fields = ['title', 'message', 'recipient__username']
    ordering = ['-created_at']
    readonly_fields = ['read_at', 'dismissed_at', 'created_at', 'updated_at']


@admin.register(AdminLoginAttempt)
class AdminLoginAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for AdminLoginAttempt model."""
    list_display = [
        'created_at', 'username', 'admin_user', 'ip_address',
        'is_successful', 'is_suspicious', 'risk_score', 'country'
    ]
    list_filter = [
        'is_successful', 'is_suspicious', 'failure_reason',
        'country', 'created_at'
    ]
    search_fields = [
        'username', 'admin_user__username', 'ip_address',
        'user_agent', 'country', 'city'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'username', 'admin_user', 'ip_address', 'user_agent',
        'is_successful', 'failure_reason', 'is_suspicious',
        'risk_score', 'country', 'city', 'metadata',
        'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        """Disable adding login attempts manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing login attempts."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting login attempts."""
        return False


@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
    """Admin configuration for AdminReport model."""
    list_display = [
        'name', 'report_type', 'schedule_type', 'is_active',
        'next_run', 'last_run', 'total_runs', 'created_by'
    ]
    list_filter = [
        'report_type', 'schedule_type', 'format', 'is_active',
        'created_at', 'next_run'
    ]
    search_fields = ['name', 'description', 'created_by__username']
    ordering = ['name']
    filter_horizontal = ['recipients']
    readonly_fields = [
        'total_runs', 'successful_runs', 'last_error',
        'created_at', 'updated_at'
    ]
    
    def save_model(self, request, obj, form, change):
        """Set created_by when saving."""
        if not change and hasattr(request.user, 'role'):  # Check if it's an AdminUser
            obj.created_by = request.user
        super().save_model(request, obj, form, change)