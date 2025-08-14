"""
API Test Client for Django REST API Testing

Provides a comprehensive client for testing Django REST API endpoints
with authentication handling, request/response validation, and performance monitoring.
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import Environment
from core.models import TestExecution, Defect, Severity


@dataclass
class APIResponse:
    """API response wrapper with validation and metrics"""
    status_code: int
    headers: Dict[str, str]
    content: Union[Dict[str, Any], List[Any], str]
    response_time: float
    request_url: str
    request_method: str
    request_headers: Dict[str, str]
    request_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status codes)"""
        return 200 <= self.status_code < 300
    
    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error (4xx status codes)"""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error (5xx status codes)"""
        return 500 <= self.status_code < 600
    
    def validate_json_schema(self, schema: Dict[str, Any]) -> List[str]:
        """Validate response content against JSON schema"""
        try:
            from jsonschema import validate, ValidationError
            validate(instance=self.content, schema=schema)
            return []
        except ValidationError as e:
            return [str(e)]
        except Exception as e:
            return [f"Schema validation error: {str(e)}"]
    
    def has_field(self, field_path: str) -> bool:
        """Check if response has specified field (supports dot notation)"""
        try:
            current = self.content
            for field in field_path.split('.'):
                if isinstance(current, dict) and field in current:
                    current = current[field]
                elif isinstance(current, list) and field.isdigit():
                    current = current[int(field)]
                else:
                    return False
            return True
        except (KeyError, IndexError, TypeError):
            return False
    
    def get_field_value(self, field_path: str) -> Any:
        """Get field value from response (supports dot notation)"""
        try:
            current = self.content
            for field in field_path.split('.'):
                if isinstance(current, dict) and field in current:
                    current = current[field]
                elif isinstance(current, list) and field.isdigit():
                    current = current[int(field)]
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError):
            return None


class APITestClient:
    """
    Comprehensive API test client for Django REST API testing
    
    Features:
    - Authentication handling (JWT, session, API key)
    - Request/response validation
    - Performance monitoring
    - Rate limiting testing
    - Error handling and retry logic
    """
    
    def __init__(self, base_url: str, environment: Environment = Environment.DEVELOPMENT):
        self.base_url = base_url.rstrip('/')
        self.environment = environment
        self.session = requests.Session()
        self.auth_token = None
        self.auth_type = None
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'QA-Testing-Framework/1.0'
        }
        self.session.headers.update(self.default_headers)
        
        # Performance tracking
        self.request_history: List[APIResponse] = []
        self.performance_thresholds = {
            'response_time_warning': 2.0,  # seconds
            'response_time_critical': 5.0,  # seconds
        }
        
        # Rate limiting tracking
        self.rate_limit_info = {}
        
        # Setup logging
        self.logger = logging.getLogger(f'api_client_{environment.value if hasattr(environment, "value") else str(environment)}')
        
    def authenticate_jwt(self, username: str, password: str, login_endpoint: str = '/api/v1/auth/login/') -> bool:
        """
        Authenticate using JWT tokens
        
        Args:
            username: User credentials
            password: User credentials
            login_endpoint: Login API endpoint
            
        Returns:
            bool: True if authentication successful
        """
        try:
            login_data = {
                'username': username,
                'password': password
            }
            
            response = self.post(login_endpoint, data=login_data, authenticate=False)
            
            if response.is_success and isinstance(response.content, dict):
                # Handle different JWT response formats
                token = None
                if 'access' in response.content:
                    token = response.content['access']
                elif 'token' in response.content:
                    token = response.content['token']
                elif 'access_token' in response.content:
                    token = response.content['access_token']
                
                if token:
                    self.auth_token = token
                    self.auth_type = 'jwt'
                    self.session.headers['Authorization'] = f'Bearer {token}'
                    self.logger.info(f"JWT authentication successful for user: {username}")
                    return True
            
            self.logger.error(f"JWT authentication failed for user: {username}")
            return False
            
        except Exception as e:
            self.logger.error(f"JWT authentication error: {str(e)}")
            return False
    
    def authenticate_session(self, username: str, password: str, login_endpoint: str = '/api/v1/auth/login/') -> bool:
        """
        Authenticate using session-based authentication
        
        Args:
            username: User credentials
            password: User credentials
            login_endpoint: Login API endpoint
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Get CSRF token first
            csrf_response = self.get('/api/v1/auth/csrf/', authenticate=False)
            if csrf_response.is_success and isinstance(csrf_response.content, dict):
                csrf_token = csrf_response.content.get('csrf_token')
                if csrf_token:
                    self.session.headers['X-CSRFToken'] = csrf_token
            
            login_data = {
                'username': username,
                'password': password
            }
            
            response = self.post(login_endpoint, data=login_data, authenticate=False)
            
            if response.is_success:
                self.auth_type = 'session'
                self.logger.info(f"Session authentication successful for user: {username}")
                return True
            
            self.logger.error(f"Session authentication failed for user: {username}")
            return False
            
        except Exception as e:
            self.logger.error(f"Session authentication error: {str(e)}")
            return False
    
    def authenticate_api_key(self, api_key: str, header_name: str = 'X-API-Key') -> bool:
        """
        Authenticate using API key
        
        Args:
            api_key: API key for authentication
            header_name: Header name for API key
            
        Returns:
            bool: True if authentication successful
        """
        try:
            self.auth_token = api_key
            self.auth_type = 'api_key'
            self.session.headers[header_name] = api_key
            self.logger.info("API key authentication configured")
            return True
            
        except Exception as e:
            self.logger.error(f"API key authentication error: {str(e)}")
            return False
    
    def logout(self, logout_endpoint: str = '/api/v1/auth/logout/') -> bool:
        """
        Logout and clear authentication
        
        Args:
            logout_endpoint: Logout API endpoint
            
        Returns:
            bool: True if logout successful
        """
        try:
            if self.auth_type:
                response = self.post(logout_endpoint)
                
                # Clear authentication regardless of response
                self.clear_authentication()
                
                if response.is_success:
                    self.logger.info("Logout successful")
                    return True
                else:
                    self.logger.warning("Logout endpoint returned error, but authentication cleared")
                    return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            self.clear_authentication()
            return False
    
    def clear_authentication(self):
        """Clear all authentication data"""
        self.auth_token = None
        self.auth_type = None
        
        # Remove auth headers
        headers_to_remove = ['Authorization', 'X-API-Key', 'X-CSRFToken']
        for header in headers_to_remove:
            self.session.headers.pop(header, None)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                     authenticate: bool = True, timeout: float = 30.0) -> APIResponse:
        """
        Make HTTP request with comprehensive tracking and validation
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            params: URL parameters
            headers: Additional headers
            authenticate: Whether to include authentication
            timeout: Request timeout in seconds
            
        Returns:
            APIResponse: Wrapped response with metrics and validation
        """
        # Prepare URL
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Prepare headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Prepare request data
        request_data = None
        if data is not None:
            if isinstance(data, dict):
                request_data = json.dumps(data)
            else:
                request_data = data
        
        # Track request start time
        start_time = time.time()
        
        try:
            # Make request
            response = self.session.request(
                method=method.upper(),
                url=url,
                data=request_data,
                params=params,
                headers=request_headers,
                timeout=timeout
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Parse response content
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    content = response.json()
                else:
                    content = response.text
            except json.JSONDecodeError:
                content = response.text
            
            # Create API response object
            api_response = APIResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=content,
                response_time=response_time,
                request_url=url,
                request_method=method.upper(),
                request_headers=dict(request_headers),
                request_data=data
            )
            
            # Track rate limiting info
            self._track_rate_limiting(api_response)
            
            # Add to request history
            self.request_history.append(api_response)
            
            # Log performance warnings
            if response_time > self.performance_thresholds['response_time_critical']:
                self.logger.warning(f"Critical response time: {response_time:.2f}s for {method} {url}")
            elif response_time > self.performance_thresholds['response_time_warning']:
                self.logger.warning(f"Slow response time: {response_time:.2f}s for {method} {url}")
            
            return api_response
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout for {method} {url}")
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error for {method} {url}")
            raise
        except Exception as e:
            self.logger.error(f"Request error for {method} {url}: {str(e)}")
            raise
    
    def _track_rate_limiting(self, response: APIResponse):
        """Track rate limiting information from response headers"""
        rate_limit_headers = {
            'x-ratelimit-limit': 'limit',
            'x-ratelimit-remaining': 'remaining',
            'x-ratelimit-reset': 'reset',
            'retry-after': 'retry_after'
        }
        
        rate_info = {}
        for header, key in rate_limit_headers.items():
            if header in response.headers:
                try:
                    rate_info[key] = int(response.headers[header])
                except ValueError:
                    rate_info[key] = response.headers[header]
        
        if rate_info:
            self.rate_limit_info[response.request_url] = {
                **rate_info,
                'timestamp': response.timestamp
            }
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, authenticate: bool = True,
            timeout: float = 30.0) -> APIResponse:
        """Make GET request"""
        return self._make_request('GET', endpoint, params=params, headers=headers,
                                authenticate=authenticate, timeout=timeout)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
             authenticate: bool = True, timeout: float = 30.0) -> APIResponse:
        """Make POST request"""
        return self._make_request('POST', endpoint, data=data, params=params,
                                headers=headers, authenticate=authenticate, timeout=timeout)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
            authenticate: bool = True, timeout: float = 30.0) -> APIResponse:
        """Make PUT request"""
        return self._make_request('PUT', endpoint, data=data, params=params,
                                headers=headers, authenticate=authenticate, timeout=timeout)
    
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
              params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
              authenticate: bool = True, timeout: float = 30.0) -> APIResponse:
        """Make PATCH request"""
        return self._make_request('PATCH', endpoint, data=data, params=params,
                                headers=headers, authenticate=authenticate, timeout=timeout)
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None, authenticate: bool = True,
               timeout: float = 30.0) -> APIResponse:
        """Make DELETE request"""
        return self._make_request('DELETE', endpoint, params=params, headers=headers,
                                authenticate=authenticate, timeout=timeout)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all requests"""
        if not self.request_history:
            return {}
        
        response_times = [r.response_time for r in self.request_history]
        
        return {
            'total_requests': len(self.request_history),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'success_rate': len([r for r in self.request_history if r.is_success]) / len(self.request_history),
            'error_rate': len([r for r in self.request_history if not r.is_success]) / len(self.request_history),
            'slow_requests': len([r for r in self.request_history if r.response_time > self.performance_thresholds['response_time_warning']]),
            'critical_requests': len([r for r in self.request_history if r.response_time > self.performance_thresholds['response_time_critical']])
        }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limiting status"""
        return self.rate_limit_info.copy()
    
    def clear_history(self):
        """Clear request history and metrics"""
        self.request_history.clear()
        self.rate_limit_info.clear()
    
    def validate_response_schema(self, response: APIResponse, schema: Dict[str, Any]) -> List[str]:
        """Validate response against JSON schema"""
        return response.validate_json_schema(schema)
    
    def assert_response_success(self, response: APIResponse, message: str = ""):
        """Assert that response indicates success"""
        if not response.is_success:
            error_msg = f"Expected successful response, got {response.status_code}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    
    def assert_response_status(self, response: APIResponse, expected_status: int, message: str = ""):
        """Assert specific response status code"""
        if response.status_code != expected_status:
            error_msg = f"Expected status {expected_status}, got {response.status_code}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    
    def assert_response_has_field(self, response: APIResponse, field_path: str, message: str = ""):
        """Assert that response has specified field"""
        if not response.has_field(field_path):
            error_msg = f"Response missing required field: {field_path}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    
    def assert_response_field_value(self, response: APIResponse, field_path: str, expected_value: Any, message: str = ""):
        """Assert that response field has expected value"""
        actual_value = response.get_field_value(field_path)
        if actual_value != expected_value:
            error_msg = f"Field {field_path}: expected {expected_value}, got {actual_value}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)