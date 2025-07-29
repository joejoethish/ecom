"""
Content management serializers for API responses.
"""
from rest_framework import serializers
from .models import Banner, Carousel, CarouselItem, ContentPage, Announcement


class BannerSerializer(serializers.ModelSerializer):
    """
    Serializer for banner management.
    """
    is_currently_active = serializers.BooleanField(read_only=True)
    click_through_rate = serializers.FloatField(read_only=True)
    target_categories_names = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'subtitle', 'description', 'image', 'mobile_image',
            'banner_type', 'position', 'link_url', 'link_text', 'opens_in_new_tab',
            'is_active', 'start_date', 'end_date', 'sort_order', 'target_categories',
            'target_categories_names', 'target_pages', 'view_count', 'click_count',
            'click_through_rate', 'is_currently_active', 'background_color',
            'text_color', 'custom_css', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'click_count', 'click_through_rate',
            'is_currently_active', 'target_categories_names', 'created_at', 'updated_at'
        ]

    def get_target_categories_names(self, obj):
        """Get names of target categories."""
        return [cat.name for cat in obj.target_categories.all()]


class BannerCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating banners.
    """
    class Meta:
        model = Banner
        fields = [
            'title', 'subtitle', 'description', 'image', 'mobile_image',
            'banner_type', 'position', 'link_url', 'link_text', 'opens_in_new_tab',
            'is_active', 'start_date', 'end_date', 'sort_order', 'target_categories',
            'target_pages', 'background_color', 'text_color', 'custom_css'
        ]

    def validate(self, data):
        """Validate banner data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("end_date must be after start_date")
        
        return data


class CarouselItemSerializer(serializers.ModelSerializer):
    """
    Serializer for carousel items.
    """
    click_through_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = CarouselItem
        fields = [
            'id', 'title', 'subtitle', 'description', 'image', 'mobile_image',
            'link_url', 'link_text', 'opens_in_new_tab', 'is_active', 'sort_order',
            'background_color', 'text_color', 'overlay_opacity', 'view_count',
            'click_count', 'click_through_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'click_count', 'click_through_rate',
            'created_at', 'updated_at'
        ]


class CarouselSerializer(serializers.ModelSerializer):
    """
    Serializer for carousel management.
    """
    items = CarouselItemSerializer(many=True, read_only=True)
    active_items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Carousel
        fields = [
            'id', 'name', 'description', 'carousel_type', 'is_active',
            'auto_play', 'auto_play_speed', 'show_indicators', 'show_navigation',
            'infinite_loop', 'items_per_view', 'items_per_view_mobile',
            'target_pages', 'items', 'active_items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'items', 'active_items_count', 'created_at', 'updated_at']


class CarouselCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating carousels.
    """
    class Meta:
        model = Carousel
        fields = [
            'name', 'description', 'carousel_type', 'is_active', 'auto_play',
            'auto_play_speed', 'show_indicators', 'show_navigation', 'infinite_loop',
            'items_per_view', 'items_per_view_mobile', 'target_pages'
        ]

    def validate_auto_play_speed(self, value):
        """Validate auto-play speed."""
        if value < 1000:
            raise serializers.ValidationError("Auto-play speed must be at least 1000ms")
        return value


class CarouselItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating carousel items.
    """
    class Meta:
        model = CarouselItem
        fields = [
            'carousel', 'title', 'subtitle', 'description', 'image', 'mobile_image',
            'link_url', 'link_text', 'opens_in_new_tab', 'is_active', 'sort_order',
            'background_color', 'text_color', 'overlay_opacity'
        ]

    def validate_overlay_opacity(self, value):
        """Validate overlay opacity."""
        if not 0 <= value <= 1:
            raise serializers.ValidationError("Overlay opacity must be between 0 and 1")
        return value


class ContentPageSerializer(serializers.ModelSerializer):
    """
    Serializer for content pages.
    """
    class Meta:
        model = ContentPage
        fields = [
            'id', 'title', 'slug', 'page_type', 'content', 'meta_title',
            'meta_description', 'is_active', 'show_in_footer', 'show_in_header',
            'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_slug(self, value):
        """Validate slug uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if ContentPage.objects.exclude(id=self.instance.id).filter(slug=value).exists():
                raise serializers.ValidationError("A page with this slug already exists")
        else:
            # Create case
            if ContentPage.objects.filter(slug=value).exists():
                raise serializers.ValidationError("A page with this slug already exists")
        return value


class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Serializer for announcements.
    """
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'message', 'announcement_type', 'is_active',
            'is_dismissible', 'start_date', 'end_date', 'target_user_types',
            'target_pages', 'is_currently_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_currently_active', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate announcement data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("end_date must be after start_date")
        
        return data


class BannerAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for banner analytics response.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    banner_type = serializers.CharField()
    position = serializers.CharField()
    views = serializers.IntegerField()
    clicks = serializers.IntegerField()
    ctr = serializers.FloatField()
    is_active = serializers.BooleanField()


class CarouselAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for carousel analytics response.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    carousel_name = serializers.CharField()
    carousel_type = serializers.CharField()
    views = serializers.IntegerField()
    clicks = serializers.IntegerField()
    ctr = serializers.FloatField()
    is_active = serializers.BooleanField()


class ContentAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for content analytics summary.
    """
    banners = serializers.DictField()
    carousels = serializers.DictField()
    total_content_views = serializers.IntegerField()
    total_content_clicks = serializers.IntegerField()


class HomepageContentSerializer(serializers.Serializer):
    """
    Serializer for homepage content response.
    """
    hero_banners = BannerSerializer(many=True)
    hero_carousel = serializers.DictField(allow_null=True)
    promotional_banners = BannerSerializer(many=True)
    announcements = AnnouncementSerializer(many=True)


class CategoryContentSerializer(serializers.Serializer):
    """
    Serializer for category page content response.
    """
    category_banners = BannerSerializer(many=True)
    category_carousel = serializers.DictField(allow_null=True)
    announcements = AnnouncementSerializer(many=True)


class BannerTrackingSerializer(serializers.Serializer):
    """
    Serializer for banner tracking requests.
    """
    banner_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['view', 'click'])

    def validate_banner_id(self, value):
        """Validate banner exists."""
        if not Banner.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Banner not found")
        return value


class CarouselTrackingSerializer(serializers.Serializer):
    """
    Serializer for carousel item tracking requests.
    """
    item_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['view', 'click'])

    def validate_item_id(self, value):
        """Validate carousel item exists."""
        if not CarouselItem.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Carousel item not found")
        return value


class ContentFilterSerializer(serializers.Serializer):
    """
    Serializer for content filtering parameters.
    """
    banner_type = serializers.CharField(required=False)
    position = serializers.CharField(required=False)
    carousel_type = serializers.CharField(required=False)
    page_path = serializers.CharField(required=False)
    category_id = serializers.IntegerField(required=False)
    user_type = serializers.CharField(required=False, default='all')
    is_active = serializers.BooleanField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

    def validate(self, data):
        """Validate filter parameters."""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from must be before date_to")
        
        return data