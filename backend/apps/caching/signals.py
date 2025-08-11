from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import CacheConfiguration, CacheMetrics, CacheAlert
from .cache_manager import cache_manager
from .optimization import cache_optimizer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=CacheConfiguration)
def cache_configuration_changed(sender, instance, created, **kwargs):
    """Handle cache configuration changes"""
    try:
        if created:
            logger.info(f"New cache configuration created: {instance.name}")
        else:
            logger.info(f"Cache configuration updated: {instance.name}")
        
        # Invalidate related cache entries if configuration changed
        if not created:
            # This would typically invalidate cache entries for this configuration
            logger.info(f"Invalidating cache entries for {instance.name}")
            
        # Trigger health check for the cache
        if instance.is_active:
            try:
                health = cache_optimizer.monitor_cache_health(instance.name)
                
                # Create alerts if health issues are detected
                if health.get('health_score', 100) < 75:
                    for alert_data in health.get('alerts', []):
                        CacheAlert.objects.get_or_create(
                            cache_name=instance.name,
                            alert_type=alert_data.alert_type,
                            severity=alert_data.severity,
                            defaults={
                                'message': alert_data.message,
                                'threshold_value': alert_data.threshold_value,
                                'current_value': alert_data.current_value
                            }
                        )
                        
            except Exception as e:
                logger.error(f"Health check failed for {instance.name}: {e}")
                
    except Exception as e:
        logger.error(f"Cache configuration signal handler failed: {e}")


@receiver(post_delete, sender=CacheConfiguration)
def cache_configuration_deleted(sender, instance, **kwargs):
    """Handle cache configuration deletion"""
    try:
        logger.info(f"Cache configuration deleted: {instance.name}")
        
        # Clean up related data
        CacheMetrics.objects.filter(cache_name=instance.name).delete()
        CacheAlert.objects.filter(cache_name=instance.name).delete()
        
        # Invalidate all cache entries for this configuration
        cache_manager.invalidate_pattern(f"{instance.name}:*", instance.name)
        
    except Exception as e:
        logger.error(f"Cache configuration deletion handler failed: {e}")


@receiver(post_save, sender=CacheMetrics)
def cache_metrics_saved(sender, instance, created, **kwargs):
    """Handle new cache metrics"""
    try:
        if not created:
            return
        
        # Check for performance issues and create alerts
        alerts_to_create = []
        
        # Check hit ratio
        if instance.hit_ratio < 0.7:
            alerts_to_create.append({
                'alert_type': 'high_miss_ratio',
                'severity': 'high' if instance.hit_ratio < 0.5 else 'medium',
                'message': f'Hit ratio is {instance.hit_ratio:.2%}, below optimal threshold',
                'threshold_value': 0.7,
                'current_value': instance.hit_ratio
            })
        
        # Check response time
        if instance.avg_response_time_ms > 100:
            alerts_to_create.append({
                'alert_type': 'slow_response',
                'severity': 'high' if instance.avg_response_time_ms > 200 else 'medium',
                'message': f'Average response time is {instance.avg_response_time_ms:.2f}ms, above threshold',
                'threshold_value': 100,
                'current_value': instance.avg_response_time_ms
            })
        
        # Check memory usage
        if instance.memory_usage_percent > 85:
            alerts_to_create.append({
                'alert_type': 'memory_usage',
                'severity': 'critical' if instance.memory_usage_percent > 95 else 'high',
                'message': f'Memory usage is {instance.memory_usage_percent:.1f}%, above threshold',
                'threshold_value': 85,
                'current_value': instance.memory_usage_percent
            })
        
        # Check error rate
        total_operations = instance.get_operations + instance.set_operations
        if total_operations > 0:
            error_rate = instance.error_count / total_operations
            if error_rate > 0.05:
                alerts_to_create.append({
                    'alert_type': 'error_rate',
                    'severity': 'critical' if error_rate > 0.1 else 'high',
                    'message': f'Error rate is {error_rate:.2%}, above threshold',
                    'threshold_value': 0.05,
                    'current_value': error_rate
                })
        
        # Create alerts (avoid duplicates)
        for alert_data in alerts_to_create:
            # Check if similar alert already exists and is not resolved
            existing_alert = CacheAlert.objects.filter(
                cache_name=instance.cache_name,
                alert_type=alert_data['alert_type'],
                is_resolved=False,
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).first()
            
            if not existing_alert:
                CacheAlert.objects.create(
                    cache_name=instance.cache_name,
                    **alert_data
                )
                logger.warning(f"Cache alert created: {alert_data['alert_type']} for {instance.cache_name}")
                
    except Exception as e:
        logger.error(f"Cache metrics signal handler failed: {e}")


