#!/usr/bin/env python
"""
Test script to check the registration endpoint directly.
"""
import os
import sys
import django
import requests
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

def test_registration_endpoint():
    """Test the registration endpoint using Django test client."""
    client = Client()
    
    # Test data
    registration_data = {
        'username': 'testuser123',
        'email': 'testuser123@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'user_type': 'customer'
    }
    
    print("Testing registration endpoint...")
    print(f"Data: {registration_data}")
    
    try:
        # Test the endpoint
        response = client.post('/api/v1/auth/register/', 
                             data=json.dumps(registration_data),
                             content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.content.decode()}")
        
        if response.status_code == 201:
            print("✓ Registration endpoint working correctly")
        else:
            print("✗ Registration endpoint has issues")
            
    except Exception as e:
        print(f"✗ Error testing registration endpoint: {str(e)}")
        import traceback
        traceback.print_exc()

def test_url_resolution():
    """Test if the URL resolves correctly."""
    try:
        from django.urls import resolve
        resolver = resolve('/api/v1/auth/register/')
        print(f"URL resolves to: {resolver.func}")
        print(f"View name: {resolver.view_name}")
        print("✓ URL resolution working")
    except Exception as e:
        print(f"✗ URL resolution failed: {str(e)}")

if __name__ == '__main__':
    print("=== Testing Authentication Registration Endpoint ===")
    test_url_resolution()
    test_registration_endpoint()