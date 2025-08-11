# Security vulnerability testing
import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from unittest.mock import patch, Mock
import re
import time
from django.conf import settings

User = get_user_model()

class BaseSecurityTestCase(APITestCase):
    """Base class for security tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin_security',
            email='admin@security.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='user_security',
            email='user@security.com',
            password='testpass123'
        )
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def authenticate_user(self):
        """Authenticate as regular user"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

class AuthenticationSecurityTest(BaseSecurityTestCase):
    """Test authentication security"""
    
    def test_password_strength_requirements(self):
        """Test password strength requirements"""
        weak_passwords = [
            '123',
            'password',
            '12345678',
            'qwerty',
            'admin',
            'test'
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                'username': f'test_user_{weak_password}',
                'email': f'test_{weak_password}@test.com',
                'password': weak_password
            }
            
            response = self.client.post('/api/admin/users/', user_data, format='json')
            # Should reject weak passwords
            self.assertIn(response.status_code, [400, 422], 
                         f"Weak password '{weak_password}' was accepted")
    
    def test_brute_force_protection(self):
        """Test brute force attack protection"""
        login_url = '/api/admin/auth/login/'
        
        # Attempt multiple failed logins
        for i in range(10):
            response = self.client.post(login_url, {
                'username': 'admin_security',
                'password': 'wrongpassword'
            }, format='json')
            
            if i >= 5:  # After 5 attempts, should be rate limited
                self.assertIn(response.status_code, [429, 423], 
                             f"No rate limiting after {i+1} failed attempts")
    
    def test_session_timeout(self):
        """Test session timeout"""
        self.authenticate_admin()
        
        # Make a request to verify authentication works
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        
        # Simulate session timeout by manipulating token
        expired_token = 'expired.token.here'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, 401)

class AuthorizationSecurityTest(BaseSecurityTestCase):
    """Test authorization and access control"""
    
    def test_unauthorized_access_prevention(self):
        """Test that unauthorized users cannot access admin endpoints"""
        # Test without authentication
        protected_endpoints = [
            '/api/admin/products/',
            '/api/admin/orders/',
            '/api/admin/users/',
            '/api/admin/settings/',
            '/api/admin/dashboard/stats/'
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 401, 
                           f"Unauthorized access allowed to {endpoint}")
    
    def test_privilege_escalation_prevention(self):
        """Test prevention of privilege escalation"""
        self.authenticate_user()  # Regular user, not admin
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            '/api/admin/settings/',
            '/api/admin/users/',
            '/api/admin/system/logs/'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403, 
                           f"Privilege escalation possible at {endpoint}")

class InputValidationSecurityTest(BaseSecurityTestCase):
    """Test input validation security"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        self.authenticate_admin()
        
        # SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE products; --",
            "' OR '1'='1",
            "'; INSERT INTO users (username) VALUES ('hacker'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET is_superuser=1; --"
        ]
        
        for payload in sql_payloads:
            # Test in search parameter
            response = self.client.get(f'/api/admin/products/?search={payload}')
            self.assertIn(response.status_code, [200, 400], 
                         f"SQL injection may be possible with payload: {payload}")
    
    def test_xss_prevention(self):
        """Test XSS (Cross-Site Scripting) prevention"""
        self.authenticate_admin()
        
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src="x" onerror="alert(1)">',
            'javascript:alert("xss")',
            '<svg onload="alert(1)">',
            '"><script>alert("xss")</script>',
            '<iframe src="javascript:alert(1)"></iframe>'
        ]
        
        for payload in xss_payloads:
            product_data = {
                'name': payload,
                'description': f'Description with {payload}',
                'price': '99.99',
                'sku': f'XSS-TEST-{hash(payload) % 1000:03d}'
            }
            
            response = self.client.post('/api/admin/products/', product_data, format='json')
            
            if response.status_code == 201:
                # Verify XSS payload was sanitized
                self.assertNotIn('<script>', response.data.get('name', ''))
                self.assertNotIn('javascript:', response.data.get('name', ''))
                self.assertNotIn('onerror=', response.data.get('description', ''))

class DataSecurityTest(BaseSecurityTestCase):
    """Test data security and privacy"""
    
    def test_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed"""
        self.authenticate_admin()
        
        # Get user data
        response = self.client.get(f'/api/admin/users/{self.admin_user.id}/')
        self.assertEqual(response.status_code, 200)
        
        # Password should not be in response
        response_text = json.dumps(response.data)
        self.assertNotIn('password', response_text.lower())
        self.assertNotIn('testpass123', response_text)
    
    def test_secure_data_transmission(self):
        """Test secure data transmission"""
        # Test HTTPS enforcement
        if hasattr(settings, 'SECURE_SSL_REDIRECT'):
            self.assertTrue(settings.SECURE_SSL_REDIRECT, 
                           "HTTPS redirect should be enabled in production")
        
        # Test secure headers
        response = self.client.get('/api/admin/dashboard/stats/')
        
        # Check for security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
        }
        
        for header, expected_value in security_headers.items():
            self.assertIn(header, response, f"Missing security header: {header}")

@pytest.mark.security
class PytestSecurityTest:
    """Pytest-based security tests"""
    
    def test_security_headers(self, client):
        """Test security headers"""
        response = client.get('/api/admin/login/')
        
        expected_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
        }
        
        for header, expected_value in expected_headers.items():
            assert header in response, f"Missing security header: {header}"
    
    def test_authentication_required(self, api_client):
        """Test authentication requirements"""
        protected_endpoints = [
            '/api/admin/products/',
            '/api/admin/orders/',
            '/api/admin/users/',
        ]
        
        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"