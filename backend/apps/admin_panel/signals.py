"""
Django signals for admin panel automation and logging.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import (
    AdminUser, AdminSession, ActivityLog, AdminLoginAttempt, 
    AdminNotification, SystemSettings
)


@receiver(post_save, sender=AdminUser)
def log_admin_user_changes(sender, instance, created, **kwargs):
    """Log admin user creation and updates."""
    action = 'create' if created else 'update'
    description = f"Admin user {'created' if created else 'updated'}: {instance.username}"
    
    ActivityLog.objects.create(
        admin_user=instance if not created else None,
        action=action,
        description=description,
        content_type=ContentType.objects.get_for_model(AdminUser),
        object_id=str(instance.id),
        changes={
            'username': instance.username,
            'email': instance.email,
            'role': instance.role,
            'department': instance.department,
            'is_admin_active': instance.is_admin_active,
        },
        ip_address='127.0.0.1',  # Will be updated by middleware
        module='users',
        severity='medium',
        is_successful=True
    )


@receiver(post_save, sender=SystemSettings)
def log_system_settings_changes(sender, instance, created, **kwargs):
    """Log system settings changes."""
    action = 'create' if created else 'update'
    description = f"System setting {'created' if created else 'updated'}: {instance.key}"
    
    ActivityLog.objects.create(
        admin_user=instance.last_modified_by,
        action=action,
        description=description,
        content_type=ContentType.objects.get_for_model(SystemSettings),
        object_id=str(instance.id),
        changes={
            'key': instance.key,
            'value': instance.value,
            'category': instance.category,
            'setting_type': instance.setting_type,
        },
        ip_address='127.0.0.1',  # Will be updated by middleware
        module='settings',
        severity='high',
        is_successful=True
    )


@receiver(user_logged_in)
def log_admin_login_success(sender, request, user, **kwargs):
    """Log successful admin login attempts."""
    if hasattr(user, 'role') and isinstance(user, AdminUser):
        # Create login attempt record
        AdminLoginAttempt.objects.create(
            username=user.username,
            admin_user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_successful=True,
            is_suspicious=False,
            risk_score=0,
            metadata={
                'login_method': 'password',
                'session_key': request.session.session_key,
            }
        )
        
        # Update user's last login IP
        user.last_login_ip = get_client_ip(request)
        user.failed_login_attempts = 0  # Reset failed attempts
        user.save(update_fields=['last_login_ip', 'failed_login_attempts'])
        
        # Create activity log
        ActivityLog.objects.create(
            admin_user=user,
            action='login',
            description=f"Admin user logged in: {user.username}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            module='authentication',
            severity='low',
            is_successful=True
        )


@receiver(user_login_failed)
def log_admin_login_failure(sender, credentials, request, **kwargs):
    """Log failed admin login attempts."""
    username = credentials.get('username', '')
    ip_address = get_client_ip(request)
    
    # Try to find the admin user
    admin_user = None
    try:
        admin_user = AdminUser.objects.get(username=username)
        admin_user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if admin_user.failed_login_attempts >= 5:
            admin_user.lock_account(duration_minutes=60)
            
        admin_user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    except AdminUser.DoesNotExist:
        pass
    
    # Create login attempt record
    AdminLoginAttempt.objects.create(
        username=username,
        admin_user=admin_user,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        is_successful=False,
        failure_reason='invalid_credentials',
        is_suspicious=check_suspicious_login(ip_address, username),
        risk_score=calculate_risk_score(ip_address, username),
        metadata={
            'attempted_username': username,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Create activity log
    ActivityLog.objects.create(
        admin_user=admin_user,
        action='login',
        description=f"Failed login attempt for: {username}",
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        module='authentication',
        severity='medium',
        is_successful=False,
        error_message='Invalid credentials'
    )


@receiver(user_logged_out)
def log_admin_logout(sender, request, user, **kwargs):
    """Log admin logout."""
    if hasattr(user, 'role') and isinstance(user, AdminUser):
        # Deactivate admin session
        try:
            session = AdminSession.objects.get(
                admin_user=user,
                session_key=request.session.session_key,
                is_active=True
            )
            session.is_active = False
            session.save(update_fields=['is_active'])
        except AdminSession.DoesNotExist:
            pass
        
        # Create activity log
        ActivityLog.objects.create(
            admin_user=user,
            action='logout',
            description=f"Admin user logged out: {user.username}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            module='authentication',
            severity='low',
            is_successful=True
        )


@receiver(post_delete)
def log_model_deletions(sender, instance, **kwargs):
    """Log deletions of important models."""
    # Only log deletions for admin panel models
    if sender._meta.app_label == 'admin_panel':
        ActivityLog.objects.create(
            action='delete',
            description=f"{sender._meta.verbose_name} deleted: {str(instance)}",
            content_type=ContentType.objects.get_for_model(sender),
            object_id=str(instance.pk),
            changes={'deleted_object': str(instance)},
            ip_address='127.0.0.1',  # Will be updated by middleware
            module=sender._meta.app_label,
            severity='high',
            is_successful=True
        )


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


def check_suspicious_login(ip_address, username):
    """Check if login attempt is suspicious."""
    # Check for multiple failed attempts from same IP
    recent_failures = AdminLoginAttempt.objects.filter(
        ip_address=ip_address,
        is_successful=False,
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    
    if recent_failures >= 3:
        return True
    
    # Check for attempts on multiple usernames from same IP
    unique_usernames = AdminLoginAttempt.objects.filter(
        ip_address=ip_address,
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).values_list('username', flat=True).distinct().count()
    
    if unique_usernames >= 5:
        return True
    
    return False


def calculate_risk_score(ip_address, username):
    """Calculate risk score for login attempt."""
    score = 0
    
    # Base score for failed attempt
    score += 20
    
    # Additional score for multiple failures from same IP
    recent_failures = AdminLoginAttempt.objects.filter(
        ip_address=ip_address,
        is_successful=False,
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).count()
    score += min(recent_failures * 10, 50)
    
    # Additional score for multiple username attempts
    unique_usernames = AdminLoginAttempt.objects.filter(
        ip_address=ip_address,
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).values_list('username', flat=True).distinct().count()
    score += min(unique_usernames * 5, 30)
    
    return min(score, 100)  # Cap at 100