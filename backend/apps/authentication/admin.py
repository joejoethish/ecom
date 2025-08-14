"""
Django admin configuration for authentication models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, UserProfile, UserSession, EmailVerification, 
    EmailVerificationAttempt, PasswordReset, PasswordResetAttempt
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    """
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'user_type',
        'is_verified', 'is_email_verified', 'is_phone_verified',
        'is_active', 'is_staff', 'failed_login_attempts', 'created_at'
    )
    list_filter = (
        'user_type', 'is_verified', 'is_email_verified', 'is_phone_verified',
        'is_active', 'is_staff', 'is_superuser', 'account_locked_until', 'created_at'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'date_of_birth', 'gender', 'avatar', 'bio', 'website'
            )
        }),
        (_('User Type'), {'fields': ('user_type',)}),
        (_('Verification Status'), {
            'fields': ('is_verified', 'is_email_verified', 'is_phone_verified')
        }),
        (_('Security'), {
            'fields': ('last_login_ip', 'failed_login_attempts', 'account_locked_until', 'password_changed_at')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Preferences'), {
            'fields': ('newsletter_subscription', 'sms_notifications', 'email_notifications')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = (
        'user', 'alternate_phone', 'emergency_contact_name',
        'profile_visibility', 'created_at'
    )
    list_filter = ('profile_visibility', 'created_at')
    search_fields = (
        'user__email', 'user__username', 'alternate_phone',
        'emergency_contact_name', 'emergency_contact_phone'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Contact Information'), {
            'fields': ('alternate_phone', 'emergency_contact_name', 'emergency_contact_phone')
        }),
        (_('Social Media'), {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        (_('Privacy'), {'fields': ('profile_visibility',)}),
        (_('Preferences'), {'fields': ('preferences',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserSession model.
    """
    list_display = (
        'user', 'session_key_short', 'ip_address', 'device_name_display',
        'login_method', 'is_active', 'last_activity', 'created_at'
    )
    list_filter = ('login_method', 'is_active', 'created_at', 'last_activity')
    search_fields = ('user__email', 'user__username', 'ip_address', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'last_activity')
    ordering = ('-last_activity',)

    def session_key_short(self, obj):
        """Display shortened session key."""
        return f"{obj.session_key[:8]}..." if obj.session_key else ""
    session_key_short.short_description = 'Session Key'

    def device_name_display(self, obj):
        """Display device name from device_info."""
        return obj.device_name
    device_name_display.short_description = 'Device'

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Session Info'), {
            'fields': ('session_key', 'ip_address', 'user_agent', 'device_info', 'location', 'login_method')
        }),
        (_('Status'), {'fields': ('is_active',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at', 'last_activity')}),
    )

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmailVerification model.
    """
    list_display = (
        'user', 'token_short', 'is_used', 'is_expired_display',
        'expires_at', 'created_at'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('created_at', 'updated_at', 'token')
    ordering = ('-created_at',)

    def token_short(self, obj):
        """Display shortened token."""
        return f"{obj.token[:8]}..." if obj.token else ""
    token_short.short_description = 'Token'

    def is_expired_display(self, obj):
        """Display if token is expired."""
        return obj.is_expired
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Token Info'), {'fields': ('token', 'expires_at', 'is_used')}),
        (_('Request Info'), {'fields': ('ip_address',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(EmailVerificationAttempt)
class EmailVerificationAttemptAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmailVerificationAttempt model.
    """
    list_display = (
        'email', 'ip_address', 'success', 'created_at'
    )
    list_filter = ('success', 'created_at')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Attempt Info'), {'fields': ('email', 'ip_address', 'success')}),
        (_('Request Details'), {'fields': ('user_agent',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """
    Admin configuration for PasswordReset model.
    """
    list_display = (
        'user', 'token_short', 'is_used', 'is_expired_display',
        'expires_at', 'created_at'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('created_at', 'updated_at', 'token')
    ordering = ('-created_at',)

    def token_short(self, obj):
        """Display shortened token."""
        return f"{obj.token[:8]}..." if obj.token else ""
    token_short.short_description = 'Token'

    def is_expired_display(self, obj):
        """Display if token is expired."""
        return obj.is_expired
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Token Info'), {'fields': ('token', 'expires_at', 'is_used')}),
        (_('Request Info'), {'fields': ('ip_address', 'user_agent')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    """
    Admin configuration for PasswordResetAttempt model.
    """
    list_display = (
        'email', 'ip_address', 'success', 'created_at'
    )
    list_filter = ('success', 'created_at')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Attempt Info'), {'fields': ('email', 'ip_address', 'success')}),
        (_('Request Details'), {'fields': ('user_agent',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )