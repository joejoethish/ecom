"""
Communications serializers for API responses.
"""
from rest_framework import serializers
from .models import (
    EmailTemplate, EmailCampaign, EmailRecipient, EmailAutomation,
    EmailAutomationInstance, EmailList, EmailSubscriber, EmailAnalytics,
    EmailDeliverabilitySettings, EmailSuppressionList
)


class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'subject',
            'html_content', 'text_content', 'variables', 'design_settings',
            'is_active', 'is_system_template', 'usage_count', 'created_by',
            'created_by_name', 'preview_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'usage_count', 'created_by_name', 'created_at', 'updated_at'
        ]


class EmailTemplateCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating email templates.
    """
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'description', 'template_type', 'subject', 'html_content',
            'text_content', 'variables', 'design_settings', 'is_active',
            'preview_data'
        ]

    def validate_variables(self, value):
        """Validate template variables format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Variables must be a list")
        
        for var in value:
            if not isinstance(var, str):
                raise serializers.ValidationError("Each variable must be a string")
            if not var.startswith('{{') or not var.endswith('}}'):
                raise serializers.ValidationError("Variables must be in {{variable}} format")
        
        return value


class EmailRecipientSerializer(serializers.ModelSerializer):
    """
    Serializer for email recipients.
    """
    class Meta:
        model = EmailRecipient
        fields = [
            'id', 'campaign', 'email', 'name', 'status', 'customer_id',
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
            'personalization_data', 'error_message', 'bounce_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
            'bounced_at', 'created_at', 'updated_at'
        ]


class EmailCampaignSerializer(serializers.ModelSerializer):
    """
    Serializer for email campaigns.
    """
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    bounce_rate = serializers.FloatField(read_only=True)
    recipients_count = serializers.SerializerMethodField()

    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'description', 'campaign_type', 'status', 'template',
            'template_name', 'subject', 'html_content', 'text_content',
            'from_name', 'from_email', 'reply_to', 'scheduled_at', 'sent_at',
            'completed_at', 'target_segments', 'recipient_filters', 'is_ab_test',
            'ab_test_config', 'total_recipients', 'delivered_count', 'opened_count',
            'clicked_count', 'bounced_count', 'unsubscribed_count', 'track_opens',
            'track_clicks', 'created_by', 'created_by_name', 'open_rate',
            'click_rate', 'bounce_rate', 'recipients_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'template_name', 'created_by_name', 'sent_at', 'completed_at',
            'total_recipients', 'delivered_count', 'opened_count', 'clicked_count',
            'bounced_count', 'unsubscribed_count', 'open_rate', 'click_rate',
            'bounce_rate', 'recipients_count', 'created_at', 'updated_at'
        ]

    def get_recipients_count(self, obj):
        """Get count of recipients."""
        return obj.recipients.count()


class EmailCampaignCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating email campaigns.
    """
    class Meta:
        model = EmailCampaign
        fields = [
            'name', 'description', 'campaign_type', 'template', 'subject',
            'html_content', 'text_content', 'from_name', 'from_email',
            'reply_to', 'scheduled_at', 'target_segments', 'recipient_filters',
            'is_ab_test', 'ab_test_config', 'track_opens', 'track_clicks'
        ]

    def validate(self, data):
        """Validate campaign data."""
        if data.get('is_ab_test') and not data.get('ab_test_config'):
            raise serializers.ValidationError("A/B test configuration is required for A/B test campaigns")
        
        return data


class EmailAutomationSerializer(serializers.ModelSerializer):
    """
    Serializer for email automations.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    active_instances_count = serializers.SerializerMethodField()

    class Meta:
        model = EmailAutomation
        fields = [
            'id', 'name', 'description', 'trigger_type', 'is_active',
            'trigger_config', 'email_sequence', 'target_segments',
            'triggered_count', 'completed_count', 'created_by', 'created_by_name',
            'active_instances_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'triggered_count', 'completed_count', 'created_by_name',
            'active_instances_count', 'created_at', 'updated_at'
        ]

    def get_active_instances_count(self, obj):
        """Get count of active automation instances."""
        return obj.instances.filter(status='active').count()


class EmailAutomationInstanceSerializer(serializers.ModelSerializer):
    """
    Serializer for email automation instances.
    """
    automation_name = serializers.CharField(source='automation.name', read_only=True)

    class Meta:
        model = EmailAutomationInstance
        fields = [
            'id', 'automation', 'automation_name', 'customer_id', 'email',
            'status', 'current_step', 'next_send_at', 'context_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'automation_name', 'created_at', 'updated_at'
        ]


