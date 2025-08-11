from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import json

User = get_user_model()

class DataImportJob(models.Model):
    """Model for tracking data import jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # File information
    file_path = models.CharField(max_length=500)
    file_format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    file_size = models.BigIntegerField()
    
    # Target model information
    target_model = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Job configuration
    mapping_config = models.JSONField(default=dict)
    validation_rules = models.JSONField(default=dict)
    transformation_rules = models.JSONField(default=dict)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    
    # Results and errors
    error_log = models.JSONField(default=list)
    validation_errors = models.JSONField(default=list)
    processing_log = models.JSONField(default=list)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration options
    skip_duplicates = models.BooleanField(default=True)
    update_existing = models.BooleanField(default=False)
    batch_size = models.IntegerField(default=1000)
    
    class Meta:
        db_table = 'data_import_jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class DataExportJob(models.Model):
    """Model for tracking data export jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('pdf', 'PDF'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Source model information
    source_model = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Export configuration
    export_format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    field_mapping = models.JSONField(default=dict)
    filter_criteria = models.JSONField(default=dict)
    sort_criteria = models.JSONField(default=list)
    
    # File information
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)
    exported_records = models.IntegerField(default=0)
    
    # Results and errors
    error_log = models.JSONField(default=list)
    processing_log = models.JSONField(default=list)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration options
    include_headers = models.BooleanField(default=True)
    compress_output = models.BooleanField(default=False)
    encrypt_output = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'data_export_jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class DataMapping(models.Model):
    """Model for storing reusable data mapping configurations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Model information
    target_model = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Mapping configuration
    field_mappings = models.JSONField(default=dict)
    default_values = models.JSONField(default=dict)
    transformation_rules = models.JSONField(default=dict)
    validation_rules = models.JSONField(default=dict)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'data_mappings'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DataSyncJob(models.Model):
    """Model for scheduled data synchronization jobs"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('disabled', 'Disabled'),
    ]
    
    FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Source and target configuration
    source_type = models.CharField(max_length=50)  # database, api, file, etc.
    source_config = models.JSONField(default=dict)
    target_model = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    schedule_config = models.JSONField(default=dict)  # cron expression, specific times, etc.
    
    # Sync configuration
    mapping_config = models.JSONField(default=dict)
    sync_mode = models.CharField(max_length=20, default='incremental')  # full, incremental
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_sync_jobs'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DataBackup(models.Model):
    """Model for data backup management"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TYPE_CHOICES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('differential', 'Differential Backup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Backup configuration
    backup_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    models_to_backup = models.JSONField(default=list)
    backup_path = models.CharField(max_length=500)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration options
    compress_backup = models.BooleanField(default=True)
    encrypt_backup = models.BooleanField(default=False)
    retention_days = models.IntegerField(default=30)
    
    class Meta:
        db_table = 'data_backups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.backup_type})"


class DataAuditLog(models.Model):
    """Model for tracking data changes and operations"""
    
    ACTION_CHOICES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('sync', 'Sync'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
        ('transform', 'Transform'),
        ('validate', 'Validate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Operation information
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    operation_id = models.UUIDField()  # Reference to the job/operation
    
    # Target information
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')
    
    # Change details
    changes = models.JSONField(default=dict)
    old_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)
    
    # Metadata
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'data_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['operation_id']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"


class DataQualityRule(models.Model):
    """Model for defining data quality rules"""
    
    RULE_TYPE_CHOICES = [
        ('required', 'Required Field'),
        ('format', 'Format Validation'),
        ('range', 'Range Validation'),
        ('unique', 'Uniqueness Check'),
        ('reference', 'Reference Integrity'),
        ('custom', 'Custom Rule'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Rule configuration
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    target_model = models.CharField(max_length=100)
    target_field = models.CharField(max_length=100)
    rule_config = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, default='error')  # error, warning, info
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_quality_rules'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DataLineage(models.Model):
    """Model for tracking data lineage and dependencies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source information
    source_type = models.CharField(max_length=50)  # table, file, api, etc.
    source_name = models.CharField(max_length=200)
    source_field = models.CharField(max_length=100, blank=True)
    
    # Target information
    target_type = models.CharField(max_length=50)
    target_name = models.CharField(max_length=200)
    target_field = models.CharField(max_length=100, blank=True)
    
    # Transformation information
    transformation_type = models.CharField(max_length=50, blank=True)
    transformation_config = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'data_lineage'
        ordering = ['source_name', 'target_name']
        unique_together = ['source_name', 'source_field', 'target_name', 'target_field']
    
    def __str__(self):
        return f"{self.source_name} -> {self.target_name}"