from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Project, Task, Milestone, ProjectRisk, TimeEntry, ProjectDocument,
    ProjectComment, ProjectNotification, ProjectTemplate, ProjectMembership,
    TaskDependency, ProjectStakeholder, ProjectChangeRequest, ProjectLessonsLearned,
    ProjectQualityMetrics, ProjectCapacityPlan, ProjectIntegration
)


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Template Data', {
            'fields': ('template_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    fields = ['user', 'role', 'hourly_rate', 'joined_at']
    readonly_fields = ['joined_at']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['title', 'status', 'priority', 'assignee', 'due_date', 'progress_percentage']
    readonly_fields = ['created_at']


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0
    fields = ['name', 'due_date', 'is_completed', 'completed_date']


class ProjectRiskInline(admin.TabularInline):
    model = ProjectRisk
    extra = 0
    fields = ['title', 'risk_level', 'probability', 'impact', 'status', 'owner']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'priority', 'project_manager', 'progress_percentage',
        'budget', 'actual_cost', 'start_date', 'end_date', 'is_overdue_display'
    ]
    list_filter = ['status', 'priority', 'start_date', 'end_date', 'created_at']
    search_fields = ['name', 'description', 'project_manager__username']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue', 'days_remaining']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'status', 'priority')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Budget & Progress', {
            'fields': ('budget', 'actual_cost', 'progress_percentage')
        }),
        ('Team', {
            'fields': ('project_manager',)
        }),
        ('Template', {
            'fields': ('template',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'custom_fields', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Computed Fields', {
            'fields': ('is_overdue', 'days_remaining'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProjectMembershipInline, TaskInline, MilestoneInline, ProjectRiskInline]
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue_display.short_description = 'Overdue'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'status', 'priority', 'assignee', 'due_date',
        'progress_percentage', 'estimated_hours', 'actual_hours', 'is_overdue_display'
    ]
    list_filter = ['status', 'priority', 'due_date', 'created_at', 'project']
    search_fields = ['title', 'description', 'project__name', 'assignee__username']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'parent_task', 'title', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        ('Assignment', {
            'fields': ('assignee', 'reviewer')
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Metadata', {
            'fields': ('tags', 'custom_fields', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue_display.short_description = 'Overdue'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'due_date', 'is_completed', 'completed_date']
    list_filter = ['is_completed', 'due_date', 'created_at']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProjectRisk)
class ProjectRiskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'risk_level', 'probability', 'impact', 'risk_score', 'status', 'owner']
    list_filter = ['risk_level', 'status', 'probability', 'impact']
    search_fields = ['title', 'description', 'project__name', 'owner__username']
    readonly_fields = ['risk_score', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'title', 'description', 'owner')
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'probability', 'impact', 'risk_score', 'status')
        }),
        ('Mitigation', {
            'fields': ('mitigation_plan', 'contingency_plan')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'date', 'hours', 'is_billable', 'created_at']
    list_filter = ['is_billable', 'date', 'created_at']
    search_fields = ['task__title', 'user__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('task', 'user', 'date', 'hours', 'is_billable')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'file_type', 'file_size', 'version', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['file_size', 'file_type', 'created_at', 'updated_at']


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'author', 'project', 'task', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username', 'project__name', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ProjectNotification)
class ProjectNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at']


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'hourly_rate', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['project__name', 'user__username']
    readonly_fields = ['joined_at']


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = ['predecessor', 'successor', 'dependency_type', 'lag_days']
    list_filter = ['dependency_type']
    search_fields = ['predecessor__title', 'successor__title']


@admin.register(ProjectStakeholder)
class ProjectStakeholderAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'role', 'organization', 'communication_frequency', 'influence_level', 'interest_level']
    list_filter = ['communication_frequency', 'preferred_method', 'influence_level', 'interest_level']
    search_fields = ['name', 'email', 'role', 'organization', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'name', 'email', 'role', 'organization')
        }),
        ('Communication', {
            'fields': ('communication_frequency', 'preferred_method', 'last_communication')
        }),
        ('Influence & Interest', {
            'fields': ('influence_level', 'interest_level')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectChangeRequest)
class ProjectChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'requested_by', 'status', 'timeline_impact_days', 'budget_impact', 'created_at']
    list_filter = ['status', 'scope_impact', 'resource_impact', 'risk_impact', 'created_at']
    search_fields = ['title', 'description', 'project__name', 'requested_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'title', 'description', 'justification', 'requested_by', 'status')
        }),
        ('Impact Assessment', {
            'fields': ('scope_impact', 'timeline_impact_days', 'budget_impact', 'resource_impact', 'risk_impact')
        }),
        ('Approval Workflow', {
            'fields': ('reviewed_by', 'approved_by', 'approval_date', 'implementation_date')
        }),
        ('Affected Items', {
            'fields': ('affected_tasks', 'affected_milestones'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectLessonsLearned)
class ProjectLessonsLearnedAdmin(admin.ModelAdmin):
    list_display = ['lesson_title', 'project', 'category', 'impact_level', 'created_by', 'created_at']
    list_filter = ['category', 'impact_level', 'created_at']
    search_fields = ['lesson_title', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'category', 'lesson_title', 'description', 'impact_level')
        }),
        ('Analysis', {
            'fields': ('what_worked_well', 'what_could_improve', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectQualityMetrics)
class ProjectQualityMetricsAdmin(admin.ModelAdmin):
    list_display = ['project', 'overall_quality_score', 'on_time_delivery_rate', 'budget_adherence_rate', 'last_calculated']
    list_filter = ['last_calculated']
    search_fields = ['project__name']
    readonly_fields = ['overall_quality_score', 'last_calculated']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'overall_quality_score')
        }),
        ('Quality Scores', {
            'fields': ('on_time_delivery_rate', 'budget_adherence_rate', 'scope_change_rate', 
                      'defect_rate', 'customer_satisfaction_score', 'team_satisfaction_score')
        }),
        ('Metrics Tracking', {
            'fields': ('total_deliverables', 'delivered_on_time', 'total_defects', 
                      'resolved_defects', 'scope_changes')
        }),
        ('Metadata', {
            'fields': ('last_calculated',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectCapacityPlan)
class ProjectCapacityPlanAdmin(admin.ModelAdmin):
    list_display = ['project', 'period_type', 'period_start', 'period_end', 'utilization_rate', 'created_by']
    list_filter = ['period_type', 'period_start', 'created_at']
    search_fields = ['project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'period_type', 'period_start', 'period_end')
        }),
        ('Capacity Metrics', {
            'fields': ('total_capacity_hours', 'allocated_hours', 'available_hours', 'utilization_rate')
        }),
        ('Resource Requirements', {
            'fields': ('required_developers', 'required_designers', 'required_testers', 'required_analysts')
        }),
        ('Analysis', {
            'fields': ('resource_gaps', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectIntegration)
class ProjectIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'integration_type', 'status', 'success_rate_display', 'last_sync', 'created_by']
    list_filter = ['integration_type', 'status', 'created_at']
    search_fields = ['name', 'project__name', 'description']
    readonly_fields = ['total_syncs', 'successful_syncs', 'failed_syncs', 'success_rate', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'integration_type', 'name', 'description', 'status')
        }),
        ('Configuration', {
            'fields': ('config_data', 'api_endpoint', 'webhook_url', 'sync_frequency_minutes'),
            'classes': ('collapse',)
        }),
        ('Monitoring', {
            'fields': ('last_sync', 'error_message')
        }),
        ('Statistics', {
            'fields': ('total_syncs', 'successful_syncs', 'failed_syncs', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color};">{rate:.1f}%</span>')
    success_rate_display.short_description = 'Success Rate'