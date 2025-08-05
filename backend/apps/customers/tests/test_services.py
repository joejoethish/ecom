"""
Tests for customer services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
<<<<<<< HEAD

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.customers.services import CustomerService, AddressService, WishlistService, CustomerActivityService
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
            self.user,
            phone_number='+1234567890',
            gender='M',
            newsletter_subscription=False
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
        self.assertFalse(profile.newsletter_subscription)
        self.assertEqual(profile.account_status, 'ACTIVE')
        
        # Check that wishlist was created
        self.assertTrue(hasattr(profile, 'wishlist'))
        self.assertEqual(profile.wishlist.name, 'My Wishlist')
    
    def test_create_customer_profile_existing(self):
        """Test creating profile for user who already has one."""
        # Create initial profile
        profile1 = CustomerService.create_customer_profile(self.user)
        
        # Try to create another - should return existing
        profile2 = CustomerService.create_customer_profile(self.user)
        
        self.assertEqual(profile1, profile2)
    
    def test_update_customer_profile(self):
        """Test updating customer profile."""
        profile = CustomerService.create_customer_profile(self.user)
        
        updated_profile = CustomerService.update_customer_profile(
            profile,
            phone_number='+9876543210',
            gender='F',
            loyalty_points=100
        )
        
        self.assertEqual(updated_profile.phone_number, '+9876543210')
        self.assertEqual(updated_profile.gender, 'F')
        self.assertEqual(updated_profile.loyalty_points, 100)
    
    def test_get_or_create_customer_profile(self):
        """Test get or create customer profile."""
        # Should create new profile
        profile1 = CustomerService.get_or_create_customer_profile(self.user)
        self.assertIsInstance(profile1, CustomerProfile)
        
        # Should return existing profile
        profile2 = CustomerService.get_or_create_customer_profile(self.user)
        self.assertEqual(profile1, profile2)
    
    def test_update_customer_login(self):
        """Test updating customer login information."""
        profile = CustomerService.create_customer_profile(self.user)
        
        CustomerService.update_customer_login(
            profile,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...'
        )
        
        profile.refresh_from_db()
        self.assertIsNotNone(profile.last_login_date)
        
        # Check activity was logged
        activities = profile.activities.filter(activity_type='LOGIN')
        self.assertEqual(activities.count(), 1)
        self.assertEqual(activities.first().ip_address, '192.168.1.1')
    
    def test_deactivate_customer(self):
        """Test deactivating customer account."""
        profile = CustomerService.create_customer_profile(self.user)
        
        deactivated_profile = CustomerService.deactivate_customer(
            profile,
            reason='Suspicious activity'
        )
        
        self.assertEqual(deactivated_profile.account_status, 'SUSPENDED')
        
        # Check activity was logged
        activities = profile.activities.filter(activity_type='SUPPORT_TICKET')
        self.assertTrue(activities.exists())
    
    def test_reactivate_customer(self):
        """Test reactivating customer account."""
        profile = CustomerService.create_customer_profile(self.user)
        profile.account_status = 'SUSPENDED'
        profile.save()
        
        reactivated_profile = CustomerService.reactivate_customer(profile)
        
        self.assertEqual(reactivated_profile.account_status, 'ACTIVE')
        
        # Check activity was logged
        activities = profile.activities.filter(
            activity_type='SUPPORT_TICKET',
            description='Account reactivated'
        )
        self.assertTrue(activities.exists())


class AddressServiceTest(TestCase):
    """Test cases for AddressService."""
    
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
    
    def test_create_address(self):
        """Test creating an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        self.assertEqual(address.customer, self.customer_profile)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.city, 'New York')
        self.assertTrue(address.is_default)  # First address should be default
    
    def test_create_multiple_addresses(self):
        """Test creating multiple addresses."""
        # Create first address
        address1 = AddressService.create_address(self.customer_profile, self.address_data)
        
        # Create second address
        address_data_2 = self.address_data.copy()
        address_data_2.update({
            'type': 'WORK',
            'city': 'Boston',
            'state': 'MA'
        })
        address2 = AddressService.create_address(self.customer_profile, address_data_2)
        
        # First address should still be default
        address1.refresh_from_db()
        self.assertTrue(address1.is_default)
        self.assertFalse(address2.is_default)
    
    def test_update_address(self):
        """Test updating an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        update_data = {
            'city': 'Boston',
            'state': 'MA',
            'postal_code': '02101'
        }
        
        updated_address = AddressService.update_address(address, update_data)
        
        self.assertEqual(updated_address.city, 'Boston')
        self.assertEqual(updated_address.state, 'MA')
        self.assertEqual(updated_address.postal_code, '02101')
    
    def test_delete_address(self):
        """Test deleting an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        address_id = address.id
        
        result = AddressService.delete_address(address)
        
        self.assertTrue(result)
        self.assertFalse(Address.objects.filter(id=address_id).exists())
    
    def test_delete_default_address_reassignment(self):
        """Test that deleting default address reassigns default to another."""
        # Create two addresses
        address1 = AddressService.create_address(self.customer_profile, self.address_data)
        
        address_data_2 = self.address_data.copy()
        address_data_2['city'] = 'Boston'
        address2 = AddressService.create_address(self.customer_profile, address_data_2)
        
        # Delete the default address
        AddressService.delete_address(address1)
        
        # Second address should become default
        address2.refresh_from_db()
        self.assertTrue(address2.is_default)
    
    def test_set_default_address(self):
        """Test setting an address as default."""
        # Create two addresses
        address1 = AddressService.create_address(self.customer_profile, self.address_data)
        
        address_data_2 = self.address_data.copy()
        address_data_2['city'] = 'Boston'
        address2 = AddressService.create_address(self.customer_profile, address_data_2)
        
        # Set second address as default
        updated_address = AddressService.set_default_address(address2, 'all')
        
        self.assertTrue(updated_address.is_default)
        self.assertTrue(updated_address.is_billing_default)
        self.assertTrue(updated_address.is_shipping_default)
        
        # First address should no longer be default
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
    
    def test_set_specific_default_address(self):
        """Test setting address as specific type of default."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        # Set as billing default only
        updated_address = AddressService.set_default_address(address, 'billing')
        
        self.assertTrue(updated_address.is_billing_default)
        self.assertTrue(updated_address.is_default)  # Should remain general default
        self.assertFalse(updated_address.is_shipping_default)


class WishlistServiceTest(TestCase):
    """Test cases for WishlistService."""
    
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
    
    def test_get_or_create_wishlist(self):
        """Test getting or creating wishlist."""
        # Should return existing wishlist (created during profile creation)
        wishlist1 = WishlistService.get_or_create_wishlist(self.customer_profile)
        self.assertEqual(wishlist1.customer, self.customer_profile)
        
        # Should return same wishlist
        wishlist2 = WishlistService.get_or_create_wishlist(self.customer_profile)
        self.assertEqual(wishlist1, wishlist2)
    
    def test_add_to_wishlist(self):
        """Test adding product to wishlist."""
        wishlist_item = WishlistService.add_to_wishlist(
            self.customer_profile,
            self.product,
            'Want to buy this'
        )
        
        self.assertEqual(wishlist_item.product, self.product)
        self.assertEqual(wishlist_item.notes, 'Want to buy this')
        
        # Check activity was logged
        activities = self.customer_profile.activities.filter(
            activity_type='ADD_TO_WISHLIST'
        )
        self.assertTrue(activities.exists())
    
    def test_add_duplicate_to_wishlist(self):
        """Test adding same product twice to wishlist."""
        # Add product first time
        item1 = WishlistService.add_to_wishlist(
            self.customer_profile,
            self.product,
            'First note'
        )
        
        # Add same product again with different note
        item2 = WishlistService.add_to_wishlist(
            self.customer_profile,
            self.product,
            'Second note'
        )
        
        # Should return same item with updated note
        self.assertEqual(item1.id, item2.id)
        item1.refresh_from_db()
        self.assertEqual(item1.notes, 'Second note')
    
    def test_remove_from_wishlist(self):
        """Test removing product from wishlist."""
        # Add product to wishlist
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        
        # Remove product
        result = WishlistService.remove_from_wishlist(self.customer_profile, self.product)
        
        self.assertTrue(result)
        
        # Check product is no longer in wishlist
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
        self.assertEqual(wishlist.items.count(), 0)
        
        # Check activity was logged
        activities = self.customer_profile.activities.filter(
            activity_type='REMOVE_FROM_WISHLIST'
        )
        self.assertTrue(activities.exists())
    
    def test_remove_nonexistent_from_wishlist(self):
        """Test removing product that's not in wishlist."""
        result = WishlistService.remove_from_wishlist(self.customer_profile, self.product)
        self.assertFalse(result)
    
    def test_clear_wishlist(self):
        """Test clearing entire wishlist."""
        # Add multiple products
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            price=Decimal('149.99'),
            category=self.category,
            sku='TEST-002'
        )
        
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        WishlistService.add_to_wishlist(self.customer_profile, product2)
        
        # Clear wishlist
        result = WishlistService.clear_wishlist(self.customer_profile)
        
        self.assertTrue(result)
        
        # Check wishlist is empty
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
        self.assertEqual(wishlist.items.count(), 0)
    
    def test_is_in_wishlist(self):
        """Test checking if product is in wishlist."""
        # Product not in wishlist
        self.assertFalse(WishlistService.is_in_wishlist(self.customer_profile, self.product))
        
        # Add product to wishlist
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        
        # Product should be in wishlist
        self.assertTrue(WishlistService.is_in_wishlist(self.customer_profile, self.product))


