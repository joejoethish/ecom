"""
Authentication models for the ecommerce platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
from core.models import TimestampedModel


class User(AbstractUser, TimestampedModel):
    """
    Custom user model extending Django's AbstractUser with profile fields.
    """
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
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
        max_length=15, 
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
    
    # Status fields
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
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
        return self.user_type == 'admin' or self.is_staff

    def get_avatar_url(self):
        """Get avatar URL or return default."""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'


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
    Track user sessions for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}..."


class PasswordResetToken(TimestampedModel):
    """
    Model to store password reset tokens for secure password reset functionality.
    Tokens are hashed before storage for security.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hash of the token
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Reset token for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def save(self, *args, **kwargs):
        """Override save to set expiration time if not provided."""
        if not self.expires_at:
            # Set expiration to 1 hour from creation as per requirements
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)


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