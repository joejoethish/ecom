from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'models', MLModelViewSet)
router.register(r'training-jobs', MLTrainingJobViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Demand Forecasting
    path('demand-forecasting/train/', DemandForecastingViewSet.as_view({'post': 'train_model'}), name='demand-forecasting-train'),
    path('demand-forecasting/predict/', DemandForecastingViewSet.as_view({'post': 'predict'}), name='demand-forecasting-predict'),
    path('demand-forecasting/historical/', DemandForecastingViewSet.as_view({'get': 'historical_forecasts'}), name='demand-forecasting-historical'),
    
    # Customer Segmentation
    path('customer-segmentation/train/', CustomerSegmentationViewSet.as_view({'post': 'train_model'}), name='customer-segmentation-train'),
    path('customer-segmentation/segment/', CustomerSegmentationViewSet.as_view({'post': 'segment_customer'}), name='customer-segmentation-segment'),
    path('customer-segmentation/distribution/', CustomerSegmentationViewSet.as_view({'get': 'segment_distribution'}), name='customer-segmentation-distribution'),
    
    # Fraud Detection
    path('fraud-detection/train/', FraudDetectionViewSet.as_view({'post': 'train_model'}), name='fraud-detection-train'),
    path('fraud-detection/detect/', FraudDetectionViewSet.as_view({'post': 'detect_fraud'}), name='fraud-detection-detect'),
    path('fraud-detection/statistics/', FraudDetectionViewSet.as_view({'get': 'fraud_statistics'}), name='fraud-detection-statistics'),
    
    # Recommendations
    path('recommendations/train/', RecommendationViewSet.as_view({'post': 'train_model'}), name='recommendations-train'),
    path('recommendations/get/', RecommendationViewSet.as_view({'post': 'get_recommendations'}), name='recommendations-get'),
    
    # Pricing Optimization
    path('pricing-optimization/train/', PricingOptimizationViewSet.as_view({'post': 'train_model'}), name='pricing-optimization-train'),
    path('pricing-optimization/optimize/', PricingOptimizationViewSet.as_view({'post': 'optimize_price'}), name='pricing-optimization-optimize'),
    
    # Churn Prediction
    path('churn-prediction/train/', ChurnPredictionViewSet.as_view({'post': 'train_model'}), name='churn-prediction-train'),
    path('churn-prediction/predict/', ChurnPredictionViewSet.as_view({'post': 'predict_churn'}), name='churn-prediction-predict'),
    path('churn-prediction/summary/', ChurnPredictionViewSet.as_view({'get': 'churn_risk_summary'}), name='churn-prediction-summary'),
    
    # Sentiment Analysis
    path('sentiment-analysis/train/', SentimentAnalysisViewSet.as_view({'post': 'train_model'}), name='sentiment-analysis-train'),
    path('sentiment-analysis/analyze/', SentimentAnalysisViewSet.as_view({'post': 'analyze_sentiment'}), name='sentiment-analysis-analyze'),
    path('sentiment-analysis/trends/', SentimentAnalysisViewSet.as_view({'get': 'sentiment_trends'}), name='sentiment-analysis-trends'),
    
    # Anomaly Detection
    path('anomaly-detection/train/', AnomalyDetectionViewSet.as_view({'post': 'train_model'}), name='anomaly-detection-train'),
    path('anomaly-detection/detect/', AnomalyDetectionViewSet.as_view({'post': 'detect_anomalies'}), name='anomaly-detection-detect'),
    path('anomaly-detection/recent/', AnomalyDetectionViewSet.as_view({'get': 'recent_anomalies'}), name='anomaly-detection-recent'),
    
    # AI Insights
    path('insights/generate/', AIInsightsViewSet.as_view({'get': 'generate_insights'}), name='ai-insights-generate'),
    path('insights/sales/', AIInsightsViewSet.as_view({'get': 'sales_insights'}), name='ai-insights-sales'),
    path('insights/customer/', AIInsightsViewSet.as_view({'get': 'customer_insights'}), name='ai-insights-customer'),
    path('insights/operational/', AIInsightsViewSet.as_view({'get': 'operational_insights'}), name='ai-insights-operational'),
]