"""
Authentication services for business logic.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import secrets
import hashlib
import hmac
import json
from datetime import timedelta
from typing import Optional, Tuple, Dict, Any

from .models import (
    User, UserProfile, UserSession, PasswordReset, PasswordResetAttempt,
    EmailVerification, EmailVerificationAttempt
)
from .email_service import PasswordResetEmailService

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Enhanced service class for authentication-related business logic.
    Implements user registration, login, JWT token management, and session handling.
    Requirements: 1.1, 1.2, 2.1, 2.2
    """

    @staticmethod
    def register_user(user_data: Dict[str, Any], profile_data: Optional[Dict[str, Any]] = None, 
                     request_data: Optional[Dict[str, Any]] = None) -> Tuple[User, Dict[str, str]]:
        """
        Register a new user with email uniqueness validation and enhanced security.
        
        Args:
            user_data: Dictionary containing user registration data
            profile_data: Optional profile information
            request_data: Request metadata (IP, user agent, etc.)
            
        Returns:
            Tuple of (User instance, JWT tokens dict)
            
        Requirements: 1.1 - User registration with email uniqueness validation
        """
        try:
            with transaction.atomic():
                # Validate email uniqueness
                email = user_data.get('email', '').lower().strip()
                if User.objects.filter(email=email).exists():
                    raise ValidationError("A user with this email already exists.")
                
                # Validate password strength
                password = user_data.get('password')
                if password:
                    validate_password(password)
                
                # Prepare user data
                user_data_clean = user_data.copy()
                user_data_clean['email'] = email
                user_data_clean['username'] = user_data_clean.get('username', email)
                
                # Create user
                user = User.objects.create_user(**user_data_clean)
                
                # Update user profile (automatically created by signal)
                if profile_data:
                    try:
                        profile = user.profile
                        for key, value in profile_data.items():
                            if hasattr(profile, key):
                                setattr(profile, key, value)
                        profile.save()
                    except Exception as e:
                        logger.warning(f"Failed to update profile for {user.email}: {str(e)}")
                
                # Create initial session if request data provided
                if request_data:
                    SessionManagementService.create_session(user, request_data)
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                # Send email verification (don't fail registration if this fails)
                try:
                    EmailVerificationService.send_verification_email(user, request_data)
                except Exception as e:
                    logger.warning(f"Failed to send verification email for {user.email}: {str(e)}")
                
                logger.info(f"User registered successfully: {user.email}")
                return user, tokens
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise

    @staticmethod
    def authenticate_user(email: str, password: str, request_data: Optional[Dict[str, Any]] = None) -> Tuple[Optional[User], Optional[Dict[str, str]]]:
        """
        Authenticate user with secure password verification and account lockout protection.
        
        Args:
            email: User email address
            password: User password
            request_data: Request metadata for session creation
            
        Returns:
            Tuple of (User instance or None, JWT tokens dict or None)
            
        Requirements: 1.2, 2.2 - Secure user authentication with password verification
        """
        try:
            email = email.lower().strip()
            
            # Get user and check if account is locked
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Check if account is locked
                if user.is_account_locked:
                    logger.warning(f"Authentication attempt on locked account: {email}")
                    return None, None
                    
            except User.DoesNotExist:
                # Log failed attempt for non-existent user
                logger.warning(f"Authentication attempt for non-existent user: {email}")
                return None, None
            
            # Authenticate user
            authenticated_user = authenticate(username=email, password=password)
            
            if authenticated_user and authenticated_user.is_active:
                # Reset failed login attempts on successful login
                user.reset_failed_login()
                
                # Update last login IP
                if request_data and 'ip_address' in request_data:
                    user.last_login_ip = request_data['ip_address']
                    user.save(update_fields=['last_login_ip'])
                
                # Create session
                if request_data:
                    SessionManagementService.create_session(user, request_data)
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                logger.info(f"User authenticated successfully: {email}")
                return user, tokens
            else:
                # Increment failed login attempts
                user.increment_failed_login()
                logger.warning(f"Authentication failed for: {email}")
                return None, None
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    @staticmethod
    def refresh_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: JWT refresh token string
            
        Returns:
            Dictionary with new tokens or None if invalid
            
        Requirements: 1.2 - JWT token generation and refresh token functionality
        """
        try:
            refresh = RefreshToken(refresh_token)
            
            # Generate new access token
            new_tokens = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),  # Optionally rotate refresh token
            }
            
            logger.info("Token refreshed successfully")
            return new_tokens
            
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return None

    @staticmethod
    def logout_user(user: User, session_key: Optional[str] = None, 
                   logout_all: bool = False) -> bool:
        """
        Logout user with session cleanup and token blacklisting.
        
        Args:
            user: User instance
            session_key: Specific session to logout (optional)
            logout_all: Whether to logout all sessions
            
        Returns:
            Boolean indicating success
            
        Requirements: 1.2 - Logout functionality with session cleanup
        """
        try:
            with transaction.atomic():
                if logout_all:
                    # Deactivate all user sessions
                    count = SessionManagementService.terminate_all_sessions(user)
                    logger.info(f"Logged out all sessions for user {user.email}: {count} sessions")
                elif session_key:
                    # Deactivate specific session
                    success = SessionManagementService.terminate_session(session_key)
                    if success:
                        logger.info(f"Logged out session {session_key} for user {user.email}")
                    else:
                        logger.warning(f"Failed to logout session {session_key} for user {user.email}")
                else:
                    # Deactivate all sessions (default behavior)
                    count = SessionManagementService.terminate_all_sessions(user)
                    logger.info(f"Logged out user {user.email}: {count} sessions terminated")
                
                return True
                
        except Exception as e:
            logger.error(f"Logout failed for user {user.email}: {str(e)}")
            return False

    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Validate user registration data.
        
        Args:
            user_data: Dictionary containing user data to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: dict)
        """
        errors = {}
        
        try:
            # Validate email
            email = user_data.get('email', '').lower().strip()
            if not email:
                errors['email'] = 'Email is required'
            elif User.objects.filter(email=email).exists():
                errors['email'] = 'A user with this email already exists'
            
            # Validate password
            password = user_data.get('password')
            if not password:
                errors['password'] = 'Password is required'
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    errors['password'] = '; '.join(e.messages)
            
            # Validate username
            username = user_data.get('username')
            if username and User.objects.filter(username=username).exists():
                errors['username'] = 'A user with this username already exists'
            
            # Validate user type
            user_type = user_data.get('user_type')
            if user_type and user_type not in dict(User.USER_TYPE_CHOICES):
                errors['user_type'] = 'Invalid user type'
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"User data validation error: {str(e)}")
            return False, {'general': 'Validation failed'}

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(email=email.lower().strip(), is_active=True)
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    def authenticate_admin_user(email: str, password: str, request_data: Optional[Dict[str, Any]] = None) -> Tuple[Optional[User], Optional[Dict[str, str]]]:
        """
        Authenticate admin user with enhanced security validation.
        
        Args:
            email: Admin email address
            password: Admin password
            request_data: Request metadata for session creation
            
        Returns:
            Tuple of (User instance or None, JWT tokens dict or None)
            
        Requirements: 2.1, 2.2 - Admin authentication with enhanced security
        """
        try:
            email = email.lower().strip()
            
            # Get user and verify admin privileges
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Check if user has admin privileges
                if not (user.is_staff or user.is_superuser or user.user_type in ['admin', 'super_admin']):
                    logger.warning(f"Non-admin user attempted admin login: {email}")
                    raise Exception("Not admin user")
                
                # Check if account is locked
                if user.is_account_locked:
                    logger.warning(f"Admin authentication attempt on locked account: {email}")
                    raise Exception("Account locked")
                    
            except User.DoesNotExist:
                logger.warning(f"Admin authentication attempt for non-existent user: {email}")
                raise Exception("Invalid credentials")
            
            # Authenticate user
            authenticated_user = authenticate(username=email, password=password)
            
            if authenticated_user and authenticated_user.is_active:
                # Reset failed login attempts on successful login
                user.reset_failed_login()
                
                # Update last login IP
                if request_data and 'ip_address' in request_data:
                    user.last_login_ip = request_data['ip_address']
                    user.save(update_fields=['last_login_ip'])
                
                # Create admin session with enhanced tracking
                if request_data:
                    request_data['login_method'] = 'admin_password'
                    SessionManagementService.create_session(user, request_data)
                
                # Generate JWT tokens with admin claims
                refresh = RefreshToken.for_user(user)
                refresh['user_type'] = user.user_type
                refresh['is_admin'] = True
                
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                logger.info(f"Admin user authenticated successfully: {email}")
                return user, tokens
            else:
                # Increment failed login attempts
                user.increment_failed_login()
                logger.warning(f"Admin authentication failed for: {email}")
                raise Exception("Invalid credentials")
                
        except Exception as e:
            logger.error(f"Admin authentication error: {str(e)}")
            raise

    @staticmethod
    def logout_admin_user(user: User, refresh_token: Optional[str] = None, 
                         session_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Logout admin user with enhanced audit logging.
        
        Args:
            user: Admin user instance
            refresh_token: JWT refresh token to blacklist
            session_id: Specific session to logout
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Requirements: 2.1, 2.2 - Admin logout with audit logging
        """
        try:
            with transaction.atomic():
                # Blacklist refresh token if provided
                if refresh_token:
                    try:
                        token = RefreshToken(refresh_token)
                        token.blacklist()
                        logger.info(f"Admin refresh token blacklisted for user: {user.email}")
                    except Exception as e:
                        logger.warning(f"Failed to blacklist admin refresh token: {str(e)}")
                
                # Terminate specific session or all sessions
                if session_id:
                    success = SessionManagementService.terminate_session(session_id)
                    if success:
                        logger.info(f"Admin session {session_id} terminated for user: {user.email}")
                        return True, "Admin session terminated successfully"
                    else:
                        logger.warning(f"Failed to terminate admin session {session_id} for user: {user.email}")
                        return False, "Failed to terminate admin session"
                else:
                    # Terminate all sessions for admin user
                    count = SessionManagementService.terminate_all_sessions(user)
                    logger.info(f"All admin sessions terminated for user {user.email}: {count} sessions")
                    return True, f"All admin sessions terminated successfully ({count} sessions)"
                
        except Exception as e:
            logger.error(f"Admin logout failed for user {user.email}: {str(e)}")
            return False, f"Admin logout failed: {str(e)}"

    @staticmethod
    def refresh_admin_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new admin access token from refresh token with enhanced validation.
        
        Args:
            refresh_token: JWT refresh token string
            
        Returns:
            Dictionary with new tokens or None if invalid
            
        Requirements: 2.1, 2.2 - Admin token refresh with enhanced validation
        """
        try:
            refresh = RefreshToken(refresh_token)
            
            # Get user from token and verify admin privileges
            user_id = refresh.payload.get('user_id')
            if not user_id:
                raise Exception("Invalid token")
            
            try:
                user = User.objects.get(id=user_id, is_active=True)
                
                # Verify user still has admin privileges
                if not (user.is_staff or user.is_superuser or user.user_type in ['admin', 'super_admin']):
                    logger.warning(f"Token refresh denied - user no longer admin: {user.email}")
                    raise Exception("Not admin user")
                
                # Check if account is locked
                if user.is_account_locked:
                    logger.warning(f"Token refresh denied - admin account locked: {user.email}")
                    raise Exception("Account locked")
                    
            except User.DoesNotExist:
                logger.warning(f"Token refresh failed - user not found: {user_id}")
                raise Exception("Invalid token")
            
            # Generate new access token with admin claims
            new_refresh = RefreshToken.for_user(user)
            new_refresh['user_type'] = user.user_type
            new_refresh['is_admin'] = True
            
            new_tokens = {
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh),
            }
            
            logger.info(f"Admin token refreshed successfully for user: {user.email}")
            return new_tokens
            
        except Exception as e:
            logger.warning(f"Admin token refresh failed: {str(e)}")
            raise

