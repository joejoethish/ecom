from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Tenant, TenantUser, TenantSubscription, TenantUsage,
    TenantInvitation, TenantAuditLog, TenantBackup
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'subdomain', 'plan', 'status', 'users_count',
        'created_at', 'is_active'
    ]
    list_filter = ['plan', 'status', 'is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'users_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subdomain', 'domain', 'is_active')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color', 'favicon'),
            'classes': ('collapse',)
        }),
        ('Subscription', {
            'fields': ('plan', 'status', 'trial_ends_at', 'subscription_starts_at', 'subscription_ends_at')
        }),
        ('Limits', {
            'fields': ('max_users', 'max_products', 'max_orders', 'max_storage_gb'),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email', 'contact_phone'),
            'classes': ('collapse',)
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('timezone', 'currency', 'language', 'features', 'custom_settings'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'users_count'),
            'classes': ('collapse',)
        }),
    )
    
    def users_count(self, obj):
        count = obj.users.count()
        url = reverse('admin:tenants_tenantuser_changelist') + f'?tenant__id__exact={obj.id}'
        return format_html('<a href="{}">{} users</a>', url, count)
    users_count.short_description = 'Users'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('users')


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'email', 'tenant_name', 'role',
        'is_active', 'last_login', 'date_joined'
    ]
    list_filter = ['role', 'is_active', 'tenant', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'last_login', 'date_joined', 'last_login_ip']
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'is_active')
        }),
        ('Tenant & Role', {
            'fields': ('tenant', 'role', 'permissions')
        }),
        ('Profile', {
            'fields': ('phone', 'avatar', 'department', 'job_title'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('last_login', 'last_login_ip', 'failed_login_attempts', 'account_locked_until'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        ('Invitation', {
            'fields': ('invited_at', 'invited_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'


@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'tenant_name', 'plan_name', 'billing_cycle', 'amount',
        'payment_status', 'next_billing_date'
    ]
    list_filter = ['billing_cycle', 'payment_status', 'created_at']
    search_fields = ['tenant__name', 'plan_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('tenant', 'plan_name', 'billing_cycle', 'amount', 'currency')
        }),
        ('Billing', {
            'fields': ('next_billing_date', 'last_billing_date', 'payment_method', 'payment_status')
        }),
        ('External IDs', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'


@admin.register(TenantUsage)
class TenantUsageAdmin(admin.ModelAdmin):
    list_display = [
        'tenant_name', 'period_start', 'users_count', 'storage_used_gb',
        'api_calls_count', 'avg_response_time'
    ]
    list_filter = ['period_start', 'tenant']
    search_fields = ['tenant__name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Period', {
            'fields': ('tenant', 'period_start', 'period_end')
        }),
        ('Usage Metrics', {
            'fields': ('users_count', 'products_count', 'orders_count', 'storage_used_gb', 'api_calls_count')
        }),
        ('Performance Metrics', {
            'fields': ('avg_response_time', 'error_rate', 'uptime_percentage'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'tenant_name', 'role', 'status',
        'invited_by_name', 'created_at', 'expires_at'
    ]
    list_filter = ['role', 'status', 'created_at', 'expires_at']
    search_fields = ['email', 'tenant__name']
    readonly_fields = ['id', 'token', 'created_at', 'accepted_at']
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('tenant', 'email', 'role', 'status')
        }),
        ('Inviter', {
            'fields': ('invited_by',)
        }),
        ('Token & Expiration', {
            'fields': ('token', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'
    
    def invited_by_name(self, obj):
        return obj.invited_by.get_full_name() or obj.invited_by.username
    invited_by_name.short_description = 'Invited By'


@admin.register(TenantAuditLog)
class TenantAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'tenant_name', 'user_name', 'action', 'model_name',
        'object_repr', 'timestamp'
    ]
    list_filter = ['action', 'model_name', 'timestamp', 'tenant']
    search_fields = ['tenant__name', 'user__username', 'object_repr']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('tenant', 'user', 'action', 'model_name', 'object_id', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'
    
    def user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return '-'
    user_name.short_description = 'User'


@admin.register(TenantBackup)
class TenantBackupAdmin(admin.ModelAdmin):
    list_display = [
        'tenant_name', 'backup_type', 'status', 'file_size_mb',
        'progress_percentage', 'created_at', 'completed_at'
    ]
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['tenant__name']
    readonly_fields = ['id', 'file_size_mb', 'created_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Backup Details', {
            'fields': ('tenant', 'backup_type', 'status', 'progress_percentage')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'file_size_mb'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return '-'
    file_size_mb.short_description = 'File Size'