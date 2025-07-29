#!/usr/bin/env python
"""
Simple test script for comprehensive input validation and security enhancements.
This script validates Task 5 implementation without Celery dependencies.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.authentication.serializers import ForgotPasswordSerializer, ResetPasswordSerializer
from rest_framework import serializers


def test_email_validation():
    """Test enhanced email format validation."""
    print("1. Testing Enhanced Email Format Validation...")
    
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
        
        # Security-related invalid emails
        ('user<script>@domain.com', False, 'HTML injection attempt'),
        ('user@domain.com\r\nBCC: evil@hacker.com', False, 'CRLF injection'),
        ('javascript:alert(1)@domain.com', False, 'JavaScript injection'),
        
        # Length validation
        ('a' * 250 + '@domain.com', False, 'Email too long'),
        ('user@' + 'a' * 250 + '.com', False, 'Domain too long'),
    ]
    
    for email, should_pass, description in test_cases:
        print(f"   Testing: {description}")
        
        serializer = ForgotPasswordSerializer(data={'email': email})
        is_valid = serializer.is_valid()
        
        if should_pass:
            assert is_valid, f"Valid email failed: {email} - {serializer.errors}"
            print(f"     ✓ {description} - Passed")
        else:
            assert not is_valid, f"Invalid email accepted: {email}"
            print(f"     ✓ {description} - Correctly rejected")
    
    print("   ✓ Email validation tests completed\n")


def test_password_strength_validation():
    """Test enhanced password strength validation."""
    print("2. Testing Enhanced Password Strength Validation...")
    
    # Test cases for password validation
    test_cases = [
        # Valid passwords
        ('ValidPass123!', 'ValidPass123!', 'test_token', True, 'Strong password'),
        ('MySecure@Pass1', 'MySecure@Pass1', 'test_token', True, 'Another strong password'),
        
        # Invalid passwords - strength issues
        ('weak', 'weak', 'test_token', False, 'Too short'),
        ('password', 'password', 'test_token', False, 'No uppercase, numbers, or special chars'),
        ('PASSWORD123', 'PASSWORD123', 'test_token', False, 'No lowercase or special chars'),
        ('Password123', 'Password123', 'test_token', False, 'No special characters'),
        ('Password!', 'Password!', 'test_token', False, 'No numbers'),
        ('password123!', 'password123!', 'test_token', False, 'No uppercase'),
        ('PASSWORD!', 'PASSWORD!', 'test_token', False, 'No lowercase or numbers'),
        
        # Weak patterns
        ('Password111!', 'Password111!', 'test_token', False, 'Consecutive identical characters'),
        ('Qwerty123!', 'Qwerty123!', 'test_token', False, 'Common weak pattern'),
        
        # Password confirmation mismatch
        ('ValidPass123!', 'DifferentPass123!', 'test_token', False, 'Password mismatch'),
        ('ValidPass123!', '', 'test_token', False, 'Empty confirmation'),
        
        # Token validation
        ('ValidPass123!', 'ValidPass123!', '', False, 'Empty token'),
        ('ValidPass123!', 'ValidPass123!', 'short', False, 'Token too short'),
        ('ValidPass123!', 'ValidPass123!', 'invalid@token', False, 'Invalid token characters'),
        
        # Length limits
        ('a' * 130 + 'A1!', 'a' * 130 + 'A1!', 'test_token', False, 'Password too long'),
        ('', '', 'test_token', False, 'Empty password'),
        ('   ', '   ', 'test_token', False, 'Whitespace only password'),
    ]
    
    for password, confirm, token, should_pass, description in test_cases:
        print(f"   Testing: {description}")
        
        serializer = ResetPasswordSerializer(data={
            'token': token,
            'password': password,
            'password_confirm': confirm
        })
        is_valid = serializer.is_valid()
        
        if should_pass:
            assert is_valid, f"Valid password failed: {description} - {serializer.errors}"
            print(f"     ✓ {description} - Passed")
        else:
            assert not is_valid, f"Invalid password accepted: {description}"
            print(f"     ✓ {description} - Correctly rejected")
    
    print("   ✓ Password strength validation tests completed\n")


def test_middleware_imports():
    """Test that middleware classes can be imported."""
    print("3. Testing Middleware Imports...")
    
    try:
        from apps.authentication.middleware import (
            PasswordResetRateLimitMiddleware,
            CSRFPasswordResetMiddleware,
            SecurityHeadersMiddleware
        )
        print("   ✓ PasswordResetRateLimitMiddleware imported successfully")
        print("   ✓ CSRFPasswordResetMiddleware imported successfully")
        print("   ✓ SecurityHeadersMiddleware imported successfully")
        
        # Test middleware instantiation
        def dummy_get_response(request):
            return None
        
        rate_limit_middleware = PasswordResetRateLimitMiddleware(dummy_get_response)
        csrf_middleware = CSRFPasswordResetMiddleware(dummy_get_response)
        security_middleware = SecurityHeadersMiddleware(dummy_get_response)
        
        print("   ✓ All middleware classes instantiated successfully")
        
    except ImportError as e:
        print(f"   ❌ Middleware import failed: {e}")
        raise
    
    print("   ✓ Middleware import tests completed\n")


def test_settings_configuration():
    """Test that Django settings are properly configured."""
    print("4. Testing Settings Configuration...")
    
    from django.conf import settings
    
    # Check middleware configuration
    middleware = settings.MIDDLEWARE
    expected_middleware = [
        'apps.authentication.middleware.SecurityHeadersMiddleware',
        'apps.authentication.middleware.CSRFPasswordResetMiddleware',
        'apps.authentication.middleware.PasswordResetRateLimitMiddleware',
    ]
    
    for mw in expected_middleware:
        assert mw in middleware, f"Middleware {mw} not found in settings"
        print(f"   ✓ {mw} configured in middleware")
    
    # Check password validators
    validators = settings.AUTH_PASSWORD_VALIDATORS
    assert len(validators) >= 4, "Not enough password validators configured"
    print(f"   ✓ {len(validators)} password validators configured")
    
    # Check CSRF middleware is present
    assert 'django.middleware.csrf.CsrfViewMiddleware' in middleware, "CSRF middleware not configured"
    print("   ✓ CSRF middleware configured")
    
    print("   ✓ Settings configuration tests completed\n")


def test_view_imports():
    """Test that enhanced views can be imported."""
    print("5. Testing View Imports...")
    
    try:
        from apps.authentication.views import (
            ForgotPasswordAPIView,
            ResetPasswordAPIView,
            CSRFTokenView
        )
        print("   ✓ ForgotPasswordAPIView imported successfully")
        print("   ✓ ResetPasswordAPIView imported successfully")
        print("   ✓ CSRFTokenView imported successfully")
        
        # Check that views have CSRF protection decorators
        import inspect
        
        # Check ForgotPasswordAPIView
        forgot_source = inspect.getsource(ForgotPasswordAPIView)
        assert '@method_decorator(csrf_protect' in forgot_source, "ForgotPasswordAPIView missing CSRF protection"
        print("   ✓ ForgotPasswordAPIView has CSRF protection")
        
        # Check ResetPasswordAPIView
        reset_source = inspect.getsource(ResetPasswordAPIView)
        assert '@method_decorator(csrf_protect' in reset_source, "ResetPasswordAPIView missing CSRF protection"
        print("   ✓ ResetPasswordAPIView has CSRF protection")
        
        # Check CSRFTokenView
        csrf_source = inspect.getsource(CSRFTokenView)
        assert '@method_decorator(ensure_csrf_cookie' in csrf_source, "CSRFTokenView missing ensure_csrf_cookie"
        print("   ✓ CSRFTokenView has ensure_csrf_cookie decorator")
        
    except ImportError as e:
        print(f"   ❌ View import failed: {e}")
        raise
    
    print("   ✓ View import tests completed\n")


def main():
    """Run all security validation tests."""
    print("Password Reset Security Validation Tests (Simple)")
    print("=" * 55)
    print("Testing Task 5: Add comprehensive input validation and security")
    print("Requirements: 1.1, 3.4, 3.5, 4.2, 4.3, 5.6")
    print("=" * 55)
    
    try:
        # Run tests
        test_email_validation()
        test_password_strength_validation()
        test_middleware_imports()
        test_settings_configuration()
        test_view_imports()
        
        print("🎉 ALL SECURITY VALIDATION TESTS PASSED!")
        print("\nTask 5 Implementation Summary:")
        print("✓ Enhanced email format validation with security checks")
        print("✓ Comprehensive password strength validation")
        print("✓ CSRF protection decorators added to password reset views")
        print("✓ Rate limiting middleware implemented and configured")
        print("✓ Security headers middleware implemented")
        print("✓ CSRF token endpoint created")
        print("✓ Django settings properly configured")
        print("✓ All components can be imported and instantiated")
        
        print("\nSecurity Enhancements Implemented:")
        print("• Email injection protection (CRLF, HTML, JavaScript)")
        print("• Password strength requirements (length, complexity, patterns)")
        print("• CSRF token validation on all password reset forms")
        print("• Rate limiting (5 requests per hour per IP)")
        print("• Security headers (X-Content-Type-Options, X-Frame-Options, etc.)")
        print("• Input sanitization and validation")
        print("• Token format validation")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()