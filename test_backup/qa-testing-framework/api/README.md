# API Testing Module

This module provides comprehensive REST API testing infrastructure for the Django e-commerce platform. It includes authentication handling, request/response validation, performance monitoring, and load testing capabilities.

## Components

### 1. APITestClient (`client.py`)

A comprehensive HTTP client for API testing with the following features:

- **Authentication Support**: JWT, session-based, and API key authentication
- **Request Methods**: GET, POST, PUT, PATCH, DELETE with full parameter support
- **Response Handling**: Automatic JSON parsing, error handling, and metrics collection
- **Performance Tracking**: Response time monitoring and rate limiting detection
- **Assertion Methods**: Built-in assertion helpers for response validation

#### Usage Example:

```python
from api.client import APITestClient
from core.interfaces import Environment

# Initialize client
client = APITestClient('http://localhost:8000', Environment.DEVELOPMENT)

# Authenticate
client.authenticate_jwt('username', 'password')

# Make requests
response = client.get('/api/v1/products/')
client.assert_response_success(response)
client.assert_response_has_field(response, 'results')

# Check performance
metrics = client.get_performance_metrics()
print(f"Average response time: {metrics['avg_response_time']:.3f}s")
```

### 2. Response Validators (`validators.py`)

Comprehensive validation utilities for API responses:

- **Schema Validation**: JSON schema validation for users, products, orders
- **Security Validation**: Security header checks and sensitive data detection
- **Performance Validation**: Response time and payload size validation
- **CRUD Validation**: Operation-specific response validation

#### Usage Example:

```python
from api.validators import APIValidator

validator = APIValidator()
result = validator.validate_full_response(
    response,
    expected_schema='user',
    operation='CREATE',
    check_security=True,
    check_performance=True
)

if not result.is_valid:
    print("Validation errors:", result.errors)
```

### 3. Performance Testing (`performance.py`)

Load testing and performance monitoring capabilities:

- **Load Testing**: Configurable concurrent user simulation
- **Stress Testing**: Gradual load increase to find breaking points
- **Spike Testing**: Sudden load increase testing
- **Performance Monitoring**: Real-time endpoint monitoring

#### Usage Example:

```python
from api.performance import APIPerformanceTester, LoadTestConfig

tester = APIPerformanceTester('http://localhost:8000')

# Simple endpoint test
results = tester.test_endpoint_performance(
    '/api/v1/products/',
    concurrent_users=10,
    duration_seconds=60
)

print(f"Success rate: {results.success_rate:.1f}%")
print(f"Average response time: {results.get_response_time_stats()['mean']:.3f}s")
```

## Key Features

### Authentication Handling

The API client supports multiple authentication methods:

1. **JWT Authentication**: Automatic token management with refresh support
2. **Session Authentication**: Cookie-based authentication with CSRF handling
3. **API Key Authentication**: Header-based API key authentication

### Request/Response Validation

Comprehensive validation includes:

- JSON schema validation against predefined schemas
- Security header validation (OWASP recommendations)
- Performance threshold validation
- Business logic validation for CRUD operations

### Performance Monitoring

Built-in performance monitoring provides:

- Response time tracking and statistics
- Rate limiting detection and tracking
- Success/failure rate monitoring
- Performance threshold alerting

### Load Testing Capabilities

Advanced load testing features:

- Configurable concurrent user simulation
- Ramp-up and ramp-down phases
- Rate limiting and think time simulation
- Comprehensive metrics collection and reporting

## Testing Coverage

The module includes comprehensive unit tests:

- `test_api_client.py`: Tests for APITestClient functionality
- `test_validators.py`: Tests for all validation utilities
- `test_performance.py`: Tests for performance testing components
- `integration_test.py`: End-to-end integration testing

## Configuration

The module supports environment-specific configuration:

- Development: Local testing with detailed logging
- Staging: Production-like testing with performance monitoring
- Production: Limited testing with safety measures

## Requirements Satisfied

This implementation satisfies the following requirements from task 6.1:

✅ **Configure REST Assured for Django API endpoint testing**
- Implemented comprehensive APITestClient with full HTTP method support

✅ **Implement APITestClient with authentication handling**
- JWT, session, and API key authentication support
- Automatic token management and refresh

✅ **Create API request/response validation utilities**
- Schema validation for all major entity types
- Security and performance validation
- CRUD operation validation

✅ **Add API performance monitoring and load testing capabilities**
- Real-time performance monitoring
- Configurable load testing with multiple scenarios
- Comprehensive metrics collection and reporting

✅ **Write unit tests for API testing utilities**
- Complete test coverage for all components
- Integration tests demonstrating end-to-end functionality
- Mock-based testing for reliable test execution

## Next Steps

The API testing infrastructure is now ready for implementing specific test cases for:

1. Authentication and user management API tests (Task 6.2)
2. Product and order management API tests (Task 6.3)
3. Payment and transaction API tests (Task 6.4)

Each subsequent task will build upon this infrastructure to create comprehensive API test suites for the e-commerce platform.