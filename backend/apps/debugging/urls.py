from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowSessionViewSet, TraceStepViewSet, PerformanceSnapshotViewSet,
    ErrorLogViewSet, DebugConfigurationViewSet, PerformanceThresholdViewSet,
    SystemHealthViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'workflow-sessions', WorkflowSessionViewSet, basename='workflow-session')
router.register(r'trace-steps', TraceStepViewSet, basename='trace-step')
router.register(r'performance-snapshots', PerformanceSnapshotViewSet, basename='performance-snapshot')
router.register(r'error-logs', ErrorLogViewSet, basename='error-log')
router.register(r'debug-configurations', DebugConfigurationViewSet, basename='debug-configuration')
router.register(r'performance-thresholds', PerformanceThresholdViewSet, basename='performance-threshold')
router.register(r'system-health', SystemHealthViewSet, basename='system-health')

app_name = 'debugging'

urlpatterns = [
    path('api/v1/debugging/', include(router.urls)),
]