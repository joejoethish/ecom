#!/usr/bin/env python
"""
Test script for password reset API endpoints.
"""
import os
import sys
import django
import requests
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from apps.authentication.models import User, PasswordResetToken, PasswordResetAttempt
from apps.authentication.services import PasswordResetService

def test_password_reset_api_endpoints():
    """Test the password reset API endpoints."""
    print("Testing Password Reset API Endpoints...")
    
    # Create a test client
    client = Client()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    print(f"Created test user: {user.email}")
    
    # Test 1: Forgot Password API
    print("\n1. Testing POST /api/v1/auth/forgot-password/")
    forgot_password_url = reverse('forgot_password_api')
    print(f"URL: {forgot_password_url}")
    
    response = client.post(forgot_password_url, {
        'email': 'test@example.com'
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Invalid email format
    print("\n2. Testing invalid email format")
    response = client.post(forgot_password_url, {
        'email': 'invalid-email'
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Get a valid token for testing
    print("\n3. Generating test token...")
    token, reset_token = PasswordResetService.generate_reset_token(
        user=user,
        ip_address='127.0.0.1',
        user_agent='test-agent'
    )
    print(f"Generated token: {token[:10]}...")
    
    # Test 4: Validate Reset Token API
    print("\n4. Testing GET /api/v1/auth/validate-reset-token/<token>/")
    validate_token_url = reverse('validate_reset_token_api', kwargs={'token': token})
    print(f"URL: {validate_token_url}")
    
    response = client.get(validate_token_url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Validate invalid token
    print("\n5. Testing invalid token validation")
    invalid_token_url = reverse('validate_reset_token_api', kwargs={'token': 'invalid-token'})
    response = client.get(invalid_token_url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 6: Reset Password API
    print("\n6. Testing POST /api/v1/auth/reset-password/")
    reset_password_url = reverse('reset_password_api')
    print(f"URL: {reset_password_url}")
    
    response = client.post(reset_password_url, {
        'token': token,
        'password': 'newpassword123',
        'password_confirm': 'newpassword123'
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 7: Try to use the same token again (should fail)
    print("\n7. Testing token reuse (should fail)")
    response = client.post(reset_password_url, {
        'token': token,
        'password': 'anotherpassword123',
        'password_confirm': 'anotherpassword123'
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 8: Password mismatch
    print("\n8. Testing password mismatch")
    new_token, _ = PasswordResetService.generate_reset_token(
        user=user,
        ip_address='127.0.0.1',
        user_agent='test-agent'
    )
    
    response = client.post(reset_password_url, {
        'token': new_token,
        'password': 'password123',
        'password_confirm': 'differentpassword123'
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Cleanup
    user.delete()
    print("\nTest completed and cleaned up.")

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n\nTesting Rate Limiting...")
    
    client = Client()
    forgot_password_url = reverse('forgot_password_api')
    
    # Make multiple requests to trigger rate limiting
    for i in range(6):  # Max is 5 per hour
        print(f"\nRequest {i+1}:")
        response = client.post(forgot_password_url, {
            'email': 'test@example.com'
        }, content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 429:
            print("Rate limit triggered!")
            print(f"Response: {response.json()}")
            break
        else:
            print(f"Response: {response.json()}")

if __name__ == '__main__':
    try:
        test_password_reset_api_endpoints()
        test_rate_limiting()
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()