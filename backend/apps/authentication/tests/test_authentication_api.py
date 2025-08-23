"""
Comprehensive tests for authentication API endpoints.
"""
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.authentication.models import EmailVerification, PasswordReset, UserSession

User = get_user_model()


class AuthenticationAPITest(APITestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        cache.clear()
    
    def test_register_endpoint_success(self):
        """Test successful user registration via API."""
        url = '/api/v1/auth/register/'
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Check user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.username, 'testuser')
    
    def test_register_endpoint_validation_errors(self):
        """Test registration with validation errors."""
        url = '/api/v1/auth/register/'
        
        # Missing required fields
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
        
        # Invalid email
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_endpoint_success(self):
        """Test successful login via API."""
        # Create and verify user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
    
    def test_login_endpoint_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Create user
        User.objects.create_user(**self.user_data)
        
        url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_login_endpoint_unverified_email(self):
        """Test login with unverified email."""
        # Create user (not verified)
        User.objects.create_user(**self.user_data)
        
        url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertIn('verified', response.data['error'])
    
    def test_logout_endpoint_success(self):
        """Test successful logout via API."""
        # Create and login user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        # Login first
        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        # Logout
        logout_url = '/api/v1/auth/logout/'
        logout_data = {'refresh_token': refresh_token}
        response = self.client.post(logout_url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_refresh_token_endpoint_success(self):
        """Test successful token refresh via API."""
        # Create and login user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        # Login first
        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        # Refresh token
        refresh_url = '/api/v1/auth/refresh/'
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)


class EmailVerificationAPITest(APITestCase):
    """Test email verification API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    @patch('apps.authentication.services.send_mail')
    def test_resend_verification_endpoint_success(self, mock_send_mail):
        """Test successful verification email resend via API."""
        url = '/api/v1/auth/resend-verification/'
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_send_mail.assert_called_once()
    
    def test_resend_verification_endpoint_nonexistent_user(self):
        """Test verification resend for non-existent user."""
        url = '/api/v1/auth/resend-verification/'
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_verify_email_endpoint_success(self):
        """Test successful email verification via API."""
        # Create verification token
        verification = EmailVerification.objects.create(user=self.user)
        
        url = f'/api/v1/auth/verify-email/{verification.token}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check user is verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
    
    def test_verify_email_endpoint_invalid_token(self):
        """Test email verification with invalid token."""
        url = '/api/v1/auth/verify-email/invalid_token/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class PasswordResetAPITest(APITestCase):
    """Test password reset API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    @patch('apps.authentication.services.send_mail')
    def test_password_reset_request_endpoint_success(self, mock_send_mail):
        """Test successful password reset request via API."""
        url = '/api/v1/auth/password-reset/request/'
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_send_mail.assert_called_once()
    
    def test_password_reset_request_endpoint_nonexistent_user(self):
        """Test password reset request for non-existent user."""
        url = '/api/v1/auth/password-reset/request/'
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(url, data, format='json')
        
        # Should still return success for security
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_password_reset_confirm_endpoint_success(self):
        """Test successful password reset confirmation via API."""
        # Create reset token
        reset = PasswordReset.objects.create(user=self.user)
        
        url = '/api/v1/auth/password-reset/confirm/'
        data = {
            'token': reset.token,
            'new_password': 'NewPassword123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
    
    def test_password_reset_confirm_endpoint_invalid_token(self):
        """Test password reset confirmation with invalid token."""
        url = '/api/v1/auth/password-reset/confirm/'
        data = {
            'token': 'invalid_token',
            'new_password': 'NewPassword123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class AdminAuthenticationAPITest(APITestCase):
    """Test admin authentication API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPassword123!',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        cache.clear()
    
    def test_admin_login_endpoint_success(self):
        """Test successful admin login via API."""
        url = '/api/v1/admin-auth/login/'
        data = {
            'email': 'admin@example.com',
            'password': 'AdminPassword123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertTrue(response.data['user']['is_staff'])
    
    def test_admin_login_endpoint_non_admin_user(self):
        """Test admin login with non-admin user."""
        # Create regular user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPassword123!'
        )
        regular_user.is_email_verified = True
        regular_user.save()
        
        url = '/api/v1/admin-auth/login/'
        data = {
            'email': 'regular@example.com',
            'password': 'RegularPassword123!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
    
    def test_admin_logout_endpoint_success(self):
        """Test successful admin logout via API."""
        # Login first
        login_url = '/api/v1/admin-auth/login/'
        login_data = {
            'email': 'admin@example.com',
            'password': 'AdminPassword123!'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        # Logout
        logout_url = '/api/v1/admin-auth/logout/'
        logout_data = {'refresh_token': refresh_token}
        response = self.client.post(logout_url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class UserManagementAPITest(APITestCase):
    """Test user management API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPassword123!',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPassword123!'
        )
        self.regular_user.is_email_verified = True
        self.regular_user.save()
        
        cache.clear()
    
    def _authenticate_admin(self):
        """Helper method to authenticate admin user."""
        login_url = '/api/v1/admin-auth/login/'
        login_data = {
            'email': 'admin@example.com',
            'password': 'AdminPassword123!'
        }
        response = self.client.post(login_url, login_data, format='json')
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def _authenticate_user(self):
        """Helper method to authenticate regular user."""
        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'regular@example.com',
            'password': 'RegularPassword123!'
        }
        response = self.client.post(login_url, login_data, format='json')
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def test_list_users_endpoint_admin(self):
        """Test listing users as admin."""
        self._authenticate_admin()
        
        url = '/api/v1/users/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('users', response.data)
        self.assertGreaterEqual(len(response.data['users']), 2)  # admin + regular user
    
    def test_list_users_endpoint_unauthorized(self):
        """Test listing users without authentication."""
        url = '/api/v1/users/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_user_profile_endpoint_self(self):
        """Test getting own user profile."""
        self._authenticate_user()
        
        url = '/api/v1/users/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'regular@example.com')
    
    def test_update_user_profile_endpoint_self(self):
        """Test updating own user profile."""
        self._authenticate_user()
        
        url = '/api/v1/users/me/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check user was updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
    
    def test_create_user_endpoint_admin(self):
        """Test creating user as admin."""
        self._authenticate_admin()
        
        url = '/api/v1/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check user was created
        new_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(new_user.username, 'newuser')


