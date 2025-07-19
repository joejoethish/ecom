"""
Tests for customer views and API endpoints.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.customers.services import CustomerService
from apps.products.models import Product, Category

User = get_user_model()


class CustomerProfileViewTest(APITestCase):
    """Test cases for CustomerProfileView."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_get_customer_profile_authenticated(self):
        """Test getting customer profile when authenticated."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'test@example.com')
        self.assertEqual(response.data['data']['full_name'], 'John Doe')
    
    def test_get_customer_profile_unauthenticated(self):
        """Test getting customer profile when not authenticated."""
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_customer_profile(self):
        """Test creating customer profile."""
        # Create user without profile
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=new_user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': '+1234567890',
            'gender': 'M',
            'newsletter_subscription': False
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['phone_number'], '+1234567890')
    
    def test_create_customer_profile_already_exists(self):
        """Test creating profile when one already exists."""
        CustomerService.create_customer_profile(self.user)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        
        data = {'phone_number': '+1234567890'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_update_customer_profile(self):
        """Test updating customer profile."""
        CustomerService.create_customer_profile(self.user)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': '+9876543210',
            'gender': 'F',
            'newsletter_subscription': False
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['phone_number'], '+9876543210')
        self.assertEqual(response.data['data']['gender'], 'F')
    
    @patch('apps.customers.views.logger')
    def test_get_customer_profile_error_handling(self, mock_logger):
        """Test error handling in get customer profile."""
        # Mock an exception in the service
        with patch('apps.customers.services.CustomerService.get_or_create_customer_profile') as mock_service:
            mock_service.side_effect = Exception('Database error')
            
            self.client.force_authenticate(user=self.user)
            url = reverse('customer-profile')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertFalse(response.data['success'])
            mock_logger.error.assert_called_once()


class AddressViewTest(APITestCase):
    """Test cases for Address views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
        
        self.address_data = {
            'type': 'HOME',
            'first_name': 'John',
            'last_name': 'Doe',
            'address_line_1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001',
            'country': 'USA',
            'phone': '+1234567890'
        }
    
    def test_get_customer_addresses(self):
        """Test getting customer addresses."""
        # Create test address
        Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['city'], 'New York')
    
    def test_create_address(self):
        """Test creating a new address."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        
        response = self.client.post(url, self.address_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['city'], 'New York')
    
    def test_create_address_validation_error(self):
        """Test creating address with validation errors."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        
        invalid_data = self.address_data.copy()
        invalid_data['postal_code'] = 'invalid@postal'
        
        response = self.client.post(url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_get_specific_address(self):
        """Test getting a specific address."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['city'], 'New York')
    
    def test_update_address(self):
        """Test updating an address."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        
        update_data = {
            'city': 'Boston',
            'state': 'MA',
            'postal_code': '02101'
        }
        
        response = self.client.put(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['city'], 'Boston')
    
    def test_delete_address(self):
        """Test deleting an address."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify address is deleted
        self.assertFalse(Address.objects.filter(id=address.id).exists())
    
    def test_access_other_customer_address(self):
        """Test that customer cannot access another customer's address."""
        # Create another customer
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_customer = CustomerService.create_customer_profile(other_user)
        
        # Create address for other customer
        other_address = Address.objects.create(
            customer=other_customer,
            **self.address_data
        )
        
        # Try to access other customer's address
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': other_address.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_set_default_address(self):
        """Test setting an address as default."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('set-default-address', kwargs={'address_id': address.id})
        
        data = {'type': 'all'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['is_default'])


class WishlistViewTest(APITestCase):
    """Test cases for Wishlist views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
        
        # Create test product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('99.99'),
            category=self.category,
            sku='TEST-001'
        )
    
    def test_get_wishlist(self):
        """Test getting customer wishlist."""
        # Add item to wishlist
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product,
            notes='Want to buy this'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'My Wishlist')
        self.assertEqual(len(response.data['data']['items']), 1)
    
    def test_add_to_wishlist(self):
        """Test adding product to wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        data = {
            'product_id': self.product.id,
            'notes': 'Want to buy this'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['notes'], 'Want to buy this')
    
    def test_add_invalid_product_to_wishlist(self):
        """Test adding non-existent product to wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        data = {
            'product_id': 99999,  # Non-existent product
            'notes': 'Want to buy this'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_remove_from_wishlist(self):
        """Test removing product from wishlist."""
        # Add product to wishlist first
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', kwargs={'product_id': self.product.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify item is removed
        self.assertFalse(WishlistItem.objects.filter(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        ).exists())
    
    def test_remove_nonexistent_from_wishlist(self):
        """Test removing product that's not in wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', kwargs={'product_id': self.product.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_check_wishlist(self):
        """Test checking if product is in wishlist."""
        # Add product to wishlist
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('check-wishlist', kwargs={'product_id': self.product.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['is_in_wishlist'])
    
    def test_clear_wishlist(self):
        """Test clearing entire wishlist."""
        # Add items to wishlist
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify wishlist is cleared
        self.assertEqual(self.customer_profile.wishlist.items.count(), 0)


class CustomerActivityViewTest(APITestCase):
    """Test cases for Customer Activity views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
    
    def test_get_customer_activities(self):
        """Test getting customer activities."""
        # Create some activities
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='User logged in'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Viewed product'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
    
    def test_get_customer_activities_filtered(self):
        """Test getting filtered customer activities."""
        # Create activities
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='User logged in'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Viewed product'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        response = self.client.get(url, {'type': 'LOGIN'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['activity_type'], 'LOGIN')
    
    def test_get_customer_analytics(self):
        """Test getting customer analytics."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_activities', response.data['data'])
        self.assertIn('customer_tier', response.data['data'])
    
    def test_log_customer_activity(self):
        """Test logging customer activity."""
        self.client.force_authenticate(user=self.user)
        url = reverse('log-customer-activity')
        
        data = {
            'activity_type': 'PRODUCT_VIEW',
            'description': 'Viewed test product',
            'metadata': {'page': 'product-detail'}
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['activity_type'], 'PRODUCT_VIEW')


class AdminCustomerViewTest(APITestCase):
    """Test cases for Admin Customer views."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customerpass123'
        )
        
        self.customer_profile = CustomerService.create_customer_profile(
            self.regular_user,
            phone_number='+1234567890'
        )
    
    def test_admin_customer_list(self):
        """Test admin customer list view."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_admin_customer_list_unauthorized(self):
        """Test admin customer list with non-admin user."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('admin-customer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_customer_detail(self):
        """Test admin customer detail view."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-detail', kwargs={'pk': self.customer_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'customer@example.com')
        self.assertIn('addresses', response.data)
        self.assertIn('wishlist', response.data)
    
    def test_admin_customer_status_update(self):
        """Test updating customer status by admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer_profile.id})
        
        data = {
            'action': 'suspend',
            'reason': 'Suspicious activity'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify status was updated
        self.customer_profile.refresh_from_db()
        self.assertEqual(self.customer_profile.account_status, 'SUSPENDED')
    
    def test_admin_customer_status_invalid_action(self):
        """Test updating customer status with invalid action."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer_profile.id})
        
        data = {'action': 'invalid_action'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class CustomerViewPermissionTest(APITestCase):
    """Test cases for customer view permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.customer1 = CustomerService.create_customer_profile(self.user1)
        self.customer2 = CustomerService.create_customer_profile(self.user2)
    
    def test_customer_cannot_access_other_profile(self):
        """Test that customers cannot access other customers' data."""
        # Create address for user2
        address = Address.objects.create(
            customer=self.customer2,
            type='HOME',
            first_name='Jane',
            last_name='Doe',
            address_line_1='456 Oak St',
            city='Boston',
            state='MA',
            postal_code='02101',
            country='USA'
        )
        
        # User1 tries to access user2's address
        self.client.force_authenticate(user=self.user1)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access customer endpoints."""
        urls = [
            reverse('customer-profile'),
            reverse('customer-addresses'),
            reverse('customer-wishlist'),
            reverse('customer-activities'),
            reverse('customer-analytics'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)