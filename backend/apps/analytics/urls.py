"""
Analytics app URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesAnalyticsViewSet, SalesMetricsViewSet, ProductSalesAnalyticsViewSet,
    CustomerAnalyticsViewSet, SalesForecastViewSet, SalesGoalViewSet,
    SalesCommissionViewSet, SalesTerritoryViewSet, SalesPipelineViewSet,
    SalesAnomalyDetectionViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'sales-analytics', SalesAnalyticsViewSet, basename='sales-analytics')
router.register(r'sales-metrics', SalesMetricsViewSet, basename='sales-metrics')
router.register(r'product-sales-analytics', ProductSalesAnalyticsViewSet, basename='product-sales-analytics')
router.register(r'customer-analytics', CustomerAnalyticsViewSet, basename='customer-analytics')
router.register(r'sales-forecasts', SalesForecastViewSet, basename='sales-forecasts')
router.register(r'sales-goals', SalesGoalViewSet, basename='sales-goals')
router.register(r'sales-commissions', SalesCommissionViewSet, basename='sales-commissions')
router.register(r'sales-territories', SalesTerritoryViewSet, basename='sales-territories')
router.register(r'sales-pipeline', SalesPipelineViewSet, basename='sales-pipeline')
router.register(r'sales-anomalies', SalesAnomalyDetectionViewSet, basename='sales-anomalies')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]