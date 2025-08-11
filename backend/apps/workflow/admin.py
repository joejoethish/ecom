from django.contrib import admin
from .models import (
    WorkflowTemplate, Workflow, WorkflowNode, WorkflowConnection,
    WorkflowExecution, WorkflowExecutionLog, WorkflowApproval,
    WorkflowSchedule, WorkflowMetrics, WorkflowIntegration
)

@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'version', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_active', 'is_system_template']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'trigger_type', 'created_by', 'created_at']
    list_filter = ['status', 'trigger_type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WorkflowNode)
class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow', 'node_type', 'node_id']
    list_filter = ['node_type']
    search_fields = ['name', 'workflow__name']

@admin.register(WorkflowConnection)
class WorkflowConnectionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'source_node', 'target_node', 'label']
    list_filter = ['workflow']

@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'status', 'triggered_by', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['workflow__name']
    readonly_fields = ['created_at']

@admin.register(WorkflowExecutionLog)
class WorkflowExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['execution', 'level', 'message', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['message']

@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    list_display = ['execution', 'approver', 'status', 'requested_at', 'responded_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['execution__workflow__name', 'approver__username']

@admin.register(WorkflowSchedule)
class WorkflowScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow', 'frequency', 'is_active', 'next_run']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'workflow__name']

@admin.register(WorkflowMetrics)
class WorkflowMetricsAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'date', 'executions_count', 'successful_executions', 'failed_executions']
    list_filter = ['date']
    search_fields = ['workflow__name']

@admin.register(WorkflowIntegration)
class WorkflowIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['integration_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at']