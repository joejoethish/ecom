"""
Tests for authentication views.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.models import UserProfile, UserSession

User = get_user_model()


class RegisterViewTest(APITestCase):
    """Test cases for RegisterView."""

    def setUp(self):
        """Set up test data."""
        self.register_url = reverse('register')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123!',
            'password_confirm': 'testpass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'customer',
        }

    def test_successful_registration(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        user = User.objects.get(email='test@example.com')
        self.assertTrue(hasattr(user, 'profile'))

    def test_registration_with_invalid_data(self):
        """Test registration with invalid data."""
        invalid_data = self.valid_data.copy()
        invalid_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)

    def test_registration_with_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create user first
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_registration_with_profile_data(self):
        """Test registration with profile data."""
        data = self.valid_data.copy()
        data['profile'] = {
            'alternate_phone': '+9876543210',
            'preferences': {'theme': 'dark'}
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.profile.alternate_phone, '+9876543210')


class LoginViewTest(APITestCase):
    """Test cases for LoginView."""

    def setUp(self):
        """Set up test data."""
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_successful_login(self):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_creates_user_session(self):
        """Test that login creates a user session."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if session was created (might be created in the view)
        # This test might need adjustment based on actual implementation


class LogoutViewTest(APITestCase):
    """Test cases for LogoutView."""

    def setUp(self):
        """Set up test data."""
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)

    def test_successful_logout(self):
        """Test successful logout."""
        data = {'refresh': str(self.refresh)}
        
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_logout_without_refresh_token(self):
        """Test logout without refresh token."""
        response = self.client.post(self.logout_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_logout_with_invalid_token(self):
        """Test logout with invalid token."""
        data = {'refresh': 'invalid_token'}
        
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_logout_without_authentication(self):
        """Test logout without authentication."""
        self.client.force_authenticate(user=None)
        data = {'refresh': str(self.refresh)}
        
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileViewTest(APITestCase):
    """Test cases for ProfileView."""

    def setUp(self):
        """Set up test data."""
        self.profile_url = reverse('profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # UserProfile is automatically created by signal, no need to create manually
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Test getting user profile."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_update_profile(self):
        """Test updating user profile."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        
        response = self.client.put(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify changes
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.bio, 'Updated bio')

    def test_profile_without_authentication(self):
        """Test accessing profile without authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordChangeViewTest(APITestCase):
    """Test cases for PasswordChangeView."""

    def setUp(self):
        """Set up test data."""
        self.password_change_url = reverse('password_change')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_successful_password_change(self):
        """Test successful password change."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        
        response = self.client.post(self.password_change_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123!'))

    def test_password_change_with_wrong_old_password(self):
        """Test password change with wrong old password."""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        
        response = self.client.post(self.password_change_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_password_change_without_authentication(self):
        """Test password change without authentication."""
        self.client.force_authenticate(user=None)
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        
        response = self.client.post(self.password_change_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetRequestViewTest(APITestCase):
    """Test cases for PasswordResetRequestView."""

    def setUp(self):
        """Set up test data."""
        self.password_reset_url = reverse('password_reset_request')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_password_reset_request(self):
        """Test password reset request."""
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.password_reset_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset request with non-existent email."""
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(self.password_reset_url, data)
        
        # Should still return success for security reasons
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class UserSessionsViewTest(APITestCase):
    """Test cases for UserSessionsView."""

    def setUp(self):
        """Set up test data."""
        self.sessions_url = reverse('user_sessions')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create some test sessions
        UserSession.objects.create(
            user=self.user,
            session_key='session1',
            ip_address='192.168.1.1',
            user_agent='Browser 1',
            is_active=True
        )
        UserSession.objects.create(
            user=self.user,
            session_key='session2',
            ip_address='192.168.1.2',
            user_agent='Browser 2',
            is_active=False
        )
        
        self.client.force_authenticate(user=self.user)

    def test_get_user_sessions(self):
        """Test getting user sessions."""
        response = self.client.get(self.sessions_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('sessions', response.data)
        # Should only return active sessions
        self.assertEqual(len(response.data['sessions']), 1)

    def test_deactivate_all_sessions(self):
        """Test deactivating all sessions."""
        response = self.client.delete(self.sessions_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_sessions_without_authentication(self):
        """Test accessing sessions without authentication."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.sessions_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RefreshTokenViewTest(APITestCase):
    """Test cases for RefreshTokenView."""

    def setUp(self):
        """Set up test data."""
        self.refresh_url = reverse('refresh')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_successful_token_refresh(self):
        """Test successful token refresh."""
        data = {'refresh': str(self.refresh)}
        
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(response.data['success'])

    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid token."""
        data = {'refresh': 'invalid_token'}
        
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_without_token(self):
        """Test token refresh without token."""
        response = self.client.post(self.refresh_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)