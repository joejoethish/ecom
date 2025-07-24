"""
Inventory URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'inventory', views.InventoryViewSet, basename='inventory_v2')
router.register(r'transactions', views.InventoryTransactionViewSet, basename='inventory-transactions_v2')
router.register(r'suppliers', views.SupplierViewSet, basename='suppliers_v2')

urlpatterns = [
    path('', include(router.urls)),
]