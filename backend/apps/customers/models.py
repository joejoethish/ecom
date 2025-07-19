"""
Customer models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from core.models import BaseModel


class CustomerProfile(BaseModel):
    """
    Enhanced customer profile model with comprehensive customer information.
    """
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('N', _('Prefer not to say')),
    ]
    
    ACCOUNT_STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('SUSPENDED', _('Suspended')),
        ('BLOCKED', _('Blocked')),
        ('PENDING_VERIFICATION', _('Pending Verification')),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_profile'
    )
    
    # Personal Information
    date_of_birth = models.DateField(_('Date of Birth'), null=True, blank=True)
    gender = models.CharField(
        _('Gender'), 
        max_length=1, 
        choices=GENDER_CHOICES, 
        blank=True
    )
    avatar = models.ImageField(
        _('Avatar'), 
        upload_to='customers/avatars/', 
        blank=True, 
        null=True
    )
    
    # Contact Information
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )
    phone_number = models.CharField(
        _('Phone Number'),
        validators=[phone_validator],
        max_length=17,
        blank=True
    )
    alternate_phone = models.CharField(
        _('Alternate Phone'),
        validators=[phone_validator],
        max_length=17,
        blank=True
    )
    
    # Account Management
    account_status = models.CharField(
        _('Account Status'),
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='ACTIVE'
    )
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    verification_date = models.DateTimeField(_('Verification Date'), null=True, blank=True)
    
    # Preferences
    newsletter_subscription = models.BooleanField(_('Newsletter Subscription'), default=True)
    sms_notifications = models.BooleanField(_('SMS Notifications'), default=True)
    email_notifications = models.BooleanField(_('Email Notifications'), default=True)
    push_notifications = models.BooleanField(_('Push Notifications'), default=True)
    
    # Customer Metrics
    total_orders = models.PositiveIntegerField(_('Total Orders'), default=0)
    total_spent = models.DecimalField(
        _('Total Spent'), 
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    loyalty_points = models.PositiveIntegerField(_('Loyalty Points'), default=0)
    
    # Timestamps
    last_login_date = models.DateTimeField(_('Last Login Date'), null=True, blank=True)
    last_order_date = models.DateTimeField(_('Last Order Date'), null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(_('Admin Notes'), blank=True, help_text=_('Internal notes for admin use'))
    
    class Meta:
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')
        indexes = [
            models.Index(fields=['account_status']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['total_orders']),
            models.Index(fields=['total_spent']),
            models.Index(fields=['last_login_date']),
        ]
    
    def __str__(self):
        return f"Customer Profile - {self.user.get_full_name() or self.user.email}"
    
    def get_full_name(self):
        """Get customer's full name."""
        return self.user.get_full_name() or self.user.email
    
    def update_order_metrics(self, order_amount):
        """Update customer order metrics."""
        self.total_orders += 1
        self.total_spent += order_amount
        self.last_order_date = models.timezone.now()
        self.save(update_fields=['total_orders', 'total_spent', 'last_order_date'])
    
    def add_loyalty_points(self, points):
        """Add loyalty points to customer account."""
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points'])
    
    def deduct_loyalty_points(self, points):
        """Deduct loyalty points from customer account."""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points'])
            return True
        return False
    
    @property
    def customer_tier(self):
        """Determine customer tier based on total spent."""
        if self.total_spent >= 100000:  # 1 Lakh
            return 'PLATINUM'
        elif self.total_spent >= 50000:  # 50K
            return 'GOLD'
        elif self.total_spent >= 10000:  # 10K
            return 'SILVER'
        else:
            return 'BRONZE'


