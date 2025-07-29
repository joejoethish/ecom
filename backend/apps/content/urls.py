"""
Content management app URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BannerViewSet, CarouselViewSet, CarouselItemViewSet,
    ContentPageViewSet, AnnouncementViewSet, ContentManagementViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'banners', BannerViewSet, basename='banners')
router.register(r'carousels', CarouselViewSet, basename='carousels')
router.register(r'carousel-items', CarouselItemViewSet, basename='carousel-items')
router.register(r'pages', ContentPageViewSet, basename='content-pages')
router.register(r'announcements', AnnouncementViewSet, basename='announcements')
router.register(r'content-management', ContentManagementViewSet, basename='content-management')

app_name = 'content'

urlpatterns = [
    path('', include(router.urls)),
]