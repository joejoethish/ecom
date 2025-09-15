#!/usr/bin/env python3
"""
Simple authentication test
"""
import requests
import json

def test_auth_endpoints():
    base_url = "http://127.0.0.1:8000"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Server status: {response.status_code}")
    except Exception as e:
        print(f"Server not running: {e}")
        return
    
    # Test registration endpoint
    test_user = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "user_type": "customer"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"Registration status: {response.status_code}")
        print(f"Registration response: {response.text[:200]}...")
    except Exception as e:
        print(f"Registration error: {e}")

if __name__ == "__main__":
    test_auth_endpoints()