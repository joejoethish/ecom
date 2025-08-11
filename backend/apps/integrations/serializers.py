from rest_framework import serializers
from .models import (
    IntegrationCategory, IntegrationProvider, Integration,
    IntegrationLog, IntegrationMapping, IntegrationWebhook,
    IntegrationSync, IntegrationTemplate
)


class IntegrationCategorySerializer(serializers.ModelSerializer):
    integration_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IntegrationCategory
        fields = '__all__'
    
    def get_integration_count(self, obj):
        return obj.integrationprovider_set.filter(status='active').count()


class IntegrationProviderSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    integration_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IntegrationProvider
        fields = '__all__'
    
    def get_integration_count(self, obj):
        return obj.integration_set.filter(status='active').count()


class IntegrationSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_logo = serializers.CharField(source='provider.logo_url', read_only=True)
    category_name = serializers.CharField(source='provider.category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    last_sync_status = serializers.SerializerMethodField()
    health_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Integration
        fields = '__all__'
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
            'webhook_secret': {'write_only': True},
        }
    
    def get_last_sync_status(self, obj):
        last_sync = obj.integrationsync_set.first()
        return last_sync.status if last_sync else None
    
    def get_health_status(self, obj):
        if obj.error_count > 10:
            return 'critical'
        elif obj.error_count > 5:
            return 'warning'
        elif obj.status == 'active':
            return 'healthy'
        else:
            return 'inactive'


class IntegrationLogSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    
    class Meta:
        model = IntegrationLog
        fields = '__all__'


class IntegrationMappingSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    
    class Meta:
        model = IntegrationMapping
        fields = '__all__'


class IntegrationWebhookSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = IntegrationWebhook
        fields = '__all__'
        extra_kwargs = {
            'secret_key': {'write_only': True},
        }
    
    def get_success_rate(self, obj):
        total = obj.success_count + obj.failure_count
        return (obj.success_count / total * 100) if total > 0 else 0


class IntegrationSyncSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = IntegrationSync
        fields = '__all__'
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None
    
    def get_success_rate(self, obj):
        total = obj.records_processed
        if total > 0:
            success = obj.records_created + obj.records_updated
            return (success / total * 100)
        return 0


class IntegrationTemplateSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_logo = serializers.CharField(source='provider.logo_url', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = IntegrationTemplate
        fields = '__all__'


class IntegrationStatsSerializer(serializers.Serializer):
    total_integrations = serializers.IntegerField()
    active_integrations = serializers.IntegerField()
    failed_integrations = serializers.IntegerField()
    total_syncs_today = serializers.IntegerField()
    successful_syncs_today = serializers.IntegerField()
    failed_syncs_today = serializers.IntegerField()
    total_api_calls_today = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    top_providers = serializers.ListField()
    recent_errors = serializers.ListField()


class IntegrationTestSerializer(serializers.Serializer):
    integration_id = serializers.UUIDField()
    test_type = serializers.ChoiceField(choices=[
        ('connection', 'Connection Test'),
        ('auth', 'Authentication Test'),
        ('api', 'API Test'),
        ('webhook', 'Webhook Test'),
        ('sync', 'Sync Test'),
    ])
    test_data = serializers.JSONField(required=False)


class IntegrationConfigSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    environment = serializers.ChoiceField(choices=[
        ('production', 'Production'),
        ('sandbox', 'Sandbox'),
        ('development', 'Development'),
    ])
    configuration = serializers.JSONField()
    mappings = serializers.ListField(required=False)
    webhooks = serializers.ListField(required=False)


class BulkIntegrationActionSerializer(serializers.Serializer):
    integration_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('sync', 'Sync'),
        ('test', 'Test'),
        ('delete', 'Delete'),
    ])
    parameters = serializers.JSONField(required=False)