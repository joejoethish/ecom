# Error Handling Guide

## Overview

This guide provides detailed information on how errors are handled in the E-Commerce Platform API. Understanding error responses is crucial for building robust applications that can gracefully handle failures.

## Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "message": "A human-readable error message",
    "code": "error_code",
    "field": "field_name",  // Optional, included for validation errors
    "details": {}  // Optional, additional error details
  }
}
```

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the success or failure of requests:

| Status Code | Category | Description |
|-------------|----------|-------------|
| 200 | Success | Request succeeded |
| 201 | Success | Resource created successfully |
| 204 | Success | Request succeeded, no content returned |
| 400 | Client Error | Bad request (validation error, malformed request) |
| 401 | Client Error | Unauthorized (authentication required) |
| 403 | Client Error | Forbidden (insufficient permissions) |
| 404 | Client Error | Resource not found |
| 405 | Client Error | Method not allowed |
| 409 | Client Error | Conflict (resource already exists) |
| 422 | Client Error | Unprocessable entity (validation error) |
| 429 | Client Error | Too many requests (rate limit exceeded) |
| 500 | Server Error | Internal server error |
| 502 | Server Error | Bad gateway |
| 503 | Server Error | Service unavailable |

## Common Error Codes

### Authentication Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 401 | authentication_required | Authentication credentials were not provided |
| 401 | invalid_credentials | Invalid username/password |
| 401 | token_not_valid | Token is invalid or expired |
| 401 | token_blacklisted | Token has been blacklisted |

### Permission Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 403 | permission_denied | User does not have permission to perform this action |
| 403 | not_authenticated | User is not authenticated |
| 403 | account_disabled | User account is disabled |

### Validation Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | validation_error | Request validation failed |
| 400 | invalid_input | Invalid input data |
| 400 | required_field | Required field is missing |
| 400 | invalid_format | Field format is invalid |

### Resource Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 404 | not_found | Resource not found |
| 409 | already_exists | Resource already exists |
| 410 | gone | Resource no longer available |

### Business Logic Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | insufficient_stock | Insufficient stock available |
| 400 | invalid_coupon | Coupon code is invalid or expired |
| 400 | payment_failed | Payment processing failed |
| 400 | order_already_processed | Order has already been processed |

### Rate Limiting Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 429 | rate_limit_exceeded | Rate limit exceeded |
| 429 | too_many_requests | Too many requests |

### Server Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 500 | server_error | Internal server error |
| 502 | bad_gateway | Bad gateway |
| 503 | service_unavailable | Service temporarily unavailable |

## Validation Error Format

Validation errors include additional information about which fields failed validation:

```json
{
  "error": {
    "message": "Validation error",
    "code": "validation_error",
    "fields": {
      "email": ["Enter a valid email address."],
      "password": ["Password must be at least 8 characters long."]
    }
  }
}
```

## Error Handling Best Practices

1. **Check HTTP status codes**: Always check the HTTP status code first
2. **Parse error responses**: Parse the error response to get detailed information
3. **Handle specific error codes**: Implement specific handling for common error codes
4. **Display user-friendly messages**: Translate error codes to user-friendly messages
5. **Log errors**: Log errors for debugging and monitoring
6. **Implement retry logic**: Implement retry logic for transient errors (e.g., 429, 503)
7. **Validate input**: Validate input before sending requests to avoid validation errors

## Example Error Handling (JavaScript)

```javascript
async function makeApiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      // Parse error response
      const errorData = await response.json();
      
      // Handle specific error codes
      switch (response.status) {
        case 401:
          // Handle authentication errors
          if (errorData.error.code === 'token_not_valid') {
            // Try to refresh token
            const refreshed = await refreshToken();
            if (refreshed) {
              // Retry with new token
              return makeApiRequest(url, {
                ...options,
                headers: {
                  ...options.headers,
                  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
              });
            } else {
              // Redirect to login
              window.location.href = '/login';
              throw new Error('Session expired. Please login again.');
            }
          }
          break;
        
        case 403:
          // Handle permission errors
          throw new Error('You do not have permission to perform this action.');
        
        case 404:
          // Handle not found errors
          throw new Error('The requested resource was not found.');
        
        case 429:
          // Handle rate limiting
          const retryAfter = response.headers.get('Retry-After');
          throw new Error(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
        
        case 400:
          // Handle validation errors
          if (errorData.error.fields) {
            const fieldErrors = Object.entries(errorData.error.fields)
              .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
              .join('; ');
            throw new Error(`Validation error: ${fieldErrors}`);
          } else {
            throw new Error(errorData.error.message || 'Invalid request');
          }
        
        default:
          // Handle other errors
          throw new Error(errorData.error.message || 'An error occurred');
      }
    }
    
    return response.json();
  } catch (error) {
    // Log error
    console.error('API request failed:', error);
    
    // Re-throw error
    throw error;
  }
}
```

## Common Error Scenarios and Solutions

### Authentication Errors

**Scenario**: Token expired
**Solution**: Refresh the token or redirect to login

```javascript
if (error.code === 'token_not_valid') {
  const refreshed = await refreshToken();
  if (refreshed) {
    // Retry request with new token
  } else {
    // Redirect to login
  }
}
```

### Validation Errors

**Scenario**: Form submission with invalid data
**Solution**: Display field-specific error messages

```javascript
if (error.code === 'validation_error' && error.fields) {
  Object.entries(error.fields).forEach(([field, errors]) => {
    // Display error for each field
    displayFieldError(field, errors[0]);
  });
}
```

### Rate Limiting Errors

**Scenario**: Too many requests
**Solution**: Implement exponential backoff

```javascript
if (error.code === 'rate_limit_exceeded') {
  const retryAfter = parseInt(response.headers.get('Retry-After') || '1');
  await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
  // Retry request
}
```

### Resource Not Found Errors

**Scenario**: Accessing a deleted resource
**Solution**: Handle gracefully and update UI

```javascript
if (error.code === 'not_found') {
  // Remove item from UI
  removeItemFromList(itemId);
  // Show notification
  showNotification('Item no longer exists');
}
```

### Server Errors

**Scenario**: Internal server error
**Solution**: Retry with exponential backoff for transient errors

```javascript
if (response.status >= 500) {
  // Implement exponential backoff
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      return await makeApiRequest(url, options);
    } catch (retryError) {
      if (attempt === 2) throw retryError;
    }
  }
}
```

## Error Monitoring and Reporting

The API includes error monitoring and reporting features:

1. **Error IDs**: Each server error includes a unique error ID for tracking
2. **Error Reporting**: You can report errors to help improve the API
3. **Status Page**: Check the API status page for known issues

### Reporting Errors

```http
POST /api/v2/errors/report/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Error occurred when processing payment",
  "steps_to_reproduce": "1. Add item to cart\n2. Proceed to checkout\n3. Select payment method\n4. Click Pay"
}
```