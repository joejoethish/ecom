from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json


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


class CustomerLifetimeValue(models.Model):
    """Advanced CLV calculation and tracking"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clv_data')
    
    # CLV Components
    historical_clv = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    predicted_clv = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Purchase behavior metrics
    purchase_frequency = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))  # purchases per period
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    customer_lifespan = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))  # in months
    
    # Profitability metrics
    gross_margin_per_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    customer_acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement metrics
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    loyalty_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    
    # Prediction confidence
    prediction_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    model_version = models.CharField(max_length=20, default='v1.0')
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    next_calculation_due = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_customer_lifetime_value'
    
    def __str__(self):
        return f"CLV for {self.customer.username}: ${self.predicted_clv}"
    
    @property
    def clv_to_cac_ratio(self):
        """Calculate CLV to CAC ratio"""
        if self.customer_acquisition_cost > 0:
            return self.predicted_clv / self.customer_acquisition_cost
        return Decimal('0.00')


class CustomerChurnPrediction(models.Model):
    """ML-based churn prediction model"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='churn_prediction')
    
    # Churn probability
    churn_probability = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))  # 0-1
    churn_risk_level = models.CharField(max_length=10, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], default='low')
    
    # Feature importance scores
    recency_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    frequency_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    monetary_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    satisfaction_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Model metadata
    model_version = models.CharField(max_length=20, default='v1.0')
    prediction_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    feature_vector = models.JSONField(default=dict)  # Store all features used
    
    # Intervention tracking
    intervention_recommended = models.BooleanField(default=False)
    intervention_applied = models.BooleanField(default=False)
    intervention_type = models.CharField(max_length=50, blank=True)
    intervention_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    predicted_at = models.DateTimeField(auto_now=True)
    next_prediction_due = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_customer_churn_prediction'
    
    def __str__(self):
        return f"Churn prediction for {self.customer.username}: {self.churn_probability:.2%}"


