#!/usr/bin/env python
"""
Direct API test using Django test client to verify user self-management endpoints.
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

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_api_endpoints():
    """Test the user self-management endpoints directly."""
    print("Testing User Self-Management API Endpoints...")
    
    try:
        # Create a user directly in the database with all required fields
        print("Creating test user...")
        import time
        timestamp = str(int(time.time()))
        
        # Delete existing test user if exists
        User.objects.filter(email=f'test{timestamp}@example.com').delete()
        
        user = User.objects.create(
            username=f'testuser{timestamp}',
            email=f'test{timestamp}@example.com',
            user_type='customer',
            uuid=f'{timestamp[:8]}{"0" * (32 - len(timestamp[:8]))}'[:32]  # Provide 32-char UUID
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
            User.objects.get(email=f'test{timestamp}@example.com')
            print("   ERROR: User still exists!")
        except User.DoesNotExist:
            print("   SUCCESS: User successfully deleted")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_endpoints()