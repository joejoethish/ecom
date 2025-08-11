# Integration tests for API endpoints
import pytest
import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from unittest.mock import patch, Mock
import time

User = get_user_model()

class APIIntegrationTestCase(APITestCase):
    """Base class for API integration tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin_integration',
            email='admin@integration.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.authenticate()
    
    def authenticate(self):
        """Authenticate the client"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

class ProductManagementIntegrationTest(APIIntegrationTestCase):
    """Integration tests for product management workflow"""
    
    def test_complete_product_lifecycle(self):
        """Test complete product lifecycle from creation to deletion"""
        # Step 1: Create a product
        product_data = {
            'name': 'Integration Test Product',
            'description': 'Product for integration testing',
            'price': '99.99',
            'sku': 'INT-TEST-001',
            'stock_quantity': 50
        }
        
        create_response = self.client.post('/api/admin/products/', product_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        product_id = create_response.data['id']
        
        # Step 2: Retrieve the product
        get_response = self.client.get(f'/api/admin/products/{product_id}/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['name'], product_data['name'])
        
        # Step 3: Update the product
        update_data = {
            'name': 'Updated Integration Test Product',
            'price': '149.99'
        }
        update_response = self.client.patch(f'/api/admin/products/{product_id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['name'], update_data['name'])
        self.assertEqual(str(update_response.data['price']), update_data['price'])
        
        # Step 4: List products and verify our product is there
        list_response = self.client.get('/api/admin/products/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        product_ids = [p['id'] for p in list_response.data['results']]
        self.assertIn(product_id, product_ids)
        
        # Step 5: Delete the product
        delete_response = self.client.delete(f'/api/admin/products/{product_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Step 6: Verify product is deleted
        get_deleted_response = self.client.get(f'/api/admin/products/{product_id}/')
        self.assertEqual(get_deleted_response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_product_category_integration(self):
        """Test product and category integration"""
        # Create a category first
        category_data = {
            'name': 'Integration Test Category',
            'description': 'Category for integration testing'
        }
        category_response = self.client.post('/api/admin/categories/', category_data, format='json')
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)
        category_id = category_response.data['id']
        
        # Create a product with the category
        product_data = {
            'name': 'Categorized Product',
            'description': 'Product with category',
            'price': '79.99',
            'sku': 'CAT-PROD-001',
            'category': category_id
        }
        product_response = self.client.post('/api/admin/products/', product_data, format='json')
        self.assertEqual(product_response.status_code, status.HTTP_201_CREATED)
        
        # Verify the relationship
        product_id = product_response.data['id']
        get_response = self.client.get(f'/api/admin/products/{product_id}/')
        self.assertEqual(get_response.data['category'], category_id)

class OrderManagementIntegrationTest(APIIntegrationTestCase):
    """Integration tests for order management workflow"""
    
    def setUp(self):
        super().setUp()
        # Create a customer for orders
        self.customer = User.objects.create_user(
            username='customer_integration',
            email='customer@integration.com',
            password='testpass123'
        )
    
    def test_complete_order_workflow(self):
        """Test complete order workflow"""
        # Step 1: Create an order
        order_data = {
            'customer': self.customer.id,
            'total_amount': '199.99',
            'status': 'pending',
            'payment_status': 'pending'
        }
        
        create_response = self.client.post('/api/admin/orders/', order_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        order_id = create_response.data['id']
        
        # Step 2: Update order status
        status_update = {'status': 'confirmed'}
        update_response = self.client.patch(f'/api/admin/orders/{order_id}/', status_update, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['status'], 'confirmed')
        
        # Step 3: Process payment
        payment_update = {'payment_status': 'paid'}
        payment_response = self.client.patch(f'/api/admin/orders/{order_id}/', payment_update, format='json')
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment_response.data['payment_status'], 'paid')
        
        # Step 4: Ship the order
        shipping_update = {
            'status': 'shipped',
            'tracking_number': 'TRACK123456'
        }
        ship_response = self.client.patch(f'/api/admin/orders/{order_id}/', shipping_update, format='json')
        self.assertEqual(ship_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ship_response.data['status'], 'shipped')
    
    def test_order_with_items_integration(self):
        """Test order with order items integration"""
        # Create a product first
        product_data = {
            'name': 'Order Item Product',
            'price': '49.99',
            'sku': 'ORDER-ITEM-001',
            'stock_quantity': 100
        }
        product_response = self.client.post('/api/admin/products/', product_data, format='json')
        product_id = product_response.data['id']
        
        # Create an order
        order_data = {
            'customer': self.customer.id,
            'total_amount': '99.98',
            'status': 'pending'
        }
        order_response = self.client.post('/api/admin/orders/', order_data, format='json')
        order_id = order_response.data['id']
        
        # Add order items
        item_data = {
            'order': order_id,
            'product': product_id,
            'quantity': 2,
            'price': '49.99'
        }
        item_response = self.client.post('/api/admin/order-items/', item_data, format='json')
        self.assertEqual(item_response.status_code, status.HTTP_201_CREATED)

class UserManagementIntegrationTest(APIIntegrationTestCase):
    """Integration tests for user management"""
    
    def test_admin_user_management_workflow(self):
        """Test admin user management workflow"""
        # Create a new admin user
        user_data = {
            'username': 'new_admin',
            'email': 'newadmin@test.com',
            'password': 'newadminpass123',
            'is_staff': True,
            'role': 'manager'
        }
        
        create_response = self.client.post('/api/admin/users/', user_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        user_id = create_response.data['id']
        
        # Update user permissions
        permission_update = {
            'permissions': ['view_products', 'add_products', 'change_products']
        }
        update_response = self.client.patch(f'/api/admin/users/{user_id}/', permission_update, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Deactivate user
        deactivate_update = {'is_active': False}
        deactivate_response = self.client.patch(f'/api/admin/users/{user_id}/', deactivate_update, format='json')
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(deactivate_response.data['is_active'])

class ReportingIntegrationTest(APIIntegrationTestCase):
    """Integration tests for reporting functionality"""
    
    def test_sales_report_generation(self):
        """Test sales report generation"""
        # Create test data
        self._create_test_sales_data()
        
        # Generate sales report
        report_params = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'format': 'json'
        }
        
        response = self.client.get('/api/admin/reports/sales/', report_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sales', response.data)
        self.assertIn('order_count', response.data)
        self.assertIn('chart_data', response.data)
    
    def test_inventory_report_generation(self):
        """Test inventory report generation"""
        # Create test inventory data
        self._create_test_inventory_data()
        
        # Generate inventory report
        response = self.client.get('/api/admin/reports/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_products', response.data)
        self.assertIn('low_stock_items', response.data)
        self.assertIn('out_of_stock_items', response.data)
    
    def _create_test_sales_data(self):
        """Create test sales data"""
        # Create products and orders for testing
        pass
    
    def _create_test_inventory_data(self):
        """Create test inventory data"""
        # Create products with various stock levels
        pass

class SystemSettingsIntegrationTest(APIIntegrationTestCase):
    """Integration tests for system settings"""
    
    def test_settings_management_workflow(self):
        """Test settings management workflow"""
        # Get current settings
        get_response = self.client.get('/api/admin/settings/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        
        # Update settings
        settings_update = {
            'site_name': 'Updated Site Name',
            'email_notifications': True,
            'maintenance_mode': False
        }
        
        update_response = self.client.patch('/api/admin/settings/', settings_update, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Verify settings were updated
        verify_response = self.client.get('/api/admin/settings/')
        self.assertEqual(verify_response.data['site_name'], settings_update['site_name'])

class BulkOperationsIntegrationTest(APIIntegrationTestCase):
    """Integration tests for bulk operations"""
    
    def test_bulk_product_operations(self):
        """Test bulk product operations"""
        # Create multiple products
        products = []
        for i in range(5):
            product_data = {
                'name': f'Bulk Product {i}',
                'price': f'{10 + i}.99',
                'sku': f'BULK-{i:03d}',
                'stock_quantity': 10 + i
            }
            response = self.client.post('/api/admin/products/', product_data, format='json')
            products.append(response.data['id'])
        
        # Test bulk update
        bulk_update_data = {
            'action': 'update',
            'ids': products[:3],
            'data': {'status': 'inactive'}
        }
        
        bulk_response = self.client.post('/api/admin/products/bulk/', bulk_update_data, format='json')
        self.assertEqual(bulk_response.status_code, status.HTTP_200_OK)
        
        # Test bulk delete
        bulk_delete_data = {
            'action': 'delete',
            'ids': products[3:]
        }
        
        delete_response = self.client.post('/api/admin/products/bulk/', bulk_delete_data, format='json')
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)

class ErrorHandlingIntegrationTest(APIIntegrationTestCase):
    """Integration tests for error handling"""
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on errors"""
        # This would test that database transactions are properly rolled back on errors
        pass
    
    def test_api_error_responses(self):
        """Test API error responses"""
        # Test various error scenarios and ensure proper error responses
        
        # Test 404 error
        response = self.client.get('/api/admin/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        
        # Test validation error
        invalid_data = {'name': '', 'price': 'invalid'}
        response = self.client.post('/api/admin/products/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

class PerformanceIntegrationTest(APIIntegrationTestCase):
    """Integration tests for performance"""
    
    def test_api_response_times(self):
        """Test API response times"""
        # Create test data
        self._create_performance_test_data()
        
        # Test list endpoint performance
        start_time = time.time()
        response = self.client.get('/api/admin/products/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(end_time - start_time, 2.0)  # Should respond within 2 seconds
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Create large dataset
        self._create_large_dataset()
        
        # Test paginated response
        response = self.client.get('/api/admin/products/?page=1&page_size=50')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)
    
    def _create_performance_test_data(self):
        """Create data for performance testing"""
        # Create test products, orders, etc.
        pass
    
    def _create_large_dataset(self):
        """Create large dataset for testing"""
        # Create large number of records for testing
        pass

class SecurityIntegrationTest(APIIntegrationTestCase):
    """Integration tests for security"""
    
    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        # Remove authentication
        self.client.credentials()
        
        # Test various endpoints
        endpoints = [
            '/api/admin/products/',
            '/api/admin/orders/',
            '/api/admin/users/',
            '/api/admin/settings/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_enforcement(self):
        """Test permission enforcement"""
        # Create user with limited permissions
        limited_user = User.objects.create_user(
            username='limited_user',
            email='limited@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Authenticate as limited user
        refresh = RefreshToken.for_user(limited_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Test access to restricted endpoints
        response = self.client.get('/api/admin/settings/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test with potentially malicious input
        malicious_data = {
            'name': '<script>alert("xss")</script>',
            'description': '<?php echo "php injection"; ?>',
            'price': '99.99',
            'sku': 'SECURITY-TEST-001'
        }
        
        response = self.client.post('/api/admin/products/', malicious_data, format='json')
        
        if response.status_code == status.HTTP_201_CREATED:
            # Verify that malicious content was sanitized
            self.assertNotIn('<script>', response.data['name'])
            self.assertNotIn('<?php', response.data['description'])

@pytest.mark.django_db
class DatabaseIntegrationTest:
    """Integration tests for database operations"""
    
    def test_database_constraints(self):
        """Test database constraints"""
        # Test unique constraints, foreign key constraints, etc.
        pass
    
    def test_database_transactions(self):
        """Test database transactions"""
        # Test that transactions work correctly
        pass
    
    def test_database_performance(self):
        """Test database query performance"""
        # Test query performance with indexes, etc.
        pass