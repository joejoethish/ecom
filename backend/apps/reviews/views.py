"""
Views for the reviews app.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from apps.products.models import Product
from core.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .models import Review, ReviewHelpfulness, ReviewReport
from .serializers import (
    ReviewListSerializer, ReviewDetailSerializer, ReviewCreateSerializer,
    ReviewUpdateSerializer, ReviewModerationSerializer, BulkModerationSerializer,
    ReviewHelpfulnessSerializer, ReviewReportSerializer, ReviewReportResolutionSerializer,
    ReviewAnalyticsSerializer, ProductReviewSummarySerializer, ModerationStatsSerializer
)
from .services import ReviewService, ReviewModerationService


class ReviewViewSet(ModelViewSet):
    """
    ViewSet for managing reviews.
    """
    queryset = Review.objects.select_related('user', 'product', 'moderated_by').prefetch_related('images')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        elif self.action == 'retrieve':
            return ReviewDetailSerializer
        elif self.action == 'moderate':
            return ReviewModerationSerializer
        elif self.action == 'bulk_moderate':
            return BulkModerationSerializer
        return ReviewListSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions and query parameters."""
        queryset = self.queryset
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        elif not self.request.user.is_staff:
            # Non-staff users can only see approved reviews
            queryset = queryset.filter(status='approved')
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Filter by verified purchase
        verified_only = self.request.query_params.get('verified_only')
        if verified_only and verified_only.lower() == 'true':
            queryset = queryset.filter(is_verified_purchase=True)
        
        # Filter by user (for user's own reviews)
        if self.action == 'list' and self.request.query_params.get('my_reviews'):
            queryset = queryset.filter(user=self.request.user)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-helpful_count')
        if ordering in ['rating', '-rating', 'created_at', '-created_at', 'helpful_count', '-helpful_count']:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create review with current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote_helpful(self, request, pk=None):
        """Vote on review helpfulness."""
        review = self.get_object()
        vote_type = request.data.get('vote')  # 'helpful' or 'not_helpful'
        
        if not vote_type or vote_type not in ['helpful', 'not_helpful']:
            return Response(
                {'error': 'Invalid vote type. Must be "helpful" or "not_helpful"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vote = ReviewService.vote_review_helpfulness(request.user, review, vote_type)
            serializer = ReviewHelpfulnessSerializer(vote, context={'request': request, 'review': review})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        """Report a review."""
        review = self.get_object()
        serializer = ReviewReportSerializer(
            data=request.data,
            context={'request': request, 'review': review}
        )
        
        if serializer.is_valid():
            try:
                report = ReviewService.report_review(
                    reporter=request.user,
                    review=review,
                    reason=serializer.validated_data['reason'],
                    description=serializer.validated_data.get('description', '')
                )
                response_serializer = ReviewReportSerializer(
                    report,
                    context={'request': request}
                )
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def moderate(self, request, pk=None):
        """Moderate a review (approve, reject, or flag)."""
        review = self.get_object()
        serializer = ReviewModerationSerializer(
            data=request.data,
            context={'request': request, 'review': review}
        )
        
        if serializer.is_valid():
            try:
                moderated_review = ReviewService.moderate_review(
                    review=review,
                    moderator=request.user,
                    action=serializer.validated_data['action'],
                    notes=serializer.validated_data.get('notes', '')
                )
                response_serializer = ReviewDetailSerializer(
                    moderated_review,
                    context={'request': request}
                )
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def bulk_moderate(self, request):
        """Bulk moderate multiple reviews."""
        serializer = BulkModerationSerializer(data=request.data)
        
        if serializer.is_valid():
            results = ReviewModerationService.bulk_moderate_reviews(
                review_ids=serializer.validated_data['review_ids'],
                moderator=request.user,
                action=serializer.validated_data['action'],
                notes=serializer.validated_data.get('notes', '')
            )
            return Response(results, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewsView(generics.ListAPIView):
    """
    View for listing reviews of a specific product.
    """
    serializer_class = ReviewListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get reviews for a specific product."""
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id)
        
        queryset = Review.objects.filter(
            product=product,
            status='approved'
        ).select_related('user', 'product').prefetch_related('images')
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Filter by verified purchase
        verified_only = self.request.query_params.get('verified_only')
        if verified_only and verified_only.lower() == 'true':
            queryset = queryset.filter(is_verified_purchase=True)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-helpful_count')
        if ordering in ['rating', '-rating', 'created_at', '-created_at', 'helpful_count', '-helpful_count']:
            queryset = queryset.order_by(ordering)
        
        return queryset


class ProductReviewSummaryView(generics.RetrieveAPIView):
    """
    View for getting product review summary.
    """
    serializer_class = ProductReviewSummarySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        """Get product review summary."""
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id)
        
        # Get analytics
        analytics = ReviewService.get_review_analytics(product=product)
        
        # Get recent reviews
        recent_reviews = Review.objects.filter(
            product=product,
            status='approved'
        ).select_related('user').prefetch_related('images').order_by('-created_at')[:5]
        
        # Calculate verified purchase percentage
        total_reviews = analytics['total_reviews']
        verified_reviews = Review.objects.filter(
            product=product,
            status='approved',
            is_verified_purchase=True
        ).count()
        
        verified_percentage = (verified_reviews / total_reviews * 100) if total_reviews > 0 else 0
        
        return {
            'product_id': product.id,
            'total_reviews': analytics['total_reviews'],
            'average_rating': analytics['average_rating'],
            'rating_distribution': analytics['rating_distribution'],
            'recent_reviews': recent_reviews,
            'verified_purchase_percentage': round(verified_percentage, 2)
        }


class ReviewAnalyticsView(generics.GenericAPIView):
    """
    View for review analytics.
    """
    serializer_class = ReviewAnalyticsSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        """Get review analytics."""
        # Get query parameters
        product_id = request.query_params.get('product')
        user_id = request.query_params.get('user')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Get product and user objects if provided
        product = None
        user = None
        
        if product_id:
            product = get_object_or_404(Product, id=product_id)
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)
        
        # Parse dates
        if date_from:
            from datetime import datetime
            date_from = datetime.fromisoformat(date_from)
        
        if date_to:
            from datetime import datetime
            date_to = datetime.fromisoformat(date_to)
        
        # Get analytics
        analytics = ReviewService.get_review_analytics(
            product=product,
            user=user,
            date_from=date_from,
            date_to=date_to
        )
        
        serializer = self.get_serializer(analytics)
        return Response(serializer.data)


class ModerationDashboardView(generics.GenericAPIView):
    """
    View for moderation dashboard.
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        """Get moderation dashboard data."""
        # Get pending reviews
        pending_reviews = ReviewModerationService.get_pending_reviews(page=1, per_page=10)
        
        # Get flagged reviews
        flagged_reviews = ReviewModerationService.get_flagged_reviews(page=1, per_page=10)
        
        # Get reported reviews
        reported_reviews = ReviewModerationService.get_reported_reviews(page=1, per_page=10)
        
        # Get moderation stats
        stats = ReviewModerationService.get_moderation_stats()
        
        return Response({
            'stats': ModerationStatsSerializer(stats).data,
            'pending_reviews': {
                'results': ReviewListSerializer(
                    pending_reviews['reviews'],
                    many=True,
                    context={'request': request}
                ).data,
                'count': pending_reviews['total_count']
            },
            'flagged_reviews': {
                'results': ReviewListSerializer(
                    flagged_reviews['reviews'],
                    many=True,
                    context={'request': request}
                ).data,
                'count': flagged_reviews['total_count']
            },
            'reported_reviews': {
                'results': ReviewReportSerializer(
                    reported_reviews['reports'],
                    many=True,
                    context={'request': request}
                ).data,
                'count': reported_reviews['total_count']
            }
        })


class ReviewReportViewSet(ModelViewSet):
    """
    ViewSet for managing review reports.
    """
    queryset = ReviewReport.objects.select_related('review', 'reporter', 'reviewed_by')
    serializer_class = ReviewReportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = self.queryset
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by reason
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(reason=reason)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a review report."""
        report = self.get_object()
        serializer = ReviewReportResolutionSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            
            if action == 'resolve':
                report.resolve(request.user, notes)
            elif action == 'dismiss':
                report.dismiss(request.user, notes)
            
            response_serializer = ReviewReportSerializer(
                report,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)