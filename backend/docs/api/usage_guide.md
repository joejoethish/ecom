# E-Commerce Platform API Usage Guide

## Introduction

Welcome to the E-Commerce Platform API documentation. This guide provides comprehensive information on how to use our API endpoints, authentication methods, error handling, and best practices.

## API Versioning

Our API uses URL-based versioning. All API endpoints are prefixed with `/api/{version}/` where `{version}` is the API version (e.g., `v1`, `v2`).

### Current Versions

- **v1**: Legacy API (Deprecated)
- **v2**: Current API (Recommended)

### Version Headers

In addition to URL-based versioning, you can also specify the API version using the following HTTP headers:

- `X-API-Version`: Specify the API version directly (e.g., `v2`)
- `Accept`: Use the format `application/vnd.api+json;version=v2`

URL-based versioning takes precedence over header-based versioning.

### Deprecation Notices

When an API version is deprecated, the following headers will be included in responses:

- `X-API-Deprecation-Warning`: Indicates that the API version is deprecated
- `X-API-Sunset-Date`: The date after which the API version will no longer be supported

## Authentication

### JWT Authentication

The API uses JWT (JSON Web Token) for authentication. To authenticate:

1. Obtain a token by sending a POST request to `/api/{version}/auth/login/` with your credentials
2. Include the token in the `Authorization` header of subsequent requests using the format: `Bearer {token}`

#### Example Authentication Flow

```http
# Step 1: Login to get token
POST /api/v2/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Step 2: Use the token in subsequent requests
GET /api/v2/products/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Refresh

Access tokens expire after 60 minutes. To get a new access token without re-authenticating:

```http
POST /api/v2/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Common Request/Response Formats

### Request Format

Most API endpoints accept JSON-formatted request bodies:

```http
POST /api/v2/products/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "name": "Product Name",
  "description": "Product description",
  "price": 99.99,
  "category": 1
}
```

### Response Format

Responses are returned in JSON format:

```json
{
  "id": 1,
  "name": "Product Name",
  "description": "Product description",
  "price": "99.99",
  "category": 1,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

### Collection Responses

Collection endpoints return paginated results:

```json
{
  "count": 100,
  "next": "http://example.com/api/v2/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Product 1",
      "price": "99.99"
    },
    {
      "id": 2,
      "name": "Product 2",
      "price": "149.99"
    }
  ]
}
```

## Error Handling

### Error Response Format

Error responses follow a consistent format:

```json
{
  "error": {
    "message": "Error message",
    "code": "error_code",
    "field": "field_name"  // Optional, included for validation errors
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | validation_error | Request validation failed |
| 401 | authentication_failed | Authentication failed |
| 403 | permission_denied | Permission denied |
| 404 | not_found | Resource not found |
| 429 | rate_limit_exceeded | Rate limit exceeded |
| 500 | server_error | Internal server error |

## Pagination

API endpoints that return collections support pagination using the following query parameters:

- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 20, max: 100)

Example:

```
GET /api/v2/products/?page=2&page_size=50
```

## Filtering and Sorting

### Filtering

Many collection endpoints support filtering using query parameters:

```
GET /api/v2/products/?category=1&price_min=10&price_max=100
```

### Sorting

Sort results using the `ordering` parameter:

```
GET /api/v2/products/?ordering=price  # Ascending order
GET /api/v2/products/?ordering=-price  # Descending order
```

## Rate Limiting

API requests are subject to rate limiting to ensure fair usage. The following headers are included in responses:

- `X-RateLimit-Limit`: Maximum number of requests allowed in the current period
- `X-RateLimit-Remaining`: Number of requests remaining in the current period
- `X-RateLimit-Reset`: Time when the rate limit will reset (Unix timestamp)

## Best Practices

1. **Use the latest API version**: Always use the latest API version for new integrations
2. **Implement token refresh**: Refresh access tokens before they expire
3. **Handle rate limiting**: Implement exponential backoff when rate limits are reached
4. **Use pagination**: Always use pagination for collection endpoints
5. **Validate responses**: Validate response data before processing
6. **Handle errors gracefully**: Implement proper error handling for all API requests
7. **Use HTTPS**: Always use HTTPS for API requests
8. **Minimize requests**: Use batch operations when available to minimize the number of requests

## API Endpoints Overview

For detailed information on specific endpoints, refer to the Swagger/OpenAPI documentation at `/api/docs/` or `/api/redoc/`.

### Authentication Endpoints

- `POST /api/v2/auth/register/`: Register a new user
- `POST /api/v2/auth/login/`: Login and get access token
- `POST /api/v2/auth/token/refresh/`: Refresh access token
- `POST /api/v2/auth/logout/`: Logout and invalidate token

### Product Endpoints

- `GET /api/v2/products/`: List products
- `POST /api/v2/products/`: Create a product
- `GET /api/v2/products/{id}/`: Get product details
- `PUT /api/v2/products/{id}/`: Update a product
- `DELETE /api/v2/products/{id}/`: Delete a product

### Category Endpoints

- `GET /api/v2/products/categories/`: List categories
- `POST /api/v2/products/categories/`: Create a category
- `GET /api/v2/products/categories/{id}/`: Get category details
- `PUT /api/v2/products/categories/{id}/`: Update a category
- `DELETE /api/v2/products/categories/{id}/`: Delete a category

### Order Endpoints

- `GET /api/v2/orders/`: List orders
- `POST /api/v2/orders/`: Create an order
- `GET /api/v2/orders/{id}/`: Get order details
- `PUT /api/v2/orders/{id}/`: Update an order
- `DELETE /api/v2/orders/{id}/`: Cancel an order

### Cart Endpoints

- `GET /api/v2/cart/`: Get cart contents
- `POST /api/v2/cart/items/`: Add item to cart
- `PUT /api/v2/cart/items/{id}/`: Update cart item
- `DELETE /api/v2/cart/items/{id}/`: Remove item from cart
- `POST /api/v2/cart/apply-coupon/`: Apply coupon to cart

## Webhooks

The API supports webhooks for real-time event notifications. To register a webhook:

```http
POST /api/v2/webhooks/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "url": "https://your-server.com/webhook",
  "events": ["order.created", "order.updated", "payment.succeeded"],
  "active": true
}
```

## Support

If you encounter any issues or have questions about the API, please contact our support team at api-support@example.com.