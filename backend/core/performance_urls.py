"""
URL patterns for performance monitoring views
"""

from django.urls import path
from . import performance_views

app_name = 'performance'

urlpatterns = [
    # Dashboard
    path('dashboard/', performance_views.performance_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/metrics/', performance_views.performance_metrics_api, name='metrics_api'),
    path('api/recommendations/', performance_views.optimization_recommendations_api, name='recommendations_api'),
    path('api/capacity/', performance_views.capacity_recommendations_api, name='capacity_api'),
    path('api/regressions/', performance_views.performance_regressions_api, name='regressions_api'),
    path('api/baselines/', performance_views.performance_baselines_api, name='baselines_api'),
    path('api/history/', performance_views.performance_history_api, name='history_api'),
    path('api/report/', performance_views.performance_report_api, name='report_api'),
    
    # Control endpoints
    path('api/reset-baseline/', performance_views.reset_baseline_api, name='reset_baseline_api'),
    path('api/update-thresholds/', performance_views.update_thresholds_api, name='update_thresholds_api'),
    path('api/monitoring/', performance_views.PerformanceMonitoringView.as_view(), name='monitoring_api'),
    
    # Export
    path('export/', performance_views.export_performance_data, name='export_data'),
]