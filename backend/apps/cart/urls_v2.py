"""
Cart URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart_v2')
router.register(r'saved-items', views.SavedItemViewSet, basename='saved-items_v2')
router.register(r'coupons', views.CouponViewSet, basename='coupons_v2')

urlpatterns = [
    path('', include(router.urls)),
]