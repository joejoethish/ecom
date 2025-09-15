#!/usr/bin/env python3
"""
Test script to verify the complete authentication workflow
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def test_backend_connection():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"✅ Backend is running (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not running: {e}")
        return False

def test_frontend_connection():
    """Test if frontend is running"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        print(f"✅ Frontend is running (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend is not running: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    print("\n🔄 Testing User Registration...")
    
    test_user = {
        "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "user_type": "customer",
        "phone_number": "+1234567890"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Registration successful for {test_user['email']}")
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Access Token: {'✓' if data.get('tokens', {}).get('access') else '✗'}")
            return data
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return None

def test_user_login(email, password):
    """Test user login endpoint"""
    print(f"\n🔄 Testing User Login for {email}...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful for {email}")
            print(f"   Access Token: {'✓' if data.get('access') else '✗'}")
            print(f"   Refresh Token: {'✓' if data.get('refresh') else '✗'}")
            return data
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return None

def test_protected_endpoint(access_token):
    """Test accessing a protected endpoint"""
    print("\n🔄 Testing Protected Endpoint Access...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/auth/profile/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Profile access successful")
            print(f"   User: {data.get('username', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
            return True
        else:
            print(f"❌ Profile access failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile request failed: {e}")
        return False

def test_forgot_password(email):
    """Test forgot password endpoint"""
    print(f"\n🔄 Testing Forgot Password for {email}...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/forgot-password/",
            json={"email": email},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Forgot password request successful")
            return True
        else:
            print(f"❌ Forgot password failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Forgot password request failed: {e}")
        return False

def test_token_refresh(refresh_token):
    """Test token refresh endpoint"""
    print("\n🔄 Testing Token Refresh...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/refresh/",
            json={"refresh": refresh_token},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token refresh successful")
            print(f"   New Access Token: {'✓' if data.get('access') else '✗'}")
            return data
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Token refresh request failed: {e}")
        return None

def main():
    """Run the complete authentication workflow test"""
    print("🚀 Starting Authentication Workflow Test")
    print("=" * 50)
    
    # Test server connections
    backend_running = test_backend_connection()
    frontend_running = test_frontend_connection()
    
    if not backend_running:
        print("\n❌ Backend server is not running. Please start it first:")
        print("   cd backend && python manage.py runserver")
        return False
    
    if not frontend_running:
        print("\n⚠️  Frontend server is not running. You may want to start it:")
        print("   cd frontend && npm run dev")
    
    # Test registration
    registration_data = test_user_registration()
    if not registration_data:
        print("\n❌ Registration test failed. Cannot continue.")
        return False
    
    user_email = registration_data.get('user', {}).get('email')
    access_token = registration_data.get('tokens', {}).get('access')
    refresh_token = registration_data.get('tokens', {}).get('refresh')
    
    # Test login with the registered user
    login_data = test_user_login(user_email, "TestPassword123!")
    if login_data:
        access_token = login_data.get('access', access_token)
        refresh_token = login_data.get('refresh', refresh_token)
    
    # Test protected endpoint access
    if access_token:
        test_protected_endpoint(access_token)
    
    # Test forgot password
    if user_email:
        test_forgot_password(user_email)
    
    # Test token refresh
    if refresh_token:
        test_token_refresh(refresh_token)
    
    print("\n" + "=" * 50)
    print("🎉 Authentication workflow test completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)