class CustomerJourneyMap(models.Model):
    """Customer journey mapping and touchpoint analysis"""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journey_maps')
    
    # Journey identification
    journey_id = models.CharField(max_length=100)  # Unique identifier for this journey
    journey_type = models.CharField(max_length=50, choices=[
        ('acquisition', 'Customer Acquisition'),
        ('onboarding', 'Customer Onboarding'),
        ('purchase', 'Purchase Journey'),
        ('support', 'Support Journey'),
        ('retention', 'Retention Journey'),
        ('reactivation', 'Reactivation Journey')
    ])
    
    # Journey metadata
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('converted', 'Converted')
    ], default='active')
    
    # Journey metrics
    total_touchpoints = models.IntegerField(default=0)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    journey_duration = models.IntegerField(default=0)  # in minutes
    
    # Journey data
    touchpoints = models.JSONField(default=list)  # List of touchpoint data
    conversion_path = models.JSONField(default=list)  # Conversion attribution path
    
    class Meta:
        db_table = 'analytics_customer_journey_maps'
        indexes = [
            models.Index(fields=['customer', 'journey_type']),
            models.Index(fields=['start_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Journey {self.journey_id} for {self.customer.username}"


class CustomerProfitabilityAnalysis(models.Model):
    """Customer profitability analysis by segment and individual"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profitability')
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Cost metrics
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retention_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Profitability metrics
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # percentage
    
    # Profitability ranking
    profitability_rank = models.IntegerField(null=True, blank=True)
    profitability_percentile = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Time-based analysis
    monthly_profit_trend = models.JSONField(default=list)  # Monthly profit data
    quarterly_profit_trend = models.JSONField(default=list)  # Quarterly profit data
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    period_start = models.DateField()
    period_end = models.DateField()
    
    class Meta:
        db_table = 'analytics_customer_profitability'
    
    def __str__(self):
        return f"Profitability for {self.customer.username}: ${self.net_profit}"
    
    @property
    def roi(self):
        """Calculate return on investment"""
        if self.total_cost > 0:
            return (self.net_profit / self.total_cost) * 100
        return Decimal('0.00')


class CustomerEngagementScore(models.Model):
    """Customer engagement scoring and tracking"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement')
    
    # Overall engagement score
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    
    # Component scores
    website_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    email_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    social_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    purchase_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    support_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement metrics
    session_frequency = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    avg_session_duration = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))  # minutes
    page_views_per_session = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # percentage
    
    # Communication engagement
    email_open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    email_click_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    sms_response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement trend
    engagement_trend = models.CharField(max_length=20, choices=[
        ('increasing', 'Increasing'),
        ('stable', 'Stable'),
        ('decreasing', 'Decreasing'),
        ('volatile', 'Volatile')
    ], default='stable')
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer_engagement'
    
    def __str__(self):
        return f"Engagement for {self.customer.username}: {self.total_score}"


class CustomerPreferenceAnalysis(models.Model):
    """Customer preference analysis and recommendation engine data"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Product preferences
    preferred_categories = models.JSONField(default=list)  # Category IDs with scores
    preferred_brands = models.JSONField(default=list)  # Brand IDs with scores
    preferred_price_range = models.JSONField(default=dict)  # Min/max price preferences
    preferred_attributes = models.JSONField(default=dict)  # Product attributes preferences
    
    # Shopping behavior preferences
    preferred_shopping_times = models.JSONField(default=list)  # Time patterns
    preferred_channels = models.JSONField(default=list)  # Channel preferences
    preferred_payment_methods = models.JSONField(default=list)  # Payment preferences
    preferred_shipping_methods = models.JSONField(default=list)  # Shipping preferences
    
    # Communication preferences
    communication_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('never', 'Never')
    ], default='weekly')
    preferred_communication_channels = models.JSONField(default=list)
    
    # Recommendation engine data
    collaborative_filtering_data = models.JSONField(default=dict)
    content_based_data = models.JSONField(default=dict)
    hybrid_model_data = models.JSONField(default=dict)
    
    # Preference confidence scores
    category_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    brand_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    price_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer_preferences'
    
    def __str__(self):
        return f"Preferences for {self.customer.username}"


class CustomerDemographicAnalysis(models.Model):
    """Customer demographic and psychographic analysis"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='demographics')
    
    # Geographic data
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Demographic data
    age_group = models.CharField(max_length=20, choices=[
        ('18-24', '18-24'),
        ('25-34', '25-34'),
        ('35-44', '35-44'),
        ('45-54', '45-54'),
        ('55-64', '55-64'),
        ('65+', '65+')
    ], blank=True)
    gender = models.CharField(max_length=10, blank=True)
    income_bracket = models.CharField(max_length=20, choices=[
        ('low', 'Low Income'),
        ('middle', 'Middle Income'),
        ('high', 'High Income'),
        ('premium', 'Premium Income')
    ], blank=True)
    
    # Psychographic data
    lifestyle_segments = models.JSONField(default=list)  # Lifestyle categories
    interests = models.JSONField(default=list)  # Interest categories
    values = models.JSONField(default=list)  # Value propositions that resonate
    personality_traits = models.JSONField(default=dict)  # Big 5 personality traits
    
    # Behavioral segments
    shopping_personality = models.CharField(max_length=30, choices=[
        ('bargain_hunter', 'Bargain Hunter'),
        ('brand_loyalist', 'Brand Loyalist'),
        ('convenience_shopper', 'Convenience Shopper'),
        ('research_oriented', 'Research Oriented'),
        ('impulse_buyer', 'Impulse Buyer'),
        ('quality_seeker', 'Quality Seeker')
    ], blank=True)
    
    # Technology adoption
    device_preferences = models.JSONField(default=list)  # Mobile, desktop, tablet
    tech_savviness = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    
    # Data sources
    data_sources = models.JSONField(default=list)  # Where demographic data came from
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_customer_demographics'
    
    def __str__(self):
        return f"Demographics for {self.customer.username}"


class CustomerSentimentAnalysis(models.Model):
    """Social media sentiment analysis and monitoring"""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sentiment_analysis')
    
    # Sentiment data
    overall_sentiment = models.CharField(max_length=20, choices=[
        ('very_positive', 'Very Positive'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
        ('very_negative', 'Very Negative')
    ], default='neutral')
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))  # -1 to 1
    
    # Source data
    source_platform = models.CharField(max_length=50, choices=[
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('reviews', 'Product Reviews'),
        ('support_chat', 'Support Chat'),
        ('email', 'Email'),
        ('survey', 'Survey Response')
    ])
    content = models.TextField()
    content_type = models.CharField(max_length=20, choices=[
        ('post', 'Social Media Post'),
        ('comment', 'Comment'),
        ('review', 'Product Review'),
        ('message', 'Direct Message'),
        ('mention', 'Brand Mention')
    ])
    
    # Analysis metadata
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    keywords_extracted = models.JSONField(default=list)
    emotions_detected = models.JSONField(default=dict)  # Joy, anger, fear, etc.
    topics_identified = models.JSONField(default=list)
    
    # Engagement metrics
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    
    # Timestamps
    content_date = models.DateTimeField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_customer_sentiment'
        indexes = [
            models.Index(fields=['customer', 'overall_sentiment']),
            models.Index(fields=['source_platform', 'content_date']),
            models.Index(fields=['analyzed_at']),
        ]
    
    def __str__(self):
        return f"Sentiment for {self.customer.username}: {self.overall_sentiment}"


