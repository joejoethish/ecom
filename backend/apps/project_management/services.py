from django.db.models import Sum, Count, Avg, Q, F, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    Project, Task, ProjectTemplate, ProjectMembership, Milestone, 
    ProjectRisk, TimeEntry, ProjectDocument, ProjectComment, 
    ProjectNotification, TaskDependency, ProjectStatus, TaskStatus, Priority
)


class ProjectAnalyticsService:
    """Service for project analytics and reporting"""
    
    @staticmethod
    def get_project_dashboard_metrics(user: User = None) -> Dict[str, Any]:
        """Get comprehensive project dashboard metrics"""
        queryset = Project.objects.all()
        if user and not user.is_superuser:
            queryset = queryset.filter(
                Q(project_manager=user) | Q(team_members=user)
            ).distinct()
        
        total_projects = queryset.count()
        active_projects = queryset.filter(status=ProjectStatus.ACTIVE).count()
        completed_projects = queryset.filter(status=ProjectStatus.COMPLETED).count()
        overdue_projects = queryset.filter(
            end_date__lt=timezone.now().date(),
            status__in=[ProjectStatus.ACTIVE, ProjectStatus.PLANNING]
        ).count()
        
        # Budget analysis
        budget_data = queryset.aggregate(
            total_budget=Sum('budget'),
            total_actual_cost=Sum('actual_cost')
        )
        
        # Progress analysis
        avg_progress = queryset.aggregate(
            avg_progress=Avg('progress_percentage')
        )['avg_progress'] or 0
        
        # Status distribution
        status_distribution = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'overdue_projects': overdue_projects,
            'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0,
            'average_progress': round(avg_progress, 2),
            'total_budget': budget_data['total_budget'] or Decimal('0.00'),
            'total_actual_cost': budget_data['total_actual_cost'] or Decimal('0.00'),
            'budget_variance': (budget_data['total_budget'] or Decimal('0.00')) - (budget_data['total_actual_cost'] or Decimal('0.00')),
            'status_distribution': list(status_distribution),
        }
    
    @staticmethod
    def get_project_performance_metrics(project_id: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific project"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        # Task metrics
        tasks = project.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status=TaskStatus.COMPLETED).count()
        overdue_tasks = tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
        ).count()
        
        # Time tracking
        time_data = TimeEntry.objects.filter(task__project=project).aggregate(
            total_hours=Sum('hours'),
            billable_hours=Sum('hours', filter=Q(is_billable=True))
        )
        
        # Budget performance
        budget_utilization = (project.actual_cost / project.budget * 100) if project.budget > 0 else 0
        
        # Team productivity
        team_productivity = ProjectMembership.objects.filter(project=project).annotate(
            completed_tasks=Count('user__assigned_tasks', filter=Q(user__assigned_tasks__status=TaskStatus.COMPLETED)),
            total_hours=Sum('user__time_entries__hours', filter=Q(user__time_entries__task__project=project))
        ).values('user__username', 'role', 'completed_tasks', 'total_hours')
        
        return {
            'project_name': project.name,
            'status': project.status,
            'progress_percentage': project.progress_percentage,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'overdue_tasks': overdue_tasks,
            'total_hours': time_data['total_hours'] or Decimal('0.00'),
            'billable_hours': time_data['billable_hours'] or Decimal('0.00'),
            'budget': project.budget,
            'actual_cost': project.actual_cost,
            'budget_utilization': round(budget_utilization, 2),
            'budget_variance': project.budget - project.actual_cost,
            'team_productivity': list(team_productivity),
            'is_overdue': project.is_overdue,
            'days_remaining': project.days_remaining,
        }
    
    @staticmethod
    def get_team_performance_analytics(user: User = None) -> Dict[str, Any]:
        """Get team performance analytics"""
        queryset = User.objects.filter(projects__isnull=False).distinct()
        
        team_stats = []
        for member in queryset:
            # Get user's project involvement
            managed_projects = member.managed_projects.count()
            member_projects = member.projects.count()
            
            # Task performance
            assigned_tasks = member.assigned_tasks.count()
            completed_tasks = member.assigned_tasks.filter(status=TaskStatus.COMPLETED).count()
            overdue_tasks = member.assigned_tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
            ).count()
            
            # Time tracking
            total_hours = member.time_entries.aggregate(
                total=Sum('hours')
            )['total'] or Decimal('0.00')
            
            team_stats.append({
                'user_id': member.id,
                'username': member.username,
                'full_name': f"{member.first_name} {member.last_name}".strip(),
                'managed_projects': managed_projects,
                'member_projects': member_projects,
                'assigned_tasks': assigned_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': (completed_tasks / assigned_tasks * 100) if assigned_tasks > 0 else 0,
                'overdue_tasks': overdue_tasks,
                'total_hours': total_hours,
            })
        
        return {
            'team_members': team_stats,
            'total_team_size': len(team_stats),
        }


