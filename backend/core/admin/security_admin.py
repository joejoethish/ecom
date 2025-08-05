"""
Django Admin interface for database security monitoring.

This module provides admin interfaces for:
- Viewing audit logs
- Monitoring security events
- Managing security metrics
- Configuring security settings

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import connection
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
import csv
from typing import Dict, List, Any
from core.database_security import database_security_manager, AuditEventType


class AuditLogProxy:
    """Proxy model for audit log entries to work with Django admin."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    class Meta:
        managed = False
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"


class SecurityEventProxy:
    """Proxy model for security events to work with Django admin."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    class Meta:
        managed = False
        verbose_name = "Security Event"
        verbose_name_plural = "Security Events"


# AuditLogProxy is not a Django model, so we can't register it with admin
# @admin.register(AuditLogProxy)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing audit logs."""
    
    list_display = [
        'timestamp', 'event_type', 'user', 'source_ip', 
        'database_name', 'table_name', 'operation', 
        'affected_rows', 'success_status', 'view_details'
    ]
    list_filter = [
        'event_type', 'success', 'database_name', 'table_name', 'operation'
    ]
    search_fields = ['user', 'source_ip', 'table_name', 'query_hash']
    readonly_fields = [
        'timestamp', 'event_type', 'user', 'source_ip', 
        'database_name', 'table_name', 'operation', 
        'affected_rows', 'query_hash', 'success', 
        'error_message', 'additional_data'
    ]
    ordering = ['-timestamp']
    list_per_page = 50
    
    def has_add_permission(self, request):
        """Audit logs cannot be added manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs cannot be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs cannot be deleted."""
        return False
    
    def get_queryset(self, request):
        """Get audit log entries from database."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, timestamp, event_type, user, source_ip, 
                           database_name, table_name, operation, affected_rows, 
                           query_hash, success, error_message, additional_data
                    FROM db_audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                """)
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to proxy objects
                audit_logs = []
                for row in rows:
                    data = dict(zip(columns, row))
                    # Parse JSON additional_data if present
                    if data.get('additional_data'):
                        try:
                            data['additional_data'] = json.loads(data['additional_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    audit_logs.append(AuditLogProxy(**data))
                
                return audit_logs
        except Exception as e:
            messages.error(request, f"Error loading audit logs: {e}")
            return []
    
    def success_status(self, obj):
        """Display success status with color coding."""
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Success</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Failed</span>'
            )
    success_status.short_description = 'Status'
    
    def view_details(self, obj):
        """Link to view detailed information."""
        return format_html(
            '<a href="javascript:void(0)" onclick="showAuditDetails({})">View Details</a>',
            obj.id
        )
    view_details.short_description = 'Details'
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist view with additional functionality."""
        extra_context = extra_context or {}
        
        # Add summary statistics
        try:
            with connection.cursor() as cursor:
                # Get event type counts for last 24 hours
                cursor.execute("""
                    SELECT event_type, COUNT(*) as count
                    FROM db_audit_log 
                    WHERE timestamp >= %s
                    GROUP BY event_type
                    ORDER BY count DESC
                """, [datetime.now() - timedelta(hours=24)])
                
                event_stats = dict(cursor.fetchall())
                
                # Get success/failure counts
                cursor.execute("""
                    SELECT success, COUNT(*) as count
                    FROM db_audit_log 
                    WHERE timestamp >= %s
                    GROUP BY success
                """, [datetime.now() - timedelta(hours=24)])
                
                success_stats = dict(cursor.fetchall())
                
                extra_context.update({
                    'event_stats': event_stats,
                    'success_stats': success_stats,
                    'total_events_24h': sum(event_stats.values()),
                })
        except Exception as e:
            messages.error(request, f"Error loading statistics: {e}")
        
        return super().changelist_view(request, extra_context)


# SecurityEventProxy is not a Django model, so we can't register it with admin
# @admin.register(SecurityEventProxy)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin interface for viewing security events."""
    
    list_display = [
        'timestamp', 'event_type', 'severity_badge', 'user', 
        'source_ip', 'description_short', 'resolved_status', 'actions'
    ]
    list_filter = ['event_type', 'severity', 'resolved']
    search_fields = ['user', 'source_ip', 'description']
    readonly_fields = [
        'timestamp', 'event_type', 'severity', 'user', 
        'source_ip', 'description', 'details'
    ]
    ordering = ['-timestamp']
    list_per_page = 25
    
    def has_add_permission(self, request):
        """Security events cannot be added manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow marking events as resolved."""
        return request.user.has_perm('auth.change_user')
    
    def has_delete_permission(self, request, obj=None):
        """Security events cannot be deleted."""
        return False
    
    def get_queryset(self, request):
        """Get security events from database."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, timestamp, event_type, severity, user, source_ip, 
                           description, details, resolved, resolved_at, resolved_by
                    FROM db_security_events 
                    ORDER BY timestamp DESC 
                    LIMIT 500
                """)
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to proxy objects
                security_events = []
                for row in rows:
                    data = dict(zip(columns, row))
                    # Parse JSON details if present
                    if data.get('details'):
                        try:
                            data['details'] = json.loads(data['details'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    security_events.append(SecurityEventProxy(**data))
                
                return security_events
        except Exception as e:
            messages.error(request, f"Error loading security events: {e}")
            return []
    
    def severity_badge(self, obj):
        """Display severity with color-coded badge."""
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107', 
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.severity
        )
    severity_badge.short_description = 'Severity'
    
    def description_short(self, obj):
        """Display truncated description."""
        if len(obj.description) > 80:
            return obj.description[:80] + '...'
        return obj.description
    description_short.short_description = 'Description'
    
    def resolved_status(self, obj):
        """Display resolved status."""
        if obj.resolved:
            return format_html(
                '<span style="color: green;">✓ Resolved</span><br>'
                '<small>by {} at {}</small>',
                obj.resolved_by or 'Unknown',
                obj.resolved_at.strftime('%Y-%m-%d %H:%M') if obj.resolved_at else 'Unknown'
            )
        else:
            return format_html('<span style="color: red;">⚠ Open</span>')
    resolved_status.short_description = 'Status'
    
    def actions(self, obj):
        """Action buttons for security events."""
        if not obj.resolved:
            return format_html(
                '<a href="javascript:void(0)" onclick="resolveSecurityEvent({})" '
                'class="button" style="font-size: 11px;">Mark Resolved</a>',
                obj.id
            )
        return '-'
    actions.short_description = 'Actions'


class SecurityDashboardAdmin(admin.ModelAdmin):
    """Custom admin view for security dashboard."""
    
    def has_module_permission(self, request):
        """Check if user has permission to view security dashboard."""
        return request.user.is_staff and request.user.has_perm('auth.view_user')
    
    @method_decorator(staff_member_required)
    def dashboard_view(self, request):
        """Display security dashboard."""
        context = self._get_dashboard_context()
        return render(request, 'admin/security_dashboard.html', context)
    
    def _get_dashboard_context(self) -> Dict[str, Any]:
        """Get context data for security dashboard."""
        context = {}
        
        try:
            with connection.cursor() as cursor:
                # Security events summary
                cursor.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM db_security_events 
                    WHERE timestamp >= %s AND resolved = FALSE
                    GROUP BY severity
                """, [datetime.now() - timedelta(days=7)])
                
                open_events = dict(cursor.fetchall())
                
                # Recent failed login attempts
                cursor.execute("""
                    SELECT user, source_ip, COUNT(*) as attempts
                    FROM db_audit_log 
                    WHERE event_type = 'LOGIN_FAILURE' 
                    AND timestamp >= %s
                    GROUP BY user, source_ip
                    HAVING attempts >= 3
                    ORDER BY attempts DESC
                    LIMIT 10
                """, [datetime.now() - timedelta(hours=24)])
                
                failed_logins = cursor.fetchall()
                
                # Top database users by activity
                cursor.execute("""
                    SELECT user, COUNT(*) as activity_count
                    FROM db_audit_log 
                    WHERE timestamp >= %s
                    GROUP BY user
                    ORDER BY activity_count DESC
                    LIMIT 10
                """, [datetime.now() - timedelta(hours=24)])
                
                top_users = cursor.fetchall()
                
                # Recent suspicious activities
                cursor.execute("""
                    SELECT timestamp, event_type, user, source_ip, description
                    FROM db_security_events 
                    WHERE severity IN ('HIGH', 'CRITICAL')
                    AND timestamp >= %s
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, [datetime.now() - timedelta(days=1)])
                
                suspicious_activities = cursor.fetchall()
                
                context.update({
                    'open_events': open_events,
                    'failed_logins': failed_logins,
                    'top_users': top_users,
                    'suspicious_activities': suspicious_activities,
                    'total_open_events': sum(open_events.values()),
                })
                
        except Exception as e:
            context['error'] = f"Error loading dashboard data: {e}"
        
        return context


