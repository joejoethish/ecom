# Authentication Workflow Guide

## Overview
This guide provides a complete overview of the authentication system implementation and testing procedures for the e-commerce platform.

## 🏗️ Architecture

### Backend (Django REST API)
- **Location**: `backend/apps/authentication/`
- **Framework**: Django REST Framework with SimpleJWT
- **Database**: MySQL with User, UserProfile, UserSession models
- **Endpoints**: Registration, Login, Logout, Profile, Password Reset

### Frontend (Next.js)
- **Location**: `frontend/src/components/auth/` and `frontend/src/app/auth/`
- **Framework**: Next.js 15 with React 19
- **State Management**: Redux Toolkit
- **API Client**: Custom axios-based client with token refresh

## 🔧 Components

### Backend Components
1. **Models** (`backend/apps/authentication/models.py`)
   - User (extends AbstractUser)
   - UserProfile (additional user data)
   - UserSession (session tracking)
   - EmailVerification (email verification tokens)

2. **Views** (`backend/apps/authentication/views.py`)
   - RegisterView - User registration
   - LoginView - User authentication
   - LogoutView - Session termination
   - ProfileView - User profile management
   - Password reset views

3. **Serializers** (`backend/apps/authentication/serializers.py`)
   - UserRegistrationSerializer
   - CustomTokenObtainPairSerializer
   - Password reset serializers

### Frontend Components
1. **Auth Components** (`frontend/src/components/auth/`)
   - LoginForm.tsx - User login interface
   - RegisterForm.tsx - User registration interface
   - ForgotPasswordForm.tsx - Password reset request
   - ResetPasswordForm.tsx - Password reset confirmation
   - EmailVerificationPage.tsx - Email verification

2. **Redux Store** (`frontend/src/store/slices/authSlice.ts`)
   - Authentication state management
   - Async thunks for API calls
   - Token management

3. **API Client** (`frontend/src/utils/api.ts`)
   - Axios configuration
   - Token refresh interceptors
   - Error handling

## 🚀 Testing the Authentication Workflow

### Prerequisites
1. **Backend Server**: Django development server running
2. **Frontend Server**: Next.js development server running
3. **Database**: MySQL database with migrations applied

### Step 1: Start the Backend Server
```bash
cd backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### Step 2: Start the Frontend Server
```bash
cd frontend
npm install
npm run dev
```

### Step 3: Access the Authentication Demo
Navigate to: `http://localhost:3000/auth-demo`

This page provides a comprehensive testing interface for:
- ✅ User Registration
- ✅ User Login
- ✅ Protected Endpoint Access
- ✅ Forgot Password
- ✅ Token Management

### Step 4: Test Registration
1. Fill out the registration form with:
   - Username: `testuser123`
   - Email: `test@example.com`
   - Password: `TestPassword123!`
   - Confirm Password: `TestPassword123!`
   - Phone: `+1234567890` (optional)
   - User Type: `Customer`

2. Click "Register"
3. Check for success message and token display

### Step 5: Test Login
1. Switch to the "Login" tab
2. Enter the registered credentials:
   - Email: `test@example.com`
   - Password: `TestPassword123!`

3. Click "Login"
4. Check for success message and token display

### Step 6: Test Protected Endpoint
1. After successful login, click "Test Protected Endpoint"
2. Verify that the user profile is fetched successfully

### Step 7: Test Forgot Password
1. Switch to the "Forgot Password" tab
2. Enter the registered email
3. Click "Send Reset Email"
4. Check for success message

## 🔍 API Endpoints

### Authentication Endpoints
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/refresh/` - Token refresh
- `GET /api/v1/auth/profile/` - Get user profile
- `PUT /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/forgot-password/` - Request password reset
- `POST /api/v1/auth/reset-password/` - Confirm password reset

### Request/Response Examples

#### Registration Request
```json
{
  "username": "testuser123",
  "email": "test@example.com",
  "password": "TestPassword123!",
  "password_confirm": "TestPassword123!",
  "user_type": "customer",
  "phone_number": "+1234567890"
}
```

#### Registration Response
```json
{
  "user": {
    "id": 1,
    "username": "testuser123",
    "email": "test@example.com",
    "user_type": "customer"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Registration successful",
  "success": true
}
```

#### Login Request
```json
{
  "email": "test@example.com",
  "password": "TestPassword123!"
}
```

#### Login Response
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "testuser123",
    "email": "test@example.com"
  },
  "message": "Login successful",
  "success": true
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend Server Not Running**
   - Error: "Network error. Please check if the backend server is running."
   - Solution: Start Django server with `python manage.py runserver`

2. **Database Connection Issues**
   - Error: Database connection errors
   - Solution: Check MySQL service and database configuration

3. **CORS Issues**
   - Error: CORS policy blocks requests
   - Solution: Verify CORS settings in Django settings

4. **Token Refresh Issues**
   - Error: Token refresh fails
   - Solution: Check JWT settings and token expiration

### Debug Steps
1. Check Django server logs for backend errors
2. Check browser console for frontend errors
3. Verify API endpoints with tools like Postman
4. Check database for user records
5. Verify JWT token format and expiration

## 📝 Test Results Summary

### Expected Test Results
- ✅ User registration creates new user record
- ✅ Login returns valid JWT tokens
- ✅ Protected endpoints require authentication
- ✅ Token refresh works automatically
- ✅ Password reset sends email (if configured)
- ✅ User sessions are tracked
- ✅ Logout invalidates tokens

### Performance Metrics
- Registration: < 2 seconds
- Login: < 1 second
- Profile fetch: < 500ms
- Token refresh: < 300ms

## 🔒 Security Features

1. **Password Security**
   - Minimum 8 characters
   - Must include uppercase, lowercase, and numbers
   - Hashed with Django's PBKDF2

2. **JWT Tokens**
   - Access token: 15 minutes expiration
   - Refresh token: 7 days expiration
   - Automatic refresh on API calls

3. **Session Management**
   - Track user sessions
   - Device and IP logging
   - Session termination on logout

4. **Rate Limiting**
   - Login attempt limits
   - Registration rate limits
   - Password reset limits

## 📊 Monitoring

### Logs to Monitor
- User registration events
- Login/logout events
- Failed authentication attempts
- Token refresh events
- Password reset requests

### Metrics to Track
- Registration conversion rate
- Login success rate
- Token refresh frequency
- Session duration
- Failed login attempts

## 🚀 Next Steps

1. **Email Integration**
   - Configure SMTP for email verification
   - Set up password reset emails
   - Add email templates

2. **Social Authentication**
   - Google OAuth integration
   - Facebook login
   - GitHub authentication

3. **Two-Factor Authentication**
   - SMS verification
   - TOTP authentication
   - Backup codes

4. **Advanced Security**
   - Device fingerprinting
   - Suspicious activity detection
   - Account lockout policies

## 📞 Support

For issues or questions about the authentication system:
1. Check the troubleshooting section above
2. Review Django and Next.js logs
3. Test with the authentication demo page
4. Verify database and server configuration

---

**Last Updated**: September 9, 2025
**Version**: 1.0.0