"""
Backend API Validation Engine

This module provides comprehensive validation of Django REST API endpoints,
including URL pattern discovery, serializer analysis, authentication validation,
and automated endpoint testing.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from django.urls import get_resolver, URLPattern, URLResolver
from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
import inspect

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass
class APIEndpoint:
    """Represents a discovered API endpoint with its metadata."""
    url_pattern: str
    name: str
    view_class: str
    http_methods: List[str]
    authentication_required: bool
    permissions: List[str]
    serializer_class: Optional[str] = None
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None


@dataclass
class ValidationResult:
    """Represents the result of API endpoint validation."""
    endpoint: str
    method: str
    status_code: int
    success: bool
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    payload_used: Optional[Dict] = None


class APIDiscoveryService:
    """Service for discovering Django REST API endpoints."""
    
    def __init__(self):
        self.client = APIClient()
        self.discovered_endpoints: List[APIEndpoint] = []
    
    def discover_all_endpoints(self) -> List[APIEndpoint]:
        """Discover all API endpoints in the Django project."""
        logger.info("Starting API endpoint discovery")
        
        try:
            resolver = get_resolver()
            self._scan_url_patterns(resolver.url_patterns, '')
            logger.info(f"Discovered {len(self.discovered_endpoints)} API endpoints")
            return self.discovered_endpoints
        except Exception as e:
            logger.error(f"Error during endpoint discovery: {str(e)}")
            return []
    
    def _scan_url_patterns(self, patterns, prefix: str = ''):
        """Recursively scan URL patterns to find API endpoints."""
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                # Handle included URL patterns
                new_prefix = prefix + str(pattern.pattern)
                self._scan_url_patterns(pattern.url_patterns, new_prefix)
            elif isinstance(pattern, URLPattern):
                # Handle individual URL patterns
                full_pattern = prefix + str(pattern.pattern)
                
                # Only process API endpoints (containing /api/)
                if '/api/' in full_pattern:
                    endpoint = self._analyze_endpoint(pattern, full_pattern)
                    if endpoint:
                        self.discovered_endpoints.append(endpoint)
    
    def _analyze_endpoint(self, pattern: URLPattern, full_pattern: str) -> Optional[APIEndpoint]:
        """Analyze a URL pattern to extract endpoint information."""
        try:
            view_func = pattern.callback
            view_class = None
            
            # Get the actual view class
            if hasattr(view_func, 'view_class'):
                view_class = view_func.view_class
            elif hasattr(view_func, 'cls'):
                view_class = view_func.cls
            
            if not view_class:
                return None
            
            # Extract HTTP methods
            http_methods = self._get_http_methods(view_class)
            
            # Check authentication requirements
            auth_required = self._requires_authentication(view_class)
            
            # Get permissions
            permissions = self._get_permissions(view_class)
            
            # Get serializer information
            serializer_class, request_schema, response_schema = self._get_serializer_info(view_class)
            
            return APIEndpoint(
                url_pattern=full_pattern,
                name=pattern.name or 'unnamed',
                view_class=view_class.__name__,
                http_methods=http_methods,
                authentication_required=auth_required,
                permissions=permissions,
                serializer_class=serializer_class,
                request_schema=request_schema,
                response_schema=response_schema
            )
        except Exception as e:
            logger.warning(f"Error analyzing endpoint {full_pattern}: {str(e)}")
            return None
    
    def _get_http_methods(self, view_class) -> List[str]:
        """Extract supported HTTP methods from view class."""
        methods = []
        
        if issubclass(view_class, ViewSet):
            # For ViewSets, check action methods
            for method_name in ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']:
                if hasattr(view_class, method_name):
                    if method_name == 'list':
                        methods.append('GET')
                    elif method_name == 'create':
                        methods.append('POST')
                    elif method_name == 'retrieve':
                        methods.append('GET')
                    elif method_name in ['update', 'partial_update']:
                        methods.extend(['PUT', 'PATCH'])
                    elif method_name == 'destroy':
                        methods.append('DELETE')
        elif issubclass(view_class, APIView):
            # For APIViews, check HTTP method handlers
            for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                if hasattr(view_class, method):
                    methods.append(method.upper())
        
        return list(set(methods))  # Remove duplicates
    
    def _requires_authentication(self, view_class) -> bool:
        """Check if the view requires authentication."""
        if hasattr(view_class, 'authentication_classes'):
            return len(view_class.authentication_classes) > 0
        return False
    
    def _get_permissions(self, view_class) -> List[str]:
        """Extract permission classes from view."""
        permissions = []
        if hasattr(view_class, 'permission_classes'):
            for perm_class in view_class.permission_classes:
                permissions.append(perm_class.__name__)
        return permissions
    
    def _get_serializer_info(self, view_class) -> Tuple[Optional[str], Optional[Dict], Optional[Dict]]:
        """Extract serializer information from view class."""
        serializer_class = None
        request_schema = None
        response_schema = None
        
        if hasattr(view_class, 'serializer_class') and view_class.serializer_class:
            serializer_class = view_class.serializer_class.__name__
            
            # Generate schema from serializer
            try:
                serializer_instance = view_class.serializer_class()
                request_schema = self._generate_schema_from_serializer(serializer_instance)
                response_schema = request_schema  # Assuming same schema for now
            except Exception as e:
                logger.warning(f"Error generating schema for {serializer_class}: {str(e)}")
        
        return serializer_class, request_schema, response_schema
    
    def _generate_schema_from_serializer(self, serializer) -> Dict:
        """Generate JSON schema from DRF serializer."""
        schema = {}
        
        for field_name, field in serializer.fields.items():
            field_schema = self._get_field_schema(field)
            schema[field_name] = field_schema
        
        return schema
    
    def _get_field_schema(self, field) -> Dict:
        """Get schema information for a serializer field."""
        schema = {
            'type': self._get_field_type(field),
            'required': field.required,
            'allow_null': field.allow_null,
        }
        
        if hasattr(field, 'max_length') and field.max_length:
            schema['max_length'] = field.max_length
        
        if hasattr(field, 'min_length') and field.min_length:
            schema['min_length'] = field.min_length
        
        if hasattr(field, 'choices') and field.choices:
            schema['choices'] = [choice[0] for choice in field.choices]
        
        return schema
    
    def _get_field_type(self, field) -> str:
        """Map DRF field types to schema types."""
        field_type_mapping = {
            serializers.CharField: 'string',
            serializers.EmailField: 'string',
            serializers.URLField: 'string',
            serializers.IntegerField: 'integer',
            serializers.FloatField: 'number',
            serializers.DecimalField: 'number',
            serializers.BooleanField: 'boolean',
            serializers.DateField: 'string',
            serializers.DateTimeField: 'string',
            serializers.JSONField: 'object',
            serializers.ListField: 'array',
        }
        
        for field_class, schema_type in field_type_mapping.items():
            if isinstance(field, field_class):
                return schema_type
        
        return 'string'  # Default fallback


class APIValidationService:
    """Service for validating API endpoints."""
    
    def __init__(self):
        self.client = APIClient()
        self.test_user = None
        self.jwt_token = None
    
    def setup_test_user(self):
        """Create a test user for authentication testing."""
        try:
            self.test_user, created = User.objects.get_or_create(
                username='api_test_user',
                defaults={
                    'email': 'test@example.com',
                    'is_active': True
                }
            )
            if created:
                self.test_user.set_password('testpassword123')
                self.test_user.save()
            
            # Generate JWT token
            refresh = RefreshToken.for_user(self.test_user)
            self.jwt_token = str(refresh.access_token)
            
            logger.info("Test user and JWT token created successfully")
        except Exception as e:
            logger.error(f"Error setting up test user: {str(e)}")
    
    def validate_endpoint(self, endpoint: APIEndpoint) -> List[ValidationResult]:
        """Validate a single API endpoint with various test scenarios."""
        results = []
        
        for method in endpoint.http_methods:
            # Test without authentication
            result = self._test_endpoint_request(endpoint, method, authenticated=False)
            results.append(result)
            
            # Test with authentication if required
            if endpoint.authentication_required:
                result = self._test_endpoint_request(endpoint, method, authenticated=True)
                results.append(result)
        
        return results
    
    def _test_endpoint_request(self, endpoint: APIEndpoint, method: str, authenticated: bool = False) -> ValidationResult:
        """Test a single request to an endpoint."""
        import time
        
        # Prepare URL (replace Django URL patterns with test values)
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        # Prepare headers
        headers = {}
        if authenticated and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        # Prepare payload for POST/PUT/PATCH requests
        payload = None
        if method in ['POST', 'PUT', 'PATCH'] and endpoint.request_schema:
            payload = self._generate_test_payload(endpoint.request_schema)
        
        try:
            start_time = time.time()
            
            # Make the request
            if method == 'GET':
                response = self.client.get(test_url, **headers)
            elif method == 'POST':
                response = self.client.post(test_url, data=payload, format='json', **headers)
            elif method == 'PUT':
                response = self.client.put(test_url, data=payload, format='json', **headers)
            elif method == 'PATCH':
                response = self.client.patch(test_url, data=payload, format='json', **headers)
            elif method == 'DELETE':
                response = self.client.delete(test_url, **headers)
            else:
                response = self.client.generic(method, test_url, **headers)
            
            response_time = time.time() - start_time
            
            # Determine if the response is successful
            success = 200 <= response.status_code < 500  # 4xx errors are expected for some tests
            error_message = None
            
            if not success:
                try:
                    error_data = response.json() if hasattr(response, 'json') else str(response.content)
                    error_message = str(error_data)
                except:
                    error_message = f"HTTP {response.status_code}"
            
            return ValidationResult(
                endpoint=test_url,
                method=method,
                status_code=response.status_code,
                success=success,
                error_message=error_message,
                response_time=response_time,
                payload_used=payload
            )
            
        except Exception as e:
            return ValidationResult(
                endpoint=test_url,
                method=method,
                status_code=0,
                success=False,
                error_message=str(e),
                response_time=None,
                payload_used=payload
            )
    
    def _prepare_test_url(self, url_pattern: str) -> str:
        """Convert Django URL pattern to a testable URL."""
        # Replace common Django URL patterns with test values
        test_url = url_pattern
        
        # Replace path parameters
        test_url = re.sub(r'<int:(\w+)>', '1', test_url)
        test_url = re.sub(r'<str:(\w+)>', 'test', test_url)
        test_url = re.sub(r'<slug:(\w+)>', 'test-slug', test_url)
        test_url = re.sub(r'<uuid:(\w+)>', '12345678-1234-5678-9012-123456789012', test_url)
        
        # Clean up regex patterns
        test_url = re.sub(r'\^', '', test_url)
        test_url = re.sub(r'\$', '', test_url)
        test_url = re.sub(r'\?P<\w+>', '', test_url)
        
        # Ensure URL starts with /
        if not test_url.startswith('/'):
            test_url = '/' + test_url
        
        return test_url
    
    def _generate_test_payload(self, schema: Dict) -> Dict:
        """Generate test payload based on schema."""
        payload = {}
        
        for field_name, field_info in schema.items():
            if not field_info.get('required', False):
                continue
            
            field_type = field_info.get('type', 'string')
            
            if field_type == 'string':
                if 'choices' in field_info:
                    payload[field_name] = field_info['choices'][0]
                else:
                    payload[field_name] = f'test_{field_name}'
            elif field_type == 'integer':
                payload[field_name] = 1
            elif field_type == 'number':
                payload[field_name] = 1.0
            elif field_type == 'boolean':
                payload[field_name] = True
            elif field_type == 'array':
                payload[field_name] = []
            elif field_type == 'object':
                payload[field_name] = {}
        
        return payload


class APIValidationEngine:
    """Main engine for comprehensive API validation."""
    
    def __init__(self):
        self.discovery_service = APIDiscoveryService()
        self.validation_service = APIValidationService()
        self.validation_results: List[ValidationResult] = []
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete API validation process."""
        logger.info("Starting comprehensive API validation")
        
        # Setup test environment
        self.validation_service.setup_test_user()
        
        # Discover all endpoints
        endpoints = self.discovery_service.discover_all_endpoints()
        
        # Validate each endpoint
        all_results = []
        for endpoint in endpoints:
            logger.info(f"Validating endpoint: {endpoint.url_pattern}")
            results = self.validation_service.validate_endpoint(endpoint)
            all_results.extend(results)
        
        self.validation_results = all_results
        
        # Generate summary report
        report = self._generate_validation_report(endpoints, all_results)
        
        logger.info("API validation completed")
        return report
    
    def _generate_validation_report(self, endpoints: List[APIEndpoint], results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_tests = len(results)
        successful_tests = len([r for r in results if r.success])
        failed_tests = total_tests - successful_tests
        
        # Group results by endpoint
        endpoint_results = {}
        for result in results:
            if result.endpoint not in endpoint_results:
                endpoint_results[result.endpoint] = []
            endpoint_results[result.endpoint].append(result)
        
        # Calculate average response times
        response_times = [r.response_time for r in results if r.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = {
            'summary': {
                'total_endpoints': len(endpoints),
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                'average_response_time': avg_response_time
            },
            'endpoints': [asdict(endpoint) for endpoint in endpoints],
            'test_results': [asdict(result) for result in results],
            'endpoint_results': {
                endpoint: [asdict(result) for result in endpoint_results[endpoint]]
                for endpoint in endpoint_results
            },
            'failed_tests': [asdict(result) for result in results if not result.success]
        }
        
        return report
    
    def get_validation_summary(self) -> str:
        """Get a human-readable validation summary."""
        if not self.validation_results:
            return "No validation results available. Run validation first."
        
        total = len(self.validation_results)
        successful = len([r for r in self.validation_results if r.success])
        failed = total - successful
        
        summary = f"""
API Validation Summary:
======================
Total Tests: {total}
Successful: {successful}
Failed: {failed}
Success Rate: {(successful/total*100):.1f}%

Failed Tests:
"""
        
        for result in self.validation_results:
            if not result.success:
                summary += f"- {result.method} {result.endpoint}: {result.error_message}\n"
        
        return summary


# Utility functions for API validation
def validate_all_apis():
    """Convenience function to run full API validation."""
    engine = APIValidationEngine()
    return engine.run_full_validation()


def get_api_endpoints():
    """Get all discovered API endpoints."""
    discovery = APIDiscoveryService()
    return discovery.discover_all_endpoints()


def test_single_endpoint(url_pattern: str, method: str = 'GET', authenticated: bool = False):
    """Test a single API endpoint."""
    validation_service = APIValidationService()
    validation_service.setup_test_user()
    
    # Create a mock endpoint for testing
    endpoint = APIEndpoint(
        url_pattern=url_pattern,
        name='test_endpoint',
        view_class='TestView',
        http_methods=[method],
        authentication_required=authenticated,
        permissions=[]
    )
    
    return validation_service._test_endpoint_request(endpoint, method, authenticated)


def generate_api_documentation():
    """Generate API documentation from discovered endpoints."""
    discovery = APIDiscoveryService()
    endpoints = discovery.discover_all_endpoints()
    
    documentation = {
        'title': 'API Documentation',
        'version': '1.0.0',
        'endpoints': []
    }
    
    for endpoint in endpoints:
        doc_endpoint = {
            'url': endpoint.url_pattern,
            'name': endpoint.name,
            'methods': endpoint.http_methods,
            'authentication_required': endpoint.authentication_required,
            'permissions': endpoint.permissions,
            'view_class': endpoint.view_class
        }
        
        if endpoint.request_schema:
            doc_endpoint['request_schema'] = endpoint.request_schema
        
        if endpoint.response_schema:
            doc_endpoint['response_schema'] = endpoint.response_schema
        
        documentation['endpoints'].append(doc_endpoint)
    
    return documentation


def check_api_health():
    """Quick health check for critical API endpoints."""
    critical_endpoints = [
        '/api/v1/auth/login/',
        '/api/v1/auth/logout/',
        '/api/v1/products/',
        '/api/v1/cart/',
        '/api/v1/orders/'
    ]
    
    health_results = []
    validation_service = APIValidationService()
    
    for endpoint_url in critical_endpoints:
        try:
            result = test_single_endpoint(endpoint_url, 'GET', False)
            health_results.append({
                'endpoint': endpoint_url,
                'status': 'healthy' if result.success else 'unhealthy',
                'response_time': result.response_time,
                'status_code': result.status_code
            })
        except Exception as e:
            health_results.append({
                'endpoint': endpoint_url,
                'status': 'error',
                'error': str(e)
            })
    
    logger.info("API health check completed")
    return {
        'timestamp': datetime.now().isoformat(),
        'results': health_results,
        'overall_health': 'healthy' if all(r.get('status') == 'healthy' for r in health_results) else 'degraded'
    }


class APIValidationMiddleware:
    """Middleware for real-time API validation during requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.validation_service = APIValidationService()
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Log API call for validation tracking
        if request.path.startswith('/api/'):
            self._log_api_call(request, response)
        
        return response
    
    def _log_api_call(self, request, response):
        """Log API call details for validation tracking."""
        try:
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'user_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add correlation ID if available
            if hasattr(request, 'correlation_id'):
                log_data['correlation_id'] = request.correlation_id
            
            logger.info(f"API Call: {json.dumps(log_data)}")
        except Exception as e:
            logger.error(f"Error logging API call: {str(e)}")


# Django management command integration
class Command:
    """Django management command for API validation."""
    
    help = 'Run comprehensive API validation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            help='Validate specific endpoint only'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'json', 'file'],
            help='Output format for validation results'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Output file path (when output=file)'
        )
    
    def handle(self, *args, **options):
        if options['endpoint']:
            # Validate single endpoint
            result = test_single_endpoint(options['endpoint'])
            self._output_result(result, options)
        else:
            # Run full validation
            engine = APIValidationEngine()
            results = engine.run_full_validation()
            self._output_results(results, options)
    
    def _output_result(self, result, options):
        """Output single validation result."""
        if options['output'] == 'json':
            print(json.dumps(asdict(result), indent=2))
        else:
            print(f"Endpoint: {result.endpoint}")
            print(f"Method: {result.method}")
            print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"Status Code: {result.status_code}")
            if result.error_message:
                print(f"Error: {result.error_message}")
    
    def _output_results(self, results, options):
        """Output full validation results."""
        if options['output'] == 'json':
            output = json.dumps(results, indent=2)
        else:
            output = f"""
API Validation Results
=====================
Total Endpoints: {results['summary']['total_endpoints']}
Total Tests: {results['summary']['total_tests']}
Success Rate: {results['summary']['success_rate']:.1f}%
Average Response Time: {results['summary']['average_response_time']:.3f}s

Failed Tests: {results['summary']['failed_tests']}
"""
            for failed_test in results['failed_tests']:
                output += f"- {failed_test['method']} {failed_test['endpoint']}: {failed_test['error_message']}\n"
        
        if options['output'] == 'file' and options['file']:
            with open(options['file'], 'w') as f:
                f.write(output)
            print(f"Results written to {options['file']}")
        else:
            print(output)