class ProjectManagementService:
    """Service for project management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_project_from_template(template_id: str, project_data: Dict[str, Any], user: User) -> Project:
        """Create a new project from a template"""
        try:
            template = ProjectTemplate.objects.get(id=template_id)
        except ProjectTemplate.DoesNotExist:
            raise ValidationError("Template not found")
        
        # Create project
        project = Project.objects.create(
            name=project_data['name'],
            description=project_data.get('description', ''),
            start_date=project_data['start_date'],
            end_date=project_data['end_date'],
            budget=project_data.get('budget', Decimal('0.00')),
            priority=project_data.get('priority', Priority.MEDIUM),
            project_manager=user,
            template=template,
            created_by=user
        )
        
        # Apply template data
        template_data = template.template_data
        
        # Create tasks from template
        if 'tasks' in template_data:
            for task_data in template_data['tasks']:
                Task.objects.create(
                    project=project,
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    priority=task_data.get('priority', Priority.MEDIUM),
                    start_date=project.start_date,
                    due_date=project.end_date,
                    estimated_hours=task_data.get('estimated_hours', Decimal('0.00')),
                    created_by=user
                )
        
        # Create milestones from template
        if 'milestones' in template_data:
            for milestone_data in template_data['milestones']:
                Milestone.objects.create(
                    project=project,
                    name=milestone_data['name'],
                    description=milestone_data.get('description', ''),
                    due_date=project.end_date,
                    created_by=user
                )
        
        return project
    
    @staticmethod
    @transaction.atomic
    def update_project_progress(project_id: str) -> Project:
        """Update project progress based on task completion"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ValidationError("Project not found")
        
        tasks = project.tasks.all()
        if tasks.exists():
            avg_progress = tasks.aggregate(
                avg_progress=Avg('progress_percentage')
            )['avg_progress'] or 0
            project.progress_percentage = round(avg_progress)
            project.save()
        
        return project
    
    @staticmethod
    def get_project_timeline(project_id: str) -> Dict[str, Any]:
        """Get project timeline with tasks and milestones"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        # Get tasks with dependencies
        tasks = project.tasks.select_related('assignee').prefetch_related('dependencies').all()
        task_data = []
        
        for task in tasks:
            dependencies = list(task.dependencies.values_list('id', flat=True))
            task_data.append({
                'id': str(task.id),
                'title': task.title,
                'start_date': task.start_date.isoformat(),
                'due_date': task.due_date.isoformat(),
                'progress': task.progress_percentage,
                'assignee': task.assignee.username if task.assignee else None,
                'status': task.status,
                'priority': task.priority,
                'dependencies': [str(dep_id) for dep_id in dependencies],
            })
        
        # Get milestones
        milestones = project.milestones.all()
        milestone_data = []
        
        for milestone in milestones:
            milestone_data.append({
                'id': str(milestone.id),
                'name': milestone.name,
                'due_date': milestone.due_date.isoformat(),
                'is_completed': milestone.is_completed,
                'completed_date': milestone.completed_date.isoformat() if milestone.completed_date else None,
            })
        
        return {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'start_date': project.start_date.isoformat(),
                'end_date': project.end_date.isoformat(),
                'status': project.status,
                'progress': project.progress_percentage,
            },
            'tasks': task_data,
            'milestones': milestone_data,
        }


class TaskManagementService:
    """Service for task management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_task_with_dependencies(task_data: Dict[str, Any], dependencies: List[str], user: User) -> Task:
        """Create a task with dependencies"""
        # Create the task
        task = Task.objects.create(
            project_id=task_data['project_id'],
            title=task_data['title'],
            description=task_data.get('description', ''),
            priority=task_data.get('priority', Priority.MEDIUM),
            start_date=task_data['start_date'],
            due_date=task_data['due_date'],
            estimated_hours=task_data.get('estimated_hours', Decimal('0.00')),
            assignee_id=task_data.get('assignee_id'),
            created_by=user
        )
        
        # Add dependencies
        for dep_id in dependencies:
            try:
                predecessor = Task.objects.get(id=dep_id)
                TaskDependency.objects.create(
                    predecessor=predecessor,
                    successor=task,
                    dependency_type='finish_to_start'
                )
            except Task.DoesNotExist:
                continue
        
        return task
    
    @staticmethod
    def get_task_dependencies_graph(project_id: str) -> Dict[str, Any]:
        """Get task dependencies as a graph structure"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        tasks = project.tasks.all()
        dependencies = TaskDependency.objects.filter(
            predecessor__project=project,
            successor__project=project
        )
        
        # Build nodes
        nodes = []
        for task in tasks:
            nodes.append({
                'id': str(task.id),
                'title': task.title,
                'status': task.status,
                'assignee': task.assignee.username if task.assignee else None,
                'start_date': task.start_date.isoformat(),
                'due_date': task.due_date.isoformat(),
                'progress': task.progress_percentage,
            })
        
        # Build edges
        edges = []
        for dep in dependencies:
            edges.append({
                'from': str(dep.predecessor.id),
                'to': str(dep.successor.id),
                'type': dep.dependency_type,
                'lag_days': dep.lag_days,
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
        }
    
    @staticmethod
    def get_user_task_workload(user_id: int, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get user's task workload for a date range"""
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {}
        
        # Get tasks in date range
        tasks = user.assigned_tasks.filter(
            start_date__lte=end_date,
            due_date__gte=start_date
        ).select_related('project')
        
        # Calculate workload by day
        workload_by_day = {}
        for task in tasks:
            task_start = max(task.start_date, start_date)
            task_end = min(task.due_date, end_date)
            
            # Distribute estimated hours across task duration
            task_days = (task_end - task_start).days + 1
            hours_per_day = task.estimated_hours / task_days if task_days > 0 else task.estimated_hours
            
            current_date = task_start
            while current_date <= task_end:
                date_str = current_date.isoformat()
                if date_str not in workload_by_day:
                    workload_by_day[date_str] = {
                        'total_hours': Decimal('0.00'),
                        'tasks': []
                    }
                
                workload_by_day[date_str]['total_hours'] += hours_per_day
                workload_by_day[date_str]['tasks'].append({
                    'id': str(task.id),
                    'title': task.title,
                    'project': task.project.name,
                    'hours': hours_per_day,
                    'priority': task.priority,
                    'status': task.status,
                })
                
                current_date += timedelta(days=1)
        
        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
            },
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'workload_by_day': workload_by_day,
            'total_tasks': tasks.count(),
            'total_estimated_hours': tasks.aggregate(total=Sum('estimated_hours'))['total'] or Decimal('0.00'),
        }


