from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

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
from .serializers import (
    CustomerSegmentSerializer,
    CustomerAnalyticsSerializer,
    CustomerBehaviorEventSerializer,
    CustomerCohortSerializer,
    CustomerLifecycleStageSerializer,
    CustomerRecommendationSerializer,
    CustomerSatisfactionSurveySerializer,
    CustomerAnalyticsSummarySerializer
)
from .services import CustomerAnalyticsService
from .advanced_analytics_service import AdvancedCustomerAnalyticsService
from .ml_analytics_service import MLCustomerAnalyticsService


class CustomerSegmentViewSet(viewsets.ModelViewSet):
    queryset = CustomerSegment.objects.all()
    serializer_class = CustomerSegmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        segment_type = self.request.query_params.get('segment_type')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if segment_type:
            queryset = queryset.filter(segment_type=segment_type)
            
        return queryset.order_by('-created_at')


class CustomerAnalyticsViewSet(viewsets.ModelViewSet):
    queryset = CustomerAnalytics.objects.select_related('customer', 'segment')
    serializer_class = CustomerAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        segment = self.request.query_params.get('segment')
        churn_risk = self.request.query_params.get('churn_risk')
        
        if segment:
            queryset = queryset.filter(segment__segment_type=segment)
        if churn_risk:
            if churn_risk == 'high':
                queryset = queryset.filter(churn_risk_score__gte=70)
            elif churn_risk == 'medium':
                queryset = queryset.filter(churn_risk_score__gte=40, churn_risk_score__lt=70)
            elif churn_risk == 'low':
                queryset = queryset.filter(churn_risk_score__lt=40)
                
        return queryset.order_by('-total_spent')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get customer analytics summary"""
        service = CustomerAnalyticsService()
        summary_data = service.get_analytics_summary()
        serializer = CustomerAnalyticsSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def segments_distribution(self, request):
        """Get customer segments distribution"""
        distribution = CustomerAnalytics.objects.values(
            'segment__name', 'segment__segment_type'
        ).annotate(
            count=Count('id'),
            total_value=Sum('total_spent'),
            avg_value=Avg('total_spent')
        ).order_by('-count')
        
        return Response(distribution)
    
    @action(detail=False, methods=['get'])
    def churn_analysis(self, request):
        """Get churn risk analysis"""
        churn_data = CustomerAnalytics.objects.aggregate(
            high_risk=Count('id', filter=Q(churn_risk_score__gte=70)),
            medium_risk=Count('id', filter=Q(churn_risk_score__gte=40, churn_risk_score__lt=70)),
            low_risk=Count('id', filter=Q(churn_risk_score__lt=40)),
            avg_risk_score=Avg('churn_risk_score')
        )
        
        return Response(churn_data)


class CustomerBehaviorEventViewSet(viewsets.ModelViewSet):
    queryset = CustomerBehaviorEvent.objects.select_related('customer')
    serializer_class = CustomerBehaviorEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        event_type = self.request.query_params.get('event_type')
        customer_id = self.request.query_params.get('customer_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
            
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def event_analytics(self, request):
        """Get behavior event analytics"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        events = CustomerBehaviorEvent.objects.filter(
            timestamp__gte=start_date
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(events)


class CustomerCohortViewSet(viewsets.ModelViewSet):
    queryset = CustomerCohort.objects.all()
    serializer_class = CustomerCohortSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().order_by('-cohort_date')
    
    @action(detail=False, methods=['post'])
    def generate_cohorts(self, request):
        """Generate cohort analysis"""
        service = CustomerAnalyticsService()
        cohorts = service.generate_cohort_analysis()
        serializer = self.get_serializer(cohorts, many=True)
        return Response(serializer.data)


class CustomerLifecycleStageViewSet(viewsets.ModelViewSet):
    queryset = CustomerLifecycleStage.objects.select_related('customer')
    serializer_class = CustomerLifecycleStageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        stage = self.request.query_params.get('stage')
        customer_id = self.request.query_params.get('customer_id')
        
        if stage:
            queryset = queryset.filter(stage=stage)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        return queryset.order_by('-stage_date')


class CustomerRecommendationViewSet(viewsets.ModelViewSet):
    queryset = CustomerRecommendation.objects.select_related('customer')
    serializer_class = CustomerRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        recommendation_type = self.request.query_params.get('recommendation_type')
        customer_id = self.request.query_params.get('customer_id')
        is_active = self.request.query_params.get('is_active')
        
        if recommendation_type:
            queryset = queryset.filter(recommendation_type=recommendation_type)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        """Track recommendation view"""
        recommendation = self.get_object()
        recommendation.views += 1
        recommendation.save()
        return Response({'status': 'view tracked'})
    
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track recommendation click"""
        recommendation = self.get_object()
        recommendation.clicks += 1
        recommendation.save()
        return Response({'status': 'click tracked'})
    
    @action(detail=True, methods=['post'])
    def track_conversion(self, request, pk=None):
        """Track recommendation conversion"""
        recommendation = self.get_object()
        recommendation.conversions += 1
        revenue = request.data.get('revenue', 0)
        recommendation.revenue_generated += Decimal(str(revenue))
        recommendation.save()
        return Response({'status': 'conversion tracked'})


class CustomerSatisfactionSurveyViewSet(viewsets.ModelViewSet):
    queryset = CustomerSatisfactionSurvey.objects.select_related('customer')
    serializer_class = CustomerSatisfactionSurveySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        survey_type = self.request.query_params.get('survey_type')
        customer_id = self.request.query_params.get('customer_id')
        
        if survey_type:
            queryset = queryset.filter(survey_type=survey_type)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        return queryset.order_by('-survey_date')
    
    @action(detail=False, methods=['get'])
    def satisfaction_metrics(self, request):
        """Get satisfaction metrics"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        metrics = CustomerSatisfactionSurvey.objects.filter(
            survey_date__gte=start_date
        ).values('survey_type').annotate(
            avg_score=Avg('score'),
            count=Count('id')
        )
        
        # Calculate NPS
        nps_surveys = CustomerSatisfactionSurvey.objects.filter(
            survey_type='nps',
            survey_date__gte=start_date
        )
        
        if nps_surveys.exists():
            promoters = nps_surveys.filter(score__gte=9).count()
            detractors = nps_surveys.filter(score__lte=6).count()
            total = nps_surveys.count()
            nps_score = ((promoters - detractors) / total) * 100 if total > 0 else 0
        else:
            nps_score = None
        
        return Response({
            'metrics': metrics,
            'nps_score': nps_score
        })


