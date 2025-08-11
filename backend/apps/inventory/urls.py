from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InventoryViewSet, InventoryTransactionViewSet,
    SupplierViewSet, WarehouseViewSet,
    PurchaseOrderViewSet, PurchaseOrderItemViewSet
)
from .analytics_views import (
    InventoryAnalyticsViewSet, InventoryKPIViewSet,
    InventoryForecastViewSet, InventoryAlertViewSet
)

router = DefaultRouter()
router.register(r'inventory', InventoryViewSet)
router.register(r'transactions', InventoryTransactionViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-order-items', PurchaseOrderItemViewSet)

# Analytics endpoints
router.register(r'analytics', InventoryAnalyticsViewSet)
router.register(r'kpis', InventoryKPIViewSet)
router.register(r'forecasts', InventoryForecastViewSet)
router.register(r'alerts', InventoryAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]