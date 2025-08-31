"""
Production Monitoring and Alerting System

This module provides production-ready monitoring capabilities including:
- Production logging configuration with log rotation
- Alerting system for performance threshold violations
- Health check endpoints for system monitoring
- Production monitoring dashboard
- Deployment and monitoring tests
"""

import logging
import logging.handlers
import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connection, transaction, models
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# Import psutil for system monitoring
try:
    import psutil
except ImportError:
    psutil = None

from .models import (
    PerformanceSnapshot, PerformanceThreshold, ErrorLog, 
    WorkflowSession, TraceStep
)
from .performance_monitoring import MetricsCollector, ThresholdManager
from .config import config as debug_config


@dataclass
class Alert:
    """Data structure for system alerts"""
    alert_id: str
    alert_type: str  # 'performance', 'error', 'system', 'security'
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    message: str
    component: str
    layer: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = timezone.now()
        if self.alert_id is None:
            self.alert_id = f"{self.alert_type}_{self.component}_{int(self.timestamp.timestamp())}"


@dataclass
class HealthCheckResult:
    """Data structure for health check results"""
    service: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class SystemStatus:
    """Data structure for overall system status"""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: datetime
    health_checks: List[HealthCheckResult]
    active_alerts: List[Alert]
    performance_summary: Dict[str, Any]
    uptime_seconds: float


