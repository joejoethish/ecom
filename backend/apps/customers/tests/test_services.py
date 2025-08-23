"""
Tests for customer services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.customers.services import CustomerService, AddressService, WishlistService
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
        self.assertEqual(profile.account_status, 'ACTIVE')


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
        self.assertEqual(address.city, 'New York')


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
    
    def test_get_or_create_wishlist(self):
        """Test getting or creating a wishlist."""
        wishlist = WishlistService.get_or_create_wishlist(self.customer)
        
        self.assertEqual(wishlist.customer, self.customer)
        self.assertEqual(wishlist.name, 'My Wishlist')
    
    def test_add_to_wishlist(self):
        """Test adding product to wishlist."""
        wishlist_item = WishlistService.add_to_wishlist(
            self.customer,
            self.product,
            'Want to buy this'
        )
        
        self.assertEqual(wishlist_item.product, self.product)
        self.assertEqual(wishlist_item.notes, 'Want to buy this')
    
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