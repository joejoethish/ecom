"""
Tests for authentication security middleware.
"""
import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.authentication.middleware import (
    AuthenticationRateLimitMiddleware,
    AccountLockoutMiddleware,
    IPSecurityMonitoringMiddleware,
    SecurityHeadersMiddleware
)
from apps.authentication.models import PasswordResetAttempt, EmailVerificationAttempt

User = get_user_model()


class AuthenticationRateLimitMiddlewareTest(TestCase):
    """Test authentication rate limiting middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuthenticationRateLimitMiddleware(lambda request: MagicMock(status_code=200))
        cache.clear()
    
    def test_login_rate_limiting(self):
        """Test rate limiting for login endpoint."""
        # Create multiple requests from same IP
        for i in range(6):  # Exceed the limit of 5
            request = self.factory.post(
                '/api/v1/auth/login/',
                data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.1'
            )
            response = self.middleware(request)
            
            if i < 5:  # First 5 should pass
                self.assertEqual(response.status_code, 200)
            else:  # 6th should be rate limited
                self.assertEqual(response.status_code, 429)
                response_data = json.loads(response.content)
                self.assertEqual(response_data['error']['code'], 'RATE_LIMIT_EXCEEDED')
    
    def test_different_endpoints_different_limits(self):
        """Test that different endpoints have different rate limits."""
        # Test login endpoint (5 requests limit)
        for i in range(5):
            request = self.factory.post(
                '/api/v1/auth/login/',
                data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.1'
            )
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
        
        # Test register endpoint (10 requests limit) - should still work
        request = self.factory.post(
            '/api/v1/auth/register/',
            data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.1'
        )
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
    
    def test_different_ips_separate_limits(self):
        """Test that different IPs have separate rate limits."""
        # Exhaust limit for first IP
        for i in range(5):
            request = self.factory.post(
                '/api/v1/auth/login/',
                data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.1'
            )
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
        
        # Request from different IP should still work
        request = self.factory.post(
            '/api/v1/auth/login/',
            data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.2'
        )
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are added to responses."""
        request = self.factory.post(
            '/api/v1/auth/login/',
            data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.1'
        )
        response = self.middleware(request)
        
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)
        self.assertIn('X-RateLimit-Reset', response)
        self.assertIn('X-RateLimit-Type', response)


class AccountLockoutMiddlewareTest(TestCase):
    """Test account lockout middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    def test_account_lockout_after_failed_attempts(self):
        """Test that account gets locked after max failed attempts."""
        # Mock response that indicates failed login
        def mock_response(request):
            response = MagicMock()
            response.status_code = 401
            response._container = [json.dumps({'error': 'Invalid credentials'}).encode('utf-8')]
            return response
        
        middleware = AccountLockoutMiddleware(mock_response)
        
        # Make 5 failed login attempts
        for i in range(5):
            request = self.factory.post(
                '/api/v1/auth/login/',
                data=json.dumps({'email': 'test@example.com', 'password': 'wrongpassword'}),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.1'
            )
            response = middleware(request)
            
            # Refresh user from database
            self.user.refresh_from_db()
            
            if i < 4:  # First 4 attempts
                self.assertFalse(self.user.is_account_locked)
                self.assertEqual(response.status_code, 401)
            else:  # 5th attempt should lock account
                self.assertTrue(self.user.is_account_locked)
                self.assertEqual(response.status_code, 423)
    
    def test_locked_account_prevents_login(self):
        """Test that locked account prevents further login attempts."""
        # Lock the account
        self.user.lock_account()
        
        def mock_response(request):
            return MagicMock(status_code=200)
        
        middleware = AccountLockoutMiddleware(mock_response)
        
        request = self.factory.post(
            '/api/v1/auth/login/',
            data=json.dumps({'email': 'test@example.com', 'password': 'testpassword'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.1'
        )
        response = middleware(request)
        
        self.assertEqual(response.status_code, 423)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error']['code'], 'ACCOUNT_LOCKED')
    
    def test_successful_login_resets_failed_attempts(self):
        """Test that successful login resets failed attempt counter."""
        # Set some failed attempts
        self.user.failed_login_attempts = 3
        self.user.save()
        
        def mock_response(request):
            return MagicMock(status_code=200)
        
        middleware = AccountLockoutMiddleware(mock_response)
        
        request = self.factory.post(
            '/api/v1/auth/login/',
            data=json.dumps({'email': 'test@example.com', 'password': 'testpassword'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.1'
        )
        middleware(request)
        
        # Check that failed attempts were reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)


class IPSecurityMonitoringMiddlewareTest(TestCase):
    """Test IP security monitoring middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = IPSecurityMonitoringMiddleware(lambda request: MagicMock(status_code=200))
        cache.clear()
    
    @patch('apps.authentication.middleware.logger')
    def test_high_request_rate_detection(self, mock_logger):
        """Test detection of high request rates from single IP."""
        # Make 31 requests in quick succession (threshold is 30)
        for i in range(31):
            request = self.factory.get('/api/v1/auth/login/', REMOTE_ADDR='192.168.1.1')
            self.middleware(request)
        
        # Check that suspicious activity was logged
        mock_logger.critical.assert_called()
        call_args = mock_logger.critical.call_args[0][0]
        self.assertIn('HIGH_REQUEST_RATE', call_args)
        self.assertIn('192.168.1.1', call_args)
    
    @patch('apps.authentication.middleware.logger')
    def test_failed_auth_attempts_detection(self, mock_logger):
        """Test detection of multiple failed authentication attempts."""
        # Make 11 failed authentication requests (threshold is 10)
        for i in range(11):
            request = self.factory.post('/api/v1/auth/login/', REMOTE_ADDR='192.168.1.1')
            # Mock failed response
            response = MagicMock()
            response.status_code = 401
            self.middleware._analyze_response_patterns(request, response)
        
        # Check that suspicious activity was logged
        mock_logger.critical.assert_called()
        call_args = mock_logger.critical.call_args[0][0]
        self.assertIn('BRUTE_FORCE_ATTEMPT', call_args)
        self.assertIn('192.168.1.1', call_args)


class SecurityHeadersMiddlewareTest(TestCase):
    """Test security headers middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(lambda request: MagicMock(status_code=200))
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        request = self.factory.get('/api/v1/auth/login/')
        response = self.middleware(request)
        
        # Check that security headers are present
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'X-Permitted-Cross-Domain-Policies',
            'Cache-Control',
            'Pragma',
            'Expires'
        ]
        
        for header in expected_headers:
            self.assertIn(header, response)
    
    def test_authentication_specific_headers(self):
        """Test that authentication-specific headers are added."""
        request = self.factory.post('/api/v1/auth/login/')
        response = self.middleware(request)
        
        # Check authentication-specific headers
        self.assertIn('X-Security-Timestamp', response)
        self.assertIn('X-Request-ID', response)
        
        # Check that cache control is more restrictive for auth endpoints
        self.assertIn('private', response['Cache-Control'])
    
    def test_rate_limit_headers_preserved(self):
        """Test that rate limit headers are preserved."""
        request = self.factory.post('/api/v1/auth/login/')
        request.rate_limit_headers = {
            'X-RateLimit-Limit': '5',
            'X-RateLimit-Remaining': '4'
        }
        
        response = self.middleware(request)
        
        self.assertEqual(response['X-RateLimit-Limit'], '5')
        self.assertEqual(response['X-RateLimit-Remaining'], '4')


class MiddlewareIntegrationTest(TestCase):
    """Test integration of all middleware components."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    def test_middleware_chain_integration(self):
        """Test that all middleware components work together."""
        # Create middleware chain
        def base_response(request):
            return MagicMock(status_code=401)  # Simulate failed login
        
        # Chain middleware in reverse order (as Django does)
        response_handler = SecurityHeadersMiddleware(base_response)
        response_handler = IPSecurityMonitoringMiddleware(response_handler)
        response_handler = AccountLockoutMiddleware(response_handler)
        response_handler = AuthenticationRateLimitMiddleware(response_handler)
        
        # Make a request that should trigger multiple middleware
        request = self.factory.post(
            '/api/v1/auth/login/',
            data=json.dumps({'email': 'test@example.com', 'password': 'wrongpassword'}),
            content_type='application/json',
            REMOTE_ADDR='192.168.1.1'
        )
        
        response = response_handler(request)
        
        # Should have security headers
        self.assertIn('X-Content-Type-Options', response)
        
        # Should have rate limit headers
        self.assertIn('X-RateLimit-Limit', response)
        
        # Should process the request (not rate limited on first attempt)
        self.assertEqual(response.status_code, 401)
    
    def test_rate_limit_overrides_other_processing(self):
        """Test that rate limiting prevents other middleware processing."""
        def base_response(request):
            return MagicMock(status_code=200)
        
        middleware = AuthenticationRateLimitMiddleware(base_response)
        
        # Exhaust rate limit
        for i in range(6):
            request = self.factory.post(
                '/api/v1/auth/login/',
                data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.1'
            )
            response = middleware(request)
            
            if i >= 5:  # Should be rate limited
                self.assertEqual(response.status_code, 429)
                # Should not reach base response handler
                break