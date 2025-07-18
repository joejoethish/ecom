"""
Cart services for the ecommerce platform.
"""
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Cart, CartItem, SavedItem
from apps.products.models import Product


class CartService:
    """
    Service class for cart operations with business logic.
    """
    
    @staticmethod
    def get_or_create_cart(user=None, session_key=None):
        """
        Get or create a cart for a user or session.
        Priority is given to user if both user and session_key are provided.
        """
        if user and user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            return cart
        
        if session_key:
            cart, created = Cart.objects.get_or_create(session_key=session_key)
            return cart
            
        return None
    
    @staticmethod
    def merge_carts(session_cart, user):
        """
        Merge a session cart into a user's cart when they log in.
        """
        if not session_cart or not user:
            return None
            
        return session_cart.merge_with_user_cart(user)
    
    @staticmethod
    def add_to_cart(cart, product_id, quantity=1, is_gift=False, gift_message=None):
        """
        Add a product to the cart with specified quantity and options.
        """
        if not cart:
            return None, "Cart not found"
            
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Check if product is out of stock
            if product.status == 'out_of_stock':
                return None, "Product is out of stock"
                
            with transaction.atomic():
                cart_item = cart.add_item(product, quantity)
                
                if is_gift:
                    cart_item.is_gift = True
                    cart_item.gift_message = gift_message
                    cart_item.save()
                    
                # Update cart last activity
                cart.last_activity = timezone.now()
                cart.save(update_fields=['last_activity', 'updated_at'])
                
                return cart_item, "Product added to cart"
                
        except Product.DoesNotExist:
            return None, "Product not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def remove_from_cart(cart, product_id):
        """
        Remove a product from the cart.
        """
        if not cart:
            return False, "Cart not found"
            
        try:
            product = Product.objects.get(id=product_id)
            
            with transaction.atomic():
                result = cart.remove_item(product)
                
                if result:
                    # Update cart last activity
                    cart.last_activity = timezone.now()
                    cart.save(update_fields=['last_activity', 'updated_at'])
                    return True, "Product removed from cart"
                else:
                    return False, "Product not in cart"
                    
        except Product.DoesNotExist:
            return False, "Product not found"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def update_quantity(cart, product_id, quantity):
        """
        Update the quantity of a product in the cart.
        """
        if not cart:
            return None, "Cart not found"
            
        if quantity <= 0:
            return CartService.remove_from_cart(cart, product_id)
            
        try:
            product = Product.objects.get(id=product_id)
            
            with transaction.atomic():
                cart_item = cart.update_item_quantity(product, quantity)
                
                if cart_item:
                    # Update cart last activity
                    cart.last_activity = timezone.now()
                    cart.save(update_fields=['last_activity', 'updated_at'])
                    return cart_item, "Quantity updated"
                else:
                    return None, "Product not in cart"
                    
        except Product.DoesNotExist:
            return None, "Product not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def clear_cart(cart):
        """
        Remove all items from the cart.
        """
        if not cart:
            return False, "Cart not found"
            
        try:
            with transaction.atomic():
                cart.clear()
                
                # Update cart last activity
                cart.last_activity = timezone.now()
                cart.save(update_fields=['last_activity', 'updated_at'])
                
                return True, "Cart cleared"
                
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def save_for_later(cart, product_id):
        """
        Move an item from cart to saved items.
        """
        if not cart or not cart.user:
            return None, "User must be logged in to save items"
            
        try:
            product = Product.objects.get(id=product_id)
            
            with transaction.atomic():
                saved_item = cart.save_item_for_later(product)
                
                if saved_item:
                    # Update cart last activity
                    cart.last_activity = timezone.now()
                    cart.save(update_fields=['last_activity', 'updated_at'])
                    return saved_item, "Item saved for later"
                else:
                    return None, "Product not in cart"
                    
        except Product.DoesNotExist:
            return None, "Product not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def move_to_cart(user, saved_item_id):
        """
        Move a saved item to the cart.
        """
        if not user:
            return None, "User must be logged in to move saved items"
            
        try:
            saved_item = SavedItem.objects.get(id=saved_item_id, user=user)
            
            with transaction.atomic():
                cart_item = saved_item.move_to_cart()
                
                if cart_item:
                    return cart_item, "Item moved to cart"
                else:
                    return None, "Failed to move item to cart"
                    
        except SavedItem.DoesNotExist:
            return None, "Saved item not found"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def apply_coupon(cart, coupon_code):
        """
        Apply a coupon code to the cart.
        This is a placeholder for future coupon functionality.
        """
        if not cart:
            return False, "Cart not found"
            
        # Placeholder for coupon validation logic
        # In a real implementation, we would check if the coupon exists and is valid
        
        cart.coupon_code = coupon_code
        cart.save(update_fields=['coupon_code', 'updated_at'])
        
        return True, "Coupon applied"
    
    @staticmethod
    def remove_coupon(cart):
        """
        Remove a coupon code from the cart.
        """
        if not cart:
            return False, "Cart not found"
            
        cart.coupon_code = None
        cart.save(update_fields=['coupon_code', 'updated_at'])
        
        return True, "Coupon removed"
    
    @staticmethod
    def clean_abandoned_carts(days=30):
        """
        Clean up abandoned carts older than the specified number of days.
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get abandoned carts
        abandoned_carts = Cart.objects.filter(
            last_activity__lt=cutoff_date,
            user__isnull=True  # Only clean session carts without users
        )
        
        count = abandoned_carts.count()
        abandoned_carts.delete()
        
        return count