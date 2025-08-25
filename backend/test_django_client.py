#!/usr/bin/env python
"""
Test authentication endpoints using Django test client.
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import Client
from django.urls import reverse
from apps.authentication.models import User

def test_registration_with_client():
    """Test registration using Django test client"""
    print("Testing registration with Django test client...")
    
    client = Client()
    
    # Test data
    import time
    timestamp = str(int(time.time()))
    test_data = {
        "username": f"clienttest{timestamp}",
        "email": f"clienttest{timestamp}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Client",
        "last_name": "Test"
    }
    
    try:
        # Get the registration URL
        url = reverse('register')
        print(f"Registration URL: {url}")
        
        # Make POST request
        response = client.post(url, data=json.dumps(test_data), content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            data = response.json()
            user_email = data.get('user', {}).get('email', 'N/A')
            print(f"User created: {user_email}")
            
            # Verify user exists in database
            user = User.objects.get(email=user_email)
            print(f"User verified in DB: {user.email}")
            print(f"User has profile: {hasattr(user, 'profile')}")
            
            return True
        else:
            print("❌ Registration failed")
            print(f"Response: {response.content.decode()[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login_with_client():
    """Test login using Django test client"""
    print("\nTesting login with Django test client...")
    
    client = Client()
    
    # First create a user
    import time
    timestamp = str(int(time.time()))
    user = User.objects.create_user(
        username=f"logintest{timestamp}",
        email=f"logintest{timestamp}@example.com",
        password="TestPassword123!"
    )
    
    # Test login
    login_data = {
        "email": user.email,
        "password": "TestPassword123!"
    }
    
    try:
        url = reverse('login')
        print(f"Login URL: {url}")
        
        response = client.post(url, data=json.dumps(login_data), content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            access_token = data.get('access', 'N/A')
            print(f"Access token received: {access_token[:50] if access_token != 'N/A' else 'N/A'}...")
            return True
        else:
            print("❌ Login failed")
            print(f"Response: {response.content.decode()[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Authentication with Django Test Client")
    print("=" * 50)
    
    # Test registration
    reg_success = test_registration_with_client()
    
    # Test login
    login_success = test_login_with_client()
    
    print("\n" + "=" * 50)
    if reg_success and login_success:
        print("✅ All authentication tests passed!")
    else:
        print("❌ Some tests failed")
    print("Test completed!")