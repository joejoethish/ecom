import django_filters
from django.db.models import Q
from .models import Documentation, DocumentationCategory, DocumentationTag


class DocumentationFilter(django_filters.FilterSet):
    """Filter for documentation"""
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=DocumentationCategory.objects.filter(is_active=True)
    )
    category_slug = django_filters.CharFilter(field_name='category__slug')
    
    # Tag filters
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=DocumentationTag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    
    # Status and visibility
    status = django_filters.ChoiceFilter(choices=Documentation.STATUS_CHOICES)
    visibility = django_filters.ChoiceFilter(choices=Documentation.VISIBILITY_CHOICES)
    
    # Author filters
    author = django_filters.CharFilter(field_name='author__username')
    author_id = django_filters.NumberFilter(field_name='author__id')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Popularity filters
    min_views = django_filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    min_likes = django_filters.NumberFilter(field_name='like_count', lookup_expr='gte')
    
    # Version filters
    version = django_filters.CharFilter()
    has_versions = django_filters.BooleanFilter(method='filter_has_versions')
    
    # Content filters
    has_template = django_filters.BooleanFilter(method='filter_has_template')
    has_translations = django_filters.BooleanFilter(method='filter_has_translations')
    
    class Meta:
        model = Documentation
        fields = [
            'search', 'category', 'category_slug', 'tags', 'status', 'visibility',
            'author', 'author_id', 'created_after', 'created_before',
            'updated_after', 'updated_before', 'published_after', 'published_before',
            'min_views', 'min_likes', 'version', 'has_versions',
            'has_template', 'has_translations'
        ]

    def filter_search(self, queryset, name, value):
        """Full-text search across title, content, and excerpt"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(excerpt__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()

    def filter_has_versions(self, queryset, name, value):
        """Filter by documents that have version history"""
        if value:
            return queryset.filter(version_history__isnull=False).distinct()
        return queryset.filter(version_history__isnull=True)

    def filter_has_template(self, queryset, name, value):
        """Filter by documents that use templates"""
        if value:
            return queryset.filter(template__isnull=False)
        return queryset.filter(template__isnull=True)

    def filter_has_translations(self, queryset, name, value):
        """Filter by documents that have translations"""
        if value:
            return queryset.filter(translations__isnull=False).distinct()
        return queryset.filter(translations__isnull=True)