class Address(BaseModel):
    """
    Enhanced customer address model with comprehensive address management.
    """
    ADDRESS_TYPES = [
        ('HOME', _('Home')),
        ('WORK', _('Work')),
        ('OTHER', _('Other')),
    ]
    
    customer = models.ForeignKey(
        CustomerProfile, 
        on_delete=models.CASCADE, 
        related_name='addresses'
    )
    type = models.CharField(_('Address Type'), max_length=10, choices=ADDRESS_TYPES)
    
    # Personal Information
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    company = models.CharField(_('Company'), max_length=100, blank=True)
    
    # Address Information
    address_line_1 = models.CharField(_('Address Line 1'), max_length=200)
    address_line_2 = models.CharField(_('Address Line 2'), max_length=200, blank=True)
    city = models.CharField(_('City'), max_length=100)
    state = models.CharField(_('State'), max_length=100)
    postal_code = models.CharField(_('Postal Code'), max_length=20)
    country = models.CharField(_('Country'), max_length=100, default='India')
    
    # Contact Information
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )
    phone = models.CharField(
        _('Phone Number'),
        validators=[phone_validator],
        max_length=17,
        blank=True
    )
    
    # Address Settings
    is_default = models.BooleanField(_('Default Address'), default=False)
    is_billing_default = models.BooleanField(_('Default Billing Address'), default=False)
    is_shipping_default = models.BooleanField(_('Default Shipping Address'), default=False)
    
    # Delivery Instructions
    delivery_instructions = models.TextField(
        _('Delivery Instructions'), 
        blank=True,
        help_text=_('Special instructions for delivery')
    )
    
    # Location Data (for future use with maps)
    latitude = models.DecimalField(
        _('Latitude'), 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        _('Longitude'), 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    # Usage Tracking
    usage_count = models.PositiveIntegerField(_('Usage Count'), default=0)
    last_used = models.DateTimeField(_('Last Used'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        indexes = [
            models.Index(fields=['customer', 'is_default']),
            models.Index(fields=['customer', 'type']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['city', 'state']),
        ]
        constraints = [
            # Ensure only one default address per customer
            models.UniqueConstraint(
                fields=['customer'],
                condition=Q(is_default=True),
                name='unique_default_address_per_customer'
            ),
            # Ensure only one default billing address per customer
            models.UniqueConstraint(
                fields=['customer'],
                condition=Q(is_billing_default=True),
                name='unique_default_billing_address_per_customer'
            ),
            # Ensure only one default shipping address per customer
            models.UniqueConstraint(
                fields=['customer'],
                condition=Q(is_shipping_default=True),
                name='unique_default_shipping_address_per_customer'
            ),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}, {self.state}"
    
    def clean(self):
        """Validate address data."""
        super().clean()
        
        # Validate postal code format (basic validation)
        if self.postal_code and not self.postal_code.replace(' ', '').isalnum():
            raise ValidationError(_('Postal code must contain only letters and numbers.'))
    
    def save(self, *args, **kwargs):
        """Override save to handle default address logic."""
        # If this is set as default, unset other defaults for this customer
        if self.is_default:
            Address.objects.filter(
                customer=self.customer, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        if self.is_billing_default:
            Address.objects.filter(
                customer=self.customer, 
                is_billing_default=True
            ).exclude(pk=self.pk).update(is_billing_default=False)
        
        if self.is_shipping_default:
            Address.objects.filter(
                customer=self.customer, 
                is_shipping_default=True
            ).exclude(pk=self.pk).update(is_shipping_default=False)
        
        super().save(*args, **kwargs)
    
    def mark_as_used(self):
        """Mark address as used and increment usage count."""
        self.usage_count += 1
        self.last_used = models.timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def get_full_address(self):
        """Get formatted full address."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, address_parts))


class Wishlist(BaseModel):
    """
    Customer wishlist model.
    """
    customer = models.OneToOneField(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    name = models.CharField(_('Wishlist Name'), max_length=100, default='My Wishlist')
    is_public = models.BooleanField(_('Public Wishlist'), default=False)
    
    class Meta:
        verbose_name = _('Wishlist')
        verbose_name_plural = _('Wishlists')
    
    def __str__(self):
        return f"{self.customer.get_full_name()}'s {self.name}"
    
    @property
    def item_count(self):
        """Get total number of items in wishlist."""
        return self.items.count()


class WishlistItem(BaseModel):
    """
    Individual items in customer wishlist.
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    added_at = models.DateTimeField(_('Added At'), auto_now_add=True)
    notes = models.TextField(_('Notes'), blank=True, help_text=_('Personal notes about this item'))
    
    class Meta:
        verbose_name = _('Wishlist Item')
        verbose_name_plural = _('Wishlist Items')
        unique_together = ('wishlist', 'product')
        indexes = [
            models.Index(fields=['wishlist', 'added_at']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist.customer.get_full_name()}'s wishlist"


class CustomerActivity(BaseModel):
    """
    Track customer activities for analytics and personalization.
    """
    ACTIVITY_TYPES = [
        ('LOGIN', _('Login')),
        ('LOGOUT', _('Logout')),
        ('PRODUCT_VIEW', _('Product View')),
        ('CATEGORY_VIEW', _('Category View')),
        ('SEARCH', _('Search')),
        ('ADD_TO_CART', _('Add to Cart')),
        ('REMOVE_FROM_CART', _('Remove from Cart')),
        ('ADD_TO_WISHLIST', _('Add to Wishlist')),
        ('REMOVE_FROM_WISHLIST', _('Remove from Wishlist')),
        ('ORDER_PLACED', _('Order Placed')),
        ('ORDER_CANCELLED', _('Order Cancelled')),
        ('REVIEW_SUBMITTED', _('Review Submitted')),
        ('SUPPORT_TICKET', _('Support Ticket')),
    ]
    
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(_('Activity Type'), max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(_('Description'), blank=True)
    
    # Related Objects (optional)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_activities'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_activities'
    )
    
    # Activity Metadata
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    session_key = models.CharField(_('Session Key'), max_length=40, blank=True)
    
    # Additional Data
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Customer Activity')
        verbose_name_plural = _('Customer Activities')
        indexes = [
            models.Index(fields=['customer', 'activity_type']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.get_activity_type_display()}"