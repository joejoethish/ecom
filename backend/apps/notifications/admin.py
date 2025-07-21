from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    NotificationTemplate, NotificationPreference, Notification,
    NotificationLog, NotificationBatch, NotificationAnalytics
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'channel', 'is_active', 'created_at']
    list_filter = ['template_type', 'channel', 'is_active', 'created_at']
    search_fields = ['name', 'template_type', 'subject_template', 'body_template']
    ordering = ['template_type', 'channel']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'channel', 'is_active')
        }),
        ('Template Content', {
            'fields': ('subject_template', 'body_template', 'html_template'),
            'description': 'Use Django template syntax with variables like {{ user_name }}, {{ order_number }}, etc.'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'channel', 'is_enabled', 'updated_at']
    list_filter = ['notification_type', 'channel', 'is_enabled', 'updated_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__username', 'notification_type', 'channel']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ['action', 'details', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'subject_truncated', 'channel', 'status', 
        'priority', 'created_at', 'sent_at', 'read_at'
    ]
    list_filter = [
        'channel', 'status', 'priority', 'created_at', 'sent_at',
        ('template', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['user__username', 'user__email', 'subject', 'message']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'delivered_at', 
        'read_at', 'retry_count', 'external_id'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'template', 'channel', 'priority', 'status')
        }),
        ('Content', {
            'fields': ('subject', 'message', 'html_content')
        }),
        ('Recipient Information', {
            'fields': ('recipient_email', 'recipient_phone')
        }),
        ('Tracking Information', {
            'fields': ('sent_at', 'delivered_at', 'read_at', 'external_id')
        }),
        ('Scheduling & Expiry', {
            'fields': ('scheduled_at', 'expires_at')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [NotificationLogInline]
    
    def subject_truncated(self, obj):
        if len(obj.subject) > 50:
            return obj.subject[:50] + '...'
        return obj.subject
    subject_truncated.short_description = 'Subject'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'template')
    
    actions = ['mark_as_read', 'retry_failed', 'cancel_pending']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(status__in=['SENT', 'DELIVERED']).update(
            status='READ',
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def retry_failed(self, request, queryset):
        from .services import NotificationService
        service = NotificationService()
        
        count = 0
        for notification in queryset.filter(status='FAILED'):
            if notification.can_retry():
                service._send_notification(notification)
                count += 1
        
        self.message_user(request, f'{count} failed notifications retried.')
    retry_failed.short_description = 'Retry failed notifications'
    
    def cancel_pending(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='CANCELLED')
        self.message_user(request, f'{updated} pending notifications cancelled.')
    cancel_pending.short_description = 'Cancel pending notifications'


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template', 'status', 'total_recipients', 
        'sent_count', 'delivered_count', 'failed_count', 'created_at'
    ]
    list_filter = ['status', 'template__template_type', 'created_at']
    search_fields = ['name', 'template__name']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'sent_count', 'delivered_count', 'failed_count',
        'started_at', 'completed_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'template', 'status', 'created_by')
        }),
        ('Target Information', {
            'fields': ('total_recipients', 'target_criteria')
        }),
        ('Statistics', {
            'fields': ('sent_count', 'delivered_count', 'failed_count')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'created_by')


@admin.register(NotificationAnalytics)
class NotificationAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'template_type', 'channel', 'sent_count', 
        'delivered_count', 'read_count', 'failed_count',
        'delivery_rate', 'read_rate', 'failure_rate'
    ]
    list_filter = ['date', 'template_type', 'channel']
    ordering = ['-date', 'template_type', 'channel']
    readonly_fields = [
        'delivery_rate', 'read_rate', 'failure_rate', 
        'created_at', 'updated_at'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification_id', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['notification__id', 'notification__user__username']
    ordering = ['-timestamp']
    readonly_fields = ['notification', 'action', 'details', 'timestamp']
    
    def notification_id(self, obj):
        return str(obj.notification.id)[:8] + '...'
    notification_id.short_description = 'Notification ID'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Custom admin views for analytics dashboard
class NotificationDashboard:
    """
    Custom dashboard for notification analytics
    """
    
    @staticmethod
    def get_dashboard_stats():
        """
        Get dashboard statistics for notifications
        """
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Today's stats
        today_notifications = Notification.objects.filter(created_at__date=today)
        today_stats = {
            'total': today_notifications.count(),
            'sent': today_notifications.filter(status__in=['SENT', 'DELIVERED', 'READ']).count(),
            'failed': today_notifications.filter(status='FAILED').count(),
            'pending': today_notifications.filter(status='PENDING').count(),
        }
        
        # Weekly stats
        weekly_notifications = Notification.objects.filter(created_at__date__gte=week_ago)
        weekly_stats = {
            'total': weekly_notifications.count(),
            'sent': weekly_notifications.filter(status__in=['SENT', 'DELIVERED', 'READ']).count(),
            'failed': weekly_notifications.filter(status='FAILED').count(),
        }
        
        # Monthly stats
        monthly_notifications = Notification.objects.filter(created_at__date__gte=month_ago)
        monthly_stats = {
            'total': monthly_notifications.count(),
            'sent': monthly_notifications.filter(status__in=['SENT', 'DELIVERED', 'READ']).count(),
            'failed': monthly_notifications.filter(status='FAILED').count(),
        }
        
        # Channel breakdown
        channel_stats = Notification.objects.filter(
            created_at__date__gte=week_ago
        ).values('channel').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status__in=['SENT', 'DELIVERED', 'READ'])),
            failed=Count('id', filter=Q(status='FAILED'))
        )
        
        return {
            'today': today_stats,
            'weekly': weekly_stats,
            'monthly': monthly_stats,
            'channels': list(channel_stats),
        }