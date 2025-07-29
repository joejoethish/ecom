#!/usr/bin/env python
"""
Validate password reset API implementation.
"""
import os
import sys
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

try:
    import django
    django.setup()
    
    from django.test import Client
    from django.urls import reverse
    from apps.authentication.models import User, PasswordResetToken
    from apps.authentication.services import PasswordResetService
    from apps.authentication.serializers import (
        ForgotPasswordSerializer, 
        ResetPasswordSerializer, 
        ValidateResetTokenSerializer
    )
    
    def validate_serializers():
        """Validate serializers are working correctly."""
        print("1. Validating Serializers...")
        
        # Test ForgotPasswordSerializer
        serializer = ForgotPasswordSerializer(data={'email': 'test@example.com'})
        assert serializer.is_valid(), f"ForgotPasswordSerializer failed: {serializer.errors}"
        print("   ✓ ForgotPasswordSerializer works")
        
        # Test invalid email
        serializer = ForgotPasswordSerializer(data={'email': 'invalid-email'})
        assert not serializer.is_valid(), "ForgotPasswordSerializer should reject invalid email"
        print("   ✓ ForgotPasswordSerializer validates email format")
        
        # Test ResetPasswordSerializer with strong password
        serializer = ResetPasswordSerializer(data={
            'token': 'test-token-12345',
            'password': 'NewSecure123!',
            'password_confirm': 'NewSecure123!'
        })
        assert serializer.is_valid(), f"ResetPasswordSerializer failed: {serializer.errors}"
        print("   ✓ ResetPasswordSerializer works")
        
        # Test password mismatch
        serializer = ResetPasswordSerializer(data={
            'token': 'test-token-12345',
            'password': 'SecurePass1!',
            'password_confirm': 'DifferentPass2!'
        })
        assert not serializer.is_valid(), "ResetPasswordSerializer should reject password mismatch"
        print("   ✓ ResetPasswordSerializer validates password confirmation")
        
        # Test ValidateResetTokenSerializer
        serializer = ValidateResetTokenSerializer(data={'token': 'test-token'})
        assert serializer.is_valid(), f"ValidateResetTokenSerializer failed: {serializer.errors}"
        print("   ✓ ValidateResetTokenSerializer works")
        
        print("   All serializers validated successfully!\n")
    
    def validate_services():
        """Validate password reset service functionality."""
        print("2. Validating Services...")
        
        # Create test user
        try:
            user = User.objects.get(email='test@example.com')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='TestPassword123!'
            )
        
        # Test token generation
        token, reset_token = PasswordResetService.generate_reset_token(
            user=user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        assert token is not None, "Token generation failed"
        assert reset_token is not None, "Reset token object creation failed"
        print("   ✓ Token generation works")
        
        # Test token validation
        validated_token, error = PasswordResetService.validate_reset_token(token)
        assert validated_token is not None, f"Token validation failed: {error}"
        assert error is None, f"Token validation returned error: {error}"
        print("   ✓ Token validation works")
        
        # Test invalid token validation
        invalid_token, error = PasswordResetService.validate_reset_token('invalid-token')
        assert invalid_token is None, "Invalid token should not validate"
        assert error is not None, "Invalid token should return error"
        print("   ✓ Invalid token rejection works")
        
        # Test password reset
        success, message = PasswordResetService.reset_password(
            token=token,
            new_password='NewSecure123!',
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        assert success, f"Password reset failed: {message}"
        print("   ✓ Password reset works")
        
        # Test token reuse (should fail)
        success, message = PasswordResetService.reset_password(
            token=token,
            new_password='AnotherSecure123!',
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        assert not success, "Token reuse should fail"
        assert 'used' in message.lower(), f"Expected 'used' in error message: {message}"
        print("   ✓ Token reuse prevention works")
        
        print("   All services validated successfully!\n")
    
    def validate_views():
        """Validate API views functionality."""
        print("3. Validating API Views...")
        
        client = Client()
        
        # Create test user
        try:
            user = User.objects.get(email='test2@example.com')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='TestPassword123!'
            )
        
        # Test forgot password API
        url = reverse('forgot_password_api')
        response = client.post(url, 
            json.dumps({'email': 'test2@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 200, f"Forgot password API failed: {response.status_code}"
        data = response.json()
        assert data['success'], f"Forgot password API returned error: {data}"
        print("   ✓ Forgot password API works")
        
        # Test with invalid email format
        response = client.post(url, 
            json.dumps({'email': 'invalid-email'}),
            content_type='application/json'
        )
        assert response.status_code == 400, "Invalid email should return 400"
        print("   ✓ Forgot password API validates email format")
        
        # Generate token for testing
        token, reset_token = PasswordResetService.generate_reset_token(
            user=user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        
        # Test validate token API
        url = reverse('validate_reset_token_api', kwargs={'token': token})
        response = client.get(url)
        assert response.status_code == 200, f"Validate token API failed: {response.status_code}"
        data = response.json()
        assert data['success'], f"Validate token API returned error: {data}"
        assert data['data']['valid'], "Token should be valid"
        print("   ✓ Validate token API works")
        
        # Test with invalid token
        url = reverse('validate_reset_token_api', kwargs={'token': 'invalid-token'})
        response = client.get(url)
        assert response.status_code == 400, "Invalid token should return 400"
        data = response.json()
        assert not data['success'], "Invalid token should return success=false"
        print("   ✓ Validate token API rejects invalid tokens")
        
        # Test reset password API
        url = reverse('reset_password_api')
        response = client.post(url,
            json.dumps({
                'token': token,
                'password': 'NewSecure123!',
                'password_confirm': 'NewSecure123!'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200, f"Reset password API failed: {response.status_code}"
        data = response.json()
        assert data['success'], f"Reset password API returned error: {data}"
        print("   ✓ Reset password API works")
        
        # Test password mismatch
        new_token, _ = PasswordResetService.generate_reset_token(
            user=user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        response = client.post(url,
            json.dumps({
                'token': new_token,
                'password': 'password1',
                'password_confirm': 'password2'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400, "Password mismatch should return 400"
        print("   ✓ Reset password API validates password confirmation")
        
        print("   All API views validated successfully!\n")
    
    def validate_urls():
        """Validate URL patterns."""
        print("4. Validating URL Patterns...")
        
        # Test URL reversing
        urls = [
            ('forgot_password_api', '/api/v1/auth/forgot-password/'),
            ('reset_password_api', '/api/v1/auth/reset-password/'),
        ]
        
        for url_name, expected_path in urls:
            actual_path = reverse(url_name)
            assert actual_path == expected_path, f"URL mismatch for {url_name}: expected {expected_path}, got {actual_path}"
            print(f"   ✓ {url_name}: {actual_path}")
        
        # Test parameterized URL
        url = reverse('validate_reset_token_api', kwargs={'token': 'test-token'})
        expected = '/api/v1/auth/validate-reset-token/test-token/'
        assert url == expected, f"Parameterized URL mismatch: expected {expected}, got {url}"
        print(f"   ✓ validate_reset_token_api: {url}")
        
        print("   All URL patterns validated successfully!\n")
    
    def main():
        """Run all validations."""
        print("Password Reset API Implementation Validation")
        print("=" * 50)
        
        try:
            validate_serializers()
            validate_services()
            validate_views()
            validate_urls()
            
            print("🎉 ALL VALIDATIONS PASSED!")
            print("\nThe password reset API endpoints have been successfully implemented:")
            print("- POST /api/v1/auth/forgot-password/")
            print("- POST /api/v1/auth/reset-password/")
            print("- GET /api/v1/auth/validate-reset-token/<token>/")
            print("\nAll endpoints include proper error handling and status codes.")
            
        except AssertionError as e:
            print(f"❌ VALIDATION FAILED: {e}")
            return False
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    if __name__ == '__main__':
        success = main()
        sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"Error setting up Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)