"""
Serializers for the admin panel RBAC system.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    AdminUser, AdminRole, AdminPermission, SystemSettings,
    ActivityLog, AdminSession, AdminNotification, AdminLoginAttempt,
    AdminReport
)


class AdminPermissionSerializer(serializers.ModelSerializer):
    """Serializer for admin permissions."""
    
    depends_on_permissions = serializers.StringRelatedField(many=True, read_only=True)
    dependent_permissions = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = AdminPermission
        fields = [
            'id', 'codename', 'name', 'description', 'module', 'action', 'resource',
            'is_sensitive', 'requires_mfa', 'ip_restricted', 'depends_on_permissions',
            'dependent_permissions', 'is_active', 'is_system_permission', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_system_permission']


class AdminRoleSerializer(serializers.ModelSerializer):
    """Serializer for admin roles."""
    
    permissions = AdminPermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    child_roles = serializers.StringRelatedField(many=True, read_only=True)
    parent_role_name = serializers.CharField(source='parent_role.display_name', read_only=True)
    all_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminRole
        fields = [
            'id', 'name', 'display_name', 'description', 'parent_role', 'level',
            'permissions', 'permission_ids', 'child_roles', 'parent_role_name',
            'all_permissions', 'is_active', 'is_system_role', 'created_at'
        ]
        read_only_fields = ['id', 'level', 'created_at', 'is_system_role']
    
    def get_all_permissions(self, obj):
        """Get all permissions including inherited ones."""
        permissions = obj.get_all_permissions()
        return AdminPermissionSerializer(permissions, many=True).data
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = super().create(validated_data)
        
        if permission_ids:
            permissions = AdminPermission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        role = super().update(instance, validated_data)
        
        if permission_ids is not None:
            permissions = AdminPermission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin users."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    permissions = AdminPermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    is_account_locked = serializers.BooleanField(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display',
            'department', 'department_display', 'phone', 'avatar', 'permissions',
            'permission_ids', 'is_admin_active', 'is_account_locked', 'last_login',
            'last_login_ip', 'failed_login_attempts', 'two_factor_enabled',
            'max_concurrent_sessions', 'session_timeout_minutes', 'notes',
            'created_by', 'password', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_login', 'last_login_ip', 'failed_login_attempts',
            'is_account_locked', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        password = validated_data.pop('password', None)
        
        user = AdminUser.objects.create_user(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        if permission_ids:
            permissions = AdminPermission.objects.filter(id__in=permission_ids)
            user.permissions.set(permissions)
        
        return user
    
    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        password = validated_data.pop('password', None)
        
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        if permission_ids is not None:
            permissions = AdminPermission.objects.filter(id__in=permission_ids)
            user.permissions.set(permissions)
        
        return user


class AdminUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for admin user lists."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    is_account_locked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display',
            'department', 'department_display', 'is_admin_active', 'is_account_locked',
            'last_login', 'created_at'
        ]


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs."""
    
    admin_user_username = serializers.CharField(source='admin_user.username', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'admin_user', 'admin_user_username', 'action', 'description',
            'content_type', 'content_type_name', 'object_id', 'changes',
            'additional_data', 'ip_address', 'user_agent', 'request_method',
            'request_path', 'module', 'severity', 'is_successful', 'error_message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AdminSessionSerializer(serializers.ModelSerializer):
    """Serializer for admin sessions."""
    
    admin_user_username = serializers.CharField(source='admin_user.username', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AdminSession
        fields = [
            'id', 'session_key', 'admin_user', 'admin_user_username', 'ip_address',
            'user_agent', 'device_type', 'browser', 'os', 'location', 'country',
            'city', 'is_trusted_device', 'is_active', 'last_activity', 'expires_at',
            'is_expired', 'is_suspicious', 'security_score', 'created_at'
        ]
        read_only_fields = ['id', 'is_expired', 'created_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    """Serializer for admin notifications."""
    
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = AdminNotification
        fields = [
            'id', 'recipient', 'sender', 'sender_username', 'title', 'message',
            'notification_type', 'priority', 'content_type', 'content_type_name',
            'object_id', 'action_url', 'action_label', 'metadata', 'is_read',
            'read_at', 'is_dismissed', 'dismissed_at', 'scheduled_for',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'read_at', 'dismissed_at', 'created_at']


class AdminLoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for admin login attempts."""
    
    admin_user_username = serializers.CharField(source='admin_user.username', read_only=True)
    
    class Meta:
        model = AdminLoginAttempt
        fields = [
            'id', 'username', 'admin_user', 'admin_user_username', 'ip_address',
            'user_agent', 'is_successful', 'failure_reason', 'is_suspicious',
            'risk_score', 'country', 'city', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for system settings."""
    
    typed_value = serializers.SerializerMethodField()
    last_modified_by_username = serializers.CharField(
        source='last_modified_by.username', 
        read_only=True
    )
    
    class Meta:
        model = SystemSettings
        fields = [
            'id', 'key', 'name', 'description', 'value', 'typed_value',
            'default_value', 'setting_type', 'category', 'subcategory',
            'validation_rules', 'options', 'is_public', 'is_encrypted',
            'requires_restart', 'is_system_setting', 'last_modified_by',
            'last_modified_by_username', 'version', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'typed_value', 'is_system_setting', 'version', 'created_at'
        ]
    
    def get_typed_value(self, obj):
        """Return the typed value of the setting."""
        return obj.get_typed_value()


class AdminReportSerializer(serializers.ModelSerializer):
    """Serializer for admin reports."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    recipients_usernames = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminReport
        fields = [
            'id', 'name', 'description', 'report_type', 'query_config', 'format',
            'schedule_type', 'schedule_config', 'next_run', 'last_run',
            'recipients', 'recipients_usernames', 'email_recipients', 'is_active',
            'created_by', 'created_by_username', 'total_runs', 'successful_runs',
            'last_error', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_runs', 'successful_runs', 'last_error', 'created_at'
        ]
    
    def get_recipients_usernames(self, obj):
        """Get usernames of report recipients."""
        return [user.username for user in obj.recipients.all()]


class PermissionCheckSerializer(serializers.Serializer):
    """Serializer for permission checking requests."""
    
    permission_codename = serializers.CharField(max_length=100)
    resource_id = serializers.CharField(max_length=100, required=False)
    context = serializers.JSONField(required=False)


class BulkPermissionAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk permission assignments."""
    
    user_ids = serializers.ListField(child=serializers.UUIDField())
    permission_ids = serializers.ListField(child=serializers.IntegerField())
    action = serializers.ChoiceField(choices=['add', 'remove', 'replace'])


class PermissionElevationSerializer(serializers.Serializer):
    """Serializer for temporary permission elevation."""
    
    user_id = serializers.UUIDField()
    permission_ids = serializers.ListField(child=serializers.IntegerField())
    duration_minutes = serializers.IntegerField(min_value=1, max_value=1440)  # Max 24 hours
    reason = serializers.CharField(max_length=500)
    requires_approval = serializers.BooleanField(default=True)


class PermissionAuditSerializer(serializers.Serializer):
    """Serializer for permission audit reports."""
    
    user_id = serializers.UUIDField(required=False)
    permission_id = serializers.IntegerField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    action_type = serializers.ChoiceField(
        choices=['granted', 'revoked', 'used', 'denied'],
        required=False
    )