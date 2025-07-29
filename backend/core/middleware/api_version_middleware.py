"""
Middleware for adding API version headers to responses.
"""
from django.conf import settings
from core.versioning import get_api_version, is_deprecated_version


class APIVersionHeaderMiddleware:
    """
    Middleware that adds API version headers to responses.
    
    This middleware adds the following headers to API responses:
    - X-API-Version: The version used for the request
    - X-API-Supported-Versions: List of all supported API versions
    - X-API-Deprecation-Warning: Warning message if the version is deprecated
    - X-API-Sunset-Date: Date when the version will be removed (for deprecated versions)
    - X-API-Recommended-Version: Recommended version to use (for deprecated versions)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add headers to API requests
        if not request.path.startswith('/api/'):
            return response
        
        # Get API version from request
        version = get_api_version(request)
        
        # Add version headers
        response['X-API-Version'] = version
        response['X-API-Supported-Versions'] = ', '.join(getattr(settings, 'API_VERSIONS', ['v1', 'v2']))
        
        # Add deprecation headers if version is deprecated
        if is_deprecated_version(version):
            response['X-API-Deprecation-Warning'] = f'API version {version} is deprecated'
            response['X-API-Sunset-Date'] = getattr(settings, 'API_SUNSET_DATES', {}).get(version, '')
            response['X-API-Recommended-Version'] = getattr(settings, 'RECOMMENDED_API_VERSION', 'v2')
        
        return response