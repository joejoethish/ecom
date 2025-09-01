#!/usr/bin/env python
"""
Simple test script for new models (rewards).
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.customers.models import CustomerProfile, Wishlist, WishlistItem
from apps.rewards.models import CustomerRewards, RewardProgram, RewardTransaction
from apps.products.models import Product, Category

User = get_user_model()

def test_models():
    """Test the new models."""
    print("Testing Models...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser2',
        defaults={
            'email': 'test2@example.com',
            'user_type': 'customer'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")
    
    # Get or create customer profile
    customer_profile, created = CustomerProfile.objects.get_or_create(user=user)
    if created:
        print(f"✓ Created customer profile for: {user.username}")
    else:
        print(f"✓ Using existing customer profile for: {user.username}")
    
    # Test Rewards Model
    print("\n1. Testing Rewards Models:")
    
    # Create reward program
    program, created = RewardProgram.objects.get_or_create(
        name='Test Rewards Program',
        defaults={
            'description': 'Test program',
            'points_per_dollar': 1.0,
            'dollar_per_point': 0.01
        }
    )
    if created:
        print(f"✓ Created reward program: {program.name}")
    else:
        print(f"✓ Using existing reward program: {program.name}")
    
    # Create customer rewards
    rewards, created = CustomerRewards.objects.get_or_create(user=user)
    if created:
        print(f"✓ Created customer rewards for: {user.username}")
    else:
        print(f"✓ Using existing customer rewards for: {user.username}")
    
    # Add some points
    rewards.add_points(100, 'purchase', 'Test purchase', 'ORDER-123')
    print(f"✓ Added 100 points. Current balance: {rewards.current_points}")
    
    # Test Wishlist Model
    print("\n2. Testing Wishlist Models:")
    
    # Get or create test category and product
    category, _ = Category.objects.get_or_create(
        slug='test-category-2',
        defaults={'name': 'Test Category 2'}
    )
    
    product, _ = Product.objects.get_or_create(
        slug='test-product-2',
        defaults={
            'name': 'Test Product 2',
            'description': 'Test product description',
            'category': category,
            'price': 99.99,
            'sku': 'TEST-002'
        }
    )
    print(f"✓ Using product: {product.name}")
    
    # Create wishlist
    wishlist, created = Wishlist.objects.get_or_create(customer=customer_profile)
    if created:
        print(f"✓ Created wishlist for: {customer_profile.user.username}")
    else:
        print(f"✓ Using existing wishlist for: {customer_profile.user.username}")
    
    # Add item to wishlist
    wishlist_item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    if created:
        print(f"✓ Added {product.name} to wishlist")
    else:
        print(f"✓ {product.name} already in wishlist")
    
    print(f"✓ Wishlist has {wishlist.item_count} items")
    
    print("\n✅ All model tests completed successfully!")

if __name__ == '__main__':
    test_models()