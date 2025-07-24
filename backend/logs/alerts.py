"""
Alerting system for the ecommerce platform.
"""
import logging
import json
import os
import time
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Create a dedicated alerts logger
alerts_logger = logging.getLogger('alerts')

# Default alert configurations
DEFAULT_ALERT_CONFIGS = [
    {
        'id': 'high_cpu_usage',
        'name': 'High CPU Usage',
        'description': 'Alert when CPU usage exceeds threshold',
        'metric': 'system_metrics',
        'field': 'cpu_percent',
        'condition': 'gt',
        'threshold': 80,
        'duration': 300,  # 5 minutes
        'cooldown': 3600,  # 1 hour
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'high_memory_usage',
        'name': 'High Memory Usage',
        'description': 'Alert when memory usage exceeds threshold',
        'metric': 'system_metrics',
        'field': 'memory_percent',
        'condition': 'gt',
        'threshold': 85,
        'duration': 300,  # 5 minutes
        'cooldown': 3600,  # 1 hour
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'high_disk_usage',
        'name': 'High Disk Usage',
        'description': 'Alert when disk usage exceeds threshold',
        'metric': 'system_metrics',
        'field': 'disk_percent',
        'condition': 'gt',
        'threshold': 90,
        'duration': 300,  # 5 minutes
        'cooldown': 3600,  # 1 hour
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'error_rate',
        'name': 'High Error Rate',
        'description': 'Alert when error rate exceeds threshold',
        'metric': 'error_rate',
        'field': 'error_count',
        'condition': 'gt',
        'threshold': 10,
        'duration': 300,  # 5 minutes
        'cooldown': 1800,  # 30 minutes
        'enabled': True,
        'severity': 'error',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'slow_response_time',
        'name': 'Slow Response Time',
        'description': 'Alert when average response time exceeds threshold',
        'metric': 'request_duration',
        'field': 'avg_time',
        'condition': 'gt',
        'threshold': 1000,  # 1 second
        'duration': 300,  # 5 minutes
        'cooldown': 1800,  # 30 minutes
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'security_events',
        'name': 'Security Events',
        'description': 'Alert when security events exceed threshold',
        'metric': 'security_events',
        'field': 'event_count',
        'condition': 'gt',
        'threshold': 5,
        'duration': 300,  # 5 minutes
        'cooldown': 1800,  # 30 minutes
        'enabled': True,
        'severity': 'error',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'database_connections',
        'name': 'High Database Connections',
        'description': 'Alert when database connections exceed threshold',
        'metric': 'database_metrics',
        'field': 'db_connections',
        'condition': 'gt',
        'threshold': 50,
        'duration': 300,  # 5 minutes
        'cooldown': 1800,  # 30 minutes
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
    {
        'id': 'api_error_rate',
        'name': 'High API Error Rate',
        'description': 'Alert when API error rate exceeds threshold',
        'metric': 'api_request',
        'field': 'error_rate',
        'condition': 'gt',
        'threshold': 5,  # 5%
        'duration': 300,  # 5 minutes
        'cooldown': 1800,  # 30 minutes
        'enabled': True,
        'severity': 'warning',
        'channels': ['email', 'slack', 'database'],
    },
]


class AlertManager:
    """
    Manager for system alerts.
    """
    def __init__(self):
        self.config_file = os.path.join(settings.BASE_DIR, 'logs', 'alert_config.json')
        self.alert_configs = self._load_alert_configs()
        self.alert_state = {}  # Track alert states
        self.thread = None
        self.stop_event = threading.Event()
    
    def _load_alert_configs(self):
        """
        Load alert configurations from file or use defaults.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config file
                self._save_alert_configs(DEFAULT_ALERT_CONFIGS)
                return DEFAULT_ALERT_CONFIGS
        except Exception as e:
            alerts_logger.error(f"Failed to load alert configurations: {str(e)}")
            return DEFAULT_ALERT_CONFIGS
    
    def _save_alert_configs(self, configs):
        """
        Save alert configurations to file.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(configs, f, indent=2)
            
            return True
        except Exception as e:
            alerts_logger.error(f"Failed to save alert configurations: {str(e)}")
            return False
    
    def get_alert_configs(self):
        """
        Get current alert configurations.
        """
        return self.alert_configs
    
    def update_alert_config(self, alert_id, **kwargs):
        """
        Update an alert configuration.
        
        Args:
            alert_id: ID of the alert to update
            **kwargs: Configuration parameters to update
        
        Returns:
            Boolean indicating success
        """
        for i, config in enumerate(self.alert_configs):
            if config['id'] == alert_id:
                # Update the specified parameters
                for key, value in kwargs.items():
                    if key in config:
                        self.alert_configs[i][key] = value
                
                # Save the updated configurations
                return self._save_alert_configs(self.alert_configs)
        
        return False
    
    def start(self):
        """
        Start the alert monitoring thread.
        """
        if self.thread is not None and self.thread.is_alive():
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """
        Stop the alert monitoring thread.
        """
        if self.thread is not None and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """
        Main monitoring loop that checks for alert conditions.
        """
        while not self.stop_event.is_set():
            try:
                self._check_alerts()
            except Exception as e:
                alerts_logger.error(f"Error in alert monitoring loop: {str(e)}")
            
            # Sleep for 60 seconds or until stopped
            self.stop_event.wait(60)
    
    def _check_alerts(self):
        """
        Check all alert conditions.
        """
        for alert_config in self.alert_configs:
            if not alert_config['enabled']:
                continue
            
            try:
                self._check_alert_condition(alert_config)
            except Exception as e:
                alerts_logger.error(f"Error checking alert {alert_config['id']}: {str(e)}")
    
    def _check_alert_condition(self, alert_config):
        """
        Check a specific alert condition.
        
        Args:
            alert_config: Alert configuration to check
        """
        alert_id = alert_config['id']
        metric = alert_config['metric']
        field = alert_config['field']
        condition = alert_config['condition']
        threshold = alert_config['threshold']
        duration = alert_config['duration']
        cooldown = alert_config['cooldown']
        
        # Check if alert is in cooldown
        if alert_id in self.alert_state:
            last_triggered = self.alert_state[alert_id]['last_triggered']
            if timezone.now() - last_triggered < timedelta(seconds=cooldown):
                return
        
        # Get metric value based on metric type
        value = self._get_metric_value(metric, field)
        
        # Check condition
        triggered = False
        if condition == 'gt' and value > threshold:
            triggered = True
        elif condition == 'lt' and value < threshold:
            triggered = True
        elif condition == 'eq' and value == threshold:
            triggered = True
        
        # Update alert state
        if triggered:
            # Check if this is a new alert or continuing alert
            if alert_id not in self.alert_state:
                self.alert_state[alert_id] = {
                    'first_detected': timezone.now(),
                    'last_checked': timezone.now(),
                    'current_value': value,
                    'triggered': False,
                }
            else:
                self.alert_state[alert_id]['last_checked'] = timezone.now()
                self.alert_state[alert_id]['current_value'] = value
            
            # Check if alert has been triggered for the required duration
            first_detected = self.alert_state[alert_id]['first_detected']
            if timezone.now() - first_detected >= timedelta(seconds=duration) and not self.alert_state[alert_id]['triggered']:
                # Trigger the alert
                self.alert_state[alert_id]['triggered'] = True
                self.alert_state[alert_id]['last_triggered'] = timezone.now()
                self._trigger_alert(alert_config, value)
        else:
            # Reset alert state if condition is no longer met
            if alert_id in self.alert_state:
                del self.alert_state[alert_id]
    
    def _get_metric_value(self, metric, field):
        """
        Get the current value for a metric.
        
        Args:
            metric: Metric type
            field: Field to check
        
        Returns:
            Current value of the metric
        """
        # This would normally query the database or metrics system
        # For now, we'll use a simple implementation
        
        if metric == 'system_metrics':
            # Get system metrics from database
            from apps.logs.models import PerformanceMetric
            
            # Get the latest system metric
            latest = PerformanceMetric.objects.filter(
                name='system_metrics'
            ).order_by('-timestamp').first()
            
            if latest:
                if field == 'cpu_percent':
                    return latest.value
                elif field == 'memory_percent':
                    return latest.response_time
                elif field == 'disk_percent':
                    # This would need to be added to the metrics
                    return 0
            
            return 0
        
        elif metric == 'error_rate':
            # Calculate error rate from logs
            from apps.logs.models import SystemLog
            from django.db.models import Count
            
            # Count errors in the last 5 minutes
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            error_count = SystemLog.objects.filter(
                level__in=['ERROR', 'CRITICAL'],
                created_at__gte=five_minutes_ago
            ).count()
            
            return error_count
        
        elif metric == 'request_duration':
            # Get average response time
            from apps.logs.models import PerformanceMetric
            from django.db.models import Avg
            
            # Calculate average response time in the last 5 minutes
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            avg_time = PerformanceMetric.objects.filter(
                name='request_duration',
                timestamp__gte=five_minutes_ago
            ).aggregate(avg_time=Avg('value'))['avg_time'] or 0
            
            return avg_time
        
        elif metric == 'security_events':
            # Count security events
            from apps.logs.models import SecurityEvent
            
            # Count security events in the last 5 minutes
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            event_count = SecurityEvent.objects.filter(
                timestamp__gte=five_minutes_ago
            ).count()
            
            return event_count
        
        elif metric == 'database_metrics':
            # Get database connections
            from apps.logs.models import PerformanceMetric
            
            # Get the latest database metric
            latest = PerformanceMetric.objects.filter(
                name='database_metrics'
            ).order_by('-timestamp').first()
            
            if latest and field == 'db_connections':
                return latest.value
            
            return 0
        
        elif metric == 'api_request':
            # Calculate API error rate
            from apps.logs.models import PerformanceMetric
            from django.db.models import Count, Case, When, IntegerField, F
            
            # Calculate error rate in the last 5 minutes
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            metrics = PerformanceMetric.objects.filter(
                name='api_request',
                timestamp__gte=five_minutes_ago
            ).aggregate(
                total=Count('id'),
                errors=Count(Case(
                    When(response_time__gte=400, then=1),
                    output_field=IntegerField()
                ))
            )
            
            total = metrics['total'] or 0
            errors = metrics['errors'] or 0
            
            if total > 0:
                return (errors / total) * 100
            
            return 0
        
        # Default
        return 0
    
    def _trigger_alert(self, alert_config, value):
        """
        Trigger an alert.
        
        Args:
            alert_config: Alert configuration
            value: Current metric value
        """
        alert_id = alert_config['id']
        name = alert_config['name']
        description = alert_config['description']
        severity = alert_config['severity']
        channels = alert_config['channels']
        
        # Log the alert
        alerts_logger.warning(
            f"Alert triggered: {name} - {description} - Current value: {value}",
            extra={
                'alert_id': alert_id,
                'alert_name': name,
                'severity': severity,
                'value': value,
                'threshold': alert_config['threshold'],
                'condition': alert_config['condition'],
            }
        )
        
        # Send alert through configured channels
        if 'email' in channels:
            self._send_email_alert(alert_config, value)
        
        if 'slack' in channels:
            self._send_slack_alert(alert_config, value)
        
        if 'database' in channels:
            self._store_alert_in_database(alert_config, value)
    
    def _send_email_alert(self, alert_config, value):
        """
        Send an email alert.
        
        Args:
            alert_config: Alert configuration
            value: Current metric value
        """
        try:
            subject = f"Alert: {alert_config['name']}"
            
            # Prepare email context
            context = {
                'alert': alert_config,
                'value': value,
                'timestamp': timezone.now(),
                'site_name': getattr(settings, 'SITE_NAME', 'Ecommerce Platform'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            }
            
            # Render email body from template
            html_message = render_to_string('logs/email/alert.html', context)
            plain_message = render_to_string('logs/email/alert.txt', context)
            
            # Get recipients from settings
            recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
            if not recipients and hasattr(settings, 'ADMINS'):
                recipients = [admin[1] for admin in settings.ADMINS]
            
            if recipients:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@example.com'),
                    recipient_list=recipients,
                    html_message=html_message,
                )
        except Exception as e:
            alerts_logger.error(f"Failed to send email alert: {str(e)}")
    
    def _send_slack_alert(self, alert_config, value):
        """
        Send a Slack alert.
        
        Args:
            alert_config: Alert configuration
            value: Current metric value
        """
        try:
            import requests
            
            # Get Slack webhook URL from settings
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if not webhook_url:
                return
            
            # Prepare Slack message
            message = {
                "text": f"*Alert: {alert_config['name']}*",
                "attachments": [
                    {
                        "color": self._get_color_for_severity(alert_config['severity']),
                        "fields": [
                            {
                                "title": "Description",
                                "value": alert_config['description'],
                                "short": False
                            },
                            {
                                "title": "Value",
                                "value": str(value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert_config['threshold']),
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert_config['severity'].upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Send the message
            requests.post(webhook_url, json=message, timeout=5)
        except Exception as e:
            alerts_logger.error(f"Failed to send Slack alert: {str(e)}")
    
    def _store_alert_in_database(self, alert_config, value):
        """
        Store an alert in the database.
        
        Args:
            alert_config: Alert configuration
            value: Current metric value
        """
        try:
            from apps.logs.models import SystemLog
            
            # Create a log entry for the alert
            SystemLog.objects.create(
                level='WARNING',
                logger_name='alerts',
                message=f"Alert triggered: {alert_config['name']} - {alert_config['description']} - Current value: {value}",
                source='alerts',
                event_type='alert_triggered',
                extra_data={
                    'alert_id': alert_config['id'],
                    'alert_name': alert_config['name'],
                    'severity': alert_config['severity'],
                    'value': value,
                    'threshold': alert_config['threshold'],
                    'condition': alert_config['condition'],
                }
            )
        except Exception as e:
            alerts_logger.error(f"Failed to store alert in database: {str(e)}")
    
    def _get_color_for_severity(self, severity):
        """
        Get color code for alert severity.
        
        Args:
            severity: Alert severity
        
        Returns:
            Color code for Slack message
        """
        if severity == 'critical':
            return "#FF0000"  # Red
        elif severity == 'error':
            return "#E74C3C"  # Light red
        elif severity == 'warning':
            return "#FFA500"  # Orange
        elif severity == 'info':
            return "#3498DB"  # Blue
        return "#808080"  # Gray for unknown severity


# Create a singleton instance
alert_manager = AlertManager()


def get_alert_configs():
    """
    Get current alert configurations.
    """
    return alert_manager.get_alert_configs()


def update_alert_config(alert_id, **kwargs):
    """
    Update an alert configuration.
    
    Args:
        alert_id: ID of the alert to update
        **kwargs: Configuration parameters to update
    
    Returns:
        Boolean indicating success
    """
    return alert_manager.update_alert_config(alert_id, **kwargs)


def start_alert_manager():
    """
    Start the alert manager.
    """
    alert_manager.start()


def stop_alert_manager():
    """
    Stop the alert manager.
    """
    alert_manager.stop()