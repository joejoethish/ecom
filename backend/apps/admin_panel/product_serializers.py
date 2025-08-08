"""
Serializers for the comprehensive product management system.
"""
from rest_framework import serializers
from django.db import transaction
from django.utils.text import slugify
from apps.products.models import Product, Category, ProductImage
from apps.inventory.models import Inventory
from .product_models import (
    ProductVariant, ProductAttribute, ProductAttributeValue, ProductBundle,
    ProductBundleItem, ProductRelationship, ProductLifecycle, ProductVersion,
    ProductTemplate, ProductQuality, ProductWarranty, ProductDigitalAsset,
    ProductSyndication, ProductAnalytics
)


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for product attribute values."""
    
    class Meta:
        model = ProductAttributeValue
        fields = [
            'id', 'value', 'display_value', 'color_code', 'sort_order', 'is_active'
        ]


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for product attributes."""
    
    values = ProductAttributeValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductAttribute
        fields = [
            'id', 'name', 'display_name', 'attribute_type', 'is_required',
            'is_variant_attribute', 'sort_order', 'values'
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants."""
    
    available_quantity = serializers.ReadOnlyField()
    effective_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'sku', 'barcode', 'attributes', 'price',
            'cost_price', 'discount_price', 'weight', 'dimensions',
            'stock_quantity', 'reserved_quantity', 'reorder_level',
            'available_quantity', 'effective_price', 'is_active', 'is_default',
            'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Enhanced serializer for product images."""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'alt_text', 'is_primary', 'sort_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductBundleItemSerializer(serializers.ModelSerializer):
    """Serializer for product bundle items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = ProductBundleItem
        fields = [
            'id', 'product', 'product_name', 'variant', 'variant_name',
            'quantity', 'is_optional', 'sort_order'
        ]


class ProductBundleSerializer(serializers.ModelSerializer):
    """Serializer for product bundles."""
    
    items = ProductBundleItemSerializer(many=True, read_only=True)
    calculated_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductBundle
        fields = [
            'id', 'name', 'description', 'bundle_type', 'pricing_type',
            'fixed_price', 'discount_percentage', 'calculated_price',
            'is_active', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for product relationships."""
    
    target_product_name = serializers.CharField(source='target_product.name', read_only=True)
    target_product_price = serializers.DecimalField(
        source='target_product.price', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = ProductRelationship
        fields = [
            'id', 'source_product', 'target_product', 'target_product_name',
            'target_product_price', 'relationship_type', 'priority', 'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductLifecycleSerializer(serializers.ModelSerializer):
    """Serializer for product lifecycle."""
    
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = ProductLifecycle
        fields = [
            'id', 'product', 'current_stage', 'previous_stage', 'concept_date',
            'development_date', 'draft_date', 'review_date', 'active_date',
            'discontinued_date', 'archived_date', 'stage_notes',
            'automated_transitions', 'requires_approval', 'approved_by',
            'approved_by_username', 'approval_date', 'approval_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductVersionSerializer(serializers.ModelSerializer):
    """Serializer for product versions."""
    
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = ProductVersion
        fields = [
            'id', 'product', 'version_number', 'product_data', 'variant_data',
            'image_data', 'change_summary', 'change_details', 'changed_by',
            'changed_by_username', 'is_current', 'is_published', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductTemplateSerializer(serializers.ModelSerializer):
    """Serializer for product templates."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ProductTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'template_data', 'required_attributes', 'optional_attributes',
            'auto_generate_sku', 'sku_pattern', 'default_pricing_rules',
            'usage_count', 'is_active', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class ProductQualitySerializer(serializers.ModelSerializer):
    """Serializer for product quality."""
    
    class Meta:
        model = ProductQuality
        fields = [
            'id', 'product', 'quality_status', 'quality_score', 'defect_rate',
            'return_rate', 'last_quality_check', 'next_quality_check',
            'quality_check_frequency', 'certifications', 'compliance_status',
            'is_recalled', 'recall_date', 'recall_reason', 'recall_severity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductWarrantySerializer(serializers.ModelSerializer):
    """Serializer for product warranty."""
    
    class Meta:
        model = ProductWarranty
        fields = [
            'id', 'product', 'warranty_period_months', 'warranty_type',
            'coverage_details', 'exclusions', 'service_provider',
            'service_contact', 'terms_and_conditions', 'warranty_document',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductDigitalAssetSerializer(serializers.ModelSerializer):
    """Serializer for product digital assets."""
    
    class Meta:
        model = ProductDigitalAsset
        fields = [
            'id', 'product', 'name', 'description', 'asset_type', 'file',
            'file_size', 'mime_type', 'metadata', 'tags', 'is_public',
            'requires_authentication', 'sort_order', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'mime_type', 'created_at', 'updated_at']


class ProductSyndicationSerializer(serializers.ModelSerializer):
    """Serializer for product syndication."""
    
    class Meta:
        model = ProductSyndication
        fields = [
            'id', 'product', 'channel_name', 'channel_type', 'channel_url',
            'sync_enabled', 'sync_frequency', 'field_mapping',
            'transformation_rules', 'sync_status', 'last_sync_date',
            'next_sync_date', 'sync_error_message', 'external_id',
            'external_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sync_status', 'last_sync_date', 'created_at', 'updated_at']


class ProductAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for product analytics."""
    
    class Meta:
        model = ProductAnalytics
        fields = [
            'id', 'product', 'total_sales', 'total_revenue', 'total_profit',
            'view_count', 'conversion_rate', 'bounce_rate', 'sales_last_30_days',
            'revenue_last_30_days', 'views_last_30_days', 'popularity_score',
            'category_rank', 'overall_rank', 'demand_forecast', 'seasonal_trends',
            'last_calculated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_calculated', 'created_at', 'updated_at']


class ComprehensiveProductSerializer(serializers.ModelSerializer):
    """Comprehensive product serializer with all related data."""
    
    # Basic product fields
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    # Related data
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    relationships_from = ProductRelationshipSerializer(many=True, read_only=True)
    lifecycle = ProductLifecycleSerializer(read_only=True)
    quality = ProductQualitySerializer(read_only=True)
    warranty = ProductWarrantySerializer(read_only=True)
    analytics = ProductAnalyticsSerializer(read_only=True)
    digital_assets = ProductDigitalAssetSerializer(many=True, read_only=True)
    syndications = ProductSyndicationSerializer(many=True, read_only=True)
    
    # Inventory information
    inventory_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'category',
            'category_name', 'brand', 'sku', 'price', 'discount_price',
            'effective_price', 'discount_percentage', 'weight', 'dimensions',
            'is_active', 'is_featured', 'meta_title', 'meta_description',
            'tags', 'status', 'primary_image', 'average_rating', 'total_reviews',
            'images', 'variants', 'relationships_from', 'lifecycle', 'quality',
            'warranty', 'analytics', 'digital_assets', 'syndications',
            'inventory_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_primary_image(self, obj):
        """Get the primary product image."""
        primary_image = obj.primary_image
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None
    
    def get_inventory_info(self, obj):
        """Get inventory information for the product."""
        try:
            inventory = obj.inventory
            return {
                'quantity': inventory.quantity,
                'reserved_quantity': inventory.reserved_quantity,
                'available_quantity': inventory.available_quantity,
                'stock_status': inventory.stock_status,
                'needs_reordering': inventory.needs_reordering,
                'reorder_point': inventory.reorder_point,
                'warehouse': inventory.warehouse.name if inventory.warehouse else None
            }
        except Inventory.DoesNotExist:
            return None


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products with comprehensive data."""
    
    # Image upload handling
    image_files = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    # Variant data
    variants_data = ProductVariantSerializer(many=True, write_only=True, required=False)
    
    # Relationship data
    relationships_data = ProductRelationshipSerializer(many=True, write_only=True, required=False)
    
    # Digital assets
    digital_assets_data = ProductDigitalAssetSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category', 'brand',
            'sku', 'price', 'discount_price', 'weight', 'dimensions',
            'is_active', 'is_featured', 'meta_title', 'meta_description',
            'tags', 'status', 'image_files', 'variants_data',
            'relationships_data', 'digital_assets_data'
        ]
    
    def validate_sku(self, value):
        """Validate SKU uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if Product.objects.exclude(pk=self.instance.pk).filter(sku=value).exists():
                raise serializers.ValidationError("Product with this SKU already exists.")
        else:
            # Create case
            if Product.objects.filter(sku=value).exists():
                raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate(self, data):
        """Validate product data."""
        # Validate pricing
        if data.get('discount_price') and data.get('price'):
            if data['discount_price'] >= data['price']:
                raise serializers.ValidationError(
                    "Discount price must be less than regular price."
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Create product with related data."""
        # Extract related data
        image_files = validated_data.pop('image_files', [])
        variants_data = validated_data.pop('variants_data', [])
        relationships_data = validated_data.pop('relationships_data', [])
        digital_assets_data = validated_data.pop('digital_assets_data', [])
        
        # Generate slug if not provided
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])
        
        # Create product
        product = Product.objects.create(**validated_data)
        
        # Create images
        for i, image_file in enumerate(image_files):
            ProductImage.objects.create(
                product=product,
                image=image_file,
                is_primary=(i == 0),
                sort_order=i
            )
        
        # Create variants
        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
        
        # Create relationships
        for relationship_data in relationships_data:
            ProductRelationship.objects.create(
                source_product=product,
                **relationship_data
            )
        
        # Create digital assets
        for asset_data in digital_assets_data:
            ProductDigitalAsset.objects.create(product=product, **asset_data)
        
        # Create lifecycle
        ProductLifecycle.objects.create(
            product=product,
            current_stage='draft',
            draft_date=timezone.now()
        )
        
        # Create analytics
        ProductAnalytics.objects.create(product=product)
        
        return product
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update product with related data."""
        # Extract related data
        image_files = validated_data.pop('image_files', [])
        variants_data = validated_data.pop('variants_data', [])
        relationships_data = validated_data.pop('relationships_data', [])
        digital_assets_data = validated_data.pop('digital_assets_data', [])
        
        # Update product
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle image updates if provided
        if image_files:
            # Remove existing images
            instance.images.all().delete()
            # Create new images
            for i, image_file in enumerate(image_files):
                ProductImage.objects.create(
                    product=instance,
                    image=image_file,
                    is_primary=(i == 0),
                    sort_order=i
                )
        
        # Handle variant updates if provided
        if variants_data:
            # Remove existing variants
            instance.variants.all().delete()
            # Create new variants
            for variant_data in variants_data:
                ProductVariant.objects.create(product=instance, **variant_data)
        
        # Handle relationship updates if provided
        if relationships_data:
            # Remove existing relationships
            instance.relationships_from.all().delete()
            # Create new relationships
            for relationship_data in relationships_data:
                ProductRelationship.objects.create(
                    source_product=instance,
                    **relationship_data
                )
        
        return instance


class BulkProductOperationSerializer(serializers.Serializer):
    """Serializer for bulk product operations."""
    
    product_ids = serializers.ListField(child=serializers.IntegerField())
    operation = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('feature', 'Feature'),
        ('unfeature', 'Unfeature'),
        ('delete', 'Delete'),
        ('update_category', 'Update Category'),
        ('update_status', 'Update Status'),
        ('export', 'Export'),
    ])
    parameters = serializers.JSONField(required=False, default=dict)


class ProductImportSerializer(serializers.Serializer):
    """Serializer for product import operations."""
    
    file = serializers.FileField()
    file_format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    import_options = serializers.JSONField(required=False, default=dict)
    update_existing = serializers.BooleanField(default=False)
    create_categories = serializers.BooleanField(default=False)


class ProductExportSerializer(serializers.Serializer):
    """Serializer for product export operations."""
    
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    export_format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    include_images = serializers.BooleanField(default=False)
    include_variants = serializers.BooleanField(default=False)
    include_relationships = serializers.BooleanField(default=False)
    filters = serializers.JSONField(required=False, default=dict)


class ProductComparisonSerializer(serializers.Serializer):
    """Serializer for product comparison."""
    
    product_ids = serializers.ListField(child=serializers.IntegerField())
    comparison_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['name', 'price', 'category', 'brand', 'rating']
    )


class ProductDuplicateDetectionSerializer(serializers.Serializer):
    """Serializer for duplicate product detection."""
    
    detection_criteria = serializers.JSONField(default={
        'name_similarity': 0.8,
        'sku_match': True,
        'brand_match': True,
        'category_match': False
    })
    auto_merge = serializers.BooleanField(default=False)
    merge_strategy = serializers.ChoiceField(
        choices=[
            ('keep_first', 'Keep First'),
            ('keep_latest', 'Keep Latest'),
            ('manual', 'Manual Review'),
        ],
        default='manual'
    )