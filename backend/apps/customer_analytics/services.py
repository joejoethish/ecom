from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from .models import (
    CustomerSegment,
    CustomerAnalytics,
    CustomerBehaviorEvent,
    CustomerCohort,
    CustomerLifecycleStage,
    CustomerRecommendation,
    CustomerSatisfactionSurvey
)

User = get_user_model()


class CustomerAnalyticsService:
    """Service class for customer analytics operations"""
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive customer analytics summary"""
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Basic customer metrics
        total_customers = CustomerAnalytics.objects.count()
        new_customers_this_month = CustomerAnalytics.objects.filter(
            created_at__gte=this_month_start
        ).count()
        
        # Customer segments
        active_customers = CustomerAnalytics.objects.filter(
            days_since_last_purchase__lte=30
        ).count()
        
        at_risk_customers = CustomerAnalytics.objects.filter(
            churn_risk_score__gte=70
        ).count()
        
        churned_customers = CustomerAnalytics.objects.filter(
            days_since_last_purchase__gte=90
        ).count()
        
        # Financial metrics
        avg_customer_value = CustomerAnalytics.objects.aggregate(
            avg_value=Avg('customer_lifetime_value')
        )['avg_value'] or Decimal('0.00')
        
        avg_order_value = CustomerAnalytics.objects.aggregate(
            avg_aov=Avg('average_order_value')
        )['avg_aov'] or Decimal('0.00')
        
        # Retention rate (customers who made a purchase in the last 30 days)
        if total_customers > 0:
            retention_rate = (active_customers / total_customers) * 100
        else:
            retention_rate = Decimal('0.00')
        
        # Satisfaction scores
        nps_score = self.calculate_nps_score()
        csat_score = self.calculate_csat_score()
        
        return {
            'total_customers': total_customers,
            'new_customers_this_month': new_customers_this_month,
            'active_customers': active_customers,
            'at_risk_customers': at_risk_customers,
            'churned_customers': churned_customers,
            'average_customer_value': avg_customer_value,
            'average_order_value': avg_order_value,
            'customer_retention_rate': retention_rate,
            'nps_score': nps_score,
            'csat_score': csat_score
        }
    
    def calculate_nps_score(self, days: int = 30) -> Decimal:
        """Calculate Net Promoter Score"""
        start_date = timezone.now() - timedelta(days=days)
        nps_surveys = CustomerSatisfactionSurvey.objects.filter(
            survey_type='nps',
            survey_date__gte=start_date
        )
        
        if not nps_surveys.exists():
            return None
        
        total = nps_surveys.count()
        promoters = nps_surveys.filter(score__gte=9).count()
        detractors = nps_surveys.filter(score__lte=6).count()
        
        nps_score = ((promoters - detractors) / total) * 100
        return Decimal(str(round(nps_score, 2)))
    
    def calculate_csat_score(self, days: int = 30) -> Decimal:
        """Calculate Customer Satisfaction Score"""
        start_date = timezone.now() - timedelta(days=days)
        csat_surveys = CustomerSatisfactionSurvey.objects.filter(
            survey_type='csat',
            survey_date__gte=start_date
        )
        
        if not csat_surveys.exists():
            return None
        
        avg_score = csat_surveys.aggregate(avg=Avg('normalized_score'))['avg']
        return Decimal(str(round(avg_score, 2))) if avg_score else None
    
    def update_customer_analytics(self, customer_id: int) -> CustomerAnalytics:
        """Update analytics for a specific customer"""
        try:
            analytics = CustomerAnalytics.objects.get(customer_id=customer_id)
        except CustomerAnalytics.DoesNotExist:
            analytics = CustomerAnalytics.objects.create(customer_id=customer_id)
        
        # This would typically integrate with order/purchase data
        # For now, we'll update basic metrics
        analytics.days_since_last_purchase = analytics.calculate_days_since_last_purchase()
        analytics.last_calculated = timezone.now()
        analytics.save()
        
        # Update customer segment
        self.update_customer_segment(analytics)
        
        return analytics
    
    def update_customer_segment(self, analytics: CustomerAnalytics):
        """Update customer segment based on analytics"""
        # Simple segmentation logic
        if analytics.total_spent >= 1000 and analytics.total_orders >= 5:
            segment_type = 'high_value'
        elif analytics.days_since_last_purchase <= 30:
            segment_type = 'frequent_buyer'
        elif analytics.days_since_last_purchase <= 90:
            segment_type = 'at_risk'
        elif analytics.total_orders == 1:
            segment_type = 'new_customer'
        else:
            segment_type = 'dormant'
        
        # Get or create segment
        segment, created = CustomerSegment.objects.get_or_create(
            segment_type=segment_type,
            defaults={
                'name': segment_type.replace('_', ' ').title(),
                'description': f'Auto-generated {segment_type} segment'
            }
        )
        
        analytics.segment = segment
        analytics.save()
    
    def generate_cohort_analysis(self) -> List[CustomerCohort]:
        """Generate cohort analysis for customers"""
        # Get customers grouped by their first purchase month
        cohorts_data = CustomerAnalytics.objects.filter(
            first_purchase_date__isnull=False
        ).extra(
            select={'cohort_month': "DATE_TRUNC('month', first_purchase_date)"}
        ).values('cohort_month').annotate(
            initial_customers=Count('id'),
            total_revenue=Sum('total_spent'),
            avg_customer_value=Avg('total_spent')
        ).order_by('cohort_month')
        
        cohorts = []
        for cohort_data in cohorts_data:
            cohort_date = cohort_data['cohort_month'].date()
            
            # Calculate current active customers for this cohort
            current_active = CustomerAnalytics.objects.filter(
                first_purchase_date__date__gte=cohort_date,
                first_purchase_date__date__lt=cohort_date.replace(day=28) + timedelta(days=4),
                days_since_last_purchase__lte=30
            ).count()
            
            cohort, created = CustomerCohort.objects.update_or_create(
                cohort_date=cohort_date,
                defaults={
                    'name': f"Cohort {cohort_date.strftime('%Y-%m')}",
                    'initial_customers': cohort_data['initial_customers'],
                    'current_active_customers': current_active,
                    'total_revenue': cohort_data['total_revenue'] or Decimal('0.00'),
                    'average_customer_value': cohort_data['avg_customer_value'] or Decimal('0.00')
                }
            )
            cohorts.append(cohort)
        
        return cohorts
    
    def track_behavior_event(self, customer_id: int, event_type: str, 
                           event_data: Dict = None, session_id: str = None,
                           ip_address: str = None, user_agent: str = None) -> CustomerBehaviorEvent:
        """Track customer behavior event"""
        event = CustomerBehaviorEvent.objects.create(
            customer_id=customer_id,
            event_type=event_type,
            event_data=event_data or {},
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update customer analytics if needed
        if event_type in ['checkout_complete', 'product_view', 'add_to_cart']:
            self.update_customer_analytics(customer_id)
        
        return event
    
    def generate_recommendations(self, customer_id: int, 
                               recommendation_type: str = 'product',
                               limit: int = 5) -> CustomerRecommendation:
        """Generate recommendations for a customer"""
        # Simple recommendation logic - in practice, this would use ML algorithms
        try:
            customer_analytics = CustomerAnalytics.objects.get(customer_id=customer_id)
        except CustomerAnalytics.DoesNotExist:
            customer_analytics = CustomerAnalytics.objects.create(customer_id=customer_id)
        
        # Get customer's preferred categories and brands
        preferred_categories = customer_analytics.preferred_categories
        preferred_brands = customer_analytics.preferred_brands
        
        # Generate dummy recommendations based on preferences
        recommended_items = []
        if preferred_categories:
            recommended_items.extend(preferred_categories[:limit])
        
        confidence_score = Decimal('75.00')  # Dummy confidence score
        
        recommendation = CustomerRecommendation.objects.create(
            customer_id=customer_id,
            recommendation_type=recommendation_type,
            recommended_items=recommended_items,
            confidence_score=confidence_score,
            algorithm_used='collaborative_filtering',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        return recommendation
    
    def update_lifecycle_stage(self, customer_id: int, new_stage: str, 
                             notes: str = '') -> CustomerLifecycleStage:
        """Update customer lifecycle stage"""
        # Get current stage
        current_stage = CustomerLifecycleStage.objects.filter(
            customer_id=customer_id
        ).order_by('-stage_date').first()
        
        previous_stage = current_stage.stage if current_stage else ''
        
        # Create new stage record
        lifecycle_stage = CustomerLifecycleStage.objects.create(
            customer_id=customer_id,
            stage=new_stage,
            previous_stage=previous_stage,
            notes=notes
        )
        
        # Calculate stage duration if there was a previous stage
        if current_stage:
            duration = (timezone.now() - current_stage.stage_date).days
            current_stage.stage_duration = duration
            current_stage.save()
        
        return lifecycle_stage
    
    def calculate_churn_risk(self, customer_id: int) -> Decimal:
        """Calculate churn risk score for a customer"""
        try:
            analytics = CustomerAnalytics.objects.get(customer_id=customer_id)
        except CustomerAnalytics.DoesNotExist:
            return Decimal('0.00')
        
        risk_score = Decimal('0.00')
        
        # Days since last purchase (higher = more risk)
        if analytics.days_since_last_purchase > 90:
            risk_score += Decimal('40.00')
        elif analytics.days_since_last_purchase > 60:
            risk_score += Decimal('25.00')
        elif analytics.days_since_last_purchase > 30:
            risk_score += Decimal('10.00')
        
        # Purchase frequency (lower = more risk)
        if analytics.purchase_frequency < 0.5:  # Less than once every 2 months
            risk_score += Decimal('30.00')
        elif analytics.purchase_frequency < 1.0:  # Less than once per month
            risk_score += Decimal('15.00')
        
        # Total orders (fewer = more risk for existing customers)
        if analytics.total_orders == 1:
            risk_score += Decimal('20.00')
        elif analytics.total_orders < 3:
            risk_score += Decimal('10.00')
        
        # Satisfaction score (lower = more risk)
        if analytics.satisfaction_score and analytics.satisfaction_score < 6:
            risk_score += Decimal('20.00')
        elif analytics.satisfaction_score and analytics.satisfaction_score < 8:
            risk_score += Decimal('10.00')
        
        # Cap at 100
        risk_score = min(risk_score, Decimal('100.00'))
        
        # Update the analytics record
        analytics.churn_risk_score = risk_score
        analytics.save()
        
        return risk_score