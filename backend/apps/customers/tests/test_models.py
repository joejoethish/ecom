"""
Tests for customer models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal

from apps.customers.models import (
    CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
)
from apps.products.models import Product, Category

User = get_user_model()


class CustomerProfileModelTest(TestCase):
    """Test cases for CustomerProfile model."""
    
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
        profile = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            gender='M',
            newsletter_subscription=True
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
        self.assertTrue(profile.newsletter_subscription)
        self.assertEqual(profile.account_status, 'ACTIVE')
        self.assertEqual(profile.total_orders, 0)
        self.assertEqual(profile.total_spent, Decimal('0.00'))
        self.assertEqual(profile.loyalty_points, 0)
    
    def test_customer_profile_str_method(self):
        """Test CustomerProfile string representation."""
        profile = CustomerProfile.objects.create(user=self.user)
        expected = f"Customer Profile - {self.user.get_full_name()}"
        self.assertEqual(str(profile), expected)
    
    def test_get_full_name_method(self):
        """Test get_full_name method."""
        profile = CustomerProfile.objects.create(user=self.user)
        self.assertEqual(profile.get_full_name(), 'John Doe')
    
    def test_update_order_metrics(self):
        """Test updating order metrics."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        profile.update_order_metrics(Decimal('100.50'))
        
        profile.refresh_from_db()
        self.assertEqual(profile.total_orders, 1)
        self.assertEqual(profile.total_spent, Decimal('100.50'))
        self.assertIsNotNone(profile.last_order_date)
    
    def test_loyalty_points_operations(self):
        """Test loyalty points add and deduct operations."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        # Add points
        profile.add_loyalty_points(100)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 100)
        
        # Deduct points - successful
        result = profile.deduct_loyalty_points(50)
        self.assertTrue(result)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 50)
        
        # Deduct points - insufficient balance
        result = profile.deduct_loyalty_points(100)
        self.assertFalse(result)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 50)
    
    def test_customer_tier_property(self):
        """Test customer tier calculation."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        # Bronze tier
        self.assertEqual(profile.customer_tier, 'BRONZE')
        
        # Silver tier
        profile.total_spent = Decimal('15000')
        self.assertEqual(profile.customer_tier, 'SILVER')
        
        # Gold tier
        profile.total_spent = Decimal('75000')
        self.assertEqual(profile.customer_tier, 'GOLD')
        
        # Platinum tier
        profile.total_spent = Decimal('150000')
        self.assertEqual(profile.customer_tier, 'PLATINUM')
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        # Valid phone numbers
        valid_phones = ['+1234567890', '1234567890', '+919876543210']
        for phone in valid_phones:
            profile = CustomerProfile(user=self.user, phone_number=phone)
            profile.full_clean()  # Should not raise ValidationError
        
        # Invalid phone numbers
        invalid_phones = ['123', 'abc123', '+123abc456']
        for phone in invalid_phones:
            profile = CustomerProfile(user=self.user, phone_number=phone)
            with self.assertRaises(ValidationError):
                profile.full_clean()


