from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
import logging

from .models import *
from .serializers import *
from .services import *

logger = logging.getLogger(__name__)


class MLModelViewSet(viewsets.ModelViewSet):
    """ViewSet for ML models management"""
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        model_type = self.request.query_params.get('model_type')
        status_filter = self.request.query_params.get('status')
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a model"""
        model = self.get_object()
        model.status = 'active'
        model.save()
        return Response({'status': 'Model activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a model"""
        model = self.get_object()
        model.status = 'inactive'
        model.save()
        return Response({'status': 'Model deactivated'})
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get performance summary of all models"""
        models = self.get_queryset()
        summary = []
        
        for model in models:
            summary.append({
                'id': model.id,
                'name': model.name,
                'type': model.model_type,
                'status': model.status,
                'accuracy': model.accuracy,
                'precision': model.precision,
                'recall': model.recall,
                'f1_score': model.f1_score,
                'last_trained': model.last_trained,
                'predictions_count': model.predictions.count()
            })
        
        return Response(summary)


class DemandForecastingViewSet(viewsets.ViewSet):
    """ViewSet for demand forecasting operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DemandForecastingService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train a new demand forecasting model"""
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start training job
            ml_model = self.service.train_model(product_id)
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': f'Demand forecasting model trained for product {product_id}'
            })
            
        except Exception as e:
            logger.error(f"Error training demand model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Generate demand predictions"""
        serializer = DemandForecastRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                product_id = serializer.validated_data['product_id']
                forecast_days = serializer.validated_data['forecast_days']
                
                predictions = self.service.predict_demand(product_id, forecast_days)
                
                # Save predictions to database
                ml_model = MLModel.objects.filter(
                    model_type='demand_forecasting',
                    parameters__product_id=product_id,
                    status='active'
                ).first()
                
                if ml_model:
                    for pred in predictions:
                        DemandForecast.objects.create(
                            product_id=product_id,
                            forecast_date=pred['date'],
                            predicted_demand=pred['predicted_demand'],
                            confidence_interval_lower=pred['confidence_lower'],
                            confidence_interval_upper=pred['confidence_upper'],
                            model=ml_model
                        )
                
                response_serializer = DemandForecastResponseSerializer(predictions, many=True)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error predicting demand: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def historical_forecasts(self, request):
        """Get historical demand forecasts"""
        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))
        
        queryset = DemandForecast.objects.all()
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        queryset = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=days)
        ).order_by('-forecast_date')
        
        serializer = DemandForecastSerializer(queryset, many=True)
        return Response(serializer.data)


class CustomerSegmentationViewSet(viewsets.ViewSet):
    """ViewSet for customer segmentation operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = CustomerSegmentationService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train customer segmentation model"""
        try:
            n_clusters = request.data.get('n_clusters', 5)
            ml_model = self.service.train_segmentation_model(n_clusters)
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': f'Customer segmentation model trained with {n_clusters} clusters'
            })
            
        except Exception as e:
            logger.error(f"Error training segmentation model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def segment_customer(self, request):
        """Segment a customer"""
        serializer = CustomerSegmentationRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.service.segment_customer(serializer.validated_data)
                
                # Save segmentation result
                customer_id = serializer.validated_data.get('customer_id', 'unknown')
                ml_model = MLModel.objects.filter(
                    model_type='customer_segmentation',
                    status='active'
                ).first()
                
                if ml_model:
                    CustomerSegment.objects.update_or_create(
                        customer_id=customer_id,
                        segment_type=result['segment_characteristics'],
                        defaults={
                            'segment_score': 0.8,  # Mock score
                            'characteristics': result,
                            'model': ml_model
                        }
                    )
                
                response_serializer = CustomerSegmentationResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error segmenting customer: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def segment_distribution(self, request):
        """Get customer segment distribution"""
        segments = CustomerSegment.objects.values('segment_type').annotate(
            count=Count('id'),
            avg_score=Avg('segment_score')
        ).order_by('-count')
        
        return Response(list(segments))


class FraudDetectionViewSet(viewsets.ViewSet):
    """ViewSet for fraud detection operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = FraudDetectionService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train fraud detection model"""
        try:
            ml_model = self.service.train_fraud_model()
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': 'Fraud detection model trained successfully'
            })
            
        except Exception as e:
            logger.error(f"Error training fraud model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def detect_fraud(self, request):
        """Detect fraud in a transaction"""
        serializer = FraudDetectionRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.service.detect_fraud(serializer.validated_data)
                
                # Save fraud detection result
                transaction_id = serializer.validated_data['transaction_id']
                ml_model = MLModel.objects.filter(
                    model_type='fraud_detection',
                    status='active'
                ).first()
                
                if ml_model:
                    FraudDetection.objects.create(
                        transaction_id=transaction_id,
                        risk_level=result['risk_level'],
                        risk_score=result['risk_score'],
                        risk_factors=result['risk_factors'],
                        model=ml_model
                    )
                
                response_serializer = FraudDetectionResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error detecting fraud: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def fraud_statistics(self, request):
        """Get fraud detection statistics"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        stats = FraudDetection.objects.filter(created_at__gte=start_date).aggregate(
            total_transactions=Count('id'),
            high_risk_count=Count('id', filter=Q(risk_level='high')),
            critical_risk_count=Count('id', filter=Q(risk_level='critical')),
            avg_risk_score=Avg('risk_score')
        )
        
        return Response(stats)


class RecommendationViewSet(viewsets.ViewSet):
    """ViewSet for product recommendation operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = RecommendationService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train recommendation model"""
        try:
            ml_model = self.service.train_recommendation_model()
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': 'Recommendation model trained successfully'
            })
            
        except Exception as e:
            logger.error(f"Error training recommendation model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def get_recommendations(self, request):
        """Get product recommendations for a user"""
        serializer = RecommendationRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_id = serializer.validated_data['user_id']
                num_recommendations = serializer.validated_data['num_recommendations']
                
                recommendations = self.service.get_recommendations(user_id, num_recommendations)
                
                # Save recommendations
                ml_model = MLModel.objects.filter(
                    model_type='recommendation',
                    status='active'
                ).first()
                
                if ml_model:
                    for rec in recommendations:
                        ProductRecommendation.objects.update_or_create(
                            customer_id=str(user_id),
                            product_id=str(rec['product_id']),
                            recommendation_type='collaborative',
                            defaults={
                                'score': rec['score'],
                                'rank': rec['rank'],
                                'context': {'reason': rec['reason']},
                                'model': ml_model
                            }
                        )
                
                response_serializer = RecommendationResponseSerializer(recommendations, many=True)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error getting recommendations: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PricingOptimizationViewSet(viewsets.ViewSet):
    """ViewSet for pricing optimization operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = PricingOptimizationService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train pricing optimization model"""
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ml_model = self.service.train_pricing_model(product_id)
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': f'Pricing optimization model trained for product {product_id}'
            })
            
        except Exception as e:
            logger.error(f"Error training pricing model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def optimize_price(self, request):
        """Optimize price for a product"""
        serializer = PricingOptimizationRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                product_id = serializer.validated_data['product_id']
                context = {
                    'current_price': serializer.validated_data['current_price'],
                    'competitor_price': serializer.validated_data['competitor_price'],
                    'inventory_level': serializer.validated_data['inventory_level'],
                    'is_weekend': serializer.validated_data['is_weekend'],
                    'day_of_week': serializer.validated_data['day_of_week'],
                    'month': serializer.validated_data['month']
                }
                
                result = self.service.optimize_price(product_id, context)
                
                # Save optimization result
                ml_model = MLModel.objects.filter(
                    model_type='pricing_optimization',
                    parameters__product_id=product_id,
                    status='active'
                ).first()
                
                if ml_model:
                    PricingOptimization.objects.create(
                        product_id=product_id,
                        current_price=result['current_price'],
                        optimized_price=result['optimized_price'],
                        expected_demand=result['expected_demand'],
                        expected_revenue=result['expected_revenue'],
                        competitor_prices={'main_competitor': context['competitor_price']},
                        demand_elasticity=-1.5,  # Mock value
                        inventory_level=context['inventory_level'],
                        model=ml_model
                    )
                
                response_serializer = PricingOptimizationResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error optimizing price: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChurnPredictionViewSet(viewsets.ViewSet):
    """ViewSet for churn prediction operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = ChurnPredictionService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train churn prediction model"""
        try:
            ml_model = self.service.train_churn_model()
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': 'Churn prediction model trained successfully'
            })
            
        except Exception as e:
            logger.error(f"Error training churn model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def predict_churn(self, request):
        """Predict customer churn"""
        serializer = ChurnPredictionRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.service.predict_churn(serializer.validated_data)
                
                # Save churn prediction
                customer_id = serializer.validated_data['customer_id']
                ml_model = MLModel.objects.filter(
                    model_type='churn_prediction',
                    status='active'
                ).first()
                
                if ml_model:
                    ChurnPrediction.objects.update_or_create(
                        customer_id=customer_id,
                        defaults={
                            'churn_probability': result['churn_probability'],
                            'risk_level': result['risk_level'],
                            'churn_factors': result['churn_factors'],
                            'retention_actions': result['retention_actions'],
                            'model': ml_model
                        }
                    )
                
                response_serializer = ChurnPredictionResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error predicting churn: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def churn_risk_summary(self, request):
        """Get churn risk summary"""
        summary = ChurnPrediction.objects.values('risk_level').annotate(
            count=Count('id'),
            avg_probability=Avg('churn_probability')
        ).order_by('-avg_probability')
        
        return Response(list(summary))


class SentimentAnalysisViewSet(viewsets.ViewSet):
    """ViewSet for sentiment analysis operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = SentimentAnalysisService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train sentiment analysis model"""
        try:
            ml_model = self.service.train_sentiment_model()
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': 'Sentiment analysis model trained successfully'
            })
            
        except Exception as e:
            logger.error(f"Error training sentiment model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def analyze_sentiment(self, request):
        """Analyze sentiment of text"""
        serializer = SentimentAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                text = serializer.validated_data['text']
                result = self.service.analyze_sentiment(text)
                
                # Save sentiment analysis
                ml_model = MLModel.objects.filter(
                    model_type='sentiment_analysis',
                    status='active'
                ).first()
                
                if ml_model:
                    SentimentAnalysis.objects.create(
                        text_content=text,
                        sentiment=result['sentiment'],
                        confidence_score=result['confidence_score'],
                        positive_score=result['positive_score'],
                        negative_score=result['negative_score'],
                        neutral_score=result['neutral_score'],
                        source_type=serializer.validated_data.get('source_type', 'api'),
                        source_id=serializer.validated_data.get('source_id', ''),
                        model=ml_model
                    )
                
                response_serializer = SentimentAnalysisResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def sentiment_trends(self, request):
        """Get sentiment trends over time"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        trends = SentimentAnalysis.objects.filter(
            created_at__gte=start_date
        ).values('sentiment').annotate(
            count=Count('id'),
            avg_confidence=Avg('confidence_score')
        ).order_by('-count')
        
        return Response(list(trends))


