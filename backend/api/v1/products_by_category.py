"""
Products by category API endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count
from apps.products.models import Category, Product


@api_view(['GET'])
def get_products_by_category(request, category_slug):
    """
    Get products by category with filtering and pagination.
    """
    try:
        # Get the category
        category = Category.objects.get(slug=category_slug, is_active=True)
        
        # Get query parameters
        page = request.GET.get('page', 1)
        sort = request.GET.get('sort', 'name')
        brand = request.GET.get('brand')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        
        # Start with products in this category
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category').prefetch_related('images')
        
        # Apply filters
        if brand:
            products = products.filter(brand__icontains=brand)
        
        if price_min:
            try:
                products = products.filter(price__gte=float(price_min))
            except ValueError:
                pass
        
        if price_max:
            try:
                products = products.filter(price__lte=float(price_max))
            except ValueError:
                pass
        
        # Apply sorting
        sort_mapping = {
            'name': 'name',
            '-name': '-name',
            'price': 'price',
            '-price': '-price',
            'created_at': 'created_at',
            '-created_at': '-created_at',
            'popularity': '-id',  # Placeholder for popularity
            'rating': '-id',  # Placeholder for rating
        }
        
        if sort in sort_mapping:
            products = products.order_by(sort_mapping[sort])
        else:
            products = products.order_by('name')
        
        # Paginate results
        paginator = Paginator(products, 20)  # 20 products per page
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Serialize products
        products_data = []
        for product in page_obj:
            # Get primary image
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image.url if primary_image else None
            
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'discount_percentage': product.discount_percentage,
                'image': image_url,
                'rating': 0,  # Placeholder - implement rating system
                'review_count': 0,  # Placeholder - implement review system
                'brand': product.brand,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'slug': product.category.slug,
                },
                'is_featured': product.is_featured,
                'free_delivery': True,  # Placeholder
                'exchange_offer': True,  # Placeholder
            })
        
        return Response({
            'success': True,
            'data': {
                'data': products_data,
                'total_count': paginator.count,
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
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
                'code': 'PRODUCTS_BY_CATEGORY_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)