class CustomerActivityServiceTest(TestCase):
    """Test cases for CustomerActivityService."""
    
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
    
    def test_log_activity(self):
        """Test logging customer activity."""
        activity = CustomerActivityService.log_activity(
            customer_profile=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Viewed test product',
            product=self.product,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...',
            session_key='abc123',
            metadata={'page': 'product-detail'}
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.customer, self.customer_profile)
        self.assertEqual(activity.activity_type, 'PRODUCT_VIEW')
        self.assertEqual(activity.product, self.product)
        self.assertEqual(activity.ip_address, '192.168.1.1')
        self.assertEqual(activity.metadata['page'], 'product-detail')
    
    def test_log_activity_minimal(self):
        """Test logging activity with minimal data."""
        activity = CustomerActivityService.log_activity(
            customer_profile=self.customer_profile,
            activity_type='LOGIN'
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.activity_type, 'LOGIN')
        self.assertEqual(activity.description, '')
    
    def test_get_customer_activities(self):
        """Test getting customer activities."""
        # Log some activities
        CustomerActivityService.log_activity(
            self.customer_profile, 'LOGIN', 'User logged in'
        )
        CustomerActivityService.log_activity(
            self.customer_profile, 'PRODUCT_VIEW', 'Viewed product'
        )
        CustomerActivityService.log_activity(
            self.customer_profile, 'LOGIN', 'User logged in again'
        )
        
        # Get all activities
        activities = CustomerActivityService.get_customer_activities(self.customer_profile)
        self.assertEqual(len(activities), 3)
        
        # Get activities by type
        login_activities = CustomerActivityService.get_customer_activities(
            self.customer_profile, 'LOGIN'
        )
        self.assertEqual(len(login_activities), 2)
        
        # Get limited activities
        limited_activities = CustomerActivityService.get_customer_activities(
            self.customer_profile, limit=2
        )
        self.assertEqual(len(limited_activities), 2)
    
    def test_get_customer_analytics(self):
        """Test getting customer analytics."""
        # Log various activities
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN')
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN')
        CustomerActivityService.log_activity(self.customer_profile, 'PRODUCT_VIEW')
        CustomerActivityService.log_activity(self.customer_profile, 'ADD_TO_CART')
        CustomerActivityService.log_activity(self.customer_profile, 'ADD_TO_WISHLIST')
        CustomerActivityService.log_activity(self.customer_profile, 'ORDER_PLACED')
        CustomerActivityService.log_activity(self.customer_profile, 'REVIEW_SUBMITTED')
        
        analytics = CustomerActivityService.get_customer_analytics(self.customer_profile)
        
        self.assertEqual(analytics['total_activities'], 7)
        self.assertEqual(analytics['login_count'], 2)
        self.assertEqual(analytics['product_views'], 1)
        self.assertEqual(analytics['cart_additions'], 1)
        self.assertEqual(analytics['wishlist_additions'], 1)
        self.assertEqual(analytics['orders_placed'], 1)
        self.assertEqual(analytics['reviews_submitted'], 1)
        self.assertEqual(analytics['customer_tier'], 'BRONZE')
        self.assertEqual(analytics['total_spent'], 0.0)
        self.assertEqual(analytics['loyalty_points'], 0)
        self.assertIsNotNone(analytics['last_activity'])
        self.assertGreaterEqual(analytics['account_age_days'], 0)
    
    def test_get_customer_analytics_empty(self):
        """Test getting analytics for customer with no activities."""
        analytics = CustomerActivityService.get_customer_analytics(self.customer_profile)
        
        self.assertEqual(analytics['total_activities'], 0)
        self.assertEqual(analytics['login_count'], 0)
        self.assertIsNone(analytics['last_activity'])
