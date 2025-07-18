"""
URL configuration for the payments app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CurrencyViewSet, PaymentMethodViewSet, PaymentViewSet,
    RefundViewSet, WalletViewSet, GiftCardViewSet
)

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'methods', PaymentMethodViewSet)
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'refunds', RefundViewSet, basename='refund')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'gift-cards', GiftCardViewSet, basename='gift-card')

app_name = 'payments'

urlpatterns = [
    path('', include(router.urls)),
]