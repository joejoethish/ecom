from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import CustomerAnalytics
from .services import CustomerAnalyticsService

User = get_user_model()


@receiver(post_save, sender=User)
def create_customer_analytics(sender, instance, created, **kwargs):
    """Create customer analytics record when a new user is created"""
    if created:
        CustomerAnalytics.objects.get_or_create(customer=instance)


@receiver(post_save, sender=CustomerAnalytics)
def update_churn_risk(sender, instance, **kwargs):
    """Update churn risk score when analytics are updated"""
    if not kwargs.get('raw', False) and not getattr(instance, '_updating_churn_risk', False):
        # Set flag to prevent recursion
        instance._updating_churn_risk = True
        try:
            service = CustomerAnalyticsService()
            service.calculate_churn_risk(instance.customer.id)
        finally:
            # Always clear the flag
            instance._updating_churn_risk = False