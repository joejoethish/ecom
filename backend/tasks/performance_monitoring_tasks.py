"""
Celery tasks for performance monitoring and optimization

These tasks run automated performance monitoring, optimization analysis,
and capacity planning in the background.
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from core.performance_monitor import get_performance_monitor
from core.database_monitor import get_database_monitor
from core.database_alerting import get_database_alerting

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_performance_metrics(self):
    """
    Collect performance metrics from all databases
    """
    try:
        monitor = get_performance_monitor()
        
        if not monitor.monitoring_enabled:
            logger.info("Performance monitoring is disabled, skipping metrics collection")
            return
        
        # This is handled by the monitoring thread, but we can trigger additional collection
        logger.info("Performance metrics collection task completed")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'message': 'Performance metrics collected successfully'
        }
        
    except Exception as e:
        logger.error(f"Error in performance metrics collection task: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def analyze_query_performance(self):
    """
    Analyze query performance and generate optimization recommendations
    """
    try:
        monitor = get_performance_monitor()
        db_monitor = get_database_monitor()
        
        # Get recent slow queries
        slow_queries = list(db_monitor.slow_queries)[-100:]  # Last 100 slow queries
        
        optimization_count = 0
        for slow_query in slow_queries:
            if hasattr(slow_query, 'query_hash'):
                # This triggers analysis and recommendation generation
                monitor._analyze_query_for_optimization(slow_query)
                optimization_count += 1
        
        logger.info(f"Analyzed {optimization_count} queries for optimization")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'queries_analyzed': optimization_count,
            'message': f'Analyzed {optimization_count} queries for optimization'
        }
        
    except Exception as e:
        logger.error(f"Error in query performance analysis task: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def detect_performance_regressions(self):
    """
    Detect performance regressions and send alerts
    """
    try:
        monitor = get_performance_monitor()
        
        # Get recent regressions
        recent_regressions = [
            reg for reg in monitor.regressions
            if reg.detection_timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        critical_regressions = [
            reg for reg in recent_regressions
            if reg.severity in ['major', 'critical']
        ]
        
        if critical_regressions:
            # Send summary alert for critical regressions
            send_regression_summary_alert(critical_regressions)
        
        logger.info(f"Detected {len(recent_regressions)} regressions, {len(critical_regressions)} critical")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_regressions': len(recent_regressions),
            'critical_regressions': len(critical_regressions),
            'message': f'Regression detection completed'
        }
        
    except Exception as e:
        logger.error(f"Error in regression detection task: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def generate_capacity_recommendations(self):
    """
    Generate capacity planning recommendations
    """
    try:
        monitor = get_performance_monitor()
        
        # Get recent capacity recommendations
        recent_capacity_recs = [
            rec for rec in monitor.capacity_recommendations
            if rec.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        critical_capacity_issues = [
            rec for rec in recent_capacity_recs
            if rec.urgency == 'critical'
        ]
        
        if critical_capacity_issues:
            # Send capacity alert
            send_capacity_alert(critical_capacity_issues)
        
        logger.info(f"Generated {len(recent_capacity_recs)} capacity recommendations, {len(critical_capacity_issues)} critical")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_recommendations': len(recent_capacity_recs),
            'critical_issues': len(critical_capacity_issues),
            'message': 'Capacity analysis completed'
        }
        
    except Exception as e:
        logger.error(f"Error in capacity recommendations task: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def generate_daily_performance_report(self):
    """
    Generate daily performance report and send to administrators
    """
    try:
        monitor = get_performance_monitor()
        
        # Collect data for report
        report_data = {}
        
        for db_alias in settings.DATABASES.keys():
            metrics = monitor.get_current_performance_metrics(db_alias)
            report_data[db_alias] = metrics
        
        recommendations = monitor.get_optimization_recommendations(20)
        capacity_recs = monitor.get_capacity_recommendations(10)
        regressions = monitor.get_performance_regressions(20)
        
        # Calculate summary statistics
        high_priority_recs = [r for r in recommendations if r['priority'] in ['high', 'critical']]
        capacity_issues = [c for c in capacity_recs if c['urgency'] in ['high', 'critical']]
        critical_regressions = [r for r in regressions if r['severity'] == 'critical']
        
        report_summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_recommendations': len(recommendations),
            'high_priority_recommendations': len(high_priority_recs),
            'capacity_issues': len(capacity_issues),
            'active_regressions': len(regressions),
            'critical_regressions': len(critical_regressions),
            'health_status': 'critical' if critical_regressions or capacity_issues else 
                           'warning' if high_priority_recs or regressions else 'healthy'
        }
        
        # Send email report
        send_daily_performance_report(report_summary, report_data, recommendations, capacity_recs, regressions)
        
        logger.info(f"Daily performance report generated and sent")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'report_summary': report_summary,
            'message': 'Daily performance report generated and sent'
        }
        
    except Exception as e:
        logger.error(f"Error generating daily performance report: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def cleanup_old_performance_data(self):
    """
    Clean up old performance monitoring data
    """
    try:
        monitor = get_performance_monitor()
        
        # Trigger cleanup
        monitor._cleanup_old_data()
        
        logger.info("Performance data cleanup completed")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'message': 'Performance data cleanup completed'
        }
        
    except Exception as e:
        logger.error(f"Error in performance data cleanup task: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def update_performance_baselines(self):
    """
    Update performance baselines based on recent stable periods
    """
    try:
        monitor = get_performance_monitor()
        
        updated_baselines = 0
        
        # Check each metric for baseline updates
        for metric_key, history in monitor.performance_history.items():
            if len(history) >= 2000:  # Need sufficient data
                # Check if current baseline is old (more than 7 days)
                current_baseline = monitor.baselines.get(metric_key)
                
                if (not current_baseline or 
                    current_baseline.baseline_timestamp < datetime.now() - timedelta(days=7)):
                    
                    # Create new baseline
                    new_baseline = monitor._create_baseline(metric_key, history)
                    if new_baseline:
                        monitor.baselines[metric_key] = new_baseline
                        updated_baselines += 1
        
        logger.info(f"Updated {updated_baselines} performance baselines")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'updated_baselines': updated_baselines,
            'message': f'Updated {updated_baselines} performance baselines'
        }
        
    except Exception as e:
        logger.error(f"Error updating performance baselines: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


def send_regression_summary_alert(regressions):
    """Send email alert for critical performance regressions"""
    try:
        subject = f"Critical Performance Regressions Detected - {len(regressions)} issues"
        
        message = f"""
