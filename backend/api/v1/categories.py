"""
Categories API endpoints.
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.products.models import Category
from apps.products.serializers import CategorySerializer, CategoryListSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    List all categories or create a new category.
    """
    queryset = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    serializer_class = CategoryListSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a category.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]


@api_view(['GET'])
def get_category_tree(request):
    """
    Get hierarchical category tree.
    """
    try:
        # Get root categories (categories without parent)
        root_categories = Category.objects.filter(
            parent=None, 
            is_active=True
        ).order_by('sort_order', 'name')
        
        def build_category_tree(categories):
            tree = []
            for category in categories:
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'image': category.image.url if category.image else None,
                    'sort_order': category.sort_order,
                    'children': build_category_tree(
                        category.children.filter(is_active=True).order_by('sort_order', 'name')
                    )
                }
                tree.append(category_data)
            return tree
        
        category_tree = build_category_tree(root_categories)
        
        return Response({
            'success': True,
            'data': category_tree
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'CATEGORY_TREE_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_featured_categories(request):
    """
    Get featured categories for homepage.
    """
    try:
        # Get categories that have featured products or are marked as featured
        featured_categories = Category.objects.filter(
            is_active=True,
            products__is_featured=True
        ).distinct().order_by('sort_order', 'name')[:9]  # Limit to 9 for homepage
        
        categories_data = []
        for category in featured_categories:
            # Get a representative icon/emoji for the category
            category_icons = {
                'mobiles': '📱',
                'fashion': '👕',
                'electronics': '💻',
                'home-furniture': '🏠',
                'appliances': '🔌',
                'travel': '✈️',
                'beauty-toys': '💄',
                'two-wheelers': '🏍️',
                'grocery': '🛒',
                'books': '📚',
                'sports': '⚽',
                'health': '💊',
                'automotive': '🚗',
                'jewelry': '💍',
                'baby-kids': '🧸'
            }
            
            icon = category_icons.get(category.slug, '🛍️')
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': icon,
                'href': f'/category/{category.slug}',
                'image': category.image.url if category.image else None,
                'products_count': category.products.filter(is_active=True).count()
            })
        
        return Response({
            'success': True,
            'data': categories_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'FEATURED_CATEGORIES_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def bulk_update_categories(request):
    """
    Bulk update category sort orders.
    """
    try:
        categories_data = request.data.get('categories', [])
        
        for category_data in categories_data:
            category_id = category_data.get('id')
            sort_order = category_data.get('sort_order')
            
            if category_id and sort_order is not None:
                Category.objects.filter(id=category_id).update(sort_order=sort_order)
        
        return Response({
            'success': True,
            'message': 'Categories updated successfully'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'BULK_UPDATE_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)