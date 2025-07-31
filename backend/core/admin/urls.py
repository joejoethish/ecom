"""
URL configuration for database administration tools.
"""

from django.urls import path, include
from .database_admin import db_admin_site

app_name = 'db_admin'

urlpatterns = [
    # Database administration site
    path('', db_admin_site.urls),
]