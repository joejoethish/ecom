"""
Tests for user management CRUD operations.
"""
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import UserSession, UserProfile

User = get_user_model()


class UserManagementTestCase(TestCase):
    """Test case for user management CRUD operations."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123',
            user_type='customer'
        )
        
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            user_type='customer'
        )
        
        # Create admin tokens
        self.admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_access_token = str(self.admin_refresh.access_token)
        
        # Create regular user tokens
        self.user_refresh = RefreshToken.for_user(self.regular_user)
        self.user_access_token = str(self.user_refresh.access_token)

    def authenticate_admin(self):
        """Authenticate as admin user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_access_token}')

    def authenticate_user(self):
        """Authenticate as regular user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_access_token}')

    def test_list_users_as_admin(self):
        """Test listing users as admin."""
        self.authenticate_admin()
        
        url = reverse('user_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('users', response.data['data'])
        self.assertIn('pagination', response.data['data'])
        
        # Should return all users
        users = response.data['data']['users']
        self.assertEqual(len(users), 3)  # admin, regular_user, test_user

    def test_list_users_as_regular_user(self):
        """Test listing users as regular user (should be denied)."""
        self.authenticate_user()
        
        url = reverse('user_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'PERMISSION_DENIED')

    def test_list_users_with_filters(self):
        """Test listing users with filters."""
        self.authenticate_admin()
        
        url = reverse('user_management')
        
        # Filter by user type
        response = self.client.get(url, {'user_type': 'customer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data['data']['users']
        self.assertEqual(len(users), 2)  # regular_user and test_user
        
        # Filter by search
        response = self.client.get(url, {'search': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data['data']['users']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['email'], 'admin@test.com')

    def test_create_user_as_admin(self):
        """Test creating user as admin."""
        self.authenticate_admin()
        
        url = reverse('user_management')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'customer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data['data'])
        
        # Verify user was created
        new_user = User.objects.get(email='newuser@test.com')
        self.assertEqual(new_user.username, 'newuser')
        self.assertEqual(new_user.user_type, 'customer')

    def test_create_user_as_regular_user(self):
        """Test creating user as regular user (should be denied)."""
        self.authenticate_user()
        
        url = reverse('user_management')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'user_type': 'customer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_user_detail_as_admin(self):
        """Test getting user detail as admin."""
        self.authenticate_admin()
        
        url = reverse('user_detail', kwargs={'user_id': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], 'testuser@test.com')

    def test_get_user_detail_as_regular_user(self):
        """Test getting user detail as regular user (should be denied)."""
        self.authenticate_user()
        
        url = reverse('user_detail', kwargs={'user_id': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_as_admin(self):
        """Test updating user as admin."""
        self.authenticate_admin()
        
        url = reverse('user_detail', kwargs={'user_id': self.test_user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user was updated
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, 'Updated')
        self.assertEqual(self.test_user.last_name, 'Name')

    def test_delete_user_as_admin(self):
        """Test deleting user as admin."""
        self.authenticate_admin()
        
        url = reverse('user_detail', kwargs={'user_id': self.test_user.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user was deleted
        self.assertFalse(User.objects.filter(id=self.test_user.id).exists())

    def test_delete_self_as_admin(self):
        """Test admin trying to delete their own account (should be denied)."""
        self.authenticate_admin()
        
        url = reverse('user_detail', kwargs={'user_id': self.admin_user.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'SELF_DELETION_DENIED')

    def test_get_current_user_profile(self):
        """Test getting current user profile."""
        self.authenticate_user()
        
        url = reverse('user_self_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], 'user@test.com')

    def test_update_current_user_profile(self):
        """Test updating current user profile."""
        self.authenticate_user()
        
        url = reverse('user_self_management')
        data = {
            'first_name': 'Updated',
            'bio': 'Updated bio'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user was updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        self.assertEqual(self.regular_user.bio, 'Updated bio')

    def test_delete_current_user_account(self):
        """Test deleting current user account."""
        self.authenticate_user()
        
        url = reverse('user_self_management')
        data = {
            'password': 'testpass123',
            'confirm_deletion': True
        }
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user was deleted
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

    def test_delete_current_user_account_wrong_password(self):
        """Test deleting current user account with wrong password."""
        self.authenticate_user()
        
        url = reverse('user_self_management')
        data = {
            'password': 'wrongpassword',
            'confirm_deletion': True
        }
        
        response = self.client.delete(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_list_user_sessions(self):
        """Test listing user sessions."""
        self.authenticate_user()
        
        # Create a test session
        UserSession.objects.create(
            user=self.regular_user,
            session_key='test_session_123',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            device_info={'browser': 'Chrome', 'os': 'Windows'},
            is_active=True
        )
        
        url = reverse('user_session_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('sessions', response.data['data'])
        self.assertEqual(len(response.data['data']['sessions']), 1)

    def test_terminate_all_sessions(self):
        """Test terminating all user sessions."""
        self.authenticate_user()
        
        # Create test sessions
        session1 = UserSession.objects.create(
            user=self.regular_user,
            session_key='test_session_1',
            ip_address='127.0.0.1',
            user_agent='Test Agent 1',
            device_info={'browser': 'Chrome', 'os': 'Windows'},
            is_active=True
        )
        session2 = UserSession.objects.create(
            user=self.regular_user,
            session_key='test_session_2',
            ip_address='127.0.0.2',
            user_agent='Test Agent 2',
            device_info={'browser': 'Firefox', 'os': 'Mac'},
            is_active=True
        )
        
        url = reverse('user_session_management')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify sessions were terminated
        session1.refresh_from_db()
        session2.refresh_from_db()
        self.assertFalse(session1.is_active)
        self.assertFalse(session2.is_active)

    def test_terminate_specific_session(self):
        """Test terminating specific user session."""
        self.authenticate_user()
        
        # Create test session
        session = UserSession.objects.create(
            user=self.regular_user,
            session_key='test_session_123',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            device_info={'browser': 'Chrome', 'os': 'Windows'},
            is_active=True
        )
        
        url = reverse('user_session_detail', kwargs={'session_id': session.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify session was terminated
        session.refresh_from_db()
        self.assertFalse(session.is_active)

    def test_terminate_nonexistent_session(self):
        """Test terminating nonexistent session."""
        self.authenticate_user()
        
        url = reverse('user_session_detail', kwargs={'session_id': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'SESSION_NOT_FOUND')

    def test_unauthenticated_access(self):
        """Test unauthenticated access to user management endpoints."""
        # Test user list
        url = reverse('user_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test user detail
        url = reverse('user_detail', kwargs={'user_id': self.test_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test current user profile
        url = reverse('user_self_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test sessions
        url = reverse('user_session_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)