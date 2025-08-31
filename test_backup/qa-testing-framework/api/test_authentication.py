"""
Authentication and User Management API Tests

Comprehensive test suite for authentication flows, user management,
role-based access control, rate limiting, and security validation.

This module implements task 6.2 from the QA testing framework specification.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator, ValidationResult
from core.interfaces import Environment, UserRole, Severity
from core.models import TestUser, Address, PaymentMethod


class TestAuthenticationAPI:
    """Test suite for authentication API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Test user credentials for different roles
        self.test_users = {
            'guest': {'username': 'guest_user', 'password': 'testpass123'},
            'customer': {'username': 'customer_user', 'password': 'testpass123'},
            'premium': {'username': 'premium_user', 'password': 'testpass123'},
            'seller': {'username': 'seller_user', 'password': 'testpass123'},
            'admin': {'username': 'admin_user', 'password': 'testpass123'},
            'super_admin': {'username': 'super_admin', 'password': 'testpass123'}
        }
        
        # API endpoints
        self.endpoints = {
            'register': '/api/v1/auth/register/',
            'login': '/api/v1/auth/login/',
            'logout': '/api/v1/auth/logout/',
            'refresh': '/api/v1/auth/refresh/',
            'profile': '/api/v1/auth/profile/',
            'change_password': '/api/v1/auth/change-password/',
            'reset_password': '/api/v1/auth/reset-password/',
            'verify_email': '/api/v1/auth/verify-email/',
            'users': '/api/v1/users/',
            'user_detail': '/api/v1/users/{id}/',
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    # User Registration Tests
    
    @patch('requests.Session.request')
    def test_user_registration_success(self, mock_request):
        """Test successful user registration"""
        # Mock successful registration response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'is_active': False,  # Requires email verification
            'date_joined': '2024-01-01T00:00:00Z'
        }
        mock_request.return_value = mock_response
        
        # Test data
        registration_data = {
            'email': 'newuser@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        # Make registration request
        response = self.client.post(self.endpoints['register'], data=registration_data, authenticate=False)
        
        # Validate response
        assert response.is_success
        assert response.status_code == 201
        
        # Validate response content
        validation_result = self.validator.response_validator.validate_success_response(response, 'user')
        assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
        
        # Check required fields
        assert response.has_field('id')
        assert response.has_field('email')
        assert response.get_field_value('email') == 'newuser@test.com'
        assert response.get_field_value('is_active') == False  # Should require verification
    
    @patch('requests.Session.request')
    def test_user_registration_validation_errors(self, mock_request):
        """Test user registration with validation errors"""
        # Mock validation error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'email': ['This field is required.'],
            'password': ['Password must be at least 8 characters long.']
        }
        mock_request.return_value = mock_response
        
        # Test data with validation errors
        registration_data = {
            'password': '123',  # Too short
            'password_confirm': '123',
            'first_name': 'Test'
        }
        
        # Make registration request
        response = self.client.post(self.endpoints['register'], data=registration_data, authenticate=False)
        
        # Validate error response
        assert response.is_client_error
        assert response.status_code == 400
        
        validation_result = self.validator.response_validator.validate_error_response(response)
        assert validation_result.is_valid
        
        # Check error structure
        assert isinstance(response.content, dict)
        assert 'email' in response.content
        assert 'password' in response.content
    
    @patch('requests.Session.request')
    def test_user_registration_duplicate_email(self, mock_request):
        """Test user registration with duplicate email"""
        # Mock duplicate email error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'email': ['User with this email already exists.']
        }
        mock_request.return_value = mock_response
        
        registration_data = {
            'email': 'existing@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post(self.endpoints['register'], data=registration_data, authenticate=False)
        
        assert response.is_client_error
        assert response.status_code == 400
        assert 'email' in response.content
        assert 'already exists' in str(response.content['email']).lower()
    
    # User Login Tests
    
    @patch('requests.Session.request')
    def test_user_login_success(self, mock_request):
        """Test successful user login with JWT token"""
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.test_signature',
            'refresh': 'refresh_token_here',
            'user': {
                'id': 1,
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'customer'
            }
        }
        mock_request.return_value = mock_response
        
        # Test login
        success = self.client.authenticate_jwt('test@example.com', 'testpass123')
        
        assert success
        assert self.client.auth_token is not None
        assert self.client.auth_type == 'jwt'
        assert 'Authorization' in self.client.session.headers
        
        # Validate authentication response
        response = self.client.request_history[-1]
        validation_result = self.validator.response_validator.validate_authentication_response(response)
        assert validation_result.is_valid
    
    @patch('requests.Session.request')
    def test_user_login_invalid_credentials(self, mock_request):
        """Test login with invalid credentials"""
        # Mock invalid credentials response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'Invalid credentials'
        }
        mock_request.return_value = mock_response
        
        success = self.client.authenticate_jwt('invalid@example.com', 'wrongpass')
        
        assert not success
        assert self.client.auth_token is None
        assert self.client.auth_type is None
    
    @patch('requests.Session.request')
    def test_user_login_inactive_account(self, mock_request):
        """Test login with inactive account"""
        # Mock inactive account response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'Account is not active'
        }
        mock_request.return_value = mock_response
        
        success = self.client.authenticate_jwt('inactive@example.com', 'testpass123')
        
        assert not success
        response = self.client.request_history[-1]
        assert response.status_code == 401
        assert 'not active' in str(response.content).lower()
    
    # Token Management Tests
    
    @patch('requests.Session.request')
    def test_token_refresh_success(self, mock_request):
        """Test successful token refresh"""
        # Mock refresh token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'access': 'new_access_token_here'
        }
        mock_request.return_value = mock_response
        
        # Set up existing refresh token
        refresh_data = {'refresh': 'existing_refresh_token'}
        
        response = self.client.post(self.endpoints['refresh'], data=refresh_data, authenticate=False)
        
        assert response.is_success
        assert response.status_code == 200
        assert response.has_field('access')
    
    @patch('requests.Session.request')
    def test_token_refresh_invalid_token(self, mock_request):
        """Test token refresh with invalid refresh token"""
        # Mock invalid refresh token response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'Token is invalid or expired'
        }
        mock_request.return_value = mock_response
        
        refresh_data = {'refresh': 'invalid_refresh_token'}
        
        response = self.client.post(self.endpoints['refresh'], data=refresh_data, authenticate=False)
        
        assert response.is_client_error
        assert response.status_code == 401
    
    # User Logout Tests
    
    @patch('requests.Session.request')
    def test_user_logout_success(self, mock_request):
        """Test successful user logout"""
        # Mock logout response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'message': 'Successfully logged out'
        }
        mock_request.return_value = mock_response
        
        # Set up authenticated state
        self.client.auth_token = 'test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer test_token'
        
        success = self.client.logout()
        
        assert success
        assert self.client.auth_token is None
        assert self.client.auth_type is None
        assert 'Authorization' not in self.client.session.headers
    
    # Password Management Tests
    
    @patch('requests.Session.request')
    def test_change_password_success(self, mock_request):
        """Test successful password change"""
        # Mock successful password change response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'message': 'Password changed successfully'
        }
        mock_request.return_value = mock_response
        
        # Set up authenticated state
        self.client.auth_token = 'test_token'
        self.client.auth_type = 'jwt'
        
        password_data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(self.endpoints['change_password'], data=password_data)
        
        assert response.is_success
        assert response.status_code == 200
    
    @patch('requests.Session.request')
    def test_change_password_wrong_old_password(self, mock_request):
        """Test password change with wrong old password"""
        # Mock wrong old password response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'old_password': ['Current password is incorrect']
        }
        mock_request.return_value = mock_response
        
        self.client.auth_token = 'test_token'
        self.client.auth_type = 'jwt'
        
        password_data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(self.endpoints['change_password'], data=password_data)
        
        assert response.is_client_error
        assert response.status_code == 400
        assert 'old_password' in response.content
    
    @patch('requests.Session.request')
    def test_reset_password_request(self, mock_request):
        """Test password reset request"""
        # Mock password reset request response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'message': 'Password reset email sent'
        }
        mock_request.return_value = mock_response
        
        reset_data = {'email': 'test@example.com'}
        
        response = self.client.post(self.endpoints['reset_password'], data=reset_data, authenticate=False)
        
        assert response.is_success
        assert response.status_code == 200
        assert 'message' in response.content


