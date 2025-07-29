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