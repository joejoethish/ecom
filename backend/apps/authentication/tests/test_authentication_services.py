"""
Comprehensive tests for authentication services.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from apps.authentication.services import (
    AuthenticationService, EmailVerificationService, 
    PasswordResetService, SessionManagementService
)
from apps.authentication.models import (
    EmailVerification, PasswordReset, UserSession,
    PasswordResetAttempt, EmailVerificationAttempt
)

User = get_user_model()


class AuthenticationServiceTest(TestCase):
    """Test authentication service functionality."""
    
    def setUp(self):
        self.service = AuthenticationService()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        cache.clear()
    
    def test_register_user_success(self):
        """Test successful user registration."""
        result = self.service.register_user(self.user_data)
        
        self.assertTrue(result['success'])
        self.assertIn('user', result)
        self.assertIn('tokens', result)
        
        # Check user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_email_verified)
    
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        User.objects.create_user(**self.user_data)
        
        # Try to register with same email
        result = self.service.register_user(self.user_data)
        
        self.assertFalse(result['success'])
        self.assertIn('email', result['errors'])
    
    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username."""
        # Create first user
        User.objects.create_user(**self.user_data)
        
        # Try to register with same username but different email
        new_data = self.user_data.copy()
        new_data['email'] = 'different@example.com'
        result = self.service.register_user(new_data)
        
        self.assertFalse(result['success'])
        self.assertIn('username', result['errors'])
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Create and verify user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        result = self.service.authenticate_user('test@example.com', 'TestPassword123!')
        
        self.assertTrue(result['success'])
        self.assertIn('user', result)
        self.assertIn('tokens', result)
        self.assertEqual(result['user']['email'], 'test@example.com')
    
    def test_authenticate_user_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        # Create user
        User.objects.create_user(**self.user_data)
        
        result = self.service.authenticate_user('test@example.com', 'wrongpassword')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Invalid email or password')
    
    def test_authenticate_user_unverified_email(self):
        """Test authentication with unverified email."""
        # Create user (email not verified by default)
        User.objects.create_user(**self.user_data)
        
        result = self.service.authenticate_user('test@example.com', 'TestPassword123!')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Email not verified')
    
    def test_authenticate_user_locked_account(self):
        """Test authentication with locked account."""
        # Create and lock user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.lock_account()
        
        result = self.service.authenticate_user('test@example.com', 'TestPassword123!')
        
        self.assertFalse(result['success'])
        self.assertIn('locked', result['error'].lower())
    
    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Create and authenticate user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        auth_result = self.service.authenticate_user('test@example.com', 'TestPassword123!')
        refresh_token = auth_result['tokens']['refresh']
        
        result = self.service.refresh_token(refresh_token)
        
        self.assertTrue(result['success'])
        self.assertIn('tokens', result)
    
    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        result = self.service.refresh_token('invalid_token')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid', result['error'])


class EmailVerificationServiceTest(TestCase):
    """Test email verification service functionality."""
    
    def setUp(self):
        self.service = EmailVerificationService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    @patch('apps.authentication.services.send_mail')
    def test_send_verification_email_success(self, mock_send_mail):
        """Test successful verification email sending."""
        result = self.service.send_verification_email(self.user.email)
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        
        # Check verification record was created
        verification = EmailVerification.objects.get(user=self.user)
        self.assertIsNotNone(verification.token)
        self.assertFalse(verification.is_used)
        
        # Check email was sent
        mock_send_mail.assert_called_once()
    
    def test_send_verification_email_nonexistent_user(self):
        """Test verification email for non-existent user."""
        result = self.service.send_verification_email('nonexistent@example.com')
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
    
    def test_send_verification_email_already_verified(self):
        """Test verification email for already verified user."""
        self.user.is_email_verified = True
        self.user.save()
        
        result = self.service.send_verification_email(self.user.email)
        
        self.assertFalse(result['success'])
        self.assertIn('already verified', result['error'])
    
    def test_verify_email_success(self):
        """Test successful email verification."""
        # Create verification token
        verification = EmailVerification.objects.create(user=self.user)
        
        result = self.service.verify_email(verification.token)
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        
        # Check user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        
        # Check verification is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token."""
        result = self.service.verify_email('invalid_token')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid', result['error'])
    
    def test_verify_email_expired_token(self):
        """Test email verification with expired token."""
        # Create expired verification
        verification = EmailVerification.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        result = self.service.verify_email(verification.token)
        
        self.assertFalse(result['success'])
        self.assertIn('expired', result['error'])
    
    def test_verify_email_used_token(self):
        """Test email verification with already used token."""
        # Create and use verification
        verification = EmailVerification.objects.create(user=self.user)
        verification.is_used = True
        verification.save()
        
        result = self.service.verify_email(verification.token)
        
        self.assertFalse(result['success'])
        self.assertIn('already been used', result['error'])


