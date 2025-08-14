"""
Unit tests for API Test Client

Tests the APITestClient functionality including authentication,
request handling, and response validation.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from core.interfaces import Environment



class TestAPIResponse:
    """Test APIResponse class"""
    
    def test_api_response_creation(self):
        """Test APIResponse object creation"""
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={'message': 'success'},
            response_time=0.5,
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={'accept': 'application/json'}
        )
        
        assert response.status_code == 200
        assert response.is_success
        assert not response.is_client_error
        assert not response.is_server_error
        assert response.response_time == 0.5
    
    def test_status_code_properties(self):
        """Test status code classification properties"""
        # Success response
        success_response = APIResponse(200, {}, {}, 0.1, '', 'GET', {})
        assert success_response.is_success
        assert not success_response.is_client_error
        assert not success_response.is_server_error
        
        # Client error response
        client_error_response = APIResponse(404, {}, {}, 0.1, '', 'GET', {})
        assert not client_error_response.is_success
        assert client_error_response.is_client_error
        assert not client_error_response.is_server_error
        
        # Server error response
        server_error_response = APIResponse(500, {}, {}, 0.1, '', 'GET', {})
        assert not server_error_response.is_success
        assert not server_error_response.is_client_error
        assert server_error_response.is_server_error
    
    def test_has_field(self):
        """Test field existence checking"""
        response = APIResponse(
            200, {}, 
            {'user': {'id': 1, 'profile': {'name': 'John'}}}, 
            0.1, '', 'GET', {}
        )
        
        assert response.has_field('user')
        assert response.has_field('user.id')
        assert response.has_field('user.profile.name')
        assert not response.has_field('user.email')
        assert not response.has_field('nonexistent')
    
    def test_get_field_value(self):
        """Test field value retrieval"""
        response = APIResponse(
            200, {}, 
            {'user': {'id': 1, 'profile': {'name': 'John'}}}, 
            0.1, '', 'GET', {}
        )
        
        assert response.get_field_value('user.id') == 1
        assert response.get_field_value('user.profile.name') == 'John'
        assert response.get_field_value('user.email') is None
        assert response.get_field_value('nonexistent') is None
    
    def test_validate_json_schema(self):
        """Test JSON schema validation"""
        response = APIResponse(
            200, {}, 
            {'name': 'John', 'age': 30}, 
            0.1, '', 'GET', {}
        )
        
        # Valid schema
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'number'}
            },
            'required': ['name', 'age']
        }
        
        errors = response.validate_json_schema(schema)
        assert len(errors) == 0
        
        # Invalid schema
        invalid_schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'}
            },
            'required': ['name', 'email']
        }
        
        errors = response.validate_json_schema(invalid_schema)
        assert len(errors) > 0


class TestAPITestClient:
    """Test APITestClient class"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = APITestClient('http://test.com', Environment.DEVELOPMENT)
    
    def test_client_initialization(self):
        """Test client initialization"""
        assert self.client.base_url == 'http://test.com'
        assert self.client.environment == Environment.DEVELOPMENT
        assert self.client.auth_token is None
        assert self.client.auth_type is None
        assert 'Content-Type' in self.client.session.headers
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test successful request making"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'message': 'success'}
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/test')
        
        assert response.status_code == 200
        assert response.is_success
        assert response.content == {'message': 'success'}
        assert response.response_time > 0
        
        # Verify request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['method'] == 'GET'
        assert kwargs['url'] == 'http://test.com/api/test'
    
    @patch('requests.Session.request')
    def test_make_request_with_data(self, mock_request):
        """Test request with JSON data"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'id': 1, 'created': True}
        mock_request.return_value = mock_response
        
        test_data = {'name': 'Test', 'value': 123}
        response = self.client.post('/api/create', data=test_data)
        
        assert response.status_code == 201
        assert response.request_data == test_data
        
        # Verify JSON data was sent
        args, kwargs = mock_request.call_args
        assert kwargs['data'] == json.dumps(test_data)
    
    @patch('requests.Session.request')
    def test_authentication_jwt(self, mock_request):
        """Test JWT authentication"""
        # Mock login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'access': 'test-jwt-token'}
        mock_request.return_value = mock_response
        
        success = self.client.authenticate_jwt('testuser', 'testpass')
        
        assert success
        assert self.client.auth_token == 'test-jwt-token'
        assert self.client.auth_type == 'jwt'
        assert 'Authorization' in self.client.session.headers
        assert self.client.session.headers['Authorization'] == 'Bearer test-jwt-token'
    
    @patch('requests.Session.request')
    def test_authentication_jwt_failure(self, mock_request):
        """Test JWT authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'error': 'Invalid credentials'}
        mock_request.return_value = mock_response
        
        success = self.client.authenticate_jwt('baduser', 'badpass')
        
        assert not success
        assert self.client.auth_token is None
        assert self.client.auth_type is None
    
    def test_authenticate_api_key(self):
        """Test API key authentication"""
        success = self.client.authenticate_api_key('test-api-key')
        
        assert success
        assert self.client.auth_token == 'test-api-key'
        assert self.client.auth_type == 'api_key'
        assert 'X-API-Key' in self.client.session.headers
        assert self.client.session.headers['X-API-Key'] == 'test-api-key'
    
    def test_clear_authentication(self):
        """Test authentication clearing"""
        # Set up authentication
        self.client.authenticate_api_key('test-key')
        assert self.client.auth_token is not None
        
        # Clear authentication
        self.client.clear_authentication()
        
        assert self.client.auth_token is None
        assert self.client.auth_type is None
        assert 'X-API-Key' not in self.client.session.headers
        assert 'Authorization' not in self.client.session.headers
    
    @patch('requests.Session.request')
    def test_performance_tracking(self, mock_request):
        """Test performance metrics tracking"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'data': 'test'}
        mock_request.return_value = mock_response
        
        # Make multiple requests
        self.client.get('/api/test1')
        self.client.get('/api/test2')
        
        # Check performance metrics
        metrics = self.client.get_performance_metrics()
        
        assert metrics['total_requests'] == 2
        assert 'avg_response_time' in metrics
        assert 'success_rate' in metrics
        assert metrics['success_rate'] == 1.0  # All successful
    
    @patch('requests.Session.request')
    def test_rate_limiting_tracking(self, mock_request):
        """Test rate limiting information tracking"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'application/json',
            'x-ratelimit-limit': '100',
            'x-ratelimit-remaining': '95',
            'x-ratelimit-reset': '1640995200'
        }
        mock_response.json.return_value = {'data': 'test'}
        mock_request.return_value = mock_response
        
        self.client.get('/api/test')
        
        rate_limit_info = self.client.get_rate_limit_status()
        assert len(rate_limit_info) > 0
        
        # Check if rate limit info was captured
        url_info = rate_limit_info.get('http://test.com/api/test')
        if url_info:
            assert 'limit' in url_info
            assert 'remaining' in url_info
    
    def test_assertion_methods(self):
        """Test response assertion methods"""
        success_response = APIResponse(200, {}, {'data': 'test'}, 0.1, '', 'GET', {})
        error_response = APIResponse(404, {}, {'error': 'Not found'}, 0.1, '', 'GET', {})
        
        # Test successful assertions
        self.client.assert_response_success(success_response)
        self.client.assert_response_status(success_response, 200)
        self.client.assert_response_has_field(success_response, 'data')
        self.client.assert_response_field_value(success_response, 'data', 'test')
        
        # Test failing assertions
        with pytest.raises(AssertionError):
            self.client.assert_response_success(error_response)
        
        with pytest.raises(AssertionError):
            self.client.assert_response_status(success_response, 201)
        
        with pytest.raises(AssertionError):
            self.client.assert_response_has_field(success_response, 'nonexistent')
        
        with pytest.raises(AssertionError):
            self.client.assert_response_field_value(success_response, 'data', 'wrong')
    
    def test_clear_history(self):
        """Test clearing request history"""
        # Add some mock history
        self.client.request_history.append(
            APIResponse(200, {}, {}, 0.1, '', 'GET', {})
        )
        
        assert len(self.client.request_history) == 1
        
        self.client.clear_history()
        
        assert len(self.client.request_history) == 0
        assert len(self.client.rate_limit_info) == 0
    
    @patch('requests.Session.request')
    def test_timeout_handling(self, mock_request):
        """Test request timeout handling"""
        import requests
        mock_request.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(requests.exceptions.Timeout):
            self.client.get('/api/test', timeout=1.0)
    
    @patch('requests.Session.request')
    def test_connection_error_handling(self, mock_request):
        """Test connection error handling"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(requests.exceptions.ConnectionError):
            self.client.get('/api/test')
    
    @patch('requests.Session.request')
    def test_non_json_response(self, mock_request):
        """Test handling of non-JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.json.side_effect = json.JSONDecodeError('No JSON', '', 0)
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/test')
        
        assert response.status_code == 200
        assert response.content == '<html><body>Test</body></html>'
    
    def test_url_handling(self):
        """Test URL construction and handling"""
        # Test relative URL
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'test'
            mock_request.return_value = mock_response
            
            self.client.get('/api/test')
            
            args, kwargs = mock_request.call_args
            assert kwargs['url'] == 'http://test.com/api/test'
        
        # Test absolute URL
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = 'test'
            mock_request.return_value = mock_response
            
            self.client.get('http://other.com/api/test')
            
            args, kwargs = mock_request.call_args
            assert kwargs['url'] == 'http://other.com/api/test'


if __name__ == '__main__':
    pytest.main([__file__])