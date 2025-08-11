from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Project, Task, Milestone, ProjectRisk, TimeEntry,
    ProjectDocument, ProjectComment, ProjectNotification,
    ProjectTemplate, ProjectMembership, TaskDependency
)
from .serializers import (
    ProjectSerializer, ProjectListSerializer, TaskSerializer,
    MilestoneSerializer, ProjectRiskSerializer, TimeEntrySerializer,
    ProjectDocumentSerializer, ProjectCommentSerializer,
    ProjectNotificationSerializer, ProjectTemplateSerializer,
    ProjectMembershipSerializer, TaskDependencySerializer,
    GanttChartSerializer, ProjectAnalyticsSerializer
)
from .services import ProjectAnalyticsService, GanttChartService, NotificationService


class ProjectTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all template categories"""
        categories = ProjectTemplate.objects.values_list('category', flat=True).distinct()
        return Response({'categories': list(categories)})


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        queryset = Project.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by project manager
        manager_id = self.request.query_params.get('manager_id')
        if manager_id:
            queryset = queryset.filter(project_manager_id=manager_id)
        
        # Filter by team member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            queryset = queryset.filter(team_members__id=member_id)
        
        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.select_related('project_manager', 'created_by', 'template')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def gantt_chart(self, request, pk=None):
        """Get Gantt chart data for the project"""
        project = self.get_object()
        service = GanttChartService()
        gantt_data = service.get_gantt_data(project)
        serializer = GanttChartSerializer(gantt_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get project analytics"""
        project = self.get_object()
        service = ProjectAnalyticsService()
        analytics_data = service.get_project_analytics(project)
        serializer = ProjectAnalyticsSerializer(analytics_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def critical_path(self, request, pk=None):
        """Get critical path analysis"""
        project = self.get_object()
        service = GanttChartService()
        critical_path = service.calculate_critical_path(project)
        return Response({'critical_path': critical_path})
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a team member to the project"""
        project = self.get_object()
        serializer = ProjectMembershipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a team member from the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        try:
            membership = ProjectMembership.objects.get(project=project, user_id=user_id)
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProjectMembership.DoesNotExist:
            return Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a project"""
        original_project = self.get_object()
        clone_data = request.data
        
        # Create new project
        new_project = Project.objects.create(
            name=clone_data.get('name', f"{original_project.name} (Copy)"),
            description=original_project.description,
            status='planning',
            priority=original_project.priority,
            start_date=clone_data.get('start_date', timezone.now().date()),
            end_date=clone_data.get('end_date', timezone.now().date() + timedelta(days=30)),
            budget=original_project.budget,
            project_manager=self.request.user,
            created_by=self.request.user,
            tags=original_project.tags,
            custom_fields=original_project.custom_fields
        )
        
        # Clone tasks if requested
        if clone_data.get('clone_tasks', False):
            self._clone_tasks(original_project, new_project)
        
        # Clone milestones if requested
        if clone_data.get('clone_milestones', False):
            self._clone_milestones(original_project, new_project)
        
        serializer = ProjectSerializer(new_project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _clone_tasks(self, original_project, new_project):
        """Helper method to clone tasks"""
        task_mapping = {}
        
        # First pass: create all tasks
        for task in original_project.tasks.all():
            new_task = Task.objects.create(
                project=new_project,
                title=task.title,
                description=task.description,
                priority=task.priority,
                start_date=task.start_date,
                due_date=task.due_date,
                estimated_hours=task.estimated_hours,
                tags=task.tags,
                custom_fields=task.custom_fields,
                created_by=self.request.user
            )
            task_mapping[task.id] = new_task
        
        # Second pass: set parent relationships
        for original_task in original_project.tasks.all():
            if original_task.parent_task:
                new_task = task_mapping[original_task.id]
                new_task.parent_task = task_mapping[original_task.parent_task.id]
                new_task.save()
    
    def _clone_milestones(self, original_project, new_project):
        """Helper method to clone milestones"""
        for milestone in original_project.milestones.all():
            Milestone.objects.create(
                project=new_project,
                name=milestone.name,
                description=milestone.description,
                due_date=milestone.due_date,
                created_by=self.request.user
            )
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        user = request.user
        
        # Projects where user is manager or team member
        user_projects = Project.objects.filter(
            Q(project_manager=user) | Q(team_members=user)
        ).distinct()
        
        stats = {
            'total_projects': user_projects.count(),
            'active_projects': user_projects.filter(status='active').count(),
            'completed_projects': user_projects.filter(status='completed').count(),
            'overdue_projects': user_projects.filter(
                end_date__lt=timezone.now().date(),
                status__in=['planning', 'active']
            ).count(),
            'total_tasks': Task.objects.filter(project__in=user_projects).count(),
            'assigned_tasks': Task.objects.filter(assignee=user).count(),
            'completed_tasks': Task.objects.filter(
                assignee=user, 
                status='completed'
            ).count(),
            'overdue_tasks': Task.objects.filter(
                assignee=user,
                due_date__lt=timezone.now().date(),
                status__in=['not_started', 'in_progress', 'blocked']
            ).count(),
        }
        
        return Response(stats)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Task.objects.all()
        
        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by assignee
        assignee_id = self.request.query_params.get('assignee_id')
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by due date
        due_date = self.request.query_params.get('due_date')
        if due_date:
            queryset = queryset.filter(due_date=due_date)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.select_related('project', 'assignee', 'reviewer', 'created_by', 'parent_task')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """Add a task dependency"""
        task = self.get_object()
        serializer = TaskDependencySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(successor=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def log_time(self, request, pk=None):
        """Log time for a task"""
        task = self.get_object()
        data = request.data.copy()
        data['task'] = task.id
        data['user_id'] = request.user.id
        
        serializer = TimeEntrySerializer(data=data)
        if serializer.is_valid():
            time_entry = serializer.save()
            
            # Update task actual hours
            total_hours = task.time_entries.aggregate(
                total=Sum('hours')
            )['total'] or Decimal('0.00')
            task.actual_hours = total_hours
            task.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status with notifications"""
        task = self.get_object()
        old_status = task.status
        new_status = request.data.get('status')
        
        if new_status and new_status != old_status:
            task.status = new_status
            
            # Set actual dates
            if new_status == 'in_progress' and not task.actual_start_date:
                task.actual_start_date = timezone.now().date()
            elif new_status == 'completed' and not task.actual_end_date:
                task.actual_end_date = timezone.now().date()
                task.progress_percentage = 100
            
            task.save()
            
            # Send notifications
            notification_service = NotificationService()
            notification_service.send_task_status_notification(task, old_status, new_status)
            
            serializer = TaskSerializer(task)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Milestone.objects.all()
        
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset.select_related('project', 'created_by')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        milestone.is_completed = True
        milestone.completed_date = timezone.now().date()
        milestone.save()
        
        # Send notifications
        notification_service = NotificationService()
        notification_service.send_milestone_notification(milestone)
        
        serializer = MilestoneSerializer(milestone)
        return Response(serializer.data)


class ProjectRiskViewSet(viewsets.ModelViewSet):
    queryset = ProjectRisk.objects.all()
    serializer_class = ProjectRiskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectRisk.objects.all()
        
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset.select_related('project', 'owner')


class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = TimeEntry.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by task
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(task__project_id=project_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.select_related('task', 'user', 'task__project')
    
    @action(detail=False, methods=['get'])
    def timesheet(self, request):
        """Get timesheet data for a user"""
        user_id = request.query_params.get('user_id', request.user.id)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = TimeEntry.objects.filter(user_id=user_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Group by date and project
        timesheet_data = {}
        for entry in queryset:
            date_str = entry.date.isoformat()
            if date_str not in timesheet_data:
                timesheet_data[date_str] = {}
            
            project_name = entry.task.project.name
            if project_name not in timesheet_data[date_str]:
                timesheet_data[date_str][project_name] = {
                    'total_hours': 0,
                    'entries': []
                }
            
            timesheet_data[date_str][project_name]['total_hours'] += float(entry.hours)
            timesheet_data[date_str][project_name]['entries'].append({
                'task': entry.task.title,
                'hours': float(entry.hours),
                'description': entry.description,
                'is_billable': entry.is_billable
            })
        
        return Response(timesheet_data)


class ProjectDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectDocument.objects.all()
        
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset.select_related('project', 'uploaded_by')
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ProjectCommentViewSet(viewsets.ModelViewSet):
    queryset = ProjectComment.objects.all()
    serializer_class = ProjectCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectComment.objects.all()
        
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        return queryset.select_related('author', 'project', 'task')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ProjectNotificationViewSet(viewsets.ModelViewSet):
    queryset = ProjectNotification.objects.all()
    serializer_class = ProjectNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProjectNotification.objects.filter(
            recipient=self.request.user
        ).select_related('project', 'task')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        serializer = ProjectNotificationSerializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        ProjectNotification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def portfolio_overview(self, request):
        """Get portfolio overview and analytics"""
        service = ProjectPortfolioService()
        overview = service.get_portfolio_overview(request.user)
        return Response(overview)
    
    @action(detail=False, methods=['post'])
    def prioritize_projects(self, request):
        """Prioritize projects based on criteria"""
        criteria = request.data.get('criteria', {})
        service = ProjectPortfolioService()
        prioritized = service.prioritize_projects(criteria)
        return Response({'prioritized_projects': prioritized})
    
    @action(detail=True, methods=['get'])
    def resource_allocation(self, request, pk=None):
        """Get resource allocation for project"""
        project = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        service = ResourceManagementService()
        allocation = service.get_resource_allocation(str(project.id), start_date, end_date)
        return Response(allocation)
    
    @action(detail=True, methods=['post'])
    def optimize_resources(self, request, pk=None):
        """Get resource optimization recommendations"""
        project = self.get_object()
        service = ResourceManagementService()
        optimization = service.optimize_resource_allocation(str(project.id))
        return Response(optimization)
    
    @action(detail=True, methods=['post'])
    def create_template(self, request, pk=None):
        """Create template from project"""
        project = self.get_object()
        template_data = request.data
        
        service = ProjectTemplateService()
        template = service.create_template_from_project(str(project.id), template_data, request.user)
        
        serializer = ProjectTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def export_data(self, request, pk=None):
        """Export project data"""
        project = self.get_object()
        format_type = request.query_params.get('format', 'json')
        
        service = ProjectIntegrationService()
        export_data = service.export_project_data(str(project.id), format_type)
        
        return Response(export_data)
    
    @action(detail=True, methods=['post'])
    def generate_reports(self, request, pk=None):
        """Generate project reports"""
        project = self.get_object()
        report_types = request.data.get('report_types', [])
        
        service = ProjectIntegrationService()
        reports = service.generate_project_reports(str(project.id), report_types)
        
        return Response(reports)
    
    @action(detail=True, methods=['post'])
    def auto_update_status(self, request, pk=None):
        """Auto-update project status based on task completion"""
        project = self.get_object()
        service = ProjectAutomationService()
        result = service.auto_update_project_status(str(project.id))
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def schedule_recurring_tasks(self, request, pk=None):
        """Schedule recurring tasks"""
        project = self.get_object()
        task_template = request.data.get('task_template', {})
        schedule = request.data.get('schedule', {})
        
        service = ProjectAutomationService()
        result = service.schedule_recurring_tasks(str(project.id), task_template, schedule)
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def template_recommendations(self, request):
        """Get project template recommendations"""
        project_type = request.query_params.get('project_type')
        budget_range = request.query_params.get('budget_range')
        
        service = ProjectTemplateService()
        recommendations = service.get_template_recommendations(project_type, budget_range)
        return Response({'recommendations': recommendations})


# Add new viewsets for enhanced functionality

class ResourceManagementViewSet(viewsets.ViewSet):
    """ViewSet for resource management operations"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def allocation_overview(self, request):
        """Get resource allocation overview"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        project_id = request.query_params.get('project_id')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        service = ResourceManagementService()
        allocation = service.get_resource_allocation(project_id, start_date, end_date)
        return Response(allocation)
    
    @action(detail=False, methods=['post'])
    def auto_assign_tasks(self, request):
        """Auto-assign tasks based on workload"""
        service = ProjectAutomationService()
        result = service.auto_assign_tasks_based_on_workload()
        return Response(result)


class ProjectAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for project analytics and insights"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        """Get dashboard metrics"""
        service = ProjectAnalyticsService()
        metrics = service.get_project_dashboard_metrics(request.user)
        return Response(metrics)
    
    @action(detail=False, methods=['get'])
    def team_performance(self, request):
        """Get team performance analytics"""
        service = ProjectAnalyticsService()
        performance = service.get_team_performance_analytics(request.user)
        return Response(performance)
    
    @action(detail=True, methods=['get'])
    def project_performance(self, request, pk=None):
        """Get specific project performance metrics"""
        service = ProjectAnalyticsService()
        performance = service.get_project_performance_metrics(pk)
        return Response(performance)


class GanttChartViewSet(viewsets.ViewSet):
    """ViewSet for Gantt chart and timeline operations"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def chart_data(self, request, pk=None):
        """Get Gantt chart data for project"""
        try:
            project = Project.objects.get(id=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        service = GanttChartService()
        gantt_data = service.get_gantt_data(project)
        return Response(gantt_data)
    
    @action(detail=True, methods=['get'])
    def critical_path(self, request, pk=None):
        """Get critical path analysis"""
        try:
            project = Project.objects.get(id=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        service = GanttChartService()
        critical_path = service.calculate_critical_path(project)
        return Response({'critical_path': critical_path})


class ProjectPortfolioViewSet(viewsets.ViewSet):
    """ViewSet for project portfolio management"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get portfolio overview"""
        service = ProjectPortfolioService()
        overview = service.get_portfolio_overview(request.user)
        return Response(overview)
    
    @action(detail=False, methods=['post'])
    def prioritize(self, request):
        """Prioritize projects"""
        criteria = request.data.get('criteria', {})
        service = ProjectPortfolioService()
        prioritized = service.prioritize_projects(criteria)
        return Response({'prioritized_projects': prioritized})


class ProjectAutomationViewSet(viewsets.ViewSet):
    """ViewSet for project automation features"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def auto_assign_tasks(self, request):
        """Auto-assign unassigned tasks"""
        service = ProjectAutomationService()
        result = service.auto_assign_tasks_based_on_workload()
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def update_project_status(self, request, pk=None):
        """Auto-update project status"""
        service = ProjectAutomationService()
        result = service.auto_update_project_status(pk)
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def schedule_recurring(self, request, pk=None):
        """Schedule recurring tasks"""
        task_template = request.data.get('task_template', {})
        schedule = request.data.get('schedule', {})
        
        service = ProjectAutomationService()
        result = service.schedule_recurring_tasks(pk, task_template, schedule)
        return Response(result)