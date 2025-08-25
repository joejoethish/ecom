#!/usr/bin/env python
"""
Simple test to check POST request handling.
"""
import requests
import json

def test_simple_post():
    """Test a simple POST request"""
    url = "http://127.0.0.1:8000/api/v1/auth/register/"
    
    # Get CSRF token first
    try:
        csrf_response = requests.get("http://127.0.0.1:8000/api/v1/auth/csrf-token/", timeout=5)
        print(f"CSRF token response: {csrf_response.status_code}")
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('csrfToken', '')
            print(f"CSRF token: {csrf_token[:20]}...")
        else:
            csrf_token = ''
    except Exception as e:
        print(f"CSRF token error: {e}")
        csrf_token = ''
    
    # Test data
    test_data = {
        "username": "simpletest123",
        "email": "simpletest@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Simple",
        "last_name": "Test"
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
    }
    
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    try:
        print("Sending POST request...")
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
        else:
            print("❌ Registration failed")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_post()