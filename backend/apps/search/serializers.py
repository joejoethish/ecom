"""
Serializers for the search app.
"""
from rest_framework import serializers
from typing import Dict, List, Any


class SearchQuerySerializer(serializers.Serializer):
    """
    Serializer for search query parameters.
    """
    q = serializers.CharField(required=False, allow_blank=True, help_text="Search query string")
    category = serializers.CharField(required=False, allow_blank=True, help_text="Category slug or comma-separated list of category slugs")
    brand = serializers.CharField(required=False, allow_blank=True, help_text="Brand name or comma-separated list of brand names")
    min_price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, allow_null=True, help_text="Minimum price filter")
    max_price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, allow_null=True, help_text="Maximum price filter")
    tags = serializers.ListField(child=serializers.CharField(), required=False, help_text="List of tags to filter by")
    is_featured = serializers.BooleanField(required=False, allow_null=True, help_text="Filter for featured products")
    discount_only = serializers.BooleanField(required=False, default=False, help_text="Filter for products with discounts")
    min_rating = serializers.FloatField(required=False, min_value=0, max_value=5, allow_null=True, help_text="Minimum rating filter")
    sort_by = serializers.CharField(required=False, allow_blank=True, help_text="Field to sort by (e.g., price_asc, price_desc, created_at)")
    page = serializers.IntegerField(required=False, min_value=1, default=1, help_text="Page number")
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20, help_text="Number of results per page")
    highlight = serializers.BooleanField(required=False, default=True, help_text="Whether to highlight matching terms")
    
    def validate(self, data):
        """
        Validate and transform the search parameters.
        """
        # Process category parameter (convert comma-separated string to list)
        if 'category' in data and data['category']:
            if ',' in data['category']:
                data['category'] = [c.strip() for c in data['category'].split(',') if c.strip()]
        
        # Process brand parameter (convert comma-separated string to list)
        if 'brand' in data and data['brand']:
            if ',' in data['brand']:
                data['brand'] = [b.strip() for b in data['brand'].split(',') if b.strip()]
        
        # Create price_range from min_price and max_price
        if 'min_price' in data or 'max_price' in data:
            min_price = data.pop('min_price', None)
            max_price = data.pop('max_price', None)
            data['price_range'] = [min_price, max_price]
        
        # Validate sort_by parameter
        valid_sort_options = [
            'price_asc', 'price_desc', 'created_at', '-created_at', 
            'name', '-name', 'discount', 'relevance'
        ]
        if 'sort_by' in data and data['sort_by'] and data['sort_by'] not in valid_sort_options:
            raise serializers.ValidationError({"sort_by": f"Invalid sort option. Valid options are: {', '.join(valid_sort_options)}"})
        
        return data


class SuggestionQuerySerializer(serializers.Serializer):
    """
    Serializer for autocomplete suggestion query.
    """
    q = serializers.CharField(required=True, allow_blank=False, help_text="Partial query to get suggestions for")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5, help_text="Maximum number of suggestions to return")
    category = serializers.CharField(required=False, allow_blank=True, help_text="Optional category context for suggestions")
    brand = serializers.CharField(required=False, allow_blank=True, help_text="Optional brand context for suggestions")
    
    def validate(self, data):
        """
        Transform context parameters into a context dictionary.
        """
        context = {}
        
        if 'category' in data and data['category']:
            context['category'] = data.pop('category')
            
        if 'brand' in data and data['brand']:
            context['brand'] = data.pop('brand')
            
        if context:
            data['context'] = context
            
        return data


class ProductSuggestionSerializer(serializers.Serializer):
    """
    Serializer for product suggestions in autocomplete results.
    """
    id = serializers.CharField()
    name = serializers.CharField()
    slug = serializers.CharField()
    price = serializers.FloatField()
    image = serializers.CharField(allow_null=True, allow_blank=True)
    category = serializers.CharField(allow_null=True, allow_blank=True)


class SuggestionResponseSerializer(serializers.Serializer):
    """
    Serializer for autocomplete suggestion response.
    """
    suggestions = serializers.ListField(child=serializers.CharField())
    products = serializers.ListField(child=ProductSuggestionSerializer())
    query = serializers.CharField()
    error = serializers.CharField(required=False)


class FilterOptionItemSerializer(serializers.Serializer):
    """
    Serializer for individual filter option items.
    """
    name = serializers.CharField()
    count = serializers.IntegerField()


class PriceRangeOptionSerializer(serializers.Serializer):
    """
    Serializer for price range filter options.
    """
    from_price = serializers.FloatField(allow_null=True, source='from')
    to_price = serializers.FloatField(allow_null=True, source='to')
    count = serializers.IntegerField()
    label = serializers.CharField()


class DiscountRangeOptionSerializer(serializers.Serializer):
    """
    Serializer for discount range filter options.
    """
    from_discount = serializers.FloatField(allow_null=True, source='from')
    to_discount = serializers.FloatField(allow_null=True, source='to')
    count = serializers.IntegerField()
    label = serializers.CharField()


class FilterOptionsSerializer(serializers.Serializer):
    """
    Serializer for filter options response.
    """
    brands = serializers.ListField(child=FilterOptionItemSerializer(), required=False)
    categories = serializers.ListField(child=FilterOptionItemSerializer(), required=False)
    tags = serializers.ListField(child=FilterOptionItemSerializer(), required=False)
    price_ranges = serializers.ListField(child=PriceRangeOptionSerializer(), required=False)
    discount_ranges = serializers.ListField(child=DiscountRangeOptionSerializer(), required=False)


class HighlightSerializer(serializers.Serializer):
    """
    Serializer for search result highlights.
    """
    name = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.ListField(child=serializers.CharField(), required=False)
    short_description = serializers.ListField(child=serializers.CharField(), required=False)


class SearchResultSerializer(serializers.Serializer):
    """
    Serializer for individual search result items.
    """
    id = serializers.CharField()
    name = serializers.CharField()
    slug = serializers.CharField()
    price = serializers.FloatField()
    discount_price = serializers.FloatField(allow_null=True)
    effective_price = serializers.FloatField()
    discount_percentage = serializers.FloatField()
    brand = serializers.CharField(allow_null=True, allow_blank=True)
    category = serializers.DictField()
    primary_image_url = serializers.CharField(allow_null=True, allow_blank=True)
    is_featured = serializers.BooleanField()
    highlight = HighlightSerializer(required=False)


class SearchResponseSerializer(serializers.Serializer):
    """
    Serializer for search response.
    """
    count = serializers.IntegerField()
    results = serializers.ListField(child=SearchResultSerializer())
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    num_pages = serializers.IntegerField()
    facets = FilterOptionsSerializer()
    query = serializers.CharField(allow_null=True, allow_blank=True)
    filters = serializers.DictField(required=False)
    sort_by = serializers.CharField(allow_null=True, allow_blank=True)
    error = serializers.CharField(required=False)


class IndexRebuildRequestSerializer(serializers.Serializer):
    """
    Serializer for index rebuild request.
    """
    force = serializers.BooleanField(default=False, help_text="Force rebuild even if index exists")


class IndexRebuildResponseSerializer(serializers.Serializer):
    """
    Serializer for index rebuild response.
    """
    status = serializers.CharField()
    message = serializers.CharField()


class RelatedProductsRequestSerializer(serializers.Serializer):
    """
    Serializer for related products request.
    """
    product_id = serializers.CharField(required=True, help_text="ID of the product to find related items for")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6, help_text="Maximum number of related products to return")