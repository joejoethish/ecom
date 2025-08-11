from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
import json

from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)


class ComplianceAdminMixin:
    """Mixin for common compliance admin functionality"""
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Editing existing object
            readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            if hasattr(obj, 'created_by'):
                obj.created_by = request.user
        super().save_model(request, obj, form, change)


class StatusFilter(SimpleListFilter):
    """Generic status filter"""
    title = 'status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        if hasattr(model_admin.model, 'STATUS_CHOICES'):
            return model_admin.model.STATUS_CHOICES
        return []
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class SeverityFilter(SimpleListFilter):
    """Filter for incident severity"""
    title = 'severity'
    parameter_name = 'severity'
    
    def lookups(self, request, model_admin):
        return [
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(severity=self.value())
        return queryset


@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'name', 'framework_type', 'version', 'status', 
        'effective_date', 'policies_count', 'controls_count', 'created_at'
    ]
    list_filter = ['framework_type', StatusFilter, 'effective_date', 'created_at']
    search_fields = ['name', 'description', 'version']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'framework_type', 'description', 'version')
        }),
        ('Dates', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('Status & Requirements', {
            'fields': ('status', 'requirements')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def policies_count(self, obj):
        count = obj.policies.count()
        if count > 0:
            url = reverse('admin:compliance_compliancepolicy_changelist')
            return format_html(
                '<a href="{}?framework__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    policies_count.short_description = 'Policies'
    
    def controls_count(self, obj):
        count = obj.controls.count()
        if count > 0:
            url = reverse('admin:compliance_compliancecontrol_changelist')
            return format_html(
                '<a href="{}?framework__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    controls_count.short_description = 'Controls'


@admin.register(CompliancePolicy)
class CompliancePolicyAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'policy_type', 'framework', 'status', 'owner',
        'effective_date', 'review_date', 'created_at'
    ]
    list_filter = [
        'policy_type', StatusFilter, 'framework', 'effective_date', 'created_at'
    ]
    search_fields = ['title', 'description', 'content']
    readonly_fields = ['id', 'approved_at', 'created_at', 'updated_at']
    raw_id_fields = ['framework', 'owner', 'approver']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'policy_type', 'framework', 'description')
        }),
        ('Content', {
            'fields': ('content', 'version', 'tags', 'attachments')
        }),
        ('Dates', {
            'fields': ('effective_date', 'review_date')
        }),
        ('Approval', {
            'fields': ('status', 'owner', 'approver', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'framework', 'owner', 'approver'
        )


@admin.register(ComplianceControl)
class ComplianceControlAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'control_id', 'title', 'framework', 'control_type',
        'implementation_status', 'risk_level', 'owner', 'last_tested'
    ]
    list_filter = [
        'control_type', 'implementation_status', 'framework', 
        'risk_level', 'frequency', 'last_tested'
    ]
    search_fields = ['control_id', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['framework', 'policy', 'owner']
    fieldsets = (
        ('Basic Information', {
            'fields': ('control_id', 'title', 'framework', 'policy', 'description')
        }),
        ('Implementation', {
            'fields': (
                'control_type', 'implementation_status', 'risk_level',
                'owner', 'implementation_details'
            )
        }),
        ('Testing', {
            'fields': (
                'testing_procedures', 'evidence_requirements', 'frequency',
                'last_tested', 'next_test_date'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'framework', 'policy', 'owner'
        )


@admin.register(ComplianceAssessment)
class ComplianceAssessmentAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'assessment_type', 'framework', 'status',
        'assessor', 'start_date', 'end_date', 'overall_score'
    ]
    list_filter = [
        'assessment_type', StatusFilter, 'framework', 
        'risk_rating', 'start_date'
    ]
    search_fields = ['title', 'description', 'scope']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['framework', 'assessor']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'assessment_type', 'framework', 'description')
        }),
        ('Schedule', {
            'fields': ('status', 'assessor', 'start_date', 'end_date')
        }),
        ('Scope & Methodology', {
            'fields': ('scope', 'methodology')
        }),
        ('Results', {
            'fields': (
                'findings', 'recommendations', 'overall_score',
                'risk_rating', 'report_file'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ComplianceIncident)
class ComplianceIncidentAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'incident_id', 'title', 'incident_type', 'severity',
        'status', 'reported_by', 'assigned_to', 'occurred_at'
    ]
    list_filter = [
        'incident_type', SeverityFilter, StatusFilter, 'framework',
        'regulatory_notification_required', 'occurred_at'
    ]
    search_fields = ['incident_id', 'title', 'description']
    readonly_fields = [
        'id', 'incident_id', 'reported_by', 'reported_at', 
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['framework', 'assigned_to']
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'incident_id', 'title', 'framework', 'incident_type',
                'description', 'severity'
            )
        }),
        ('Assignment', {
            'fields': ('status', 'reported_by', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('occurred_at', 'reported_at', 'resolved_at')
        }),
        ('Analysis', {
            'fields': (
                'impact_assessment', 'root_cause', 'remediation_actions',
                'lessons_learned'
            )
        }),
        ('Regulatory', {
            'fields': (
                'regulatory_notification_required', 'regulatory_notification_sent',
                'notification_date'
            )
        }),
        ('Attachments', {
            'fields': ('attachments',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'framework', 'reported_by', 'assigned_to'
        )


@admin.register(ComplianceTraining)
class ComplianceTrainingAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'training_type', 'framework', 'status',
        'mandatory', 'duration_hours', 'records_count', 'created_at'
    ]
    list_filter = [
        'training_type', StatusFilter, 'framework', 'mandatory',
        'assessment_required', 'created_at'
    ]
    search_fields = ['title', 'description', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['framework', 'created_by']
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'training_type', 'framework', 'description',
                'content', 'duration_hours'
            )
        }),
        ('Configuration', {
            'fields': (
                'status', 'mandatory', 'target_audience', 'prerequisites',
                'learning_objectives', 'validity_period_months'
            )
        }),
        ('Assessment', {
            'fields': ('assessment_required', 'passing_score')
        }),
        ('Materials', {
            'fields': ('materials',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def records_count(self, obj):
        count = obj.records.count()
        if count > 0:
            url = reverse('admin:compliance_compliancetrainingrecord_changelist')
            return format_html(
                '<a href="{}?training__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    records_count.short_description = 'Records'


@admin.register(ComplianceTrainingRecord)
class ComplianceTrainingRecordAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'training', 'status', 'assigned_date',
        'due_date', 'completed_date', 'score', 'certificate_issued'
    ]
    list_filter = [
        'status', 'assigned_date', 'due_date', 'completed_date',
        'certificate_issued', 'training__framework'
    ]
    search_fields = ['user__username', 'user__email', 'training__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['training', 'user']
    fieldsets = (
        ('Assignment', {
            'fields': ('training', 'user', 'assigned_date', 'due_date')
        }),
        ('Progress', {
            'fields': (
                'status', 'started_date', 'completed_date',
                'score', 'attempts', 'time_spent_hours'
            )
        }),
        ('Certification', {
            'fields': ('certificate_issued', 'certificate_file')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('training', 'user')


@admin.register(ComplianceAuditTrail)
class ComplianceAuditTrailAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'action', 'model_name',
        'object_repr', 'ip_address'
    ]
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    readonly_fields = [
        'id', 'user', 'action', 'model_name', 'object_id',
        'object_repr', 'changes', 'ip_address', 'user_agent',
        'session_key', 'timestamp'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changes_display(self, obj):
        if obj.changes:
            return format_html('<pre>{}</pre>', json.dumps(obj.changes, indent=2))
        return '-'
    changes_display.short_description = 'Changes'
    
    fieldsets = (
        ('Action', {
            'fields': ('user', 'action', 'timestamp')
        }),
        ('Object', {
            'fields': ('model_name', 'object_id', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes_display',)
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'session_key')
        })
    )


@admin.register(ComplianceRiskAssessment)
class ComplianceRiskAssessmentAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'framework', 'risk_category', 'likelihood',
        'impact', 'inherent_risk_score', 'residual_risk_score',
        'status', 'risk_owner'
    ]
    list_filter = [
        'risk_category', 'likelihood', 'impact', 'status',
        'framework', 'review_date'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['framework', 'risk_owner']
    filter_horizontal = ['controls']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'framework', 'description', 'risk_category')
        }),
        ('Risk Assessment', {
            'fields': (
                'likelihood', 'impact', 'inherent_risk_score',
                'residual_risk_score', 'status'
            )
        }),
        ('Management', {
            'fields': ('risk_owner', 'mitigation_strategies', 'controls')
        }),
        ('Review', {
            'fields': ('review_date', 'last_reviewed')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ComplianceVendor)
class ComplianceVendorAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'name', 'vendor_type', 'risk_level', 'status',
        'contract_end_date', 'next_assessment_date', 'assessment_score'
    ]
    list_filter = [
        'vendor_type', 'risk_level', StatusFilter,
        'contract_start_date', 'next_assessment_date'
    ]
    search_fields = ['name', 'description', 'contact_person', 'contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'vendor_type', 'description', 'website'
            )
        }),
        ('Contact', {
            'fields': (
                'contact_person', 'contact_email', 'contact_phone', 'address'
            )
        }),
        ('Risk & Status', {
            'fields': ('risk_level', 'status', 'data_access_level')
        }),
        ('Contract', {
            'fields': ('contract_start_date', 'contract_end_date', 'services_provided')
        }),
        ('Compliance', {
            'fields': (
                'compliance_requirements', 'certifications',
                'last_assessment_date', 'next_assessment_date', 'assessment_score'
            )
        }),
        ('Documentation', {
            'fields': ('documents', 'notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ComplianceReport)
class ComplianceReportAdmin(ComplianceAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'framework', 'status',
        'generated_by', 'generated_at', 'scheduled'
    ]
    list_filter = [
        'report_type', StatusFilter, 'framework', 'scheduled',
        'schedule_frequency', 'generated_at'
    ]
    search_fields = ['title', 'description']
    readonly_fields = [
        'id', 'generated_by', 'generated_at', 'file_path',
        'file_size', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['framework']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'report_type', 'framework', 'description')
        }),
        ('Parameters', {
            'fields': ('parameters',)
        }),
        ('Generation', {
            'fields': (
                'status', 'generated_by', 'generated_at',
                'file_path', 'file_size'
            )
        }),
        ('Scheduling', {
            'fields': (
                'scheduled', 'schedule_frequency', 'next_run', 'recipients'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# Admin site customization
admin.site.site_header = 'Compliance Management System'
admin.site.site_title = 'Compliance Admin'
admin.site.index_title = 'Compliance Administration'

# Custom admin actions
def activate_selected(modeladmin, request, queryset):
    """Activate selected objects"""
    updated = queryset.update(status='active')
    modeladmin.message_user(
        request, f'{updated} items were successfully activated.'
    )
activate_selected.short_description = 'Activate selected items'

def deactivate_selected(modeladmin, request, queryset):
    """Deactivate selected objects"""
    updated = queryset.update(status='inactive')
    modeladmin.message_user(
        request, f'{updated} items were successfully deactivated.'
    )
deactivate_selected.short_description = 'Deactivate selected items'

# Add actions to relevant admin classes
ComplianceFrameworkAdmin.actions = [activate_selected, deactivate_selected]
CompliancePolicyAdmin.actions = [activate_selected, deactivate_selected]
ComplianceTrainingAdmin.actions = [activate_selected, deactivate_selected]