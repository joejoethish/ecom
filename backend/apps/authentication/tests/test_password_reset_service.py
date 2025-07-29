"""
Unit tests for PasswordResetService.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
from apps.authentication.services import PasswordResetService
import hashlib

User = get_user_model()


class PasswordResetServiceTest(TestCase):
    """Test cases for PasswordResetService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.ip_address = '192.168.1.1'
        self.user_agent = 'Test User Agent'
    
    def test_generate_reset_token(self):
        """Test token generation functionality."""
        raw_token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        # Verify token properties
        self.assertIsNotNone(raw_token)
        self.assertGreaterEqual(len(raw_token), 32)
        self.assertEqual(reset_token.user, self.user)
        self.assertEqual(reset_token.ip_address, self.ip_address)
        self.assertFalse(reset_token.is_used)
        self.assertFalse(reset_token.is_expired)
        
        # Verify token hash
        expected_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        self.assertEqual(reset_token.token_hash, expected_hash)
    
    def test_validate_reset_token(self):
        """Test token validation functionality."""
        raw_token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address=self.ip_address
        )
        
        # Valid token should pass validation
        validated_token, error = PasswordResetService.validate_reset_token(raw_token)
        self.assertIsNotNone(validated_token)
        self.assertIsNone(error)
        self.assertEqual(validated_token.id, reset_token.id)
        
        # Invalid token should fail validation
        invalid_token, error = PasswordResetService.validate_reset_token('invalid_token')
        self.assertIsNone(invalid_token)
        self.assertIsNotNone(error)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        test_ip = '192.168.1.100'
        
        # Should be allowed initially
        allowed, count = PasswordResetService.check_rate_limit(test_ip)
        self.assertTrue(allowed)
        
        # Create 5 attempts to hit the limit
        for i in range(5):
            PasswordResetService.log_reset_attempt(
                ip_address=test_ip,
                email='test@example.com',
                success=False
            )
        
        # Should be blocked now
        allowed, count = PasswordResetService.check_rate_limit(test_ip)
        self.assertFalse(allowed)
        self.assertGreaterEqual(count, 5)
    
    def test_password_reset(self):
        """Test password reset functionality."""
        raw_token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address=self.ip_address
        )
        
        old_password_hash = self.user.password
        new_password = 'newpassword123'
        
        success, message = PasswordResetService.reset_password(
            token=raw_token,
            new_password=new_password,
            ip_address=self.ip_address
        )
        
        self.assertTrue(success)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.password, old_password_hash)
        self.assertTrue(self.user.check_password(new_password))
        
        # Token should be invalidated
        reset_token.refresh_from_db()
        self.assertTrue(reset_token.is_used)
    
    def test_token_invalidation_after_use(self):
        """Test that tokens are invalidated after use."""
        raw_token, reset_token = PasswordResetService.generate_reset_token(
            user=self.user,
            ip_address=self.ip_address
        )
        
        # Use the token
        PasswordResetService.reset_password(
            token=raw_token,
            new_password='newpassword123',
            ip_address=self.ip_address
        )
        
        # Try to use the same token again
        success, message = PasswordResetService.reset_password(
            token=raw_token,
            new_password='anothernewpassword',
            ip_address=self.ip_address
        )
        self.assertFalse(success)
    
    def test_request_password_reset_flow(self):
        """Test complete password reset request flow."""
        success, message, token = PasswordResetService.request_password_reset(
            email=self.user.email,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(token)
    
    def test_nonexistent_email_protection(self):
        """Test email enumeration protection."""
        success, message, token = PasswordResetService.request_password_reset(
            email='nonexistent@example.com',
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        # Should still return success to prevent enumeration
        self.assertTrue(success)
        self.assertIsNone(token)
    
    def test_constant_time_compare(self):
        """Test constant-time comparison functionality."""
        token1 = "test_token_123"
        token2 = "test_token_123"
        token3 = "different_token"
        
        self.assertTrue(PasswordResetService._constant_time_compare(token1, token2))
        self.assertFalse(PasswordResetService._constant_time_compare(token1, token3))
    
    def test_cleanup_expired_tokens(self):
        """Test expired token cleanup."""
        # Create an expired token
        expired_token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=timezone.now() - timedelta(hours=2),
            ip_address=self.ip_address
        )
        
        cleaned_count = PasswordResetService.cleanup_expired_tokens()
        self.assertGreaterEqual(cleaned_count, 1)
        
        # Verify token was deleted
        self.assertFalse(
            PasswordResetToken.objects.filter(id=expired_token.id).exists()
        )
    
    def test_cleanup_old_attempts(self):
        """Test old attempt cleanup."""
        # Create an old attempt
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address=self.ip_address,
            email='test@example.com',
            success=False
        )
        # Manually set old date
        old_attempt.created_at = timezone.now() - timedelta(days=31)
        old_attempt.save()
        
        cleaned_count = PasswordResetService.cleanup_old_attempts(days_old=30)
        self.assertGreaterEqual(cleaned_count, 1)
        
        # Verify attempt was deleted
        self.assertFalse(
            PasswordResetAttempt.objects.filter(id=old_attempt.id).exists()
        )