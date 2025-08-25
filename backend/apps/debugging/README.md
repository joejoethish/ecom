# API Validation Engine

The API Validation Engine is a comprehensive tool for discovering, analyzing, and testing Django REST API endpoints automatically.

## Features

- **Automatic API Discovery**: Scans Django URL patterns to discover all API endpoints
- **Schema Analysis**: Extracts request/response schemas from DRF serializers
- **Authentication Testing**: Tests endpoints with and without authentication
- **Automated Validation**: Generates test payloads and validates API responses
- **Performance Monitoring**: Measures response times for all endpoints
- **Health Checks**: Quick validation of critical API endpoints
- **Comprehensive Reporting**: Detailed validation reports in multiple formats

## Components

### APIDiscoveryService
Discovers and analyzes Django REST API endpoints:
- Scans URL patterns recursively
- Extracts HTTP methods, authentication requirements, and permissions
- Analyzes serializers to generate request/response schemas
- Maps DRF field types to JSON schema types

### APIValidationService
Validates discovered endpoints:
- Creates test users and JWT tokens for authentication testing
- Converts Django URL patterns to testable URLs
- Generates test payloads based on serializer schemas
- Tests endpoints with various scenarios (authenticated/unauthenticated)
- Measures response times and validates status codes

### APIValidationEngine
Main orchestrator that combines discovery and validation:
- Runs complete validation workflows
- Generates comprehensive reports
- Provides summary statistics and failure analysis

## Usage

### Django Management Command

```bash
# Run full API validation
python manage.py validate_apis

# Validate specific endpoint
python manage.py validate_apis --endpoint /api/v1/products/

# Run health check on critical endpoints
python manage.py validate_apis --health-check

# Output results as JSON
python manage.py validate_apis --output json

# Save results to file
python manage.py validate_apis --output file --file validation_report.json
```

### Programmatic Usage

```python
from apps.debugging.api_validation import (
    validate_all_apis,
    get_api_endpoints,
    test_single_endpoint,
    check_api_health
)

# Run full validation
results = validate_all_apis()

# Get all discovered endpoints
endpoints = get_api_endpoints()

# Test single endpoint
result = test_single_endpoint('/api/v1/products/', 'GET', authenticated=False)

# Quick health check
health = check_api_health()
```

### Middleware Integration

Add the validation middleware to track API calls in real-time:

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'apps.debugging.api_validation.APIValidationMiddleware',
]
```

## Configuration

The validation engine works with standard Django and DRF configurations. Key settings:

- `REST_FRAMEWORK`: DRF configuration for authentication and permissions
- `DJANGO_SETTINGS_MODULE`: Django settings module
- Database configuration for test user creation

## Output Formats

### Console Output
Human-readable summary with success rates and failure details.

### JSON Output
Structured data suitable for integration with other tools:

```json
{
  "summary": {
    "total_endpoints": 25,
    "total_tests": 50,
    "successful_tests": 48,
    "failed_tests": 2,
    "success_rate": 96.0,
    "average_response_time": 0.125
  },
  "endpoints": [...],
  "test_results": [...],
  "failed_tests": [...]
}
```

## Testing

The engine includes comprehensive unit and integration tests:

```bash
# Run all tests
python manage.py test apps.debugging.tests

# Run specific test classes
python manage.py test apps.debugging.tests.test_integration
```

## Error Handling

The validation engine handles various error scenarios:
- Missing serializers or view classes
- Authentication failures
- Network timeouts
- Invalid URL patterns
- Database connection issues

All errors are logged and included in validation reports for debugging.

## Performance Considerations

- Uses Django's test client for lightweight testing
- Reuses test users and JWT tokens across requests
- Implements connection pooling for database operations
- Provides configurable timeout settings
- Supports parallel validation for large API sets

## Integration with CI/CD

The validation engine can be integrated into CI/CD pipelines:

```bash
# In CI script
python manage.py validate_apis --output json --file api_validation.json
# Parse results and fail build if success rate < threshold
```

## Troubleshooting

Common issues and solutions:

1. **Import Errors**: Ensure Django settings are properly configured
2. **Database Errors**: Check database connectivity and permissions
3. **Authentication Errors**: Verify JWT configuration and user creation
4. **URL Pattern Errors**: Check Django URL configuration and routing
5. **Serializer Errors**: Ensure DRF serializers are properly defined

## Contributing

When adding new features:
1. Update the appropriate service class
2. Add comprehensive tests
3. Update documentation
4. Ensure backward compatibility
5. Follow Django and DRF best practices