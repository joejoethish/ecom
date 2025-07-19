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
            newsletter_subscription=False
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
        self.assertFalse(profile.newsletter_subscription)
        self.assertEqual(profile.account_status, 'ACTIVE')
        self.assertEqual(profile.total_orders, 0)
        self.assertEqual(profile.total_spent, Decimal('0.00'))
        self.assertEqual(profile.loyalty_points, 0)
    
    def test_customer_profile_str(self):
        """Test string representation of customer profile."""
        profile = CustomerProfile.objects.create(user=self.user)
        expected_str = f"Customer Profile - {self.user.get_full_name()}"
        self.assertEqual(str(profile), expected_str)
    
    def test_get_full_name(self):
        """Test getting customer's full name."""
        profile = CustomerProfile.objects.create(user=self.user)
        self.assertEqual(profile.get_full_name(), 'John Doe')
        
        # Test with user without full name
        user_no_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='testpass123'
        )
        profile_no_name = CustomerProfile.objects.create(user=user_no_name)
        self.assertEqual(profile_no_name.get_full_name(), 'noname@example.com')
    
    def test_update_order_metrics(self):
        """Test updating customer order metrics."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        # Update metrics
        order_amount = Decimal('99.99')
        profile.update_order_metrics(order_amount)
        
        profile.refresh_from_db()
        self.assertEqual(profile.total_orders, 1)
        self.assertEqual(profile.total_spent, order_amount)
        self.assertIsNotNone(profile.last_order_date)
    
    def test_add_loyalty_points(self):
        """Test adding loyalty points."""
        profile = CustomerProfile.objects.create(user=self.user)
        
        profile.add_loyalty_points(100)
        
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 100)
        
        # Add more points
        profile.add_loyalty_points(50)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 150)
    
    def test_deduct_loyalty_points_success(self):
        """Test deducting loyalty points successfully."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            loyalty_points=100
        )
        
        result = profile.deduct_loyalty_points(50)
        
        self.assertTrue(result)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 50)
    
    def test_deduct_loyalty_points_insufficient(self):
        """Test deducting loyalty points with insufficient balance."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            loyalty_points=30
        )
        
        result = profile.deduct_loyalty_points(50)
        
        self.assertFalse(result)
        profile.refresh_from_db()
        self.assertEqual(profile.loyalty_points, 30)  # Should remain unchanged
    
    def test_customer_tier_bronze(self):
        """Test customer tier calculation - Bronze."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('5000.00')
        )
        self.assertEqual(profile.customer_tier, 'BRONZE')
    
    def test_customer_tier_silver(self):
        """Test customer tier calculation - Silver."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('25000.00')
        )
        self.assertEqual(profile.customer_tier, 'SILVER')
    
    def test_customer_tier_gold(self):
        """Test customer tier calculation - Gold."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('75000.00')
        )
        self.assertEqual(profile.customer_tier, 'GOLD')
    
    def test_customer_tier_platinum(self):
        """Test customer tier calculation - Platinum."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('150000.00')
        )
        self.assertEqual(profile.customer_tier, 'PLATINUM')
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        # Valid phone number
        profile = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+1234567890'
        )
        profile.full_clean()  # Should not raise ValidationError
        
        # Invalid phone number
        profile.phone_number = 'invalid-phone'
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_unique_user_constraint(self):
        """Test that each user can have only one customer profile."""
        CustomerProfile.objects.create(user=self.user)
        
        with self.assertRaises(IntegrityError):
            CustomerProfile.objects.create(user=self.user)


class AddressModelTest(TestCase):
    """Test cases for Address model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.user)
        
        self.address_data = {
            'customer': self.customer_profile,
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
        address = Address.objects.create(**self.address_data)
        
        self.assertEqual(address.customer, self.customer_profile)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.first_name, 'John')
        self.assertEqual(address.city, 'New York')
        self.assertEqual(address.usage_count, 0)
        self.assertFalse(address.is_default)
    
    def test_address_str(self):
        """Test string representation of address."""
        address = Address.objects.create(**self.address_data)
        expected_str = "John Doe - New York, NY"
        self.assertEqual(str(address), expected_str)
    
    def test_get_full_address(self):
        """Test getting formatted full address."""
        address = Address.objects.create(**self.address_data)
        expected_address = "123 Main St, New York, NY, 10001, USA"
        self.assertEqual(address.get_full_address(), expected_address)
        
        # Test with address line 2
        address.address_line_2 = "Apt 4B"
        address.save()
        expected_address_with_line2 = "123 Main St, Apt 4B, New York, NY, 10001, USA"
        self.assertEqual(address.get_full_address(), expected_address_with_line2)
    
    def test_mark_as_used(self):
        """Test marking address as used."""
        address = Address.objects.create(**self.address_data)
        
        address.mark_as_used()
        
        address.refresh_from_db()
        self.assertEqual(address.usage_count, 1)
        self.assertIsNotNone(address.last_used)
        
        # Mark as used again
        address.mark_as_used()
        address.refresh_from_db()
        self.assertEqual(address.usage_count, 2)
    
    def test_default_address_constraint(self):
        """Test that only one default address per customer is allowed."""
        # Create first address as default
        address1 = Address.objects.create(**self.address_data)
        address1.is_default = True
        address1.save()
        
        # Create second address as default
        address_data_2 = self.address_data.copy()
        address_data_2['type'] = 'WORK'
        address2 = Address.objects.create(**address_data_2)
        address2.is_default = True
        address2.save()
        
        # First address should no longer be default
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)
    
    def test_default_billing_address_constraint(self):
        """Test that only one default billing address per customer is allowed."""
        # Create first address as default billing
        address1 = Address.objects.create(**self.address_data)
        address1.is_billing_default = True
        address1.save()
        
        # Create second address as default billing
        address_data_2 = self.address_data.copy()
        address_data_2['type'] = 'WORK'
        address2 = Address.objects.create(**address_data_2)
        address2.is_billing_default = True
        address2.save()
        
        # First address should no longer be default billing
        address1.refresh_from_db()
        self.assertFalse(address1.is_billing_default)
        self.assertTrue(address2.is_billing_default)
    
    def test_default_shipping_address_constraint(self):
        """Test that only one default shipping address per customer is allowed."""
        # Create first address as default shipping
        address1 = Address.objects.create(**self.address_data)
        address1.is_shipping_default = True
        address1.save()
        
        # Create second address as default shipping
        address_data_2 = self.address_data.copy()
        address_data_2['type'] = 'WORK'
        address2 = Address.objects.create(**address_data_2)
        address2.is_shipping_default = True
        address2.save()
        
        # First address should no longer be default shipping
        address1.refresh_from_db()
        self.assertFalse(address1.is_shipping_default)
        self.assertTrue(address2.is_shipping_default)
    
    def test_postal_code_validation(self):
        """Test postal code validation."""
        address = Address.objects.create(**self.address_data)
        
        # Valid postal codes
        valid_codes = ['10001', 'SW1A 1AA', '12345-6789', 'K1A0A6']
        for code in valid_codes:
            address.postal_code = code
            address.full_clean()  # Should not raise ValidationError
        
        # Invalid postal codes
        invalid_codes = ['invalid@postal', '!@#$%']
        for code in invalid_codes:
            address.postal_code = code
            with self.assertRaises(ValidationError):
                address.full_clean()


