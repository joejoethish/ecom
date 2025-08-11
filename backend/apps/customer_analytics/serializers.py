from rest_framework import serializers
from .models import (
    CustomerSegment,
    CustomerAnalytics,
    CustomerBehaviorEvent,
    CustomerCohort,
    CustomerLifecycleStage,
    CustomerRecommendation,
    CustomerSatisfactionSurvey,
    CustomerLifetimeValue,
    CustomerChurnPrediction,
    CustomerJourneyMap,
    CustomerProfitabilityAnalysis,
    CustomerEngagementScore,
    CustomerPreferenceAnalysis,
    CustomerDemographicAnalysis,
    CustomerSentimentAnalysis,
    CustomerFeedbackAnalysis,
    CustomerRiskAssessment
)


class CustomerSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSegment
        fields = '__all__'


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    segment_name = serializers.CharField(source='segment.name', read_only=True)
    
    class Meta:
        model = CustomerAnalytics
        fields = '__all__'


class CustomerBehaviorEventSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerBehaviorEvent
        fields = '__all__'


class CustomerCohortSerializer(serializers.ModelSerializer):
    retention_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerCohort
        fields = '__all__'


class CustomerLifecycleStageSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerLifecycleStage
        fields = '__all__'


class CustomerRecommendationSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    click_through_rate = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerRecommendation
        fields = '__all__'


class CustomerSatisfactionSurveySerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    normalized_score = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerSatisfactionSurvey
        fields = '__all__'


class CustomerAnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for customer analytics summary data"""
    total_customers = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    active_customers = serializers.IntegerField()
    at_risk_customers = serializers.IntegerField()
    churned_customers = serializers.IntegerField()
    average_customer_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    customer_retention_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    nps_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    csat_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)


class CustomerLifetimeValueSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    clv_to_cac_ratio = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerLifetimeValue
        fields = '__all__'


class CustomerChurnPredictionSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerChurnPrediction
        fields = '__all__'


class CustomerJourneyMapSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerJourneyMap
        fields = '__all__'


class CustomerProfitabilityAnalysisSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    roi = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerProfitabilityAnalysis
        fields = '__all__'


class CustomerEngagementScoreSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerEngagementScore
        fields = '__all__'


class CustomerPreferenceAnalysisSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerPreferenceAnalysis
        fields = '__all__'


class CustomerDemographicAnalysisSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerDemographicAnalysis
        fields = '__all__'


class CustomerSentimentAnalysisSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerSentimentAnalysis
        fields = '__all__'


class CustomerFeedbackAnalysisSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerFeedbackAnalysis
        fields = '__all__'


class CustomerRiskAssessmentSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = CustomerRiskAssessment
        fields = '__all__'