"""
Signals for the reviews app.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review, ReviewHelpfulness


@receiver(post_save, sender=Review)
def update_product_rating_on_review_save(sender, instance, created, **kwargs):
    """
    Update product rating aggregation when a review is saved.
    """
    # Only update if review status is approved or if it was just approved
    if instance.status == 'approved':
        instance.product.update_rating_aggregation()
        
        # Update rating distribution
        try:
            rating = instance.product.rating
            rating.update_rating_distribution()
        except:
            pass


@receiver(post_delete, sender=Review)
def update_product_rating_on_review_delete(sender, instance, **kwargs):
    """
    Update product rating aggregation when a review is deleted.
    """
    instance.product.update_rating_aggregation()
    
    # Update rating distribution
    try:
        rating = instance.product.rating
        rating.update_rating_distribution()
    except:
        pass


@receiver(post_save, sender=ReviewHelpfulness)
def update_review_helpfulness_on_vote_save(sender, instance, created, **kwargs):
    """
    Update review helpfulness counts when a vote is saved.
    This is handled in the model's save method, but we can add additional logic here if needed.
    """
    pass


@receiver(post_delete, sender=ReviewHelpfulness)
def update_review_helpfulness_on_vote_delete(sender, instance, **kwargs):
    """
    Update review helpfulness counts when a vote is deleted.
    This is handled in the model's delete method, but we can add additional logic here if needed.
    """
    pass