#!/usr/bin/env python
"""
Test script to verify authentication endpoints work correctly.
"""
import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def test_register_endpoint():
    """Test the register endpoint"""
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    test_data = {
        "username": "testuser999",
        "email": "test999@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        print("Sending registration request...")
        response = requests.post(url, json=test_data, timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration endpoint working correctly!")
            data = response.json()
            user_id = data.get('user', {}).get('id', 'N/A')
            print(f"User ID: {user_id}")
            return True
        else:
            print("❌ Registration endpoint has issues")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the Django server first.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - there may be an issue with the endpoint")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_login_endpoint():
    """Test the login endpoint"""
    url = "http://127.0.0.1:8000/api/v1/auth/login/"
    
    test_data = {
        "email": "test999@example.com",
        "password": "TestPassword123!"
    }
    
    try:
        print("Sending login request...")
        response = requests.post(url, json=test_data, timeout=10)
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login endpoint working correctly!")
            return True
        else:
            print("❌ Login endpoint has issues")
            print(f"Login Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the Django server first.")
        return False
    except Exception as e:
        print(f"❌ Error testing login endpoint: {e}")
        return False

if __name__ == "__main__":
    print("Testing Authentication Endpoints...")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing Registration Endpoint:")
    reg_success = test_register_endpoint()
    
    # Test login only if registration succeeded
    if reg_success:
        print("\n2. Testing Login Endpoint:")
        test_login_endpoint()
    else:
        print("\n2. Skipping login test due to registration failure")
    
    print("\n" + "=" * 50)
    print("Test completed!")