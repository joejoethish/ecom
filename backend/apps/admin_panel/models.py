"""
Admin Panel models for comprehensive admin management.
"""
import uuid
import json
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from datetime import timedelta
from core.models import TimestampedModel


class AdminUser(AbstractUser, TimestampedModel):
    """
    Separate admin user model with extended fields for admin panel access.
    """
    ADMIN_ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
        ('support', 'Support'),
        ('viewer', 'Viewer'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('it', 'IT Department'),
        ('sales', 'Sales Department'),
        ('marketing', 'Marketing Department'),
        ('customer_service', 'Customer Service'),
        ('finance', 'Finance Department'),
        ('operations', 'Operations'),
        ('hr', 'Human Resources'),
        ('management', 'Management'),
    ]
    
    # Core admin fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ADMIN_ROLE_CHOICES, default='viewer')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    
    # Contact information
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    avatar = models.ImageField(upload_to='admin_avatars/', blank=True, null=True)
    
    # Security fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    must_change_password = models.BooleanField(default=False)
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # Session management
    max_concurrent_sessions = models.IntegerField(default=3)
    session_timeout_minutes = models.IntegerField(default=60)
    
    # Permissions
    permissions = models.ManyToManyField('AdminPermission', blank=True, related_name='admin_users')
    
    # Status and metadata
    is_admin_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_admins')
    
    # Override groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='admin_user_set',
        related_query_name='admin_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='admin_user_set',
        related_query_name='admin_user',
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'admin_users'
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['department']),
            models.Index(fields=['is_admin_active']),
            models.Index(fields=['last_login_ip']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def lock_account(self, duration_minutes=60):
        """Lock the account for specified duration."""
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])

    def unlock_account(self):
        """Unlock the account."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])


class AdminRole(TimestampedModel):
    """
    Hierarchical role structure for admin users.
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Hierarchy
    parent_role = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_roles')
    level = models.IntegerField(default=0)  # 0 = highest level
    
    # Permissions
    permissions = models.ManyToManyField('AdminPermission', blank=True, related_name='roles')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False)  # Cannot be deleted
    
    class Meta:
        db_table = 'admin_roles'
        verbose_name = 'Admin Role'
        verbose_name_plural = 'Admin Roles'
        ordering = ['level', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['level']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.display_name

    def get_all_permissions(self):
        """Get all permissions including inherited from parent roles."""
        permissions = set(self.permissions.all())
        
        # Add permissions from parent roles
        current_role = self.parent_role
        while current_role:
            permissions.update(current_role.permissions.all())
            current_role = current_role.parent_role
            
        return permissions


class AdminPermission(TimestampedModel):
    """
    Granular permission definitions for all admin modules.
    """
    MODULE_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('products', 'Products'),
        ('orders', 'Orders'),
        ('customers', 'Customers'),
        ('inventory', 'Inventory'),
        ('analytics', 'Analytics'),
        ('reports', 'Reports'),
        ('settings', 'Settings'),
        ('users', 'User Management'),
        ('content', 'Content Management'),
        ('promotions', 'Promotions'),
        ('shipping', 'Shipping'),
        ('payments', 'Payments'),
        ('notifications', 'Notifications'),
        ('system', 'System Administration'),
    ]
    
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('publish', 'Publish'),
        ('manage', 'Manage'),
        ('configure', 'Configure'),
    ]
    
    # Permission identification
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Categorization
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100, blank=True)  # Specific resource within module
    
    # Permission properties
    is_sensitive = models.BooleanField(default=False)  # Requires additional approval
    requires_mfa = models.BooleanField(default=False)  # Requires multi-factor auth
    ip_restricted = models.BooleanField(default=False)  # Can be IP restricted
    
    # Dependencies
    depends_on = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependents')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_system_permission = models.BooleanField(default=False)  # Cannot be deleted
    
    class Meta:
        db_table = 'admin_permissions'
        verbose_name = 'Admin Permission'
        verbose_name_plural = 'Admin Permissions'
        ordering = ['module', 'action', 'resource']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['module']),
            models.Index(fields=['action']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_sensitive']),
        ]

    def __str__(self):
        return f"{self.module}.{self.action}.{self.resource or 'all'}"


