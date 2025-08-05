"""
Database Administration Tools for MySQL Integration

This module provides comprehensive database administration interfaces including:
- Database monitoring and management interface
- Backup management and restoration tools
- User and permission management interface
- Database health dashboard and reporting

Requirements: 4.1, 6.1, 6.6
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import connection, connections
from django.core.paginator import Paginator
from django.urls import path, reverse
from django.conf import settings
import csv
from io import StringIO

from core.database_monitor import DatabaseMonitor
from core.backup_manager import MySQLBackupManager, BackupConfig
from core.database_security import DatabaseSecurityManager

logger = logging.getLogger(__name__)


class DatabaseMetricsProxy:
    """Proxy model for database metrics to work with Django admin."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    class Meta:
        managed = False
        verbose_name = "Database Metric"
        verbose_name_plural = "Database Metrics"


class BackupProxy:
    """Proxy model for backup entries to work with Django admin."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    class Meta:
        managed = False
        verbose_name = "Database Backup"
        verbose_name_plural = "Database Backups"


class DatabaseMetricsAdmin(admin.ModelAdmin):
    """Admin interface for database monitoring and metrics."""
    
    list_display = [
        'database_alias', 'timestamp', 'status_badge', 'health_score',
        'connection_usage_percent', 'queries_per_second', 'replication_lag',
        'cpu_usage', 'memory_usage', 'disk_usage', 'actions'
    ]
    list_filter = ['database_alias', 'status']
    readonly_fields = [
        'database_alias', 'timestamp', 'status', 'health_score',
        'active_connections', 'total_connections', 'connection_usage_percent',
        'queries_per_second', 'average_query_time', 'slow_queries',
        'replication_lag', 'replication_status', 'cpu_usage', 'memory_usage',
        'disk_usage', 'innodb_buffer_pool_hit_rate'
    ]
    ordering = ['-timestamp']
    list_per_page = 25
    
    def has_add_permission(self, request):
        """Metrics cannot be added manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Metrics cannot be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Metrics cannot be deleted."""
        return False
    
    def get_queryset(self, request):
        """Get database metrics from monitoring system."""
        try:
            # Initialize database monitor if not already done
            if not hasattr(self, '_db_monitor'):
                self._db_monitor = DatabaseMonitor()
            
            metrics_list = []
            
            # Get latest metrics for each database
            for db_alias in settings.DATABASES.keys():
                try:
                    # Get cached metrics
                    from django.core.cache import cache
                    cached_metrics = cache.get(f"db_metrics_{db_alias}")
                    
                    if cached_metrics:
                        metrics_list.append(DatabaseMetricsProxy(**cached_metrics))
                    else:
                        # Create placeholder metrics if none available
                        placeholder_metrics = {
                            'database_alias': db_alias,
                            'timestamp': datetime.now().isoformat(),
                            'status': 'unknown',
                            'health_score': 0.0,
                            'connection_usage_percent': 0.0,
                            'queries_per_second': 0.0,
                            'replication_lag': 0.0,
                            'cpu_usage': 0.0,
                            'memory_usage': 0.0,
                            'disk_usage': 0.0,
                            'active_connections': 0,
                            'total_connections': 0,
                            'average_query_time': 0.0,
                            'slow_queries': 0,
                            'replication_status': 'Unknown',
                            'innodb_buffer_pool_hit_rate': 0.0
                        }
                        metrics_list.append(DatabaseMetricsProxy(**placeholder_metrics))
                        
                except Exception as e:
                    logger.error(f"Error getting metrics for {db_alias}: {e}")
            
            return metrics_list
            
        except Exception as e:
            messages.error(request, f"Error loading database metrics: {e}")
            return []
    
    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'healthy': '#28a745',
            'warning': '#ffc107',
            'critical': '#dc3545',
            'unknown': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def actions(self, obj):
        """Action buttons for database management."""
        return format_html(
            '<a href="javascript:void(0)" onclick="refreshMetrics(\'{}\')" '
            'class="button" style="font-size: 11px; margin-right: 5px;">Refresh</a>'
            '<a href="javascript:void(0)" onclick="viewDetails(\'{}\')" '
            'class="button" style="font-size: 11px;">Details</a>',
            obj.database_alias, obj.database_alias
        )
    actions.short_description = 'Actions'


# BackupProxy is not a Django model, so we can't register it with admin
# @admin.register(BackupProxy)
class BackupAdmin(admin.ModelAdmin):
    """Admin interface for backup management."""
    
    list_display = [
        'backup_id', 'backup_type', 'timestamp', 'database_name',
        'file_size_mb', 'status_badge', 'actions'
    ]
    list_filter = ['backup_type', 'database_name']
    search_fields = ['backup_id', 'database_name']
    readonly_fields = [
        'backup_id', 'backup_type', 'timestamp', 'file_path',
        'file_size', 'checksum', 'encrypted', 'compression',
        'database_name', 'mysql_version', 'binlog_position'
    ]
    ordering = ['-timestamp']
    list_per_page = 20
    
    def has_add_permission(self, request):
        """Backups are created through management interface."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Backups cannot be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of old backups."""
        return request.user.has_perm('auth.delete_user')
    
    def get_queryset(self, request):
        """Get backup list from backup manager."""
        try:
            # Initialize backup manager
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key'),
                retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
            )
            backup_manager = MySQLBackupManager(backup_config)
            
            # Get all backups
            backups = backup_manager.storage.list_backups()
            
            # Convert to proxy objects
            backup_proxies = []
            for backup in backups:
                backup_data = {
                    'backup_id': backup.backup_id,
                    'backup_type': backup.backup_type,
                    'timestamp': backup.timestamp,
                    'file_path': backup.file_path,
                    'file_size': backup.file_size,
                    'checksum': backup.checksum,
                    'encrypted': backup.encrypted,
                    'compression': backup.compression,
                    'database_name': backup.database_name,
                    'mysql_version': backup.mysql_version,
                    'binlog_position': backup.binlog_position,
                }
                backup_proxies.append(BackupProxy(**backup_data))
            
            return backup_proxies
            
        except Exception as e:
            messages.error(request, f"Error loading backups: {e}")
            return []
    
    def file_size_mb(self, obj):
        """Display file size in MB."""
        size_mb = obj.file_size / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    file_size_mb.short_description = 'Size'
    
    def status_badge(self, obj):
        """Display backup status."""
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">COMPLETE</span>'
        )
    status_badge.short_description = 'Status'
    
    def actions(self, obj):
        """Action buttons for backup management."""
        return format_html(
            '<a href="javascript:void(0)" onclick="verifyBackup(\'{}\')" '
            'class="button" style="font-size: 11px; margin-right: 5px;">Verify</a>'
            '<a href="javascript:void(0)" onclick="restoreBackup(\'{}\')" '
            'class="button" style="font-size: 11px; margin-right: 5px;">Restore</a>'
            '<a href="javascript:void(0)" onclick="downloadBackup(\'{}\')" '
            'class="button" style="font-size: 11px;">Download</a>',
            obj.backup_id, obj.backup_id, obj.backup_id
        )
    actions.short_description = 'Actions'


class DatabaseAdministrationSite(admin.AdminSite):
    """Custom admin site for database administration."""
    
    site_header = "Database Administration"
    site_title = "DB Admin"
    index_title = "Database Management Dashboard"
    
    def get_urls(self):
        """Add custom URLs for database administration."""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='db_dashboard'),
            path('health-check/', self.admin_view(self.health_check_view), name='health_check'),
            path('backup-management/', self.admin_view(self.backup_management_view), name='backup_management'),
            path('user-management/', self.admin_view(self.user_management_view), name='user_management'),
            path('performance-report/', self.admin_view(self.performance_report_view), name='performance_report'),
            
            # API endpoints
            path('api/create-backup/', self.admin_view(self.create_backup_api), name='create_backup_api'),
            path('api/verify-backup/', self.admin_view(self.verify_backup_api), name='verify_backup_api'),
            path('api/restore-backup/', self.admin_view(self.restore_backup_api), name='restore_backup_api'),
            path('api/refresh-metrics/', self.admin_view(self.refresh_metrics_api), name='refresh_metrics_api'),
            path('api/create-user/', self.admin_view(self.create_user_api), name='create_user_api'),
            path('api/test-connection/', self.admin_view(self.test_connection_api), name='test_connection_api'),
            path('api/export-report/', self.admin_view(self.export_report_api), name='export_report_api'),
        ]
        return custom_urls + urls
    
    @method_decorator(staff_member_required)
    def dashboard_view(self, request):
        """Main database administration dashboard."""
        context = self._get_dashboard_context()
        return render(request, 'admin/database_dashboard.html', context)
    
    @method_decorator(staff_member_required)
    def health_check_view(self, request):
        """Database health check interface."""
        context = self._get_health_check_context()
        return render(request, 'admin/database_health_check.html', context)
    
    @method_decorator(staff_member_required)
    def backup_management_view(self, request):
        """Backup management interface."""
        context = self._get_backup_management_context()
        return render(request, 'admin/backup_management.html', context)
    
    @method_decorator(staff_member_required)
    def user_management_view(self, request):
        """Database user management interface."""
        context = self._get_user_management_context()
        return render(request, 'admin/user_management.html', context)
    
    @method_decorator(staff_member_required)
    def performance_report_view(self, request):
        """Performance reporting interface."""
        context = self._get_performance_report_context()
        return render(request, 'admin/performance_report.html', context)
    
    def _get_dashboard_context(self) -> Dict[str, Any]:
        """Get context data for main dashboard."""
        context = {}
        
        try:
            # Database status summary
            db_status = {}
            for db_alias in settings.DATABASES.keys():
                try:
                    conn = connections[db_alias]
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        db_status[db_alias] = 'healthy'
                except Exception:
                    db_status[db_alias] = 'error'
            
            # Backup status
            try:
                backup_config = BackupConfig(
                    backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                    encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key')
                )
                backup_manager = MySQLBackupManager(backup_config)
                backup_status = backup_manager.get_backup_status()
            except Exception as e:
                backup_status = {'error': str(e)}
            
            # Recent alerts (from cache or database)
            recent_alerts = self._get_recent_alerts()
            
            # System metrics
            system_metrics = self._get_system_metrics()
            
            context.update({
                'db_status': db_status,
                'backup_status': backup_status,
                'recent_alerts': recent_alerts,
                'system_metrics': system_metrics,
                'total_databases': len(settings.DATABASES),
                'healthy_databases': sum(1 for status in db_status.values() if status == 'healthy'),
            })
            
        except Exception as e:
            context['error'] = f"Error loading dashboard data: {e}"
        
        return context
    
    def _get_health_check_context(self) -> Dict[str, Any]:
        """Get context data for health check."""
        context = {}
        
        try:
            health_results = {}
            
            for db_alias in settings.DATABASES.keys():
                health_results[db_alias] = self._perform_health_check(db_alias)
            
            context.update({
                'health_results': health_results,
                'overall_health': all(
                    result.get('status') == 'healthy' 
                    for result in health_results.values()
                )
            })
            
        except Exception as e:
            context['error'] = f"Error performing health check: {e}"
        
        return context
    
    def _get_backup_management_context(self) -> Dict[str, Any]:
        """Get context data for backup management."""
        context = {}
        
        try:
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key')
            )
            backup_manager = MySQLBackupManager(backup_config)
            
            # Get backup statistics
            backups = backup_manager.storage.list_backups()
            full_backups = [b for b in backups if b.backup_type == 'full']
            incremental_backups = [b for b in backups if b.backup_type == 'incremental']
            
            # Calculate storage usage
            total_size = sum(b.file_size for b in backups)
            
            context.update({
                'total_backups': len(backups),
                'full_backups': len(full_backups),
                'incremental_backups': len(incremental_backups),
                'total_size_gb': round(total_size / (1024**3), 2),
                'latest_backup': backups[0] if backups else None,
                'backup_config': {
                    'retention_days': backup_config.retention_days,
                    'backup_dir': backup_config.backup_dir,
                    'compression_enabled': backup_config.compression_enabled,
                }
            })
            
        except Exception as e:
            context['error'] = f"Error loading backup data: {e}"
        
        return context
    
    def _get_user_management_context(self) -> Dict[str, Any]:
        """Get context data for user management."""
        context = {}
        
        try:
            # Get database users
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT User, Host, Select_priv, Insert_priv, Update_priv, 
                           Delete_priv, Create_priv, Drop_priv, Super_priv,
                           ssl_type, max_connections, password_expired
                    FROM mysql.user 
                    WHERE User != ''
                    ORDER BY User
                """)
                
                columns = [col[0] for col in cursor.description]
                users = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Get user privileges summary
            privilege_summary = {}
            for user in users:
                username = f"{user['User']}@{user['Host']}"
                privilege_summary[username] = {
                    'read': user['Select_priv'] == 'Y',
                    'write': any([
                        user['Insert_priv'] == 'Y',
                        user['Update_priv'] == 'Y',
                        user['Delete_priv'] == 'Y'
                    ]),
                    'admin': user['Super_priv'] == 'Y',
                    'ssl_required': user['ssl_type'] != '',
                    'max_connections': user['max_connections'],
                    'password_expired': user['password_expired'] == 'Y'
                }
            
            context.update({
                'database_users': users,
                'privilege_summary': privilege_summary,
                'total_users': len(users),
                'admin_users': sum(1 for u in users if u['Super_priv'] == 'Y'),
                'ssl_users': sum(1 for u in users if u['ssl_type'] != ''),
            })
            
        except Exception as e:
            context['error'] = f"Error loading user data: {e}"
        
        return context
    
    def _get_performance_report_context(self) -> Dict[str, Any]:
        """Get context data for performance report."""
        context = {}
        
        try:
            with connection.cursor() as cursor:
                # Query performance metrics
                cursor.execute("SHOW STATUS LIKE 'Queries'")
                total_queries = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW STATUS LIKE 'Uptime'")
                uptime = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
                slow_queries = int(cursor.fetchone()[1])
                
                # Connection metrics
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                active_connections = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_connections = int(cursor.fetchone()[1])
                
                # InnoDB metrics
                cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'")
                buffer_reads = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_reads'")
                disk_reads = int(cursor.fetchone()[1])
                
                buffer_hit_rate = ((buffer_reads - disk_reads) / buffer_reads * 100) if buffer_reads > 0 else 0
                
                context.update({
                    'total_queries': total_queries,
                    'queries_per_second': round(total_queries / uptime, 2) if uptime > 0 else 0,
                    'slow_queries': slow_queries,
                    'slow_query_rate': round(slow_queries / total_queries * 100, 2) if total_queries > 0 else 0,
                    'active_connections': active_connections,
                    'max_connections': max_connections,
                    'connection_usage': round(active_connections / max_connections * 100, 2),
                    'buffer_hit_rate': round(buffer_hit_rate, 2),
                    'uptime_hours': round(uptime / 3600, 2),
                })
                
        except Exception as e:
            context['error'] = f"Error loading performance data: {e}"
        
        return context
    
    def _perform_health_check(self, db_alias: str) -> Dict[str, Any]:
        """Perform comprehensive health check for a database."""
        health_result = {
            'status': 'unknown',
            'checks': {},
            'recommendations': []
        }
        
        try:
            conn = connections[db_alias]
            with conn.cursor() as cursor:
                # Connection test
                cursor.execute("SELECT 1")
                health_result['checks']['connection'] = 'PASS'
                
                # Version check
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                health_result['checks']['version'] = f"MySQL {version}"
                
                # Storage engine check
                cursor.execute("SHOW ENGINES")
                engines = cursor.fetchall()
                innodb_available = any(engine[0] == 'InnoDB' and engine[1] in ['YES', 'DEFAULT'] for engine in engines)
                health_result['checks']['innodb'] = 'PASS' if innodb_available else 'FAIL'
                
                # Configuration checks
                cursor.execute("SHOW VARIABLES LIKE 'innodb_buffer_pool_size'")
                buffer_pool_size = int(cursor.fetchone()[1])
                if buffer_pool_size < 128 * 1024 * 1024:  # Less than 128MB
                    health_result['recommendations'].append("Consider increasing innodb_buffer_pool_size")
                
                cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_conn = int(cursor.fetchone()[1])
                if max_conn < 100:
                    health_result['recommendations'].append("Consider increasing max_connections")
                
                # Determine overall status
                failed_checks = sum(1 for check in health_result['checks'].values() if check == 'FAIL')
                if failed_checks == 0:
                    health_result['status'] = 'healthy'
                elif failed_checks <= 2:
                    health_result['status'] = 'warning'
                else:
                    health_result['status'] = 'critical'
                    
        except Exception as e:
            health_result['status'] = 'error'
            health_result['error'] = str(e)
        
        return health_result
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent database alerts."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT timestamp, event_type, severity, description
                    FROM db_security_events 
                    WHERE timestamp >= %s AND resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, [datetime.now() - timedelta(hours=24)])
                
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics."""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    # API Endpoints
    
    @method_decorator(staff_member_required)
    def create_backup_api(self, request):
        """API endpoint to create a new backup."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            backup_type = data.get('backup_type', 'full')
            database_alias = data.get('database_alias', 'default')
            
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key')
            )
            backup_manager = MySQLBackupManager(backup_config)
            
            if backup_type == 'full':
                metadata = backup_manager.create_full_backup(database_alias)
            else:
                metadata = backup_manager.create_incremental_backup(database_alias)
            
            return JsonResponse({
                'success': True,
                'backup_id': metadata.backup_id,
                'message': f'{backup_type.title()} backup created successfully'
            })
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return JsonResponse({'error': f'Backup creation failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def verify_backup_api(self, request):
        """API endpoint to verify backup integrity."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            backup_id = data.get('backup_id')
            
            if not backup_id:
                return JsonResponse({'error': 'Backup ID required'}, status=400)
            
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key')
            )
            backup_manager = MySQLBackupManager(backup_config)
            
            is_valid = backup_manager.verify_backup_integrity(backup_id)
            
            return JsonResponse({
                'success': True,
                'valid': is_valid,
                'message': 'Backup is valid' if is_valid else 'Backup integrity check failed'
            })
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return JsonResponse({'error': f'Backup verification failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def restore_backup_api(self, request):
        """API endpoint to restore from backup."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            backup_id = data.get('backup_id')
            database_alias = data.get('database_alias', 'default')
            target_database = data.get('target_database')
            
            if not backup_id:
                return JsonResponse({'error': 'Backup ID required'}, status=400)
            
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/backups'),
                encryption_key=getattr(settings, 'BACKUP_ENCRYPTION_KEY', 'default-key')
            )
            backup_manager = MySQLBackupManager(backup_config)
            
            success = backup_manager.restore_from_backup(backup_id, database_alias, target_database)
            
            return JsonResponse({
                'success': success,
                'message': 'Backup restored successfully' if success else 'Backup restoration failed'
            })
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return JsonResponse({'error': f'Backup restoration failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def refresh_metrics_api(self, request):
        """API endpoint to refresh database metrics."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            database_alias = data.get('database_alias', 'default')
            
            # Force refresh of metrics
            db_monitor = DatabaseMonitor()
            db_monitor._collect_database_metrics(database_alias)
            
            return JsonResponse({
                'success': True,
                'message': f'Metrics refreshed for {database_alias}'
            })
            
        except Exception as e:
            logger.error(f"Metrics refresh failed: {e}")
            return JsonResponse({'error': f'Metrics refresh failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def create_user_api(self, request):
        """API endpoint to create database user."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            privileges = data.get('privileges', [])
            host = data.get('host', '%')
            
            if not username or not password:
                return JsonResponse({'error': 'Username and password required'}, status=400)
            
            security_manager = DatabaseSecurityManager()
            
            # Create user with specified privileges
            with connection.cursor() as cursor:
                create_sql = f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'"
                cursor.execute(create_sql)
                
                if privileges:
                    grant_sql = f"GRANT {', '.join(privileges)} ON *.* TO '{username}'@'{host}'"
                    cursor.execute(grant_sql)
                
                cursor.execute("FLUSH PRIVILEGES")
            
            return JsonResponse({
                'success': True,
                'message': f'User {username} created successfully'
            })
            
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return JsonResponse({'error': f'User creation failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def test_connection_api(self, request):
        """API endpoint to test database connection."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            database_alias = data.get('database_alias', 'default')
            
            conn = connections[database_alias]
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            return JsonResponse({
                'success': True,
                'connected': result[0] == 1,
                'message': f'Connection to {database_alias} successful'
            })
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return JsonResponse({'error': f'Connection test failed: {e}'}, status=500)
    
    @method_decorator(staff_member_required)
    def export_report_api(self, request):
        """API endpoint to export performance report."""
        try:
            report_type = request.GET.get('type', 'performance')
            format_type = request.GET.get('format', 'csv')
            
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
                
                writer = csv.writer(response)
                
                if report_type == 'performance':
                    context = self._get_performance_report_context()
                    writer.writerow(['Metric', 'Value'])
                    for key, value in context.items():
                        if key != 'error':
                            writer.writerow([key.replace('_', ' ').title(), value])
                
                elif report_type == 'health':
                    health_context = self._get_health_check_context()
                    writer.writerow(['Database', 'Status', 'Checks', 'Recommendations'])
                    for db_alias, health in health_context.get('health_results', {}).items():
                        writer.writerow([
                            db_alias,
                            health.get('status', 'unknown'),
                            '; '.join(f"{k}: {v}" for k, v in health.get('checks', {}).items()),
                            '; '.join(health.get('recommendations', []))
                        ])
                
                return response
            
            else:
                return JsonResponse({'error': 'Unsupported format'}, status=400)
                
        except Exception as e:
            logger.error(f"Report export failed: {e}")
            return JsonResponse({'error': f'Report export failed: {e}'}, status=500)


# Create the database administration site
db_admin_site = DatabaseAdministrationSite(name='db_admin')

# Register models with the custom admin site
# Note: Proxy classes are not Django models, so they can't be registered
# db_admin_site.register(DatabaseMetricsProxy, DatabaseMetricsAdmin)
# db_admin_site.register(BackupProxy, BackupAdmin)