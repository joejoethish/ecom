"""
Product serializers for the ecommerce platform.
"""
from rest_framework import serializers
from django.db import transaction
from .models import Product, Category, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'sort_order']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for product categories with nested children.
    """
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'parent', 
            'parent_name', 'full_name', 'is_active', 'sort_order', 
            'children', 'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_children(self, obj):
        """Get active child categories."""
        if obj.children.filter(is_active=True, is_deleted=False).exists():
            return CategorySerializer(
                obj.children.filter(is_active=True, is_deleted=False), 
                many=True,
                context=self.context
            ).data
        return []

    def get_products_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(is_active=True, is_deleted=False).count()


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for category lists (without nested children).
    """
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'parent', 
            'parent_name', 'full_name', 'is_active', 'sort_order', 
            'products_count', 'created_at', 'updated_at'
        ]

    def get_products_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(is_active=True, is_deleted=False).count()


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view with essential fields.
    """
    category = CategoryListSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category', 
            'brand', 'sku', 'price', 'discount_price', 'effective_price',
            'discount_percentage', 'is_featured', 'status', 'primary_image',
            'tags_list', 'created_at', 'updated_at'
        ]

    def get_primary_image(self, obj):
        """Get primary product image."""
        primary_image = obj.primary_image
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

    def get_tags_list(self, obj):
        """Get product tags as a list."""
        return obj.get_tags_list()


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for product detail view.
    """
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'brand', 'sku', 'price', 'discount_price', 
            'effective_price', 'discount_percentage', 'weight', 'dimensions',
            'is_active', 'is_featured', 'status', 'tags', 'tags_list',
            'meta_title', 'meta_description', 'images', 'primary_image',
            'created_at', 'updated_at'
        ]

    def get_primary_image(self, obj):
        """Get primary product image."""
        primary_image = obj.primary_image
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

    def get_tags_list(self, obj):
        """Get product tags as a list."""
        return obj.get_tags_list()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products.
    """
    category_id = serializers.UUIDField(write_only=True)
    images_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category_id',
            'brand', 'sku', 'price', 'discount_price', 'weight', 
            'dimensions', 'is_active', 'is_featured', 'status', 'tags',
            'meta_title', 'meta_description', 'images_data'
        ]

    def validate_category_id(self, value):
        """Validate that category exists and is active."""
        try:
            category = Category.objects.get(id=value, is_active=True, is_deleted=False)
            return category
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found or inactive.")

    def validate_sku(self, value):
        """Validate SKU uniqueness."""
        instance = getattr(self, 'instance', None)
        if Product.objects.filter(sku=value, is_deleted=False).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value

    def validate(self, attrs):
        """Validate discount price is less than regular price."""
        price = attrs.get('price')
        discount_price = attrs.get('discount_price')
        
        if discount_price and price and discount_price >= price:
            raise serializers.ValidationError({
                'discount_price': 'Discount price must be less than regular price.'
            })
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create product with images."""
        category = validated_data.pop('category_id')
        images_data = validated_data.pop('images_data', [])
        
        validated_data['category'] = category
        product = Product.objects.create(**validated_data)
        
        # Create product images
        for i, image_data in enumerate(images_data):
            ProductImage.objects.create(
                product=product,
                image=image_data.get('image'),
                alt_text=image_data.get('alt_text', ''),
                is_primary=image_data.get('is_primary', i == 0),
                sort_order=image_data.get('sort_order', i)
            )
        
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update product with images."""
        category = validated_data.pop('category_id', None)
        images_data = validated_data.pop('images_data', None)
        
        if category:
            validated_data['category'] = category
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update images if provided
        if images_data is not None:
            # Delete existing images
            instance.images.all().delete()
            
            # Create new images
            for i, image_data in enumerate(images_data):
                ProductImage.objects.create(
                    product=instance,
                    image=image_data.get('image'),
                    alt_text=image_data.get('alt_text', ''),
                    is_primary=image_data.get('is_primary', i == 0),
                    sort_order=image_data.get('sort_order', i)
                )
        
        return instance

    def to_representation(self, instance):
        """Return detailed representation after create/update."""
        return ProductDetailSerializer(instance, context=self.context).data