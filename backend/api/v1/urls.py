"""
API v1 URL configuration.
"""
from django.urls import path, include
from .categories import (
    CategoryListCreateView, 
    CategoryDetailView, 
    get_category_tree, 
    get_featured_categories,
    bulk_update_categories
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
    path('content/', include('apps.content.urls')),
    path('notifications/', include('apps.notifications.urls')),
    
    # Categories API
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/tree/', get_category_tree, name='category-tree'),
    path('categories/featured/', get_featured_categories, name='featured-categories'),
    path('categories/bulk-update/', bulk_update_categories, name='bulk-update-categories'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
]