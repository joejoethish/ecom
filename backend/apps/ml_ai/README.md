# Machine Learning and AI System

This module provides comprehensive machine learning and artificial intelligence capabilities for the e-commerce admin panel, including predictive analytics, automated insights, and intelligent decision support.

## Features

### 1. Demand Forecasting
- **Purpose**: Predict future product demand for inventory planning
- **Algorithm**: Random Forest Regression with seasonal decomposition
- **Features**: Historical sales, seasonality, trends, external factors
- **Output**: Daily/weekly/monthly demand predictions with confidence intervals

### 2. Customer Segmentation
- **Purpose**: Automatically segment customers based on behavior patterns
- **Algorithm**: K-Means clustering with RFM analysis
- **Features**: Purchase frequency, monetary value, recency, lifetime value
- **Output**: Customer segments (high-value, loyal, at-risk, new, dormant)

### 3. Fraud Detection
- **Purpose**: Identify potentially fraudulent transactions in real-time
- **Algorithm**: Isolation Forest for anomaly detection
- **Features**: Transaction amount, timing, customer profile, payment method
- **Output**: Risk score, risk level, and specific risk factors

### 4. Product Recommendations
- **Purpose**: Generate personalized product recommendations
- **Algorithm**: Collaborative filtering with item-item similarity
- **Features**: User-item interactions, product attributes, purchase history
- **Output**: Ranked product recommendations with relevance scores

### 5. Pricing Optimization
- **Purpose**: Optimize product pricing for maximum revenue
- **Algorithm**: Random Forest with price elasticity modeling
- **Features**: Current price, competitor prices, demand, inventory levels
- **Output**: Optimal price points with expected demand and revenue

### 6. Churn Prediction
- **Purpose**: Identify customers at risk of churning
- **Algorithm**: Random Forest Classification with feature importance
- **Features**: Purchase patterns, support interactions, engagement metrics
- **Output**: Churn probability, risk level, and retention recommendations

### 7. Sentiment Analysis
- **Purpose**: Analyze customer sentiment from reviews and feedback
- **Algorithm**: Naive Bayes with TF-IDF vectorization
- **Features**: Text content, linguistic patterns, context
- **Output**: Sentiment classification (positive/negative/neutral) with confidence

### 8. Anomaly Detection
- **Purpose**: Detect unusual patterns in business metrics
- **Algorithm**: Isolation Forest for multivariate anomaly detection
- **Features**: Sales metrics, conversion rates, user behavior
- **Output**: Anomaly scores, severity levels, and contextual information

### 9. AI-Powered Insights
- **Purpose**: Generate actionable business insights automatically
- **Algorithm**: Multi-model ensemble with rule-based reasoning
- **Features**: Cross-functional data analysis, trend identification
- **Output**: Prioritized insights with recommendations and confidence levels

## API Endpoints

### Model Management
- `GET /api/admin/ml-ai/models/` - List all ML models
- `POST /api/admin/ml-ai/models/` - Create new ML model
- `GET /api/admin/ml-ai/models/{id}/` - Get model details
- `PUT /api/admin/ml-ai/models/{id}/` - Update model
- `DELETE /api/admin/ml-ai/models/{id}/` - Delete model
- `POST /api/admin/ml-ai/models/{id}/activate/` - Activate model
- `POST /api/admin/ml-ai/models/{id}/deactivate/` - Deactivate model

### Demand Forecasting
- `POST /api/admin/ml-ai/demand-forecasting/train/` - Train forecasting model
- `POST /api/admin/ml-ai/demand-forecasting/predict/` - Generate predictions
- `GET /api/admin/ml-ai/demand-forecasting/historical/` - Get historical forecasts

### Customer Segmentation
- `POST /api/admin/ml-ai/customer-segmentation/train/` - Train segmentation model
- `POST /api/admin/ml-ai/customer-segmentation/segment/` - Segment customer
- `GET /api/admin/ml-ai/customer-segmentation/distribution/` - Get segment distribution

### Fraud Detection
- `POST /api/admin/ml-ai/fraud-detection/train/` - Train fraud model
- `POST /api/admin/ml-ai/fraud-detection/detect/` - Detect fraud
- `GET /api/admin/ml-ai/fraud-detection/statistics/` - Get fraud statistics

### Product Recommendations
- `POST /api/admin/ml-ai/recommendations/train/` - Train recommendation model
- `POST /api/admin/ml-ai/recommendations/get/` - Get recommendations

### Pricing Optimization
- `POST /api/admin/ml-ai/pricing-optimization/train/` - Train pricing model
- `POST /api/admin/ml-ai/pricing-optimization/optimize/` - Optimize pricing

### Churn Prediction
- `POST /api/admin/ml-ai/churn-prediction/train/` - Train churn model
- `POST /api/admin/ml-ai/churn-prediction/predict/` - Predict churn
- `GET /api/admin/ml-ai/churn-prediction/summary/` - Get churn summary

### Sentiment Analysis
- `POST /api/admin/ml-ai/sentiment-analysis/train/` - Train sentiment model
- `POST /api/admin/ml-ai/sentiment-analysis/analyze/` - Analyze sentiment
- `GET /api/admin/ml-ai/sentiment-analysis/trends/` - Get sentiment trends

### Anomaly Detection
- `POST /api/admin/ml-ai/anomaly-detection/train/` - Train anomaly model
- `POST /api/admin/ml-ai/anomaly-detection/detect/` - Detect anomalies
- `GET /api/admin/ml-ai/anomaly-detection/recent/` - Get recent anomalies

### AI Insights
- `GET /api/admin/ml-ai/insights/generate/` - Generate all insights
- `GET /api/admin/ml-ai/insights/sales/` - Generate sales insights
- `GET /api/admin/ml-ai/insights/customer/` - Generate customer insights
- `GET /api/admin/ml-ai/insights/operational/` - Generate operational insights

### Training Jobs
- `GET /api/admin/ml-ai/training-jobs/` - List training jobs
- `POST /api/admin/ml-ai/training-jobs/start_training/` - Start training job
- `POST /api/admin/ml-ai/training-jobs/{id}/cancel_training/` - Cancel training job

## Management Commands

### Train ML Models
```bash
python manage.py train_ml_models --model-type demand_forecasting --product-id PROD_001
python manage.py train_ml_models --model-type customer_segmentation
python manage.py train_ml_models  # Train all models
```

### Generate AI Insights
```bash
python manage.py generate_ai_insights --insight-type sales
python manage.py generate_ai_insights --insight-type customer
python manage.py generate_ai_insights --priority high --limit 5
```

## Data Models

### Core Models
- **MLModel**: Stores ML model metadata and performance metrics
- **MLPrediction**: Generic prediction results with confidence scores
- **MLTrainingJob**: Tracks model training jobs and progress

### Specific Models
- **DemandForecast**: Demand predictions with confidence intervals
- **CustomerSegment**: Customer segmentation results
- **FraudDetection**: Fraud detection results with risk factors
- **ProductRecommendation**: Product recommendations with scores
- **PricingOptimization**: Price optimization results
- **ChurnPrediction**: Customer churn predictions
- **SentimentAnalysis**: Text sentiment analysis results
- **AnomalyDetection**: Business metric anomaly detection
- **AIInsight**: AI-generated business insights

## Configuration

### Required Dependencies
```python
# Machine Learning
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0
joblib>=1.3.0

# Optional: Advanced ML
tensorflow>=2.13.0  # For deep learning models
xgboost>=1.7.0      # For gradient boosting
lightgbm>=4.0.0     # For efficient gradient boosting
```

### Settings
```python
# settings.py
ML_AI_SETTINGS = {
    'MODEL_STORAGE_PATH': 'ml_models/',
    'TRAINING_DATA_PATH': 'training_data/',
    'CACHE_TIMEOUT': 3600,  # 1 hour
    'MAX_TRAINING_TIME': 1800,  # 30 minutes
    'DEFAULT_CONFIDENCE_THRESHOLD': 0.7,
    'ENABLE_AUTO_RETRAINING': True,
    'RETRAINING_INTERVAL_DAYS': 7,
}
```

## Usage Examples

### Demand Forecasting
```python
from apps.ml_ai.services import DemandForecastingService

service = DemandForecastingService()
model = service.train_model('PROD_001')
predictions = service.predict_demand('PROD_001', forecast_days=30)
```

### Fraud Detection
```python
from apps.ml_ai.services import FraudDetectionService

service = FraudDetectionService()
model = service.train_fraud_model()

transaction_data = {
    'amount': 1500,
    'hour_of_day': 2,
    'customer_age_days': 5,
    # ... other features
}
result = service.detect_fraud(transaction_data)
```

### AI Insights
```python
from apps.ml_ai.services import AIInsightsService

service = AIInsightsService()
insights = service.generate_all_insights()
sales_insights = service.generate_sales_insights()
```

## Performance Considerations

### Model Training
- Models are trained asynchronously to avoid blocking requests
- Training data is cached to improve performance
- Model files are stored efficiently using joblib compression

### Prediction Serving
- Active models are cached in memory for fast predictions
- Batch prediction endpoints for processing multiple items
- Confidence thresholds to filter low-quality predictions

### Monitoring
- Model performance metrics are tracked automatically
- Prediction accuracy is monitored over time
- Alerts for model degradation or anomalies

## Security

### Data Privacy
- Sensitive customer data is anonymized before training
- Model files are stored securely with access controls
- Prediction logs can be configured for retention policies

### Access Control
- API endpoints require authentication
- Role-based permissions for different ML operations
- Audit logging for all ML activities

## Testing

### Unit Tests
```bash
python manage.py test apps.ml_ai.tests
```

### Integration Tests
```bash
python manage.py test apps.ml_ai.tests.MLAIAPITestCase
```

### Performance Tests
```bash
python manage.py test apps.ml_ai.tests.PerformanceTestCase
```

## Monitoring and Maintenance

### Model Performance
- Accuracy metrics are tracked over time
- Model drift detection alerts
- Automatic retraining schedules

### System Health
- Prediction latency monitoring
- Error rate tracking
- Resource usage optimization

### Data Quality
- Input data validation
- Feature drift detection
- Data completeness checks

## Troubleshooting

### Common Issues
1. **Model Training Fails**: Check data quality and feature completeness
2. **Low Prediction Accuracy**: Retrain with more recent data
3. **High Latency**: Check model complexity and caching configuration
4. **Memory Issues**: Optimize model size and batch processing

### Debugging
- Enable detailed logging in settings
- Use Django debug toolbar for performance analysis
- Monitor database query patterns for optimization opportunities

## Future Enhancements

### Planned Features
- Deep learning models for complex patterns
- Real-time streaming predictions
- A/B testing framework for model comparison
- AutoML capabilities for automated model selection
- Integration with external ML platforms (AWS SageMaker, Google AI)

### Scalability Improvements
- Distributed training for large datasets
- Model serving with load balancing
- GPU acceleration for deep learning models
- Kubernetes deployment for auto-scaling