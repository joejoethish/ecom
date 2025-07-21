"""
Admin configuration for reviews app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Review, ReviewHelpfulness, ReviewImage, ReviewReport


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    """
    list_display = [
        'id', 'product_name', 'user_email', 'rating', 'status', 
        'is_verified_purchase', 'helpful_score', 'created_at'
    ]
    list_filter = [
        'status', 'rating', 'is_verified_purchase', 'created_at'
    ]
    search_fields = [
        'product__name', 'user__email', 'title', 'comment'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'helpful_count', 'not_helpful_count',
        'helpfulness_score', 'moderated_at'
    ]
    fieldsets = (
        ('Review Information', {
            'fields': (
                'product', 'user', 'order_item', 'rating', 'title', 'comment'
            )
        }),
        ('Additional Details', {
            'fields': ('pros', 'cons', 'is_verified_purchase'),
            'classes': ('collapse',)
        }),
        ('Moderation', {
            'fields': (
                'status', 'moderated_by', 'moderated_at', 'moderation_notes'
            )
        }),
        ('Helpfulness', {
            'fields': (
                'helpful_count', 'not_helpful_count', 'helpfulness_score'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def product_name(self, obj):
        """Display product name with link."""
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_name.short_description = 'Product'
    
    def user_email(self, obj):
        """Display user email with link."""
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
    
    def helpful_score(self, obj):
        """Display helpfulness score."""
        return f"{obj.helpfulness_score}%"
    helpful_score.short_description = 'Helpful Score'
    
    actions = ['approve_reviews', 'reject_reviews', 'flag_reviews']
    
    def approve_reviews(self, request, queryset):
        """Bulk approve reviews."""
        count = 0
        for review in queryset:
            if review.status != 'approved':
                review.approve(request.user)
                count += 1
        self.message_user(request, f'{count} reviews approved.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def reject_reviews(self, request, queryset):
        """Bulk reject reviews."""
        count = 0
        for review in queryset:
            if review.status != 'rejected':
                review.reject(request.user, "Bulk rejection")
                count += 1
        self.message_user(request, f'{count} reviews rejected.')
    reject_reviews.short_description = 'Reject selected reviews'
    
    def flag_reviews(self, request, queryset):
        """Bulk flag reviews."""
        count = 0
        for review in queryset:
            if review.status != 'flagged':
                review.flag(request.user, "Bulk flagging")
                count += 1
        self.message_user(request, f'{count} reviews flagged.')
    flag_reviews.short_description = 'Flag selected reviews'


class ReviewImageInline(admin.TabularInline):
    """
    Inline admin for review images.
    """
    model = ReviewImage
    extra = 0
    fields = ['image', 'caption', 'sort_order']
    readonly_fields = ['created_at']


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewHelpfulness model.
    """
    list_display = ['id', 'review_id', 'user_email', 'vote', 'created_at']
    list_filter = ['vote', 'created_at']
    search_fields = ['review__product__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def review_id(self, obj):
        """Display review ID with link."""
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">{}</a>', url, obj.review.id)
    review_id.short_description = 'Review'
    
    def user_email(self, obj):
        """Display user email with link."""
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewImage model.
    """
    list_display = ['id', 'review_id', 'image_preview', 'caption', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__product__name', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def review_id(self, obj):
        """Display review ID with link."""
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">{}</a>', url, obj.review.id)
    review_id.short_description = 'Review'
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewReport model.
    """
    list_display = [
        'id', 'review_id', 'reporter_email', 'reason', 'status', 
        'reviewed_by_email', 'created_at'
    ]
    list_filter = ['reason', 'status', 'created_at']
    search_fields = [
        'review__product__name', 'reporter__email', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
    fieldsets = (
        ('Report Information', {
            'fields': ('review', 'reporter', 'reason', 'description')
        }),
        ('Resolution', {
            'fields': (
                'status', 'reviewed_by', 'reviewed_at', 'resolution_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def review_id(self, obj):
        """Display review ID with link."""
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">{}</a>', url, obj.review.id)
    review_id.short_description = 'Review'
    
    def reporter_email(self, obj):
        """Display reporter email with link."""
        url = reverse('admin:authentication_user_change', args=[obj.reporter.id])
        return format_html('<a href="{}">{}</a>', url, obj.reporter.email)
    reporter_email.short_description = 'Reporter'
    
    def reviewed_by_email(self, obj):
        """Display reviewer email with link."""
        if obj.reviewed_by:
            url = reverse('admin:authentication_user_change', args=[obj.reviewed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.email)
        return "Not reviewed"
    reviewed_by_email.short_description = 'Reviewed By'
    
    actions = ['resolve_reports', 'dismiss_reports']
    
    def resolve_reports(self, request, queryset):
        """Bulk resolve reports."""
        count = 0
        for report in queryset:
            if report.status == 'pending':
                report.resolve(request.user, "Bulk resolution")
                count += 1
        self.message_user(request, f'{count} reports resolved.')
    resolve_reports.short_description = 'Resolve selected reports'
    
    def dismiss_reports(self, request, queryset):
        """Bulk dismiss reports."""
        count = 0
        for report in queryset:
            if report.status == 'pending':
                report.dismiss(request.user, "Bulk dismissal")
                count += 1
        self.message_user(request, f'{count} reports dismissed.')
    dismiss_reports.short_description = 'Dismiss selected reports'