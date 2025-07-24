"""
Product views for API v2 with enhanced features and backward compatibility.
"""
from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from core.permissions import IsAdminOrReadOnly
from core.pagination import StandardResultsSetPagination
from core.versioning import VersionedViewMixin, VersionedSerializerMixin, DeprecationWarningMixin
from core.docs import (
    document_api, document_product_view, paginated_response, 
    common_parameters, filter_parameters, create_examples
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Product, Category
from .serializers_v2 import (
    ProductListSerializerV2, ProductDetailSerializerV2, ProductCreateUpdateSerializerV2,
    CategorySerializerV2, CategorySerializer as CategoryListSerializerV2
)
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    CategorySerializer, CategoryListSerializer
)
from .filters import ProductFilter, CategoryFilter
from .views import CategoryViewSet as CategoryViewSetV1, ProductViewSet as ProductViewSetV1


@extend_schema(tags=["Categories"])
class CategoryViewSetV2(CategoryViewSetV1, VersionedViewMixin, VersionedSerializerMixin, DeprecationWarningMixin):
    """
    Enhanced CategoryViewSet for API v2 with additional features.
    
    This viewset provides CRUD operations for product categories with enhanced features in API v2.
    It maintains backward compatibility with API v1 while adding new functionality like breadcrumb and tree views.
    """
    serializer_class_map = {
        'v1': CategorySerializer,
        'v2': CategorySerializerV2
    }

    def get_serializer_class(self):
        """Return version-specific serializer based on action and API version."""
        version = self.get_version()
        
        if self.action == 'list':
            if version == 'v2':
                return CategorySerializerV2
            return CategoryListSerializer
        
        # Use version-specific serializer
        return self.serializer_class_map.get(version, CategorySerializer)

    @extend_schema(
        summary="Get category breadcrumb path",
        description="Returns the breadcrumb path for a specific category, including all parent categories.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "breadcrumb": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "slug": {"type": "string"},
                                "url": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        tags=["Categories"]
    )
    @action(detail=True, methods=['get'])
    def breadcrumb(self, request, slug=None):
        """Get category breadcrumb path (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Breadcrumb endpoint is only available in API v2")
        
        category = self.get_object()
        breadcrumb = []
        current = category
        
        while current:
            breadcrumb.insert(0, {
                'id': str(current.id),
                'name': current.name,
                'slug': current.slug,
                'url': f'/categories/{current.slug}/'
            })
            current = current.parent
        
        return Response({'breadcrumb': breadcrumb})

    @extend_schema(
        summary="Get complete category tree",
        description="Returns the complete category hierarchy as a nested tree structure.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "tree": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "slug": {"type": "string"},
                                "children": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/CategoryNode"}
                                }
                            }
                        }
                    }
                }
            }
        },
        tags=["Categories"]
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get complete category tree (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Tree endpoint is only available in API v2")
        
        def build_tree(parent=None):
            categories = self.get_queryset().filter(parent=parent)
            tree = []
            
            for category in categories:
                node = {
                    'id': str(category.id),
                    'name': category.name,
                    'slug': category.slug,
                    'children': build_tree(category)
                }
                tree.append(node)
            
            return tree
        
        tree = build_tree()
        return Response({'tree': tree})


@extend_schema(tags=["Products"])
class ProductViewSetV2(ProductViewSetV1, VersionedViewMixin, VersionedSerializerMixin, DeprecationWarningMixin):
    """
    Enhanced ProductViewSet for API v2 with additional features and backward compatibility.
    
    This viewset provides CRUD operations for products with enhanced features in API v2.
    It maintains backward compatibility with API v1 while adding new functionality.
    """
    serializer_class_map = {
        'v1': {
            'list': ProductListSerializer,
            'detail': ProductDetailSerializer,
            'create_update': ProductCreateUpdateSerializer
        },
        'v2': {
            'list': ProductListSerializerV2,
            'detail': ProductDetailSerializerV2,
            'create_update': ProductCreateUpdateSerializerV2
        }
    }

    def get_serializer_class(self):
        """Return version-specific serializer based on action and API version."""
        version = self.get_version()
        version_serializers = self.serializer_class_map.get(version, self.serializer_class_map['v1'])
        
        if self.action == 'list':
            return version_serializers['list']
        elif self.action in ['create', 'update', 'partial_update']:
            return version_serializers['create_update']
        else:
            return version_serializers['detail']

    @extend_schema(
        summary="Get trending products",
        description="Returns a list of trending products based on popularity metrics.",
        responses={200: ProductListSerializerV2(many=True)},
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Maximum number of products to return",
                required=False,
                default=10
            ),
        ],
        tags=["Products"]
    )
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending products (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Trending endpoint is only available in API v2")
        
        # This would typically be based on view counts, sales, etc.
        # For now, return featured products as trending
        queryset = self.get_queryset().filter(is_featured=True)[:10]
        serializer = ProductListSerializerV2(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Get personalized product recommendations",
        description="Returns a list of recommended products based on user browsing history and preferences.",
        responses={200: ProductListSerializerV2(many=True)},
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Maximum number of products to return",
                required=False,
                default=8
            ),
        ],
        tags=["Products"]
    )
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get product recommendations (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Recommendations endpoint is only available in API v2")
        
        # This would typically use ML algorithms for recommendations
        # For now, return random products from popular categories
        queryset = self.get_queryset().order_by('?')[:8]
        serializer = ProductListSerializerV2(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Get related products",
        description="Returns a list of products related to the specified product. In v2, includes products from parent and child categories.",
        responses={200: ProductListSerializerV2(many=True)},
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Maximum number of products to return",
                required=False,
                default=8
            ),
        ],
        tags=["Products"]
    )
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Get related products (enhanced in v2)."""
        product = self.get_object()
        
        # Get related products from same category
        related = Product.objects.filter(
            category=product.category,
            is_active=True,
            is_deleted=False
        ).exclude(id=product.id)
        
        # In v2, also include products from parent/child categories
        if self.is_version('v2'):
            category_ids = [product.category.id]
            
            # Add parent category
            if product.category.parent:
                category_ids.append(product.category.parent.id)
            
            # Add child categories
            child_categories = product.category.children.filter(is_active=True, is_deleted=False)
            category_ids.extend(child_categories.values_list('id', flat=True))
            
            related = Product.objects.filter(
                category_id__in=category_ids,
                is_active=True,
                is_deleted=False
            ).exclude(id=product.id)
        
        related = related[:8]
        
        if self.is_version('v2'):
            serializer = ProductListSerializerV2(related, many=True, context={'request': request})
        else:
            serializer = ProductListSerializer(related, many=True, context={'request': request})
        
        return Response(serializer.data)

    @extend_schema(
        summary="Get detailed product availability",
        description="Returns detailed availability information for a specific product including stock status, quantity, and restock information.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "sku": {"type": "string"},
                    "status": {"type": "string", "enum": ["in_stock", "out_of_stock", "unknown"]},
                    "quantity": {"type": "integer", "nullable": true},
                    "estimated_restock_date": {"type": "string", "format": "date", "nullable": true},
                    "can_backorder": {"type": "boolean"},
                    "low_stock_threshold": {"type": "integer", "nullable": true},
                    "is_low_stock": {"type": "boolean", "nullable": true},
                    "reserved_quantity": {"type": "integer", "nullable": true}
                }
            }
        },
        tags=["Products"]
    )
    @action(detail=True, methods=['get'])
    def availability(self, request, slug=None):
        """Get detailed product availability (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Availability endpoint is only available in API v2")
        
        product = self.get_object()
        availability_data = {
            'product_id': str(product.id),
            'sku': product.sku,
            'status': 'unknown',
            'quantity': None,
            'estimated_restock_date': None,
            'can_backorder': False
        }
        
        if hasattr(product, 'inventory'):
            inventory = product.inventory
            availability_data.update({
                'quantity': inventory.quantity,
                'status': 'in_stock' if inventory.quantity > 0 else 'out_of_stock',
                'low_stock_threshold': inventory.minimum_stock_level,
                'is_low_stock': inventory.quantity <= inventory.minimum_stock_level,
                'reserved_quantity': getattr(inventory, 'reserved_quantity', 0)
            })
        
        return Response(availability_data)

    @extend_schema(
        summary="Get availability for multiple products",
        description="Returns availability information for multiple products in a single request.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "products": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "sku": {"type": "string"},
                                "status": {"type": "string", "enum": ["in_stock", "out_of_stock", "unknown"]},
                                "quantity": {"type": "integer", "nullable": true}
                            }
                        }
                    }
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        },
        parameters=[
            OpenApiParameter(
                name="ids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of product IDs",
                required=True,
                example="1,2,3,4"
            ),
        ],
        tags=["Products"]
    )
    @action(detail=False, methods=['get'])
    def bulk_availability(self, request):
        """Get availability for multiple products (v2 only)."""
        if not self.is_version('v2'):
            return self.version_not_supported("Bulk availability endpoint is only available in API v2")
        
        product_ids = request.GET.get('ids', '').split(',')
        if not product_ids or not product_ids[0]:
            return Response({'error': 'Product IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_deleted=False
        ).select_related('inventory')
        
        availability_data = []
        for product in products:
            data = {
                'product_id': str(product.id),
                'sku': product.sku,
                'status': 'unknown',
                'quantity': None
            }
            
            if hasattr(product, 'inventory'):
                inventory = product.inventory
                data.update({
                    'quantity': inventory.quantity,
                    'status': 'in_stock' if inventory.quantity > 0 else 'out_of_stock'
                })
            
            availability_data.append(data)
        
        return Response({'products': availability_data})

    @extend_schema(
        summary="Advanced product search",
        description="Provides advanced search capabilities with multiple filtering options. Enhanced in v2 with additional filters.",
        responses={200: ProductListSerializerV2(many=True)},
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search query for product name, description, brand, or tags",
                required=False
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by category ID",
                required=False
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                description="Minimum price filter",
                required=False
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                description="Maximum price filter",
                required=False
            ),
            OpenApiParameter(
                name="brand",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by brand name",
                required=False
            ),
            OpenApiParameter(
                name="min_rating",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Filter by minimum rating (v2 only)",
                required=False
            ),
            OpenApiParameter(
                name="availability",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by availability status (v2 only): 'in_stock' or 'out_of_stock'",
                required=False,
                enum=["in_stock", "out_of_stock"]
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field (prefix with '-' for descending order)",
                required=False,
                enum=["price", "-price", "name", "-name", "created_at", "-created_at"]
            ),
        ],
        tags=["Products", "Search"]
    )
    @action(detail=False, methods=['get'])
    def advanced_search(self, request):
        """Advanced search with filters (enhanced in v2)."""
        queryset = self.get_queryset()
        
        # Basic search
        query = request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # V2 specific filters
        if self.is_version('v2'):
            # Rating filter
            min_rating = request.GET.get('min_rating')
            if min_rating:
                # This would filter by average rating
                pass
            
            # Availability filter
            availability = request.GET.get('availability')
            if availability == 'in_stock':
                queryset = queryset.filter(inventory__quantity__gt=0)
            elif availability == 'out_of_stock':
                queryset = queryset.filter(inventory__quantity=0)
        
        # Apply standard filters
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            if self.is_version('v2'):
                serializer = ProductListSerializerV2(page, many=True, context={'request': request})
            else:
                serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        if self.is_version('v2'):
            serializer = ProductListSerializerV2(queryset, many=True, context={'request': request})
        else:
            serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        
        return Response(serializer.data)