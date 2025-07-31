"""
URL configuration for core functionality.

This module provides URL patterns for:
- Security admin interface
- Audit log management
- Security event monitoring
- Security reports and exports
- Database monitoring and alerting

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from django.urls import path, include
from django.contrib import admin
from core.admin.security_admin import security_admin_site

app_name = 'core'

urlpatterns = [
    # Security admin interface
    path('security-admin/', security_admin_site.urls),
    
    # Database monitoring and alerting API
    path('api/monitoring/', include('core.monitoring_urls')),
    
    # Database error handling and recovery
    path('database-errors/', include('core.error_handling_urls')),
    
    # Additional security endpoints can be added here
    # path('api/security/', include('core.api.security_urls')),
]