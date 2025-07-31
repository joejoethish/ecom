#!/usr/bin/env python
"""
Production Migration Monitor

This script monitors the production migration process in real-time,
providing alerts and automatic rollback capabilities if issues are detected.
"""

import os
import sys
import time
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.production')
django.setup()

from django.db import connections
from django.conf import settings
from core.performance_monitor import DatabaseMonitor


class ProductionMigrationMonitor:
    """Monitor production migration with real-time alerts and rollback capabilities"""
    
    def __init__(self):
        self.monitor = DatabaseMonitor()
        self.start_time = datetime.now()
        self.monitoring_active = True
        self.alert_history = []
        self.performance_baseline = self.load_performance_baseline()
        
        # Configuration
        self.config = {
            'monitoring_interval': 30,  # seconds
            'alert_thresholds': {
                'cpu_usage': 85,
                'memory_usage': 90,
                'disk_usage': 95,
                'connection_usage': 85,
                'query_response_time': 5.0,  # seconds
                'error_rate': 5,  # percentage
                'replication_lag': 300  # seconds
            },
            'rollback_triggers': {
                'consecutive_alerts': 3,
                'critical_error_rate': 10,
                'performance_degradation': 50  # percentage
            },
            'notification': {
                'email_enabled': True,
                'slack_enabled': True,
                'sms_enabled': False
            }
        }
    
    def load_performance_baseline(self):
        """Load performance baseline for comparison"""
        baseline_file = 'performance_baseline_production.json'
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return None
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        print(f"Starting production migration monitoring at {self.start_time}")
        print(f"Monitoring interval: {self.config['monitoring_interval']} seconds")
        print("Press Ctrl+C to stop monitoring\n")
        
        consecutive_alerts = 0
        
        try:
            while self.monitoring_active:
                # Collect metrics
                metrics = self.collect_metrics()
                
                # Analyze metrics
                alerts = self.analyze_metrics(metrics)
                
                # Handle alerts
                if alerts:
                    consecutive_alerts += 1
                    self.handle_alerts(alerts, consecutive_alerts)
                    
                    # Check for rollback triggers
                    if self.should_trigger_rollback(alerts, consecutive_alerts):
                        self.trigger_emergency_rollback()
                        break
                else:
                    consecutive_alerts = 0
                
                # Log status
                self.log_status(metrics, alerts)
                
                # Wait for next monitoring cycle
                time.sleep(self.config['monitoring_interval'])
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Monitoring error: {e}")
            self.send_alert(f"Migration monitoring error: {e}", severity='CRITICAL')
        
        finally:
            self.cleanup_monitoring()
    
    def collect_metrics(self):
        """Collect system and database metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self.collect_system_metrics(),
            'database': self.collect_database_metrics(),
            'application': self.collect_application_metrics()
        }
        
        return metrics
    
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            with open('/proc/loadavg', 'r') as f:
                load_avg = float(f.read().split()[0])
            
            # Memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
                mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
                memory_usage = ((mem_total - mem_available) / mem_total) * 100
            
            # Disk usage
            import shutil
            disk_usage = shutil.disk_usage('/')
            disk_usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
            
            return {
                'cpu_usage': load_avg * 100,  # Approximate CPU usage
                'memory_usage': memory_usage,
                'disk_usage': disk_usage_percent,
                'load_average': load_avg
            }
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return {}
    
    def collect_database_metrics(self):
        """Collect database-specific metrics"""
        try:
            metrics = {}
            
            # Test database connectivity
            start_time = time.time()
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
            connection_time = time.time() - start_time
            
            # Query performance test
            start_time = time.time()
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            # Connection pool status
            connection_count = len(connections['default'].queries)
            
            metrics.update({
                'connection_time': connection_time,
                'query_response_time': query_time,
                'connection_count': connection_count,
                'user_count': user_count
            })
            
            # MySQL-specific metrics (if using MySQL)
            if 'mysql' in settings.DATABASES['default']['ENGINE']:
                mysql_metrics = self.collect_mysql_metrics()
                metrics.update(mysql_metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting database metrics: {e}")
            return {'error': str(e)}
    
    def collect_mysql_metrics(self):
        """Collect MySQL-specific metrics"""
        try:
            with connections['default'].cursor() as cursor:
                # Get MySQL status variables
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                threads_connected = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW STATUS LIKE 'Threads_running'")
                threads_running = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
                slow_queries = int(cursor.fetchone()[1])
                
                cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_connections = int(cursor.fetchone()[1])
                
                connection_usage = (threads_connected / max_connections) * 100
                
                return {
                    'threads_connected': threads_connected,
                    'threads_running': threads_running,
                    'slow_queries': slow_queries,
                    'max_connections': max_connections,
                    'connection_usage': connection_usage
                }
                
        except Exception as e:
            print(f"Error collecting MySQL metrics: {e}")
            return {}
    
    def collect_application_metrics(self):
        """Collect application-level metrics"""
        try:
            # Test API endpoints
            api_metrics = self.test_api_endpoints()
            
            # Test cache
            cache_metrics = self.test_cache_performance()
            
            return {
                'api': api_metrics,
                'cache': cache_metrics
            }
            
        except Exception as e:
            print(f"Error collecting application metrics: {e}")
            return {}
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        endpoints = [
            '/api/v1/health/',
            '/api/v1/products/',
            '/api/v1/categories/'
        ]
        
        results = {}
        base_url = 'http://localhost:8000'
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                results[endpoint] = {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                }
                
            except Exception as e:
                results[endpoint] = {
                    'error': str(e),
                    'success': False
                }
        
        return results
    
    def test_cache_performance(self):
        """Test cache performance"""
        try:
            from django.core.cache import cache
            
            # Test cache write
            start_time = time.time()
            cache.set('monitor_test', 'test_value', 60)
            write_time = time.time() - start_time
            
            # Test cache read
            start_time = time.time()
            value = cache.get('monitor_test')
            read_time = time.time() - start_time
            
            return {
                'write_time': write_time,
                'read_time': read_time,
                'success': value == 'test_value'
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def analyze_metrics(self, metrics):
        """Analyze metrics and generate alerts"""
        alerts = []
        
        # System alerts
        system_metrics = metrics.get('system', {})
        if system_metrics.get('cpu_usage', 0) > self.config['alert_thresholds']['cpu_usage']:
            alerts.append({
                'type': 'SYSTEM',
                'severity': 'WARNING',
                'message': f"High CPU usage: {system_metrics['cpu_usage']:.1f}%",
                'metric': 'cpu_usage',
                'value': system_metrics['cpu_usage']
            })
        
        if system_metrics.get('memory_usage', 0) > self.config['alert_thresholds']['memory_usage']:
            alerts.append({
                'type': 'SYSTEM',
                'severity': 'WARNING',
                'message': f"High memory usage: {system_metrics['memory_usage']:.1f}%",
                'metric': 'memory_usage',
                'value': system_metrics['memory_usage']
            })
        
        if system_metrics.get('disk_usage', 0) > self.config['alert_thresholds']['disk_usage']:
            alerts.append({
                'type': 'SYSTEM',
                'severity': 'CRITICAL',
                'message': f"High disk usage: {system_metrics['disk_usage']:.1f}%",
                'metric': 'disk_usage',
                'value': system_metrics['disk_usage']
            })
        
        # Database alerts
        db_metrics = metrics.get('database', {})
        if db_metrics.get('query_response_time', 0) > self.config['alert_thresholds']['query_response_time']:
            alerts.append({
                'type': 'DATABASE',
                'severity': 'WARNING',
                'message': f"Slow query response: {db_metrics['query_response_time']:.2f}s",
                'metric': 'query_response_time',
                'value': db_metrics['query_response_time']
            })
        
        if db_metrics.get('connection_usage', 0) > self.config['alert_thresholds']['connection_usage']:
            alerts.append({
                'type': 'DATABASE',
                'severity': 'WARNING',
                'message': f"High connection usage: {db_metrics['connection_usage']:.1f}%",
                'metric': 'connection_usage',
                'value': db_metrics['connection_usage']
            })
        
        # Application alerts
        app_metrics = metrics.get('application', {})
        api_metrics = app_metrics.get('api', {})
        
        failed_endpoints = [ep for ep, data in api_metrics.items() if not data.get('success', True)]
        if failed_endpoints:
            alerts.append({
                'type': 'APPLICATION',
                'severity': 'CRITICAL',
                'message': f"API endpoints failing: {failed_endpoints}",
                'metric': 'api_health',
                'value': len(failed_endpoints)
            })
        
        # Performance degradation alerts
        if self.performance_baseline:
            performance_alerts = self.check_performance_degradation(metrics)
            alerts.extend(performance_alerts)
        
        return alerts
    
    def check_performance_degradation(self, current_metrics):
        """Check for performance degradation compared to baseline"""
        alerts = []
        
        try:
            baseline_query_time = self.performance_baseline.get('avg_query_time', 0)
            current_query_time = current_metrics.get('database', {}).get('query_response_time', 0)
            
            if baseline_query_time > 0 and current_query_time > 0:
                degradation = ((current_query_time - baseline_query_time) / baseline_query_time) * 100
                
                if degradation > self.config['rollback_triggers']['performance_degradation']:
                    alerts.append({
                        'type': 'PERFORMANCE',
                        'severity': 'CRITICAL',
                        'message': f"Performance degradation: {degradation:.1f}%",
                        'metric': 'performance_degradation',
                        'value': degradation
                    })
        
        except Exception as e:
            print(f"Error checking performance degradation: {e}")
        
        return alerts
    
    def handle_alerts(self, alerts, consecutive_count):
        """Handle generated alerts"""
        for alert in alerts:
            # Add to alert history
            alert['timestamp'] = datetime.now().isoformat()
            alert['consecutive_count'] = consecutive_count
            self.alert_history.append(alert)
            
            # Send notifications
            self.send_alert(alert['message'], alert['severity'])
            
            # Log alert
            print(f"[{alert['severity']}] {alert['message']}")
    
    def should_trigger_rollback(self, alerts, consecutive_count):
        """Determine if automatic rollback should be triggered"""
        # Check consecutive alerts
        if consecutive_count >= self.config['rollback_triggers']['consecutive_alerts']:
            return True
        
        # Check for critical alerts
        critical_alerts = [a for a in alerts if a['severity'] == 'CRITICAL']
        if len(critical_alerts) > 0:
            return True
        
        # Check error rate
        api_alerts = [a for a in alerts if a['type'] == 'APPLICATION']
        if len(api_alerts) > 0:
            return True
        
        return False
    
    def trigger_emergency_rollback(self):
        """Trigger emergency rollback"""
        print("\n" + "="*50)
        print("EMERGENCY ROLLBACK TRIGGERED")
        print("="*50)
        
        try:
            # Send critical alert
            self.send_alert("Emergency rollback triggered during migration", 'CRITICAL')
            
            # Execute rollback command
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'final_migration_cutover',
                '--environment=production',
                '--rollback'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Emergency rollback completed successfully")
                self.send_alert("Emergency rollback completed successfully", 'INFO')
            else:
                print(f"Emergency rollback failed: {result.stderr}")
                self.send_alert(f"Emergency rollback failed: {result.stderr}", 'CRITICAL')
        
        except Exception as e:
            print(f"Emergency rollback error: {e}")
            self.send_alert(f"Emergency rollback error: {e}", 'CRITICAL')
        
        self.monitoring_active = False
    
    def send_alert(self, message, severity='INFO'):
        """Send alert notifications"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] [{severity}] Migration Monitor: {message}"
        
        # Email notification
        if self.config['notification']['email_enabled']:
            self.send_email_alert(full_message, severity)
        
        # Slack notification
        if self.config['notification']['slack_enabled']:
            self.send_slack_alert(full_message, severity)
    
    def send_email_alert(self, message, severity):
        """Send email alert"""
        try:
            # Email configuration (should be in settings)
            smtp_server = getattr(settings, 'EMAIL_HOST', 'localhost')
            smtp_port = getattr(settings, 'EMAIL_PORT', 587)
            smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
            smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            
            # Recipients
            recipients = ['admin@ecommerce.com', 'devops@ecommerce.com']
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{severity}] Production Migration Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, message, severity):
        """Send Slack alert"""
        try:
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
            if not webhook_url:
                return
            
            # Color coding based on severity
            color_map = {
                'INFO': 'good',
                'WARNING': 'warning',
                'CRITICAL': 'danger'
            }
            
            payload = {
                'text': 'Production Migration Alert',
                'attachments': [{
                    'color': color_map.get(severity, 'warning'),
                    'text': message,
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def log_status(self, metrics, alerts):
        """Log current status"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # System status
        system = metrics.get('system', {})
        db = metrics.get('database', {})
        
        status_line = (
            f"[{timestamp}] "
            f"CPU: {system.get('cpu_usage', 0):.1f}% | "
            f"MEM: {system.get('memory_usage', 0):.1f}% | "
            f"DISK: {system.get('disk_usage', 0):.1f}% | "
            f"DB: {db.get('query_response_time', 0):.3f}s | "
            f"Alerts: {len(alerts)}"
        )
        
        print(status_line)
        
        # Save to log file
        with open('migration_monitor.log', 'a') as f:
            f.write(status_line + '\n')
            if alerts:
                for alert in alerts:
                    f.write(f"  ALERT: {alert['message']}\n")
    
    def cleanup_monitoring(self):
        """Cleanup monitoring resources"""
        print("\nCleaning up monitoring resources...")
        
        # Save final report
        report = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_alerts': len(self.alert_history),
            'alert_history': self.alert_history
        }
        
        with open('migration_monitor_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("Monitoring cleanup completed")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Production Migration Monitor")
        print("Usage: python production_migration_monitor.py")
        print("\nThis script monitors the production migration process and provides")
        print("real-time alerts and automatic rollback capabilities.")
        return
    
    monitor = ProductionMigrationMonitor()
    monitor.start_monitoring()


if __name__ == '__main__':
    main()