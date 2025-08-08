"""
Comprehensive Category Management Serializers for Admin Panel.
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .category_models import (
    CategoryTemplate, EnhancedCategory, CategoryAttribute, 
    CategoryPerformanceMetric, CategoryMerchandising, CategoryAuditLog,
    CategoryRelationship, CategoryImportExport, CategoryRecommendation
)
from .models import AdminUser


class CategoryTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for category templates.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CategoryTemplate
        fields = [
            'id', 'name', 'description', 'default_attributes', 'seo_template',
            'image_requirements', 'is_active', 'is_system_template', 'usage_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_count', 'created_by_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CategoryAttributeSerializer(serializers.ModelSerializer):
    """
    Serializer for category attributes.
    """
    class Meta:
        model = CategoryAttribute
        fields = [
            'id', 'category', 'name', 'slug', 'description', 'attribute_type',
            'is_required', 'is_filterable', 'is_searchable', 'is_comparable',
            'options', 'validation_rules', 'default_value', 'display_order',
            'display_name', 'help_text', 'unit', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']


class CategoryPerformanceMetricSerializer(serializers.ModelSerializer):
    """
    Serializer for category performance metrics.
    """
    class Meta:
        model = CategoryPerformanceMetric
        fields = [
            'id', 'category', 'date', 'page_views', 'unique_visitors', 'bounce_rate',
            'avg_time_on_page', 'total_orders', 'total_revenue', 'avg_order_value',
            'conversion_rate', 'products_viewed', 'products_added_to_cart',
            'products_purchased', 'search_queries', 'filter_usage', 'social_shares',
            'reviews_count', 'avg_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CategoryMerchandisingSerializer(serializers.ModelSerializer):
    """
    Serializer for category merchandising.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)
    click_through_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    conversion_rate_calc = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, source='conversion_rate')
    
    class Meta:
        model = CategoryMerchandising
        fields = [
            'id', 'category', 'name', 'merchandising_type', 'configuration',
            'display_rules', 'targeting_rules', 'start_date', 'end_date',
            'position', 'priority', 'is_active', 'impressions', 'clicks',
            'conversions', 'created_by', 'created_by_name', 'is_currently_active',
            'click_through_rate', 'conversion_rate_calc', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'impressions', 'clicks', 'conversions', 'created_by_name',
            'is_currently_active', 'click_through_rate', 'conversion_rate_calc',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CategoryAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for category audit logs.
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CategoryAuditLog
        fields = [
            'id', 'category', 'action', 'field_changes', 'previous_state',
            'additional_data', 'user', 'user_name', 'session_key', 'ip_address',
            'user_agent', 'reason', 'batch_id', 'created_at'
        ]
        read_only_fields = ['user_name', 'created_at']


class CategoryRelationshipSerializer(serializers.ModelSerializer):
    """
    Serializer for category relationships.
    """
    from_category_name = serializers.CharField(source='from_category.name', read_only=True)
    to_category_name = serializers.CharField(source='to_category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CategoryRelationship
        fields = [
            'id', 'from_category', 'from_category_name', 'to_category', 'to_category_name',
            'relationship_type', 'strength', 'is_bidirectional', 'weight', 'description',
            'metadata', 'is_active', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'from_category_name', 'to_category_name', 'created_by_name',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, data):
        """Validate that categories are not the same."""
        if data['from_category'] == data['to_category']:
            raise serializers.ValidationError("A category cannot have a relationship with itself.")
        return data


class CategoryImportExportSerializer(serializers.ModelSerializer):
    """
    Serializer for category import/export operations.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    duration = serializers.DurationField(read_only=True)
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = CategoryImportExport
        fields = [
            'id', 'operation_type', 'format', 'status', 'source_file', 'result_file',
            'error_file', 'import_config', 'field_mapping', 'validation_rules',
            'total_records', 'processed_records', 'successful_records', 'failed_records',
            'errors', 'warnings', 'started_at', 'completed_at', 'created_by',
            'created_by_name', 'duration', 'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'result_file', 'error_file', 'total_records', 'processed_records',
            'successful_records', 'failed_records', 'errors', 'warnings', 'started_at',
            'completed_at', 'created_by_name', 'duration', 'success_rate',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CategoryRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for category recommendations.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    implemented_by_name = serializers.CharField(source='implemented_by.username', read_only=True)
    
    class Meta:
        model = CategoryRecommendation
        fields = [
            'id', 'category', 'category_name', 'recommendation_type', 'title',
            'description', 'rationale', 'expected_impact', 'recommended_changes',
            'implementation_steps', 'priority', 'confidence_score', 'potential_impact_score',
            'status', 'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_notes',
            'implemented_by', 'implemented_by_name', 'implemented_at', 'implementation_notes',
            'model_version', 'training_data_date', 'algorithm_used', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'category_name', 'reviewed_by_name', 'implemented_by_name',
            'created_at', 'updated_at'
        ]


class EnhancedCategorySerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for enhanced categories.
    """
    # Computed fields
    full_path = serializers.CharField(read_only=True)
    breadcrumb = serializers.JSONField(read_only=True)
    
    # Related data
    children = serializers.SerializerMethodField()
    attributes = CategoryAttributeSerializer(many=True, read_only=True)
    performance_metrics = CategoryPerformanceMetricSerializer(many=True, read_only=True)
    merchandising = CategoryMerchandisingSerializer(many=True, read_only=True)
    
    # User information
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    last_modified_by_name = serializers.CharField(source='last_modified_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    # Template information
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = EnhancedCategory
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'parent',
            'level', 'lft', 'rght', 'tree_id', 'image', 'banner', 'icon', 'color_scheme',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
            'og_title', 'og_description', 'og_image', 'status', 'visibility',
            'is_featured', 'sort_order', 'published_at', 'scheduled_publish_at',
            'scheduled_unpublish_at', 'view_count', 'product_count', 'conversion_rate',
            'avg_order_value', 'language', 'translations', 'template', 'template_name',
            'custom_attributes', 'display_settings', 'access_roles', 'restricted_users',
            'created_by', 'created_by_name', 'last_modified_by', 'last_modified_by_name',
            'approved_by', 'approved_by_name', 'approved_at', 'external_id', 'sync_status',
            'last_synced_at', 'full_path', 'breadcrumb', 'children', 'attributes',
            'performance_metrics', 'merchandising', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'level', 'lft', 'rght', 'tree_id', 'view_count', 'product_count',
            'full_path', 'breadcrumb', 'children', 'attributes', 'performance_metrics',
            'merchandising', 'created_by_name', 'last_modified_by_name', 'approved_by_name',
            'template_name', 'created_at', 'updated_at'
        ]

    def get_children(self, obj):
        """Get immediate children categories."""
        children = obj.children.filter(status='active').order_by('sort_order', 'name')
        return EnhancedCategoryListSerializer(children, many=True, context=self.context).data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['last_modified_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['last_modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)

    def validate_parent(self, value):
        """Validate parent category to prevent circular references."""
        if value and self.instance:
            # Check if the new parent is a descendant of current category
            if self.instance.is_ancestor_of(value):
                raise serializers.ValidationError(
                    "Cannot set a descendant category as parent (circular reference)."
                )
        return value


class EnhancedCategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for category lists.
    """
    full_path = serializers.CharField(read_only=True)
    children_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = EnhancedCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'level', 'image',
            'status', 'visibility', 'is_featured', 'sort_order', 'product_count',
            'conversion_rate', 'language', 'created_by_name', 'full_path',
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'level', 'product_count', 'full_path', 'children_count',
            'created_by_name', 'created_at', 'updated_at'
        ]

    def get_children_count(self, obj):
        """Get count of immediate children."""
        return obj.children.filter(status='active').count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for category tree structure with drag-and-drop support.
    """
    children = serializers.SerializerMethodField()
    can_move = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = EnhancedCategory
        fields = [
            'id', 'name', 'slug', 'parent', 'level', 'sort_order', 'status',
            'is_featured', 'product_count', 'children', 'can_move', 'can_delete'
        ]

    def get_children(self, obj):
        """Get children for tree structure."""
        children = obj.children.filter(status__in=['active', 'draft']).order_by('sort_order', 'name')
        return CategoryTreeSerializer(children, many=True, context=self.context).data

    def get_can_move(self, obj):
        """Check if user can move this category."""
        user = self.context['request'].user
        # Add permission logic here
        return True  # Simplified for now

    def get_can_delete(self, obj):
        """Check if user can delete this category."""
        user = self.context['request'].user
        # Check if category has products or children
        has_products = obj.product_count > 0
        has_children = obj.children.exists()
        # Add permission logic here
        return not (has_products or has_children)


class CategoryBulkOperationSerializer(serializers.Serializer):
    """
    Serializer for bulk category operations.
    """
    OPERATION_CHOICES = [
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('delete', 'Delete'),
        ('move', 'Move'),
        ('update_status', 'Update Status'),
        ('update_visibility', 'Update Visibility'),
        ('assign_template', 'Assign Template'),
        ('export', 'Export'),
    ]
    
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000
    )
    operation = serializers.ChoiceField(choices=OPERATION_CHOICES)
    parameters = serializers.JSONField(default=dict, required=False)
    reason = serializers.CharField(max_length=500, required=False)

    def validate_category_ids(self, value):
        """Validate that all category IDs exist."""
        existing_ids = set(
            EnhancedCategory.objects.filter(id__in=value).values_list('id', flat=True)
        )
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"Categories not found: {list(missing_ids)}"
            )
        return value

    def validate(self, data):
        """Validate operation parameters."""
        operation = data['operation']
        parameters = data.get('parameters', {})
        
        if operation == 'move' and 'target_parent' not in parameters:
            raise serializers.ValidationError(
                "Move operation requires 'target_parent' in parameters."
            )
        
        if operation == 'update_status' and 'status' not in parameters:
            raise serializers.ValidationError(
                "Update status operation requires 'status' in parameters."
            )
        
        if operation == 'update_visibility' and 'visibility' not in parameters:
            raise serializers.ValidationError(
                "Update visibility operation requires 'visibility' in parameters."
            )
        
        if operation == 'assign_template' and 'template_id' not in parameters:
            raise serializers.ValidationError(
                "Assign template operation requires 'template_id' in parameters."
            )
        
        return data


class CategoryAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for category analytics dashboard.
    """
    category_id = serializers.UUIDField()
    category_name = serializers.CharField()
    
    # Performance metrics
    total_views = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    bounce_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Sales metrics
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Product metrics
    product_count = serializers.IntegerField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Trend data
    trend_data = serializers.JSONField()
    comparison_data = serializers.JSONField()


class CategorySearchSerializer(serializers.Serializer):
    """
    Serializer for advanced category search.
    """
    query = serializers.CharField(max_length=200, required=False)
    status = serializers.MultipleChoiceField(
        choices=EnhancedCategory.STATUS_CHOICES,
        required=False
    )
    visibility = serializers.MultipleChoiceField(
        choices=EnhancedCategory.VISIBILITY_CHOICES,
        required=False
    )
    parent = serializers.UUIDField(required=False, allow_null=True)
    level = serializers.IntegerField(min_value=0, required=False)
    is_featured = serializers.BooleanField(required=False)
    language = serializers.CharField(max_length=10, required=False)
    created_by = serializers.UUIDField(required=False)
    created_after = serializers.DateTimeField(required=False)
    created_before = serializers.DateTimeField(required=False)
    has_products = serializers.BooleanField(required=False)
    min_product_count = serializers.IntegerField(min_value=0, required=False)
    max_product_count = serializers.IntegerField(min_value=0, required=False)
    min_conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    max_conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Sorting
    ordering = serializers.CharField(max_length=50, required=False)
    
    # Pagination
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)

    def validate_ordering(self, value):
        """Validate ordering field."""
        allowed_fields = [
            'name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at',
            'sort_order', '-sort_order', 'level', '-level', 'product_count', '-product_count',
            'conversion_rate', '-conversion_rate'
        ]
        if value and value not in allowed_fields:
            raise serializers.ValidationError(f"Invalid ordering field. Allowed: {allowed_fields}")
        return value