# E-Commerce Platform API Documentation

## Overview

This directory contains comprehensive documentation for the E-Commerce Platform API. The API is designed to provide a complete set of endpoints for building e-commerce applications, including product management, order processing, payment integration, and more.

## Documentation Structure

- **[Authentication Guide](authentication_guide.md)**: How to authenticate with the API
- **[Error Handling Guide](error_handling.md)**: How errors are handled and reported
- **[Usage Guide](usage_guide.md)**: General API usage guidelines and best practices
- **[Versioning Guide](versioning_guide.md)**: How API versioning works and how to use different versions

## API Documentation Tools

The API documentation is available through multiple interfaces:

1. **Swagger UI**: Interactive API documentation with request/response examples
   - URL: `/api/docs/`

2. **ReDoc**: Alternative API documentation with a different UI
   - URL: `/api/redoc/`

3. **OpenAPI Schema**: Raw OpenAPI schema in JSON format
   - URL: `/api/schema/`

4. **OpenAPI Schema (YAML)**: Raw OpenAPI schema in YAML format
   - URL: `/api/schema.yaml`

## API Versioning

The API supports multiple versions to ensure backward compatibility while allowing for new features and improvements. Currently, the following versions are supported:

- **v1**: Legacy API (Deprecated)
- **v2**: Current API (Recommended)

For more information on API versioning, see the [Versioning Guide](versioning_guide.md).

## Authentication

The API uses JWT (JSON Web Token) for authentication. To authenticate:

1. Obtain a token by sending a POST request to `/api/{version}/auth/login/` with your credentials
2. Include the token in the `Authorization` header of subsequent requests using the format: `Bearer {token}`

For more information on authentication, see the [Authentication Guide](authentication_guide.md).

## Error Handling

All API errors follow a consistent format:

```json
{
  "error": {
    "message": "A human-readable error message",
    "code": "error_code",
    "field": "field_name"  // Optional, included for validation errors
  }
}
```

For more information on error handling, see the [Error Handling Guide](error_handling.md).

## API Endpoints

The API provides endpoints for the following resources:

- **Authentication**: User registration, login, and token management
- **Products**: Product management, categories, and attributes
- **Orders**: Order processing, tracking, and management
- **Cart**: Shopping cart management
- **Customers**: Customer management and profiles
- **Payments**: Payment processing and management
- **Shipping**: Shipping and logistics
- **Sellers**: Multi-vendor seller management
- **Analytics**: Analytics and reporting
- **Content**: Content management (banners, carousels)
- **Reviews**: Product reviews and ratings
- **Search**: Advanced search and filtering
- **Notifications**: Notification management

For detailed information on specific endpoints, refer to the Swagger/OpenAPI documentation at `/api/docs/` or `/api/redoc/`.

## Testing the API

You can test the API using tools like cURL, Postman, or any HTTP client. Here's an example of how to authenticate and make a request using cURL:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'

# Use the token to make a request
curl -X GET http://localhost:8000/api/v2/products/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## API Client Libraries

The API can be used with any HTTP client library. Here are some examples:

### JavaScript (Fetch API)

```javascript
// Login to get token
async function login(email, password) {
  const response = await fetch('/api/v2/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  return response.json();
}

// Make authenticated request
async function fetchProducts() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/v2/products/', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return response.json();
}
```

### Python (Requests)

```python
import requests

# Login to get token
def login(email, password):
    response = requests.post(
        'http://localhost:8000/api/v2/auth/login/',
        json={'email': email, 'password': password}
    )
    return response.json()

# Make authenticated request
def fetch_products(token):
    response = requests.get(
        'http://localhost:8000/api/v2/products/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()
```

## Support

If you encounter any issues or have questions about the API, please contact our support team at api-support@example.com.