class TestUserManagementAPI:
    """Test suite for user management API endpoints"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Set up authenticated admin user
        self.client.auth_token = 'admin_test_token'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer admin_test_token'
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    # User Profile Management Tests
    
    @patch('requests.Session.request')
    def test_get_user_profile_success(self, mock_request):
        """Test successful user profile retrieval"""
        # Mock user profile response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+1234567890',
            'is_active': True,
            'date_joined': '2024-01-01T00:00:00Z',
            'role': 'customer'
        }
        mock_request.return_value = mock_response
        
        response = self.client.get(self.endpoints['profile'])
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate user schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'user')
        assert validation_result.is_valid, f"Validation errors: {validation_result.errors}"
        
        # Check required fields
        assert response.has_field('id')
        assert response.has_field('email')
        assert response.has_field('first_name')
        assert response.has_field('last_name')
    
    @patch('requests.Session.request')
    def test_update_user_profile_success(self, mock_request):
        """Test successful user profile update"""
        # Mock profile update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1234567890',
            'is_active': True,
            'date_joined': '2024-01-01T00:00:00Z',
            'role': 'customer'
        }
        mock_request.return_value = mock_response
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1234567890'
        }
        
        response = self.client.patch(self.endpoints['profile'], data=update_data)
        
        assert response.is_success
        assert response.status_code == 200
        assert response.get_field_value('first_name') == 'Updated'
        assert response.get_field_value('last_name') == 'Name'
    
    @patch('requests.Session.request')
    def test_get_user_profile_unauthenticated(self, mock_request):
        """Test user profile access without authentication"""
        # Mock unauthenticated response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'Authentication credentials were not provided.'
        }
        mock_request.return_value = mock_response
        
        # Clear authentication
        self.client.clear_authentication()
        
        response = self.client.get(self.endpoints['profile'], authenticate=False)
        
        assert response.is_client_error
        assert response.status_code == 401
    
    # User CRUD Operations Tests
    
    @patch('requests.Session.request')
    def test_list_users_success(self, mock_request):
        """Test successful user listing (admin only)"""
        # Mock users list response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 1,
                    'email': 'user1@example.com',
                    'first_name': 'User',
                    'last_name': 'One',
                    'is_active': True,
                    'date_joined': '2024-01-01T00:00:00Z',
                    'role': 'customer'
                },
                {
                    'id': 2,
                    'email': 'user2@example.com',
                    'first_name': 'User',
                    'last_name': 'Two',
                    'is_active': True,
                    'date_joined': '2024-01-02T00:00:00Z',
                    'role': 'seller'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        response = self.client.get(self.endpoints['users'])
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate pagination schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'list')
        assert validation_result.is_valid
        
        # Check pagination fields
        assert response.has_field('count')
        assert response.has_field('results')
        assert isinstance(response.get_field_value('results'), list)
        assert len(response.get_field_value('results')) == 2
    
    @patch('requests.Session.request')
    def test_get_user_detail_success(self, mock_request):
        """Test successful user detail retrieval"""
        # Mock user detail response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+1234567890',
            'is_active': True,
            'date_joined': '2024-01-01T00:00:00Z',
            'role': 'customer',
            'addresses': [
                {
                    'id': 1,
                    'street': '123 Test St',
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': '12345',
                    'country': 'US',
                    'address_type': 'shipping'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        user_id = 1
        endpoint = self.endpoints['user_detail'].format(id=user_id)
        response = self.client.get(endpoint)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate user schema
        validation_result = self.validator.response_validator.validate_success_response(response, 'user')
        assert validation_result.is_valid
        
        # Check user details
        assert response.get_field_value('id') == 1
        assert response.has_field('addresses')
    
    @patch('requests.Session.request')
    def test_create_user_success(self, mock_request):
        """Test successful user creation (admin only)"""
        # Mock user creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 3,
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'is_active': True,
            'date_joined': '2024-01-03T00:00:00Z',
            'role': 'customer'
        }
        mock_request.return_value = mock_response
        
        user_data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'customer'
        }
        
        response = self.client.post(self.endpoints['users'], data=user_data)
        
        assert response.is_success
        assert response.status_code == 201
        
        # Validate CRUD response
        validation_result = self.validator.response_validator.validate_crud_response(response, 'CREATE')
        assert validation_result.is_valid
        
        assert response.has_field('id')
        assert response.get_field_value('email') == 'newuser@example.com'
    
    @patch('requests.Session.request')
    def test_update_user_success(self, mock_request):
        """Test successful user update (admin only)"""
        # Mock user update response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'is_active': False,
            'date_joined': '2024-01-01T00:00:00Z',
            'role': 'customer'
        }
        mock_request.return_value = mock_response
        
        user_id = 1
        endpoint = self.endpoints['user_detail'].format(id=user_id)
        
        update_data = {
            'first_name': 'Updated',
            'is_active': False
        }
        
        response = self.client.patch(endpoint, data=update_data)
        
        assert response.is_success
        assert response.status_code == 200
        
        # Validate CRUD response
        validation_result = self.validator.response_validator.validate_crud_response(response, 'UPDATE')
        assert validation_result.is_valid
        
        assert response.get_field_value('first_name') == 'Updated'
        assert response.get_field_value('is_active') == False
    
    @patch('requests.Session.request')
    def test_delete_user_success(self, mock_request):
        """Test successful user deletion (admin only)"""
        # Mock user deletion response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ''
        mock_request.return_value = mock_response
        
        user_id = 1
        endpoint = self.endpoints['user_detail'].format(id=user_id)
        
        response = self.client.delete(endpoint)
        
        assert response.is_success
        assert response.status_code == 204
        
        # Validate CRUD response
        validation_result = self.validator.response_validator.validate_crud_response(response, 'DELETE')
        assert validation_result.is_valid


class TestRoleBasedAccessControl:
    """Test suite for role-based access control"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        
        # Define role-based endpoints and permissions
        self.role_permissions = {
            'guest': {
                'allowed': ['/api/v1/auth/register/', '/api/v1/auth/login/', '/api/v1/products/'],
                'forbidden': ['/api/v1/auth/profile/', '/api/v1/users/', '/api/v1/admin/']
            },
            'customer': {
                'allowed': ['/api/v1/auth/profile/', '/api/v1/products/', '/api/v1/orders/'],
                'forbidden': ['/api/v1/users/', '/api/v1/admin/', '/api/v1/sellers/']
            },
            'seller': {
                'allowed': ['/api/v1/auth/profile/', '/api/v1/products/', '/api/v1/sellers/', '/api/v1/orders/'],
                'forbidden': ['/api/v1/users/', '/api/v1/admin/']
            },
            'admin': {
                'allowed': ['/api/v1/auth/profile/', '/api/v1/users/', '/api/v1/admin/', '/api/v1/products/'],
                'forbidden': []
            }
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    def _authenticate_as_role(self, role: str):
        """Helper method to authenticate as specific role"""
        role_tokens = {
            'guest': None,  # No authentication
            'customer': 'customer_token_123',
            'seller': 'seller_token_123',
            'admin': 'admin_token_123'
        }
        
        if role != 'guest':
            self.client.auth_token = role_tokens[role]
            self.client.auth_type = 'jwt'
            self.client.session.headers['Authorization'] = f'Bearer {role_tokens[role]}'
    
    @patch('requests.Session.request')
    def test_customer_access_allowed_endpoints(self, mock_request):
        """Test customer access to allowed endpoints"""
        # Mock successful response for allowed endpoints
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'message': 'success'}
        mock_request.return_value = mock_response
        
        self._authenticate_as_role('customer')
        
        allowed_endpoints = self.role_permissions['customer']['allowed']
        
        for endpoint in allowed_endpoints:
            response = self.client.get(endpoint)
            assert response.is_success, f"Customer should have access to {endpoint}"
            assert response.status_code == 200
    
    @patch('requests.Session.request')
    def test_customer_access_forbidden_endpoints(self, mock_request):
        """Test customer access to forbidden endpoints"""
        # Mock forbidden response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'You do not have permission to perform this action.'
        }
        mock_request.return_value = mock_response
        
        self._authenticate_as_role('customer')
        
        forbidden_endpoints = self.role_permissions['customer']['forbidden']
        
        for endpoint in forbidden_endpoints:
            response = self.client.get(endpoint)
            assert response.is_client_error, f"Customer should not have access to {endpoint}"
            assert response.status_code == 403
    
    @patch('requests.Session.request')
    def test_seller_access_control(self, mock_request):
        """Test seller role access control"""
        # Mock responses based on endpoint
        def mock_request_side_effect(*args, **kwargs):
            url = kwargs.get('url', '')
            
            if '/api/v1/sellers/' in url or '/api/v1/products/' in url:
                # Allowed for sellers
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.headers = {'content-type': 'application/json'}
                mock_resp.json.return_value = {'message': 'success'}
                return mock_resp
            elif '/api/v1/admin/' in url:
                # Forbidden for sellers
                mock_resp = Mock()
                mock_resp.status_code = 403
                mock_resp.headers = {'content-type': 'application/json'}
                mock_resp.json.return_value = {'detail': 'Permission denied'}
                return mock_resp
            else:
                # Default response
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.headers = {'content-type': 'application/json'}
                mock_resp.json.return_value = {'message': 'success'}
                return mock_resp
        
        mock_request.side_effect = mock_request_side_effect
        
        self._authenticate_as_role('seller')
        
        # Test allowed endpoints
        allowed_response = self.client.get('/api/v1/sellers/')
        assert allowed_response.is_success
        
        # Test forbidden endpoints
        forbidden_response = self.client.get('/api/v1/admin/')
        assert forbidden_response.is_client_error
        assert forbidden_response.status_code == 403
    
    @patch('requests.Session.request')
    def test_admin_full_access(self, mock_request):
        """Test admin role has full access"""
        # Mock successful response for all endpoints
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'message': 'success'}
        mock_request.return_value = mock_response
        
        self._authenticate_as_role('admin')
        
        # Test various endpoints that should be accessible to admin
        admin_endpoints = [
            '/api/v1/users/',
            '/api/v1/admin/',
            '/api/v1/products/',
            '/api/v1/orders/',
            '/api/v1/sellers/'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            assert response.is_success, f"Admin should have access to {endpoint}"
            assert response.status_code == 200


class TestAPIRateLimiting:
    """Test suite for API rate limiting and security validation"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_rate_limiting_enforcement(self, mock_request):
        """Test API rate limiting enforcement"""
        # Mock rate limit responses
        def mock_request_side_effect(*args, **kwargs):
            # First few requests succeed
            if len(self.client.request_history) < 5:
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.headers = {
                    'content-type': 'application/json',
                    'x-ratelimit-limit': '10',
                    'x-ratelimit-remaining': str(9 - len(self.client.request_history)),
                    'x-ratelimit-reset': str(int(time.time()) + 3600)
                }
                mock_resp.json.return_value = {'message': 'success'}
                return mock_resp
            else:
                # Rate limit exceeded
                mock_resp = Mock()
                mock_resp.status_code = 429
                mock_resp.headers = {
                    'content-type': 'application/json',
                    'x-ratelimit-limit': '10',
                    'x-ratelimit-remaining': '0',
                    'retry-after': '3600'
                }
                mock_resp.json.return_value = {
                    'detail': 'Rate limit exceeded. Try again later.'
                }
                return mock_resp
        
        mock_request.side_effect = mock_request_side_effect
        
        # Make multiple requests to trigger rate limiting
        for i in range(7):
            response = self.client.get('/api/v1/products/', authenticate=False)
            
            if i < 5:
                assert response.is_success
                assert response.status_code == 200
                # Check rate limit headers
                assert 'x-ratelimit-limit' in response.headers
                assert 'x-ratelimit-remaining' in response.headers
            else:
                assert response.status_code == 429
                assert 'retry-after' in response.headers
                assert 'rate limit' in str(response.content).lower()
    
    @patch('requests.Session.request')
    def test_rate_limit_headers_validation(self, mock_request):
        """Test rate limit headers are properly set"""
        # Mock response with rate limit headers
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'application/json',
            'x-ratelimit-limit': '100',
            'x-ratelimit-remaining': '99',
            'x-ratelimit-reset': str(int(time.time()) + 3600)
        }
        mock_response.json.return_value = {'message': 'success'}
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/v1/products/', authenticate=False)
        
        assert response.is_success
        
        # Validate rate limit headers
        assert 'x-ratelimit-limit' in response.headers
        assert 'x-ratelimit-remaining' in response.headers
        assert 'x-ratelimit-reset' in response.headers
        
        # Check rate limit tracking
        rate_limit_info = self.client.get_rate_limit_status()
        assert len(rate_limit_info) > 0
    
    @patch('requests.Session.request')
    def test_authentication_rate_limiting(self, mock_request):
        """Test rate limiting on authentication endpoints"""
        # Mock failed login attempts
        def mock_request_side_effect(*args, **kwargs):
            if len(self.client.request_history) < 3:
                # Failed login attempts
                mock_resp = Mock()
                mock_resp.status_code = 401
                mock_resp.headers = {
                    'content-type': 'application/json',
                    'x-ratelimit-limit': '5',
                    'x-ratelimit-remaining': str(4 - len(self.client.request_history))
                }
                mock_resp.json.return_value = {'detail': 'Invalid credentials'}
                return mock_resp
            else:
                # Rate limit exceeded
                mock_resp = Mock()
                mock_resp.status_code = 429
                mock_resp.headers = {
                    'content-type': 'application/json',
                    'x-ratelimit-limit': '5',
                    'x-ratelimit-remaining': '0',
                    'retry-after': '900'  # 15 minutes
                }
                mock_resp.json.return_value = {
                    'detail': 'Too many failed login attempts. Try again later.'
                }
                return mock_resp
        
        mock_request.side_effect = mock_request_side_effect
        
        # Make multiple failed login attempts
        for i in range(5):
            login_data = {'username': 'test@example.com', 'password': 'wrongpass'}
            response = self.client.post('/api/v1/auth/login/', data=login_data, authenticate=False)
            
            if i < 3:
                assert response.status_code == 401  # Invalid credentials
            else:
                assert response.status_code == 429  # Rate limited
                assert 'retry-after' in response.headers


class TestAPISecurityValidation:
    """Test suite for API security validation"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_security_headers_validation(self, mock_request):
        """Test security headers are properly set"""
        # Mock response with security headers
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'application/json',
            'x-content-type-options': 'nosniff',
            'x-frame-options': 'DENY',
            'x-xss-protection': '1; mode=block',
            'strict-transport-security': 'max-age=31536000; includeSubDomains',
            'content-security-policy': "default-src 'self'"
        }
        mock_response.json.return_value = {'message': 'success'}
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/v1/products/', authenticate=False)
        
        assert response.is_success
        
        # Validate security headers
        security_result = self.validator.security_validator.validate_security_headers(response)
        assert security_result.is_valid or len(security_result.warnings) == 0
    
    @patch('requests.Session.request')
    def test_sensitive_data_exposure_check(self, mock_request):
        """Test for sensitive data exposure in responses"""
        # Mock response that might contain sensitive data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            # Should not contain sensitive fields like password, secret keys, etc.
        }
        mock_request.return_value = mock_response
        
        response = self.client.get('/api/v1/auth/profile/')
        
        assert response.is_success
        
        # Check for sensitive data exposure
        sensitive_data_result = self.validator.security_validator.validate_sensitive_data_exposure(response)
        assert sensitive_data_result.is_valid
    
    @patch('requests.Session.request')
    def test_input_validation_security(self, mock_request):
        """Test input validation for security vulnerabilities"""
        # Mock response for malicious input attempts
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'email': ['Enter a valid email address.']
        }
        mock_request.return_value = mock_response
        
        # Test SQL injection attempt
        malicious_data = {
            'email': "'; DROP TABLE users; --",
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/v1/auth/login/', data=malicious_data, authenticate=False)
        
        # Should be rejected with validation error, not cause server error
        assert response.is_client_error
        assert response.status_code == 400
        assert not response.is_server_error  # Should not cause 500 error
    
    @patch('requests.Session.request')
    def test_xss_protection_validation(self, mock_request):
        """Test XSS protection in API responses"""
        # Mock response for XSS attempt
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'first_name': ['Invalid characters in name.']
        }
        mock_request.return_value = mock_response
        
        # Test XSS attempt in user data
        xss_data = {
            'first_name': '<script>alert("xss")</script>',
            'last_name': 'User',
            'email': 'test@example.com'
        }
        
        response = self.client.patch('/api/v1/auth/profile/', data=xss_data)
        
        # Should be rejected with validation error
        assert response.is_client_error
        assert response.status_code == 400
    
    @patch('requests.Session.request')
    def test_csrf_protection_validation(self, mock_request):
        """Test CSRF protection for state-changing operations"""
        # Mock CSRF token requirement
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'detail': 'CSRF Failed: CSRF token missing or incorrect.'
        }
        mock_request.return_value = mock_response
        
        # Attempt state-changing operation without CSRF token
        update_data = {'first_name': 'Updated'}
        
        response = self.client.patch('/api/v1/auth/profile/', data=update_data)
        
        # Should be rejected due to missing CSRF token
        assert response.is_client_error
        assert response.status_code == 403


if __name__ == '__main__':
    pytest.main([__file__, '-v'])