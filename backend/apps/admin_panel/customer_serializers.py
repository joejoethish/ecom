"""
Advanced Customer Management System serializers for the admin panel.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.orders.models import Order
from .customer_models import (
    CustomerSegment, CustomerSegmentMembership, CustomerLifecycleStage, CustomerLifecycleHistory,
    CustomerCommunicationHistory, CustomerSupportTicket, CustomerSupportTicketResponse,
    CustomerAnalytics, CustomerPaymentMethod, CustomerLoyaltyProgram, CustomerLoyaltyTransaction,
    CustomerRiskAssessment, CustomerGDPRCompliance, CustomerJourneyMapping,
    CustomerSatisfactionSurvey, CustomerReferralProgram, CustomerSocialMediaIntegration,
    CustomerWinBackCampaign, CustomerAccountHealthScore, CustomerPreferenceCenter,
    CustomerComplaintManagement, CustomerServiceLevelAgreement, CustomerChurnPrediction
)

User = get_user_model()


class CustomerProfileDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive customer profile serializer with all related data.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    customer_tier = serializers.CharField(read_only=True)
    
    # Related data counts
    addresses_count = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()
    support_tickets_count = serializers.SerializerMethodField()
    wishlist_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = ('total_orders', 'total_spent', 'loyalty_points', 'last_login_date', 'last_order_date')

    def get_addresses_count(self, obj):
        return obj.addresses.count()

    def get_orders_count(self, obj):
        return Order.objects.filter(customer=obj.user).count()

    def get_support_tickets_count(self, obj):
        return obj.support_tickets.count()

    def get_wishlist_items_count(self, obj):
        try:
            return obj.wishlist.items.count()
        except:
            return 0


class CustomerSegmentSerializer(serializers.ModelSerializer):
    """
    Customer segment serializer.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CustomerSegment
        fields = '__all__'
        read_only_fields = ('customer_count', 'last_calculated')


class CustomerSegmentMembershipSerializer(serializers.ModelSerializer):
    """
    Customer segment membership serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    segment_name = serializers.CharField(source='segment.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = CustomerSegmentMembership
        fields = '__all__'


class CustomerLifecycleStageSerializer(serializers.ModelSerializer):
    """
    Customer lifecycle stage serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    current_stage_display = serializers.CharField(source='get_current_stage_display', read_only=True)
    previous_stage_display = serializers.CharField(source='get_previous_stage_display', read_only=True)
    
    class Meta:
        model = CustomerLifecycleStage
        fields = '__all__'
        read_only_fields = ('days_in_current_stage', 'total_stage_changes', 'last_calculated')


