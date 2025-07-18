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
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created.
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Profile created for user: {instance.email}")
        except Exception as e:
            logger.error(f"Failed to create profile for user {instance.email}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when User is saved.
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Create profile if it doesn't exist
            UserProfile.objects.get_or_create(user=instance)
    except Exception as e:
        logger.error(f"Failed to save profile for user {instance.email}: {str(e)}")


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
        
        UserSession.objects.update_or_create(
            user=user,
            session_key=session_key,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_type': device_type,
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


# Signal to handle user verification events
@receiver(post_save, sender=User)
def handle_user_verification(sender, instance, **kwargs):
    """
    Handle user verification status changes.
    """
    try:
        # Check if email verification status changed
        if instance.is_email_verified and not kwargs.get('created', False):
            # User email was just verified
            logger.info(f"Email verified for user: {instance.email}")
            
            # You can add additional logic here, such as:
            # - Sending welcome email
            # - Updating user permissions
            # - Triggering other business logic
        
        # Check if phone verification status changed
        if instance.is_phone_verified and not kwargs.get('created', False):
            logger.info(f"Phone verified for user: {instance.email}")
            
            # Additional logic for phone verification
            
    except Exception as e:
        logger.error(f"Failed to handle user verification for {instance.email}: {str(e)}")


# Signal to handle user type changes
@receiver(post_save, sender=User)
def handle_user_type_change(sender, instance, **kwargs):
    """
    Handle user type changes (customer to seller, etc.).
    """
    try:
        if not kwargs.get('created', False):
            # This is an update, check if user_type changed
            if hasattr(instance, '_original_user_type'):
                old_type = instance._original_user_type
                new_type = instance.user_type
                
                if old_type != new_type:
                    logger.info(f"User type changed for {instance.email}: {old_type} -> {new_type}")
                    
                    # Handle specific type changes
                    if new_type == 'seller':
                        # User became a seller
                        # You might want to create seller-specific records
                        pass
                    elif new_type == 'admin':
                        # User became an admin
                        # You might want to grant additional permissions
                        pass
                        
    except Exception as e:
        logger.error(f"Failed to handle user type change for {instance.email}: {str(e)}")


# Store original user type for comparison
@receiver(post_save, sender=User)
def store_original_user_type(sender, instance, **kwargs):
    """
    Store the original user type for comparison in future saves.
    """
    try:
        if not kwargs.get('created', False):
            # Store current user_type for next comparison
            instance._original_user_type = instance.user_type
    except Exception as e:
        logger.error(f"Failed to store original user type: {str(e)}")