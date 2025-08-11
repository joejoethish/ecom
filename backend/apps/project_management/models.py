from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from decimal import Decimal


class ProjectStatus(models.TextChoices):
    PLANNING = 'planning', 'Planning'
    ACTIVE = 'active', 'Active'
    ON_HOLD = 'on_hold', 'On Hold'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class TaskStatus(models.TextChoices):
    NOT_STARTED = 'not_started', 'Not Started'
    IN_PROGRESS = 'in_progress', 'In Progress'
    BLOCKED = 'blocked', 'Blocked'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Priority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class RiskLevel(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class ProjectTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    template_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_templates'
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PLANNING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Budget and Cost
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Team
    project_manager = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_projects'
    )
    team_members = models.ManyToManyField(
        User, 
        through='ProjectMembership',
        related_name='projects'
    )
    
    # Template
    template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Metadata
    tags = models.JSONField(default=list)
    custom_fields = models.JSONField(default=dict)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.end_date < timezone.now().date() and self.status != ProjectStatus.COMPLETED

    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.status == ProjectStatus.COMPLETED:
            return 0
        return (self.end_date - timezone.now().date()).days


class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Project Manager'),
        ('lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('tester', 'Tester'),
        ('analyst', 'Business Analyst'),
        ('stakeholder', 'Stakeholder'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_memberships'
        unique_together = ['project', 'user']


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    
    # Basic Info
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.NOT_STARTED)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Assignment
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_tasks')
    
    # Dates and Time
    start_date = models.DateField()
    due_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Dependencies
    dependencies = models.ManyToManyField('self', through='TaskDependency', symmetrical=False)
    
    # Metadata
    tags = models.JSONField(default=list)
    custom_fields = models.JSONField(default=dict)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['due_date', 'priority']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status != TaskStatus.COMPLETED


class TaskDependency(models.Model):
    DEPENDENCY_TYPES = [
        ('finish_to_start', 'Finish to Start'),
        ('start_to_start', 'Start to Start'),
        ('finish_to_finish', 'Finish to Finish'),
        ('start_to_finish', 'Start to Finish'),
    ]
    
    predecessor = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='successor_dependencies')
    successor = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='predecessor_dependencies')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPES, default='finish_to_start')
    lag_days = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'task_dependencies'
        unique_together = ['predecessor', 'successor']


class Milestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    
    # Associated tasks
    tasks = models.ManyToManyField(Task, blank=True, related_name='milestones')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'milestones'
        ordering = ['due_date']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ProjectRisk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    probability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Probability from 1-10"
    )
    impact = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Impact from 1-10"
    )
    mitigation_plan = models.TextField()
    contingency_plan = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_risks')
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('monitoring', 'Monitoring'),
        ('mitigated', 'Mitigated'),
        ('closed', 'Closed'),
    ], default='open')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_risks'
        ordering = ['-probability', '-impact']

    @property
    def risk_score(self):
        return self.probability * self.impact


class TimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.TextField()
    is_billable = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'time_entries'
        ordering = ['-date']


class ProjectDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='project_documents/')
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)
    version = models.CharField(max_length=20, default='1.0')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_documents'
        ordering = ['-created_at']


class ProjectComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_comments'
        ordering = ['-created_at']


class ProjectNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('milestone_reached', 'Milestone Reached'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('project_status_changed', 'Project Status Changed'),
        ('comment_added', 'Comment Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_notifications'
        ordering = ['-created_at']


class ProjectStakeholder(models.Model):
    """Model for project stakeholders"""
    COMMUNICATION_FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('as_needed', 'As Needed'),
    ]
    
    COMMUNICATION_METHOD_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('meeting', 'Meeting'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('dashboard', 'Dashboard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    role = models.CharField(max_length=100)
    organization = models.CharField(max_length=200, blank=True)
    communication_frequency = models.CharField(max_length=20, choices=COMMUNICATION_FREQUENCY_CHOICES, default='weekly')
    preferred_method = models.CharField(max_length=20, choices=COMMUNICATION_METHOD_CHOICES, default='email')
    influence_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Influence level from 1-5"
    )
    interest_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Interest level from 1-5"
    )
    last_communication = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_stakeholders'
        unique_together = ['project', 'email']

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class ProjectChangeRequest(models.Model):
    """Model for project change requests"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('cancelled', 'Cancelled'),
    ]
    
    IMPACT_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    justification = models.TextField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_changes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    # Impact assessment
    scope_impact = models.CharField(max_length=20, choices=IMPACT_LEVEL_CHOICES, default='medium')
    timeline_impact_days = models.IntegerField(default=0)
    budget_impact = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    resource_impact = models.CharField(max_length=20, choices=IMPACT_LEVEL_CHOICES, default='medium')
    risk_impact = models.CharField(max_length=20, choices=IMPACT_LEVEL_CHOICES, default='medium')
    
    # Approval workflow
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_changes')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_changes')
    approval_date = models.DateTimeField(null=True, blank=True)
    implementation_date = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    affected_tasks = models.ManyToManyField(Task, blank=True, related_name='change_requests')
    affected_milestones = models.ManyToManyField(Milestone, blank=True, related_name='change_requests')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_change_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.project.name}"


class ProjectLessonsLearned(models.Model):
    """Model for capturing project lessons learned"""
    CATEGORY_CHOICES = [
        ('planning', 'Planning'),
        ('execution', 'Execution'),
        ('monitoring', 'Monitoring'),
        ('communication', 'Communication'),
        ('risk_management', 'Risk Management'),
        ('resource_management', 'Resource Management'),
        ('quality', 'Quality'),
        ('stakeholder_management', 'Stakeholder Management'),
        ('technology', 'Technology'),
        ('process', 'Process'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='lessons_learned')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    lesson_title = models.CharField(max_length=200)
    description = models.TextField()
    what_worked_well = models.TextField()
    what_could_improve = models.TextField()
    recommendations = models.TextField()
    impact_level = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_lessons_learned'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lesson_title} - {self.project.name}"


class ProjectQualityMetrics(models.Model):
    """Model for tracking project quality metrics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='quality_metrics')
    
    # Quality scores (0-100)
    overall_quality_score = models.FloatField(default=0.0)
    on_time_delivery_rate = models.FloatField(default=0.0)
    budget_adherence_rate = models.FloatField(default=0.0)
    scope_change_rate = models.FloatField(default=0.0)
    defect_rate = models.FloatField(default=0.0)
    customer_satisfaction_score = models.FloatField(default=0.0)
    team_satisfaction_score = models.FloatField(default=0.0)
    
    # Metrics tracking
    total_deliverables = models.IntegerField(default=0)
    delivered_on_time = models.IntegerField(default=0)
    total_defects = models.IntegerField(default=0)
    resolved_defects = models.IntegerField(default=0)
    scope_changes = models.IntegerField(default=0)
    
    # Dates
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_quality_metrics'

    def calculate_quality_score(self):
        """Calculate overall quality score based on metrics"""
        scores = [
            self.on_time_delivery_rate,
            self.budget_adherence_rate,
            100 - self.scope_change_rate,  # Lower scope change is better
            100 - self.defect_rate,  # Lower defect rate is better
            self.customer_satisfaction_score,
            self.team_satisfaction_score,
        ]
        
        # Filter out zero scores and calculate average
        valid_scores = [score for score in scores if score > 0]
        if valid_scores:
            self.overall_quality_score = sum(valid_scores) / len(valid_scores)
        else:
            self.overall_quality_score = 0.0
        
        self.save()
        return self.overall_quality_score


class ProjectCapacityPlan(models.Model):
    """Model for project capacity planning"""
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='capacity_plans')
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='weekly')
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Capacity metrics
    total_capacity_hours = models.FloatField(default=0.0)
    allocated_hours = models.FloatField(default=0.0)
    available_hours = models.FloatField(default=0.0)
    utilization_rate = models.FloatField(default=0.0)
    
    # Resource requirements
    required_developers = models.IntegerField(default=0)
    required_designers = models.IntegerField(default=0)
    required_testers = models.IntegerField(default=0)
    required_analysts = models.IntegerField(default=0)
    
    # Gaps and recommendations
    resource_gaps = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_capacity_plans'
        unique_together = ['project', 'period_start', 'period_end']
        ordering = ['period_start']

    def __str__(self):
        return f"{self.project.name} - {self.period_start} to {self.period_end}"


class ProjectIntegration(models.Model):
    """Model for external tool integrations"""
    INTEGRATION_TYPES = [
        ('jira', 'Jira'),
        ('github', 'GitHub'),
        ('gitlab', 'GitLab'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('confluence', 'Confluence'),
        ('trello', 'Trello'),
        ('asana', 'Asana'),
        ('monday', 'Monday.com'),
        ('notion', 'Notion'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('pending', 'Pending Setup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='integrations')
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuration
    config_data = models.JSONField(default=dict)
    api_endpoint = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency_minutes = models.IntegerField(default=60)
    error_message = models.TextField(blank=True)
    
    # Sync statistics
    total_syncs = models.IntegerField(default=0)
    successful_syncs = models.IntegerField(default=0)
    failed_syncs = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_integrations'
        unique_together = ['project', 'integration_type', 'name']

    def __str__(self):
        return f"{self.project.name} - {self.get_integration_type_display()}"

    @property
    def success_rate(self):
        """Calculate integration success rate"""
        if self.total_syncs == 0:
            return 0.0
        return (self.successful_syncs / self.total_syncs) * 100