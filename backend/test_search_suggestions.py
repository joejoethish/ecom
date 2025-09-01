#!/usr/bin/env python
"""
Simple test script to verify search suggestions API endpoint.
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import Client
from django.urls import reverse
from apps.products.models import Product, Category
import json

def test_search_suggestions():
    """Test the search suggestions endpoint."""
    print("Testing Search Suggestions API...")
    
    # Create test client
    client = Client()
    
    try:
        # Test 1: Basic suggestions endpoint
        print("\n1. Testing basic suggestions endpoint...")
        url = '/api/v1/search/suggestions/'
        response = client.get(url, {'q': 'test'})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure: {list(data.keys())}")
            print(f"Query: {data.get('query', 'N/A')}")
            print(f"Suggestions count: {len(data.get('suggestions', []))}")
            print(f"Products count: {len(data.get('products', []))}")
        else:
            print(f"Error: {response.content.decode()}")
        
        # Test 2: Empty query
        print("\n2. Testing empty query...")
        response = client.get(url, {'q': ''})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Empty query response: {data}")
        
        # Test 3: Short query
        print("\n3. Testing short query...")
        response = client.get(url, {'q': 'a'})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Short query response: {data}")
        
        # Test 4: Check if we have any products in database
        print("\n4. Checking database content...")
        products_count = Product.objects.filter(is_active=True, is_deleted=False).count()
        categories_count = Category.objects.filter(is_active=True, is_deleted=False).count()
        print(f"Active products in database: {products_count}")
        print(f"Active categories in database: {categories_count}")
        
        if products_count > 0:
            # Get a sample product name to test with
            sample_product = Product.objects.filter(is_active=True, is_deleted=False).first()
            if sample_product:
                print(f"Sample product: {sample_product.name}")
                
                # Test with actual product name
                print(f"\n5. Testing with actual product name...")
                test_query = sample_product.name[:4].lower()  # First 4 characters
                response = client.get(url, {'q': test_query})
                print(f"Query: '{test_query}'")
                print(f"Status Code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Found {len(data.get('suggestions', []))} suggestions")
                    print(f"Found {len(data.get('products', []))} products")
                    if data.get('products'):
                        print(f"First product: {data['products'][0].get('name', 'N/A')}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_search_suggestions()