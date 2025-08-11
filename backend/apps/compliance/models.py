from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

class ComplianceFramework(models.Model):
    """Model for different compliance frameworks (GDPR, CCPA, SOX, etc.)"""
    FRAMEWORK_TYPES = [
        ('gdpr', 'General Data Protection Regulation'),
        ('ccpa', 'California Consumer Privacy Act'),
        ('sox', 'Sarbanes-Oxley Act'),
        ('hipaa', 'Health Insurance Portability and Accountability Act'),
        ('pci_dss', 'Payment Card Industry Data Security Standard'),
        ('iso_27001', 'ISO 27001'),
        ('nist', 'NIST Cybersecurity Framework'),
        ('custom', 'Custom Framework'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    framework_type = models.CharField(max_length=50, choices=FRAMEWORK_TYPES)
    description = models.TextField()
    version = models.CharField(max_length=50)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    requirements = models.JSONField(default=dict)  # Store framework requirements
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_frameworks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.version})"

class CompliancePolicy(models.Model):
    """Model for compliance policies"""
    POLICY_TYPES = [
        ('data_protection', 'Data Protection'),
        ('privacy', 'Privacy'),
        ('security', 'Security'),
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('vendor', 'Vendor Management'),
        ('training', 'Training'),
        ('incident_response', 'Incident Response'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='policies')
    title = models.CharField(max_length=200)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)
    description = models.TextField()
    content = models.TextField()
    version = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effective_date = models.DateField()
    review_date = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_policies')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_policies')
    approved_at = models.DateTimeField(null=True, blank=True)
    tags = models.JSONField(default=list)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_policies'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"

class ComplianceControl(models.Model):
    """Model for compliance controls"""
    CONTROL_TYPES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
        ('compensating', 'Compensating'),
    ]
    
    IMPLEMENTATION_STATUS = [
        ('not_implemented', 'Not Implemented'),
        ('in_progress', 'In Progress'),
        ('implemented', 'Implemented'),
        ('testing', 'Testing'),
        ('operational', 'Operational'),
        ('needs_improvement', 'Needs Improvement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='controls')
    policy = models.ForeignKey(CompliancePolicy, on_delete=models.CASCADE, related_name='controls', null=True, blank=True)
    control_id = models.CharField(max_length=50)  # e.g., GDPR-001, SOX-302
    title = models.CharField(max_length=200)
    description = models.TextField()
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPES)
    implementation_status = models.CharField(max_length=30, choices=IMPLEMENTATION_STATUS, default='not_implemented')
    risk_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_controls')
    implementation_details = models.TextField(blank=True)
    testing_procedures = models.TextField(blank=True)
    evidence_requirements = models.JSONField(default=list)
    frequency = models.CharField(max_length=50)  # daily, weekly, monthly, quarterly, annually
    last_tested = models.DateField(null=True, blank=True)
    next_test_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_controls'
        unique_together = ['framework', 'control_id']
        ordering = ['control_id']
    
    def __str__(self):
        return f"{self.control_id}: {self.title}"

class ComplianceAssessment(models.Model):
    """Model for compliance assessments"""
    ASSESSMENT_TYPES = [
        ('self_assessment', 'Self Assessment'),
        ('internal_audit', 'Internal Audit'),
        ('external_audit', 'External Audit'),
        ('regulatory_review', 'Regulatory Review'),
        ('vendor_assessment', 'Vendor Assessment'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=30, choices=ASSESSMENT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    assessor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conducted_assessments')
    start_date = models.DateField()
    end_date = models.DateField()
    scope = models.TextField()
    methodology = models.TextField()
    findings = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    risk_rating = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], null=True, blank=True)
    report_file = models.FileField(upload_to='compliance/assessments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_assessments'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.framework.name}"

class ComplianceIncident(models.Model):
    """Model for compliance incidents"""
    INCIDENT_TYPES = [
        ('data_breach', 'Data Breach'),
        ('privacy_violation', 'Privacy Violation'),
        ('policy_violation', 'Policy Violation'),
        ('control_failure', 'Control Failure'),
        ('regulatory_violation', 'Regulatory Violation'),
        ('vendor_incident', 'Vendor Incident'),
        ('other', 'Other'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('contained', 'Contained'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_id = models.CharField(max_length=50, unique=True)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='incidents')
    title = models.CharField(max_length=200)
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_incidents')
    occurred_at = models.DateTimeField()
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    impact_assessment = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    remediation_actions = models.JSONField(default=list)
    lessons_learned = models.TextField(blank=True)
    regulatory_notification_required = models.BooleanField(default=False)
    regulatory_notification_sent = models.BooleanField(default=False)
    notification_date = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_incidents'
        ordering = ['-occurred_at']
    
    def __str__(self):
        return f"{self.incident_id}: {self.title}"

class ComplianceTraining(models.Model):
    """Model for compliance training programs"""
    TRAINING_TYPES = [
        ('general_awareness', 'General Awareness'),
        ('role_specific', 'Role Specific'),
        ('technical', 'Technical'),
        ('regulatory', 'Regulatory'),
        ('policy', 'Policy'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='training_programs')
    title = models.CharField(max_length=200)
    training_type = models.CharField(max_length=30, choices=TRAINING_TYPES)
    description = models.TextField()
    content = models.TextField()
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    mandatory = models.BooleanField(default=False)
    target_audience = models.JSONField(default=list)  # roles, departments
    prerequisites = models.TextField(blank=True)
    learning_objectives = models.JSONField(default=list)
    assessment_required = models.BooleanField(default=False)
    passing_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    validity_period_months = models.IntegerField(default=12)
    materials = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_training'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ComplianceTrainingRecord(models.Model):
    """Model for tracking individual training completion"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training = models.ForeignKey(ComplianceTraining, on_delete=models.CASCADE, related_name='records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    assigned_date = models.DateField()
    started_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    attempts = models.IntegerField(default=0)
    time_spent_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    certificate_issued = models.BooleanField(default=False)
    certificate_file = models.FileField(upload_to='compliance/certificates/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_training_records'
        unique_together = ['training', 'user']
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.training.title}"

class ComplianceAuditTrail(models.Model):
    """Model for compliance audit trails"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('complete', 'Complete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_key = models.CharField(max_length=40, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_audit_trails'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.timestamp}"

class ComplianceRiskAssessment(models.Model):
    """Model for compliance risk assessments"""
    RISK_CATEGORIES = [
        ('operational', 'Operational'),
        ('financial', 'Financial'),
        ('regulatory', 'Regulatory'),
        ('reputational', 'Reputational'),
        ('strategic', 'Strategic'),
        ('technology', 'Technology'),
    ]
    
    LIKELIHOOD_LEVELS = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    IMPACT_LEVELS = [
        ('negligible', 'Negligible'),
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('catastrophic', 'Catastrophic'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='risk_assessments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    risk_category = models.CharField(max_length=20, choices=RISK_CATEGORIES)
    likelihood = models.CharField(max_length=20, choices=LIKELIHOOD_LEVELS)
    impact = models.CharField(max_length=20, choices=IMPACT_LEVELS)
    inherent_risk_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(25)])
    residual_risk_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(25)])
    risk_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_risks')
    mitigation_strategies = models.JSONField(default=list)
    controls = models.ManyToManyField(ComplianceControl, related_name='mitigated_risks')
    review_date = models.DateField()
    last_reviewed = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('identified', 'Identified'),
        ('assessed', 'Assessed'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Accepted'),
        ('transferred', 'Transferred'),
        ('avoided', 'Avoided'),
    ], default='identified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_risk_assessments'
        ordering = ['-inherent_risk_score', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.framework.name}"

class ComplianceVendor(models.Model):
    """Model for vendor compliance management"""
    VENDOR_TYPES = [
        ('technology', 'Technology'),
        ('service', 'Service'),
        ('consulting', 'Consulting'),
        ('outsourcing', 'Outsourcing'),
        ('cloud', 'Cloud Provider'),
        ('other', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('under_review', 'Under Review'),
        ('terminated', 'Terminated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    description = models.TextField()
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    address = models.TextField()
    website = models.URLField(blank=True)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()
    services_provided = models.TextField()
    data_access_level = models.CharField(max_length=50)
    compliance_requirements = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    last_assessment_date = models.DateField(null=True, blank=True)
    next_assessment_date = models.DateField()
    assessment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    documents = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_vendors'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ComplianceReport(models.Model):
    """Model for compliance reports"""
    REPORT_TYPES = [
        ('dashboard', 'Dashboard Report'),
        ('assessment', 'Assessment Report'),
        ('audit', 'Audit Report'),
        ('incident', 'Incident Report'),
        ('training', 'Training Report'),
        ('risk', 'Risk Report'),
        ('vendor', 'Vendor Report'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    description = models.TextField()
    parameters = models.JSONField(default=dict)  # filters, date ranges, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    next_run = models.DateTimeField(null=True, blank=True)
    recipients = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title