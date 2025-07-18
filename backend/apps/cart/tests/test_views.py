"""
Tests for cart views.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import uuid
import json

from apps.cart.models import Cart, CartItem, SavedItem
from apps.products.models import Product, Category

User = get_user_model()


class CartViewsTest(TestCase):
    """
    Test case for cart views.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Create another test user
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpassword',
            first_name='Test2',
            last_name='User2'
        )
        
        # Create a category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            description='Test description 1',
            category=self.category,
            sku='TP1',
            price=Decimal('10.00'),
            status='active'
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            category=self.category,
            sku='TP2',
            price=Decimal('20.00'),
            status='active'
        )
        
        self.product3 = Product.objects.create(
            name='Test Product 3',
            slug='test-product-3',
            description='Test description 3',
            category=self.category,
            sku='TP3',
            price=Decimal('30.00'),
            status='out_of_stock'
        )
        
        # Create a cart for user1
        self.cart = Cart.objects.create(user=self.user)
        
        # Add items to the cart
        self.cart_item1 = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )
        
        # Create a saved item for user1
        self.saved_item = SavedItem.objects.create(
            user=self.user,
            product=self.product2,
            quantity=1
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_cart_view_authenticated(self):
        """Test cart view for authenticated user."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart']['total_items_count'], 2)
        self.assertEqual(len(response.data['cart']['items']), 1)
        self.assertEqual(response.data['cart']['items'][0]['product']['name'], 'Test Product 1')
    
    def test_cart_view_unauthenticated(self):
        """Test cart view for unauthenticated user."""
        # Create a session
        session = self.client.session
        session.create()
        session_key = session.session_key
        session.save()
        
        # Create a cart for the session
        session_cart = Cart.objects.create(session_key=session_key)
        CartItem.objects.create(
            cart=session_cart,
            product=self.product2,
            quantity=3
        )
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart']['total_items_count'], 3)
        self.assertEqual(len(response.data['cart']['items']), 1)
        self.assertEqual(response.data['cart']['items'][0]['product']['name'], 'Test Product 2')
    
    def test_add_to_cart_authenticated(self):
        """Test adding to cart for authenticated user."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Add to cart
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product2.id),
                'quantity': 3,
                'is_gift': True,
                'gift_message': 'Happy Birthday!'
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_item']['product']['name'], 'Test Product 2')
        self.assertEqual(response.data['cart_item']['quantity'], 3)
        self.assertTrue(response.data['cart_item']['is_gift'])
        self.assertEqual(response.data['cart_item']['gift_message'], 'Happy Birthday!')
        
        # Check database
        cart_item = CartItem.objects.get(cart=self.cart, product=self.product2)
        self.assertEqual(cart_item.quantity, 3)
        self.assertTrue(cart_item.is_gift)
        self.assertEqual(cart_item.gift_message, 'Happy Birthday!')
    
    def test_add_to_cart_unauthenticated(self):
        """Test adding to cart for unauthenticated user."""
        # Create a session
        session = self.client.session
        session.create()
        session_key = session.session_key
        session.save()
        
        # Add to cart
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product1.id),
                'quantity': 2
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_item']['product']['name'], 'Test Product 1')
        self.assertEqual(response.data['cart_item']['quantity'], 2)
        
        # Check database
        session_cart = Cart.objects.get(session_key=session_key)
        cart_item = CartItem.objects.get(cart=session_cart, product=self.product1)
        self.assertEqual(cart_item.quantity, 2)
    
    def test_add_to_cart_out_of_stock(self):
        """Test adding out of stock product to cart."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Add to cart
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product3.id),
                'quantity': 1
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product is out of stock')
        
        # Check database
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product3).exists())
    
    def test_update_cart_item(self):
        """Test updating cart item quantity."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Update cart item
        response = self.client.put(
            reverse('update-cart-item'),
            {
                'product_id': str(self.product1.id),
                'quantity': 5
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_item']['quantity'], 5)
        
        # Check database
        cart_item = CartItem.objects.get(cart=self.cart, product=self.product1)
        self.assertEqual(cart_item.quantity, 5)
    
    def test_remove_from_cart(self):
        """Test removing from cart."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Remove from cart
        response = self.client.post(
            reverse('remove-from-cart'),
            {
                'product_id': str(self.product1.id)
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Product removed from cart')
        
        # Check database
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())
    
    def test_clear_cart(self):
        """Test clearing cart."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Clear cart
        response = self.client.post(reverse('clear-cart'))
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Cart cleared')
        
        # Check database
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)
    
    def test_save_for_later(self):
        """Test saving for later."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Save for later
        response = self.client.post(
            reverse('save-for-later'),
            {
                'product_id': str(self.product1.id)
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['saved_item']['product']['name'], 'Test Product 1')
        
        # Check database
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())
        self.assertTrue(SavedItem.objects.filter(user=self.user, product=self.product1).exists())
    
    def test_move_to_cart(self):
        """Test moving to cart."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Move to cart
        response = self.client.post(
            reverse('move-to-cart'),
            {
                'saved_item_id': str(self.saved_item.id)
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_item']['product']['name'], 'Test Product 2')
        
        # Check database
        self.assertTrue(CartItem.objects.filter(cart=self.cart, product=self.product2).exists())
        self.assertFalse(SavedItem.objects.filter(id=self.saved_item.id).exists())
    
    def test_saved_items_view(self):
        """Test saved items view."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Get saved items
        response = self.client.get(reverse('saved-items'))
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['saved_items']), 1)
        self.assertEqual(response.data['saved_items'][0]['product']['name'], 'Test Product 2')
    
    def test_apply_coupon(self):
        """Test applying coupon."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Apply coupon
        response = self.client.post(
            reverse('apply-coupon'),
            {
                'coupon_code': 'TESTCODE'
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Coupon applied')
        
        # Check database
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.coupon_code, 'TESTCODE')
    
    def test_remove_coupon(self):
        """Test removing coupon."""
        # Set coupon on cart
        self.cart.coupon_code = 'TESTCODE'
        self.cart.save()
        
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Remove coupon
        response = self.client.post(reverse('remove-coupon'))
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Coupon removed')
        
        # Check database
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.coupon_code)
    
    def test_cart_merge_on_login(self):
        """Test cart merging when user logs in."""
        # This would typically be tested in an integration test with the authentication system
        # Here we'll just test the underlying functionality
        
        # Create a session cart
        session_cart = Cart.objects.create(session_key='test_session')
        CartItem.objects.create(
            cart=session_cart,
            product=self.product2,
            quantity=3
        )
        
        # Merge carts
        merged_cart = session_cart.merge_with_user_cart(self.user)
        
        # Check merged cart
        self.assertEqual(merged_cart.user, self.user)
        self.assertEqual(merged_cart.items.count(), 2)  # Original item + merged item
        self.assertEqual(merged_cart.items.get(product=self.product2).quantity, 3)
        
        # Check that session cart was deleted
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(id=session_cart.id)
    
    def test_invalid_product_id(self):
        """Test handling invalid product ID."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Try to add with invalid ID
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': 'invalid-id',
                'quantity': 1
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
        # Try with non-existent but valid UUID
        random_uuid = str(uuid.uuid4())
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': random_uuid,
                'quantity': 1
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product not found')
    
    def test_missing_required_fields(self):
        """Test handling missing required fields."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Try to add without product_id
        response = self.client.post(
            reverse('add-to-cart'),
            {
                'quantity': 1
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product ID is required')
        
        # Try to update without product_id
        response = self.client.put(
            reverse('update-cart-item'),
            {
                'quantity': 5
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product ID is required')
        
        # Try to remove without product_id
        response = self.client.post(
            reverse('remove-from-cart'),
            {},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product ID is required')
        
        # Try to apply coupon without coupon_code
        response = self.client.post(
            reverse('apply-coupon'),
            {},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Coupon code is required')
        
        # Try to move to cart without saved_item_id
        response = self.client.post(
            reverse('move-to-cart'),
            {},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Saved item ID is required')
    
    def test_authentication_required_endpoints(self):
        """Test endpoints that require authentication."""
        # Try to access saved items without authentication
        response = self.client.get(reverse('saved-items'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to save for later without authentication
        response = self.client.post(
            reverse('save-for-later'),
            {
                'product_id': str(self.product1.id)
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to move to cart without authentication
        response = self.client.post(
            reverse('move-to-cart'),
            {
                'saved_item_id': str(self.saved_item.id)
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_cart_item_zero_quantity(self):
        """Test updating cart item with zero quantity removes the item."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Update cart item with zero quantity
        response = self.client.put(
            reverse('update-cart-item'),
            {
                'product_id': str(self.product1.id),
                'quantity': 0
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertTrue('removed' in response.data['message'].lower())
        
        # Check database - item should be removed
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())
    
    def test_update_cart_item_negative_quantity(self):
        """Test updating cart item with negative quantity."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Update cart item with negative quantity
        response = self.client.put(
            reverse('update-cart-item'),
            {
                'product_id': str(self.product1.id),
                'quantity': -5
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertTrue('removed' in response.data['message'].lower())
        
        # Check database - item should be removed
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())
    
    def test_update_cart_item_excessive_quantity(self):
        """Test updating cart item with excessive quantity."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Update cart item with excessive quantity
        response = self.client.put(
            reverse('update-cart-item'),
            {
                'product_id': str(self.product1.id),
                'quantity': 150
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check database - quantity should be capped at 100
        cart_item = CartItem.objects.get(cart=self.cart, product=self.product1)
        self.assertEqual(cart_item.quantity, 100)
    
    def test_cart_item_line_total(self):
        """Test cart item line total calculation."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check line total in response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart']['items'][0]['line_total'], '20.00')
        
        # Add product with discount price
        self.product2.discount_price = Decimal('15.00')
        self.product2.save()
        
        self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product2.id),
                'quantity': 2
            },
            format='json'
        )
        
        # Get cart again
        response = self.client.get(reverse('cart'))
        
        # Check line total for discounted product
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Find the item for product2
        product2_item = None
        for item in response.data['cart']['items']:
            if item['product']['name'] == 'Test Product 2':
                product2_item = item
                break
        
        self.assertIsNotNone(product2_item)
        self.assertEqual(product2_item['line_total'], '30.00')  # 2 * 15.00
    
    def test_cart_subtotal(self):
        """Test cart subtotal calculation."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Add another product
        self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product2.id),
                'quantity': 3
            },
            format='json'
        )
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check subtotal
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart']['subtotal'], '80.00')  # (2 * 10.00) + (3 * 20.00)
    
    def test_cart_with_custom_price(self):
        """Test cart with custom price items."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Set custom price on cart item
        self.cart_item1.custom_price = Decimal('5.00')
        self.cart_item1.save()
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check line total with custom price
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart']['items'][0]['line_total'], '10.00')  # 2 * 5.00
        self.assertEqual(response.data['cart']['subtotal'], '10.00')
    
    def test_cart_with_gift_items(self):
        """Test cart with gift items."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Set item as gift
        self.cart_item1.is_gift = True
        self.cart_item1.gift_message = "Happy Birthday!"
        self.cart_item1.save()
        
        # Get cart
        response = self.client.get(reverse('cart'))
        
        # Check gift properties
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['cart']['items'][0]['is_gift'])
        self.assertEqual(response.data['cart']['items'][0]['gift_message'], "Happy Birthday!")
    
    def test_cart_total_weight(self):
        """Test cart total weight calculation."""
        # Set product weights
        self.product1.weight = Decimal('0.5')  # 0.5 kg
        self.product1.save()
        
        self.product2.weight = Decimal('1.0')  # 1.0 kg
        self.product2.save()
        
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Add product2 to cart
        self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': str(self.product2.id),
                'quantity': 3
            },
            format='json'
        )
        
        # Calculate expected total weight
        expected_weight = (2 * Decimal('0.5')) + (3 * Decimal('1.0'))  # 2*0.5 + 3*1.0 = 4.0 kg
        
        # Get cart
        cart = Cart.objects.get(user=self.user)
        
        # Check total weight
        self.assertEqual(cart.total_weight, expected_weight)
    
    def test_save_for_later_nonexistent_product(self):
        """Test saving a nonexistent product for later."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Try to save nonexistent product
        response = self.client.post(
            reverse('save-for-later'),
            {
                'product_id': str(uuid.uuid4())
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Product not found')
    
    def test_move_to_cart_nonexistent_saved_item(self):
        """Test moving a nonexistent saved item to cart."""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Try to move nonexistent saved item
        response = self.client.post(
            reverse('move-to-cart'),
            {
                'saved_item_id': str(uuid.uuid4())
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Saved item not found')
    
    def test_move_another_users_saved_item(self):
        """Test moving another user's saved item."""
        # Create saved item for user2
        other_saved_item = SavedItem.objects.create(
            user=self.user2,
            product=self.product1,
            quantity=1
        )
        
        # Login as user1
        self.client.force_authenticate(user=self.user)
        
        # Try to move user2's saved item
        response = self.client.post(
            reverse('move-to-cart'),
            {
                'saved_item_id': str(other_saved_item.id)
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Saved item not found')
        
        # Check that saved item still exists
        self.assertTrue(SavedItem.objects.filter(id=other_saved_item.id).exists())