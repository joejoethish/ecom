from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowSessionViewSet, TraceStepViewSet, PerformanceSnapshotViewSet,
    ErrorLogViewSet, DebugConfigurationViewSet, PerformanceThresholdViewSet,
    SystemHealthViewSet, RouteDiscoveryViewSet, FrontendRouteViewSet,
    APICallDiscoveryViewSet, RouteDiscoverySessionViewSet,
    WorkflowTracingViewSet, DatabaseHealthViewSet, TestingFrameworkViewSet
)
from .performance_views import (
    system_health_summary, performance_metrics, performance_trends,
    optimization_recommendations, performance_thresholds, collect_manual_metric,
    metrics_summary, initialize_service, shutdown_service,
    PerformanceMonitoringAPIView
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
router.register(r'database-health', DatabaseHealthViewSet, basename='database-health')
router.register(r'testing-framework', TestingFrameworkViewSet, basename='testing-framework')

app_name = 'debugging'

urlpatterns = [
    path('api/v1/debugging/', include(router.urls)),
    
    # Performance monitoring endpoints
    path('api/v1/debugging/performance/health/', system_health_summary, name='performance-health'),
    path('api/v1/debugging/performance/metrics/', performance_metrics, name='performance-metrics'),
    path('api/v1/debugging/performance/trends/', performance_trends, name='performance-trends'),
    path('api/v1/debugging/performance/recommendations/', optimization_recommendations, name='performance-recommendations'),
    path('api/v1/debugging/performance/thresholds/', performance_thresholds, name='performance-thresholds-api'),
    path('api/v1/debugging/performance/collect/', collect_manual_metric, name='collect-manual-metric'),
    path('api/v1/debugging/performance/summary/', metrics_summary, name='metrics-summary'),
    path('api/v1/debugging/performance/initialize/', initialize_service, name='initialize-service'),
    path('api/v1/debugging/performance/shutdown/', shutdown_service, name='shutdown-service'),
    path('api/v1/debugging/performance/', PerformanceMonitoringAPIView.as_view(), name='performance-monitoring-api'),
]