from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Core project management
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'milestones', views.MilestoneViewSet)
router.register(r'risks', views.ProjectRiskViewSet)
router.register(r'time-entries', views.TimeEntryViewSet)
router.register(r'documents', views.ProjectDocumentViewSet)
router.register(r'comments', views.ProjectCommentViewSet)
router.register(r'notifications', views.ProjectNotificationViewSet)
router.register(r'templates', views.ProjectTemplateViewSet)

# Advanced project management features
router.register(r'analytics', views.ProjectAnalyticsViewSet, basename='project-analytics')
router.register(r'gantt', views.GanttChartViewSet, basename='gantt-chart')
router.register(r'portfolio', views.ProjectPortfolioViewSet, basename='project-portfolio')
router.register(r'resources', views.ResourceManagementViewSet, basename='resource-management')
router.register(r'automation', views.ProjectAutomationViewSet, basename='project-automation')

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Additional custom endpoints
    path('api/dashboard/stats/', views.ProjectViewSet.as_view({'get': 'dashboard_stats'}), name='dashboard-stats'),
    path('api/portfolio/overview/', views.ProjectPortfolioViewSet.as_view({'get': 'overview'}), name='portfolio-overview'),
    path('api/resources/allocation/', views.ResourceManagementViewSet.as_view({'get': 'allocation_overview'}), name='resource-allocation'),
    path('api/analytics/dashboard/', views.ProjectAnalyticsViewSet.as_view({'get': 'dashboard_metrics'}), name='analytics-dashboard'),
    path('api/automation/auto-assign/', views.ProjectAutomationViewSet.as_view({'post': 'auto_assign_tasks'}), name='auto-assign-tasks'),
]