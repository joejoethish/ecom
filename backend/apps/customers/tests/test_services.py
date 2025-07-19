"""
Tests for customer services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch

from apps.customers.models import (
    CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
)
from apps.customers.services import (
    CustomerService, AddressService, WishlistService, CustomerActivityService
)
from apps.products.models import Product, Category

User = get_user_model()


class CustomerServiceTest(TestCase):
    """Test cases for CustomerService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_create_customer_profile(self):
        """Test creating a customer profile."""
        profile = CustomerService.create_customer_profile(
            user=self.user,
            phone_number='+1234567890',
            gender='M'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
        
        # Check that wishlist was created
        self.assertTrue(hasattr(profile, 'wishlist'))
        self.assertEqual(profile.wishlist.name, 'My Wishlist')
    
    def test_create_customer_profile_existing(self):
        """Test creating profile when one already exists."""
        # Create initial profile
        existing_profile = CustomerProfile.objects.create(user=self.user)
        
        # Try to create another profile
        profile = CustomerService.create_customer_profile(user=self.user)
        
        # Should return existing profile
        self.assertEqual(profile, existing_profile)
    
    def test_update_customer_profile(self):
        """Test updating customer profile."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        updated_profile = CustomerService.update_customer_profile(
            customer_profile=profile,
            phone_number='+1234567890',
            gender='M',
            newsletter_subscription=False
        )
        
        self.assertEqual(updated_profile.phone_number, '+1234567890')
        self.assertEqual(updated_profile.gender, 'M')
        self.assertFalse(updated_profile.newsletter_subscription)
    
    def test_get_or_create_customer_profile_existing(self):
        """Test get_or_create with existing profile."""
        existing_profile = CustomerProfile.objects.create(user=self.user)
        
        profile = CustomerService.get_or_create_customer_profile(self.user)
        
        self.assertEqual(profile, existing_profile)
    
    def test_get_or_create_customer_profile_new(self):
        """Test get_or_create with new profile."""
        profile = CustomerService.get_or_create_customer_profile(self.user)
        
        self.assertEqual(profile.user, self.user)
        self.assertTrue(hasattr(profile, 'wishlist'))
    
    def test_update_customer_login(self):
        """Test updating customer login information."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        CustomerService.update_customer_login(
            customer_profile=profile,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...'
        )
        
        profile.refresh_from_db()
        self.assertIsNotNone(profile.last_login_date)
        
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=profile,
            activity_type='LOGIN'
        ).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.ip_address, '192.168.1.1')
    
    def test_deactivate_customer(self):
        """Test deactivating a customer account."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        deactivated_profile = CustomerService.deactivate_customer(
            customer_profile=profile,
            reason='Suspicious activity'
        )
        
        self.assertEqual(deactivated_profile.account_status, 'SUSPENDED')
        
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=profile,
            activity_type='SUPPORT_TICKET'
        ).first()
        self.assertIsNotNone(activity)
        self.assertIn('suspended', activity.description.lower())
    
    def test_reactivate_customer(self):
        """Test reactivating a customer account."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            account_status='SUSPENDED'
        )
        
        reactivated_profile = CustomerService.reactivate_customer(profile)
        
        self.assertEqual(reactivated_profile.account_status, 'ACTIVE')
        
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=profile,
            activity_type='SUPPORT_TICKET'
        ).first()
        self.assertIsNotNone(activity)
        self.assertIn('reactivated', activity.description.lower())


