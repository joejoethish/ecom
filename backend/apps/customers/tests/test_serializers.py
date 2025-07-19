"""
Tests for customer serializers.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from decimal import Decimal

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem
from apps.customers.serializers import (
    CustomerProfileSerializer, CustomerProfileCreateSerializer,
    AddressSerializer, AddressCreateSerializer,
    WishlistSerializer, WishlistItemSerializer,
    CustomerActivitySerializer, CustomerAnalyticsSerializer,
    CustomerListSerializer, CustomerDetailSerializer
)
from apps.customers.services import CustomerService
from apps.products.models import Product, Category

User = get_user_model()


class CustomerProfileSerializerTest(TestCase):
    """Test cases for CustomerProfileSerializer."""
    
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
            phone_number='+1234567890',
            gender='M'
        )
        self.factory = APIRequestFactory()
    
    def test_serialize_customer_profile(self):
        """Test serializing customer profile."""
        serializer = CustomerProfileSerializer(self.customer_profile)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['full_name'], 'John Doe')
        self.assertEqual(data['phone_number'], '+1234567890')
        self.assertEqual(data['gender'], 'M')
        self.assertEqual(data['customer_tier'], 'BRONZE')
        self.assertEqual(data['account_status'], 'ACTIVE')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_update_customer_profile(self):
        """Test updating customer profile through serializer."""
        data = {
            'phone_number': '+9876543210',
            'gender': 'F',
            'newsletter_subscription': False,
            'user': {
                'first_name': 'Jane',
                'last_name': 'Smith'
            }
        }
        
        serializer = CustomerProfileSerializer(
            self.customer_profile, 
            data=data, 
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.phone_number, '+9876543210')
        self.assertEqual(updated_profile.gender, 'F')
        self.assertFalse(updated_profile.newsletter_subscription)
        
        # Check user fields were updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
    
    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated."""
        data = {
            'total_orders': 100,
            'total_spent': '5000.00',
            'loyalty_points': 500,
            'account_status': 'SUSPENDED'
        }
        
        serializer = CustomerProfileSerializer(
            self.customer_profile,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        # Read-only fields should not be updated
        self.assertEqual(updated_profile.total_orders, 0)
        self.assertEqual(updated_profile.total_spent, Decimal('0.00'))
        self.assertEqual(updated_profile.loyalty_points, 0)
        self.assertEqual(updated_profile.account_status, 'ACTIVE')


class CustomerProfileCreateSerializerTest(TestCase):
    """Test cases for CustomerProfileCreateSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()
    
    def test_create_customer_profile(self):
        """Test creating customer profile through serializer."""
        data = {
            'phone_number': '+1234567890',
            'gender': 'M',
            'newsletter_subscription': False,
            'user': {
                'first_name': 'John',
                'last_name': 'Doe'
            }
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = CustomerProfileCreateSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.gender, 'M')
        self.assertFalse(profile.newsletter_subscription)
        
        # Check user fields were updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')


class AddressSerializerTest(TestCase):
    """Test cases for AddressSerializer."""
    
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
    
    def test_serialize_address(self):
        """Test serializing address."""
        address = Address.objects.create(
            customer=self.customer_profile,
            **self.address_data
        )
        
        serializer = AddressSerializer(address)
        data = serializer.data
        
        self.assertEqual(data['type'], 'HOME')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['city'], 'New York')
        self.assertEqual(data['full_address'], address.get_full_address())
        self.assertIn('created_at', data)
    
    def test_create_address(self):
        """Test creating address through serializer."""
        serializer = AddressCreateSerializer(
            data=self.address_data,
            context={'customer_profile': self.customer_profile}
        )
        
        self.assertTrue(serializer.is_valid())
        address = serializer.save()
        
        self.assertEqual(address.customer, self.customer_profile)
        self.assertEqual(address.type, 'HOME')
        self.assertEqual(address.city, 'New York')
    
    def test_validate_postal_code(self):
        """Test postal code validation."""
        # Valid postal codes
        valid_data = self.address_data.copy()
        valid_data['postal_code'] = '12345'
        
        serializer = AddressCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid postal code
        invalid_data = self.address_data.copy()
        invalid_data['postal_code'] = 'invalid@postal'
        
        serializer = AddressCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('postal_code', serializer.errors)
    
    def test_first_address_defaults(self):
        """Test that first address gets set as all defaults."""
        serializer = AddressCreateSerializer(
            data=self.address_data,
            context={'customer_profile': self.customer_profile}
        )
        
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        
        # Should be set as all defaults since it's the first address
        self.assertTrue(validated_data['is_default'])
        self.assertTrue(validated_data['is_billing_default'])
        self.assertTrue(validated_data['is_shipping_default'])


class WishlistSerializerTest(TestCase):
    """Test cases for WishlistSerializer."""
    
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
    
    def test_serialize_wishlist(self):
        """Test serializing wishlist."""
        wishlist = self.customer_profile.wishlist
        
        # Add item to wishlist
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product,
            notes='Want to buy this'
        )
        
        serializer = WishlistSerializer(wishlist)
        data = serializer.data
        
        self.assertEqual(data['name'], 'My Wishlist')
        self.assertEqual(data['item_count'], 1)
        self.assertEqual(data['customer_name'], self.user.email)
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['notes'], 'Want to buy this')
    
    def test_serialize_empty_wishlist(self):
        """Test serializing empty wishlist."""
        wishlist = self.customer_profile.wishlist
        
        serializer = WishlistSerializer(wishlist)
        data = serializer.data
        
        self.assertEqual(data['item_count'], 0)
        self.assertEqual(len(data['items']), 0)


class WishlistItemSerializerTest(TestCase):
    """Test cases for WishlistItemSerializer."""
    
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
    
    def test_serialize_wishlist_item(self):
        """Test serializing wishlist item."""
        wishlist_item = WishlistItem.objects.create(
            wishlist=self.customer_profile.wishlist,
            product=self.product,
            notes='Want to buy this'
        )
        
        serializer = WishlistItemSerializer(wishlist_item)
        data = serializer.data
        
        self.assertEqual(data['notes'], 'Want to buy this')
        self.assertIn('product', data)
        self.assertEqual(data['product']['name'], 'Test Product')
        self.assertIn('added_at', data)
    
    def test_create_wishlist_item(self):
        """Test creating wishlist item through serializer."""
        data = {
            'product_id': self.product.id,
            'notes': 'Want to buy this'
        }
        
        serializer = WishlistItemSerializer(
            data=data,
            context={'customer_profile': self.customer_profile}
        )
        
        self.assertTrue(serializer.is_valid())
        wishlist_item = serializer.save()
        
        self.assertEqual(wishlist_item.product, self.product)
        self.assertEqual(wishlist_item.notes, 'Want to buy this')
    
    def test_create_wishlist_item_invalid_product(self):
        """Test creating wishlist item with invalid product ID."""
        data = {
            'product_id': 99999,  # Non-existent product
            'notes': 'Want to buy this'
        }
        
        serializer = WishlistItemSerializer(
            data=data,
            context={'customer_profile': self.customer_profile}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)


class CustomerListSerializerTest(TestCase):
    """Test cases for CustomerListSerializer."""
    
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
        
        # Create address
        Address.objects.create(
            customer=self.customer_profile,
            type='HOME',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA'
        )
    
    def test_serialize_customer_list(self):
        """Test serializing customer for list view."""
        serializer = CustomerListSerializer(self.customer_profile)
        data = serializer.data
        
        self.assertEqual(data['full_name'], 'John Doe')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['phone_number'], '+1234567890')
        self.assertEqual(data['customer_tier'], 'BRONZE')
        self.assertEqual(data['address_count'], 1)
        self.assertEqual(data['wishlist_count'], 0)


class CustomerDetailSerializerTest(TestCase):
    """Test cases for CustomerDetailSerializer."""
    
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
    
    def test_serialize_customer_detail(self):
        """Test serializing customer for detail view."""
        serializer = CustomerDetailSerializer(self.customer_profile)
        data = serializer.data
        
        self.assertEqual(data['full_name'], 'John Doe')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['username'], 'testuser')
        self.assertIn('addresses', data)
        self.assertIn('wishlist', data)
        self.assertIn('recent_activities', data)


class CustomerAnalyticsSerializerTest(TestCase):
    """Test cases for CustomerAnalyticsSerializer."""
    
    def test_serialize_analytics_data(self):
        """Test serializing analytics data."""
        analytics_data = {
            'total_activities': 10,
            'login_count': 5,
            'product_views': 3,
            'cart_additions': 2,
            'wishlist_additions': 1,
            'orders_placed': 1,
            'reviews_submitted': 0,
            'last_activity': '2023-01-01T12:00:00Z',
            'customer_tier': 'BRONZE',
            'total_spent': 150.50,
            'loyalty_points': 75,
            'account_age_days': 30
        }
        
        serializer = CustomerAnalyticsSerializer(analytics_data)
        data = serializer.data
        
        self.assertEqual(data['total_activities'], 10)
        self.assertEqual(data['login_count'], 5)
        self.assertEqual(data['customer_tier'], 'BRONZE')
        self.assertEqual(data['total_spent'], 150.50)
        self.assertEqual(data['loyalty_points'], 75)