#!/usr/bin/env python
"""
Test script for new APIs (wishlist, rewards, orders).
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.customers.models import CustomerProfile
from apps.rewards.models import CustomerRewards, RewardProgram
from apps.products.models import Product, Category
import json

User = get_user_model()

def test_apis():
    """Test the new APIs."""
    client = Client()
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'user_type': 'customer'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Get or create customer profile
    customer_profile, _ = CustomerProfile.objects.get_or_create(user=user)
    
    # Get or create test product and category
    category, _ = Category.objects.get_or_create(
        slug='test-category',
        defaults={
            'name': 'Test Category'
        }
    )
    
    product, _ = Product.objects.get_or_create(
        slug='test-product',
        defaults={
            'name': 'Test Product',
            'description': 'Test product description',
            'category': category,
            'price': 99.99,
            'sku': 'TEST-001'
        }
    )
    
    # Login user
    client.login(username='testuser', password='testpass123')
    
    print("Testing APIs...")
    
    # Test Wishlist API
    print("\n1. Testing Wishlist API:")
    
    # Get wishlist
    response = client.get('/api/v1/wishlist/')
    print(f"GET /api/v1/wishlist/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Wishlist items: {len(data.get('data', {}).get('items', []))}")
    
    # Add to wishlist
    response = client.post('/api/v1/wishlist/', {
        'product_id': product.id
    })
    print(f"POST /api/v1/wishlist/ - Status: {response.status_code}")
    
    # Test Rewards API
    print("\n2. Testing Rewards API:")
    
    # Create reward program
    program = RewardProgram.objects.create(
        name='Test Rewards Program',
        description='Test program',
        points_per_dollar=1.0,
        dollar_per_point=0.01
    )
    
    # Get rewards
    response = client.get('/api/v1/rewards/')
    print(f"GET /api/v1/rewards/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Current points: {data.get('current_points', 0)}")
    
    # Test Orders API
    print("\n3. Testing Orders API:")
    
    # Get orders
    response = client.get('/api/v1/orders/orders/')
    print(f"GET /api/v1/orders/orders/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Orders count: {len(data.get('results', []))}")
    
    print("\nAPI tests completed!")

if __name__ == '__main__':
    test_apis()