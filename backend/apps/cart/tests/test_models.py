"""
Tests for cart models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.cart.models import Cart, CartItem, SavedItem
from apps.products.models import Product, Category

User = get_user_model()


class CartModelTest(TestCase):
    """
    Test case for Cart model.
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
            discount_price=Decimal('15.00'),
            status='active'
        )
        
        # Create a cart
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_creation(self):
        """Test cart creation."""
        self.assertEqual(str(self.cart), f"Cart for {self.user.email}")
        self.assertEqual(self.cart.total_items_count, 0)
        self.assertEqual(self.cart.subtotal, 0)
    
    def test_add_item(self):
        """Test adding an item to the cart."""
        # Add an item
        cart_item = self.cart.add_item(self.product1, 2)
        
        # Check if the item was added correctly
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(self.cart.total_items_count, 2)
        self.assertEqual(self.cart.subtotal, Decimal('20.00'))
        
        # Add the same product again
        cart_item = self.cart.add_item(self.product1, 1)
        
        # Check if the quantity was updated
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(self.cart.total_items_count, 3)
        self.assertEqual(self.cart.subtotal, Decimal('30.00'))
    
    def test_remove_item(self):
        """Test removing an item from the cart."""
        # Add items
        self.cart.add_item(self.product1, 2)
        self.cart.add_item(self.product2, 1)
        
        # Check initial state
        self.assertEqual(self.cart.total_items_count, 3)
        
        # Remove an item
        result = self.cart.remove_item(self.product1)
        
        # Check if the item was removed
        self.assertTrue(result)
        self.assertEqual(self.cart.total_items_count, 1)
        self.assertEqual(self.cart.items.count(), 1)
        
        # Try to remove a non-existent item
        result = self.cart.remove_item(self.product1)
        
        # Check that it returns False
        self.assertFalse(result)
    
    def test_update_item_quantity(self):
        """Test updating item quantity."""
        # Add an item
        self.cart.add_item(self.product1, 2)
        
        # Update quantity
        cart_item = self.cart.update_item_quantity(self.product1, 5)
        
        # Check if quantity was updated
        self.assertEqual(cart_item.quantity, 5)
        self.assertEqual(self.cart.total_items_count, 5)
        
        # Update with zero quantity should remove the item
        cart_item = self.cart.update_item_quantity(self.product1, 0)
        
        # Check if item was removed
        self.assertIsNone(cart_item)
        self.assertEqual(self.cart.total_items_count, 0)
        
        # Try to update a non-existent item
        cart_item = self.cart.update_item_quantity(self.product1, 3)
        
        # Check that it returns None
        self.assertIsNone(cart_item)
    
    def test_clear(self):
        """Test clearing the cart."""
        # Add items
        self.cart.add_item(self.product1, 2)
        self.cart.add_item(self.product2, 3)
        
        # Check initial state
        self.assertEqual(self.cart.total_items_count, 5)
        
        # Clear the cart
        self.cart.clear()
        
        # Check if cart is empty
        self.assertEqual(self.cart.total_items_count, 0)
        self.assertEqual(self.cart.items.count(), 0)
    
    def test_save_item_for_later(self):
        """Test saving an item for later."""
        # Add an item
        self.cart.add_item(self.product1, 2)
        
        # Save for later
        saved_item = self.cart.save_item_for_later(self.product1)
        
        # Check if item was moved to saved items
        self.assertEqual(saved_item.product, self.product1)
        self.assertEqual(saved_item.quantity, 2)
        self.assertEqual(self.cart.total_items_count, 0)
        self.assertEqual(SavedItem.objects.filter(user=self.user).count(), 1)
        
        # Try to save a non-existent item
        saved_item = self.cart.save_item_for_later(self.product1)
        
        # Check that it returns None
        self.assertIsNone(saved_item)
    
    def test_merge_with_user_cart(self):
        """Test merging a session cart with a user cart."""
        # Create a session cart
        session_cart = Cart.objects.create(session_key='test_session')
        session_cart.add_item(self.product1, 2)
        session_cart.add_item(self.product2, 3)
        
        # Create another user with a cart
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpassword',
            first_name='Test2',
            last_name='User2'
        )
        user_cart = Cart.objects.create(user=user2)
        user_cart.add_item(self.product1, 1)
        
        # Merge session cart into user cart
        merged_cart = session_cart.merge_with_user_cart(user2)
        
        # Check if items were merged correctly
        self.assertEqual(merged_cart.total_items_count, 6)  # 1 + 2 + 3
        self.assertEqual(merged_cart.items.filter(product=self.product1).first().quantity, 3)
        self.assertEqual(merged_cart.items.filter(product=self.product2).first().quantity, 3)
        
        # Check that session cart was deleted
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(id=session_cart.id)
        
        # Test merging into a user without a cart
        session_cart2 = Cart.objects.create(session_key='test_session2')
        session_cart2.add_item(self.product1, 2)
        
        user3 = User.objects.create_user(
            email='test3@example.com',
            password='testpassword',
            first_name='Test3',
            last_name='User3'
        )
        
        # Merge session cart into user without a cart
        merged_cart2 = session_cart2.merge_with_user_cart(user3)
        
        # Check if cart was assigned to user
        self.assertEqual(merged_cart2.user, user3)
        self.assertIsNone(merged_cart2.session_key)
        self.assertEqual(merged_cart2.total_items_count, 2)