class PasswordResetServiceTest(TestCase):
    """Test password reset service functionality."""
    
    def setUp(self):
        self.service = PasswordResetService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    @patch('apps.authentication.services.send_mail')
    def test_request_password_reset_success(self, mock_send_mail):
        """Test successful password reset request."""
        result = self.service.request_password_reset('test@example.com')
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        
        # Check reset record was created
        reset = PasswordReset.objects.get(user=self.user)
        self.assertIsNotNone(reset.token)
        self.assertFalse(reset.is_used)
        
        # Check email was sent
        mock_send_mail.assert_called_once()
    
    def test_request_password_reset_nonexistent_user(self):
        """Test password reset for non-existent user."""
        result = self.service.request_password_reset('nonexistent@example.com')
        
        # Should still return success for security (don't reveal if email exists)
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        
        # But no reset record should be created
        self.assertEqual(PasswordReset.objects.count(), 0)
    
    def test_confirm_password_reset_success(self):
        """Test successful password reset confirmation."""
        # Create reset token
        reset = PasswordReset.objects.create(user=self.user)
        new_password = 'NewPassword123!'
        
        result = self.service.confirm_password_reset(reset.token, new_password)
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        
        # Check reset is marked as used
        reset.refresh_from_db()
        self.assertTrue(reset.is_used)
    
    def test_confirm_password_reset_invalid_token(self):
        """Test password reset with invalid token."""
        result = self.service.confirm_password_reset('invalid_token', 'NewPassword123!')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid', result['error'])
    
    def test_confirm_password_reset_expired_token(self):
        """Test password reset with expired token."""
        # Create expired reset
        reset = PasswordReset.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        result = self.service.confirm_password_reset(reset.token, 'NewPassword123!')
        
        self.assertFalse(result['success'])
        self.assertIn('expired', result['error'])
    
    def test_confirm_password_reset_weak_password(self):
        """Test password reset with weak password."""
        reset = PasswordReset.objects.create(user=self.user)
        
        result = self.service.confirm_password_reset(reset.token, 'weak')
        
        self.assertFalse(result['success'])
        self.assertIn('password', result['errors'])


class SessionManagementServiceTest(TestCase):
    """Test session management service functionality."""
    
    def setUp(self):
        self.service = SessionManagementService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    def test_create_session_success(self):
        """Test successful session creation."""
        session_data = {
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Agent',
            'device_info': 'Test Device'
        }
        
        result = self.service.create_session(self.user, session_data)
        
        self.assertTrue(result['success'])
        self.assertIn('session', result)
        
        # Check session was created
        session = UserSession.objects.get(user=self.user)
        self.assertEqual(session.ip_address, '192.168.1.1')
        self.assertTrue(session.is_active)
    
    def test_get_user_sessions(self):
        """Test retrieving user sessions."""
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
            is_active=False
        )
        
        result = self.service.get_user_sessions(self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['sessions']), 2)
    
    def test_terminate_session_success(self):
        """Test successful session termination."""
        # Create session
        session = UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            is_active=True
        )
        
        result = self.service.terminate_session(self.user, session.session_id)
        
        self.assertTrue(result['success'])
        
        # Check session is inactive
        session.refresh_from_db()
        self.assertFalse(session.is_active)
    
    def test_terminate_session_invalid_id(self):
        """Test terminating non-existent session."""
        result = self.service.terminate_session(self.user, 'invalid_id')
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
    
    def test_terminate_all_sessions(self):
        """Test terminating all user sessions."""
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
        
        result = self.service.terminate_all_sessions(self.user)
        
        self.assertTrue(result['success'])
        
        # Check all sessions are inactive
        active_sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertEqual(active_sessions.count(), 0)
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        # Create expired session
        UserSession.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            is_active=False,
            last_activity=timezone.now() - timedelta(days=31)
        )
        
        result = self.service.cleanup_expired_sessions()
        
        self.assertTrue(result['success'])
        self.assertGreater(result['cleaned_count'], 0)
        
        # Check session was deleted
        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 0)


class AuthenticationIntegrationTest(TestCase):
    """Test integration of all authentication services."""
    
    def setUp(self):
        self.auth_service = AuthenticationService()
        self.email_service = EmailVerificationService()
        self.password_service = PasswordResetService()
        self.session_service = SessionManagementService()
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        cache.clear()
    
    @patch('apps.authentication.services.send_mail')
    def test_complete_registration_flow(self, mock_send_mail):
        """Test complete user registration and verification flow."""
        # 1. Register user
        register_result = self.auth_service.register_user(self.user_data)
        self.assertTrue(register_result['success'])
        
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_email_verified)
        
        # 2. Send verification email
        email_result = self.email_service.send_verification_email(user.email)
        self.assertTrue(email_result['success'])
        
        # 3. Verify email
        verification = EmailVerification.objects.get(user=user)
        verify_result = self.email_service.verify_email(verification.token)
        self.assertTrue(verify_result['success'])
        
        # 4. Login after verification
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        login_result = self.auth_service.authenticate_user('test@example.com', 'TestPassword123!')
        self.assertTrue(login_result['success'])
    
    @patch('apps.authentication.services.send_mail')
    def test_complete_password_reset_flow(self, mock_send_mail):
        """Test complete password reset flow."""
        # 1. Create and verify user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        # 2. Request password reset
        reset_result = self.password_service.request_password_reset(user.email)
        self.assertTrue(reset_result['success'])
        
        # 3. Confirm password reset
        reset = PasswordReset.objects.get(user=user)
        new_password = 'NewPassword123!'
        confirm_result = self.password_service.confirm_password_reset(reset.token, new_password)
        self.assertTrue(confirm_result['success'])
        
        # 4. Login with new password
        login_result = self.auth_service.authenticate_user(user.email, new_password)
        self.assertTrue(login_result['success'])
        
        # 5. Old password should not work
        old_login_result = self.auth_service.authenticate_user(user.email, 'TestPassword123!')
        self.assertFalse(old_login_result['success'])
    
    def test_session_management_flow(self):
        """Test complete session management flow."""
        # 1. Create user
        user = User.objects.create_user(**self.user_data)
        user.is_email_verified = True
        user.save()
        
        # 2. Create session
        session_data = {
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Agent',
            'device_info': 'Test Device'
        }
        session_result = self.session_service.create_session(user, session_data)
        self.assertTrue(session_result['success'])
        
        # 3. Get sessions
        sessions_result = self.session_service.get_user_sessions(user)
        self.assertTrue(sessions_result['success'])
        self.assertEqual(len(sessions_result['sessions']), 1)
        
        # 4. Terminate session
        session_id = sessions_result['sessions'][0]['session_id']
        terminate_result = self.session_service.terminate_session(user, session_id)
        self.assertTrue(terminate_result['success'])
        
        # 5. Verify session is terminated
        sessions_result = self.session_service.get_user_sessions(user)
        active_sessions = [s for s in sessions_result['sessions'] if s['is_active']]
        self.assertEqual(len(active_sessions), 0)