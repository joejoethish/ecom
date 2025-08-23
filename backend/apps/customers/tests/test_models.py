"""
Tests for customer models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
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
        expected_str = f"{self.user.get_full_name()} ({self.user.email})"
        self.assertEqual(str(profile), expected_str)
    
    def test_customer_tier_bronze(self):
        """Test customer tier calculation - Bronze."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('500.00')
        )
        self.assertEqual(profile.customer_tier, 'BRONZE')
    
    def test_customer_tier_silver(self):
        """Test customer tier calculation - Silver."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('5000.00')
        )
        self.assertEqual(profile.customer_tier, 'SILVER')
    
    def test_customer_tier_gold(self):
        """Test customer tier calculation - Gold."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('25000.00')
        )
        self.assertEqual(profile.customer_tier, 'GOLD')
    
    def test_customer_tier_platinum(self):
        """Test customer tier calculation - Platinum."""
        profile = CustomerProfile.objects.create(
            user=self.user,
            total_spent=Decimal('150000.00')
        )
        self.assertEqual(profile.customer_tier, 'PLATINUM')


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
        
        self.address_data = {
            'customer': self.customer,
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
        
        self.assertEqual(address.customer, self.customer)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.first_name, 'John')
        self.assertEqual(address.city, 'New York')
        self.assertEqual(address.usage_count, 0)
    
    def test_address_str_method(self):
        """Test Address string representation."""
        address = Address.objects.create(**self.address_data)
        expected_str = f"{address.first_name} {address.last_name}, {address.city}"
        self.assertEqual(str(address), expected_str)


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
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=10
        )
    
    def test_create_wishlist(self):
        """Test creating a wishlist."""
        wishlist = Wishlist.objects.create(
            customer=self.customer,
            name='My Wishlist'
        )
        
        self.assertEqual(wishlist.customer, self.customer)
        self.assertEqual(wishlist.name, 'My Wishlist')
        self.assertIsNotNone(wishlist.created_at)
    
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
    
    def test_create_customer_activity(self):
        """Test creating a customer activity."""
        activity = CustomerActivity.objects.create(
            customer=self.customer,
            activity_type='LOGIN',
            description='User logged in'
        )
        
        self.assertEqual(activity.customer, self.customer)
        self.assertEqual(activity.activity_type, 'LOGIN')
        self.assertEqual(activity.description, 'User logged in')
        self.assertIsNotNone(activity.timestamp)