class RiskManagementService:
    """Service for project risk management"""
    
    @staticmethod
    def assess_project_risks(project_id: str) -> Dict[str, Any]:
        """Assess and analyze project risks"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        risks = project.risks.all()
        
        # Risk analysis
        total_risks = risks.count()
        high_risks = risks.filter(risk_level__in=['high', 'critical']).count()
        open_risks = risks.filter(status='open').count()
        
        # Risk score distribution
        risk_scores = [risk.risk_score for risk in risks]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Risk by category
        risk_by_level = risks.values('risk_level').annotate(
            count=Count('id'),
            avg_score=Avg(F('probability') * F('impact'))
        ).order_by('-avg_score')
        
        return {
            'project_name': project.name,
            'total_risks': total_risks,
            'high_risks': high_risks,
            'open_risks': open_risks,
            'average_risk_score': round(avg_risk_score, 2),
            'risk_distribution': list(risk_by_level),
            'risk_details': [
                {
                    'id': str(risk.id),
                    'title': risk.title,
                    'risk_level': risk.risk_level,
                    'probability': risk.probability,
                    'impact': risk.impact,
                    'risk_score': risk.risk_score,
                    'status': risk.status,
                    'owner': risk.owner.username,
                }
                for risk in risks.select_related('owner')
            ]
        }
    
    @staticmethod
    def get_risk_mitigation_recommendations(risk_id: str) -> Dict[str, Any]:
        """Get risk mitigation recommendations"""
        try:
            risk = ProjectRisk.objects.get(id=risk_id)
        except ProjectRisk.DoesNotExist:
            return {}
        
        # Basic recommendations based on risk score and type
        recommendations = []
        
        if risk.risk_score >= 50:  # High risk
            recommendations.extend([
                "Immediate attention required - assign dedicated risk owner",
                "Develop detailed contingency plan with specific actions",
                "Schedule weekly risk review meetings",
                "Consider project scope or timeline adjustments",
            ])
        elif risk.risk_score >= 25:  # Medium risk
            recommendations.extend([
                "Monitor closely and update mitigation plan",
                "Schedule bi-weekly risk reviews",
                "Prepare contingency resources",
            ])
        else:  # Low risk
            recommendations.extend([
                "Continue monitoring with monthly reviews",
                "Document lessons learned for future projects",
            ])
        
        return {
            'risk': {
                'id': str(risk.id),
                'title': risk.title,
                'risk_score': risk.risk_score,
                'risk_level': risk.risk_level,
            },
            'recommendations': recommendations,
            'current_mitigation_plan': risk.mitigation_plan,
            'current_contingency_plan': risk.contingency_plan,
        }


class ReportingService:
    """Service for generating project reports"""
    
    @staticmethod
    def generate_project_status_report(project_id: str) -> Dict[str, Any]:
        """Generate comprehensive project status report"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        # Basic project info
        report = {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'priority': project.priority,
                'progress_percentage': project.progress_percentage,
                'start_date': project.start_date.isoformat(),
                'end_date': project.end_date.isoformat(),
                'budget': project.budget,
                'actual_cost': project.actual_cost,
                'project_manager': project.project_manager.username,
                'is_overdue': project.is_overdue,
                'days_remaining': project.days_remaining,
            }
        }
        
        # Task summary
        tasks = project.tasks.all()
        task_summary = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status=TaskStatus.COMPLETED).count(),
            'in_progress_tasks': tasks.filter(status=TaskStatus.IN_PROGRESS).count(),
            'not_started_tasks': tasks.filter(status=TaskStatus.NOT_STARTED).count(),
            'blocked_tasks': tasks.filter(status=TaskStatus.BLOCKED).count(),
            'overdue_tasks': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
            ).count(),
        }
        report['task_summary'] = task_summary
        
        # Team summary
        team_members = ProjectMembership.objects.filter(project=project).select_related('user')
        team_summary = []
        for membership in team_members:
            user_tasks = tasks.filter(assignee=membership.user)
            team_summary.append({
                'user': membership.user.username,
                'role': membership.role,
                'assigned_tasks': user_tasks.count(),
                'completed_tasks': user_tasks.filter(status=TaskStatus.COMPLETED).count(),
                'total_hours': membership.user.time_entries.filter(
                    task__project=project
                ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00'),
            })
        report['team_summary'] = team_summary
        
        # Milestone summary
        milestones = project.milestones.all()
        milestone_summary = {
            'total_milestones': milestones.count(),
            'completed_milestones': milestones.filter(is_completed=True).count(),
            'upcoming_milestones': milestones.filter(
                is_completed=False,
                due_date__gte=timezone.now().date()
            ).count(),
            'overdue_milestones': milestones.filter(
                is_completed=False,
                due_date__lt=timezone.now().date()
            ).count(),
        }
        report['milestone_summary'] = milestone_summary
        
        # Risk summary
        risks = project.risks.all()
        risk_summary = {
            'total_risks': risks.count(),
            'high_risks': risks.filter(risk_level__in=['high', 'critical']).count(),
            'open_risks': risks.filter(status='open').count(),
            'average_risk_score': risks.aggregate(
                avg_score=Avg(F('probability') * F('impact'))
            )['avg_score'] or 0,
        }
        report['risk_summary'] = risk_summary
        
        # Financial summary
        financial_summary = {
            'budget': project.budget,
            'actual_cost': project.actual_cost,
            'budget_variance': project.budget - project.actual_cost,
            'budget_utilization': (project.actual_cost / project.budget * 100) if project.budget > 0 else 0,
        }
        report['financial_summary'] = financial_summary
        
        report['generated_at'] = timezone.now().isoformat()
        
        return report
    
    @staticmethod
    def generate_team_productivity_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate team productivity report for a date range"""
        # Get all users with project involvement
        users = User.objects.filter(
            Q(managed_projects__isnull=False) | 
            Q(projects__isnull=False) |
            Q(assigned_tasks__isnull=False)
        ).distinct()
        
        report = {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'team_productivity': []
        }
        
        for user in users:
            # Time entries in date range
            time_entries = user.time_entries.filter(
                date__range=[start_date, end_date]
            )
            
            # Tasks completed in date range
            completed_tasks = user.assigned_tasks.filter(
                actual_end_date__range=[start_date, end_date],
                status=TaskStatus.COMPLETED
            )
            
            # Current assignments
            current_tasks = user.assigned_tasks.filter(
                status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS]
            )
            
            productivity_data = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                },
                'total_hours': time_entries.aggregate(total=Sum('hours'))['total'] or Decimal('0.00'),
                'billable_hours': time_entries.filter(is_billable=True).aggregate(
                    total=Sum('hours')
                )['total'] or Decimal('0.00'),
                'completed_tasks': completed_tasks.count(),
                'current_tasks': current_tasks.count(),
                'projects_involved': user.projects.count(),
                'managed_projects': user.managed_projects.count(),
            }
            
            report['team_productivity'].append(productivity_data)
        
        # Sort by total hours descending
        report['team_productivity'].sort(key=lambda x: x['total_hours'], reverse=True)
        
        return report


class NotificationService:
    """Service for project notifications"""
    
    @staticmethod
    def create_task_assignment_notification(task: Task):
        """Create notification when task is assigned"""
        if task.assignee:
            ProjectNotification.objects.create(
                recipient=task.assignee,
                notification_type='task_assigned',
                title=f'New Task Assigned: {task.title}',
                message=f'You have been assigned a new task "{task.title}" in project "{task.project.name}".',
                project=task.project,
                task=task
            )
    
    @staticmethod
    def create_deadline_notifications():
        """Create notifications for approaching deadlines"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        next_week = timezone.now().date() + timedelta(days=7)
        
        # Tasks due tomorrow
        tasks_due_tomorrow = Task.objects.filter(
            due_date=tomorrow,
            status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS],
            assignee__isnull=False
        ).select_related('assignee', 'project')
        
        for task in tasks_due_tomorrow:
            ProjectNotification.objects.get_or_create(
                recipient=task.assignee,
                notification_type='deadline_approaching',
                title=f'Task Due Tomorrow: {task.title}',
                message=f'Your task "{task.title}" in project "{task.project.name}" is due tomorrow.',
                project=task.project,
                task=task,
                defaults={'created_at': timezone.now()}
            )
        
        # Projects ending next week
        projects_ending = Project.objects.filter(
            end_date__lte=next_week,
            end_date__gt=timezone.now().date(),
            status=ProjectStatus.ACTIVE
        ).select_related('project_manager')
        
        for project in projects_ending:
            ProjectNotification.objects.get_or_create(
                recipient=project.project_manager,
                notification_type='deadline_approaching',
                title=f'Project Deadline Approaching: {project.name}',
                message=f'Project "{project.name}" is scheduled to end on {project.end_date}.',
                project=project,
                defaults={'created_at': timezone.now()}
            )
    
    @staticmethod
    def get_user_notifications(user: User, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        queryset = user.project_notifications.select_related('project', 'task')
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        notifications = []
        for notification in queryset.order_by('-created_at')[:50]:  # Limit to 50 most recent
            notifications.append({
                'id': str(notification.id),
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'project': {
                    'id': str(notification.project.id),
                    'name': notification.project.name,
                } if notification.project else None,
                'task': {
                    'id': str(notification.task.id),
                    'title': notification.task.title,
                } if notification.task else None,
            })
        
        return notifications

class GanttChartService:
    """Service for Gantt chart and timeline visualization"""
    
    @staticmethod
    def get_gantt_data(project: Project) -> Dict[str, Any]:
        """Get comprehensive Gantt chart data"""
        tasks = project.tasks.select_related('assignee', 'parent_task').prefetch_related('dependencies').all()
        milestones = project.milestones.all()
        
        # Build task hierarchy
        task_hierarchy = []
        root_tasks = tasks.filter(parent_task__isnull=True)
        
        for task in root_tasks:
            task_data = GanttChartService._build_task_node(task, tasks)
            task_hierarchy.append(task_data)
        
        # Calculate critical path
        critical_path = GanttChartService.calculate_critical_path(project)
        
        return {
            'project_id': str(project.id),
            'project_name': project.name,
            'project_start': project.start_date,
            'project_end': project.end_date,
            'tasks': task_hierarchy,
            'milestones': [
                {
                    'id': str(milestone.id),
                    'name': milestone.name,
                    'due_date': milestone.due_date,
                    'is_completed': milestone.is_completed,
                    'completed_date': milestone.completed_date,
                }
                for milestone in milestones
            ],
            'critical_path': critical_path,
            'timeline_stats': GanttChartService._calculate_timeline_stats(project)
        }
    
    @staticmethod
    def _build_task_node(task: Task, all_tasks) -> Dict[str, Any]:
        """Build task node with children"""
        subtasks = [t for t in all_tasks if t.parent_task_id == task.id]
        
        return {
            'id': str(task.id),
            'title': task.title,
            'start_date': task.start_date,
            'due_date': task.due_date,
            'actual_start_date': task.actual_start_date,
            'actual_end_date': task.actual_end_date,
            'progress_percentage': task.progress_percentage,
            'status': task.status,
            'priority': task.priority,
            'assignee': task.assignee.username if task.assignee else None,
            'estimated_hours': float(task.estimated_hours),
            'actual_hours': float(task.actual_hours),
            'dependencies': [
                {
                    'predecessor_id': str(dep.predecessor.id),
                    'dependency_type': dep.dependency_type,
                    'lag_days': dep.lag_days
                }
                for dep in task.predecessor_dependencies.all()
            ],
            'children': [GanttChartService._build_task_node(subtask, all_tasks) for subtask in subtasks],
            'is_milestone': False,
            'is_critical': False,  # Will be updated by critical path calculation
        }
    
    @staticmethod
    def calculate_critical_path(project: Project) -> List[str]:
        """Calculate critical path using CPM algorithm"""
        tasks = project.tasks.all()
        task_dict = {str(task.id): task for task in tasks}
        
        # Build dependency graph
        graph = {}
        for task in tasks:
            task_id = str(task.id)
            graph[task_id] = {
                'duration': (task.due_date - task.start_date).days,
                'predecessors': [str(dep.predecessor.id) for dep in task.predecessor_dependencies.all()],
                'successors': [str(dep.successor.id) for dep in task.successor_dependencies.all()],
                'early_start': 0,
                'early_finish': 0,
                'late_start': 0,
                'late_finish': 0,
                'slack': 0
            }
        
        # Forward pass - calculate early start and finish
        for task_id in graph:
            if not graph[task_id]['predecessors']:
                graph[task_id]['early_start'] = 0
            else:
                max_early_finish = max(
                    graph[pred_id]['early_finish'] 
                    for pred_id in graph[task_id]['predecessors']
                )
                graph[task_id]['early_start'] = max_early_finish
            
            graph[task_id]['early_finish'] = graph[task_id]['early_start'] + graph[task_id]['duration']
        
        # Find project duration
        project_duration = max(graph[task_id]['early_finish'] for task_id in graph)
        
        # Backward pass - calculate late start and finish
        for task_id in reversed(list(graph.keys())):
            if not graph[task_id]['successors']:
                graph[task_id]['late_finish'] = project_duration
            else:
                min_late_start = min(
                    graph[succ_id]['late_start'] 
                    for succ_id in graph[task_id]['successors']
                )
                graph[task_id]['late_finish'] = min_late_start
            
            graph[task_id]['late_start'] = graph[task_id]['late_finish'] - graph[task_id]['duration']
            graph[task_id]['slack'] = graph[task_id]['late_start'] - graph[task_id]['early_start']
        
        # Find critical path (tasks with zero slack)
        critical_path = [task_id for task_id in graph if graph[task_id]['slack'] == 0]
        
        return critical_path
    
    @staticmethod
    def _calculate_timeline_stats(project: Project) -> Dict[str, Any]:
        """Calculate timeline statistics"""
        tasks = project.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status=TaskStatus.COMPLETED).count()
        
        # Calculate schedule performance
        on_time_tasks = tasks.filter(
            status=TaskStatus.COMPLETED,
            actual_end_date__lte=F('due_date')
        ).count()
        
        overdue_tasks = tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
        ).count()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'on_time_tasks': on_time_tasks,
            'on_time_rate': (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0,
            'overdue_tasks': overdue_tasks,
            'project_duration_days': (project.end_date - project.start_date).days,
            'elapsed_days': (timezone.now().date() - project.start_date).days,
            'remaining_days': (project.end_date - timezone.now().date()).days,
        }