# Register the security dashboard
# Note: SecurityEventProxy is not a Django model, so we can't use it with admin
# security_dashboard = SecurityDashboardAdmin(SecurityEventProxy, admin.site)


class SecurityReportsAdmin:
    """Admin interface for security reports and exports."""
    
    @staticmethod
    @staff_member_required
    def export_audit_logs(request):
        """Export audit logs to CSV."""
        try:
            # Get date range from request
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="audit_logs_{start_date}_to_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Timestamp', 'Event Type', 'User', 'Source IP', 
                'Database', 'Table', 'Operation', 'Affected Rows', 
                'Success', 'Error Message'
            ])
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT timestamp, event_type, user, source_ip, database_name, 
                           table_name, operation, affected_rows, success, error_message
                    FROM db_audit_log 
                    WHERE DATE(timestamp) BETWEEN %s AND %s
                    ORDER BY timestamp DESC
                """, [start_date, end_date])
                
                for row in cursor.fetchall():
                    writer.writerow(row)
            
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'Export failed: {e}'}, status=500)
    
    @staticmethod
    @staff_member_required
    def security_summary_report(request):
        """Generate security summary report."""
        try:
            days = int(request.GET.get('days', 7))
            start_date = datetime.now() - timedelta(days=days)
            
            with connection.cursor() as cursor:
                # Get comprehensive security metrics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as failed_events,
                        COUNT(DISTINCT user) as unique_users,
                        COUNT(DISTINCT source_ip) as unique_ips
                    FROM db_audit_log 
                    WHERE timestamp >= %s
                """, [start_date])
                
                summary = cursor.fetchone()
                
                # Get event type breakdown
                cursor.execute("""
                    SELECT event_type, COUNT(*) as count
                    FROM db_audit_log 
                    WHERE timestamp >= %s
                    GROUP BY event_type
                    ORDER BY count DESC
                """, [start_date])
                
                event_breakdown = cursor.fetchall()
                
                # Get security events by severity
                cursor.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM db_security_events 
                    WHERE timestamp >= %s
                    GROUP BY severity
                """, [start_date])
                
                security_breakdown = cursor.fetchall()
                
                report_data = {
                    'period_days': days,
                    'summary': {
                        'total_events': summary[0],
                        'failed_events': summary[1],
                        'unique_users': summary[2],
                        'unique_ips': summary[3],
                        'success_rate': round((summary[0] - summary[1]) / summary[0] * 100, 2) if summary[0] > 0 else 0
                    },
                    'event_breakdown': [{'type': row[0], 'count': row[1]} for row in event_breakdown],
                    'security_breakdown': [{'severity': row[0], 'count': row[1]} for row in security_breakdown],
                    'generated_at': datetime.now().isoformat()
                }
                
                return JsonResponse(report_data)
                
        except Exception as e:
            return JsonResponse({'error': f'Report generation failed: {e}'}, status=500)


# Custom admin site configuration
class SecurityAdminSite(admin.AdminSite):
    """Custom admin site for security monitoring."""
    
    site_header = "Database Security Monitoring"
    site_title = "Security Admin"
    index_title = "Security Dashboard"
    
    def get_urls(self):
        """Add custom URLs for security admin."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            # path('security-dashboard/', security_dashboard.dashboard_view, name='security_dashboard'),
            path('export-audit-logs/', SecurityReportsAdmin.export_audit_logs, name='export_audit_logs'),
            path('security-report/', SecurityReportsAdmin.security_summary_report, name='security_report'),
        ]
        return custom_urls + urls


