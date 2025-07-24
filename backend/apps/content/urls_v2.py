"""
Content URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'pages', views.PageViewSet, basename='pages_v2')
router.register(r'banners', views.BannerViewSet, basename='banners_v2')
router.register(r'promotions', views.PromotionViewSet, basename='promotions_v2')
router.register(r'media', views.MediaViewSet, basename='media_v2')

urlpatterns = [
    path('', include(router.urls)),
    path('menu/', views.MenuView.as_view(), name='menu_v2'),
    path('settings/', views.ContentSettingsView.as_view(), name='content-settings_v2'),
]