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