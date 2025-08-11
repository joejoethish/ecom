from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Framework"""
    created_by = UserBasicSerializer(read_only=True)
    policies_count = serializers.SerializerMethodField()
    controls_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceFramework
        fields = [
            'id', 'name', 'framework_type', 'description', 'version',
            'effective_date', 'expiry_date', 'status', 'requirements',
            'created_by', 'created_at', 'updated_at', 'policies_count',
            'controls_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_policies_count(self, obj):
        return obj.policies.count()
    
    def get_controls_count(self, obj):
        return obj.controls.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CompliancePolicySerializer(serializers.ModelSerializer):
    """Serializer for Compliance Policy"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    owner = UserBasicSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True, required=False)
    approver = UserBasicSerializer(read_only=True)
    approver_id = serializers.IntegerField(write_only=True, required=False)
    controls_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CompliancePolicy
        fields = [
            'id', 'framework', 'framework_id', 'title', 'policy_type',
            'description', 'content', 'version', 'status', 'effective_date',
            'review_date', 'owner', 'owner_id', 'approver', 'approver_id',
            'approved_at', 'tags', 'attachments', 'created_at', 'updated_at',
            'controls_count'
        ]
        read_only_fields = ['id', 'approved_at', 'created_at', 'updated_at']
    
    def get_controls_count(self, obj):
        return obj.controls.count()


class ComplianceControlSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Control"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    policy = CompliancePolicySerializer(read_only=True)
    policy_id = serializers.UUIDField(write_only=True, required=False)
    owner = UserBasicSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ComplianceControl
        fields = [
            'id', 'framework', 'framework_id', 'policy', 'policy_id',
            'control_id', 'title', 'description', 'control_type',
            'implementation_status', 'risk_level', 'owner', 'owner_id',
            'implementation_details', 'testing_procedures', 'evidence_requirements',
            'frequency', 'last_tested', 'next_test_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Assessment"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    assessor = UserBasicSerializer(read_only=True)
    assessor_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ComplianceAssessment
        fields = [
            'id', 'framework', 'framework_id', 'title', 'assessment_type',
            'description', 'status', 'assessor', 'assessor_id', 'start_date',
            'end_date', 'scope', 'methodology', 'findings', 'recommendations',
            'overall_score', 'risk_rating', 'report_file', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceIncidentSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Incident"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    reported_by = UserBasicSerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ComplianceIncident
        fields = [
            'id', 'incident_id', 'framework', 'framework_id', 'title',
            'incident_type', 'description', 'severity', 'status',
            'reported_by', 'assigned_to', 'assigned_to_id', 'occurred_at',
            'reported_at', 'resolved_at', 'impact_assessment', 'root_cause',
            'remediation_actions', 'lessons_learned', 'regulatory_notification_required',
            'regulatory_notification_sent', 'notification_date', 'attachments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'incident_id', 'reported_by', 'reported_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        # Generate incident ID
        import uuid
        validated_data['incident_id'] = f"INC-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)


class ComplianceTrainingSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Training"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    created_by = UserBasicSerializer(read_only=True)
    records_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceTraining
        fields = [
            'id', 'framework', 'framework_id', 'title', 'training_type',
            'description', 'content', 'duration_hours', 'status', 'mandatory',
            'target_audience', 'prerequisites', 'learning_objectives',
            'assessment_required', 'passing_score', 'validity_period_months',
            'materials', 'created_by', 'created_at', 'updated_at',
            'records_count', 'completion_rate'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_records_count(self, obj):
        return obj.records.count()
    
    def get_completion_rate(self, obj):
        total_records = obj.records.count()
        if total_records == 0:
            return 0
        completed_records = obj.records.filter(status='completed').count()
        return round((completed_records / total_records) * 100, 2)
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ComplianceTrainingRecordSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Training Record"""
    training = ComplianceTrainingSerializer(read_only=True)
    training_id = serializers.UUIDField(write_only=True)
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ComplianceTrainingRecord
        fields = [
            'id', 'training', 'training_id', 'user', 'user_id', 'status',
            'assigned_date', 'started_date', 'completed_date', 'due_date',
            'score', 'attempts', 'time_spent_hours', 'certificate_issued',
            'certificate_file', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceAuditTrailSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Audit Trail"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ComplianceAuditTrail
        fields = [
            'id', 'user', 'action', 'model_name', 'object_id', 'object_repr',
            'changes', 'ip_address', 'user_agent', 'session_key', 'timestamp'
        ]
        read_only_fields = ['id', 'user', 'action', 'model_name', 'object_id',
                           'object_repr', 'changes', 'ip_address', 'user_agent',
                           'session_key', 'timestamp']


class ComplianceRiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Risk Assessment"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True)
    risk_owner = UserBasicSerializer(read_only=True)
    risk_owner_id = serializers.IntegerField(write_only=True, required=False)
    controls = ComplianceControlSerializer(many=True, read_only=True)
    control_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ComplianceRiskAssessment
        fields = [
            'id', 'framework', 'framework_id', 'title', 'description',
            'risk_category', 'likelihood', 'impact', 'inherent_risk_score',
            'residual_risk_score', 'risk_owner', 'risk_owner_id',
            'mitigation_strategies', 'controls', 'control_ids', 'review_date',
            'last_reviewed', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        control_ids = validated_data.pop('control_ids', [])
        risk_assessment = super().create(validated_data)
        if control_ids:
            risk_assessment.controls.set(control_ids)
        return risk_assessment
    
    def update(self, instance, validated_data):
        control_ids = validated_data.pop('control_ids', None)
        risk_assessment = super().update(instance, validated_data)
        if control_ids is not None:
            risk_assessment.controls.set(control_ids)
        return risk_assessment


class ComplianceVendorSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Vendor"""
    
    class Meta:
        model = ComplianceVendor
        fields = [
            'id', 'name', 'vendor_type', 'description', 'contact_person',
            'contact_email', 'contact_phone', 'address', 'website',
            'risk_level', 'status', 'contract_start_date', 'contract_end_date',
            'services_provided', 'data_access_level', 'compliance_requirements',
            'certifications', 'last_assessment_date', 'next_assessment_date',
            'assessment_score', 'documents', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Report"""
    framework = ComplianceFrameworkSerializer(read_only=True)
    framework_id = serializers.UUIDField(write_only=True, required=False)
    generated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'title', 'report_type', 'framework', 'framework_id',
            'description', 'parameters', 'status', 'generated_by',
            'generated_at', 'file_path', 'file_size', 'scheduled',
            'schedule_frequency', 'next_run', 'recipients',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'generated_by', 'generated_at', 'file_path',
                           'file_size', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['generated_by'] = self.context['request'].user
        return super().create(validated_data)


# Dashboard and Analytics Serializers
class ComplianceDashboardSerializer(serializers.Serializer):
    """Serializer for compliance dashboard data"""
    total_frameworks = serializers.IntegerField()
    active_frameworks = serializers.IntegerField()
    total_policies = serializers.IntegerField()
    approved_policies = serializers.IntegerField()
    total_controls = serializers.IntegerField()
    implemented_controls = serializers.IntegerField()
    open_incidents = serializers.IntegerField()
    critical_incidents = serializers.IntegerField()
    pending_assessments = serializers.IntegerField()
    overdue_trainings = serializers.IntegerField()
    high_risks = serializers.IntegerField()
    vendor_assessments_due = serializers.IntegerField()


class ComplianceMetricsSerializer(serializers.Serializer):
    """Serializer for compliance metrics"""
    framework_compliance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    policy_approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    control_implementation_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    incident_resolution_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    training_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    risk_mitigation_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    vendor_compliance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


# Bulk Operation Serializers
class BulkComplianceActionSerializer(serializers.Serializer):
    """Serializer for bulk compliance actions"""
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ])
    object_ids = serializers.ListField(child=serializers.UUIDField())
    parameters = serializers.JSONField(required=False, default=dict)


class ComplianceExportSerializer(serializers.Serializer):
    """Serializer for compliance data export"""
    export_type = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ])
    model_name = serializers.CharField()
    filters = serializers.JSONField(required=False, default=dict)
    fields = serializers.ListField(child=serializers.CharField(), required=False)
    date_range = serializers.JSONField(required=False)


class ComplianceImportSerializer(serializers.Serializer):
    """Serializer for compliance data import"""
    file = serializers.FileField()
    model_name = serializers.CharField()
    import_options = serializers.JSONField(required=False, default=dict)
    validate_only = serializers.BooleanField(default=False)