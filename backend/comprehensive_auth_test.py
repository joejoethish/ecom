#!/usr/bin/env python
"""
Comprehensive authentication system test.
"""
import os
import sys
import django
import requests
import json
import time

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_external_request():
    """Test the registration endpoint using external HTTP request."""
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    registration_data = {
        'username': 'externaltest123',
        'email': 'externaltest123@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'External',
        'last_name': 'Test',
        'user_type': 'customer'
    }
    
    print("Testing external HTTP request to registration endpoint...")
    
    try:
        # First, let's check if the server is running
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"Server status check: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running on http://127.0.0.1:8000/")
        return
    except Exception as e:
        print(f"✗ Error checking server: {str(e)}")
        return
    
    try:
        # Test the registration endpoint
        response = requests.post(url, 
                               json=registration_data,
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✓ External registration request working correctly")
        else:
            print("✗ External registration request has issues")
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection refused - server might not be running")
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
    except Exception as e:
        print(f"✗ Error with external request: {str(e)}")

def test_login_endpoint():
    """Test the login endpoint."""
    client = Client()
    
    # First create a user
    user_data = {
        'username': 'logintest123',
        'email': 'logintest123@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'Login',
        'last_name': 'Test',
        'user_type': 'customer'
    }
    
    print("\nTesting login endpoint...")
    
    # Register user first
    reg_response = client.post('/api/v1/auth/register/', 
                              data=json.dumps(user_data),
                              content_type='application/json')
    
    if reg_response.status_code != 201:
        print(f"✗ Failed to create test user: {reg_response.status_code}")
        return
    
    # Now test login
    login_data = {
        'email': 'logintest123@example.com',
        'password': 'TestPassword123!'
    }
    
    login_response = client.post('/api/v1/auth/login/',
                                data=json.dumps(login_data),
                                content_type='application/json')
    
    print(f"Login Status Code: {login_response.status_code}")
    print(f"Login Response: {login_response.content.decode()}")
    
    if login_response.status_code == 200:
        print("✓ Login endpoint working correctly")
    else:
        print("✗ Login endpoint has issues")

def test_seller_registration():
    """Test seller registration specifically."""
    client = Client()
    
    seller_data = {
        'username': 'sellertest123',
        'email': 'sellertest123@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'Seller',
        'last_name': 'Test',
        'user_type': 'seller'
    }
    
    print("\nTesting seller registration...")
    
    response = client.post('/api/v1/auth/register/', 
                          data=json.dumps(seller_data),
                          content_type='application/json')
    
    print(f"Seller Registration Status Code: {response.status_code}")
    print(f"Seller Registration Response: {response.content.decode()}")
    
    if response.status_code == 201:
        print("✓ Seller registration working correctly")
    else:
        print("✗ Seller registration has issues")

def check_database_users():
    """Check what users exist in the database."""
    print("\nChecking database users...")
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")
    
    for user in users.order_by('-id')[:5]:  # Show last 5 users
        print(f"- {user.username} ({user.email}) - {user.user_type} - Created: {user.date_joined}")

if __name__ == '__main__':
    print("=== Comprehensive Authentication System Test ===")
    
    # Test internal Django client
    test_login_endpoint()
    test_seller_registration()
    
    # Check database state
    check_database_users()
    
    # Test external HTTP request
    test_external_request()