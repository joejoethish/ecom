"""
Authentication URL patterns for API v2.
"""
from django.urls import path
from .views_v2 import (
    RegisterViewV2, LoginViewV2, LogoutViewV2, RefreshTokenViewV2,
    ProfileViewV2, PasswordChangeViewV2, PasswordResetRequestViewV2,
    PasswordResetConfirmViewV2, VerifyEmailViewV2, ResendVerificationViewV2,
    UserSessionsViewV2
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterViewV2.as_view(), name='register_v2'),
    path('login/', LoginViewV2.as_view(), name='login_v2'),
    path('logout/', LogoutViewV2.as_view(), name='logout_v2'),
    path('refresh/', RefreshTokenViewV2.as_view(), name='refresh_v2'),
    
    # Profile management
    path('profile/', ProfileViewV2.as_view(), name='profile_v2'),
    
    # Password management
    path('password/change/', PasswordChangeViewV2.as_view(), name='password_change_v2'),
    path('password/reset/', PasswordResetRequestViewV2.as_view(), name='password_reset_request_v2'),
    path('password/reset/confirm/', PasswordResetConfirmViewV2.as_view(), name='password_reset_confirm_v2'),
    
    # Email verification
    path('verify-email/', VerifyEmailViewV2.as_view(), name='verify_email_v2'),
    path('resend-verification/', ResendVerificationViewV2.as_view(), name='resend_verification_v2'),
    
    # Session management
    path('sessions/', UserSessionsViewV2.as_view(), name='user_sessions_v2'),
]