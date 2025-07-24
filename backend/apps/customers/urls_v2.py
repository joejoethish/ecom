"""
Customers URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customers_v2')
router.register(r'addresses', views.AddressViewSet, basename='addresses_v2')
router.register(r'preferences', views.CustomerPreferenceViewSet, basename='preferences_v2')

urlpatterns = [
    path('', include(router.urls)),
]