"""
Cart URL patterns.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('remove/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('clear/', views.ClearCartView.as_view(), name='clear-cart'),
    path('save-for-later/', views.SaveForLaterView.as_view(), name='save-for-later'),
    path('move-to-cart/', views.MoveToCartView.as_view(), name='move-to-cart'),
    path('saved-items/', views.SavedItemsView.as_view(), name='saved-items'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply-coupon'),
    path('remove-coupon/', views.RemoveCouponView.as_view(), name='remove-coupon'),
]