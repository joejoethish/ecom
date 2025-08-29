"""
Automated Testing and Validation Framework

This module provides comprehensive automated testing tools for API endpoints,
response validation, authentication flows, and CORS configuration validation.
"""

import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin, urlparse
import re

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import jsonschema
from jsonschema import validate, ValidationError as JSONSchemaValidationError

from .api_validation import APIDiscoveryService, APIEndpoint
from .models import WorkflowSession, TraceStep, ErrorLog

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass
class TestResult:
    """Represents the result of a single test execution."""
    test_name: str
    endpoint: str
    method: str
    status_code: int
    success: bool
    response_time: float
    error_message: Optional[str] = None
    payload_used: Optional[Dict] = None
    response_data: Optional[Dict] = None
    validation_errors: List[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class TestSuite:
    """Represents a collection of test results."""
    name: str
    description: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    results: List[TestResult]
    summary: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class APITestFramework:
    """Comprehensive API testing framework with automated endpoint validation."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or 'http://localhost:8000'
        self.client = APIClient()
        self.session = requests.Session()
        self.test_user = None
        self.jwt_token = None
        self.admin_user = None
        self.admin_token = None
        self.discovery_service = APIDiscoveryService()
        
        # Test configuration
        self.timeout = 30  # seconds
        self.max_concurrent_tests = 10
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
        
        # Response schemas for validation
        self.response_schemas = {}
        self.load_response_schemas()
    
    def setup_test_environment(self):
        """Set up test users and authentication tokens."""
        try:
            # Create regular test user
            self.test_user, created = User.objects.get_or_create(
                username='api_test_user',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'is_active': True
                }
            )
            if created:
                self.test_user.set_password('testpassword123')
                self.test_user.save()
            
            # Generate JWT token for regular user
            refresh = RefreshToken.for_user(self.test_user)
            self.jwt_token = str(refresh.access_token)
            
            # Create admin test user
            self.admin_user, created = User.objects.get_or_create(
                username='api_admin_user',
                defaults={
                    'email': 'admin@example.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                self.admin_user.set_password('adminpassword123')
                self.admin_user.save()
            
            # Generate JWT token for admin user
            admin_refresh = RefreshToken.for_user(self.admin_user)
            self.admin_token = str(admin_refresh.access_token)
            
            logger.info("Test environment setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up test environment: {str(e)}")
            raise
    
    def load_response_schemas(self):
        """Load expected response schemas for validation."""
        # Define common response schemas
        self.response_schemas = {
            'user_profile': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'first_name': {'type': 'string'},
                    'last_name': {'type': 'string'},
                    'is_active': {'type': 'boolean'}
                },
                'required': ['id', 'username', 'email']
            },
            'product_list': {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer'},
                    'next': {'type': ['string', 'null']},
                    'previous': {'type': ['string', 'null']},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'price': {'type': 'string'},
                                'description': {'type': 'string'}
                            },
                            'required': ['id', 'name', 'price']
                        }
                    }
                },
                'required': ['count', 'results']
            },
            'error_response': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                    'code': {'type': 'string'}
                }
            },
            'jwt_token': {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'}
                },
                'required': ['access', 'refresh']
            }
        }
    
    def run_comprehensive_tests(self) -> TestSuite:
        """Run comprehensive API testing suite."""
        logger.info("Starting comprehensive API testing suite")
        start_time = time.time()
        
        # Setup test environment
        self.setup_test_environment()
        
        # Discover all endpoints
        endpoints = self.discovery_service.discover_all_endpoints()
        
        # Run all test categories
        all_results = []
        
        # 1. Basic endpoint validation
        endpoint_results = self.test_all_endpoints(endpoints)
        all_results.extend(endpoint_results)
        
        # 2. Authentication flow testing
        auth_results = self.test_authentication_flows()
        all_results.extend(auth_results)
        
        # 3. Response format validation
        format_results = self.test_response_formats(endpoints)
        all_results.extend(format_results)
        
        # 4. CORS configuration testing
        cors_results = self.test_cors_configuration(endpoints)
        all_results.extend(cors_results)
        
        # 5. Performance testing
        performance_results = self.test_performance_thresholds(endpoints)
        all_results.extend(performance_results)
        
        # Calculate summary statistics
        execution_time = time.time() - start_time
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r.success])
        failed_tests = total_tests - passed_tests
        
        # Generate detailed summary
        summary = self._generate_test_summary(all_results, endpoints)
        
        test_suite = TestSuite(
            name="Comprehensive API Test Suite",
            description="Complete validation of all API endpoints and functionality",
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            execution_time=execution_time,
            results=all_results,
            summary=summary
        )
        
        logger.info(f"Comprehensive testing completed: {passed_tests}/{total_tests} tests passed")
        return test_suite
    
    def test_all_endpoints(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test all discovered API endpoints with various scenarios."""
        logger.info(f"Testing {len(endpoints)} discovered endpoints")
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_tests) as executor:
            # Submit all endpoint tests
            future_to_endpoint = {}
            
            for endpoint in endpoints:
                for method in endpoint.http_methods:
                    # Test without authentication
                    future = executor.submit(
                        self._test_endpoint_scenario,
                        endpoint, method, authenticated=False
                    )
                    future_to_endpoint[future] = (endpoint, method, False)
                    
                    # Test with authentication if required
                    if endpoint.authentication_required:
                        future = executor.submit(
                            self._test_endpoint_scenario,
                            endpoint, method, authenticated=True
                        )
                        future_to_endpoint[future] = (endpoint, method, True)
            
            # Collect results
            for future in as_completed(future_to_endpoint):
                endpoint, method, authenticated = future_to_endpoint[future]
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                except Exception as e:
                    error_result = TestResult(
                        test_name=f"endpoint_test_{method.lower()}",
                        endpoint=endpoint.url_pattern,
                        method=method,
                        status_code=0,
                        success=False,
                        response_time=0.0,
                        error_message=f"Test execution failed: {str(e)}"
                    )
                    results.append(error_result)
        
        return results
    
    def _test_endpoint_scenario(self, endpoint: APIEndpoint, method: str, authenticated: bool) -> TestResult:
        """Test a specific endpoint scenario."""
        test_name = f"endpoint_test_{method.lower()}_{'auth' if authenticated else 'noauth'}"
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        # Prepare headers
        headers = {}
        if authenticated:
            token = self.admin_token if 'admin' in endpoint.url_pattern else self.jwt_token
            headers['Authorization'] = f'Bearer {token}'
        
        # Prepare payload for write operations
        payload = None
        if method in ['POST', 'PUT', 'PATCH'] and endpoint.request_schema:
            payload = self._generate_test_payload(endpoint.request_schema)
        
        # Execute test with retry logic
        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                
                # Make the request
                response = self._make_request(method, test_url, headers, payload)
                
                response_time = time.time() - start_time
                
                # Validate response
                validation_errors = self._validate_response(response, endpoint, method)
                
                # Determine success
                success = self._is_response_successful(response, endpoint, authenticated)
                
                return TestResult(
                    test_name=test_name,
                    endpoint=test_url,
                    method=method,
                    status_code=response.status_code,
                    success=success and len(validation_errors) == 0,
                    response_time=response_time,
                    error_message=None if success else f"HTTP {response.status_code}",
                    payload_used=payload,
                    response_data=self._safe_json_parse(response),
                    validation_errors=validation_errors
                )
                
            except Exception as e:
                if attempt == self.retry_attempts - 1:  # Last attempt
                    return TestResult(
                        test_name=test_name,
                        endpoint=test_url,
                        method=method,
                        status_code=0,
                        success=False,
                        response_time=0.0,
                        error_message=str(e),
                        payload_used=payload
                    )
                else:
                    time.sleep(self.retry_delay)
                    continue
    
    def _make_request(self, method: str, url: str, headers: Dict, payload: Dict = None):
        """Make HTTP request using Django test client."""
        # Set headers on client
        for key, value in headers.items():
            if key == 'Authorization':
                self.client.credentials(HTTP_AUTHORIZATION=value)
        
        # Make request based on method
        if method == 'GET':
            return self.client.get(url)
        elif method == 'POST':
            return self.client.post(url, data=payload, format='json')
        elif method == 'PUT':
            return self.client.put(url, data=payload, format='json')
        elif method == 'PATCH':
            return self.client.patch(url, data=payload, format='json')
        elif method == 'DELETE':
            return self.client.delete(url)
        else:
            return self.client.generic(method, url, data=payload, format='json')
    
    def _prepare_test_url(self, url_pattern: str) -> str:
        """Convert Django URL pattern to testable URL."""
        test_url = url_pattern
        
        # Replace path parameters with test values
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
        """Generate test payload based on request schema."""
        payload = {}
        
        for field_name, field_info in schema.items():
            if not field_info.get('required', False):
                continue
            
            field_type = field_info.get('type', 'string')
            
            if field_type == 'string':
                if 'choices' in field_info:
                    payload[field_name] = field_info['choices'][0]
                elif field_name.lower() in ['email', 'email_address']:
                    payload[field_name] = 'test@example.com'
                elif field_name.lower() in ['password', 'password1', 'password2']:
                    payload[field_name] = 'testpassword123'
                elif field_name.lower() in ['username', 'user_name']:
                    payload[field_name] = 'testuser'
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
    
    def _validate_response(self, response, endpoint: APIEndpoint, method: str) -> List[str]:
        """Validate response format and content."""
        validation_errors = []
        
        try:
            # Check if response has content
            if hasattr(response, 'content') and response.content:
                # Try to parse JSON
                try:
                    response_data = json.loads(response.content)
                except json.JSONDecodeError:
                    if response.status_code < 400:  # Only error for successful responses
                        validation_errors.append("Response is not valid JSON")
                    return validation_errors
                
                # Validate against known schemas
                schema_key = self._get_schema_key(endpoint, method, response.status_code)
                if schema_key and schema_key in self.response_schemas:
                    try:
                        validate(response_data, self.response_schemas[schema_key])
                    except JSONSchemaValidationError as e:
                        validation_errors.append(f"Schema validation failed: {e.message}")
                
                # Check for common response patterns
                if response.status_code == 200:
                    if method == 'GET' and 'results' in response_data:
                        # Paginated response
                        if not isinstance(response_data['results'], list):
                            validation_errors.append("Paginated response 'results' should be a list")
                    elif method in ['POST', 'PUT', 'PATCH']:
                        # Creation/update response should have ID
                        if isinstance(response_data, dict) and 'id' not in response_data:
                            validation_errors.append("Creation/update response should include 'id' field")
                
                elif response.status_code >= 400:
                    # Error responses should have error information
                    if not any(key in response_data for key in ['error', 'detail', 'message', 'non_field_errors']):
                        validation_errors.append("Error response should include error information")
        
        except Exception as e:
            validation_errors.append(f"Response validation error: {str(e)}")
        
        return validation_errors
    
    def _get_schema_key(self, endpoint: APIEndpoint, method: str, status_code: int) -> Optional[str]:
        """Determine which schema to use for validation."""
        if status_code >= 400:
            return 'error_response'
        
        # Map endpoints to schemas based on patterns
        url_lower = endpoint.url_pattern.lower()
        
        if 'auth' in url_lower and 'login' in url_lower:
            return 'jwt_token'
        elif 'user' in url_lower or 'profile' in url_lower:
            return 'user_profile'
        elif 'product' in url_lower and method == 'GET':
            return 'product_list'
        
        return None
    
    def _is_response_successful(self, response, endpoint: APIEndpoint, authenticated: bool) -> bool:
        """Determine if response indicates success based on context."""
        status_code = response.status_code
        
        # Authentication required but not provided
        if endpoint.authentication_required and not authenticated:
            return status_code in [401, 403]  # Expected authentication errors
        
        # Successful responses
        if authenticated or not endpoint.authentication_required:
            return 200 <= status_code < 400
        
        return False
    
    def _safe_json_parse(self, response) -> Optional[Dict]:
        """Safely parse JSON response."""
        try:
            if hasattr(response, 'json'):
                return response.json()
            elif hasattr(response, 'content'):
                return json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            pass
        return None
    
    def _generate_test_summary(self, results: List[TestResult], endpoints: List[APIEndpoint]) -> Dict[str, Any]:
        """Generate detailed test summary statistics."""
        # Group results by category
        endpoint_results = [r for r in results if r.test_name.startswith('endpoint_test')]
        auth_results = [r for r in results if r.test_name.startswith('auth_test')]
        format_results = [r for r in results if r.test_name.startswith('format_test')]
        cors_results = [r for r in results if r.test_name.startswith('cors_test')]
        performance_results = [r for r in results if r.test_name.startswith('performance_test')]
        
        # Calculate response time statistics
        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Group by status codes
        status_codes = {}
        for result in results:
            code = result.status_code
            if code not in status_codes:
                status_codes[code] = 0
            status_codes[code] += 1
        
        # Identify problematic endpoints
        failed_endpoints = {}
        for result in results:
            if not result.success:
                endpoint = result.endpoint
                if endpoint not in failed_endpoints:
                    failed_endpoints[endpoint] = []
                failed_endpoints[endpoint].append({
                    'method': result.method,
                    'error': result.error_message,
                    'validation_errors': result.validation_errors
                })
        
        return {
            'categories': {
                'endpoint_tests': {
                    'total': len(endpoint_results),
                    'passed': len([r for r in endpoint_results if r.success]),
                    'failed': len([r for r in endpoint_results if not r.success])
                },
                'authentication_tests': {
                    'total': len(auth_results),
                    'passed': len([r for r in auth_results if r.success]),
                    'failed': len([r for r in auth_results if not r.success])
                },
                'format_tests': {
                    'total': len(format_results),
                    'passed': len([r for r in format_results if r.success]),
                    'failed': len([r for r in format_results if not r.success])
                },
                'cors_tests': {
                    'total': len(cors_results),
                    'passed': len([r for r in cors_results if r.success]),
                    'failed': len([r for r in cors_results if not r.success])
                },
                'performance_tests': {
                    'total': len(performance_results),
                    'passed': len([r for r in performance_results if r.success]),
                    'failed': len([r for r in performance_results if not r.success])
                }
            },
            'performance_metrics': {
                'average_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'total_endpoints_tested': len(endpoints)
            },
            'status_code_distribution': status_codes,
            'failed_endpoints': failed_endpoints,
            'validation_errors': [
                r.validation_errors for r in results 
                if r.validation_errors and len(r.validation_errors) > 0
            ]
        }
    
    def test_single_endpoint(self, method: str, endpoint: str, payload: Optional[Dict] = None, 
                           headers: Optional[Dict] = None, expected_status: Optional[int] = None) -> Dict[str, Any]:
        """
        Test a single API endpoint with custom parameters.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint URL
            payload: Request payload for POST/PUT/PATCH requests
            headers: Custom headers to include
            expected_status: Expected HTTP status code
            
        Returns:
            Dictionary containing test results
        """
        start_time = time.time()
        
        try:
            # Prepare headers
            test_headers = {'Content-Type': 'application/json'}
            if headers:
                test_headers.update(headers)
            
            # Make the request
            if method.upper() == 'GET':
                response = self.client.get(endpoint, **test_headers)
            elif method.upper() == 'POST':
                response = self.client.post(endpoint, data=json.dumps(payload) if payload else None, 
                                          content_type='application/json', **test_headers)
            elif method.upper() == 'PUT':
                response = self.client.put(endpoint, data=json.dumps(payload) if payload else None,
                                         content_type='application/json', **test_headers)
            elif method.upper() == 'PATCH':
                response = self.client.patch(endpoint, data=json.dumps(payload) if payload else None,
                                           content_type='application/json', **test_headers)
            elif method.upper() == 'DELETE':
                response = self.client.delete(endpoint, **test_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Parse response data
            response_data = None
            try:
                if response.content:
                    response_data = json.loads(response.content.decode('utf-8'))
            except json.JSONDecodeError:
                response_data = {'raw_content': response.content.decode('utf-8')}
            
            # Check expected status
            status_match = True
            if expected_status and response.status_code != expected_status:
                status_match = False
            
            success = response.status_code < 400 and status_match
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'response_data': response_data,
                'headers': dict(response.headers),
                'error_message': None if success else f"Request failed with status {response.status_code}",
                'status_match': status_match,
                'expected_status': expected_status
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'status_code': None,
                'response_time_ms': response_time,
                'response_data': None,
                'headers': {},
                'error_message': str(e),
                'status_match': False,
                'expected_status': expected_status
            }
    
    def test_workflow_sequence(self, workflow_type: str, test_data: Dict[str, Any], 
                             user: Optional[Any] = None) -> Dict[str, Any]:
        """
        Test a complete workflow sequence.
        
        Args:
            workflow_type: Type of workflow to test (login, product_fetch, cart_update, checkout)
            test_data: Test data for the workflow
            user: User object for authenticated requests
            
        Returns:
            Dictionary containing workflow test results
        """
        start_time = time.time()
        workflow_results = []
        
        try:
            # Set up authentication if user provided
            if user:
                refresh = RefreshToken.for_user(user)
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
            
            # Define workflow sequences
            if workflow_type == 'login':
                workflow_results = self._test_login_workflow(test_data)
            elif workflow_type == 'product_fetch':
                workflow_results = self._test_product_fetch_workflow(test_data)
            elif workflow_type == 'cart_update':
                workflow_results = self._test_cart_update_workflow(test_data)
            elif workflow_type == 'checkout':
                workflow_results = self._test_checkout_workflow(test_data)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")
            
            total_time = (time.time() - start_time) * 1000
            success = all(result.get('success', False) for result in workflow_results)
            
            return {
                'success': success,
                'workflow_type': workflow_type,
                'total_time_ms': total_time,
                'steps': workflow_results,
                'step_count': len(workflow_results),
                'failed_steps': [r for r in workflow_results if not r.get('success', False)],
                'error_message': None if success else "One or more workflow steps failed"
            }
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'workflow_type': workflow_type,
                'total_time_ms': total_time,
                'steps': workflow_results,
                'step_count': len(workflow_results),
                'failed_steps': workflow_results,
                'error_message': str(e)
            }
    
    def _test_login_workflow(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test login workflow sequence"""
        results = []
        
        # Step 1: Login request
        login_result = self.test_single_endpoint(
            method='POST',
            endpoint='/api/v1/auth/login/',
            payload={
                'username': test_data.get('username', 'testuser'),
                'password': test_data.get('password', 'testpass123')
            },
            expected_status=200
        )
        login_result['step_name'] = 'login_request'
        results.append(login_result)
        
        # Step 2: Token validation (if login successful)
        if login_result['success'] and login_result.get('response_data'):
            token = login_result['response_data'].get('access')
            if token:
                profile_result = self.test_single_endpoint(
                    method='GET',
                    endpoint='/api/v1/auth/profile/',
                    headers={'Authorization': f'Bearer {token}'},
                    expected_status=200
                )
                profile_result['step_name'] = 'token_validation'
                results.append(profile_result)
        
        return results
    
    def _test_product_fetch_workflow(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test product fetch workflow sequence"""
        results = []
        
        # Step 1: Get product list
        products_result = self.test_single_endpoint(
            method='GET',
            endpoint='/api/v1/products/',
            expected_status=200
        )
        products_result['step_name'] = 'product_list'
        results.append(products_result)
        
        # Step 2: Get specific product (if list successful)
        if products_result['success'] and products_result.get('response_data'):
            products = products_result['response_data'].get('results', [])
            if products:
                product_id = products[0].get('id')
                if product_id:
                    product_detail_result = self.test_single_endpoint(
                        method='GET',
                        endpoint=f'/api/v1/products/{product_id}/',
                        expected_status=200
                    )
                    product_detail_result['step_name'] = 'product_detail'
                    results.append(product_detail_result)
        
        return results
    
    def _test_cart_update_workflow(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test cart update workflow sequence"""
        results = []
        
        # Step 1: Get current cart
        cart_result = self.test_single_endpoint(
            method='GET',
            endpoint='/api/v1/cart/',
            expected_status=200
        )
        cart_result['step_name'] = 'get_cart'
        results.append(cart_result)
        
        # Step 2: Add item to cart
        add_item_result = self.test_single_endpoint(
            method='POST',
            endpoint='/api/v1/cart/items/',
            payload={
                'product_id': test_data.get('product_id', 1),
                'quantity': test_data.get('quantity', 1)
            },
            expected_status=201
        )
        add_item_result['step_name'] = 'add_cart_item'
        results.append(add_item_result)
        
        return results
    
    def _test_checkout_workflow(self, test_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test checkout workflow sequence"""
        results = []
        
        # Step 1: Get cart for checkout
        cart_result = self.test_single_endpoint(
            method='GET',
            endpoint='/api/v1/cart/',
            expected_status=200
        )
        cart_result['step_name'] = 'checkout_cart_review'
        results.append(cart_result)
        
        # Step 2: Create order
        order_result = self.test_single_endpoint(
            method='POST',
            endpoint='/api/v1/orders/',
            payload={
                'shipping_address': test_data.get('shipping_address', {}),
                'payment_method': test_data.get('payment_method', 'credit_card')
            },
            expected_status=201
        )
        order_result['step_name'] = 'create_order'
        results.append(order_result)
        
        return results


# Alias for backward compatibility
APITestingFramework = APITestFramework


class ResponseFormatValidator:
    """Advanced response format validation with schema checking."""
    
    def __init__(self):
        self.schemas = {}
        self.validation_rules = {}
        self.load_default_schemas()
        self.load_validation_rules()
    
    def load_default_schemas(self):
        """Load default response schemas for common API patterns."""
        self.schemas.update({
            'paginated_list': {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'minimum': 0},
                    'next': {'type': ['string', 'null']},
                    'previous': {'type': ['string', 'null']},
                    'results': {'type': 'array'}
                },
                'required': ['count', 'results'],
                'additionalProperties': False
            },
            'detail_response': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'minimum': 1}
                },
                'required': ['id']
            },
            'error_400': {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'},
                    'error': {'type': 'string'},
                    'field_errors': {'type': 'object'}
                },
                'anyOf': [
                    {'required': ['detail']},
                    {'required': ['error']},
                    {'required': ['field_errors']}
                ]
            },
            'error_401': {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'required': ['detail']
            },
            'error_403': {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'required': ['detail']
            },
            'error_404': {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'required': ['detail']
            },
            'error_500': {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'},
                    'error': {'type': 'string'}
                },
                'anyOf': [
                    {'required': ['detail']},
                    {'required': ['error']}
                ]
            },
            'success_message': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'success': {'type': 'boolean'}
                },
                'required': ['message']
            }
        })
    
    def load_validation_rules(self):
        """Load validation rules for different response types."""
        self.validation_rules = {
            'headers': {
                'content_type_json': {
                    'rule': lambda headers: headers.get('Content-Type', '').startswith('application/json'),
                    'message': 'Content-Type should be application/json for JSON responses'
                },
                'cors_headers': {
                    'rule': lambda headers: 'Access-Control-Allow-Origin' in headers,
                    'message': 'CORS headers should be present for cross-origin requests'
                }
            },
            'status_codes': {
                'valid_range': {
                    'rule': lambda code: 100 <= code <= 599,
                    'message': 'Status code should be in valid HTTP range (100-599)'
                },
                'success_codes': {
                    'rule': lambda code: code in [200, 201, 202, 204],
                    'message': 'Success responses should use standard success codes'
                },
                'error_codes': {
                    'rule': lambda code: code in [400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503],
                    'message': 'Error responses should use standard error codes'
                }
            },
            'response_body': {
                'json_parseable': {
                    'rule': lambda body: self._is_valid_json(body),
                    'message': 'Response body should be valid JSON'
                },
                'not_empty_for_success': {
                    'rule': lambda body, status: status == 204 or bool(body.strip()),
                    'message': 'Success responses should not be empty (except 204 No Content)'
                }
            }
        }
    
    def validate_response_format(self, response, endpoint_info: Dict = None) -> List[str]:
        """Comprehensive response format validation."""
        validation_errors = []
        
        try:
            # Extract response components
            status_code = getattr(response, 'status_code', 0)
            headers = dict(getattr(response, 'headers', {}))
            content = getattr(response, 'content', b'')
            
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Validate headers
            header_errors = self._validate_headers(headers, status_code)
            validation_errors.extend(header_errors)
            
            # Validate status code
            status_errors = self._validate_status_code(status_code, endpoint_info)
            validation_errors.extend(status_errors)
            
            # Validate response body
            body_errors = self._validate_response_body(content, status_code, headers)
            validation_errors.extend(body_errors)
            
            # Schema validation
            schema_errors = self._validate_against_schema(content, status_code, endpoint_info)
            validation_errors.extend(schema_errors)
            
            # Custom validation rules
            custom_errors = self._apply_custom_validation_rules(response, endpoint_info)
            validation_errors.extend(custom_errors)
            
        except Exception as e:
            validation_errors.append(f"Response validation error: {str(e)}")
        
        return validation_errors
    
    def _validate_headers(self, headers: Dict, status_code: int) -> List[str]:
        """Validate response headers."""
        errors = []
        
        # Check Content-Type for JSON responses
        content_type = headers.get('Content-Type', '')
        if status_code != 204 and not content_type.startswith('application/json'):
            errors.append("Missing or incorrect Content-Type header for JSON API")
        
        # Check for security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        missing_security_headers = [h for h in security_headers if h not in headers]
        if missing_security_headers:
            errors.append(f"Missing security headers: {', '.join(missing_security_headers)}")
        
        # Check CORS headers for cross-origin requests
        if 'Origin' in headers and 'Access-Control-Allow-Origin' not in headers:
            errors.append("Missing CORS headers for cross-origin request")
        
        return errors
    
    def _validate_status_code(self, status_code: int, endpoint_info: Dict = None) -> List[str]:
        """Validate HTTP status code appropriateness."""
        errors = []
        
        # Check if status code is in valid range
        if not (100 <= status_code <= 599):
            errors.append(f"Invalid HTTP status code: {status_code}")
            return errors
        
        # Validate status code based on endpoint method
        if endpoint_info:
            method = endpoint_info.get('method', '').upper()
            
            if method == 'POST':
                if status_code not in [200, 201, 202, 400, 401, 403, 409, 422, 500]:
                    errors.append(f"Unusual status code {status_code} for POST request")
            elif method == 'GET':
                if status_code not in [200, 304, 400, 401, 403, 404, 500]:
                    errors.append(f"Unusual status code {status_code} for GET request")
            elif method == 'PUT':
                if status_code not in [200, 201, 204, 400, 401, 403, 404, 409, 422, 500]:
                    errors.append(f"Unusual status code {status_code} for PUT request")
            elif method == 'DELETE':
                if status_code not in [200, 204, 400, 401, 403, 404, 500]:
                    errors.append(f"Unusual status code {status_code} for DELETE request")
        
        return errors
    
    def _validate_response_body(self, content: str, status_code: int, headers: Dict) -> List[str]:
        """Validate response body format and content."""
        errors = []
        
        # Check if response should have content
        if status_code == 204:  # No Content
            if content.strip():
                errors.append("204 No Content response should not have body content")
            return errors
        
        # Check if content is valid JSON for JSON responses
        content_type = headers.get('Content-Type', '')
        if content_type.startswith('application/json'):
            if not self._is_valid_json(content):
                errors.append("Response body is not valid JSON")
                return errors
            
            # Parse JSON for further validation
            try:
                data = json.loads(content)
                
                # Check for empty responses that should have content
                if status_code in [200, 201] and not data:
                    errors.append("Success response should not be empty")
                
                # Validate error response structure
                if status_code >= 400:
                    error_fields = ['error', 'detail', 'message', 'non_field_errors']
                    if not any(field in data for field in error_fields):
                        errors.append("Error response should contain error information")
                
            except json.JSONDecodeError:
                errors.append("Response body contains invalid JSON")
        
        return errors
    
    def _validate_against_schema(self, content: str, status_code: int, endpoint_info: Dict = None) -> List[str]:
        """Validate response against predefined schemas."""
        errors = []
        
        if not content.strip():
            return errors
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return errors  # JSON validation already handled elsewhere
        
        # Determine appropriate schema
        schema_key = self._determine_schema_key(data, status_code, endpoint_info)
        
        if schema_key and schema_key in self.schemas:
            try:
                validate(data, self.schemas[schema_key])
            except JSONSchemaValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")
        
        return errors
    
    def _determine_schema_key(self, data: Dict, status_code: int, endpoint_info: Dict = None) -> Optional[str]:
        """Determine which schema to use for validation."""
        # Error response schemas
        if status_code >= 400:
            return f'error_{status_code}' if f'error_{status_code}' in self.schemas else 'error_400'
        
        # Success response schemas
        if isinstance(data, dict):
            # Check for paginated response
            if 'count' in data and 'results' in data:
                return 'paginated_list'
            
            # Check for detail response
            if 'id' in data and len(data) > 1:
                return 'detail_response'
            
            # Check for success message
            if 'message' in data or 'success' in data:
                return 'success_message'
        
        return None
    
    def _apply_custom_validation_rules(self, response, endpoint_info: Dict = None) -> List[str]:
        """Apply custom validation rules based on endpoint patterns."""
        errors = []
        
        try:
            # Extract endpoint information
            if not endpoint_info:
                return errors
            
            endpoint_path = endpoint_info.get('path', '')
            method = endpoint_info.get('method', '').upper()
            status_code = getattr(response, 'status_code', 0)
            
            # Authentication endpoint validation
            if 'auth' in endpoint_path.lower() and 'login' in endpoint_path.lower():
                if status_code == 200:
                    try:
                        data = json.loads(response.content)
                        if 'access' not in data or 'refresh' not in data:
                            errors.append("Login response should include access and refresh tokens")
                    except (json.JSONDecodeError, AttributeError):
                        pass
            
            # List endpoint validation
            if method == 'GET' and status_code == 200:
                try:
                    data = json.loads(response.content)
                    if isinstance(data, dict) and 'results' in data:
                        # Paginated list should have proper pagination info
                        if 'count' not in data:
                            errors.append("Paginated list should include 'count' field")
                        
                        # Check if results is actually a list
                        if not isinstance(data['results'], list):
                            errors.append("'results' field should be a list")
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Creation endpoint validation
            if method == 'POST' and status_code in [200, 201]:
                try:
                    data = json.loads(response.content)
                    if isinstance(data, dict) and 'id' not in data:
                        errors.append("Creation response should include 'id' field")
                except (json.JSONDecodeError, AttributeError):
                    pass
            
        except Exception as e:
            errors.append(f"Custom validation error: {str(e)}")
        
        return errors
    
    def _is_valid_json(self, content: str) -> bool:
        """Check if content is valid JSON."""
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def register_custom_schema(self, name: str, schema: Dict):
        """Register a custom response schema."""
        self.schemas[name] = schema
    
    def register_validation_rule(self, category: str, name: str, rule_func, message: str):
        """Register a custom validation rule."""
        if category not in self.validation_rules:
            self.validation_rules[category] = {}
        
        self.validation_rules[category][name] = {
            'rule': rule_func,
            'message': message
        }


