"""
Tests for authentication serializers.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.authentication.serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer,
    UserProfileSerializer
)
from apps.authentication.models import UserProfile

User = get_user_model()


class UserRegistrationSerializerTest(TestCase):
    """Test cases for UserRegistrationSerializer."""

    def setUp(self):
        """Set up test data."""
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123!',
            'password_confirm': 'testpass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'customer',
            'phone_number': '+1234567890',
        }

    def test_valid_registration_data(self):
        """Test serializer with valid registration data."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test validation when passwords don't match."""
        data = self.valid_data.copy()
        data['password_confirm'] = 'differentpass'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_email(self):
        """Test validation with duplicate email."""
        # Create a user first
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_duplicate_username(self):
        """Test validation with duplicate username."""
        # Create a user first
        User.objects.create_user(
            username='testuser',
            email='other@example.com',
            password='pass123'
        )
        
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_create_user(self):
        """Test creating user through serializer."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123!'))
        self.assertTrue(hasattr(user, 'profile'))

    def test_create_user_with_profile_data(self):
        """Test creating user with profile data."""
        data = self.valid_data.copy()
        data['profile'] = {
            'alternate_phone': '+9876543210',
            'preferences': {'theme': 'dark'}
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.profile.alternate_phone, '+9876543210')
        self.assertEqual(user.profile.preferences['theme'], 'dark')

    def test_weak_password_validation(self):
        """Test password validation with weak password."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password_confirm'] = '123'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890'
        )
        # UserProfile is automatically created by signal, just update it
        self.user.profile.alternate_phone = '+9876543210'
        self.user.profile.save()

    def test_serialize_user(self):
        """Test serializing user data."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['user_type'], 'customer')
        self.assertIn('profile', data)
        self.assertIn('avatar_url', data)

    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated."""
        serializer = UserSerializer(self.user)
        
        # These fields should be in read_only_fields
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_verified',
            'is_phone_verified', 'is_email_verified'
        ]
        
        for field in read_only_fields:
            self.assertIn(field, serializer.Meta.read_only_fields)


class UserUpdateSerializerTest(TestCase):
    """Test cases for UserUpdateSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_update_user_basic_fields(self):
        """Test updating basic user fields."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+9999999999',
            'bio': 'Updated bio'
        }
        
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.phone_number, '+9999999999')
        self.assertEqual(updated_user.bio, 'Updated bio')

    def test_update_user_with_profile(self):
        """Test updating user with profile data."""
        data = {
            'first_name': 'Updated',
            'profile': {
                'alternate_phone': '+1111111111',
                'preferences': {'theme': 'light'}
            }
        }
        
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.profile.alternate_phone, '+1111111111')
        self.assertEqual(updated_user.profile.preferences['theme'], 'light')


class PasswordChangeSerializerTest(TestCase):
    """Test cases for PasswordChangeSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.factory = APIRequestFactory()

    def test_valid_password_change(self):
        """Test valid password change data."""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        
        serializer = PasswordChangeSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())

    def test_incorrect_old_password(self):
        """Test with incorrect old password."""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123!',
            'new_password_confirm': 'newpass123!'
        }
        
        serializer = PasswordChangeSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_new_password_mismatch(self):
        """Test when new passwords don't match."""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123!',
            'new_password_confirm': 'differentpass!'
        }
        
        serializer = PasswordChangeSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class PasswordResetRequestSerializerTest(TestCase):
    """Test cases for PasswordResetRequestSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_email(self):
        """Test with valid email."""
        data = {'email': 'test@example.com'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_nonexistent_email(self):
        """Test with non-existent email."""
        data = {'email': 'nonexistent@example.com'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_invalid_email_format(self):
        """Test with invalid email format."""
        data = {'email': 'invalid-email'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class UserProfileSerializerTest(TestCase):
    """Test cases for UserProfileSerializer."""

    def test_serialize_profile(self):
        """Test serializing profile data."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # UserProfile is automatically created by signal, just update it
        profile = user.profile
        profile.alternate_phone = '+9876543210'
        profile.preferences = {'theme': 'dark'}
        profile.profile_visibility = 'private'
        profile.save()
        
        serializer = UserProfileSerializer(profile)
        data = serializer.data
        
        self.assertEqual(data['alternate_phone'], '+9876543210')
        self.assertEqual(data['preferences']['theme'], 'dark')
        self.assertEqual(data['profile_visibility'], 'private')

    def test_profile_fields(self):
        """Test that all expected fields are included."""
        serializer = UserProfileSerializer()
        expected_fields = [
            'alternate_phone', 'emergency_contact_name', 'emergency_contact_phone',
            'preferences', 'facebook_url', 'twitter_url', 'instagram_url',
            'linkedin_url', 'profile_visibility'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.fields)