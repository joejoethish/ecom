from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import PerformanceAlert, PerformanceMetric, PerformanceIncident
from .utils import AlertManager

logger = logging.getLogger(__name__)

@receiver(post_save, sender=PerformanceMetric)
def check_performance_thresholds(sender, instance, created, **kwargs):
    """Automatically check thresholds when new metrics are created"""
    if created and instance.severity in ['high', 'critical']:
        # Check if we need to create alerts
        try:
            alerts = AlertManager.check_thresholds()
            
            # Send notifications for critical alerts
            for alert in alerts:
                if alert.severity == 'critical':
                    send_alert_notification(alert)
                    
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")

@receiver(post_save, sender=PerformanceAlert)
def handle_new_alert(sender, instance, created, **kwargs):
    """Handle new performance alerts"""
    if created:
        logger.warning(f"New performance alert created: {instance.name} - {instance.severity}")
        
        # Auto-create incident for critical alerts
        if instance.severity == 'critical':
            try:
                # Check if similar incident already exists
                existing_incident = PerformanceIncident.objects.filter(
                    status__in=['open', 'investigating'],
                    incident_type='degradation',
                    started_at__gte=timezone.now() - timezone.timedelta(hours=1)
                ).first()
                
                if not existing_incident:
                    incident_count = PerformanceIncident.objects.count() + 1
                    incident_id = f"PERF-{incident_count:04d}"
                    
                    PerformanceIncident.objects.create(
                        incident_id=incident_id,
                        title=f"Performance Alert: {instance.name}",
                        description=f"Critical performance alert triggered: {instance.description}",
                        incident_type='degradation',
                        severity=instance.severity,
                        affected_services=[instance.metric_type],
                        timeline=[{
                            'timestamp': timezone.now().isoformat(),
                            'action': 'incident_created',
                            'user': 'system',
                            'comment': f'Auto-created from alert {instance.id}'
                        }],
                        created_by_id=1  # System user
                    )
                    
            except Exception as e:
                logger.error(f"Error creating incident from alert: {e}")

def send_alert_notification(alert):
    """Send alert notification via email"""
    try:
        subject = f"[CRITICAL] Performance Alert: {alert.name}"
        message = f"""
        A critical performance alert has been triggered:
        
        Alert: {alert.name}
        Description: {alert.description}
        Metric: {alert.metric_type}
        Current Value: {alert.current_value}
        Threshold: {alert.threshold_value}
        Severity: {alert.severity}
        Time: {alert.triggered_at}
        
        Please investigate immediately.
        """
        
        # Get admin emails from settings
        admin_emails = getattr(settings, 'PERFORMANCE_ALERT_EMAILS', [])
        
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            alert.notification_sent = True
            alert.save()
            
    except Exception as e:
        logger.error(f"Error sending alert notification: {e}")

@receiver(post_save, sender=PerformanceIncident)
def handle_incident_status_change(sender, instance, created, **kwargs):
    """Handle incident status changes"""
    if not created:
        # Log status changes
        logger.info(f"Incident {instance.incident_id} status changed to {instance.status}")
        
        # Send notifications for resolved incidents
        if instance.status == 'resolved' and instance.severity in ['high', 'critical']:
            try:
                subject = f"[RESOLVED] Performance Incident: {instance.title}"
                message = f"""
                Performance incident has been resolved:
                
                Incident ID: {instance.incident_id}
                Title: {instance.title}
                Severity: {instance.severity}
                Duration: {(instance.resolved_at - instance.started_at).total_seconds() / 60:.0f} minutes
                Resolution: {instance.resolution}
                
                The system is now operating normally.
                """
                
                admin_emails = getattr(settings, 'PERFORMANCE_ALERT_EMAILS', [])
                
                if admin_emails:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=False
                    )
                    
            except Exception as e:
                logger.error(f"Error sending incident resolution notification: {e}")

# Cleanup old performance data
@receiver(pre_delete, sender=PerformanceMetric)
def log_metric_deletion(sender, instance, **kwargs):
    """Log when performance metrics are deleted"""
    logger.info(f"Deleting performance metric: {instance.metric_type} - {instance.name}")

# Auto-cleanup task (would be called by Celery task)
def cleanup_old_performance_data():
    """Clean up old performance data to prevent database bloat"""
    try:
        # Keep metrics for 30 days
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        # Delete old metrics except critical ones
        old_metrics = PerformanceMetric.objects.filter(
            timestamp__lt=cutoff_date
        ).exclude(severity='critical')
        
        deleted_count = old_metrics.count()
        old_metrics.delete()
        
        logger.info(f"Cleaned up {deleted_count} old performance metrics")
        
        # Keep database logs for 7 days
        db_cutoff_date = timezone.now() - timezone.timedelta(days=7)
        old_db_logs = DatabasePerformanceLog.objects.filter(
            timestamp__lt=db_cutoff_date
        ).exclude(is_slow_query=True)
        
        db_deleted_count = old_db_logs.count()
        old_db_logs.delete()
        
        logger.info(f"Cleaned up {db_deleted_count} old database performance logs")
        
    except Exception as e:
        logger.error(f"Error cleaning up old performance data: {e}")