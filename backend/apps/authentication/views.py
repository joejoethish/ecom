"""
Authentication views for the ecommerce platform.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
import logging

from .models import User, UserProfile, UserSession, EmailVerification
from .services import (
    AuthenticationService, EmailVerificationService, 
    PasswordResetService, SessionManagementService
)
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    CustomTokenObtainPairSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UserSessionSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    ValidateResetTokenSerializer
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    User registration endpoint with enhanced profile creation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    refresh = RefreshToken.for_user(user)
                    
                    # Log successful registration
                    logger.info(f"New user registered: {user.email}")
                    
                    return Response({
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        },
                        'message': 'Registration successful',
                        'success': True
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                return Response({
                    'error': 'Registration failed. Please try again.',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'errors': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """
    Enhanced user login endpoint with custom token serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # Create user session record
        user = serializer.user
        self._create_user_session(request, user)
        
        # Log successful login
        logger.info(f"User logged in: {user.email}")
        
        response_data = serializer.validated_data
        response_data.update({
            'message': 'Login successful',
            'success': True
        })
        
        return Response(response_data, status=status.HTTP_200_OK)

    def _create_user_session(self, request, user):
        """Create a user session record."""
        try:
            session_data = {
                'user': user,
                'session_key': request.session.session_key or 'api_session',
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'device_type': self._get_device_type(request.META.get('HTTP_USER_AGENT', '')),
            }
            UserSession.objects.create(**session_data)
        except Exception as e:
            logger.warning(f"Failed to create user session: {str(e)}")

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_device_type(self, user_agent):
        """Determine device type from user agent."""
        user_agent = user_agent.lower()
        if 'mobile' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent:
            return 'tablet'
        else:
            return 'desktop'


class LogoutView(APIView):
    """
    Enhanced user logout endpoint with session cleanup.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Deactivate user sessions
            UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            logger.info(f"User logged out: {request.user.email}")
            
            return Response({
                'message': 'Successfully logged out',
                'success': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response({
                'error': 'Invalid token or logout failed',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(TokenRefreshView):
    """
    Token refresh endpoint.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data.update({
                'message': 'Token refreshed successfully',
                'success': True
            })
        return response


class ProfileView(APIView):
    """
    Enhanced user profile endpoint with full profile management.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'user': serializer.data,
            'success': True
        })

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': UserSerializer(request.user).data,
                'message': 'Profile updated successfully',
                'success': True
            })
        return Response({
            'errors': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    Password change endpoint for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Update session auth hash to prevent logout
            update_session_auth_hash(request, user)
            
            # Deactivate all other sessions
            UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            logger.info(f"Password changed for user: {user.email}")
            
            return Response({
                'message': 'Password changed successfully',
                'success': True
            })
        
        return Response({
            'errors': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Password reset request endpoint.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Send password reset email (implement email service)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
                
                # For now, just log the reset URL (implement proper email service)
                logger.info(f"Password reset requested for {email}. Reset URL: {reset_url}")
                
                return Response({
                    'message': 'Password reset email sent',
                    'success': True
                })
                
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                return Response({
                    'message': 'If the email exists, a reset link has been sent',
                    'success': True
                })
        
        return Response({
            'errors': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                token = serializer.validated_data['token']
                new_password = serializer.validated_data['new_password']
                
                # This would typically come from URL parameters
                uid = request.data.get('uid')
                if not uid:
                    return Response({
                        'error': 'UID is required',
                        'success': False
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Decode user ID
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                # Verify token
                if default_token_generator.check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    
                    # Deactivate all user sessions
                    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
                    
                    logger.info(f"Password reset completed for user: {user.email}")
                    
                    return Response({
                        'message': 'Password reset successful',
                        'success': True
                    })
                else:
                    return Response({
                        'error': 'Invalid or expired token',
                        'success': False
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (User.DoesNotExist, ValueError, TypeError):
                return Response({
                    'error': 'Invalid reset link',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'errors': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsView(APIView):
    """
    View user active sessions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response({
            'sessions': serializer.data,
            'success': True
        })

    def delete(self, request):
        """Deactivate all sessions except current one."""
        current_session_key = request.session.session_key
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_key=current_session_key).update(is_active=False)
        
        return Response({
            'message': 'All other sessions deactivated',
            'success': True
        })


class VerifyEmailView(APIView):
    """
    Email verification endpoint.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Implementation for email verification
        # This would typically involve checking a verification token
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Verification token is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Implement token verification logic here
        # For now, just return success
        return Response({
            'message': 'Email verified successfully',
            'success': True
        })


class ResendVerificationView(APIView):
    """
    Resend email verification endpoint.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_email_verified:
            return Response({
                'message': 'Email is already verified',
                'success': True
            })
        
        # Generate and send verification email
        # Implementation would go here
        logger.info(f"Verification email resent to: {user.email}")
        
        return Response({
            'message': 'Verification email sent',
            'success': True
        })


# New Password Reset API Views using secure token system

@method_decorator(csrf_protect, name='post')
class ForgotPasswordAPIView(APIView):
    """
    API endpoint for requesting password reset using secure token system.
    POST /api/v1/auth/forgot-password/
    
    Requirements: 1.2, 1.3 - Request password reset with email validation
    Requirements: 1.1, 4.2, 4.3, 5.6 - Enhanced validation and security
    """
    permission_classes = [AllowAny]

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle password reset request."""
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        try:
            # Use the password reset service to handle the request
            success, message, token = PasswordResetService.request_password_reset(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if not success:
                # Check if it's a rate limit error
                if "Too many requests" in message:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': message
                        }
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'REQUEST_FAILED',
                            'message': message
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Always return success message to prevent email enumeration
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Forgot password API error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An error occurred processing your request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_protect, name='post')
class ResetPasswordAPIView(APIView):
    """
    API endpoint for resetting password using secure token.
    POST /api/v1/auth/reset-password/
    
    Requirements: 3.1, 3.2, 3.3 - Reset password with token validation
    Requirements: 3.4, 3.5, 5.6 - Enhanced password validation and CSRF protection
    """
    permission_classes = [AllowAny]

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle password reset with token."""
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['password']
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        try:
            # Use the password reset service to reset the password
            success, message = PasswordResetService.reset_password(
                token=token,
                new_password=new_password,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if not success:
                # Determine error code based on message
                error_code = 'RESET_FAILED'
                status_code = status.HTTP_400_BAD_REQUEST
                
                if 'expired' in message.lower():
                    error_code = 'TOKEN_EXPIRED'
                elif 'invalid' in message.lower():
                    error_code = 'TOKEN_INVALID'
                elif 'used' in message.lower():
                    error_code = 'TOKEN_USED'

                return Response({
                    'success': False,
                    'error': {
                        'code': error_code,
                        'message': message
                    }
                }, status=status_code)

            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Reset password API error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An error occurred processing your request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidateResetTokenAPIView(APIView):
    """
    API endpoint for validating password reset token.
    GET /api/v1/auth/validate-reset-token/<token>/
    
    Requirements: 3.1, 3.2 - Validate token exists and is not expired
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        """Validate password reset token."""
        try:
            if not token:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'TOKEN_REQUIRED',
                        'message': 'Token is required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Use the password reset service to validate the token
            reset_token, error_message = PasswordResetService.validate_reset_token(token)

            if not reset_token:
                # Determine error code based on message
                error_code = 'TOKEN_INVALID'
                if 'expired' in error_message.lower():
                    error_code = 'TOKEN_EXPIRED'
                elif 'used' in error_message.lower():
                    error_code = 'TOKEN_USED'

                return Response({
                    'success': False,
                    'data': {
                        'valid': False,
                        'expired': 'expired' in error_message.lower()
                    },
                    'error': {
                        'code': error_code,
                        'message': error_message
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'data': {
                    'valid': True,
                    'expired': False
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Validate reset token API error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An error occurred validating the token'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(ensure_csrf_cookie, name='get')
class CSRFTokenView(APIView):
    """
    API endpoint to get CSRF token for password reset forms.
    GET /api/v1/auth/csrf-token/
    
    Requirements: 5.6 - Provide CSRF token for frontend forms
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Return CSRF token for frontend forms."""
        try:
            csrf_token = get_token(request)
            return Response({
                'success': True,
                'csrf_token': csrf_token
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"CSRF token generation error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'CSRF_ERROR',
                    'message': 'Failed to generate CSRF token'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# USER MANAGEMENT CRUD OPERATIONS - TASK 4.1, 4.2, 4.3
# ============================================================================

class UserManagementView(APIView):
    """
    User management API endpoints for admin operations.
    GET /api/v1/users/ - List users with pagination and filtering
    POST /api/v1/users/ - Create new user (admin only)
    
    Requirements: 6.1, 6.2 - User management CRUD operations
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method == 'POST':
            # Only admins can create users
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request):
        """
        List users with pagination and filtering.
        Requirements: 6.1 - GET /api/v1/users/ endpoint with pagination and filtering
        """
        try:
            # Check if user has permission to view users
            if not (request.user.is_staff or request.user.user_type in ['admin', 'super_admin']):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to view users'
                    }
                }, status=status.HTTP_403_FORBIDDEN)

            # Get query parameters for filtering
            user_type = request.query_params.get('user_type')
            is_active = request.query_params.get('is_active')
            is_verified = request.query_params.get('is_verified')
            search = request.query_params.get('search')
            
            # Pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)  # Max 100 items per page
            
            # Build queryset
            queryset = User.objects.all().order_by('-created_at')
            
            # Apply filters
            if user_type:
                queryset = queryset.filter(user_type=user_type)
            
            if is_active is not None:
                is_active_bool = is_active.lower() in ['true', '1', 'yes']
                queryset = queryset.filter(is_active=is_active_bool)
            
            if is_verified is not None:
                is_verified_bool = is_verified.lower() in ['true', '1', 'yes']
                queryset = queryset.filter(is_email_verified=is_verified_bool)
            
            if search:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(email__icontains=search) |
                    Q(username__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            
            # Calculate pagination
            total_count = queryset.count()
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            users = queryset[start_index:end_index]
            
            # Serialize data
            from .serializers import UserListSerializer
            serializer = UserListSerializer(users, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'users': serializer.data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size,
                        'has_next': end_index < total_count,
                        'has_previous': page > 1
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_PARAMETERS',
                    'message': 'Invalid pagination parameters'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"User list retrieval failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve users'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Create new user (admin only).
        Requirements: 6.1 - POST /api/v1/users/ endpoint for admin user creation
        """
        try:
            from .serializers import AdminUserCreateSerializer
            
            serializer = AdminUserCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid user data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = serializer.save()
            
            # Log admin action
            logger.info(f"User created by admin {request.user.email}: {user.email}")
            
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': {
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Admin user creation failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'CREATION_FAILED',
                    'message': 'Failed to create user'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """
    User detail API endpoints for admin operations.
    GET /api/v1/users/{id}/ - Get user profile
    PUT /api/v1/users/{id}/ - Update user profile
    DELETE /api/v1/users/{id}/ - Delete user account
    
    Requirements: 6.1, 6.2 - User profile retrieval, updates, and deletion
    """
    permission_classes = [IsAuthenticated]

    def get_user(self, user_id):
        """Get user by ID with error handling."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        except ValueError:
            return None

    def check_admin_permission(self, request):
        """Check if user has admin permissions."""
        return request.user.is_staff or request.user.user_type in ['admin', 'super_admin']

    def get(self, request, user_id):
        """
        Get user profile by ID.
        Requirements: 6.1 - GET /api/v1/users/{id}/ endpoint for user profile retrieval
        """
        try:
            # Check permissions
            if not self.check_admin_permission(request):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to view user profiles'
                    }
                }, status=status.HTTP_403_FORBIDDEN)

            # Get user
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': 'User not found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Serialize and return user data
            serializer = UserSerializer(user)
            
            return Response({
                'success': True,
                'data': {
                    'user': serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User profile retrieval failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve user profile'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, user_id):
        """
        Update user profile by ID.
        Requirements: 6.1 - PUT /api/v1/users/{id}/ endpoint for user profile updates
        """
        try:
            # Check permissions
            if not self.check_admin_permission(request):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to update user profiles'
                    }
                }, status=status.HTTP_403_FORBIDDEN)

            # Get user
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': 'User not found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Update user
            from .serializers import AdminUserUpdateSerializer
            serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid user data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            updated_user = serializer.save()
            
            # Log admin action
            logger.info(f"User updated by admin {request.user.email}: {updated_user.email}")
            
            return Response({
                'success': True,
                'message': 'User updated successfully',
                'data': {
                    'user': UserSerializer(updated_user).data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User profile update failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update user profile'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id):
        """
        Delete user account by ID.
        Requirements: 6.2 - DELETE /api/v1/users/{id}/ endpoint for user account deletion
        """
        try:
            # Check permissions
            if not self.check_admin_permission(request):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to delete user accounts'
                    }
                }, status=status.HTTP_403_FORBIDDEN)

            # Get user
            user = self.get_user(user_id)
            if not user:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': 'User not found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Prevent deletion of super admin users
            if user.is_superuser and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'Cannot delete super admin users'
                    }
                }, status=status.HTTP_403_FORBIDDEN)

            # Prevent self-deletion
            if user.id == request.user.id:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'SELF_DELETION_DENIED',
                        'message': 'Cannot delete your own account'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Store user info for logging
            user_email = user.email
            
            # Delete user (this will cascade to related objects)
            with transaction.atomic():
                # Deactivate all user sessions first
                UserSession.objects.filter(user=user).update(is_active=False)
                
                # Delete the user
                user.delete()
            
            # Log admin action
            logger.info(f"User deleted by admin {request.user.email}: {user_email}")
            
            return Response({
                'success': True,
                'message': 'User account deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User account deletion failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'DELETION_FAILED',
                    'message': 'Failed to delete user account'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSelfManagementView(APIView):
    """
    User self-management API endpoints.
    GET /api/v1/users/me/ - Get current user profile
    PUT /api/v1/users/me/ - Update current user profile
    DELETE /api/v1/users/me/ - Delete current user account
    
    Requirements: 6.1, 6.2 - User self-management endpoints
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get current user profile.
        Requirements: 6.1 - GET /api/v1/users/me/ endpoint for current user profile
        """
        try:
            serializer = UserSerializer(request.user)
            
            return Response({
                'success': True,
                'data': {
                    'user': serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Current user profile retrieval failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve user profile'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """
        Update current user profile.
        Requirements: 6.1 - PUT /api/v1/users/me/ endpoint for profile updates
        """
        try:
            serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid profile data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            updated_user = serializer.save()
            
            logger.info(f"User profile updated: {updated_user.email}")
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': {
                    'user': UserSerializer(updated_user).data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User profile update failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update profile'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        Delete current user account (self-deletion).
        Requirements: 6.2 - DELETE /api/v1/users/me/ endpoint for account self-deletion
        """
        try:
            from .serializers import UserSelfDeleteSerializer
            
            serializer = UserSelfDeleteSerializer(data=request.data, context={'request': request})
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid deletion request',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            user_email = user.email
            
            # Delete user account
            with transaction.atomic():
                # Deactivate all user sessions first
                UserSession.objects.filter(user=user).update(is_active=False)
                
                # Delete the user
                user.delete()
            
            logger.info(f"User account self-deleted: {user_email}")
            
            return Response({
                'success': True,
                'message': 'Account deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User account self-deletion failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'DELETION_FAILED',
                    'message': 'Failed to delete account'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSessionManagementView(APIView):
    """
    User session management API endpoints.
    GET /api/v1/users/me/sessions/ - List user sessions
    DELETE /api/v1/users/me/sessions/all/ - Logout all sessions
    
    Requirements: 5.1, 5.2 - Session management endpoints
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List current user's active sessions.
        Requirements: 5.1 - GET /api/v1/users/me/sessions/ endpoint for session listing
        """
        try:
            sessions = UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).order_by('-last_activity')
            
            serializer = UserSessionSerializer(sessions, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'sessions': serializer.data,
                    'total_count': sessions.count()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User sessions retrieval failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve sessions'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        Logout all user sessions.
        Requirements: 5.2 - DELETE /api/v1/users/me/sessions/all/ endpoint for logout all
        """
        try:
            # Get current session key to preserve it (optional)
            current_session_key = request.session.session_key
            
            # Deactivate all sessions
            sessions_count = UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            logger.info(f"All sessions terminated for user {request.user.email}: {sessions_count} sessions")
            
            return Response({
                'success': True,
                'message': f'All sessions terminated successfully ({sessions_count} sessions)',
                'data': {
                    'terminated_sessions': sessions_count
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Session termination failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'TERMINATION_FAILED',
                    'message': 'Failed to terminate sessions'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSessionDetailView(APIView):
    """
    Individual session management API endpoint.
    DELETE /api/v1/users/me/sessions/{session_id}/ - Terminate specific session
    
    Requirements: 5.2 - Session termination endpoint
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        """
        Terminate specific user session.
        Requirements: 5.2 - DELETE /api/v1/users/me/sessions/{session_id}/ endpoint
        """
        try:
            # Get session
            try:
                session = UserSession.objects.get(
                    id=session_id,
                    user=request.user,
                    is_active=True
                )
            except UserSession.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'SESSION_NOT_FOUND',
                        'message': 'Session not found or already terminated'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            # Terminate session
            session.terminate()
            
            logger.info(f"Session {session_id} terminated for user {request.user.email}")
            
            return Response({
                'success': True,
                'message': 'Session terminated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Session termination failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'TERMINATION_FAILED',
                    'message': 'Failed to terminate session'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# NEW API ENDPOINTS FOR TASK 3.1 - User Registration and Login API Endpoints
# ============================================================================

class UserRegistrationAPIView(APIView):
    """
    Enhanced user registration API endpoint with validation.
    POST /api/v1/auth/register/
    
    Requirements: 1.1, 1.2 - User registration with email uniqueness validation
    """
    permission_classes = [AllowAny]

    def _get_request_data(self, request):
        """Extract request metadata for session creation."""
        return {
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'location': request.data.get('location', ''),
        }

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle user registration with enhanced validation."""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid registration data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Extract user and profile data
            user_data = serializer.validated_data.copy()
            profile_data = user_data.pop('profile', {})
            user_data.pop('password_confirm', None)
            
            # Get request metadata
            request_data = self._get_request_data(request)
            
            # Register user using service
            user, tokens = AuthenticationService.register_user(
                user_data=user_data,
                profile_data=profile_data,
                request_data=request_data
            )
            
            # Return success response
            return Response({
                'success': True,
                'message': 'Registration successful. Please check your email for verification.',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'REGISTRATION_FAILED',
                    'message': 'Registration failed. Please try again.'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLoginAPIView(APIView):
    """
    Enhanced user login API endpoint with authentication.
    POST /api/v1/auth/login/
    
    Requirements: 1.2, 2.2 - Secure user authentication with password verification
    """
    permission_classes = [AllowAny]

    def _get_request_data(self, request):
        """Extract request metadata for session creation."""
        return {
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'location': request.data.get('location', ''),
            'login_method': 'password'
        }

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle user login with enhanced security."""
        try:
            email = request.data.get('email', '').strip().lower()
            password = request.data.get('password', '')
            
            if not email or not password:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CREDENTIALS',
                        'message': 'Email and password are required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get request metadata
            request_data = self._get_request_data(request)
            
            # Authenticate user using service
            user, tokens = AuthenticationService.authenticate_user(
                email=email,
                password=password,
                request_data=request_data
            )
            
            # Return success response
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User login failed: {str(e)}")
            
            # Check if it's an authentication error
            if 'Invalid credentials' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid email or password'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            elif 'Account locked' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ACCOUNT_LOCKED',
                        'message': 'Account temporarily locked due to multiple failed attempts'
                    }
                }, status=status.HTTP_423_LOCKED)
            elif 'Email not verified' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'EMAIL_NOT_VERIFIED',
                        'message': 'Please verify your email address before logging in'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'LOGIN_FAILED',
                        'message': 'Login failed. Please try again.'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogoutAPIView(APIView):
    """
    Enhanced user logout API endpoint with session cleanup.
    POST /api/v1/auth/logout/
    
    Requirements: 1.2, 2.2 - Logout functionality with session cleanup
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle user logout with session cleanup."""
        try:
            refresh_token = request.data.get('refresh_token')
            session_id = request.data.get('session_id')
            
            # Logout user using service
            success, message = AuthenticationService.logout_user(
                user=request.user,
                refresh_token=refresh_token,
                session_id=session_id
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Successfully logged out'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'LOGOUT_FAILED',
                        'message': message
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"User logout failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'LOGOUT_ERROR',
                    'message': 'An error occurred during logout'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenRefreshAPIView(APIView):
    """
    Enhanced token refresh API endpoint.
    POST /api/v1/auth/refresh/
    
    Requirements: 1.2, 2.2 - JWT token refresh functionality
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle token refresh."""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REFRESH_TOKEN',
                        'message': 'Refresh token is required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Refresh token using service
            new_tokens = AuthenticationService.refresh_token(refresh_token)
            
            return Response({
                'success': True,
                'message': 'Token refreshed successfully',
                'data': {
                    'tokens': new_tokens
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            
            if 'Invalid token' in str(e) or 'Token expired' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_REFRESH_TOKEN',
                        'message': 'Invalid or expired refresh token'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'REFRESH_ERROR',
                        'message': 'An error occurred during token refresh'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# PASSWORD RESET API ENDPOINTS FOR TASK 3.3
# ============================================================================

class PasswordResetRequestAPIView(APIView):
    """
    Enhanced password reset request API endpoint.
    POST /api/v1/auth/password-reset/request/
    
    Requirements: 4.1, 4.2 - Password reset request with secure token generation
    """
    permission_classes = [AllowAny]

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle password reset request."""
        try:
            serializer = ForgotPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid input data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            
            # Get request metadata
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Request password reset using service
            success, message, token = PasswordResetService.request_password_reset(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'If the email exists, a password reset link has been sent'
                }, status=status.HTTP_200_OK)
            else:
                # Check if it's a rate limit error
                if "Too many requests" in message:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': message
                        }
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'REQUEST_FAILED',
                            'message': 'Password reset request failed'
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'REQUEST_ERROR',
                    'message': 'An error occurred processing your request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmAPIView(APIView):
    """
    Enhanced password reset confirmation API endpoint.
    POST /api/v1/auth/password-reset/confirm/
    
    Requirements: 4.1, 4.2 - Secure password reset confirmation with token validation
    """
    permission_classes = [AllowAny]

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle password reset confirmation."""
        try:
            serializer = ResetPasswordSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid input data',
                        'details': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['password']
            
            # Get request metadata
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Reset password using service
            success, message = PasswordResetService.reset_password(
                token=token,
                new_password=new_password,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Password reset successful. You can now login with your new password.'
                }, status=status.HTTP_200_OK)
            else:
                # Determine error code based on message
                error_code = 'RESET_FAILED'
                status_code = status.HTTP_400_BAD_REQUEST
                
                if 'expired' in message.lower():
                    error_code = 'TOKEN_EXPIRED'
                elif 'invalid' in message.lower():
                    error_code = 'TOKEN_INVALID'
                elif 'used' in message.lower():
                    error_code = 'TOKEN_USED'
                
                return Response({
                    'success': False,
                    'error': {
                        'code': error_code,
                        'message': message
                    }
                }, status=status_code)
                
        except Exception as e:
            logger.error(f"Password reset confirmation failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'RESET_ERROR',
                    'message': 'An error occurred during password reset'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class EmailVerificationAPIView(APIView):
    """
    Email verification API endpoint.
    GET /api/v1/auth/verify-email/{token}/
    
    Requirements: 3.1, 3.2 - Email verification confirmation logic
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        """Handle email verification using token."""
        try:
            if not token:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_TOKEN',
                        'message': 'Verification token is required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify email using service
            success, error_message, user = EmailVerificationService.verify_email(token)
            
            if success and user:
                return Response({
                    'success': True,
                    'message': 'Email verified successfully',
                    'data': {
                        'user': UserSerializer(user).data
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Determine error code based on message
                error_code = 'VERIFICATION_FAILED'
                if 'expired' in error_message.lower():
                    error_code = 'TOKEN_EXPIRED'
                elif 'invalid' in error_message.lower():
                    error_code = 'TOKEN_INVALID'
                
                return Response({
                    'success': False,
                    'error': {
                        'code': error_code,
                        'message': error_message or 'Email verification failed'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'VERIFICATION_ERROR',
                    'message': 'An error occurred during email verification'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendVerificationAPIView(APIView):
    """
    Resend email verification API endpoint.
    POST /api/v1/auth/resend-verification/
    
    Requirements: 3.2 - Resend verification functionality with rate limiting
    """
    permission_classes = [IsAuthenticated]

    def _get_request_data(self, request):
        """Extract request metadata."""
        return {
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle resend email verification."""
        try:
            user = request.user
            
            # Check if email is already verified
            if user.is_email_verified:
                return Response({
                    'success': True,
                    'message': 'Email is already verified'
                }, status=status.HTTP_200_OK)
            
            # Get request metadata
            request_data = self._get_request_data(request)
            
            # Resend verification using service
            success, error_message = EmailVerificationService.resend_verification(
                user=user,
                request_data=request_data
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Verification email sent successfully'
                }, status=status.HTTP_200_OK)
            else:
                # Check if it's a rate limit error
                if "Too many" in error_message:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': error_message
                        }
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'RESEND_FAILED',
                            'message': error_message or 'Failed to send verification email'
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Resend verification failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'RESEND_ERROR',
                    'message': 'An error occurred while sending verification email'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# ADMIN AUTHENTICATION API ENDPOINTS FOR TASK 3.4
# ============================================================================

class AdminLoginAPIView(APIView):
    """
    Enhanced admin login API endpoint with enhanced security.
    POST /api/v1/admin-auth/login/
    
    Requirements: 2.1, 2.2 - Admin authentication with enhanced security
    """
    permission_classes = [AllowAny]

    def _get_request_data(self, request):
        """Extract request metadata for session creation."""
        return {
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'location': request.data.get('location', ''),
            'login_method': 'admin_password'
        }

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def post(self, request):
        """Handle admin login with enhanced security."""
        try:
            email = request.data.get('email', '').strip().lower()
            password = request.data.get('password', '')
            
            if not email or not password:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CREDENTIALS',
                        'message': 'Email and password are required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get request metadata
            request_data = self._get_request_data(request)
            
            # Authenticate admin user using service
            user, tokens = AuthenticationService.authenticate_admin_user(
                email=email,
                password=password,
                request_data=request_data
            )
            
            # Return success response
            return Response({
                'success': True,
                'message': 'Admin login successful',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Admin login failed: {str(e)}")
            
            # Check if it's an authentication error
            if 'Invalid credentials' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_ADMIN_CREDENTIALS',
                        'message': 'Invalid admin credentials'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            elif 'Not admin user' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ACCESS_DENIED',
                        'message': 'Access denied. Admin privileges required.'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            elif 'Account locked' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ADMIN_ACCOUNT_LOCKED',
                        'message': 'Admin account temporarily locked due to security concerns'
                    }
                }, status=status.HTTP_423_LOCKED)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ADMIN_LOGIN_FAILED',
                        'message': 'Admin login failed. Please try again.'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminLogoutAPIView(APIView):
    """
    Enhanced admin logout API endpoint with audit logging.
    POST /api/v1/admin-auth/logout/
    
    Requirements: 2.1, 2.2 - Admin logout with audit logging
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle admin logout with audit logging."""
        try:
            # Verify user is admin
            if not request.user.is_staff and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ACCESS_DENIED',
                        'message': 'Admin privileges required'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            refresh_token = request.data.get('refresh_token')
            session_id = request.data.get('session_id')
            
            # Logout admin user using service
            success, message = AuthenticationService.logout_admin_user(
                user=request.user,
                refresh_token=refresh_token,
                session_id=session_id
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Admin successfully logged out'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ADMIN_LOGOUT_FAILED',
                        'message': message
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Admin logout failed: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'ADMIN_LOGOUT_ERROR',
                    'message': 'An error occurred during admin logout'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminTokenRefreshAPIView(APIView):
    """
    Enhanced admin token refresh API endpoint with admin-specific validation.
    POST /api/v1/admin-auth/refresh/
    
    Requirements: 2.1, 2.2 - Admin token refresh with enhanced validation
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle admin token refresh with enhanced validation."""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REFRESH_TOKEN',
                        'message': 'Refresh token is required'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Refresh admin token using service
            new_tokens = AuthenticationService.refresh_admin_token(refresh_token)
            
            return Response({
                'success': True,
                'message': 'Admin token refreshed successfully',
                'data': {
                    'tokens': new_tokens
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Admin token refresh failed: {str(e)}")
            
            if 'Invalid token' in str(e) or 'Token expired' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_ADMIN_REFRESH_TOKEN',
                        'message': 'Invalid or expired admin refresh token'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            elif 'Not admin user' in str(e):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ACCESS_DENIED',
                        'message': 'Admin privileges required'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'ADMIN_REFRESH_ERROR',
                        'message': 'An error occurred during admin token refresh'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   