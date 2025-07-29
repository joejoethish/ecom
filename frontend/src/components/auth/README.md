# Authentication System

This directory contains the complete authentication system for the ecommerce platform frontend.

## Components

### Core Components

- **LoginForm**: Complete login form with validation and error handling
- **RegisterForm**: Registration form supporting customer and seller account types
- **LogoutButton**: Reusable logout button component
- **UserProfile**: User profile display and editing component

### Route Protection

- **AuthGuard**: Main authentication guard component with flexible configuration
- **ProtectedRoute**: Wrapper for routes requiring authentication
- **GuestRoute**: Wrapper for guest-only routes (login/register pages)

### Providers

- **AuthProvider**: Initializes authentication state on app startup

## Redux Integration

### Auth Slice (`/store/slices/authSlice.ts`)

The authentication state is managed through Redux Toolkit with the following async thunks:

- `loginUser`: Handles user login
- `registerUser`: Handles user registration  
- `logoutUser`: Handles user logout
- `fetchUserProfile`: Fetches current user profile
- `updateUserProfile`: Updates user profile
- `initializeAuth`: Initializes auth state from stored tokens

### State Structure

```typescript
interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}
```

## Utilities

### Storage (`/utils/storage.ts`)
- Token management (get, set, remove)
- User data persistence
- Generic storage utilities

### Validation (`/utils/validation.ts`)
- Email validation
- Password strength validation
- Username validation
- Form validation helpers

### API Client (`/utils/api.ts`)
- Axios-based API client
- Automatic token attachment
- Token refresh handling
- Error handling

## Middleware

### Authentication Middleware (`/middleware/auth.ts`)
- Route protection at the Next.js middleware level
- Redirects for protected/guest routes
- Cookie-based authentication checking

## Hooks

### useAuth Hook (`/hooks/useAuth.ts`)
Custom hook providing:
- Authentication state
- User type helpers (isAdmin, isSeller, isCustomer)
- Error clearing functionality

## Usage Examples

### Basic Route Protection

```tsx
import { ProtectedRoute } from '@/components/auth';

function ProfilePage() {
  return (
    <ProtectedRoute>
      <div>Protected content</div>
    </ProtectedRoute>
  );
}
```

### Admin-Only Route

```tsx
import { ProtectedRoute } from '@/components/auth';

function AdminPage() {
  return (
    <ProtectedRoute allowedUserTypes={['admin']}>
      <div>Admin only content</div>
    </ProtectedRoute>
  );
}
```

### Using Auth Hook

```tsx
import { useAuth } from '@/hooks/useAuth';

function MyComponent() {
  const { user, isAuthenticated, isAdmin } = useAuth();
  
  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }
  
  return (
    <div>
      Welcome, {user?.username}!
      {isAdmin && <div>Admin panel access</div>}
    </div>
  );
}
```

### Manual Authentication Check

```tsx
import { AuthGuard } from '@/components/auth';

function CustomComponent() {
  return (
    <AuthGuard
      requireAuth={true}
      allowedUserTypes={['seller', 'admin']}
      redirectTo="/unauthorized"
      fallback={<div>Loading...</div>}
    >
      <div>Seller/Admin content</div>
    </AuthGuard>
  );
}
```

## Features

✅ **Complete Authentication Flow**
- Login/Register/Logout
- Token-based authentication
- Automatic token refresh
- Persistent sessions

✅ **Route Protection**
- Middleware-level protection
- Component-level guards
- Role-based access control

✅ **User Management**
- Profile viewing/editing
- User type support (customer/seller/admin)
- Account verification status

✅ **Form Validation**
- Client-side validation
- Real-time error feedback
- Comprehensive validation rules

✅ **Error Handling**
- API error handling
- Network error handling
- User-friendly error messages

✅ **TypeScript Support**
- Full type safety
- Comprehensive interfaces
- Type-safe Redux integration

✅ **Testing Ready**
- Jest/React Testing Library setup
- Mock utilities included
- Example test cases

## Security Features

- JWT token management
- Automatic token refresh
- Secure token storage
- CSRF protection ready
- Input validation and sanitization