class SystemSettings(TimestampedModel):
    """
    Category-based configuration management for the entire system.
    """
    SETTING_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('text', 'Text'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('password', 'Password'),
        ('file', 'File'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General Settings'),
        ('email', 'Email Configuration'),
        ('sms', 'SMS Configuration'),
        ('payment', 'Payment Settings'),
        ('shipping', 'Shipping Settings'),
        ('tax', 'Tax Configuration'),
        ('security', 'Security Settings'),
        ('performance', 'Performance Settings'),
        ('seo', 'SEO Settings'),
        ('social', 'Social Media'),
        ('analytics', 'Analytics'),
        ('backup', 'Backup Settings'),
        ('maintenance', 'Maintenance'),
        ('api', 'API Configuration'),
        ('integration', 'Third-party Integrations'),
    ]
    
    # Setting identification
    key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Setting value and type
    value = models.TextField()
    default_value = models.TextField(blank=True)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPE_CHOICES, default='string')
    
    # Categorization
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True)
    
    # Validation and constraints
    validation_rules = models.JSONField(default=dict, blank=True)  # JSON schema for validation
    options = models.JSONField(default=list, blank=True)  # Available options for choice fields
    
    # Properties
    is_public = models.BooleanField(default=False)  # Can be accessed by frontend
    is_encrypted = models.BooleanField(default=False)  # Value is encrypted
    requires_restart = models.BooleanField(default=False)  # Requires app restart
    is_system_setting = models.BooleanField(default=False)  # Cannot be deleted
    
    # Metadata
    last_modified_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['category', 'subcategory', 'name']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
            models.Index(fields=['last_modified_by']),
        ]

    def __str__(self):
        return f"{self.category}.{self.key}"

    def get_typed_value(self):
        """Return the value converted to its proper type."""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value


class ActivityLog(TimestampedModel):
    """
    Comprehensive audit trails with JSON change tracking.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ('error', 'Error'),
        ('security', 'Security Event'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # User and session info
    admin_user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Target object
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Change tracking
    changes = models.JSONField(default=dict, blank=True)  # Before/after values
    additional_data = models.JSONField(default=dict, blank=True)  # Extra context
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Classification
    module = models.CharField(max_length=50, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    
    # Status
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['module', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['is_successful']),
        ]
        # Partition by month for better performance
        db_table_comment = 'PARTITION BY RANGE (YEAR(created_at)*100 + MONTH(created_at))'

    def __str__(self):
        user = self.admin_user.username if self.admin_user else 'Anonymous'
        return f"{user} - {self.action} - {self.created_at}"


class AdminSession(TimestampedModel):
    """
    Session management and concurrent login control for admin users.
    """
    # Session identification
    session_key = models.CharField(max_length=40, unique=True)
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='admin_sessions')
    
    # Session details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Location and security
    location = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_trusted_device = models.BooleanField(default=False)
    
    # Session status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Security flags
    is_suspicious = models.BooleanField(default=False)
    security_score = models.IntegerField(default=100)  # 0-100, lower is more suspicious
    
    class Meta:
        db_table = 'admin_sessions'
        verbose_name = 'Admin Session'
        verbose_name_plural = 'Admin Sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['admin_user', 'is_active']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_suspicious']),
        ]

    def __str__(self):
        return f"{self.admin_user.username} - {self.ip_address} - {self.last_activity}"

    @property
    def is_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at

    def extend_session(self, minutes=60):
        """Extend session expiration."""
        self.expires_at = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['expires_at'])


class AdminNotification(TimestampedModel):
    """
    Internal admin notifications and alerts.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('security', 'Security Alert'),
        ('system', 'System Notification'),
        ('task', 'Task Notification'),
        ('reminder', 'Reminder'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Recipients
    recipient = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Related object
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action and metadata
    action_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'admin_notifications'
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class AdminLoginAttempt(TimestampedModel):
    """
    Detailed login tracking for security monitoring.
    """
    # User identification
    username = models.CharField(max_length=150)
    admin_user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_attempts')
    
    # Attempt details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Result
    is_successful = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    # Security analysis
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.IntegerField(default=0)  # 0-100, higher is more risky
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'admin_login_attempts'
        verbose_name = 'Admin Login Attempt'
        verbose_name_plural = 'Admin Login Attempts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['is_successful']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['admin_user', 'created_at']),
        ]

    def __str__(self):
        status = "Success" if self.is_successful else "Failed"
        return f"{status} login: {self.username} from {self.ip_address}"


class AdminReport(TimestampedModel):
    """
    Reporting query configurations and scheduled reports.
    """
    REPORT_TYPE_CHOICES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('customer', 'Customer Report'),
        ('financial', 'Financial Report'),
        ('activity', 'Activity Report'),
        ('security', 'Security Report'),
        ('performance', 'Performance Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    SCHEDULE_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    # Report identification
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    # Configuration
    query_config = models.JSONField(default=dict)  # Report parameters and filters
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Scheduling
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='once')
    schedule_config = models.JSONField(default=dict)  # Cron-like configuration
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Recipients
    recipients = models.ManyToManyField(AdminUser, blank=True, related_name='subscribed_reports')
    email_recipients = models.JSONField(default=list, blank=True)  # External email addresses
    
    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='created_reports')
    
    # Execution tracking
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'admin_reports'
        verbose_name = 'Admin Report'
        verbose_name_plural = 'Admin Reports'
        ordering = ['name']
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['schedule_type']),
            models.Index(fields=['next_run']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"