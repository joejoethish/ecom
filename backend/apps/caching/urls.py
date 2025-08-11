from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CacheConfigurationViewSet, CacheMetricsViewSet, CacheInvalidationViewSet,
    CacheWarmingViewSet, CacheAlertViewSet, CacheOptimizationViewSet,
    CDNManagementViewSet
)

router = DefaultRouter()
router.register(r'configurations', CacheConfigurationViewSet)
router.register(r'metrics', CacheMetricsViewSet)
router.register(r'invalidations', CacheInvalidationViewSet)
router.register(r'warming', CacheWarmingViewSet)
router.register(r'alerts', CacheAlertViewSet)
router.register(r'optimizations', CacheOptimizationViewSet)
router.register(r'cdn', CDNManagementViewSet, basename='cdn')

urlpatterns = [
    path('api/admin/caching/', include(router.urls)),
]