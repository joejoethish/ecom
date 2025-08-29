"""
Test cases for the automated testing and validation framework.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .testing_framework import (
    APITestFramework,
    ResponseFormatValidator,
    AuthenticationFlowTester,
    CORSConfigurationValidator,
    PerformanceTestSuite,
    ComprehensiveTestRunner,
    TestResult,
    TestSuite
)
from .api_validation import APIDiscoveryService, APIEndpoint

User = get_user_model()


class APITestFrameworkTestCase(APITestCase):
    """Test cases for the main API testing framework."""
    
    def setUp(self):
        self.framework = APITestFramework()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_setup_test_environment(self):
        """Test setting up the test environment."""
        self.framework.setup_test_environment()
        
        # Check that test users were created
        self.assertIsNotNone(self.framework.test_user)
        self.assertIsNotNone(self.framework.admin_user)
        self.assertIsNotNone(self.framework.jwt_token)
        self.assertIsNotNone(self.framework.admin_token)
    
    def test_load_response_schemas(self):
        """Test loading response schemas."""
        self.framework.load_response_schemas()
        
        # Check that schemas are loaded
        self.assertIn('user_profile', self.framework.response_schemas)
        self.assertIn('product_list', self.framework.response_schemas)
        self.assertIn('error_response', self.framework.response_schemas)
        self.assertIn('jwt_token', self.framework.response_schemas)
    
    def test_prepare_test_url(self):
        """Test URL pattern preparation."""
        test_cases = [
            ('/api/v1/users/<int:id>/', '/api/v1/users/1/'),
            ('/api/v1/products/<str:slug>/', '/api/v1/products/test/'),
            ('/api/v1/orders/<uuid:order_id>/', '/api/v1/orders/12345678-1234-5678-9012-123456789012/'),
            ('^api/v1/test/$', '/api/v1/test/'),
        ]
        
        for input_pattern, expected_output in test_cases:
            result = self.framework._prepare_test_url(input_pattern)
            self.assertEqual(result, expected_output)
    
    def test_generate_test_payload(self):
        """Test test payload generation."""
        schema = {
            'username': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'required': True},
            'age': {'type': 'integer', 'required': False},
            'is_active': {'type': 'boolean', 'required': True}
        }
        
        payload = self.framework._generate_test_payload(schema)
        
        # Check required fields are present
        self.assertIn('username', payload)
        self.assertIn('email', payload)
        self.assertIn('is_active', payload)
        
        # Check types
        self.assertIsInstance(payload['username'], str)
        self.assertIsInstance(payload['is_active'], bool)
    
    @patch('apps.debugging.testing_framework.APIDiscoveryService')
    def test_run_comprehensive_tests(self, mock_discovery):
        """Test running comprehensive test suite."""
        # Mock endpoint discovery
        mock_endpoint = APIEndpoint(
            url_pattern='/api/v1/test/',
            name='test_endpoint',
            view_class='TestView',
            http_methods=['GET', 'POST'],
            authentication_required=False,
            permissions=[]
        )
        mock_discovery.return_value.discover_all_endpoints.return_value = [mock_endpoint]
        
        # Mock the individual test methods to avoid actual HTTP calls
        with patch.object(self.framework, 'test_all_endpoints', return_value=[]):
            with patch.object(self.framework, 'test_authentication_flows', return_value=[]):
                with patch.object(self.framework, 'test_response_formats', return_value=[]):
                    with patch.object(self.framework, 'test_cors_configuration', return_value=[]):
                        with patch.object(self.framework, 'test_performance_thresholds', return_value=[]):
                            result = self.framework.run_comprehensive_tests()
        
        # Check result structure
        self.assertIsInstance(result, TestSuite)
        self.assertEqual(result.name, "Comprehensive API Test Suite")
        self.assertIsInstance(result.results, list)


class ResponseFormatValidatorTestCase(TestCase):
    """Test cases for response format validation."""
    
    def setUp(self):
        self.validator = ResponseFormatValidator()
    
    def test_load_default_schemas(self):
        """Test loading default schemas."""
        self.validator.load_default_schemas()
        
        # Check that default schemas are loaded
        self.assertIn('paginated_list', self.validator.schemas)
        self.assertIn('detail_response', self.validator.schemas)
        self.assertIn('error_400', self.validator.schemas)
    
    def test_validate_headers(self):
        """Test header validation."""
        # Test valid headers
        valid_headers = {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }
        errors = self.validator._validate_headers(valid_headers, 200)
        self.assertEqual(len(errors), 0)
        
        # Test missing headers
        invalid_headers = {}
        errors = self.validator._validate_headers(invalid_headers, 200)
        self.assertGreater(len(errors), 0)
    
    def test_validate_status_code(self):
        """Test status code validation."""
        # Test valid status codes
        valid_codes = [200, 201, 400, 401, 404, 500]
        for code in valid_codes:
            errors = self.validator._validate_status_code(code)
            self.assertEqual(len(errors), 0)
        
        # Test invalid status code
        errors = self.validator._validate_status_code(999)
        self.assertGreater(len(errors), 0)
    
    def test_is_valid_json(self):
        """Test JSON validation."""
        # Valid JSON
        self.assertTrue(self.validator._is_valid_json('{"key": "value"}'))
        self.assertTrue(self.validator._is_valid_json('[]'))
        
        # Invalid JSON
        self.assertFalse(self.validator._is_valid_json('invalid json'))
        self.assertFalse(self.validator._is_valid_json('{"key": }'))
    
    def test_register_custom_schema(self):
        """Test registering custom schemas."""
        custom_schema = {
            'type': 'object',
            'properties': {
                'custom_field': {'type': 'string'}
            }
        }
        
        self.validator.register_custom_schema('custom_test', custom_schema)
        self.assertIn('custom_test', self.validator.schemas)
        self.assertEqual(self.validator.schemas['custom_test'], custom_schema)


class AuthenticationFlowTesterTestCase(APITestCase):
    """Test cases for authentication flow testing."""
    
    def setUp(self):
        self.tester = AuthenticationFlowTester(self.client)
    
    def test_setup_test_users(self):
        """Test setting up test users."""
        self.tester._setup_test_users()
        
        # Check that users were created
        self.assertIsNotNone(self.tester.test_user)
        self.assertIsNotNone(self.tester.admin_user)
        
        # Check user properties
        self.assertEqual(self.tester.test_user.username, 'auth_test_user')
        self.assertTrue(self.tester.admin_user.is_staff)
        self.assertTrue(self.tester.admin_user.is_superuser)
    
    @patch('apps.debugging.testing_framework.AuthenticationFlowTester._make_single_request')
    def test_jwt_login_success(self, mock_request):
        """Test successful JWT login."""
        # Mock successful login response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access': 'test_access_token',
            'refresh': 'test_refresh_token'
        }
        mock_request.return_value = mock_response
        
        self.tester._setup_test_users()
        result = self.tester._test_jwt_login('testuser', 'testpass')
        
        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIn('access_token', self.tester.tokens)
    
    @patch('apps.debugging.testing_framework.AuthenticationFlowTester._make_single_request')
    def test_jwt_login_failure(self, mock_request):
        """Test failed JWT login."""
        # Mock failed login response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'detail': 'Invalid credentials'}
        mock_request.return_value = mock_response
        
        result = self.tester._test_jwt_login('invalid', 'invalid', expect_success=False)
        
        self.assertTrue(result.success)  # Success because we expected failure
        self.assertEqual(result.status_code, 401)


class CORSConfigurationValidatorTestCase(TestCase):
    """Test cases for CORS configuration validation."""
    
    def setUp(self):
        self.validator = CORSConfigurationValidator()
    
    def test_validate_preflight_response(self):
        """Test preflight response validation."""
        # Mock valid preflight response
        mock_response = MagicMock()
        mock_response.headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        
        errors = self.validator._validate_preflight_response(mock_response, 'http://localhost:3000')
        self.assertEqual(len(errors), 0)
    
    def test_validate_preflight_response_missing_headers(self):
        """Test preflight response with missing headers."""
        # Mock response with missing headers
        mock_response = MagicMock()
        mock_response.headers = {}
        
        errors = self.validator._validate_preflight_response(mock_response, 'http://localhost:3000')
        self.assertGreater(len(errors), 0)
        
        # Check for specific error messages
        error_messages = ' '.join(errors)
        self.assertIn('Access-Control-Allow-Origin', error_messages)
        self.assertIn('Access-Control-Allow-Methods', error_messages)
    
    def test_validate_cors_response(self):
        """Test CORS response validation."""
        # Mock valid CORS response
        mock_response = MagicMock()
        mock_response.headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000'
        }
        
        errors = self.validator._validate_cors_response(mock_response, 'http://localhost:3000')
        self.assertEqual(len(errors), 0)
    
    def test_validate_credentials_cors_response(self):
        """Test CORS response validation with credentials."""
        # Mock valid credentials CORS response
        mock_response = MagicMock()
        mock_response.headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Credentials': 'true'
        }
        
        errors = self.validator._validate_credentials_cors_response(mock_response, 'http://localhost:3000')
        self.assertEqual(len(errors), 0)
        
        # Test with wildcard origin (should fail)
        mock_response.headers['Access-Control-Allow-Origin'] = '*'
        errors = self.validator._validate_credentials_cors_response(mock_response, 'http://localhost:3000')
        self.assertGreater(len(errors), 0)


class PerformanceTestSuiteTestCase(APITestCase):
    """Test cases for performance testing."""
    
    def setUp(self):
        self.performance_tester = PerformanceTestSuite(self.client)
    
    def test_performance_thresholds_configuration(self):
        """Test performance thresholds configuration."""
        thresholds = self.performance_tester.performance_thresholds
        
        # Check that thresholds are set
        self.assertIn('response_time_warning', thresholds)
        self.assertIn('response_time_critical', thresholds)
        self.assertIn('concurrent_users', thresholds)
        
        # Check reasonable values
        self.assertGreater(thresholds['response_time_warning'], 0)
        self.assertGreater(thresholds['response_time_critical'], thresholds['response_time_warning'])
    
    @patch('apps.debugging.testing_framework.PerformanceTestSuite._make_single_request')
    def test_single_endpoint_performance(self, mock_request):
        """Test single endpoint performance measurement."""
        # Mock endpoint
        endpoint = APIEndpoint(
            url_pattern='/api/v1/test/',
            name='test_endpoint',
            view_class='TestView',
            http_methods=['GET'],
            authentication_required=False,
            permissions=[]
        )
        
        # Mock fast response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        result = self.performance_tester._test_single_endpoint_performance(endpoint, 'GET')
        
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.test_name, 'performance_test_response_time')
        self.assertEqual(result.method, 'GET')
        self.assertIsNotNone(result.payload_used)


class ComprehensiveTestRunnerTestCase(TestCase):
    """Test cases for the comprehensive test runner."""
    
    def setUp(self):
        self.runner = ComprehensiveTestRunner()
    
    @patch('apps.debugging.testing_framework.APITestFramework.run_comprehensive_tests')
    def test_run_all_tests(self, mock_run_tests):
        """Test running all tests."""
        # Mock test suite result
        mock_test_suite = TestSuite(
            name="Test Suite",
            description="Test Description",
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            execution_time=30.0,
            results=[],
            summary={}
        )
        mock_run_tests.return_value = mock_test_suite
        
        result = self.runner.run_all_tests()
        
        # Check result structure
        self.assertIn('test_suite', result)
        self.assertIn('reports', result)
        self.assertIn('timestamp', result)
    
    def test_generate_executive_summary(self):
        """Test executive summary generation."""
        test_suite = TestSuite(
            name="Test Suite",
            description="Test Description",
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
            execution_time=30.0,
            results=[],
            summary={}
        )
        
        summary = self.runner._generate_executive_summary(test_suite)
        
        # Check summary structure
        self.assertIn('overall_health', summary)
        self.assertIn('total_tests', summary)
        self.assertIn('success_rate', summary)
        self.assertEqual(summary['total_tests'], 10)
        self.assertEqual(summary['passed_tests'], 9)
        self.assertEqual(summary['success_rate'], 90.0)
    
    def test_generate_recommendations(self):
        """Test recommendations generation."""
        # Create test results with various issues
        results = [
            TestResult(
                test_name="performance_test_slow",
                endpoint="/api/v1/slow/",
                method="GET",
                status_code=200,
                success=True,
                response_time=0.6,  # Slow response
                error_message=None
            ),
            TestResult(
                test_name="auth_test_failure",
                endpoint="/api/v1/auth/",
                method="POST",
                status_code=401,
                success=False,
                response_time=0.1,
                error_message="Authentication failed"
            )
        ]
        
        recommendations = self.runner._generate_recommendations(results)
        
        # Check that recommendations are generated
        self.assertIsInstance(recommendations, list)
        
        # Check for performance recommendation
        perf_recs = [r for r in recommendations if r['category'] == 'performance']
        self.assertGreater(len(perf_recs), 0)
        
        # Check for security recommendation
        security_recs = [r for r in recommendations if r['category'] == 'security']
        self.assertGreater(len(security_recs), 0)


class TestResultTestCase(TestCase):
    """Test cases for TestResult data class."""
    
    def test_test_result_creation(self):
        """Test creating TestResult instances."""
        result = TestResult(
            test_name="test_example",
            endpoint="/api/v1/test/",
            method="GET",
            status_code=200,
            success=True,
            response_time=0.1
        )
        
        self.assertEqual(result.test_name, "test_example")
        self.assertEqual(result.endpoint, "/api/v1/test/")
        self.assertEqual(result.method, "GET")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.success)
        self.assertEqual(result.response_time, 0.1)
        self.assertIsNotNone(result.timestamp)
    
    def test_test_result_with_errors(self):
        """Test TestResult with validation errors."""
        result = TestResult(
            test_name="test_with_errors",
            endpoint="/api/v1/test/",
            method="POST",
            status_code=400,
            success=False,
            response_time=0.05,
            error_message="Validation failed",
            validation_errors=["Missing required field", "Invalid format"]
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Validation failed")
        self.assertEqual(len(result.validation_errors), 2)


class TestSuiteTestCase(TestCase):
    """Test cases for TestSuite data class."""
    
    def test_test_suite_creation(self):
        """Test creating TestSuite instances."""
        results = [
            TestResult("test1", "/api/v1/test1/", "GET", 200, True, 0.1),
            TestResult("test2", "/api/v1/test2/", "POST", 201, True, 0.15),
            TestResult("test3", "/api/v1/test3/", "GET", 400, False, 0.05)
        ]
        
        suite = TestSuite(
            name="Test Suite",
            description="Example test suite",
            total_tests=3,
            passed_tests=2,
            failed_tests=1,
            execution_time=5.0,
            results=results,
            summary={"key": "value"}
        )
        
        self.assertEqual(suite.name, "Test Suite")
        self.assertEqual(suite.total_tests, 3)
        self.assertEqual(suite.passed_tests, 2)
        self.assertEqual(suite.failed_tests, 1)
        self.assertEqual(len(suite.results), 3)
        self.assertIsNotNone(suite.timestamp)