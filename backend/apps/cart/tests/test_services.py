"""
Tests for cart services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.cart.models import Cart, CartItem, SavedItem
from apps.cart.services import CartService
from apps.products.models import Product, Category

User = get_user_model()


class CartServiceTest(TestCase):
    """
    Test case for CartService.
    """
    
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
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
            status='out_of_stock'
        )
    
    def test_get_or_create_cart(self):
        """Test getting or creating a cart."""
        # Get cart for user
        cart = CartService.get_or_create_cart(user=self.user)
        
        # Check if cart was created
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)
        
        # Get cart for session
        session_cart = CartService.get_or_create_cart(session_key='test_session')
        
        # Check if cart was created
        self.assertIsNotNone(session_cart)
        self.assertEqual(session_cart.session_key, 'test_session')
        
        # Get cart with both user and session (should prioritize user)
        user_cart = CartService.get_or_create_cart(user=self.user, session_key='test_session')
        
        # Check if user cart was returned
        self.assertEqual(user_cart, cart)
        
        # Test with no user or session
        no_cart = CartService.get_or_create_cart()
        
        # Check that None was returned
        self.assertIsNone(no_cart)
    
    def test_merge_carts(self):
        """Test merging carts."""
        # Create a session cart
        session_cart = Cart.objects.create(session_key='test_session')
        session_cart.add_item(self.product1, 2)
        
        # Merge with user
        merged_cart = CartService.merge_carts(session_cart, self.user)
        
        # Check if cart was merged
        self.assertEqual(merged_cart.user, self.user)
        self.assertEqual(merged_cart.total_items_count, 2)
        
        # Test with None values
        result = CartService.merge_carts(None, self.user)
        self.assertIsNone(result)
        
        result = CartService.merge_carts(session_cart, None)
        self.assertIsNone(result)
    
    def test_add_to_cart(self):
        """Test adding to cart."""
        # Create a cart
        cart = Cart.objects.create(user=self.user)
        
        # Add product to cart
        cart_item, message = CartService.add_to_cart(cart, str(self.product1.id), 2)
        
        # Check if product was added
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(message, "Product added to cart")
        
        # Add out of stock product
        cart_item, message = CartService.add_to_cart(cart, str(self.product2.id), 1)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Product is out of stock")
        
        # Add with gift options
        cart_item, message = CartService.add_to_cart(
            cart, 
            str(self.product1.id), 
            1, 
            is_gift=True, 
            gift_message="Happy Birthday!"
        )
        
        # Check if gift options were set
        self.assertTrue(cart_item.is_gift)
        self.assertEqual(cart_item.gift_message, "Happy Birthday!")
        
        # Test with invalid product ID
        cart_item, message = CartService.add_to_cart(cart, "invalid-id", 1)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Product not found")
        
        # Test with None cart
        cart_item, message = CartService.add_to_cart(None, str(self.product1.id), 1)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Cart not found")
    
    def test_remove_from_cart(self):
        """Test removing from cart."""
        # Create a cart and add an item
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)
        
        # Remove from cart
        success, message = CartService.remove_from_cart(cart, str(self.product1.id))
        
        # Check if item was removed
        self.assertTrue(success)
        self.assertEqual(message, "Product removed from cart")
        self.assertEqual(cart.total_items_count, 0)
        
        # Try to remove a product that's not in the cart
        success, message = CartService.remove_from_cart(cart, str(self.product1.id))
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Product not in cart")
        
        # Test with invalid product ID
        success, message = CartService.remove_from_cart(cart, "invalid-id")
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Product not found")
        
        # Test with None cart
        success, message = CartService.remove_from_cart(None, str(self.product1.id))
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Cart not found")
    
    def test_update_quantity(self):
        """Test updating quantity."""
        # Create a cart and add an item
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)
        
        # Update quantity
        cart_item, message = CartService.update_quantity(cart, str(self.product1.id), 5)
        
        # Check if quantity was updated
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 5)
        self.assertEqual(message, "Quantity updated")
        
        # Update with zero quantity (should remove item)
        cart_item, message = CartService.update_quantity(cart, str(self.product1.id), 0)
        
        # Check if item was removed
        self.assertIsNone(cart_item)
        self.assertTrue(message.startswith("Product removed"))
        self.assertEqual(cart.total_items_count, 0)
        
        # Try to update a product that's not in the cart
        cart_item, message = CartService.update_quantity(cart, str(self.product1.id), 3)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Product not in cart")
        
        # Test with invalid product ID
        cart_item, message = CartService.update_quantity(cart, "invalid-id", 3)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Product not found")
        
        # Test with None cart
        cart_item, message = CartService.update_quantity(None, str(self.product1.id), 3)
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Cart not found")
    
    def test_clear_cart(self):
        """Test clearing cart."""
        # Create a cart and add items
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)
        
        # Clear cart
        success, message = CartService.clear_cart(cart)
        
        # Check if cart was cleared
        self.assertTrue(success)
        self.assertEqual(message, "Cart cleared")
        self.assertEqual(cart.total_items_count, 0)
        
        # Test with None cart
        success, message = CartService.clear_cart(None)
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Cart not found")
    
    def test_save_for_later(self):
        """Test saving for later."""
        # Create a cart and add an item
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)
        
        # Save for later
        saved_item, message = CartService.save_for_later(cart, str(self.product1.id))
        
        # Check if item was saved for later
        self.assertIsNotNone(saved_item)
        self.assertEqual(saved_item.product, self.product1)
        self.assertEqual(saved_item.quantity, 2)
        self.assertEqual(message, "Item saved for later")
        self.assertEqual(cart.total_items_count, 0)
        
        # Try to save a product that's not in the cart
        saved_item, message = CartService.save_for_later(cart, str(self.product1.id))
        
        # Check that it failed
        self.assertIsNone(saved_item)
        self.assertEqual(message, "Product not in cart")
        
        # Test with invalid product ID
        saved_item, message = CartService.save_for_later(cart, "invalid-id")
        
        # Check that it failed
        self.assertIsNone(saved_item)
        self.assertEqual(message, "Product not found")
        
        # Test with None cart
        saved_item, message = CartService.save_for_later(None, str(self.product1.id))
        
        # Check that it failed
        self.assertIsNone(saved_item)
        self.assertEqual(message, "User must be logged in to save items")
        
        # Test with cart without user
        session_cart = Cart.objects.create(session_key='test_session')
        session_cart.add_item(self.product1, 1)
        
        saved_item, message = CartService.save_for_later(session_cart, str(self.product1.id))
        
        # Check that it failed
        self.assertIsNone(saved_item)
        self.assertEqual(message, "User must be logged in to save items")
    
    def test_move_to_cart(self):
        """Test moving to cart."""
        # Create a saved item
        saved_item = SavedItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=2
        )
        
        # Move to cart
        cart_item, message = CartService.move_to_cart(self.user, str(saved_item.id))
        
        # Check if item was moved to cart
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(message, "Item moved to cart")
        
        # Check if saved item was deleted
        self.assertEqual(SavedItem.objects.filter(user=self.user).count(), 0)
        
        # Test with invalid saved item ID
        cart_item, message = CartService.move_to_cart(self.user, "invalid-id")
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "Saved item not found")
        
        # Test with None user
        cart_item, message = CartService.move_to_cart(None, str(saved_item.id))
        
        # Check that it failed
        self.assertIsNone(cart_item)
        self.assertEqual(message, "User must be logged in to move saved items")
    
    def test_apply_coupon(self):
        """Test applying coupon."""
        # Create a cart
        cart = Cart.objects.create(user=self.user)
        
        # Apply coupon
        success, message = CartService.apply_coupon(cart, "TESTCODE")
        
        # Check if coupon was applied
        self.assertTrue(success)
        self.assertEqual(message, "Coupon applied")
        self.assertEqual(cart.coupon_code, "TESTCODE")
        
        # Test with None cart
        success, message = CartService.apply_coupon(None, "TESTCODE")
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Cart not found")
    
    def test_remove_coupon(self):
        """Test removing coupon."""
        # Create a cart with coupon
        cart = Cart.objects.create(user=self.user, coupon_code="TESTCODE")
        
        # Remove coupon
        success, message = CartService.remove_coupon(cart)
        
        # Check if coupon was removed
        self.assertTrue(success)
        self.assertEqual(message, "Coupon removed")
        self.assertIsNone(cart.coupon_code)
        
        # Test with None cart
        success, message = CartService.remove_coupon(None)
        
        # Check that it failed
        self.assertFalse(success)
        self.assertEqual(message, "Cart not found")
    
    def test_clean_abandoned_carts(self):
        """Test cleaning abandoned carts."""
        # Create abandoned carts
        for i in range(5):
            Cart.objects.create(session_key=f"abandoned_{i}")
        
        # Create recent carts
        for i in range(3):
            Cart.objects.create(session_key=f"recent_{i}")
        
        # Create user carts
        for i in range(2):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="testpassword"
            )
            Cart.objects.create(user=user)
        
        # Set last_activity for abandoned carts to be old
        import datetime
        from django.utils import timezone
        
        old_date = timezone.now() - datetime.timedelta(days=31)
        Cart.objects.filter(session_key__startswith="abandoned_").update(last_activity=old_date)
        
        # Clean abandoned carts
        count = CartService.clean_abandoned_carts()
        
        # Check if abandoned carts were cleaned
        self.assertEqual(count, 5)
        self.assertEqual(Cart.objects.filter(session_key__startswith="abandoned_").count(), 0)
        self.assertEqual(Cart.objects.filter(session_key__startswith="recent_").count(), 3)
        self.assertEqual(Cart.objects.filter(user__isnull=False).count(), 2)