"""
Admin authentication URL patterns.
"""
from django.urls import path
from .views import (
    AdminLoginAPIView, AdminLogoutAPIView, AdminTokenRefreshAPIView
)

urlpatterns = [
    # Admin authentication endpoints
    path('login/', AdminLoginAPIView.as_view(), name='admin_login'),
    path('logout/', AdminLogoutAPIView.as_view(), name='admin_logout'),
    path('refresh/', AdminTokenRefreshAPIView.as_view(), name='admin_refresh'),
]