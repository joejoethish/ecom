from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Project, Task, Milestone, ProjectRisk, TimeEntry, 
    ProjectDocument, ProjectComment, ProjectNotification,
    ProjectTemplate, ProjectMembership, TaskDependency
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ProjectTemplateSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ProjectTemplate
        fields = '__all__'


class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'user_id', 'role', 'hourly_rate', 'joined_at']


class TaskDependencySerializer(serializers.ModelSerializer):
    predecessor_title = serializers.CharField(source='predecessor.title', read_only=True)
    successor_title = serializers.CharField(source='successor.title', read_only=True)
    
    class Meta:
        model = TaskDependency
        fields = ['id', 'predecessor', 'successor', 'predecessor_title', 'successor_title', 
                 'dependency_type', 'lag_days']


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer = UserSerializer(read_only=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    parent_task_title = serializers.CharField(source='parent_task.title', read_only=True)
    subtasks_count = serializers.SerializerMethodField()
    dependencies = TaskDependencySerializer(source='predecessor_dependencies', many=True, read_only=True)
    time_entries_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = '__all__'
    
    def get_subtasks_count(self, obj):
        return obj.subtasks.count()
    
    def get_time_entries_count(self, obj):
        return obj.time_entries.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class MilestoneSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = '__all__'
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()


class ProjectRiskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    risk_score = serializers.ReadOnlyField()
    
    class Meta:
        model = ProjectRisk
        fields = '__all__'


class TimeEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    project_name = serializers.CharField(source='task.project.name', read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = '__all__'


class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectDocument
        fields = '__all__'


class ProjectCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectComment
        fields = '__all__'
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return ProjectCommentSerializer(obj.replies.all(), many=True).data
        return []


class ProjectNotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = ProjectNotification
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    project_manager = UserSerializer(read_only=True)
    project_manager_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    template = ProjectTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    # Computed fields
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    overdue_tasks_count = serializers.SerializerMethodField()
    team_members_count = serializers.SerializerMethodField()
    milestones_count = serializers.SerializerMethodField()
    risks_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    total_hours_logged = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    # Related data (optional)
    team_members = ProjectMembershipSerializer(source='projectmembership_set', many=True, read_only=True)
    recent_tasks = serializers.SerializerMethodField()
    upcoming_milestones = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_completed_tasks_count(self, obj):
        return obj.tasks.filter(status='completed').count()
    
    def get_overdue_tasks_count(self, obj):
        from django.utils import timezone
        return obj.tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['not_started', 'in_progress', 'blocked']
        ).count()
    
    def get_team_members_count(self, obj):
        return obj.team_members.count()
    
    def get_milestones_count(self, obj):
        return obj.milestones.count()
    
    def get_risks_count(self, obj):
        return obj.risks.count()
    
    def get_documents_count(self, obj):
        return obj.documents.count()
    
    def get_total_hours_logged(self, obj):
        from django.db.models import Sum
        total = obj.tasks.aggregate(
            total_hours=Sum('time_entries__hours')
        )['total_hours']
        return float(total) if total else 0.0
    
    def get_recent_tasks(self, obj):
        recent_tasks = obj.tasks.order_by('-updated_at')[:5]
        return TaskSerializer(recent_tasks, many=True).data
    
    def get_upcoming_milestones(self, obj):
        from django.utils import timezone
        upcoming = obj.milestones.filter(
            due_date__gte=timezone.now().date(),
            is_completed=False
        ).order_by('due_date')[:3]
        return MilestoneSerializer(upcoming, many=True).data


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists"""
    project_manager = UserSerializer(read_only=True)
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    team_members_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'priority', 'start_date', 
            'end_date', 'progress_percentage', 'budget', 'actual_cost',
            'project_manager', 'tasks_count', 'completed_tasks_count', 
            'team_members_count', 'is_overdue', 'days_remaining', 'created_at'
        ]
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_completed_tasks_count(self, obj):
        return obj.tasks.filter(status='completed').count()
    
    def get_team_members_count(self, obj):
        return obj.team_members.count()


class GanttChartSerializer(serializers.Serializer):
    """Serializer for Gantt chart data"""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    tasks = serializers.SerializerMethodField()
    milestones = serializers.SerializerMethodField()
    
    def get_tasks(self, obj):
        tasks_data = []
        for task in obj.tasks.all():
            tasks_data.append({
                'id': str(task.id),
                'title': task.title,
                'start_date': task.start_date,
                'due_date': task.due_date,
                'actual_start_date': task.actual_start_date,
                'actual_end_date': task.actual_end_date,
                'progress_percentage': task.progress_percentage,
                'status': task.status,
                'assignee': task.assignee.username if task.assignee else None,
                'parent_task_id': str(task.parent_task.id) if task.parent_task else None,
                'dependencies': [
                    {
                        'predecessor_id': str(dep.predecessor.id),
                        'dependency_type': dep.dependency_type,
                        'lag_days': dep.lag_days
                    }
                    for dep in task.predecessor_dependencies.all()
                ]
            })
        return tasks_data
    
    def get_milestones(self, obj):
        milestones_data = []
        for milestone in obj.milestones.all():
            milestones_data.append({
                'id': str(milestone.id),
                'name': milestone.name,
                'due_date': milestone.due_date,
                'is_completed': milestone.is_completed,
                'completed_date': milestone.completed_date
            })
        return milestones_data


class ProjectAnalyticsSerializer(serializers.Serializer):
    """Serializer for project analytics data"""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    
    # Progress metrics
    overall_progress = serializers.FloatField()
    tasks_completed = serializers.IntegerField()
    tasks_total = serializers.IntegerField()
    milestones_completed = serializers.IntegerField()
    milestones_total = serializers.IntegerField()
    
    # Time metrics
    estimated_hours = serializers.FloatField()
    actual_hours = serializers.FloatField()
    hours_variance = serializers.FloatField()
    
    # Budget metrics
    budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    actual_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    budget_variance = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Risk metrics
    total_risks = serializers.IntegerField()
    high_risks = serializers.IntegerField()
    critical_risks = serializers.IntegerField()
    
    # Team metrics
    team_size = serializers.IntegerField()
    active_team_members = serializers.IntegerField()
    
    # Timeline metrics
    days_elapsed = serializers.IntegerField()
    days_remaining = serializers.IntegerField()
    is_on_schedule = serializers.BooleanField()
    is_overdue = serializers.BooleanField()

class ResourceAllocationSerializer(serializers.Serializer):
    """Serializer for resource allocation data"""
    user = UserSerializer()
    total_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    utilization_percentage = serializers.FloatField()
    available_hours = serializers.FloatField()
    is_overallocated = serializers.BooleanField()
    projects = serializers.DictField()
    tasks = serializers.ListField()


class ProjectPrioritizationSerializer(serializers.Serializer):
    """Serializer for project prioritization data"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
    total_score = serializers.FloatField()
    budget_score = serializers.FloatField()
    timeline_score = serializers.FloatField()
    risk_score = serializers.FloatField()
    strategic_score = serializers.FloatField()
    budget = serializers.FloatField()
    end_date = serializers.DateField()
    days_remaining = serializers.IntegerField()


class PortfolioOverviewSerializer(serializers.Serializer):
    """Serializer for portfolio overview data"""
    portfolio_metrics = serializers.DictField()
    status_distribution = serializers.DictField()
    priority_distribution = serializers.DictField()
    risk_analysis = serializers.DictField()
    timeline_analysis = serializers.DictField()


class CriticalPathSerializer(serializers.Serializer):
    """Serializer for critical path analysis"""
    task_id = serializers.UUIDField()
    task_title = serializers.CharField()
    early_start = serializers.IntegerField()
    early_finish = serializers.IntegerField()
    late_start = serializers.IntegerField()
    late_finish = serializers.IntegerField()
    slack = serializers.IntegerField()
    is_critical = serializers.BooleanField()


class ProjectExportSerializer(serializers.Serializer):
    """Serializer for project export data"""
    project = serializers.DictField()
    tasks = serializers.ListField()
    milestones = serializers.ListField()
    team_members = serializers.ListField()
    risks = serializers.ListField()
    time_entries = serializers.ListField()
    documents = serializers.ListField()
    export_metadata = serializers.DictField()


class ProjectReportsSerializer(serializers.Serializer):
    """Serializer for project reports"""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    generated_at = serializers.DateTimeField()
    reports = serializers.DictField()


class TaskWorkloadSerializer(serializers.Serializer):
    """Serializer for task workload data"""
    user = UserSerializer()
    date_range = serializers.DictField()
    workload_by_day = serializers.DictField()
    total_tasks = serializers.IntegerField()
    total_estimated_hours = serializers.DecimalField(max_digits=8, decimal_places=2)


class ProjectAutomationResultSerializer(serializers.Serializer):
    """Serializer for automation results"""
    project_id = serializers.UUIDField()
    old_status = serializers.CharField()
    new_status = serializers.CharField()
    completion_rate = serializers.FloatField()
    status_changed = serializers.BooleanField()


class RecurringTaskScheduleSerializer(serializers.Serializer):
    """Serializer for recurring task schedule"""
    project_id = serializers.UUIDField()
    tasks_created = serializers.IntegerField()
    tasks = serializers.ListField()
    schedule = serializers.DictField()


class TemplateRecommendationSerializer(serializers.Serializer):
    """Serializer for template recommendations"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    estimated_duration_days = serializers.IntegerField()
    task_count = serializers.IntegerField()
    milestone_count = serializers.IntegerField()
    risk_count = serializers.IntegerField()
    usage_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    created_by = serializers.CharField()
    created_at = serializers.DateTimeField()


class ProjectQualityMetricsSerializer(serializers.Serializer):
    """Serializer for project quality metrics"""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    quality_score = serializers.FloatField()
    on_time_delivery_rate = serializers.FloatField()
    budget_adherence_rate = serializers.FloatField()
    scope_change_rate = serializers.FloatField()
    defect_rate = serializers.FloatField()
    customer_satisfaction_score = serializers.FloatField()
    team_satisfaction_score = serializers.FloatField()


class StakeholderCommunicationSerializer(serializers.Serializer):
    """Serializer for stakeholder communication data"""
    stakeholder_id = serializers.IntegerField()
    stakeholder_name = serializers.CharField()
    role = serializers.CharField()
    communication_frequency = serializers.CharField()
    preferred_method = serializers.CharField()
    last_communication = serializers.DateTimeField()
    satisfaction_level = serializers.IntegerField()


class ProjectChangeRequestSerializer(serializers.Serializer):
    """Serializer for project change requests"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    requested_by = UserSerializer()
    impact_assessment = serializers.DictField()
    status = serializers.CharField()
    approval_date = serializers.DateTimeField()
    implementation_date = serializers.DateTimeField()


class ProjectLessonsLearnedSerializer(serializers.Serializer):
    """Serializer for project lessons learned"""
    id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    category = serializers.CharField()
    lesson_title = serializers.CharField()
    description = serializers.CharField()
    what_worked_well = serializers.CharField()
    what_could_improve = serializers.CharField()
    recommendations = serializers.CharField()
    created_by = UserSerializer()
    created_at = serializers.DateTimeField()


class ProjectCapacityPlanningSerializer(serializers.Serializer):
    """Serializer for capacity planning data"""
    period = serializers.CharField()
    total_capacity_hours = serializers.FloatField()
    allocated_hours = serializers.FloatField()
    available_hours = serializers.FloatField()
    utilization_rate = serializers.FloatField()
    resource_gaps = serializers.ListField()
    recommendations = serializers.ListField()