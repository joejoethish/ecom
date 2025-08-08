"""
Comprehensive Promotion and Coupon Management Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    Promotion, Coupon, PromotionUsage, PromotionAnalytics,
    PromotionApproval, PromotionAuditLog, PromotionTemplate,
    PromotionSchedule, PromotionProduct, PromotionCategory,
    PromotionType, PromotionStatus, TargetType, PromotionChannel
)


class PromotionProductSerializer(serializers.ModelSerializer):
    """Serializer for promotion products"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = PromotionProduct
        fields = ['id', 'product', 'product_name', 'product_sku', 'is_included']


class PromotionCategorySerializer(serializers.ModelSerializer):
    """Serializer for promotion categories"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = PromotionCategory
        fields = ['id', 'category', 'category_name', 'is_included']


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for coupons"""
    can_be_used = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'is_single_use', 'usage_count', 'usage_limit',
            'is_active', 'can_be_used', 'usage_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def get_can_be_used(self, obj):
        return obj.can_be_used()
    
    def get_usage_percentage(self, obj):
        if obj.usage_limit and obj.usage_limit > 0:
            return round((obj.usage_count / obj.usage_limit) * 100, 2)
        return 0


class PromotionAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for promotion analytics"""
    roi_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PromotionAnalytics
        fields = [
            'date', 'total_uses', 'unique_customers', 'total_discount_given',
            'total_revenue_generated', 'average_order_value', 'conversion_rate',
            'click_through_rate', 'channel_breakdown', 'roi_percentage'
        ]
    
    def get_roi_percentage(self, obj):
        if obj.total_discount_given > 0:
            return round(((obj.total_revenue_generated - obj.total_discount_given) / obj.total_discount_given) * 100, 2)
        return 0


class PromotionUsageSerializer(serializers.ModelSerializer):
    """Serializer for promotion usage tracking"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    savings_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PromotionUsage
        fields = [
            'id', 'customer', 'customer_name', 'customer_email', 'order',
            'order_number', 'coupon_code', 'discount_amount', 'original_amount',
            'final_amount', 'savings_percentage', 'channel', 'is_suspicious',
            'fraud_reasons', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']
    
    def get_savings_percentage(self, obj):
        if obj.original_amount > 0:
            return round((obj.discount_amount / obj.original_amount) * 100, 2)
        return 0


class PromotionApprovalSerializer(serializers.ModelSerializer):
    """Serializer for promotion approvals"""
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    
    class Meta:
        model = PromotionApproval
        fields = [
            'id', 'approver', 'approver_name', 'status', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PromotionAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for promotion audit logs"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PromotionAuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'changes', 'old_values',
            'new_values', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class PromotionScheduleSerializer(serializers.ModelSerializer):
    """Serializer for promotion schedules"""
    
    class Meta:
        model = PromotionSchedule
        fields = [
            'id', 'action', 'scheduled_time', 'is_executed', 'executed_at',
            'execution_result', 'created_at'
        ]
        read_only_fields = ['id', 'is_executed', 'executed_at', 'execution_result', 'created_at']


class PromotionTemplateSerializer(serializers.ModelSerializer):
    """Serializer for promotion templates"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = PromotionTemplate
        fields = [
            'id', 'name', 'description', 'category', 'template_data',
            'usage_count', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class PromotionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for promotion lists"""
    promotion_type_display = serializers.CharField(source='get_promotion_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_type_display = serializers.CharField(source='get_target_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    usage_percentage = serializers.SerializerMethodField()
    budget_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'promotion_type', 'promotion_type_display', 'status',
            'status_display', 'target_type', 'target_type_display', 'discount_value',
            'start_date', 'end_date', 'usage_count', 'usage_limit_total',
            'budget_spent', 'budget_limit', 'conversion_rate', 'roi',
            'priority', 'is_active', 'days_remaining', 'usage_percentage',
            'budget_percentage', 'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_usage_percentage(self, obj):
        if obj.usage_limit_total and obj.usage_limit_total > 0:
            return round((obj.usage_count / obj.usage_limit_total) * 100, 2)
        return 0
    
    def get_budget_percentage(self, obj):
        if obj.budget_limit and obj.budget_limit > 0:
            return round((obj.budget_spent / obj.budget_limit) * 100, 2)
        return 0


class PromotionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for promotion CRUD operations"""
    promotion_type_display = serializers.CharField(source='get_promotion_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_type_display = serializers.CharField(source='get_target_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    # Related data
    promotion_products = PromotionProductSerializer(many=True, read_only=True)
    promotion_categories = PromotionCategorySerializer(many=True, read_only=True)
    coupons = CouponSerializer(many=True, read_only=True)
    schedules = PromotionScheduleSerializer(many=True, read_only=True)
    
    # Computed fields
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    usage_percentage = serializers.SerializerMethodField()
    budget_percentage = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'internal_notes', 'promotion_type',
            'promotion_type_display', 'status', 'status_display', 'discount_value',
            'max_discount_amount', 'buy_quantity', 'get_quantity', 'get_discount_percentage',
            'start_date', 'end_date', 'timezone', 'usage_limit_total',
            'usage_limit_per_customer', 'usage_count', 'minimum_order_amount',
            'minimum_quantity', 'target_type', 'target_type_display',
            'target_customer_segments', 'target_customer_ids', 'allowed_channels',
            'can_stack_with_other_promotions', 'stackable_promotion_types',
            'excluded_promotion_ids', 'priority', 'is_ab_test', 'ab_test_group',
            'ab_test_traffic_percentage', 'requires_approval', 'approved_by',
            'approved_by_name', 'approved_at', 'budget_limit', 'budget_spent',
            'conversion_rate', 'roi', 'fraud_score', 'is_flagged_for_review',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'promotion_products', 'promotion_categories', 'coupons', 'schedules',
            'is_active', 'days_remaining', 'usage_percentage', 'budget_percentage',
            'performance_metrics'
        ]
        read_only_fields = [
            'id', 'usage_count', 'budget_spent', 'conversion_rate', 'roi',
            'fraud_score', 'approved_at', 'created_at', 'updated_at'
        ]
    
    def get_usage_percentage(self, obj):
        if obj.usage_limit_total and obj.usage_limit_total > 0:
            return round((obj.usage_count / obj.usage_limit_total) * 100, 2)
        return 0
    
    def get_budget_percentage(self, obj):
        if obj.budget_limit and obj.budget_limit > 0:
            return round((obj.budget_spent / obj.budget_limit) * 100, 2)
        return 0
    
    def get_performance_metrics(self, obj):
        """Get aggregated performance metrics"""
        from django.db.models import Sum, Avg, Count
        
        analytics = obj.analytics.aggregate(
            total_uses=Sum('total_uses'),
            total_customers=Sum('unique_customers'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated'),
            avg_conversion_rate=Avg('conversion_rate'),
            avg_ctr=Avg('click_through_rate')
        )
        
        return {
            'total_uses': analytics['total_uses'] or 0,
            'total_customers': analytics['total_customers'] or 0,
            'total_discount_given': float(analytics['total_discount'] or 0),
            'total_revenue_generated': float(analytics['total_revenue'] or 0),
            'average_conversion_rate': float(analytics['avg_conversion_rate'] or 0),
            'average_click_through_rate': float(analytics['avg_ctr'] or 0),
        }
    
    def validate(self, data):
        """Validate promotion data"""
        errors = {}
        
        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                errors['end_date'] = "End date must be after start date"
        
        # Validate discount value based on type
        promotion_type = data.get('promotion_type')
        discount_value = data.get('discount_value')
        
        if promotion_type == PromotionType.PERCENTAGE and discount_value:
            if discount_value > 100:
                errors['discount_value'] = "Percentage discount cannot exceed 100%"
        
        # Validate BOGO configuration
        if promotion_type == PromotionType.BOGO:
            if not data.get('buy_quantity') or data['buy_quantity'] < 1:
                errors['buy_quantity'] = "Buy quantity must be at least 1 for BOGO promotions"
            if not data.get('get_quantity') or data['get_quantity'] < 1:
                errors['get_quantity'] = "Get quantity must be at least 1 for BOGO promotions"
        
        # Validate budget
        if data.get('budget_limit') and data.get('budget_limit') <= 0:
            errors['budget_limit'] = "Budget limit must be greater than 0"
        
        # Validate usage limits
        if data.get('usage_limit_total') and data.get('usage_limit_total') <= 0:
            errors['usage_limit_total'] = "Usage limit must be greater than 0"
        
        if data.get('usage_limit_per_customer') and data.get('usage_limit_per_customer') <= 0:
            errors['usage_limit_per_customer'] = "Usage limit per customer must be greater than 0"
        
        # Validate A/B test configuration
        if data.get('is_ab_test'):
            if not data.get('ab_test_group'):
                errors['ab_test_group'] = "A/B test group is required for A/B test promotions"
            
            traffic_percentage = data.get('ab_test_traffic_percentage')
            if traffic_percentage and (traffic_percentage <= 0 or traffic_percentage > 100):
                errors['ab_test_traffic_percentage'] = "Traffic percentage must be between 0 and 100"
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data


class PromotionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating promotions"""
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of product IDs to include in promotion"
    )
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of category IDs to include in promotion"
    )
    excluded_product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of product IDs to exclude from promotion"
    )
    excluded_category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of category IDs to exclude from promotion"
    )
    coupon_codes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        help_text="List of coupon codes to create for this promotion"
    )
    
    class Meta:
        model = Promotion
        fields = [
            'name', 'description', 'internal_notes', 'promotion_type', 'discount_value',
            'max_discount_amount', 'buy_quantity', 'get_quantity', 'get_discount_percentage',
            'start_date', 'end_date', 'timezone', 'usage_limit_total',
            'usage_limit_per_customer', 'minimum_order_amount', 'minimum_quantity',
            'target_type', 'target_customer_segments', 'target_customer_ids',
            'allowed_channels', 'can_stack_with_other_promotions',
            'stackable_promotion_types', 'excluded_promotion_ids', 'priority',
            'is_ab_test', 'ab_test_group', 'ab_test_traffic_percentage',
            'requires_approval', 'budget_limit', 'product_ids', 'category_ids',
            'excluded_product_ids', 'excluded_category_ids', 'coupon_codes'
        ]
    
    def validate(self, data):
        """Validate promotion creation data"""
        # Use the same validation as PromotionDetailSerializer
        return PromotionDetailSerializer().validate(data)
    
    def create(self, validated_data):
        """Create promotion with related objects"""
        # Extract related data
        product_ids = validated_data.pop('product_ids', [])
        category_ids = validated_data.pop('category_ids', [])
        excluded_product_ids = validated_data.pop('excluded_product_ids', [])
        excluded_category_ids = validated_data.pop('excluded_category_ids', [])
        coupon_codes = validated_data.pop('coupon_codes', [])
        
        # Set created_by from request user
        validated_data['created_by'] = self.context['request'].user
        
        # Create promotion
        promotion = Promotion.objects.create(**validated_data)
        
        # Create promotion products
        for product_id in product_ids:
            PromotionProduct.objects.create(
                promotion=promotion,
                product_id=product_id,
                is_included=True
            )
        
        for product_id in excluded_product_ids:
            PromotionProduct.objects.create(
                promotion=promotion,
                product_id=product_id,
                is_included=False
            )
        
        # Create promotion categories
        for category_id in category_ids:
            PromotionCategory.objects.create(
                promotion=promotion,
                category_id=category_id,
                is_included=True
            )
        
        for category_id in excluded_category_ids:
            PromotionCategory.objects.create(
                promotion=promotion,
                category_id=category_id,
                is_included=False
            )
        
        # Create coupons
        for code in coupon_codes:
            Coupon.objects.create(
                promotion=promotion,
                code=code.upper()
            )
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=self.context['request'].user,
            action='created',
            changes={'promotion_created': True},
            ip_address=self.context['request'].META.get('REMOTE_ADDR'),
            user_agent=self.context['request'].META.get('HTTP_USER_AGENT', '')
        )
        
        return promotion


class PromotionBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk promotion actions"""
    promotion_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of promotion IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=[
            ('activate', 'Activate'),
            ('deactivate', 'Deactivate'),
            ('pause', 'Pause'),
            ('delete', 'Delete'),
            ('duplicate', 'Duplicate'),
        ],
        help_text="Action to perform on selected promotions"
    )
    
    def validate_promotion_ids(self, value):
        """Validate that all promotion IDs exist"""
        existing_ids = set(
            Promotion.objects.filter(id__in=value).values_list('id', flat=True)
        )
        provided_ids = set(value)
        
        if existing_ids != provided_ids:
            missing_ids = provided_ids - existing_ids
            raise serializers.ValidationError(
                f"The following promotion IDs do not exist: {list(missing_ids)}"
            )
        
        return value


class PromotionReportSerializer(serializers.Serializer):
    """Serializer for promotion reports"""
    date_from = serializers.DateField(required=True)
    date_to = serializers.DateField(required=True)
    promotion_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Specific promotion IDs to include in report"
    )
    promotion_types = serializers.ListField(
        child=serializers.ChoiceField(choices=PromotionType.choices),
        required=False,
        help_text="Promotion types to include in report"
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=PromotionChannel.choices),
        required=False,
        help_text="Channels to include in report"
    )
    include_analytics = serializers.BooleanField(default=True)
    include_usage_details = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """Validate report parameters"""
        if data['date_from'] > data['date_to']:
            raise serializers.ValidationError("date_from must be before date_to")
        
        # Limit report range to prevent performance issues
        date_range = (data['date_to'] - data['date_from']).days
        if date_range > 365:
            raise serializers.ValidationError("Report range cannot exceed 365 days")
        
        return data