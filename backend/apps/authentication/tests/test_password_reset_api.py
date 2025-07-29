"""
Test cases for password reset API endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
import json

from apps.authentication.models import User, PasswordResetToken, PasswordResetAttempt
from apps.authentication.services import PasswordResetService

User = get_user_model()


class PasswordResetAPITestCase(TestCase):
    """Test cases for password reset API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

    def test_forgot_password_api_valid_email(self):
        """Test forgot password API with valid email."""
        url = reverse('forgot_password_api')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('reset link has been sent', response_data['message'])

    def test_forgot_password_api_invalid_email_format(self):
        """Test forgot password API with invalid email format."""
        url = reverse('forgot_password_api')
        data = {'email': 'invalid-email'}
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')

    def test_forgot_password_api_nonexistent_email(self):
        """Test forgot password API with non-existent email (should still return success)."""
        url = reverse('forgot_password_api')
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        # Should return success to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])

    def test_validate_reset_token_api_valid_token(self):
        """Test validate reset token API with valid token."""
        # Generate a valid token
        token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        
        url = reverse('validate_reset_token_api', kwargs={'token': token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['data']['valid'])
        self.assertFalse(response_data['data']['expired'])

    def test_validate_reset_token_api_invalid_token(self):
        """Test validate reset token API with invalid token."""
        url = reverse('validate_reset_token_api', kwargs={'token': 'invalid-token'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertFalse(response_data['data']['valid'])
        self.assertEqual(response_data['error']['code'], 'TOKEN_INVALID')

    def test_reset_password_api_valid_token(self):
        """Test reset password API with valid token."""
        # Generate a valid token
        token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        
        url = reverse('reset_password_api')
        data = {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('successfully', response_data['message'])

    def test_reset_password_api_password_mismatch(self):
        """Test reset password API with password mismatch."""
        # Generate a valid token
        token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        
        url = reverse('reset_password_api')
        data = {
            'token': token,
            'password': 'password123',
            'password_confirm': 'differentpassword123'
        }
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')

    def test_reset_password_api_token_reuse(self):
        """Test that tokens cannot be reused."""
        # Generate a valid token
        token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        
        url = reverse('reset_password_api')
        data = {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        # First use should succeed
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second use should fail
        data['password'] = 'anotherpassword123'
        data['password_confirm'] = 'anotherpassword123'
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error']['code'], 'TOKEN_USED')

    def test_reset_password_api_invalid_token(self):
        """Test reset password API with invalid token."""
        url = reverse('reset_password_api')
        data = {
            'token': 'invalid-token',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error']['code'], 'TOKEN_INVALID')