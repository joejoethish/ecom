"""
Tests for product API views.
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.products.models import Category, Product, ProductImage

User = get_user_model()


class ProductAPITestCase(APITestCase):
    """Base test case for product API tests."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )

        # Create categories
        self.parent_category = Category.objects.create(
            name='Electronics',
            description='Electronic products',
            is_active=True
        )
        self.child_category = Category.objects.create(
            name='Smartphones',
            description='Mobile phones and smartphones',
            parent=self.parent_category,
            is_active=True
        )
        self.inactive_category = Category.objects.create(
            name='Inactive Category',
            description='This category is inactive',
            is_active=False
        )

        # Create products
        self.active_product = Product.objects.create(
            name='iPhone 15',
            description='Latest iPhone model with advanced features',
            short_description='Apple\'s newest smartphone',
            category=self.child_category,
            brand='Apple',
            sku='IPHONE15-001',
            price=Decimal('999.99'),
            discount_price=Decimal('899.99'),
            weight=Decimal('0.2'),
            is_active=True,
            is_featured=True,
            status='active',
            tags='smartphone, apple, ios, mobile'
        )
        
        self.inactive_product = Product.objects.create(
            name='Old Phone',
            description='An old phone model',
            category=self.child_category,
            brand='OldBrand',
            sku='OLD-001',
            price=Decimal('199.99'),
            is_active=False,
            status='inactive'
        )

        self.draft_product = Product.objects.create(
            name='Draft Product',
            description='A product in draft status',
            category=self.child_category,
            brand='TestBrand',
            sku='DRAFT-001',
            price=Decimal('299.99'),
            is_active=True,
            status='draft'
        )

        # Create product images
        self.product_image = ProductImage.objects.create(
            product=self.active_product,
            image='products/iphone15.jpg',
            alt_text='iPhone 15 main image',
            is_primary=True,
            sort_order=1
        )

        # API client
        self.client = APIClient()


