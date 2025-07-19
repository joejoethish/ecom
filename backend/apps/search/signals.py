"""
Signal processors for Elasticsearch indexing.
"""
from django_elasticsearch_dsl.signals import RealTimeSignalProcessor
from django.db import models
from django.apps import apps
from celery import shared_task


@shared_task
def update_document(app_label, model_name, instance_id, action):
    """
    Celery task to update Elasticsearch document.
    """
    from django_elasticsearch_dsl.registries import registry
    
    model = apps.get_model(app_label, model_name)
    instance = model.objects.filter(id=instance_id).first()
    
    if instance:
        registry.update(instance)
    elif action == 'delete':
        registry.delete(instance_id, app_label, model_name)


@shared_task
def delete_document(instance_id, app_label, model_name):
    """
    Celery task to delete Elasticsearch document.
    """
    from django_elasticsearch_dsl.registries import registry
    
    registry.delete(instance_id, app_label, model_name)


class CelerySignalProcessor(RealTimeSignalProcessor):
    """
    Celery-based signal processor for Elasticsearch indexing.
    This offloads indexing operations to Celery tasks for better performance.
    """
    
    def handle_save(self, sender, instance, **kwargs):
        """
        Handle save signal by dispatching a Celery task.
        """
        try:
            app_label = instance._meta.app_label
            model_name = instance._meta.model_name
            
            update_document.delay(app_label, model_name, str(instance.id), 'save')
        except Exception as e:
            # Fallback to synchronous processing if Celery is not available
            try:
                super().handle_save(sender, instance, **kwargs)
            except Exception as es_error:
                # If Elasticsearch is also not available, just skip indexing
                pass
    
    def handle_delete(self, sender, instance, **kwargs):
        """
        Handle delete signal by dispatching a Celery task.
        """
        try:
            app_label = instance._meta.app_label
            model_name = instance._meta.model_name
            
            delete_document.delay(str(instance.id), app_label, model_name)
        except Exception as e:
            # Fallback to synchronous processing if Celery is not available
            try:
                super().handle_delete(sender, instance, **kwargs)
            except Exception as es_error:
                # If Elasticsearch is also not available, just skip indexing
                pass