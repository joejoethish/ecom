"""
Django admin configuration for chart models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .chart_models import (
    ChartTemplate, Chart, ChartVersion, ChartAnnotation,
    ChartComment, ChartShare, ChartPerformanceMetric,
    ChartDataCache, ChartExport
)

@admin.register(ChartTemplate)
class ChartTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'chart_type', 'category', 'is_public', 
        'created_by', 'created_at'
    ]
    list_filter = [
        'chart_type', 'category', 'is_public', 'created_at'
    ]
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'chart_type', 'category')
        }),
        ('Configuration', {
            'fields': ('data_source', 'config', 'is_public')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly_fields.append('created_by')
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Chart)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'chart_type', 'status', 'is_real_time', 
        'access_count', 'created_by', 'updated_at'
    ]
    list_filter = [
        'chart_type', 'status', 'is_real_time', 'theme', 
        'created_at', 'updated_at'
    ]
    search_fields = ['title', 'description']
    readonly_fields = [
        'id', 'access_count', 'last_accessed', 
        'created_at', 'updated_at'
    ]
    filter_horizontal = ['allowed_users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'chart_type', 'template')
        }),
        ('Data Configuration', {
            'fields': ('data_source', 'config', 'refresh_interval')
        }),
        ('Styling', {
            'fields': ('theme', 'colors', 'custom_css')
        }),
        ('Access Control', {
            'fields': ('is_public', 'allowed_users', 'allowed_roles', 'status')
        }),
        ('Real-time Settings', {
            'fields': ('is_real_time',)
        }),
        ('Statistics', {
            'fields': ('access_count', 'last_accessed'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly_fields.append('created_by')
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def view_chart_link(self, obj):
        if obj.pk:
            url = reverse('admin:chart-preview', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">View Chart</a>', url)
        return '-'
    view_chart_link.short_description = 'Preview'

@admin.register(ChartVersion)
class ChartVersionAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'version_number', 'title', 
        'created_by', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['chart__title', 'title', 'changes_summary']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Version Information', {
            'fields': ('chart', 'version_number', 'title')
        }),
        ('Changes', {
            'fields': ('changes_summary', 'config')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly_fields.extend(['chart', 'version_number', 'created_by'])
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChartAnnotation)
class ChartAnnotationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'chart', 'annotation_type', 
        'is_visible', 'created_by', 'created_at'
    ]
    list_filter = ['annotation_type', 'is_visible', 'created_at']
    search_fields = ['title', 'content', 'chart__title']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Annotation Details', {
            'fields': ('chart', 'annotation_type', 'title', 'content')
        }),
        ('Position & Style', {
            'fields': ('position', 'style', 'is_visible')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChartComment)
class ChartCommentAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'content_preview', 'is_resolved', 
        'created_by', 'created_at'
    ]
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['content', 'chart__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('chart', 'parent', 'content')
        }),
        ('Position & Status', {
            'fields': ('position', 'is_resolved')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChartShare)
class ChartShareAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'share_type', 'share_token_preview', 
        'is_active', 'access_count', 'expires_at', 'created_at'
    ]
    list_filter = ['share_type', 'is_active', 'created_at', 'expires_at']
    search_fields = ['chart__title', 'share_token']
    readonly_fields = ['id', 'share_token', 'access_count', 'created_at']
    
    fieldsets = (
        ('Share Details', {
            'fields': ('chart', 'share_type', 'share_token')
        }),
        ('Configuration', {
            'fields': ('expires_at', 'is_active', 'settings')
        }),
        ('Statistics', {
            'fields': ('access_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def share_token_preview(self, obj):
        return f"{obj.share_token[:8]}..." if obj.share_token else '-'
    share_token_preview.short_description = 'Token'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChartPerformanceMetric)
class ChartPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'load_time', 'data_size', 'render_time', 
        'ip_address', 'timestamp'
    ]
    list_filter = ['timestamp']
    search_fields = ['chart__title', 'ip_address']
    readonly_fields = ['id', 'timestamp']
    
    fieldsets = (
        ('Performance Data', {
            'fields': ('chart', 'load_time', 'data_size', 'render_time')
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Performance metrics are auto-generated
    
    def has_change_permission(self, request, obj=None):
        return False  # Performance metrics are read-only

@admin.register(ChartDataCache)
class ChartDataCacheAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'cache_key_preview', 'expires_at', 'created_at'
    ]
    list_filter = ['expires_at', 'created_at']
    search_fields = ['chart__title', 'cache_key']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Cache Details', {
            'fields': ('chart', 'cache_key', 'expires_at')
        }),
        ('Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cache_key_preview(self, obj):
        return f"{obj.cache_key[:20]}..." if len(obj.cache_key) > 20 else obj.cache_key
    cache_key_preview.short_description = 'Cache Key'
    
    def has_add_permission(self, request):
        return False  # Cache entries are auto-generated

@admin.register(ChartExport)
class ChartExportAdmin(admin.ModelAdmin):
    list_display = [
        'chart', 'export_format', 'file_size_mb', 
        'created_by', 'created_at'
    ]
    list_filter = ['export_format', 'created_at']
    search_fields = ['chart__title', 'file_path']
    readonly_fields = ['id', 'file_path', 'file_size', 'created_at']
    
    fieldsets = (
        ('Export Details', {
            'fields': ('chart', 'export_format', 'export_settings')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return '-'
    file_size_mb.short_description = 'File Size'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Custom admin views for chart management
class ChartAdminMixin:
    """Mixin for chart-related admin functionality."""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Filter to only show charts the user has access to
            qs = qs.filter(
                models.Q(is_public=True) |
                models.Q(created_by=request.user) |
                models.Q(allowed_users=request.user)
            ).distinct()
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "chart":
            # Filter charts based on user permissions
            if not request.user.is_superuser:
                kwargs["queryset"] = Chart.objects.filter(
                    models.Q(is_public=True) |
                    models.Q(created_by=request.user) |
                    models.Q(allowed_users=request.user)
                ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Apply mixin to relevant admin classes
ChartAnnotationAdmin.__bases__ = (ChartAdminMixin,) + ChartAnnotationAdmin.__bases__
ChartCommentAdmin.__bases__ = (ChartAdminMixin,) + ChartCommentAdmin.__bases__
ChartShareAdmin.__bases__ = (ChartAdminMixin,) + ChartShareAdmin.__bases__
ChartExportAdmin.__bases__ = (ChartAdminMixin,) + ChartExportAdmin.__bases__