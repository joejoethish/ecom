"""
Cart URL patterns.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSet
router = DefaultRouter()
router.register(r'viewset', views.CartViewSet, basename='cart-viewset')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Direct APIView URLs (main endpoints)
    path('get/', views.CartView.as_view(), name='cart'),
    path('add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('remove/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('clear/', views.ClearCartView.as_view(), name='clear-cart'),
    path('save-for-later/', views.SaveForLaterView.as_view(), name='save-for-later'),
    path('move-to-cart/', views.MoveToCartView.as_view(), name='move-to-cart'),
    path('saved-items/', views.SavedItemsView.as_view(), name='saved-items'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply-coupon'),
    path('remove-coupon/', views.RemoveCouponView.as_view(), name='remove-coupon'),
    
    # Legacy APIView URLs (keeping for backward compatibility)
    path('legacy/', views.CartView.as_view(), name='legacy-cart'),
    path('legacy/add/', views.AddToCartView.as_view(), name='legacy-add-to-cart'),
    path('legacy/update/', views.UpdateCartItemView.as_view(), name='legacy-update-cart-item'),
    path('legacy/remove/', views.RemoveFromCartView.as_view(), name='legacy-remove-from-cart'),
    path('legacy/clear/', views.ClearCartView.as_view(), name='legacy-clear-cart'),
    path('legacy/save-for-later/', views.SaveForLaterView.as_view(), name='legacy-save-for-later'),
    path('legacy/move-to-cart/', views.MoveToCartView.as_view(), name='legacy-move-to-cart'),
    path('legacy/saved-items/', views.SavedItemsView.as_view(), name='legacy-saved-items'),
    path('legacy/apply-coupon/', views.ApplyCouponView.as_view(), name='legacy-apply-coupon'),
    path('legacy/remove-coupon/', views.RemoveCouponView.as_view(), name='legacy-remove-coupon'),
]