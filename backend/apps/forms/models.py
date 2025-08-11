from django.db import models
from django.contrib.auth import get_user_model
# JSONSchemaValidator not available in this Django version
# from django.core.validators import JSONSchemaValidator
import uuid
import json
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()

class FormTemplate(models.Model):
    """Form template for reusable form structures"""
    FORM_TYPES = [
        ('contact', 'Contact Form'),
        ('survey', 'Survey Form'),
        ('registration', 'Registration Form'),
        ('feedback', 'Feedback Form'),
        ('application', 'Application Form'),
        ('custom', 'Custom Form'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    form_type = models.CharField(max_length=50, choices=FORM_TYPES, default='custom')
    schema = models.JSONField(default=dict)  # Form structure and validation rules
    settings = models.JSONField(default=dict)  # Form settings and configuration
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"

class Form(models.Model):
    """Dynamic form instances"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    template = models.ForeignKey(FormTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    schema = models.JSONField(default=dict)  # Form structure
    validation_rules = models.JSONField(default=dict)  # Validation configuration
    conditional_logic = models.JSONField(default=dict)  # Conditional field display
    settings = models.JSONField(default=dict)  # Form settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_multi_step = models.BooleanField(default=False)
    steps_config = models.JSONField(default=dict)  # Multi-step configuration
    auto_save_enabled = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    approval_workflow = models.JSONField(default=dict)
    encryption_enabled = models.BooleanField(default=False)
    spam_protection_enabled = models.BooleanField(default=True)
    analytics_enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'forms'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class FormField(models.Model):
    """Individual form fields"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Textarea'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('tel', 'Phone'),
        ('url', 'URL'),
        ('password', 'Password'),
        ('select', 'Select Dropdown'),
        ('multiselect', 'Multi-Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('time', 'Time'),
        ('file', 'File Upload'),
        ('image', 'Image Upload'),
        ('signature', 'Digital Signature'),
        ('rating', 'Rating'),
        ('slider', 'Slider'),
        ('hidden', 'Hidden Field'),
        ('html', 'HTML Content'),
        ('divider', 'Divider'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)  # Field name/key
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    default_value = models.TextField(blank=True)
    options = models.JSONField(default=list)  # For select, radio, checkbox fields
    validation_rules = models.JSONField(default=dict)
    conditional_logic = models.JSONField(default=dict)
    is_required = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    step = models.PositiveIntegerField(default=1)  # For multi-step forms
    css_classes = models.CharField(max_length=200, blank=True)
    attributes = models.JSONField(default=dict)  # Additional HTML attributes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_fields'
        ordering = ['order']
        unique_together = ['form', 'name']
    
    def __str__(self):
        return f"{self.form.name} - {self.label}"

class FormSubmission(models.Model):
    """Form submission data"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    data = models.JSONField(default=dict)  # Form submission data
    encrypted_data = models.TextField(blank=True)  # Encrypted sensitive data
    files = models.JSONField(default=dict)  # File upload references
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    completion_time = models.DurationField(null=True, blank=True)
    is_spam = models.BooleanField(default=False)
    spam_score = models.FloatField(default=0.0)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'form_submissions'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.form.name} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    
    def encrypt_data(self, data):
        """Encrypt sensitive form data"""
        if not hasattr(settings, 'FORM_ENCRYPTION_KEY'):
            return json.dumps(data)
        
        fernet = Fernet(settings.FORM_ENCRYPTION_KEY.encode())
        return fernet.encrypt(json.dumps(data).encode()).decode()
    
    def decrypt_data(self):
        """Decrypt sensitive form data"""
        if not self.encrypted_data or not hasattr(settings, 'FORM_ENCRYPTION_KEY'):
            return {}
        
        fernet = Fernet(settings.FORM_ENCRYPTION_KEY.encode())
        decrypted = fernet.decrypt(self.encrypted_data.encode()).decode()
        return json.loads(decrypted)

class FormVersion(models.Model):
    """Form version control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    schema = models.JSONField(default=dict)
    changes = models.JSONField(default=dict)  # Change log
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'form_versions'
        ordering = ['-created_at']
        unique_together = ['form', 'version_number']
    
    def __str__(self):
        return f"{self.form.name} v{self.version_number}"

class FormAnalytics(models.Model):
    """Form analytics and performance tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    starts = models.PositiveIntegerField(default=0)
    completions = models.PositiveIntegerField(default=0)
    abandonment_rate = models.FloatField(default=0.0)
    average_completion_time = models.DurationField(null=True, blank=True)
    conversion_rate = models.FloatField(default=0.0)
    field_analytics = models.JSONField(default=dict)  # Per-field analytics
    device_analytics = models.JSONField(default=dict)  # Device breakdown
    source_analytics = models.JSONField(default=dict)  # Traffic source breakdown
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_analytics'
        unique_together = ['form', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.form.name} - {self.date}"

class FormApprovalWorkflow(models.Model):
    """Form approval workflow management"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    step = models.PositiveIntegerField(default=1)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'form_approval_workflows'
        ordering = ['step', '-created_at']
    
    def __str__(self):
        return f"{self.submission.form.name} - Step {self.step}"

class FormIntegration(models.Model):
    """External system integrations"""
    INTEGRATION_TYPES = [
        ('webhook', 'Webhook'),
        ('email', 'Email'),
        ('crm', 'CRM System'),
        ('marketing', 'Marketing Platform'),
        ('database', 'External Database'),
        ('api', 'REST API'),
        ('zapier', 'Zapier'),
        ('custom', 'Custom Integration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='integrations')
    name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=50, choices=INTEGRATION_TYPES)
    endpoint_url = models.URLField(blank=True)
    configuration = models.JSONField(default=dict)
    headers = models.JSONField(default=dict)
    field_mapping = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    retry_count = models.PositiveIntegerField(default=3)
    timeout = models.PositiveIntegerField(default=30)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_integrations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.form.name} - {self.name}"

class FormABTest(models.Model):
    """A/B testing for forms"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    original_form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='ab_tests_original')
    variant_form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='ab_tests_variant')
    traffic_split = models.FloatField(default=50.0)  # Percentage for variant
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    success_metric = models.CharField(max_length=50, default='conversion_rate')
    confidence_level = models.FloatField(default=95.0)
    results = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_ab_tests'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name