"""
Categories API endpoints for dynamic data.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.products.models import Category, Product


@api_view(['GET'])
def get_featured_categories(request):
    """
    Get featured categories for homepage with product counts.
    """
    try:
        # Get categories with product counts
        categories = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('-product_count')[:12]
        
        categories_data = []
        for category in categories:
            # Map category names to icons and hrefs
            icon_mapping = {
                'Electronics': '💻',
                'Fashion': '👗', 
                'Home & Kitchen': '🏠',
                'Books': '📚',
                'Sports': '⚽',
                'Beauty': '💄',
                'Mobiles': '📱',
                'Appliances': '🔌',
                'Travel': '✈️',
                'Grocery': '🛒'
            }
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'icon': icon_mapping.get(category.name, '📦'),
                'href': f'/category/{category.slug}',
                'product_count': category.product_count,
                'is_featured': True
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


@api_view(['GET'])
def get_all_categories(request):
    """
    Get all active categories with product counts.
    """
    try:
        categories = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('name')
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'product_count': category.product_count,
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat()
            })
        
        return Response({
            'success': True,
            'data': categories_data,
            'total_count': len(categories_data)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'ALL_CATEGORIES_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_category_details(request, category_slug):
    """
    Get detailed information about a specific category.
    """
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
        
        # Get product count
        product_count = Product.objects.filter(
            category=category,
            is_active=True
        ).count()
        
        # Get top brands in this category
        top_brands = Product.objects.filter(
            category=category,
            is_active=True
        ).values('brand').annotate(
            count=Count('brand')
        ).order_by('-count')[:10]
        
        category_data = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'product_count': product_count,
            'top_brands': [{'name': brand['brand'], 'count': brand['count']} for brand in top_brands],
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat()
        }
        
        return Response({
            'success': True,
            'data': category_data
        })
        
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'message': 'Category not found',
                'code': 'CATEGORY_NOT_FOUND'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'CATEGORY_DETAILS_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_category_filters(request, category_slug):
    """
    Get available filters for a specific category.
    """
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
        
        # Get all products in this category
        products = Product.objects.filter(
            category=category,
            is_active=True
        )
        
        # Get unique brands
        brands = products.values('brand').annotate(
            count=Count('brand')
        ).order_by('brand')
        
        # Get price ranges
        price_ranges = [
            {'from': None, 'to': 100, 'label': 'Under $100'},
            {'from': 100, 'to': 500, 'label': '$100 - $500'},
            {'from': 500, 'to': 1000, 'label': '$500 - $1000'},
            {'from': 1000, 'to': None, 'label': '$1000+'}
        ]
        
        # Count products in each price range
        for price_range in price_ranges:
            if price_range['from'] is None:
                count = products.filter(price__lt=price_range['to']).count()
            elif price_range['to'] is None:
                count = products.filter(price__gte=price_range['from']).count()
            else:
                count = products.filter(
                    price__gte=price_range['from'],
                    price__lt=price_range['to']
                ).count()
            price_range['count'] = count
        
        filters_data = {
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug
            },
            'brands': [{'name': brand['brand'], 'count': brand['count']} for brand in brands],
            'price_ranges': price_ranges,
            'total_products': products.count()
        }
        
        return Response({
            'success': True,
            'data': filters_data
        })
        
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'message': 'Category not found',
                'code': 'CATEGORY_NOT_FOUND'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'CATEGORY_FILTERS_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)