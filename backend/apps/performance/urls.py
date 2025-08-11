from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PerformanceMetricViewSet, ApplicationPerformanceMonitorViewSet,
    DatabasePerformanceLogViewSet, PerformanceAlertViewSet,
    PerformanceBenchmarkViewSet, PerformanceReportViewSet,
    PerformanceIncidentViewSet
)

router = DefaultRouter()
router.register(r'metrics', PerformanceMetricViewSet)
router.register(r'apm', ApplicationPerformanceMonitorViewSet)
router.register(r'database', DatabasePerformanceLogViewSet)
router.register(r'alerts', PerformanceAlertViewSet)
router.register(r'benchmarks', PerformanceBenchmarkViewSet)
router.register(r'reports', PerformanceReportViewSet)
router.register(r'incidents', PerformanceIncidentViewSet)

urlpatterns = [
    path('api/admin/performance/', include(router.urls)),
]