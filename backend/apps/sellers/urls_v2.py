"""
Sellers URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'sellers', views.SellerViewSet, basename='sellers_v2')
router.register(r'stores', views.StoreViewSet, basename='stores_v2')
router.register(r'commissions', views.CommissionViewSet, basename='commissions_v2')

urlpatterns = [
    path('', include(router.urls)),
]