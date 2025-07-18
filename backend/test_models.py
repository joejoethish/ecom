#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

# Setup Django
django.setup()

try:
    from apps.authentication.models import User
    print("SUCCESS: User model imported successfully!")
    print(f"User model: {User}")
    print(f"User fields: {[f.name for f in User._meta.fields]}")
except Exception as e:
    print(f"ERROR: Failed to import User model: {e}")
    import traceback
    traceback.print_exc()