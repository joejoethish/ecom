"""
API v1 URL configuration.
"""
from django.urls import path, include
from .categories import (
    get_featured_categories,
    get_all_categories,
    get_category_details,
    get_category_filters
)
from .products import (
    get_featured_products,
    get_products_by_category,
    search_products
)

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('products/', include('apps.products.urls')),
    path('search/', include('apps.search.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('payments/', include('apps.payments.urls')),
    # Other app URLs will be added as they are implemented
    # path('orders/', include('apps.orders.urls')),
    # path('cart/', include('apps.cart.urls')),
    path('customers/', include('apps.customers.urls')),
    # path('sellers/', include('apps.sellers.urls')),
    path('shipping/', include('apps.shipping.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('customer-analytics/', include('apps.customer_analytics.urls')),
    path('content/', include('apps.content.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('promotions/', include('apps.promotions.urls')),
    path('admin/data-management/', include('apps.data_management.urls')),
    path('admin/security/', include('apps.security_management.urls')),
    
    # Categories API
    path('categories/', get_all_categories, name='all-categories'),
    path('categories/featured/', get_featured_categories, name='featured-categories'),
    path('categories/<slug:category_slug>/', get_category_details, name='category-details'),
    path('categories/<slug:category_slug>/filters/', get_category_filters, name='category-filters'),
    
    # Products API
    path('products/featured/', get_featured_products, name='featured-products'),
    path('products/category/<slug:category_slug>/', get_products_by_category, name='products-by-category'),
    path('products/search/', search_products, name='search-products'),
]