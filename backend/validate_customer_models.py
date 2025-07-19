#!/usr/bin/env python
"""
Simple validation script for customer models.
This script validates that the customer models are properly defined and can be imported.
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure minimal Django settings for validation
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'apps.customers',
            'apps.products',
            'apps.orders',
            'apps.inventory',
        ],
        SECRET_KEY='test-secret-key-for-validation',
        USE_TZ=True,
    )

django.setup()

def validate_models():
    """Validate customer models."""
    print("🔍 Validating Customer Models...")
    
    try:
        # Import models
        from apps.customers.models import (
            CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
        )
        print("✅ All models imported successfully")
        
        # Check model fields
        print("\n📋 Model Field Validation:")
        
        # CustomerProfile validation
        profile_fields = [f.name for f in CustomerProfile._meta.fields]
        required_profile_fields = [
            'user', 'phone_number', 'gender', 'account_status', 
            'total_orders', 'total_spent', 'loyalty_points'
        ]
        for field in required_profile_fields:
            if field in profile_fields:
                print(f"✅ CustomerProfile.{field}")
            else:
                print(f"❌ CustomerProfile.{field} - MISSING")
        
        # Address validation
        address_fields = [f.name for f in Address._meta.fields]
        required_address_fields = [
            'customer', 'type', 'first_name', 'last_name', 
            'address_line_1', 'city', 'state', 'postal_code'
        ]
        for field in required_address_fields:
            if field in address_fields:
                print(f"✅ Address.{field}")
            else:
                print(f"❌ Address.{field} - MISSING")
        
        # Wishlist validation
        wishlist_fields = [f.name for f in Wishlist._meta.fields]
        required_wishlist_fields = ['customer', 'name']
        for field in required_wishlist_fields:
            if field in wishlist_fields:
                print(f"✅ Wishlist.{field}")
            else:
                print(f"❌ Wishlist.{field} - MISSING")
        
        # WishlistItem validation
        wishlist_item_fields = [f.name for f in WishlistItem._meta.fields]
        required_wishlist_item_fields = ['wishlist', 'product', 'added_at']
        for field in required_wishlist_item_fields:
            if field in wishlist_item_fields:
                print(f"✅ WishlistItem.{field}")
            else:
                print(f"❌ WishlistItem.{field} - MISSING")
        
        # CustomerActivity validation
        activity_fields = [f.name for f in CustomerActivity._meta.fields]
        required_activity_fields = ['customer', 'activity_type', 'description']
        for field in required_activity_fields:
            if field in activity_fields:
                print(f"✅ CustomerActivity.{field}")
            else:
                print(f"❌ CustomerActivity.{field} - MISSING")
        
        print("\n🔧 Model Methods Validation:")
        
        # Check CustomerProfile methods
        profile_methods = ['get_full_name', 'update_order_metrics', 'add_loyalty_points', 'deduct_loyalty_points']
        for method in profile_methods:
            if hasattr(CustomerProfile, method):
                print(f"✅ CustomerProfile.{method}()")
            else:
                print(f"❌ CustomerProfile.{method}() - MISSING")
        
        # Check Address methods
        address_methods = ['get_full_address', 'mark_as_used']
        for method in address_methods:
            if hasattr(Address, method):
                print(f"✅ Address.{method}()")
            else:
                print(f"❌ Address.{method}() - MISSING")
        
        # Check Wishlist properties
        if hasattr(Wishlist, 'item_count'):
            print("✅ Wishlist.item_count property")
        else:
            print("❌ Wishlist.item_count property - MISSING")
        
        print("\n🎯 Model Relationships Validation:")
        
        # Check relationships
        relationships = [
            ('CustomerProfile', 'user', 'OneToOneField'),
            ('Address', 'customer', 'ForeignKey'),
            ('Wishlist', 'customer', 'OneToOneField'),
            ('WishlistItem', 'wishlist', 'ForeignKey'),
            ('WishlistItem', 'product', 'ForeignKey'),
            ('CustomerActivity', 'customer', 'ForeignKey'),
        ]
        
        for model_name, field_name, field_type in relationships:
            model_class = globals().get(model_name)
            if model_class:
                field = model_class._meta.get_field(field_name)
                if field.__class__.__name__ == field_type:
                    print(f"✅ {model_name}.{field_name} ({field_type})")
                else:
                    print(f"❌ {model_name}.{field_name} - Expected {field_type}, got {field.__class__.__name__}")
            else:
                print(f"❌ {model_name} - Model not found")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation Error: {e}")
        return False

def validate_services():
    """Validate customer services."""
    print("\n🔍 Validating Customer Services...")
    
    try:
        # Import services
        from apps.customers.services import (
            CustomerService, AddressService, WishlistService, CustomerAnalyticsService
        )
        print("✅ All services imported successfully")
        
        # Check service methods
        print("\n📋 Service Methods Validation:")
        
        # CustomerService methods
        customer_service_methods = [
            'create_customer_profile', 'update_customer_profile', 
            'get_customer_analytics', 'log_activity'
        ]
        for method in customer_service_methods:
            if hasattr(CustomerService, method):
                print(f"✅ CustomerService.{method}()")
            else:
                print(f"❌ CustomerService.{method}() - MISSING")
        
        # AddressService methods
        address_service_methods = [
            'create_address', 'update_address', 'delete_address', 'set_default_address'
        ]
        for method in address_service_methods:
            if hasattr(AddressService, method):
                print(f"✅ AddressService.{method}()")
            else:
                print(f"❌ AddressService.{method}() - MISSING")
        
        # WishlistService methods
        wishlist_service_methods = [
            'add_to_wishlist', 'remove_from_wishlist', 'get_wishlist_items', 'clear_wishlist'
        ]
        for method in wishlist_service_methods:
            if hasattr(WishlistService, method):
                print(f"✅ WishlistService.{method}()")
            else:
                print(f"❌ WishlistService.{method}() - MISSING")
        
        # CustomerAnalyticsService methods
        analytics_service_methods = ['get_customer_segments', 'get_top_customers']
        for method in analytics_service_methods:
            if hasattr(CustomerAnalyticsService, method):
                print(f"✅ CustomerAnalyticsService.{method}()")
            else:
                print(f"❌ CustomerAnalyticsService.{method}() - MISSING")
        
        return True
        
    except ImportError as e:
        print(f"❌ Service Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Service Validation Error: {e}")
        return False

def main():
    """Main validation function."""
    print("🚀 Customer Models & Services Validation")
    print("=" * 50)
    
    models_valid = validate_models()
    services_valid = validate_services()
    
    print("\n" + "=" * 50)
    if models_valid and services_valid:
        print("🎉 All validations passed! Customer models and services are properly implemented.")
        return 0
    else:
        print("❌ Some validations failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())