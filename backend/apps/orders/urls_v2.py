"""
Orders URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order_v2')
router.register(r'returns', views.ReturnRequestViewSet, basename='return-request_v2')
router.register(r'replacements', views.ReplacementViewSet, basename='replacement_v2')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice_v2')

urlpatterns = [
    path('', include(router.urls)),
]