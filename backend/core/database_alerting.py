"""
Database Alerting System

This module provides comprehensive alerting capabilities for database monitoring:
- Email alerts with customizable templates
- Webhook notifications for external systems
- Slack integration for team notifications
- Alert escalation and acknowledgment
- Alert suppression and grouping
"""

import logging
import json
import requests
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class AlertChannel:
    """Alert channel configuration"""
    name: str
    type: str  # email, webhook, slack
    enabled: bool = True
    config: Dict[str, Any] = None
    severity_filter: List[str] = None  # ['warning', 'critical']
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.severity_filter is None:
            self.severity_filter = ['warning', 'critical']


class DatabaseAlerting:
    """
    Comprehensive database alerting system with multiple notification channels
    """
    
    def __init__(self):
        self.channels = self._load_alert_channels()
        self.alert_templates = self._load_alert_templates()
        self.suppressed_alerts = {}  # For alert suppression
        self.acknowledged_alerts = {}  # For alert acknowledgment
        
    def _load_alert_channels(self) -> List[AlertChannel]:
        """Load alert channels from settings"""
        channels = []
        
        # Email channel
        email_recipients = getattr(settings, 'DB_ALERT_EMAIL_RECIPIENTS', [])
        if email_recipients:
            channels.append(AlertChannel(
                name='email',
                type='email',
                enabled=getattr(settings, 'DB_ALERT_EMAIL_ENABLED', True),
                config={
                    'recipients': email_recipients,
                    'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    'smtp_host': getattr(settings, 'EMAIL_HOST', 'localhost'),
                    'smtp_port': getattr(settings, 'EMAIL_PORT', 587),
                    'smtp_user': getattr(settings, 'EMAIL_HOST_USER', ''),
                    'smtp_password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
                    'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
                }
            ))
        
        # Webhook channel
        webhook_url = getattr(settings, 'DB_ALERT_WEBHOOK_URL', '')
        if webhook_url:
            channels.append(AlertChannel(
                name='webhook',
                type='webhook',
                enabled=getattr(settings, 'DB_ALERT_WEBHOOK_ENABLED', True),
                config={
                    'url': webhook_url,
                    'headers': getattr(settings, 'DB_ALERT_WEBHOOK_HEADERS', {}),
                    'timeout': getattr(settings, 'DB_ALERT_WEBHOOK_TIMEOUT', 30),
                }
            ))
        
        # Slack channel
        slack_webhook = getattr(settings, 'DB_ALERT_SLACK_WEBHOOK', '')
        if slack_webhook:
            channels.append(AlertChannel(
                name='slack',
                type='slack',
                enabled=getattr(settings, 'DB_ALERT_SLACK_ENABLED', True),
                config={
                    'webhook_url': slack_webhook,
                    'channel': getattr(settings, 'DB_ALERT_SLACK_CHANNEL', '#alerts'),
                    'username': getattr(settings, 'DB_ALERT_SLACK_USERNAME', 'Database Monitor'),
                    'icon_emoji': getattr(settings, 'DB_ALERT_SLACK_ICON', ':warning:'),
                }
            ))
        
        return channels
    
    def _load_alert_templates(self) -> Dict[str, str]:
        """Load alert message templates"""
        return {
            'email_subject': 'Database Alert: {database} - {severity}',
            'email_body': '''
Database Alert Details:

Database: {database}
Metric: {metric_name}
Current Value: {current_value}
Threshold: {threshold_value}
Severity: {severity}
Time: {timestamp}
Status: {status}

Message: {message}

{recommendations}

Alert ID: {alert_id}
            ''',
            'slack_message': '''
:warning: *Database Alert*

*Database:* {database}
*Metric:* {metric_name}
*Current Value:* {current_value}
*Threshold:* {threshold_value}
*Severity:* {severity}
*Time:* {timestamp}

*Message:* {message}

{recommendations}
            ''',
            'webhook_payload': {
                'alert_id': '{alert_id}',
                'database': '{database}',
                'metric_name': '{metric_name}',
                'current_value': '{current_value}',
                'threshold_value': '{threshold_value}',
                'severity': '{severity}',
                'message': '{message}',
                'timestamp': '{timestamp}',
                'status': 'active'
            }
        }
    
    def send_alert(self, alert_data: Dict[str, Any]):
        """Send alert through all configured channels"""
        # Check if alert should be suppressed
        if self._is_alert_suppressed(alert_data):
            logger.debug(f"Alert suppressed: {alert_data['alert_id']}")
            return
        
        # Check if alert is acknowledged
        if self._is_alert_acknowledged(alert_data):
            logger.debug(f"Alert acknowledged: {alert_data['alert_id']}")
            return
        
        # Send through each enabled channel
        for channel in self.channels:
            if not channel.enabled:
                continue
            
            # Check severity filter
            if alert_data['severity'] not in channel.severity_filter:
                continue
            
            try:
                if channel.type == 'email':
                    self._send_email_alert(alert_data, channel)
                elif channel.type == 'webhook':
                    self._send_webhook_alert(alert_data, channel)
                elif channel.type == 'slack':
                    self._send_slack_alert(alert_data, channel)
                    
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.name}: {e}")
    
    def _send_email_alert(self, alert_data: Dict[str, Any], channel: AlertChannel):
        """Send email alert"""
        try:
            # Generate recommendations
            recommendations = self._generate_recommendations(alert_data)
            
            # Prepare template data
            template_data = {
                **alert_data,
                'recommendations': recommendations,
                'status': 'ACTIVE'
            }
            
            # Format subject and body
            subject = self.alert_templates['email_subject'].format(**template_data)
            body = self.alert_templates['email_body'].format(**template_data)
            
            # Send email
            send_mail(
                subject=subject,
                message=body,
                from_email=channel.config['from_email'],
                recipient_list=channel.config['recipients'],
                fail_silently=False
            )
            
            logger.info(f"Email alert sent for {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any], channel: AlertChannel):
        """Send webhook alert"""
        try:
            # Prepare payload
            payload = {}
            for key, template in self.alert_templates['webhook_payload'].items():
                if isinstance(template, str):
                    payload[key] = template.format(**alert_data)
                else:
                    payload[key] = template
            
            # Add recommendations
            payload['recommendations'] = self._generate_recommendations(alert_data)
            
            # Send webhook
            response = requests.post(
                channel.config['url'],
                json=payload,
                headers=channel.config.get('headers', {}),
                timeout=channel.config.get('timeout', 30)
            )
            
            response.raise_for_status()
            logger.info(f"Webhook alert sent for {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            raise
    
    def _send_slack_alert(self, alert_data: Dict[str, Any], channel: AlertChannel):
        """Send Slack alert"""
        try:
            # Generate recommendations
            recommendations = self._generate_recommendations(alert_data)
            
            # Prepare template data
            template_data = {
                **alert_data,
                'recommendations': recommendations
            }
            
            # Format message
            message = self.alert_templates['slack_message'].format(**template_data)
            
            # Determine color based on severity
            color = {
                'warning': 'warning',
                'critical': 'danger'
            }.get(alert_data['severity'], 'warning')
            
            # Prepare Slack payload
            payload = {
                'channel': channel.config['channel'],
                'username': channel.config['username'],
                'icon_emoji': channel.config['icon_emoji'],
                'attachments': [
                    {
                        'color': color,
                        'text': message,
                        'ts': int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                channel.config['webhook_url'],
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"Slack alert sent for {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            raise
    
    def _generate_recommendations(self, alert_data: Dict[str, Any]) -> str:
        """Generate recommendations based on alert type"""
        metric_name = alert_data.get('metric_name', '')
        severity = alert_data.get('severity', '')
        
        recommendations = {
            'connection_usage': [
                "• Check for connection leaks in application code",
                "• Consider increasing max_connections if needed",
                "• Review connection pooling configuration",
                "• Kill idle connections if necessary"
            ],
            'query_response_time': [
                "• Review slow query log for optimization opportunities",
                "• Check for missing indexes on frequently queried columns",
                "• Consider query optimization or rewriting",
                "• Monitor system resources (CPU, memory, disk I/O)"
            ],
            'slow_queries': [
                "• Analyze slow query patterns and add appropriate indexes",
                "• Review query execution plans with EXPLAIN",
                "• Consider query caching for frequently executed queries",
                "• Optimize JOIN operations and WHERE clauses"
            ],
            'replication_lag': [
                "• Check network connectivity between master and slave",
                "• Review replication configuration and settings",
                "• Monitor disk I/O on slave server",
                "• Consider parallel replication if supported"
            ],
            'cpu_usage': [
                "• Identify resource-intensive queries",
                "• Check for inefficient indexes or table scans",
                "• Consider scaling up server resources",
                "• Review concurrent connection limits"
            ],
            'memory_usage': [
                "• Review buffer pool and cache settings",
                "• Check for memory leaks in connections",
                "• Consider increasing server memory",
                "• Optimize query cache configuration"
            ],
            'disk_usage': [
                "• Clean up old log files and temporary data",
                "• Archive or purge old data",
                "• Consider adding more disk space",
                "• Review backup retention policies"
            ],
            'health_score': [
                "• Review all database metrics for issues",
                "• Check system resources and performance",
                "• Investigate recent changes or deployments",
                "• Consider maintenance tasks like index optimization"
            ]
        }
        
        metric_recommendations = recommendations.get(metric_name, [
            "• Review database metrics and logs",
            "• Check system resources and performance",
            "• Consider contacting database administrator"
        ])
        
        if severity == 'critical':
            metric_recommendations.insert(0, "• IMMEDIATE ACTION REQUIRED")
        
        return "\n".join(metric_recommendations)
    
    def _is_alert_suppressed(self, alert_data: Dict[str, Any]) -> bool:
        """Check if alert should be suppressed"""
        alert_key = f"{alert_data['database']}_{alert_data['metric_name']}"
        
        if alert_key in self.suppressed_alerts:
            suppression_end = self.suppressed_alerts[alert_key]
            if datetime.now() < suppression_end:
                return True
            else:
                # Suppression expired
                del self.suppressed_alerts[alert_key]
        
        return False
    
    def _is_alert_acknowledged(self, alert_data: Dict[str, Any]) -> bool:
        """Check if alert is acknowledged"""
        alert_id = alert_data.get('alert_id', '')
        return alert_id in self.acknowledged_alerts
    
    def suppress_alert(self, database: str, metric_name: str, duration_minutes: int = 60):
        """Suppress alerts for a specific metric"""
        alert_key = f"{database}_{metric_name}"
        suppression_end = datetime.now() + timedelta(minutes=duration_minutes)
        self.suppressed_alerts[alert_key] = suppression_end
        
        logger.info(f"Alert suppressed for {alert_key} until {suppression_end}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = 'system'):
        """Acknowledge an alert"""
        self.acknowledged_alerts[alert_id] = {
            'acknowledged_by': acknowledged_by,
            'acknowledged_at': datetime.now()
        }
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
    
    def send_resolution_alert(self, alert_data: Dict[str, Any]):
        """Send alert resolution notification"""
        # Update alert data for resolution
        resolution_data = {
            **alert_data,
            'status': 'RESOLVED',
            'message': f"Alert resolved: {alert_data['message']}",
            'resolved_at': datetime.now().isoformat()
        }
        
        # Send through channels that support resolution notifications
        for channel in self.channels:
            if not channel.enabled:
                continue
            
            try:
                if channel.type == 'webhook':
                    self._send_webhook_resolution(resolution_data, channel)
                elif channel.type == 'slack':
                    self._send_slack_resolution(resolution_data, channel)
                # Email resolutions are typically not sent to avoid spam
                    
            except Exception as e:
                logger.error(f"Failed to send resolution via {channel.name}: {e}")
    
    def _send_webhook_resolution(self, alert_data: Dict[str, Any], channel: AlertChannel):
        """Send webhook resolution notification"""
        try:
            payload = {
                'alert_id': alert_data['alert_id'],
                'database': alert_data['database'],
                'metric_name': alert_data['metric_name'],
                'status': 'resolved',
                'resolved_at': alert_data['resolved_at'],
                'message': alert_data['message']
            }
            
            response = requests.post(
                channel.config['url'],
                json=payload,
                headers=channel.config.get('headers', {}),
                timeout=channel.config.get('timeout', 30)
            )
            
            response.raise_for_status()
            logger.info(f"Webhook resolution sent for {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook resolution: {e}")
    
    def _send_slack_resolution(self, alert_data: Dict[str, Any], channel: AlertChannel):
        """Send Slack resolution notification"""
        try:
            message = f":white_check_mark: *Alert Resolved*\n\n" \
                     f"*Database:* {alert_data['database']}\n" \
                     f"*Metric:* {alert_data['metric_name']}\n" \
                     f"*Resolved:* {alert_data['resolved_at']}\n\n" \
                     f"*Message:* {alert_data['message']}"
            
            payload = {
                'channel': channel.config['channel'],
                'username': channel.config['username'],
                'icon_emoji': ':white_check_mark:',
                'attachments': [
                    {
                        'color': 'good',
                        'text': message,
                        'ts': int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                channel.config['webhook_url'],
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"Slack resolution sent for {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack resolution: {e}")
    
    def test_channels(self) -> Dict[str, bool]:
        """Test all configured alert channels"""
        results = {}
        
        test_alert = {
            'alert_id': 'test_alert_' + str(int(datetime.now().timestamp())),
            'database': 'test_db',
            'metric_name': 'test_metric',
            'current_value': 95.0,
            'threshold_value': 80.0,
            'severity': 'warning',
            'message': 'This is a test alert to verify channel configuration',
            'timestamp': datetime.now().isoformat()
        }
        
        for channel in self.channels:
            if not channel.enabled:
                results[channel.name] = False
                continue
            
            try:
                if channel.type == 'email':
                    self._send_email_alert(test_alert, channel)
                elif channel.type == 'webhook':
                    self._send_webhook_alert(test_alert, channel)
                elif channel.type == 'slack':
                    self._send_slack_alert(test_alert, channel)
                
                results[channel.name] = True
                
            except Exception as e:
                logger.error(f"Channel test failed for {channel.name}: {e}")
                results[channel.name] = False
        
        return results
    
    def get_suppressed_alerts(self) -> Dict[str, datetime]:
        """Get currently suppressed alerts"""
        # Clean up expired suppressions
        now = datetime.now()
        expired_keys = [key for key, end_time in self.suppressed_alerts.items() if now >= end_time]
        for key in expired_keys:
            del self.suppressed_alerts[key]
        
        return self.suppressed_alerts.copy()
    
    def get_acknowledged_alerts(self) -> Dict[str, Dict[str, Any]]:
        """Get acknowledged alerts"""
        return self.acknowledged_alerts.copy()
    
    def clear_acknowledgments(self, older_than_hours: int = 24):
        """Clear old acknowledgments"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        expired_alerts = []
        for alert_id, ack_data in self.acknowledged_alerts.items():
            if ack_data['acknowledged_at'] < cutoff_time:
                expired_alerts.append(alert_id)
        
        for alert_id in expired_alerts:
            del self.acknowledged_alerts[alert_id]
        
        logger.info(f"Cleared {len(expired_alerts)} old acknowledgments")


# Global alerting instance
_database_alerting = None


def get_database_alerting() -> DatabaseAlerting:
    """Get the global database alerting instance"""
    global _database_alerting
    if _database_alerting is None:
        _database_alerting = DatabaseAlerting()
    return _database_alerting


def initialize_database_alerting() -> DatabaseAlerting:
    """Initialize database alerting system"""
    global _database_alerting
    _database_alerting = DatabaseAlerting()
    return _database_alerting