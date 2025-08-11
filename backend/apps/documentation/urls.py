from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentationCategoryViewSet, DocumentationTemplateViewSet,
    DocumentationViewSet, DocumentationAnalyticsViewSet,
    DocumentationReviewViewSet
)

app_name = 'documentation'

router = DefaultRouter()
router.register(r'categories', DocumentationCategoryViewSet)
router.register(r'templates', DocumentationTemplateViewSet)
router.register(r'documents', DocumentationViewSet)
router.register(r'analytics', DocumentationAnalyticsViewSet)
router.register(r'reviews', DocumentationReviewViewSet)

urlpatterns = [
    path('api/documentation/', include(router.urls)),
]