class ResourceManagementService:
    """Service for resource allocation and capacity management"""
    
    @staticmethod
    def get_resource_allocation(project_id: str = None, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get resource allocation analysis"""
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # Filter tasks by project if specified
        tasks_query = Task.objects.filter(
            start_date__lte=end_date,
            due_date__gte=start_date
        )
        
        if project_id:
            tasks_query = tasks_query.filter(project_id=project_id)
        
        tasks = tasks_query.select_related('assignee', 'project').all()
        
        # Group by user
        user_allocations = {}
        for task in tasks:
            if not task.assignee:
                continue
                
            user_id = task.assignee.id
            if user_id not in user_allocations:
                user_allocations[user_id] = {
                    'user': {
                        'id': user_id,
                        'username': task.assignee.username,
                        'full_name': f"{task.assignee.first_name} {task.assignee.last_name}".strip(),
                    },
                    'total_hours': Decimal('0.00'),
                    'projects': {},
                    'tasks': []
                }
            
            user_allocations[user_id]['total_hours'] += task.estimated_hours
            user_allocations[user_id]['tasks'].append({
                'id': str(task.id),
                'title': task.title,
                'project': task.project.name,
                'estimated_hours': float(task.estimated_hours),
                'start_date': task.start_date,
                'due_date': task.due_date,
                'status': task.status,
                'priority': task.priority,
            })
            
            # Group by project
            project_name = task.project.name
            if project_name not in user_allocations[user_id]['projects']:
                user_allocations[user_id]['projects'][project_name] = Decimal('0.00')
            user_allocations[user_id]['projects'][project_name] += task.estimated_hours
        
        # Calculate capacity utilization (assuming 40 hours per week)
        working_days = (end_date - start_date).days
        working_hours_available = working_days * 8  # 8 hours per day
        
        for user_id in user_allocations:
            allocation = user_allocations[user_id]
            utilization = (float(allocation['total_hours']) / working_hours_available * 100) if working_hours_available > 0 else 0
            allocation['utilization_percentage'] = round(utilization, 2)
            allocation['available_hours'] = working_hours_available - float(allocation['total_hours'])
            allocation['is_overallocated'] = utilization > 100
        
        return {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'resource_allocations': list(user_allocations.values()),
            'summary': {
                'total_users': len(user_allocations),
                'overallocated_users': sum(1 for alloc in user_allocations.values() if alloc['is_overallocated']),
                'total_allocated_hours': sum(float(alloc['total_hours']) for alloc in user_allocations.values()),
                'average_utilization': sum(alloc['utilization_percentage'] for alloc in user_allocations.values()) / len(user_allocations) if user_allocations else 0,
            }
        }
    
    @staticmethod
    def optimize_resource_allocation(project_id: str) -> Dict[str, Any]:
        """Suggest resource allocation optimizations"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        tasks = project.tasks.filter(status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS])
        team_members = project.team_members.all()
        
        # Calculate current workload for each team member
        member_workloads = {}
        for member in team_members:
            current_tasks = member.assigned_tasks.filter(
                project=project,
                status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS]
            )
            total_hours = current_tasks.aggregate(total=Sum('estimated_hours'))['total'] or Decimal('0.00')
            
            member_workloads[member.id] = {
                'user': member,
                'current_hours': total_hours,
                'current_tasks': current_tasks.count(),
                'capacity_score': float(total_hours),  # Simplified capacity scoring
            }
        
        # Find unassigned tasks
        unassigned_tasks = tasks.filter(assignee__isnull=True)
        
        # Generate recommendations
        recommendations = []
        
        # Recommend assignments for unassigned tasks
        for task in unassigned_tasks:
            # Find team member with lowest workload
            best_member = min(member_workloads.values(), key=lambda x: x['capacity_score'])
            
            recommendations.append({
                'type': 'assignment',
                'task_id': str(task.id),
                'task_title': task.title,
                'recommended_assignee': best_member['user'].username,
                'reason': f"Lowest current workload ({best_member['current_hours']} hours)",
                'priority': task.priority,
            })
            
            # Update workload for next iteration
            best_member['capacity_score'] += float(task.estimated_hours)
        
        # Find overloaded team members
        avg_workload = sum(data['capacity_score'] for data in member_workloads.values()) / len(member_workloads) if member_workloads else 0
        
        for member_data in member_workloads.values():
            if member_data['capacity_score'] > avg_workload * 1.5:  # 50% above average
                recommendations.append({
                    'type': 'rebalance',
                    'user': member_data['user'].username,
                    'current_hours': member_data['current_hours'],
                    'reason': f"Workload {member_data['capacity_score']:.1f} hours is above average ({avg_workload:.1f})",
                    'suggestion': "Consider redistributing some tasks to other team members",
                })
        
        return {
            'project_name': project.name,
            'team_size': len(member_workloads),
            'unassigned_tasks': unassigned_tasks.count(),
            'average_workload': round(avg_workload, 2),
            'recommendations': recommendations,
            'workload_distribution': [
                {
                    'user': data['user'].username,
                    'current_hours': float(data['current_hours']),
                    'current_tasks': data['current_tasks'],
                    'utilization_vs_average': (data['capacity_score'] / avg_workload * 100) if avg_workload > 0 else 0,
                }
                for data in member_workloads.values()
            ]
        }


