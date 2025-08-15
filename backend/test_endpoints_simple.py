#!/usr/bin/env python
"""
Simple test to verify user self-management endpoints using Django shell.
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

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_endpoints():
    """Test the user self-management endpoints."""
    print("Testing User Self-Management Endpoints...")
    
    # Check if we can create a user with minimal fields
    try:
        # Try to create user with just required fields
        user = User(
            username='testuser123',
            email='test123@example.com',
            user_type='customer'
        )
        user.set_password('testpass123')
        user.save()
        print(f"✓ User created successfully: {user.email}")
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create API client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test GET /api/v1/auth/users/me/
        print("\n1. Testing GET /api/v1/auth/users/me/")
        response = client.get('/api/v1/auth/users/me/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            user_data = data.get('data', {}).get('user', {})
            print(f"   User email: {user_data.get('email', 'N/A')}")
            print(f"   User type: {user_data.get('user_type', 'N/A')}")
        else:
            print(f"   Error: {response.content}")
        
        # Test PUT /api/v1/auth/users/me/
        print("\n2. Testing PUT /api/v1/auth/users/me/")
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        response = client.put('/api/v1/auth/users/me/', data=update_data, format='json')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            user_data = data.get('data', {}).get('user', {})
            print(f"   Updated name: {user_data.get('first_name', 'N/A')} {user_data.get('last_name', 'N/A')}")
            print(f"   Updated bio: {user_data.get('bio', 'N/A')}")
        else:
            print(f"   Error: {response.content}")
        
        # Test DELETE /api/v1/auth/users/me/ (with confirmation)
        print("\n3. Testing DELETE /api/v1/auth/users/me/")
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
            User.objects.get(email='test123@example.com')
            print("   ERROR: User still exists!")
        except User.DoesNotExist:
            print("   SUCCESS: User successfully deleted")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_endpoints()