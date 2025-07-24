"""
Admin interface for logs and monitoring.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SystemLog, BusinessMetric, PerformanceMetric, SecurityEvent


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    """
    Admin interface for SystemLog model.
    """
    list_display = ('created_at', 'level', 'source', 'event_type', 'short_message', 'user_id')
    list_filter = ('level', 'source', 'event_type', 'created_at')
    search_fields = ('message', 'logger_name', 'user_id', 'ip_address', 'request_path')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def short_message(self, obj):
        """
        Return a truncated version of the message.
        """
        if len(obj.message) > 100:
            return obj.message[:100] + '...'
        return obj.message
    
    short_message.short_description = 'Message'


@admin.register(BusinessMetric)
class BusinessMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for BusinessMetric model.
    """
    list_display = ('timestamp', 'name', 'value', 'dimensions_display')
    list_filter = ('name', 'timestamp')
    search_fields = ('name', 'dimensions')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def dimensions_display(self, obj):
        """
        Format the dimensions as a string.
        """
        if not obj.dimensions:
            return '-'
        
        return ', '.join(f"{k}: {v}" for k, v in obj.dimensions.items())
    
    dimensions_display.short_description = 'Dimensions'


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for PerformanceMetric model.
    """
    list_display = ('timestamp', 'name', 'value', 'endpoint', 'method', 'response_time')
    list_filter = ('name', 'method', 'timestamp')
    search_fields = ('name', 'endpoint')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityEvent model.
    """
    list_display = ('timestamp', 'event_type', 'username', 'ip_address', 'request_path', 'details_display')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('username', 'ip_address', 'request_path', 'user_agent')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def details_display(self, obj):
        """
        Format the details as a string.
        """
        if not obj.details:
            return '-'
        
        return ', '.join(f"{k}: {v}" for k, v in obj.details.items())
    
    details_display.short_description = 'Details'