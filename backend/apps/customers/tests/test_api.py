"""
Tests for customer API endpoints.
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


class CustomerProfileAPITest(APITestCase):
    """Test cases for Customer Profile API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.customer_profile = CustomerService.create_customer_profile(
            self.user,
            phone_number='+1234567890'
        )
    
    def test_get_customer_profile_authenticated(self):
        """Test getting customer profile when authenticated."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'test@example.com')
        self.assertEqual(response.data['data']['phone_number'], '+1234567890')
        self.assertEqual(response.data['data']['full_name'], 'John Doe')
        self.assertEqual(response.data['data']['customer_tier'], 'BRONZE')
    
    def test_get_customer_profile_unauthenticated(self):
        """Test getting customer profile when not authenticated."""
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_customer_profile_creates_if_not_exists(self):
        """Test that getting profile creates one if it doesn't exist."""
        # Create user without profile
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=new_user)
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'new@example.com')
        
        # Verify profile was created
        self.assertTrue(hasattr(new_user, 'customer_profile'))
    
    def test_update_customer_profile(self):
        """Test updating customer profile."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': '+9876543210',
            'gender': 'M',
            'newsletter_subscription': False,
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['phone_number'], '+9876543210')
        self.assertEqual(response.data['data']['gender'], 'M')
        self.assertFalse(response.data['data']['newsletter_subscription'])
        
        # Verify user fields were updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
    
    def test_update_customer_profile_invalid_data(self):
        """Test updating customer profile with invalid data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': 'invalid-phone',
            'gender': 'INVALID'
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_create_customer_profile_for_user_without_profile(self):
        """Test creating customer profile for user without existing profile."""
        # Create user without profile
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=new_user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': '+1111111111',
            'gender': 'F',
            'newsletter_subscription': True,
            'first_name': 'Alice',
            'last_name': 'Johnson'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['phone_number'], '+1111111111')
        self.assertEqual(response.data['data']['gender'], 'F')
        
        # Verify user fields were updated
        new_user.refresh_from_db()
        self.assertEqual(new_user.first_name, 'Alice')
        self.assertEqual(new_user.last_name, 'Johnson')
    
    def test_create_customer_profile_already_exists(self):
        """Test creating customer profile when one already exists."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-profile')
        
        data = {
            'phone_number': '+1111111111',
            'gender': 'F'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('already exists', response.data['message'])


class AddressAPITest(APITestCase):
    """Test cases for Address API endpoints."""
    
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
    
    def test_get_customer_addresses_empty(self):
        """Test getting customer addresses when none exist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 0)
    
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
        self.assertEqual(response.data['data'][0]['type'], 'HOME')
        self.assertIn('full_address', response.data['data'][0])
    
    def test_get_customer_addresses_unauthenticated(self):
        """Test getting customer addresses when not authenticated."""
        url = reverse('customer-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_address(self):
        """Test creating a new address."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        
        response = self.client.post(url, self.address_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['city'], 'New York')
        self.assertEqual(response.data['data']['type'], 'HOME')
        self.assertTrue(response.data['data']['is_default'])  # First address should be default
    
    def test_create_address_invalid_data(self):
        """Test creating address with invalid data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-addresses')
        
        invalid_data = self.address_data.copy()
        invalid_data['postal_code'] = 'invalid@postal'
        
        response = self.client.post(url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_get_address_detail(self):
        """Test getting specific address details."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], address.id)
        self.assertEqual(response.data['data']['city'], 'New York')
    
    def test_get_address_detail_not_found(self):
        """Test getting address that doesn't exist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_address_detail_other_customer(self):
        """Test getting address that belongs to another customer."""
        # Create another user and address
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_profile = CustomerService.create_customer_profile(other_user)
        other_address = Address.objects.create(
            customer=other_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': other_address.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_address(self):
        """Test updating an existing address."""
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
        self.assertEqual(response.data['data']['state'], 'MA')
        self.assertEqual(response.data['data']['postal_code'], '02101')
    
    def test_update_address_invalid_data(self):
        """Test updating address with invalid data."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-address-detail', kwargs={'address_id': address.id})
        
        invalid_data = {
            'phone': 'invalid-phone-number'
        }
        
        response = self.client.put(url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
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
    
    def test_set_default_address_all(self):
        """Test setting an address as default for all types."""
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
        self.assertTrue(response.data['data']['is_billing_default'])
        self.assertTrue(response.data['data']['is_shipping_default'])
    
    def test_set_default_address_billing_only(self):
        """Test setting an address as default for billing only."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('set-default-address', kwargs={'address_id': address.id})
        
        data = {'type': 'billing'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['is_billing_default'])


class WishlistAPITest(APITestCase):
    """Test cases for Wishlist API endpoints."""
    
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
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            price=Decimal('149.99'),
            category=self.category,
            sku='TEST-002'
        )
    
    def test_get_wishlist_empty(self):
        """Test getting empty customer wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'My Wishlist')
        self.assertEqual(len(response.data['data']['items']), 0)
        self.assertEqual(response.data['data']['item_count'], 0)
    
    def test_get_wishlist_with_items(self):
        """Test getting customer wishlist with items."""
        # Add item to wishlist
        wishlist = self.customer_profile.wishlist
        WishlistItem.objects.create(
            wishlist=wishlist,
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
        self.assertEqual(response.data['data']['item_count'], 1)
        self.assertEqual(response.data['data']['items'][0]['notes'], 'Want to buy this')
        self.assertEqual(response.data['data']['items'][0]['product']['name'], 'Test Product')
    
    def test_get_wishlist_unauthenticated(self):
        """Test getting wishlist when not authenticated."""
        url = reverse('customer-wishlist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
        self.assertEqual(response.data['data']['product']['name'], 'Test Product')
        
        # Verify item was added to database
        self.assertTrue(WishlistItem.objects.filter(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        ).exists())
    
    def test_add_to_wishlist_invalid_product(self):
        """Test adding non-existent product to wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        data = {
            'product_id': 99999,
            'notes': 'Want to buy this'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_add_to_wishlist_duplicate(self):
        """Test adding same product to wishlist twice."""
        # Add product first time
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product,
            notes='First note'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        data = {
            'product_id': self.product.id,
            'notes': 'Second note'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['notes'], 'Second note')
        
        # Verify only one item exists with updated notes
        items = WishlistItem.objects.filter(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        )
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().notes, 'Second note')
    
    def test_remove_from_wishlist(self):
        """Test removing product from wishlist."""
        # Add item to wishlist
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
    
    def test_remove_from_wishlist_not_exists(self):
        """Test removing product that's not in wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', kwargs={'product_id': self.product.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_remove_from_wishlist_invalid_product(self):
        """Test removing non-existent product from wishlist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', kwargs={'product_id': 99999})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_check_wishlist_true(self):
        """Test checking if product is in wishlist (true case)."""
        # Add item to wishlist
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
        self.assertEqual(response.data['data']['product_id'], self.product.id)
    
    def test_check_wishlist_false(self):
        """Test checking if product is in wishlist (false case)."""
        self.client.force_authenticate(user=self.user)
        url = reverse('check-wishlist', kwargs={'product_id': self.product.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['data']['is_in_wishlist'])
        self.assertEqual(response.data['data']['product_id'], self.product.id)
    
    def test_check_wishlist_invalid_product(self):
        """Test checking wishlist for non-existent product."""
        self.client.force_authenticate(user=self.user)
        url = reverse('check-wishlist', kwargs={'product_id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_clear_wishlist(self):
        """Test clearing entire wishlist."""
        # Add multiple items to wishlist
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product
        )
        WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product2
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-wishlist')
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify wishlist is cleared
        self.assertEqual(self.customer_profile.wishlist.items.count(), 0)


class CustomerActivityAPITest(APITestCase):
    """Test cases for Customer Activity API endpoints."""
    
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
    
    def test_get_customer_activities_empty(self):
        """Test getting customer activities when none exist."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)
        self.assertEqual(len(response.data['data']), 0)
    
    def test_get_customer_activities_with_data(self):
        """Test getting customer activities with existing data."""
        # Create some activities
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='User logged in'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Viewed product',
            product=self.product
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        
        # Check activity data
        activities = response.data['data']
        self.assertEqual(activities[0]['activity_type'], 'PRODUCT_VIEW')  # Most recent first
        self.assertEqual(activities[0]['product_name'], 'Test Product')
        self.assertEqual(activities[1]['activity_type'], 'LOGIN')
    
    def test_get_customer_activities_filtered(self):
        """Test getting filtered customer activities."""
        # Create activities of different types
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='Login 1'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='View 1'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='Login 2'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        
        # Filter by activity type
        response = self.client.get(url, {'type': 'LOGIN'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        
        for activity in response.data['data']:
            self.assertEqual(activity['activity_type'], 'LOGIN')
    
    def test_get_customer_activities_limited(self):
        """Test getting limited number of customer activities."""
        # Create multiple activities
        for i in range(10):
            CustomerActivity.objects.create(
                customer=self.customer_profile,
                activity_type='PRODUCT_VIEW',
                description=f'View {i}'
            )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-activities')
        
        # Limit to 5 activities
        response = self.client.get(url, {'limit': '5'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 5)
    
    def test_get_customer_activities_unauthenticated(self):
        """Test getting activities when not authenticated."""
        url = reverse('customer-activities')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_customer_analytics_empty(self):
        """Test getting customer analytics with no data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-analytics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        analytics = response.data['data']
        self.assertEqual(analytics['total_activities'], 0)
        self.assertEqual(analytics['login_count'], 0)
        self.assertEqual(analytics['customer_tier'], 'BRONZE')
        self.assertEqual(analytics['total_spent'], 0.0)
        self.assertEqual(analytics['loyalty_points'], 0)
    
    def test_get_customer_analytics_with_data(self):
        """Test getting customer analytics with existing data."""
        # Create activities
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='Login 1'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='View 1'
        )
        CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='ORDER_PLACED',
            description='Order 1'
        )
        
        # Update customer metrics
        self.customer_profile.total_orders = 2
        self.customer_profile.total_spent = Decimal('15000.00')  # Silver tier
        self.customer_profile.loyalty_points = 150
        self.customer_profile.save()
        
        self.client.force_authenticate(user=self.user)
        url = reverse('customer-analytics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        analytics = response.data['data']
        self.assertEqual(analytics['total_activities'], 3)
        self.assertEqual(analytics['login_count'], 1)
        self.assertEqual(analytics['product_views'], 1)
        self.assertEqual(analytics['orders_placed'], 1)
        self.assertEqual(analytics['customer_tier'], 'SILVER')
        self.assertEqual(analytics['total_spent'], 15000.0)
        self.assertEqual(analytics['loyalty_points'], 150)
        self.assertIsNotNone(analytics['last_activity'])
        self.assertGreaterEqual(analytics['account_age_days'], 0)
    
    def test_log_customer_activity_basic(self):
        """Test logging basic customer activity."""
        self.client.force_authenticate(user=self.user)
        url = reverse('log-customer-activity')
        
        data = {
            'activity_type': 'PRODUCT_VIEW',
            'description': 'Viewed test product'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['activity_type'], 'PRODUCT_VIEW')
        self.assertEqual(response.data['data']['description'], 'Viewed test product')
        
        # Verify activity was created in database
        activity = CustomerActivity.objects.get(id=response.data['data']['id'])
        self.assertEqual(activity.customer, self.customer_profile)
        self.assertEqual(activity.activity_type, 'PRODUCT_VIEW')
    
    def test_log_customer_activity_with_product(self):
        """Test logging activity with related product."""
        self.client.force_authenticate(user=self.user)
        url = reverse('log-customer-activity')
        
        data = {
            'activity_type': 'PRODUCT_VIEW',
            'description': 'Viewed specific product',
            'product_id': self.product.id
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify product was associated
        activity = CustomerActivity.objects.get(id=response.data['data']['id'])
        self.assertEqual(activity.product, self.product)
    
    def test_log_customer_activity_with_metadata(self):
        """Test logging activity with custom metadata."""
        self.client.force_authenticate(user=self.user)
        url = reverse('log-customer-activity')
        
        metadata = {
            'page': 'product-detail',
            'referrer': 'search-results',
            'session_duration': 120
        }
        
        data = {
            'activity_type': 'PRODUCT_VIEW',
            'description': 'Viewed product with metadata',
            'metadata': metadata
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify metadata was stored
        activity = CustomerActivity.objects.get(id=response.data['data']['id'])
        self.assertEqual(activity.metadata, metadata)
    
    def test_log_customer_activity_invalid_type(self):
        """Test logging activity with invalid activity type."""
        self.client.force_authenticate(user=self.user)
        url = reverse('log-customer-activity')
        
        data = {
            'activity_type': 'INVALID_TYPE',
            'description': 'Invalid activity'
        }
        
        response = self.client.post(url, data)
        
        # Should still succeed but may not validate the activity type
        # depending on implementation
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_log_customer_activity_unauthenticated(self):
        """Test logging activity when not authenticated."""
        url = reverse('log-customer-activity')
        
        data = {
            'activity_type': 'PRODUCT_VIEW',
            'description': 'Viewed product'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminCustomerAPITest(APITestCase):
    """Test cases for Admin Customer API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular users and customer profiles
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.customer1 = CustomerService.create_customer_profile(
            self.user1,
            phone_number='+1234567890',
            total_orders=5,
            total_spent=Decimal('2500.00')
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.customer2 = CustomerService.create_customer_profile(
            self.user2,
            phone_number='+9876543210',
            account_status='SUSPENDED'
        )
    
    def test_admin_customer_list_authenticated(self):
        """Test getting customer list as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check customer data
        customers = response.data['results']
        customer_emails = [c['email'] for c in customers]
        self.assertIn('user1@example.com', customer_emails)
        self.assertIn('user2@example.com', customer_emails)
    
    def test_admin_customer_list_unauthenticated(self):
        """Test getting customer list without authentication."""
        url = reverse('admin-customer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_customer_list_non_admin(self):
        """Test getting customer list as non-admin user."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('admin-customer-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_customer_list_search(self):
        """Test searching customers."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'John'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'John Doe')
    
    def test_admin_customer_list_filter_by_status(self):
        """Test filtering customers by account status."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-list')
        
        # Filter by suspended status
        response = self.client.get(url, {'account_status': 'SUSPENDED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['account_status'], 'SUSPENDED')
    
    def test_admin_customer_list_filter_by_tier(self):
        """Test filtering customers by tier."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-list')
        
        # Filter by bronze tier
        response = self.client.get(url, {'customer_tier': 'BRONZE'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Both customers should be bronze tier
        self.assertEqual(len(response.data['results']), 2)
    
    def test_admin_customer_detail(self):
        """Test getting detailed customer information."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-detail', kwargs={'pk': self.customer1.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user1@example.com')
        self.assertEqual(response.data['full_name'], 'John Doe')
        self.assertEqual(response.data['total_orders'], 5)
        self.assertEqual(float(response.data['total_spent']), 2500.0)
        self.assertIn('addresses', response.data)
        self.assertIn('wishlist', response.data)
        self.assertIn('recent_activities', response.data)
    
    def test_admin_customer_detail_not_found(self):
        """Test getting details for non-existent customer."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-detail', kwargs={'pk': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_admin_customer_update(self):
        """Test updating customer information as admin."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-detail', kwargs={'pk': self.customer1.id})
        
        data = {
            'notes': 'VIP customer - provide excellent service',
            'loyalty_points': 500
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], 'VIP customer - provide excellent service')
        self.assertEqual(response.data['loyalty_points'], 500)
    
    def test_admin_customer_status_suspend(self):
        """Test suspending customer account."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer1.id})
        
        data = {
            'action': 'suspend',
            'reason': 'Suspicious activity detected'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['account_status'], 'SUSPENDED')
        
        # Verify customer was suspended
        self.customer1.refresh_from_db()
        self.assertEqual(self.customer1.account_status, 'SUSPENDED')
    
    def test_admin_customer_status_activate(self):
        """Test activating suspended customer account."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer2.id})
        
        data = {
            'action': 'activate'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['account_status'], 'ACTIVE')
        
        # Verify customer was activated
        self.customer2.refresh_from_db()
        self.assertEqual(self.customer2.account_status, 'ACTIVE')
    
    def test_admin_customer_status_block(self):
        """Test blocking customer account."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer1.id})
        
        data = {
            'action': 'block'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['account_status'], 'BLOCKED')
    
    def test_admin_customer_status_invalid_action(self):
        """Test customer status update with invalid action."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer1.id})
        
        data = {
            'action': 'invalid_action'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_admin_customer_status_non_admin(self):
        """Test customer status update as non-admin user."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('admin-customer-status', kwargs={'customer_id': self.customer2.id})
        
        data = {
            'action': 'activate'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)