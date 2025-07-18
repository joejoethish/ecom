"""
Cart models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from decimal import Decimal
from core.models import BaseModel


class Cart(BaseModel):
    """
    Shopping cart model with enhanced functionality.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Cart metadata
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"Cart for {self.user.email if self.user else self.session_key}"
    
    @property
    def total_items_count(self):
        """Return the total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate the subtotal of all items in the cart."""
        return sum(item.line_total for item in self.items.all())
    
    @property
    def total_weight(self):
        """Calculate the total weight of all items in the cart."""
        return sum(item.total_weight for item in self.items.all() if item.total_weight)
    
    def clear(self):
        """Remove all items from the cart."""
        self.items.all().delete()
    
    def add_item(self, product, quantity=1):
        """
        Add a product to the cart or update quantity if it already exists.
        Returns the cart item.
        """
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        return cart_item
    
    def remove_item(self, product):
        """Remove a specific product from the cart."""
        try:
            cart_item = self.items.get(product=product)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def update_item_quantity(self, product, quantity):
        """Update the quantity of a specific product in the cart."""
        try:
            cart_item = self.items.get(product=product)
            if quantity <= 0:
                cart_item.delete()
                return None
            cart_item.quantity = quantity
            cart_item.save()
            return cart_item
        except CartItem.DoesNotExist:
            return None
    
    def save_item_for_later(self, product):
        """Move an item from cart to saved items."""
        try:
            cart_item = self.items.get(product=product)
            saved_item, created = SavedItem.objects.get_or_create(
                user=self.user,
                product=product,
                defaults={'quantity': cart_item.quantity}
            )
            if not created:
                saved_item.quantity = cart_item.quantity
                saved_item.save()
            cart_item.delete()
            return saved_item
        except CartItem.DoesNotExist:
            return None
    
    def merge_with_user_cart(self, user):
        """
        Merge this session cart with a user's cart when they log in.
        """
        if not user:
            return
            
        try:
            user_cart = Cart.objects.get(user=user)
            
            # Move items from session cart to user cart
            for item in self.items.all():
                user_cart.add_item(item.product, item.quantity)
                
            # Clear the session cart
            self.delete()
            return user_cart
            
        except Cart.DoesNotExist:
            # If user doesn't have a cart, assign this cart to the user
            self.user = user
            self.session_key = None
            self.save()
            return self


class CartItem(BaseModel):
    """
    Cart item model with enhanced functionality.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    # Additional fields for better cart management
    is_gift = models.BooleanField(default=False)
    gift_message = models.CharField(max_length=200, blank=True, null=True)
    custom_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['added_at']
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def line_total(self):
        """Calculate the total price for this line item."""
        if self.custom_price:
            return self.custom_price * self.quantity
        return self.product.effective_price * self.quantity
    
    @property
    def total_weight(self):
        """Calculate the total weight for this line item."""
        if self.product.weight:
            return self.product.weight * self.quantity
        return None
    
    def save(self, *args, **kwargs):
        """Override save to ensure quantity constraints."""
        if self.quantity < 1:
            self.quantity = 1
        elif self.quantity > 100:
            self.quantity = 100
        super().save(*args, **kwargs)


class SavedItem(BaseModel):
    """
    Saved item model for "save for later" functionality.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['saved_at']),
        ]
    
    def __str__(self):
        return f"Saved: {self.product.name} x {self.quantity}"
    
    def move_to_cart(self):
        """Move this saved item to the user's cart."""
        if not self.user:
            return None
            
        cart, created = Cart.objects.get_or_create(user=self.user)
        cart_item = cart.add_item(self.product, self.quantity)
        self.delete()
        return cart_item