class CustomerLifecycleHistorySerializer(serializers.ModelSerializer):
    """
    Customer lifecycle history serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = CustomerLifecycleHistory
        fields = '__all__'


class CustomerCommunicationHistorySerializer(serializers.ModelSerializer):
    """
    Customer communication history serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    communication_type_display = serializers.CharField(source='get_communication_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CustomerCommunicationHistory
        fields = '__all__'


class CustomerSupportTicketResponseSerializer(serializers.ModelSerializer):
    """
    Support ticket response serializer.
    """
    admin_user_name = serializers.CharField(source='admin_user.username', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = CustomerSupportTicketResponse
        fields = '__all__'


class CustomerSupportTicketSerializer(serializers.ModelSerializer):
    """
    Customer support ticket serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Related data
    responses = CustomerSupportTicketResponseSerializer(many=True, read_only=True)
    responses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerSupportTicket
        fields = '__all__'
        read_only_fields = ('ticket_number', 'first_response_at', 'resolved_at', 'closed_at', 'sla_breached')

    def get_responses_count(self, obj):
        return obj.responses.count()


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    """
    Customer analytics serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    
    class Meta:
        model = CustomerAnalytics
        fields = '__all__'
        read_only_fields = ('last_calculated',)


class CustomerPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Customer payment method serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    
    class Meta:
        model = CustomerPaymentMethod
        fields = '__all__'
        read_only_fields = ('token', 'usage_count', 'last_used', 'added_ip', 'verification_attempts')


class CustomerLoyaltyTransactionSerializer(serializers.ModelSerializer):
    """
    Customer loyalty transaction serializer.
    """
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = CustomerLoyaltyTransaction
        fields = '__all__'


class CustomerLoyaltyProgramSerializer(serializers.ModelSerializer):
    """
    Customer loyalty program serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    current_tier_display = serializers.CharField(source='get_current_tier_display', read_only=True)
    
    # Recent transactions
    recent_transactions = CustomerLoyaltyTransactionSerializer(source='transactions', many=True, read_only=True)
    
    class Meta:
        model = CustomerLoyaltyProgram
        fields = '__all__'
        read_only_fields = ('enrolled_date',)


class CustomerRiskAssessmentSerializer(serializers.ModelSerializer):
    """
    Customer risk assessment serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    overall_risk_level_display = serializers.CharField(source='get_overall_risk_level_display', read_only=True)
    fraud_risk_level_display = serializers.CharField(source='get_fraud_risk_level_display', read_only=True)
    credit_risk_level_display = serializers.CharField(source='get_credit_risk_level_display', read_only=True)
    
    class Meta:
        model = CustomerRiskAssessment
        fields = '__all__'
        read_only_fields = ('last_assessed',)


class CustomerGDPRComplianceSerializer(serializers.ModelSerializer):
    """
    Customer GDPR compliance serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    
    class Meta:
        model = CustomerGDPRCompliance
        fields = '__all__'
        read_only_fields = ('last_consent_update',)


class CustomerJourneyMappingSerializer(serializers.ModelSerializer):
    """
    Customer journey mapping serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    touchpoint_display = serializers.CharField(source='get_touchpoint_display', read_only=True)
    
    class Meta:
        model = CustomerJourneyMapping
        fields = '__all__'


class CustomerSatisfactionSurveySerializer(serializers.ModelSerializer):
    """
    Customer satisfaction survey serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    survey_type_display = serializers.CharField(source='get_survey_type_display', read_only=True)
    
    class Meta:
        model = CustomerSatisfactionSurvey
        fields = '__all__'


class CustomerReferralProgramSerializer(serializers.ModelSerializer):
    """
    Customer referral program serializer.
    """
    referrer_name = serializers.CharField(source='referrer.get_full_name', read_only=True)
    referred_customer_name = serializers.CharField(source='referred_customer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CustomerReferralProgram
        fields = '__all__'
        read_only_fields = ('referral_code',)


class AddressSerializer(serializers.ModelSerializer):
    """
    Customer address serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ('usage_count', 'last_used')


class WishlistItemSerializer(serializers.ModelSerializer):
    """
    Wishlist item serializer.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = '__all__'


class WishlistSerializer(serializers.ModelSerializer):
    """
    Customer wishlist serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    items = WishlistItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Wishlist
        fields = '__all__'


class CustomerActivitySerializer(serializers.ModelSerializer):
    """
    Customer activity serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = CustomerActivity
        fields = '__all__'


class CustomerImportSerializer(serializers.Serializer):
    """
    Serializer for customer import functionality.
    """
    file = serializers.FileField()
    format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ], default='csv')
    update_existing = serializers.BooleanField(default=False)
    send_welcome_email = serializers.BooleanField(default=False)


class CustomerExportSerializer(serializers.Serializer):
    """
    Serializer for customer export functionality.
    """
    format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('pdf', 'PDF'),
    ], default='csv')
    include_addresses = serializers.BooleanField(default=True)
    include_orders = serializers.BooleanField(default=True)
    include_analytics = serializers.BooleanField(default=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    segment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )


class CustomerMergeSerializer(serializers.Serializer):
    """
    Serializer for customer merge functionality.
    """
    primary_customer_id = serializers.IntegerField()
    secondary_customer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    merge_orders = serializers.BooleanField(default=True)
    merge_addresses = serializers.BooleanField(default=True)
    merge_loyalty_points = serializers.BooleanField(default=True)
    merge_communication_history = serializers.BooleanField(default=True)
    send_notification = serializers.BooleanField(default=True)


class CustomerSplitSerializer(serializers.Serializer):
    """
    Serializer for customer split functionality.
    """
    customer_id = serializers.IntegerField()
    new_email = serializers.EmailField()
    split_orders = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    split_addresses = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    send_notification = serializers.BooleanField(default=True)


class CustomerBulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk customer actions.
    """
    ACTION_CHOICES = [
        ('update_segment', 'Update Segment'),
        ('update_lifecycle_stage', 'Update Lifecycle Stage'),
        ('send_email', 'Send Email'),
        ('export_data', 'Export Data'),
        ('delete', 'Delete'),
        ('suspend', 'Suspend'),
        ('activate', 'Activate'),
    ]
    
    customer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    parameters = serializers.JSONField(default=dict)


class CustomerSearchSerializer(serializers.Serializer):
    """
    Serializer for advanced customer search.
    """
    query = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    account_status = serializers.CharField(required=False, allow_blank=True)
    customer_tier = serializers.CharField(required=False, allow_blank=True)
    lifecycle_stage = serializers.CharField(required=False, allow_blank=True)
    segment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    total_spent_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    total_spent_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    total_orders_min = serializers.IntegerField(required=False)
    total_orders_max = serializers.IntegerField(required=False)
    last_order_date_from = serializers.DateField(required=False)
    last_order_date_to = serializers.DateField(required=False)
    registration_date_from = serializers.DateField(required=False)
    registration_date_to = serializers.DateField(required=False)
    has_support_tickets = serializers.BooleanField(required=False)
    risk_level = serializers.CharField(required=False, allow_blank=True)
    
    # Pagination
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=25, min_value=1, max_value=100)
    
    # Sorting
    ordering = serializers.CharField(default='-created_at', required=False)


class CustomerSocialMediaIntegrationSerializer(serializers.ModelSerializer):
    """
    Customer social media integration serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = CustomerSocialMediaIntegration
        fields = '__all__'
        read_only_fields = ('last_updated',)


class CustomerWinBackCampaignSerializer(serializers.ModelSerializer):
    """
    Customer win-back campaign serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    
    class Meta:
        model = CustomerWinBackCampaign
        fields = '__all__'
        read_only_fields = ('started_at', 'completed_at')


class CustomerAccountHealthScoreSerializer(serializers.ModelSerializer):
    """
    Customer account health score serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    health_level_display = serializers.CharField(source='get_health_level_display', read_only=True)
    
    class Meta:
        model = CustomerAccountHealthScore
        fields = '__all__'
        read_only_fields = ('last_calculated',)


class CustomerPreferenceCenterSerializer(serializers.ModelSerializer):
    """
    Customer preference center serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    
    class Meta:
        model = CustomerPreferenceCenter
        fields = '__all__'
        read_only_fields = ('last_updated',)


class CustomerComplaintManagementSerializer(serializers.ModelSerializer):
    """
    Customer complaint management serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    complaint_type_display = serializers.CharField(source='get_complaint_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = CustomerComplaintManagement
        fields = '__all__'
        read_only_fields = ('complaint_number', 'received_at', 'acknowledged_at', 'resolved_at', 'closed_at')


class CustomerServiceLevelAgreementSerializer(serializers.ModelSerializer):
    """
    Customer SLA tracking serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    sla_type_display = serializers.CharField(source='get_sla_type_display', read_only=True)
    
    class Meta:
        model = CustomerServiceLevelAgreement
        fields = '__all__'


class CustomerChurnPredictionSerializer(serializers.ModelSerializer):
    """
    Customer churn prediction serializer.
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    model_used_display = serializers.CharField(source='get_model_used_display', read_only=True)
    churn_risk_level_display = serializers.CharField(source='get_churn_risk_level_display', read_only=True)
    
    class Meta:
        model = CustomerChurnPrediction
        fields = '__all__'
        read_only_fields = ('prediction_date', 'last_updated')


class CustomerAnalyticsReportSerializer(serializers.Serializer):
    """
    Serializer for customer analytics reports.
    """
    REPORT_TYPE_CHOICES = [
        ('overview', 'Customer Overview'),
        ('segmentation', 'Customer Segmentation'),
        ('lifecycle', 'Customer Lifecycle'),
        ('churn_analysis', 'Churn Analysis'),
        ('ltv_analysis', 'Lifetime Value Analysis'),
        ('satisfaction', 'Customer Satisfaction'),
        ('support_metrics', 'Support Metrics'),
    ]
    
    report_type = serializers.ChoiceField(choices=REPORT_TYPE_CHOICES)
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    segment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    include_charts = serializers.BooleanField(default=True)
    format = serializers.ChoiceField(choices=[
        ('json', 'JSON'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], default='json')