class AnomalyDetectionViewSet(viewsets.ViewSet):
    """ViewSet for anomaly detection operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AnomalyDetectionService()
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train anomaly detection model"""
        try:
            ml_model = self.service.train_anomaly_model()
            
            return Response({
                'model_id': ml_model.id,
                'status': 'Training completed',
                'message': 'Anomaly detection model trained successfully'
            })
            
        except Exception as e:
            logger.error(f"Error training anomaly model: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def detect_anomalies(self, request):
        """Detect anomalies in business metrics"""
        serializer = AnomalyDetectionRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.service.detect_anomalies(serializer.validated_data)
                
                # Save anomaly detection result
                if result['is_anomaly']:
                    ml_model = MLModel.objects.filter(
                        model_type='anomaly_detection',
                        status='active'
                    ).first()
                    
                    if ml_model:
                        AnomalyDetection.objects.create(
                            anomaly_type=result['anomaly_type'],
                            anomaly_score=result['anomaly_score'],
                            threshold=result['threshold'],
                            data_point=serializer.validated_data,
                            actual_value=serializer.validated_data['sales'],
                            context=result['metrics'],
                            model=ml_model
                        )
                
                response_serializer = AnomalyDetectionResponseSerializer(result)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error detecting anomalies: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def recent_anomalies(self, request):
        """Get recent anomalies"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        anomalies = AnomalyDetection.objects.filter(
            created_at__gte=start_date
        ).order_by('-created_at')
        
        serializer = AnomalyDetectionSerializer(anomalies, many=True)
        return Response(serializer.data)


class AIInsightsViewSet(viewsets.ViewSet):
    """ViewSet for AI-generated business insights"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = AIInsightsService()
    
    @action(detail=False, methods=['get'])
    def generate_insights(self, request):
        """Generate comprehensive AI insights"""
        try:
            insights = self.service.generate_all_insights()
            
            # Save insights to database
            for insight in insights:
                # Find or create a generic AI model for insights
                ml_model, created = MLModel.objects.get_or_create(
                    name="AI Business Insights",
                    model_type='nlp',
                    defaults={
                        'description': 'AI-powered business insights generator',
                        'status': 'active',
                        'created_by_id': 1
                    }
                )
                
                AIInsight.objects.create(
                    title=insight['title'],
                    insight_type=insight['type'],
                    priority=insight['priority'],
                    description=insight['description'],
                    recommendations=insight['recommendations'],
                    potential_impact=f"Confidence: {insight['confidence']:.2%}",
                    confidence_level=insight['confidence'],
                    model=ml_model
                )
            
            response_serializer = AIInsightsResponseSerializer(insights, many=True)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def sales_insights(self, request):
        """Generate sales-specific insights"""
        try:
            insights = self.service.generate_sales_insights()
            response_serializer = AIInsightsResponseSerializer(insights, many=True)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating sales insights: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def customer_insights(self, request):
        """Generate customer-specific insights"""
        try:
            insights = self.service.generate_customer_insights()
            response_serializer = AIInsightsResponseSerializer(insights, many=True)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating customer insights: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def operational_insights(self, request):
        """Generate operational insights"""
        try:
            insights = self.service.generate_operational_insights()
            response_serializer = AIInsightsResponseSerializer(insights, many=True)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating operational insights: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLTrainingJobViewSet(viewsets.ModelViewSet):
    """ViewSet for ML training job management"""
    queryset = MLTrainingJob.objects.all()
    serializer_class = MLTrainingJobSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def start_training(self, request):
        """Start a new training job"""
        serializer = ModelTrainingRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                model_type = serializer.validated_data['model_type']
                parameters = serializer.validated_data['parameters']
                hyperparameters = serializer.validated_data['hyperparameters']
                
                # Create ML model record
                ml_model = MLModel.objects.create(
                    name=f"{model_type.replace('_', ' ').title()} Model",
                    model_type=model_type,
                    description=f"Auto-generated {model_type} model",
                    parameters=parameters,
                    hyperparameters=hyperparameters,
                    status='training',
                    created_by=request.user
                )
                
                # Create training job
                training_job = MLTrainingJob.objects.create(
                    model=ml_model,
                    status='pending',
                    training_config={
                        'model_type': model_type,
                        'parameters': parameters,
                        'hyperparameters': hyperparameters
                    },
                    started_at=timezone.now()
                )
                
                # In a real implementation, you would start the training asynchronously
                # For now, we'll just mark it as completed
                training_job.status = 'completed'
                training_job.completed_at = timezone.now()
                training_job.progress_percentage = 100.0
                training_job.save()
                
                ml_model.status = 'active'
                ml_model.last_trained = timezone.now()
                ml_model.save()
                
                response_serializer = ModelTrainingResponseSerializer({
                    'job_id': training_job.id,
                    'status': training_job.status,
                    'message': f'Training job for {model_type} completed successfully'
                })
                
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error starting training job: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel_training(self, request, pk=None):
        """Cancel a training job"""
        training_job = self.get_object()
        if training_job.status in ['pending', 'running']:
            training_job.status = 'cancelled'
            training_job.completed_at = timezone.now()
            training_job.save()
            
            return Response({'status': 'Training job cancelled'})
        else:
            return Response(
                {'error': 'Cannot cancel completed or failed job'},
                status=status.HTTP_400_BAD_REQUEST
            )