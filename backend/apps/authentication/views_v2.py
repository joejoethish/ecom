"""
Authentication views for API v2 with enhanced features and backward compatibility.
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from core.versioning import VersionedViewMixin, VersionedSerializerMixin
from .serializers_v2 import (
    UserSerializerV2, RegisterSerializerV2, LoginSerializerV2, PasswordChangeSerializerV2
)
from .views import (
    RegisterView as RegisterViewV1,
    LoginView as LoginViewV1,
    LogoutView as LogoutViewV1,
    RefreshTokenView as RefreshTokenViewV1,
    ProfileView as ProfileViewV1,
    PasswordChangeView as PasswordChangeViewV1,
    PasswordResetRequestView as PasswordResetRequestViewV1,
    PasswordResetConfirmView as PasswordResetConfirmViewV1,
    VerifyEmailView as VerifyEmailViewV1,
    ResendVerificationView as ResendVerificationViewV1,
    UserSessionsView as UserSessionsViewV1
)


class RegisterViewV2(RegisterViewV1, VersionedViewMixin, VersionedSerializerMixin):
    """
    Enhanced registration view for API v2.
    """
    serializer_class_map = {
        'v1': RegisterViewV1.serializer_class,
        'v2': RegisterSerializerV2
    }
    
    def get_serializer_class(self):
        """Return version-specific serializer."""
        version = self.get_version()
        return self.serializer_class_map.get(version, RegisterSerializerV2)
    
    def post(self, request, *args, **kwargs):
        """Handle registration with version-specific behavior."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # V2 specific: Return more detailed user info
        if self.is_version('v2'):
            return Response({
                'user': UserSerializerV2(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        
        # V1 fallback
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)


class LoginViewV2(LoginViewV1, VersionedViewMixin, VersionedSerializerMixin):
    """
    Enhanced login view for API v2.
    """
    serializer_class_map = {
        'v1': LoginViewV1.serializer_class,
        'v2': LoginSerializerV2
    }
    
    def get_serializer_class(self):
        """Return version-specific serializer."""
        version = self.get_version()
        return self.serializer_class_map.get(version, LoginSerializerV2)
    
    def post(self, request, *args, **kwargs):
        """Handle login with version-specific behavior."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.update_last_login()
        
        # V2 specific: Return more detailed user info and handle remember_me
        if self.is_version('v2'):
            remember_me = serializer.validated_data.get('remember_me', False)
            
            # Extend token lifetime for remember_me
            if remember_me:
                from datetime import timedelta
                refresh.set_exp(lifetime=timedelta(days=30))
            
            return Response({
                'user': UserSerializerV2(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Login successful'
            })
        
        # V1 fallback
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class ProfileViewV2(ProfileViewV1, VersionedViewMixin, VersionedSerializerMixin):
    """
    Enhanced profile view for API v2.
    """
    serializer_class_map = {
        'v1': ProfileViewV1.serializer_class,
        'v2': UserSerializerV2
    }
    
    def get_serializer_class(self):
        """Return version-specific serializer."""
        version = self.get_version()
        return self.serializer_class_map.get(version, UserSerializerV2)
    
    def get(self, request, *args, **kwargs):
        """Get user profile with version-specific behavior."""
        serializer = self.get_serializer(request.user)
        
        # V2 specific: Include additional user data
        if self.is_version('v2'):
            from django.utils import timezone
            
            # Get user activity data
            last_login = request.user.last_login or request.user.date_joined
            days_since_login = (timezone.now() - last_login).days
            
            return Response({
                'user': serializer.data,
                'activity': {
                    'last_login': last_login,
                    'days_since_login': days_since_login,
                    'is_recently_active': days_since_login < 7
                }
            })
        
        # V1 fallback
        return Response(serializer.data)


class PasswordChangeViewV2(PasswordChangeViewV1, VersionedViewMixin, VersionedSerializerMixin):
    """
    Enhanced password change view for API v2.
    """
    serializer_class_map = {
        'v1': PasswordChangeViewV1.serializer_class,
        'v2': PasswordChangeSerializerV2
    }
    
    def get_serializer_class(self):
        """Return version-specific serializer."""
        version = self.get_version()
        return self.serializer_class_map.get(version, PasswordChangeSerializerV2)


# Use v1 implementations for other views
LogoutViewV2 = LogoutViewV1
RefreshTokenViewV2 = RefreshTokenViewV1
PasswordResetRequestViewV2 = PasswordResetRequestViewV1
PasswordResetConfirmViewV2 = PasswordResetConfirmViewV1
VerifyEmailViewV2 = VerifyEmailViewV1
ResendVerificationViewV2 = ResendVerificationViewV1
UserSessionsViewV2 = UserSessionsViewV1