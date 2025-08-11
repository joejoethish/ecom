"""
Content management serializers for API responses.
"""
from rest_framework import serializers
from .models import (
    Banner, Carousel, CarouselItem, ContentPage, Announcement,
    ContentTemplate, AdvancedContentPage, ContentVersion, ContentWorkflow,
    ContentWorkflowInstance, ContentAsset, ContentCategory, ContentTag,
    ContentAnalytics, ContentSchedule, ContentSyndication
)


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


# Advanced Content Management Serializers

class ContentCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for content categories.
    """
    full_path = serializers.CharField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = ContentCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'icon', 'color',
            'sort_order', 'is_active', 'meta_title', 'meta_description',
            'full_path', 'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_path', 'children', 'created_at', 'updated_at']

    def get_children(self, obj):
        """Get child categories."""
        children = obj.children.filter(is_active=True).order_by('sort_order', 'name')
        return ContentCategorySerializer(children, many=True).data


class ContentTagSerializer(serializers.ModelSerializer):
    """
    Serializer for content tags.
    """
    class Meta:
        model = ContentTag
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'usage_count',
            'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class ContentTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for content templates.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ContentTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'structure',
            'preview_image', 'is_active', 'is_system_template', 'created_by',
            'created_by_name', 'usage_count', 'default_styles', 'required_fields',
            'optional_fields', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by_name', 'usage_count', 'created_at', 'updated_at'
        ]


class ContentVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for content versions.
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ContentVersion
        fields = [
            'id', 'version_number', 'title', 'content', 'content_json',
            'change_summary', 'created_by', 'created_by_name', 'is_current',
            'metadata_snapshot', 'created_at'
        ]
        read_only_fields = [
            'id', 'version_number', 'created_by_name', 'is_current', 'created_at'
        ]


class ContentWorkflowSerializer(serializers.ModelSerializer):
    """
    Serializer for content workflows.
    """
    applicable_categories_names = serializers.SerializerMethodField()

    class Meta:
        model = ContentWorkflow
        fields = [
            'id', 'name', 'description', 'workflow_type', 'is_active',
            'is_default', 'steps', 'auto_publish', 'notification_settings',
            'applicable_content_types', 'applicable_categories',
            'applicable_categories_names', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applicable_categories_names', 'created_at', 'updated_at']

    def get_applicable_categories_names(self, obj):
        """Get names of applicable categories."""
        return [cat.name for cat in obj.applicable_categories.all()]


class ContentWorkflowInstanceSerializer(serializers.ModelSerializer):
    """
    Serializer for content workflow instances.
    """
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    initiated_by_name = serializers.CharField(source='initiated_by.username', read_only=True)
    content_page_title = serializers.CharField(source='content_page.title', read_only=True)

    class Meta:
        model = ContentWorkflowInstance
        fields = [
            'id', 'content_page', 'content_page_title', 'workflow', 'workflow_name',
            'status', 'current_step', 'initiated_by', 'initiated_by_name',
            'workflow_data', 'completion_date', 'comments', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'workflow_name', 'initiated_by_name', 'content_page_title',
            'created_at', 'updated_at'
        ]


class ContentAssetSerializer(serializers.ModelSerializer):
    """
    Serializer for content assets.
    """
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_names = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ContentAsset
        fields = [
            'id', 'name', 'description', 'asset_type', 'file', 'thumbnail',
            'file_size', 'file_size_formatted', 'mime_type', 'original_filename',
            'category', 'category_name', 'tags', 'tag_names', 'usage_count',
            'last_used', 'is_public', 'uploaded_by', 'uploaded_by_name',
            'alt_text', 'caption', 'copyright_info', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploaded_by_name', 'category_name', 'tag_names',
            'file_size_formatted', 'usage_count', 'last_used', 'created_at', 'updated_at'
        ]

    def get_tag_names(self, obj):
        """Get names of tags."""
        return [tag.name for tag in obj.tags.all()]

    def get_file_size_formatted(self, obj):
        """Format file size in human readable format."""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class AdvancedContentPageSerializer(serializers.ModelSerializer):
    """
    Serializer for advanced content pages.
    """
    author_name = serializers.CharField(source='author.username', read_only=True)
    editor_name = serializers.CharField(source='editor.username', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    tag_names = serializers.SerializerMethodField()
    is_currently_published = serializers.BooleanField(read_only=True)
    current_version = serializers.SerializerMethodField()
    workflow_status = serializers.SerializerMethodField()

    class Meta:
        model = AdvancedContentPage
        fields = [
            'id', 'title', 'slug', 'page_type', 'excerpt', 'content', 'content_json',
            'template', 'template_name', 'category', 'category_name', 'tags', 'tag_names',
            'status', 'author', 'author_name', 'editor', 'editor_name', 'reviewer',
            'reviewer_name', 'is_published', 'publish_date', 'unpublish_date',
            'featured_until', 'meta_title', 'meta_description', 'meta_keywords',
            'canonical_url', 'personalization_type', 'personalization_rules',
            'target_segments', 'view_count', 'engagement_score', 'conversion_rate',
            'bounce_rate', 'is_ab_test', 'ab_test_name', 'ab_test_variant',
            'ab_test_traffic_split', 'language', 'translation_parent', 'is_public',
            'required_permissions', 'allowed_user_groups', 'social_image',
            'social_title', 'social_description', 'is_currently_published',
            'current_version', 'workflow_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author_name', 'editor_name', 'reviewer_name', 'category_name',
            'template_name', 'tag_names', 'is_currently_published', 'current_version',
            'workflow_status', 'view_count', 'engagement_score', 'conversion_rate',
            'bounce_rate', 'created_at', 'updated_at'
        ]

    def get_tag_names(self, obj):
        """Get names of tags."""
        return [tag.name for tag in obj.tags.all()]

    def get_current_version(self, obj):
        """Get current version number."""
        current_version = obj.versions.filter(is_current=True).first()
        return current_version.version_number if current_version else None

    def get_workflow_status(self, obj):
        """Get current workflow status."""
        active_workflow = obj.workflow_instances.filter(
            status__in=['pending', 'in_progress']
        ).first()
        if active_workflow:
            return {
                'workflow_name': active_workflow.workflow.name,
                'status': active_workflow.status,
                'current_step': active_workflow.current_step
            }
        return None


class AdvancedContentPageCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating advanced content pages.
    """
    class Meta:
        model = AdvancedContentPage
        fields = [
            'title', 'slug', 'page_type', 'excerpt', 'content', 'content_json',
            'template', 'category', 'tags', 'status', 'editor', 'reviewer',
            'is_published', 'publish_date', 'unpublish_date', 'featured_until',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
            'personalization_type', 'personalization_rules', 'target_segments',
            'is_ab_test', 'ab_test_name', 'ab_test_variant', 'ab_test_traffic_split',
            'language', 'translation_parent', 'is_public', 'required_permissions',
            'allowed_user_groups', 'social_image', 'social_title', 'social_description'
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness."""
        if self.instance:
            if AdvancedContentPage.objects.exclude(id=self.instance.id).filter(slug=value).exists():
                raise serializers.ValidationError("A page with this slug already exists")
        else:
            if AdvancedContentPage.objects.filter(slug=value).exists():
                raise serializers.ValidationError("A page with this slug already exists")
        return value

    def validate(self, data):
        """Validate content page data."""
        publish_date = data.get('publish_date')
        unpublish_date = data.get('unpublish_date')
        
        if publish_date and unpublish_date and publish_date >= unpublish_date:
            raise serializers.ValidationError("unpublish_date must be after publish_date")
        
        ab_test_traffic_split = data.get('ab_test_traffic_split', 50)
        if not 1 <= ab_test_traffic_split <= 100:
            raise serializers.ValidationError("ab_test_traffic_split must be between 1 and 100")
        
        return data


class ContentScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for content schedules.
    """
    content_page_title = serializers.CharField(source='content_page.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ContentSchedule
        fields = [
            'id', 'content_page', 'content_page_title', 'action_type',
            'scheduled_time', 'status', 'action_data', 'executed_at',
            'execution_log', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'content_page_title', 'created_by_name', 'status',
            'executed_at', 'execution_log', 'created_at'
        ]


class ContentSyndicationSerializer(serializers.ModelSerializer):
    """
    Serializer for content syndication.
    """
    categories_names = serializers.SerializerMethodField()
    tags_names = serializers.SerializerMethodField()

    class Meta:
        model = ContentSyndication
        fields = [
            'id', 'name', 'description', 'platform_type', 'is_active',
            'platform_config', 'api_endpoint', 'content_filters',
            'categories', 'categories_names', 'tags', 'tags_names',
            'auto_sync', 'sync_frequency', 'last_sync', 'sync_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'categories_names', 'tags_names', 'last_sync',
            'sync_count', 'created_at', 'updated_at'
        ]

    def get_categories_names(self, obj):
        """Get names of categories."""
        return [cat.name for cat in obj.categories.all()]

    def get_tags_names(self, obj):
        """Get names of tags."""
        return [tag.name for tag in obj.tags.all()]


# Page Builder Serializers

class PageBuilderComponentSerializer(serializers.Serializer):
    """
    Serializer for page builder components.
    """
    id = serializers.CharField()
    type = serializers.CharField()
    props = serializers.DictField()
    children = serializers.ListField(child=serializers.DictField(), required=False)
    styles = serializers.DictField(required=False)


class PageBuilderDataSerializer(serializers.Serializer):
    """
    Serializer for page builder data structure.
    """
    components = PageBuilderComponentSerializer(many=True)
    layout = serializers.DictField(required=False)
    theme = serializers.DictField(required=False)
    custom_css = serializers.CharField(required=False)


# Content Analytics Serializers

class ContentPerformanceSerializer(serializers.Serializer):
    """
    Serializer for content performance analytics.
    """
    page_id = serializers.IntegerField()
    title = serializers.CharField()
    page_type = serializers.CharField()
    views = serializers.IntegerField()
    engagement_score = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    avg_time_on_page = serializers.FloatField()
    social_shares = serializers.IntegerField()


class ContentDashboardSerializer(serializers.Serializer):
    """
    Serializer for content management dashboard.
    """
    total_pages = serializers.IntegerField()
    published_pages = serializers.IntegerField()
    draft_pages = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_assets = serializers.IntegerField()
    recent_activity = serializers.ListField()
    top_performing_pages = ContentPerformanceSerializer(many=True)


# Workflow Management Serializers

class WorkflowStepSerializer(serializers.Serializer):
    """
    Serializer for workflow steps.
    """
    step_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    assignee_role = serializers.CharField()
    required_permissions = serializers.ListField(child=serializers.CharField(), required=False)
    auto_approve = serializers.BooleanField(default=False)
    timeout_hours = serializers.IntegerField(required=False)


class WorkflowActionSerializer(serializers.Serializer):
    """
    Serializer for workflow actions.
    """
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_changes'])
    comments = serializers.CharField(required=False)
    next_step = serializers.IntegerField(required=False)


# Content Import/Export Serializers

class ContentExportSerializer(serializers.Serializer):
    """
    Serializer for content export requests.
    """
    content_ids = serializers.ListField(child=serializers.IntegerField())
    export_format = serializers.ChoiceField(choices=['json', 'csv', 'xml'])
    include_assets = serializers.BooleanField(default=False)
    include_versions = serializers.BooleanField(default=False)


class ContentImportSerializer(serializers.Serializer):
    """
    Serializer for content import requests.
    """
    import_file = serializers.FileField()
    import_format = serializers.ChoiceField(choices=['json', 'csv', 'xml'])
    overwrite_existing = serializers.BooleanField(default=False)
    create_backup = serializers.BooleanField(default=True)