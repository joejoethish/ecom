"""
Sellers URL patterns.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'kyc', views.SellerKYCViewSet, basename='seller-kyc')
router.register(r'bank-accounts', views.SellerBankAccountViewSet, basename='seller-bank-accounts')
router.register(r'payouts', views.SellerPayoutHistoryViewSet, basename='seller-payouts')

# Admin routers
admin_router = DefaultRouter()
admin_router.register(r'sellers', views.AdminSellerViewSet, basename='admin-sellers')
admin_router.register(r'kyc', views.AdminSellerKYCViewSet, basename='admin-kyc')
admin_router.register(r'bank-accounts', views.AdminSellerBankAccountViewSet, basename='admin-bank-accounts')
admin_router.register(r'payouts', views.AdminSellerPayoutViewSet, basename='admin-payouts')

urlpatterns = [
    # Seller registration
    path('register/', views.SellerRegistrationView.as_view(), name='seller-register'),
    
    # Seller profile management
    path('profile/', views.SellerProfileView.as_view(), name='seller-profile'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Admin routes
    path('admin/', include(admin_router.urls)),
]