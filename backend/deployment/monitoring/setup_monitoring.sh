#!/bin/bash

# Production Monitoring and Alerting Setup Script
# This script sets up comprehensive monitoring for MySQL database

set -e

# Configuration variables
ENVIRONMENT=${ENVIRONMENT:-production}
MONITORING_USER=${MONITORING_USER:-monitor}
MONITORING_PASSWORD=${MONITORING_PASSWORD:-monitor_password}
ALERT_EMAIL=${ALERT_EMAIL:-admin@ecommerce.com}
SLACK_WEBHOOK=${SLACK_WEBHOOK}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Install monitoring dependencies
install_dependencies() {
    log_info "Installing monitoring dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        cron \
        mailutils \
        curl \
        jq \
        bc
    
    # Install Python packages
    pip3 install \
        mysql-connector-python \
        psutil \
        requests \
        pyyaml \
        prometheus-client
    
    log_info "Dependencies installed successfully"
}

# Create monitoring user in MySQL
create_monitoring_user() {
    log_info "Creating monitoring user in MySQL..."
    
    mysql -u root << EOF
CREATE USER IF NOT EXISTS '${MONITORING_USER}'@'localhost' IDENTIFIED BY '${MONITORING_PASSWORD}';
GRANT REPLICATION CLIENT ON *.* TO '${MONITORING_USER}'@'localhost';
GRANT PROCESS ON *.* TO '${MONITORING_USER}'@'localhost';
GRANT SELECT ON performance_schema.* TO '${MONITORING_USER}'@'localhost';
GRANT SELECT ON information_schema.* TO '${MONITORING_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

    log_info "Monitoring user created successfully"
}

