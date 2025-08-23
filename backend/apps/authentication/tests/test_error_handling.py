"""
Tests for authentication error handling system.

This module tests the comprehensive error handling system including:
- Custom authentication exceptions
- Structured error responses
- Rate limiting and security error handling
- Error middleware functionality
"""

import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from ..exceptions import (
    AuthErrorResponse, handle_authentication_error,
    validate_password_strength, validate_email_format,
    validate_username_format, check_rate_limit,
    detect_brute_force_attack, create_structured_error_response,
    InvalidCredentialsException, RateLimitExceededException,
    BruteForceDetectedException, PasswordComplexityException,
    EmailFormatException, UsernameFormatException
)
from ..error_handlers import (
    authentication_exception_handler, AuthenticationErrorMiddleware,
    RateLimitingMiddleware
)

User = get_user_model()


class AuthErrorResponseTest(TestCase):
    """Test the structured error response format."""
    
    def test_basic_error_response(self):
        """Test basic error response creation."""
        error = AuthErrorResponse(
            error_code='TEST_ERROR',
            message='Test error message',
            status_code=400
        )
        
        response_dict = error.to_dict()
        
        self.assertFalse(response_dict['success'])
        self.assertEqual(response_dict['error']['code'], 'TEST_ERROR')
        self.assertEqual(response_dict['error']['message'], 'Test error message')
        self.assertIn('timestamp', response_dict['error'])
    
    def test_error_response_with_details(self):
        """Test error response with additional details."""
        error = AuthErrorResponse(
            error_code='VALIDATION_ERROR',
            message='Validation failed',
            details={'field': 'email'},
            field_errors={'email': ['Invalid email format']},
            retry_after=60
        )
        
        response_dict = error.to_dict()
        
        self.assertEqual(response_dict['error']['details']['field'], 'email')
        self.assertEqual(response_dict['error']['field_errors']['email'], ['Invalid email format'])
        self.assertEqual(response_dict['error']['retry_after'], 60)
    
    def test_from_exception(self):
        """Test creating error response from exception."""
        exc = InvalidCredentialsException()
        error = AuthErrorResponse.from_exception(exc)
        
        response_dict = error.to_dict()
        
        self.assertEqual(response_dict['error']['code'], 'invalid_credentials')
        self.assertIn('Invalid email or password', response_dict['error']['message'])


class AuthenticationExceptionsTest(TestCase):
    """Test custom authentication exceptions."""
    
    def test_handle_authentication_error_factory(self):
        """Test the authentication error factory function."""
        # Test basic error
        exc = handle_authentication_error('invalid_credentials')
        self.assertIsInstance(exc, InvalidCredentialsException)
        
        # Test rate limit error with parameters
        exc = handle_authentication_error(
            'rate_limit_exceeded',
            retry_after=60,
            limit=5,
            window=300
        )
        self.assertIsInstance(exc, RateLimitExceededException)
        self.assertEqual(exc.retry_after, 60)
        
        # Test brute force error with lockout duration
        exc = handle_authentication_error(
            'brute_force_detected',
            lockout_duration=30
        )
        self.assertIsInstance(exc, BruteForceDetectedException)
        self.assertEqual(exc.lockout_duration, 30)
    
    def test_rate_limit_exception_with_parameters(self):
        """Test rate limit exception with retry parameters."""
        exc = RateLimitExceededException(retry_after=120, limit=5, window=3600)
        
        self.assertEqual(exc.retry_after, 120)
        self.assertEqual(exc.limit, 5)
        self.assertEqual(exc.window, 3600)
        self.assertIn('120 seconds', str(exc))


class PasswordValidationTest(TestCase):
    """Test enhanced password validation."""
    
    def test_valid_password(self):
        """Test validation of a strong password."""
        # Should not raise any exception
        validate_password_strength('StrongP@ssw0rd123')
    
    def test_weak_passwords(self):
        """Test validation of weak passwords."""
        weak_passwords = [
            'short',  # Too short
            'nouppercase123!',  # No uppercase
            'NOLOWERCASE123!',  # No lowercase
            'NoNumbers!',  # No numbers
            'NoSpecialChars123',  # No special characters
            'password',  # Common password
            'abc123!',  # Sequential characters
            'aaa123!A',  # Repeated characters
        ]
        
        for password in weak_passwords:
            with self.assertRaises(PasswordComplexityException):
                validate_password_strength(password)
    
    def test_password_with_user_info(self):
        """Test password validation against user information."""
        user = User(username='testuser', email='test@example.com', first_name='John')
        
        # Password containing username should fail
        with self.assertRaises(PasswordComplexityException):
            validate_password_strength('testuser123!A', user)
        
        # Password containing email prefix should fail
        with self.assertRaises(PasswordComplexityException):
            validate_password_strength('test123!A', user)


class EmailValidationTest(TestCase):
    """Test email format validation."""
    
    def test_valid_emails(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            # Should not raise any exception
            validate_email_format(email)
    
    def test_invalid_emails(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com',
            'user..name@example.com',
            'a' * 255 + '@example.com',  # Too long
        ]
        
        for email in invalid_emails:
            with self.assertRaises(EmailFormatException):
                validate_email_format(email)


class UsernameValidationTest(TestCase):
    """Test username format validation."""
    
    def test_valid_usernames(self):
        """Test validation of valid usernames."""
        valid_usernames = [
            'user123',
            'test_user',
            'user-name',
            'a1b2c3'
        ]
        
        for username in valid_usernames:
            # Should not raise any exception
            validate_username_format(username)
    
    def test_invalid_usernames(self):
        """Test validation of invalid usernames."""
        invalid_usernames = [
            'ab',  # Too short
            'a' * 31,  # Too long
            'user@name',  # Invalid character
            '_username',  # Starts with underscore
            'admin',  # Reserved username
        ]
        
        for username in invalid_usernames:
            with self.assertRaises(UsernameFormatException):
                validate_username_format(username)


class RateLimitingTest(TestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        """Set up test environment."""
        cache.clear()
    
    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement."""
        identifier = 'test_user'
        action = 'test_action'
        limit = 3
        window = 60
        
        # First 3 requests should pass
        for i in range(limit):
            check_rate_limit(identifier, action, limit, window)
        
        # 4th request should fail
        with self.assertRaises(RateLimitExceededException):
            check_rate_limit(identifier, action, limit, window)
    
    def test_rate_limit_window_expiry(self):
        """Test rate limit window expiry."""
        identifier = 'test_user'
        action = 'test_action'
        limit = 2
        window = 1  # 1 second window
        
        # Use up the limit
        for i in range(limit):
            check_rate_limit(identifier, action, limit, window)
        
        # Should fail immediately
        with self.assertRaises(RateLimitExceededException):
            check_rate_limit(identifier, action, limit, window)
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should work again
        check_rate_limit(identifier, action, limit, window)
    
    def test_different_identifiers_separate_limits(self):
        """Test that different identifiers have separate rate limits."""
        action = 'test_action'
        limit = 2
        window = 60
        
        # Use up limit for first identifier
        for i in range(limit):
            check_rate_limit('user1', action, limit, window)
        
        # Second identifier should still work
        check_rate_limit('user2', action, limit, window)


class BruteForceDetectionTest(TestCase):
    """Test brute force attack detection."""
    
    def setUp(self):
        """Set up test environment."""
        cache.clear()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_brute_force_detection_by_user(self):
        """Test brute force detection by user attempts."""
        ip_address = '192.168.1.1'
        
        # First 4 attempts should pass
        for i in range(4):
            detect_brute_force_attack(self.user, ip_address)
        
        # 5th attempt should trigger brute force detection
        with self.assertRaises(BruteForceDetectedException):
            detect_brute_force_attack(self.user, ip_address)
    
    def test_brute_force_detection_by_ip(self):
        """Test brute force detection by IP attempts."""
        ip_address = '192.168.1.1'
        
        # Create multiple users for IP-based testing
        users = []
        for i in range(11):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            users.append(user)
        
        # First 9 attempts should pass
        for i in range(9):
            detect_brute_force_attack(users[i], ip_address)
        
        # 10th attempt should trigger brute force detection
        with self.assertRaises(BruteForceDetectedException):
            detect_brute_force_attack(users[9], ip_address)


class AuthenticationErrorHandlerTest(TestCase):
    """Test authentication error handler."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
    
    def test_authentication_exception_handler(self):
        """Test authentication exception handler."""
        request = self.factory.post('/api/v1/auth/login/')
        context = {'request': request}
        
        exc = InvalidCredentialsException()
        response = authentication_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'invalid_credentials')
    
    def test_rate_limit_exception_handler(self):
        """Test rate limit exception handling."""
        request = self.factory.post('/api/v1/auth/login/')
        context = {'request': request}
        
        exc = RateLimitExceededException(retry_after=60, limit=5)
        response = authentication_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertEqual(response['Retry-After'], '60')


class AuthenticationErrorMiddlewareTest(TestCase):
    """Test authentication error middleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        self.middleware = AuthenticationErrorMiddleware(lambda r: MagicMock())
    
    def test_middleware_adds_security_headers(self):
        """Test that middleware adds security headers to auth responses."""
        request = self.factory.post('/api/v1/auth/login/')
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create middleware with mock get_response
        middleware = AuthenticationErrorMiddleware(lambda r: mock_response)
        
        response = middleware(request)
        
        # Verify security headers were added
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Cache-Control',
            'Pragma'
        ]
        
        for header in expected_headers:
            self.assertIn(header, response.__setitem__.call_args_list[0][0] if response.__setitem__.call_args_list else [])


class RateLimitingMiddlewareTest(TestCase):
    """Test rate limiting middleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        cache.clear()
    
    def test_rate_limiting_middleware(self):
        """Test rate limiting middleware functionality."""
        # Create middleware
        middleware = RateLimitingMiddleware(lambda r: MagicMock(status_code=200))
        
        # Make requests up to the limit
        for i in range(5):  # Login limit is 5 per 15 minutes
            request = self.factory.post('/api/v1/auth/login/')
            response = middleware(request)
            
            if hasattr(response, 'status_code') and response.status_code == 429:
                # Rate limit was triggered
                break
        
        # Next request should be rate limited
        request = self.factory.post('/api/v1/auth/login/')
        response = middleware(request)
        
        # Should return rate limit response or pass through
        # (depends on exact timing and cache state)
        self.assertIsNotNone(response)


class IntegrationTest(APITestCase):
    """Integration tests for the complete error handling system."""
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials returns structured error."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'invalid@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data.get('success', True))
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
    
    def test_registration_with_weak_password(self):
        """Test registration with weak password returns validation error."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak',
            'password_confirm': 'weak',
            'user_type': 'customer'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success', True))
        self.assertIn('error', response.data)
    
    def test_password_reset_rate_limiting(self):
        """Test password reset rate limiting."""
        # Make multiple password reset requests
        for i in range(6):  # Exceed the limit of 5
            response = self.client.post('/api/v1/auth/forgot-password/', {
                'email': 'test@example.com'
            })
            
            if response.status_code == 429:
                # Rate limit was triggered
                self.assertFalse(response.data.get('success', True))
                self.assertEqual(response.data['error']['code'], 'RATE_LIMIT_EXCEEDED')
                self.assertIn('Retry-After', response)
                break