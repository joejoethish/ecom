from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import (
    Tenant, TenantUser, TenantSubscription, TenantUsage,
    TenantInvitation, TenantAuditLog, TenantBackup
)


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""
    users_count = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'domain', 'subdomain',
            'logo', 'primary_color', 'secondary_color', 'favicon',
            'plan', 'status', 'trial_ends_at', 'subscription_starts_at', 'subscription_ends_at',
            'max_users', 'max_products', 'max_orders', 'max_storage_gb',
            'contact_name', 'contact_email', 'contact_phone',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'timezone', 'currency', 'language',
            'features', 'custom_settings',
            'created_at', 'updated_at', 'is_active',
            'users_count', 'subscription_status', 'usage_stats'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'users_count', 'subscription_status', 'usage_stats']
    
    def get_users_count(self, obj):
        return obj.users.count()
    
    def get_subscription_status(self, obj):
        if hasattr(obj, 'subscription'):
            return {
                'plan': obj.subscription.plan_name,
                'status': obj.subscription.payment_status,
                'next_billing': obj.subscription.next_billing_date,
            }
        return None
    
    def get_usage_stats(self, obj):
        latest_usage = obj.usage_records.first()
        if latest_usage:
            return {
                'users': latest_usage.users_count,
                'storage_gb': float(latest_usage.storage_used_gb),
                'api_calls': latest_usage.api_calls_count,
            }
        return None


class TenantCreateSerializer(serializers.Serializer):
    """Serializer for creating new tenant"""
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=100)
    subdomain = serializers.CharField(max_length=100)
    contact_name = serializers.CharField(max_length=200)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=20, required=False)
    plan = serializers.ChoiceField(choices=Tenant.PLAN_CHOICES, default='starter')
    
    # Owner details
    owner_username = serializers.CharField(max_length=150)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(write_only=True)
    owner_first_name = serializers.CharField(max_length=30, required=False)
    owner_last_name = serializers.CharField(max_length=150, required=False)
    
    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Tenant with this slug already exists.")
        return value
    
    def validate_subdomain(self, value):
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("Tenant with this subdomain already exists.")
        return value
    
    def validate_owner_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'avatar', 'department', 'job_title',
            'permissions', 'last_login', 'last_login_ip',
            'failed_login_attempts', 'account_locked_until',
            'preferences', 'invited_at', 'invited_by',
            'is_active', 'date_joined', 'tenant_name'
        ]
        read_only_fields = [
            'id', 'last_login', 'last_login_ip', 'failed_login_attempts',
            'account_locked_until', 'invited_at', 'invited_by', 'date_joined', 'tenant_name'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class TenantUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tenant users"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'phone', 'department', 'job_title', 'permissions'
        ]
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = TenantUser.objects.create_user(password=password, **validated_data)
        return user


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for TenantSubscription model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    days_until_renewal = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantSubscription
        fields = [
            'id', 'tenant_name', 'plan_name', 'billing_cycle',
            'amount', 'currency', 'next_billing_date', 'last_billing_date',
            'payment_method', 'payment_status',
            'stripe_subscription_id', 'stripe_customer_id',
            'created_at', 'updated_at', 'days_until_renewal'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant_name', 'days_until_renewal']
    
    def get_days_until_renewal(self, obj):
        if obj.next_billing_date:
            from django.utils import timezone
            delta = obj.next_billing_date - timezone.now()
            return delta.days
        return None


class TenantUsageSerializer(serializers.ModelSerializer):
    """Serializer for TenantUsage model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    period_days = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUsage
        fields = [
            'id', 'tenant_name', 'users_count', 'products_count', 'orders_count',
            'storage_used_gb', 'api_calls_count', 'avg_response_time',
            'error_rate', 'uptime_percentage',
            'period_start', 'period_end', 'period_days', 'created_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'period_days', 'created_at']
    
    def get_period_days(self, obj):
        delta = obj.period_end - obj.period_start
        return delta.days


class TenantInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TenantInvitation model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'tenant_name', 'email', 'role', 'invited_by_name',
            'status', 'expires_at', 'is_expired',
            'created_at', 'accepted_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'invited_by_name', 'is_expired',
            'created_at', 'accepted_at'
        ]
    
    def get_is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()


class TenantInvitationCreateSerializer(serializers.Serializer):
    """Serializer for creating tenant invitations"""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=TenantUser.ROLE_CHOICES)
    
    def validate_email(self, value):
        # Check if user already exists in tenant
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if TenantUser.objects.filter(tenant=request.tenant, email=value).exists():
                raise serializers.ValidationError("User with this email already exists in tenant.")
        return value


class TenantAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for TenantAuditLog model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TenantAuditLog
        fields = [
            'id', 'tenant_name', 'user_name', 'action', 'model_name',
            'object_id', 'object_repr', 'changes',
            'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'tenant_name', 'user_name', 'timestamp']


class TenantBackupSerializer(serializers.ModelSerializer):
    """Serializer for TenantBackup model"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantBackup
        fields = [
            'id', 'tenant_name', 'backup_type', 'status',
            'file_path', 'file_size', 'file_size_mb',
            'progress_percentage', 'error_message',
            'started_at', 'completed_at', 'duration', 'created_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'file_size_mb', 'duration',
            'started_at', 'completed_at', 'created_at'
        ]
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return str(delta)
        return None


class TenantDashboardSerializer(serializers.Serializer):
    """Serializer for tenant dashboard data"""
    tenant = TenantSerializer(read_only=True)
    stats = serializers.DictField(read_only=True)
    recent_activity = TenantAuditLogSerializer(many=True, read_only=True)
    usage_chart_data = serializers.ListField(read_only=True)
    alerts = serializers.ListField(read_only=True)


class TenantSettingsSerializer(serializers.Serializer):
    """Serializer for tenant settings"""
    branding = serializers.DictField()
    features = serializers.DictField()
    limits = serializers.DictField()
    notifications = serializers.DictField()
    security = serializers.DictField()
    integrations = serializers.DictField()
    
    def validate_branding(self, value):
        required_fields = ['primary_color', 'secondary_color']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


class TenantAnalyticsSerializer(serializers.Serializer):
    """Serializer for tenant analytics data"""
    period = serializers.DictField(read_only=True)
    usage_summary = serializers.DictField(read_only=True)
    daily_usage = serializers.ListField(read_only=True)
    performance_metrics = serializers.DictField(read_only=True)
    cost_analysis = serializers.DictField(read_only=True)
    trends = serializers.DictField(read_only=True)