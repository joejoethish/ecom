"""
Customers URL patterns.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.CustomerProfileView.as_view(), name='customer-profile'),
    path('addresses/', views.AddressListView.as_view(), name='customer-addresses'),
]