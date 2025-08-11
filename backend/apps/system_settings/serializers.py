from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingNotification, SettingAuditLog,
    SettingEnvironmentSync, SettingDataType, SettingAccessLevel
)


class SettingCategorySerializer(serializers.ModelSerializer):
    """Serializer for setting categories with hierarchy"""
    subcategories = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    settings_count = serializers.SerializerMethodField()

    class Meta:
        model = SettingCategory
        fields = [
            'id', 'name', 'display_name', 'description', 'parent',
            'order', 'icon', 'is_active', 'subcategories', 'full_path',
            'settings_count', 'created_at', 'updated_at'
        ]

    def get_subcategories(self, obj):
        if hasattr(obj, 'subcategories'):
            return SettingCategorySerializer(obj.subcategories.all(), many=True).data
        return []

    def get_full_path(self, obj):
        return obj.get_full_path()

    def get_settings_count(self, obj):
        return obj.settings.filter(is_active=True).count()


class SystemSettingSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for system settings"""
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    category_path = serializers.SerializerMethodField()
    typed_value = serializers.SerializerMethodField()
    validation_errors = serializers.SerializerMethodField()
    dependencies = serializers.SerializerMethodField()
    dependents = serializers.SerializerMethodField()
    change_history_count = serializers.SerializerMethodField()
    last_changed = serializers.SerializerMethodField()
    performance_impact = serializers.SerializerMethodField()

    class Meta:
        model = SystemSetting
        fields = [
            'id', 'key', 'display_name', 'description', 'category', 'category_name',
            'category_path', 'data_type', 'value', 'typed_value', 'default_value',
            'min_value', 'max_value', 'min_length', 'max_length', 'regex_pattern',
            'allowed_values', 'is_encrypted', 'access_level', 'allowed_roles',
            'is_active', 'is_required', 'requires_restart', 'is_sensitive',
            'environment', 'help_text', 'documentation_url', 'version',
            'validation_errors', 'dependencies', 'dependents', 'change_history_count',
            'last_changed', 'performance_impact', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['version', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_category_path(self, obj):
        return obj.category.get_full_path() if obj.category else ''

    def get_typed_value(self, obj):
        try:
            return obj.get_typed_value()
        except:
            return obj.value

    def get_validation_errors(self, obj):
        try:
            obj.clean()
            return []
        except Exception as e:
            return [str(e)]

    def get_dependencies(self, obj):
        return SettingDependencySerializer(obj.dependencies.all(), many=True).data

    def get_dependents(self, obj):
        return SettingDependencySerializer(obj.dependents.all(), many=True).data

    def get_change_history_count(self, obj):
        return obj.change_history.count()

    def get_last_changed(self, obj):
        last_change = obj.change_history.first()
        return last_change.changed_at if last_change else obj.updated_at

    def get_performance_impact(self, obj):
        from .services import SettingsPerformanceService
        return SettingsPerformanceService.analyze_performance_impact(obj)

    def validate_value(self, value):
        """Validate setting value"""
        if hasattr(self, 'instance') and self.instance:
            from .services import SettingsValidationService
            if not SettingsValidationService.validate_setting_value(self.instance, value):
                raise serializers.ValidationError("Invalid value for this setting type")
        return value


class SystemSettingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating settings"""
    
    class Meta:
        model = SystemSetting
        fields = [
            'key', 'display_name', 'description', 'category', 'data_type',
            'value', 'default_value', 'min_value', 'max_value', 'min_length',
            'max_length', 'regex_pattern', 'allowed_values', 'is_encrypted',
            'access_level', 'allowed_roles', 'is_active', 'is_required',
            'requires_restart', 'is_sensitive', 'environment', 'help_text',
            'documentation_url'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class SettingChangeHistorySerializer(serializers.ModelSerializer):
    """Serializer for setting change history"""
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    setting_display_name = serializers.CharField(source='setting.display_name', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = SettingChangeHistory
        fields = [
            'id', 'setting', 'setting_key', 'setting_display_name', 'old_value',
            'new_value', 'version', 'change_reason', 'changed_by', 'changed_by_name',
            'changed_at', 'ip_address', 'user_agent', 'requires_approval',
            'approved_by', 'approved_by_name', 'approved_at', 'approval_status'
        ]


class SettingBackupSerializer(serializers.ModelSerializer):
    """Serializer for setting backups"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    settings_count = serializers.SerializerMethodField()
    backup_size = serializers.SerializerMethodField()

    class Meta:
        model = SettingBackup
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_name',
            'created_at', 'environment', 'backup_type', 'settings_count',
            'backup_size'
        ]
        read_only_fields = ['backup_data', 'created_by', 'created_at']

    def get_settings_count(self, obj):
        return len(obj.backup_data.get('settings', []))

    def get_backup_size(self, obj):
        import sys
        return sys.getsizeof(str(obj.backup_data))


class SettingBackupCreateSerializer(serializers.Serializer):
    """Serializer for creating backups"""
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    environment = serializers.CharField(max_length=50, default='production')


class SettingBackupRestoreSerializer(serializers.Serializer):
    """Serializer for restoring backups"""
    conflict_resolution = serializers.ChoiceField(
        choices=['skip', 'overwrite', 'version'],
        default='skip'
    )


class SettingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for setting templates"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    settings_count = serializers.SerializerMethodField()

    class Meta:
        model = SettingTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'is_public', 'created_by', 'created_by_name', 'created_at',
            'updated_at', 'usage_count', 'settings_count'
        ]
        read_only_fields = ['template_data', 'created_by', 'usage_count']

    def get_settings_count(self, obj):
        return len(obj.template_data.get('settings', []))


class SettingTemplateCreateSerializer(serializers.Serializer):
    """Serializer for creating templates"""
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField()
    is_public = serializers.BooleanField(default=False)


class SettingTemplateApplySerializer(serializers.Serializer):
    """Serializer for applying templates"""
    overwrite_existing = serializers.BooleanField(default=False)


class SettingDependencySerializer(serializers.ModelSerializer):
    """Serializer for setting dependencies"""
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    setting_display_name = serializers.CharField(source='setting.display_name', read_only=True)
    depends_on_key = serializers.CharField(source='depends_on.key', read_only=True)
    depends_on_display_name = serializers.CharField(source='depends_on.display_name', read_only=True)

    class Meta:
        model = SettingDependency
        fields = [
            'id', 'setting', 'setting_key', 'setting_display_name',
            'depends_on', 'depends_on_key', 'depends_on_display_name',
            'dependency_type', 'condition'
        ]


class SettingNotificationSerializer(serializers.ModelSerializer):
    """Serializer for setting notifications"""
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    setting_display_name = serializers.CharField(source='setting.display_name', read_only=True)

    class Meta:
        model = SettingNotification
        fields = [
            'id', 'setting', 'setting_key', 'setting_display_name',
            'notification_type', 'recipients', 'trigger_conditions',
            'is_active', 'created_at'
        ]


class SettingAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for setting audit logs"""
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    setting_display_name = serializers.CharField(source='setting.display_name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = SettingAuditLog
        fields = [
            'id', 'setting', 'setting_key', 'setting_display_name',
            'action', 'user', 'user_name', 'timestamp', 'ip_address',
            'user_agent', 'details', 'compliance_flags'
        ]


class SettingEnvironmentSyncSerializer(serializers.ModelSerializer):
    """Serializer for environment synchronization"""
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    setting_display_name = serializers.CharField(source='setting.display_name', read_only=True)

    class Meta:
        model = SettingEnvironmentSync
        fields = [
            'id', 'setting', 'setting_key', 'setting_display_name',
            'source_environment', 'target_environment', 'sync_status',
            'last_sync_at', 'sync_details'
        ]


class SettingSearchSerializer(serializers.Serializer):
    """Serializer for settings search"""
    query = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False)
    environment = serializers.CharField(max_length=50, default='production')
    data_type = serializers.ChoiceField(choices=SettingDataType.choices, required=False)
    access_level = serializers.ChoiceField(choices=SettingAccessLevel.choices, required=False)
    requires_restart = serializers.BooleanField(required=False)
    is_sensitive = serializers.BooleanField(required=False)


class SettingBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating settings"""
    settings = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    change_reason = serializers.CharField(required=False, allow_blank=True)


class SettingExportSerializer(serializers.Serializer):
    """Serializer for exporting settings"""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    environment = serializers.CharField(max_length=50, default='production')
    format = serializers.ChoiceField(choices=['json', 'yaml', 'csv'], default='json')
    include_sensitive = serializers.BooleanField(default=False)


class SettingImportSerializer(serializers.Serializer):
    """Serializer for importing settings"""
    file = serializers.FileField()
    format = serializers.ChoiceField(choices=['json', 'yaml', 'csv'])
    conflict_resolution = serializers.ChoiceField(
        choices=['skip', 'overwrite', 'version'],
        default='skip'
    )
    validate_only = serializers.BooleanField(default=False)


class SettingComplianceSerializer(serializers.Serializer):
    """Serializer for compliance reporting"""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    compliance_flags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    environment = serializers.CharField(max_length=50, default='production')


class SettingMonitoringSerializer(serializers.Serializer):
    """Serializer for settings monitoring"""
    setting_keys = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    alert_thresholds = serializers.DictField(
        child=serializers.CharField(),
        required=False
    )
    notification_channels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )