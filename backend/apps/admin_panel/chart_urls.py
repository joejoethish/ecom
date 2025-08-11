"""
Chart URLs for advanced data visualization
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .chart_views import (
    ChartViewSet, ChartTemplateViewSet, ChartAnnotationViewSet,
    ChartCommentViewSet, ChartRealTimeDataView, ChartAnalyticsView
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'charts', ChartViewSet)
router.register(r'chart-templates', ChartTemplateViewSet)
router.register(r'chart-annotations', ChartAnnotationViewSet)
router.register(r'chart-comments', ChartCommentViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Real-time data endpoints
    path('charts/<uuid:chart_id>/realtime/', ChartRealTimeDataView.as_view(), name='chart-realtime'),
    
    # Analytics endpoints
    path('chart-analytics/', ChartAnalyticsView.as_view(), name='chart-analytics'),
]