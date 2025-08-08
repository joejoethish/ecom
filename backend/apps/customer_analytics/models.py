from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class CustomerSegment(models.Model):
    """Customer segmentation model for analytics"""
    SEGMENT_TYPES = [
        ('high_value', 'High Value'),
        ('frequent_buyer', 'Frequent Buyer'),
        ('at_risk', 'At Risk'),
        ('new_customer', 'New Customer'),
        ('loyal', 'Loyal Customer'),
        ('dormant', 'Dormant'),
    ]
    
    name = models.CharField(max_length=100)
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPES)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict)  # Store segmentation criteria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'analytics_customer_segments'
    
    def __str__(self):
        return f"{self.name} ({self.get_segment_type_display()})"


class CustomerAnalytics(models.Model):
    """Customer analytics and metrics model"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics')
    segment = models.ForeignKey(CustomerSegment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Purchase behavior metrics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    first_purchase_date = models.DateTimeField(null=True, blank=True)
    last_purchase_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    days_since_last_purchase = models.IntegerField(default=0)
    purchase_frequency = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # orders per month
    customer_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Behavioral indicators
    preferred_categories = models.JSONField(default=list)  # List of category IDs
    preferred_brands = models.JSONField(default=list)  # List of brand names
    shopping_patterns = models.JSONField(default=dict)  # Time-based shopping patterns
    
    # Risk indicators
    churn_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    satisfaction_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # 1-10
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer_analytics'
    
    def __str__(self):
        return f"Analytics for {self.customer.username}"
    
    def calculate_days_since_last_purchase(self):
        """Calculate days since last purchase"""
        if self.last_purchase_date:
            return (timezone.now() - self.last_purchase_date).days
        return 0
    
    def update_metrics(self):
        """Update customer metrics based on order history"""
        # This method should be implemented to calculate metrics
        # from the customer's order history
        pass


class CustomerBehaviorEvent(models.Model):
    """Track customer behavior events for analytics"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_start', 'Checkout Started'),
        ('checkout_complete', 'Checkout Completed'),
        ('search', 'Search'),
        ('wishlist_add', 'Added to Wishlist'),
        ('review_submit', 'Review Submitted'),
        ('support_contact', 'Support Contact'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='behavior_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict)  # Store event-specific data
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_customer_behavior_events'
        indexes = [
            models.Index(fields=['customer', 'event_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.get_event_type_display()}"


class CustomerCohort(models.Model):
    """Customer cohort analysis model"""
    name = models.CharField(max_length=100)
    cohort_date = models.DateField()  # Usually first purchase month
    description = models.TextField(blank=True)
    
    # Cohort metrics
    initial_customers = models.IntegerField(default=0)
    current_active_customers = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_customer_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer_cohorts'
        unique_together = ['cohort_date']
    
    def __str__(self):
        return f"Cohort {self.cohort_date.strftime('%Y-%m')}"
    
    @property
    def retention_rate(self):
        """Calculate retention rate"""
        if self.initial_customers > 0:
            return (self.current_active_customers / self.initial_customers) * 100
        return 0


class CustomerLifecycleStage(models.Model):
    """Customer lifecycle stage tracking"""
    LIFECYCLE_STAGES = [
        ('prospect', 'Prospect'),
        ('new', 'New Customer'),
        ('active', 'Active Customer'),
        ('at_risk', 'At Risk'),
        ('dormant', 'Dormant'),
        ('reactivated', 'Reactivated'),
        ('churned', 'Churned'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lifecycle_stages')
    stage = models.CharField(max_length=20, choices=LIFECYCLE_STAGES)
    stage_date = models.DateTimeField(auto_now_add=True)
    previous_stage = models.CharField(max_length=20, choices=LIFECYCLE_STAGES, blank=True)
    
    # Stage-specific metrics
    stage_duration = models.IntegerField(default=0)  # Days in current stage
    stage_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'analytics_customer_lifecycle_stages'
        indexes = [
            models.Index(fields=['customer', 'stage']),
            models.Index(fields=['stage_date']),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.get_stage_display()}"


class CustomerRecommendation(models.Model):
    """Store customer recommendations for analytics"""
    RECOMMENDATION_TYPES = [
        ('product', 'Product Recommendation'),
        ('category', 'Category Recommendation'),
        ('brand', 'Brand Recommendation'),
        ('cross_sell', 'Cross-sell'),
        ('up_sell', 'Up-sell'),
        ('reorder', 'Reorder Suggestion'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Recommendation data
    recommended_items = models.JSONField(default=list)  # List of product IDs or other items
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    algorithm_used = models.CharField(max_length=50, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Performance tracking
    views = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        db_table = 'analytics_customer_recommendations'
        indexes = [
            models.Index(fields=['customer', 'recommendation_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.customer.username} - {self.get_recommendation_type_display()}"
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.views > 0:
            return (self.clicks / self.views) * 100
        return 0
    
    @property
    def conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks > 0:
            return (self.conversions / self.clicks) * 100
        return 0


class CustomerSatisfactionSurvey(models.Model):
    """Customer satisfaction survey responses"""
    SURVEY_TYPES = [
        ('nps', 'Net Promoter Score'),
        ('csat', 'Customer Satisfaction'),
        ('ces', 'Customer Effort Score'),
        ('product_review', 'Product Review'),
        ('service_feedback', 'Service Feedback'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='satisfaction_surveys')
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPES)
    
    # Survey data
    score = models.IntegerField()  # Score value (scale depends on survey type)
    max_score = models.IntegerField(default=10)  # Maximum possible score
    feedback_text = models.TextField(blank=True)
    
    # Context
    order_id = models.CharField(max_length=50, blank=True)  # Related order if applicable
    product_id = models.CharField(max_length=50, blank=True)  # Related product if applicable
    
    # Metadata
    survey_date = models.DateTimeField(auto_now_add=True)
    response_time = models.IntegerField(null=True, blank=True)  # Time taken to respond in seconds
    
    class Meta:
        db_table = 'analytics_customer_satisfaction_surveys'
        indexes = [
            models.Index(fields=['customer', 'survey_type']),
            models.Index(fields=['survey_date']),
            models.Index(fields=['score']),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.get_survey_type_display()}: {self.score}/{self.max_score}"
    
    @property
    def normalized_score(self):
        """Get normalized score (0-100)"""
        return (self.score / self.max_score) * 100