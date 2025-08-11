from django.contrib import admin
from .models import (
    SecurityThreat, SecurityIncident, SecurityAudit, SecurityPolicy,
    SecurityVulnerability, SecurityTraining, SecurityTrainingRecord,
    SecurityRiskAssessment, SecurityMonitoringRule, SecurityAlert,
    SecurityConfiguration
)


@admin.register(SecurityThreat)
class SecurityThreatAdmin(admin.ModelAdmin):
    list_display = ['threat_type', 'severity', 'status', 'source_ip', 'detected_at', 'assigned_to']
    list_filter = ['severity', 'status', 'detection_method', 'detected_at']
    search_fields = ['threat_type', 'description', 'source_ip', 'target_resource']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('threat_type', 'severity', 'status', 'description')
        }),
        ('Technical Details', {
            'fields': ('source_ip', 'target_resource', 'detection_method', 'threat_indicators')
        }),
        ('Response', {
            'fields': ('mitigation_actions', 'assigned_to', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('detected_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ['incident_number', 'title', 'incident_type', 'severity', 'status', 'occurred_at', 'reported_by']
    list_filter = ['incident_type', 'severity', 'status', 'occurred_at']
    search_fields = ['incident_number', 'title', 'description']
    readonly_fields = ['id', 'incident_number', 'created_at', 'updated_at']
    date_hierarchy = 'occurred_at'
    filter_horizontal = ['assigned_team']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('incident_number', 'title', 'incident_type', 'severity', 'status')
        }),
        ('Details', {
            'fields': ('description', 'impact_assessment', 'affected_systems', 'affected_users')
        }),
        ('Response', {
            'fields': ('timeline', 'response_actions', 'lessons_learned', 'assigned_team')
        }),
        ('Timestamps', {
            'fields': ('occurred_at', 'detected_at', 'resolved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityVulnerability)
class SecurityVulnerabilityAdmin(admin.ModelAdmin):
    list_display = ['vulnerability_id', 'title', 'severity', 'status', 'cvss_score', 'discovered_date', 'assigned_to']
    list_filter = ['severity', 'status', 'exploit_available', 'patch_available', 'discovered_date']
    search_fields = ['vulnerability_id', 'title', 'description', 'cve_id']
    readonly_fields = ['id', 'vulnerability_id', 'created_at', 'updated_at']
    date_hierarchy = 'discovered_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vulnerability_id', 'title', 'description', 'severity', 'status')
        }),
        ('Technical Details', {
            'fields': ('cvss_score', 'cve_id', 'affected_systems', 'affected_components')
        }),
        ('Risk Assessment', {
            'fields': ('exploit_available', 'patch_available', 'remediation_steps', 'workaround')
        }),
        ('Management', {
            'fields': ('assigned_to', 'due_date', 'resolved_date')
        }),
        ('Timestamps', {
            'fields': ('discovered_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityAudit)
class SecurityAuditAdmin(admin.ModelAdmin):
    list_display = ['audit_name', 'audit_type', 'status', 'scheduled_date', 'auditor']
    list_filter = ['audit_type', 'status', 'scheduled_date']
    search_fields = ['audit_name', 'scope', 'methodology']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('audit_name', 'audit_type', 'status', 'auditor')
        }),
        ('Planning', {
            'fields': ('scope', 'objectives', 'methodology', 'compliance_frameworks')
        }),
        ('Results', {
            'fields': ('findings', 'recommendations', 'report_path')
        }),
        ('Timestamps', {
            'fields': ('scheduled_date', 'completed_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_name', 'policy_type', 'version', 'status', 'effective_date', 'owner']
    list_filter = ['policy_type', 'status', 'effective_date']
    search_fields = ['policy_name', 'description', 'policy_content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('policy_name', 'policy_type', 'version', 'status', 'description')
        }),
        ('Content', {
            'fields': ('policy_content', 'compliance_requirements', 'enforcement_rules', 'exceptions')
        }),
        ('Management', {
            'fields': ('owner', 'approver', 'effective_date', 'review_date', 'expiry_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityTraining)
class SecurityTrainingAdmin(admin.ModelAdmin):
    list_display = ['training_name', 'training_type', 'status', 'duration_minutes', 'created_by']
    list_filter = ['training_type', 'status', 'created_at']
    search_fields = ['training_name', 'description', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('training_name', 'training_type', 'status', 'description')
        }),
        ('Content', {
            'fields': ('content', 'duration_minutes', 'completion_criteria')
        }),
        ('Requirements', {
            'fields': ('required_for_roles', 'certificate_template')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityTrainingRecord)
class SecurityTrainingRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'training', 'status', 'score', 'attempts', 'completed_at']
    list_filter = ['status', 'certificate_issued', 'completed_at']
    search_fields = ['user__username', 'training__training_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'completed_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'training', 'status')
        }),
        ('Progress', {
            'fields': ('score', 'attempts', 'started_at', 'completed_at', 'expires_at')
        }),
        ('Certification', {
            'fields': ('certificate_issued',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityRiskAssessment)
class SecurityRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_name', 'asset_category', 'risk_level', 'risk_score', 'status', 'assessor']
    list_filter = ['risk_level', 'status', 'assessment_date']
    search_fields = ['assessment_name', 'asset_description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'assessment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('assessment_name', 'asset_category', 'asset_description', 'status')
        }),
        ('Risk Analysis', {
            'fields': ('threat_sources', 'vulnerabilities', 'existing_controls')
        }),
        ('Risk Calculation', {
            'fields': ('likelihood', 'impact', 'risk_level', 'risk_score')
        }),
        ('Recommendations', {
            'fields': ('recommended_controls', 'residual_risk')
        }),
        ('Management', {
            'fields': ('assessor', 'assessment_date', 'review_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityMonitoringRule)
class SecurityMonitoringRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'rule_type', 'status', 'severity', 'trigger_count', 'last_triggered']
    list_filter = ['rule_type', 'status', 'severity', 'created_at']
    search_fields = ['rule_name', 'description', 'rule_logic']
    readonly_fields = ['id', 'trigger_count', 'last_triggered', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('rule_name', 'rule_type', 'status', 'description')
        }),
        ('Rule Configuration', {
            'fields': ('rule_logic', 'conditions', 'actions', 'severity')
        }),
        ('Performance', {
            'fields': ('false_positive_rate', 'trigger_count', 'last_triggered')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'severity', 'status', 'source_system', 'created_at', 'assigned_to']
    list_filter = ['alert_type', 'severity', 'status', 'source_system', 'created_at']
    search_fields = ['title', 'description', 'source_system']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'alert_type', 'severity', 'status', 'description')
        }),
        ('Source', {
            'fields': ('source_system', 'rule', 'event_data')
        }),
        ('Management', {
            'fields': ('assigned_to', 'acknowledged_by', 'acknowledged_at', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SecurityConfiguration)
class SecurityConfigurationAdmin(admin.ModelAdmin):
    list_display = ['config_name', 'config_type', 'status', 'validation_status', 'last_validated', 'managed_by']
    list_filter = ['config_type', 'status', 'validation_status', 'created_at']
    search_fields = ['config_name', 'description']
    readonly_fields = ['id', 'last_validated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('config_name', 'config_type', 'status', 'description')
        }),
        ('Configuration', {
            'fields': ('configuration_data', 'baseline_config', 'compliance_requirements')
        }),
        ('Validation', {
            'fields': ('validation_status', 'validation_errors', 'last_validated')
        }),
        ('Management', {
            'fields': ('managed_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )