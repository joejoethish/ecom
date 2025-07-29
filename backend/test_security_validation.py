#!/usr/bin/env python
"""
Test script for comprehensive input validation and security enhancements.
This script validates Task 5 implementation:
- Email format validation on forgot password endpoint
- Password strength validation for reset endpoint
- CSRF protection for all password reset forms
- Rate limiting middleware for password reset endpoints
"""
import os
import sys
import django
import time
import json
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
from apps.authentication.services import PasswordResetService

User = get_user_model()


def test_email_validation():
    """Test enhanced email format validation."""
    print("1. Testing Enhanced Email Format Validation...")
    
    client = Client()
    forgot_password_url = reverse('forgot_password_api')
    
    # Test cases for email validation
    test_cases = [
        # Valid emails
        ('test@example.com', True, 'Valid email'),
        ('user.name@domain.co.uk', True, 'Valid email with subdomain'),
        
        # Invalid emails - format issues
        ('', False, 'Empty email'),
        ('   ', False, 'Whitespace only'),
        ('invalid-email', False, 'Missing @ symbol'),
        ('user@', False, 'Missing domain'),
        ('@domain.com', False, 'Missing local part'),
        ('user@domain', False, 'Invalid domain format'),
        
        # Security-related invalid emails
        ('user<script>@domain.com', False, 'HTML injection attempt'),
        ('user@domain.com\r\nBCC: evil@hacker.com', False, 'CRLF injection'),
        ('javascript:alert(1)@domain.com', False, 'JavaScript injection'),
        ('data:text/html,<script>alert(1)</script>@domain.com', False, 'Data URI injection'),
        
        # Length validation
        ('a' * 250 + '@domain.com', False, 'Email too long'),
        ('user@' + 'a' * 250 + '.com', False, 'Domain too long'),
    ]
    
    for email, should_pass, description in test_cases:
        print(f"   Testing: {description}")
        
        # Get CSRF token first
        csrf_response = client.get(reverse('csrf_token'))
        csrf_token = csrf_response.json().get('csrf_token')
        
        response = client.post(
            forgot_password_url,
            {'email': email},
            HTTP_X_CSRFTOKEN=csrf_token,
            content_type='application/json'
        )
        
        if should_pass:
            # Valid emails should return 200 (even if user doesn't exist)
            assert response.status_code == 200, f"Valid email failed: {email}"
            print(f"     ✓ {description} - Passed")
        else:
            # Invalid emails should return 400
            assert response.status_code == 400, f"Invalid email accepted: {email}"
            response_data = response.json()
            assert not response_data.get('success', True), f"Invalid email marked as success: {email}"
            print(f"     ✓ {description} - Correctly rejected")
    
    print("   ✓ Email validation tests completed\n")


def test_password_strength_validation():
    """Test enhanced password strength validation."""
    print("2. Testing Enhanced Password Strength Validation...")
    
    # Create a test user and token
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='oldpassword123'
    )
    
    token, reset_token = PasswordResetService.generate_reset_token(
        user=user,
        ip_address='127.0.0.1'
    )
    
    client = Client()
    reset_password_url = reverse('reset_password_api')
    
    # Test cases for password validation
    test_cases = [
        # Valid passwords
        ('ValidPass123!', 'ValidPass123!', True, 'Strong password'),
        ('MySecure@Pass1', 'MySecure@Pass1', True, 'Another strong password'),
        
        # Invalid passwords - strength issues
        ('weak', 'weak', False, 'Too short'),
        ('password', 'password', False, 'No uppercase, numbers, or special chars'),
        ('PASSWORD123', 'PASSWORD123', False, 'No lowercase or special chars'),
        ('Password123', 'Password123', False, 'No special characters'),
        ('Password!', 'Password!', False, 'No numbers'),
        ('password123!', 'password123!', False, 'No uppercase'),
        ('PASSWORD!', 'PASSWORD!', False, 'No lowercase or numbers'),
        
        # Weak patterns
        ('Password111!', 'Password111!', False, 'Consecutive identical characters'),
        ('Password123!', 'Password123!', False, 'Sequential numbers'),
        ('Qwerty123!', 'Qwerty123!', False, 'Common weak pattern'),
        ('Admin123!', 'Admin123!', False, 'Common weak word'),
        
        # Password confirmation mismatch
        ('ValidPass123!', 'DifferentPass123!', False, 'Password mismatch'),
        ('ValidPass123!', '', False, 'Empty confirmation'),
        
        # Length limits
        ('a' * 130 + 'A1!', 'a' * 130 + 'A1!', False, 'Password too long'),
        ('', '', False, 'Empty password'),
        ('   ', '   ', False, 'Whitespace only password'),
    ]
    
    for password, confirm, should_pass, description in test_cases:
        print(f"   Testing: {description}")
        
        # Generate new token for each test
        new_token, _ = PasswordResetService.generate_reset_token(
            user=user,
            ip_address='127.0.0.1'
        )
        
        # Get CSRF token
        csrf_response = client.get(reverse('csrf_token'))
        csrf_token = csrf_response.json().get('csrf_token')
        
        response = client.post(
            reset_password_url,
            {
                'token': new_token,
                'password': password,
                'password_confirm': confirm
            },
            HTTP_X_CSRFTOKEN=csrf_token,
            content_type='application/json'
        )
        
        if should_pass:
            assert response.status_code == 200, f"Valid password failed: {description}"
            print(f"     ✓ {description} - Passed")
        else:
            assert response.status_code == 400, f"Invalid password accepted: {description}"
            response_data = response.json()
            assert not response_data.get('success', True), f"Invalid password marked as success: {description}"
            print(f"     ✓ {description} - Correctly rejected")
    
    # Cleanup
    user.delete()
    print("   ✓ Password strength validation tests completed\n")


def test_csrf_protection():
    """Test CSRF protection on password reset forms."""
    print("3. Testing CSRF Protection...")
    
    client = Client()
    forgot_password_url = reverse('forgot_password_api')
    reset_password_url = reverse('reset_password_api')
    csrf_token_url = reverse('csrf_token')
    
    # Test CSRF token endpoint
    print("   Testing CSRF token endpoint...")
    csrf_response = client.get(csrf_token_url)
    assert csrf_response.status_code == 200, "CSRF token endpoint failed"
    csrf_data = csrf_response.json()
    assert csrf_data.get('success'), "CSRF token response not successful"
    assert 'csrf_token' in csrf_data, "CSRF token not in response"
    print("     ✓ CSRF token endpoint working")
    
    csrf_token = csrf_data['csrf_token']
    
    # Test forgot password with CSRF token
    print("   Testing forgot password with CSRF token...")
    response = client.post(
        forgot_password_url,
        {'email': 'test@example.com'},
        HTTP_X_CSRFTOKEN=csrf_token,
        content_type='application/json'
    )
    assert response.status_code == 200, "Forgot password with CSRF token failed"
    print("     ✓ Forgot password with CSRF token working")
    
    # Test forgot password without CSRF token (should fail)
    print("   Testing forgot password without CSRF token...")
    client_no_csrf = Client(enforce_csrf_checks=True)
    response = client_no_csrf.post(
        forgot_password_url,
        {'email': 'test@example.com'},
        content_type='application/json'
    )
    assert response.status_code == 403, "Forgot password without CSRF token should fail"
    print("     ✓ Forgot password correctly rejected without CSRF token")
    
    # Test reset password with CSRF token
    print("   Testing reset password with CSRF token...")
    user = User.objects.create_user(
        username='csrftest',
        email='csrf@example.com',
        password='oldpass123'
    )
    token, _ = PasswordResetService.generate_reset_token(
        user=user,
        ip_address='127.0.0.1'
    )
    
    response = client.post(
        reset_password_url,
        {
            'token': token,
            'password': 'NewSecure123!',
            'password_confirm': 'NewSecure123!'
        },
        HTTP_X_CSRFTOKEN=csrf_token,
        content_type='application/json'
    )
    assert response.status_code == 200, "Reset password with CSRF token failed"
    print("     ✓ Reset password with CSRF token working")
    
    # Cleanup
    user.delete()
    print("   ✓ CSRF protection tests completed\n")


def test_rate_limiting():
    """Test rate limiting middleware for password reset endpoints."""
    print("4. Testing Rate Limiting Middleware...")
    
    client = Client()
    forgot_password_url = reverse('forgot_password_api')
    
    # Get CSRF token
    csrf_response = client.get(reverse('csrf_token'))
    csrf_token = csrf_response.json().get('csrf_token')
    
    print("   Testing rate limiting on forgot password endpoint...")
    
    # Make requests up to the limit
    for i in range(5):  # Rate limit is 5 per hour
        print(f"     Request {i+1}/5...")
        response = client.post(
            forgot_password_url,
            {'email': f'test{i}@example.com'},
            HTTP_X_CSRFTOKEN=csrf_token,
            content_type='application/json'
        )
        
        if response.status_code == 200:
            print(f"       ✓ Request {i+1} successful")
            # Check rate limit headers
            assert 'X-RateLimit-Limit' in response, "Rate limit headers missing"
            assert 'X-RateLimit-Remaining' in response, "Rate limit remaining header missing"
        else:
            print(f"       ⚠ Request {i+1} failed with status {response.status_code}")
    
    # The next request should be rate limited
    print("     Testing rate limit enforcement...")
    response = client.post(
        forgot_password_url,
        {'email': 'ratelimited@example.com'},
        HTTP_X_CSRFTOKEN=csrf_token,
        content_type='application/json'
    )
    
    assert response.status_code == 429, f"Rate limiting not enforced, got status {response.status_code}"
    response_data = response.json()
    assert not response_data.get('success'), "Rate limited request marked as success"
    assert response_data.get('error', {}).get('code') == 'RATE_LIMIT_EXCEEDED', "Wrong error code for rate limit"
    assert 'Retry-After' in response, "Retry-After header missing"
    
    print("     ✓ Rate limiting correctly enforced")
    print("   ✓ Rate limiting tests completed\n")


def test_security_headers():
    """Test security headers in responses."""
    print("5. Testing Security Headers...")
    
    client = Client()
    
    # Test endpoints
    endpoints = [
        ('forgot_password_api', 'POST'),
        ('reset_password_api', 'POST'),
        ('csrf_token', 'GET'),
    ]
    
    for endpoint_name, method in endpoints:
        print(f"   Testing security headers for {endpoint_name}...")
        url = reverse(endpoint_name)
        
        if method == 'GET':
            response = client.get(url)
        else:
            # Get CSRF token for POST requests
            csrf_response = client.get(reverse('csrf_token'))
            csrf_token = csrf_response.json().get('csrf_token')
            
            if endpoint_name == 'forgot_password_api':
                response = client.post(
                    url,
                    {'email': 'test@example.com'},
                    HTTP_X_CSRFTOKEN=csrf_token,
                    content_type='application/json'
                )
            elif endpoint_name == 'reset_password_api':
                # Create test user and token
                user = User.objects.create_user(
                    username='headertest',
                    email='header@example.com',
                    password='oldpass123'
                )
                token, _ = PasswordResetService.generate_reset_token(
                    user=user,
                    ip_address='127.0.0.1'
                )
                
                response = client.post(
                    url,
                    {
                        'token': token,
                        'password': 'NewSecure123!',
                        'password_confirm': 'NewSecure123!'
                    },
                    HTTP_X_CSRFTOKEN=csrf_token,
                    content_type='application/json'
                )
                user.delete()
        
        # Check security headers
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
        ]
        
        for header in expected_headers:
            assert header in response, f"Security header {header} missing from {endpoint_name}"
            print(f"     ✓ {header}: {response[header]}")
    
    print("   ✓ Security headers tests completed\n")


def main():
    """Run all security validation tests."""
    print("Password Reset Security Validation Tests")
    print("=" * 50)
    print("Testing Task 5: Add comprehensive input validation and security")
    print("Requirements: 1.1, 3.4, 3.5, 4.2, 4.3, 5.6")
    print("=" * 50)
    
    try:
        # Clean up any existing test data
        User.objects.filter(username__startswith='test').delete()
        User.objects.filter(email__contains='test').delete()
        PasswordResetToken.objects.all().delete()
        PasswordResetAttempt.objects.all().delete()
        
        # Run tests
        test_email_validation()
        test_password_strength_validation()
        test_csrf_protection()
        test_rate_limiting()
        test_security_headers()
        
        print("🎉 ALL SECURITY VALIDATION TESTS PASSED!")
        print("\nTask 5 Implementation Summary:")
        print("✓ Enhanced email format validation with security checks")
        print("✓ Comprehensive password strength validation")
        print("✓ CSRF protection for all password reset forms")
        print("✓ Rate limiting middleware for password reset endpoints")
        print("✓ Security headers added to all responses")
        print("✓ Input sanitization and validation")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up test data
        try:
            User.objects.filter(username__startswith='test').delete()
            User.objects.filter(email__contains='test').delete()
        except:
            pass


if __name__ == '__main__':
    main()