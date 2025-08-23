# E2E Workflow Debugging System

## Overview

The E2E Workflow Debugging System is a comprehensive debugging and validation platform designed to ensure seamless integration between the Next.js frontend, Django REST API backend, and MySQL database. This system provides automated discovery, validation, tracing, and monitoring capabilities to identify and resolve integration issues across the entire technology stack.

## Features

### 🔍 Workflow Tracing
- **Correlation ID Management**: Unique IDs track requests across all system layers
- **Step-by-Step Tracking**: Monitor individual operations within workflows
- **Performance Timing**: Measure response times at each layer
- **Error Correlation**: Link errors across frontend, API, and database

### 📊 Performance Monitoring
- **Real-time Metrics**: Collect performance data from all system layers
- **Threshold Management**: Configurable warning and critical thresholds
- **Automated Alerting**: Notifications when performance degrades
- **Historical Analysis**: Track performance trends over time

### 🚨 Error Logging
- **Comprehensive Error Tracking**: Capture errors across all layers
- **Stack Trace Preservation**: Full error context for debugging
- **Error Classification**: Categorize by severity and type
- **Resolution Tracking**: Mark errors as resolved with notes

### 📈 Interactive Dashboard
- **System Health Overview**: Real-time status of all components
- **Workflow Visualization**: Interactive trace visualization
- **Performance Analytics**: Charts and metrics for system performance
- **Error Analysis**: Grouped error reports with resolution suggestions

## Architecture

### Core Components

1. **Models** (`models.py`)
   - `WorkflowSession`: Track complete user workflows
   - `TraceStep`: Individual steps within workflows
   - `PerformanceSnapshot`: Performance metrics collection
   - `ErrorLog`: Comprehensive error logging
   - `DebugConfiguration`: System configuration
   - `PerformanceThreshold`: Performance alerting thresholds

2. **Utilities** (`utils.py`)
   - `WorkflowTracer`: Workflow tracing utility
   - `PerformanceMonitor`: Performance metrics collection
   - `ErrorLogger`: Error logging utility

3. **Middleware** (`middleware.py`)
   - `CorrelationIdMiddleware`: Request correlation tracking
   - `DebuggingMiddleware`: Performance monitoring and error capture

4. **API Endpoints** (`views.py`, `serializers.py`)
   - RESTful API for accessing debugging data
   - Real-time system health monitoring
   - Performance analytics and reporting

## Installation

The debugging system is already installed and configured in the Django project:

1. **App Registration**: Added to `INSTALLED_APPS` in settings
2. **Middleware Configuration**: Correlation ID and debugging middleware enabled
3. **URL Configuration**: API endpoints available at `/api/v1/debugging/`
4. **Database Migration**: Tables created and configured
5. **Default Configuration**: Performance thresholds and settings initialized

## Usage

### Starting a Workflow Trace

```python
from apps.debugging.utils import WorkflowTracer

# Initialize tracer
tracer = WorkflowTracer()

# Start workflow
workflow = tracer.start_workflow(
    workflow_type='login',
    user=request.user,
    metadata={'ip_address': request.META.get('REMOTE_ADDR')}
)

# Add trace steps
step = tracer.add_trace_step(
    workflow_session=workflow,
    layer='api',
    component='AuthViewSet',
    operation='authenticate'
)

# Complete the step
tracer.complete_trace_step(step, metadata={'success': True})
```

### Recording Performance Metrics

```python
from apps.debugging.utils import PerformanceMonitor

# Record a performance metric
PerformanceMonitor.record_metric(
    layer='api',
    component='ProductViewSet',
    metric_name='response_time',
    metric_value=150.0,
    correlation_id=request.correlation_id
)
```

### Logging Errors

