"""
URL configuration for ecommerce_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
# from core.views import api_documentation_guide, api_guides_list, api_endpoints_list

# Create schema view for drf-yasg (alternative documentation)
schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce Platform API",
        default_version='v2',
        description="A comprehensive API for the multi-vendor e-commerce platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('admin/monitoring/', include('apps.logs.urls')),  # Temporarily disabled
    
    # Database administration interface
    path('db-admin/', include('core.admin.urls')),
    
    # Admin panel interface
    path('admin-panel/', include('apps.admin_panel.urls')),
    
    # System settings management
    path('', include('apps.system_settings.urls')),
    
    # Integration management
    path('', include('apps.integrations.urls')),
    
    # Workflow automation system
    path('', include('apps.workflow.urls')),
    
    # Multi-tenant architecture
    path('', include('apps.tenants.urls')),
    
    # Internationalization system
    path('', include('apps.internationalization.urls')),
    
    path('api/v1/', include('api.v1.urls')),
    # path('api/v2/', include('api.v2.urls')),  # Temporarily disabled
    
    # Core monitoring endpoints
    path('api/core/', include('core.urls')),
    
    # Security admin interface
    path('', include('core.urls')),
    
    # API Documentation - drf-spectacular (OpenAPI 3.0) - Temporarily disabled
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema.yaml', SpectacularAPIView.as_view(format='yaml'), name='schema-yaml'),
    # path('api/docs/', SpectacularSwaggerView.as_view(
    #     url_name='schema',
    #     template_name='swagger-ui.html',
    #     swagger_ui_settings={
    #         'deepLinking': True,
    #         'persistAuthorization': True,
    #         'displayOperationId': True,
    #         'defaultModelsExpandDepth': 3,
    #         'defaultModelExpandDepth': 3,
    #         'docExpansion': 'list',
    #         'filter': True,
    #     }
    # ), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(
    #     url_name='schema',
    #     template_name='redoc.html',
    #     redoc_ui_settings={
    #         'hideDownloadButton': False,
    #         'hideHostname': False,
    #         'expandResponses': '200,201',
    #         'pathInMiddlePanel': True,
    #     }
    # ), name='redoc'),
    
    # API Documentation Guides - Temporarily disabled
    # path('api/docs/guides/', RedirectView.as_view(url='/api/docs/guides/usage/'), name='api-guides'),
    # path('api/docs/guides/<str:guide_name>/', api_documentation_guide, name='api-guide'),
    # path('api/docs/guides.json', api_guides_list, name='api-guides-list'),
    # path('api/docs/endpoints.json', api_endpoints_list, name='api-endpoints-list'),
    
    # Alternative API Documentation - drf-yasg (Swagger 2.0) - Temporarily disabled
    # path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('api/swagger/<str:format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # path('api/swagger/yaml/', schema_view.without_ui(cache_timeout=0, format='.yaml'), name='schema-yaml'),
    # path('api/docs/yasg/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar URLs
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns