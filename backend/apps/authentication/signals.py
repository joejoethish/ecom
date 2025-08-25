"""
Authentication signals for handling user-related events.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
import logging

from .models import UserProfile, UserSession

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    Handle UserProfile creation and updates when User is saved.
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Profile created for user: {instance.email}")
        except Exception as e:
            logger.error(f"Failed to create profile for user {instance.email}: {str(e)}")
    else:
        # For updates, ensure profile exists but don't save it again to avoid recursion
        try:
            if not hasattr(instance, 'profile'):
                UserProfile.objects.get_or_create(user=instance)
        except Exception as e:
            logger.error(f"Failed to ensure profile exists for user {instance.email}: {str(e)}")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login events.
    """
    try:
        # Get client information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_type = get_device_type(user_agent)
        
        # Create or update user session
        session_key = request.session.session_key or 'web_session'
        
        # Create session record with device info
        device_info = {
            'type': device_type,
            'user_agent': user_agent[:200]  # Limit length
        }
        
        UserSession.objects.update_or_create(
            user=user,
            session_key=session_key,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent[:500],  # Limit length to avoid issues
                'device_info': device_info,
                'is_active': True,
            }
        )
        
        logger.info(f"User logged in: {user.email} from {ip_address}")
        
    except Exception as e:
        logger.error(f"Failed to log user login for {user.email}: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events.
    """
    try:
        if user:
            # Deactivate current session
            session_key = request.session.session_key
            if session_key:
                UserSession.objects.filter(
                    user=user,
                    session_key=session_key
                ).update(is_active=False)
            
            logger.info(f"User logged out: {user.email}")
            
    except Exception as e:
        logger.error(f"Failed to log user logout: {str(e)}")


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Clean up user-related data before user deletion.
    """
    try:
        # Deactivate all user sessions
        UserSession.objects.filter(user=instance).update(is_active=False)
        
        logger.info(f"Cleaned up data for user: {instance.email}")
        
    except Exception as e:
        logger.error(f"Failed to cleanup data for user {instance.email}: {str(e)}")


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_device_type(user_agent):
    """
    Determine device type from user agent string.
    """
    user_agent = user_agent.lower()
    
    if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone']):
        return 'mobile'
    elif any(tablet in user_agent for tablet in ['tablet', 'ipad']):
        return 'tablet'
    else:
        return 'desktop'


# Consolidated signal handler for user verification and type changes
@receiver(post_save, sender=User)
def handle_user_changes(sender, instance, created, **kwargs):
    """
    Handle user verification status changes and user type changes.
    """
    if created:
        return  # Skip for new users
        
    try:
        # Check if email verification status changed
        if instance.is_email_verified:
            logger.info(f"Email verified for user: {instance.email}")
            
        # Check if phone verification status changed
        if instance.is_phone_verified:
            logger.info(f"Phone verified for user: {instance.email}")
            
        # Handle user type changes if needed
        # Note: We're not storing original user type to avoid complexity
        # If needed, this can be implemented with a separate tracking model
            
    except Exception as e:
        logger.error(f"Failed to handle user changes for {instance.email}: {str(e)}")