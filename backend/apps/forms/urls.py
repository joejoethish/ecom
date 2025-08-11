from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FormTemplateViewSet, FormViewSet, FormFieldViewSet, FormSubmissionViewSet,
    FormVersionViewSet, FormAnalyticsViewSet, FormIntegrationViewSet,
    FormABTestViewSet, PublicFormViewSet
)

# Admin router for authenticated users
admin_router = DefaultRouter()
admin_router.register(r'templates', FormTemplateViewSet)
admin_router.register(r'forms', FormViewSet)
admin_router.register(r'fields', FormFieldViewSet)
admin_router.register(r'submissions', FormSubmissionViewSet)
admin_router.register(r'versions', FormVersionViewSet)
admin_router.register(r'analytics', FormAnalyticsViewSet)
admin_router.register(r'integrations', FormIntegrationViewSet)
admin_router.register(r'ab-tests', FormABTestViewSet)

# Public router for form rendering and submission
public_router = DefaultRouter()
public_router.register(r'public', PublicFormViewSet)

urlpatterns = [
    # Admin API endpoints
    path('api/admin/forms/', include(admin_router.urls)),
    
    # Public API endpoints
    path('api/forms/', include(public_router.urls)),
    
    # Additional endpoints
    path('api/admin/forms/builder/', include([
        path('field-types/', FormFieldViewSet.as_view({'get': 'list'}), name='field-types'),
        path('validation-rules/', FormViewSet.as_view({'get': 'list'}), name='validation-rules'),
    ])),
]