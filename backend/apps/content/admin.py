"""
Content management admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Banner, Carousel, CarouselItem, ContentPage, Announcement

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """
    Admin interface for banner management.
    """
    list_display = [
        'title', 'banner_type', 'position', 'is_active',
        'is_currently_active', 'view_count', 'click_count',
        'click_through_rate', 'sort_order'
    ]
    list_filter = [
        'banner_type', 'position', 'is_active', 'start_date',
        'end_date', 'created_at', 'is_deleted'
    ]
    search_fields = ['title', 'subtitle', 'description']
    readonly_fields = [
        'view_count', 'click_count', 'click_through_rate',
        'is_currently_active', 'created_at', 'updated_at'
    ]
    ordering = ['sort_order', '-created_at']
    filter_horizontal = ['target_categories']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return Banner.objects.all()
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image Preview'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'description')
        }),
        ('Images', {
            'fields': ('image', 'mobile_image')
        }),
        ('Banner Configuration', {
            'fields': ('banner_type', 'position', 'sort_order')
        }),
        ('Link Configuration', {
            'fields': ('link_url', 'link_text', 'opens_in_new_tab')
        }),
        ('Targeting', {
            'fields': ('target_categories', 'target_pages')
        }),
        ('Scheduling', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color', 'custom_css'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': (
                'view_count', 'click_count', 'click_through_rate',
                'is_currently_active'
            ),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_banners', 'deactivate_banners', 'soft_delete_banners']
    
    def activate_banners(self, request, queryset):
        """Activate selected banners."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} banners activated.')
    activate_banners.short_description = 'Activate selected banners'
    
    def deactivate_banners(self, request, queryset):
        """Deactivate selected banners."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} banners deactivated.')
    deactivate_banners.short_description = 'Deactivate selected banners'
    
    def soft_delete_banners(self, request, queryset):
        """Soft delete selected banners."""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} banners deleted.')
    soft_delete_banners.short_description = 'Delete selected banners'

class CarouselItemInline(admin.TabularInline):
    """
    Inline admin for carousel items.
    """
    model = CarouselItem
    extra = 0
    fields = [
        'title', 'image', 'link_url', 'is_active',
        'sort_order', 'view_count', 'click_count'
    ]
    readonly_fields = ['view_count', 'click_count']
    ordering = ['sort_order']

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    """
    Admin interface for carousel management.
    """
    list_display = [
        'name', 'carousel_type', 'is_active', 'active_items_count',
        'auto_play', 'auto_play_speed', 'created_at'
    ]
    list_filter = ['carousel_type', 'is_active', 'auto_play', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['active_items_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [CarouselItemInline]
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return Carousel.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'carousel_type')
        }),
        ('Display Settings', {
            'fields': (
                'is_active', 'items_per_view', 'items_per_view_mobile',
                'show_indicators', 'show_navigation', 'infinite_loop'
            )
        }),
        ('Auto-play Settings', {
            'fields': ('auto_play', 'auto_play_speed')
        }),
        ('Targeting', {
            'fields': ('target_pages',)
        }),
        ('Analytics', {
            'fields': ('active_items_count',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_carousels', 'deactivate_carousels', 'soft_delete_carousels']
    
    def activate_carousels(self, request, queryset):
        """Activate selected carousels."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} carousels activated.')
    activate_carousels.short_description = 'Activate selected carousels'
    
    def deactivate_carousels(self, request, queryset):
        """Deactivate selected carousels."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} carousels deactivated.')
    deactivate_carousels.short_description = 'Deactivate selected carousels'
    
    def soft_delete_carousels(self, request, queryset):
        """Soft delete selected carousels."""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} carousels deleted.')
    soft_delete_carousels.short_description = 'Delete selected carousels'

@admin.register(CarouselItem)
class CarouselItemAdmin(admin.ModelAdmin):
    """
    Admin interface for carousel items.
    """
    list_display = [
        'title', 'carousel', 'is_active', 'sort_order',
        'view_count', 'click_count', 'click_through_rate'
    ]
    list_filter = ['carousel', 'is_active', 'created_at', 'is_deleted']
    search_fields = ['title', 'subtitle', 'description', 'carousel__name']
    readonly_fields = [
        'view_count', 'click_count', 'click_through_rate',
        'created_at', 'updated_at'
    ]
    ordering = ['carousel', 'sort_order']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return CarouselItem.objects.all()
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image Preview'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('carousel', 'title', 'subtitle', 'description')
        }),
        ('Images', {
            'fields': ('image', 'mobile_image')
        }),
        ('Link Configuration', {
            'fields': ('link_url', 'link_text', 'opens_in_new_tab')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color', 'overlay_opacity'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'click_count', 'click_through_rate'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    """
    Admin interface for content pages.
    """
    list_display = [
        'title', 'slug', 'page_type', 'is_active',
        'show_in_footer', 'show_in_header', 'sort_order'
    ]
    list_filter = [
        'page_type', 'is_active', 'show_in_footer',
        'show_in_header', 'created_at', 'is_deleted'
    ]
    search_fields = ['title', 'slug', 'content', 'meta_title', 'meta_description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['sort_order', 'title']
    prepopulated_fields = {'slug': ('title',)}
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentPage.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': (
                'is_active', 'show_in_footer', 'show_in_header', 'sort_order'
            )
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_pages', 'deactivate_pages', 'soft_delete_pages']
    
    def activate_pages(self, request, queryset):
        """Activate selected pages."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} pages activated.')
    activate_pages.short_description = 'Activate selected pages'
    
    def deactivate_pages(self, request, queryset):
        """Deactivate selected pages."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} pages deactivated.')
    deactivate_pages.short_description = 'Deactivate selected pages'
    
    def soft_delete_pages(self, request, queryset):
        """Soft delete selected pages."""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} pages deleted.')
    soft_delete_pages.short_description = 'Delete selected pages'

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Admin interface for announcements.
    """
    list_display = [
        'title', 'announcement_type', 'is_active', 'is_currently_active',
        'is_dismissible', 'start_date', 'end_date'
    ]
    list_filter = [
        'announcement_type', 'is_active', 'is_dismissible',
        'start_date', 'end_date', 'created_at', 'is_deleted'
    ]
    search_fields = ['title', 'message']
    readonly_fields = ['is_currently_active', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return Announcement.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'announcement_type')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_dismissible')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date')
        }),
        ('Targeting', {
            'fields': ('target_user_types', 'target_pages')
        }),
        ('Status', {
            'fields': ('is_currently_active',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_announcements', 'deactivate_announcements', 'soft_delete_announcements']
    
    def activate_announcements(self, request, queryset):
        """Activate selected announcements."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} announcements activated.')
    activate_announcements.short_description = 'Activate selected announcements'
    
    def deactivate_announcements(self, request, queryset):
        """Deactivate selected announcements."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} announcements deactivated.')
    deactivate_announcements.short_description = 'Deactivate selected announcements'
    
    def soft_delete_announcements(self, request, queryset):
        """Soft delete selected announcements."""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} announcements deleted.')
    soft_delete_announcements.short_description = 'Delete selected announcements'

# Advanced Content Management Admin

from .models import (
    ContentTemplate, AdvancedContentPage, ContentVersion, ContentWorkflow,
    ContentWorkflowInstance, ContentAsset, ContentCategory, ContentTag,
    ContentAnalytics, ContentSchedule, ContentSyndication
)


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for content categories.
    """
    list_display = ['name', 'parent', 'sort_order', 'is_active', 'created_at']
    list_filter = ['parent', 'is_active', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['full_path', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentCategory.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'sort_order', 'is_active')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('full_path', 'is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentTag)
class ContentTagAdmin(admin.ModelAdmin):
    """
    Admin interface for content tags.
    """
    list_display = ['name', 'usage_count', 'is_featured', 'created_at']
    list_filter = ['is_featured', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-usage_count', 'name']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentTag.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('color', 'is_featured')
        }),
        ('Analytics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentTemplate)
class ContentTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for content templates.
    """
    list_display = ['name', 'template_type', 'is_active', 'is_system_template', 'usage_count', 'created_by', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_system_template', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-usage_count', 'name']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentTemplate.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type')
        }),
        ('Template Configuration', {
            'fields': ('structure', 'default_styles', 'required_fields', 'optional_fields')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_system_template', 'preview_image')
        }),
        ('Analytics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_by', 'is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class ContentVersionInline(admin.TabularInline):
    """
    Inline admin for content versions.
    """
    model = ContentVersion
    extra = 0
    readonly_fields = ['version_number', 'created_by', 'is_current', 'created_at']
    fields = ['version_number', 'title', 'change_summary', 'created_by', 'is_current', 'created_at']
    ordering = ['-version_number']


@admin.register(AdvancedContentPage)
class AdvancedContentPageAdmin(admin.ModelAdmin):
    """
    Admin interface for advanced content pages.
    """
    list_display = ['title', 'page_type', 'status', 'author', 'is_published', 'language', 'view_count', 'created_at']
    list_filter = ['page_type', 'status', 'is_published', 'language', 'author', 'created_at', 'is_deleted']
    search_fields = ['title', 'content', 'excerpt']
    readonly_fields = ['view_count', 'engagement_score', 'conversion_rate', 'bounce_rate', 'is_currently_published', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    inlines = [ContentVersionInline]
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return AdvancedContentPage.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type', 'excerpt', 'content', 'content_json')
        }),
        ('Categorization', {
            'fields': ('template', 'category', 'tags')
        }),
        ('Workflow & Status', {
            'fields': ('status', 'author', 'editor', 'reviewer')
        }),
        ('Publishing', {
            'fields': ('is_published', 'publish_date', 'unpublish_date', 'featured_until', 'is_currently_published')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Personalization', {
            'fields': ('personalization_type', 'personalization_rules', 'target_segments'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'engagement_score', 'conversion_rate', 'bounce_rate'),
            'classes': ('collapse',)
        }),
        ('A/B Testing', {
            'fields': ('is_ab_test', 'ab_test_name', 'ab_test_variant', 'ab_test_traffic_split'),
            'classes': ('collapse',)
        }),
        ('Localization', {
            'fields': ('language', 'translation_parent'),
            'classes': ('collapse',)
        }),
        ('Access Control', {
            'fields': ('is_public', 'required_permissions', 'allowed_user_groups'),
            'classes': ('collapse',)
        }),
        ('Social Media', {
            'fields': ('social_image', 'social_title', 'social_description'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentWorkflow)
class ContentWorkflowAdmin(admin.ModelAdmin):
    """
    Admin interface for content workflows.
    """
    list_display = ['name', 'workflow_type', 'is_active', 'is_default', 'auto_publish', 'created_at']
    list_filter = ['workflow_type', 'is_active', 'is_default', 'auto_publish', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['applicable_categories']
    ordering = ['name']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentWorkflow.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'workflow_type')
        }),
        ('Configuration', {
            'fields': ('steps', 'auto_publish', 'notification_settings')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default')
        }),
        ('Applicability', {
            'fields': ('applicable_content_types', 'applicable_categories')
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentWorkflowInstance)
class ContentWorkflowInstanceAdmin(admin.ModelAdmin):
    """
    Admin interface for content workflow instances.
    """
    list_display = ['content_page', 'workflow', 'status', 'current_step', 'initiated_by', 'created_at']
    list_filter = ['workflow', 'status', 'initiated_by', 'created_at', 'is_deleted']
    search_fields = ['content_page__title', 'workflow__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentWorkflowInstance.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('content_page', 'workflow', 'initiated_by')
        }),
        ('Status', {
            'fields': ('status', 'current_step', 'completion_date')
        }),
        ('Data', {
            'fields': ('workflow_data', 'comments', 'rejection_reason')
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentAsset)
class ContentAssetAdmin(admin.ModelAdmin):
    """
    Admin interface for content assets.
    """
    list_display = ['name', 'asset_type', 'file_size', 'category', 'is_public', 'usage_count', 'uploaded_by', 'created_at']
    list_filter = ['asset_type', 'category', 'is_public', 'uploaded_by', 'created_at', 'is_deleted']
    search_fields = ['name', 'description', 'original_filename']
    readonly_fields = ['file_size', 'mime_type', 'usage_count', 'last_used', 'created_at', 'updated_at']
    filter_horizontal = ['tags']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentAsset.objects.all()
    
    def file_preview(self, obj):
        """Display file preview for images."""
        if obj.asset_type == 'image' and obj.file:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.file.url
            )
        return '-'
    file_preview.short_description = 'Preview'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'asset_type')
        }),
        ('File Information', {
            'fields': ('file', 'thumbnail', 'file_size', 'mime_type', 'original_filename')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Metadata', {
            'fields': ('alt_text', 'caption', 'copyright_info')
        }),
        ('Settings', {
            'fields': ('is_public', 'uploaded_by')
        }),
        ('Analytics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentSchedule)
class ContentScheduleAdmin(admin.ModelAdmin):
    """
    Admin interface for content schedules.
    """
    list_display = ['content_page', 'action_type', 'scheduled_time', 'status', 'created_by', 'created_at']
    list_filter = ['action_type', 'status', 'created_by', 'created_at', 'is_deleted']
    search_fields = ['content_page__title']
    readonly_fields = ['executed_at', 'execution_log', 'created_at']
    ordering = ['scheduled_time']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentSchedule.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('content_page', 'action_type', 'scheduled_time')
        }),
        ('Configuration', {
            'fields': ('action_data', 'created_by')
        }),
        ('Status', {
            'fields': ('status', 'executed_at', 'execution_log')
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentSyndication)
class ContentSyndicationAdmin(admin.ModelAdmin):
    """
    Admin interface for content syndication.
    """
    list_display = ['name', 'platform_type', 'is_active', 'auto_sync', 'sync_frequency', 'last_sync', 'sync_count']
    list_filter = ['platform_type', 'is_active', 'auto_sync', 'created_at', 'is_deleted']
    search_fields = ['name', 'description']
    readonly_fields = ['last_sync', 'sync_count', 'created_at', 'updated_at']
    filter_horizontal = ['categories', 'tags']
    ordering = ['name']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentSyndication.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'platform_type')
        }),
        ('Configuration', {
            'fields': ('platform_config', 'api_endpoint', 'authentication_data')
        }),
        ('Content Filtering', {
            'fields': ('content_filters', 'categories', 'tags')
        }),
        ('Sync Settings', {
            'fields': ('is_active', 'auto_sync', 'sync_frequency')
        }),
        ('Analytics', {
            'fields': ('last_sync', 'sync_count'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentAnalytics)
class ContentAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for content analytics.
    """
    list_display = ['content_page', 'metric_type', 'metric_value', 'date', 'user_segment', 'traffic_source']
    list_filter = ['metric_type', 'date', 'user_segment', 'traffic_source', 'device_type', 'is_deleted']
    search_fields = ['content_page__title']
    readonly_fields = ['date', 'created_at', 'updated_at']
    ordering = ['-date']
    
    def get_queryset(self, request):
        """Include soft-deleted items for admin."""
        return ContentAnalytics.objects.all()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('content_page', 'metric_type', 'metric_value', 'date')
        }),
        ('Segmentation', {
            'fields': ('user_segment', 'traffic_source', 'device_type', 'location')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('System', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )