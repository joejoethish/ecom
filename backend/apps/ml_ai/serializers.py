from rest_framework import serializers
from .models import *


class MLModelSerializer(serializers.ModelSerializer):
    """Serializer for ML models"""
    
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'model_type', 'version', 'status', 'description',
            'parameters', 'hyperparameters', 'accuracy', 'precision', 'recall',
            'f1_score', 'created_by', 'created_at', 'updated_at', 'last_trained'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MLPredictionSerializer(serializers.ModelSerializer):
    """Serializer for ML predictions"""
    
    class Meta:
        model = MLPrediction
        fields = [
            'id', 'model', 'content_type', 'object_id', 'input_data',
            'prediction_result', 'confidence_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DemandForecastSerializer(serializers.ModelSerializer):
    """Serializer for demand forecasts"""
    
    class Meta:
        model = DemandForecast
        fields = [
            'id', 'product_id', 'forecast_date', 'predicted_demand',
            'confidence_interval_lower', 'confidence_interval_upper',
            'actual_demand', 'seasonal_factor', 'trend_factor',
            'promotional_factor', 'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CustomerSegmentSerializer(serializers.ModelSerializer):
    """Serializer for customer segments"""
    
    class Meta:
        model = CustomerSegment
        fields = [
            'id', 'customer_id', 'segment_type', 'segment_score',
            'characteristics', 'model', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FraudDetectionSerializer(serializers.ModelSerializer):
    """Serializer for fraud detection results"""
    
    class Meta:
        model = FraudDetection
        fields = [
            'id', 'transaction_id', 'risk_level', 'risk_score',
            'risk_factors', 'action_taken', 'is_confirmed_fraud',
            'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for product recommendations"""
    
    class Meta:
        model = ProductRecommendation
        fields = [
            'id', 'customer_id', 'product_id', 'recommendation_type',
            'score', 'rank', 'context', 'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PricingOptimizationSerializer(serializers.ModelSerializer):
    """Serializer for pricing optimization"""
    
    class Meta:
        model = PricingOptimization
        fields = [
            'id', 'product_id', 'current_price', 'optimized_price',
            'expected_demand', 'expected_revenue', 'competitor_prices',
            'demand_elasticity', 'inventory_level', 'model',
            'created_at', 'applied_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChurnPredictionSerializer(serializers.ModelSerializer):
    """Serializer for churn predictions"""
    
    class Meta:
        model = ChurnPrediction
        fields = [
            'id', 'customer_id', 'churn_probability', 'risk_level',
            'churn_factors', 'retention_actions', 'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SentimentAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for sentiment analysis"""
    
    class Meta:
        model = SentimentAnalysis
        fields = [
            'id', 'text_content', 'sentiment', 'confidence_score',
            'positive_score', 'negative_score', 'neutral_score',
            'source_type', 'source_id', 'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Serializer for anomaly detection"""
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'anomaly_type', 'anomaly_score', 'threshold',
            'data_point', 'expected_value', 'actual_value', 'context',
            'is_investigated', 'investigation_notes', 'model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MLTrainingJobSerializer(serializers.ModelSerializer):
    """Serializer for ML training jobs"""
    
    class Meta:
        model = MLTrainingJob
        fields = [
            'id', 'model', 'status', 'training_config', 'progress_percentage',
            'current_epoch', 'total_epochs', 'training_metrics',
            'validation_metrics', 'log_file_path', 'error_message',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer for AI insights"""
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'title', 'insight_type', 'priority', 'description',
            'recommendations', 'supporting_data', 'potential_impact',
            'confidence_level', 'is_reviewed', 'is_implemented',
            'model', 'created_at', 'reviewed_at'
        ]
        read_only_fields = ['id', 'created_at']


# Request/Response Serializers for API endpoints

class DemandForecastRequestSerializer(serializers.Serializer):
    """Serializer for demand forecast requests"""
    product_id = serializers.CharField(max_length=100)
    forecast_days = serializers.IntegerField(default=30, min_value=1, max_value=365)


class DemandForecastResponseSerializer(serializers.Serializer):
    """Serializer for demand forecast responses"""
    date = serializers.DateField()
    predicted_demand = serializers.IntegerField()
    confidence_lower = serializers.IntegerField()
    confidence_upper = serializers.IntegerField()


class CustomerSegmentationRequestSerializer(serializers.Serializer):
    """Serializer for customer segmentation requests"""
    customer_id = serializers.CharField(max_length=100, required=False)
    total_orders = serializers.IntegerField()
    total_spent = serializers.FloatField()
    avg_order_value = serializers.FloatField()
    days_since_last_order = serializers.IntegerField()
    lifetime_days = serializers.IntegerField()
    return_rate = serializers.FloatField()


class CustomerSegmentationResponseSerializer(serializers.Serializer):
    """Serializer for customer segmentation responses"""
    cluster_id = serializers.IntegerField()
    segment_characteristics = serializers.CharField()


class FraudDetectionRequestSerializer(serializers.Serializer):
    """Serializer for fraud detection requests"""
    transaction_id = serializers.CharField(max_length=100)
    amount = serializers.FloatField()
    hour_of_day = serializers.IntegerField(min_value=0, max_value=23)
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    num_items = serializers.IntegerField(min_value=1)
    customer_age_days = serializers.IntegerField(min_value=0)
    payment_method = serializers.IntegerField(min_value=0, max_value=2)
    shipping_address_matches = serializers.BooleanField()


class FraudDetectionResponseSerializer(serializers.Serializer):
    """Serializer for fraud detection responses"""
    is_fraud_risk = serializers.BooleanField()
    risk_score = serializers.FloatField()
    risk_level = serializers.CharField()
    risk_factors = serializers.ListField(child=serializers.CharField())
    anomaly_score = serializers.FloatField()


class RecommendationRequestSerializer(serializers.Serializer):
    """Serializer for recommendation requests"""
    user_id = serializers.IntegerField()
    num_recommendations = serializers.IntegerField(default=10, min_value=1, max_value=50)


class RecommendationResponseSerializer(serializers.Serializer):
    """Serializer for recommendation responses"""
    product_id = serializers.IntegerField()
    score = serializers.FloatField()
    rank = serializers.IntegerField()
    reason = serializers.CharField()


class PricingOptimizationRequestSerializer(serializers.Serializer):
    """Serializer for pricing optimization requests"""
    product_id = serializers.CharField(max_length=100)
    current_price = serializers.FloatField()
    competitor_price = serializers.FloatField()
    inventory_level = serializers.IntegerField()
    is_weekend = serializers.BooleanField()
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)
    month = serializers.IntegerField(min_value=1, max_value=12)


class PricingOptimizationResponseSerializer(serializers.Serializer):
    """Serializer for pricing optimization responses"""
    current_price = serializers.FloatField()
    optimized_price = serializers.FloatField()
    current_demand = serializers.IntegerField()
    expected_demand = serializers.IntegerField()
    expected_revenue = serializers.FloatField()
    price_change_percent = serializers.FloatField()


class ChurnPredictionRequestSerializer(serializers.Serializer):
    """Serializer for churn prediction requests"""
    customer_id = serializers.CharField(max_length=100)
    days_since_signup = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_spent = serializers.FloatField()
    avg_order_value = serializers.FloatField()
    days_since_last_order = serializers.IntegerField()
    support_tickets = serializers.IntegerField()
    return_rate = serializers.FloatField()


class ChurnPredictionResponseSerializer(serializers.Serializer):
    """Serializer for churn prediction responses"""
    churn_probability = serializers.FloatField()
    risk_level = serializers.CharField()
    churn_factors = serializers.ListField(child=serializers.CharField())
    retention_actions = serializers.ListField(child=serializers.CharField())
    feature_importance = serializers.DictField()


class SentimentAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for sentiment analysis requests"""
    text = serializers.CharField()
    source_type = serializers.CharField(max_length=50, required=False)
    source_id = serializers.CharField(max_length=100, required=False)


class SentimentAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for sentiment analysis responses"""
    sentiment = serializers.CharField()
    confidence_score = serializers.FloatField()
    positive_score = serializers.FloatField()
    negative_score = serializers.FloatField()
    neutral_score = serializers.FloatField()
    text_length = serializers.IntegerField()
    word_count = serializers.IntegerField()


class AnomalyDetectionRequestSerializer(serializers.Serializer):
    """Serializer for anomaly detection requests"""
    sales = serializers.FloatField()
    orders = serializers.IntegerField()
    avg_order_value = serializers.FloatField()
    conversion_rate = serializers.FloatField()


class AnomalyDetectionResponseSerializer(serializers.Serializer):
    """Serializer for anomaly detection responses"""
    is_anomaly = serializers.BooleanField()
    anomaly_score = serializers.FloatField()
    anomaly_type = serializers.CharField()
    severity = serializers.CharField()
    threshold = serializers.FloatField()
    metrics = serializers.DictField()
    timestamp = serializers.CharField()


class ModelTrainingRequestSerializer(serializers.Serializer):
    """Serializer for model training requests"""
    model_type = serializers.ChoiceField(choices=[
        'demand_forecasting', 'customer_segmentation', 'fraud_detection',
        'recommendation', 'pricing_optimization', 'churn_prediction',
        'sentiment_analysis', 'anomaly_detection'
    ])
    parameters = serializers.DictField(default=dict)
    hyperparameters = serializers.DictField(default=dict)


class ModelTrainingResponseSerializer(serializers.Serializer):
    """Serializer for model training responses"""
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    message = serializers.CharField()


class AIInsightsResponseSerializer(serializers.Serializer):
    """Serializer for AI insights responses"""
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.CharField()
    recommendations = serializers.ListField(child=serializers.CharField())
    confidence = serializers.FloatField()