"""
Tests for customer services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
=======
from unittest.mock import patch
>>>>>>> Task-10.3

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
<<<<<<< HEAD
            self.user,
            phone_number='+1234567890',
            gender='M',
            newsletter_subscription=False
=======
            user=self.user,
            phone_number='+1234567890',
            gender='M'
>>>>>>> Task-10.3
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
<<<<<<< HEAD
        self.assertFalse(profile.newsletter_subscription)
        self.assertEqual(profile.account_status, 'ACTIVE')
=======
>>>>>>> Task-10.3
        
        # Check that wishlist was created
        self.assertTrue(hasattr(profile, 'wishlist'))
        self.assertEqual(profile.wishlist.name, 'My Wishlist')
    
<<<<<<< HEAD
    def test_create_customer_profile_duplicate(self):
        """Test creating customer profile for user who already has one."""
        # Create first profile
        profile1 = CustomerService.create_customer_profile(self.user)
        
        # Try to create another profile for same user
        profile2 = CustomerService.create_customer_profile(self.user)
        
        # Should return existing profile
        self.assertEqual(profile1, profile2)
    
    def test_update_customer_profile(self):
        """Test updating customer profile."""
        profile = CustomerService.create_customer_profile(self.user)
        
        updated_profile = CustomerService.update_customer_profile(
            profile,
            phone_number='+9876543210',
            gender='F',
            loyalty_points=100
        )
        
        self.assertEqual(updated_profile.phone_number, '+9876543210')
        self.assertEqual(updated_profile.gender, 'F')
        self.assertEqual(updated_profile.loyalty_points, 100)
    
    def test_get_or_create_customer_profile_existing(self):
        """Test getting existing customer profile."""
        profile = CustomerService.create_customer_profile(self.user)
        
        retrieved_profile = CustomerService.get_or_create_customer_profile(self.user)
        
        self.assertEqual(profile, retrieved_profile)
    
    def test_get_or_create_customer_profile_new(self):
        """Test creating new customer profile when none exists."""
        profile = CustomerService.get_or_create_customer_profile(self.user)
        
        self.assertIsInstance(profile, CustomerProfile)
        self.assertEqual(profile.user, self.user)
    
    def test_update_customer_login(self):
        """Test updating customer login information."""
        profile = CustomerService.create_customer_profile(self.user)
        
        CustomerService.update_customer_login(
            profile,
=======
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
>>>>>>> Task-10.3
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...'
        )
        
        profile.refresh_from_db()
        self.assertIsNotNone(profile.last_login_date)
        
<<<<<<< HEAD
        # Check that login activity was logged
        login_activities = profile.activities.filter(activity_type='LOGIN')
        self.assertEqual(login_activities.count(), 1)
        self.assertEqual(login_activities.first().ip_address, '192.168.1.1')
    
    def test_deactivate_customer(self):
        """Test deactivating customer account."""
        profile = CustomerService.create_customer_profile(self.user)
        
        deactivated_profile = CustomerService.deactivate_customer(
            profile,
=======
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
>>>>>>> Task-10.3
            reason='Suspicious activity'
        )
        
        self.assertEqual(deactivated_profile.account_status, 'SUSPENDED')
        
<<<<<<< HEAD
        # Check that activity was logged
        activities = profile.activities.filter(activity_type='SUPPORT_TICKET')
        self.assertEqual(activities.count(), 1)
        self.assertIn('suspended', activities.first().description.lower())
    
    def test_reactivate_customer(self):
        """Test reactivating customer account."""
        profile = CustomerService.create_customer_profile(self.user)
        profile.account_status = 'SUSPENDED'
        profile.save()
=======
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
>>>>>>> Task-10.3
        
        reactivated_profile = CustomerService.reactivate_customer(profile)
        
        self.assertEqual(reactivated_profile.account_status, 'ACTIVE')
        
<<<<<<< HEAD
        # Check that activity was logged
        activities = profile.activities.filter(activity_type='SUPPORT_TICKET')
        self.assertEqual(activities.count(), 1)
        self.assertIn('reactivated', activities.first().description.lower())
=======
        # Check activity was logged
        activity = CustomerActivity.objects.filter(
            customer=profile,
            activity_type='SUPPORT_TICKET'
        ).first()
        self.assertIsNotNone(activity)
        self.assertIn('reactivated', activity.description.lower())
>>>>>>> Task-10.3


class AddressServiceTest(TestCase):
    """Test cases for AddressService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
