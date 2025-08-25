"""
Unit tests for API validation engine.
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import path, include
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated

from apps.debugging.api_validation import (
    APIDiscoveryService,
    APIValidationService,
    APIValidationEngine,
    APIEndpoint,
    ValidationResult,
    validate_all_apis,
    get_api_endpoints,
    test_single_endpoint,
    check_api_health
)

User = get_user_model()


# Mock serializers for testing
class TestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(required=True)
    age = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(default=True)


# Mock views for testing
class TestAPIView(APIView):
    serializer_class = TestSerializer
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        return Response({'message': 'GET success'})
    
    def post(self, request):
        return Response({'message': 'POST success'}, status=status.HTTP_201_CREATED)


class AuthenticatedAPIView(APIView):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({'message': 'Authenticated GET success'})


class TestViewSet(ModelViewSet):
    serializer_class = TestSerializer
    authentication_classes = []
    permission_classes = []
    
    def list(self, request):
        return Response([{'id': 1, 'name': 'test'}])
    
    def create(self, request):
        return Response({'id': 1, 'name': 'created'}, status=status.HTTP_201_CREATED)


class APIDiscoveryServiceTest(TestCase):
    """Test cases for API discovery service."""
    
    def setUp(self):
        self.discovery_service = APIDiscoveryService()
    
    @patch('apps.debugging.api_validation.get_resolver')
    def test_discover_all_endpoints(self, mock_get_resolver):
        """Test endpoint discovery functionality."""
        # Mock URL resolver
        mock_resolver = Mock()
        mock_pattern = Mock()
        mock_pattern.pattern = '/api/test/'
        mock_pattern.callback = TestAPIView.as_view()
        mock_pattern.name = 'test-api'
        
        mock_resolver.url_patterns = [mock_pattern]
        mock_get_resolver.return_value = mock_resolver
        
        endpoints = self.discovery_service.discover_all_endpoints()
        
        self.assertIsInstance(endpoints, list)
        mock_get_resolver.assert_called_once()
    
    def test_get_http_methods_apiview(self):
        """Test HTTP method extraction from APIView."""
        methods = self.discovery_service._get_http_methods(TestAPIView)
        
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
    
    def test_get_http_methods_viewset(self):
        """Test HTTP method extraction from ViewSet."""
        methods = self.discovery_service._get_http_methods(TestViewSet)
        
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
    
    def test_requires_authentication(self):
        """Test authentication requirement detection."""
        # Test view without authentication
        auth_required = self.discovery_service._requires_authentication(TestAPIView)
        self.assertFalse(auth_required)
        
        # Test view with authentication
        auth_required = self.discovery_service._requires_authentication(AuthenticatedAPIView)
        self.assertTrue(auth_required)
    
    def test_get_permissions(self):
        """Test permission extraction from view."""
        permissions = self.discovery_service._get_permissions(AuthenticatedAPIView)
        
        self.assertIn('IsAuthenticated', permissions)
    
    def test_get_serializer_info(self):
        """Test serializer information extraction."""
        serializer_class, request_schema, response_schema = self.discovery_service._get_serializer_info(TestAPIView)
        
        self.assertEqual(serializer_class, 'TestSerializer')
        self.assertIsInstance(request_schema, dict)
        self.assertIn('name', request_schema)
        self.assertIn('email', request_schema)
    
    def test_generate_schema_from_serializer(self):
        """Test schema generation from serializer."""
        serializer = TestSerializer()
        schema = self.discovery_service._generate_schema_from_serializer(serializer)
        
        self.assertIn('name', schema)
        self.assertIn('email', schema)
        self.assertIn('age', schema)
        self.assertIn('is_active', schema)
        
        # Check field properties
        self.assertEqual(schema['name']['type'], 'string')
        self.assertTrue(schema['name']['required'])
        self.assertEqual(schema['email']['type'], 'string')
        self.assertTrue(schema['email']['required'])
        self.assertEqual(schema['age']['type'], 'integer')
        self.assertFalse(schema['age']['required'])
    
    def test_get_field_type(self):
        """Test field type mapping."""
        char_field = serializers.CharField()
        email_field = serializers.EmailField()
        int_field = serializers.IntegerField()
        bool_field = serializers.BooleanField()
        
        self.assertEqual(self.discovery_service._get_field_type(char_field), 'string')
        self.assertEqual(self.discovery_service._get_field_type(email_field), 'string')
        self.assertEqual(self.discovery_service._get_field_type(int_field), 'integer')
        self.assertEqual(self.discovery_service._get_field_type(bool_field), 'boolean')


class APIValidationServiceTest(TestCase):
    """Test cases for API validation service."""
    
    def setUp(self):
        self.validation_service = APIValidationService()
    
    def test_setup_test_user(self):
        """Test test user creation."""
        self.validation_service.setup_test_user()
        
        self.assertIsNotNone(self.validation_service.test_user)
        self.assertIsNotNone(self.validation_service.jwt_token)
        self.assertEqual(self.validation_service.test_user.username, 'api_test_user')
    
    def test_prepare_test_url(self):
        """Test URL pattern conversion to testable URL."""
        # Test integer parameter replacement
        test_url = self.validation_service._prepare_test_url('/api/users/<int:user_id>/')
        self.assertEqual(test_url, '/api/users/1/')
        
        # Test string parameter replacement
        test_url = self.validation_service._prepare_test_url('/api/products/<str:category>/')
        self.assertEqual(test_url, '/api/products/test/')
        
        # Test slug parameter replacement
        test_url = self.validation_service._prepare_test_url('/api/posts/<slug:slug>/')
        self.assertEqual(test_url, '/api/posts/test-slug/')
        
        # Test UUID parameter replacement
        test_url = self.validation_service._prepare_test_url('/api/items/<uuid:item_id>/')
        self.assertIn('12345678-1234-5678-9012-123456789012', test_url)
    
    def test_generate_test_payload(self):
        """Test payload generation from schema."""
        schema = {
            'name': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'required': True},
            'age': {'type': 'integer', 'required': False},
            'is_active': {'type': 'boolean', 'required': True},
            'tags': {'type': 'array', 'required': False},
            'metadata': {'type': 'object', 'required': False}
        }
        
        payload = self.validation_service._generate_test_payload(schema)
        
        # Check required fields are included
        self.assertIn('name', payload)
        self.assertIn('email', payload)
        self.assertIn('is_active', payload)
        
        # Check optional fields are not included
        self.assertNotIn('age', payload)
        self.assertNotIn('tags', payload)
        self.assertNotIn('metadata', payload)
        
        # Check data types
        self.assertIsInstance(payload['name'], str)
        self.assertIsInstance(payload['email'], str)
        self.assertIsInstance(payload['is_active'], bool)
    
    @patch('apps.debugging.api_validation.APIClient')
    def test_test_endpoint_request(self, mock_client_class):
        """Test endpoint request testing."""
        # Mock API client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'success'}
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Create test endpoint
        endpoint = APIEndpoint(
            url_pattern='/api/test/',
            name='test',
            view_class='TestView',
            http_methods=['GET'],
            authentication_required=False,
            permissions=[]
        )
        
        # Test the request
        result = self.validation_service._test_endpoint_request(endpoint, 'GET', False)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertEqual(result.method, 'GET')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.success)


class APIValidationEngineTest(TestCase):
    """Test cases for API validation engine."""
    
    def setUp(self):
        self.engine = APIValidationEngine()
    
    @patch('apps.debugging.api_validation.APIDiscoveryService')
    @patch('apps.debugging.api_validation.APIValidationService')
    def test_run_full_validation(self, mock_validation_service, mock_discovery_service):
        """Test full validation process."""
        # Mock discovery service
        mock_discovery = Mock()
        mock_endpoint = APIEndpoint(
            url_pattern='/api/test/',
            name='test',
            view_class='TestView',
            http_methods=['GET'],
            authentication_required=False,
            permissions=[]
        )
        mock_discovery.discover_all_endpoints.return_value = [mock_endpoint]
        mock_discovery_service.return_value = mock_discovery
        
        # Mock validation service
        mock_validation = Mock()
        mock_result = ValidationResult(
            endpoint='/api/test/',
            method='GET',
            status_code=200,
            success=True
        )
        mock_validation.validate_endpoint.return_value = [mock_result]
        mock_validation_service.return_value = mock_validation
        
        # Run validation
        report = self.engine.run_full_validation()
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('endpoints', report)
        self.assertIn('test_results', report)
        self.assertIn('endpoint_results', report)
        self.assertIn('failed_tests', report)
        
        # Check summary
        summary = report['summary']
        self.assertEqual(summary['total_endpoints'], 1)
        self.assertEqual(summary['total_tests'], 1)
        self.assertEqual(summary['successful_tests'], 1)
        self.assertEqual(summary['failed_tests'], 0)
        self.assertEqual(summary['success_rate'], 100.0)
    
    def test_generate_validation_report(self):
        """Test validation report generation."""
        # Create test data
        endpoint = APIEndpoint(
            url_pattern='/api/test/',
            name='test',
            view_class='TestView',
            http_methods=['GET'],
            authentication_required=False,
            permissions=[]
        )
        
        result = ValidationResult(
            endpoint='/api/test/',
            method='GET',
            status_code=200,
            success=True,
            response_time=0.1
        )
        
        report = self.engine._generate_validation_report([endpoint], [result])
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertEqual(report['summary']['total_endpoints'], 1)
        self.assertEqual(report['summary']['total_tests'], 1)
        self.assertEqual(report['summary']['successful_tests'], 1)
        self.assertEqual(report['summary']['success_rate'], 100.0)
        self.assertEqual(report['summary']['average_response_time'], 0.1)


class UtilityFunctionsTest(TestCase):
    """Test cases for utility functions."""
    
    @patch('apps.debugging.api_validation.APIValidationEngine')
    def test_validate_all_apis(self, mock_engine_class):
        """Test validate_all_apis utility function."""
        mock_engine = Mock()
        mock_engine.run_full_validation.return_value = {'test': 'result'}
        mock_engine_class.return_value = mock_engine
        
        result = validate_all_apis()
        
        self.assertEqual(result, {'test': 'result'})
        mock_engine.run_full_validation.assert_called_once()
    
    @patch('apps.debugging.api_validation.APIDiscoveryService')
    def test_get_api_endpoints(self, mock_discovery_service):
        """Test get_api_endpoints utility function."""
        mock_discovery = Mock()
        mock_discovery.discover_all_endpoints.return_value = ['endpoint1', 'endpoint2']
        mock_discovery_service.return_value = mock_discovery
        
        result = get_api_endpoints()
        
        self.assertEqual(result, ['endpoint1', 'endpoint2'])
        mock_discovery.discover_all_endpoints.assert_called_once()
    
    @patch('apps.debugging.api_validation.APIValidationService')
    def test_test_single_endpoint(self, mock_validation_service):
        """Test test_single_endpoint utility function."""
        mock_validation = Mock()
        mock_result = ValidationResult(
            endpoint='/api/test/',
            method='GET',
            status_code=200,
            success=True
        )
        mock_validation._test_endpoint_request.return_value = mock_result
        mock_validation_service.return_value = mock_validation
        
        result = test_single_endpoint('/api/test/', 'GET', False)
        
        self.assertEqual(result, mock_result)
        mock_validation.setup_test_user.assert_called_once()
    
    @patch('apps.debugging.api_validation.test_single_endpoint')
    def test_check_api_health(self, mock_test_endpoint):
        """Test check_api_health utility function."""
        mock_result = ValidationResult(
            endpoint='/api/v1/auth/login/',
            method='GET',
            status_code=200,
            success=True,
            response_time=0.1
        )
        mock_test_endpoint.return_value = mock_result
        
        result = check_api_health()
        
        self.assertIn('timestamp', result)
        self.assertIn('results', result)
        self.assertIn('overall_health', result)
        self.assertEqual(result['overall_health'], 'healthy')
        
        # Check that critical endpoints were tested
        self.assertEqual(mock_test_endpoint.call_count, 5)  # 5 critical endpoints


class APIValidationMiddlewareTest(TestCase):
    """Test cases for API validation middleware."""
    
    def setUp(self):
        from apps.debugging.api_validation import APIValidationMiddleware
        self.middleware = APIValidationMiddleware(lambda request: Mock(status_code=200))
    
    @patch('apps.debugging.api_validation.logger')
    def test_api_call_logging(self, mock_logger):
        """Test API call logging functionality."""
        # Create mock request
        request = Mock()
        request.method = 'GET'
        request.path = '/api/test/'
        request.user = Mock()
        request.user.is_authenticated = True
        request.correlation_id = 'test-correlation-id'
        
        # Process request
        response = self.middleware(request)
        
        # Check that logging was called
        mock_logger.info.assert_called()
        
        # Check log data structure
        log_calls = mock_logger.info.call_args_list
        api_log_call = [call for call in log_calls if 'API Call:' in str(call)]
        self.assertTrue(len(api_log_call) > 0)
    
    def test_non_api_request_not_logged(self):
        """Test that non-API requests are not logged."""
        with patch('apps.debugging.api_validation.logger') as mock_logger:
            # Create mock request for non-API path
            request = Mock()
            request.path = '/admin/users/'
            
            # Process request
            self.middleware(request)
            
            # Check that API logging was not called
            log_calls = mock_logger.info.call_args_list
            api_log_calls = [call for call in log_calls if 'API Call:' in str(call)]
            self.assertEqual(len(api_log_calls), 0)