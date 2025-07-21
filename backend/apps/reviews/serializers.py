"""
Serializers for the reviews app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.products.models import Product
from .models import Review, ReviewHelpfulness, ReviewImage, ReviewReport
from .services import ReviewService

User = get_user_model()


class ReviewImageSerializer(serializers.ModelSerializer):
    """
    Serializer for review images.
    """
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewUserSerializer(serializers.ModelSerializer):
    """
    Serializer for user information in reviews.
    """
    full_name = serializers.ReadOnlyField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar_url']
        read_only_fields = ['id', 'username', 'full_name', 'avatar_url']
    
    def get_avatar_url(self, obj):
        """Get user avatar URL."""
        return obj.get_avatar_url()


class ReviewProductSerializer(serializers.ModelSerializer):
    """
    Serializer for product information in reviews.
    """
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'primary_image']
        read_only_fields = ['id', 'name', 'slug', 'primary_image']
    
    def get_primary_image(self, obj):
        """Get primary product image."""
        primary_image = obj.primary_image
        if primary_image:
            return {
                'id': primary_image.id,
                'image': primary_image.image.url if primary_image.image else None,
                'alt_text': primary_image.alt_text
            }
        return None


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reviews.
    """
    user = ReviewUserSerializer(read_only=True)
    product = ReviewProductSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    helpfulness_score = serializers.ReadOnlyField()
    user_vote = serializers.SerializerMethodField()
    can_moderate = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product', 'rating', 'title', 'comment', 'pros', 'cons',
            'is_verified_purchase', 'status', 'helpful_count', 'not_helpful_count',
            'helpfulness_score', 'images', 'user_vote', 'can_moderate', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'product', 'is_verified_purchase', 'status',
            'helpful_count', 'not_helpful_count', 'helpfulness_score',
            'user_vote', 'can_moderate', 'created_at'
        ]
    
    def get_user_vote(self, obj):
        """Get current user's vote on this review."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = ReviewHelpfulness.objects.filter(
                review=obj, user=request.user
            ).first()
            return vote.vote if vote else None
        return None
    
    def get_can_moderate(self, obj):
        """Check if current user can moderate this review."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_moderated_by(request.user)
        return False


class ReviewDetailSerializer(ReviewListSerializer):
    """
    Serializer for detailed review view.
    """
    moderated_by = ReviewUserSerializer(read_only=True)
    
    class Meta(ReviewListSerializer.Meta):
        fields = ReviewListSerializer.Meta.fields + [
            'moderated_by', 'moderated_at', 'moderation_notes'
        ]
        read_only_fields = ReviewListSerializer.Meta.read_only_fields + [
            'moderated_by', 'moderated_at', 'moderation_notes'
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews.
    """
    images = ReviewImageSerializer(many=True, required=False)
    
    class Meta:
        model = Review
        fields = [
            'product', 'rating', 'title', 'comment', 'pros', 'cons', 'images'
        ]
    
    def validate(self, attrs):
        """Validate review creation."""
        user = self.context['request'].user
        product = attrs['product']
        
        # Check if user can review this product
        can_review, reason, order_item = ReviewService.can_user_review_product(user, product)
        if not can_review:
            raise serializers.ValidationError(reason)
        
        # Store order_item for later use
        attrs['_order_item'] = order_item
        return attrs
    
    def create(self, validated_data):
        """Create a new review."""
        images_data = validated_data.pop('images', [])
        order_item = validated_data.pop('_order_item')
        user = self.context['request'].user
        
        # Create review using service
        review = ReviewService.create_review(
            user=user,
            product=validated_data['product'],
            rating=validated_data['rating'],
            title=validated_data['title'],
            comment=validated_data['comment'],
            pros=validated_data.get('pros', ''),
            cons=validated_data.get('cons', ''),
        )
        
        # Create images
        for image_data in images_data:
            ReviewImage.objects.create(review=review, **image_data)
        
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating reviews.
    """
    images = ReviewImageSerializer(many=True, required=False)
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment', 'pros', 'cons', 'images']
    
    def validate(self, attrs):
        """Validate review update."""
        if self.instance.status == 'approved':
            raise serializers.ValidationError("Cannot update an approved review")
        return attrs
    
    def update(self, instance, validated_data):
        """Update review."""
        images_data = validated_data.pop('images', None)
        
        # Update review using service
        updated_review = ReviewService.update_review(instance, **validated_data)
        
        # Update images if provided
        if images_data is not None:
            # Delete existing images
            instance.images.all().delete()
            # Create new images
            for image_data in images_data:
                ReviewImage.objects.create(review=instance, **image_data)
        
        return updated_review


class ReviewModerationSerializer(serializers.Serializer):
    """
    Serializer for review moderation.
    """
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('flag', 'Flag'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate moderation action."""
        review = self.context['review']
        user = self.context['request'].user
        
        if not review.can_be_moderated_by(user):
            raise serializers.ValidationError("You don't have permission to moderate this review")
        
        return attrs


class BulkModerationSerializer(serializers.Serializer):
    """
    Serializer for bulk review moderation.
    """
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('flag', 'Flag'),
    ]
    
    review_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReviewHelpfulnessSerializer(serializers.ModelSerializer):
    """
    Serializer for review helpfulness votes.
    """
    class Meta:
        model = ReviewHelpfulness
        fields = ['id', 'vote', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        """Validate helpfulness vote."""
        user = self.context['request'].user
        review = self.context['review']
        
        if user == review.user:
            raise serializers.ValidationError("You cannot vote on your own review")
        
        return attrs


class ReviewReportSerializer(serializers.ModelSerializer):
    """
    Serializer for review reports.
    """
    reporter = ReviewUserSerializer(read_only=True)
    review = ReviewDetailSerializer(read_only=True)
    
    class Meta:
        model = ReviewReport
        fields = [
            'id', 'review', 'reporter', 'reason', 'description', 'status',
            'reviewed_by', 'reviewed_at', 'resolution_notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'review', 'reporter', 'status', 'reviewed_by',
            'reviewed_at', 'resolution_notes', 'created_at'
        ]
    
    def validate(self, attrs):
        """Validate report creation."""
        user = self.context['request'].user
        review = self.context['review']
        
        if user == review.user:
            raise serializers.ValidationError("You cannot report your own review")
        
        # Check if user already reported this review
        if ReviewReport.objects.filter(reporter=user, review=review).exists():
            raise serializers.ValidationError("You have already reported this review")
        
        return attrs


class ReviewReportResolutionSerializer(serializers.Serializer):
    """
    Serializer for resolving review reports.
    """
    ACTION_CHOICES = [
        ('resolve', 'Resolve'),
        ('dismiss', 'Dismiss'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReviewAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for review analytics.
    """
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    rating_counts = serializers.DictField()


class ProductReviewSummarySerializer(serializers.Serializer):
    """
    Serializer for product review summary.
    """
    product_id = serializers.UUIDField()
    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    recent_reviews = ReviewListSerializer(many=True)
    verified_purchase_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ModerationStatsSerializer(serializers.Serializer):
    """
    Serializer for moderation statistics.
    """
    pending_reviews = serializers.IntegerField()
    flagged_reviews = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    approved_reviews = serializers.IntegerField()
    rejected_reviews = serializers.IntegerField()