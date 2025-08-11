from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
import logging
import os

from .models import *

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MLModel)
def ml_model_post_save(sender, instance, created, **kwargs):
    """Handle ML model save events"""
    if created:
        logger.info(f"New ML model created: {instance.name} ({instance.model_type})")
        
        # Clear model cache
        cache_key = f"ml_models_{instance.model_type}"
        cache.delete(cache_key)
        
        # Log model creation
        from apps.logs.models import SystemLog
        SystemLog.objects.create(
            level='INFO',
            message=f"ML model created: {instance.name}",
            category='ml_ai',
            details={
                'model_id': str(instance.id),
                'model_type': instance.model_type,
                'status': instance.status
            }
        )
    
    # Update model status cache
    if instance.status == 'active':
        cache_key = f"active_model_{instance.model_type}"
        cache.set(cache_key, instance.id, timeout=3600)  # 1 hour
    
    # Log status changes
    if not created and instance.status in ['active', 'inactive', 'deprecated']:
        logger.info(f"ML model status changed: {instance.name} -> {instance.status}")


@receiver(pre_delete, sender=MLModel)
def ml_model_pre_delete(sender, instance, **kwargs):
    """Handle ML model deletion"""
    logger.info(f"ML model being deleted: {instance.name}")
    
    # Clean up model files
    if instance.model_file_path and os.path.exists(instance.model_file_path):
        try:
            os.remove(instance.model_file_path)
            logger.info(f"Deleted model file: {instance.model_file_path}")
        except Exception as e:
            logger.error(f"Error deleting model file: {str(e)}")
    
    # Clear caches
    cache_key = f"ml_models_{instance.model_type}"
    cache.delete(cache_key)
    
    cache_key = f"active_model_{instance.model_type}"
    cache.delete(cache_key)


@receiver(post_save, sender=MLPrediction)
def ml_prediction_post_save(sender, instance, created, **kwargs):
    """Handle ML prediction save events"""
    if created:
        # Update model usage statistics
        model = instance.model
        model_stats_key = f"model_stats_{model.id}"
        
        stats = cache.get(model_stats_key, {
            'total_predictions': 0,
            'last_prediction': None
        })
        
        stats['total_predictions'] += 1
        stats['last_prediction'] = timezone.now().isoformat()
        
        cache.set(model_stats_key, stats, timeout=86400)  # 24 hours
        
        # Log high-confidence predictions
        if instance.confidence_score and instance.confidence_score > 0.9:
            logger.info(f"High-confidence prediction: {instance.confidence_score:.3f} for model {model.name}")


@receiver(post_save, sender=FraudDetection)
def fraud_detection_post_save(sender, instance, created, **kwargs):
    """Handle fraud detection events"""
    if created and instance.risk_level in ['high', 'critical']:
        logger.warning(f"High fraud risk detected: {instance.transaction_id} - {instance.risk_level}")
        
        # Send alert notification
        from apps.notifications.models import Notification
        Notification.objects.create(
            title=f"High Fraud Risk Detected",
            message=f"Transaction {instance.transaction_id} flagged as {instance.risk_level} risk",
            notification_type='security_alert',
            priority='high' if instance.risk_level == 'high' else 'critical',
            data={
                'transaction_id': instance.transaction_id,
                'risk_score': instance.risk_score,
                'risk_factors': instance.risk_factors
            }
        )
        
        # Update fraud statistics cache
        fraud_stats_key = "fraud_detection_stats"
        stats = cache.get(fraud_stats_key, {
            'total_high_risk': 0,
            'total_critical_risk': 0,
            'last_alert': None
        })
        
        if instance.risk_level == 'high':
            stats['total_high_risk'] += 1
        elif instance.risk_level == 'critical':
            stats['total_critical_risk'] += 1
        
        stats['last_alert'] = timezone.now().isoformat()
        cache.set(fraud_stats_key, stats, timeout=86400)


