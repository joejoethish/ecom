from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json
import uuid


class SettingCategory(models.Model):
    """Hierarchical organization of settings with categories and subcategories"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Setting Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.display_name

    def get_full_path(self):
        """Get full hierarchical path"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.display_name}"
        return self.display_name


class SettingDataType(models.TextChoices):
    STRING = 'string', 'String'
    INTEGER = 'integer', 'Integer'
    FLOAT = 'float', 'Float'
    BOOLEAN = 'boolean', 'Boolean'
    JSON = 'json', 'JSON'
    EMAIL = 'email', 'Email'
    URL = 'url', 'URL'
    PASSWORD = 'password', 'Password'
    FILE = 'file', 'File'
    COLOR = 'color', 'Color'
    DATE = 'date', 'Date'
    DATETIME = 'datetime', 'DateTime'


class SettingAccessLevel(models.TextChoices):
    PUBLIC = 'public', 'Public'
    ADMIN = 'admin', 'Admin Only'
    SUPERUSER = 'superuser', 'Superuser Only'
    ROLE_BASED = 'role_based', 'Role Based'


class SystemSetting(models.Model):
    """Core system settings with comprehensive features"""
    key = models.CharField(max_length=200, unique=True, db_index=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(SettingCategory, on_delete=models.CASCADE, related_name='settings')
    
    # Data type and validation
    data_type = models.CharField(max_length=20, choices=SettingDataType.choices, default=SettingDataType.STRING)
    value = models.TextField()
    default_value = models.TextField()
    
    # Validation rules
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    regex_pattern = models.CharField(max_length=500, blank=True)
    allowed_values = models.JSONField(null=True, blank=True)  # For enum-like values
    
    # Security and access
    is_encrypted = models.BooleanField(default=False)
    access_level = models.CharField(max_length=20, choices=SettingAccessLevel.choices, default=SettingAccessLevel.ADMIN)
    allowed_roles = models.JSONField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)
    requires_restart = models.BooleanField(default=False)
    is_sensitive = models.BooleanField(default=False)
    
    # Environment specific
    environment = models.CharField(max_length=50, default='production')
    
    # Documentation
    help_text = models.TextField(blank=True)
    documentation_url = models.URLField(blank=True)
    
    # Versioning
    version = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='created_settings')
    updated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='updated_settings')

    class Meta:
        ordering = ['category__order', 'display_name']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['environment']),
        ]

    def __str__(self):
        return f"{self.key}: {self.display_name}"

    def clean(self):
        """Validate setting value against data type and rules"""
        if not self.value and self.is_required:
            raise ValidationError("This setting is required and cannot be empty.")
        
        if self.value:
            self._validate_data_type()
            self._validate_constraints()

    def _validate_data_type(self):
        """Validate value matches data type"""
        try:
            if self.data_type == SettingDataType.INTEGER:
                int(self.value)
            elif self.data_type == SettingDataType.FLOAT:
                float(self.value)
            elif self.data_type == SettingDataType.BOOLEAN:
                if self.value.lower() not in ['true', 'false', '1', '0']:
                    raise ValidationError("Boolean value must be true/false or 1/0")
            elif self.data_type == SettingDataType.JSON:
                json.loads(self.value)
            elif self.data_type == SettingDataType.EMAIL:
                from django.core.validators import validate_email
                validate_email(self.value)
            elif self.data_type == SettingDataType.URL:
                from django.core.validators import URLValidator
                URLValidator()(self.value)
        except (ValueError, ValidationError) as e:
            raise ValidationError(f"Invalid {self.data_type} value: {e}")

    def _validate_constraints(self):
        """Validate value against constraints"""
        if self.data_type in [SettingDataType.INTEGER, SettingDataType.FLOAT]:
            numeric_value = float(self.value)
            if self.min_value is not None and numeric_value < self.min_value:
                raise ValidationError(f"Value must be at least {self.min_value}")
            if self.max_value is not None and numeric_value > self.max_value:
                raise ValidationError(f"Value must be at most {self.max_value}")
        
        if self.data_type == SettingDataType.STRING:
            if self.min_length is not None and len(self.value) < self.min_length:
                raise ValidationError(f"Value must be at least {self.min_length} characters")
            if self.max_length is not None and len(self.value) > self.max_length:
                raise ValidationError(f"Value must be at most {self.max_length} characters")
        
        if self.regex_pattern:
            import re
            if not re.match(self.regex_pattern, self.value):
                raise ValidationError("Value does not match required pattern")
        
        if self.allowed_values and self.value not in self.allowed_values:
            raise ValidationError(f"Value must be one of: {', '.join(self.allowed_values)}")

    def get_decrypted_value(self):
        """Get decrypted value if encrypted"""
        if self.is_encrypted and hasattr(settings, 'SETTINGS_ENCRYPTION_KEY'):
            try:
                fernet = Fernet(settings.SETTINGS_ENCRYPTION_KEY.encode())
                return fernet.decrypt(self.value.encode()).decode()
            except Exception:
                return self.value
        return self.value

    def set_encrypted_value(self, value):
        """Set encrypted value"""
        if self.is_encrypted and hasattr(settings, 'SETTINGS_ENCRYPTION_KEY'):
            try:
                fernet = Fernet(settings.SETTINGS_ENCRYPTION_KEY.encode())
                self.value = fernet.encrypt(value.encode()).decode()
            except Exception:
                self.value = value
        else:
            self.value = value

    def get_typed_value(self):
        """Get value converted to appropriate Python type"""
        value = self.get_decrypted_value()
        
        if self.data_type == SettingDataType.INTEGER:
            return int(value)
        elif self.data_type == SettingDataType.FLOAT:
            return float(value)
        elif self.data_type == SettingDataType.BOOLEAN:
            return value.lower() in ['true', '1']
        elif self.data_type == SettingDataType.JSON:
            return json.loads(value)
        return value