class CustomerFeedbackAnalysis(models.Model):
    """Customer feedback analysis with text mining and NLP"""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback_analysis')
    
    # Feedback source
    feedback_type = models.CharField(max_length=30, choices=[
        ('product_review', 'Product Review'),
        ('service_feedback', 'Service Feedback'),
        ('support_ticket', 'Support Ticket'),
        ('survey_response', 'Survey Response'),
        ('chat_transcript', 'Chat Transcript'),
        ('email_feedback', 'Email Feedback')
    ])
    source_id = models.CharField(max_length=100, blank=True)  # ID of the source record
    
    # Feedback content
    original_text = models.TextField()
    processed_text = models.TextField(blank=True)  # Cleaned and processed text
    language = models.CharField(max_length=10, default='en')
    
    # NLP Analysis results
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    emotion_scores = models.JSONField(default=dict)  # Emotion analysis results
    key_phrases = models.JSONField(default=list)  # Extracted key phrases
    named_entities = models.JSONField(default=list)  # Named entity recognition
    topics = models.JSONField(default=list)  # Topic modeling results
    
    # Classification results
    feedback_category = models.CharField(max_length=50, choices=[
        ('product_quality', 'Product Quality'),
        ('customer_service', 'Customer Service'),
        ('shipping_delivery', 'Shipping & Delivery'),
        ('pricing', 'Pricing'),
        ('website_usability', 'Website Usability'),
        ('payment_process', 'Payment Process'),
        ('return_policy', 'Return Policy'),
        ('general', 'General Feedback')
    ], blank=True)
    
    urgency_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='low')
    
    # Action items
    requires_response = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    action_description = models.TextField(blank=True)
    
    # Analysis metadata
    analysis_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    model_version = models.CharField(max_length=20, default='v1.0')
    
    # Timestamps
    feedback_date = models.DateTimeField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_customer_feedback'
        indexes = [
            models.Index(fields=['customer', 'feedback_type']),
            models.Index(fields=['feedback_category', 'urgency_level']),
            models.Index(fields=['feedback_date']),
        ]
    
    def __str__(self):
        return f"Feedback analysis for {self.customer.username} - {self.feedback_type}"


class CustomerRiskAssessment(models.Model):
    """Customer risk assessment and fraud detection"""
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='risk_assessment')
    
    # Overall risk score
    overall_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100
    risk_level = models.CharField(max_length=20, choices=[
        ('very_low', 'Very Low Risk'),
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk')
    ], default='low')
    
    # Risk component scores
    fraud_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    payment_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    chargeback_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    return_abuse_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Risk indicators
    suspicious_activities = models.JSONField(default=list)  # List of suspicious activities
    risk_factors = models.JSONField(default=dict)  # Risk factors and their weights
    protective_factors = models.JSONField(default=dict)  # Factors that reduce risk
    
    # Behavioral patterns
    unusual_purchase_patterns = models.BooleanField(default=False)
    velocity_violations = models.BooleanField(default=False)  # Too many orders too quickly
    geographic_anomalies = models.BooleanField(default=False)
    device_fingerprint_changes = models.BooleanField(default=False)
    
    # Historical data
    total_chargebacks = models.IntegerField(default=0)
    total_returns = models.IntegerField(default=0)
    failed_payment_attempts = models.IntegerField(default=0)
    account_age_days = models.IntegerField(default=0)
    
    # Actions taken
    monitoring_level = models.CharField(max_length=20, choices=[
        ('none', 'No Monitoring'),
        ('basic', 'Basic Monitoring'),
        ('enhanced', 'Enhanced Monitoring'),
        ('strict', 'Strict Monitoring')
    ], default='basic')
    
    restrictions_applied = models.JSONField(default=list)  # List of applied restrictions
    manual_review_required = models.BooleanField(default=False)
    
    # Timestamps
    last_assessment = models.DateTimeField(auto_now=True)
    next_assessment_due = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_customer_risk'
    
    def __str__(self):
        return f"Risk assessment for {self.customer.username}: {self.risk_level}"