@receiver(post_save, sender=ChurnPrediction)
def churn_prediction_post_save(sender, instance, created, **kwargs):
    """Handle churn prediction events"""
    if created and instance.risk_level in ['medium', 'high']:
        logger.info(f"Customer churn risk detected: {instance.customer_id} - {instance.risk_level}")
        
        # Create retention task
        from apps.notifications.models import Notification
        Notification.objects.create(
            title=f"Customer Churn Risk: {instance.risk_level.title()}",
            message=f"Customer {instance.customer_id} has {instance.churn_probability:.1%} churn probability",
            notification_type='customer_retention',
            priority='medium' if instance.risk_level == 'medium' else 'high',
            data={
                'customer_id': instance.customer_id,
                'churn_probability': instance.churn_probability,
                'retention_actions': instance.retention_actions
            }
        )


@receiver(post_save, sender=AnomalyDetection)
def anomaly_detection_post_save(sender, instance, created, **kwargs):
    """Handle anomaly detection events"""
    if created:
        logger.warning(f"Anomaly detected: {instance.anomaly_type} - Score: {instance.anomaly_score:.3f}")
        
        # Send alert for significant anomalies
        if instance.anomaly_score < -0.3:  # Significant anomaly threshold
            from apps.notifications.models import Notification
            Notification.objects.create(
                title=f"Business Anomaly Detected",
                message=f"{instance.anomaly_type.replace('_', ' ').title()} anomaly detected",
                notification_type='business_alert',
                priority='high' if instance.anomaly_score < -0.5 else 'medium',
                data={
                    'anomaly_type': instance.anomaly_type,
                    'anomaly_score': instance.anomaly_score,
                    'data_point': instance.data_point
                }
            )
        
        # Update anomaly statistics
        anomaly_stats_key = f"anomaly_stats_{instance.anomaly_type}"
        stats = cache.get(anomaly_stats_key, {
            'total_anomalies': 0,
            'avg_score': 0,
            'last_anomaly': None
        })
        
        stats['total_anomalies'] += 1
        stats['avg_score'] = (stats['avg_score'] * (stats['total_anomalies'] - 1) + instance.anomaly_score) / stats['total_anomalies']
        stats['last_anomaly'] = timezone.now().isoformat()
        
        cache.set(anomaly_stats_key, stats, timeout=86400)


@receiver(post_save, sender=MLTrainingJob)
def training_job_post_save(sender, instance, created, **kwargs):
    """Handle training job events"""
    if not created:
        # Log status changes
        if instance.status == 'completed':
            logger.info(f"Training job completed: {instance.model.name}")
            
            # Update model status
            instance.model.status = 'active'
            instance.model.last_trained = timezone.now()
            instance.model.save()
            
        elif instance.status == 'failed':
            logger.error(f"Training job failed: {instance.model.name} - {instance.error_message}")
            
            # Update model status
            instance.model.status = 'inactive'
            instance.model.save()
            
            # Send failure notification
            from apps.notifications.models import Notification
            Notification.objects.create(
                title="ML Model Training Failed",
                message=f"Training failed for {instance.model.name}",
                notification_type='system_alert',
                priority='medium',
                data={
                    'model_id': str(instance.model.id),
                    'error_message': instance.error_message
                }
            )


@receiver(post_save, sender=AIInsight)
def ai_insight_post_save(sender, instance, created, **kwargs):
    """Handle AI insight events"""
    if created:
        logger.info(f"New AI insight generated: {instance.title} ({instance.priority})")
        
        # Send notification for high-priority insights
        if instance.priority in ['high', 'critical']:
            from apps.notifications.models import Notification
            Notification.objects.create(
                title=f"AI Insight: {instance.title}",
                message=instance.description,
                notification_type='business_insight',
                priority=instance.priority,
                data={
                    'insight_id': str(instance.id),
                    'insight_type': instance.insight_type,
                    'recommendations': instance.recommendations,
                    'confidence_level': instance.confidence_level
                }
            )
        
        # Update insight statistics
        insight_stats_key = f"ai_insights_{instance.insight_type}"
        stats = cache.get(insight_stats_key, {
            'total_insights': 0,
            'avg_confidence': 0,
            'last_insight': None
        })
        
        stats['total_insights'] += 1
        stats['avg_confidence'] = (stats['avg_confidence'] * (stats['total_insights'] - 1) + instance.confidence_level) / stats['total_insights']
        stats['last_insight'] = timezone.now().isoformat()
        
        cache.set(insight_stats_key, stats, timeout=86400)