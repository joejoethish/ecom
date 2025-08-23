from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold
)


@admin.register(WorkflowSession)
class WorkflowSessionAdmin(admin.ModelAdmin):
    list_display = [
        'correlation_id', 'workflow_type', 'user', 'status', 
        'start_time', 'end_time', 'duration_display'
    ]
    list_filter = ['workflow_type', 'status', 'start_time']
    search_fields = ['correlation_id', 'workflow_type', 'user__username']
    readonly_fields = ['correlation_id', 'start_time', 'duration_display']
    date_hierarchy = 'start_time'
    
    def duration_display(self, obj):
        if obj.end_time and obj.start_time:
            delta = obj.end_time - obj.start_time
            return f"{int(delta.total_seconds() * 1000)}ms"
        return "In Progress"
    duration_display.short_description = "Duration"


class TraceStepInline(admin.TabularInline):
    model = TraceStep
    extra = 0
    readonly_fields = ['start_time', 'end_time', 'duration_ms']


@admin.register(TraceStep)
class TraceStepAdmin(admin.ModelAdmin):
    list_display = [
        'workflow_session', 'layer', 'component', 'operation', 
        'status', 'start_time', 'duration_ms'
    ]
    list_filter = ['layer', 'component', 'status', 'start_time']
    search_fields = ['component', 'operation', 'workflow_session__correlation_id']
    readonly_fields = ['start_time', 'end_time']
    date_hierarchy = 'start_time'


@admin.register(PerformanceSnapshot)
class PerformanceSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'layer', 'component', 'metric_name', 
        'metric_value', 'threshold_status', 'correlation_id'
    ]
    list_filter = ['layer', 'component', 'metric_name', 'timestamp']
    search_fields = ['component', 'correlation_id']
    readonly_fields = ['timestamp', 'threshold_status']
    date_hierarchy = 'timestamp'
    
    def threshold_status(self, obj):
        if obj.threshold_critical and obj.metric_value >= obj.threshold_critical:
            return format_html('<span style="color: red;">Critical</span>')
        elif obj.threshold_warning and obj.metric_value >= obj.threshold_warning:
            return format_html('<span style="color: orange;">Warning</span>')
        return format_html('<span style="color: green;">Normal</span>')
    threshold_status.short_description = "Status"


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'layer', 'component', 'severity', 'error_type', 
        'user', 'resolved', 'correlation_id'
    ]
    list_filter = ['layer', 'component', 'severity', 'resolved', 'timestamp']
    search_fields = ['error_type', 'error_message', 'component', 'correlation_id']
    readonly_fields = ['timestamp', 'stack_trace_display']
    date_hierarchy = 'timestamp'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def stack_trace_display(self, obj):
        if obj.stack_trace:
            return format_html('<pre>{}</pre>', obj.stack_trace[:1000])
        return "No stack trace"
    stack_trace_display.short_description = "Stack Trace"
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)
        self.message_user(request, f"{queryset.count()} errors marked as resolved.")
    mark_resolved.short_description = "Mark selected errors as resolved"
    
    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False)
        self.message_user(request, f"{queryset.count()} errors marked as unresolved.")
    mark_unresolved.short_description = "Mark selected errors as unresolved"


@admin.register(DebugConfiguration)
class DebugConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'config_type', 'enabled', 'created_at', 'updated_at']
    list_filter = ['config_type', 'enabled', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PerformanceThreshold)
class PerformanceThresholdAdmin(admin.ModelAdmin):
    list_display = [
        'metric_name', 'layer', 'component', 'warning_threshold', 
        'critical_threshold', 'enabled', 'updated_at'
    ]
    list_filter = ['metric_name', 'layer', 'enabled', 'updated_at']
    search_fields = ['metric_name', 'layer', 'component']
    readonly_fields = ['created_at', 'updated_at']
