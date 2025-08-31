"""
URL configuration for debugging and monitoring endpoints
"""

from django.urls import path, include
from .production_monitoring import (
    health_check_view,
    detailed_health_check_view,
    alerts_view,
    resolve_alert_view,
    monitoring_dashboard_view
)

app_name = 'debugging'

# Production monitoring URLs
production_patterns = [
    path('health/', health_check_view, name='health_check'),
    path('health/detailed/', detailed_health_check_view, name='detailed_health_check'),
    path('alerts/', alerts_view, name='alerts'),
    path('alerts/resolve/', resolve_alert_view, name='resolve_alert'),
    path('dashboard/', monitoring_dashboard_view, name='monitoring_dashboard'),
]

# Main URL patterns
urlpatterns = [
    # Production monitoring
    path('production/', include(production_patterns)),
    
    # Health check at root level for load balancers
    path('health/', health_check_view, name='root_health_check'),
]