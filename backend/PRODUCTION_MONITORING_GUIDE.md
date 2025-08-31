# Production Monitoring System Guide

## Overview

The production monitoring system provides comprehensive monitoring, alerting, and health checking capabilities for the e-commerce platform. It includes automated alerting, performance tracking, system health monitoring, and production-ready logging.

## Features

### 1. Production Logging
- **Rotating log files** with automatic cleanup
- **Structured logging** with different log levels
- **Log file management** with size limits and retention policies
- **Multiple log types**: application, error, performance, security

### 2. Alerting System
- **Real-time monitoring** of performance metrics
- **Threshold-based alerts** with configurable rules
- **Alert deduplication** with cooldown periods
- **Multiple notification channels** (email, webhook, Slack)
- **Auto-resolution** when conditions clear

### 3. Health Checks
- **Database connectivity** and performance monitoring
- **Cache system** health and response times
- **System resources** (disk space, memory usage)
- **External services** availability checks

### 4. Monitoring Dashboard
- **System status overview** with real-time data
- **Performance summaries** and trend analysis
- **Active alerts** and alert history
- **Health check results** with detailed metrics

## Quick Start

### 1. Installation

The monitoring system is automatically available when the debugging app is installed. Ensure these dependencies are available:

```bash
pip install psutil  # For system monitoring (optional but recommended)
```

### 2. Configuration

Add to your Django settings:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'apps.debugging',
]

# Optional: Configure logging directory
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Optional: Configure alert recipients
ALERT_EMAIL_RECIPIENTS = ['admin@example.com']

# Optional: Configure monitoring summary recipients
MONITORING_SUMMARY_RECIPIENTS = ['ops@example.com']
```

### 3. URL Configuration

Add to your main `urls.py`:

```python
# urls.py
urlpatterns = [
    # ... other patterns
    path('api/debug/', include('apps.debugging.urls')),
]
```

### 4. Start Monitoring

```python
# In your Django startup (e.g., apps.py or management command)
from apps.debugging.production_monitoring import initialize_production_monitoring

initialize_production_monitoring()
```

Or use the management command:

```bash
python manage.py production_monitoring start
```

## API Endpoints

### Health Check Endpoints

- `GET /api/debug/production/health/` - Basic health check
- `GET /api/debug/production/health/detailed/` - Detailed health status
- `GET /api/debug/production/dashboard/` - Full monitoring dashboard

### Alert Management

- `GET /api/debug/production/alerts/` - List active alerts and history
- `POST /api/debug/production/alerts/resolve/` - Manually resolve an alert

### Example Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2025-08-31T15:46:18.468121Z",
  "service": "ecommerce-backend"
}
```

### Example Detailed Health Check Response

```json
{
  "overall_status": "healthy",
  "timestamp": "2025-08-31T15:46:18.468121Z",
  "uptime_seconds": 3600.5,
  "health_checks": [
    {
      "service": "database",
      "status": "healthy",
      "response_time_ms": 12.5,
      "details": {
        "query_time_ms": 12.5
      },
      "error_message": null
    }
  ],
  "active_alerts_count": 0,
  "performance_summary": {
    "error_count_1h": 0
  }
}
```

## Management Commands

### Start/Stop Monitoring

```bash
# Start production monitoring
python manage.py production_monitoring start

# Stop production monitoring
python manage.py production_monitoring stop

# Check system status
python manage.py production_monitoring status
```

### Health Checks

```bash
# Run all health checks
python manage.py production_monitoring health
```

### Data Management

```bash
# Clean up old monitoring data (keep 30 days)
python manage.py production_monitoring cleanup --days 30

# Generate performance report
python manage.py production_monitoring report --hours 24
```

### Alert Management

```bash
# List active alerts
python manage.py production_monitoring alerts

# Resolve a specific alert
python manage.py production_monitoring resolve <alert_id>
```

## Celery Tasks (Optional)

If Celery is configured, the system includes automated tasks:

### Scheduled Tasks

- **Daily cleanup**: Removes old monitoring data
- **Health checks**: Runs comprehensive health checks every 15 minutes
- **Daily summaries**: Sends monitoring summary emails
- **Session archival**: Archives old workflow sessions weekly