class CategoryAPITest(ProductAPITestCase):
    """Test cases for Category API endpoints."""

    def test_list_categories_anonymous(self):
        """Test listing categories as anonymous user."""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should only see active categories
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertIn('Electronics', category_names)
        self.assertIn('Smartphones', category_names)
        self.assertNotIn('Inactive Category', category_names)

    def test_list_categories_admin(self):
        """Test listing categories as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin should see all categories including inactive
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertIn('Electronics', category_names)
        self.assertIn('Smartphones', category_names)
        self.assertIn('Inactive Category', category_names)

    def test_retrieve_category_by_slug(self):
        """Test retrieving a specific category by slug."""
        url = reverse('category-detail', kwargs={'slug': self.parent_category.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronics')
        self.assertEqual(response.data['slug'], 'electronics')
        self.assertIn('children', response.data)
        self.assertEqual(len(response.data['children']), 1)
        self.assertEqual(response.data['children'][0]['name'], 'Smartphones')

    def test_create_category_admin(self):
        """Test creating a category as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-list')
        data = {
            'name': 'New Category',
            'description': 'A new category for testing',
            'parent': self.parent_category.id,
            'is_active': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Category')
        self.assertEqual(response.data['slug'], 'new-category')
        self.assertEqual(response.data['parent'], str(self.parent_category.id))

    def test_create_category_unauthorized(self):
        """Test creating a category as regular user (should fail)."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('category-list')
        data = {
            'name': 'Unauthorized Category',
            'description': 'Should not be created'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_category_admin(self):
        """Test updating a category as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-detail', kwargs={'slug': self.child_category.slug})
        data = {
            'name': 'Updated Smartphones',
            'description': 'Updated description for smartphones'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Smartphones')
        self.assertEqual(response.data['description'], 'Updated description for smartphones')

    def test_delete_category_admin(self):
        """Test deleting a category as admin."""
        category_to_delete = Category.objects.create(
            name='Delete Me',
            description='Category to be deleted'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('category-detail', kwargs={'slug': category_to_delete.slug})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        category_to_delete.refresh_from_db()
        self.assertTrue(category_to_delete.is_deleted)

    def test_root_categories_endpoint(self):
        """Test the root categories endpoint."""
        url = reverse('category-root-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return categories without parent
        for category in response.data['results']:
            self.assertIsNone(category['parent'])

    def test_category_children_endpoint(self):
        """Test the category children endpoint."""
        url = reverse('category-children', kwargs={'slug': self.parent_category.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Smartphones')

    def test_category_products_endpoint(self):
        """Test the category products endpoint."""
        url = reverse('category-products', kwargs={'slug': self.child_category.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return active products for anonymous users
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        self.assertNotIn('Old Phone', product_names)  # inactive
        self.assertNotIn('Draft Product', product_names)  # draft status

    def test_category_search(self):
        """Test category search functionality."""
        url = reverse('category-list')
        response = self.client.get(url, {'search': 'smart'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertIn('Smartphones', category_names)
        self.assertNotIn('Electronics', category_names)

    def test_category_filtering(self):
        """Test category filtering."""
        url = reverse('category-list')
        
        # Filter by parent
        response = self.client.get(url, {'parent': self.parent_category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Smartphones')
        
        # Filter root categories
        response = self.client.get(url, {'is_root': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for category in response.data['results']:
            self.assertIsNone(category['parent'])


class ProductAPITest(ProductAPITestCase):
    """Test cases for Product API endpoints."""

    def test_list_products_anonymous(self):
        """Test listing products as anonymous user."""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should only see active products with active status
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        self.assertNotIn('Old Phone', product_names)  # inactive
        self.assertNotIn('Draft Product', product_names)  # draft status

    def test_list_products_admin(self):
        """Test listing products as admin user."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin should see all products
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        self.assertIn('Old Phone', product_names)
        self.assertIn('Draft Product', product_names)

    def test_retrieve_product_by_slug(self):
        """Test retrieving a specific product by slug."""
        url = reverse('product-detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 15')
        self.assertEqual(response.data['slug'], 'iphone-15')
        self.assertEqual(response.data['sku'], 'IPHONE15-001')
        self.assertEqual(float(response.data['price']), 999.99)
        self.assertEqual(float(response.data['discount_price']), 899.99)
        self.assertEqual(float(response.data['effective_price']), 899.99)
        self.assertIn('category', response.data)
        self.assertIn('images', response.data)
        self.assertEqual(len(response.data['images']), 1)

    def test_create_product_admin(self):
        """Test creating a product as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'A new product for testing',
            'short_description': 'New test product',
            'category_id': str(self.child_category.id),
            'brand': 'TestBrand',
            'sku': 'NEW-001',
            'price': '199.99',
            'weight': '0.5',
            'is_active': True,
            'status': 'active',
            'tags': 'test, new, product'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')
        self.assertEqual(response.data['slug'], 'new-product')
        self.assertEqual(response.data['sku'], 'NEW-001')

    def test_create_product_unauthorized(self):
        """Test creating a product as regular user (should fail)."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('product-list')
        data = {
            'name': 'Unauthorized Product',
            'category_id': str(self.child_category.id),
            'sku': 'UNAUTH-001',
            'price': '99.99'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_duplicate_sku(self):
        """Test creating a product with duplicate SKU (should fail)."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'Duplicate SKU Product',
            'category_id': str(self.child_category.id),
            'sku': 'IPHONE15-001',  # Same as existing product
            'price': '99.99'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sku', response.data)

    def test_create_product_invalid_category(self):
        """Test creating a product with invalid category."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'Invalid Category Product',
            'category_id': str(self.inactive_category.id),  # Inactive category
            'sku': 'INVALID-001',
            'price': '99.99'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category_id', response.data)

    def test_update_product_admin(self):
        """Test updating a product as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'slug': self.active_product.slug})
        data = {
            'name': 'Updated iPhone 15',
            'price': '1099.99',
            'discount_price': '999.99'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated iPhone 15')
        self.assertEqual(float(response.data['price']), 1099.99)
        self.assertEqual(float(response.data['discount_price']), 999.99)

    def test_delete_product_admin(self):
        """Test deleting a product as admin."""
        product_to_delete = Product.objects.create(
            name='Delete Me',
            category=self.child_category,
            sku='DELETE-001',
            price=Decimal('99.99')
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'slug': product_to_delete.slug})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        product_to_delete.refresh_from_db()
        self.assertTrue(product_to_delete.is_deleted)

    def test_product_search(self):
        """Test product search functionality."""
        url = reverse('product-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'iPhone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        
        # Search by brand
        response = self.client.get(url, {'search': 'Apple'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        
        # Search by tags
        response = self.client.get(url, {'search': 'smartphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)

    def test_product_filtering(self):
        """Test product filtering functionality."""
        url = reverse('product-list')
        
        # Filter by category
        response = self.client.get(url, {'category': self.child_category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertEqual(product['category']['id'], str(self.child_category.id))
        
        # Filter by brand
        response = self.client.get(url, {'brand': 'Apple'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertEqual(product['brand'], 'Apple')
        
        # Filter by price range
        response = self.client.get(url, {'min_price': '500', 'max_price': '1000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            price = float(product['price'])
            self.assertGreaterEqual(price, 500)
            self.assertLessEqual(price, 1000)
        
        # Filter featured products
        response = self.client.get(url, {'is_featured': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertTrue(product['is_featured'])
        
        # Filter products with discount
        response = self.client.get(url, {'has_discount': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertIsNotNone(product['discount_price'])

    def test_product_ordering(self):
        """Test product ordering functionality."""
        url = reverse('product-list')
        
        # Order by price ascending
        response = self.client.get(url, {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices))
        
        # Order by price descending
        response = self.client.get(url, {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
        
        # Order by name
        response = self.client.get(url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [prod['name'] for prod in response.data['results']]
        self.assertEqual(names, sorted(names))

    def test_featured_products_endpoint(self):
        """Test the featured products endpoint."""
        url = reverse('product-featured')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertTrue(product['is_featured'])

    def test_on_sale_products_endpoint(self):
        """Test the on sale products endpoint."""
        url = reverse('product-on-sale')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for product in response.data['results']:
            self.assertIsNotNone(product['discount_price'])

    def test_brands_endpoint(self):
        """Test the brands endpoint."""
        url = reverse('product-brands')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Check if Apple brand is in the list
        brand_names = [brand['brand'] for brand in response.data]
        self.assertIn('Apple', brand_names)

    def test_price_range_endpoint(self):
        """Test the price range endpoint."""
        url = reverse('product-price-range')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('min_price', response.data)
        self.assertIn('max_price', response.data)
        self.assertIsNotNone(response.data['min_price'])
        self.assertIsNotNone(response.data['max_price'])

    def test_search_suggestions_endpoint(self):
        """Test the search suggestions endpoint."""
        url = reverse('product-search-suggestions')
        
        # Test with valid query
        response = self.client.get(url, {'q': 'iph'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('products', response.data)
        self.assertIn('brands', response.data)
        self.assertIn('categories', response.data)
        
        # Test with short query (should return empty)
        response = self.client.get(url, {'q': 'i'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        
        # Test with no query
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_toggle_featured_endpoint(self):
        """Test the toggle featured endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-toggle-featured', kwargs={'slug': self.active_product.slug})
        
        # Product is currently featured, toggle should make it not featured
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_featured'])
        
        # Toggle again should make it featured
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_featured'])

    def test_toggle_featured_unauthorized(self):
        """Test toggle featured endpoint without admin permissions."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('product-toggle-featured', kwargs={'slug': self.active_product.slug})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_active_endpoint(self):
        """Test the toggle active endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-toggle-active', kwargs={'slug': self.active_product.slug})
        
        # Product is currently active, toggle should make it inactive
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        
        # Toggle again should make it active
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])

    def test_pagination(self):
        """Test pagination functionality."""
        # Create more products to test pagination
        for i in range(25):
            Product.objects.create(
                name=f'Test Product {i}',
                category=self.child_category,
                sku=f'TEST-{i:03d}',
                price=Decimal('99.99'),
                is_active=True,
                status='active'
            )
        
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Default page size should be 20
        self.assertLessEqual(len(response.data['results']), 20)
        
        # Test custom page size
        response = self.client.get(url, {'page_size': '10'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 10)

    def test_complex_filtering_combination(self):
        """Test complex filtering with multiple parameters."""
        url = reverse('product-list')
        
        # Combine multiple filters
        params = {
            'category': self.child_category.id,
            'brand': 'Apple',
            'min_price': '500',
            'max_price': '1500',
            'is_featured': 'true',
            'has_discount': 'true',
            'search': 'iPhone',
            'ordering': '-price'
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all filters are applied
        for product in response.data['results']:
            self.assertEqual(product['category']['id'], str(self.child_category.id))
            self.assertEqual(product['brand'], 'Apple')
            self.assertGreaterEqual(float(product['price']), 500)
            self.assertLessEqual(float(product['price']), 1500)
            self.assertTrue(product['is_featured'])
            self.assertIsNotNone(product['discount_price'])
            self.assertIn('iPhone', product['name'])


class ProductFilterTest(ProductAPITestCase):
    """Test cases specifically for product filtering functionality."""

    def setUp(self):
        """Set up additional test data for filtering."""
        super().setUp()
        
        # Create additional categories and products for comprehensive filtering tests
        self.books_category = Category.objects.create(
            name='Books',
            description='Books and literature',
            is_active=True
        )
        
        self.book_product = Product.objects.create(
            name='Python Programming Book',
            description='Learn Python programming',
            category=self.books_category,
            brand='TechBooks',
            sku='BOOK-001',
            price=Decimal('49.99'),
            weight=Decimal('0.5'),
            is_active=True,
            status='active',
            tags='book, programming, python, education'
        )
        
        self.expensive_product = Product.objects.create(
            name='Luxury Watch',
            description='Premium luxury watch',
            category=self.parent_category,
            brand='LuxuryBrand',
            sku='WATCH-001',
            price=Decimal('2999.99'),
            discount_price=Decimal('2499.99'),
            weight=Decimal('0.3'),
            is_active=True,
            status='active',
            is_featured=True
        )

    def test_category_tree_filtering(self):
        """Test filtering by category tree (including descendants)."""
        url = reverse('product-list')
        
        # Filter by parent category should include products from child categories
        response = self.client.get(url, {'category_tree': 'Electronics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)  # From child category
        self.assertIn('Luxury Watch', product_names)  # From parent category

    def test_effective_price_filtering(self):
        """Test filtering by effective price (considering discounts)."""
        url = reverse('product-list')
        
        # Filter by effective price range
        response = self.client.get(url, {
            'min_effective_price': '800',
            'max_effective_price': '1000'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            effective_price = float(product['effective_price'])
            self.assertGreaterEqual(effective_price, 800)
            self.assertLessEqual(effective_price, 1000)

    def test_tags_filtering(self):
        """Test filtering by tags."""
        url = reverse('product-list')
        
        # Filter by single tag
        response = self.client.get(url, {'tags': 'smartphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        
        # Filter by multiple tags
        response = self.client.get(url, {'tags': 'programming,python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('Python Programming Book', product_names)

    def test_weight_filtering(self):
        """Test filtering by weight range."""
        url = reverse('product-list')
        
        response = self.client.get(url, {
            'min_weight': '0.1',
            'max_weight': '0.4'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            # Note: weight might not be in the list serializer, so we check the actual product
            product_obj = Product.objects.get(slug=product['slug'])
            if product_obj.weight:
                self.assertGreaterEqual(float(product_obj.weight), 0.1)
                self.assertLessEqual(float(product_obj.weight), 0.4)

    def test_date_filtering(self):
        """Test filtering by creation/update dates."""
        url = reverse('product-list')
        
        # Filter by creation date
        from django.utils import timezone
        from datetime import timedelta
        
        yesterday = timezone.now() - timedelta(days=1)
        tomorrow = timezone.now() + timedelta(days=1)
        
        response = self.client.get(url, {
            'created_after': yesterday.isoformat(),
            'created_before': tomorrow.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All products should be within the date range
        self.assertGreater(len(response.data['results']), 0)

    def test_multiple_brand_filtering(self):
        """Test filtering by multiple brands."""
        url = reverse('product-list')
        
        response = self.client.get(url, {'brand_in': 'Apple,TechBooks'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        brands = [prod['brand'] for prod in response.data['results']]
        for brand in brands:
            self.assertIn(brand, ['Apple', 'TechBooks'])

    def test_status_filtering(self):
        """Test filtering by product status."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        
        # Filter by single status
        response = self.client.get(url, {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            # Note: status might not be in list serializer for non-admin
            product_obj = Product.objects.get(slug=product['slug'])
            self.assertEqual(product_obj.status, 'active')
        
        # Filter by multiple statuses
        response = self.client.get(url, {'status_in': 'active,draft'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            product_obj = Product.objects.get(slug=product['slug'])
            self.assertIn(product_obj.status, ['active', 'draft'])

    def test_sku_filtering(self):
        """Test filtering by SKU."""
        url = reverse('product-list')
        
        # Exact SKU match
        response = self.client.get(url, {'sku': 'IPHONE15-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['sku'], 'IPHONE15-001')
        
        # SKU contains
        response = self.client.get(url, {'sku_contains': 'IPHONE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            self.assertIn('IPHONE', product['sku'])

    def test_advanced_search_filtering(self):
        """Test advanced search with multiple terms."""
        url = reverse('product-list')
        
        # Search with multiple terms (should use AND logic)
        response = self.client.get(url, {'search': 'iPhone Apple'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should find products that contain both terms
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertIn('iPhone 15', product_names)
        
        # Search that should return no results
        response = self.client.get(url, {'search': 'iPhone Book'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)