from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
import uuid

User = get_user_model()

class SecurityThreat(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('investigating', 'Investigating'),
        ('mitigated', 'Mitigated'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    threat_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    target_resource = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()
    detection_method = models.CharField(max_length=100)
    threat_indicators = models.JSONField(default=dict)
    mitigation_actions = models.JSONField(default=list)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    detected_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-detected_at']

class SecurityIncident(models.Model):
    INCIDENT_TYPES = [
        ('data_breach', 'Data Breach'),
        ('malware', 'Malware'),
        ('phishing', 'Phishing'),
        ('ddos', 'DDoS Attack'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('insider_threat', 'Insider Threat'),
        ('system_compromise', 'System Compromise'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('contained', 'Contained'),
        ('eradicated', 'Eradicated'),
        ('recovered', 'Recovered'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=20, choices=SecurityThreat.SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    impact_assessment = models.TextField(blank=True)
    affected_systems = models.JSONField(default=list)
    affected_users = models.JSONField(default=list)
    timeline = models.JSONField(default=list)
    response_actions = models.JSONField(default=list)
    lessons_learned = models.TextField(blank=True)
    assigned_team = models.ManyToManyField(User, related_name='security_incidents')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    occurred_at = models.DateTimeField()
    detected_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-occurred_at']

class SecurityAudit(models.Model):
    AUDIT_TYPES = [
        ('access_control', 'Access Control'),
        ('data_protection', 'Data Protection'),
        ('network_security', 'Network Security'),
        ('application_security', 'Application Security'),
        ('compliance', 'Compliance'),
        ('vulnerability', 'Vulnerability Assessment'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_name = models.CharField(max_length=200)
    audit_type = models.CharField(max_length=50, choices=AUDIT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    scope = models.TextField()
    objectives = models.JSONField(default=list)
    methodology = models.TextField()
    findings = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    compliance_frameworks = models.JSONField(default=list)
    auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    report_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']

class SecurityPolicy(models.Model):
    POLICY_TYPES = [
        ('access_control', 'Access Control'),
        ('data_classification', 'Data Classification'),
        ('incident_response', 'Incident Response'),
        ('acceptable_use', 'Acceptable Use'),
        ('password', 'Password Policy'),
        ('encryption', 'Encryption'),
        ('backup', 'Backup and Recovery'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_name = models.CharField(max_length=200)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField()
    policy_content = models.TextField()
    compliance_requirements = models.JSONField(default=list)
    enforcement_rules = models.JSONField(default=list)
    exceptions = models.JSONField(default=list)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_policies')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_policies')
    effective_date = models.DateTimeField()
    review_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-effective_date']

class SecurityVulnerability(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Informational'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
        ('accepted_risk', 'Accepted Risk'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vulnerability_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    cvss_score = models.FloatField(null=True, blank=True)
    cve_id = models.CharField(max_length=50, blank=True)
    affected_systems = models.JSONField(default=list)
    affected_components = models.JSONField(default=list)
    exploit_available = models.BooleanField(default=False)
    patch_available = models.BooleanField(default=False)
    remediation_steps = models.TextField(blank=True)
    workaround = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    discovered_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-cvss_score', '-discovered_date']

class SecurityTraining(models.Model):
    TRAINING_TYPES = [
        ('security_awareness', 'Security Awareness'),
        ('phishing_simulation', 'Phishing Simulation'),
        ('incident_response', 'Incident Response'),
        ('compliance', 'Compliance Training'),
        ('technical_security', 'Technical Security'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_name = models.CharField(max_length=200)
    training_type = models.CharField(max_length=50, choices=TRAINING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField()
    content = models.TextField()
    duration_minutes = models.IntegerField()
    required_for_roles = models.JSONField(default=list)
    completion_criteria = models.JSONField(default=dict)
    certificate_template = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['training_name']

class SecurityTrainingRecord(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey(SecurityTraining, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    score = models.FloatField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'training']
        ordering = ['-completed_at']

class SecurityRiskAssessment(models.Model):
    RISK_LEVELS = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('implemented', 'Implemented'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment_name = models.CharField(max_length=200)
    asset_category = models.CharField(max_length=100)
    asset_description = models.TextField()
    threat_sources = models.JSONField(default=list)
    vulnerabilities = models.JSONField(default=list)
    existing_controls = models.JSONField(default=list)
    likelihood = models.CharField(max_length=20, choices=RISK_LEVELS)
    impact = models.CharField(max_length=20, choices=RISK_LEVELS)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    risk_score = models.FloatField()
    recommended_controls = models.JSONField(default=list)
    residual_risk = models.CharField(max_length=20, choices=RISK_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    assessor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assessment_date = models.DateTimeField(default=timezone.now)
    review_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-risk_score', '-assessment_date']

class SecurityMonitoringRule(models.Model):
    RULE_TYPES = [
        ('intrusion_detection', 'Intrusion Detection'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('compliance_monitoring', 'Compliance Monitoring'),
        ('threat_hunting', 'Threat Hunting'),
        ('data_loss_prevention', 'Data Loss Prevention'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField()
    rule_logic = models.TextField()
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=list)
    severity = models.CharField(max_length=20, choices=SecurityThreat.SEVERITY_CHOICES)
    false_positive_rate = models.FloatField(default=0.0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rule_name']

class SecurityAlert(models.Model):
    ALERT_TYPES = [
        ('security_event', 'Security Event'),
        ('policy_violation', 'Policy Violation'),
        ('anomaly_detected', 'Anomaly Detected'),
        ('compliance_issue', 'Compliance Issue'),
        ('system_health', 'System Health'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SecurityThreat.SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    title = models.CharField(max_length=200)
    description = models.TextField()
    source_system = models.CharField(max_length=100)
    rule = models.ForeignKey(SecurityMonitoringRule, on_delete=models.SET_NULL, null=True, blank=True)
    event_data = models.JSONField(default=dict)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class SecurityConfiguration(models.Model):
    CONFIG_TYPES = [
        ('firewall', 'Firewall'),
        ('antivirus', 'Antivirus'),
        ('ids_ips', 'IDS/IPS'),
        ('siem', 'SIEM'),
        ('dlp', 'Data Loss Prevention'),
        ('encryption', 'Encryption'),
        ('backup', 'Backup'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_name = models.CharField(max_length=200)
    config_type = models.CharField(max_length=50, choices=CONFIG_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField()
    configuration_data = models.JSONField(default=dict)
    baseline_config = models.JSONField(default=dict)
    compliance_requirements = models.JSONField(default=list)
    last_validated = models.DateTimeField(null=True, blank=True)
    validation_status = models.CharField(max_length=20, default='pending')
    validation_errors = models.JSONField(default=list)
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['config_name']