class SettingChangeHistory(models.Model):
    """Track all changes to settings with versioning"""
    setting = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='change_history')
    old_value = models.TextField(blank=True)
    new_value = models.TextField()
    version = models.IntegerField()
    change_reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_changes')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='approved')

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['setting', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]

    def __str__(self):
        return f"{self.setting.key} changed at {self.changed_at}"


class SettingBackup(models.Model):
    """Settings backup and restore functionality"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    backup_data = models.JSONField()
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=50)
    backup_type = models.CharField(max_length=20, choices=[
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('pre_change', 'Pre-Change'),
    ], default='manual')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Backup: {self.name} ({self.created_at})"


class SettingTemplate(models.Model):
    """Settings templates for quick configuration deployment"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    template_data = models.JSONField()
    category = models.ForeignKey(SettingCategory, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SettingDependency(models.Model):
    """Manage dependencies between settings"""
    setting = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='dependents')
    dependency_type = models.CharField(max_length=20, choices=[
        ('required', 'Required'),
        ('conditional', 'Conditional'),
        ('exclusive', 'Mutually Exclusive'),
    ])
    condition = models.JSONField(null=True, blank=True)  # Condition for conditional dependencies
    
    class Meta:
        unique_together = ['setting', 'depends_on']

    def __str__(self):
        return f"{self.setting.key} depends on {self.depends_on.key}"


class SettingNotification(models.Model):
    """Notification system for setting changes"""
    setting = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
    ])
    recipients = models.JSONField()  # List of email addresses, webhook URLs, etc.
    trigger_conditions = models.JSONField(default=dict)  # When to trigger notifications
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.setting.key}"


class SettingAuditLog(models.Model):
    """Comprehensive audit trail for compliance"""
    setting = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=[
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('export', 'Exported'),
        ('import', 'Imported'),
    ])
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    compliance_flags = models.JSONField(default=list)  # For regulatory compliance tracking
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['setting', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.action} {self.setting.key} by {self.user} at {self.timestamp}"


class SettingEnvironmentSync(models.Model):
    """Synchronization across multiple environments"""
    setting = models.ForeignKey(SystemSetting, on_delete=models.CASCADE, related_name='environment_syncs')
    source_environment = models.CharField(max_length=50)
    target_environment = models.CharField(max_length=50)
    sync_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('conflict', 'Conflict'),
    ])
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_details = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['setting', 'source_environment', 'target_environment']

    def __str__(self):
        return f"Sync {self.setting.key} from {self.source_environment} to {self.target_environment}"