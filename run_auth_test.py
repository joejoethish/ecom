#!/usr/bin/env python3
"""
Complete authentication workflow test with server management
"""
import subprocess
import time
import requests
import json
import os
import sys
from datetime import datetime

def start_backend_server():
    """Start the Django backend server"""
    print("🚀 Starting Django backend server...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.getcwd(), 'backend')
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return None
    
    try:
        # Start Django server
        process = subprocess.Popen(
            [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Test if server is running
        for i in range(10):
            try:
                response = requests.get("http://127.0.0.1:8000/", timeout=2)
                print(f"✅ Backend server is running (Status: {response.status_code})")
                return process
            except:
                time.sleep(1)
                continue
        
        print("❌ Failed to start backend server")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def test_authentication_endpoints():
    """Test all authentication endpoints"""
    base_url = "http://127.0.0.1:8000/api/v1"
    
    print("\n🔄 Testing Authentication Endpoints...")
    
    # Test user registration
    test_user = {
        "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "user_type": "customer",
        "phone_number": "+1234567890"
    }
    
    print(f"\n📝 Testing Registration for {test_user['email']}...")
    try:
        response = requests.post(
            f"{base_url}/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Registration Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful!")
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Username: {data.get('user', {}).get('username')}")
            print(f"   Email: {data.get('user', {}).get('email')}")
            print(f"   Access Token: {'✓' if data.get('tokens', {}).get('access') else '✗'}")
            print(f"   Refresh Token: {'✓' if data.get('tokens', {}).get('refresh') else '✗'}")
            
            # Test login with the registered user
            print(f"\n🔐 Testing Login for {test_user['email']}...")
            login_data = {
                "email": test_user['email'],
                "password": test_user['password']
            }
            
            login_response = requests.post(
                f"{base_url}/auth/login/",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Login Status: {login_response.status_code}")
            if login_response.status_code == 200:
                login_data = login_response.json()
                print("✅ Login successful!")
                access_token = login_data.get('access')
                
                # Test protected endpoint
                if access_token:
                    print(f"\n🔒 Testing Protected Endpoint Access...")
                    profile_response = requests.get(
                        f"{base_url}/auth/profile/",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"
                        },
                        timeout=10
                    )
                    
                    print(f"Profile Access Status: {profile_response.status_code}")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        print("✅ Protected endpoint access successful!")
                        print(f"   Profile Username: {profile_data.get('username')}")
                        print(f"   Profile Email: {profile_data.get('email')}")
                    else:
                        print(f"❌ Profile access failed: {profile_response.text}")
                
                # Test forgot password
                print(f"\n🔑 Testing Forgot Password...")
                forgot_response = requests.post(
                    f"{base_url}/auth/forgot-password/",
                    json={"email": test_user['email']},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                print(f"Forgot Password Status: {forgot_response.status_code}")
                if forgot_response.status_code in [200, 201]:
                    print("✅ Forgot password request successful!")
                else:
                    print(f"❌ Forgot password failed: {forgot_response.text}")
                
            else:
                print(f"❌ Login failed: {login_response.text}")
                
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")

def test_frontend_components():
    """Test frontend authentication components"""
    print("\n🎨 Testing Frontend Components...")
    
    # Check if frontend files exist
    frontend_components = [
        "frontend/src/components/auth/LoginForm.tsx",
        "frontend/src/components/auth/RegisterForm.tsx",
        "frontend/src/components/auth/ForgotPasswordForm.tsx",
        "frontend/src/store/slices/authSlice.ts",
        "frontend/src/utils/api.ts"
    ]
    
    for component in frontend_components:
        if os.path.exists(component):
            print(f"✅ {component}")
        else:
            print(f"❌ {component} - Missing")

def main():
    """Run the complete authentication workflow test"""
    print("🚀 Complete Authentication Workflow Test")
    print("=" * 60)
    
    # Start backend server
    server_process = start_backend_server()
    if not server_process:
        print("❌ Cannot start backend server. Exiting.")
        return False
    
    try:
        # Test authentication endpoints
        test_authentication_endpoints()
        
        # Test frontend components
        test_frontend_components()
        
        print("\n" + "=" * 60)
        print("🎉 Authentication workflow test completed!")
        
    finally:
        # Clean up server process
        if server_process:
            print("\n🛑 Stopping backend server...")
            server_process.terminate()
            server_process.wait()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)