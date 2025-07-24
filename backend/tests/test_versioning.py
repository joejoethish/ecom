"""
Tests for API versioning functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from apps.authentication.models import User
from apps.products.models import Product, Category


class APIVersioningTestCase(TestCase):
    """Test case for API versioning functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Create test admin user
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            short_description='Short description',
            price=99.99,
            category=self.category,
            brand='Test Brand',
            sku='TEST-SKU-001'
        )
        
        # Set up clients
        self.client = Client()
        self.admin_client = Client()
        self.admin_client.login(email='admin@example.com', password='adminpassword')

    def test_url_path_versioning(self):
        """Test URL path versioning."""
        # Test v1 endpoint
        response_v1 = self.client.get('/api/v1/products/')
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['X-API-Version'], 'v1')
        
        # Test v2 endpoint
        response_v2 = self.client.get('/api/v2/products/')
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2['X-API-Version'], 'v2')
        
        # Verify different response structures between versions
        data_v1 = json.loads(response_v1.content)
        data_v2 = json.loads(response_v2.content)
        
        # Check if v2 has additional fields compared to v1
        if data_v1['results'] and data_v2['results']:
            v1_product = data_v1['results'][0]
            v2_product = data_v2['results'][0]
            
            # V2 should have additional fields like rating_average
            self.assertNotIn('rating_average', v1_product)
            self.assertIn('rating_average', v2_product)

    def test_accept_header_versioning(self):
        """Test Accept header versioning."""
        # Test with v1 Accept header
        response_v1 = self.client.get(
            '/api/v1/products/',
            HTTP_ACCEPT='application/json; version=v1'
        )
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['X-API-Version'], 'v1')
        
        # Test with v2 Accept header
        response_v2 = self.client.get(
            '/api/v1/products/',
            HTTP_ACCEPT='application/json; version=v2'
        )
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2['X-API-Version'], 'v2')
        
        # Test with vendor specific media type
        response_v2_vendor = self.client.get(
            '/api/v1/products/',
            HTTP_ACCEPT='application/vnd.ecommerce.v2+json'
        )
        self.assertEqual(response_v2_vendor.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2_vendor['X-API-Version'], 'v2')

    def test_custom_header_versioning(self):
        """Test custom header versioning."""
        # Test with v1 custom header
        response_v1 = self.client.get(
            '/api/v1/products/',
            HTTP_X_API_VERSION='v1'
        )
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['X-API-Version'], 'v1')
        
        # Test with v2 custom header
        response_v2 = self.client.get(
            '/api/v1/products/',
            HTTP_X_API_VERSION='v2'
        )
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2['X-API-Version'], 'v2')

    def test_version_specific_endpoints(self):
        """Test version-specific endpoints."""
        # Test v2-only endpoint (trending products)
        response_v2 = self.client.get('/api/v2/products/trending/')
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        
        # Same endpoint should not exist in v1
        response_v1 = self.client.get('/api/v1/products/trending/')
        self.assertEqual(response_v1.status_code, status.HTTP_404_NOT_FOUND)

    def test_version_headers(self):
        """Test version headers in responses."""
        response = self.client.get('/api/v2/products/')
        
        # Check for version headers
        self.assertEqual(response['X-API-Version'], 'v2')
        self.assertIn('X-API-Supported-Versions', response)
        
        # Check for recommended version header (only present for deprecated versions)
        self.assertNotIn('X-API-Recommended-Version', response)

    def test_authentication_versioning(self):
        """Test authentication endpoints with versioning."""
        # Test login endpoint in v1
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        response_v1 = self.client.post(
            '/api/v1/auth/login/',
            data=login_data,
            content_type='application/json'
        )
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['X-API-Version'], 'v1')
        
        # Test login endpoint in v2
        response_v2 = self.client.post(
            '/api/v2/auth/login/',
            data=login_data,
            content_type='application/json'
        )
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2['X-API-Version'], 'v2')

    def test_invalid_version(self):
        """Test invalid version handling."""
        # Test with invalid version in URL
        response = self.client.get('/api/v999/products/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test with invalid version in header (should default to v1)
        response = self.client.get(
            '/api/v1/products/',
            HTTP_X_API_VERSION='v999'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-API-Version'], 'v1')  # Should default to v1