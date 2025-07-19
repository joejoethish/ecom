"""
Customers URL patterns.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Customer Profile Management
    path('profile/', views.CustomerProfileView.as_view(), name='customer-profile'),
    
    # Address Management
    path('addresses/', views.AddressListView.as_view(), name='customer-addresses'),
    path('addresses/<int:address_id>/', views.AddressDetailView.as_view(), name='customer-address-detail'),
    path('addresses/<int:address_id>/set-default/', views.SetDefaultAddressView.as_view(), name='set-default-address'),
    
    # Wishlist Management
    path('wishlist/', views.WishlistView.as_view(), name='customer-wishlist'),
    path('wishlist/items/<int:product_id>/', views.WishlistItemView.as_view(), name='wishlist-item'),
    path('wishlist/check/<int:product_id>/', views.CheckWishlistView.as_view(), name='check-wishlist'),
    
    # Activity and Analytics
    path('activities/', views.CustomerActivityView.as_view(), name='customer-activities'),
    path('analytics/', views.CustomerAnalyticsView.as_view(), name='customer-analytics'),
    path('log-activity/', views.log_customer_activity, name='log-customer-activity'),
    
    # Admin Endpoints
    path('admin/customers/', views.AdminCustomerListView.as_view(), name='admin-customer-list'),
    path('admin/customers/<int:pk>/', views.AdminCustomerDetailView.as_view(), name='admin-customer-detail'),
    path('admin/customers/<int:customer_id>/status/', views.AdminCustomerStatusView.as_view(), name='admin-customer-status'),
]