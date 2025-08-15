"""
Tests for admin authentication functionality.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.authentication.services import AuthenticationService

User = get_user_model()


class AdminAuthenticationTestCase(TestCase):
    """Test cases for admin authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='AdminPass123!',
            user_type='admin',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='UserPass123!',
            user_type='customer'
        )

    def test_admin_login_success(self):
        """Test successful admin login."""
        url = reverse('admin_login')
        data = {
            'email': 'admin@test.com',
            'password': 'AdminPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('user', response.data['data'])

    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials."""
        url = reverse('admin_login')
        data = {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'INVALID_ADMIN_CREDENTIALS')

    def test_regular_user_admin_login_denied(self):
        """Test that regular users cannot use admin login."""
        url = reverse('admin_login')
        data = {
            'email': 'user@test.com',
            'password': 'UserPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'ACCESS_DENIED')

    def test_admin_service_authenticate_success(self):
        """Test admin authentication service method."""
        request_data = {
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Agent'
        }
        
        user, tokens = AuthenticationService.authenticate_admin_user(
            email='admin@test.com',
            password='AdminPass123!',
            request_data=request_data
        )
        
        self.assertIsNotNone(user)
        self.assertIsNotNone(tokens)
        self.assertEqual(user.email, 'admin@test.com')
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)

    def test_admin_service_authenticate_non_admin(self):
        """Test admin authentication service rejects non-admin users."""
        request_data = {
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Agent'
        }
        
        with self.assertRaises(Exception) as context:
            AuthenticationService.authenticate_admin_user(
                email='user@test.com',
                password='UserPass123!',
                request_data=request_data
            )
        
        self.assertIn('Not admin user', str(context.exception))

    def test_admin_logout_success(self):
        """Test admin logout functionality."""
        # First login to get tokens
        user, tokens = AuthenticationService.authenticate_admin_user(
            email='admin@test.com',
            password='AdminPass123!',
            request_data={'ip_address': '127.0.0.1'}
        )
        
        # Test logout
        success, message = AuthenticationService.logout_admin_user(
            user=user,
            refresh_token=tokens['refresh']
        )
        
        self.assertTrue(success)
        self.assertIn('terminated successfully', message)

    def test_admin_token_refresh_success(self):
        """Test admin token refresh functionality."""
        # First login to get tokens
        user, tokens = AuthenticationService.authenticate_admin_user(
            email='admin@test.com',
            password='AdminPass123!',
            request_data={'ip_address': '127.0.0.1'}
        )
        
        # Test token refresh
        new_tokens = AuthenticationService.refresh_admin_token(tokens['refresh'])
        
        self.assertIsNotNone(new_tokens)
        self.assertIn('access', new_tokens)
        self.assertIn('refresh', new_tokens)