"""
Reviews URL patterns for API v2.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# For now, v2 uses the same views as v1
router = DefaultRouter()
router.register(r'product-reviews', views.ProductReviewViewSet, basename='product-reviews_v2')
router.register(r'seller-reviews', views.SellerReviewViewSet, basename='seller-reviews_v2')
router.register(r'review-replies', views.ReviewReplyViewSet, basename='review-replies_v2')

urlpatterns = [
    path('', include(router.urls)),
    path('summary/<uuid:product_id>/', views.ReviewSummaryView.as_view(), name='review-summary_v2'),
]