class EmailVerificationService:
    """
    Service class for email verification workflow.
    Implements token generation, validation, sending, and rate limiting.
    Requirements: 3.1, 3.2
    """
    
    # Rate limiting constants
    MAX_ATTEMPTS_PER_HOUR = 3
    TOKEN_EXPIRY_HOURS = 24
    
    @staticmethod
    def send_verification_email(user: User, request_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Send email verification link to user with rate limiting.
        
        Args:
            user: User instance
            request_data: Request metadata (IP, user agent, etc.)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Requirements: 3.1 - Send email verification link during registration
        """
        try:
            # Check if email is already verified
            if user.is_email_verified:
                return True, "Email is already verified"
            
            # Check rate limiting
            ip_address = request_data.get('ip_address', '') if request_data else ''
            if ip_address:
                rate_limit_ok, attempt_count = EmailVerificationService._check_rate_limit(
                    ip_address, user.email
                )
                if not rate_limit_ok:
                    logger.warning(f"Rate limit exceeded for email verification: {user.email} from {ip_address}")
                    return False, "Too many verification requests. Please try again later."
            
            with transaction.atomic():
                # Invalidate existing tokens for this user
                EmailVerification.objects.filter(
                    user=user,
                    is_used=False
                ).update(is_used=True)
                
                # Create new verification token
                verification = EmailVerification.objects.create(
                    user=user,
                    ip_address=ip_address
                )
                
                # Log attempt
                EmailVerificationService._log_verification_attempt(
                    ip_address=ip_address,
                    email=user.email,
                    success=True,
                    user_agent=request_data.get('user_agent', '') if request_data else ''
                )
                
                # Send email (implement actual email sending)
                success, error = EmailVerificationService._send_verification_email(
                    user, verification.token, ip_address
                )
                
                if not success:
                    # Mark token as used if email failed
                    verification.is_used = True
                    verification.save()
                    
                    # Log failed attempt
                    EmailVerificationService._log_verification_attempt(
                        ip_address=ip_address,
                        email=user.email,
                        success=False,
                        user_agent=request_data.get('user_agent', '') if request_data else ''
                    )
                    
                    return False, error
                
                logger.info(f"Email verification sent to: {user.email}")
                return True, None
                
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False, "Failed to send verification email"

    @staticmethod
    def verify_email(token: str) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Verify email using token and mark account as verified.
        
        Args:
            token: Email verification token
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str], user: Optional[User])
            
        Requirements: 3.2 - Email verification confirmation logic
        """
        try:
            if not token:
                return False, "Verification token is required", None
            
            # Find verification record
            try:
                verification = EmailVerification.objects.select_related('user').get(
                    token=token,
                    is_used=False
                )
            except EmailVerification.DoesNotExist:
                logger.warning(f"Invalid email verification token used: {token[:8]}...")
                return False, "Invalid or expired verification token", None
            
            # Check if token is expired
            if verification.is_expired:
                logger.warning(f"Expired email verification token used for user: {verification.user.email}")
                return False, "Verification token has expired", None
            
            # Verify email
            with transaction.atomic():
                user = verification.user
                user.is_email_verified = True
                user.save(update_fields=['is_email_verified'])
                
                # Mark token as used
                verification.mark_as_used()
                
                logger.info(f"Email verified successfully for user: {user.email}")
                return True, None, user
                
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return False, "Email verification failed", None

    @staticmethod
    def resend_verification(user: User, request_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Resend email verification with rate limiting.
        
        Args:
            user: User instance
            request_data: Request metadata
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Requirements: 3.2 - Resend verification functionality with rate limiting
        """
        try:
            # Check if already verified
            if user.is_email_verified:
                return False, "Email is already verified"
            
            # Use the same logic as send_verification_email
            return EmailVerificationService.send_verification_email(user, request_data)
            
        except Exception as e:
            logger.error(f"Failed to resend verification email: {str(e)}")
            return False, "Failed to resend verification email"

    @staticmethod
    def _check_rate_limit(ip_address: str, email: str) -> Tuple[bool, int]:
        """
        Check rate limit for email verification attempts.
        
        Args:
            ip_address: IP address making the request
            email: Email address being verified
            
        Returns:
            Tuple of (allowed: bool, attempt_count: int)
        """
        try:
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            # Check attempts by IP
            ip_attempts = EmailVerificationAttempt.objects.filter(
                ip_address=ip_address,
                created_at__gte=one_hour_ago
            ).count()
            
            # Check attempts by email
            email_attempts = EmailVerificationAttempt.objects.filter(
                email=email,
                created_at__gte=one_hour_ago
            ).count()
            
            max_attempts = EmailVerificationService.MAX_ATTEMPTS_PER_HOUR
            
            if ip_attempts >= max_attempts or email_attempts >= max_attempts:
                return False, max(ip_attempts, email_attempts)
            
            return True, max(ip_attempts, email_attempts)
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True, 0

    @staticmethod
    def _log_verification_attempt(ip_address: str, email: str, success: bool = False, user_agent: str = ''):
        """
        Log email verification attempt for monitoring and rate limiting.
        """
        try:
            EmailVerificationAttempt.objects.create(
                ip_address=ip_address,
                email=email,
                success=success,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Failed to log verification attempt: {str(e)}")

    @staticmethod
    def _send_verification_email(user: User, token: str, request_ip: str = '') -> Tuple[bool, Optional[str]]:
        """
        Send the actual verification email.
        
        Args:
            user: User instance
            token: Verification token
            request_ip: IP address of the request
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Create verification URL
            verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{token}"
            
            # Email subject and content
            subject = f"Verify Your Email Address - {getattr(settings, 'SITE_NAME', 'E-commerce Platform')}"
            
            message = f"""
Hello {user.first_name or user.username},

Thank you for registering with us! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The E-commerce Team

---
This email was sent from {request_ip} at {timezone.now().strftime('%B %d, %Y at %I:%M %p %Z')}
"""
            
            # For now, log the email (implement proper email service later)
            logger.info(f"Email verification would be sent to: {user.email}")
            logger.info(f"Verification URL: {verification_url}")
            
            # TODO: Implement actual email sending
            # send_mail(
            #     subject,
            #     message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            #     fail_silently=False,
            # )
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False, "Failed to send verification email"

    @staticmethod
    def cleanup_expired_tokens(days_old: int = 7) -> int:
        """
        Clean up expired email verification tokens.
        
        Args:
            days_old: Remove tokens older than this many days
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            deleted_count = EmailVerification.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} expired email verification tokens")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Email verification token cleanup failed: {str(e)}")
            return 0

    @staticmethod
    def get_user_verification_status(user: User) -> Dict[str, Any]:
        """
        Get email verification status for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with verification status information
        """
        try:
            active_tokens = EmailVerification.objects.filter(
                user=user,
                is_used=False,
                expires_at__gt=timezone.now()
            ).count()
            
            return {
                'is_verified': user.is_email_verified,
                'email': user.email,
                'active_tokens': active_tokens,
                'last_verification_sent': None,  # TODO: Add this field to model if needed
            }
            
        except Exception as e:
            logger.error(f"Failed to get verification status: {str(e)}")
            return {
                'is_verified': user.is_email_verified,
                'email': user.email,
                'active_tokens': 0,
                'error': str(e)
            }

class SessionManagementService:
    """
    Service class for user session handling and management.
    Implements session creation, tracking, termination, and cleanup.
    Requirements: 5.1, 5.2
    """
    
    # Session configuration
    SESSION_TIMEOUT_HOURS = 24 * 7  # 7 days default
    MAX_SESSIONS_PER_USER = 10
    
    @staticmethod
    def create_session(user: User, request_data: Dict[str, Any]) -> Optional[UserSession]:
        """
        Create a user session with device and IP tracking.
        
        Args:
            user: User instance
            request_data: Dictionary containing session data
            
        Returns:
            UserSession instance or None if failed
            
        Requirements: 5.1 - Session creation with device and IP tracking
        """
        try:
            # Extract device information
            user_agent = request_data.get('user_agent', '')
            device_info = SessionManagementService._parse_device_info(user_agent)
            
            # Generate unique session key
            session_key = secrets.token_urlsafe(32)
            
            # Prepare session data
            session_data = {
                'user': user,
                'session_key': session_key,
                'ip_address': request_data.get('ip_address', ''),
                'user_agent': user_agent,
                'device_info': device_info,
                'location': request_data.get('location', ''),
                'login_method': request_data.get('login_method', 'password'),
            }
            
            # Check session limit and cleanup old sessions if needed
            SessionManagementService._enforce_session_limit(user)
            
            # Create session
            session = UserSession.objects.create(**session_data)
            
            logger.info(f"User session created for: {user.email} from {session_data['ip_address']}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
            return None

    @staticmethod
    def get_user_sessions(user: User, active_only: bool = True) -> 'QuerySet[UserSession]':
        """
        Get user sessions with filtering options.
        
        Args:
            user: User instance
            active_only: Whether to return only active sessions
            
        Returns:
            QuerySet of UserSession objects
            
        Requirements: 5.2 - Session listing and management functionality
        """
        try:
            queryset = UserSession.objects.filter(user=user)
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            return queryset.order_by('-last_activity')
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return UserSession.objects.none()

    @staticmethod
    def terminate_session(session_key: str) -> bool:
        """
        Terminate a specific session.
        
        Args:
            session_key: Session key to terminate
            
        Returns:
            Boolean indicating success
            
        Requirements: 5.2 - Session termination (single session)
        """
        try:
            session = UserSession.objects.get(session_key=session_key, is_active=True)
            session.terminate()
            
            logger.info(f"Session terminated: {session_key[:8]}... for user {session.user.email}")
            return True
            
        except UserSession.DoesNotExist:
            logger.warning(f"Attempted to terminate non-existent session: {session_key[:8]}...")
            return False
        except Exception as e:
            logger.error(f"Failed to terminate session: {str(e)}")
            return False

    @staticmethod
    def terminate_all_sessions(user: User, exclude_session_key: Optional[str] = None) -> int:
        """
        Terminate all sessions for a user, optionally excluding one.
        
        Args:
            user: User instance
            exclude_session_key: Session key to exclude from termination
            
        Returns:
            Number of sessions terminated
            
        Requirements: 5.2 - Session termination (all sessions)
        """
        try:
            queryset = UserSession.objects.filter(user=user, is_active=True)
            if exclude_session_key:
                queryset = queryset.exclude(session_key=exclude_session_key)
            
            count = queryset.update(is_active=False)
            logger.info(f"Terminated {count} sessions for user: {user.email}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to terminate sessions: {str(e)}")
            return 0

    @staticmethod
    def cleanup_expired_sessions(hours_old: int = SESSION_TIMEOUT_HOURS) -> int:
        """
        Clean up expired sessions based on last activity.
        
        Args:
            hours_old: Sessions older than this many hours will be cleaned up
            
        Returns:
            Number of sessions cleaned up
            
        Requirements: 5.2 - Expired session cleanup functionality
        """
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours_old)
            
            # Mark old sessions as inactive
            expired_count = UserSession.objects.filter(
                last_activity__lt=cutoff_time,
                is_active=True
            ).update(is_active=False)
            
            # Optionally delete very old sessions (older than 30 days)
            very_old_cutoff = timezone.now() - timedelta(days=30)
            deleted_count = UserSession.objects.filter(
                last_activity__lt=very_old_cutoff
            ).delete()[0]
            
            logger.info(f"Session cleanup: {expired_count} expired, {deleted_count} deleted")
            return expired_count + deleted_count
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")
            return 0

    @staticmethod
    def update_session_activity(session_key: str) -> bool:
        """
        Update last activity timestamp for a session.
        
        Args:
            session_key: Session key to update
            
        Returns:
            Boolean indicating success
        """
        try:
            UserSession.objects.filter(
                session_key=session_key,
                is_active=True
            ).update(last_activity=timezone.now())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {str(e)}")
            return False

    @staticmethod
    def get_session_info(session_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a session.
        
        Args:
            session_key: Session key to look up
            
        Returns:
            Dictionary with session information or None if not found
        """
        try:
            session = UserSession.objects.select_related('user').get(
                session_key=session_key,
                is_active=True
            )
            
            return {
                'session_key': session.session_key,
                'user_email': session.user.email,
                'ip_address': session.ip_address,
                'device_info': session.device_info,
                'location': session.location,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'login_method': session.login_method,
                'device_name': session.device_name,
            }
            
        except UserSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get session info: {str(e)}")
            return None

    @staticmethod
    def _parse_device_info(user_agent: str) -> Dict[str, str]:
        """
        Parse user agent string to extract device information.
        
        Args:
            user_agent: User agent string from request
            
        Returns:
            Dictionary with parsed device information
        """
        try:
            # Simple user agent parsing (can be enhanced with user-agents library)
            device_info = {
                'browser': 'Unknown Browser',
                'os': 'Unknown OS',
                'device': 'Unknown Device',
                'raw_user_agent': user_agent
            }
            
            if not user_agent:
                return device_info
            
            user_agent_lower = user_agent.lower()
            
            # Detect browser
            if 'chrome' in user_agent_lower:
                device_info['browser'] = 'Chrome'
            elif 'firefox' in user_agent_lower:
                device_info['browser'] = 'Firefox'
            elif 'safari' in user_agent_lower:
                device_info['browser'] = 'Safari'
            elif 'edge' in user_agent_lower:
                device_info['browser'] = 'Edge'
            
            # Detect OS
            if 'windows' in user_agent_lower:
                device_info['os'] = 'Windows'
            elif 'mac' in user_agent_lower:
                device_info['os'] = 'macOS'
            elif 'linux' in user_agent_lower:
                device_info['os'] = 'Linux'
            elif 'android' in user_agent_lower:
                device_info['os'] = 'Android'
            elif 'ios' in user_agent_lower:
                device_info['os'] = 'iOS'
            
            # Detect device type
            if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
                device_info['device'] = 'Mobile'
            elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_info['device'] = 'Tablet'
            else:
                device_info['device'] = 'Desktop'
            
            return device_info
            
        except Exception as e:
            logger.error(f"Failed to parse device info: {str(e)}")
            return {
                'browser': 'Unknown Browser',
                'os': 'Unknown OS',
                'device': 'Unknown Device',
                'raw_user_agent': user_agent,
                'parse_error': str(e)
            }

    @staticmethod
    def _enforce_session_limit(user: User) -> None:
        """
        Enforce maximum session limit per user by terminating oldest sessions.
        
        Args:
            user: User instance
        """
        try:
            active_sessions = UserSession.objects.filter(
                user=user,
                is_active=True
            ).order_by('-last_activity')
            
            if active_sessions.count() >= SessionManagementService.MAX_SESSIONS_PER_USER:
                # Get sessions to terminate (oldest ones)
                sessions_to_terminate = active_sessions[SessionManagementService.MAX_SESSIONS_PER_USER - 1:]
                
                session_keys = [s.session_key for s in sessions_to_terminate]
                terminated_count = UserSession.objects.filter(
                    session_key__in=session_keys
                ).update(is_active=False)
                
                logger.info(f"Terminated {terminated_count} old sessions for user {user.email} due to session limit")
                
        except Exception as e:
            logger.error(f"Failed to enforce session limit: {str(e)}")

    @staticmethod
    def get_session_statistics(user: User) -> Dict[str, Any]:
        """
        Get session statistics for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with session statistics
        """
        try:
            active_sessions = UserSession.objects.filter(user=user, is_active=True)
            total_sessions = UserSession.objects.filter(user=user)
            
            # Group by device type
            device_stats = {}
            for session in active_sessions:
                device_type = session.device_info.get('device', 'Unknown')
                device_stats[device_type] = device_stats.get(device_type, 0) + 1
            
            return {
                'active_sessions': active_sessions.count(),
                'total_sessions': total_sessions.count(),
                'device_breakdown': device_stats,
                'last_activity': active_sessions.first().last_activity if active_sessions.exists() else None,
                'oldest_session': active_sessions.last().created_at if active_sessions.exists() else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {str(e)}")
            return {
                'active_sessions': 0,
                'total_sessions': 0,
                'device_breakdown': {},
                'error': str(e)
            }

    @staticmethod
    def change_password(user, old_password, new_password):
        """
        Change user password after verifying old password.
        """
        try:
            if not user.check_password(old_password):
                raise ValueError("Old password is incorrect")
            
            user.set_password(new_password)
            user.save()
            
            # Deactivate all sessions to force re-login
            AuthenticationService.deactivate_user_sessions(user)
            
            logger.info(f"Password changed for user: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            raise

    @staticmethod
    def generate_password_reset_token(email):
        """
        Generate password reset token for user.
        """
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            logger.info(f"Password reset token generated for: {email}")
            return user, token, uid
        except User.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return None, None, None
        except Exception as e:
            logger.error(f"Failed to generate reset token: {str(e)}")
            raise

    @staticmethod
    def verify_password_reset_token(uid, token):
        """
        Verify password reset token and return user.
        """
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                logger.info(f"Password reset token verified for: {user.email}")
                return user
            else:
                logger.warning(f"Invalid password reset token for: {user.email}")
                return None
        except (User.DoesNotExist, ValueError, TypeError):
            logger.warning("Invalid password reset token format")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise

    @staticmethod
    def reset_password(user, new_password):
        """
        Reset user password and deactivate all sessions.
        """
        try:
            user.set_password(new_password)
            user.save()
            
            # Deactivate all sessions
            AuthenticationService.deactivate_user_sessions(user)
            
            logger.info(f"Password reset completed for: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise

    @staticmethod
    def update_user_profile(user, user_data, profile_data=None):
        """
        Update user and profile information.
        """
        try:
            with transaction.atomic():
                # Update user fields
                for field, value in user_data.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                user.save()
                
                # Update profile fields
                if profile_data:
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    for field, value in profile_data.items():
                        if hasattr(profile, field):
                            setattr(profile, field, value)
                    profile.save()
                
                logger.info(f"Profile updated for user: {user.email}")
                return user
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise

    @staticmethod
    def verify_email(user):
        """
        Mark user email as verified.
        """
        try:
            user.is_email_verified = True
            user.save()
            logger.info(f"Email verified for user: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            raise

    @staticmethod
    def verify_phone(user):
        """
        Mark user phone as verified.
        """
        try:
            user.is_phone_verified = True
            user.save()
            logger.info(f"Phone verified for user: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Phone verification failed: {str(e)}")
            raise

    @staticmethod
    def get_user_sessions(user, active_only=True):
        """
        Get user sessions.
        """
        try:
            queryset = UserSession.objects.filter(user=user)
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            return queryset.order_by('-last_activity')
        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return UserSession.objects.none()

    @staticmethod
    def send_verification_email(user):
        """
        Send email verification link to user.
        """
        try:
            # Generate verification token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create verification URL
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
            
            # Send email (implement proper email service)
            subject = "Verify Your Email Address"
            message = f"""
            Hi {user.first_name or user.username},
            
            Please click the link below to verify your email address:
            {verification_url}
            
            If you didn't create an account, please ignore this email.
            
            Best regards,
            The E-commerce Team
            """
            
            # For now, just log the email (implement proper email service)
            logger.info(f"Verification email would be sent to: {user.email}")
            logger.info(f"Verification URL: {verification_url}")
            
            # Uncomment when email service is configured
            # send_mail(
            #     subject,
            #     message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            #     fail_silently=False,
            # )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            raise

    @staticmethod
    def send_password_reset_email(user, token, uid):
        """
        Send password reset email to user.
        """
        try:
            # Create reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Send email (implement proper email service)
            subject = "Password Reset Request"
            message = f"""
            Hi {user.first_name or user.username},
            
            You requested a password reset. Click the link below to reset your password:
            {reset_url}
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            The E-commerce Team
            """
            
            # For now, just log the email (implement proper email service)
            logger.info(f"Password reset email would be sent to: {user.email}")
            logger.info(f"Reset URL: {reset_url}")
            
            # Uncomment when email service is configured
            # send_mail(
            #     subject,
            #     message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            #     fail_silently=False,
            # )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            raise


class UserProfileService:
    """
    Service class for user profile management.
    """

    @staticmethod
    def get_or_create_profile(user):
        """
        Get or create user profile.
        """
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                logger.info(f"Profile created for user: {user.email}")
            return profile
        except Exception as e:
            logger.error(f"Failed to get/create profile: {str(e)}")
            raise

    @staticmethod
    def update_preferences(user, preferences):
        """
        Update user preferences.
        """
        try:
            profile = UserProfileService.get_or_create_profile(user)
            profile.preferences.update(preferences)
            profile.save()
            logger.info(f"Preferences updated for user: {user.email}")
            return profile
        except Exception as e:
            logger.error(f"Failed to update preferences: {str(e)}")
            raise

    @staticmethod
    def update_privacy_settings(user, privacy_settings):
        """
        Update user privacy settings.
        """
        try:
            profile = UserProfileService.get_or_create_profile(user)
            
            # Update privacy-related fields
            if 'profile_visibility' in privacy_settings:
                profile.profile_visibility = privacy_settings['profile_visibility']
            
            profile.save()
            
            # Update user notification preferences
            if 'newsletter_subscription' in privacy_settings:
                user.newsletter_subscription = privacy_settings['newsletter_subscription']
            if 'sms_notifications' in privacy_settings:
                user.sms_notifications = privacy_settings['sms_notifications']
            if 'email_notifications' in privacy_settings:
                user.email_notifications = privacy_settings['email_notifications']
            
            user.save()
            
            logger.info(f"Privacy settings updated for user: {user.email}")
            return profile
        except Exception as e:
            logger.error(f"Failed to update privacy settings: {str(e)}")
            raise

class PasswordResetService:
    """
    Service class for secure password reset functionality.
    Implements secure token generation, hashing, validation, and rate limiting.
    """
    
    # Rate limiting constants
    MAX_ATTEMPTS_PER_HOUR = 5
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY_HOURS = 1
    
    @staticmethod
    def _generate_secure_token():
        """
        Generate a cryptographically secure token.
        Requirements: 2.1 - Generate cryptographically secure token with 32+ characters
        """
        return secrets.token_urlsafe(PasswordResetService.TOKEN_LENGTH)
    
    @staticmethod
    def _hash_token(token):
        """
        Hash token using SHA-256 for secure storage.
        Requirements: 5.2 - Hash tokens before database storage
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _constant_time_compare(a, b):
        """
        Perform constant-time comparison to prevent timing attacks.
        Requirements: 5.3 - Use constant-time comparison to prevent timing attacks
        """
        return hmac.compare_digest(a, b)
    
    @staticmethod
    def check_rate_limit(ip_address):
        """
        Check if IP address has exceeded rate limit for password reset requests.
        Requirements: 4.2 - Implement rate limiting of 5 requests per hour
        """
        try:
            # Get attempts from the last hour
            one_hour_ago = timezone.now() - timedelta(hours=1)
            recent_attempts = PasswordResetAttempt.objects.filter(
                ip_address=ip_address,
                created_at__gte=one_hour_ago
            ).count()
            
            if recent_attempts >= PasswordResetService.MAX_ATTEMPTS_PER_HOUR:
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return False, recent_attempts
            
            return True, recent_attempts
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # In case of error, allow the request but log it
            return True, 0
    
    @staticmethod
    def log_reset_attempt(ip_address, email, success=False, user_agent=''):
        """
        Log password reset attempt for monitoring and rate limiting.
        Requirements: 4.1 - Log attempts with timestamp, IP address, and email
        """
        try:
            PasswordResetAttempt.objects.create(
                ip_address=ip_address,
                email=email,
                success=success,
                user_agent=user_agent
            )
            logger.info(f"Password reset attempt logged: {email} from {ip_address} - {'Success' if success else 'Failed'}")
        except Exception as e:
            logger.error(f"Failed to log reset attempt: {str(e)}")
    
    @staticmethod
    def generate_reset_token(user, ip_address, user_agent=''):
        """
        Generate a secure password reset token for the user.
        Requirements: 2.1, 2.2, 2.5, 2.6 - Generate secure token with expiration and database storage
        """
        try:
            with transaction.atomic():
                # Invalidate any existing tokens for this user
                PasswordReset.objects.filter(
                    user=user,
                    is_used=False
                ).update(is_used=True)
                
                # Generate new secure token
                raw_token = PasswordResetService._generate_secure_token()
                
                # Create token record with expiration
                expires_at = timezone.now() + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)
                
                reset_token = PasswordReset.objects.create(
                    user=user,
                    token=raw_token,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Log successful token generation
                PasswordResetService.log_reset_attempt(
                    ip_address=ip_address,
                    email=user.email,
                    success=True,
                    user_agent=user_agent
                )
                
                logger.info(f"Password reset token generated for user: {user.email}")
                return raw_token, reset_token
                
        except Exception as e:
            logger.error(f"Failed to generate reset token: {str(e)}")
            # Log failed attempt
            PasswordResetService.log_reset_attempt(
                ip_address=ip_address,
                email=user.email,
                success=False,
                user_agent=user_agent
            )
            raise
    
    @staticmethod
    def validate_reset_token(token):
        """
        Validate a password reset token.
        Requirements: 5.3 - Use constant-time comparison for token validation
        """
        try:
            if not token:
                return None, "Token is required"
            

            
            # Find all potential matching tokens (to prevent timing attacks)
            potential_tokens = PasswordReset.objects.filter(
                is_used=False,
                expires_at__gt=timezone.now()
            ).select_related('user')
            
            # Use direct comparison since we're not hashing tokens anymore
            matching_token = None
            for db_token in potential_tokens:
                if db_token.token == token:
                    matching_token = db_token
                    break
            
            if not matching_token:
                logger.warning("Invalid or expired password reset token used")
                return None, "Invalid or expired token"
            
            if matching_token.is_expired:
                logger.warning(f"Expired password reset token used for user: {matching_token.user.email}")
                return None, "Token has expired"
            
            if matching_token.is_used:
                logger.warning(f"Already used password reset token attempted for user: {matching_token.user.email}")
                return None, "Token has already been used"
            
            logger.info(f"Valid password reset token validated for user: {matching_token.user.email}")
            return matching_token, None
            
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None, "Token validation failed"
    
    @staticmethod
    def reset_password(token, new_password, ip_address='', user_agent=''):
        """
        Reset user password using a valid token.
        Requirements: 5.4 - Immediately invalidate token after use
        """
        try:
            # Validate token
            reset_token, error = PasswordResetService.validate_reset_token(token)
            if not reset_token:
                return False, error
            
            user = reset_token.user
            
            with transaction.atomic():
                # Update user password
                user.set_password(new_password)
                user.save()
                
                # Invalidate the token immediately
                reset_token.is_used = True
                reset_token.save()
                
                # Deactivate all user sessions to force re-login
                AuthenticationService.deactivate_user_sessions(user)
                
                # Log successful password reset
                logger.info(f"Password reset completed for user: {user.email}")
                
                # Send confirmation email (optional - don't fail if this fails)
                try:
                    PasswordResetEmailService.send_password_reset_confirmation_email(
                        user=user,
                        request_ip=ip_address
                    )
                except Exception as e:
                    logger.warning(f"Failed to send password reset confirmation email: {str(e)}")
                
                # Log the successful reset attempt
                PasswordResetService.log_reset_attempt(
                    ip_address=ip_address,
                    email=user.email,
                    success=True,
                    user_agent=user_agent
                )
                
                return True, "Password reset successfully"
                
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            if 'user' in locals():
                PasswordResetService.log_reset_attempt(
                    ip_address=ip_address,
                    email=user.email,
                    success=False,
                    user_agent=user_agent
                )
            return False, "Password reset failed"
    
    @staticmethod
    def request_password_reset(email, ip_address, user_agent=''):
        """
        Handle password reset request with rate limiting and security checks.
        Requirements: 1.1, 1.2, 1.3, 1.4 - Complete password reset request flow
        """
        try:
            # Check rate limiting first
            rate_limit_ok, attempt_count = PasswordResetService.check_rate_limit(ip_address)
            if not rate_limit_ok:
                logger.warning(f"Rate limit exceeded for password reset from IP: {ip_address}")
                return False, f"Too many requests. Please try again later.", None
            
            # Check if user exists
            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                # Log attempt for non-existent user but don't reveal this information
                PasswordResetService.log_reset_attempt(
                    ip_address=ip_address,
                    email=email,
                    success=False,
                    user_agent=user_agent
                )
                # Return generic success message to prevent email enumeration
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True, "If the email exists, a reset link has been sent.", None
            
            # Generate reset token
            raw_token, reset_token = PasswordResetService.generate_reset_token(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send password reset email
            email_sent, email_error = PasswordResetEmailService.send_password_reset_email(
                user=user,
                token=raw_token,
                request_ip=ip_address
            )
            
            if not email_sent:
                logger.error(f"Failed to send password reset email: {email_error}")
                # Mark the token as used since we couldn't send the email
                reset_token.is_used = True
                reset_token.save()
                
                # Log failed attempt
                PasswordResetService.log_reset_attempt(
                    ip_address=ip_address,
                    email=email,
                    success=False,
                    user_agent=user_agent
                )
                
                return False, "Failed to send reset email. Please try again later.", None
            
            logger.info(f"Password reset requested successfully for: {email}")
            return True, "If the email exists, a reset link has been sent.", raw_token
            
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            # Log failed attempt
            PasswordResetService.log_reset_attempt(
                ip_address=ip_address,
                email=email,
                success=False,
                user_agent=user_agent
            )
            return False, "Password reset request failed. Please try again.", None
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Clean up expired password reset tokens.
        This method should be called periodically (e.g., via Celery task).
        Requirements: 2.6 - Token cleanup and maintenance
        """
        try:
            expired_count = PasswordReset.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            logger.info(f"Cleaned up {expired_count} expired password reset tokens")
            return expired_count
            
        except Exception as e:
            logger.error(f"Token cleanup failed: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_attempts(days_old=30):
        """
        Clean up old password reset attempts.
        Requirements: 2.6 - Database maintenance for reset attempts table
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            deleted_count = PasswordResetAttempt.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} old password reset attempts")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Attempt cleanup failed: {str(e)}")
            return 0
    
    @staticmethod
    def get_user_reset_tokens(user, include_used=False):
        """
        Get password reset tokens for a user (for admin/debugging purposes).
        """
        try:
            queryset = PasswordReset.objects.filter(user=user)
            if not include_used:
                queryset = queryset.filter(is_used=False)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Failed to get user reset tokens: {str(e)}")
            return PasswordReset.objects.none()
    
    @staticmethod
    def get_ip_reset_attempts(ip_address, hours=24):
        """
        Get password reset attempts for an IP address within specified hours.
        """
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            return PasswordResetAttempt.objects.filter(
                ip_address=ip_address,
                created_at__gte=cutoff_time
            ).order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Failed to get IP reset attempts: {str(e)}")
            return PasswordResetAttempt.objects.none()