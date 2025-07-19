"""
Customer serializers for API endpoints.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from typing import Dict, Any

from .models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from .services import CustomerService, AddressService, WishlistService
from apps.products.serializers import ProductSerializer

User = get_user_model()


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    customer_tier = serializers.CharField(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'full_name', 'email', 'username', 'first_name', 'last_name',
            'date_of_birth', 'gender', 'avatar', 'phone_number', 'alternate_phone',
            'account_status', 'is_verified', 'verification_date',
            'newsletter_subscription', 'sms_notifications', 'email_notifications', 'push_notifications',
            'total_orders', 'total_spent', 'loyalty_points', 'customer_tier',
            'last_login_date', 'last_order_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'full_name', 'email', 'username', 'account_status', 'is_verified', 
            'verification_date', 'total_orders', 'total_spent', 'loyalty_points', 
            'customer_tier', 'last_login_date', 'last_order_date', 'created_at', 'updated_at'
        ]
    
    def update(self, instance, validated_data):
        """Update customer profile using service layer."""
        # Handle user fields separately
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Update user fields if provided
        if user_data:
            user = instance.user
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save()
        
        # Update profile using service
        return CustomerService.update_customer_profile(instance, **validated_data)


class CustomerProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating customer profiles.
    """
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = CustomerProfile
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'avatar',
            'phone_number', 'alternate_phone', 'newsletter_subscription',
            'sms_notifications', 'email_notifications', 'push_notifications'
        ]
    
    def create(self, validated_data):
        """Create customer profile using service layer."""
        user_data = validated_data.pop('user', {})
        user = self.context['request'].user
        
        # Update user fields if provided
        if user_data:
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save()
        
        return CustomerService.create_customer_profile(user, **validated_data)


class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for customer addresses.
    """
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'type', 'first_name', 'last_name', 'company',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'phone', 'is_default', 'is_billing_default', 'is_shipping_default',
            'delivery_instructions', 'latitude', 'longitude', 'usage_count', 'last_used',
            'full_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used', 'full_address', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create address using service layer."""
        customer_profile = self.context['customer_profile']
        return AddressService.create_address(customer_profile, validated_data)
    
    def update(self, instance, validated_data):
        """Update address using service layer."""
        return AddressService.update_address(instance, validated_data)


class AddressCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating addresses with validation.
    """
    class Meta:
        model = Address
        fields = [
            'type', 'first_name', 'last_name', 'company',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'phone', 'is_default', 'is_billing_default', 'is_shipping_default',
            'delivery_instructions', 'latitude', 'longitude'
        ]
    
    def validate_postal_code(self, value):
        """Validate postal code format."""
        if value and not value.replace(' ', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Postal code must contain only letters, numbers, spaces, and hyphens.")
        return value
    
    def validate(self, data):
        """Validate address data."""
        # Ensure at least one default is set if this is the first address
        customer_profile = self.context.get('customer_profile')
        if customer_profile and not customer_profile.addresses.exists():
            data['is_default'] = True
            data['is_billing_default'] = True
            data['is_shipping_default'] = True
        
        return data


class WishlistItemSerializer(serializers.ModelSerializer):
    """
    Serializer for wishlist items.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'notes', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def create(self, validated_data):
        """Create wishlist item using service layer."""
        customer_profile = self.context['customer_profile']
        product_id = validated_data.pop('product_id')
        
        try:
            from apps.products.models import Product
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'Product not found.'})
        
        return WishlistService.add_to_wishlist(
            customer_profile, 
            product, 
            validated_data.get('notes', '')
        )


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for customer wishlist.
    """
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'name', 'is_public', 'items', 'item_count', 'customer_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer_name', 'created_at', 'updated_at']


class CustomerActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for customer activities.
    """
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = CustomerActivity
        fields = [
            'id', 'activity_type', 'activity_type_display', 'description',
            'product_name', 'order_number', 'ip_address', 'user_agent',
            'session_key', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CustomerAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for customer analytics data.
    """
    total_activities = serializers.IntegerField()
    login_count = serializers.IntegerField()
    product_views = serializers.IntegerField()
    cart_additions = serializers.IntegerField()
    wishlist_additions = serializers.IntegerField()
    orders_placed = serializers.IntegerField()
    reviews_submitted = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
    customer_tier = serializers.CharField()
    total_spent = serializers.FloatField()
    loyalty_points = serializers.IntegerField()
    account_age_days = serializers.IntegerField()


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Serializer for customer list view (admin).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    customer_tier = serializers.CharField(read_only=True)
    address_count = serializers.SerializerMethodField()
    wishlist_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'account_status',
            'is_verified', 'total_orders', 'total_spent', 'loyalty_points',
            'customer_tier', 'last_login_date', 'last_order_date',
            'address_count', 'wishlist_count', 'created_at'
        ]
    
    def get_address_count(self, obj):
        """Get number of addresses for customer."""
        return obj.addresses.count()
    
    def get_wishlist_count(self, obj):
        """Get number of items in customer's wishlist."""
        try:
            return obj.wishlist.item_count
        except:
            return 0


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for customer information (admin view).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    customer_tier = serializers.CharField(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    wishlist = WishlistSerializer(read_only=True)
    recent_activities = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'full_name', 'email', 'username', 'date_of_birth', 'gender',
            'avatar', 'phone_number', 'alternate_phone', 'account_status',
            'is_verified', 'verification_date', 'newsletter_subscription',
            'sms_notifications', 'email_notifications', 'push_notifications',
            'total_orders', 'total_spent', 'loyalty_points', 'customer_tier',
            'last_login_date', 'last_order_date', 'notes',
            'addresses', 'wishlist', 'recent_activities',
            'created_at', 'updated_at'
        ]
    
    def get_recent_activities(self, obj):
        """Get recent customer activities."""
        recent_activities = obj.activities.all()[:10]
        return CustomerActivitySerializer(recent_activities, many=True).data


class CustomerSearchSerializer(serializers.Serializer):
    """
    Serializer for customer search parameters.
    """
    search = serializers.CharField(required=False, help_text="Search by name, email, or phone")
    account_status = serializers.ChoiceField(
        choices=CustomerProfile.ACCOUNT_STATUS_CHOICES,
        required=False,
        help_text="Filter by account status"
    )
    is_verified = serializers.BooleanField(required=False, help_text="Filter by verification status")
    customer_tier = serializers.ChoiceField(
        choices=[('BRONZE', 'Bronze'), ('SILVER', 'Silver'), ('GOLD', 'Gold'), ('PLATINUM', 'Platinum')],
        required=False,
        help_text="Filter by customer tier"
    )
    min_orders = serializers.IntegerField(required=False, help_text="Minimum number of orders")
    max_orders = serializers.IntegerField(required=False, help_text="Maximum number of orders")
    min_spent = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, help_text="Minimum amount spent")
    max_spent = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, help_text="Maximum amount spent")
    date_joined_from = serializers.DateField(required=False, help_text="Joined from date")
    date_joined_to = serializers.DateField(required=False, help_text="Joined to date")
    last_login_from = serializers.DateField(required=False, help_text="Last login from date")
    last_login_to = serializers.DateField(required=False, help_text="Last login to date")