def test_response_formats(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
    """Test response format validation for all endpoints."""
    logger.info("Testing response formats and schema validation")
    results = []
    validator = ResponseFormatValidator()
    
    # Test a subset of endpoints for format validation
    test_endpoints = endpoints[:20]  # Limit for performance
    
    for endpoint in test_endpoints:
        for method in endpoint.http_methods:
            try:
                # Make test request
                test_url = self._prepare_test_url(endpoint.url_pattern)
                headers = {}
                
                # Use authentication if required
                if endpoint.authentication_required:
                    headers['Authorization'] = f'Bearer {self.jwt_token}'
                
                start_time = time.time()
                response = self._make_request(method, test_url, headers)
                response_time = time.time() - start_time
                
                # Validate response format
                endpoint_info = {
                    'path': endpoint.url_pattern,
                    'method': method
                }
                
                format_errors = validator.validate_response_format(response, endpoint_info)
                
                result = TestResult(
                    test_name=f"format_test_{method.lower()}",
                    endpoint=test_url,
                    method=method,
                    status_code=response.status_code,
                    success=len(format_errors) == 0,
                    response_time=response_time,
                    error_message='; '.join(format_errors) if format_errors else None,
                    validation_errors=format_errors
                )
                
                results.append(result)
                
            except Exception as e:
                error_result = TestResult(
                    test_name=f"format_test_{method.lower()}",
                    endpoint=endpoint.url_pattern,
                    method=method,
                    status_code=0,
                    success=False,
                    response_time=0.0,
                    error_message=f"Format test failed: {str(e)}"
                )
                results.append(error_result)
    
    return results

# Add the method to APITestFramework class
APITestFramework.test_response_formats = test_response_formats
class AuthenticationFlowTester:
    """Comprehensive authentication flow testing for JWT and session management."""
    
    def __init__(self, client: APIClient):
        self.client = client
        self.test_credentials = {
            'username': 'auth_test_user',
            'password': 'authtest123',
            'email': 'authtest@example.com'
        }
        self.admin_credentials = {
            'username': 'auth_admin_user',
            'password': 'authadmin123',
            'email': 'authadmin@example.com'
        }
        self.tokens = {}
        self.session_data = {}
    
    def run_authentication_tests(self) -> List[TestResult]:
        """Run comprehensive authentication flow tests."""
        logger.info("Running authentication flow tests")
        results = []
        
        # Setup test users
        self._setup_test_users()
        
        # Test JWT authentication flows
        jwt_results = self._test_jwt_flows()
        results.extend(jwt_results)
        
        # Test session authentication flows
        session_results = self._test_session_flows()
        results.extend(session_results)
        
        # Test permission and authorization
        permission_results = self._test_permission_flows()
        results.extend(permission_results)
        
        # Test token refresh and expiration
        token_results = self._test_token_management()
        results.extend(token_results)
        
        # Test logout and session cleanup
        cleanup_results = self._test_logout_flows()
        results.extend(cleanup_results)
        
        return results
    
    def _setup_test_users(self):
        """Create test users for authentication testing."""
        try:
            # Create regular test user
            self.test_user, created = User.objects.get_or_create(
                username=self.test_credentials['username'],
                defaults={
                    'email': self.test_credentials['email'],
                    'is_active': True
                }
            )
            if created:
                self.test_user.set_password(self.test_credentials['password'])
                self.test_user.save()
            
            # Create admin test user
            self.admin_user, created = User.objects.get_or_create(
                username=self.admin_credentials['username'],
                defaults={
                    'email': self.admin_credentials['email'],
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                self.admin_user.set_password(self.admin_credentials['password'])
                self.admin_user.save()
                
        except Exception as e:
            logger.error(f"Error setting up test users: {str(e)}")
            raise
    
    def _test_jwt_flows(self) -> List[TestResult]:
        """Test JWT authentication flows."""
        results = []
        
        # Test 1: Valid login
        login_result = self._test_jwt_login(
            self.test_credentials['username'],
            self.test_credentials['password']
        )
        results.append(login_result)
        
        # Test 2: Invalid credentials
        invalid_login_result = self._test_jwt_login(
            'invalid_user',
            'invalid_password',
            expect_success=False
        )
        results.append(invalid_login_result)
        
        # Test 3: Missing credentials
        missing_creds_result = self._test_jwt_login('', '', expect_success=False)
        results.append(missing_creds_result)
        
        # Test 4: Inactive user
        inactive_result = self._test_inactive_user_login()
        results.append(inactive_result)
        
        # Test 5: Token usage
        if login_result.success and 'access_token' in self.tokens:
            token_usage_result = self._test_jwt_token_usage()
            results.append(token_usage_result)
        
        return results
    
    def _test_jwt_login(self, username: str, password: str, expect_success: bool = True) -> TestResult:
        """Test JWT login endpoint."""
        start_time = time.time()
        
        try:
            # Attempt login
            response = self.client.post('/api/v1/auth/login/', {
                'username': username,
                'password': password
            }, format='json')
            
            response_time = time.time() - start_time
            
            if expect_success:
                success = response.status_code == 200
                error_message = None
                
                if success:
                    try:
                        data = response.json()
                        if 'access' in data and 'refresh' in data:
                            self.tokens['access_token'] = data['access']
                            self.tokens['refresh_token'] = data['refresh']
                        else:
                            success = False
                            error_message = "Login response missing access or refresh token"
                    except (json.JSONDecodeError, KeyError):
                        success = False
                        error_message = "Invalid login response format"
                else:
                    error_message = f"Login failed with status {response.status_code}"
            else:
                # Expecting failure
                success = response.status_code in [400, 401]
                error_message = None if success else f"Expected authentication failure, got {response.status_code}"
            
            return TestResult(
                test_name="auth_test_jwt_login",
                endpoint="/api/v1/auth/login/",
                method="POST",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                payload_used={'username': username, 'password': '***'},
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_jwt_login",
                endpoint="/api/v1/auth/login/",
                method="POST",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_jwt_token_usage(self) -> TestResult:
        """Test using JWT token for authenticated requests."""
        start_time = time.time()
        
        try:
            # Use token to access protected endpoint
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access_token"]}')
            
            response = self.client.get('/api/v1/auth/user/')
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_message = None
            
            if success:
                try:
                    data = response.json()
                    if 'username' not in data:
                        success = False
                        error_message = "User profile response missing username"
                except json.JSONDecodeError:
                    success = False
                    error_message = "Invalid user profile response format"
            else:
                error_message = f"Token authentication failed with status {response.status_code}"
            
            return TestResult(
                test_name="auth_test_jwt_token_usage",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_jwt_token_usage",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            # Clear credentials
            self.client.credentials()
    
    def _test_inactive_user_login(self) -> TestResult:
        """Test login with inactive user account."""
        start_time = time.time()
        
        try:
            # Create inactive user
            inactive_user, created = User.objects.get_or_create(
                username='inactive_test_user',
                defaults={
                    'email': 'inactive@example.com',
                    'is_active': False
                }
            )
            if created:
                inactive_user.set_password('testpass123')
                inactive_user.save()
            else:
                inactive_user.is_active = False
                inactive_user.save()
            
            # Attempt login with inactive user
            response = self.client.post('/api/v1/auth/login/', {
                'username': 'inactive_test_user',
                'password': 'testpass123'
            }, format='json')
            
            response_time = time.time() - start_time
            
            # Should fail with 401 or 400
            success = response.status_code in [400, 401]
            error_message = None if success else f"Expected authentication failure for inactive user, got {response.status_code}"
            
            return TestResult(
                test_name="auth_test_inactive_user",
                endpoint="/api/v1/auth/login/",
                method="POST",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                payload_used={'username': 'inactive_test_user', 'password': '***'}
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_inactive_user",
                endpoint="/api/v1/auth/login/",
                method="POST",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_session_flows(self) -> List[TestResult]:
        """Test session-based authentication flows."""
        results = []
        
        # Test session login
        session_login_result = self._test_session_login()
        results.append(session_login_result)
        
        # Test session usage
        if session_login_result.success:
            session_usage_result = self._test_session_usage()
            results.append(session_usage_result)
        
        return results
    
    def _test_session_login(self) -> TestResult:
        """Test session-based login."""
        start_time = time.time()
        
        try:
            # Use Django's login
            from django.contrib.auth import authenticate, login
            from django.test import RequestFactory
            
            # Create a request factory for session testing
            factory = RequestFactory()
            request = factory.post('/login/')
            
            # Authenticate user
            user = authenticate(
                username=self.test_credentials['username'],
                password=self.test_credentials['password']
            )
            
            response_time = time.time() - start_time
            
            success = user is not None and user.is_active
            error_message = None if success else "Session authentication failed"
            
            if success:
                self.session_data['user_id'] = user.id
                self.session_data['username'] = user.username
            
            return TestResult(
                test_name="auth_test_session_login",
                endpoint="/login/",
                method="POST",
                status_code=200 if success else 401,
                success=success,
                response_time=response_time,
                error_message=error_message,
                payload_used={'username': self.test_credentials['username'], 'password': '***'}
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_session_login",
                endpoint="/login/",
                method="POST",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_session_usage(self) -> TestResult:
        """Test using session for authenticated requests."""
        start_time = time.time()
        
        try:
            # Force authenticate user for session testing
            self.client.force_authenticate(user=self.test_user)
            
            response = self.client.get('/api/v1/auth/user/')
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_message = None if success else f"Session usage failed with status {response.status_code}"
            
            return TestResult(
                test_name="auth_test_session_usage",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_session_usage",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            # Clear authentication
            self.client.force_authenticate(user=None)
    
    def _test_permission_flows(self) -> List[TestResult]:
        """Test permission and authorization flows."""
        results = []
        
        # Test admin-only endpoint with regular user
        admin_access_result = self._test_admin_endpoint_access()
        results.append(admin_access_result)
        
        # Test user-specific data access
        user_data_result = self._test_user_data_access()
        results.append(user_data_result)
        
        return results
    
    def _test_admin_endpoint_access(self) -> TestResult:
        """Test accessing admin-only endpoints."""
        start_time = time.time()
        
        try:
            # Try to access admin endpoint with regular user token
            if 'access_token' in self.tokens:
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access_token"]}')
            
            response = self.client.get('/api/v1/admin/users/')
            response_time = time.time() - start_time
            
            # Should fail with 403 Forbidden
            success = response.status_code == 403
            error_message = None if success else f"Expected 403 for admin endpoint, got {response.status_code}"
            
            return TestResult(
                test_name="auth_test_admin_access",
                endpoint="/api/v1/admin/users/",
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_admin_access",
                endpoint="/api/v1/admin/users/",
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            self.client.credentials()
    
    def _test_user_data_access(self) -> TestResult:
        """Test accessing user-specific data."""
        start_time = time.time()
        
        try:
            # Access user's own profile
            if 'access_token' in self.tokens:
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access_token"]}')
            
            response = self.client.get('/api/v1/auth/user/')
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_message = None
            
            if success:
                try:
                    data = response.json()
                    if data.get('username') != self.test_credentials['username']:
                        success = False
                        error_message = "User data access returned wrong user information"
                except json.JSONDecodeError:
                    success = False
                    error_message = "Invalid user data response format"
            else:
                error_message = f"User data access failed with status {response.status_code}"
            
            return TestResult(
                test_name="auth_test_user_data_access",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_user_data_access",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            self.client.credentials()
    
    def _test_token_management(self) -> List[TestResult]:
        """Test JWT token refresh and expiration handling."""
        results = []
        
        # Test token refresh
        if 'refresh_token' in self.tokens:
            refresh_result = self._test_token_refresh()
            results.append(refresh_result)
        
        # Test expired token handling
        expired_result = self._test_expired_token()
        results.append(expired_result)
        
        return results
    
    def _test_token_refresh(self) -> TestResult:
        """Test JWT token refresh functionality."""
        start_time = time.time()
        
        try:
            response = self.client.post('/api/v1/auth/token/refresh/', {
                'refresh': self.tokens['refresh_token']
            }, format='json')
            
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_message = None
            
            if success:
                try:
                    data = response.json()
                    if 'access' in data:
                        self.tokens['access_token'] = data['access']
                    else:
                        success = False
                        error_message = "Token refresh response missing access token"
                except json.JSONDecodeError:
                    success = False
                    error_message = "Invalid token refresh response format"
            else:
                error_message = f"Token refresh failed with status {response.status_code}"
            
            return TestResult(
                test_name="auth_test_token_refresh",
                endpoint="/api/v1/auth/token/refresh/",
                method="POST",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_token_refresh",
                endpoint="/api/v1/auth/token/refresh/",
                method="POST",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_expired_token(self) -> TestResult:
        """Test handling of expired tokens."""
        start_time = time.time()
        
        try:
            # Use an obviously invalid/expired token
            expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6IjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwIiwidXNlcl9pZCI6MX0.invalid"
            
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
            
            response = self.client.get('/api/v1/auth/user/')
            response_time = time.time() - start_time
            
            # Should fail with 401 Unauthorized
            success = response.status_code == 401
            error_message = None if success else f"Expected 401 for expired token, got {response.status_code}"
            
            return TestResult(
                test_name="auth_test_expired_token",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_expired_token",
                endpoint="/api/v1/auth/user/",
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            self.client.credentials()
    
    def _test_logout_flows(self) -> List[TestResult]:
        """Test logout and session cleanup."""
        results = []
        
        # Test JWT logout
        logout_result = self._test_jwt_logout()
        results.append(logout_result)
        
        return results
    
    def _test_jwt_logout(self) -> TestResult:
        """Test JWT logout functionality."""
        start_time = time.time()
        
        try:
            if 'refresh_token' in self.tokens:
                response = self.client.post('/api/v1/auth/logout/', {
                    'refresh': self.tokens['refresh_token']
                }, format='json')
            else:
                # Test logout without token
                response = self.client.post('/api/v1/auth/logout/', format='json')
            
            response_time = time.time() - start_time
            
            # Logout should succeed or return appropriate error
            success = response.status_code in [200, 204, 400, 401]
            error_message = None if success else f"Unexpected logout response: {response.status_code}"
            
            return TestResult(
                test_name="auth_test_jwt_logout",
                endpoint="/api/v1/auth/logout/",
                method="POST",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message=error_message,
                response_data=self._safe_json_parse(response)
            )
            
        except Exception as e:
            return TestResult(
                test_name="auth_test_jwt_logout",
                endpoint="/api/v1/auth/logout/",
                method="POST",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _safe_json_parse(self, response) -> Optional[Dict]:
        """Safely parse JSON response."""
        try:
            if hasattr(response, 'json'):
                return response.json()
            elif hasattr(response, 'content'):
                return json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            pass
        return None


def test_authentication_flows(self) -> List[TestResult]:
    """Test comprehensive authentication flows."""
    logger.info("Testing authentication flows")
    
    auth_tester = AuthenticationFlowTester(self.client)
    return auth_tester.run_authentication_tests()

# Add the method to APITestFramework class
APITestFramework.test_authentication_flows = test_authentication_flows

class CORSConfigurationValidator:
    """Comprehensive CORS configuration validation for cross-origin requests."""
    
    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
        self.test_origins = [
            'http://localhost:3000',  # Next.js dev server
            'http://localhost:3001',  # Alternative frontend port
            'https://example.com',    # Production domain
            'https://app.example.com', # Subdomain
            'http://127.0.0.1:3000',  # IP address
            'null'                    # File protocol
        ]
        self.required_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        self.optional_headers = [
            'Access-Control-Allow-Credentials',
            'Access-Control-Max-Age',
            'Access-Control-Expose-Headers'
        ]
    
    def validate_cors_configuration(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Validate CORS configuration for all API endpoints."""
        logger.info("Validating CORS configuration")
        results = []
        
        # Test preflight requests
        preflight_results = self._test_preflight_requests(endpoints)
        results.extend(preflight_results)
        
        # Test actual CORS requests
        cors_results = self._test_cors_requests(endpoints)
        results.extend(cors_results)
        
        # Test CORS with credentials
        credentials_results = self._test_cors_with_credentials(endpoints)
        results.extend(credentials_results)
        
        # Test invalid origins
        invalid_origin_results = self._test_invalid_origins(endpoints)
        results.extend(invalid_origin_results)
        
        return results
    
    def _test_preflight_requests(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test CORS preflight (OPTIONS) requests."""
        results = []
        
        # Test subset of endpoints for performance
        test_endpoints = [ep for ep in endpoints if 'POST' in ep.http_methods or 'PUT' in ep.http_methods][:10]
        
        for endpoint in test_endpoints:
            for origin in self.test_origins[:3]:  # Test with first 3 origins
                result = self._test_single_preflight(endpoint, origin)
                results.append(result)
        
        return results
    
    def _test_single_preflight(self, endpoint: APIEndpoint, origin: str) -> TestResult:
        """Test a single preflight request."""
        start_time = time.time()
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        try:
            # Make OPTIONS request with CORS headers
            headers = {
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            # Use requests library for more control over headers
            import requests
            response = requests.options(
                f"{self.base_url}{test_url}",
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            # Validate preflight response
            validation_errors = self._validate_preflight_response(response, origin)
            
            success = (
                response.status_code in [200, 204] and
                len(validation_errors) == 0
            )
            
            return TestResult(
                test_name="cors_test_preflight",
                endpoint=test_url,
                method="OPTIONS",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message='; '.join(validation_errors) if validation_errors else None,
                validation_errors=validation_errors,
                payload_used={'origin': origin}
            )
            
        except Exception as e:
            return TestResult(
                test_name="cors_test_preflight",
                endpoint=test_url,
                method="OPTIONS",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                payload_used={'origin': origin}
            )
    
    def _validate_preflight_response(self, response, origin: str) -> List[str]:
        """Validate preflight response headers."""
        errors = []
        headers = dict(response.headers)
        
        # Check required CORS headers
        if 'Access-Control-Allow-Origin' not in headers:
            errors.append("Missing Access-Control-Allow-Origin header")
        else:
            allowed_origin = headers['Access-Control-Allow-Origin']
            if allowed_origin != '*' and allowed_origin != origin:
                errors.append(f"Access-Control-Allow-Origin '{allowed_origin}' doesn't match request origin '{origin}'")
        
        if 'Access-Control-Allow-Methods' not in headers:
            errors.append("Missing Access-Control-Allow-Methods header")
        else:
            allowed_methods = headers['Access-Control-Allow-Methods']
            if 'POST' not in allowed_methods and 'PUT' not in allowed_methods:
                errors.append("Access-Control-Allow-Methods should include POST or PUT")
        
        if 'Access-Control-Allow-Headers' not in headers:
            errors.append("Missing Access-Control-Allow-Headers header")
        else:
            allowed_headers = headers['Access-Control-Allow-Headers'].lower()
            required_headers = ['content-type', 'authorization']
            for header in required_headers:
                if header not in allowed_headers:
                    errors.append(f"Access-Control-Allow-Headers should include '{header}'")
        
        # Check Max-Age for preflight caching
        if 'Access-Control-Max-Age' in headers:
            try:
                max_age = int(headers['Access-Control-Max-Age'])
                if max_age < 0:
                    errors.append("Access-Control-Max-Age should be non-negative")
            except ValueError:
                errors.append("Access-Control-Max-Age should be a valid integer")
        
        return errors
    
    def _test_cors_requests(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test actual CORS requests (not preflight)."""
        results = []
        
        # Test subset of endpoints
        test_endpoints = endpoints[:5]
        
        for endpoint in test_endpoints:
            for method in ['GET', 'POST']:
                if method in endpoint.http_methods:
                    for origin in self.test_origins[:2]:  # Test with first 2 origins
                        result = self._test_single_cors_request(endpoint, method, origin)
                        results.append(result)
        
        return results
    
    def _test_single_cors_request(self, endpoint: APIEndpoint, method: str, origin: str) -> TestResult:
        """Test a single CORS request."""
        start_time = time.time()
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        try:
            headers = {'Origin': origin}
            
            # Add authentication if required
            if endpoint.authentication_required:
                # Use a test token (this would need to be set up)
                headers['Authorization'] = 'Bearer test_token'
            
            # Prepare payload for POST requests
            payload = None
            if method == 'POST' and endpoint.request_schema:
                payload = {'test': 'data'}
            
            # Make request
            import requests
            if method == 'GET':
                response = requests.get(f"{self.base_url}{test_url}", headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(
                    f"{self.base_url}{test_url}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
            else:
                response = requests.request(
                    method,
                    f"{self.base_url}{test_url}",
                    headers=headers,
                    timeout=10
                )
            
            response_time = time.time() - start_time
            
            # Validate CORS response
            validation_errors = self._validate_cors_response(response, origin)
            
            # Success if we get a response and CORS headers are correct
            success = len(validation_errors) == 0
            
            return TestResult(
                test_name="cors_test_request",
                endpoint=test_url,
                method=method,
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message='; '.join(validation_errors) if validation_errors else None,
                validation_errors=validation_errors,
                payload_used={'origin': origin, 'method': method}
            )
            
        except Exception as e:
            return TestResult(
                test_name="cors_test_request",
                endpoint=test_url,
                method=method,
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                payload_used={'origin': origin, 'method': method}
            )
    
    def _validate_cors_response(self, response, origin: str) -> List[str]:
        """Validate CORS response headers."""
        errors = []
        headers = dict(response.headers)
        
        # Check Access-Control-Allow-Origin
        if 'Access-Control-Allow-Origin' not in headers:
            errors.append("Missing Access-Control-Allow-Origin header in response")
        else:
            allowed_origin = headers['Access-Control-Allow-Origin']
            if allowed_origin != '*' and allowed_origin != origin:
                errors.append(f"Access-Control-Allow-Origin '{allowed_origin}' doesn't match request origin '{origin}'")
        
        # Check for exposed headers if any
        if 'Access-Control-Expose-Headers' in headers:
            exposed_headers = headers['Access-Control-Expose-Headers']
            # Validate that exposed headers are reasonable
            if 'authorization' in exposed_headers.lower():
                errors.append("Authorization header should not be exposed via CORS")
        
        return errors
    
    def _test_cors_with_credentials(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test CORS requests with credentials."""
        results = []
        
        # Test authenticated endpoints
        auth_endpoints = [ep for ep in endpoints if ep.authentication_required][:3]
        
        for endpoint in auth_endpoints:
            result = self._test_credentials_cors(endpoint)
            results.append(result)
        
        return results
    
    def _test_credentials_cors(self, endpoint: APIEndpoint) -> TestResult:
        """Test CORS request with credentials."""
        start_time = time.time()
        test_url = self._prepare_test_url(endpoint.url_pattern)
        origin = 'http://localhost:3000'
        
        try:
            headers = {
                'Origin': origin,
                'Authorization': 'Bearer test_token'
            }
            
            # Make request with credentials
            import requests
            response = requests.get(
                f"{self.base_url}{test_url}",
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            # Validate credentials CORS response
            validation_errors = self._validate_credentials_cors_response(response, origin)
            
            success = len(validation_errors) == 0
            
            return TestResult(
                test_name="cors_test_credentials",
                endpoint=test_url,
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message='; '.join(validation_errors) if validation_errors else None,
                validation_errors=validation_errors,
                payload_used={'origin': origin, 'credentials': True}
            )
            
        except Exception as e:
            return TestResult(
                test_name="cors_test_credentials",
                endpoint=test_url,
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                payload_used={'origin': origin, 'credentials': True}
            )
    
    def _validate_credentials_cors_response(self, response, origin: str) -> List[str]:
        """Validate CORS response for requests with credentials."""
        errors = []
        headers = dict(response.headers)
        
        # When credentials are involved, origin cannot be *
        if 'Access-Control-Allow-Origin' in headers:
            allowed_origin = headers['Access-Control-Allow-Origin']
            if allowed_origin == '*':
                errors.append("Access-Control-Allow-Origin cannot be '*' when credentials are used")
            elif allowed_origin != origin:
                errors.append(f"Access-Control-Allow-Origin '{allowed_origin}' doesn't match request origin '{origin}'")
        else:
            errors.append("Missing Access-Control-Allow-Origin header")
        
        # Check for Allow-Credentials header
        if 'Access-Control-Allow-Credentials' not in headers:
            errors.append("Missing Access-Control-Allow-Credentials header for credentialed request")
        else:
            allow_credentials = headers['Access-Control-Allow-Credentials'].lower()
            if allow_credentials != 'true':
                errors.append("Access-Control-Allow-Credentials should be 'true' for credentialed requests")
        
        return errors
    
    def _test_invalid_origins(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test CORS behavior with invalid/disallowed origins."""
        results = []
        
        invalid_origins = [
            'http://malicious.com',
            'https://evil.example.com',
            'http://localhost:9999'
        ]
        
        # Test one endpoint with invalid origins
        if endpoints:
            endpoint = endpoints[0]
            for origin in invalid_origins:
                result = self._test_invalid_origin(endpoint, origin)
                results.append(result)
        
        return results
    
    def _test_invalid_origin(self, endpoint: APIEndpoint, origin: str) -> TestResult:
        """Test CORS request with invalid origin."""
        start_time = time.time()
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        try:
            headers = {'Origin': origin}
            
            # Make request
            import requests
            response = requests.get(
                f"{self.base_url}{test_url}",
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            # Validate that invalid origin is handled properly
            validation_errors = self._validate_invalid_origin_response(response, origin)
            
            success = len(validation_errors) == 0
            
            return TestResult(
                test_name="cors_test_invalid_origin",
                endpoint=test_url,
                method="GET",
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error_message='; '.join(validation_errors) if validation_errors else None,
                validation_errors=validation_errors,
                payload_used={'origin': origin}
            )
            
        except Exception as e:
            return TestResult(
                test_name="cors_test_invalid_origin",
                endpoint=test_url,
                method="GET",
                status_code=0,
                success=False,
                response_time=time.time() - start_time,
                error_message=str(e),
                payload_used={'origin': origin}
            )
    
    def _validate_invalid_origin_response(self, response, origin: str) -> List[str]:
        """Validate response for invalid origin requests."""
        errors = []
        headers = dict(response.headers)
        
        # For invalid origins, either:
        # 1. No CORS headers should be present, OR
        # 2. Access-Control-Allow-Origin should not match the invalid origin
        
        if 'Access-Control-Allow-Origin' in headers:
            allowed_origin = headers['Access-Control-Allow-Origin']
            if allowed_origin == origin:
                errors.append(f"Invalid origin '{origin}' should not be allowed")
            # If it's '*', that might be acceptable depending on configuration
        
        return errors
    
    def _prepare_test_url(self, url_pattern: str) -> str:
        """Convert Django URL pattern to testable URL."""
        test_url = url_pattern
        
        # Replace path parameters with test values
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


def test_cors_configuration(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
    """Test CORS configuration for cross-origin requests."""
    logger.info("Testing CORS configuration")
    
    cors_validator = CORSConfigurationValidator(self.base_url)
    return cors_validator.validate_cors_configuration(endpoints)

# Add the method to APITestFramework class
APITestFramework.test_cors_configuration = test_cors_configuration
class PerformanceTestSuite:
    """Performance testing suite for API endpoints."""
    
    def __init__(self, client: APIClient):
        self.client = client
        self.performance_thresholds = {
            'response_time_warning': 200,  # ms
            'response_time_critical': 500,  # ms
            'memory_usage_warning': 100,   # MB
            'memory_usage_critical': 200,  # MB
            'concurrent_users': 10,
            'load_test_duration': 30,      # seconds
        }
    
    def test_performance_thresholds(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test API endpoints against performance thresholds."""
        logger.info("Testing performance thresholds")
        results = []
        
        # Test response time thresholds
        response_time_results = self._test_response_times(endpoints)
        results.extend(response_time_results)
        
        # Test concurrent request handling
        concurrency_results = self._test_concurrent_requests(endpoints)
        results.extend(concurrency_results)
        
        # Test load handling
        load_results = self._test_load_performance(endpoints)
        results.extend(load_results)
        
        return results
    
    def _test_response_times(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test response time performance for endpoints."""
        results = []
        
        # Test subset of endpoints for performance
        test_endpoints = endpoints[:10]
        
        for endpoint in test_endpoints:
            for method in endpoint.http_methods:
                if method in ['GET', 'POST']:  # Focus on common methods
                    result = self._test_single_endpoint_performance(endpoint, method)
                    results.append(result)
        
        return results
    
    def _test_single_endpoint_performance(self, endpoint: APIEndpoint, method: str) -> TestResult:
        """Test performance of a single endpoint."""
        test_url = self._prepare_test_url(endpoint.url_pattern)
        
        # Warm up request
        try:
            self._make_single_request(endpoint, method, test_url)
        except:
            pass
        
        # Performance test - multiple requests
        response_times = []
        errors = []
        
        for i in range(5):  # 5 test requests
            try:
                start_time = time.time()
                response = self._make_single_request(endpoint, method, test_url)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                response_times.append(response_time)
                
                if response.status_code >= 500:
                    errors.append(f"Request {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                errors.append(f"Request {i+1}: {str(e)}")
        
        # Calculate statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        # Determine success based on thresholds
        success = (
            avg_response_time < self.performance_thresholds['response_time_critical'] and
            len(errors) == 0
        )
        
        # Generate warning if above warning threshold
        warning_messages = []
        if avg_response_time > self.performance_thresholds['response_time_warning']:
            warning_messages.append(f"Average response time {avg_response_time:.1f}ms exceeds warning threshold")
        
        error_message = None
        if errors:
            error_message = f"Errors: {'; '.join(errors)}"
        elif warning_messages:
            error_message = '; '.join(warning_messages)
        
        return TestResult(
            test_name="performance_test_response_time",
            endpoint=test_url,
            method=method,
            status_code=200 if success else 0,
            success=success,
            response_time=avg_response_time / 1000,  # Convert back to seconds
            error_message=error_message,
            payload_used={
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'min_response_time_ms': min_response_time,
                'total_requests': len(response_times),
                'error_count': len(errors)
            }
        )
    
    def _test_concurrent_requests(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test concurrent request handling."""
        results = []
        
        # Test one endpoint for concurrency
        if endpoints:
            endpoint = endpoints[0]  # Use first endpoint
            if 'GET' in endpoint.http_methods:
                result = self._test_endpoint_concurrency(endpoint, 'GET')
                results.append(result)
        
        return results
    
    def _test_endpoint_concurrency(self, endpoint: APIEndpoint, method: str) -> TestResult:
        """Test concurrent requests to a single endpoint."""
        test_url = self._prepare_test_url(endpoint.url_pattern)
        concurrent_users = self.performance_thresholds['concurrent_users']
        
        start_time = time.time()
        
        def make_request():
            try:
                request_start = time.time()
                response = self._make_single_request(endpoint, method, test_url)
                request_time = time.time() - request_start
                return {
                    'success': response.status_code < 400,
                    'status_code': response.status_code,
                    'response_time': request_time,
                    'error': None
                }
            except Exception as e:
                return {
                    'success': False,
                    'status_code': 0,
                    'response_time': 0,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_users)]
            request_results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = len([r for r in request_results if r['success']])
        failed_requests = len(request_results) - successful_requests
        response_times = [r['response_time'] for r in request_results if r['response_time'] > 0]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Determine success
        success = (
            failed_requests == 0 and
            avg_response_time < (self.performance_thresholds['response_time_critical'] / 1000)
        )
        
        error_message = None
        if failed_requests > 0:
            error_message = f"{failed_requests}/{concurrent_users} requests failed"
        elif avg_response_time > (self.performance_thresholds['response_time_warning'] / 1000):
            error_message = f"Average response time {avg_response_time*1000:.1f}ms under load exceeds warning threshold"
        
        return TestResult(
            test_name="performance_test_concurrency",
            endpoint=test_url,
            method=method,
            status_code=200 if success else 0,
            success=success,
            response_time=total_time,
            error_message=error_message,
            payload_used={
                'concurrent_users': concurrent_users,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'avg_response_time_ms': avg_response_time * 1000,
                'total_time': total_time
            }
        )
    
    def _test_load_performance(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
        """Test sustained load performance."""
        results = []
        
        # Test one endpoint for load
        if endpoints:
            endpoint = endpoints[0]
            if 'GET' in endpoint.http_methods:
                result = self._test_endpoint_load(endpoint, 'GET')
                results.append(result)
        
        return results
    
    def _test_endpoint_load(self, endpoint: APIEndpoint, method: str) -> TestResult:
        """Test sustained load on a single endpoint."""
        test_url = self._prepare_test_url(endpoint.url_pattern)
        duration = self.performance_thresholds['load_test_duration']
        
        start_time = time.time()
        end_time = start_time + duration
        
        request_count = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        # Make requests for the specified duration
        while time.time() < end_time:
            try:
                request_start = time.time()
                response = self._make_single_request(endpoint, method, test_url)
                request_time = time.time() - request_start
                
                request_count += 1
                response_times.append(request_time)
                
                if response.status_code < 400:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception:
                request_count += 1
                failed_requests += 1
            
            # Small delay to prevent overwhelming
            time.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        requests_per_second = request_count / total_time if total_time > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        success_rate = (successful_requests / request_count * 100) if request_count > 0 else 0
        
        # Determine success
        success = (
            success_rate >= 95 and  # 95% success rate
            avg_response_time < (self.performance_thresholds['response_time_critical'] / 1000)
        )
        
        error_message = None
        if success_rate < 95:
            error_message = f"Success rate {success_rate:.1f}% below 95% threshold"
        elif avg_response_time > (self.performance_thresholds['response_time_warning'] / 1000):
            error_message = f"Average response time {avg_response_time*1000:.1f}ms under sustained load exceeds warning threshold"
        
        return TestResult(
            test_name="performance_test_load",
            endpoint=test_url,
            method=method,
            status_code=200 if success else 0,
            success=success,
            response_time=avg_response_time,
            error_message=error_message,
            payload_used={
                'duration_seconds': duration,
                'total_requests': request_count,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'requests_per_second': requests_per_second,
                'success_rate_percent': success_rate,
                'avg_response_time_ms': avg_response_time * 1000
            }
        )
    
    def _make_single_request(self, endpoint: APIEndpoint, method: str, test_url: str):
        """Make a single request to an endpoint."""
        headers = {}
        
        # Add authentication if required
        if endpoint.authentication_required:
            # This would need to be set up with a valid token
            headers['Authorization'] = 'Bearer test_token'
        
        # Prepare payload for write operations
        payload = None
        if method in ['POST', 'PUT', 'PATCH'] and endpoint.request_schema:
            payload = {'test': 'data'}
        
        # Make request using Django test client
        for key, value in headers.items():
            if key == 'Authorization':
                self.client.credentials(HTTP_AUTHORIZATION=value)
        
        if method == 'GET':
            return self.client.get(test_url)
        elif method == 'POST':
            return self.client.post(test_url, data=payload, format='json')
        elif method == 'PUT':
            return self.client.put(test_url, data=payload, format='json')
        elif method == 'PATCH':
            return self.client.patch(test_url, data=payload, format='json')
        elif method == 'DELETE':
            return self.client.delete(test_url)
        else:
            return self.client.generic(method, test_url, data=payload, format='json')
    
    def _prepare_test_url(self, url_pattern: str) -> str:
        """Convert Django URL pattern to testable URL."""
        test_url = url_pattern
        
        # Replace path parameters with test values
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


def test_performance_thresholds(self, endpoints: List[APIEndpoint]) -> List[TestResult]:
    """Test API endpoints against performance thresholds."""
    logger.info("Testing performance thresholds")
    
    performance_tester = PerformanceTestSuite(self.client)
    return performance_tester.test_performance_thresholds(endpoints)

# Add the method to APITestFramework class
APITestFramework.test_performance_thresholds = test_performance_thresholds


class ComprehensiveTestRunner:
    """Main test runner for the comprehensive testing suite."""
    
    def __init__(self, base_url: str = None):
        self.framework = APITestFramework(base_url)
        self.test_results = []
        self.test_reports = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all automated tests and return comprehensive results."""
        logger.info("Starting comprehensive automated testing suite")
        
        try:
            # Run the comprehensive test suite
            test_suite = self.framework.run_comprehensive_tests()
            
            # Generate detailed reports
            reports = self._generate_comprehensive_reports(test_suite)
            
            # Save results
            self.test_results = test_suite.results
            self.test_reports = reports
            
            return {
                'test_suite': asdict(test_suite),
                'reports': reports,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_comprehensive_reports(self, test_suite: TestSuite) -> Dict[str, Any]:
        """Generate comprehensive test reports."""
        reports = {}
        
        # Executive summary
        reports['executive_summary'] = self._generate_executive_summary(test_suite)
        
        # Detailed category reports
        reports['category_reports'] = self._generate_category_reports(test_suite.results)
        
        # Performance analysis
        reports['performance_analysis'] = self._generate_performance_analysis(test_suite.results)
        
        # Security analysis
        reports['security_analysis'] = self._generate_security_analysis(test_suite.results)
        
        # Recommendations
        reports['recommendations'] = self._generate_recommendations(test_suite.results)
        
        return reports
    
    def _generate_executive_summary(self, test_suite: TestSuite) -> Dict[str, Any]:
        """Generate executive summary of test results."""
        return {
            'overall_health': 'healthy' if test_suite.passed_tests / test_suite.total_tests > 0.9 else 'degraded',
            'total_tests': test_suite.total_tests,
            'passed_tests': test_suite.passed_tests,
            'failed_tests': test_suite.failed_tests,
            'success_rate': (test_suite.passed_tests / test_suite.total_tests * 100) if test_suite.total_tests > 0 else 0,
            'execution_time': test_suite.execution_time,
            'critical_issues': len([r for r in test_suite.results if not r.success and 'critical' in r.error_message.lower() if r.error_message]),
            'warning_issues': len([r for r in test_suite.results if not r.success and 'warning' in r.error_message.lower() if r.error_message])
        }
    
    def _generate_category_reports(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate reports by test category."""
        categories = {}
        
        for result in results:
            category = result.test_name.split('_')[0]  # Extract category from test name
            
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_response_time': 0,
                    'issues': []
                }
            
            categories[category]['total'] += 1
            if result.success:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
                if result.error_message:
                    categories[category]['issues'].append({
                        'endpoint': result.endpoint,
                        'method': result.method,
                        'error': result.error_message
                    })
        
        # Calculate average response times
        for category in categories:
            category_results = [r for r in results if r.test_name.startswith(category)]
            response_times = [r.response_time for r in category_results if r.response_time > 0]
            categories[category]['avg_response_time'] = sum(response_times) / len(response_times) if response_times else 0
        
        return categories
    
    def _generate_performance_analysis(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate performance analysis report."""
        performance_results = [r for r in results if r.test_name.startswith('performance')]
        
        if not performance_results:
            return {'message': 'No performance tests executed'}
        
        response_times = [r.response_time for r in performance_results if r.response_time > 0]
        
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'slow_endpoints': [
                {
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'response_time': r.response_time
                }
                for r in performance_results
                if r.response_time > 0.5  # Slower than 500ms
            ],
            'performance_issues': [r.error_message for r in performance_results if not r.success and r.error_message]
        }
    
    def _generate_security_analysis(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate security analysis report."""
        auth_results = [r for r in results if r.test_name.startswith('auth')]
        cors_results = [r for r in results if r.test_name.startswith('cors')]
        
        security_issues = []
        
        # Check authentication issues
        failed_auth = [r for r in auth_results if not r.success]
        for result in failed_auth:
            security_issues.append({
                'type': 'authentication',
                'severity': 'high',
                'description': result.error_message,
                'endpoint': result.endpoint
            })
        
        # Check CORS issues
        failed_cors = [r for r in cors_results if not r.success]
        for result in failed_cors:
            security_issues.append({
                'type': 'cors',
                'severity': 'medium',
                'description': result.error_message,
                'endpoint': result.endpoint
            })
        
        return {
            'total_security_tests': len(auth_results) + len(cors_results),
            'passed_security_tests': len([r for r in auth_results + cors_results if r.success]),
            'security_issues': security_issues,
            'security_score': ((len(auth_results) + len(cors_results) - len(security_issues)) / 
                             max(len(auth_results) + len(cors_results), 1) * 100)
        }
    
    def _generate_recommendations(self, results: List[TestResult]) -> List[Dict[str, Any]]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Performance recommendations
        slow_tests = [r for r in results if r.response_time > 0.5]
        if slow_tests:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'Optimize slow API endpoints',
                'description': f'{len(slow_tests)} endpoints have response times > 500ms',
                'action_items': [
                    'Review database queries for N+1 problems',
                    'Implement caching for frequently accessed data',
                    'Consider pagination for large result sets',
                    'Optimize serializer performance'
                ]
            })
        
        # Authentication recommendations
        failed_auth = [r for r in results if r.test_name.startswith('auth') and not r.success]
        if failed_auth:
            recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'title': 'Fix authentication issues',
                'description': f'{len(failed_auth)} authentication tests failed',
                'action_items': [
                    'Review JWT token configuration',
                    'Verify authentication middleware setup',
                    'Check user permission configurations',
                    'Test token refresh mechanisms'
                ]
            })
        
        # CORS recommendations
        failed_cors = [r for r in results if r.test_name.startswith('cors') and not r.success]
        if failed_cors:
            recommendations.append({
                'category': 'security',
                'priority': 'medium',
                'title': 'Configure CORS properly',
                'description': f'{len(failed_cors)} CORS tests failed',
                'action_items': [
                    'Review CORS_ALLOWED_ORIGINS settings',
                    'Configure proper CORS headers',
                    'Test cross-origin requests from frontend',
                    'Verify credentials handling in CORS'
                ]
            })
        
        # Format validation recommendations
        format_failures = [r for r in results if r.test_name.startswith('format') and not r.success]
        if format_failures:
            recommendations.append({
                'category': 'api_design',
                'priority': 'medium',
                'title': 'Improve API response formats',
                'description': f'{len(format_failures)} format validation tests failed',
                'action_items': [
                    'Standardize error response formats',
                    'Ensure consistent JSON schema compliance',
                    'Add proper HTTP status codes',
                    'Include required response headers'
                ]
            })
        
        return recommendations


# Utility functions for easy access
def run_comprehensive_api_tests(base_url: str = None) -> Dict[str, Any]:
    """Run comprehensive API testing suite."""
    runner = ComprehensiveTestRunner(base_url)
    return runner.run_all_tests()


def run_quick_api_health_check() -> Dict[str, Any]:
    """Run a quick API health check."""
    framework = APITestFramework()
    framework.setup_test_environment()
    
    # Discover critical endpoints
    discovery = APIDiscoveryService()
    endpoints = discovery.discover_all_endpoints()
    
    # Test subset of critical endpoints
    critical_endpoints = [ep for ep in endpoints if any(
        keyword in ep.url_pattern.lower() 
        for keyword in ['auth', 'user', 'product', 'order']
    )][:5]
    
    results = []
    for endpoint in critical_endpoints:
        if 'GET' in endpoint.http_methods:
            result = framework._test_endpoint_scenario(endpoint, 'GET', False)
            results.append(result)
    
    passed = len([r for r in results if r.success])
    total = len(results)
    
    return {
        'status': 'healthy' if passed == total else 'degraded',
        'passed_tests': passed,
        'total_tests': total,
        'success_rate': (passed / total * 100) if total > 0 else 0,
        'results': [asdict(r) for r in results],
        'timestamp': datetime.now().isoformat()
    }