### Manual Task Execution

```python
from apps.debugging.tasks import cleanup_monitoring_data, health_check_all_services

# Clean up old data
result = cleanup_monitoring_data.delay(days_to_keep=30)

# Run health checks
health_result = health_check_all_services.delay()
```

## Alert Configuration

### Default Thresholds

```python
ALERT_THRESHOLDS = {
    'api_response_time': {'warning': 500, 'critical': 2000},  # ms
    'database_query_time': {'warning': 100, 'critical': 500},  # ms
    'memory_usage': {'warning': 80, 'critical': 95},  # %
    'cpu_usage': {'warning': 80, 'critical': 95},  # %
    'error_rate': {'warning': 1, 'critical': 5},  # errors/min
    'disk_usage': {'warning': 85, 'critical': 95},  # %
}
```

### Custom Alert Rules

You can customize alert rules by modifying the `AlertingSystem._load_alert_rules()` method or by creating a configuration file.

## Logging Configuration

### Log Files

- `application.log` - General application logs
- `error.log` - Error-level logs only
- `performance.log` - Performance metrics (if configured)
- `security.log` - Security-related events (if configured)

### Log Rotation

- **Max file size**: 50MB (application/error), 100MB (performance)
- **Backup count**: 10 files (application/error), 5 files (performance)
- **Automatic cleanup**: Files older than 30 days are removed

## Production Deployment

### 1. Environment Variables

```bash
# .env
LOG_DIR=/var/log/ecommerce
ALERT_EMAIL_RECIPIENTS=admin@company.com,ops@company.com
MONITORING_SUMMARY_RECIPIENTS=ops@company.com
```

### 2. System Requirements

- **Disk space**: Ensure adequate space for log files
- **Memory**: Monitor memory usage for alert thresholds
- **Permissions**: Write access to log directory

### 3. Load Balancer Integration

Configure your load balancer to use the health check endpoint:

```
Health Check URL: /api/debug/production/health/
Expected Response: 200 OK with {"status": "healthy"}
```

### 4. Monitoring Integration

The system can integrate with external monitoring tools:

- **Prometheus**: Export metrics via custom endpoints
- **Grafana**: Create dashboards using the API data
- **PagerDuty**: Configure webhook notifications
- **Slack**: Set up alert notifications

## Troubleshooting

### Common Issues

1. **Alerts not firing**: Check that monitoring is started and thresholds are configured
2. **Health checks failing**: Verify database connectivity and system resources
3. **Log files not rotating**: Check file permissions and disk space
4. **Email alerts not sending**: Verify SMTP configuration in Django settings

### Debug Commands

```bash
# Test the monitoring system
python test_production_monitoring.py

# Check Django configuration
python manage.py check

# Verify database connectivity
python manage.py dbshell
```

### Log Analysis

```bash
# View recent application logs
tail -f logs/application.log

# Search for errors
grep "ERROR" logs/application.log

# Monitor performance logs
tail -f logs/performance.log
```

## Security Considerations

1. **Log file access**: Restrict access to log files in production
2. **Alert notifications**: Use secure channels for sensitive alerts
3. **Health check endpoints**: Consider authentication for detailed health checks
4. **Data retention**: Regularly clean up old monitoring data

## Performance Impact

The monitoring system is designed to have minimal performance impact:

- **Background monitoring**: Runs in separate threads
- **Efficient queries**: Uses database aggregation for metrics
- **Configurable intervals**: Adjust monitoring frequency as needed
- **Resource monitoring**: Monitors its own resource usage

## Support and Maintenance

### Regular Tasks

1. **Review alert thresholds** monthly
2. **Clean up old log files** weekly
3. **Test alert notifications** quarterly
4. **Update monitoring rules** as system evolves

### Monitoring the Monitor

The system includes self-monitoring capabilities:

- **Health check for monitoring components**
- **Alerts for monitoring system failures**
- **Performance metrics for monitoring overhead**

For additional support or customization, refer to the source code in `apps/debugging/production_monitoring.py`.