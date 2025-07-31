"""
Database Maintenance Celery Tasks

This module provides Celery tasks for automated database maintenance including:
- Scheduled index maintenance and optimization
- Automated data cleanup and archiving
- Database statistics collection and monitoring
- Maintenance reporting and alerting
"""

import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

from core.database_maintenance import (
    DatabaseMaintenanceScheduler,
    IndexMaintenanceManager,
    DataCleanupManager,
    DatabaseStatisticsCollector,
    run_database_maintenance,
    get_maintenance_recommendations
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def run_daily_maintenance_task(self, database_alias: str = 'default', dry_run: bool = False):
    """
    Run daily database maintenance routine
    """
    try:
        logger.info(f"Starting daily maintenance for database: {database_alias}")
        
        result = run_database_maintenance(database_alias, dry_run)
        
        if result['status'] == 'completed':
            logger.info(f"Daily maintenance completed successfully for {database_alias}")
            
            # Send maintenance report if configured
            if getattr(settings, 'SEND_MAINTENANCE_REPORTS', False):
                send_maintenance_report.delay(result)
            
            return {
                'status': 'success',
                'database_alias': database_alias,
                'duration_seconds': result['duration_seconds'],
                'improvements': result.get('improvements', {}),
                'tasks_completed': len(result.get('tasks', []))
            }
        else:
            logger.error(f"Daily maintenance failed for {database_alias}: {result.get('error', 'Unknown error')}")
            raise Exception(f"Maintenance failed: {result.get('error', 'Unknown error')}")
            
    except Exception as exc:
        logger.error(f"Daily maintenance task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_tables_task(self, database_alias: str = 'default', table_names: List[str] = None):
    """
    Analyze database tables and update statistics
    """
    try:
        logger.info(f"Starting table analysis for database: {database_alias}")
        
        index_manager = IndexMaintenanceManager(database_alias)
        
        if table_names:
            # Analyze specific tables (would need to implement this method)
            results = []
            for table_name in table_names:
                # This would require implementing analyze_specific_table method
                logger.info(f"Analyzing table: {table_name}")
        else:
            # Analyze all tables
            results = index_manager.analyze_all_tables()
        
        logger.info(f"Table analysis completed. Analyzed {len(results)} tables")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'tables_analyzed': len(results),
            'results': [r.to_dict() for r in results]
        }
        
    except Exception as exc:
        logger.error(f"Table analysis task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def optimize_fragmented_tables_task(self, database_alias: str = 'default'):
    """
    Optimize tables with high fragmentation
    """
    try:
        logger.info(f"Starting table optimization for database: {database_alias}")
        
        index_manager = IndexMaintenanceManager(database_alias)
        results = index_manager.optimize_fragmented_tables()
        
        total_size_reduction = sum(r.before_size_mb - r.after_size_mb for r in results)
        avg_fragmentation_improvement = sum(r.fragmentation_before - r.fragmentation_after for r in results) / len(results) if results else 0
        
        logger.info(f"Table optimization completed. Optimized {len(results)} tables, "
                   f"freed {total_size_reduction:.2f}MB, "
                   f"average fragmentation improvement: {avg_fragmentation_improvement:.2f}%")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'tables_optimized': len(results),
            'size_reduction_mb': total_size_reduction,
            'fragmentation_improvement': avg_fragmentation_improvement,
            'results': [r.to_dict() for r in results]
        }
        
    except Exception as exc:
        logger.error(f"Table optimization task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_data_task(self, database_alias: str = 'default', dry_run: bool = False):
    """
    Clean up old data according to configured rules
    """
    try:
        logger.info(f"Starting data cleanup for database: {database_alias} (dry_run: {dry_run})")
        
        cleanup_manager = DataCleanupManager(database_alias)
        results = cleanup_manager.cleanup_old_data(dry_run)
        
        total_rows_cleaned = sum(r.rows_affected for r in results)
        total_size_freed = sum(r.data_size_freed_mb for r in results)
        
        logger.info(f"Data cleanup completed. Cleaned {total_rows_cleaned} rows from {len(results)} tables, "
                   f"freed {total_size_freed:.2f}MB")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'dry_run': dry_run,
            'tables_cleaned': len(results),
            'rows_cleaned': total_rows_cleaned,
            'size_freed_mb': total_size_freed,
            'results': [r.to_dict() for r in results]
        }
        
    except Exception as exc:
        logger.error(f"Data cleanup task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def collect_database_statistics_task(self, database_alias: str = 'default'):
    """
    Collect comprehensive database statistics
    """
    try:
        logger.info(f"Collecting database statistics for: {database_alias}")
        
        stats_collector = DatabaseStatisticsCollector(database_alias)
        statistics = stats_collector.collect_database_statistics()
        
        # Cache statistics for trend analysis
        from django.core.cache import cache
        cache_key = f"db_stats_{database_alias}_{datetime.now().strftime('%Y%m%d')}"
        cache.set(cache_key, statistics.to_dict(), 86400 * 7)  # Keep for 7 days
        
        logger.info(f"Database statistics collected. Total size: {statistics.total_size_mb:.2f}MB, "
                   f"Tables: {statistics.total_tables}, Indexes: {statistics.total_indexes}")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'statistics': statistics.to_dict()
        }
        
    except Exception as exc:
        logger.error(f"Statistics collection task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def rebuild_indexes_task(self, database_alias: str = 'default', table_names: List[str] = None):
    """
    Rebuild indexes for specified tables or all tables
    """
    try:
        logger.info(f"Starting index rebuild for database: {database_alias}")
        
        index_manager = IndexMaintenanceManager(database_alias)
        results = index_manager.rebuild_indexes(table_names)
        
        total_size_change = sum(r.after_size_mb - r.before_size_mb for r in results)
        
        logger.info(f"Index rebuild completed. Rebuilt indexes for {len(results)} tables, "
                   f"size change: {total_size_change:+.2f}MB")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'tables_processed': len(results),
            'size_change_mb': total_size_change,
            'results': [r.to_dict() for r in results]
        }
        
    except Exception as exc:
        logger.error(f"Index rebuild task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def archive_old_orders_task(self, database_alias: str = 'default', days_old: int = 365, dry_run: bool = False):
    """
    Archive old completed orders
    """
    try:
        logger.info(f"Starting order archival for database: {database_alias} (days_old: {days_old}, dry_run: {dry_run})")
        
        cleanup_manager = DataCleanupManager(database_alias)
        result = cleanup_manager.archive_old_orders(days_old, dry_run)
        
        if result:
            logger.info(f"Order archival completed. Archived {result.rows_affected} orders")
            
            return {
                'status': 'success',
                'database_alias': database_alias,
                'dry_run': dry_run,
                'orders_archived': result.rows_affected,
                'result': result.to_dict()
            }
        else:
            logger.info("No old orders found to archive")
            return {
                'status': 'success',
                'database_alias': database_alias,
                'orders_archived': 0,
                'message': 'No old orders found to archive'
            }
        
    except Exception as exc:
        logger.error(f"Order archival task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_maintenance_recommendations_task(self, database_alias: str = 'default'):
    """
    Generate maintenance recommendations based on current database state
    """
    try:
        logger.info(f"Generating maintenance recommendations for database: {database_alias}")
        
        recommendations = get_maintenance_recommendations(database_alias)
        
        if 'error' in recommendations:
            raise Exception(recommendations['error'])
        
        # Send high priority recommendations via email if configured
        high_priority_recommendations = [
            rec for rec in recommendations.get('recommendations', [])
            if rec.get('priority') == 'high'
        ]
        
        if high_priority_recommendations and getattr(settings, 'SEND_MAINTENANCE_ALERTS', False):
            send_maintenance_alert.delay(database_alias, high_priority_recommendations)
        
        logger.info(f"Generated {len(recommendations.get('recommendations', []))} maintenance recommendations")
        
        return {
            'status': 'success',
            'database_alias': database_alias,
            'recommendations_count': len(recommendations.get('recommendations', [])),
            'high_priority_count': len(high_priority_recommendations),
            'recommendations': recommendations
        }
        
    except Exception as exc:
        logger.error(f"Maintenance recommendations task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_maintenance_report(self, maintenance_result: Dict[str, Any]):
    """
    Send maintenance report via email
    """
    try:
        if not getattr(settings, 'SEND_MAINTENANCE_REPORTS', False):
            return {'status': 'skipped', 'reason': 'Maintenance reports disabled'}
        
        database_alias = maintenance_result.get('database_alias', 'default')
        status = maintenance_result.get('status', 'unknown')
        duration = maintenance_result.get('duration_seconds', 0)
        improvements = maintenance_result.get('improvements', {})
        
        subject = f"Database Maintenance Report - {database_alias} ({status})"
        
        # Build email content
        message_lines = [
            f"Database Maintenance Report for {database_alias}",
            f"Status: {status}",
            f"Duration: {duration:.2f} seconds",
            "",
            "Improvements:",
            f"  - Size reduction: {improvements.get('size_reduction_mb', 0):.2f} MB",
            f"  - Fragmentation improvement: {improvements.get('fragmentation_improvement_percent', 0):.2f}%",
            f"  - Rows cleaned: {improvements.get('total_rows_cleaned', 0):,}",
            "",
            "Tasks completed:"
        ]
        
        for task in maintenance_result.get('tasks', []):
            message_lines.append(f"  - {task['task_type']}: {task['summary']}")
        
        if status == 'failed':
            message_lines.extend([
                "",
                f"Error: {maintenance_result.get('error', 'Unknown error')}"
            ])
        
        message = "\n".join(message_lines)
        
        # Send email to administrators
        admin_emails = getattr(settings, 'MAINTENANCE_REPORT_RECIPIENTS', [])
        if not admin_emails:
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
        
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            logger.info(f"Maintenance report sent to {len(admin_emails)} recipients")
            
            return {
                'status': 'success',
                'recipients': len(admin_emails),
                'database_alias': database_alias
            }
        else:
            logger.warning("No admin email addresses configured for maintenance reports")
            return {'status': 'skipped', 'reason': 'No admin emails configured'}
        
    except Exception as exc:
        logger.error(f"Failed to send maintenance report: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_maintenance_alert(self, database_alias: str, recommendations: List[Dict[str, Any]]):
    """
    Send maintenance alert for high priority recommendations
    """
    try:
        if not getattr(settings, 'SEND_MAINTENANCE_ALERTS', False):
            return {'status': 'skipped', 'reason': 'Maintenance alerts disabled'}
        
        subject = f"Database Maintenance Alert - {database_alias}"
        
        message_lines = [
            f"High priority maintenance recommendations for database: {database_alias}",
            "",
            "Recommendations:"
        ]
        
        for rec in recommendations:
            message_lines.extend([
                f"  Priority: {rec.get('priority', 'unknown').upper()}",
                f"  Type: {rec.get('type', 'unknown')}",
                f"  Message: {rec.get('message', 'No message')}",
                f"  Recommended Action: {rec.get('action', 'No action specified')}",
                ""
            ])
        
        message_lines.append("Please review and take appropriate action.")
        message = "\n".join(message_lines)
        
        # Send email to administrators
        admin_emails = getattr(settings, 'MAINTENANCE_ALERT_RECIPIENTS', [])
        if not admin_emails:
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
        
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            logger.info(f"Maintenance alert sent to {len(admin_emails)} recipients")
            
            return {
                'status': 'success',
                'recipients': len(admin_emails),
                'database_alias': database_alias,
                'recommendations_count': len(recommendations)
            }
        else:
            logger.warning("No admin email addresses configured for maintenance alerts")
            return {'status': 'skipped', 'reason': 'No admin emails configured'}
        
    except Exception as exc:
        logger.error(f"Failed to send maintenance alert: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def weekly_maintenance_task(self, database_alias: str = 'default'):
    """
    Run weekly comprehensive maintenance routine
    """
    try:
        logger.info(f"Starting weekly maintenance for database: {database_alias}")
        
        results = {
            'started_at': datetime.now().isoformat(),
            'database_alias': database_alias,
            'tasks': []
        }
        
        # 1. Collect statistics
        stats_result = collect_database_statistics_task.apply(args=[database_alias])
        results['tasks'].append({
            'task': 'collect_statistics',
            'result': stats_result.result
        })
        
        # 2. Generate recommendations
        recommendations_result = generate_maintenance_recommendations_task.apply(args=[database_alias])
        results['tasks'].append({
            'task': 'generate_recommendations',
            'result': recommendations_result.result
        })
        
        # 3. Rebuild indexes for large tables (weekly task)
        rebuild_result = rebuild_indexes_task.apply(args=[database_alias, None])
        results['tasks'].append({
            'task': 'rebuild_indexes',
            'result': rebuild_result.result
        })
        
        # 4. Archive old orders
        archive_result = archive_old_orders_task.apply(args=[database_alias, 365, False])
        results['tasks'].append({
            'task': 'archive_orders',
            'result': archive_result.result
        })
        
        results['completed_at'] = datetime.now().isoformat()
        results['status'] = 'completed'
        
        logger.info(f"Weekly maintenance completed for database: {database_alias}")
        
        # Send weekly report
        if getattr(settings, 'SEND_WEEKLY_MAINTENANCE_REPORTS', False):
            send_weekly_maintenance_report.delay(results)
        
        return results
        
    except Exception as exc:
        logger.error(f"Weekly maintenance task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_weekly_maintenance_report(self, weekly_results: Dict[str, Any]):
    """
    Send weekly maintenance report
    """
    try:
        if not getattr(settings, 'SEND_WEEKLY_MAINTENANCE_REPORTS', False):
            return {'status': 'skipped', 'reason': 'Weekly maintenance reports disabled'}
        
        database_alias = weekly_results.get('database_alias', 'default')
        
        subject = f"Weekly Database Maintenance Report - {database_alias}"
        
        message_lines = [
            f"Weekly Database Maintenance Report for {database_alias}",
            f"Period: {weekly_results.get('started_at', 'Unknown')} - {weekly_results.get('completed_at', 'Unknown')}",
            "",
            "Tasks completed:"
        ]
        
        for task_info in weekly_results.get('tasks', []):
            task_name = task_info['task']
            task_result = task_info['result']
            
            if task_result.get('status') == 'success':
                message_lines.append(f"  ✓ {task_name}: Success")
                
                # Add specific details based on task type
                if task_name == 'collect_statistics':
                    stats = task_result.get('statistics', {})
                    message_lines.append(f"    - Total size: {stats.get('total_size_mb', 0):.2f} MB")
                    message_lines.append(f"    - Tables: {stats.get('total_tables', 0)}")
                    message_lines.append(f"    - Fragmentation: {stats.get('fragmentation_percent', 0):.2f}%")
                
                elif task_name == 'generate_recommendations':
                    rec_count = task_result.get('recommendations_count', 0)
                    high_priority = task_result.get('high_priority_count', 0)
                    message_lines.append(f"    - Recommendations: {rec_count} ({high_priority} high priority)")
                
                elif task_name == 'rebuild_indexes':
                    tables_processed = task_result.get('tables_processed', 0)
                    size_change = task_result.get('size_change_mb', 0)
                    message_lines.append(f"    - Tables processed: {tables_processed}")
                    message_lines.append(f"    - Size change: {size_change:+.2f} MB")
                
                elif task_name == 'archive_orders':
                    orders_archived = task_result.get('orders_archived', 0)
                    message_lines.append(f"    - Orders archived: {orders_archived:,}")
            else:
                message_lines.append(f"  ✗ {task_name}: Failed")
        
        message = "\n".join(message_lines)
        
        # Send email to administrators
        admin_emails = getattr(settings, 'WEEKLY_MAINTENANCE_REPORT_RECIPIENTS', [])
        if not admin_emails:
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
        
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            logger.info(f"Weekly maintenance report sent to {len(admin_emails)} recipients")
            
            return {
                'status': 'success',
                'recipients': len(admin_emails),
                'database_alias': database_alias
            }
        else:
            logger.warning("No admin email addresses configured for weekly maintenance reports")
            return {'status': 'skipped', 'reason': 'No admin emails configured'}
        
    except Exception as exc:
        logger.error(f"Failed to send weekly maintenance report: {str(exc)}")
        raise self.retry(exc=exc)