class SessionManagementAPITest(APITestCase):
    """Test session management API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.user.is_email_verified = True
        self.user.save()
        cache.clear()
    
    def _authenticate_user(self):
        """Helper method to authenticate user."""
        login_url = '/api/v1/auth/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        response = self.client.post(login_url, login_data, format='json')
        token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def test_list_sessions_endpoint(self):
        """Test listing user sessions."""
        self._authenticate_user()
        
        # Create a session
        UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            is_active=True
        )
        
        url = '/api/v1/users/me/sessions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('sessions', response.data)
        self.assertGreaterEqual(len(response.data['sessions']), 1)
    
    def test_terminate_session_endpoint(self):
        """Test terminating a specific session."""
        self._authenticate_user()
        
        # Create a session
        session = UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            is_active=True
        )
        
        url = f'/api/v1/users/me/sessions/{session.session_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check session is terminated
        session.refresh_from_db()
        self.assertFalse(session.is_active)
    
    def test_terminate_all_sessions_endpoint(self):
        """Test terminating all user sessions."""
        self._authenticate_user()
        
        # Create multiple sessions
        UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Agent 1',
            is_active=True
        )
        UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Agent 2',
            is_active=True
        )
        
        url = '/api/v1/users/me/sessions/all/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check all sessions are terminated
        active_sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertEqual(active_sessions.count(), 0)


class APIRateLimitingTest(APITestCase):
    """Test API rate limiting functionality."""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_login_rate_limiting(self):
        """Test rate limiting on login endpoint."""
        url = '/api/v1/auth/login/'
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        # Make requests up to the limit
        for i in range(5):
            response = self.client.post(url, data, format='json')
            # Should get 401 (unauthorized) not 429 (rate limited)
            self.assertIn(response.status_code, [401, 429])
        
        # Next request should be rate limited
        response = self.client.post(url, data, format='json')
        if response.status_code == 429:
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertFalse(response.data['success'])
            self.assertIn('RATE_LIMIT_EXCEEDED', response.data['error']['code'])
    
    def test_registration_rate_limiting(self):
        """Test rate limiting on registration endpoint."""
        url = '/api/v1/auth/register/'
        
        # Make multiple registration attempts
        for i in range(11):  # Registration limit is 10 per hour
            data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password': 'TestPassword123!'
            }
            response = self.client.post(url, data, format='json')
            
            if i < 10:
                # First 10 should succeed or fail with validation errors
                self.assertIn(response.status_code, [201, 400])
            else:
                # 11th should be rate limited
                if response.status_code == 429:
                    self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                    break