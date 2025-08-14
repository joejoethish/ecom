"""
Authentication models for the ecommerce platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
import secrets
import hashlib
from core.models import TimestampedModel


class User(AbstractUser, TimestampedModel):
    """
    Enhanced custom user model with email verification, security fields, and session tracking.
    """
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    # Core fields
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    
    # Profile fields
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Enhanced status fields for security
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # Security fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    # Additional profile information
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_email_verified']),
            models.Index(fields=['last_login_ip']),
            models.Index(fields=['account_locked_until']),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_customer(self):
        """Check if user is a customer."""
        return self.user_type == 'customer'

    @property
    def is_seller(self):
        """Check if user is a seller."""
        return self.user_type == 'seller'

    @property
    def is_admin_user(self):
        """Check if user is an admin."""
        return self.user_type in ['admin', 'super_admin'] or self.is_staff

    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])

    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])

    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
        self.save(update_fields=['failed_login_attempts'])

    def reset_failed_login(self):
        """Reset failed login attempts on successful login."""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])

    def get_avatar_url(self):
        """Get avatar URL or return default."""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'


class EmailVerification(TimestampedModel):
    """
    Model to store email verification tokens for secure email verification functionality.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Email verification for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def save(self, *args, **kwargs):
        """Override save to set expiration time and generate token if not provided."""
        if not self.token:
            # Generate a secure random token
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            # Set expiration to 24 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def mark_as_used(self):
        """Mark the token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])


class EmailVerificationAttempt(TimestampedModel):
    """
    Model to track email verification attempts for rate limiting and security monitoring.
    """
    ip_address = models.GenericIPAddressField()
    email = models.EmailField()
    success = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Email Verification Attempt'
        verbose_name_plural = 'Email Verification Attempts'
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} verification attempt for {self.email} from {self.ip_address}"


class UserProfile(TimestampedModel):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional profile fields
    alternate_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    
    # Preferences stored as JSON
    preferences = models.JSONField(default=dict, blank=True)
    
    # Social media links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('friends', 'Friends Only'),
        ],
        default='public'
    )
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.email} - Profile"


class UserSession(TimestampedModel):
    """
    Enhanced user session tracking for security and multi-device management.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=128, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Enhanced device information stored as JSON
    device_info = models.JSONField(default=dict, help_text="Device information including browser, OS, device type")
    
    # Location and security fields
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Session security
    login_method = models.CharField(max_length=20, default='password', choices=[
        ('password', 'Password'),
        ('social', 'Social Login'),
        ('admin', 'Admin Login'),
    ])
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}..."

    def terminate(self):
        """Terminate this session."""
        self.is_active = False
        self.save(update_fields=['is_active'])

    @property
    def device_name(self):
        """Get a human-readable device name."""
        if self.device_info:
            browser = self.device_info.get('browser', 'Unknown Browser')
            os = self.device_info.get('os', 'Unknown OS')
            return f"{browser} on {os}"
        return "Unknown Device"

    @classmethod
    def cleanup_expired_sessions(cls, days=30):
        """Clean up sessions older than specified days."""
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(last_activity__lt=cutoff_date).delete()


class PasswordReset(TimestampedModel):
    """
    Enhanced model for secure password reset functionality with token management.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Password Reset'
        verbose_name_plural = 'Password Resets'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Password reset for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def save(self, *args, **kwargs):
        """Override save to generate token and set expiration time if not provided."""
        if not self.token:
            # Generate a secure random token
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            # Set expiration to 1 hour from creation as per requirements
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def mark_as_used(self):
        """Mark the token as used to prevent reuse."""
        self.is_used = True
        self.save(update_fields=['is_used'])

    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired and used tokens."""
        cutoff_date = timezone.now()
        return cls.objects.filter(
            models.Q(expires_at__lt=cutoff_date) | models.Q(is_used=True)
        ).delete()


class PasswordResetAttempt(TimestampedModel):
    """
    Model to track password reset attempts for rate limiting and security monitoring.
    Used to implement rate limiting of 5 requests per hour per IP address.
    """
    ip_address = models.GenericIPAddressField()
    email = models.EmailField()
    success = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Password Reset Attempt'
        verbose_name_plural = 'Password Reset Attempts'
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ip_address', 'success']),
        ]
        
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} reset attempt for {self.email} from {self.ip_address}"