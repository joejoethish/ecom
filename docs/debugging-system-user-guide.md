# E2E Workflow Debugging System - User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Dashboard Interface](#dashboard-interface)
4. [Workflow Tracing](#workflow-tracing)
5. [Performance Monitoring](#performance-monitoring)
6. [Error Analysis](#error-analysis)
7. [Route Discovery](#route-discovery)
8. [API Testing Tools](#api-testing-tools)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

## Overview

The E2E Workflow Debugging System provides comprehensive tools for monitoring, debugging, and optimizing the entire application stack. It traces user workflows from frontend interactions through API calls to database operations, providing real-time insights into system behavior and performance.

### Key Features

- **End-to-End Workflow Tracing**: Track complete user journeys across all system layers
- **Real-Time Performance Monitoring**: Monitor response times, memory usage, and system health
- **Comprehensive Error Tracking**: Correlate errors across frontend, backend, and database layers
- **Interactive Debugging Dashboard**: Visual interface for system monitoring and debugging
- **Automated Route Discovery**: Automatically map frontend routes to backend API endpoints
- **API Testing Tools**: Test and validate API endpoints directly from the dashboard
- **Performance Optimization**: Identify bottlenecks and receive optimization recommendations

## Getting Started

### Accessing the Debug Dashboard

1. Navigate to `/debug` in your application
2. Log in with admin credentials (required for full access)
3. The dashboard will display the current system health overview

### Basic Navigation

The debug dashboard consists of several main sections:

- **System Health**: Overall system status and alerts
- **Active Workflows**: Currently running workflow traces
- **Performance Metrics**: Real-time performance data
- **Error Logs**: Recent errors and their correlation
- **Route Discovery**: Frontend-backend API mapping
- **API Testing**: Interactive API endpoint testing

## Dashboard Interface

### System Health Overview

The main dashboard displays:

```
┌─────────────────────────────────────────────────────────────┐
│ System Health Status: ● Healthy                            │
├─────────────────────────────────────────────────────────────┤
│ Active Workflows: 12    Recent Errors: 2    Alerts: 0     │
├─────────────────────────────────────────────────────────────┤
│ Layer Status:                                               │
│ ● Frontend: Healthy     ● API: Healthy                     │
│ ● Database: Healthy     ● Cache: Healthy                   │
└─────────────────────────────────────────────────────────────┘
```

### Status Indicators

- **🟢 Healthy**: All systems operating normally
- **🟡 Degraded**: Some performance issues detected
- **🔴 Critical**: Significant issues requiring attention

### Real-Time Updates

The dashboard updates automatically every 5 seconds with:
- New workflow traces
- Performance metrics
- Error logs
- System health changes

## Workflow Tracing

### Understanding Workflow Types

The system tracks several workflow types:

1. **Login Workflow**: User authentication process
2. **Product Fetch**: Product catalog and detail retrieval
3. **Cart Operations**: Add/remove items from cart
4. **Checkout**: Complete purchase process
5. **Order Management**: Order tracking and updates

### Viewing Workflow Traces

1. Click on **"Active Workflows"** or **"Workflow History"**
2. Select a workflow to view detailed trace information
3. Each trace shows:
   - Correlation ID for tracking
   - Start and end times
   - Individual steps with timing
   - Any errors encountered

### Workflow Trace Example

```
Workflow: User Login (correlation-id: abc123)
├── Frontend: LoginForm.form_submit (50ms)
├── API: AuthenticationView.authenticate_user (120ms)
├── Database: UserModel.user_lookup (25ms)
├── API: JWTService.generate_token (30ms)
└── Frontend: AuthService.store_token (15ms)
Total Duration: 240ms
```

### Filtering and Searching

- **Filter by Type**: Select specific workflow types
- **Filter by Status**: Show only completed, failed, or in-progress workflows
- **Filter by User**: View workflows for specific users
- **Search by Correlation ID**: Find specific workflow traces
- **Date Range**: Filter by time period

## Performance Monitoring

### Key Metrics

The system monitors several performance metrics:

#### Response Time Metrics
- **API Response Time**: Time for API endpoints to respond
- **Database Query Time**: Time for database operations
- **Frontend Render Time**: Time for components to render

#### Resource Usage Metrics
- **Memory Usage**: RAM consumption by different components
- **CPU Usage**: Processor utilization
- **Connection Pool**: Database connection usage

#### Throughput Metrics
- **Requests per Second**: API endpoint throughput
- **Workflows per Minute**: Completed workflow rate
- **Error Rate**: Percentage of failed operations

### Performance Thresholds

Configure performance thresholds for automatic alerting:

```json
{
  "api_response_time": {
    "warning": 200,
    "critical": 500
  },
  "database_query_time": {
    "warning": 50,
    "critical": 100
  },
  "memory_usage": {
    "warning": 100,
    "critical": 200
  }
}
```

### Performance Alerts

When thresholds are exceeded:
1. Alerts appear in the dashboard
2. Email notifications are sent (if configured)
3. Detailed analysis is provided
4. Optimization recommendations are suggested

### Performance Trends

View historical performance data:
- **Hourly Trends**: Performance over the last 24 hours
- **Daily Trends**: Performance over the last 30 days
- **Comparison Views**: Compare current vs. historical performance

## Error Analysis

### Error Correlation

The system correlates errors across all layers using correlation IDs:

```
Error Chain for correlation-id: xyz789
├── Frontend: NetworkError - API request timeout
├── API: DatabaseError - Connection pool exhausted
└── Database: ConnectionError - Max connections reached
```

### Error Severity Levels

- **Debug**: Development information
- **Info**: General information
- **Warning**: Potential issues
- **Error**: Actual errors that need attention
- **Critical**: Severe errors requiring immediate action

### Error Resolution

1. **View Error Details**: Click on any error to see full details
2. **Check Related Errors**: View all errors with the same correlation ID
3. **Mark as Resolved**: Update error status when fixed
4. **Add Resolution Notes**: Document the fix for future reference

### Error Patterns

The system identifies common error patterns:
- **Recurring Errors**: Errors that happen frequently
- **Error Clusters**: Multiple related errors
- **Performance-Related Errors**: Errors caused by performance issues

## Route Discovery

### Automatic Route Scanning

The system automatically discovers:
- **Frontend Routes**: All Next.js pages and API routes
- **API Endpoints**: All Django REST API endpoints
- **Route Dependencies**: Mapping between frontend routes and API calls

### Route Discovery Results

View discovered routes in the **Route Discovery** section:

```
Frontend Routes (25 discovered)
├── /products (ProductsPage)
│   ├── GET /api/products
│   └── GET /api/categories
├── /cart (CartPage)
│   ├── GET /api/cart
│   ├── POST /api/cart/add
│   └── DELETE /api/cart/remove
└── /checkout (CheckoutPage)
    ├── POST /api/orders
    └── POST /api/payments
```

### Manual Route Scanning

Trigger a new route discovery scan:
1. Go to **Route Discovery** section
2. Click **"Scan Routes"** button
3. Wait for scan completion
4. Review updated results

### Route Validation

Validate discovered routes:
1. Click **"Validate Routes"** button
2. System tests all discovered API endpoints
3. View validation results and any issues found

## API Testing Tools

### Interactive API Testing

Test API endpoints directly from the dashboard:

1. **Select Endpoint**: Choose from discovered or enter custom endpoint
2. **Configure Request**:
   - HTTP method (GET, POST, PUT, DELETE, PATCH)
   - Request headers
   - Request payload (for POST/PUT requests)
   - Authentication settings
3. **Send Request**: Execute the API call
4. **View Response**: See response data, status code, and timing

### Test Request Example

```json
{
  "method": "POST",
  "endpoint": "/api/products",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-token"
  },
  "payload": {
    "name": "Test Product",
    "price": 99.99,
    "category": "Electronics"
  }
}
```

### Batch Testing

Test multiple endpoints at once:
1. Create test suite with multiple requests
2. Execute all tests in sequence
3. View consolidated results
4. Export test results for documentation

### Authentication Testing

Test different authentication scenarios:
- **No Authentication**: Test public endpoints
- **JWT Authentication**: Test with valid/invalid tokens
- **Session Authentication**: Test with session cookies
- **Permission Testing**: Test with different user roles

## Configuration

### Debug Configuration Settings

Access configuration via **Settings** section:

#### Tracing Configuration
```json
{
  "tracing_enabled": true,
  "trace_all_requests": false,
  "trace_sampling_rate": 0.1,
  "max_trace_duration": 300000
}
```

#### Performance Monitoring
```json
{
  "performance_monitoring_enabled": true,
  "metric_collection_interval": 5000,
  "performance_alerts_enabled": true,
  "alert_email_recipients": ["admin@example.com"]
}
```

#### Error Logging
```json
{
  "error_logging_enabled": true,
  "log_level": "warning",
  "error_retention_days": 30,
  "stack_trace_enabled": true
}
```

### Environment-Specific Settings

Configure different settings for each environment:

#### Development
- Enable all debugging features
- Detailed logging
- No performance thresholds

#### Staging
- Enable performance monitoring
- Moderate logging
- Relaxed performance thresholds

#### Production
- Essential monitoring only
- Error logging only
- Strict performance thresholds

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
1. Check if debugging app is enabled in Django settings
2. Verify user has admin permissions
3. Check browser console for JavaScript errors
4. Ensure WebSocket connection is working

#### Missing Workflow Traces
1. Verify correlation ID middleware is enabled
2. Check if tracing is enabled in configuration
3. Ensure frontend is sending correlation headers
4. Check database connectivity

#### Performance Metrics Not Updating
1. Verify performance monitoring is enabled
2. Check metric collection interval settings
3. Ensure background tasks are running
4. Check for database connection issues

#### Route Discovery Not Working
1. Verify Next.js app structure is standard
2. Check file system permissions
3. Ensure route discovery service is running
4. Check for syntax errors in route files

### Debug Mode

Enable debug mode for additional information:
1. Set `DEBUG_DEBUGGING_SYSTEM=True` in environment
2. Restart the application
3. Additional logging will be available
4. More detailed error messages will be shown

### Log Analysis

Check application logs for debugging issues:

```bash
# Backend logs
tail -f backend/logs/debugging.log

# Frontend logs (browser console)
# Check Network tab for API call issues

# Database logs
# Check slow query log for performance issues
```

## Best Practices

### Performance Optimization

1. **Monitor Key Metrics**: Focus on response time, memory usage, and error rates
2. **Set Appropriate Thresholds**: Configure realistic performance thresholds
3. **Regular Review**: Review performance trends weekly
4. **Optimize Based on Data**: Use metrics to guide optimization efforts

### Error Management

1. **Correlation ID Usage**: Always use correlation IDs for request tracking
2. **Meaningful Error Messages**: Provide clear, actionable error messages
3. **Error Resolution**: Mark errors as resolved when fixed
4. **Pattern Recognition**: Look for recurring error patterns

### Workflow Tracing

1. **Trace Critical Paths**: Focus on important user workflows
2. **Sampling**: Use sampling in production to reduce overhead
3. **Metadata**: Include relevant metadata in trace steps
4. **Regular Cleanup**: Archive old trace data regularly

### Security Considerations

1. **Access Control**: Limit debug dashboard access to authorized users
2. **Data Sensitivity**: Be careful with sensitive data in traces
3. **Production Usage**: Use minimal tracing in production
4. **Log Retention**: Set appropriate log retention policies

### Maintenance

1. **Regular Updates**: Keep the debugging system updated
2. **Database Maintenance**: Regular cleanup of old data
3. **Performance Review**: Monitor the debugging system's own performance
4. **Backup**: Regular backup of debugging configuration and data

## Advanced Features

### Custom Metrics

Add custom performance metrics:

```javascript
// Frontend
import { WorkflowTracer } from '@/lib/workflow-tracing';

const tracer = new WorkflowTracer();
tracer.recordMetric({
  layer: 'frontend',
  component: 'CustomComponent',
  metricName: 'custom_operation_time',
  metricValue: operationTime,
  metadata: { operation: 'custom_operation' }
});
```

```python
# Backend
from apps.debugging.utils import PerformanceMonitor

PerformanceMonitor.record_metric(
    layer='api',
    component='CustomView',
    metric_name='custom_processing_time',
    metric_value=processing_time,
    metadata={'operation': 'custom_processing'}
)
```

### Custom Workflow Types

Define custom workflow types:

```python
# Backend - Add to WorkflowSession.WORKFLOW_TYPES
WORKFLOW_TYPES = [
    # ... existing types
    ('custom_workflow', 'Custom Workflow'),
]
```

### Integration with External Tools

#### Grafana Integration
Export metrics to Grafana for advanced visualization:

```python
# Configure Grafana data source
GRAFANA_CONFIG = {
    'url': 'http://grafana:3000',
    'api_key': 'your-api-key',
    'dashboard_id': 'debugging-dashboard'
}
```

#### Slack Notifications
Configure Slack alerts for critical issues:

```python
SLACK_CONFIG = {
    'webhook_url': 'https://hooks.slack.com/...',
    'channel': '#alerts',
    'alert_threshold': 'critical'
}
```

## API Reference

For detailed API documentation, see [API Reference](debugging-system-api-reference.md).

## Support

For additional support:
- Check the troubleshooting section above
- Review application logs
- Contact the development team
- Submit issues via the project repository