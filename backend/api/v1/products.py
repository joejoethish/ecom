"""
Products API endpoints.
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from apps.products.models import Product, Category
from apps.products.serializers import ProductDetailSerializer, ProductListSerializer


@api_view(['GET'])
def get_featured_products(request):
    """
    Get featured products for homepage.
    """
    try:
        featured_products = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related('category').prefetch_related('images', 'reviews')[:12]
        
        products_data = []
        for product in featured_products:
            # Calculate average rating
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            review_count = product.reviews.count()
            
            # Get primary image
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image.url if primary_image else None
            
            # Calculate discount percentage
            discount_percentage = 0
            if product.discount_price and product.discount_price < product.price:
                discount_percentage = int(((product.price - product.discount_price) / product.price) * 100)
            
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'discount_percentage': discount_percentage,
                'image': image_url,
                'rating': round(avg_rating, 1),
                'review_count': review_count,
                'brand': product.brand,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'slug': product.category.slug
                },
                'is_featured': product.is_featured,
                'free_delivery': True,  # For now, assume all featured products have free delivery
                'exchange_offer': discount_percentage > 10  # Exchange offer for products with >10% discount
            })
        
        return Response({
            'success': True,
            'data': products_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'FEATURED_PRODUCTS_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_products_by_category(request, category_slug):
    """
    Get products by category.
    """
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
        
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category').prefetch_related('images', 'reviews')
        
        # Apply filters
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        brand = request.GET.get('brand')
        sort_by = request.GET.get('sort', 'name')
        
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if brand:
            products = products.filter(brand__icontains=brand)
        
        # Sorting
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'rating':
            products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        else:
            products = products.order_by('name')
        
        products_data = []
        for product in products:
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            review_count = product.reviews.count()
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image.url if primary_image else None
            
            discount_percentage = 0
            if product.discount_price and product.discount_price < product.price:
                discount_percentage = int(((product.price - product.discount_price) / product.price) * 100)
            
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'discount_percentage': discount_percentage,
                'image': image_url,
                'rating': round(avg_rating, 1),
                'review_count': review_count,
                'brand': product.brand,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'slug': product.category.slug
                }
            })
        
        return Response({
            'success': True,
            'data': {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description
                },
                'products': products_data,
                'total_count': len(products_data)
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


@api_view(['GET'])
def search_products(request):
    """
    Search products by name, description, or brand.
    """
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({
                'success': False,
                'error': {
                    'message': 'Search query is required',
                    'code': 'MISSING_QUERY'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            is_active=True
        ).select_related('category').prefetch_related('images', 'reviews')
        
        products_data = []
        for product in products:
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            review_count = product.reviews.count()
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image.url if primary_image else None
            
            discount_percentage = 0
            if product.discount_price and product.discount_price < product.price:
                discount_percentage = int(((product.price - product.discount_price) / product.price) * 100)
            
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'discount_percentage': discount_percentage,
                'image': image_url,
                'rating': round(avg_rating, 1),
                'review_count': review_count,
                'brand': product.brand,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'slug': product.category.slug
                }
            })
        
        return Response({
            'success': True,
            'data': {
                'query': query,
                'products': products_data,
                'total_count': len(products_data)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'SEARCH_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)