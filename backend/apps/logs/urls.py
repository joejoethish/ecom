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
]