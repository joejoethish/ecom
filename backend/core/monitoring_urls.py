"""
URL patterns for database monitoring API endpoints
"""

from django.urls import path
from . import monitoring_views

app_name = 'monitoring'

urlpatterns = [
    # Current metrics and health
    path('metrics/', monitoring_views.get_current_metrics, name='current_metrics'),
    path('metrics/<str:database>/history/', monitoring_views.get_metrics_history, name='metrics_history'),
    path('health/', monitoring_views.get_health_summary, name='health_summary'),
    path('dashboard/', monitoring_views.get_dashboard_data, name='dashboard_data'),
    
    # Slow queries
    path('slow-queries/', monitoring_views.get_slow_queries, name='slow_queries'),
    
    # Alerts
    path('alerts/', monitoring_views.get_active_alerts, name='active_alerts'),
    path('alerts/history/', monitoring_views.get_alert_history, name='alert_history'),
    path('alerts/acknowledge/', monitoring_views.acknowledge_alert, name='acknowledge_alert'),
    path('alerts/suppress/', monitoring_views.suppress_alert, name='suppress_alert'),
    path('alerts/test-channels/', monitoring_views.test_alert_channels, name='test_alert_channels'),
    
    # Configuration
    path('config/', monitoring_views.get_monitoring_config, name='monitoring_config'),
    path('config/threshold/', monitoring_views.update_threshold, name='update_threshold'),
    path('control/', monitoring_views.control_monitoring, name='control_monitoring'),
]