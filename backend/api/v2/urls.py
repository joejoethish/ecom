"""
API v2 URL configuration.
"""
from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.urls_v2')),
    path('products/', include('apps.products.urls_v2')),
    path('search/', include('apps.search.urls_v2')),
    path('inventory/', include('apps.inventory.urls_v2')),
    path('payments/', include('apps.payments.urls_v2')),
    path('orders/', include('apps.orders.urls_v2')),
    path('cart/', include('apps.cart.urls_v2')),
    path('customers/', include('apps.customers.urls_v2')),
    path('sellers/', include('apps.sellers.urls_v2')),
    path('shipping/', include('apps.shipping.urls_v2')),
    path('reviews/', include('apps.reviews.urls_v2')),
    path('analytics/', include('apps.analytics.urls_v2')),
    path('content/', include('apps.content.urls_v2')),
    path('notifications/', include('apps.notifications.urls_v2')),
]