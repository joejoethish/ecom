"""
Tests for authentication models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.authentication.models import User, UserProfile, UserSession

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+1234567890',
        }

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.user_type, 'customer')
        self.assertFalse(user.is_verified)
        self.assertFalse(user.is_phone_verified)
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.newsletter_subscription)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.user_type, 'customer')  # Default type

    def test_email_uniqueness(self):
        """Test that email must be unique."""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',  # Same email
                password='testpass123'
            )

    def test_username_field(self):
        """Test that email is used as username field."""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_full_name_property(self):
        """Test full_name property."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
        
        # Test with no first/last name
        user.first_name = ''
        user.last_name = ''
        user.save()
        self.assertEqual(user.full_name, 'testuser')

    def test_user_type_properties(self):
        """Test user type properties."""
        user = User.objects.create_user(**self.user_data)
        
        # Test customer
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_seller)
        self.assertFalse(user.is_admin_user)
        
        # Test seller
        user.user_type = 'seller'
        user.save()
        self.assertFalse(user.is_customer)
        self.assertTrue(user.is_seller)
        self.assertFalse(user.is_admin_user)
        
        # Test admin
        user.user_type = 'admin'
        user.save()
        self.assertFalse(user.is_customer)
        self.assertFalse(user.is_seller)
        self.assertTrue(user.is_admin_user)

    def test_get_avatar_url(self):
        """Test get_avatar_url method."""
        user = User.objects.create_user(**self.user_data)
        
        # Test without avatar
        self.assertEqual(user.get_avatar_url(), '/static/images/default-avatar.png')

    def test_phone_number_validation(self):
        """Test phone number validation."""
        # Valid phone numbers should work
        valid_phones = ['+1234567890', '1234567890', '+12345678901234']
        
        for i, phone in enumerate(valid_phones):
            user_data = self.user_data.copy()
            user_data['phone_number'] = phone
            user_data['email'] = f'test{i}@example.com'
            user_data['username'] = f'user{i}'
            
            user = User(**user_data)
            user.full_clean()  # This should not raise ValidationError

    def test_str_method(self):
        """Test string representation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_user_profile(self):
        """Test creating a user profile."""
        # Get the existing profile created by signal
        profile = self.user.profile
        
        # Update it with test data
        profile.alternate_phone = '+9876543210'
        profile.emergency_contact_name = 'Emergency Contact'
        profile.emergency_contact_phone = '+1111111111'
        profile.preferences = {'theme': 'dark', 'language': 'en'}
        profile.profile_visibility = 'public'
        profile.save()
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.alternate_phone, '+9876543210')
        self.assertEqual(profile.preferences['theme'], 'dark')
        self.assertEqual(profile.profile_visibility, 'public')

    def test_profile_str_method(self):
        """Test profile string representation."""
        profile = self.user.profile  # Use existing profile created by signal
        self.assertEqual(str(profile), 'test@example.com - Profile')

    def test_profile_defaults(self):
        """Test profile default values."""
        profile = self.user.profile  # Use existing profile created by signal
        
        self.assertEqual(profile.preferences, {})
        self.assertEqual(profile.profile_visibility, 'public')
        self.assertEqual(profile.alternate_phone, '')


class UserSessionModelTest(TestCase):
    """Test cases for UserSession model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_user_session(self):
        """Test creating a user session."""
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test Browser',
            device_type='desktop',
            location='Test City'
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.session_key, 'test_session_key')
        self.assertEqual(session.ip_address, '192.168.1.1')
        self.assertEqual(session.device_type, 'desktop')
        self.assertTrue(session.is_active)

    def test_session_str_method(self):
        """Test session string representation."""
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session_key_12345',
            ip_address='192.168.1.1',
            user_agent='Test Browser'
        )
        
        self.assertEqual(str(session), 'test@example.com - test_ses...')

    def test_session_defaults(self):
        """Test session default values."""
        session = UserSession.objects.create(
            user=self.user,
            session_key='test_session',
            ip_address='127.0.0.1',
            user_agent='Test'
        )
        
        self.assertTrue(session.is_active)
        self.assertEqual(session.device_type, '')
        self.assertEqual(session.location, '')