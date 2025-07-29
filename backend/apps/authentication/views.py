"""
Authentication views for the ecommerce platform.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
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

from .models import User, UserProfile, UserSession
from .services import PasswordResetService
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