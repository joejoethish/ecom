"""
Views for the search app.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from .serializers import (
    SearchQuerySerializer, SuggestionQuerySerializer, FilterOptionsSerializer,
    SearchResponseSerializer, SuggestionResponseSerializer, IndexRebuildRequestSerializer,
    IndexRebuildResponseSerializer, RelatedProductsRequestSerializer
)
from .services import SearchService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class ProductSearchView(APIView):
    """
    API view for searching products with filtering, sorting, and pagination.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        query_serializer=SearchQuerySerializer,
        operation_description="Search for products with filtering and sorting",
        responses={
            200: SearchResponseSerializer,
            400: "Bad Request - Invalid parameters"
        }
    )
    def get(self, request):
        """
        Search for products with filtering, sorting, and pagination.
        """
        serializer = SearchQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        data = serializer.validated_data
        query = data.get('q', '')
        page = data.get('page', 1)
        page_size = data.get('page_size', 20)
        sort_by = data.get('sort_by', None)
        highlight = data.get('highlight', True)
        
        # Build filters dictionary
        filters = {}
        for key, value in data.items():
            if key not in ['q', 'page', 'page_size', 'sort_by', 'highlight'] and value is not None:
                filters[key] = value
        
        # Log search query for analytics
        logger.info(f"Search query: '{query}' with filters: {filters}")
        
        # Perform search
        results = SearchService.search_products(
            query=query,
            filters=filters,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            highlight=highlight
        )
        
        return Response(results)


class SearchSuggestionsView(APIView):
    """
    API view for search autocomplete suggestions.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        query_serializer=SuggestionQuerySerializer,
        operation_description="Get autocomplete suggestions for search",
        responses={
            200: SuggestionResponseSerializer,
            400: "Bad Request - Invalid parameters"
        }
    )
    def get(self, request):
        """
        Get autocomplete suggestions for search.
        """
        serializer = SuggestionQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['q']
        limit = serializer.validated_data.get('limit', 5)
        context = serializer.validated_data.get('context', None)
        
        # Log suggestion query for analytics
        logger.info(f"Suggestion query: '{query}' with context: {context}")
        
        # Try to use Elasticsearch first, fallback to database
        try:
            suggestions = SearchService.get_suggestions(query, context, limit)
        except Exception as e:
            logger.warning(f"Elasticsearch suggestions failed, falling back to database: {str(e)}")
            # Fallback to database-based suggestions
            suggestions = self._get_database_suggestions(query, limit, context)
        
        return Response(suggestions)
    
    def _get_database_suggestions(self, query: str, limit: int = 5, context: dict = None):
        """
        Fallback method to get suggestions from database when Elasticsearch is unavailable.
        """
        from apps.products.models import Product, Category
        from django.db.models import Q
        
        if len(query) < 2:
            return {'suggestions': [], 'products': [], 'query': query}
        
        # Get products queryset
        products_qs = Product.objects.filter(
            is_active=True,
            is_deleted=False,
            status='active'
        ).select_related('category').prefetch_related('images')
        
        # Apply context filters if provided
        if context:
            if context.get('category'):
                products_qs = products_qs.filter(category__slug=context['category'])
            if context.get('brand'):
                products_qs = products_qs.filter(brand__iexact=context['brand'])
        
        # Get text suggestions
        text_suggestions = set()
        
        # Product name suggestions
        product_names = products_qs.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit * 2]
        
        for name in product_names:
            words = name.lower().split()
            for word in words:
                if query.lower() in word and len(word) > 2:
                    text_suggestions.add(word.capitalize())
        
        # Brand suggestions
        brands = products_qs.filter(
            brand__icontains=query,
            brand__isnull=False,
            brand__gt=''
        ).values_list('brand', flat=True).distinct()[:3]
        
        for brand in brands:
            if query.lower() in brand.lower():
                text_suggestions.add(brand)
        
        # Category suggestions
        categories_qs = Category.objects.filter(
            name__icontains=query,
            is_active=True,
            is_deleted=False
        )
        
        if context and context.get('category'):
            # If category context is provided, look for subcategories
            try:
                parent_category = Category.objects.get(slug=context['category'])
                categories_qs = categories_qs.filter(parent=parent_category)
            except Category.DoesNotExist:
                pass
        
        categories = categories_qs.values_list('name', flat=True)[:3]
        
        for category in categories:
            if query.lower() in category.lower():
                text_suggestions.add(category)
        
        # Convert to list and limit
        suggestions_list = list(text_suggestions)[:limit]
        
        # Get top matching products
        products = products_qs.filter(
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
        
        return {
            'suggestions': suggestions_list,
            'products': product_suggestions,
            'query': query
        }


class FilterOptionsView(APIView):
    """
    API view for getting available filter options.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get available filter options for the search interface",
        responses={
            200: FilterOptionsSerializer,
            500: "Internal Server Error - Elasticsearch unavailable"
        }
    )
    def get(self, request):
        """
        Get available filter options for the search interface.
        """
        filter_options = SearchService.get_filter_options()
        
        return Response(filter_options)


class PopularSearchesView(APIView):
    """
    API view for getting popular search terms.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get popular search terms",
        manual_parameters=[
            openapi.Parameter(
                'limit', 
                openapi.IN_QUERY, 
                description="Maximum number of popular searches to return", 
                type=openapi.TYPE_INTEGER,
                default=10
            )
        ],
        responses={
            200: "List of popular search terms with metadata"
        }
    )
    def get(self, request):
        """
        Get popular search terms.
        """
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
            
        popular_searches = SearchService.get_popular_searches(limit)
        
        return Response({'popular_searches': popular_searches})


class RebuildIndexView(APIView):
    """
    API view for rebuilding the Elasticsearch index.
    Admin only endpoint.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        request_body=IndexRebuildRequestSerializer,
        operation_description="Rebuild the Elasticsearch index for products",
        responses={
            200: IndexRebuildResponseSerializer,
            401: "Unauthorized - Authentication required",
            500: "Internal Server Error - Index rebuild failed"
        }
    )
    def post(self, request):
        """
        Rebuild the Elasticsearch index for products.
        """
        serializer = IndexRebuildRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Log index rebuild request
        logger.info(f"Index rebuild requested by user: {request.user.username}")
        
        result = SearchService.rebuild_index()
        
        if result['status'] == 'error':
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(result)


class RelatedProductsView(APIView):
    """
    API view for getting related products.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        query_serializer=RelatedProductsRequestSerializer,
        operation_description="Get related products based on a product ID",
        responses={
            200: "List of related products",
            400: "Bad Request - Invalid parameters",
            404: "Not Found - Product not found"
        }
    )
    def get(self, request):
        """
        Get related products based on a product ID.
        """
        serializer = RelatedProductsRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product_id']
        limit = serializer.validated_data.get('limit', 6)
        
        related_products = SearchService.get_related_products(product_id, limit)
        
        if related_products is None:
            return Response(
                {"error": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response({'related_products': related_products})