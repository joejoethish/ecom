"""
Shipping URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'shipping-methods', views.ShippingMethodViewSet, basename='shipping-methods_v2')
router.register(r'shipping-zones', views.ShippingZoneViewSet, basename='shipping-zones_v2')
router.register(r'shipping-rates', views.ShippingRateViewSet, basename='shipping-rates_v2')
router.register(r'carriers', views.CarrierViewSet, basename='carriers_v2')

urlpatterns = [
    path('', include(router.urls)),
    path('calculate/', views.ShippingCalculationView.as_view(), name='shipping-calculate_v2'),
    path('track/<str:tracking_number>/', views.TrackShipmentView.as_view(), name='track-shipment_v2'),
]