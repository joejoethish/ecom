from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationCategoryViewSet, IntegrationProviderViewSet,
    IntegrationViewSet, IntegrationTemplateViewSet,
    IntegrationLogViewSet, IntegrationSyncViewSet
)
from . import webhook_views

router = DefaultRouter()
router.register(r'categories', IntegrationCategoryViewSet)
router.register(r'providers', IntegrationProviderViewSet)
router.register(r'integrations', IntegrationViewSet)
router.register(r'templates', IntegrationTemplateViewSet)
router.register(r'logs', IntegrationLogViewSet)
router.register(r'syncs', IntegrationSyncViewSet)

urlpatterns = [
    path('api/integrations/', include(router.urls)),
    path('api/integrations/webhooks/', include('apps.integrations.webhook_urls')),
]