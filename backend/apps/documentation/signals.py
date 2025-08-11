from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from django.utils import timezone
from .models import Documentation, DocumentationVersion


@receiver(pre_save, sender=Documentation)
def update_search_vector(sender, instance, **kwargs):
    """Update search vector when documentation is saved"""
    if instance.title and instance.content:
        instance.search_vector = (
            SearchVector('title', weight='A') +
            SearchVector('content', weight='B') +
            SearchVector('excerpt', weight='C')
        )


@receiver(post_save, sender=Documentation)
def create_initial_version(sender, instance, created, **kwargs):
    """Create initial version when documentation is first created"""
    if created:
        DocumentationVersion.objects.create(
            documentation=instance,
            version_number=instance.version,
            title=instance.title,
            content=instance.content,
            metadata=instance.metadata,
            changes_summary='Initial version',
            created_by=instance.author
        )


@receiver(post_save, sender=Documentation)
def update_published_date(sender, instance, **kwargs):
    """Update published date when status changes to published"""
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])