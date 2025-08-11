"""
Content management app URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BannerViewSet, CarouselViewSet, CarouselItemViewSet,
    ContentPageViewSet, AnnouncementViewSet, ContentManagementViewSet
)
from .advanced_views import (
    ContentTemplateViewSet, AdvancedContentPageViewSet, ContentWorkflowViewSet,
    ContentWorkflowInstanceViewSet, ContentAssetViewSet, ContentCategoryViewSet,
    ContentTagViewSet, PageBuilderViewSet, ContentManagementAdvancedViewSet
)

# Create router and register viewsets
router = DefaultRouter()

# Basic content management
router.register(r'banners', BannerViewSet, basename='banners')
router.register(r'carousels', CarouselViewSet, basename='carousels')
router.register(r'carousel-items', CarouselItemViewSet, basename='carousel-items')
router.register(r'pages', ContentPageViewSet, basename='content-pages')
router.register(r'announcements', AnnouncementViewSet, basename='announcements')
router.register(r'content-management', ContentManagementViewSet, basename='content-management')

# Advanced content management
router.register(r'templates', ContentTemplateViewSet, basename='content-templates')
router.register(r'advanced-pages', AdvancedContentPageViewSet, basename='advanced-content-pages')
router.register(r'workflows', ContentWorkflowViewSet, basename='content-workflows')
router.register(r'workflow-instances', ContentWorkflowInstanceViewSet, basename='workflow-instances')
router.register(r'assets', ContentAssetViewSet, basename='content-assets')
router.register(r'categories', ContentCategoryViewSet, basename='content-categories')
router.register(r'tags', ContentTagViewSet, basename='content-tags')
router.register(r'page-builder', PageBuilderViewSet, basename='page-builder')
router.register(r'advanced-management', ContentManagementAdvancedViewSet, basename='advanced-content-management')

app_name = 'content'

urlpatterns = [
    path('', include(router.urls)),
]