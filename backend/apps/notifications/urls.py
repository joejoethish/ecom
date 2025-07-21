from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Template views
    NotificationTemplateListCreateView,
    NotificationTemplateDetailView,
    
    # Preference views
    NotificationPreferenceListView,
    NotificationPreferenceUpdateView,
    NotificationPreferenceDetailView,
    
    # Notification views
    NotificationListView,
    NotificationDetailView,
    NotificationCreateView,
    NotificationMarkAsReadView,
    NotificationMarkAllAsReadView,
    NotificationStatsView,
    NotificationSettingsView,
    
    # Batch views
    NotificationBatchListCreateView,
    NotificationBatchDetailView,
    
    # Analytics views
    NotificationAnalyticsListView,
    NotificationAnalyticsSummaryView,
    
    # Utility views
    retry_failed_notifications,
    update_analytics,
    notification_types,
)

app_name = 'notifications'

urlpatterns = [
    # Notification Templates (Admin only)
    path('templates/', NotificationTemplateListCreateView.as_view(), name='template-list-create'),
    path('templates/<int:pk>/', NotificationTemplateDetailView.as_view(), name='template-detail'),
    
    # Notification Preferences
    path('preferences/', NotificationPreferenceListView.as_view(), name='preference-list'),
    path('preferences/update/', NotificationPreferenceUpdateView.as_view(), name='preference-update'),
    path('preferences/<int:pk>/', NotificationPreferenceDetailView.as_view(), name='preference-detail'),
    
    # Notifications
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<uuid:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('create/', NotificationCreateView.as_view(), name='notification-create'),
    path('mark-as-read/', NotificationMarkAsReadView.as_view(), name='notification-mark-as-read'),
    path('mark-all-as-read/', NotificationMarkAllAsReadView.as_view(), name='notification-mark-all-as-read'),
    path('stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    
    # Notification Batches (Admin only)
    path('batches/', NotificationBatchListCreateView.as_view(), name='batch-list-create'),
    path('batches/<uuid:pk>/', NotificationBatchDetailView.as_view(), name='batch-detail'),
    
    # Analytics (Admin only)
    path('analytics/', NotificationAnalyticsListView.as_view(), name='analytics-list'),
    path('analytics/summary/', NotificationAnalyticsSummaryView.as_view(), name='analytics-summary'),
    
    # Utility endpoints
    path('retry-failed/', retry_failed_notifications, name='retry-failed'),
    path('update-analytics/', update_analytics, name='update-analytics'),
    path('types/', notification_types, name='notification-types'),
]