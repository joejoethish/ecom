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
    CustomerSatisfactionSurvey
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