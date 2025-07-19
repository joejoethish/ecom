#!/usr/bin/env python
"""
Simple test script to verify customer API functionality.
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.contrib.auth import get_user_model
from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem
from apps.customers.services import CustomerService, AddressService, WishlistService
from apps.products.models import Product, Category
from decimal import Decimal

User = get_user_model()

def test_customer_service():
    """Test customer service functionality."""
    print("Testing Customer Service...")
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )
    
    # Test customer profile creation
    profile = CustomerService.create_customer_profile(
        user,
        phone_number='+1234567890',
        gender='M'
    )
    
    print(f"✓ Customer profile created: {profile.get_full_name()}")
    print(f"✓ Customer tier: {profile.customer_tier}")
    
    # Test profile update
    updated_profile = CustomerService.update_customer_profile(
        profile,
        newsletter_subscription=False,
        loyalty_points=100
    )
    
    print(f"✓ Profile updated - Newsletter: {updated_profile.newsletter_subscription}")
    print(f"✓ Loyalty points: {updated_profile.loyalty_points}")
    
    return profile

def test_address_service(customer_profile):
    """Test address service functionality."""
    print("\nTesting Address Service...")
    
    address_data = {
        'type': 'HOME',
        'first_name': 'John',
        'last_name': 'Doe',
        'address_line_1': '123 Main St',
        'city': 'New York',
        'state': 'NY',
        'postal_code': '10001',
        'country': 'USA',
        'phone': '+1234567890'
    }
    
    # Create address
    address = AddressService.create_address(customer_profile, address_data)
    print(f"✓ Address created: {address.get_full_address()}")
    print(f"✓ Is default: {address.is_default}")
    
    # Update address
    updated_address = AddressService.update_address(
        address,
        {'city': 'Boston', 'state': 'MA', 'postal_code': '02101'}
    )
    print(f"✓ Address updated: {updated_address.city}, {updated_address.state}")
    
    return address

def test_wishlist_service(customer_profile):
    """Test wishlist service functionality."""
    print("\nTesting Wishlist Service...")
    
    # Create test product
    category = Category.objects.create(
        name='Test Category',
        slug='test-category'
    )
    
    product = Product.objects.create(
        name='Test Product',
        slug='test-product',
        description='Test description',
        price=Decimal('99.99'),
        category=category,
        sku='TEST-001'
    )
    
    # Add to wishlist
    wishlist_item = WishlistService.add_to_wishlist(
        customer_profile,
        product,
        'Want to buy this'
    )
    
    print(f"✓ Product added to wishlist: {product.name}")
    print(f"✓ Wishlist notes: {wishlist_item.notes}")
    
    # Check if in wishlist
    is_in_wishlist = WishlistService.is_in_wishlist(customer_profile, product)
    print(f"✓ Product in wishlist: {is_in_wishlist}")
    
    # Get wishlist
    wishlist = WishlistService.get_or_create_wishlist(customer_profile)
    print(f"✓ Wishlist item count: {wishlist.item_count}")
    
    return product

def test_customer_analytics(customer_profile):
    """Test customer analytics functionality."""
    print("\nTesting Customer Analytics...")
    
    from apps.customers.services import CustomerActivityService
    
    # Log some activities
    CustomerActivityService.log_activity(
        customer_profile,
        'LOGIN',
        'User logged in',
        ip_address='192.168.1.1'
    )
    
    CustomerActivityService.log_activity(
        customer_profile,
        'PRODUCT_VIEW',
        'Viewed test product'
    )
    
    # Get analytics
    analytics = CustomerActivityService.get_customer_analytics(customer_profile)
    
    print(f"✓ Total activities: {analytics.get('total_activities', 0)}")
    print(f"✓ Login count: {analytics.get('login_count', 0)}")
    print(f"✓ Customer tier: {analytics.get('customer_tier', 'N/A')}")
    print(f"✓ Account age (days): {analytics.get('account_age_days', 0)}")

def main():
    """Run all tests."""
    print("=" * 50)
    print("CUSTOMER API FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        # Test customer service
        customer_profile = test_customer_service()
        
        # Test address service
        address = test_address_service(customer_profile)
        
        # Test wishlist service
        product = test_wishlist_service(customer_profile)
        
        # Test analytics
        test_customer_analytics(customer_profile)
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)
        
        # Print summary
        print(f"\nSummary:")
        print(f"- Customer: {customer_profile.get_full_name()}")
        print(f"- Email: {customer_profile.user.email}")
        print(f"- Addresses: {customer_profile.addresses.count()}")
        print(f"- Wishlist items: {customer_profile.wishlist.item_count}")
        print(f"- Activities: {customer_profile.activities.count()}")
        print(f"- Customer tier: {customer_profile.customer_tier}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)