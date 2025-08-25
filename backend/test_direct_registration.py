#!/usr/bin/env python
"""
Test script to verify registration logic directly without HTTP.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.authentication.serializers import UserRegistrationSerializer
from apps.authentication.models import User
from django.db import transaction

def test_direct_registration():
    """Test registration logic directly"""
    print("Testing direct registration logic...")
    
    import time
    timestamp = str(int(time.time()))
    test_data = {
        "username": f"directtest{timestamp}",
        "email": f"directtest{timestamp}@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Direct",
        "last_name": "Test"
    }
    
    try:
        # Test serializer validation
        print("1. Testing serializer validation...")
        serializer = UserRegistrationSerializer(data=test_data)
        
        if serializer.is_valid():
            print("✅ Serializer validation passed")
            
            # Test user creation
            print("2. Testing user creation...")
            with transaction.atomic():
                user = serializer.save()
                print(f"✅ User created successfully: {user.email}")
                print(f"   User ID: {user.id}")
                print(f"   Username: {user.username}")
                print(f"   Has profile: {hasattr(user, 'profile')}")
                
                if hasattr(user, 'profile'):
                    print(f"   Profile ID: {user.profile.id}")
                
                return True
        else:
            print("❌ Serializer validation failed:")
            for field, errors in serializer.errors.items():
                print(f"   {field}: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error during direct registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_creation_minimal():
    """Test minimal user creation"""
    print("\nTesting minimal user creation...")
    
    try:
        # Check if we can create a user directly
        import time
        timestamp = str(int(time.time()))
        user = User.objects.create_user(
            username=f"minimal{timestamp}",
            email=f"minimal{timestamp}@example.com",
            password="TestPassword123!"
        )
        print(f"✅ Minimal user created: {user.email}")
        print(f"   Has profile: {hasattr(user, 'profile')}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating minimal user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Registration Logic Directly...")
    print("=" * 50)
    
    # Test minimal user creation first
    minimal_success = test_user_creation_minimal()
    
    if minimal_success:
        # Test full registration logic
        test_direct_registration()
    
    print("\n" + "=" * 50)
    print("Direct test completed!")