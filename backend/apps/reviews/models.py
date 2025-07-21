"""
Review models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel


class Review(BaseModel):
    """
    Product review model with rating system and verification.
    """
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]
    
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        help_text="Order item that verifies the purchase"
    )
    
    # Review content
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Verification and moderation
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="True if the reviewer purchased the product"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)
    
    # Helpfulness tracking
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    
    # Additional metadata
    pros = models.TextField(blank=True, help_text="What the reviewer liked")
    cons = models.TextField(blank=True, help_text="What the reviewer didn't like")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['rating', 'status']),
            models.Index(fields=['is_verified_purchase', 'status']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_review_per_user_per_product'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        # Auto-verify purchase if order_item is provided
        if self.order_item and not self.is_verified_purchase:
            self.is_verified_purchase = True
        
        # Set moderated_at timestamp when status changes to approved/rejected
        if self.pk:
            old_review = Review.objects.get(pk=self.pk)
            if old_review.status != self.status and self.status in ['approved', 'rejected']:
                self.moderated_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update product rating aggregation after saving
        self.product.update_rating_aggregation()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        # Update product rating aggregation after deletion
        product.update_rating_aggregation()

    @property
    def helpfulness_score(self):
        """Calculate helpfulness score as a percentage."""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0
        return round((self.helpful_count / total_votes) * 100, 1)

    def can_be_moderated_by(self, user):
        """Check if a user can moderate this review."""
        return user.is_staff or user.user_type == 'admin'

    def approve(self, moderator=None):
        """Approve the review."""
        self.status = 'approved'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save()

    def reject(self, moderator=None, notes=""):
        """Reject the review."""
        self.status = 'rejected'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_notes = notes
        self.save()

    def flag(self, moderator=None, notes=""):
        """Flag the review for further review."""
        self.status = 'flagged'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_notes = notes
        self.save()


class ReviewHelpfulness(BaseModel):
    """
    Track user votes on review helpfulness.
    """
    VOTE_CHOICES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    ]
    
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='helpfulness_votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='review_votes'
    )
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['review', 'user'],
                name='unique_vote_per_user_per_review'
            )
        ]
        indexes = [
            models.Index(fields=['review', 'vote']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.review.id} ({self.vote})"

    def save(self, *args, **kwargs):
        # Update review helpfulness counts
        if self.pk:
            # Get old vote to update counts correctly
            old_vote = ReviewHelpfulness.objects.get(pk=self.pk)
            if old_vote.vote != self.vote:
                # Remove old vote count
                if old_vote.vote == 'helpful':
                    self.review.helpful_count = max(0, self.review.helpful_count - 1)
                else:
                    self.review.not_helpful_count = max(0, self.review.not_helpful_count - 1)
                
                # Add new vote count
                if self.vote == 'helpful':
                    self.review.helpful_count += 1
                else:
                    self.review.not_helpful_count += 1
                
                self.review.save()
        else:
            # New vote
            if self.vote == 'helpful':
                self.review.helpful_count += 1
            else:
                self.review.not_helpful_count += 1
            self.review.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Update review helpfulness counts
        if self.vote == 'helpful':
            self.review.helpful_count = max(0, self.review.helpful_count - 1)
        else:
            self.review.not_helpful_count = max(0, self.review.not_helpful_count - 1)
        self.review.save()
        
        super().delete(*args, **kwargs)


class ReviewImage(BaseModel):
    """
    Images attached to reviews.
    """
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='reviews/')
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['review', 'sort_order']),
        ]

    def __str__(self):
        return f"Review {self.review.id} - Image {self.sort_order}"


class ReviewReport(BaseModel):
    """
    User reports for inappropriate reviews.
    """
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('irrelevant', 'Irrelevant to Product'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='review_reports'
    )
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['review', 'reporter'],
                name='unique_report_per_user_per_review'
            )
        ]
        indexes = [
            models.Index(fields=['review', 'status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Report by {self.reporter.email} for Review {self.review.id}"

    def resolve(self, reviewer=None, notes=""):
        """Mark the report as resolved."""
        self.status = 'resolved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.resolution_notes = notes
        self.save()

    def dismiss(self, reviewer=None, notes=""):
        """Dismiss the report."""
        self.status = 'dismissed'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.resolution_notes = notes
        self.save()