class AdvancedCustomerAnalyticsViewSet(viewsets.ViewSet):
    """Advanced customer analytics with ML capabilities"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.advanced_service = AdvancedCustomerAnalyticsService()
        self.ml_service = MLCustomerAnalyticsService()
    
    @action(detail=False, methods=['get'])
    def clv_analysis(self, request):
        """Get comprehensive CLV analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            
            if customer_id:
                # Get CLV for specific customer
                clv_data = self.advanced_service.calculate_customer_lifetime_value(int(customer_id))
                return Response({
                    'customer_id': customer_id,
                    'historical_clv': float(clv_data.historical_clv),
                    'predicted_clv': float(clv_data.predicted_clv),
                    'purchase_frequency': float(clv_data.purchase_frequency),
                    'average_order_value': float(clv_data.average_order_value),
                    'customer_lifespan': float(clv_data.customer_lifespan),
                    'clv_to_cac_ratio': float(clv_data.clv_to_cac_ratio),
                    'engagement_score': float(clv_data.engagement_score),
                    'loyalty_score': float(clv_data.loyalty_score),
                    'prediction_confidence': float(clv_data.prediction_confidence)
                })
            else:
                # Get CLV segmentation
                segments = self.advanced_service.segment_customers_by_clv()
                return Response(segments)
                
        except Exception as e:
            return Response(
                {'error': f'Error in CLV analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def churn_prediction(self, request):
        """Get churn prediction analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            
            if customer_id:
                # Get churn prediction for specific customer
                churn_data = self.advanced_service.predict_customer_churn(int(customer_id))
                return Response({
                    'customer_id': customer_id,
                    'churn_probability': float(churn_data.churn_probability),
                    'churn_risk_level': churn_data.churn_risk_level,
                    'recency_score': float(churn_data.recency_score),
                    'frequency_score': float(churn_data.frequency_score),
                    'monetary_score': float(churn_data.monetary_score),
                    'engagement_score': float(churn_data.engagement_score),
                    'satisfaction_score': float(churn_data.satisfaction_score),
                    'prediction_confidence': float(churn_data.prediction_confidence),
                    'intervention_recommended': churn_data.intervention_recommended,
                    'feature_vector': churn_data.feature_vector
                })
            else:
                # Get churn analysis summary
                summary = self.advanced_service.get_churn_analysis_summary()
                return Response(summary)
                
        except Exception as e:
            return Response(
                {'error': f'Error in churn prediction: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def behavior_analysis(self, request):
        """Get customer behavior analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            behavior_patterns = self.advanced_service.analyze_customer_behavior_patterns(int(customer_id))
            return Response(behavior_patterns)
            
        except Exception as e:
            return Response(
                {'error': f'Error in behavior analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def journey_mapping(self, request):
        """Create customer journey map"""
        try:
            customer_id = request.data.get('customer_id')
            journey_type = request.data.get('journey_type', 'purchase')
            
            if not customer_id:
                return Response(
                    {'error': 'customer_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            journey_map = self.advanced_service.map_customer_journey(int(customer_id), journey_type)
            return Response({
                'journey_id': journey_map.journey_id,
                'journey_type': journey_map.journey_type,
                'status': journey_map.status,
                'total_touchpoints': journey_map.total_touchpoints,
                'touchpoints': journey_map.touchpoints,
                'conversion_path': journey_map.conversion_path,
                'start_date': journey_map.start_date.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in journey mapping: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def cac_analysis(self, request):
        """Get customer acquisition cost analysis"""
        try:
            analysis = self.advanced_service.analyze_customer_acquisition_cost()
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Error in CAC analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def retention_analysis(self, request):
        """Get customer retention analysis"""
        try:
            analysis = self.advanced_service.analyze_customer_retention()
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Error in retention analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def profitability_analysis(self, request):
        """Get customer profitability analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            profitability = self.advanced_service.analyze_customer_profitability(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'total_revenue': float(profitability.total_revenue),
                'gross_revenue': float(profitability.gross_revenue),
                'net_revenue': float(profitability.net_revenue),
                'total_cost': float(profitability.total_cost),
                'gross_profit': float(profitability.gross_profit),
                'net_profit': float(profitability.net_profit),
                'profit_margin': float(profitability.profit_margin),
                'roi': float(profitability.roi),
                'profitability_rank': profitability.profitability_rank,
                'profitability_percentile': float(profitability.profitability_percentile),
                'monthly_profit_trend': profitability.monthly_profit_trend,
                'quarterly_profit_trend': profitability.quarterly_profit_trend
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in profitability analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def engagement_scoring(self, request):
        """Get customer engagement scoring"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            engagement = self.advanced_service.calculate_customer_engagement_score(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'total_score': float(engagement.total_score),
                'website_engagement': float(engagement.website_engagement),
                'email_engagement': float(engagement.email_engagement),
                'social_engagement': float(engagement.social_engagement),
                'purchase_engagement': float(engagement.purchase_engagement),
                'support_engagement': float(engagement.support_engagement),
                'session_frequency': float(engagement.session_frequency),
                'avg_session_duration': float(engagement.avg_session_duration),
                'page_views_per_session': float(engagement.page_views_per_session),
                'bounce_rate': float(engagement.bounce_rate),
                'email_open_rate': float(engagement.email_open_rate),
                'email_click_rate': float(engagement.email_click_rate),
                'sms_response_rate': float(engagement.sms_response_rate),
                'engagement_trend': engagement.engagement_trend
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in engagement scoring: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MLCustomerAnalyticsViewSet(viewsets.ViewSet):
    """ML-based customer analytics"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ml_service = MLCustomerAnalyticsService()
    
    @action(detail=False, methods=['get'])
    def preference_analysis(self, request):
        """Get customer preference analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preferences = self.ml_service.analyze_customer_preferences(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'preferred_categories': preferences.preferred_categories,
                'preferred_brands': preferences.preferred_brands,
                'preferred_price_range': preferences.preferred_price_range,
                'preferred_attributes': preferences.preferred_attributes,
                'preferred_shopping_times': preferences.preferred_shopping_times,
                'preferred_channels': preferences.preferred_channels,
                'preferred_payment_methods': preferences.preferred_payment_methods,
                'preferred_shipping_methods': preferences.preferred_shipping_methods,
                'communication_frequency': preferences.communication_frequency,
                'preferred_communication_channels': preferences.preferred_communication_channels,
                'category_confidence': float(preferences.category_confidence),
                'brand_confidence': float(preferences.brand_confidence),
                'price_confidence': float(preferences.price_confidence)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in preference analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_recommendations(self, request):
        """Generate product recommendations"""
        try:
            customer_id = request.data.get('customer_id')
            recommendation_type = request.data.get('recommendation_type', 'product')
            algorithm = request.data.get('algorithm', 'hybrid')
            limit = int(request.data.get('limit', 10))
            
            if not customer_id:
                return Response(
                    {'error': 'customer_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            recommendation = self.ml_service.generate_product_recommendations(
                int(customer_id), recommendation_type, algorithm, limit
            )
            
            return Response({
                'recommendation_id': recommendation.id,
                'customer_id': customer_id,
                'recommendation_type': recommendation.recommendation_type,
                'algorithm_used': recommendation.algorithm_used,
                'recommended_items': recommendation.recommended_items,
                'confidence_score': float(recommendation.confidence_score),
                'expires_at': recommendation.expires_at.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error generating recommendations: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def cross_sell_opportunities(self, request):
        """Get cross-sell and up-sell opportunities"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            opportunities = self.ml_service.identify_cross_sell_opportunities(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'opportunities': opportunities
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error identifying cross-sell opportunities: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def demographic_analysis(self, request):
        """Get customer demographic analysis"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            demographics = self.ml_service.analyze_customer_demographics(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'country': demographics.country,
                'state': demographics.state,
                'city': demographics.city,
                'postal_code': demographics.postal_code,
                'timezone': demographics.timezone,
                'age_group': demographics.age_group,
                'gender': demographics.gender,
                'income_bracket': demographics.income_bracket,
                'lifestyle_segments': demographics.lifestyle_segments,
                'interests': demographics.interests,
                'values': demographics.values,
                'personality_traits': demographics.personality_traits,
                'shopping_personality': demographics.shopping_personality,
                'device_preferences': demographics.device_preferences,
                'tech_savviness': demographics.tech_savviness,
                'data_sources': demographics.data_sources,
                'confidence_score': float(demographics.confidence_score)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in demographic analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def sentiment_analysis(self, request):
        """Analyze customer sentiment"""
        try:
            customer_id = request.data.get('customer_id')
            content = request.data.get('content')
            source_platform = request.data.get('source_platform')
            content_type = request.data.get('content_type')
            
            if not all([customer_id, content, source_platform, content_type]):
                return Response(
                    {'error': 'customer_id, content, source_platform, and content_type are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            sentiment = self.ml_service.analyze_customer_sentiment(
                int(customer_id), content, source_platform, content_type
            )
            
            return Response({
                'sentiment_id': sentiment.id,
                'customer_id': customer_id,
                'overall_sentiment': sentiment.overall_sentiment,
                'sentiment_score': float(sentiment.sentiment_score),
                'confidence_score': float(sentiment.confidence_score),
                'keywords_extracted': sentiment.keywords_extracted,
                'emotions_detected': sentiment.emotions_detected,
                'topics_identified': sentiment.topics_identified,
                'analyzed_at': sentiment.analyzed_at.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in sentiment analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def brand_mentions(self, request):
        """Monitor brand mentions"""
        try:
            customer_id = request.query_params.get('customer_id')
            mentions = self.ml_service.monitor_brand_mentions(
                int(customer_id) if customer_id else None
            )
            return Response({
                'mentions': mentions,
                'total_mentions': len(mentions)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error monitoring brand mentions: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def feedback_analysis(self, request):
        """Analyze customer feedback with NLP"""
        try:
            customer_id = request.data.get('customer_id')
            feedback_text = request.data.get('feedback_text')
            feedback_type = request.data.get('feedback_type')
            source_id = request.data.get('source_id', '')
            
            if not all([customer_id, feedback_text, feedback_type]):
                return Response(
                    {'error': 'customer_id, feedback_text, and feedback_type are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            analysis = self.ml_service.analyze_customer_feedback(
                int(customer_id), feedback_text, feedback_type, source_id
            )
            
            return Response({
                'analysis_id': analysis.id,
                'customer_id': customer_id,
                'sentiment_score': float(analysis.sentiment_score),
                'emotion_scores': analysis.emotion_scores,
                'key_phrases': analysis.key_phrases,
                'named_entities': analysis.named_entities,
                'topics': analysis.topics,
                'feedback_category': analysis.feedback_category,
                'urgency_level': analysis.urgency_level,
                'requires_response': analysis.requires_response,
                'analysis_confidence': float(analysis.analysis_confidence),
                'analyzed_at': analysis.analyzed_at.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in feedback analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def risk_assessment(self, request):
        """Get customer risk assessment"""
        try:
            customer_id = request.query_params.get('customer_id')
            if not customer_id:
                return Response(
                    {'error': 'customer_id parameter is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            risk_assessment = self.ml_service.assess_customer_risk(int(customer_id))
            return Response({
                'customer_id': customer_id,
                'overall_risk_score': float(risk_assessment.overall_risk_score),
                'risk_level': risk_assessment.risk_level,
                'fraud_risk_score': float(risk_assessment.fraud_risk_score),
                'payment_risk_score': float(risk_assessment.payment_risk_score),
                'chargeback_risk_score': float(risk_assessment.chargeback_risk_score),
                'return_abuse_risk_score': float(risk_assessment.return_abuse_risk_score),
                'suspicious_activities': risk_assessment.suspicious_activities,
                'risk_factors': risk_assessment.risk_factors,
                'protective_factors': risk_assessment.protective_factors,
                'monitoring_level': risk_assessment.monitoring_level,
                'restrictions_applied': risk_assessment.restrictions_applied,
                'manual_review_required': risk_assessment.manual_review_required,
                'last_assessment': risk_assessment.last_assessment.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in risk assessment: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )