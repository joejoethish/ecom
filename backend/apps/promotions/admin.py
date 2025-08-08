"""
Comprehensive Promotion and Coupon Management Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count
from .models import (
    Promotion, Coupon, PromotionUsage, PromotionAnalytics,
    PromotionApproval, PromotionAuditLog, PromotionTemplate,
    PromotionSchedule, PromotionProduct, PromotionCategory
)


class PromotionProductInline(admin.TabularInline):
    """Inline for promotion products"""
    model = PromotionProduct
    extra = 0
    # autocomplete_fields = ['product']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


class PromotionCategoryInline(admin.TabularInline):
    """Inline for promotion categories"""
    model = PromotionCategory
    extra = 0
    # autocomplete_fields = ['category']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


class CouponInline(admin.TabularInline):
    """Inline for coupons"""
    model = Coupon
    extra = 0
    readonly_fields = ['usage_count', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion')


class PromotionScheduleInline(admin.TabularInline):
    """Inline for promotion schedules"""
    model = PromotionSchedule
    extra = 0
    readonly_fields = ['is_executed', 'executed_at', 'execution_result']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Comprehensive promotion admin interface"""
    list_display = [
        'name', 'promotion_type', 'status_badge', 'discount_value',
        'active_status', 'usage_progress', 'budget_progress',
        'conversion_rate', 'roi', 'priority', 'created_by', 'created_at'
    ]
    list_filter = [
        'promotion_type', 'status', 'target_type', 'is_ab_test',
        'requires_approval', 'is_flagged_for_review', 'created_at'
    ]
    search_fields = ['name', 'description', 'internal_notes']
    readonly_fields = [
        'id', 'usage_count', 'budget_spent', 'conversion_rate', 'roi',
        'fraud_score', 'approved_at', 'created_at', 'updated_at',
        'performance_summary', 'usage_analytics'
    ]
    # autocomplete_fields = ['created_by', 'approved_by']  # Disabled due to model reference issues
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'internal_notes', 'status')
        }),
        ('Promotion Configuration', {
            'fields': (
                'promotion_type', 'discount_value', 'max_discount_amount',
                'buy_quantity', 'get_quantity', 'get_discount_percentage'
            )
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date', 'timezone')
        }),
        ('Usage Limits', {
            'fields': (
                'usage_limit_total', 'usage_limit_per_customer', 'usage_count',
                'minimum_order_amount', 'minimum_quantity'
            )
        }),
        ('Targeting', {
            'fields': (
                'target_type', 'target_customer_segments', 'target_customer_ids',
                'allowed_channels'
            )
        }),
        ('Stacking Rules', {
            'fields': (
                'can_stack_with_other_promotions', 'stackable_promotion_types',
                'excluded_promotion_ids'
            )
        }),
        ('A/B Testing', {
            'fields': ('is_ab_test', 'ab_test_group', 'ab_test_traffic_percentage'),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': ('requires_approval', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Budget Management', {
            'fields': ('budget_limit', 'budget_spent', 'priority')
        }),
        ('Performance Metrics', {
            'fields': ('conversion_rate', 'roi', 'performance_summary'),
            'classes': ('collapse',)
        }),
        ('Fraud Detection', {
            'fields': ('fraud_score', 'is_flagged_for_review'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('usage_analytics',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [
        PromotionProductInline,
        PromotionCategoryInline,
        CouponInline,
        PromotionScheduleInline
    ]
    
    actions = ['activate_promotions', 'deactivate_promotions', 'duplicate_promotions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'created_by', 'approved_by'
        ).prefetch_related('analytics')
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'draft': 'gray',
            'pending_approval': 'orange',
            'approved': 'blue',
            'active': 'green',
            'paused': 'yellow',
            'expired': 'red',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def active_status(self, obj):
        """Display if promotion is currently active"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    active_status.short_description = 'Active'
    active_status.boolean = True
    
    def usage_progress(self, obj):
        """Display usage progress bar"""
        if obj.usage_limit_total:
            percentage = (obj.usage_count / obj.usage_limit_total) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
                '{}%</div></div>',
                min(percentage, 100), color, int(percentage)
            )
        return format_html('<span style="color: gray;">No limit</span>')
    usage_progress.short_description = 'Usage'
    
    def budget_progress(self, obj):
        """Display budget progress bar"""
        if obj.budget_limit:
            percentage = (obj.budget_spent / obj.budget_limit) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
                '{}%</div></div>',
                min(percentage, 100), color, int(percentage)
            )
        return format_html('<span style="color: gray;">No limit</span>')
    budget_progress.short_description = 'Budget'
    
    def performance_summary(self, obj):
        """Display performance summary"""
        analytics = obj.analytics.aggregate(
            total_uses=Sum('total_uses'),
            total_customers=Sum('unique_customers'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated')
        )
        
        return format_html(
            '<div style="font-size: 12px;">'
            '<strong>Total Uses:</strong> {}<br>'
            '<strong>Unique Customers:</strong> {}<br>'
            '<strong>Total Discount:</strong> ${:,.2f}<br>'
            '<strong>Total Revenue:</strong> ${:,.2f}<br>'
            '</div>',
            analytics['total_uses'] or 0,
            analytics['total_customers'] or 0,
            float(analytics['total_discount'] or 0),
            float(analytics['total_revenue'] or 0)
        )
    performance_summary.short_description = 'Performance Summary'
    
    def usage_analytics(self, obj):
        """Display usage analytics chart link"""
        if obj.pk:
            url = reverse('admin:promotions_promotionanalytics_changelist')
            return format_html(
                '<a href="{}?promotion__id__exact={}" target="_blank">View Analytics</a>',
                url, obj.pk
            )
        return '-'
    usage_analytics.short_description = 'Analytics'
    
    def activate_promotions(self, request, queryset):
        """Bulk activate promotions"""
        updated = 0
        for promotion in queryset:
            if promotion.status != 'active' and promotion.is_active:
                promotion.status = 'active'
                promotion.save()
                updated += 1
        
        self.message_user(request, f'{updated} promotions were activated.')
    activate_promotions.short_description = 'Activate selected promotions'
    
    def deactivate_promotions(self, request, queryset):
        """Bulk deactivate promotions"""
        updated = queryset.filter(status='active').update(status='paused')
        self.message_user(request, f'{updated} promotions were deactivated.')
    deactivate_promotions.short_description = 'Deactivate selected promotions'
    
    def duplicate_promotions(self, request, queryset):
        """Bulk duplicate promotions"""
        duplicated = 0
        for promotion in queryset:
            # Create duplicate
            duplicate_data = {}
            for field in promotion._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at', 'usage_count', 'budget_spent']:
                    duplicate_data[field.name] = getattr(promotion, field.name)
            
            duplicate_data['name'] = f"{promotion.name} (Copy)"
            duplicate_data['status'] = 'draft'
            duplicate_data['created_by'] = request.user
            duplicate_data['approved_by'] = None
            duplicate_data['approved_at'] = None
            
            Promotion.objects.create(**duplicate_data)
            duplicated += 1
        
        self.message_user(request, f'{duplicated} promotions were duplicated.')
    duplicate_promotions.short_description = 'Duplicate selected promotions'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Coupon admin interface"""
    list_display = [
        'code', 'promotion_link', 'is_active', 'usage_progress',
        'can_be_used_status', 'created_at'
    ]
    list_filter = ['is_active', 'is_single_use', 'created_at']
    search_fields = ['code', 'promotion__name']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    # autocomplete_fields = ['promotion']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion')
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def usage_progress(self, obj):
        """Display usage progress"""
        if obj.usage_limit:
            percentage = (obj.usage_count / obj.usage_limit) * 100
            return format_html('{}% ({}/{})', int(percentage), obj.usage_count, obj.usage_limit)
        return f'{obj.usage_count} (no limit)'
    usage_progress.short_description = 'Usage'
    
    def can_be_used_status(self, obj):
        """Display if coupon can be used"""
        if obj.can_be_used():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')
    can_be_used_status.short_description = 'Status'
    can_be_used_status.boolean = True


@admin.register(PromotionUsage)
class PromotionUsageAdmin(admin.ModelAdmin):
    """Promotion usage admin interface"""
    list_display = [
        'promotion_link', 'customer_link', 'order_link', 'coupon_code',
        'discount_amount', 'savings_percentage', 'channel', 'suspicious_flag', 'used_at'
    ]
    list_filter = [
        'channel', 'is_suspicious', 'used_at',
        'promotion__promotion_type', 'promotion__status'
    ]
    search_fields = [
        'promotion__name', 'customer__email', 'customer__first_name',
        'customer__last_name', 'order__order_number', 'coupon__code'
    ]
    readonly_fields = [
        'discount_amount', 'original_amount', 'final_amount',
        'ip_address', 'user_agent', 'used_at'
    ]
    # autocomplete_fields = ['promotion', 'customer', 'order', 'coupon']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'promotion', 'customer', 'order', 'coupon'
        )
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def customer_link(self, obj):
        """Link to customer"""
        if obj.customer:
            url = reverse('admin:customers_customer_change', args=[obj.customer.pk])
            return format_html('<a href="{}">{}</a>', url, obj.customer.get_full_name())
        return '-'
    customer_link.short_description = 'Customer'
    
    def order_link(self, obj):
        """Link to order"""
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.pk])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Order'
    
    def coupon_code(self, obj):
        """Display coupon code"""
        return obj.coupon.code if obj.coupon else '-'
    coupon_code.short_description = 'Coupon'
    
    def savings_percentage(self, obj):
        """Calculate savings percentage"""
        if obj.original_amount > 0:
            percentage = (obj.discount_amount / obj.original_amount) * 100
            return f'{percentage:.1f}%'
        return '0%'
    savings_percentage.short_description = 'Savings %'
    
    def suspicious_flag(self, obj):
        """Display suspicious flag"""
        if obj.is_suspicious:
            return format_html('<span style="color: red;">⚠ Suspicious</span>')
        return format_html('<span style="color: green;">✓ Normal</span>')
    suspicious_flag.short_description = 'Fraud Check'
    suspicious_flag.boolean = True


@admin.register(PromotionAnalytics)
class PromotionAnalyticsAdmin(admin.ModelAdmin):
    """Promotion analytics admin interface"""
    list_display = [
        'promotion_link', 'date', 'total_uses', 'unique_customers',
        'total_discount_given', 'total_revenue_generated', 'conversion_rate',
        'roi_percentage'
    ]
    list_filter = ['date', 'promotion__promotion_type']
    search_fields = ['promotion__name']
    readonly_fields = ['date']
    # autocomplete_fields = ['promotion']  # Disabled due to model reference issues
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion')
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def roi_percentage(self, obj):
        """Calculate ROI percentage"""
        if obj.total_discount_given > 0:
            roi = ((obj.total_revenue_generated - obj.total_discount_given) / obj.total_discount_given) * 100
            color = 'green' if roi > 0 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, roi)
        return '0%'
    roi_percentage.short_description = 'ROI %'


@admin.register(PromotionApproval)
class PromotionApprovalAdmin(admin.ModelAdmin):
    """Promotion approval admin interface"""
    list_display = [
        'promotion_link', 'approver', 'status_badge', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['promotion__name', 'approver__username', 'comments']
    readonly_fields = ['created_at', 'updated_at']
    # autocomplete_fields = ['promotion', 'approver']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion', 'approver')
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'changes_requested': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(PromotionAuditLog)
class PromotionAuditLogAdmin(admin.ModelAdmin):
    """Promotion audit log admin interface"""
    list_display = [
        'promotion_link', 'user', 'action_badge', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = ['promotion__name', 'user__username']
    readonly_fields = [
        'promotion', 'user', 'action', 'changes', 'old_values',
        'new_values', 'ip_address', 'user_agent', 'timestamp'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion', 'user')
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def action_badge(self, obj):
        """Display action with color coding"""
        colors = {
            'created': 'green',
            'updated': 'blue',
            'activated': 'green',
            'deactivated': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'deleted': 'red'
        }
        color = colors.get(obj.action, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'


@admin.register(PromotionTemplate)
class PromotionTemplateAdmin(admin.ModelAdmin):
    """Promotion template admin interface"""
    list_display = [
        'name', 'category', 'usage_count', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    # autocomplete_fields = ['created_by']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(PromotionSchedule)
class PromotionScheduleAdmin(admin.ModelAdmin):
    """Promotion schedule admin interface"""
    list_display = [
        'promotion_link', 'action_badge', 'scheduled_time', 'execution_status', 'created_at'
    ]
    list_filter = ['action', 'is_executed', 'scheduled_time']
    search_fields = ['promotion__name']
    readonly_fields = ['is_executed', 'executed_at', 'execution_result', 'created_at']
    # autocomplete_fields = ['promotion']  # Disabled due to model reference issues
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion')
    
    def promotion_link(self, obj):
        """Link to promotion"""
        url = reverse('admin:promotions_promotion_change', args=[obj.promotion.pk])
        return format_html('<a href="{}">{}</a>', url, obj.promotion.name)
    promotion_link.short_description = 'Promotion'
    
    def action_badge(self, obj):
        """Display action with color coding"""
        colors = {
            'activate': 'green',
            'deactivate': 'orange',
            'pause': 'yellow',
            'resume': 'blue'
        }
        color = colors.get(obj.action, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    
    def execution_status(self, obj):
        """Display execution status"""
        if obj.is_executed:
            return format_html('<span style="color: green;">✓ Executed</span>')
        elif obj.scheduled_time < timezone.now():
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        else:
            return format_html('<span style="color: blue;">⏳ Pending</span>')
    execution_status.short_description = 'Status'
    execution_status.boolean = True