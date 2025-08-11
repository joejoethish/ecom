# Unit tests for Django views and API endpoints
import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
from decimal import Decimal

User = get_user_model()

class BaseAPITestCase(APITestCase):
    """Base test case for API testing"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='testpass123'
        )
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def authenticate_user(self):
        """Authenticate as regular user"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

class AuthenticationViewTest(BaseAPITestCase):
    """Test authentication views"""
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        url = reverse('admin_login')
        data = {
            'username': 'admin_test',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials"""
        url = reverse('admin_login')
        data = {
            'username': 'admin_test',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_admin_login_non_staff_user(self):
        """Test admin login with non-staff user"""
        url = reverse('admin_login')
        data = {
            'username': 'user_test',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_token_refresh(self):
        """Test JWT token refresh"""
        refresh = RefreshToken.for_user(self.admin_user)
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_admin_logout(self):
        """Test admin logout"""
        self.authenticate_admin()
        url = reverse('admin_logout')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class DashboardViewTest(BaseAPITestCase):
    """Test dashboard views"""
    
    def test_dashboard_stats_authenticated(self):
        """Test dashboard stats with authentication"""
        self.authenticate_admin()
        url = reverse('dashboard_stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orders', response.data)
        self.assertIn('total_revenue', response.data)
        self.assertIn('total_customers', response.data)
        self.assertIn('total_products', response.data)
    
    def test_dashboard_stats_unauthenticated(self):
        """Test dashboard stats without authentication"""
        url = reverse('dashboard_stats')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_charts_data(self):
        """Test dashboard charts data"""
        self.authenticate_admin()
        url = reverse('dashboard_charts')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sales_chart', response.data)
        self.assertIn('orders_chart', response.data)

class ProductViewTest(BaseAPITestCase):
    """Test product CRUD views"""
    
    def setUp(self):
        super().setUp()
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test product description',
            'price': '99.99',
            'sku': 'TEST-SKU-001',
            'stock_quantity': 100
        }
    
    def test_product_list_view(self):
        """Test product list view"""
        self.authenticate_admin()
        url = reverse('product_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
    
    def test_product_create_view(self):
        """Test product creation"""
        self.authenticate_admin()
        url = reverse('product_list')
        
        response = self.client.post(url, self.product_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], self.product_data['name'])
        self.assertEqual(response.data['sku'], self.product_data['sku'])
    
    def test_product_create_invalid_data(self):
        """Test product creation with invalid data"""
        self.authenticate_admin()
        url = reverse('product_list')
        
        invalid_data = self.product_data.copy()
        invalid_data['price'] = 'invalid_price'
        
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_product_detail_view(self):
        """Test product detail view"""
        from apps.products.models import Product
        
        self.authenticate_admin()
        product = Product.objects.create(**self.product_data)
        url = reverse('product_detail', kwargs={'pk': product.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], product.name)
    
    def test_product_update_view(self):
        """Test product update"""
        from apps.products.models import Product
        
        self.authenticate_admin()
        product = Product.objects.create(**self.product_data)
        url = reverse('product_detail', kwargs={'pk': product.pk})
        
        update_data = {'name': 'Updated Product Name'}
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Product Name')
    
    def test_product_delete_view(self):
        """Test product deletion"""
        from apps.products.models import Product
        
        self.authenticate_admin()
        product = Product.objects.create(**self.product_data)
        url = reverse('product_detail', kwargs={'pk': product.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
    
    def test_product_bulk_operations(self):
        """Test product bulk operations"""
        self.authenticate_admin()
        url = reverse('product_bulk')
        
        bulk_data = {
            'action': 'delete',
            'ids': [1, 2, 3]
        }
        
        response = self.client.post(url, bulk_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class OrderViewTest(BaseAPITestCase):
    """Test order management views"""
    
    def setUp(self):
        super().setUp()
        self.order_data = {
            'customer': self.regular_user.id,
            'total_amount': '150.00',
            'status': 'pending'
        }
    
    def test_order_list_view(self):
        """Test order list view"""
        self.authenticate_admin()
        url = reverse('order_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_order_detail_view(self):
        """Test order detail view"""
        from apps.orders.models import Order
        
        self.authenticate_admin()
        order = Order.objects.create(**self.order_data)
        url = reverse('order_detail', kwargs={'pk': order.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], order.status)
    
    def test_order_status_update(self):
        """Test order status update"""
        from apps.orders.models import Order
        
        self.authenticate_admin()
        order = Order.objects.create(**self.order_data)
        url = reverse('order_status_update', kwargs={'pk': order.pk})
        
        update_data = {'status': 'confirmed'}
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')

class PermissionViewTest(BaseAPITestCase):
    """Test permission-based view access"""
    
    def test_admin_only_view_access(self):
        """Test admin-only view access"""
        # Test with admin user
        self.authenticate_admin()
        url = reverse('admin_settings')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test with regular user
        self.authenticate_user()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_permission_required_decorator(self):
        """Test permission required decorator"""
        # This would test custom permission decorators
        pass

class ValidationViewTest(BaseAPITestCase):
    """Test view validation"""
    
    def test_input_validation(self):
        """Test input validation"""
        self.authenticate_admin()
        url = reverse('product_list')
        
        # Test with missing required fields
        invalid_data = {'name': ''}
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
    
    def test_data_sanitization(self):
        """Test data sanitization"""
        self.authenticate_admin()
        url = reverse('product_list')
        
        # Test with potentially malicious input
        malicious_data = {
            'name': '<script>alert("xss")</script>',
            'description': 'Normal description',
            'price': '99.99',
            'sku': 'TEST-SKU-002'
        }
        
        response = self.client.post(url, malicious_data, format='json')
        
        # Should either reject or sanitize the input
        if response.status_code == status.HTTP_201_CREATED:
            self.assertNotIn('<script>', response.data['name'])

class ErrorHandlingViewTest(BaseAPITestCase):
    """Test error handling in views"""
    
    def test_404_error_handling(self):
        """Test 404 error handling"""
        self.authenticate_admin()
        url = reverse('product_detail', kwargs={'pk': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_500_error_handling(self):
        """Test 500 error handling"""
        # This would test how your views handle server errors
        pass
    
    @patch('apps.products.views.ProductViewSet.list')
    def test_database_error_handling(self, mock_list):
        """Test database error handling"""
        mock_list.side_effect = Exception('Database connection error')
        
        self.authenticate_admin()
        url = reverse('product_list')
        
        response = self.client.get(url)
        
        # Should handle the error gracefully
        self.assertIn(response.status_code, [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE])

class PerformanceViewTest(BaseAPITestCase):
    """Test view performance"""
    
    def test_pagination_performance(self):
        """Test pagination performance"""
        from apps.products.models import Product
        
        # Create test data
        products = []
        for i in range(100):
            products.append(Product(
                name=f'Product {i}',
                price=Decimal('10.00'),
                sku=f'SKU-{i:03d}'
            ))
        Product.objects.bulk_create(products)
        
        self.authenticate_admin()
        url = reverse('product_list')
        
        # Test first page
        response = self.client.get(url + '?page=1&page_size=20')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
    
    def test_query_optimization(self):
        """Test query optimization"""
        # This would test that views use select_related, prefetch_related, etc.
        pass

@pytest.mark.django_db
class AsyncViewTest:
    """Test async views (if using async views)"""
    
    @pytest.mark.asyncio
    async def test_async_view_response(self):
        """Test async view response"""
        # This would test async views if you're using them
        pass