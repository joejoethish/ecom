"""
Authentication URL patterns.
"""
from django.urls import path, include
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password management (legacy endpoints)
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # New secure password reset API endpoints
    path('forgot-password/', views.ForgotPasswordAPIView.as_view(), name='forgot_password_api'),
    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset_password_api'),
    path('validate-reset-token/<str:token>/', views.ValidateResetTokenAPIView.as_view(), name='validate_reset_token_api'),
    path('csrf-token/', views.CSRFTokenView.as_view(), name='csrf_token'),
    
    # Email verification - Updated to use complete API views
    path('verify-email/<str:token>/', views.EmailVerificationAPIView.as_view(), name='verify_email_api'),
    path('resend-verification/', views.ResendVerificationAPIView.as_view(), name='resend_verification_api'),
    
    # Legacy email verification endpoints (for backward compatibility)
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification-legacy/', views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # Session management
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    
    # Admin authentication endpoints
    path('admin-auth/', include('apps.authentication.admin_urls')),
]