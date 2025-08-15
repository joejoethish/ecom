#!/usr/bin/env python
"""
Simple test script to verify user self-management endpoints are working.
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_user_self_management_endpoints():
    """Test the user self-management endpoints."""
    print("Testing User Self-Management Endpoints...")
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        user_type='customer'
    )
    
    # Create JWT token for authentication
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Create API client
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test GET /api/v1/users/me/
    print("1. Testing GET /api/v1/users/me/")
    response = client.get('/api/v1/auth/users/me/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   User email: {data.get('data', {}).get('user', {}).get('email', 'N/A')}")
    else:
        print(f"   Error: {response.content}")
    
    # Test PUT /api/v1/users/me/
    print("\n2. Testing PUT /api/v1/users/me/")
    update_data = {
        'first_name': 'Updated',
        'last_name': 'Name'
    }
    response = client.put('/api/v1/auth/users/me/', data=update_data, format='json')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Updated name: {data.get('data', {}).get('user', {}).get('first_name', 'N/A')} {data.get('data', {}).get('user', {}).get('last_name', 'N/A')}")
    else:
        print(f"   Error: {response.content}")
    
    # Test DELETE /api/v1/users/me/ (with confirmation)
    print("\n3. Testing DELETE /api/v1/users/me/")
    delete_data = {
        'password': 'testpass123',
        'confirm_deletion': True
    }
    response = client.delete('/api/v1/auth/users/me/', data=delete_data, format='json')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Message: {data.get('message', 'N/A')}")
    else:
        print(f"   Error: {response.content}")
    
    # Verify user is deleted
    print("\n4. Verifying user deletion")
    try:
        User.objects.get(email='test@example.com')
        print("   ERROR: User still exists!")
    except User.DoesNotExist:
        print("   SUCCESS: User successfully deleted")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_user_self_management_endpoints()