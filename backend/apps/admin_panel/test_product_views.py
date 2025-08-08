"""
Tests for the comprehensive product management views.
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category, ProductImage
from apps.admin_panel.models import AdminUser
from apps.admin_panel.product_models import (
    ProductVariant, ProductBundle, ProductLifecycle, ProductAnalytics
)

User = get_user_model()


class ProductViewSetTestCase(APITestCase):
    """Test cases for ComprehensiveProductViewSet."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = AdminUser.objects.create(
            username='testadmin',
            email='admin@test.com',
            role='admin'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            category=self.category,
            sku='TEST-001',
            price=Decimal('99.99'),
            is_active=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_product_list(self):
        """Test product list endpoint."""
        url = reverse('admin_panel:admin-products-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
    
    def test_product_detail(self):
        """Test product detail endpoint."""
        url = reverse('admin_panel:admin-products-detail', kwargs={'pk': self.product.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')
        self.assertEqual(response.data['sku'], 'TEST-001')
    
    def test_product_create(self):
        """Test product creation."""
        url = reverse('admin_panel:admin-products-list')
        data = {
            'name': 'New Test Product',
            'description': 'New test product description',
            'category': self.category.id,
            'sku': 'TEST-002',
            'price': '149.99',
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        
        new_product = Product.objects.get(sku='TEST-002')
        self.assertEqual(new_product.name, 'New Test Product')
        self.assertEqual(new_product.price, Decimal('149.99'))
    
    def test_product_update(self):
        """Test product update."""
        url = reverse('admin_panel:admin-products-detail', kwargs={'pk': self.product.pk})
        data = {
            'name': 'Updated Test Product',
            'description': 'Updated description',
            'category': self.category.id,
            'sku': 'TEST-001',
            'price': '199.99',
            'is_active': True
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Test Product')
        self.assertEqual(self.product.price, Decimal('199.99'))
    
    def test_product_delete(self):
        """Test product deletion."""
        url = reverse('admin_panel:admin-products-detail', kwargs={'pk': self.product.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)
    
    def test_bulk_operations_activate(self):
        """Test bulk activate operation."""
        # Create additional products
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test product 2 description',
            category=self.category,
            sku='TEST-002',
            price=Decimal('79.99'),
            is_active=False
        )
        
        url = reverse('admin_panel:admin-products-bulk-operations')
        data = {
            'product_ids': [self.product.id, product2.id],
            'operation': 'activate'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check products are activated
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertTrue(self.product.is_active)
        self.assertTrue(product2.is_active)
    
    def test_product_analytics(self):
        """Test product analytics endpoint."""
        # Create analytics for the product
        ProductAnalytics.objects.create(
            product=self.product,
            total_sales=100,
            total_revenue=Decimal('9999.00'),
            view_count=500
        )
        
        url = reverse('admin_panel:admin-products-analytics', kwargs={'pk': self.product.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sales'], 100)
        self.assertEqual(response.data['view_count'], 500)
    
    def test_lifecycle_transition(self):
        """Test product lifecycle transition."""
        # Create lifecycle for the product
        ProductLifecycle.objects.create(
            product=self.product,
            current_stage='draft'
        )
        
        url = reverse('admin_panel:admin-products-lifecycle-transition', kwargs={'pk': self.product.pk})
        data = {
            'stage': 'active',
            'notes': 'Transitioning to active stage'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check lifecycle was updated
        lifecycle = ProductLifecycle.objects.get(product=self.product)
        self.assertEqual(lifecycle.current_stage, 'active')
    
    def test_product_filtering(self):
        """Test product filtering."""
        # Create additional products for filtering
        Product.objects.create(
            name='Inactive Product',
            slug='inactive-product',
            description='Inactive product description',
            category=self.category,
            sku='INACTIVE-001',
            price=Decimal('49.99'),
            is_active=False
        )
        
        # Test filtering by active status
        url = reverse('admin_panel:admin-products-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
        
        # Test filtering by category
        response = self.client.get(url, {'category': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_product_comparison(self):
        """Test product comparison endpoint."""
        # Create additional product
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test product 2 description',
            category=self.category,
            sku='TEST-002',
            price=Decimal('79.99'),
            is_active=True
        )
        
        url = reverse('admin_panel:admin-products-compare-products')
        data = {
            'product_ids': [self.product.id, product2.id],
            'comparison_fields': ['name', 'price', 'category']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['name'], 'Test Product')
        self.assertEqual(response.data['products'][1]['name'], 'Test Product 2')


class ProductVariantViewSetTestCase(APITestCase):
    """Test cases for ProductVariantViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            category=self.category,
            sku='TEST-001',
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_variant_creation(self):
        """Test product variant creation."""
        url = reverse('admin_panel:admin-product-variants-list')
        data = {
            'product': self.product.id,
            'name': 'Red Large',
            'attributes': {'color': 'red', 'size': 'large'},
            'price': '109.99',
            'cost_price': '60.00',
            'stock_quantity': 50,
            'is_default': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductVariant.objects.count(), 1)
        
        variant = ProductVariant.objects.first()
        self.assertEqual(variant.name, 'Red Large')
        self.assertEqual(variant.attributes['color'], 'red')
        self.assertTrue(variant.is_default)
    
    def test_bulk_variant_creation(self):
        """Test bulk variant creation."""
        url = reverse('admin_panel:admin-product-variants-bulk-create')
        data = {
            'product_id': self.product.id,
            'variants': [
                {
                    'name': 'Red Small',
                    'attributes': {'color': 'red', 'size': 'small'},
                    'price': '99.99',
                    'cost_price': '55.00',
                    'stock_quantity': 30
                },
                {
                    'name': 'Blue Large',
                    'attributes': {'color': 'blue', 'size': 'large'},
                    'price': '109.99',
                    'cost_price': '60.00',
                    'stock_quantity': 25
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['created_count'], 2)
        self.assertEqual(ProductVariant.objects.count(), 2)


class ProductAnalyticsViewSetTestCase(APITestCase):
    """Test cases for ProductAnalyticsViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            category=self.category,
            sku='TEST-001',
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.analytics = ProductAnalytics.objects.create(
            product=self.product,
            total_sales=150,
            total_revenue=Decimal('14999.50'),
            view_count=750,
            conversion_rate=Decimal('0.2000')
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoint."""
        url = reverse('admin_panel:admin-product-analytics-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_products', response.data)
        self.assertIn('overall_metrics', response.data)
        self.assertEqual(len(response.data['top_products']), 1)