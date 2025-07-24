"""
Payments URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payments_v2')
router.register(r'wallets', views.WalletViewSet, basename='wallets_v2')
router.register(r'gift-cards', views.GiftCardViewSet, basename='gift-cards_v2')

urlpatterns = [
    path('', include(router.urls)),
]