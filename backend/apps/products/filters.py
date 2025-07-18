"""
Custom filters for product API endpoints.
"""
import django_filters
from django.db.models import Q
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """
    Custom filter set for Product model with advanced filtering capabilities.
    """
    # Price range filtering
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Effective price range (considering discount)
    min_effective_price = django_filters.NumberFilter(method='filter_min_effective_price')
    max_effective_price = django_filters.NumberFilter(method='filter_max_effective_price')
    
    # Category filtering
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True, is_deleted=False)
    )
    category_slug = django_filters.CharFilter(field_name='category__slug')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    
    # Include products from child categories
    category_tree = django_filters.CharFilter(method='filter_category_tree')
    
    # Brand filtering
    brand = django_filters.CharFilter(lookup_expr='iexact')
    brand_in = django_filters.CharFilter(method='filter_brand_in')
    
    # Status filtering
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    status_in = django_filters.CharFilter(method='filter_status_in')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Tags filtering
    tags = django_filters.CharFilter(method='filter_tags')
    
    # SKU filtering
    sku = django_filters.CharFilter(lookup_expr='iexact')
    sku_contains = django_filters.CharFilter(field_name='sku', lookup_expr='icontains')
    
    # Weight filtering
    min_weight = django_filters.NumberFilter(field_name='weight', lookup_expr='gte')
    max_weight = django_filters.NumberFilter(field_name='weight', lookup_expr='lte')
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'description': ['icontains'],
            'short_description': ['icontains'],
        }

    def filter_min_effective_price(self, queryset, name, value):
        """Filter by minimum effective price (considering discount)."""
        return queryset.extra(
            where=[
                "CASE WHEN discount_price IS NOT NULL THEN discount_price ELSE price END >= %s"
            ],
            params=[value]
        )

    def filter_max_effective_price(self, queryset, name, value):
        """Filter by maximum effective price (considering discount)."""
        return queryset.extra(
            where=[
                "CASE WHEN discount_price IS NOT NULL THEN discount_price ELSE price END <= %s"
            ],
            params=[value]
        )

    def filter_category_tree(self, queryset, name, value):
        """Filter products by category and all its descendants."""
        try:
            category = Category.objects.get(
                Q(slug=value) | Q(name__iexact=value),
                is_active=True,
                is_deleted=False
            )
            # Get all descendant categories
            descendant_categories = category.get_descendants()
            category_ids = [category.id] + [cat.id for cat in descendant_categories]
            return queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()

    def filter_has_discount(self, queryset, name, value):
        """Filter products that have discount price set."""
        if value:
            return queryset.filter(discount_price__isnull=False)
        else:
            return queryset.filter(discount_price__isnull=True)

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        if not value:
            return queryset
        
        search_terms = value.split()
        query = Q()
        
        for term in search_terms:
            term_query = (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(short_description__icontains=term) |
                Q(brand__icontains=term) |
                Q(sku__icontains=term) |
                Q(tags__icontains=term) |
                Q(category__name__icontains=term)
            )
            query &= term_query
        
        return queryset.filter(query).distinct()

    def filter_tags(self, queryset, name, value):
        """Filter products by tags (comma-separated)."""
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        query = Q()
        
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)

    def filter_brand_in(self, queryset, name, value):
        """Filter products by multiple brands (comma-separated)."""
        if not value:
            return queryset
        
        brands = [brand.strip() for brand in value.split(',') if brand.strip()]
        return queryset.filter(brand__in=brands)

    def filter_status_in(self, queryset, name, value):
        """Filter products by multiple statuses (comma-separated)."""
        if not value:
            return queryset
        
        statuses = [status.strip() for status in value.split(',') if status.strip()]
        return queryset.filter(status__in=statuses)




class CategoryFilter(django_filters.FilterSet):
    """
    Custom filter set for Category model.
    """
    # Parent category filtering
    parent = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True, is_deleted=False)
    )
    parent_slug = django_filters.CharFilter(field_name='parent__slug')
    parent_name = django_filters.CharFilter(field_name='parent__name', lookup_expr='icontains')
    
    # Root categories (no parent)
    is_root = django_filters.BooleanFilter(method='filter_is_root')
    
    # Categories with children
    has_children = django_filters.BooleanFilter(method='filter_has_children')
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter()
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Category
        fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'description': ['icontains'],
            'slug': ['exact', 'icontains'],
        }

    def filter_is_root(self, queryset, name, value):
        """Filter root categories (categories without parent)."""
        if value:
            return queryset.filter(parent__isnull=True)
        else:
            return queryset.filter(parent__isnull=False)

    def filter_has_children(self, queryset, name, value):
        """Filter categories that have child categories."""
        if value:
            return queryset.filter(children__isnull=False).distinct()
        else:
            return queryset.filter(children__isnull=True)

    def filter_search(self, queryset, name, value):
        """Search across category name and description."""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()