class WishlistModelTest(TestCase):
    """Test cases for Wishlist model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.user)
    
    def test_create_wishlist(self):
        """Test creating a wishlist."""
        wishlist = Wishlist.objects.create(
            customer=self.customer_profile,
            name='My Wishlist'
        )
        
        self.assertEqual(wishlist.customer, self.customer_profile)
        self.assertEqual(wishlist.name, 'My Wishlist')
        self.assertFalse(wishlist.is_public)
    
    def test_wishlist_str(self):
        """Test string representation of wishlist."""
        wishlist = Wishlist.objects.create(
            customer=self.customer_profile,
            name='Holiday Wishlist'
        )
        expected_str = f"{self.customer_profile.get_full_name()}'s Holiday Wishlist"
        self.assertEqual(str(wishlist), expected_str)
    
    def test_item_count_property_empty(self):
        """Test item count property with empty wishlist."""
        wishlist = Wishlist.objects.create(customer=self.customer_profile)
        self.assertEqual(wishlist.item_count, 0)
    
    def test_item_count_property_with_items(self):
        """Test item count property with items."""
        wishlist = Wishlist.objects.create(customer=self.customer_profile)
        
        # Create test products
        category = Category.objects.create(name='Test Category', slug='test-category')
        product1 = Product.objects.create(
            name='Product 1', slug='product-1', category=category,
            price=Decimal('99.99'), sku='PROD-001'
        )
        product2 = Product.objects.create(
            name='Product 2', slug='product-2', category=category,
            price=Decimal('149.99'), sku='PROD-002'
        )
        
        # Add items to wishlist
        WishlistItem.objects.create(wishlist=wishlist, product=product1)
        WishlistItem.objects.create(wishlist=wishlist, product=product2)
        
        self.assertEqual(wishlist.item_count, 2)


class WishlistItemModelTest(TestCase):
    """Test cases for WishlistItem model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.user)
        self.wishlist = Wishlist.objects.create(customer=self.customer_profile)
        
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
    
    def test_create_wishlist_item(self):
        """Test creating a wishlist item."""
        item = WishlistItem.objects.create(
            wishlist=self.wishlist,
            product=self.product,
            notes='Want to buy this'
        )
        
        self.assertEqual(item.wishlist, self.wishlist)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.notes, 'Want to buy this')
        self.assertIsNotNone(item.added_at)
    
    def test_wishlist_item_str(self):
        """Test string representation of wishlist item."""
        item = WishlistItem.objects.create(
            wishlist=self.wishlist,
            product=self.product
        )
        expected_str = f"{self.product.name} in {self.customer_profile.get_full_name()}'s wishlist"
        self.assertEqual(str(item), expected_str)
    
    def test_unique_together_constraint(self):
        """Test that same product cannot be added to wishlist twice."""
        WishlistItem.objects.create(
            wishlist=self.wishlist,
            product=self.product
        )
        
        with self.assertRaises(IntegrityError):
            WishlistItem.objects.create(
                wishlist=self.wishlist,
                product=self.product
            )


