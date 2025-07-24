"""
Custom middleware for the ecommerce platform.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class APIVersionMiddleware(MiddlewareMixin):
    """
    Middleware to handle API versioning and add version information to responses.
    Supports both URL path versioning and Accept header versioning.
    """
    
    def process_request(self, request):
        """
        Process incoming request to extract API version.
        """
        # Default version
        version = 'v1'
        
        # Extract version from URL path (highest priority)
        if request.path.startswith('/api/'):
            path_parts = request.path.split('/')
            if len(path_parts) >= 3 and path_parts[2].startswith('v'):
                version = path_parts[2]
        
        # Extract version from Accept header (if not found in URL)
        elif 'HTTP_ACCEPT' in request.META:
            accept_header = request.META['HTTP_ACCEPT']
            
            # Check for version in Accept header (e.g., application/json; version=v2)
            if 'version=' in accept_header:
                import re
                version_match = re.search(r'version=(v\d+)', accept_header)
                if version_match:
                    version = version_match.group(1)
            
            # Check for versioned media type (e.g., application/vnd.ecommerce.v2+json)
            elif 'application/vnd.ecommerce.' in accept_header:
                import re
                version_match = re.search(r'application/vnd\.ecommerce\.(v\d+)\+json', accept_header)
                if version_match:
                    version = version_match.group(1)
        
        # Extract version from custom header (lowest priority)
        elif 'HTTP_X_API_VERSION' in request.META:
            version = request.META['HTTP_X_API_VERSION']
        
        # Validate version
        allowed_versions = getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
        if version not in allowed_versions:
            version = 'v1'  # Default to v1 if invalid
        
        # Set version on request object
        request.version = version
        request.api_version = version
        
        return None
    
    def process_response(self, request, response):
        """
        Process response to add version headers.
        """
        if hasattr(request, 'api_version') and hasattr(response, '__setitem__'):
            # Add version header
            response['X-API-Version'] = request.api_version
            
            # Add supported versions header
            allowed_versions = getattr(settings, 'API_VERSIONS', ['v1', 'v2'])
            response['X-API-Supported-Versions'] = ', '.join(allowed_versions)
            
            # Add deprecation warnings for deprecated versions
            deprecated_versions = getattr(settings, 'DEPRECATED_API_VERSIONS', [])
            if request.api_version in deprecated_versions:
                response['X-API-Deprecation-Warning'] = f'API version {request.api_version} is deprecated'
                sunset_dates = getattr(settings, 'API_SUNSET_DATES', {})
                if request.api_version in sunset_dates:
                    response['X-API-Sunset-Date'] = sunset_dates[request.api_version]
                
                # Add recommended version header
                recommended_version = getattr(settings, 'RECOMMENDED_API_VERSION', 'v2')
                response['X-API-Recommended-Version'] = recommended_version
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests for monitoring and debugging.
    """
    
    def process_request(self, request):
        """
        Log incoming API requests.
        """
        if request.path.startswith('/api/'):
            logger.info(
                f"API Request: {request.method} {request.path} "
                f"- User: {getattr(request.user, 'username', 'Anonymous')} "
                f"- IP: {self.get_client_ip(request)} "
                f"- Version: {getattr(request, 'api_version', 'unknown')}"
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Log API response status.
        """
        if request.path.startswith('/api/'):
            logger.info(
                f"API Response: {request.method} {request.path} "
                f"- Status: {response.status_code} "
                f"- User: {getattr(request.user, 'username', 'Anonymous')}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CORSMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware for API endpoints.
    """
    
    def process_response(self, request, response):
        """
        Add CORS headers to API responses.
        """
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = getattr(settings, 'CORS_ALLOWED_ORIGINS', '*')
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Accept-Language, Content-Language, Content-Type, '
                'Authorization, X-API-Version, X-Requested-With'
            )
            response['Access-Control-Expose-Headers'] = (
                'X-API-Version, X-API-Deprecation-Warning, X-API-Sunset-Date'
            )
            response['Access-Control-Max-Age'] = '86400'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware for API endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_cache = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Check rate limits for API requests.
        """
        if not request.path.startswith('/api/'):
            return None
        
        # Skip rate limiting for authenticated admin users
        if request.user.is_authenticated and request.user.is_staff:
            return None
        
        client_ip = self.get_client_ip(request)
        rate_limit = getattr(settings, 'API_RATE_LIMIT', 1000)  # requests per hour
        
        # Simple in-memory rate limiting (in production, use Redis)
        import time
        current_time = int(time.time() / 3600)  # Hour bucket
        key = f"{client_ip}:{current_time}"
        
        if key in self.rate_limit_cache:
            self.rate_limit_cache[key] += 1
        else:
            self.rate_limit_cache[key] = 1
        
        if self.rate_limit_cache[key] > rate_limit:
            return JsonResponse(
                {
                    'error': {
                        'message': 'Rate limit exceeded',
                        'code': 'rate_limit_exceeded',
                        'retry_after': 3600
                    }
                },
                status=429
            )
        
        return None
    
    def get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip