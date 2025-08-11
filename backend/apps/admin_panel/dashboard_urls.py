"""
URL routing for Advanced Dashboard System.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .dashboard_views import (
    DashboardWidgetViewSet, DashboardLayoutViewSet, DashboardTemplateViewSet,
    DashboardUserPreferenceViewSet, DashboardAlertViewSet, DashboardExportViewSet,
    DashboardDataSourceViewSet, DashboardAnalyticsView, DashboardRealTimeView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'widgets', DashboardWidgetViewSet, basename='dashboard-widget')
router.register(r'layouts', DashboardLayoutViewSet, basename='dashboard-layout')
router.register(r'templates', DashboardTemplateViewSet, basename='dashboard-template')
router.register(r'preferences', DashboardUserPreferenceViewSet, basename='dashboard-preference')
router.register(r'alerts', DashboardAlertViewSet, basename='dashboard-alert')
router.register(r'exports', DashboardExportViewSet, basename='dashboard-export')
router.register(r'data-sources', DashboardDataSourceViewSet, basename='dashboard-datasource')

# Additional URL patterns for non-ViewSet views
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Analytics and statistics
    path('analytics/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    
    # Real-time updates
    path('realtime/', DashboardRealTimeView.as_view(), name='dashboard-realtime'),
    
    # Widget data endpoints
    path('widgets/<uuid:pk>/data/', DashboardWidgetViewSet.as_view({'get': 'data'}), name='widget-data'),
    path('widgets/<uuid:pk>/duplicate/', DashboardWidgetViewSet.as_view({'post': 'duplicate'}), name='widget-duplicate'),
    path('widgets/popular/', DashboardWidgetViewSet.as_view({'get': 'popular'}), name='widgets-popular'),
    
    # Layout management endpoints
    path('layouts/<uuid:pk>/duplicate/', DashboardLayoutViewSet.as_view({'post': 'duplicate'}), name='layout-duplicate'),
    path('layouts/<uuid:pk>/add-widget/', DashboardLayoutViewSet.as_view({'post': 'add_widget'}), name='layout-add-widget'),
    path('layouts/<uuid:pk>/remove-widget/', DashboardLayoutViewSet.as_view({'delete': 'remove_widget'}), name='layout-remove-widget'),
    path('layouts/<uuid:pk>/update-positions/', DashboardLayoutViewSet.as_view({'post': 'update_positions'}), name='layout-update-positions'),
    path('layouts/<uuid:pk>/set-default/', DashboardLayoutViewSet.as_view({'post': 'set_as_default'}), name='layout-set-default'),
    
    # Template endpoints
    path('templates/<int:pk>/apply/', DashboardTemplateViewSet.as_view({'post': 'apply'}), name='template-apply'),
    
    # User preferences
    path('preferences/my/', DashboardUserPreferenceViewSet.as_view({'get': 'my_preferences', 'post': 'my_preferences'}), name='my-preferences'),
    
    # Alert management
    path('alerts/<uuid:pk>/acknowledge/', DashboardAlertViewSet.as_view({'post': 'acknowledge'}), name='alert-acknowledge'),
    path('alerts/<uuid:pk>/resolve/', DashboardAlertViewSet.as_view({'post': 'resolve'}), name='alert-resolve'),
    path('alerts/active/', DashboardAlertViewSet.as_view({'get': 'active'}), name='alerts-active'),
    
    # Export management
    path('exports/<uuid:pk>/download/', DashboardExportViewSet.as_view({'get': 'download'}), name='export-download'),
    
    # Data source management
    path('data-sources/<int:pk>/test-connection/', DashboardDataSourceViewSet.as_view({'post': 'test_connection'}), name='datasource-test'),
    path('data-sources/<int:pk>/sync/', DashboardDataSourceViewSet.as_view({'post': 'sync_data'}), name='datasource-sync'),
    
    # Chart endpoints
    path('', include('apps.admin_panel.chart_urls')),
]