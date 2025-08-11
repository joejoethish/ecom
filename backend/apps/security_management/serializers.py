from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SecurityThreat, SecurityIncident, SecurityAudit, SecurityPolicy,
    SecurityVulnerability, SecurityTraining, SecurityTrainingRecord,
    SecurityRiskAssessment, SecurityMonitoringRule, SecurityAlert,
    SecurityConfiguration
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class SecurityThreatSerializer(serializers.ModelSerializer):
    assigned_to_details = UserBasicSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = SecurityThreat
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityIncidentSerializer(serializers.ModelSerializer):
    assigned_team_details = UserBasicSerializer(source='assigned_team', many=True, read_only=True)
    reported_by_details = UserBasicSerializer(source='reported_by', read_only=True)
    
    class Meta:
        model = SecurityIncident
        fields = '__all__'
        read_only_fields = ['id', 'incident_number', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Auto-generate incident number
        import uuid
        validated_data['incident_number'] = f"INC-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)

class SecurityAuditSerializer(serializers.ModelSerializer):
    auditor_details = UserBasicSerializer(source='auditor', read_only=True)
    
    class Meta:
        model = SecurityAudit
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityPolicySerializer(serializers.ModelSerializer):
    owner_details = UserBasicSerializer(source='owner', read_only=True)
    approver_details = UserBasicSerializer(source='approver', read_only=True)
    
    class Meta:
        model = SecurityPolicy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityVulnerabilitySerializer(serializers.ModelSerializer):
    assigned_to_details = UserBasicSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = SecurityVulnerability
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Auto-generate vulnerability ID
        import uuid
        validated_data['vulnerability_id'] = f"VULN-{str(uuid.uuid4())[:8].upper()}"
        return super().create(validated_data)

class SecurityTrainingSerializer(serializers.ModelSerializer):
    created_by_details = UserBasicSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = SecurityTraining
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityTrainingRecordSerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source='user', read_only=True)
    training_details = SecurityTrainingSerializer(source='training', read_only=True)
    
    class Meta:
        model = SecurityTrainingRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityRiskAssessmentSerializer(serializers.ModelSerializer):
    assessor_details = UserBasicSerializer(source='assessor', read_only=True)
    
    class Meta:
        model = SecurityRiskAssessment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityMonitoringRuleSerializer(serializers.ModelSerializer):
    created_by_details = UserBasicSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = SecurityMonitoringRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityAlertSerializer(serializers.ModelSerializer):
    rule_details = SecurityMonitoringRuleSerializer(source='rule', read_only=True)
    assigned_to_details = UserBasicSerializer(source='assigned_to', read_only=True)
    acknowledged_by_details = UserBasicSerializer(source='acknowledged_by', read_only=True)
    
    class Meta:
        model = SecurityAlert
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityConfigurationSerializer(serializers.ModelSerializer):
    managed_by_details = UserBasicSerializer(source='managed_by', read_only=True)
    
    class Meta:
        model = SecurityConfiguration
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

# Dashboard and Analytics Serializers
class SecurityDashboardStatsSerializer(serializers.Serializer):
    total_threats = serializers.IntegerField()
    active_incidents = serializers.IntegerField()
    critical_vulnerabilities = serializers.IntegerField()
    pending_audits = serializers.IntegerField()
    overdue_trainings = serializers.IntegerField()
    high_risk_assessments = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    compliance_score = serializers.FloatField()

class ThreatTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    threat_count = serializers.IntegerField()
    severity_breakdown = serializers.DictField()

class IncidentMetricsSerializer(serializers.Serializer):
    incident_type = serializers.CharField()
    count = serializers.IntegerField()
    avg_resolution_time = serializers.FloatField()

class VulnerabilityMetricsSerializer(serializers.Serializer):
    severity = serializers.CharField()
    count = serializers.IntegerField()
    avg_age_days = serializers.FloatField()

class ComplianceMetricsSerializer(serializers.Serializer):
    framework = serializers.CharField()
    compliance_percentage = serializers.FloatField()
    total_controls = serializers.IntegerField()
    compliant_controls = serializers.IntegerField()

class SecurityTrainingMetricsSerializer(serializers.Serializer):
    training_type = serializers.CharField()
    total_users = serializers.IntegerField()
    completed_users = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_score = serializers.FloatField()