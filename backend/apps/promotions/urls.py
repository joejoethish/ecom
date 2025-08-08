"""
Promotion and Coupon Management URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromotionViewSet, CouponViewSet, PromotionTemplateViewSet

app_name = 'promotions'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'templates', PromotionTemplateViewSet, basename='template')

urlpatterns = [
    path('api/', include(router.urls)),
]