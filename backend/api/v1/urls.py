"""
API v1 URL configuration.
"""
from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('products/', include('apps.products.urls')),
    path('search/', include('apps.search.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('payments/', include('apps.payments.urls')),
    # Other app URLs will be added as they are implemented
    # path('orders/', include('apps.orders.urls')),
    # path('cart/', include('apps.cart.urls')),
    # path('customers/', include('apps.customers.urls')),
    # path('sellers/', include('apps.sellers.urls')),
    path('shipping/', include('apps.shipping.urls')),
    # path('reviews/', include('apps.reviews.urls')),
    # path('analytics/', include('apps.analytics.urls')),
    # path('content/', include('apps.content.urls')),
    # path('notifications/', include('apps.notifications.urls')),
]