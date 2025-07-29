"""
Product serializers for API v2 with enhanced features and backward compatibility.
"""
from rest_framework import serializers
from django.db import transaction
from .models import Product, Category, ProductImage
from .serializers import (
    ProductImageSerializer as ProductImageSerializerV1,
    CategorySerializer as CategorySerializerV1,
    ProductListSerializer as ProductListSerializerV1,
    ProductDetailSerializer as ProductDetailSerializerV1,
    ProductCreateUpdateSerializer as ProductCreateUpdateSerializerV1
)


class ProductImageSerializerV2(ProductImageSerializerV1):
    """
    Enhanced product image serializer for v2 with additional metadata.
    """
    file_size = serializers.SerializerMethodField()
    dimensions = serializers.SerializerMethodField()
    
    class Meta(ProductImageSerializerV1.Meta):
        fields = ProductImageSerializerV1.Meta.fields + ['file_size', 'dimensions']
    
    def get_file_size(self, obj):
        """Get image file size in bytes."""
        try:
            return obj.image.size if obj.image else None
        except (ValueError, OSError):
            return None
    
    def get_dimensions(self, obj):
        """Get image dimensions."""
        try:
            if obj.image:
                return {
                    'width': obj.image.width,
                    'height': obj.image.height
                }
        except (ValueError, OSError, AttributeError):
            pass
        return None


class CategorySerializerV2(CategorySerializerV1):
    """
    Enhanced category serializer for v2 with additional features.
    """
    breadcrumb = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    
    class Meta(CategorySerializerV1.Meta):
        fields = CategorySerializerV1.Meta.fields + ['breadcrumb', 'level']
    
    def get_breadcrumb(self, obj):
        """Get category breadcrumb path."""
        breadcrumb = []
        current = obj
        while current:
            breadcrumb.insert(0, {
                'id': str(current.id),
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        return breadcrumb
    
    def get_level(self, obj):
        """Get category nesting level."""
        level = 0
        current = obj.parent
        while current:
            level += 1
            current = current.parent
        return level


class ProductListSerializerV2(ProductListSerializerV1):
    """
    Enhanced product list serializer for v2 with additional fields.
    """
    category = CategorySerializerV2(read_only=True)
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    
    class Meta(ProductListSerializerV1.Meta):
        fields = ProductListSerializerV1.Meta.fields + [
            'rating_average', 'rating_count', 'availability_status'
        ]
    
    def get_rating_average(self, obj):
        """Get average product rating."""
        # This would typically come from a related reviews model
        # For now, return a placeholder
        return None
    
    def get_rating_count(self, obj):
        """Get total number of ratings."""
        # This would typically come from a related reviews model
        # For now, return a placeholder
        return 0
    
    def get_availability_status(self, obj):
        """Get product availability status."""
        if hasattr(obj, 'inventory'):
            if obj.inventory.quantity > 0:
                return 'in_stock'
            elif obj.inventory.quantity == 0:
                return 'out_of_stock'
            else:
                return 'discontinued'
        return 'unknown'


class ProductDetailSerializerV2(ProductDetailSerializerV1):
    """
    Enhanced product detail serializer for v2 with comprehensive information.
    """
    category = CategorySerializerV2(read_only=True)
    images = ProductImageSerializerV2(many=True, read_only=True)
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    stock_quantity = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    
    class Meta(ProductDetailSerializerV1.Meta):
        fields = ProductDetailSerializerV1.Meta.fields + [
            'rating_average', 'rating_count', 'availability_status',
            'stock_quantity', 'related_products'
        ]
    
    def get_rating_average(self, obj):
        """Get average product rating."""
        # This would typically come from a related reviews model
        return None
    
    def get_rating_count(self, obj):
        """Get total number of ratings."""
        # This would typically come from a related reviews model
        return 0
    
    def get_availability_status(self, obj):
        """Get product availability status."""
        if hasattr(obj, 'inventory'):
            if obj.inventory.quantity > 0:
                return 'in_stock'
            elif obj.inventory.quantity == 0:
                return 'out_of_stock'
            else:
                return 'discontinued'
        return 'unknown'
    
    def get_stock_quantity(self, obj):
        """Get current stock quantity."""
        if hasattr(obj, 'inventory'):
            return obj.inventory.quantity
        return None
    
    def get_related_products(self, obj):
        """Get related products in the same category."""
        related = Product.objects.filter(
            category=obj.category,
            is_active=True,
            is_deleted=False
        ).exclude(id=obj.id)[:4]
        
        return ProductListSerializerV2(
            related, 
            many=True, 
            context=self.context
        ).data


class ProductCreateUpdateSerializerV2(ProductCreateUpdateSerializerV1):
    """
    Enhanced product create/update serializer for v2 with additional validation.
    """
    seo_keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="SEO keywords for the product"
    )
    
    class Meta(ProductCreateUpdateSerializerV1.Meta):
        fields = ProductCreateUpdateSerializerV1.Meta.fields + ['seo_keywords']
    
    def validate_seo_keywords(self, value):
        """Validate SEO keywords."""
        if value and len(value) > 10:
            raise serializers.ValidationError("Maximum 10 SEO keywords allowed.")
        return value
    
    def validate_price(self, value):
        """Enhanced price validation for v2."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        if value > 999999.99:
            raise serializers.ValidationError("Price cannot exceed 999,999.99.")
        return value
    
    def to_representation(self, instance):
        """Return v2 detailed representation after create/update."""
        return ProductDetailSerializerV2(instance, context=self.context).data


# Backward compatibility aliases
ProductImageSerializer = ProductImageSerializerV1
CategorySerializer = CategorySerializerV1
ProductListSerializer = ProductListSerializerV1
ProductDetailSerializer = ProductDetailSerializerV1
ProductCreateUpdateSerializer = ProductCreateUpdateSerializerV1