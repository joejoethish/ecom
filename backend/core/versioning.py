"""
API versioning utilities and classes.
"""
from rest_framework.versioning import URLPathVersioning, AcceptHeaderVersioning
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import re


class CustomURLPathVersioning(URLPathVersioning):
    """
    Custom URL path versioning that supports version-specific behavior.
    """
    allowed_versions = getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
    default_version = getattr(settings, 'DEFAULT_API_VERSION', 'v1')
    version_param = 'version'
    
    def determine_version(self, request, *args, **kwargs):
        version = super().determine_version(request, *args, **kwargs)
        
        # Validate version
        if version not in self.allowed_versions:
            return self.default_version
            
        return version
    
    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None):
        """
        Override to ensure version is included in reversed URLs.
        """
        if request.version != self.default_version:
            return super().reverse(viewname, args, kwargs, request, format)
        return super().reverse(viewname, args, kwargs, request, format)


class CustomAcceptHeaderVersioning(AcceptHeaderVersioning):
    """
    Custom accept header versioning for API clients that prefer header-based versioning.
    Supports both Accept header and custom X-API-Version header.
    """
    allowed_versions = getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
    default_version = getattr(settings, 'DEFAULT_API_VERSION', 'v1')
    version_param = 'version'
    
    def determine_version(self, request, *args, **kwargs):
        # First try custom X-API-Version header
        version = request.META.get('HTTP_X_API_VERSION')
        if version:
            # Clean version string (remove 'v' prefix if present)
            version = version.lower().strip()
            if not version.startswith('v'):
                version = f'v{version}'
            
            if version in self.allowed_versions:
                return version
        
        # Fall back to Accept header versioning
        version = super().determine_version(request, *args, **kwargs)
        
        # Validate version
        if version and version in self.allowed_versions:
            return version
            
        return self.default_version


class HybridVersioning(URLPathVersioning):
    """
    Hybrid versioning that supports both URL path and header-based versioning.
    URL path takes precedence over headers.
    """
    allowed_versions = getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
    default_version = getattr(settings, 'DEFAULT_API_VERSION', 'v1')
    version_param = 'version'
    
    def determine_version(self, request, *args, **kwargs):
        # First try URL path versioning
        try:
            version = super().determine_version(request, *args, **kwargs)
            if version and version in self.allowed_versions:
                return version
        except:
            pass
        
        # Fall back to header versioning
        version = request.META.get('HTTP_X_API_VERSION')
        if version:
            version = version.lower().strip()
            if not version.startswith('v'):
                version = f'v{version}'
            
            if version in self.allowed_versions:
                return version
        
        # Check Accept header
        accept_header = request.META.get('HTTP_ACCEPT', '')
        version_match = re.search(r'application/vnd\.api\+json;version=([^,\s]+)', accept_header)
        if version_match:
            version = version_match.group(1).lower().strip()
            if not version.startswith('v'):
                version = f'v{version}'
            
            if version in self.allowed_versions:
                return version
        
        return self.default_version


class VersionedSerializerMixin:
    """
    Mixin to provide version-specific serializer selection.
    """
    serializer_class_map = {}
    
    def get_serializer_class(self):
        """
        Return the serializer class based on API version.
        """
        version = getattr(self.request, 'version', 'v1')
        
        # Check if version-specific serializer exists
        if version in self.serializer_class_map:
            return self.serializer_class_map[version]
        
        # Fall back to default serializer
        return super().get_serializer_class()


class VersionedViewMixin:
    """
    Mixin to provide version-specific view behavior.
    """
    
    def get_version(self):
        """
        Get the API version from the request.
        """
        return getattr(self.request, 'version', 'v1')
    
    def is_version(self, version):
        """
        Check if the current request is for a specific version.
        """
        return self.get_version() == version
    
    def version_not_supported(self, message="API version not supported"):
        """
        Return a version not supported response.
        """
        return Response(
            {
                'error': {
                    'message': message,
                    'code': 'version_not_supported',
                    'supported_versions': getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )


def get_api_version(request):
    """
    Utility function to get API version from request.
    """
    return getattr(request, 'version', 'v1')


def is_deprecated_version(version):
    """
    Check if an API version is deprecated.
    """
    deprecated_versions = getattr(settings, 'DEPRECATED_API_VERSIONS', [])
    return version in deprecated_versions


class DeprecationWarningMixin:
    """
    Mixin to add deprecation warnings to API responses.
    """
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add deprecation warning headers if version is deprecated.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        
        version = get_api_version(request)
        if is_deprecated_version(version):
            response['X-API-Deprecation-Warning'] = f'API version {version} is deprecated'
            response['X-API-Sunset-Date'] = getattr(settings, 'API_SUNSET_DATES', {}).get(version, '')
        
        return response