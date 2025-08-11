from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import json

User = get_user_model()

class WorkflowTemplate(models.Model):
    """Template for reusable workflow definitions"""
    CATEGORY_CHOICES = [
        ('approval', 'Approval Process'),
        ('notification', 'Notification'),
        ('data_processing', 'Data Processing'),
        ('integration', 'System Integration'),
        ('customer_journey', 'Customer Journey'),
        ('supply_chain', 'Supply Chain'),
        ('financial', 'Financial Process'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    version = models.CharField(max_length=20, default='1.0.0')
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workflow_templates'
        ordering = ['-created_at']

class Workflow(models.Model):
    """Main workflow definition"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]
    
    TRIGGER_CHOICES = [
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('event', 'Event-based'),
        ('webhook', 'Webhook'),
        ('api', 'API Call'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='manual')
    trigger_config = models.JSONField(default=dict)
    workflow_definition = models.JSONField(default=dict)  # Visual workflow structure
    variables = models.JSONField(default=dict)  # Workflow variables
    settings = models.JSONField(default=dict)  # Workflow settings
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workflows'
        ordering = ['-created_at']

class WorkflowNode(models.Model):
    """Individual nodes in a workflow"""
    NODE_TYPES = [
        ('start', 'Start'),
        ('end', 'End'),
        ('task', 'Task'),
        ('decision', 'Decision'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('integration', 'Integration'),
        ('delay', 'Delay'),
        ('condition', 'Condition'),
        ('loop', 'Loop'),
        ('parallel', 'Parallel'),
        ('merge', 'Merge'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_id = models.CharField(max_length=100)  # Unique within workflow
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position = models.JSONField(default=dict)  # x, y coordinates
    config = models.JSONField(default=dict)  # Node-specific configuration
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_nodes'
        unique_together = ['workflow', 'node_id']

class WorkflowConnection(models.Model):
    """Connections between workflow nodes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='connections')
    source_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='outgoing_connections')
    target_node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE, related_name='incoming_connections')
    condition = models.JSONField(default=dict)  # Conditional logic for connection
    label = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_connections'

class WorkflowExecution(models.Model):
    """Workflow execution instance"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    trigger_data = models.JSONField(default=dict)
    execution_data = models.JSONField(default=dict)  # Runtime data
    current_node = models.ForeignKey(WorkflowNode, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Generic relation for associated objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        db_table = 'workflow_executions'
        ordering = ['-created_at']

class WorkflowExecutionLog(models.Model):
    """Log entries for workflow execution"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='logs')
    node = models.ForeignKey(WorkflowNode, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    message = models.TextField()
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_execution_logs'
        ordering = ['timestamp']

class WorkflowApproval(models.Model):
    """Approval requests within workflows"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='approvals')
    node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE)
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflow_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    comments = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'workflow_approvals'
        ordering = ['-requested_at']

class WorkflowSchedule(models.Model):
    """Scheduled workflow executions"""
    FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('cron', 'Cron Expression'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    cron_expression = models.CharField(max_length=100, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_schedules'

class WorkflowMetrics(models.Model):
    """Performance metrics for workflows"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    executions_count = models.IntegerField(default=0)
    successful_executions = models.IntegerField(default=0)
    failed_executions = models.IntegerField(default=0)
    average_duration = models.DurationField(null=True, blank=True)
    total_duration = models.DurationField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'workflow_metrics'
        unique_together = ['workflow', 'date']

class WorkflowIntegration(models.Model):
    """External system integrations"""
    INTEGRATION_TYPES = [
        ('api', 'REST API'),
        ('webhook', 'Webhook'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('database', 'Database'),
        ('file', 'File System'),
        ('ftp', 'FTP/SFTP'),
        ('cloud', 'Cloud Service'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    endpoint_url = models.URLField(blank=True)
    authentication = models.JSONField(default=dict)
    configuration = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_integrations'