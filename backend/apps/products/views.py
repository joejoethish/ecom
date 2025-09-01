"""
Product views for the ecommerce platform.
"""
from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from core.permissions import IsAdminOrReadOnly
from core.pagination import StandardResultsSetPagination
from .models import Product, Category
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    CategorySerializer, CategoryListSerializer
)
from .filters import ProductFilter, CategoryFilter


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product categories with full CRUD operations.
    """
    queryset = Category.objects.filter(is_deleted=False)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at', 'updated_at']
    ordering = ['sort_order', 'name']
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see active categories
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    @action(detail=False, methods=['get'])
    def root_categories(self, request):
        """Get root categories (categories without parent)."""
        queryset = self.get_queryset().filter(parent__isnull=True)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, slug=None):
        """Get child categories of a specific category."""
        category = self.get_object()
        queryset = category.children.filter(is_deleted=False)
        
        # Non-admin users can only see active categories
        if not (request.user.is_authenticated and request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products in a specific category."""
        category = self.get_object()
        
        # Get products from this category and all descendant categories
        descendant_categories = category.get_descendants()
        category_ids = [category.id] + [cat.id for cat in descendant_categories]
        
        queryset = Product.objects.filter(
            category_id__in=category_ids,
            is_deleted=False
        )
        
        # Non-admin users can only see active products
        if not (request.user.is_authenticated and request.user.is_staff):
            queryset = queryset.filter(is_active=True, status='active')
        
        # Apply product filters
        product_filter = ProductFilter(request.GET, queryset=queryset)
        queryset = product_filter.qs
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for products with full CRUD operations, filtering, and search.
    """
    queryset = Product.objects.filter(is_deleted=False)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'brand', 'sku', 'tags']
    ordering_fields = [
        'name', 'price', 'discount_price', 'created_at', 'updated_at', 
        'brand', 'weight', 'is_featured'
    ]
    ordering = ['-created_at']
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter queryset based on user permissions and add annotations."""
        queryset = super().get_queryset()
        
        # Non-admin users can only see active products
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True, status='active')
        
        # Add annotations for better performance
        queryset = queryset.select_related('category').prefetch_related('images')
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        else:
            return ProductDetailSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products."""
        queryset = self.get_queryset().filter(is_featured=True)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Get products on sale (with discount price)."""
        queryset = self.get_queryset().filter(discount_price__isnull=False)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def brands(self, request):
        """Get list of all brands with product counts."""
        queryset = self.get_queryset()
        
        # Get brands with product counts
        brands = queryset.values('brand').annotate(
            product_count=Count('id')
        ).filter(
            brand__isnull=False,
            brand__gt=''
        ).order_by('brand')
        
        return Response(brands)

    @action(detail=False, methods=['get'])
    def price_range(self, request):
        """Get price range for filtering."""
        queryset = self.get_queryset()
        
        # Calculate price range considering discount prices
        from django.db.models import Case, When, Min, Max
        
        price_range = queryset.aggregate(
            min_price=Min(
                Case(
                    When(discount_price__isnull=False, then='discount_price'),
                    default='price'
                )
            ),
            max_price=Max(
                Case(
                    When(discount_price__isnull=False, then='discount_price'),
                    default='price'
                )
            )
        )
        
        return Response(price_range)

    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Get search suggestions based on query."""
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 5))
        
        if not query or len(query) < 2:
            return Response({'suggestions': [], 'products': [], 'query': query})
        
        queryset = self.get_queryset()
        
        # Get text suggestions from product names and brands
        text_suggestions = set()
        
        # Product name suggestions
        product_names = queryset.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit * 2]
        
        for name in product_names:
            # Extract words that match the query
            words = name.lower().split()
            for word in words:
                if query.lower() in word and len(word) > 2:
                    text_suggestions.add(word.capitalize())
        
        # Brand suggestions
        brands = queryset.filter(
            brand__icontains=query,
            brand__isnull=False,
            brand__gt=''
        ).values_list('brand', flat=True).distinct()[:3]
        
        for brand in brands:
            if query.lower() in brand.lower():
                text_suggestions.add(brand)
        
        # Category suggestions
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True,
            is_deleted=False
        ).values_list('name', flat=True)[:3]
        
        for category in categories:
            if query.lower() in category.lower():
                text_suggestions.add(category)
        
        # Convert to list and limit
        suggestions_list = list(text_suggestions)[:limit]
        
        # Get top matching products for rich suggestions
        products = queryset.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        ).select_related('category').prefetch_related('images')[:3]
        
        product_suggestions = []
        for product in products:
            primary_image = product.primary_image
            product_suggestions.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.effective_price),
                'image': primary_image.image.url if primary_image else None,
                'category': product.category.name if product.category else None
            })
        
        return Response({
            'suggestions': suggestions_list,
            'products': product_suggestions,
            'query': query
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_featured(self, request, slug=None):
        """Toggle featured status of a product."""
        product = self.get_object()
        product.is_featured = not product.is_featured
        product.save()
        
        return Response({
            'message': f'Product {"featured" if product.is_featured else "unfeatured"} successfully',
            'is_featured': product.is_featured
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, slug=None):
        """Toggle active status of a product."""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        
        return Response({
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'is_active': product.is_active
        })

    def perform_destroy(self, instance):
        """Soft delete the product."""
        instance.delete()  # This will use the soft delete from BaseModel