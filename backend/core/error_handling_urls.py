"""
URL patterns for database error handling monitoring and management
"""

from django.urls import path
from . import error_handling_views

app_name = 'error_handling'

urlpatterns = [
    # Dashboard
    path('dashboard/', error_handling_views.error_handling_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/statistics/', error_handling_views.error_statistics_api, name='statistics_api'),
    path('api/recent-errors/', error_handling_views.recent_errors_api, name='recent_errors_api'),
    path('api/connection-pools/', error_handling_views.connection_pool_status_api, name='connection_pools_api'),
    path('api/reset-degradation/', error_handling_views.reset_degradation_mode_api, name='reset_degradation_api'),
    path('api/deadlock-analysis/', error_handling_views.deadlock_analysis_api, name='deadlock_analysis_api'),
    path('api/circuit-breakers/', error_handling_views.circuit_breaker_status_api, name='circuit_breakers_api'),
    path('api/health-check/', error_handling_views.health_check_api, name='health_check_api'),
    path('api/error-trends/', error_handling_views.error_trends_api, name='error_trends_api'),
    
    # Metrics endpoint for monitoring systems
    path('metrics/', error_handling_views.error_handling_metrics, name='metrics'),
]