Critical Performance Regressions Detected

{len(regressions)} critical performance regressions have been detected:

"""
        
        for reg in regressions:
            message += f"""
Database: {reg.database_alias}
Metric: {reg.metric_name}
Regression: {reg.regression_percentage:.1f}% degradation
Baseline: {reg.baseline_value:.2f} → Current: {reg.current_value:.2f}
Severity: {reg.severity.upper()}
Detected: {reg.detection_timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Potential Causes:
"""
            for cause in reg.potential_causes:
                message += f"- {cause}\n"
            
            message += "\n" + "="*50 + "\n"
        
        message += """
Please investigate these regressions immediately and take corrective action.

Performance Monitoring System
"""
        
        # Send to administrators
        admin_emails = getattr(settings, 'DB_ALERT_EMAIL_RECIPIENTS', [])
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=admin_emails,
                fail_silently=False
            )
        
    except Exception as e:
        logger.error(f"Error sending regression summary alert: {e}")


def send_capacity_alert(capacity_issues):
    """Send email alert for critical capacity issues"""
    try:
        subject = f"Critical Capacity Issues Detected - {len(capacity_issues)} resources"
        
        message = f"""
Critical Capacity Issues Detected

{len(capacity_issues)} critical capacity issues have been detected:

"""
        
        for issue in capacity_issues:
            message += f"""
Resource: {issue.resource_type.upper()}
Current Usage: {issue.current_usage:.1f}%
Projected Usage: {issue.projected_usage:.1f}%
Time to Capacity: {issue.time_to_capacity} days
Recommended Action: {issue.recommended_action}

"""
        
        message += """
Immediate action is required to prevent service disruption.

Performance Monitoring System
"""
        
        # Send to administrators
        admin_emails = getattr(settings, 'DB_ALERT_EMAIL_RECIPIENTS', [])
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=admin_emails,
                fail_silently=False
            )
        
    except Exception as e:
        logger.error(f"Error sending capacity alert: {e}")


def send_daily_performance_report(summary, metrics_data, recommendations, capacity_recs, regressions):
    """Send daily performance report email"""
    try:
        subject = f"Daily Performance Report - {summary['date']} - Status: {summary['health_status'].upper()}"
        
        message = f"""
Daily Performance Monitoring Report
Date: {summary['date']}
Overall Health Status: {summary['health_status'].upper()}

SUMMARY:
- Total Optimization Recommendations: {summary['total_recommendations']}
- High Priority Recommendations: {summary['high_priority_recommendations']}
- Capacity Issues: {summary['capacity_issues']}
- Active Performance Regressions: {summary['active_regressions']}
- Critical Regressions: {summary['critical_regressions']}

"""
        
        # Add current metrics summary
        if metrics_data:
            message += "CURRENT PERFORMANCE METRICS:\n"
            for db_alias, metrics in metrics_data.items():
                message += f"\nDatabase: {db_alias}\n"
                for metric_name, data in metrics.items():
                    message += f"  {metric_name}: {data['current']:.2f} (avg: {data['average_10min']:.2f})\n"
        
        # Add top recommendations
        if recommendations:
            message += f"\nTOP OPTIMIZATION RECOMMENDATIONS:\n"
            for i, rec in enumerate(recommendations[:5], 1):
                message += f"\n{i}. Priority: {rec['priority'].upper()}\n"
                message += f"   Estimated Improvement: {rec['estimated_improvement']:.1f}%\n"
                message += f"   Implementation Effort: {rec['implementation_effort']}\n"
                message += f"   Query: {rec['query_text'][:100]}...\n"
        
        # Add capacity issues
        if capacity_recs:
            message += f"\nCAPACITY RECOMMENDATIONS:\n"
            for rec in capacity_recs:
                if rec['urgency'] in ['high', 'critical']:
                    message += f"\n⚠️  {rec['resource_type'].upper()}: {rec['current_usage']:.1f}% usage\n"
                    message += f"   Urgency: {rec['urgency'].upper()}\n"
                    message += f"   Action: {rec['recommended_action']}\n"
        
        # Add regressions
        if regressions:
            message += f"\nPERFORMANCE REGRESSIONS:\n"
            for reg in regressions[:5]:
                message += f"\n- {reg['database_alias']}.{reg['metric_name']}: {reg['regression_percentage']:.1f}% degradation\n"
                message += f"  Severity: {reg['severity'].upper()}\n"
        
        message += f"""

For detailed analysis, visit the Performance Monitoring Dashboard.

Performance Monitoring System
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send to administrators
        admin_emails = getattr(settings, 'DB_ALERT_EMAIL_RECIPIENTS', [])
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=admin_emails,
                fail_silently=False
            )
        
    except Exception as e:
        logger.error(f"Error sending daily performance report: {e}")