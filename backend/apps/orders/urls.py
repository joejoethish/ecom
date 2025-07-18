"""
Orders URL patterns.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'returns', views.ReturnRequestViewSet, basename='return-request')
router.register(r'replacements', views.ReplacementViewSet, basename='replacement')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
]