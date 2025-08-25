from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowSessionViewSet, TraceStepViewSet, PerformanceSnapshotViewSet,
    ErrorLogViewSet, DebugConfigurationViewSet, PerformanceThresholdViewSet,
    SystemHealthViewSet, RouteDiscoveryViewSet, FrontendRouteViewSet,
    APICallDiscoveryViewSet, RouteDiscoverySessionViewSet,
    WorkflowTracingViewSet, DatabaseMonitoringViewSet
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
router.register(r'route-discovery', RouteDiscoveryViewSet, basename='route-discovery')
router.register(r'frontend-routes', FrontendRouteViewSet, basename='frontend-route')
router.register(r'api-call-discovery', APICallDiscoveryViewSet, basename='api-call-discovery')
router.register(r'discovery-sessions', RouteDiscoverySessionViewSet, basename='discovery-session')
router.register(r'workflow-tracing', WorkflowTracingViewSet, basename='workflow-tracing')
router.register(r'database-monitoring', DatabaseMonitoringViewSet, basename='database-monitoring')

app_name = 'debugging'

urlpatterns = [
    path('api/v1/debugging/', include(router.urls)),
]