"""
Authentication API Integration Tests

End-to-end integration tests for authentication and user management APIs.
Tests complete user journeys and cross-module interactions.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator
from api.auth_test_data import AuthTestDataFactory, get_test_users, get_user_by_role
from core.interfaces import Environment, UserRole


class TestAuthenticationIntegration:
    """Integration tests for complete authentication flows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.data_factory = AuthTestDataFactory(Environment.DEVELOPMENT)
        self.test_users = get_test_users(Environment.DEVELOPMENT)
        self.endpoints = self.data_factory.get_api_endpoints()
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_complete_user_registration_flow(self, mock_request):
        """Test complete user registration and verification flow"""
        # Mock responses for registration flow
        responses = [
            # Registration response
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 100,
                    'email': 'newuser@testdomain.com',
                    'first_name': 'New',
                    'last_name': 'User',
                    'is_active': False,
                    'date_joined': '2024-01-01T00:00:00Z'
                }
            ),
            # Email verification response
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'message': 'Email verified successfully',
                    'user': {
                        'id': 100,
                        'email': 'newuser@testdomain.com',
                        'is_active': True
                    }
                }
            ),
            # Login after verification
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.signature',
                    'refresh': 'refresh_token_here',
                    'user': {
                        'id': 100,
                        'email': 'newuser@testdomain.com',
                        'first_name': 'New',
                        'last_name': 'User',
                        'is_active': True
                    }
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Step 1: Register new user
        registration_data = {
            'email': 'newuser@testdomain.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        registration_response = self.client.post(
            self.endpoints['register'], 
            data=registration_data, 
            authenticate=False
        )
        
        # Validate registration
        assert registration_response.is_success
        assert registration_response.status_code == 201
        assert registration_response.has_field('id')
        assert registration_response.get_field_value('is_active') == False
        
        # Step 2: Verify email (simulate clicking verification link)
        verification_data = {
            'token': 'verification_token_123',
            'user_id': 100
        }
        
        verification_response = self.client.post(
            self.endpoints['verify_email'],
            data=verification_data,
            authenticate=False
        )
        
        # Validate verification
        assert verification_response.is_success
        assert verification_response.status_code == 200
        
        # Step 3: Login with verified account
        login_success = self.client.authenticate_jwt('newuser@testdomain.com', 'securepass123')
        
        assert login_success
        assert self.client.auth_token is not None
        
        # Validate complete flow
        assert len(self.client.request_history) == 3
        
        # Check that all responses are valid
        for response in self.client.request_history:
            validation_result = self.validator.validate_full_response(response)
            assert validation_result.is_valid or len(validation_result.errors) == 0
    
    @patch('requests.Session.request')
    def test_user_profile_management_flow(self, mock_request):
        """Test complete user profile management flow"""
        # Mock responses for profile management
        responses = [
            # Get profile
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 1,
                    'email': 'customer1@testdomain.com',
                    'first_name': 'Customer1',
                    'last_name': 'User',
                    'phone': '+15550011001',
                    'is_active': True,
                    'date_joined': '2024-01-01T00:00:00Z'
                }
            ),
            # Update profile
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 1,
                    'email': 'customer1@testdomain.com',
                    'first_name': 'UpdatedName',
                    'last_name': 'UpdatedLastName',
                    'phone': '+15550011002',
                    'is_active': True,
                    'date_joined': '2024-01-01T00:00:00Z'
                }
            ),
            # Change password
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'message': 'Password changed successfully'
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Setup authenticated user
        customer_user = get_user_by_role(UserRole.CUSTOMER)
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        
        # Step 1: Get current profile
        profile_response = self.client.get(self.endpoints['profile'])
        
        assert profile_response.is_success
        assert profile_response.status_code == 200
        assert profile_response.has_field('email')
        
        original_first_name = profile_response.get_field_value('first_name')
        
        # Step 2: Update profile
        update_data = {
            'first_name': 'UpdatedName',
            'last_name': 'UpdatedLastName',
            'phone': '+15550011002'
        }
        
        update_response = self.client.patch(self.endpoints['profile'], data=update_data)
        
        assert update_response.is_success
        assert update_response.status_code == 200
        assert update_response.get_field_value('first_name') == 'UpdatedName'
        assert update_response.get_field_value('first_name') != original_first_name
        
        # Step 3: Change password
        password_data = {
            'old_password': 'customerpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        password_response = self.client.post(self.endpoints['change_password'], data=password_data)
        
        assert password_response.is_success
        assert password_response.status_code == 200
        
        # Validate all operations
        assert len(self.client.request_history) == 3
        
        for response in self.client.request_history:
            validation_result = self.validator.validate_full_response(response)
            assert validation_result.is_valid or len(validation_result.errors) == 0
    
    @patch('requests.Session.request')
    def test_role_based_access_flow(self, mock_request):
        """Test role-based access control across different user types"""
        # Mock responses for different access levels
        def mock_request_side_effect(*args, **kwargs):
            url = kwargs.get('url', '')
            headers = kwargs.get('headers', {})
            
            # Check authorization header to determine user role
            auth_header = headers.get('Authorization', '')
            
            if 'customer_token' in auth_header:
                # Customer access
                if '/api/v1/auth/profile/' in url:
                    return Mock(
                        status_code=200,
                        headers={'content-type': 'application/json'},
                        json=lambda: {'id': 1, 'role': 'customer'}
                    )
                elif '/api/v1/admin/' in url:
                    return Mock(
                        status_code=403,
                        headers={'content-type': 'application/json'},
                        json=lambda: {'detail': 'Permission denied'}
                    )
            elif 'admin_token' in auth_header:
                # Admin access
                if '/api/v1/users/' in url:
                    return Mock(
                        status_code=200,
                        headers={'content-type': 'application/json'},
                        json=lambda: {'count': 10, 'results': []}
                    )
                elif '/api/v1/admin/' in url:
                    return Mock(
                        status_code=200,
                        headers={'content-type': 'application/json'},
                        json=lambda: {'message': 'Admin access granted'}
                    )
            
            # Default unauthorized response
            return Mock(
                status_code=401,
                headers={'content-type': 'application/json'},
                json=lambda: {'detail': 'Authentication required'}
            )
        
        mock_request.side_effect = mock_request_side_effect
        
        # Test customer access
        self.client.auth_token = 'customer_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer customer_token_123'
        
        # Customer should access profile
        profile_response = self.client.get(self.endpoints['profile'])
        assert profile_response.is_success
        assert profile_response.status_code == 200
        
        # Customer should NOT access admin endpoints
        admin_response = self.client.get(self.endpoints['admin'])
        assert admin_response.is_client_error
        assert admin_response.status_code == 403
        
        # Switch to admin user
        self.client.auth_token = 'admin_token_123'
        self.client.session.headers['Authorization'] = 'Bearer admin_token_123'
        
        # Admin should access user management
        users_response = self.client.get(self.endpoints['users'])
        assert users_response.is_success
        assert users_response.status_code == 200
        
        # Admin should access admin endpoints
        admin_access_response = self.client.get(self.endpoints['admin'])
        assert admin_access_response.is_success
        assert admin_access_response.status_code == 200
    
    @patch('requests.Session.request')
    def test_token_lifecycle_flow(self, mock_request):
        """Test complete JWT token lifecycle"""
        # Mock responses for token lifecycle
        responses = [
            # Initial login
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'access': 'initial_access_token',
                    'refresh': 'refresh_token_123',
                    'user': {'id': 1, 'email': 'test@example.com'}
                }
            ),
            # Token refresh
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'access': 'new_access_token'
                }
            ),
            # Logout
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'message': 'Successfully logged out'
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # Step 1: Login and get tokens
        login_success = self.client.authenticate_jwt('test@example.com', 'testpass123')
        
        assert login_success
        assert self.client.auth_token == 'initial_access_token'
        
        # Step 2: Refresh token
        refresh_data = {'refresh': 'refresh_token_123'}
        refresh_response = self.client.post(self.endpoints['refresh'], data=refresh_data, authenticate=False)
        
        assert refresh_response.is_success
        assert refresh_response.status_code == 200
        assert refresh_response.has_field('access')
        
        # Step 3: Logout
        logout_success = self.client.logout()
        
        assert logout_success
        assert self.client.auth_token is None
        assert self.client.auth_type is None
    
    @patch('requests.Session.request')
    def test_security_validation_flow(self, mock_request):
        """Test security validation across authentication endpoints"""
        # Mock security-compliant responses
        def mock_request_side_effect(*args, **kwargs):
            return Mock(
                status_code=200,
                headers={
                    'content-type': 'application/json',
                    'x-content-type-options': 'nosniff',
                    'x-frame-options': 'DENY',
                    'x-xss-protection': '1; mode=block',
                    'strict-transport-security': 'max-age=31536000',
                    'x-ratelimit-limit': '100',
                    'x-ratelimit-remaining': '99'
                },
                json=lambda: {'message': 'success'}
            )
        
        mock_request.side_effect = mock_request_side_effect
        
        # Test various endpoints for security compliance
        test_endpoints = [
            self.endpoints['register'],
            self.endpoints['login'],
            self.endpoints['profile']
        ]
        
        for endpoint in test_endpoints:
            response = self.client.get(endpoint, authenticate=False)
            
            # Validate security headers
            security_result = self.validator.security_validator.validate_security_headers(response)
            assert security_result.is_valid or len(security_result.warnings) <= 2  # Allow minor warnings
            
            # Check for sensitive data exposure
            sensitive_result = self.validator.security_validator.validate_sensitive_data_exposure(response)
            assert sensitive_result.is_valid
    
    @patch('requests.Session.request')
    def test_rate_limiting_integration(self, mock_request):
        """Test rate limiting integration across authentication endpoints"""
        request_count = 0
        
        def mock_request_side_effect(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            
            if request_count <= 5:
                # Normal responses
                return Mock(
                    status_code=200,
                    headers={
                        'content-type': 'application/json',
                        'x-ratelimit-limit': '10',
                        'x-ratelimit-remaining': str(10 - request_count),
                        'x-ratelimit-reset': str(int(time.time()) + 3600)
                    },
                    json=lambda: {'message': 'success'}
                )
            else:
                # Rate limited
                return Mock(
                    status_code=429,
                    headers={
                        'content-type': 'application/json',
                        'x-ratelimit-limit': '10',
                        'x-ratelimit-remaining': '0',
                        'retry-after': '3600'
                    },
                    json=lambda: {'detail': 'Rate limit exceeded'}
                )
        
        mock_request.side_effect = mock_request_side_effect
        
        # Make requests until rate limited
        for i in range(8):
            response = self.client.get(self.endpoints['products'], authenticate=False)
            
            if i < 5:
                assert response.is_success
                assert 'x-ratelimit-remaining' in response.headers
            else:
                assert response.status_code == 429
                assert 'retry-after' in response.headers
        
        # Verify rate limit tracking
        rate_limit_info = self.client.get_rate_limit_status()
        assert len(rate_limit_info) > 0


class TestUserManagementIntegration:
    """Integration tests for user management operations"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)
        self.validator = APIValidator()
        self.data_factory = AuthTestDataFactory(Environment.DEVELOPMENT)
        self.endpoints = self.data_factory.get_api_endpoints()
        
        # Setup admin authentication
        self.client.auth_token = 'admin_token_123'
        self.client.auth_type = 'jwt'
        self.client.session.headers['Authorization'] = 'Bearer admin_token_123'
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.client.clear_authentication()
        self.client.clear_history()
    
    @patch('requests.Session.request')
    def test_user_crud_operations_flow(self, mock_request):
        """Test complete CRUD operations for user management"""
        # Mock responses for CRUD operations
        responses = [
            # Create user
            Mock(
                status_code=201,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 101,
                    'email': 'newuser@testdomain.com',
                    'first_name': 'New',
                    'last_name': 'User',
                    'is_active': True,
                    'role': 'customer'
                }
            ),
            # Read user
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 101,
                    'email': 'newuser@testdomain.com',
                    'first_name': 'New',
                    'last_name': 'User',
                    'is_active': True,
                    'role': 'customer'
                }
            ),
            # Update user
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'id': 101,
                    'email': 'newuser@testdomain.com',
                    'first_name': 'Updated',
                    'last_name': 'User',
                    'is_active': True,
                    'role': 'customer'
                }
            ),
            # Delete user
            Mock(
                status_code=204,
                headers={},
                text=''
            )
        ]
        
        mock_request.side_effect = responses
        
        # CREATE: Create new user
        user_data = {
            'email': 'newuser@testdomain.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'customer'
        }
        
        create_response = self.client.post(self.endpoints['users'], data=user_data)
        
        assert create_response.is_success
        assert create_response.status_code == 201
        
        # Validate CRUD response
        create_validation = self.validator.validate_crud_response(create_response, 'CREATE')
        assert create_validation.is_valid
        
        user_id = create_response.get_field_value('id')
        
        # READ: Get user details
        user_detail_endpoint = self.endpoints['user_detail'].format(id=user_id)
        read_response = self.client.get(user_detail_endpoint)
        
        assert read_response.is_success
        assert read_response.status_code == 200
        
        read_validation = self.validator.validate_crud_response(read_response, 'READ')
        assert read_validation.is_valid
        
        # UPDATE: Update user
        update_data = {'first_name': 'Updated'}
        update_response = self.client.patch(user_detail_endpoint, data=update_data)
        
        assert update_response.is_success
        assert update_response.status_code == 200
        assert update_response.get_field_value('first_name') == 'Updated'
        
        update_validation = self.validator.validate_crud_response(update_response, 'UPDATE')
        assert update_validation.is_valid
        
        # DELETE: Delete user
        delete_response = self.client.delete(user_detail_endpoint)
        
        assert delete_response.is_success
        assert delete_response.status_code == 204
        
        delete_validation = self.validator.validate_crud_response(delete_response, 'DELETE')
        assert delete_validation.is_valid
        
        # Verify all operations completed
        assert len(self.client.request_history) == 4
    
    @patch('requests.Session.request')
    def test_bulk_user_operations(self, mock_request):
        """Test bulk user operations and pagination"""
        # Mock responses for bulk operations
        responses = [
            # List users (paginated)
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'count': 25,
                    'next': 'http://localhost:8000/api/v1/users/?page=2',
                    'previous': None,
                    'results': [
                        {
                            'id': i,
                            'email': f'user{i}@testdomain.com',
                            'first_name': f'User{i}',
                            'last_name': 'Test',
                            'is_active': True,
                            'role': 'customer'
                        } for i in range(1, 11)
                    ]
                }
            ),
            # Bulk update response
            Mock(
                status_code=200,
                headers={'content-type': 'application/json'},
                json=lambda: {
                    'updated_count': 5,
                    'message': 'Bulk update completed successfully'
                }
            )
        ]
        
        mock_request.side_effect = responses
        
        # List users with pagination
        list_response = self.client.get(self.endpoints['users'])
        
        assert list_response.is_success
        assert list_response.status_code == 200
        
        # Validate pagination
        pagination_validation = self.validator.validate_success_response(list_response, 'list')
        assert pagination_validation.is_valid
        
        assert list_response.has_field('count')
        assert list_response.has_field('results')
        assert list_response.has_field('next')
        
        results = list_response.get_field_value('results')
        assert isinstance(results, list)
        assert len(results) == 10
        
        # Bulk update operation
        bulk_update_data = {
            'user_ids': [1, 2, 3, 4, 5],
            'update_data': {'is_active': False}
        }
        
        bulk_response = self.client.patch(self.endpoints['users'], data=bulk_update_data)
        
        assert bulk_response.is_success
        assert bulk_response.status_code == 200
        assert bulk_response.has_field('updated_count')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])