class CustomerActivityModelTest(TestCase):
    """Test cases for CustomerActivity model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.user)
        
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
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Viewed test product',
            product=self.product,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...',
            session_key='abc123',
            metadata={'page': 'product-detail'}
        )
        
        self.assertEqual(activity.customer, self.customer_profile)
        self.assertEqual(activity.activity_type, 'PRODUCT_VIEW')
        self.assertEqual(activity.description, 'Viewed test product')
        self.assertEqual(activity.product, self.product)
        self.assertEqual(activity.ip_address, '192.168.1.1')
        self.assertEqual(activity.user_agent, 'Mozilla/5.0...')
        self.assertEqual(activity.session_key, 'abc123')
        self.assertEqual(activity.metadata['page'], 'product-detail')
    
    def test_customer_activity_str(self):
        """Test string representation of customer activity."""
        activity = CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='User logged in'
        )
        expected_str = f"{self.customer_profile.get_full_name()} - Login"
        self.assertEqual(str(activity), expected_str)
    
    def test_activity_ordering(self):
        """Test that activities are ordered by creation date (newest first)."""
        # Create activities with slight time difference
        activity1 = CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN',
            description='First login'
        )
        
        activity2 = CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='PRODUCT_VIEW',
            description='Product view'
        )
        
        activities = CustomerActivity.objects.all()
        self.assertEqual(activities[0], activity2)  # Most recent first
        self.assertEqual(activities[1], activity1)
    
    def test_activity_with_minimal_data(self):
        """Test creating activity with minimal required data."""
        activity = CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN'
        )
        
        self.assertEqual(activity.customer, self.customer_profile)
        self.assertEqual(activity.activity_type, 'LOGIN')
        self.assertEqual(activity.description, '')
        self.assertIsNone(activity.product)
        self.assertIsNone(activity.order)
        self.assertEqual(activity.metadata, {})
    
    def test_activity_metadata_default(self):
        """Test that metadata field defaults to empty dict."""
        activity = CustomerActivity.objects.create(
            customer=self.customer_profile,
            activity_type='LOGIN'
        )
        
        self.assertIsInstance(activity.metadata, dict)
        self.assertEqual(activity.metadata, {})
        
        # Test that we can add to metadata
        activity.metadata['test_key'] = 'test_value'
        activity.save()
        
        activity.refresh_from_db()
        self.assertEqual(activity.metadata['test_key'], 'test_value')