class AddressServiceTest(TestCase):
    """Test cases for AddressService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
    
    def test_create_address(self):
        """Test creating an address."""
        address_data = {
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
        
        address = AddressService.create_address(self.customer, address_data)
        
        self.assertEqual(address.customer, self.customer)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.first_name, 'John')
        
        # First address should be set as default
        self.assertTrue(address.is_default)
        self.assertTrue(address.is_billing_default)
        self.assertTrue(address.is_shipping_default)
    
    def test_create_second_address(self):
        """Test creating a second address (should not be default)."""
        # Create first address
        address1 = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
        
        # Create second address
        address_data = {
            'type': 'WORK',
            'first_name': 'John',
            'last_name': 'Doe',
            'address_line_1': '456 Work Ave',
            'city': 'Boston',
            'state': 'MA',
            'postal_code': '02101',
            'country': 'USA'
        }
        
        address2 = AddressService.create_address(self.customer, address_data)
        
        # Second address should not be default
        self.assertFalse(address2.is_default)
        self.assertFalse(address2.is_billing_default)
        self.assertFalse(address2.is_shipping_default)
    
    def test_update_address(self):
        """Test updating an address."""
        address = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
        
        update_data = {
            'address_line_1': '456 Updated St',
            'city': 'Boston',
            'state': 'MA'
        }
        
        updated_address = AddressService.update_address(address, update_data)
        
        self.assertEqual(updated_address.address_line_1, '456 Updated St')
        self.assertEqual(updated_address.city, 'Boston')
        self.assertEqual(updated_address.state, 'MA')
    
    def test_delete_address_non_default(self):
        """Test deleting a non-default address."""
        # Create two addresses
        address1 = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            is_default=True
        )
        
        address2 = Address.objects.create(
            customer=self.customer,
            type='WORK',
            first_name='John',
            last_name='Doe',
            address_line_1='456 Work Ave',
            city='Boston',
            state='MA',
            postal_code='02101',
            country='USA'
        )
        
        # Delete non-default address
        result = AddressService.delete_address(address2)
        
        self.assertTrue(result)
        self.assertFalse(Address.objects.filter(id=address2.id).exists())
        
        # Default address should remain unchanged
        address1.refresh_from_db()
        self.assertTrue(address1.is_default)
    
    def test_delete_default_address(self):
        """Test deleting a default address."""
        # Create two addresses
        address1 = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            is_default=True
        )
        
        address2 = Address.objects.create(
            customer=self.customer,
            type='WORK',
            first_name='John',
            last_name='Doe',
            address_line_1='456 Work Ave',
            city='Boston',
            state='MA',
            postal_code='02101',
            country='USA'
        )
        
        # Delete default address
        result = AddressService.delete_address(address1)
        
        self.assertTrue(result)
        self.assertFalse(Address.objects.filter(id=address1.id).exists())
        
        # Second address should become default
        address2.refresh_from_db()
        self.assertTrue(address2.is_default)
    
    def test_set_default_address(self):
        """Test setting an address as default."""
        address = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
        
        # Set as default for all types
        updated_address = AddressService.set_default_address(address, 'all')
        
        self.assertTrue(updated_address.is_default)
        self.assertTrue(updated_address.is_billing_default)
        self.assertTrue(updated_address.is_shipping_default)
        
        # Set as billing default only
        address2 = Address.objects.create(
            customer=self.customer,
            type='WORK',
            first_name='John',
            last_name='Doe',
            address_line_1='456 Work Ave',
            city='Boston',
            state='MA',
            postal_code='02101',
            country='USA'
        )
        
        updated_address2 = AddressService.set_default_address(address2, 'billing')
        
        self.assertFalse(updated_address2.is_default)
        self.assertTrue(updated_address2.is_billing_default)
        self.assertFalse(updated_address2.is_shipping_default)


class WishlistServiceTest(TestCase):
    """Test cases for WishlistService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
        
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
    
    def test_get_or_create_wishlist_existing(self):
        """Test getting existing wishlist."""
        existing_wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        wishlist = WishlistService.get_or_create_wishlist(self.customer)
        
        self.assertEqual(wishlist, existing_wishlist)
    
    def test_get_or_create_wishlist_new(self):
        """Test creating new wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(self.customer)
        
        self.assertEqual(wishlist.customer, self.customer)
        self.assertEqual(wishlist.name, 'My Wishlist')
    
    def test_add_to_wishlist_new_item(self):
        """Test adding a new item to wishlist."""
        wishlist_item = WishlistService.add_to_wishlist(
            customer_profile=self.customer,
            product=self.product,
            notes='Want to buy this'
        )
        
        self.assertEqual(wishlist_item.product, self.product)
        self.assertEqual(wishlist_item.notes, 'Want to buy this')
        
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=self.customer,
            activity_type='ADD_TO_WISHLIST'
        ).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.product, self.product)
    
    def test_add_to_wishlist_existing_item(self):
        """Test adding an existing item to wishlist."""
        # Create wishlist and item
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        existing_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product,
            notes='Original notes'
        )
        
        # Try to add same item with new notes
        wishlist_item = WishlistService.add_to_wishlist(
            customer_profile=self.customer,
            product=self.product,
            notes='Updated notes'
        )
        
        # Should return existing item with updated notes
        self.assertEqual(wishlist_item, existing_item)
        wishlist_item.refresh_from_db()
        self.assertEqual(wishlist_item.notes, 'Updated notes')
    
    def test_remove_from_wishlist_existing(self):
        """Test removing an existing item from wishlist."""
        # Create wishlist and item
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        result = WishlistService.remove_from_wishlist(self.customer, self.product)
        
        self.assertTrue(result)
        self.assertFalse(
            WishlistItem.objects.filter(
                wishlist=wishlist,
                product=self.product
            ).exists()
        )
        
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=self.customer,
            activity_type='REMOVE_FROM_WISHLIST'
        ).first()
        self.assertIsNotNone(activity)
    
    def test_remove_from_wishlist_non_existing(self):
        """Test removing a non-existing item from wishlist."""
        result = WishlistService.remove_from_wishlist(self.customer, self.product)
        
        self.assertFalse(result)
    
    def test_clear_wishlist(self):
        """Test clearing all items from wishlist."""
        # Create wishlist with items
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        # Create multiple products and add to wishlist
        for i in range(3):
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description='Test description',
                price=Decimal('99.99'),
                category=self.category,
                sku=f'TEST-00{i}'
            )
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=product
            )
        
        result = WishlistService.clear_wishlist(self.customer)
        
        self.assertTrue(result)
        self.assertEqual(wishlist.items.count(), 0)
    
    def test_is_in_wishlist_true(self):
        """Test checking if product is in wishlist (true case)."""
        # Create wishlist and item
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        result = WishlistService.is_in_wishlist(self.customer, self.product)
        
        self.assertTrue(result)
    
    def test_is_in_wishlist_false(self):
        """Test checking if product is in wishlist (false case)."""
        result = WishlistService.is_in_wishlist(self.customer, self.product)
        
        self.assertFalse(result)


class CustomerActivityServiceTest(TestCase):
    """Test cases for CustomerActivityService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
        
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
    
    def test_log_activity(self):
        """Test logging a customer activity."""
        activity = CustomerActivityService.log_activity(
            customer_profile=self.customer,
            activity_type='PRODUCT_VIEW',
            description='Viewed test product',
            product=self.product,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...',
            metadata={'page': 'product-detail'}
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.customer, self.customer)
        self.assertEqual(activity.activity_type, 'PRODUCT_VIEW')
        self.assertEqual(activity.product, self.product)
        self.assertEqual(activity.ip_address, '192.168.1.1')
        self.assertEqual(activity.metadata, {'page': 'product-detail'})
    
    @patch('apps.customers.services.logger')
    def test_log_activity_error_handling(self, mock_logger):
        """Test error handling in log_activity."""
        # Force an error by passing invalid data
        with patch('apps.customers.models.CustomerActivity.objects.create', side_effect=Exception('Test error')):
            activity = CustomerActivityService.log_activity(
                customer_profile=self.customer,
                activity_type='INVALID_TYPE',
                description='Test'
            )
            
            self.assertIsNone(activity)
            mock_logger.error.assert_called_once()
    
    def test_get_customer_activities(self):
        """Test getting customer activities."""
        # Create multiple activities
        activities_data = [
            ('LOGIN', 'User logged in'),
            ('PRODUCT_VIEW', 'Viewed product'),
            ('ADD_TO_CART', 'Added to cart'),
        ]
        
        for activity_type, description in activities_data:
            CustomerActivity.objects.create(
                customer=self.customer,
                activity_type=activity_type,
                description=description
            )
        
        # Get all activities
        activities = CustomerActivityService.get_customer_activities(self.customer)
        
        self.assertEqual(len(activities), 3)
        
        # Get filtered activities
        login_activities = CustomerActivityService.get_customer_activities(
            self.customer,
            activity_type='LOGIN'
        )
        
        self.assertEqual(len(login_activities), 1)
        self.assertEqual(login_activities[0].activity_type, 'LOGIN')
    
    def test_get_customer_activities_with_limit(self):
        """Test getting customer activities with limit."""
        # Create multiple activities
        for i in range(10):
            CustomerActivity.objects.create(
                customer=self.customer,
                activity_type='PRODUCT_VIEW',
                description=f'Activity {i}'
            )
        
        activities = CustomerActivityService.get_customer_activities(
            self.customer,
            limit=5
        )
        
        self.assertEqual(len(activities), 5)
    
    def test_get_customer_analytics(self):
        """Test getting customer analytics."""
        # Create various activities
        activities_data = [
            ('LOGIN', 'Login 1'),
            ('LOGIN', 'Login 2'),
            ('PRODUCT_VIEW', 'View 1'),
            ('PRODUCT_VIEW', 'View 2'),
            ('PRODUCT_VIEW', 'View 3'),
            ('ADD_TO_CART', 'Cart 1'),
            ('ADD_TO_WISHLIST', 'Wishlist 1'),
            ('ORDER_PLACED', 'Order 1'),
            ('REVIEW_SUBMITTED', 'Review 1'),
        ]
        
        for activity_type, description in activities_data:
            CustomerActivity.objects.create(
                customer=self.customer,
                activity_type=activity_type,
                description=description
            )
        
        # Update customer profile with some data
        self.customer.total_spent = Decimal('15000')
        self.customer.loyalty_points = 500
        self.customer.save()
        
        analytics = CustomerActivityService.get_customer_analytics(self.customer)
        
        self.assertEqual(analytics['total_activities'], 9)
        self.assertEqual(analytics['login_count'], 2)
        self.assertEqual(analytics['product_views'], 3)
        self.assertEqual(analytics['cart_additions'], 1)
        self.assertEqual(analytics['wishlist_additions'], 1)
        self.assertEqual(analytics['orders_placed'], 1)
        self.assertEqual(analytics['reviews_submitted'], 1)
        self.assertEqual(analytics['customer_tier'], 'SILVER')
        self.assertEqual(analytics['total_spent'], 15000.0)
        self.assertEqual(analytics['loyalty_points'], 500)
        self.assertIsNotNone(analytics['last_activity'])
        self.assertIsNotNone(analytics['account_age_days'])
    
    @patch('apps.customers.services.logger')
    def test_get_customer_analytics_error_handling(self, mock_logger):
        """Test error handling in get_customer_analytics."""
        # Force an error
        with patch.object(self.customer, 'activities', side_effect=Exception('Test error')):
            analytics = CustomerActivityService.get_customer_analytics(self.customer)
            
            self.assertEqual(analytics, {})
            mock_logger.error.assert_called_once()