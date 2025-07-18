"""
Tests for authentication services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.authentication.services import AuthenticationService, UserProfileService
from apps.authentication.models import UserProfile, UserSession

User = get_user_model()


class AuthenticationServiceTest(TestCase):
    """Test cases for AuthenticationService."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_register_user(self):
        """Test user registration through service."""
        user, tokens = AuthenticationService.register_user(self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertTrue(hasattr(user, 'profile'))

    def test_register_user_with_profile_data(self):
        """Test user registration with profile data."""
        profile_data = {
            'alternate_phone': '+9876543210',
            'preferences': {'theme': 'dark'}
        }
        
        user, tokens = AuthenticationService.register_user(
            self.user_data, profile_data
        )
        
        self.assertEqual(user.profile.alternate_phone, '+9876543210')
        self.assertEqual(user.profile.preferences['theme'], 'dark')

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Create user first
        User.objects.create_user(**self.user_data)
        
        user, tokens = AuthenticationService.authenticate_user(
            'test@example.com', 'testpass123'
        )
        
        self.assertIsNotNone(user)
        self.assertIsNotNone(tokens)
        self.assertEqual(user.email, 'test@example.com')
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)

    def test_authenticate_user_failure(self):
        """Test failed user authentication."""
        # Create user first
        User.objects.create_user(**self.user_data)
        
        user, tokens = AuthenticationService.authenticate_user(
            'test@example.com', 'wrongpassword'
        )
        
        self.assertIsNone(user)
        self.assertIsNone(tokens)

    def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user."""
        user, tokens = AuthenticationService.authenticate_user(
            'nonexistent@example.com', 'testpass123'
        )
        
        self.assertIsNone(user)
        self.assertIsNone(tokens)

    def test_create_user_session(self):
        """Test creating user session."""
        user = User.objects.create_user(**self.user_data)
        request_data = {
            'session_key': 'test_session',
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Browser',
            'device_type': 'desktop'
        }
        
        session = AuthenticationService.create_user_session(user, request_data)
        
        self.assertIsNotNone(session)
        self.assertEqual(session.user, user)
        self.assertEqual(session.session_key, 'test_session')
        self.assertEqual(session.ip_address, '192.168.1.1')
        self.assertTrue(session.is_active)

    def test_deactivate_user_sessions(self):
        """Test deactivating user sessions."""
        user = User.objects.create_user(**self.user_data)
        
        # Create multiple sessions
        UserSession.objects.create(
            user=user, session_key='session1', ip_address='127.0.0.1',
            user_agent='Browser 1', is_active=True
        )
        UserSession.objects.create(
            user=user, session_key='session2', ip_address='127.0.0.1',
            user_agent='Browser 2', is_active=True
        )
        
        count = AuthenticationService.deactivate_user_sessions(user)
        
        self.assertEqual(count, 2)
        self.assertEqual(
            UserSession.objects.filter(user=user, is_active=True).count(), 0
        )

    def test_deactivate_user_sessions_exclude_one(self):
        """Test deactivating user sessions excluding one."""
        user = User.objects.create_user(**self.user_data)
        
        # Create multiple sessions
        UserSession.objects.create(
            user=user, session_key='session1', ip_address='127.0.0.1',
            user_agent='Browser 1', is_active=True
        )
        UserSession.objects.create(
            user=user, session_key='session2', ip_address='127.0.0.1',
            user_agent='Browser 2', is_active=True
        )
        
        count = AuthenticationService.deactivate_user_sessions(
            user, exclude_session_key='session1'
        )
        
        self.assertEqual(count, 1)
        self.assertEqual(
            UserSession.objects.filter(
                user=user, session_key='session1', is_active=True
            ).count(), 1
        )

    def test_change_password_success(self):
        """Test successful password change."""
        user = User.objects.create_user(**self.user_data)
        
        result = AuthenticationService.change_password(
            user, 'testpass123', 'newpass123'
        )
        
        self.assertTrue(result)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))

    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        user = User.objects.create_user(**self.user_data)
        
        with self.assertRaises(ValueError):
            AuthenticationService.change_password(
                user, 'wrongpass', 'newpass123'
            )

    def test_generate_password_reset_token(self):
        """Test generating password reset token."""
        user = User.objects.create_user(**self.user_data)
        
        returned_user, token, uid = AuthenticationService.generate_password_reset_token(
            'test@example.com'
        )
        
        self.assertEqual(returned_user, user)
        self.assertIsNotNone(token)
        self.assertIsNotNone(uid)

    def test_generate_password_reset_token_nonexistent_user(self):
        """Test generating password reset token for non-existent user."""
        user, token, uid = AuthenticationService.generate_password_reset_token(
            'nonexistent@example.com'
        )
        
        self.assertIsNone(user)
        self.assertIsNone(token)
        self.assertIsNone(uid)

    def test_verify_password_reset_token_success(self):
        """Test successful password reset token verification."""
        user = User.objects.create_user(**self.user_data)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verified_user = AuthenticationService.verify_password_reset_token(uid, token)
        
        self.assertEqual(verified_user, user)

    def test_verify_password_reset_token_invalid(self):
        """Test password reset token verification with invalid token."""
        user = User.objects.create_user(**self.user_data)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verified_user = AuthenticationService.verify_password_reset_token(
            uid, 'invalid_token'
        )
        
        self.assertIsNone(verified_user)

    def test_reset_password(self):
        """Test password reset."""
        user = User.objects.create_user(**self.user_data)
        
        result = AuthenticationService.reset_password(user, 'newpass123')
        
        self.assertTrue(result)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))

    def test_update_user_profile(self):
        """Test updating user profile."""
        user = User.objects.create_user(**self.user_data)
        
        user_data = {'first_name': 'Updated', 'bio': 'New bio'}
        profile_data = {'alternate_phone': '+9999999999'}
        
        updated_user = AuthenticationService.update_user_profile(
            user, user_data, profile_data
        )
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.bio, 'New bio')
        self.assertEqual(updated_user.profile.alternate_phone, '+9999999999')

    def test_verify_email(self):
        """Test email verification."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_email_verified)
        
        result = AuthenticationService.verify_email(user)
        
        self.assertTrue(result)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_verify_phone(self):
        """Test phone verification."""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_phone_verified)
        
        result = AuthenticationService.verify_phone(user)
        
        self.assertTrue(result)
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)

    def test_get_user_sessions(self):
        """Test getting user sessions."""
        user = User.objects.create_user(**self.user_data)
        
        # Create sessions
        UserSession.objects.create(
            user=user, session_key='session1', ip_address='127.0.0.1',
            user_agent='Browser 1', is_active=True
        )
        UserSession.objects.create(
            user=user, session_key='session2', ip_address='127.0.0.1',
            user_agent='Browser 2', is_active=False
        )
        
        # Get active sessions only
        active_sessions = AuthenticationService.get_user_sessions(user, active_only=True)
        self.assertEqual(active_sessions.count(), 1)
        
        # Get all sessions
        all_sessions = AuthenticationService.get_user_sessions(user, active_only=False)
        self.assertEqual(all_sessions.count(), 2)