<<<<<<< HEAD
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
        
        self.address_data = {
=======
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
    
    def test_create_address(self):
        """Test creating an address."""
        address_data = {
>>>>>>> Task-10.3
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
<<<<<<< HEAD
    
    def test_create_address(self):
        """Test creating an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        self.assertEqual(address.customer, self.customer_profile)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.city, 'New York')
        self.assertTrue(address.is_default)  # First address should be default
    
    def test_create_second_address_not_default(self):
        """Test that second address is not automatically default."""
        # Create first address
        AddressService.create_address(self.customer_profile, self.address_data)
        
        # Create second address
        second_address_data = self.address_data.copy()
        second_address_data.update({
            'type': 'WORK',
            'city': 'Boston',
            'state': 'MA'
        })
        
        second_address = AddressService.create_address(self.customer_profile, second_address_data)
        
        self.assertFalse(second_address.is_default)
    
    def test_update_address(self):
        """Test updating an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        update_data = {
            'city': 'Boston',
            'state': 'MA',
            'postal_code': '02101'
=======
        
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
>>>>>>> Task-10.3
        }
        
        updated_address = AddressService.update_address(address, update_data)
        
<<<<<<< HEAD
        self.assertEqual(updated_address.city, 'Boston')
        self.assertEqual(updated_address.state, 'MA')
        self.assertEqual(updated_address.postal_code, '02101')
    
    def test_delete_address(self):
        """Test deleting an address."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        address_id = address.id
        
        result = AddressService.delete_address(address)
        
        self.assertTrue(result)
        self.assertFalse(Address.objects.filter(id=address_id).exists())
    
    def test_delete_default_address_reassigns_default(self):
        """Test that deleting default address reassigns default to another address."""
        # Create two addresses
        address1 = AddressService.create_address(self.customer_profile, self.address_data)
        
        second_address_data = self.address_data.copy()
        second_address_data.update({'type': 'WORK', 'city': 'Boston'})
        address2 = AddressService.create_address(self.customer_profile, second_address_data)
        
        # Delete the default address
        AddressService.delete_address(address1)
        
        # Check that second address became default
        address2.refresh_from_db()
        self.assertTrue(address2.is_default)
    
    def test_set_default_address_all(self):
        """Test setting address as default for all types."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
=======
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
>>>>>>> Task-10.3
        updated_address = AddressService.set_default_address(address, 'all')
        
        self.assertTrue(updated_address.is_default)
        self.assertTrue(updated_address.is_billing_default)
        self.assertTrue(updated_address.is_shipping_default)
<<<<<<< HEAD
    
    def test_set_default_address_billing_only(self):
        """Test setting address as default for billing only."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        updated_address = AddressService.set_default_address(address, 'billing')
        
        self.assertTrue(updated_address.is_billing_default)
        # Other defaults should remain unchanged
    
    def test_set_default_address_shipping_only(self):
        """Test setting address as default for shipping only."""
        address = AddressService.create_address(self.customer_profile, self.address_data)
        
        updated_address = AddressService.set_default_address(address, 'shipping')
        
        self.assertTrue(updated_address.is_shipping_default)
=======
        
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
>>>>>>> Task-10.3


class WishlistServiceTest(TestCase):
    """Test cases for WishlistService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
<<<<<<< HEAD
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
=======
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
>>>>>>> Task-10.3
        
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
<<<<<<< HEAD
        # Wishlist should be created automatically with customer profile
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
        
        self.assertEqual(wishlist.customer, self.customer_profile)
        self.assertEqual(wishlist.name, 'My Wishlist')
    
    def test_get_or_create_wishlist_new(self):
        """Test creating new wishlist when none exists."""
        # Delete the auto-created wishlist
        self.customer_profile.wishlist.delete()
        
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
        
        self.assertEqual(wishlist.customer, self.customer_profile)
        self.assertEqual(wishlist.name, 'My Wishlist')
    
    def test_add_to_wishlist(self):
        """Test adding product to wishlist."""
        wishlist_item = WishlistService.add_to_wishlist(
            self.customer_profile,
            self.product,
            'Want to buy this'
=======
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
>>>>>>> Task-10.3
        )
        
        self.assertEqual(wishlist_item.product, self.product)
        self.assertEqual(wishlist_item.notes, 'Want to buy this')
        
<<<<<<< HEAD
        # Check that activity was logged
        activities = self.customer_profile.activities.filter(activity_type='ADD_TO_WISHLIST')
        self.assertEqual(activities.count(), 1)
    
    def test_add_to_wishlist_duplicate(self):
        """Test adding same product to wishlist twice."""
        # Add product first time
        item1 = WishlistService.add_to_wishlist(self.customer_profile, self.product, 'First note')
        
        # Add same product again
        item2 = WishlistService.add_to_wishlist(self.customer_profile, self.product, 'Second note')
        
        # Should return same item with updated notes
        self.assertEqual(item1.id, item2.id)
        self.assertEqual(item2.notes, 'Second note')
    
    def test_remove_from_wishlist(self):
        """Test removing product from wishlist."""
        # Add product to wishlist
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        
        # Remove product from wishlist
        result = WishlistService.remove_from_wishlist(self.customer_profile, self.product)
        
        self.assertTrue(result)
        
        # Check that item was removed
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
        self.assertEqual(wishlist.items.count(), 0)
        
        # Check that activity was logged
        activities = self.customer_profile.activities.filter(activity_type='REMOVE_FROM_WISHLIST')
        self.assertEqual(activities.count(), 1)
    
    def test_remove_from_wishlist_not_exists(self):
        """Test removing product that's not in wishlist."""
        result = WishlistService.remove_from_wishlist(self.customer_profile, self.product)
=======
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
>>>>>>> Task-10.3
        
        self.assertFalse(result)
    
    def test_clear_wishlist(self):
<<<<<<< HEAD
        """Test clearing entire wishlist."""
        # Add multiple products to wishlist
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            price=Decimal('149.99'),
            category=self.category,
            sku='TEST-002'
        )
        
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        WishlistService.add_to_wishlist(self.customer_profile, product2)
        
        # Clear wishlist
        result = WishlistService.clear_wishlist(self.customer_profile)
        
        self.assertTrue(result)
        
        # Check that all items were removed
        wishlist = WishlistService.get_or_create_wishlist(self.customer_profile)
=======
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
>>>>>>> Task-10.3
        self.assertEqual(wishlist.items.count(), 0)
    
    def test_is_in_wishlist_true(self):
        """Test checking if product is in wishlist (true case)."""
<<<<<<< HEAD
        WishlistService.add_to_wishlist(self.customer_profile, self.product)
        
        result = WishlistService.is_in_wishlist(self.customer_profile, self.product)
=======
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
>>>>>>> Task-10.3
        
        self.assertTrue(result)
    
    def test_is_in_wishlist_false(self):
        """Test checking if product is in wishlist (false case)."""
<<<<<<< HEAD
        result = WishlistService.is_in_wishlist(self.customer_profile, self.product)
=======
        result = WishlistService.is_in_wishlist(self.customer, self.product)
>>>>>>> Task-10.3
        
        self.assertFalse(result)


class CustomerActivityServiceTest(TestCase):
    """Test cases for CustomerActivityService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
<<<<<<< HEAD
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerService.create_customer_profile(self.user)
=======
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(user=self.user)
>>>>>>> Task-10.3
        
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
    
<<<<<<< HEAD
    def test_log_activity_basic(self):
        """Test logging basic customer activity."""
        activity = CustomerActivityService.log_activity(
            self.customer_profile,
            'LOGIN',
            'User logged in',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...'
        )
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity.customer, self.customer_profile)
        self.assertEqual(activity.activity_type, 'LOGIN')
        self.assertEqual(activity.description, 'User logged in')
        self.assertEqual(activity.ip_address, '192.168.1.1')
    
    def test_log_activity_with_product(self):
        """Test logging activity with related product."""
        activity = CustomerActivityService.log_activity(
            self.customer_profile,
            'PRODUCT_VIEW',
            'Viewed product',
            product=self.product,
            metadata={'page': 'product-detail'}
        )
        
        self.assertEqual(activity.product, self.product)
        self.assertEqual(activity.metadata, {'page': 'product-detail'})
    
    def test_log_activity_with_metadata(self):
        """Test logging activity with custom metadata."""
        metadata = {
            'search_query': 'test product',
            'filters': ['category:electronics', 'price:100-200'],
            'results_count': 5
        }
        
        activity = CustomerActivityService.log_activity(
            self.customer_profile,
            'SEARCH',
            'Performed search',
            metadata=metadata
        )
        
        self.assertEqual(activity.metadata, metadata)
    
    def test_get_customer_activities_all(self):
        """Test getting all customer activities."""
        # Log multiple activities
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 1')
        CustomerActivityService.log_activity(self.customer_profile, 'PRODUCT_VIEW', 'View 1')
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 2')
        
        activities = CustomerActivityService.get_customer_activities(self.customer_profile)
        
        self.assertEqual(len(activities), 3)
        # Should be ordered by most recent first
        self.assertEqual(activities[0].description, 'Login 2')
    
    def test_get_customer_activities_filtered(self):
        """Test getting filtered customer activities."""
        # Log multiple activities
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 1')
        CustomerActivityService.log_activity(self.customer_profile, 'PRODUCT_VIEW', 'View 1')
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 2')
        
        login_activities = CustomerActivityService.get_customer_activities(
            self.customer_profile,
            activity_type='LOGIN'
        )
        
        self.assertEqual(len(login_activities), 2)
        for activity in login_activities:
            self.assertEqual(activity.activity_type, 'LOGIN')
    
    def test_get_customer_activities_limited(self):
        """Test getting limited number of customer activities."""
        # Log multiple activities
        for i in range(10):
            CustomerActivityService.log_activity(
                self.customer_profile,
                'PRODUCT_VIEW',
                f'View {i}'
            )
        
        activities = CustomerActivityService.get_customer_activities(
            self.customer_profile,
=======
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
>>>>>>> Task-10.3
            limit=5
        )
        
        self.assertEqual(len(activities), 5)
    
    def test_get_customer_analytics(self):
        """Test getting customer analytics."""
<<<<<<< HEAD
        # Log various activities
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 1')
        CustomerActivityService.log_activity(self.customer_profile, 'LOGIN', 'Login 2')
        CustomerActivityService.log_activity(self.customer_profile, 'PRODUCT_VIEW', 'View 1')
        CustomerActivityService.log_activity(self.customer_profile, 'ADD_TO_CART', 'Cart 1')
        CustomerActivityService.log_activity(self.customer_profile, 'ADD_TO_WISHLIST', 'Wishlist 1')
        CustomerActivityService.log_activity(self.customer_profile, 'ORDER_PLACED', 'Order 1')
        
        # Update customer metrics
        self.customer_profile.total_orders = 2
        self.customer_profile.total_spent = Decimal('250.00')
        self.customer_profile.loyalty_points = 50
        self.customer_profile.save()
        
        analytics = CustomerActivityService.get_customer_analytics(self.customer_profile)
        
        self.assertEqual(analytics['total_activities'], 6)
        self.assertEqual(analytics['login_count'], 2)
        self.assertEqual(analytics['product_views'], 1)
        self.assertEqual(analytics['cart_additions'], 1)
        self.assertEqual(analytics['wishlist_additions'], 1)
        self.assertEqual(analytics['orders_placed'], 1)
        self.assertEqual(analytics['customer_tier'], 'BRONZE')
        self.assertEqual(analytics['total_spent'], 250.00)
        self.assertEqual(analytics['loyalty_points'], 50)
        self.assertIsNotNone(analytics['last_activity'])
        self.assertGreaterEqual(analytics['account_age_days'], 0)
    
    def test_get_customer_analytics_empty(self):
        """Test getting analytics for customer with no activities."""
        analytics = CustomerActivityService.get_customer_analytics(self.customer_profile)
        
        self.assertEqual(analytics['total_activities'], 0)
        self.assertEqual(analytics['login_count'], 0)
        self.assertEqual(analytics['customer_tier'], 'BRONZE')
        self.assertEqual(analytics['total_spent'], 0.0)
        self.assertIsNone(analytics['last_activity'])
=======
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
>>>>>>> Task-10.3
