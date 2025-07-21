from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    NotificationTemplate, NotificationPreference, Notification,
    NotificationLog, NotificationBatch, NotificationAnalytics
)

User = get_user_model()


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for notification templates
    """
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'channel', 'channel_display', 'subject_template', 'body_template',
            'html_template', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate template data
        """
        # Ensure unique combination of template_type and channel
        template_type = data.get('template_type')
        channel = data.get('channel')
        
        if template_type and channel:
            queryset = NotificationTemplate.objects.filter(
                template_type=template_type,
                channel=channel
            )
            
            # Exclude current instance if updating
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Template for {template_type} - {channel} already exists"
                )
        
        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for notification preferences
    """
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'is_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationPreferenceUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk updating notification preferences
    """
    preferences = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        write_only=True
    )
    
    def validate_preferences(self, value):
        """
        Validate preferences data
        """
        valid_notification_types = [choice[0] for choice in NotificationPreference.NOTIFICATION_TYPES]
        valid_channels = [choice[0] for choice in NotificationPreference.CHANNELS]
        
        for pref in value:
            if 'notification_type' not in pref:
                raise serializers.ValidationError("notification_type is required")
            if 'channel' not in pref:
                raise serializers.ValidationError("channel is required")
            if 'is_enabled' not in pref:
                raise serializers.ValidationError("is_enabled is required")
            
            if pref['notification_type'] not in valid_notification_types:
                raise serializers.ValidationError(f"Invalid notification_type: {pref['notification_type']}")
            if pref['channel'] not in valid_channels:
                raise serializers.ValidationError(f"Invalid channel: {pref['channel']}")
            
            # Convert is_enabled to boolean
            if isinstance(pref['is_enabled'], str):
                pref['is_enabled'] = pref['is_enabled'].lower() in ['true', '1', 'yes']
        
        return value


class NotificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for notification logs
    """
    class Meta:
        model = NotificationLog
        fields = ['id', 'action', 'details', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications
    """
    user = serializers.StringRelatedField(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    logs = NotificationLogSerializer(many=True, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_retry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'template', 'channel', 'channel_display',
            'priority', 'priority_display', 'status', 'status_display',
            'subject', 'message', 'html_content', 'recipient_email',
            'recipient_phone', 'sent_at', 'delivered_at', 'read_at',
            'scheduled_at', 'expires_at', 'metadata', 'external_id',
            'error_message', 'retry_count', 'max_retries',
            'is_expired', 'can_retry', 'logs', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'sent_at', 'delivered_at', 'read_at', 'external_id',
            'error_message', 'retry_count', 'is_expired', 'can_retry',
            'logs', 'created_at', 'updated_at'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications
    """
    template_type = serializers.CharField(write_only=True)
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=Notification.CHANNELS),
        write_only=True,
        required=False
    )
    context_data = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = Notification
        fields = [
            'template_type', 'channels', 'context_data', 'priority',
            'scheduled_at', 'expires_at'
        ]
    
    def validate_template_type(self, value):
        """
        Validate template type exists
        """
        if not NotificationTemplate.objects.filter(template_type=value, is_active=True).exists():
            raise serializers.ValidationError(f"No active templates found for type: {value}")
        return value
    
    def validate_scheduled_at(self, value):
        """
        Validate scheduled time is in the future
        """
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value
    
    def validate_expires_at(self, value):
        """
        Validate expiry time is in the future
        """
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry time must be in the future")
        return value


class NotificationBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for notification batches
    """
    template = NotificationTemplateSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'name', 'template', 'status', 'status_display',
            'total_recipients', 'sent_count', 'delivered_count', 'failed_count',
            'success_rate', 'target_criteria', 'scheduled_at', 'started_at',
            'completed_at', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'template', 'sent_count', 'delivered_count', 'failed_count',
            'started_at', 'completed_at', 'created_by', 'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        """
        Calculate success rate for the batch
        """
        if obj.total_recipients > 0:
            return round((obj.sent_count / obj.total_recipients) * 100, 2)
        return 0


class NotificationBatchCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notification batches
    """
    template_type = serializers.CharField(write_only=True)
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=Notification.CHANNELS),
        write_only=True
    )
    context_data = serializers.JSONField(write_only=True, required=False)
    user_criteria = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = NotificationBatch
        fields = [
            'name', 'template_type', 'channels', 'context_data',
            'user_criteria', 'scheduled_at'
        ]
    
    def validate_template_type(self, value):
        """
        Validate template type exists
        """
        if not NotificationTemplate.objects.filter(template_type=value, is_active=True).exists():
            raise serializers.ValidationError(f"No active templates found for type: {value}")
        return value
    
    def validate_scheduled_at(self, value):
        """
        Validate scheduled time is in the future
        """
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value


class NotificationAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for notification analytics
    """
    template_type_display = serializers.SerializerMethodField()
    channel_display = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationAnalytics
        fields = [
            'id', 'date', 'template_type', 'template_type_display',
            'channel', 'channel_display', 'sent_count', 'delivered_count',
            'read_count', 'failed_count', 'delivery_rate', 'read_rate',
            'failure_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_template_type_display(self, obj):
        """
        Get display name for template type
        """
        template_types = dict(NotificationTemplate.TEMPLATE_TYPES)
        return template_types.get(obj.template_type, obj.template_type)
    
    def get_channel_display(self, obj):
        """
        Get display name for channel
        """
        channels = dict(NotificationTemplate.CHANNELS)
        return channels.get(obj.channel, obj.channel)


class NotificationAnalyticsSummarySerializer(serializers.Serializer):
    """
    Serializer for notification analytics summary
    """
    total_sent = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    total_read = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    overall_delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overall_read_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overall_failure_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Channel breakdown
    channel_breakdown = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Template type breakdown
    template_breakdown = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Daily trends
    daily_trends = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )


class NotificationMarkAsReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True
    )
    
    def validate_notification_ids(self, value):
        """
        Validate notification IDs exist and belong to the user
        """
        user = self.context['request'].user
        
        existing_ids = set(
            Notification.objects.filter(
                id__in=value,
                user=user
            ).values_list('id', flat=True)
        )
        
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid notification IDs: {list(invalid_ids)}"
            )
        
        return value


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics
    """
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    
    # Channel breakdown
    email_count = serializers.IntegerField()
    sms_count = serializers.IntegerField()
    push_count = serializers.IntegerField()
    in_app_count = serializers.IntegerField()
    
    # Recent activity
    today_count = serializers.IntegerField()
    this_week_count = serializers.IntegerField()
    this_month_count = serializers.IntegerField()


class NotificationSettingsSerializer(serializers.Serializer):
    """
    Serializer for notification settings overview
    """
    user_preferences = NotificationPreferenceSerializer(many=True, read_only=True)
    available_types = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    available_channels = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )