import django_filters
from django.db import models
from django.contrib.auth import get_user_model
from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)

User = get_user_model()


class ComplianceFrameworkFilter(django_filters.FilterSet):
    """Filter for Compliance Framework"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    framework_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceFramework.FRAMEWORK_TYPES
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceFramework.STATUS_CHOICES
    )
    effective_date = django_filters.DateFromToRangeFilter()
    expiry_date = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    created_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    has_policies = django_filters.BooleanFilter(method='filter_has_policies')
    has_controls = django_filters.BooleanFilter(method='filter_has_controls')
    
    class Meta:
        model = ComplianceFramework
        fields = [
            'name', 'framework_type', 'status', 'effective_date',
            'expiry_date', 'created_at', 'created_by'
        ]
    
    def filter_has_policies(self, queryset, name, value):
        if value:
            return queryset.filter(policies__isnull=False).distinct()
        return queryset.filter(policies__isnull=True)
    
    def filter_has_controls(self, queryset, name, value):
        if value:
            return queryset.filter(controls__isnull=False).distinct()
        return queryset.filter(controls__isnull=True)


class CompliancePolicyFilter(django_filters.FilterSet):
    """Filter for Compliance Policy"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    policy_type = django_filters.MultipleChoiceFilter(
        choices=CompliancePolicy.POLICY_TYPES
    )
    status = django_filters.MultipleChoiceFilter(
        choices=CompliancePolicy.STATUS_CHOICES
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    framework_type = django_filters.CharFilter(
        field_name='framework__framework_type'
    )
    owner = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    approver = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    effective_date = django_filters.DateFromToRangeFilter()
    review_date = django_filters.DateFromToRangeFilter()
    approved_at = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    tags = django_filters.CharFilter(method='filter_tags')
    needs_review = django_filters.BooleanFilter(method='filter_needs_review')
    
    class Meta:
        model = CompliancePolicy
        fields = [
            'title', 'policy_type', 'status', 'framework', 'owner',
            'approver', 'effective_date', 'review_date', 'created_at'
        ]
    
    def filter_tags(self, queryset, name, value):
        return queryset.filter(tags__icontains=value)
    
    def filter_needs_review(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(review_date__lte=timezone.now().date())
        return queryset.exclude(review_date__lte=timezone.now().date())


class ComplianceControlFilter(django_filters.FilterSet):
    """Filter for Compliance Control"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    control_id = django_filters.CharFilter(lookup_expr='icontains')
    control_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceControl.CONTROL_TYPES
    )
    implementation_status = django_filters.MultipleChoiceFilter(
        choices=ComplianceControl.IMPLEMENTATION_STATUS
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    policy = django_filters.ModelChoiceFilter(
        queryset=CompliancePolicy.objects.all()
    )
    owner = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    risk_level = django_filters.RangeFilter()
    frequency = django_filters.CharFilter(lookup_expr='icontains')
    last_tested = django_filters.DateFromToRangeFilter()
    next_test_date = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    overdue_testing = django_filters.BooleanFilter(method='filter_overdue_testing')
    
    class Meta:
        model = ComplianceControl
        fields = [
            'title', 'control_id', 'control_type', 'implementation_status',
            'framework', 'policy', 'owner', 'risk_level', 'frequency'
        ]
    
    def filter_overdue_testing(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(next_test_date__lt=timezone.now().date())
        return queryset.exclude(next_test_date__lt=timezone.now().date())


class ComplianceAssessmentFilter(django_filters.FilterSet):
    """Filter for Compliance Assessment"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    assessment_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceAssessment.ASSESSMENT_TYPES
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceAssessment.STATUS_CHOICES
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    assessor = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()
    overall_score = django_filters.RangeFilter()
    risk_rating = django_filters.MultipleChoiceFilter(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    created_at = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = ComplianceAssessment
        fields = [
            'title', 'assessment_type', 'status', 'framework',
            'assessor', 'start_date', 'end_date', 'risk_rating'
        ]


class ComplianceIncidentFilter(django_filters.FilterSet):
    """Filter for Compliance Incident"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    incident_id = django_filters.CharFilter(lookup_expr='icontains')
    incident_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceIncident.INCIDENT_TYPES
    )
    severity = django_filters.MultipleChoiceFilter(
        choices=ComplianceIncident.SEVERITY_LEVELS
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceIncident.STATUS_CHOICES
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    reported_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    assigned_to = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    occurred_at = django_filters.DateFromToRangeFilter()
    reported_at = django_filters.DateFromToRangeFilter()
    resolved_at = django_filters.DateFromToRangeFilter()
    regulatory_notification_required = django_filters.BooleanFilter()
    regulatory_notification_sent = django_filters.BooleanFilter()
    created_at = django_filters.DateFromToRangeFilter()
    open_incidents = django_filters.BooleanFilter(method='filter_open_incidents')
    overdue_incidents = django_filters.BooleanFilter(method='filter_overdue_incidents')
    
    class Meta:
        model = ComplianceIncident
        fields = [
            'title', 'incident_id', 'incident_type', 'severity', 'status',
            'framework', 'reported_by', 'assigned_to', 'occurred_at'
        ]
    
    def filter_open_incidents(self, queryset, name, value):
        if value:
            return queryset.exclude(status__in=['resolved', 'closed'])
        return queryset.filter(status__in=['resolved', 'closed'])
    
    def filter_overdue_incidents(self, queryset, name, value):
        from django.utils import timezone
        from datetime import timedelta
        
        if value:
            # Consider incidents overdue if open for more than 30 days
            overdue_date = timezone.now() - timedelta(days=30)
            return queryset.filter(
                reported_at__lt=overdue_date,
                status__in=['reported', 'investigating', 'contained']
            )
        return queryset


class ComplianceTrainingFilter(django_filters.FilterSet):
    """Filter for Compliance Training"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    training_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceTraining.TRAINING_TYPES
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceTraining.STATUS_CHOICES
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    mandatory = django_filters.BooleanFilter()
    assessment_required = django_filters.BooleanFilter()
    created_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    duration_hours = django_filters.RangeFilter()
    validity_period_months = django_filters.RangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    target_audience = django_filters.CharFilter(method='filter_target_audience')
    
    class Meta:
        model = ComplianceTraining
        fields = [
            'title', 'training_type', 'status', 'framework', 'mandatory',
            'assessment_required', 'created_by', 'duration_hours'
        ]
    
    def filter_target_audience(self, queryset, name, value):
        return queryset.filter(target_audience__icontains=value)


class ComplianceTrainingRecordFilter(django_filters.FilterSet):
    """Filter for Compliance Training Record"""
    training = django_filters.ModelChoiceFilter(
        queryset=ComplianceTraining.objects.all()
    )
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceTrainingRecord.STATUS_CHOICES
    )
    assigned_date = django_filters.DateFromToRangeFilter()
    started_date = django_filters.DateFromToRangeFilter()
    completed_date = django_filters.DateFromToRangeFilter()
    due_date = django_filters.DateFromToRangeFilter()
    score = django_filters.RangeFilter()
    certificate_issued = django_filters.BooleanFilter()
    created_at = django_filters.DateFromToRangeFilter()
    overdue_training = django_filters.BooleanFilter(method='filter_overdue_training')
    
    class Meta:
        model = ComplianceTrainingRecord
        fields = [
            'training', 'user', 'status', 'assigned_date',
            'due_date', 'certificate_issued'
        ]
    
    def filter_overdue_training(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                due_date__lt=timezone.now().date(),
                status__in=['not_started', 'in_progress']
            )
        return queryset


class ComplianceAuditTrailFilter(django_filters.FilterSet):
    """Filter for Compliance Audit Trail"""
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    action = django_filters.MultipleChoiceFilter(
        choices=ComplianceAuditTrail.ACTION_TYPES
    )
    model_name = django_filters.CharFilter(lookup_expr='icontains')
    object_id = django_filters.CharFilter(lookup_expr='exact')
    object_repr = django_filters.CharFilter(lookup_expr='icontains')
    ip_address = django_filters.CharFilter(lookup_expr='exact')
    timestamp = django_filters.DateFromToRangeFilter()
    session_key = django_filters.CharFilter(lookup_expr='exact')
    
    class Meta:
        model = ComplianceAuditTrail
        fields = [
            'user', 'action', 'model_name', 'object_id',
            'ip_address', 'timestamp'
        ]


class ComplianceRiskAssessmentFilter(django_filters.FilterSet):
    """Filter for Compliance Risk Assessment"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    risk_category = django_filters.MultipleChoiceFilter(
        choices=ComplianceRiskAssessment.RISK_CATEGORIES
    )
    likelihood = django_filters.MultipleChoiceFilter(
        choices=ComplianceRiskAssessment.LIKELIHOOD_LEVELS
    )
    impact = django_filters.MultipleChoiceFilter(
        choices=ComplianceRiskAssessment.IMPACT_LEVELS
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    risk_owner = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    inherent_risk_score = django_filters.RangeFilter()
    residual_risk_score = django_filters.RangeFilter()
    status = django_filters.MultipleChoiceFilter(choices=[
        ('identified', 'Identified'),
        ('assessed', 'Assessed'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Accepted'),
        ('transferred', 'Transferred'),
        ('avoided', 'Avoided'),
    ])
    review_date = django_filters.DateFromToRangeFilter()
    last_reviewed = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    high_risk = django_filters.BooleanFilter(method='filter_high_risk')
    overdue_review = django_filters.BooleanFilter(method='filter_overdue_review')
    
    class Meta:
        model = ComplianceRiskAssessment
        fields = [
            'title', 'risk_category', 'likelihood', 'impact',
            'framework', 'risk_owner', 'status', 'review_date'
        ]
    
    def filter_high_risk(self, queryset, name, value):
        if value:
            return queryset.filter(inherent_risk_score__gte=15)
        return queryset.filter(inherent_risk_score__lt=15)
    
    def filter_overdue_review(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(review_date__lt=timezone.now().date())
        return queryset.exclude(review_date__lt=timezone.now().date())


class ComplianceVendorFilter(django_filters.FilterSet):
    """Filter for Compliance Vendor"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    vendor_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceVendor.VENDOR_TYPES
    )
    risk_level = django_filters.MultipleChoiceFilter(
        choices=ComplianceVendor.RISK_LEVELS
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceVendor.STATUS_CHOICES
    )
    contact_email = django_filters.CharFilter(lookup_expr='icontains')
    contract_start_date = django_filters.DateFromToRangeFilter()
    contract_end_date = django_filters.DateFromToRangeFilter()
    last_assessment_date = django_filters.DateFromToRangeFilter()
    next_assessment_date = django_filters.DateFromToRangeFilter()
    assessment_score = django_filters.RangeFilter()
    data_access_level = django_filters.CharFilter(lookup_expr='icontains')
    created_at = django_filters.DateFromToRangeFilter()
    assessment_due = django_filters.BooleanFilter(method='filter_assessment_due')
    contract_expiring = django_filters.BooleanFilter(method='filter_contract_expiring')
    
    class Meta:
        model = ComplianceVendor
        fields = [
            'name', 'vendor_type', 'risk_level', 'status',
            'contract_start_date', 'contract_end_date'
        ]
    
    def filter_assessment_due(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(next_assessment_date__lte=timezone.now().date())
        return queryset.exclude(next_assessment_date__lte=timezone.now().date())
    
    def filter_contract_expiring(self, queryset, name, value):
        from django.utils import timezone
        from datetime import timedelta
        
        if value:
            # Consider contracts expiring within 90 days
            expiry_threshold = timezone.now().date() + timedelta(days=90)
            return queryset.filter(contract_end_date__lte=expiry_threshold)
        return queryset


class ComplianceReportFilter(django_filters.FilterSet):
    """Filter for Compliance Report"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    report_type = django_filters.MultipleChoiceFilter(
        choices=ComplianceReport.REPORT_TYPES
    )
    status = django_filters.MultipleChoiceFilter(
        choices=ComplianceReport.STATUS_CHOICES
    )
    framework = django_filters.ModelChoiceFilter(
        queryset=ComplianceFramework.objects.all()
    )
    generated_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    generated_at = django_filters.DateFromToRangeFilter()
    scheduled = django_filters.BooleanFilter()
    schedule_frequency = django_filters.CharFilter(lookup_expr='exact')
    next_run = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = ComplianceReport
        fields = [
            'title', 'report_type', 'status', 'framework',
            'generated_by', 'scheduled', 'schedule_frequency'
        ]


# Custom filter for date ranges with predefined options
class DateRangeFilter(django_filters.Filter):
    """Custom filter for common date ranges"""
    
    def filter(self, qs, value):
        if not value:
            return qs
        
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        if value == 'today':
            start_date = now.date()
            end_date = start_date
        elif value == 'yesterday':
            start_date = (now - timedelta(days=1)).date()
            end_date = start_date
        elif value == 'this_week':
            start_date = (now - timedelta(days=now.weekday())).date()
            end_date = now.date()
        elif value == 'last_week':
            start_date = (now - timedelta(days=now.weekday() + 7)).date()
            end_date = (now - timedelta(days=now.weekday() + 1)).date()
        elif value == 'this_month':
            start_date = now.replace(day=1).date()
            end_date = now.date()
        elif value == 'last_month':
            last_month = now.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1).date()
            end_date = last_month.date()
        elif value == 'this_quarter':
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1).date()
            end_date = now.date()
        elif value == 'this_year':
            start_date = now.replace(month=1, day=1).date()
            end_date = now.date()
        else:
            return qs
        
        return qs.filter(**{
            f'{self.field_name}__date__gte': start_date,
            f'{self.field_name}__date__lte': end_date
        })


# Advanced search filter
class ComplianceAdvancedSearchFilter(django_filters.FilterSet):
    """Advanced search across multiple compliance models"""
    search_term = django_filters.CharFilter(method='filter_search_term')
    search_models = django_filters.MultipleChoiceFilter(
        choices=[
            ('framework', 'Frameworks'),
            ('policy', 'Policies'),
            ('control', 'Controls'),
            ('incident', 'Incidents'),
            ('assessment', 'Assessments'),
            ('training', 'Training'),
            ('risk', 'Risk Assessments'),
            ('vendor', 'Vendors'),
        ],
        method='filter_search_models'
    )
    
    def filter_search_term(self, queryset, name, value):
        # This would be implemented in the view to search across multiple models
        return queryset
    
    def filter_search_models(self, queryset, name, value):
        # This would be implemented in the view to filter by model types
        return queryset