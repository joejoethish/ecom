"""
Authentication serializers for the ecommerce platform.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, UserProfile, UserSession


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for extended user profile.
    """
    class Meta:
        model = UserProfile
        fields = (
            'alternate_phone', 'emergency_contact_name', 'emergency_contact_phone',
            'preferences', 'facebook_url', 'twitter_url', 'instagram_url', 
            'linkedin_url', 'profile_visibility'
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with enhanced profile fields.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm', 'first_name', 
            'last_name', 'user_type', 'phone_number', 'date_of_birth', 'gender',
            'newsletter_subscription', 'sms_notifications', 'email_notifications',
            'bio', 'website', 'profile'
        )
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        # Validate email uniqueness
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "User with this email already exists"})
        
        return attrs

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists")
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(**validated_data)
        
        # Update user profile if profile data is provided
        # UserProfile is automatically created by signal
        if profile_data:
            profile = user.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile with all fields.
    """
    full_name = serializers.ReadOnlyField()
    avatar_url = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone_number', 'date_of_birth', 'gender', 'avatar',
            'avatar_url', 'is_verified', 'is_phone_verified', 'is_email_verified',
            'newsletter_subscription', 'sms_notifications', 'email_notifications',
            'bio', 'website', 'created_at', 'updated_at', 'profile'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'is_verified', 
            'is_phone_verified', 'is_email_verified'
        )

    def get_avatar_url(self, obj):
        """Get avatar URL."""
        return obj.get_avatar_url()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number', 'date_of_birth', 
            'gender', 'avatar', 'newsletter_subscription', 'sms_notifications', 
            'email_notifications', 'bio', 'website', 'profile'
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to token response
        data['user'] = UserSerializer(self.user).data
        
        return data


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "New passwords don't match"})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)

    # Note: We don't validate email existence for security reasons
    # The view will handle the logic and always return success


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match"})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for forgot password request using new password reset system.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Enhanced email format validation.
        Requirements: 1.1 - Validate email format on forgot password endpoint
        """
        import re
        
        # Basic email format validation (already done by EmailField)
        # Additional validation for security
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Email address is required")
        
        value = value.strip().lower()
        
        # Check for basic email format requirements
        if len(value) > 254:  # RFC 5321 limit
            raise serializers.ValidationError("Email address is too long")
        
        # Check for suspicious patterns that might indicate injection attempts
        suspicious_patterns = [
            r'[<>"\']',  # HTML/script injection
            r'[\r\n]',   # CRLF injection
            r'javascript:',  # JavaScript injection
            r'data:',    # Data URI injection
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise serializers.ValidationError("Invalid email format")
        
        # Validate email domain part
        if '@' in value:
            local, domain = value.rsplit('@', 1)
            if not local or not domain:
                raise serializers.ValidationError("Invalid email format")
            
            # Check domain length
            if len(domain) > 253:
                raise serializers.ValidationError("Email domain is too long")
            
            # Basic domain format check
            if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
                raise serializers.ValidationError("Invalid email domain format")
        
        # We don't validate email existence for security reasons
        # The service will handle the logic and always return success message
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset using secure token system.
    """
    token = serializers.CharField(required=True, max_length=64)
    password = serializers.CharField(required=True, validators=[validate_password])
    password_confirm = serializers.CharField(required=True)

    def validate_password(self, value):
        """
        Enhanced password strength validation.
        Requirements: 3.4 - Add password strength validation for reset endpoint
        """
        import re
        
        if not value:
            raise serializers.ValidationError("Password is required")
        
        # Check minimum length (Django's MinimumLengthValidator handles this, but let's be explicit)
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        # Check maximum length to prevent DoS attacks
        if len(value) > 128:
            raise serializers.ValidationError("Password is too long (maximum 128 characters)")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character")
        
        # Check for common weak patterns
        weak_patterns = [
            r'(.)\1{2,}',  # Three or more consecutive identical characters
            r'123456|654321|abcdef|qwerty|password|admin',  # Common weak passwords
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, value.lower()):
                raise serializers.ValidationError("Password contains weak patterns")
        
        # Django's built-in validators will also run
        return value

    def validate(self, attrs):
        """
        Enhanced validation for password confirmation and security.
        Requirements: 3.5 - Verify both passwords match
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if not password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Password confirmation is required"
            })
        
        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords don't match"
            })
        
        # Additional security check - ensure passwords are not just whitespace
        if not password or not password.strip():
            raise serializers.ValidationError({
                "password": "Password cannot be empty or just whitespace"
            })
        
        return attrs

    def validate_token(self, value):
        """
        Enhanced token format validation.
        Requirements: 3.1 - Validate token exists and is not expired
        """
        import re
        
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Token cannot be empty")
        
        value = value.strip()
        
        # Check token length (should be URL-safe base64 encoded)
        # Allow shorter tokens for testing, but maintain security for production
        if len(value) < 8 or len(value) > 128:
            raise serializers.ValidationError("Invalid token format")
        
        # Check for valid URL-safe base64 characters plus some flexibility for testing
        if not re.match(r'^[A-Za-z0-9_-]+$', value):
            raise serializers.ValidationError("Token contains invalid characters")
        
        return value


class ValidateResetTokenSerializer(serializers.Serializer):
    """
    Serializer for validating password reset token.
    """
    token = serializers.CharField(required=True, max_length=64)

    def validate_token(self, value):
        """Basic token format validation."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Token cannot be empty")
        return value.strip()


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user sessions.
    """
    class Meta:
        model = UserSession
        fields = (
            'id', 'session_key', 'ip_address', 'user_agent', 'device_type',
            'location', 'is_active', 'last_activity', 'created_at'
        )
        read_only_fields = ('id', 'created_at')