"""
Test category routing API endpoints.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.products.models import Category, Product
from apps.authentication.models import User


class CategoryRoutingAPITest(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test categories
        self.electronics_category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic products and gadgets',
            is_active=True
        )
        
        self.fashion_category = Category.objects.create(
            name='Fashion',
            slug='fashion',
            description='Fashion and clothing',
            is_active=True
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            description='Latest iPhone model',
            category=self.electronics_category,
            brand='Apple',
            sku='IPHONE15-001',
            price=999.00,
            discount_price=899.00,
            is_active=True,
            is_featured=True
        )
        
        self.product2 = Product.objects.create(
            name='Samsung Galaxy S24',
            slug='samsung-galaxy-s24',
            description='Latest Samsung Galaxy model',
            category=self.electronics_category,
            brand='Samsung',
            sku='GALAXY-S24-001',
            price=899.00,
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            name='Nike Air Max',
            slug='nike-air-max',
            description='Comfortable running shoes',
            category=self.fashion_category,
            brand='Nike',
            sku='NIKE-AIRMAX-001',
            price=150.00,
            is_active=True
        )

    def test_get_all_categories(self):
        """Test getting all categories."""
        url = reverse('all-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['total_count'], 2)
        
        # Check category data
        category_names = [cat['name'] for cat in data['data']]
        self.assertIn('Electronics', category_names)
        self.assertIn('Fashion', category_names)

    def test_get_category_details(self):
        """Test getting category details."""
        url = reverse('category-details', kwargs={'category_slug': 'electronics'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'Electronics')
        self.assertEqual(data['data']['slug'], 'electronics')
        self.assertEqual(data['data']['product_count'], 2)
        
        # Check top brands
        brand_names = [brand['name'] for brand in data['data']['top_brands']]
        self.assertIn('Apple', brand_names)
        self.assertIn('Samsung', brand_names)

    def test_get_category_filters(self):
        """Test getting category filters."""
        url = reverse('category-filters', kwargs={'category_slug': 'electronics'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['category']['name'], 'Electronics')
        self.assertEqual(data['data']['total_products'], 2)
        
        # Check brands filter
        brand_names = [brand['name'] for brand in data['data']['brands']]
        self.assertIn('Apple', brand_names)
        self.assertIn('Samsung', brand_names)
        
        # Check price ranges
        self.assertTrue(len(data['data']['price_ranges']) > 0)

    def test_get_products_by_category(self):
        """Test getting products by category."""
        url = reverse('products-by-category', kwargs={'category_slug': 'electronics'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 2)
        self.assertEqual(data['data']['total_count'], 2)
        self.assertEqual(data['data']['page'], 1)
        self.assertEqual(data['data']['total_pages'], 1)
        
        # Check product data
        product_names = [product['name'] for product in data['data']['data']]
        self.assertIn('iPhone 15', product_names)
        self.assertIn('Samsung Galaxy S24', product_names)

    def test_get_products_by_category_with_filters(self):
        """Test getting products by category with filters."""
        url = reverse('products-by-category', kwargs={'category_slug': 'electronics'})
        
        # Test brand filter
        response = self.client.get(url, {'brand': 'Apple'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 1)
        self.assertEqual(data['data']['data'][0]['name'], 'iPhone 15')
        
        # Test price filter
        response = self.client.get(url, {'price_min': '900'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 1)
        self.assertEqual(data['data']['data'][0]['name'], 'iPhone 15')

    def test_get_products_by_category_with_sorting(self):
        """Test getting products by category with sorting."""
        url = reverse('products-by-category', kwargs={'category_slug': 'electronics'})
        
        # Test name sorting
        response = self.client.get(url, {'sort': 'name'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 2)
        
        # Test price sorting
        response = self.client.get(url, {'sort': 'price'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 2)

    def test_get_products_by_category_pagination(self):
        """Test pagination for products by category."""
        # Create more products to test pagination
        for i in range(25):
            Product.objects.create(
                name=f'Test Product {i}',
                slug=f'test-product-{i}',
                description=f'Test product {i}',
                category=self.electronics_category,
                brand='TestBrand',
                sku=f'TEST-{i:03d}',
                price=100.00 + i,
                is_active=True
            )
        
        url = reverse('products-by-category', kwargs={'category_slug': 'electronics'})
        
        # Test first page
        response = self.client.get(url, {'page': '1'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 20)  # 20 per page
        self.assertEqual(data['data']['page'], 1)
        self.assertTrue(data['data']['has_next'])
        self.assertFalse(data['data']['has_previous'])
        
        # Test second page
        response = self.client.get(url, {'page': '2'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['data']), 7)  # Remaining products
        self.assertEqual(data['data']['page'], 2)
        self.assertFalse(data['data']['has_next'])
        self.assertTrue(data['data']['has_previous'])

    def test_category_not_found(self):
        """Test handling of non-existent category."""
        url = reverse('category-details', kwargs={'category_slug': 'nonexistent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'CATEGORY_NOT_FOUND')

    def test_products_by_nonexistent_category(self):
        """Test getting products for non-existent category."""
        url = reverse('products-by-category', kwargs={'category_slug': 'nonexistent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'CATEGORY_NOT_FOUND')

    def test_featured_categories(self):
        """Test getting featured categories."""
        url = reverse('featured-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertTrue(len(data['data']) > 0)
        
        # Check that categories have required fields
        for category in data['data']:
            self.assertIn('id', category)
            self.assertIn('name', category)
            self.assertIn('slug', category)
            self.assertIn('product_count', category)
            self.assertIn('href', category)
            self.assertTrue(category['href'].startswith('/category/'))


if __name__ == '__main__':
    import django
    import os
    import sys
    
    # Add the backend directory to the Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
    django.setup()
    
    # Run the tests
    import unittest
    unittest.main()