"""
URL configuration for the logs and monitoring app.
"""
from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    # Dashboard views
    path('dashboard/', views.MonitoringDashboardView.as_view(), name='dashboard'),
    path('analysis/', views.LogAnalysisView.as_view(), name='analysis'),
    path('alerts/', views.AlertConfigView.as_view(), name='alerts'),
    
    # API endpoints
    path('api/system-health/', views.SystemHealthAPIView.as_view(), name='api_system_health'),
    path('api/error-metrics/', views.ErrorMetricsAPIView.as_view(), name='api_error_metrics'),
    path('api/performance-metrics/', views.PerformanceMetricsAPIView.as_view(), name='api_performance_metrics'),
    path('api/security-metrics/', views.SecurityMetricsAPIView.as_view(), name='api_security_metrics'),
    path('api/alerts/', views.AlertAPIView.as_view(), name='api_alerts'),
    
    # Log aggregation endpoints
    path('api/frontend-logs/', views.receive_frontend_logs, name='api_frontend_logs'),
    path('api/logs/', views.get_aggregated_logs, name='api_logs'),
    path('api/logs/create/', views.create_log_entry, name='api_create_log'),
    path('api/workflow-trace/<str:correlation_id>/', views.get_workflow_trace, name='api_workflow_trace'),
    path('api/error-patterns/', views.get_error_patterns, name='api_error_patterns'),
    path('api/cleanup-logs/', views.cleanup_old_logs, name='api_cleanup_logs'),
]