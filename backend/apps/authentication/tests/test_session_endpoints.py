"""
Tests for session management API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserSession
from apps.authentication.services import SessionManagementService

User = get_user_model()


class SessionManagementAPITestCase(TestCase):
    """Test case for session management API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            user_type='customer'
        )
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test sessions
        self.session1 = SessionManagementService.create_session(self.user, {
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'location': 'Test Location 1'
        })
        
        self.session2 = SessionManagementService.create_session(self.user, {
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            'location': 'Test Location 2'
        })
    
    def test_get_user_sessions(self):
        """Test GET /api/v1/auth/users/me/sessions/ endpoint."""
        url = reverse('user_session_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('sessions', data['data'])
        self.assertEqual(len(data['data']['sessions']), 2)
        
        # Check session data structure
        session_data = data['data']['sessions'][0]
        expected_fields = ['id', 'session_key', 'ip_address', 'user_agent', 
                          'device_info', 'location', 'is_active', 'last_activity', 
                          'created_at', 'device_name', 'login_method', 'is_current']
        
        for field in expected_fields:
            self.assertIn(field, session_data)
    
    def test_terminate_specific_session(self):
        """Test DELETE /api/v1/auth/users/me/sessions/{session_id}/ endpoint."""
        url = reverse('user_session_detail', kwargs={'session_id': self.session1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertEqual(data['data']['session_id'], self.session1.id)
        
        # Verify session was terminated
        self.session1.refresh_from_db()
        self.assertFalse(self.session1.is_active)
    
    def test_terminate_nonexistent_session(self):
        """Test terminating a non-existent session."""
        url = reverse('user_session_detail', kwargs={'session_id': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'SESSION_NOT_FOUND')
    
    def test_terminate_all_sessions(self):
        """Test DELETE /api/v1/auth/users/me/sessions/all/ endpoint."""
        url = reverse('user_session_terminate_all')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertIn('terminated_count', data['data'])
        
        # Verify sessions were terminated
        active_sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertEqual(active_sessions.count(), 0)
    
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access session endpoints."""
        self.client.credentials()  # Remove authentication
        
        # Test GET sessions
        url = reverse('user_session_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test DELETE specific session
        url = reverse('user_session_detail', kwargs={'session_id': self.session1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test DELETE all sessions
        url = reverse('user_session_terminate_all')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_session_belongs_to_user(self):
        """Test that users can only access their own sessions."""
        # Create another user and session
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123',
            user_type='customer'
        )
        
        other_session = SessionManagementService.create_session(other_user, {
            'ip_address': '10.0.0.1',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'location': 'Other Location'
        })
        
        # Try to access other user's session
        url = reverse('user_session_detail', kwargs={'session_id': other_session.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data['error']['code'], 'SESSION_NOT_FOUND')
        
        # Verify other user's session is still active
        other_session.refresh_from_db()
        self.assertTrue(other_session.is_active)