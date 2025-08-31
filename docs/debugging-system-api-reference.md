# E2E Workflow Debugging System - API Reference

## Table of Contents

1. [Authentication](#authentication)
2. [Workflow Session API](#workflow-session-api)
3. [Trace Step API](#trace-step-api)
4. [Performance Snapshot API](#performance-snapshot-api)
5. [Error Log API](#error-log-api)
6. [System Health API](#system-health-api)
7. [Route Discovery API](#route-discovery-api)
8. [Configuration API](#configuration-api)
9. [WebSocket API](#websocket-api)
10. [Frontend JavaScript API](#frontend-javascript-api)
11. [Error Codes](#error-codes)
12. [Rate Limiting](#rate-limiting)

## Authentication

All API endpoints require authentication. Use JWT tokens in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Required Permissions

- **Admin Users**: Full access to all debugging endpoints
- **Regular Users**: Limited access to their own workflow data
- **Anonymous Users**: No access to debugging endpoints

## Workflow Session API

### List Workflow Sessions

```http
GET /api/v1/debugging/workflow-sessions/
```

**Query Parameters:**
- `workflow_type` (string): Filter by workflow type
- `status` (string): Filter by status (in_progress, completed, failed)
- `user` (integer): Filter by user ID
- `start_time__gte` (datetime): Filter by start time (greater than or equal)
- `start_time__lte` (datetime): Filter by start time (less than or equal)
- `page` (integer): Page number for pagination
- `page_size` (integer): Number of results per page

**Response:**
```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/debugging/workflow-sessions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
      "workflow_type": "login",
      "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
      },
      "session_key": "abc123",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T10:30:02Z",
      "status": "completed",
      "duration_ms": 2000,
      "metadata": {
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.1"
      },
      "trace_steps": [
        {
          "id": 1,
          "layer": "frontend",
          "component": "LoginForm",
          "operation": "form_submit",
          "start_time": "2024-01-15T10:30:00Z",
          "end_time": "2024-01-15T10:30:00.050Z",
          "status": "completed",
          "duration_ms": 50,
          "metadata": {}
        }
      ]
    }
  ]
}
```

### Create Workflow Session

```http
POST /api/v1/debugging/workflow-sessions/
```

**Request Body:**
```json
{
  "workflow_type": "login",
  "user": 1,
  "session_key": "abc123",
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_type": "login",
  "user": 1,
  "session_key": "abc123",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": null,
  "status": "in_progress",
  "duration_ms": null,
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1"
  }
}
```

### Get Workflow Session

```http
GET /api/v1/debugging/workflow-sessions/{id}/
```

**Response:** Same as create response with trace_steps included.

### Complete Workflow Session

```http
POST /api/v1/debugging/workflow-sessions/{id}/complete/
```

**Request Body:**
```json
{
  "metadata": {
    "completion_reason": "success"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "end_time": "2024-01-15T10:30:02Z",
  "duration_ms": 2000
}
```

### Fail Workflow Session

```http
POST /api/v1/debugging/workflow-sessions/{id}/fail/
```

**Request Body:**
```json
{
  "error_message": "Authentication failed",
  "metadata": {
    "error_code": "AUTH_001"
  }
}
```

### Get Workflow Statistics

```http
GET /api/v1/debugging/workflow-sessions/stats/
```

**Response:**
```json
{
  "total_workflows": 1500,
  "completed_workflows": 1350,
  "failed_workflows": 150,
  "average_duration_ms": 2500,
  "workflow_types": {
    "login": 500,
    "product_fetch": 600,
    "cart_update": 300,
    "checkout": 100
  },
  "recent_activity": [
    {
      "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
      "workflow_type": "login",
      "status": "completed",
      "start_time": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Trace Step API

### List Trace Steps

```http
GET /api/v1/debugging/trace-steps/
```

**Query Parameters:**
- `workflow_session` (integer): Filter by workflow session ID
- `layer` (string): Filter by layer (frontend, api, database, cache, external)
- `component` (string): Filter by component name
- `status` (string): Filter by status
- `start_time__gte` (datetime): Filter by start time

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "layer": "frontend",
      "component": "LoginForm",
      "operation": "form_submit",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T10:30:00.050Z",
      "status": "completed",
      "duration_ms": 50,
      "metadata": {
        "form_data": {
          "username": "testuser"
        }
      }
    }
  ]
}
```

### Create Trace Step

```http
POST /api/v1/debugging/trace-steps/
```

**Request Body:**
```json
{
  "workflow_session": 1,
  "layer": "api",
  "component": "AuthView",
  "operation": "authenticate_user",
  "start_time": "2024-01-15T10:30:00.050Z",
  "metadata": {
    "username": "testuser",
    "authentication_method": "password"
  }
}
```

### Complete Trace Step

```http
POST /api/v1/debugging/trace-steps/{id}/complete/
```

**Request Body:**
```json
{
  "metadata": {
    "result": "success",
    "user_id": 1
  }
}
```

## Performance Snapshot API

### List Performance Snapshots

```http
GET /api/v1/debugging/performance-snapshots/
```

**Query Parameters:**
- `layer` (string): Filter by layer
- `component` (string): Filter by component
- `metric_name` (string): Filter by metric name
- `correlation_id` (uuid): Filter by correlation ID
- `timestamp__gte` (datetime): Filter by timestamp

**Response:**
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00Z",
      "layer": "api",
      "component": "AuthView",
      "metric_name": "response_time",
      "metric_value": 120.5,
      "threshold_warning": 200.0,
      "threshold_critical": 500.0,
      "is_warning": false,
      "is_critical": false,
      "metadata": {
        "endpoint": "/api/auth/login",
        "method": "POST"
      }
    }
  ]
}
```

### Create Performance Snapshot

```http
POST /api/v1/debugging/performance-snapshots/
```

**Request Body:**
```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "layer": "api",
  "component": "AuthView",
  "metric_name": "response_time",
  "metric_value": 120.5,
  "metadata": {
    "endpoint": "/api/auth/login",
    "method": "POST"
  }
}
```

### Get Performance Alerts

```http
GET /api/v1/debugging/performance-snapshots/alerts/
```

**Response:**
```json
{
  "alerts": [
    {
      "type": "warning",
      "metric": {
        "id": 1,
        "layer": "api",
        "component": "ProductView",
        "metric_name": "response_time",
        "metric_value": 250.0,
        "threshold_warning": 200.0,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    },
    {
      "type": "critical",
      "metric": {
        "id": 2,
        "layer": "database",
        "component": "ProductModel",
        "metric_name": "query_time",
        "metric_value": 1500.0,
        "threshold_critical": 1000.0,
        "timestamp": "2024-01-15T10:30:01Z"
      }
    }
  ]
}
```

## Error Log API

### List Error Logs

```http
GET /api/v1/debugging/error-logs/
```

**Query Parameters:**
- `layer` (string): Filter by layer
- `component` (string): Filter by component
- `severity` (string): Filter by severity (debug, info, warning, error, critical)
- `error_type` (string): Filter by error type
- `resolved` (boolean): Filter by resolution status
- `correlation_id` (uuid): Filter by correlation ID
- `search` (string): Search in error message and type

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00Z",
      "layer": "api",
      "component": "AuthView",
      "severity": "error",
      "error_type": "ValidationError",
      "error_message": "Invalid username or password",
      "stack_trace": "Traceback (most recent call last):\n...",
      "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
      },
      "request_path": "/api/auth/login",
      "request_method": "POST",
      "user_agent": "Mozilla/5.0...",
      "ip_address": "192.168.1.1",
      "resolved": false,
      "resolution_notes": null,
      "metadata": {
        "form_data": {
          "username": "testuser"
        }
      }
    }
  ]
}
```

### Create Error Log

```http
POST /api/v1/debugging/error-logs/
```

**Request Body:**
```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "layer": "frontend",
  "component": "LoginForm",
  "severity": "error",
  "error_type": "NetworkError",
  "error_message": "Failed to connect to server",
  "stack_trace": "Error: Failed to connect to server\n    at fetch...",
  "request_path": "/login",
  "request_method": "POST",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1",
  "metadata": {
    "timeout": 5000,
    "retry_count": 3
  }
}
```

### Resolve Error Log

```http
POST /api/v1/debugging/error-logs/{id}/resolve/
```

**Request Body:**
```json
{
  "resolution_notes": "Fixed by updating server configuration"
}
```

### Get Error Summary

```http
GET /api/v1/debugging/error-logs/summary/
```

**Response:**
```json
{
  "total_errors": 150,
  "recent_errors": 25,
  "unresolved_errors": 10,
  "severity_distribution": {
    "debug": 5,
    "info": 20,
    "warning": 50,
    "error": 60,
    "critical": 15
  },
  "layer_distribution": {
    "frontend": 40,
    "api": 70,
    "database": 30,
    "cache": 5,
    "external": 5
  },
  "top_error_types": {
    "ValidationError": 25,
    "NetworkError": 20,
    "DatabaseError": 15,
    "AuthenticationError": 10,
    "PermissionError": 5
  }
}
```

## System Health API

### Get System Health

```http
GET /api/v1/debugging/system-health/
```

**Response:**
```json
{
  "overall_status": "healthy",
  "active_workflows": 12,
  "recent_errors": 2,
  "performance_alerts": 0,
  "layers": {
    "frontend": {
      "status": "healthy",
      "errors": 0,
      "performance_issues": 0
    },
    "api": {
      "status": "healthy",
      "errors": 1,
      "performance_issues": 0
    },
    "database": {
      "status": "degraded",
      "errors": 1,
      "performance_issues": 1
    },
    "cache": {
      "status": "healthy",
      "errors": 0,
      "performance_issues": 0
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Route Discovery API

### Trigger Route Scan

```http
POST /api/v1/debugging/route-discovery/scan/
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "start_time": "2024-01-15T10:30:00Z"
}
```

### Get Discovery Results

```http
GET /api/v1/debugging/route-discovery/results/
```

**Response:**
```json
{
  "routes": [
    {
      "path": "/products",
      "route_type": "page",
      "component_name": "ProductsPage",
      "api_calls": [
        {
          "method": "GET",
          "endpoint": "/api/products",
          "requires_authentication": false
        }
      ]
    }
  ],
  "totalRoutes": 25,
  "apiCallsCount": 45,
  "lastScanned": "2024-01-15T10:30:00Z",
  "scanDuration": 5000
}
```

### Get Dependency Map

```http
GET /api/v1/debugging/route-discovery/dependencies/
```

**Response:**
```json
{
  "frontend_routes": [
    {
      "path": "/products",
      "route_type": "page",
      "component_name": "ProductsPage"
    }
  ],
  "api_endpoints": [
    "/api/products",
    "/api/categories",
    "/api/cart"
  ],
  "dependencies": [
    {
      "frontend_route": "/products",
      "api_endpoint": "/api/products",
      "method": "GET",
      "component": "ProductsPage"
    }
  ]
}
```

### Validate Routes

```http
POST /api/v1/debugging/route-discovery/validate/
```

**Response:**
```json
{
  "totalRoutes": 25,
  "validRoutes": 23,
  "invalidRoutes": 2,
  "errors": [
    "Route /invalid-route not found",
    "API endpoint /api/missing returns 404"
  ]
}
```

## Configuration API

### List Debug Configurations

```http
GET /api/v1/debugging/debug-configurations/
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "tracing_enabled",
      "config_type": "tracing_enabled",
      "enabled": true,
      "config_data": {
        "sample_rate": 0.1,
        "max_duration": 300000
      },
      "description": "Enable workflow tracing",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Update Debug Configuration

```http
PUT /api/v1/debugging/debug-configurations/{id}/
```

**Request Body:**
```json
{
  "enabled": true,
  "config_data": {
    "sample_rate": 0.2,
    "max_duration": 600000
  },
  "description": "Updated tracing configuration"
}
```

### List Performance Thresholds

```http
GET /api/v1/debugging/performance-thresholds/
```

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "metric_name": "response_time",
      "layer": "api",
      "component": "AuthView",
      "warning_threshold": 200.0,
      "critical_threshold": 500.0,
      "enabled": true,
      "alert_on_warning": true,
      "alert_on_critical": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## WebSocket API

### Connection

Connect to the WebSocket endpoint for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/debugging/');
```

### Message Types

#### Workflow Update
```json
{
  "type": "workflow_update",
  "data": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "workflow_type": "login",
    "status": "completed",
    "duration_ms": 2000
  }
}
```

#### Error Alert
```json
{
  "type": "error_alert",
  "data": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "severity": "critical",
    "error_type": "DatabaseError",
    "error_message": "Connection timeout",
    "layer": "database",
    "component": "ProductModel"
  }
}
```

#### Performance Alert
```json
{
  "type": "performance_alert",
  "data": {
    "layer": "api",
    "component": "ProductView",
    "metric_name": "response_time",
    "metric_value": 750.0,
    "threshold_critical": 500.0,
    "alert_type": "critical"
  }
}
```

#### System Health Update
```json
{
  "type": "system_health_update",
  "data": {
    "overall_status": "degraded",
    "changed_layers": ["database"],
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Frontend JavaScript API

### WorkflowTracer Class

```javascript
import { WorkflowTracer } from '@/lib/workflow-tracing';

const tracer = new WorkflowTracer();

// Start workflow
await tracer.startWorkflow({
  workflowType: 'login',
  metadata: { username: 'testuser' }
});

// Trace step
await tracer.traceStep({
  layer: 'frontend',
  component: 'LoginForm',
  operation: 'form_submit',
  metadata: { formData: {...} }
});

// Record metric
await tracer.recordMetric({
  layer: 'frontend',
  component: 'LoginForm',
  metricName: 'render_time',
  metricValue: 150.5,
  metadata: { componentCount: 5 }
});

// Log error
await tracer.logError({
  layer: 'frontend',
  component: 'LoginForm',
  errorType: 'ValidationError',
  errorMessage: 'Invalid input',
  metadata: { field: 'username' }
});

// Complete workflow
await tracer.completeWorkflow();

// Fail workflow
await tracer.failWorkflow({
  errorMessage: 'Authentication failed'
});
```

### Correlation ID Service

```javascript
import { generateCorrelationId, getCurrentCorrelationId } from '@/services/correlationId';

// Generate new correlation ID
const correlationId = generateCorrelationId();

// Get current correlation ID
const currentId = getCurrentCorrelationId();

// Set correlation ID for request
fetch('/api/products', {
  headers: {
    'X-Correlation-ID': correlationId
  }
});
```

### Performance Monitoring

```javascript
import { PerformanceMonitor } from '@/utils/performance';

// Monitor component render time
const monitor = new PerformanceMonitor();

monitor.startTiming('component_render');
// ... component rendering
const renderTime = monitor.endTiming('component_render');

// Record the metric
await tracer.recordMetric({
  layer: 'frontend',
  component: 'ProductList',
  metricName: 'render_time',
  metricValue: renderTime
});
```

## Error Codes

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Custom Error Codes

#### Workflow Errors
- `WORKFLOW_001`: Invalid workflow type
- `WORKFLOW_002`: Workflow already completed
- `WORKFLOW_003`: Workflow not found
- `WORKFLOW_004`: Invalid correlation ID

#### Tracing Errors
- `TRACE_001`: Invalid trace step data
- `TRACE_002`: Trace step not found
- `TRACE_003`: Invalid layer or component

#### Performance Errors
- `PERF_001`: Invalid metric name
- `PERF_002`: Metric value out of range
- `PERF_003`: Threshold configuration error

#### Route Discovery Errors
- `ROUTE_001`: Route scan failed
- `ROUTE_002`: Invalid route configuration
- `ROUTE_003`: Route validation failed

## Rate Limiting

### Default Limits

- **Workflow Creation**: 100 requests per minute per user
- **Trace Steps**: 1000 requests per minute per user
- **Performance Metrics**: 500 requests per minute per user
- **Error Logging**: 200 requests per minute per user
- **Route Discovery**: 10 scans per hour per user

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_001",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## SDK Examples

### Python SDK

```python
from debugging_client import DebuggingClient

client = DebuggingClient(
    base_url='http://localhost:8000',
    token='your-jwt-token'
)

# Start workflow
workflow = client.start_workflow(
    workflow_type='login',
    metadata={'username': 'testuser'}
)

# Add trace step
client.add_trace_step(
    workflow_id=workflow.id,
    layer='api',
    component='AuthView',
    operation='authenticate_user'
)

# Record performance metric
client.record_metric(
    correlation_id=workflow.correlation_id,
    layer='api',
    component='AuthView',
    metric_name='response_time',
    metric_value=120.5
)

# Complete workflow
client.complete_workflow(workflow.id)
```

### JavaScript SDK

```javascript
import { DebuggingClient } from '@debugging/client';

const client = new DebuggingClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// Start workflow
const workflow = await client.startWorkflow({
  workflowType: 'login',
  metadata: { username: 'testuser' }
});

// Add trace step
await client.addTraceStep({
  workflowId: workflow.id,
  layer: 'frontend',
  component: 'LoginForm',
  operation: 'form_submit'
});

// Record performance metric
await client.recordMetric({
  correlationId: workflow.correlationId,
  layer: 'frontend',
  component: 'LoginForm',
  metricName: 'render_time',
  metricValue: 150.5
});

// Complete workflow
await client.completeWorkflow(workflow.id);
```