"""
Notifications URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notifications_v2')
router.register(r'channels', views.NotificationChannelViewSet, basename='notification-channels_v2')
router.register(r'templates', views.NotificationTemplateViewSet, basename='notification-templates_v2')
router.register(r'preferences', views.NotificationPreferenceViewSet, basename='notification-preferences_v2')

urlpatterns = [
    path('', include(router.urls)),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark-all-read_v2'),
    path('unsubscribe/<str:token>/', views.UnsubscribeView.as_view(), name='unsubscribe_v2'),
]