class CartItemModelTest(TestCase):
    """
    Test case for CartItem model.
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
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            category=self.category,
            sku='TP1',
            price=Decimal('10.00'),
            discount_price=Decimal('8.00'),
            status='active'
        )
        
        # Create a cart
        self.cart = Cart.objects.create(user=self.user)
        
        # Create a cart item
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_cart_item_creation(self):
        """Test cart item creation."""
        self.assertEqual(str(self.cart_item), f"{self.product.name} x 2")
        self.assertEqual(self.cart_item.line_total, Decimal('16.00'))  # 2 * 8.00 (discount price)
    
    def test_cart_item_with_custom_price(self):
        """Test cart item with custom price."""
        # Update cart item with custom price
        self.cart_item.custom_price = Decimal('5.00')
        self.cart_item.save()
        
        # Check if line total uses custom price
        self.assertEqual(self.cart_item.line_total, Decimal('10.00'))  # 2 * 5.00
    
    def test_cart_item_quantity_constraints(self):
        """Test cart item quantity constraints."""
        # Try to set quantity below minimum
        self.cart_item.quantity = 0
        self.cart_item.save()
        
        # Check if quantity was set to minimum
        self.assertEqual(self.cart_item.quantity, 1)
        
        # Try to set quantity above maximum
        self.cart_item.quantity = 150
        self.cart_item.save()
        
        # Check if quantity was set to maximum
        self.assertEqual(self.cart_item.quantity, 100)
    
    def test_cart_item_total_weight(self):
        """Test cart item total weight calculation."""
        # Initially weight is None
        self.assertIsNone(self.cart_item.total_weight)
        
        # Set product weight
        self.product.weight = Decimal('0.5')
        self.product.save()
        
        # Refresh cart item from database
        self.cart_item.refresh_from_db()
        
        # Check total weight
        self.assertEqual(self.cart_item.total_weight, Decimal('1.0'))  # 2 * 0.5


class SavedItemModelTest(TestCase):
    """
    Test case for SavedItem model.
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
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            category=self.category,
            sku='TP1',
            price=Decimal('10.00'),
            status='active'
        )
        
        # Create a saved item
        self.saved_item = SavedItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=2
        )
    
    def test_saved_item_creation(self):
        """Test saved item creation."""
        self.assertEqual(str(self.saved_item), f"Saved: {self.product.name} x 2")
    
    def test_move_to_cart(self):
        """Test moving a saved item to cart."""
        # Move to cart
        cart_item = self.saved_item.move_to_cart()
        
        # Check if item was moved to cart
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        
        # Check if saved item was deleted
        with self.assertRaises(SavedItem.DoesNotExist):
            SavedItem.objects.get(id=self.saved_item.id)
        
        # Check if cart was created
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items_count, 2)