```python
from apps.debugging.utils import ErrorLogger

# Log an error
ErrorLogger.log_error(
    layer='api',
    component='ProductViewSet',
    error_type='ValidationError',
    error_message='Invalid product data',
    correlation_id=request.correlation_id,
    user=request.user
)

# Log an exception with stack trace
ErrorLogger.log_exception(
    exception=e,
    layer='api',
    component='ProductViewSet',
    correlation_id=request.correlation_id,
    user=request.user,
    request=request
)
```

## API Endpoints

### Workflow Sessions
- `GET /api/v1/debugging/workflow-sessions/` - List workflow sessions
- `POST /api/v1/debugging/workflow-sessions/` - Create workflow session
- `GET /api/v1/debugging/workflow-sessions/{id}/` - Get workflow details
- `POST /api/v1/debugging/workflow-sessions/{id}/complete/` - Mark as completed
- `GET /api/v1/debugging/workflow-sessions/stats/` - Get workflow statistics

### Performance Monitoring
- `GET /api/v1/debugging/performance-snapshots/` - List performance metrics
- `POST /api/v1/debugging/performance-snapshots/` - Record metric
- `GET /api/v1/debugging/performance-snapshots/alerts/` - Get performance alerts

### Error Logging
- `GET /api/v1/debugging/error-logs/` - List error logs
- `POST /api/v1/debugging/error-logs/` - Log error
- `POST /api/v1/debugging/error-logs/{id}/resolve/` - Mark error as resolved
- `GET /api/v1/debugging/error-logs/summary/` - Get error statistics

### System Health
- `GET /api/v1/debugging/system-health/` - Get system health status

### Configuration
- `GET /api/v1/debugging/debug-configurations/` - List configurations
- `GET /api/v1/debugging/performance-thresholds/` - List thresholds

## Configuration

### Default Performance Thresholds

| Layer | Metric | Warning | Critical |
|-------|--------|---------|----------|
| API | Response Time | 500ms | 2000ms |
| Database | Response Time | 100ms | 500ms |
| Frontend | Response Time | 200ms | 1000ms |
| System | Memory Usage | 80% | 95% |
| System | CPU Usage | 70% | 90% |
| API | Error Rate | 5% | 10% |
| Cache | Hit Rate | 80% | 60% |

### Debug Configurations

- **Tracing Enabled**: Enable/disable request tracing
- **Performance Monitoring**: Configure metrics collection
- **Error Logging**: Set logging levels and retention
- **Dashboard Settings**: Configure dashboard behavior

## Management Commands

### Setup Default Configuration
```bash
python manage.py setup_debugging_defaults
```

This command creates default performance thresholds and debug configurations.

## Database Tables

- `debugging_workflow_session` - Workflow tracking
- `debugging_trace_step` - Individual trace steps
- `debugging_performance_snapshot` - Performance metrics
- `debugging_error_log` - Error logs
- `debugging_configuration` - System configuration
- `debugging_performance_threshold` - Performance thresholds

## Middleware Integration

The debugging system automatically integrates with Django requests through middleware:

1. **Correlation ID Assignment**: Every request gets a unique correlation ID
2. **Performance Tracking**: Response times are automatically recorded
3. **Error Capture**: Exceptions are automatically logged with context
4. **Request Context**: User, IP, and request details are captured

## Admin Interface

The debugging system includes a comprehensive Django admin interface for:

- Viewing workflow sessions and trace steps
- Monitoring performance metrics and alerts
- Managing error logs and resolutions
- Configuring system settings and thresholds

Access the admin interface at `/admin/` and navigate to the "E2E Workflow Debugging System" section.

## Next Steps

This implementation provides the core infrastructure for the E2E Workflow Debugging System. Future tasks will build upon this foundation to add:

1. Frontend route discovery and mapping
2. Backend API validation engine
3. Database monitoring and validation
4. Interactive debugging dashboard
5. Automated testing and validation tools

## Support

For questions or issues with the debugging system, refer to:
- Django admin interface for data inspection
- API endpoints for programmatic access
- Log files for system diagnostics
- Performance metrics for system health