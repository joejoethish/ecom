#!/usr/bin/env python
"""
Manual test for password reset API endpoints.
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from apps.authentication.models import User
from apps.authentication.services import PasswordResetService

def test_api_endpoints():
    """Test the API endpoints manually."""
    print("Testing Password Reset API Endpoints...")
    
    # Create test client
    client = Client()
    
    # Create test user
    try:
        user = User.objects.get(email='test@example.com')
        print("Using existing test user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        print("Created new test user")
    
    # Test 1: Forgot Password API
    print("\n1. Testing POST /api/v1/auth/forgot-password/")
    try:
        url = reverse('forgot_password_api')
        print(f"URL: {url}")
        
        response = client.post(url, 
            json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Generate token and test validation
    print("\n2. Testing token generation and validation")
    try:
        token, reset_token = PasswordResetService.generate_reset_token(
            user=user,
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )
        print(f"Generated token: {token[:10]}...")
        
        # Test validate token API
        url = reverse('validate_reset_token_api', kwargs={'token': token})
        print(f"Validation URL: {url}")
        
        response = client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Reset password
    print("\n3. Testing POST /api/v1/auth/reset-password/")
    try:
        url = reverse('reset_password_api')
        print(f"URL: {url}")
        
        response = client.post(url,
            json.dumps({
                'token': token,
                'password': 'newpassword123',
                'password_confirm': 'newpassword123'
            }),
            content_type='application/json'
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_api_endpoints()