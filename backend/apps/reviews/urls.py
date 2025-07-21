"""
URL configuration for reviews app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReviewViewSet, ProductReviewsView, ProductReviewSummaryView,
    ReviewAnalyticsView, ModerationDashboardView, ReviewReportViewSet
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'reports', ReviewReportViewSet, basename='review-report')

app_name = 'reviews'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Product-specific review endpoints
    path('products/<uuid:product_id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),
    path('products/<uuid:product_id>/reviews/summary/', ProductReviewSummaryView.as_view(), name='product-review-summary'),
    
    # Analytics and moderation
    path('analytics/', ReviewAnalyticsView.as_view(), name='review-analytics'),
    path('moderation/dashboard/', ModerationDashboardView.as_view(), name='moderation-dashboard'),
]