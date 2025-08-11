"""
Advanced Business Intelligence URL Configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .bi_views import (
    BIDashboardViewSet, BIWidgetViewSet, BIDataSourceViewSet,
    BIInsightViewSet, BIMLModelViewSet, BIRealtimeViewSet,
    BIDataGovernanceViewSet, BIAnalyticsSessionViewSet, BIExportViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'dashboards', BIDashboardViewSet, basename='bi-dashboard')
router.register(r'widgets', BIWidgetViewSet, basename='bi-widget')
router.register(r'data-sources', BIDataSourceViewSet, basename='bi-data-source')
router.register(r'insights', BIInsightViewSet, basename='bi-insight')
router.register(r'ml-models', BIMLModelViewSet, basename='bi-ml-model')
router.register(r'realtime', BIRealtimeViewSet, basename='bi-realtime')
router.register(r'governance', BIDataGovernanceViewSet, basename='bi-governance')
router.register(r'analytics-sessions', BIAnalyticsSessionViewSet, basename='bi-analytics-session')
router.register(r'export', BIExportViewSet, basename='bi-export')

app_name = 'bi'

urlpatterns = [
    path('', include(router.urls)),
]