class EmailListSerializer(serializers.ModelSerializer):
    """
    Serializer for email lists.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    welcome_template_name = serializers.CharField(source='welcome_email_template.name', read_only=True)

    class Meta:
        model = EmailList
        fields = [
            'id', 'name', 'description', 'is_active', 'double_opt_in',
            'send_welcome_email', 'welcome_email_template', 'welcome_template_name',
            'subscriber_count', 'active_subscriber_count', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subscriber_count', 'active_subscriber_count', 'created_by_name',
            'welcome_template_name', 'created_at', 'updated_at'
        ]


class EmailSubscriberSerializer(serializers.ModelSerializer):
    """
    Serializer for email subscribers.
    """
    email_list_name = serializers.CharField(source='email_list.name', read_only=True)

    class Meta:
        model = EmailSubscriber
        fields = [
            'id', 'email_list', 'email_list_name', 'email', 'name', 'status',
            'customer_id', 'subscribed_at', 'unsubscribed_at', 'confirmed_at',
            'custom_fields', 'source', 'ip_address', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email_list_name', 'subscribed_at', 'unsubscribed_at',
            'confirmed_at', 'created_at', 'updated_at'
        ]


class EmailAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for email analytics.
    """
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    automation_name = serializers.CharField(source='automation.name', read_only=True)

    class Meta:
        model = EmailAnalytics
        fields = [
            'id', 'campaign', 'campaign_name', 'automation', 'automation_name',
            'metric_type', 'metric_value', 'date', 'segment', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'campaign_name', 'automation_name', 'created_at', 'updated_at'
        ]


class EmailDeliverabilitySettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for email deliverability settings.
    """
    class Meta:
        model = EmailDeliverabilitySettings
        fields = [
            'id', 'name', 'provider', 'is_active', 'is_default', 'configuration',
            'daily_limit', 'hourly_limit', 'reputation_score', 'emails_sent_today',
            'emails_sent_this_hour', 'last_reset_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'emails_sent_today', 'emails_sent_this_hour', 'last_reset_date',
            'created_at', 'updated_at'
        ]

    def validate_configuration(self, value):
        """Validate provider configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Configuration must be a dictionary")
        return value


class EmailSuppressionListSerializer(serializers.ModelSerializer):
    """
    Serializer for email suppression list.
    """
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    added_by_name = serializers.CharField(source='added_by.username', read_only=True)

    class Meta:
        model = EmailSuppressionList
        fields = [
            'id', 'email', 'suppression_type', 'reason', 'campaign', 'campaign_name',
            'automation', 'automation_name', 'suppressed_at', 'added_by',
            'added_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'campaign_name', 'automation_name', 'added_by_name',
            'suppressed_at', 'created_at', 'updated_at'
        ]


# Dashboard and Analytics Serializers

class EmailDashboardSerializer(serializers.Serializer):
    """
    Serializer for email dashboard data.
    """
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_subscribers = serializers.IntegerField()
    emails_sent_today = serializers.IntegerField()
    avg_open_rate = serializers.FloatField()
    avg_click_rate = serializers.FloatField()
    recent_campaigns = EmailCampaignSerializer(many=True)
    top_performing_campaigns = EmailCampaignSerializer(many=True)


class EmailPerformanceSerializer(serializers.Serializer):
    """
    Serializer for email performance analytics.
    """
    campaign_id = serializers.IntegerField()
    campaign_name = serializers.CharField()
    sent_count = serializers.IntegerField()
    delivered_count = serializers.IntegerField()
    opened_count = serializers.IntegerField()
    clicked_count = serializers.IntegerField()
    bounced_count = serializers.IntegerField()
    unsubscribed_count = serializers.IntegerField()
    open_rate = serializers.FloatField()
    click_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()


class EmailTemplatePreviewSerializer(serializers.Serializer):
    """
    Serializer for email template preview.
    """
    template_id = serializers.IntegerField()
    preview_data = serializers.DictField()
    render_html = serializers.BooleanField(default=True)
    render_text = serializers.BooleanField(default=False)


class EmailCampaignTestSerializer(serializers.Serializer):
    """
    Serializer for sending test emails.
    """
    campaign_id = serializers.IntegerField()
    test_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=10
    )
    personalization_data = serializers.DictField(required=False)


class EmailBulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk email actions.
    """
    action = serializers.ChoiceField(choices=[
        'pause', 'resume', 'cancel', 'delete', 'duplicate'
    ])
    campaign_ids = serializers.ListField(child=serializers.IntegerField())
    
    def validate_campaign_ids(self, value):
        """Validate campaign IDs exist."""
        if not value:
            raise serializers.ValidationError("At least one campaign ID is required")
        return value


class EmailSegmentationSerializer(serializers.Serializer):
    """
    Serializer for email segmentation criteria.
    """
    segment_name = serializers.CharField(max_length=200)
    criteria = serializers.DictField()
    estimated_size = serializers.IntegerField(read_only=True)


class EmailA11yTestSerializer(serializers.Serializer):
    """
    Serializer for email accessibility testing.
    """
    template_id = serializers.IntegerField()
    test_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'color_contrast', 'alt_text', 'semantic_structure',
            'keyboard_navigation', 'screen_reader'
        ]),
        default=['color_contrast', 'alt_text', 'semantic_structure']
    )