"""
Cart serializers for the ecommerce platform.
"""
from rest_framework import serializers
from .models import Cart, CartItem, SavedItem
from apps.products.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items.
    """
    product = ProductSerializer(read_only=True)
    line_total = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 
            'product', 
            'quantity', 
            'is_gift', 
            'gift_message', 
            'added_at', 
            'line_total'
        ]


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    coupon_code = serializers.CharField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 
            'items', 
            'total_items_count', 
            'subtotal', 
            'coupon_code',
            'created_at', 
            'updated_at',
            'last_activity'
        ]


class SavedItemSerializer(serializers.ModelSerializer):
    """
    Serializer for saved items.
    """
    product = ProductSerializer(read_only=True)

    class Meta:
        model = SavedItem
        fields = [
            'id', 
            'product', 
            'quantity', 
            'saved_at'
        ]