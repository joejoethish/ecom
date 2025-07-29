#!/usr/bin/env python
"""
Check URL patterns for password reset API.
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

try:
    import django
    django.setup()
    
    from django.urls import reverse
    
    print("Checking URL patterns...")
    
    # Test URL patterns
    urls_to_test = [
        'forgot_password_api',
        'reset_password_api',
    ]
    
    for url_name in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"✓ {url_name}: {url}")
        except Exception as e:
            print(f"✗ {url_name}: {e}")
    
    # Test URL with parameter
    try:
        url = reverse('validate_reset_token_api', kwargs={'token': 'test-token'})
        print(f"✓ validate_reset_token_api: {url}")
    except Exception as e:
        print(f"✗ validate_reset_token_api: {e}")
    
    print("\nURL patterns check completed!")
    
except Exception as e:
    print(f"Error setting up Django: {e}")
    import traceback
    traceback.print_exc()