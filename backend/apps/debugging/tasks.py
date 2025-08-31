"""
Celery tasks for debugging and monitoring system
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .production_monitoring import cleanup_old_data
from .models import PerformanceSnapshot, ErrorLog, WorkflowSession


@shared_task(bind=True, max_retries=3)
def cleanup_monitoring_data(self, days_to_keep=30):
    """
    Celery task to clean up old monitoring data
    
    Args:
        days_to_keep (int): Number of days of data to retain
    
    Returns:
        dict: Cleanup results
    """
    try:
        logging.info(f"Starting monitoring data cleanup, keeping {days_to_keep} days")
        
        result = cleanup_old_data(days_to_keep)
        
        logging.info(f"Monitoring data cleanup completed: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in monitoring data cleanup task: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            raise self.retry(countdown=retry_delay, exc=e)
        
        # Final failure
        return {'error': str(e), 'retries_exhausted': True}


@shared_task(bind=True)
def generate_performance_report(self, hours=24):
    """
    Generate performance report for specified time period
    
    Args:
        hours (int): Number of hours to include in report
    
    Returns:
        dict: Performance report data
    """
    try:
        from django.db import models
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get performance metrics summary
        metrics_summary = PerformanceSnapshot.objects.filter(
            timestamp__gte=cutoff_time
        ).values('layer', 'component', 'metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value'),
            min_value=models.Min('metric_value'),
            count=models.Count('id')
        ).order_by('layer', 'component', 'metric_name')
        
        # Get error summary
        error_summary = ErrorLog.objects.filter(
            timestamp__gte=cutoff_time
        ).values('layer', 'component', 'error_type').annotate(
            error_count=models.Count('id')
        ).order_by('-error_count')
        
        # Get workflow session summary
        workflow_summary = WorkflowSession.objects.filter(
            created_at__gte=cutoff_time
        ).aggregate(
            total_sessions=models.Count('id'),
            completed_sessions=models.Count('id', filter=models.Q(status='completed')),
            failed_sessions=models.Count('id', filter=models.Q(status='failed')),
            avg_duration=models.Avg('duration_seconds')
        )
        
        report = {
            'report_period_hours': hours,
            'generated_at': timezone.now().isoformat(),
            'metrics_summary': list(metrics_summary),
            'error_summary': list(error_summary),
            'workflow_summary': workflow_summary,
            'total_metrics_collected': sum(m['count'] for m in metrics_summary),
            'total_errors': sum(e['error_count'] for e in error_summary)
        }
        
        logging.info(f"Generated performance report for {hours} hours: "
                    f"{report['total_metrics_collected']} metrics, "
                    f"{report['total_errors']} errors")
        
        return report
        
    except Exception as e:
        logging.error(f"Error generating performance report: {e}")
        return {'error': str(e)}


@shared_task(bind=True)
def health_check_all_services(self):
    """
    Run comprehensive health checks on all services
    
    Returns:
        dict: Health check results
    """
    try:
        from .production_monitoring import health_service
        
        health_results = health_service.run_all_health_checks()
        
        # Convert to serializable format
        results = []
        for result in health_results:
            results.append({
                'service': result.service,
                'status': result.status,
                'response_time_ms': result.response_time_ms,
                'details': result.details,
                'timestamp': result.timestamp.isoformat(),
                'error_message': result.error_message
            })
        
        # Determine overall health
        unhealthy_count = len([r for r in results if r['status'] == 'unhealthy'])
        degraded_count = len([r for r in results if r['status'] == 'degraded'])
        
        overall_status = 'healthy'
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        
        health_summary = {
            'overall_status': overall_status,
            'total_services': len(results),
            'healthy_services': len([r for r in results if r['status'] == 'healthy']),
            'degraded_services': degraded_count,
            'unhealthy_services': unhealthy_count,
            'check_timestamp': timezone.now().isoformat(),
            'service_results': results
        }
        
        logging.info(f"Health check completed: {overall_status} "
                    f"({health_summary['healthy_services']}/{health_summary['total_services']} healthy)")
        
        return health_summary
        
    except Exception as e:
        logging.error(f"Error in health check task: {e}")
        return {'error': str(e), 'overall_status': 'unhealthy'}


@shared_task(bind=True)
def archive_old_workflow_sessions(self, days_to_keep=90):
    """
    Archive old workflow sessions to reduce database size
    
    Args:
        days_to_keep (int): Number of days of sessions to keep active
    
    Returns:
        dict: Archive results
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Find old sessions to archive
        old_sessions = WorkflowSession.objects.filter(
            created_at__lt=cutoff_date,
            archived=False
        )
        
        archived_count = 0
        for session in old_sessions:
            # Mark as archived instead of deleting
            session.archived = True
            session.archived_at = timezone.now()
            session.save()
            archived_count += 1
        
        logging.info(f"Archived {archived_count} old workflow sessions")
        
        return {
            'archived_sessions': archived_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error archiving workflow sessions: {e}")
        return {'error': str(e)}


@shared_task(bind=True)
def send_daily_monitoring_summary(self):
    """
    Send daily monitoring summary email to administrators
    
    Returns:
        dict: Email sending results
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Generate 24-hour performance report
        report = generate_performance_report.apply(args=[24]).get()
        
        if 'error' in report:
            raise Exception(f"Failed to generate report: {report['error']}")
        
        # Run health checks
        health_summary = health_check_all_services.apply().get()
        
        if 'error' in health_summary:
            raise Exception(f"Failed to get health summary: {health_summary['error']}")
        
        # Get active alerts
        from .production_monitoring import alerting_system
        active_alerts = alerting_system.get_active_alerts()
        
        # Compose email
        subject = f"Daily Monitoring Summary - {timezone.now().strftime('%Y-%m-%d')}"
        
        body = f"""
Daily Monitoring Summary
========================

System Health: {health_summary['overall_status'].upper()}
- Healthy Services: {health_summary['healthy_services']}/{health_summary['total_services']}
- Degraded Services: {health_summary['degraded_services']}
- Unhealthy Services: {health_summary['unhealthy_services']}

Performance Metrics (24 hours):
- Total Metrics Collected: {report['total_metrics_collected']}
- Total Errors: {report['total_errors']}
- Workflow Sessions: {report['workflow_summary']['total_sessions']}
- Completed Sessions: {report['workflow_summary']['completed_sessions']}
- Failed Sessions: {report['workflow_summary']['failed_sessions']}

Active Alerts: {len(active_alerts)}
"""
        
        if active_alerts:
            body += "\nActive Alerts:\n"
            for alert in active_alerts:
                body += f"- [{alert.severity.upper()}] {alert.title}\n"
        
        body += f"\nReport generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Send email
        recipients = getattr(settings, 'MONITORING_SUMMARY_RECIPIENTS', [])
        if recipients:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
            logging.info(f"Daily monitoring summary sent to {len(recipients)} recipients")
            return {'sent': True, 'recipients': len(recipients)}
        else:
            logging.warning("No recipients configured for monitoring summary")
            return {'sent': False, 'reason': 'no_recipients'}
        
    except Exception as e:
        logging.error(f"Error sending daily monitoring summary: {e}")
        return {'sent': False, 'error': str(e)}


# Task scheduling configuration for Celery Beat
CELERY_BEAT_SCHEDULE = {
    'cleanup-monitoring-data': {
        'task': 'apps.debugging.tasks.cleanup_monitoring_data',
        'schedule': timedelta(days=1),  # Run daily
        'kwargs': {'days_to_keep': 30},
        'options': {'expires': 3600}
    },
    'daily-monitoring-summary': {
        'task': 'apps.debugging.tasks.send_daily_monitoring_summary',
        'schedule': timedelta(days=1),  # Run daily
        'options': {'expires': 3600}
    },
    'health-check-services': {
        'task': 'apps.debugging.tasks.health_check_all_services',
        'schedule': timedelta(minutes=15),  # Run every 15 minutes
        'options': {'expires': 300}
    },
    'archive-old-sessions': {
        'task': 'apps.debugging.tasks.archive_old_workflow_sessions',
        'schedule': timedelta(days=7),  # Run weekly
        'kwargs': {'days_to_keep': 90},
        'options': {'expires': 3600}
    }
}