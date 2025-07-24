"""
Authentication serializers for API v2 with enhanced features and backward compatibility.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User


class UserSerializerV2(serializers.ModelSerializer):
    """
    Enhanced user serializer for v2 with additional fields.
    """
    full_name = serializers.SerializerMethodField()
    account_age = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_verified', 'date_joined', 'account_age',
            'last_login', 'profile_image'
        ]
        read_only_fields = ['id', 'is_active', 'is_verified', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Get user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_account_age(self, obj):
        """Get account age in days."""
        from django.utils import timezone
        if obj.date_joined:
            delta = timezone.now() - obj.date_joined
            return delta.days
        return None


class RegisterSerializerV2(serializers.ModelSerializer):
    """
    Enhanced registration serializer for v2 with additional validation.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    terms_accepted = serializers.BooleanField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'confirm_password', 'terms_accepted', 'profile_image'
        ]
    
    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value
    
    def validate_terms_accepted(self, value):
        """Validate terms are accepted."""
        if not value:
            raise serializers.ValidationError(_("You must accept the terms and conditions."))
        return value
    
    def validate(self, data):
        """Validate passwords match."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("Passwords do not match.")
            })
        return data
    
    def create(self, validated_data):
        """Create and return a new user."""
        validated_data.pop('confirm_password')
        validated_data.pop('terms_accepted')
        
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializerV2(serializers.Serializer):
    """
    Enhanced login serializer for v2 with additional features.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(required=False, default=False)
    
    def validate(self, data):
        """Validate credentials and return user."""
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
            
            if not user.is_active:
                msg = _('User account is disabled.')
                raise serializers.ValidationError(msg, code='authorization')
            
            data['user'] = user
            return data
        
        msg = _('Must include "email" and "password".')
        raise serializers.ValidationError(msg, code='authorization')


class PasswordChangeSerializerV2(serializers.Serializer):
    """
    Enhanced password change serializer for v2 with additional validation.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value
    
    def validate(self, data):
        """Validate new passwords match and differ from current."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("New passwords do not match.")
            })
        
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError({
                'new_password': _("New password must be different from current password.")
            })
        
        # Password strength validation
        password = data['new_password']
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({
                'new_password': _("Password must contain at least one digit.")
            })
        
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({
                'new_password': _("Password must contain at least one uppercase letter.")
            })
        
        if not any(char.islower() for char in password):
            raise serializers.ValidationError({
                'new_password': _("Password must contain at least one lowercase letter.")
            })
        
        return data