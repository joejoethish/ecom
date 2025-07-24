# Authentication Guide

## Overview

This guide provides detailed information on how to authenticate with the E-Commerce Platform API. The API uses JWT (JSON Web Token) for authentication, which provides a secure and stateless authentication mechanism.

## Authentication Flow

1. **Register a new user** (if you don't have an account)
2. **Login to get access and refresh tokens**
3. **Use the access token for API requests**
4. **Refresh the access token when it expires**
5. **Logout to invalidate tokens**

## Endpoints

### Register

```http
POST /api/v2/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Response:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "date_joined": "2023-01-01T12:00:00Z"
}
```

### Login

```http
POST /api/v2/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Refresh Token

```http
POST /api/v2/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Logout

```http
POST /api/v2/auth/logout/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**

```json
{
  "detail": "Successfully logged out."
}
```

## Using the Access Token

Include the access token in the `Authorization` header of your API requests:

```http
GET /api/v2/products/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Token Expiration

- Access tokens expire after 60 minutes
- Refresh tokens expire after 7 days
- When an access token expires, use the refresh token to get a new access token
- If the refresh token expires, the user must log in again

## Security Best Practices

1. **Store tokens securely**: Never store tokens in localStorage or cookies without proper security measures
2. **Use HTTPS**: Always use HTTPS for API requests to prevent token interception
3. **Implement token refresh**: Refresh access tokens before they expire
4. **Validate tokens**: Validate tokens on the server side before processing requests
5. **Implement logout**: Always implement logout functionality to invalidate tokens
6. **Handle token expiration**: Implement proper error handling for token expiration

## Common Authentication Errors

| Status Code | Error Code | Description | Solution |
|-------------|------------|-------------|----------|
| 401 | token_not_valid | Token is invalid or expired | Refresh the token or login again |
| 401 | authentication_failed | Authentication credentials were not provided | Include the Authorization header |
| 401 | invalid_token | Token is invalid | Check the token format |
| 401 | token_blacklisted | Token has been blacklisted | Login again to get a new token |

## Example Authentication Flow (JavaScript)

```javascript
// Login
async function login(email, password) {
  const response = await fetch('/api/v2/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const data = await response.json();
  
  // Store tokens securely
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  
  return data;
}

// Make authenticated request
async function fetchData(url) {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  
  if (response.status === 401) {
    // Token expired, try to refresh
    const refreshed = await refreshToken();
    if (refreshed) {
      return fetchData(url); // Retry with new token
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }
  
  return response.json();
}

// Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  try {
    const response = await fetch('/api/v2/auth/token/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return true;
  } catch (error) {
    return false;
  }
}

// Logout
async function logout() {
  const refreshToken = localStorage.getItem('refresh_token');
  const accessToken = localStorage.getItem('access_token');
  
  try {
    await fetch('/api/v2/auth/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });
  } finally {
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}
```

## Additional Authentication Methods

### Social Authentication

The API also supports authentication via social providers:

```http
POST /api/v2/auth/social/{provider}/
Content-Type: application/json

{
  "access_token": "social_provider_token"
}
```

Where `{provider}` can be:
- `google`
- `facebook`
- `apple`

### Two-Factor Authentication (2FA)

For enhanced security, the API supports two-factor authentication:

1. Enable 2FA:

```http
POST /api/v2/auth/2fa/enable/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

2. Verify 2FA:

```http
POST /api/v2/auth/2fa/verify/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "code": "123456"
}
```

## API Keys (For Service-to-Service Authentication)

For service-to-service authentication, the API supports API keys:

1. Generate an API key:

```http
POST /api/v2/auth/api-keys/
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

{
  "name": "Service Integration",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

2. Use the API key:

```http
GET /api/v2/products/
X-API-Key: api_key_value
```