# Setup monitoring scripts
setup_monitoring_scripts() {
    log_info "Setting up monitoring scripts..."
    
    # Create monitoring directory
    mkdir -p /opt/mysql-monitoring
    cd /opt/mysql-monitoring
    
    # Create main monitoring script
    cat > mysql_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
MySQL Production Monitoring Script
Monitors database health, performance, and sends alerts
"""

import mysql.connector
import psutil
import json
import smtplib
import requests
import time
import logging
import os
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mysql-monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MySQLMonitor:
    def __init__(self, config_file='/opt/mysql-monitoring/config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.db_config = self.config['database']
        self.thresholds = self.config['thresholds']
        self.alerts = self.config['alerts']
        
    def get_db_connection(self):
        """Get database connection."""
        try:
            return mysql.connector.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=True
            )
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None
    
    def check_database_connectivity(self):
        """Check if database is accessible."""
        conn = self.get_db_connection()
        if conn:
            conn.close()
            return True, "Database connection successful"
        return False, "Database connection failed"
    
    def get_database_metrics(self):
        """Get database performance metrics."""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        metrics = {}
        
        try:
            # Get global status
            cursor.execute("SHOW GLOBAL STATUS")
            status = {row['Variable_name']: row['Value'] for row in cursor.fetchall()}
            
            # Get global variables
            cursor.execute("SHOW GLOBAL VARIABLES")
            variables = {row['Variable_name']: row['Value'] for row in cursor.fetchall()}
            
            # Calculate key metrics
            metrics['connections'] = {
                'current': int(status.get('Threads_connected', 0)),
                'max': int(variables.get('max_connections', 0)),
                'usage_percent': (int(status.get('Threads_connected', 0)) / int(variables.get('max_connections', 1))) * 100
            }
            
            metrics['queries'] = {
                'total': int(status.get('Queries', 0)),
                'slow': int(status.get('Slow_queries', 0)),
                'qps': 0  # Will be calculated with time difference
            }
            
            metrics['innodb'] = {
                'buffer_pool_size': int(variables.get('innodb_buffer_pool_size', 0)),
                'buffer_pool_pages_total': int(status.get('Innodb_buffer_pool_pages_total', 0)),
                'buffer_pool_pages_free': int(status.get('Innodb_buffer_pool_pages_free', 0)),
                'buffer_pool_usage_percent': ((int(status.get('Innodb_buffer_pool_pages_total', 0)) - 
                                             int(status.get('Innodb_buffer_pool_pages_free', 0))) / 
                                            max(int(status.get('Innodb_buffer_pool_pages_total', 1)), 1)) * 100
            }
            
            # Get replication status if enabled
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            if slave_status:
                metrics['replication'] = {
                    'io_running': slave_status.get('Slave_IO_Running') == 'Yes',
                    'sql_running': slave_status.get('Slave_SQL_Running') == 'Yes',
                    'seconds_behind_master': slave_status.get('Seconds_Behind_Master'),
                    'last_error': slave_status.get('Last_Error', '')
                }
            
            # Get table sizes
            cursor.execute("""
                SELECT 
                    table_schema,
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                GROUP BY table_schema
            """)
            metrics['database_sizes'] = {row['table_schema']: row['size_mb'] for row in cursor.fetchall()}
            
        except Exception as e:
            logger.error(f"Error getting database metrics: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
        
        return metrics
    
    def get_system_metrics(self):
        """Get system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except PermissionError:
                    continue
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': disk_usage,
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return None
    
    def check_thresholds(self, db_metrics, sys_metrics):
        """Check if any metrics exceed thresholds."""
        alerts = []
        
        if not db_metrics or not sys_metrics:
            alerts.append({
                'severity': 'critical',
                'message': 'Failed to collect metrics',
                'timestamp': datetime.now().isoformat()
            })
            return alerts
        
        # Check CPU threshold
        if sys_metrics['cpu_percent'] > self.thresholds['cpu']:
            alerts.append({
                'severity': 'warning',
                'message': f"High CPU usage: {sys_metrics['cpu_percent']:.1f}% (threshold: {self.thresholds['cpu']}%)",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check memory threshold
        if sys_metrics['memory']['percent'] > self.thresholds['memory']:
            alerts.append({
                'severity': 'warning',
                'message': f"High memory usage: {sys_metrics['memory']['percent']:.1f}% (threshold: {self.thresholds['memory']}%)",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check disk usage
        for mount, usage in sys_metrics['disk'].items():
            if usage['percent'] > self.thresholds['disk']:
                alerts.append({
                    'severity': 'warning',
                    'message': f"High disk usage on {mount}: {usage['percent']:.1f}% (threshold: {self.thresholds['disk']}%)",
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check database connections
        if db_metrics['connections']['usage_percent'] > self.thresholds['connections']:
            alerts.append({
                'severity': 'warning',
                'message': f"High connection usage: {db_metrics['connections']['usage_percent']:.1f}% ({db_metrics['connections']['current']}/{db_metrics['connections']['max']})",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check replication lag
        if 'replication' in db_metrics:
            repl = db_metrics['replication']
            if not repl['io_running'] or not repl['sql_running']:
                alerts.append({
                    'severity': 'critical',
                    'message': f"Replication stopped - IO: {repl['io_running']}, SQL: {repl['sql_running']}",
                    'timestamp': datetime.now().isoformat()
                })
            elif repl['seconds_behind_master'] and repl['seconds_behind_master'] > self.thresholds['replication_lag']:
                alerts.append({
                    'severity': 'warning',
                    'message': f"High replication lag: {repl['seconds_behind_master']}s (threshold: {self.thresholds['replication_lag']}s)",
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def send_email_alert(self, alerts):
        """Send email alerts."""
        if not self.alerts.get('email_enabled', False):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.alerts['email_from']
            msg['To'] = self.alerts['email_to']
            msg['Subject'] = f"MySQL Alert - {len(alerts)} issues detected"
            
            body = "MySQL Monitoring Alert\n\n"
            body += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for alert in alerts:
                body += f"[{alert['severity'].upper()}] {alert['message']}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.alerts['smtp_host'], self.alerts['smtp_port'])
            if self.alerts.get('smtp_tls', False):
                server.starttls()
            if self.alerts.get('smtp_user'):
                server.login(self.alerts['smtp_user'], self.alerts['smtp_password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {len(alerts)} issues")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
    
    def send_slack_alert(self, alerts):
        """Send Slack alerts."""
        if not self.alerts.get('slack_webhook'):
            return
        
        try:
            color = 'danger' if any(a['severity'] == 'critical' for a in alerts) else 'warning'
            
            payload = {
                'text': f'MySQL Alert - {len(alerts)} issues detected',
                'attachments': [{
                    'color': color,
                    'fields': [
                        {
                            'title': f"[{alert['severity'].upper()}]",
                            'value': alert['message'],
                            'short': False
                        } for alert in alerts
                    ],
                    'footer': 'MySQL Monitoring',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(self.alerts['slack_webhook'], json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent for {len(alerts)} issues")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {str(e)}")
    
    def save_metrics(self, db_metrics, sys_metrics):
        """Save metrics to file for historical analysis."""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'database': db_metrics,
                'system': sys_metrics
            }
            
            metrics_file = f"/var/log/mysql-metrics-{datetime.now().strftime('%Y%m%d')}.json"
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(metrics_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {str(e)}")
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        logger.info("Starting monitoring cycle")
        
        # Check database connectivity
        db_connected, db_message = self.check_database_connectivity()
        if not db_connected:
            alerts = [{
                'severity': 'critical',
                'message': db_message,
                'timestamp': datetime.now().isoformat()
            }]
            self.send_email_alert(alerts)
            self.send_slack_alert(alerts)
            return
        
        # Get metrics
        db_metrics = self.get_database_metrics()
        sys_metrics = self.get_system_metrics()
        
        # Save metrics
        self.save_metrics(db_metrics, sys_metrics)
        
        # Check thresholds and send alerts
        alerts = self.check_thresholds(db_metrics, sys_metrics)
        
        if alerts:
            logger.warning(f"Found {len(alerts)} alerts")
            self.send_email_alert(alerts)
            self.send_slack_alert(alerts)
        else:
            logger.info("All metrics within normal ranges")

def main():
    """Main function."""
    monitor = MySQLMonitor()
    monitor.run_monitoring_cycle()

if __name__ == '__main__':
    main()
EOF

    chmod +x mysql_monitor.py
    
    log_info "Monitoring scripts created successfully"
}

# Create monitoring configuration
create_monitoring_config() {
    log_info "Creating monitoring configuration..."
    
    cat > /opt/mysql-monitoring/config.json << EOF
{
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "${MONITORING_USER}",
        "password": "${MONITORING_PASSWORD}"
    },
    "thresholds": {
        "cpu": 80,
        "memory": 85,
        "disk": 90,
        "connections": 80,
        "slow_queries": 5,
        "replication_lag": 300
    },
    "alerts": {
        "email_enabled": true,
        "email_from": "mysql-monitor@ecommerce.com",
        "email_to": "${ALERT_EMAIL}",
        "smtp_host": "localhost",
        "smtp_port": 587,
        "smtp_tls": true,
        "smtp_user": "",
        "smtp_password": "",
        "slack_webhook": "${SLACK_WEBHOOK}"
    }
}
EOF

    log_info "Monitoring configuration created"
}

# Setup log rotation for monitoring logs
setup_log_rotation() {
    log_info "Setting up log rotation for monitoring..."
    
    cat > /etc/logrotate.d/mysql-monitoring << EOF
/var/log/mysql-monitoring.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}

/var/log/mysql-metrics-*.json {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

    log_info "Log rotation configured"
}

# Setup cron jobs for monitoring
setup_cron_jobs() {
    log_info "Setting up cron jobs for monitoring..."
    
    # Add monitoring cron job
    cat > /etc/cron.d/mysql-monitoring << EOF
# MySQL Monitoring Cron Jobs
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Run monitoring every 5 minutes
*/5 * * * * root /opt/mysql-monitoring/mysql_monitor.py >> /var/log/mysql-monitoring-cron.log 2>&1

# Daily health report
0 8 * * * root /opt/mysql-monitoring/daily_report.py >> /var/log/mysql-monitoring-cron.log 2>&1
EOF

    log_info "Cron jobs configured"
}

# Create daily report script
create_daily_report() {
    log_info "Creating daily report script..."
    
    cat > /opt/mysql-monitoring/daily_report.py << 'EOF'
#!/usr/bin/env python3
"""
MySQL Daily Health Report Generator
"""

import json
import glob
import statistics
from datetime import datetime, timedelta
from collections import defaultdict

def generate_daily_report():
    """Generate daily health report."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    metrics_file = f"/var/log/mysql-metrics-{yesterday}.json"
    
    try:
        with open(metrics_file, 'r') as f:
            metrics_data = [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"No metrics data found for {yesterday}")
        return
    
    if not metrics_data:
        print(f"No metrics data available for {yesterday}")
        return
    
    # Analyze metrics
    cpu_values = [m['system']['cpu_percent'] for m in metrics_data if 'system' in m]
    memory_values = [m['system']['memory']['percent'] for m in metrics_data if 'system' in m]
    connection_values = [m['database']['connections']['usage_percent'] for m in metrics_data if 'database' in m and 'connections' in m['database']]
    
    report = f"""
MySQL Daily Health Report - {yesterday}
{'='*50}

System Metrics:
- CPU Usage: Avg {statistics.mean(cpu_values):.1f}%, Max {max(cpu_values):.1f}%
- Memory Usage: Avg {statistics.mean(memory_values):.1f}%, Max {max(memory_values):.1f}%
- Connection Usage: Avg {statistics.mean(connection_values):.1f}%, Max {max(connection_values):.1f}%

Total Monitoring Cycles: {len(metrics_data)}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    print(report)
    
    # Save report to file
    report_file = f"/var/log/mysql-daily-report-{yesterday}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    generate_daily_report()
EOF

    chmod +x /opt/mysql-monitoring/daily_report.py
    
    log_info "Daily report script created"
}

# Setup Prometheus metrics (optional)
setup_prometheus_metrics() {
    log_info "Setting up Prometheus metrics endpoint..."
    
    cat > /opt/mysql-monitoring/prometheus_exporter.py << 'EOF'
#!/usr/bin/env python3
"""
MySQL Prometheus Metrics Exporter
"""

import time
import json
import mysql.connector
from prometheus_client import start_http_server, Gauge, Counter, Info
from mysql_monitor import MySQLMonitor

# Define Prometheus metrics
mysql_up = Gauge('mysql_up', 'MySQL server availability')
mysql_connections = Gauge('mysql_connections_current', 'Current MySQL connections')
mysql_connections_max = Gauge('mysql_connections_max', 'Maximum MySQL connections')
mysql_slow_queries = Counter('mysql_slow_queries_total', 'Total slow queries')
mysql_buffer_pool_usage = Gauge('mysql_innodb_buffer_pool_usage_percent', 'InnoDB buffer pool usage percentage')
mysql_replication_lag = Gauge('mysql_replication_lag_seconds', 'MySQL replication lag in seconds')

system_cpu = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
system_memory = Gauge('system_memory_usage_percent', 'System memory usage percentage')
system_disk_usage = Gauge('system_disk_usage_percent', 'System disk usage percentage', ['mountpoint'])

def collect_and_export_metrics():
    """Collect metrics and export to Prometheus."""
    monitor = MySQLMonitor()
    
    # Check database connectivity
    db_connected, _ = monitor.check_database_connectivity()
    mysql_up.set(1 if db_connected else 0)
    
    if not db_connected:
        return
    
    # Get metrics
    db_metrics = monitor.get_database_metrics()
    sys_metrics = monitor.get_system_metrics()
    
    if db_metrics:
        # Database metrics
        mysql_connections.set(db_metrics['connections']['current'])
        mysql_connections_max.set(db_metrics['connections']['max'])
        mysql_slow_queries._value._value = db_metrics['queries']['slow']
        mysql_buffer_pool_usage.set(db_metrics['innodb']['buffer_pool_usage_percent'])
        
        # Replication metrics
        if 'replication' in db_metrics:
            lag = db_metrics['replication']['seconds_behind_master']
            mysql_replication_lag.set(lag if lag is not None else -1)
    
    if sys_metrics:
        # System metrics
        system_cpu.set(sys_metrics['cpu_percent'])
        system_memory.set(sys_metrics['memory']['percent'])
        
        for mount, usage in sys_metrics['disk'].items():
            system_disk_usage.labels(mountpoint=mount).set(usage['percent'])

def main():
    """Main function."""
    # Start Prometheus metrics server
    start_http_server(9104)
    print("Prometheus metrics server started on port 9104")
    
    while True:
        try:
            collect_and_export_metrics()
            time.sleep(30)  # Collect metrics every 30 seconds
        except Exception as e:
            print(f"Error collecting metrics: {str(e)}")
            time.sleep(30)

if __name__ == '__main__':
    main()
EOF

    chmod +x /opt/mysql-monitoring/prometheus_exporter.py
    
    # Create systemd service for Prometheus exporter
    cat > /etc/systemd/system/mysql-prometheus-exporter.service << EOF
[Unit]
Description=MySQL Prometheus Exporter
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mysql-monitoring
ExecStart=/opt/mysql-monitoring/prometheus_exporter.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mysql-prometheus-exporter
    systemctl start mysql-prometheus-exporter
    
    log_info "Prometheus metrics exporter configured and started"
}

# Main execution
main() {
    log_info "Starting MySQL monitoring and alerting setup..."
    
    install_dependencies
    create_monitoring_user
    setup_monitoring_scripts
    create_monitoring_config
    setup_log_rotation
    setup_cron_jobs
    create_daily_report
    setup_prometheus_metrics
    
    log_info "MySQL monitoring and alerting setup completed successfully!"
    log_info "Monitoring logs: /var/log/mysql-monitoring.log"
    log_info "Metrics data: /var/log/mysql-metrics-*.json"
    log_info "Prometheus metrics: http://localhost:9104/metrics"
    
    # Test monitoring
    log_info "Running initial monitoring test..."
    /opt/mysql-monitoring/mysql_monitor.py
}

# Run main function
main "$@"