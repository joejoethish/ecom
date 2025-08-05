"""
Signal processors for Elasticsearch indexing.
"""
from django_elasticsearch_dsl.signals import RealTimeSignalProcessor
from django.db import models
from django.apps import apps
from django.utils import timezone
from celery import shared_task
from tasks.monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def update_document(self, app_label, model_name, instance_id, action):
    """
    Celery task to update Elasticsearch document with monitoring and retry logic.
    Also sends real-time WebSocket updates when products are indexed.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from django_elasticsearch_dsl.registries import registry
        
        logger.info(f"Updating Elasticsearch document: {app_label}.{model_name} ID: {instance_id}")
        
        model = apps.get_model(app_label, model_name)
        instance = model.objects.filter(id=instance_id).first()
        
        if instance:
            registry.update(instance)
            logger.info(f"Successfully updated document in Elasticsearch: {app_label}.{model_name} ID: {instance_id}")
            
            # Send real-time WebSocket update for product indexing
            if app_label == 'products' and model_name == 'product':
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    from django.utils import timezone
                    
                    channel_layer = get_channel_layer()
                    
                    # Send to inventory updates group (for admin/seller dashboards)
                    product_data = {
                        'id': str(instance.id),
                        'name': instance.name,
                        'sku': instance.sku,
                        'price': float(instance.price),
                        'category': instance.category.name if instance.category else None,
                        'is_active': instance.is_active
                    }
                    
                    async_to_sync(channel_layer.group_send)(
                        'inventory_updates',
                        {
                            'type': 'inventory_update',
                            'update_type': 'product_indexed',
                            'product_id': str(instance.id),
                            'data': product_data,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                except Exception as ws_exc:
                    logger.error(f"Error sending WebSocket update: {str(ws_exc)}")
            
            return {"status": "success", "action": "update", "document_id": instance_id}
        elif action == 'delete':
            registry.delete(instance_id, app_label, model_name)
            logger.info(f"Successfully deleted document from Elasticsearch: {app_label}.{model_name} ID: {instance_id}")
            return {"status": "success", "action": "delete", "document_id": instance_id}
        else:
            logger.warning(f"Instance not found for indexing: {app_label}.{model_name} ID: {instance_id}")
            return {"status": "warning", "message": "Instance not found", "document_id": instance_id}
            
    except Exception as exc:
        logger.error(f"Error updating Elasticsearch document: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def delete_document(self, instance_id, app_label, model_name):
    """
    Celery task to delete Elasticsearch document with monitoring and retry logic.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from django_elasticsearch_dsl.registries import registry
        
        logger.info(f"Deleting Elasticsearch document: {app_label}.{model_name} ID: {instance_id}")
        
        registry.delete(instance_id, app_label, model_name)
        
        logger.info(f"Successfully deleted document from Elasticsearch: {app_label}.{model_name} ID: {instance_id}")
        return {"status": "success", "action": "delete", "document_id": instance_id}
        
    except Exception as exc:
        logger.error(f"Error deleting Elasticsearch document: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


class CelerySignalProcessor(RealTimeSignalProcessor):
    """
    Celery-based signal processor for Elasticsearch indexing.
    This offloads indexing operations to Celery tasks for better performance.
    """
    
    def handle_save(self, sender, instance, **kwargs):
        """
        Handle save signal by dispatching a Celery task.
        """
        from django.conf import settings
        
        try:
            app_label = instance._meta.app_label
            model_name = instance._meta.model_name
            
            # Skip Celery tasks during testing
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                # Run synchronously during tests
                try:
                    update_document(app_label, model_name, str(instance.id), 'save')
                except Exception:
                    # Ignore Elasticsearch errors during testing
                    pass
            else:
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
        from django.conf import settings
        
        try:
            app_label = instance._meta.app_label
            model_name = instance._meta.model_name
            
            # Skip Celery tasks during testing
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                # Run synchronously during tests
                try:
                    delete_document(str(instance.id), app_label, model_name)
                except Exception:
                    # Ignore Elasticsearch errors during testing
                    pass
            else:
                delete_document.delay(str(instance.id), app_label, model_name)
        except Exception as e:
            # Fallback to synchronous processing if Celery is not available
            try:
                super().handle_delete(sender, instance, **kwargs)
            except Exception as es_error:
                # If Elasticsearch is also not available, just skip indexing
                pass
