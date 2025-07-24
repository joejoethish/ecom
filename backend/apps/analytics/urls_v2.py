"""
Analytics URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'events', views.AnalyticsEventViewSet, basename='analytics-events_v2')
router.register(r'reports', views.ReportViewSet, basename='analytics-reports_v2')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.DashboardDataView.as_view(), name='analytics-dashboard_v2'),
    path('export/', views.ExportDataView.as_view(), name='analytics-export_v2'),
]