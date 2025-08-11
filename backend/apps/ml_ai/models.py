from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class MLModel(models.Model):
    """Base model for ML models and their metadata"""
    MODEL_TYPES = [
        ('demand_forecasting', 'Demand Forecasting'),
        ('customer_segmentation', 'Customer Segmentation'),
        ('fraud_detection', 'Fraud Detection'),
        ('recommendation', 'Recommendation Engine'),
        ('pricing_optimization', 'Pricing Optimization'),
        ('churn_prediction', 'Churn Prediction'),
        ('quality_control', 'Quality Control'),
        ('supply_chain', 'Supply Chain Optimization'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('image_recognition', 'Image Recognition'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('predictive_maintenance', 'Predictive Maintenance'),
        ('nlp', 'Natural Language Processing'),
        ('voice_recognition', 'Voice Recognition'),
    ]
    
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deprecated', 'Deprecated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    version = models.CharField(max_length=20, default='1.0.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    description = models.TextField()
    
    # Model configuration
    parameters = models.JSONField(default=dict)
    hyperparameters = models.JSONField(default=dict)
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    
    # File paths
    model_file_path = models.CharField(max_length=500, blank=True)
    training_data_path = models.CharField(max_length=500, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ml_models'
        ordering = ['-created_at']


class MLPrediction(models.Model):
    """Store ML predictions and their results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    
    # Generic foreign key to link to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    input_data = models.JSONField()
    prediction_result = models.JSONField()
    confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ml_predictions'
        ordering = ['-created_at']


class DemandForecast(models.Model):
    """Demand forecasting predictions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.CharField(max_length=100)
    forecast_date = models.DateField()
    predicted_demand = models.IntegerField()
    confidence_interval_lower = models.IntegerField()
    confidence_interval_upper = models.IntegerField()
    actual_demand = models.IntegerField(null=True, blank=True)
    
    # Factors influencing the forecast
    seasonal_factor = models.FloatField(default=1.0)
    trend_factor = models.FloatField(default=1.0)
    promotional_factor = models.FloatField(default=1.0)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'demand_forecasts'
        unique_together = ['product_id', 'forecast_date']


class CustomerSegment(models.Model):
    """Customer segmentation results"""
    SEGMENT_TYPES = [
        ('high_value', 'High Value'),
        ('loyal', 'Loyal'),
        ('at_risk', 'At Risk'),
        ('new', 'New'),
        ('dormant', 'Dormant'),
        ('price_sensitive', 'Price Sensitive'),
        ('premium', 'Premium'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=100)
    segment_type = models.CharField(max_length=50, choices=SEGMENT_TYPES)
    segment_score = models.FloatField()
    
    # Segment characteristics
    characteristics = models.JSONField(default=dict)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_segments'
        unique_together = ['customer_id', 'segment_type']


class FraudDetection(models.Model):
    """Fraud detection results"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    risk_score = models.FloatField()
    
    # Risk factors
    risk_factors = models.JSONField(default=list)
    
    # Actions taken
    action_taken = models.CharField(max_length=100, blank=True)
    is_confirmed_fraud = models.BooleanField(null=True, blank=True)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fraud_detections'


class ProductRecommendation(models.Model):
    """Product recommendation results"""
    RECOMMENDATION_TYPES = [
        ('collaborative', 'Collaborative Filtering'),
        ('content_based', 'Content-Based'),
        ('hybrid', 'Hybrid'),
        ('trending', 'Trending'),
        ('personalized', 'Personalized'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100)
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    score = models.FloatField()
    rank = models.IntegerField()
    
    # Context information
    context = models.JSONField(default=dict)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_recommendations'
        unique_together = ['customer_id', 'product_id', 'recommendation_type']


class PricingOptimization(models.Model):
    """Dynamic pricing optimization results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    optimized_price = models.DecimalField(max_digits=10, decimal_places=2)
    expected_demand = models.IntegerField()
    expected_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Pricing factors
    competitor_prices = models.JSONField(default=dict)
    demand_elasticity = models.FloatField()
    inventory_level = models.IntegerField()
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'pricing_optimizations'


class ChurnPrediction(models.Model):
    """Customer churn prediction results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=100)
    churn_probability = models.FloatField()
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ])
    
    # Churn factors
    churn_factors = models.JSONField(default=list)
    
    # Retention recommendations
    retention_actions = models.JSONField(default=list)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'churn_predictions'


class SentimentAnalysis(models.Model):
    """Sentiment analysis results"""
    SENTIMENT_TYPES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('mixed', 'Mixed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text_content = models.TextField()
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_TYPES)
    confidence_score = models.FloatField()
    
    # Detailed sentiment scores
    positive_score = models.FloatField()
    negative_score = models.FloatField()
    neutral_score = models.FloatField()
    
    # Source information
    source_type = models.CharField(max_length=50)  # review, social_media, support_ticket
    source_id = models.CharField(max_length=100)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sentiment_analysis'


class AnomalyDetection(models.Model):
    """Anomaly detection results"""
    ANOMALY_TYPES = [
        ('sales', 'Sales Anomaly'),
        ('inventory', 'Inventory Anomaly'),
        ('user_behavior', 'User Behavior Anomaly'),
        ('system', 'System Anomaly'),
        ('financial', 'Financial Anomaly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPES)
    anomaly_score = models.FloatField()
    threshold = models.FloatField()
    
    # Anomaly details
    data_point = models.JSONField()
    expected_value = models.FloatField(null=True, blank=True)
    actual_value = models.FloatField()
    
    # Context
    context = models.JSONField(default=dict)
    
    # Actions
    is_investigated = models.BooleanField(default=False)
    investigation_notes = models.TextField(blank=True)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'anomaly_detections'


class MLTrainingJob(models.Model):
    """Track ML model training jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='training_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Training configuration
    training_config = models.JSONField(default=dict)
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0)
    current_epoch = models.IntegerField(default=0)
    total_epochs = models.IntegerField(default=100)
    
    # Results
    training_metrics = models.JSONField(default=dict)
    validation_metrics = models.JSONField(default=dict)
    
    # Logs
    log_file_path = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ml_training_jobs'
        ordering = ['-created_at']


class AIInsight(models.Model):
    """Store AI-generated business insights"""
    INSIGHT_TYPES = [
        ('sales_trend', 'Sales Trend'),
        ('customer_behavior', 'Customer Behavior'),
        ('inventory_optimization', 'Inventory Optimization'),
        ('pricing_strategy', 'Pricing Strategy'),
        ('market_opportunity', 'Market Opportunity'),
        ('risk_assessment', 'Risk Assessment'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    
    description = models.TextField()
    recommendations = models.JSONField(default=list)
    supporting_data = models.JSONField(default=dict)
    
    # Impact assessment
    potential_impact = models.TextField()
    confidence_level = models.FloatField()
    
    # Status
    is_reviewed = models.BooleanField(default=False)
    is_implemented = models.BooleanField(default=False)
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_insights'
        ordering = ['-priority', '-created_at']