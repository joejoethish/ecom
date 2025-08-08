"""
Promotion and Coupon Management Signals
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import F
from decimal import Decimal
from .models import (
    PromotionUsage, PromotionAnalytics, Promotion, Coupon,
    PromotionAuditLog, PromotionSchedule
)


@receiver(post_save, sender=PromotionUsage)
def update_promotion_analytics(sender, instance, created, **kwargs):
    """Update promotion analytics when usage is recorded"""
    if created:
        # Update promotion usage count
        instance.promotion.usage_count = F('usage_count') + 1
        instance.promotion.budget_spent = F('budget_spent') + instance.discount_amount
        instance.promotion.save(update_fields=['usage_count', 'budget_spent'])
        
        # Update coupon usage count if applicable
        if instance.coupon:
            instance.coupon.usage_count = F('usage_count') + 1
            instance.coupon.save(update_fields=['usage_count'])
        
        # Update or create daily analytics
        date = instance.used_at.date()
        analytics, created = PromotionAnalytics.objects.get_or_create(
            promotion=instance.promotion,
            date=date,
            defaults={
                'total_uses': 1,
                'unique_customers': 1,
                'total_discount_given': instance.discount_amount,
                'total_revenue_generated': instance.final_amount,
                'average_order_value': instance.final_amount,
                'channel_breakdown': {instance.channel: 1}
            }
        )
        
        if not created:
            # Update existing analytics
            analytics.total_uses = F('total_uses') + 1
            analytics.total_discount_given = F('total_discount_given') + instance.discount_amount
            analytics.total_revenue_generated = F('total_revenue_generated') + instance.final_amount
            
            # Update channel breakdown
            channel_breakdown = analytics.channel_breakdown or {}
            channel_breakdown[instance.channel] = channel_breakdown.get(instance.channel, 0) + 1
            analytics.channel_breakdown = channel_breakdown
            
            analytics.save()
            
            # Recalculate average order value
            analytics.refresh_from_db()
            if analytics.total_uses > 0:
                analytics.average_order_value = analytics.total_revenue_generated / analytics.total_uses
                analytics.save(update_fields=['average_order_value'])


@receiver(post_save, sender=PromotionUsage)
def detect_promotion_fraud(sender, instance, created, **kwargs):
    """Detect potential fraud in promotion usage"""
    if created:
        fraud_reasons = []
        fraud_score = 0
        
        # Check for rapid usage from same IP
        recent_usage = PromotionUsage.objects.filter(
            ip_address=instance.ip_address,
            used_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).count()
        
        if recent_usage > 5:
            fraud_reasons.append('Rapid usage from same IP')
            fraud_score += 30
        
        # Check for unusual discount amounts
        avg_discount = PromotionUsage.objects.filter(
            promotion=instance.promotion
        ).aggregate(avg_discount=models.Avg('discount_amount'))['avg_discount']
        
        if avg_discount and instance.discount_amount > avg_discount * 3:
            fraud_reasons.append('Unusually high discount amount')
            fraud_score += 25
        
        # Check for suspicious user agent patterns
        if not instance.user_agent or len(instance.user_agent) < 20:
            fraud_reasons.append('Suspicious or missing user agent')
            fraud_score += 15
        
        # Check for usage outside normal hours (if pattern exists)
        hour = instance.used_at.hour
        if hour < 6 or hour > 23:
            fraud_reasons.append('Usage outside normal hours')
            fraud_score += 10
        
        # Update fraud detection fields
        if fraud_score > 30:
            instance.is_suspicious = True
            instance.fraud_reasons = fraud_reasons
            instance.save(update_fields=['is_suspicious', 'fraud_reasons'])
            
            # Flag promotion for review if fraud score is high
            if fraud_score > 50:
                instance.promotion.fraud_score = F('fraud_score') + fraud_score
                instance.promotion.is_flagged_for_review = True
                instance.promotion.save(update_fields=['fraud_score', 'is_flagged_for_review'])


@receiver(pre_save, sender=Promotion)
def promotion_status_change_handler(sender, instance, **kwargs):
    """Handle promotion status changes"""
    if instance.pk:
        try:
            old_instance = Promotion.objects.get(pk=instance.pk)
            
            # Check if status changed to active
            if old_instance.status != 'active' and instance.status == 'active':
                # Validate promotion can be activated
                now = timezone.now()
                if instance.start_date > now:
                    # Schedule activation
                    PromotionSchedule.objects.get_or_create(
                        promotion=instance,
                        action='activate',
                        scheduled_time=instance.start_date,
                        defaults={'is_executed': False}
                    )
                
                # Schedule deactivation
                if instance.end_date:
                    PromotionSchedule.objects.get_or_create(
                        promotion=instance,
                        action='deactivate',
                        scheduled_time=instance.end_date,
                        defaults={'is_executed': False}
                    )
            
            # Check if end date changed
            if old_instance.end_date != instance.end_date and instance.end_date:
                # Update scheduled deactivation
                PromotionSchedule.objects.filter(
                    promotion=instance,
                    action='deactivate',
                    is_executed=False
                ).update(scheduled_time=instance.end_date)
        
        except Promotion.DoesNotExist:
            pass


@receiver(post_save, sender=Promotion)
def calculate_promotion_roi(sender, instance, **kwargs):
    """Calculate ROI for promotion"""
    if instance.budget_spent > 0:
        # Get total revenue generated
        total_revenue = PromotionAnalytics.objects.filter(
            promotion=instance
        ).aggregate(
            total_revenue=models.Sum('total_revenue_generated')
        )['total_revenue'] or 0
        
        # Calculate ROI
        if instance.budget_spent > 0:
            roi = ((total_revenue - instance.budget_spent) / instance.budget_spent) * 100
            instance.roi = roi
            instance.save(update_fields=['roi'])


@receiver(post_save, sender=PromotionUsage)
def update_conversion_rate(sender, instance, created, **kwargs):
    """Update promotion conversion rate"""
    if created:
        # This would need integration with website analytics to track
        # promotion views vs usage for accurate conversion rate
        # For now, we'll use a simplified calculation
        
        # Get total promotion exposures (this would come from analytics)
        # For demo purposes, we'll assume 10 exposures per usage
        estimated_exposures = instance.promotion.usage_count * 10
        
        if estimated_exposures > 0:
            conversion_rate = (instance.promotion.usage_count / estimated_exposures) * 100
            instance.promotion.conversion_rate = conversion_rate
            instance.promotion.save(update_fields=['conversion_rate'])


# Import models for signal registration
from django.db import models