"""
Wishlist URL patterns for API v1.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Wishlist Management
    path('', views.WishlistView.as_view(), name='wishlist-list'),
    path('add/', views.WishlistView.as_view(), name='wishlist-add'),
    path('clear/', views.WishlistView.as_view(), name='wishlist-clear'),
    path('<int:product_id>/', views.WishlistItemView.as_view(), name='wishlist-remove'),
    path('check/', views.CheckWishlistView.as_view(), name='wishlist-check'),
]