class AddressModelTest(TestCase):
    """Test cases for Address model."""
    
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
        address = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            phone='+1234567890'
        )
        
        self.assertEqual(address.customer, self.customer)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.first_name, 'John')
        self.assertEqual(address.city, 'New York')
        self.assertEqual(address.usage_count, 0)
    
    def test_address_str_method(self):
        """Test Address string representation."""
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
        
        expected = "John Doe - New York, NY"
        self.assertEqual(str(address), expected)
    
    def test_default_address_constraint(self):
        """Test that only one default address is allowed per customer."""
        # Create first address as default
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
        
        # Create second address as default
        address2 = Address.objects.create(
            customer=self.customer,
            type='WORK',
            first_name='John',
            last_name='Doe',
            address_line_1='456 Work Ave',
            city='Boston',
            state='MA',
            postal_code='02101',
            country='USA',
            is_default=True
        )
        
        # Refresh first address - should no longer be default
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)
    
    def test_mark_as_used_method(self):
        """Test mark_as_used method."""
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
        
        address.mark_as_used()
        
        address.refresh_from_db()
        self.assertEqual(address.usage_count, 1)
        self.assertIsNotNone(address.last_used)
    
    def test_get_full_address_method(self):
        """Test get_full_address method."""
        address = Address.objects.create(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            address_line_2='Apt 4B',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
        
        expected = "123 Main St, Apt 4B, New York, NY, 10001, USA"
        self.assertEqual(address.get_full_address(), expected)
    
    def test_phone_number_validation(self):
        """Test address phone number validation."""
        # Valid phone number
        address = Address(
            customer=self.customer,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            phone='+1234567890'
        )
        address.full_clean()  # Should not raise ValidationError
        
        # Invalid phone number
        address.phone = 'invalid-phone'
        with self.assertRaises(ValidationError):
            address.full_clean()


class WishlistModelTest(TestCase):
    """Test cases for Wishlist and WishlistItem models."""
    
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
    
    def test_create_wishlist(self):
        """Test creating a wishlist."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        self.assertEqual(wishlist.customer, self.customer)
        self.assertEqual(wishlist.name, 'My Wishlist')
        self.assertFalse(wishlist.is_public)
    
    def test_wishlist_str_method(self):
        """Test Wishlist string representation."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        expected = f"{self.customer.get_full_name()}'s My Wishlist"
        self.assertEqual(str(wishlist), expected)
    
    def test_wishlist_item_count_property(self):
        """Test wishlist item_count property."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        self.assertEqual(wishlist.item_count, 0)
        
        # Add item to wishlist
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        self.assertEqual(wishlist.item_count, 1)
    
    def test_create_wishlist_item(self):
        """Test creating a wishlist item."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product,
            notes='Want to buy this'
        )
        
        self.assertEqual(item.wishlist, wishlist)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.notes, 'Want to buy this')
        self.assertIsNotNone(item.added_at)
    
    def test_wishlist_item_str_method(self):
        """Test WishlistItem string representation."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        expected = f"{self.product.name} in {self.customer.get_full_name()}'s wishlist"
        self.assertEqual(str(item), expected)
    
    def test_wishlist_item_unique_constraint(self):
        """Test that same product cannot be added twice to same wishlist."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        # Create first item
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        # Try to create duplicate item
        with self.assertRaises(IntegrityError):
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=self.product
            )


class CustomerActivityModelTest(TestCase):
    """Test cases for CustomerActivity model."""
    
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
    
    def test_create_customer_activity(self):
        """Test creating a customer activity."""
        activity = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='LOGIN',
            description='User logged in',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...',
            session_key='abc123',
            metadata={'device': 'mobile'}
        )
        
        self.assertEqual(activity.customer, self.customer)
        self.assertEqual(activity.activity_type, 'LOGIN')
        self.assertEqual(activity.description, 'User logged in')
        self.assertEqual(activity.ip_address, '192.168.1.1')
        self.assertEqual(activity.metadata, {'device': 'mobile'})
    
    def test_customer_activity_str_method(self):
        """Test CustomerActivity string representation."""
        activity = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='PRODUCT_VIEW',
            description='Viewed product',
            product=self.product
        )
        
        expected = f"{self.customer.get_full_name()} - Product View"
        self.assertEqual(str(activity), expected)
    
    def test_customer_activity_with_product(self):
        """Test customer activity with related product."""
        activity = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='PRODUCT_VIEW',
            description='Viewed product',
            product=self.product
        )
        
        self.assertEqual(activity.product, self.product)
    
    def test_customer_activity_ordering(self):
        """Test customer activity ordering (most recent first)."""
        # Create activities with different timestamps
        activity1 = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='LOGIN',
            description='First login'
        )
        
        activity2 = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='PRODUCT_VIEW',
            description='Viewed product'
        )
        
        activities = list(CustomerActivity.objects.all())
        self.assertEqual(activities[0], activity2)  # Most recent first
        self.assertEqual(activities[1], activity1)