@receiver(post_save, sender=CacheAlert)
def cache_alert_created(sender, instance, created, **kwargs):
    """Handle new cache alerts"""
    try:
        if not created:
            return
        
        logger.warning(f"New cache alert: {instance.alert_type} for {instance.cache_name} ({instance.severity})")
        
        # Send notifications for critical alerts
        if instance.severity == 'critical':
            # This would typically send email/SMS notifications
            logger.critical(f"Critical cache alert: {instance.message}")
            
            # You could integrate with notification services here
            # send_alert_notification(instance)
        
        # Trigger automatic optimization for certain alert types
        if instance.alert_type in ['high_miss_ratio', 'memory_usage', 'slow_response']:
            try:
                # Run optimization analysis
                optimization_result = cache_optimizer.optimize_cache_configuration(instance.cache_name)
                
                if optimization_result.get('optimizations_found', 0) > 0:
                    logger.info(f"Automatic optimization suggestions generated for {instance.cache_name}")
                    
            except Exception as e:
                logger.error(f"Automatic optimization failed: {e}")
                
    except Exception as e:
        logger.error(f"Cache alert signal handler failed: {e}")


@receiver(pre_save, sender=CacheAlert)
def cache_alert_resolving(sender, instance, **kwargs):
    """Handle cache alert resolution"""
    try:
        if instance.pk:  # Existing instance
            old_instance = CacheAlert.objects.get(pk=instance.pk)
            
            # Check if alert is being resolved
            if not old_instance.is_resolved and instance.is_resolved:
                logger.info(f"Cache alert resolved: {instance.alert_type} for {instance.cache_name}")
                
                # Set resolution timestamp if not already set
                if not instance.resolved_at:
                    instance.resolved_at = timezone.now()
                    
    except CacheAlert.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Cache alert resolution handler failed: {e}")


# Custom signal for cache operations
import django.dispatch

cache_operation_performed = django.dispatch.Signal()


@receiver(cache_operation_performed)
def handle_cache_operation(sender, operation, cache_name, key, success, response_time, **kwargs):
    """Handle cache operation signals"""
    try:
        # This would be called by the cache manager to track operations
        logger.debug(f"Cache {operation} on {cache_name}: {key} ({'success' if success else 'failed'}) in {response_time:.3f}ms")
        
        # Update real-time metrics
        # This could be used to update dashboard metrics in real-time
        
    except Exception as e:
        logger.error(f"Cache operation signal handler failed: {e}")


# Signal for cache warming completion
cache_warming_completed = django.dispatch.Signal()


@receiver(cache_warming_completed)
def handle_cache_warming_completion(sender, cache_name, keys_warmed, success_count, failure_count, **kwargs):
    """Handle cache warming completion"""
    try:
        logger.info(f"Cache warming completed for {cache_name}: {success_count} successful, {failure_count} failed")
        
        # Update warming statistics
        from .models import CacheWarming
        
        warming_configs = CacheWarming.objects.filter(cache_name=cache_name, is_active=True)
        for config in warming_configs:
            config.success_count += success_count
            config.failure_count += failure_count
            config.last_run = timezone.now()
            config.save()
            
    except Exception as e:
        logger.error(f"Cache warming completion handler failed: {e}")


# Signal for cache invalidation
cache_invalidation_performed = django.dispatch.Signal()


@receiver(cache_invalidation_performed)
def handle_cache_invalidation(sender, cache_name, keys, pattern, invalidation_type, user, **kwargs):
    """Handle cache invalidation signals"""
    try:
        logger.info(f"Cache invalidation performed on {cache_name}: type={invalidation_type}")
        
        # This signal would be sent by the cache manager when invalidations occur
        # It allows for additional processing or logging
        
    except Exception as e:
        logger.error(f"Cache invalidation signal handler failed: {e}")