# Create custom admin site instance
security_admin_site = SecurityAdminSite(name='security_admin')

# Register models with custom admin site
# Note: Proxy classes are not Django models, so they can't be registered
# security_admin_site.register(AuditLogProxy, AuditLogAdmin)
# security_admin_site.register(SecurityEventProxy, SecurityEventAdmin)

# Additional admin actions and views
class SecurityActionsAdmin:
    """Additional security actions and utilities."""
    
    @staticmethod
    @staff_member_required
    def resolve_security_event(request):
        """Mark a security event as resolved."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            data = json.loads(request.body)
            event_id = data.get('event_id')
            
            if not event_id:
                return JsonResponse({'error': 'Event ID required'}, status=400)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE db_security_events 
                    SET resolved = TRUE, resolved_at = %s, resolved_by = %s
                    WHERE id = %s
                """, [datetime.now(), request.user.username, event_id])
                
                if cursor.rowcount > 0:
                    # Log the resolution
                    database_security_manager.log_audit_event(
                        event_type=AuditEventType.CONFIGURATION_CHANGE,
                        user=request.user.username,
                        source_ip=request.META.get('REMOTE_ADDR', 'unknown'),
                        database='ecommerce_db',
                        table='db_security_events',
                        operation='RESOLVE_EVENT',
                        affected_rows=1,
                        query_hash=f"resolve_{event_id}",
                        success=True,
                        additional_data={'event_id': event_id}
                    )
                    
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'error': 'Event not found'}, status=404)
                    
        except Exception as e:
            return JsonResponse({'error': f'Failed to resolve event: {e}'}, status=500)
    
    @staticmethod
    @staff_member_required
    def run_security_scan(request):
        """Run a comprehensive security scan."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            scan_results = []
            
            # Check for weak passwords (simulated)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM auth_user 
                    WHERE LENGTH(password) < 60
                """)
                weak_passwords = cursor.fetchone()[0]
                
                if weak_passwords > 0:
                    scan_results.append(f"Found {weak_passwords} users with potentially weak passwords")
                
                # Check for inactive admin accounts
                cursor.execute("""
                    SELECT COUNT(*) FROM auth_user 
                    WHERE is_superuser = TRUE AND last_login < %s
                """, [datetime.now() - timedelta(days=90)])
                
                inactive_admins = cursor.fetchone()[0]
                if inactive_admins > 0:
                    scan_results.append(f"Found {inactive_admins} inactive admin accounts")
                
                # Check for suspicious login patterns
                cursor.execute("""
                    SELECT COUNT(DISTINCT source_ip) as ip_count
                    FROM db_audit_log 
                    WHERE event_type = 'LOGIN_FAILURE' 
                    AND timestamp >= %s
                    HAVING ip_count > 10
                """, [datetime.now() - timedelta(hours=24)])
                
                result = cursor.fetchone()
                if result and result[0] > 10:
                    scan_results.append(f"Detected login attempts from {result[0]} different IPs in 24h")
            
            # Log security scan
            database_security_manager.log_audit_event(
                event_type=AuditEventType.CONFIGURATION_CHANGE,
                user=request.user.username,
                source_ip=request.META.get('REMOTE_ADDR', 'unknown'),
                database='ecommerce_db',
                table='security_scan',
                operation='SECURITY_SCAN',
                affected_rows=0,
                query_hash='security_scan',
                success=True,
                additional_data={'scan_results': scan_results}
            )
            
            return JsonResponse({
                'success': True,
                'results': scan_results if scan_results else ['No security issues detected']
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Security scan failed: {e}'}, status=500)
    
    @staticmethod
    @staff_member_required
    def test_database_security(request):
        """Test database security configuration."""
        if request.method != 'POST':
            return JsonResponse({'error': 'POST method required'}, status=405)
        
        try:
            test_results = {}
            
            # Test SSL connection
            ssl_test = database_security_manager.setup_ssl_encryption()
            test_results['ssl_encryption'] = 'PASS' if ssl_test else 'FAIL'
            
            # Test audit logging
            with connection.cursor() as cursor:
                cursor.execute("SHOW VARIABLES LIKE 'general_log'")
                general_log = cursor.fetchone()
                test_results['audit_logging'] = 'PASS' if general_log and general_log[1] == 'ON' else 'FAIL'
                
                # Test user privileges
                cursor.execute("SELECT COUNT(*) FROM mysql.user WHERE Super_priv = 'Y'")
                super_users = cursor.fetchone()[0]
                test_results['privilege_separation'] = 'PASS' if super_users <= 2 else 'WARN'
                
                # Test password policies
                cursor.execute("SHOW VARIABLES LIKE 'validate_password%'")
                password_validation = cursor.fetchall()
                test_results['password_policy'] = 'PASS' if password_validation else 'WARN'
            
            # Log security test
            database_security_manager.log_audit_event(
                event_type=AuditEventType.CONFIGURATION_CHANGE,
                user=request.user.username,
                source_ip=request.META.get('REMOTE_ADDR', 'unknown'),
                database='ecommerce_db',
                table='security_test',
                operation='SECURITY_TEST',
                affected_rows=0,
                query_hash='security_test',
                success=True,
                additional_data={'test_results': test_results}
            )
            
            return JsonResponse({
                'success': True,
                'results': test_results
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Security test failed: {e}'}, status=500)
    
    @staticmethod
    @staff_member_required
    def audit_log_detail(request, log_id):
        """Display detailed audit log information."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM db_audit_log WHERE id = %s
                """, [log_id])
                
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                if not row:
                    return JsonResponse({'error': 'Audit log not found'}, status=404)
                
                log_data = dict(zip(columns, row))
                
                # Parse additional_data if present
                if log_data.get('additional_data'):
                    try:
                        log_data['additional_data'] = json.loads(log_data['additional_data'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                return render(request, 'admin/audit_log_detail.html', {
                    'log_data': log_data,
                    'title': f'Audit Log Detail - {log_id}'
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Failed to load audit log: {e}'}, status=500)


# Update the custom admin site with additional URLs
def get_security_admin_urls():
    """Get all security admin URLs."""
    from django.urls import path
    
    return [
        # path('security-dashboard/', security_dashboard.dashboard_view, name='security_dashboard'),
        path('export-audit-logs/', SecurityReportsAdmin.export_audit_logs, name='export_audit_logs'),
        path('security-report/', SecurityReportsAdmin.security_summary_report, name='security_report'),
        path('resolve-security-event/', SecurityActionsAdmin.resolve_security_event, name='resolve_security_event'),
        path('run-security-scan/', SecurityActionsAdmin.run_security_scan, name='run_security_scan'),
        path('test-database-security/', SecurityActionsAdmin.test_database_security, name='test_database_security'),
        path('audit-log-detail/<int:log_id>/', SecurityActionsAdmin.audit_log_detail, name='audit_log_detail'),
    ]


# Override the get_urls method for the custom admin site
SecurityAdminSite.get_urls = lambda self: get_security_admin_urls() + super(SecurityAdminSite, self).get_urls()


# Initialize the database security manager instance
try:
    database_security_manager = database_security_manager
except NameError:
    from core.database_security import DatabaseSecurityManager
    database_security_manager = DatabaseSecurityManager()