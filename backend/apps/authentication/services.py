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
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import secrets
import hashlib
import hmac
from datetime import timedelta

from .models import User, UserProfile, UserSession, PasswordResetToken, PasswordResetAttempt
from .email_service import PasswordResetEmailService
from .email_service import PasswordResetEmailService
from .email_service import PasswordResetEmailService

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service class for authentication-related business logic.
    """

    @staticmethod
    def register_user(user_data, profile_data=None):
        """
        Register a new user with optional profile data.
        """
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(**user_data)
                
                # Update user profile (automatically created by signal)
                if profile_data:
                    profile = user.profile
                    for key, value in profile_data.items():
                        setattr(profile, key, value)
                    profile.save()
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                logger.info(f"User registered successfully: {user.email}")
                return user, tokens
                
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise

    @staticmethod
    def authenticate_user(email, password):
        """
        Authenticate user with email and password.
        """
        try:
            user = authenticate(username=email, password=password)
            if user and user.is_active:
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                logger.info(f"User authenticated successfully: {email}")
                return user, tokens
            else:
                logger.warning(f"Authentication failed for: {email}")
                return None, None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    @staticmethod
    def create_user_session(user, request_data):
        """
        Create a user session record.
        """
        try:
            session_data = {
                'user': user,
                'session_key': request_data.get('session_key', 'api_session'),
                'ip_address': request_data.get('ip_address', ''),
                'user_agent': request_data.get('user_agent', ''),
                'device_type': request_data.get('device_type', 'unknown'),
                'location': request_data.get('location', ''),
            }
            session = UserSession.objects.create(**session_data)
            logger.info(f"User session created for: {user.email}")
            return session
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
            return None

    @staticmethod
    def deactivate_user_sessions(user, exclude_session_key=None):
        """
        Deactivate user sessions, optionally excluding a specific session.
        """
        try:
            queryset = UserSession.objects.filter(user=user, is_active=True)
            if exclude_session_key:
                queryset = queryset.exclude(session_key=exclude_session_key)
            
            count = queryset.update(is_active=False)
            logger.info(f"Deactivated {count} sessions for user: {user.email}")
            return count
        except Exception as e:
            logger.error(f"Failed to deactivate sessions: {str(e)}")
            return 0

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
                PasswordResetToken.objects.filter(
                    user=user,
                    is_used=False
                ).update(is_used=True)
                
                # Generate new secure token
                raw_token = PasswordResetService._generate_secure_token()
                token_hash = PasswordResetService._hash_token(raw_token)
                
                # Create token record with expiration
                expires_at = timezone.now() + timedelta(hours=PasswordResetService.TOKEN_EXPIRY_HOURS)
                
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    ip_address=ip_address
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
            
            token_hash = PasswordResetService._hash_token(token)
            
            # Find all potential matching tokens (to prevent timing attacks)
            potential_tokens = PasswordResetToken.objects.filter(
                is_used=False,
                expires_at__gt=timezone.now()
            ).select_related('user')
            
            # Use constant-time comparison to find matching token
            matching_token = None
            for db_token in potential_tokens:
                if PasswordResetService._constant_time_compare(db_token.token_hash, token_hash):
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
            expired_count = PasswordResetToken.objects.filter(
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
            queryset = PasswordResetToken.objects.filter(user=user)
            if not include_used:
                queryset = queryset.filter(is_used=False)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Failed to get user reset tokens: {str(e)}")
            return PasswordResetToken.objects.none()
    
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