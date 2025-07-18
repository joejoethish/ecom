"""
Core serializers for the ecommerce platform.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer with common fields and methods.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for public information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'is_verified', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']


class TimestampSerializer(serializers.Serializer):
    """
    Serializer for timestamp fields.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class PaginationSerializer(serializers.Serializer):
    """
    Serializer for pagination metadata.
    """
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    current_page = serializers.IntegerField()


class ErrorSerializer(serializers.Serializer):
    """
    Serializer for error responses.
    """
    message = serializers.CharField()
    code = serializers.CharField()
    status_code = serializers.IntegerField()
    details = serializers.JSONField(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """
    Serializer for successful API responses.
    """
    success = serializers.BooleanField(default=True)
    data = serializers.JSONField(required=False)
    message = serializers.CharField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for error API responses.
    """
    success = serializers.BooleanField(default=False)
    error = ErrorSerializer()