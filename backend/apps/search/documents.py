"""
Elasticsearch document definitions for the search app.
"""
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from apps.products.models import Product, Category, ProductImage
from django.conf import settings
import json


@registry.register_document
class ProductDocument(Document):
    """
    Elasticsearch document for Product model.
    """
    # Category fields with nested structure for hierarchical categories
    category = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(
            analyzer='standard',
            fields={
                'raw': fields.KeywordField(),
                'suggest': fields.CompletionField(),
                'ngram': fields.TextField(analyzer='ngram_analyzer'),
            }
        ),
        'slug': fields.KeywordField(),
        'parent_id': fields.KeywordField(),
        'full_name': fields.TextField(),
    })
    
    # Nested fields for product images
    images = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'image': fields.TextField(),
        'alt_text': fields.TextField(),
        'is_primary': fields.BooleanField(),
        'sort_order': fields.IntegerField(),
    })
    
    # Enhanced text fields with multiple analyzers for better search
    name = fields.TextField(
        analyzer='standard',
        fields={
            'raw': fields.KeywordField(),
            'ngram': fields.TextField(analyzer='ngram_analyzer'),
            'edge_ngram': fields.TextField(analyzer='edge_ngram_analyzer'),
        }
    )
    
    description = fields.TextField(
        analyzer='standard',
        fields={
            'ngram': fields.TextField(analyzer='ngram_analyzer'),
        }
    )
    
    short_description = fields.TextField(
        analyzer='standard',
        fields={
            'ngram': fields.TextField(analyzer='ngram_analyzer'),
        }
    )
    
    # Brand field with multiple analyzers
    brand = fields.TextField(
        analyzer='standard',
        fields={
            'raw': fields.KeywordField(),
            'ngram': fields.TextField(analyzer='ngram_analyzer'),
            'suggest': fields.CompletionField(),
        }
    )
    
    # Price fields with range support
    price = fields.FloatField()
    discount_price = fields.FloatField(null_value=0.0)
    effective_price = fields.FloatField()  # Calculated field for sorting and filtering
    discount_percentage = fields.FloatField()  # Calculated field
    
    # Additional fields with specific analyzers
    name_suggest = fields.CompletionField()
    search_keywords = fields.TextField(analyzer='ngram_analyzer')  # Combined field for full-text search
    tags = fields.ListField(fields.KeywordField())
    
    # Dimensions as individual fields for filtering
    dimensions_length = fields.FloatField(null_value=0.0)
    dimensions_width = fields.FloatField(null_value=0.0)
    dimensions_height = fields.FloatField(null_value=0.0)
    
    # Primary image URL for display in search results
    primary_image_url = fields.TextField()
    
    class Index:
        name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_products"
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS
    
    class Django:
        model = Product
        # Only index active products
        queryset_pagination = settings.ELASTICSEARCH_BULK_SIZE
        
        def get_queryset(self):
            """
            Return the queryset that should be indexed by elasticsearch.
            """
            return Product.objects.filter(
                is_active=True, 
                status='active'
            ).select_related(
                'category'
            ).prefetch_related(
                'images'
            )
        
        # Fields to include in the document
        fields = [
            'id',
            'slug',
            'sku',
            'weight',
            'is_featured',
            'status',
            'created_at',
            'updated_at',
            'meta_title',
            'meta_description',
        ]
    
    def prepare_category(self, instance):
        """
        Prepare the category data for indexing.
        """
        if instance.category:
            parent_id = str(instance.category.parent.id) if instance.category.parent else None
            return {
                'id': str(instance.category.id),
                'name': instance.category.name,
                'slug': instance.category.slug,
                'parent_id': parent_id,
                'full_name': instance.category.full_name,
            }
        return {}
    
    def prepare_images(self, instance):
        """
        Prepare the images data for indexing.
        """
        images = []
        for image in instance.images.all():
            images.append({
                'id': str(image.id),
                'image': image.image.url if image.image else '',
                'alt_text': image.alt_text,
                'is_primary': image.is_primary,
                'sort_order': image.sort_order,
            })
        return images
    
    def prepare_name_suggest(self, instance):
        """
        Prepare the name suggest field for autocomplete.
        """
        suggestions = [instance.name]
        
        # Add brand to suggestions if available
        if instance.brand:
            suggestions.append(instance.brand)
        
        # Add category name to suggestions
        if instance.category:
            suggestions.append(instance.category.name)
            
        # Add SKU to suggestions
        suggestions.append(instance.sku)
        
        # Add tags to suggestions
        suggestions.extend(instance.get_tags_list())
        
        return suggestions
    
    def prepare_tags(self, instance):
        """
        Prepare the tags field.
        """
        return instance.get_tags_list()
    
    def prepare_search_keywords(self, instance):
        """
        Prepare a combined field for full-text search.
        """
        keywords = [
            instance.name,
            instance.short_description,
            instance.brand,
            instance.sku,
        ]
        
        if instance.category:
            keywords.append(instance.category.name)
            
        keywords.extend(instance.get_tags_list())
        
        return ' '.join(filter(None, keywords))
    
    def prepare_effective_price(self, instance):
        """
        Prepare the effective price field.
        """
        return float(instance.effective_price)
    
    def prepare_discount_percentage(self, instance):
        """
        Prepare the discount percentage field.
        """
        return float(instance.discount_percentage)
    
    def prepare_dimensions_length(self, instance):
        """
        Extract length from dimensions JSON.
        """
        try:
            if isinstance(instance.dimensions, str):
                dimensions = json.loads(instance.dimensions)
            else:
                dimensions = instance.dimensions
            return float(dimensions.get('length', 0))
        except (ValueError, AttributeError, TypeError):
            return 0.0
    
    def prepare_dimensions_width(self, instance):
        """
        Extract width from dimensions JSON.
        """
        try:
            if isinstance(instance.dimensions, str):
                dimensions = json.loads(instance.dimensions)
            else:
                dimensions = instance.dimensions
            return float(dimensions.get('width', 0))
        except (ValueError, AttributeError, TypeError):
            return 0.0
    
    def prepare_dimensions_height(self, instance):
        """
        Extract height from dimensions JSON.
        """
        try:
            if isinstance(instance.dimensions, str):
                dimensions = json.loads(instance.dimensions)
            else:
                dimensions = instance.dimensions
            return float(dimensions.get('height', 0))
        except (ValueError, AttributeError, TypeError):
            return 0.0
    
    def prepare_primary_image_url(self, instance):
        """
        Get the primary image URL for display in search results.
        """
        primary_image = instance.primary_image
        if primary_image and primary_image.image:
            return primary_image.image.url
        return ""