"""
Authentication services for business logic.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from .models import User, UserProfile, UserSession

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