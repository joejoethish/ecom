"""
Review services for business logic and validation.
"""
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.orders.models import OrderItem
from apps.products.models import Product
from .models import Review, ReviewHelpfulness, ReviewReport


class ReviewService:
    """
    Service class for review-related business logic.
    """
    
    @staticmethod
    def can_user_review_product(user, product):
        """
        Check if a user can review a product.
        
        Args:
            user: User instance
            product: Product instance
            
        Returns:
            tuple: (can_review: bool, reason: str, order_item: OrderItem or None)
        """
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(user=user, product=product).first()
        if existing_review:
            return False, "You have already reviewed this product", None
        
        # Check if user has purchased this product
        order_item = OrderItem.objects.filter(
            order__customer=user,
            product=product,
            order__status='delivered'
        ).first()
        
        if not order_item:
            return False, "You can only review products you have purchased", None
        
        return True, "Can review", order_item
    
    @staticmethod
    def create_review(user, product, rating, title, comment, pros="", cons="", images=None):
        """
        Create a new review with validation.
        
        Args:
            user: User instance
            product: Product instance
            rating: int (1-5)
            title: str
            comment: str
            pros: str (optional)
            cons: str (optional)
            images: list of image files (optional)
            
        Returns:
            Review instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate user can review product
        can_review, reason, order_item = ReviewService.can_user_review_product(user, product)
        if not can_review:
            raise ValidationError(reason)
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5")
        
        # Validate required fields
        if not title.strip():
            raise ValidationError("Review title is required")
        
        if not comment.strip():
            raise ValidationError("Review comment is required")
        
        # Create review
        with transaction.atomic():
            review = Review.objects.create(
                user=user,
                product=product,
                order_item=order_item,
                rating=rating,
                title=title.strip(),
                comment=comment.strip(),
                pros=pros.strip(),
                cons=cons.strip(),
                is_verified_purchase=True,
                status='pending'  # Reviews need moderation by default
            )
            
            # Add images if provided
            if images:
                from .models import ReviewImage
                for i, image in enumerate(images):
                    ReviewImage.objects.create(
                        review=review,
                        image=image,
                        sort_order=i
                    )
        
        return review
    
    @staticmethod
    def update_review(review, **kwargs):
        """
        Update an existing review.
        
        Args:
            review: Review instance
            **kwargs: Fields to update
            
        Returns:
            Review instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Only allow updates if review is not approved yet
        if review.status == 'approved':
            raise ValidationError("Cannot update an approved review")
        
        # Validate rating if provided
        if 'rating' in kwargs:
            rating = kwargs['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                raise ValidationError("Rating must be between 1 and 5")
        
        # Update fields
        for field, value in kwargs.items():
            if hasattr(review, field):
                if field in ['title', 'comment', 'pros', 'cons'] and isinstance(value, str):
                    setattr(review, field, value.strip())
                else:
                    setattr(review, field, value)
        
        # Reset status to pending if content changed
        content_fields = ['rating', 'title', 'comment', 'pros', 'cons']
        if any(field in kwargs for field in content_fields):
            review.status = 'pending'
            review.moderated_by = None
            review.moderated_at = None
            review.moderation_notes = ""
        
        review.save()
        return review
    
    @staticmethod
    def moderate_review(review, moderator, action, notes=""):
        """
        Moderate a review (approve, reject, or flag).
        
        Args:
            review: Review instance
            moderator: User instance (moderator)
            action: str ('approve', 'reject', 'flag')
            notes: str (optional moderation notes)
            
        Returns:
            Review instance
            
        Raises:
            ValidationError: If validation fails
        """
        if not review.can_be_moderated_by(moderator):
            raise ValidationError("You don't have permission to moderate this review")
        
        if action == 'approve':
            review.approve(moderator)
        elif action == 'reject':
            review.reject(moderator, notes)
        elif action == 'flag':
            review.flag(moderator, notes)
        else:
            raise ValidationError("Invalid moderation action")
        
        return review
    
    @staticmethod
    def vote_review_helpfulness(user, review, vote):
        """
        Vote on review helpfulness.
        
        Args:
            user: User instance
            review: Review instance
            vote: str ('helpful' or 'not_helpful')
            
        Returns:
            ReviewHelpfulness instance
            
        Raises:
            ValidationError: If validation fails
        """
        if user == review.user:
            raise ValidationError("You cannot vote on your own review")
        
        if vote not in ['helpful', 'not_helpful']:
            raise ValidationError("Invalid vote type")
        
        # Update or create vote
        helpfulness, created = ReviewHelpfulness.objects.update_or_create(
            user=user,
            review=review,
            defaults={'vote': vote}
        )
        
        return helpfulness
    
    @staticmethod
    def report_review(reporter, review, reason, description=""):
        """
        Report a review for inappropriate content.
        
        Args:
            reporter: User instance
            review: Review instance
            reason: str (report reason)
            description: str (optional description)
            
        Returns:
            ReviewReport instance
            
        Raises:
            ValidationError: If validation fails
        """
        if reporter == review.user:
            raise ValidationError("You cannot report your own review")
        
        # Check if user already reported this review
        existing_report = ReviewReport.objects.filter(
            reporter=reporter,
            review=review
        ).first()
        
        if existing_report:
            raise ValidationError("You have already reported this review")
        
        report = ReviewReport.objects.create(
            reporter=reporter,
            review=review,
            reason=reason,
            description=description.strip()
        )
        
        return report
    
    @staticmethod
    def get_product_reviews(product, status='approved', user=None, page=1, per_page=10):
        """
        Get reviews for a product with pagination and filtering.
        
        Args:
            product: Product instance
            status: str (review status filter)
            user: User instance (optional, for filtering user's reviews)
            page: int (page number)
            per_page: int (reviews per page)
            
        Returns:
            dict: {
                'reviews': QuerySet,
                'total_count': int,
                'page': int,
                'per_page': int,
                'has_next': bool,
                'has_previous': bool
            }
        """
        queryset = Review.objects.filter(product=product)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if user:
            queryset = queryset.filter(user=user)
        
        # Order by helpfulness and date
        queryset = queryset.order_by('-helpful_count', '-created_at')
        
        # Pagination
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        reviews = queryset[start:end]
        
        return {
            'reviews': reviews,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_next': end < total_count,
            'has_previous': page > 1
        }
    
    @staticmethod
    def get_review_analytics(product=None, user=None, date_from=None, date_to=None):
        """
        Get review analytics and statistics.
        
        Args:
            product: Product instance (optional)
            user: User instance (optional)
            date_from: datetime (optional)
            date_to: datetime (optional)
            
        Returns:
            dict: Analytics data
        """
        queryset = Review.objects.filter(status='approved')
        
        if product:
            queryset = queryset.filter(product=product)
        
        if user:
            queryset = queryset.filter(user=user)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Basic statistics
        stats = queryset.aggregate(
            total_reviews=Count('id'),
            average_rating=Avg('rating'),
            rating_1_count=Count('id', filter=Q(rating=1)),
            rating_2_count=Count('id', filter=Q(rating=2)),
            rating_3_count=Count('id', filter=Q(rating=3)),
            rating_4_count=Count('id', filter=Q(rating=4)),
            rating_5_count=Count('id', filter=Q(rating=5)),
        )
        
        # Calculate percentages
        total = stats['total_reviews'] or 1
        rating_distribution = {
            5: round((stats['rating_5_count'] / total) * 100, 1),
            4: round((stats['rating_4_count'] / total) * 100, 1),
            3: round((stats['rating_3_count'] / total) * 100, 1),
            2: round((stats['rating_2_count'] / total) * 100, 1),
            1: round((stats['rating_1_count'] / total) * 100, 1),
        }
        
        return {
            'total_reviews': stats['total_reviews'],
            'average_rating': round(stats['average_rating'] or 0, 2),
            'rating_distribution': rating_distribution,
            'rating_counts': {
                5: stats['rating_5_count'],
                4: stats['rating_4_count'],
                3: stats['rating_3_count'],
                2: stats['rating_2_count'],
                1: stats['rating_1_count'],
            }
        }


class ReviewModerationService:
    """
    Service class for review moderation functionality.
    """
    
    @staticmethod
    def get_pending_reviews(page=1, per_page=20):
        """
        Get pending reviews for moderation.
        
        Args:
            page: int (page number)
            per_page: int (reviews per page)
            
        Returns:
            dict: Paginated pending reviews
        """
        queryset = Review.objects.filter(status='pending').order_by('created_at')
        
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        reviews = queryset[start:end]
        
        return {
            'reviews': reviews,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_next': end < total_count,
            'has_previous': page > 1
        }
    
    @staticmethod
    def get_flagged_reviews(page=1, per_page=20):
        """
        Get flagged reviews for moderation.
        
        Args:
            page: int (page number)
            per_page: int (reviews per page)
            
        Returns:
            dict: Paginated flagged reviews
        """
        queryset = Review.objects.filter(status='flagged').order_by('created_at')
        
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        reviews = queryset[start:end]
        
        return {
            'reviews': reviews,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_next': end < total_count,
            'has_previous': page > 1
        }
    
    @staticmethod
    def get_reported_reviews(page=1, per_page=20):
        """
        Get reviews with pending reports.
        
        Args:
            page: int (page number)
            per_page: int (reviews per page)
            
        Returns:
            dict: Paginated reported reviews
        """
        queryset = ReviewReport.objects.filter(
            status='pending'
        ).select_related('review', 'reporter').order_by('created_at')
        
        total_count = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        reports = queryset[start:end]
        
        return {
            'reports': reports,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_next': end < total_count,
            'has_previous': page > 1
        }
    
    @staticmethod
    def bulk_moderate_reviews(review_ids, moderator, action, notes=""):
        """
        Bulk moderate multiple reviews.
        
        Args:
            review_ids: list of review IDs
            moderator: User instance
            action: str ('approve', 'reject', 'flag')
            notes: str (optional moderation notes)
            
        Returns:
            dict: Results summary
        """
        reviews = Review.objects.filter(id__in=review_ids)
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for review in reviews:
            try:
                ReviewService.moderate_review(review, moderator, action, notes)
                results['success'] += 1
            except ValidationError as e:
                results['failed'] += 1
                results['errors'].append(f"Review {review.id}: {str(e)}")
        
        return results
    
    @staticmethod
    def get_moderation_stats():
        """
        Get moderation statistics.
        
        Returns:
            dict: Moderation statistics
        """
        return {
            'pending_reviews': Review.objects.filter(status='pending').count(),
            'flagged_reviews': Review.objects.filter(status='flagged').count(),
            'pending_reports': ReviewReport.objects.filter(status='pending').count(),
            'approved_reviews': Review.objects.filter(status='approved').count(),
            'rejected_reviews': Review.objects.filter(status='rejected').count(),
        }