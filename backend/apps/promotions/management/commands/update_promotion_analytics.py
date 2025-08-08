"""
Management command to update promotion analytics and performance metrics
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F
from apps.promotions.models import (
    Promotion, PromotionUsage, PromotionAnalytics, PromotionStatus
)
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update promotion analytics and performance metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to process (default: 7)',
        )
        parser.add_argument(
            '--promotion-id',
            type=str,
            help='Process specific promotion by ID',
        )
        parser.add_argument(
            '--recalculate-all',
            action='store_true',
            help='Recalculate all historical analytics',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        promotion_id = options.get('promotion_id')
        recalculate_all = options['recalculate_all']
        
        now = timezone.now()
        
        if recalculate_all:
            start_date = None
            self.stdout.write('Recalculating all historical analytics...')
        else:
            start_date = (now - timedelta(days=days)).date()
            self.stdout.write(f'Processing analytics for the last {days} days...')
        
        # Get promotions to process
        promotions_queryset = Promotion.objects.all()
        
        if promotion_id:
            promotions_queryset = promotions_queryset.filter(id=promotion_id)
            if not promotions_queryset.exists():
                self.stdout.write(
                    self.style.ERROR(f'Promotion with ID {promotion_id} not found.')
                )
                return
        
        processed_count = 0
        
        for promotion in promotions_queryset:
            try:
                self.process_promotion_analytics(promotion, start_date)
                processed_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated analytics for promotion "{promotion.name}" (ID: {promotion.id})'
                    )
                )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing promotion {promotion.id}: {str(e)}'
                    )
                )
                logger.error(f'Error processing promotion {promotion.id}: {str(e)}', exc_info=True)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed analytics for {processed_count} promotions.'
            )
        )
    
    def process_promotion_analytics(self, promotion, start_date=None):
        """Process analytics for a specific promotion"""
        
        # Get usage data
        usage_queryset = PromotionUsage.objects.filter(promotion=promotion)
        
        if start_date:
            usage_queryset = usage_queryset.filter(used_at__date__gte=start_date)
        
        # Group usage by date
        usage_by_date = {}
        for usage in usage_queryset.select_related('customer'):
            date = usage.used_at.date()
            if date not in usage_by_date:
                usage_by_date[date] = {
                    'usages': [],
                    'customers': set(),
                    'channels': {}
                }
            
            usage_by_date[date]['usages'].append(usage)
            usage_by_date[date]['customers'].add(usage.customer.id)
            
            channel = usage.channel
            usage_by_date[date]['channels'][channel] = usage_by_date[date]['channels'].get(channel, 0) + 1
        
        # Update or create analytics for each date
        for date, data in usage_by_date.items():
            usages = data['usages']
            unique_customers = len(data['customers'])
            channel_breakdown = data['channels']
            
            # Calculate metrics
            total_uses = len(usages)
            total_discount = sum(usage.discount_amount for usage in usages)
            total_revenue = sum(usage.final_amount for usage in usages)
            avg_order_value = total_revenue / total_uses if total_uses > 0 else 0
            
            # Update or create analytics record
            analytics, created = PromotionAnalytics.objects.update_or_create(
                promotion=promotion,
                date=date,
                defaults={
                    'total_uses': total_uses,
                    'unique_customers': unique_customers,
                    'total_discount_given': total_discount,
                    'total_revenue_generated': total_revenue,
                    'average_order_value': avg_order_value,
                    'channel_breakdown': channel_breakdown,
                }
            )
            
            # Calculate conversion rate (simplified - would need view data in real implementation)
            # Assuming 10 views per usage for demo purposes
            estimated_views = total_uses * 10
            conversion_rate = (total_uses / estimated_views * 100) if estimated_views > 0 else 0
            analytics.conversion_rate = conversion_rate
            analytics.save(update_fields=['conversion_rate'])
        
        # Update promotion-level metrics
        self.update_promotion_metrics(promotion)
    
    def update_promotion_metrics(self, promotion):
        """Update promotion-level performance metrics"""
        
        # Get aggregated analytics
        analytics_summary = promotion.analytics.aggregate(
            total_uses=Sum('total_uses'),
            total_customers=Sum('unique_customers'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated'),
            avg_conversion_rate=Avg('conversion_rate')
        )
        
        # Update promotion fields
        promotion.usage_count = analytics_summary['total_uses'] or 0
        promotion.budget_spent = analytics_summary['total_discount'] or 0
        promotion.conversion_rate = analytics_summary['avg_conversion_rate'] or 0
        
        # Calculate ROI
        total_revenue = analytics_summary['total_revenue'] or 0
        total_discount = analytics_summary['total_discount'] or 0
        
        if total_discount > 0:
            roi = ((total_revenue - total_discount) / total_discount) * 100
            promotion.roi = roi
        else:
            promotion.roi = 0
        
        promotion.save(update_fields=[
            'usage_count', 'budget_spent', 'conversion_rate', 'roi'
        ])
        
        # Check if promotion should be flagged for review
        self.check_promotion_performance(promotion)
    
    def check_promotion_performance(self, promotion):
        """Check promotion performance and flag if needed"""
        
        # Flag promotions with poor performance
        if promotion.conversion_rate < 1.0 and promotion.usage_count > 100:
            promotion.is_flagged_for_review = True
            promotion.save(update_fields=['is_flagged_for_review'])
            
            logger.warning(
                f'Promotion {promotion.id} flagged for review due to low conversion rate: {promotion.conversion_rate}%'
            )
        
        # Flag promotions approaching budget limit
        if promotion.budget_limit and promotion.budget_spent >= promotion.budget_limit * 0.9:
            promotion.is_flagged_for_review = True
            promotion.save(update_fields=['is_flagged_for_review'])
            
            logger.warning(
                f'Promotion {promotion.id} flagged for review due to high budget usage: {promotion.budget_spent}/{promotion.budget_limit}'
            )
        
        # Flag promotions with high fraud score
        if promotion.fraud_score > 50:
            promotion.is_flagged_for_review = True
            promotion.save(update_fields=['is_flagged_for_review'])
            
            logger.warning(
                f'Promotion {promotion.id} flagged for review due to high fraud score: {promotion.fraud_score}'
            )