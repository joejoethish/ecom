"""
Tests for search suggestions functionality.
"""
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Product, Category
from apps.authentication.models import User


class SearchSuggestionsAPITestCase(APITestCase):
    """Test cases for search suggestions API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Create test categories
        self.electronics = Category.objects.create(
            name="Electronics",
            slug="electronics",
            is_active=True
        )
        
        self.smartphones = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=self.electronics,
            is_active=True
        )
        
        # Create test products
        self.iphone = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            description="Latest iPhone with advanced features",
            short_description="Premium smartphone",
            category=self.smartphones,
            brand="Apple",
            sku="IPHONE15PRO",
            price=999.99,
            is_active=True,
            status='active'
        )
        
        self.samsung = Product.objects.create(
            name="Samsung Galaxy S24",
            slug="samsung-galaxy-s24",
            description="Flagship Android smartphone",
            short_description="Android smartphone",
            category=self.smartphones,
            brand="Samsung",
            sku="GALAXYS24",
            price=899.99,
            is_active=True,
            status='active'
        )
        
        self.laptop = Product.objects.create(
            name="MacBook Pro 16",
            slug="macbook-pro-16",
            description="Professional laptop for developers",
            short_description="Professional laptop",
            category=self.electronics,
            brand="Apple",
            sku="MACBOOKPRO16",
            price=2499.99,
            is_active=True,
            status='active'
        )
        
        # Create inactive product (should not appear in suggestions)
        self.inactive_product = Product.objects.create(
            name="Old Phone",
            slug="old-phone",
            description="Discontinued phone",
            category=self.smartphones,
            brand="OldBrand",
            sku="OLDPHONE",
            price=199.99,
            is_active=False,
            status='inactive'
        )
    
    def test_suggestions_with_valid_query(self):
        """Test suggestions endpoint with valid query."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'iphone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('suggestions', data)
        self.assertIn('products', data)
        self.assertIn('query', data)
        self.assertEqual(data['query'], 'iphone')
        
        # Should find iPhone in products
        product_names = [p['name'] for p in data['products']]
        self.assertIn('iPhone 15 Pro', product_names)
    
    def test_suggestions_with_brand_query(self):
        """Test suggestions with brand name query."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'apple'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should find Apple products
        product_names = [p['name'] for p in data['products']]
        self.assertTrue(
            any('iPhone' in name or 'MacBook' in name for name in product_names)
        )
        
        # Should include Apple in text suggestions
        self.assertIn('Apple', data['suggestions'])
    
    def test_suggestions_with_category_query(self):
        """Test suggestions with category name query."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'smartphone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should include category in suggestions
        self.assertIn('Smartphones', data['suggestions'])
    
    def test_suggestions_with_short_query(self):
        """Test suggestions with query less than 2 characters."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'i'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return empty results for short queries
        self.assertEqual(data['suggestions'], [])
        self.assertEqual(data['products'], [])
    
    def test_suggestions_with_empty_query(self):
        """Test suggestions with empty query."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return empty results
        self.assertEqual(data['suggestions'], [])
        self.assertEqual(data['products'], [])
    
    def test_suggestions_limit_parameter(self):
        """Test suggestions with limit parameter."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'phone', 'limit': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should respect limit for text suggestions
        self.assertLessEqual(len(data['suggestions']), 2)
        # Products are limited to 3 by default in the view
        self.assertLessEqual(len(data['products']), 3)
    
    def test_suggestions_excludes_inactive_products(self):
        """Test that suggestions exclude inactive products."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'old'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should not include inactive product
        product_names = [p['name'] for p in data['products']]
        self.assertNotIn('Old Phone', product_names)
    
    def test_suggestions_product_structure(self):
        """Test that product suggestions have correct structure."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'iphone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        if data['products']:
            product = data['products'][0]
            required_fields = ['id', 'name', 'slug', 'price', 'image', 'category']
            
            for field in required_fields:
                self.assertIn(field, product)
            
            # Verify data types
            self.assertIsInstance(product['price'], (int, float))
            self.assertIsInstance(product['name'], str)
            self.assertIsInstance(product['slug'], str)
    
    def test_suggestions_case_insensitive(self):
        """Test that suggestions are case insensitive."""
        url = reverse('search-suggestions')
        
        # Test with lowercase
        response_lower = self.client.get(url, {'q': 'iphone'})
        # Test with uppercase
        response_upper = self.client.get(url, {'q': 'IPHONE'})
        # Test with mixed case
        response_mixed = self.client.get(url, {'q': 'iPhone'})
        
        self.assertEqual(response_lower.status_code, status.HTTP_200_OK)
        self.assertEqual(response_upper.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mixed.status_code, status.HTTP_200_OK)
        
        # All should return similar results
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()
        
        # Should all find iPhone product
        for data in [data_lower, data_upper, data_mixed]:
            product_names = [p['name'] for p in data['products']]
            self.assertTrue(
                any('iPhone' in name for name in product_names)
            )
    
    def test_suggestions_partial_match(self):
        """Test that suggestions work with partial matches."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'gala'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should find Samsung Galaxy
        product_names = [p['name'] for p in data['products']]
        self.assertTrue(
            any('Galaxy' in name for name in product_names)
        )
    
    def test_suggestions_no_results(self):
        """Test suggestions when no results are found."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'nonexistentproduct'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return empty results but still valid structure
        self.assertEqual(data['suggestions'], [])
        self.assertEqual(data['products'], [])
        self.assertEqual(data['query'], 'nonexistentproduct')
    
    def test_suggestions_invalid_parameters(self):
        """Test suggestions with invalid parameters."""
        url = reverse('search-suggestions')
        
        # Test with invalid limit
        response = self.client.get(url, {'q': 'test', 'limit': 'invalid'})
        # Should handle gracefully and use default limit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_suggestions_special_characters(self):
        """Test suggestions with special characters in query."""
        url = reverse('search-suggestions')
        response = self.client.get(url, {'q': 'iphone-15'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should handle special characters gracefully
        self.assertIsInstance(data['suggestions'], list)
        self.assertIsInstance(data['products'], list)


class SearchSuggestionsServiceTestCase(TestCase):
    """Test cases for search suggestions service methods."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            is_active=True
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test description",
            category=self.category,
            brand="Test Brand",
            sku="TESTSKU",
            price=99.99,
            is_active=True,
            status='active'
        )
    
    def test_database_fallback_suggestions(self):
        """Test database fallback when Elasticsearch is unavailable."""
        from apps.search.views import SearchSuggestionsView
        
        view = SearchSuggestionsView()
        suggestions = view._get_database_suggestions('test', 5)
        
        self.assertIn('suggestions', suggestions)
        self.assertIn('products', suggestions)
        self.assertIn('query', suggestions)
        self.assertEqual(suggestions['query'], 'test')
        
        # Should find test product
        product_names = [p['name'] for p in suggestions['products']]
        self.assertIn('Test Product', product_names)