class ProductionLogger:
    """Production-ready logging configuration with log rotation"""
    
    def __init__(self):
        self.log_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        self.ensure_log_directory()
        self.setup_production_logging()
    
    def ensure_log_directory(self):
        """Ensure log directory exists"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def setup_production_logging(self):
        """Setup production logging configuration with rotation"""
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Application log with rotation
        app_log_file = os.path.join(self.log_dir, 'application.log')
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        
        # Error log with rotation
        error_log_file = os.path.join(self.log_dir, 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(app_formatter)
        
        # Console handler for development
        if settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(levelname)s: %(name)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Add handlers to root logger
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        
        logging.info("Production logging configuration initialized")
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """Get information about log files"""
        log_files = {}
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(self.log_dir, filename)
                stat = os.stat(filepath)
                log_files[filename] = {
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                }
        
        return log_files
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        cleaned_files = []
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log') and '.' in filename:
                filepath = os.path.join(self.log_dir, filename)
                if os.path.getctime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        cleaned_files.append(filename)
                    except OSError as e:
                        logging.error(f"Failed to remove old log file {filename}: {e}")
        
        if cleaned_files:
            logging.info(f"Cleaned up {len(cleaned_files)} old log files: {cleaned_files}")
        
        return cleaned_files


class AlertingSystem:
    """Production alerting system for performance threshold violations"""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_history = []
        self.notification_channels = self._setup_notification_channels()
        self.alert_rules = self._load_alert_rules()
        self.is_monitoring = False
        self._monitoring_thread = None
        
    def _setup_notification_channels(self) -> Dict[str, Any]:
        """Setup notification channels (email, webhook, etc.)"""
        channels = {}
        
        # Email notifications
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            channels['email'] = {
                'enabled': True,
                'recipients': getattr(settings, 'ALERT_EMAIL_RECIPIENTS', []),
            }
        
        return channels
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules configuration"""
        return {
            'performance_thresholds': {
                'api_response_time': {'warning': 500, 'critical': 2000},  # ms
                'database_query_time': {'warning': 100, 'critical': 500},  # ms
                'memory_usage': {'warning': 80, 'critical': 95},  # %
                'cpu_usage': {'warning': 80, 'critical': 95},  # %
                'error_rate': {'warning': 1, 'critical': 5},  # errors/min
                'disk_usage': {'warning': 85, 'critical': 95},  # %
            },
            'alert_settings': {
                'cooldown_minutes': 15,  # Minimum time between same alerts
                'auto_resolve_minutes': 30,  # Auto-resolve if condition clears
            }
        }
    
    def start_monitoring(self):
        """Start continuous alert monitoring"""
        if self.is_monitoring:
            logging.warning("Alert monitoring already running")
            return
        
        self.is_monitoring = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logging.info("Started production alert monitoring")
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_monitoring = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logging.info("Stopped production alert monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_performance_alerts()
                self._check_system_alerts()
                self._check_error_alerts()
                self._auto_resolve_alerts()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Error in alert monitoring loop: {e}")
                time.sleep(30)  # Wait before retrying
    
    def _check_performance_alerts(self):
        """Check for performance threshold violations"""
        # Get recent performance metrics (last 5 minutes)
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        recent_metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=five_minutes_ago
        ).values('layer', 'component', 'metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value')
        )
        
        for metric in recent_metrics:
            metric_name = metric['metric_name']
            avg_value = metric['avg_value']
            max_value = metric['max_value']
            
            # Check against thresholds
            thresholds = self.alert_rules['performance_thresholds'].get(metric_name)
            if not thresholds:
                continue
            
            # Check critical threshold
            if max_value >= thresholds['critical']:
                self._create_alert(
                    alert_type='performance',
                    severity='critical',
                    title=f"Critical {metric_name} threshold exceeded",
                    message=f"{metric_name} reached {max_value:.2f}, exceeding critical threshold of {thresholds['critical']}",
                    component=metric['component'],
                    layer=metric['layer'],
                    metric_name=metric_name,
                    current_value=max_value,
                    threshold_value=thresholds['critical']
                )
    
    def _check_system_alerts(self):
        """Check for system-level alerts"""
        if not psutil:
            return
            
        try:
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            thresholds = self.alert_rules['performance_thresholds']['disk_usage']
            if disk_percent >= thresholds['critical']:
                self._create_alert(
                    alert_type='system',
                    severity='critical',
                    title="Critical disk usage",
                    message=f"Disk usage at {disk_percent:.1f}%, exceeding critical threshold",
                    component='filesystem',
                    layer='system',
                    metric_name='disk_usage',
                    current_value=disk_percent,
                    threshold_value=thresholds['critical']
                )
        except Exception as e:
            logging.error(f"Error checking system alerts: {e}")
    
    def _check_error_alerts(self):
        """Check for error rate alerts"""
        # Get recent errors (last 5 minutes)
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=five_minutes_ago
        ).values('layer', 'component').annotate(
            error_count=models.Count('id')
        )
        
        for error_data in recent_errors:
            error_rate = error_data['error_count'] / 5  # errors per minute
            
            thresholds = self.alert_rules['performance_thresholds']['error_rate']
            if error_rate >= thresholds['critical']:
                self._create_alert(
                    alert_type='error',
                    severity='critical',
                    title=f"Critical error rate in {error_data['component']}",
                    message=f"Error rate at {error_rate:.2f} errors/min in {error_data['layer']}.{error_data['component']}",
                    component=error_data['component'],
                    layer=error_data['layer'],
                    metric_name='error_rate',
                    current_value=error_rate,
                    threshold_value=thresholds['critical']
                )
    
    def _create_alert(self, alert_type: str, severity: str, title: str, 
                     message: str, component: str, layer: str,
                     metric_name: Optional[str] = None,
                     current_value: Optional[float] = None,
                     threshold_value: Optional[float] = None,
                     correlation_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Create and process a new alert"""
        
        # Create alert key for deduplication
        alert_key = f"{alert_type}_{layer}_{component}_{metric_name}"
        
        # Check cooldown period
        if alert_key in self.active_alerts:
            last_alert = self.active_alerts[alert_key]
            cooldown_minutes = self.alert_rules['alert_settings']['cooldown_minutes']
            if (timezone.now() - last_alert.timestamp).total_seconds() < (cooldown_minutes * 60):
                return  # Skip duplicate alert within cooldown period
        
        # Create new alert
        alert = Alert(
            alert_id=f"{alert_key}_{int(timezone.now().timestamp())}",
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            component=component,
            layer=layer,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        # Store alert
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        # Log alert
        logging.warning(f"ALERT [{severity.upper()}] {title}: {message}")
    
    def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        
        # Email notifications
        if self.notification_channels.get('email', {}).get('enabled'):
            self._send_email_alert(alert)
    
    def _send_email_alert(self, alert: Alert):
        """Send email alert notification"""
        try:
            email_config = self.notification_channels['email']
            recipients = email_config['recipients']
            
            if not recipients:
                return
            
            subject = f"[{alert.severity.upper()}] {alert.title}"
            
            body = f"""
Alert Details:
- Type: {alert.alert_type}
- Severity: {alert.severity}
- Component: {alert.layer}.{alert.component}
- Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message: {alert.message}

Alert ID: {alert.alert_id}
"""
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
    
    def _auto_resolve_alerts(self):
        """Auto-resolve alerts if conditions have cleared"""
        auto_resolve_minutes = self.alert_rules['alert_settings']['auto_resolve_minutes']
        resolve_threshold = timezone.now() - timedelta(minutes=auto_resolve_minutes)
        
        resolved_alerts = []
        
        for alert_key, alert in list(self.active_alerts.items()):
            if alert.resolved or alert.timestamp > resolve_threshold:
                continue
            
            # Check if the condition that triggered the alert has cleared
            if self._check_alert_condition_cleared(alert):
                alert.resolved = True
                alert.resolved_at = timezone.now()
                resolved_alerts.append(alert_key)
                
                logging.info(f"Auto-resolved alert: {alert.title}")
        
        # Remove resolved alerts from active alerts
        for alert_key in resolved_alerts:
            del self.active_alerts[alert_key]
    
    def _check_alert_condition_cleared(self, alert: Alert) -> bool:
        """Check if the condition that triggered an alert has cleared"""
        if not alert.metric_name or alert.threshold_value is None:
            return False
        
        try:
            # Get recent metrics for this component/metric
            recent_time = timezone.now() - timedelta(minutes=5)
            recent_metrics = PerformanceSnapshot.objects.filter(
                timestamp__gte=recent_time,
                layer=alert.layer,
                component=alert.component,
                metric_name=alert.metric_name
            ).aggregate(
                avg_value=models.Avg('metric_value'),
                max_value=models.Max('metric_value')
            )
            
            if not recent_metrics['avg_value']:
                return False
            
            # Check if values are now below threshold
            avg_value = recent_metrics['avg_value']
            max_value = recent_metrics['max_value']
            
            # Use a 10% buffer below threshold to avoid flapping
            buffer_threshold = alert.threshold_value * 0.9
            
            return max_value < buffer_threshold and avg_value < buffer_threshold
            
        except Exception as e:
            logging.error(f"Error checking alert condition for {alert.alert_id}: {e}")
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified hours"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "manual") -> bool:
        """Manually resolve an alert"""
        for alert_key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = timezone.now()
                alert.metadata = alert.metadata or {}
                alert.metadata['resolved_by'] = resolved_by
                
                del self.active_alerts[alert_key]
                logging.info(f"Manually resolved alert {alert_id} by {resolved_by}")
                return True
        
        return False


class HealthCheckService:
    """Health check service for system monitoring"""
    
    def __init__(self):
        self.health_checks = {
            'database': self._check_database_health,
            'cache': self._check_cache_health,
            'disk_space': self._check_disk_space,
            'memory': self._check_memory_usage,
        }
    
    def run_all_health_checks(self) -> List[HealthCheckResult]:
        """Run all health checks and return results"""
        results = []
        
        for service_name, check_function in self.health_checks.items():
            try:
                start_time = time.time()
                result = check_function()
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                results.append(HealthCheckResult(
                    service=service_name,
                    status=result['status'],
                    response_time_ms=response_time,
                    details=result.get('details', {}),
                    timestamp=timezone.now(),
                    error_message=result.get('error_message')
                ))
                
            except Exception as e:
                results.append(HealthCheckResult(
                    service=service_name,
                    status='unhealthy',
                    response_time_ms=0,
                    details={},
                    timestamp=timezone.now(),
                    error_message=str(e)
                ))
        
        return results
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            query_time = (time.time() - start_time) * 1000
            
            # Determine status
            if query_time > 100:
                status = 'degraded'
            elif query_time > 50:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'details': {
                    'query_time_ms': round(query_time, 2),
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error_message': str(e),
                'details': {}
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check Redis cache connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test cache operations
            test_key = 'health_check_test'
            test_value = f'test_{int(time.time())}'
            
            cache.set(test_key, test_value, timeout=60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            operation_time = (time.time() - start_time) * 1000
            
            if retrieved_value != test_value:
                return {
                    'status': 'unhealthy',
                    'error_message': 'Cache value mismatch',
                    'details': {'operation_time_ms': round(operation_time, 2)}
                }
            
            # Determine status based on response time
            if operation_time > 100:
                status = 'degraded'
            elif operation_time > 50:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'details': {
                    'operation_time_ms': round(operation_time, 2),
                    'test_successful': True
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error_message': str(e),
                'details': {}
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage"""
        try:
            if not psutil:
                return {
                    'status': 'degraded',
                    'error_message': 'psutil not available',
                    'details': {}
                }
            
            disk_usage = psutil.disk_usage('/')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Determine status
            if used_percent >= 95:
                status = 'unhealthy'
            elif used_percent >= 85:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'details': {
                    'used_percent': round(used_percent, 2),
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2)
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error_message': str(e),
                'details': {}
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            if not psutil:
                return {
                    'status': 'degraded',
                    'error_message': 'psutil not available',
                    'details': {}
                }
            
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            # Determine status
            if used_percent >= 95:
                status = 'unhealthy'
            elif used_percent >= 85:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'details': {
                    'used_percent': round(used_percent, 2),
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2)
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error_message': str(e),
                'details': {}
            }