class UserProfileServiceTest(TestCase):
    """Test cases for UserProfileService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_get_or_create_profile_create(self):
        """Test creating new profile."""
        profile = UserProfileService.get_or_create_profile(self.user)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.user)

    def test_get_or_create_profile_get_existing(self):
        """Test getting existing profile."""
        # Profile already exists from signal, just update it
        existing_profile = self.user.profile
        existing_profile.alternate_phone = '+1234567890'
        existing_profile.save()
        
        profile = UserProfileService.get_or_create_profile(self.user)
        
        self.assertEqual(profile, existing_profile)
        self.assertEqual(profile.alternate_phone, '+1234567890')

    def test_update_preferences(self):
        """Test updating user preferences."""
        preferences = {'theme': 'dark', 'language': 'en'}
        
        profile = UserProfileService.update_preferences(self.user, preferences)
        
        self.assertEqual(profile.preferences['theme'], 'dark')
        self.assertEqual(profile.preferences['language'], 'en')

    def test_update_preferences_merge(self):
        """Test updating preferences merges with existing."""
        # Create profile with existing preferences
        profile = UserProfile.objects.create(
            user=self.user,
            preferences={'theme': 'light', 'notifications': True}
        )
        
        new_preferences = {'theme': 'dark', 'language': 'en'}
        updated_profile = UserProfileService.update_preferences(
            self.user, new_preferences
        )
        
        self.assertEqual(updated_profile.preferences['theme'], 'dark')
        self.assertEqual(updated_profile.preferences['language'], 'en')
        self.assertTrue(updated_profile.preferences['notifications'])

    def test_update_privacy_settings(self):
        """Test updating privacy settings."""
        privacy_settings = {
            'profile_visibility': 'private',
            'newsletter_subscription': False,
            'sms_notifications': False,
            'email_notifications': True
        }
        
        profile = UserProfileService.update_privacy_settings(
            self.user, privacy_settings
        )
        
        self.assertEqual(profile.profile_visibility, 'private')
        
        # Check user fields were updated
        self.user.refresh_from_db()
        self.assertFalse(self.user.newsletter_subscription)
        self.assertFalse(self.user.sms_notifications)
        self.assertTrue(self.user.email_notifications)