class ProjectPortfolioService:
    """Service for project portfolio management and prioritization"""
    
    @staticmethod
    def get_portfolio_overview(user: User = None) -> Dict[str, Any]:
        """Get comprehensive portfolio overview"""
        queryset = Project.objects.all()
        if user and not user.is_superuser:
            queryset = queryset.filter(
                Q(project_manager=user) | Q(team_members=user)
            ).distinct()
        
        projects = queryset.select_related('project_manager').prefetch_related('team_members').all()
        
        # Portfolio metrics
        total_projects = len(projects)
        total_budget = sum(p.budget for p in projects)
        total_actual_cost = sum(p.actual_cost for p in projects)
        
        # Status distribution
        status_counts = {}
        for status_choice in ProjectStatus.choices:
            status_counts[status_choice[0]] = sum(1 for p in projects if p.status == status_choice[0])
        
        # Priority distribution
        priority_counts = {}
        for priority_choice in Priority.choices:
            priority_counts[priority_choice[0]] = sum(1 for p in projects if p.priority == priority_choice[0])
        
        # Risk analysis
        high_risk_projects = []
        for project in projects:
            risk_score = project.risks.aggregate(
                avg_score=Avg(F('probability') * F('impact'))
            )['avg_score'] or 0
            
            if risk_score > 50:  # High risk threshold
                high_risk_projects.append({
                    'id': str(project.id),
                    'name': project.name,
                    'risk_score': round(risk_score, 2),
                    'status': project.status,
                })
        
        # Resource utilization
        total_team_members = User.objects.filter(projects__in=projects).distinct().count()
        
        # Timeline analysis
        overdue_projects = [p for p in projects if p.is_overdue]
        upcoming_deadlines = [
            p for p in projects 
            if p.end_date <= timezone.now().date() + timedelta(days=30) and not p.is_overdue
        ]
        
        return {
            'portfolio_metrics': {
                'total_projects': total_projects,
                'total_budget': total_budget,
                'total_actual_cost': total_actual_cost,
                'budget_variance': total_budget - total_actual_cost,
                'total_team_members': total_team_members,
            },
            'status_distribution': status_counts,
            'priority_distribution': priority_counts,
            'risk_analysis': {
                'high_risk_projects_count': len(high_risk_projects),
                'high_risk_projects': high_risk_projects,
            },
            'timeline_analysis': {
                'overdue_projects_count': len(overdue_projects),
                'overdue_projects': [
                    {
                        'id': str(p.id),
                        'name': p.name,
                        'end_date': p.end_date,
                        'days_overdue': (timezone.now().date() - p.end_date).days,
                    }
                    for p in overdue_projects
                ],
                'upcoming_deadlines_count': len(upcoming_deadlines),
                'upcoming_deadlines': [
                    {
                        'id': str(p.id),
                        'name': p.name,
                        'end_date': p.end_date,
                        'days_remaining': p.days_remaining,
                    }
                    for p in upcoming_deadlines
                ],
            }
        }
    
    @staticmethod
    def prioritize_projects(criteria: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Prioritize projects based on multiple criteria"""
        if not criteria:
            criteria = {
                'budget_weight': 0.3,
                'timeline_weight': 0.2,
                'risk_weight': 0.2,
                'strategic_weight': 0.3,
            }
        
        projects = Project.objects.filter(status__in=[ProjectStatus.PLANNING, ProjectStatus.ACTIVE]).all()
        
        prioritized_projects = []
        for project in projects:
            # Calculate scores for each criterion
            budget_score = min(float(project.budget) / 1000000, 10)  # Normalize to 0-10 scale
            
            timeline_score = 10 - min((project.end_date - timezone.now().date()).days / 365 * 10, 10)
            
            risk_score = project.risks.aggregate(
                avg_score=Avg(F('probability') * F('impact'))
            )['avg_score'] or 0
            risk_score = 10 - (risk_score / 10)  # Invert so lower risk = higher score
            
            # Strategic importance based on priority
            strategic_score = {
                Priority.CRITICAL: 10,
                Priority.HIGH: 7,
                Priority.MEDIUM: 5,
                Priority.LOW: 2,
            }.get(project.priority, 5)
            
            # Calculate weighted total score
            total_score = (
                budget_score * criteria['budget_weight'] +
                timeline_score * criteria['timeline_weight'] +
                risk_score * criteria['risk_weight'] +
                strategic_score * criteria['strategic_weight']
            )
            
            prioritized_projects.append({
                'id': str(project.id),
                'name': project.name,
                'status': project.status,
                'priority': project.priority,
                'total_score': round(total_score, 2),
                'budget_score': round(budget_score, 2),
                'timeline_score': round(timeline_score, 2),
                'risk_score': round(risk_score, 2),
                'strategic_score': strategic_score,
                'budget': float(project.budget),
                'end_date': project.end_date,
                'days_remaining': project.days_remaining,
            })
        
        # Sort by total score descending
        prioritized_projects.sort(key=lambda x: x['total_score'], reverse=True)
        
        return prioritized_projects


class ProjectTemplateService:
    """Service for project template management and best practices"""
    
    @staticmethod
    def create_template_from_project(project_id: str, template_data: Dict[str, Any], user: User) -> ProjectTemplate:
        """Create a template from an existing project"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ValidationError("Project not found")
        
        # Extract template data from project
        template_structure = {
            'project_settings': {
                'default_priority': project.priority,
                'estimated_duration_days': (project.end_date - project.start_date).days,
                'budget_template': float(project.budget),
            },
            'tasks': [],
            'milestones': [],
            'risks': [],
            'team_roles': [],
        }
        
        # Extract tasks
        for task in project.tasks.all():
            task_template = {
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'estimated_hours': float(task.estimated_hours),
                'relative_start_day': (task.start_date - project.start_date).days,
                'relative_due_day': (task.due_date - project.start_date).days,
                'tags': task.tags,
                'parent_task_title': task.parent_task.title if task.parent_task else None,
            }
            template_structure['tasks'].append(task_template)
        
        # Extract milestones
        for milestone in project.milestones.all():
            milestone_template = {
                'name': milestone.name,
                'description': milestone.description,
                'relative_due_day': (milestone.due_date - project.start_date).days,
            }
            template_structure['milestones'].append(milestone_template)
        
        # Extract common risks
        for risk in project.risks.all():
            risk_template = {
                'title': risk.title,
                'description': risk.description,
                'risk_level': risk.risk_level,
                'probability': risk.probability,
                'impact': risk.impact,
                'mitigation_plan': risk.mitigation_plan,
                'contingency_plan': risk.contingency_plan,
            }
            template_structure['risks'].append(risk_template)
        
        # Extract team roles
        for membership in project.projectmembership_set.all():
            if membership.role not in [role['role'] for role in template_structure['team_roles']]:
                template_structure['team_roles'].append({
                    'role': membership.role,
                    'hourly_rate': float(membership.hourly_rate) if membership.hourly_rate else None,
                })
        
        # Create template
        template = ProjectTemplate.objects.create(
            name=template_data['name'],
            description=template_data.get('description', f"Template created from project: {project.name}"),
            category=template_data.get('category', 'Custom'),
            template_data=template_structure,
            created_by=user
        )
        
        return template
    
    @staticmethod
    def get_template_recommendations(project_type: str = None, budget_range: str = None) -> List[Dict[str, Any]]:
        """Get template recommendations based on criteria"""
        templates = ProjectTemplate.objects.filter(is_active=True)
        
        if project_type:
            templates = templates.filter(category__icontains=project_type)
        
        recommendations = []
        for template in templates:
            # Calculate template metrics
            template_data = template.template_data
            
            estimated_duration = template_data.get('project_settings', {}).get('estimated_duration_days', 0)
            task_count = len(template_data.get('tasks', []))
            milestone_count = len(template_data.get('milestones', []))
            risk_count = len(template_data.get('risks', []))
            
            # Usage statistics
            usage_count = Project.objects.filter(template=template).count()
            success_rate = Project.objects.filter(
                template=template,
                status=ProjectStatus.COMPLETED
            ).count() / usage_count * 100 if usage_count > 0 else 0
            
            recommendations.append({
                'id': str(template.id),
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'estimated_duration_days': estimated_duration,
                'task_count': task_count,
                'milestone_count': milestone_count,
                'risk_count': risk_count,
                'usage_count': usage_count,
                'success_rate': round(success_rate, 2),
                'created_by': template.created_by.username,
                'created_at': template.created_at,
            })
        
        # Sort by success rate and usage count
        recommendations.sort(key=lambda x: (x['success_rate'], x['usage_count']), reverse=True)
        
        return recommendations


class ProjectIntegrationService:
    """Service for project integration with external tools and systems"""
    
    @staticmethod
    def export_project_data(project_id: str, format_type: str = 'json') -> Dict[str, Any]:
        """Export project data in various formats"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        # Gather all project data
        project_data = {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'priority': project.priority,
                'start_date': project.start_date.isoformat(),
                'end_date': project.end_date.isoformat(),
                'budget': float(project.budget),
                'actual_cost': float(project.actual_cost),
                'progress_percentage': project.progress_percentage,
                'project_manager': project.project_manager.username,
                'tags': project.tags,
                'custom_fields': project.custom_fields,
            },
            'tasks': [],
            'milestones': [],
            'team_members': [],
            'risks': [],
            'time_entries': [],
            'documents': [],
        }
        
        # Export tasks
        for task in project.tasks.all():
            task_data = {
                'id': str(task.id),
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'start_date': task.start_date.isoformat(),
                'due_date': task.due_date.isoformat(),
                'estimated_hours': float(task.estimated_hours),
                'actual_hours': float(task.actual_hours),
                'progress_percentage': task.progress_percentage,
                'assignee': task.assignee.username if task.assignee else None,
                'parent_task_id': str(task.parent_task.id) if task.parent_task else None,
                'tags': task.tags,
                'dependencies': [
                    {
                        'predecessor_id': str(dep.predecessor.id),
                        'dependency_type': dep.dependency_type,
                        'lag_days': dep.lag_days,
                    }
                    for dep in task.predecessor_dependencies.all()
                ]
            }
            project_data['tasks'].append(task_data)
        
        # Export milestones
        for milestone in project.milestones.all():
            milestone_data = {
                'id': str(milestone.id),
                'name': milestone.name,
                'description': milestone.description,
                'due_date': milestone.due_date.isoformat(),
                'is_completed': milestone.is_completed,
                'completed_date': milestone.completed_date.isoformat() if milestone.completed_date else None,
            }
            project_data['milestones'].append(milestone_data)
        
        # Export team members
        for membership in project.projectmembership_set.all():
            member_data = {
                'user_id': membership.user.id,
                'username': membership.user.username,
                'full_name': f"{membership.user.first_name} {membership.user.last_name}".strip(),
                'email': membership.user.email,
                'role': membership.role,
                'hourly_rate': float(membership.hourly_rate) if membership.hourly_rate else None,
                'joined_at': membership.joined_at.isoformat(),
            }
            project_data['team_members'].append(member_data)
        
        # Export risks
        for risk in project.risks.all():
            risk_data = {
                'id': str(risk.id),
                'title': risk.title,
                'description': risk.description,
                'risk_level': risk.risk_level,
                'probability': risk.probability,
                'impact': risk.impact,
                'risk_score': risk.risk_score,
                'status': risk.status,
                'mitigation_plan': risk.mitigation_plan,
                'contingency_plan': risk.contingency_plan,
                'owner': risk.owner.username,
            }
            project_data['risks'].append(risk_data)
        
        # Export time entries
        for time_entry in TimeEntry.objects.filter(task__project=project):
            time_data = {
                'id': str(time_entry.id),
                'task_id': str(time_entry.task.id),
                'user': time_entry.user.username,
                'date': time_entry.date.isoformat(),
                'hours': float(time_entry.hours),
                'description': time_entry.description,
                'is_billable': time_entry.is_billable,
            }
            project_data['time_entries'].append(time_data)
        
        # Export documents
        for document in project.documents.all():
            doc_data = {
                'id': str(document.id),
                'name': document.name,
                'description': document.description,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'version': document.version,
                'uploaded_by': document.uploaded_by.username,
                'created_at': document.created_at.isoformat(),
            }
            project_data['documents'].append(doc_data)
        
        project_data['export_metadata'] = {
            'exported_at': timezone.now().isoformat(),
            'format': format_type,
            'version': '1.0',
        }
        
        return project_data
    
    @staticmethod
    def generate_project_reports(project_id: str, report_types: List[str] = None) -> Dict[str, Any]:
        """Generate various project reports"""
        if not report_types:
            report_types = ['status', 'financial', 'resource', 'risk', 'timeline']
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        reports = {}
        
        if 'status' in report_types:
            reports['status_report'] = ReportingService.generate_project_status_report(project_id)
        
        if 'financial' in report_types:
            reports['financial_report'] = ProjectAnalyticsService.get_project_performance_metrics(project_id)
        
        if 'resource' in report_types:
            reports['resource_report'] = ResourceManagementService.get_resource_allocation(project_id)
        
        if 'risk' in report_types:
            reports['risk_report'] = RiskManagementService.assess_project_risks(project_id)
        
        if 'timeline' in report_types:
            reports['timeline_report'] = GanttChartService.get_gantt_data(project)
        
        return {
            'project_id': project_id,
            'project_name': project.name,
            'generated_at': timezone.now().isoformat(),
            'reports': reports,
        }


class ProjectAutomationService:
    """Service for project automation and workflow integration"""
    
    @staticmethod
    def auto_update_project_status(project_id: str) -> Dict[str, Any]:
        """Automatically update project status based on task completion"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        tasks = project.tasks.all()
        if not tasks.exists():
            return {'message': 'No tasks found for project'}
        
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status=TaskStatus.COMPLETED).count()
        completion_rate = completed_tasks / total_tasks * 100
        
        old_status = project.status
        new_status = old_status
        
        # Auto-update status based on completion rate
        if completion_rate == 100:
            new_status = ProjectStatus.COMPLETED
            if not project.actual_end_date:
                project.actual_end_date = timezone.now().date()
        elif completion_rate > 0 and project.status == ProjectStatus.PLANNING:
            new_status = ProjectStatus.ACTIVE
            if not project.actual_start_date:
                project.actual_start_date = timezone.now().date()
        
        # Update progress percentage
        project.progress_percentage = round(completion_rate)
        
        if new_status != old_status:
            project.status = new_status
            project.save()
            
            # Send notifications
            NotificationService.create_project_status_notification(project, old_status, new_status)
        else:
            project.save()
        
        return {
            'project_id': str(project.id),
            'old_status': old_status,
            'new_status': new_status,
            'completion_rate': completion_rate,
            'status_changed': new_status != old_status,
        }
    
    @staticmethod
    def auto_assign_tasks_based_on_workload() -> Dict[str, Any]:
        """Automatically assign unassigned tasks based on team member workload"""
        unassigned_tasks = Task.objects.filter(
            assignee__isnull=True,
            status=TaskStatus.NOT_STARTED
        ).select_related('project')
        
        assignments_made = []
        
        for task in unassigned_tasks:
            # Get project team members
            team_members = task.project.team_members.all()
            
            if not team_members.exists():
                continue
            
            # Calculate current workload for each team member
            member_workloads = []
            for member in team_members:
                current_workload = member.assigned_tasks.filter(
                    status__in=[TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS]
                ).aggregate(total_hours=Sum('estimated_hours'))['total_hours'] or Decimal('0.00')
                
                member_workloads.append({
                    'member': member,
                    'workload': current_workload,
                })
            
            # Assign to member with lowest workload
            if member_workloads:
                best_member = min(member_workloads, key=lambda x: x['workload'])
                task.assignee = best_member['member']
                task.save()
                
                # Create notification
                NotificationService.create_task_assignment_notification(task)
                
                assignments_made.append({
                    'task_id': str(task.id),
                    'task_title': task.title,
                    'assigned_to': best_member['member'].username,
                    'previous_workload': float(best_member['workload']),
                })
        
        return {
            'assignments_made': len(assignments_made),
            'assignments': assignments_made,
        }
    
    @staticmethod
    def schedule_recurring_tasks(project_id: str, task_template: Dict[str, Any], schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule recurring tasks based on template and schedule"""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {}
        
        # Parse schedule
        frequency = schedule.get('frequency', 'weekly')  # daily, weekly, monthly
        interval = schedule.get('interval', 1)  # every N periods
        end_date = datetime.strptime(schedule.get('end_date'), '%Y-%m-%d').date() if schedule.get('end_date') else project.end_date
        
        created_tasks = []
        current_date = timezone.now().date()
        
        while current_date <= end_date:
            # Create task
            task = Task.objects.create(
                project=project,
                title=f"{task_template['title']} - {current_date.strftime('%Y-%m-%d')}",
                description=task_template.get('description', ''),
                priority=task_template.get('priority', Priority.MEDIUM),
                start_date=current_date,
                due_date=current_date + timedelta(days=task_template.get('duration_days', 1)),
                estimated_hours=task_template.get('estimated_hours', Decimal('1.00')),
                assignee_id=task_template.get('assignee_id'),
                created_by_id=task_template.get('created_by_id'),
                tags=task_template.get('tags', []),
            )
            
            created_tasks.append({
                'id': str(task.id),
                'title': task.title,
                'start_date': task.start_date,
                'due_date': task.due_date,
            })
            
            # Calculate next date
            if frequency == 'daily':
                current_date += timedelta(days=interval)
            elif frequency == 'weekly':
                current_date += timedelta(weeks=interval)
            elif frequency == 'monthly':
                # Approximate monthly increment
                current_date += timedelta(days=30 * interval)
        
        return {
            'project_id': str(project.id),
            'tasks_created': len(created_tasks),
            'tasks': created_tasks,
            'schedule': schedule,
        }   
 
    @staticmethod
    def send_task_status_notification(task: Task, old_status: str, new_status: str):
        """Send notification when task status changes"""
        if task.assignee:
            ProjectNotification.objects.create(
                recipient=task.assignee,
                notification_type='task_completed' if new_status == TaskStatus.COMPLETED else 'project_status_changed',
                title=f'Task Status Updated: {task.title}',
                message=f'Task "{task.title}" status changed from {old_status} to {new_status}.',
                project=task.project,
                task=task
            )
    
    @staticmethod
    def send_milestone_notification(milestone: Milestone):
        """Send notification when milestone is completed"""
        ProjectNotification.objects.create(
            recipient=milestone.project.project_manager,
            notification_type='milestone_reached',
            title=f'Milestone Completed: {milestone.name}',
            message=f'Milestone "{milestone.name}" has been completed in project "{milestone.project.name}".',
            project=milestone.project
        )
    
    @staticmethod
    def create_project_status_notification(project: Project, old_status: str, new_status: str):
        """Create notification when project status changes"""
        ProjectNotification.objects.create(
            recipient=project.project_manager,
            notification_type='project_status_changed',
            title=f'Project Status Updated: {project.name}',
            message=f'Project "{project.name}" status changed from {old_status} to {new_status}.',
            project=project
        )