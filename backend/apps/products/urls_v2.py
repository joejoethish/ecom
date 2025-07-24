"""
Products URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_v2 import CategoryViewSetV2, ProductViewSetV2

router = DefaultRouter()
router.register(r'categories', CategoryViewSetV2)
router.register(r'', ProductViewSetV2)

urlpatterns = [
    path('', include(router.urls)),
]