class ProductionMonitoringDashboard:
    """Production monitoring dashboard for system overview"""
    
    def __init__(self):
        self.health_service = HealthCheckService()
        self.alerting_system = AlertingSystem()
        self.start_time = timezone.now()
    
    def get_system_status(self) -> SystemStatus:
        """Get overall system status"""
        # Run health checks
        health_checks = self.health_service.run_all_health_checks()
        
        # Get active alerts
        active_alerts = self.alerting_system.get_active_alerts()
        
        # Determine overall status
        overall_status = self._determine_overall_status(health_checks, active_alerts)
        
        # Get performance summary
        performance_summary = self._get_performance_summary()
        
        # Calculate uptime
        uptime_seconds = (timezone.now() - self.start_time).total_seconds()
        
        return SystemStatus(
            status=overall_status,
            timestamp=timezone.now(),
            health_checks=health_checks,
            active_alerts=active_alerts,
            performance_summary=performance_summary,
            uptime_seconds=uptime_seconds
        )
    
    def _determine_overall_status(self, health_checks: List[HealthCheckResult], 
                                active_alerts: List[Alert]) -> str:
        """Determine overall system status"""
        # Check for critical alerts
        critical_alerts = [a for a in active_alerts if a.severity == 'critical']
        if critical_alerts:
            return 'unhealthy'
        
        # Check health check results
        unhealthy_services = [hc for hc in health_checks if hc.status == 'unhealthy']
        if unhealthy_services:
            return 'unhealthy'
        
        degraded_services = [hc for hc in health_checks if hc.status == 'degraded']
        high_alerts = [a for a in active_alerts if a.severity in ['high', 'medium']]
        
        if degraded_services or high_alerts:
            return 'degraded'
        
        return 'healthy'
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the last hour"""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        try:
            # Get recent performance metrics
            recent_metrics = PerformanceSnapshot.objects.filter(
                timestamp__gte=one_hour_ago
            ).values('metric_name').annotate(
                avg_value=models.Avg('metric_value'),
                max_value=models.Max('metric_value'),
                min_value=models.Min('metric_value'),
                count=models.Count('id')
            )
            
            summary = {}
            for metric in recent_metrics:
                summary[metric['metric_name']] = {
                    'avg': round(metric['avg_value'], 2),
                    'max': round(metric['max_value'], 2),
                    'min': round(metric['min_value'], 2),
                    'samples': metric['count']
                }
            
            # Get error count
            error_count = ErrorLog.objects.filter(timestamp__gte=one_hour_ago).count()
            summary['error_count_1h'] = error_count
            
            return summary
            
        except Exception as e:
            logging.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}


# Global instances
production_logger = ProductionLogger()
alerting_system = AlertingSystem()
health_service = HealthCheckService()
monitoring_dashboard = ProductionMonitoringDashboard()


# Django Views for Production Monitoring

@require_http_methods(["GET"])
def health_check_view(request):
    """Health check endpoint for load balancers and monitoring systems"""
    try:
        # Quick health check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'ecommerce-backend'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'ecommerce-backend',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def detailed_health_check_view(request):
    """Detailed health check with all service statuses"""
    try:
        system_status = monitoring_dashboard.get_system_status()
        
        response_data = {
            'overall_status': system_status.status,
            'timestamp': system_status.timestamp.isoformat(),
            'uptime_seconds': system_status.uptime_seconds,
            'health_checks': [
                {
                    'service': hc.service,
                    'status': hc.status,
                    'response_time_ms': hc.response_time_ms,
                    'details': hc.details,
                    'error_message': hc.error_message
                }
                for hc in system_status.health_checks
            ],
            'active_alerts_count': len(system_status.active_alerts),
            'performance_summary': system_status.performance_summary
        }
        
        status_code = 200 if system_status.status == 'healthy' else 503
        return JsonResponse(response_data, status=status_code)
        
    except Exception as e:
        return JsonResponse({
            'overall_status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def alerts_view(request):
    """Get active alerts and alert history"""
    try:
        active_alerts = alerting_system.get_active_alerts()
        hours = int(request.GET.get('hours', 24))
        alert_history = alerting_system.get_alert_history(hours=hours)
        
        return JsonResponse({
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'alert_history': [asdict(alert) for alert in alert_history],
            'total_active': len(active_alerts),
            'total_history': len(alert_history)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def resolve_alert_view(request):
    """Manually resolve an alert"""
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        resolved_by = data.get('resolved_by', 'api')
        
        if not alert_id:
            return JsonResponse({'error': 'alert_id is required'}, status=400)
        
        success = alerting_system.resolve_alert(alert_id, resolved_by)
        
        if success:
            return JsonResponse({'message': f'Alert {alert_id} resolved successfully'})
        else:
            return JsonResponse({'error': f'Alert {alert_id} not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def monitoring_dashboard_view(request):
    """Production monitoring dashboard data"""
    try:
        system_status = monitoring_dashboard.get_system_status()
        
        # Get log files info
        log_files_info = production_logger.get_log_files_info()
        
        dashboard_data = {
            'system_status': {
                'status': system_status.status,
                'timestamp': system_status.timestamp.isoformat(),
                'uptime_seconds': system_status.uptime_seconds,
                'uptime_formatted': str(timedelta(seconds=int(system_status.uptime_seconds)))
            },
            'health_checks': [
                {
                    'service': hc.service,
                    'status': hc.status,
                    'response_time_ms': hc.response_time_ms,
                    'details': hc.details,
                    'error_message': hc.error_message,
                    'timestamp': hc.timestamp.isoformat()
                }
                for hc in system_status.health_checks
            ],
            'alerts': {
                'active': [asdict(alert) for alert in system_status.active_alerts],
                'active_count': len(system_status.active_alerts),
                'critical_count': len([a for a in system_status.active_alerts if a.severity == 'critical']),
                'high_count': len([a for a in system_status.active_alerts if a.severity == 'high'])
            },
            'performance': system_status.performance_summary,
            'logs': log_files_info
        }
        
        return JsonResponse(dashboard_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


# Utility functions for production deployment

def start_production_monitoring():
    """Start production monitoring services"""
    try:
        # Start alerting system
        alerting_system.start_monitoring()
        
        # Setup production logging
        production_logger.setup_production_logging()
        
        logging.info("Production monitoring started successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to start production monitoring: {e}")
        return False


def stop_production_monitoring():
    """Stop production monitoring services"""
    try:
        alerting_system.stop_monitoring()
        logging.info("Production monitoring stopped")
        return True
        
    except Exception as e:
        logging.error(f"Failed to stop production monitoring: {e}")
        return False


def cleanup_old_data(days_to_keep: int = 30):
    """Clean up old monitoring data"""
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Clean up old performance snapshots
        deleted_snapshots = PerformanceSnapshot.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        # Clean up old error logs
        deleted_errors = ErrorLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        # Clean up old workflow sessions
        deleted_sessions = WorkflowSession.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        # Clean up old log files
        cleaned_log_files = production_logger.cleanup_old_logs(days_to_keep)
        
        logging.info(f"Cleaned up old data: {deleted_snapshots} snapshots, "
                    f"{deleted_errors} errors, {deleted_sessions} sessions, "
                    f"{len(cleaned_log_files)} log files")
        
        return {
            'deleted_snapshots': deleted_snapshots,
            'deleted_errors': deleted_errors,
            'deleted_sessions': deleted_sessions,
            'cleaned_log_files': len(cleaned_log_files)
        }
        
    except Exception as e:
        logging.error(f"Error cleaning up old data: {e}")
        return {'error': str(e)}


# Production monitoring initialization
def initialize_production_monitoring():
    """Initialize production monitoring on Django startup"""
    try:
        # Start monitoring services
        start_production_monitoring()
        
        logging.info("Production monitoring initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize production monitoring: {e}")


# Export main components
__all__ = [
    'ProductionLogger',
    'AlertingSystem', 
    'HealthCheckService',
    'ProductionMonitoringDashboard',
    'Alert',
    'HealthCheckResult',
    'SystemStatus',
    'health_check_view',
    'detailed_health_check_view',
    'alerts_view',
    'resolve_alert_view',
    'monitoring_dashboard_view',
    'start_production_monitoring',
    'stop_production_monitoring',
    'cleanup_old_data',
    'initialize_production_monitoring'
]