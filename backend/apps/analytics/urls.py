"""
Analytics app URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsViewSet, DailySalesReportViewSet, ProductPerformanceReportViewSet,
    CustomerAnalyticsViewSet, InventoryReportViewSet, SystemMetricsViewSet,
    ReportExportViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'daily-sales-reports', DailySalesReportViewSet, basename='daily-sales-reports')
router.register(r'product-performance', ProductPerformanceReportViewSet, basename='product-performance')
router.register(r'customer-analytics', CustomerAnalyticsViewSet, basename='customer-analytics')
router.register(r'inventory-reports', InventoryReportViewSet, basename='inventory-reports')
router.register(r'system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register(r'report-exports', ReportExportViewSet, basename='report-exports')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]