"""
Advanced Content Management System models for comprehensive content management.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import BaseModel
import json

User = get_user_model()


class Banner(BaseModel):
    """
    Banner model for promotional banners across the platform.
    """
    BANNER_TYPES = [
        ('hero', 'Hero Banner'),
        ('promotional', 'Promotional Banner'),
        ('category', 'Category Banner'),
        ('product', 'Product Banner'),
        ('sidebar', 'Sidebar Banner'),
    ]
    
    BANNER_POSITIONS = [
        ('top', 'Top'),
        ('middle', 'Middle'),
        ('bottom', 'Bottom'),
        ('sidebar', 'Sidebar'),
        ('popup', 'Popup'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', blank=True, null=True)
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPES, default='promotional')
    position = models.CharField(max_length=20, choices=BANNER_POSITIONS, default='top')
    
    # Link configuration
    link_url = models.URLField(blank=True, help_text="External URL or internal path")
    link_text = models.CharField(max_length=100, blank=True, default="Learn More")
    opens_in_new_tab = models.BooleanField(default=False)
    
    # Display configuration
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Targeting
    target_categories = models.ManyToManyField(
        'products.Category', 
        blank=True,
        help_text="Show banner only on these category pages"
    )
    target_pages = models.JSONField(
        default=list,
        blank=True,
        help_text="List of page paths where banner should appear"
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    # Styling
    background_color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    text_color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    custom_css = models.TextField(blank=True, help_text="Custom CSS for banner styling")

    class Meta:
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),
            models.Index(fields=['banner_type', 'position']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.title} ({self.banner_type})"

    @property
    def is_currently_active(self):
        """Check if banner is currently active based on dates."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    @property
    def click_through_rate(self):
        """Calculate click-through rate as percentage."""
        if self.view_count == 0:
            return 0
        return round((self.click_count / self.view_count) * 100, 2)

    def increment_views(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_clicks(self):
        """Increment click count."""
        self.click_count += 1
        self.save(update_fields=['click_count'])


class Carousel(BaseModel):
    """
    Carousel model for managing image/content carousels.
    """
    CAROUSEL_TYPES = [
        ('hero', 'Hero Carousel'),
        ('product', 'Product Carousel'),
        ('category', 'Category Carousel'),
        ('testimonial', 'Testimonial Carousel'),
        ('brand', 'Brand Carousel'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    carousel_type = models.CharField(max_length=20, choices=CAROUSEL_TYPES, default='hero')
    is_active = models.BooleanField(default=True)
    auto_play = models.BooleanField(default=True)
    auto_play_speed = models.PositiveIntegerField(
        default=5000,
        help_text="Auto-play speed in milliseconds"
    )
    show_indicators = models.BooleanField(default=True)
    show_navigation = models.BooleanField(default=True)
    infinite_loop = models.BooleanField(default=True)
    
    # Display configuration
    items_per_view = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    items_per_view_mobile = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Targeting
    target_pages = models.JSONField(
        default=list,
        blank=True,
        help_text="List of page paths where carousel should appear"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'carousel_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.carousel_type})"

    @property
    def active_items_count(self):
        """Get count of active carousel items."""
        return self.items.filter(is_active=True).count()


class CarouselItem(BaseModel):
    """
    Individual items within a carousel.
    """
    carousel = models.ForeignKey(
        Carousel,
        on_delete=models.CASCADE,
        related_name='items'
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='carousel/')
    mobile_image = models.ImageField(upload_to='carousel/mobile/', blank=True, null=True)
    
    # Link configuration
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True, default="View More")
    opens_in_new_tab = models.BooleanField(default=False)
    
    # Display configuration
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Styling
    background_color = models.CharField(max_length=7, blank=True)
    text_color = models.CharField(max_length=7, blank=True)
    overlay_opacity = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['carousel', 'is_active', 'sort_order']),
        ]

    def __str__(self):
        return f"{self.carousel.name} - {self.title}"

    @property
    def click_through_rate(self):
        """Calculate click-through rate as percentage."""
        if self.view_count == 0:
            return 0
        return round((self.click_count / self.view_count) * 100, 2)

    def increment_views(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_clicks(self):
        """Increment click count."""
        self.click_count += 1
        self.save(update_fields=['click_count'])


class ContentPage(BaseModel):
    """
    Model for managing static content pages like About Us, Terms, etc.
    """
    PAGE_TYPES = [
        ('about', 'About Us'),
        ('terms', 'Terms & Conditions'),
        ('privacy', 'Privacy Policy'),
        ('faq', 'FAQ'),
        ('contact', 'Contact Us'),
        ('custom', 'Custom Page'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='custom')
    content = models.TextField()
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=False)
    show_in_header = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'show_in_footer']),
            models.Index(fields=['is_active', 'show_in_header']),
        ]

    def __str__(self):
        return self.title


class Announcement(BaseModel):
    """
    Model for site-wide announcements and notifications.
    """
    ANNOUNCEMENT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('promotion', 'Promotion'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    target_user_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of user types: ['all', 'customers', 'sellers', 'admins']"
    )
    target_pages = models.JSONField(
        default=list,
        blank=True,
        help_text="List of page paths where announcement should appear"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_currently_active(self):
        """Check if announcement is currently active based on dates."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


# Advanced Content Management System Models

class ContentTemplate(BaseModel):
    """
    Template library for reusable content structures.
    """
    TEMPLATE_TYPES = [
        ('page', 'Page Template'),
        ('email', 'Email Template'),
        ('banner', 'Banner Template'),
        ('product', 'Product Template'),
        ('blog', 'Blog Template'),
        ('landing', 'Landing Page Template'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    structure = models.JSONField(help_text="Template structure definition")
    preview_image = models.ImageField(upload_to='templates/previews/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    usage_count = models.PositiveIntegerField(default=0)
    
    # Template configuration
    default_styles = models.JSONField(default=dict, blank=True)
    required_fields = models.JSONField(default=list, blank=True)
    optional_fields = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
            models.Index(fields=['is_system_template']),
        ]

    def __str__(self):
        return f"{self.name} ({self.template_type})"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class ContentCategory(BaseModel):
    """
    Hierarchical category system for content organization.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=100, blank=True, help_text="Icon class or name")
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name_plural = "Content Categories"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Get full category path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class ContentTag(BaseModel):
    """
    Tagging system for content classification.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    usage_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.name

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class AdvancedContentPage(BaseModel):
    """
    Advanced content page with versioning, workflow, and personalization.
    """
    PAGE_TYPES = [
        ('page', 'Static Page'),
        ('landing', 'Landing Page'),
        ('blog', 'Blog Post'),
        ('news', 'News Article'),
        ('help', 'Help Article'),
        ('legal', 'Legal Document'),
        ('custom', 'Custom Page'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('rejected', 'Rejected'),
    ]

    PERSONALIZATION_TYPES = [
        ('none', 'No Personalization'),
        ('segment', 'User Segment'),
        ('location', 'Geographic'),
        ('device', 'Device Type'),
        ('behavior', 'Behavioral'),
        ('custom', 'Custom Rules'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='page')
    excerpt = models.TextField(blank=True, help_text="Short description or summary")
    
    # Content
    content = models.TextField()
    content_json = models.JSONField(default=dict, blank=True, help_text="Structured content for page builder")
    template = models.ForeignKey(ContentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Categorization
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(ContentTag, blank=True)
    
    # Workflow and Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_content')
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_content')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_content')
    
    # Publishing
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    unpublish_date = models.DateTimeField(null=True, blank=True)
    featured_until = models.DateTimeField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    canonical_url = models.URLField(blank=True)
    
    # Personalization
    personalization_type = models.CharField(max_length=20, choices=PERSONALIZATION_TYPES, default='none')
    personalization_rules = models.JSONField(default=dict, blank=True)
    target_segments = models.JSONField(default=list, blank=True)
    
    # Analytics and Performance
    view_count = models.PositiveIntegerField(default=0)
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_name = models.CharField(max_length=200, blank=True)
    ab_test_variant = models.CharField(max_length=50, blank=True)
    ab_test_traffic_split = models.PositiveIntegerField(default=50, validators=[MinValueValidator(1), MaxValueValidator(100)])
    
    # Localization
    language = models.CharField(max_length=10, default='en')
    translation_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='translations')
    
    # Access Control
    is_public = models.BooleanField(default=True)
    required_permissions = models.JSONField(default=list, blank=True)
    allowed_user_groups = models.JSONField(default=list, blank=True)
    
    # Social Media
    social_image = models.ImageField(upload_to='content/social/', blank=True, null=True)
    social_title = models.CharField(max_length=200, blank=True)
    social_description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_published']),
            models.Index(fields=['slug']),
            models.Index(fields=['page_type', 'status']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['publish_date']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_currently_published(self):
        """Check if content is currently published."""
        if not self.is_published or self.status != 'published':
            return False
        
        now = timezone.now()
        if self.publish_date and self.publish_date > now:
            return False
        if self.unpublish_date and self.unpublish_date < now:
            return False
        
        return True

    def increment_views(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ContentVersion(BaseModel):
    """
    Version history for content pages.
    """
    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    content_json = models.JSONField(default=dict, blank=True)
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_current = models.BooleanField(default=False)
    
    # Metadata snapshot
    metadata_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['content_page', 'version_number']
        indexes = [
            models.Index(fields=['content_page', 'version_number']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.content_page.title} - v{self.version_number}"


class ContentWorkflow(BaseModel):
    """
    Workflow management for content approval process.
    """
    WORKFLOW_TYPES = [
        ('simple', 'Simple Approval'),
        ('multi_level', 'Multi-Level Review'),
        ('peer_review', 'Peer Review'),
        ('legal_review', 'Legal Review'),
        ('custom', 'Custom Workflow'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Workflow configuration
    steps = models.JSONField(default=list, help_text="Workflow steps configuration")
    auto_publish = models.BooleanField(default=False)
    notification_settings = models.JSONField(default=dict, blank=True)
    
    # Content type restrictions
    applicable_content_types = models.JSONField(default=list, blank=True)
    applicable_categories = models.ManyToManyField(ContentCategory, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'is_default']),
        ]

    def __str__(self):
        return self.name


class ContentWorkflowInstance(BaseModel):
    """
    Individual workflow instances for content items.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='workflow_instances')
    workflow = models.ForeignKey(ContentWorkflow, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_step = models.PositiveIntegerField(default=0)
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_workflows')
    
    # Workflow data
    workflow_data = models.JSONField(default=dict, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Comments and feedback
    comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_page', 'status']),
            models.Index(fields=['workflow', 'status']),
        ]

    def __str__(self):
        return f"{self.content_page.title} - {self.workflow.name}"


class ContentAsset(BaseModel):
    """
    Digital asset management for content.
    """
    ASSET_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    file = models.FileField(upload_to='content/assets/')
    thumbnail = models.ImageField(upload_to='content/assets/thumbnails/', blank=True, null=True)
    
    # File metadata
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    original_filename = models.CharField(max_length=255)
    
    # Categorization
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(ContentTag, blank=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Access control
    is_public = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # SEO and metadata
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    copyright_info = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_type', 'is_public']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return self.name

    def increment_usage(self):
        """Increment usage count and update last used."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class ContentAnalytics(BaseModel):
    """
    Analytics and performance tracking for content.
    """
    METRIC_TYPES = [
        ('view', 'Page View'),
        ('engagement', 'Engagement'),
        ('conversion', 'Conversion'),
        ('share', 'Social Share'),
        ('download', 'Download'),
        ('click', 'Click'),
    ]

    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='analytics')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    
    # Segmentation data
    user_segment = models.CharField(max_length=100, blank=True)
    traffic_source = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['content_page', 'metric_type', 'date', 'user_segment']
        indexes = [
            models.Index(fields=['content_page', 'date']),
            models.Index(fields=['metric_type', 'date']),
        ]

    def __str__(self):
        return f"{self.content_page.title} - {self.metric_type} ({self.date})"


class ContentSchedule(BaseModel):
    """
    Content scheduling and publication management.
    """
    ACTION_TYPES = [
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ('archive', 'Archive'),
        ('delete', 'Delete'),
        ('update', 'Update'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='schedules')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Action configuration
    action_data = models.JSONField(default=dict, blank=True)
    
    # Execution tracking
    executed_at = models.DateTimeField(null=True, blank=True)
    execution_log = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_time', 'status']),
            models.Index(fields=['content_page', 'status']),
        ]

    def __str__(self):
        return f"{self.content_page.title} - {self.action_type} at {self.scheduled_time}"


class ContentSyndication(BaseModel):
    """
    Content syndication and distribution management.
    """
    PLATFORM_TYPES = [
        ('social_media', 'Social Media'),
        ('rss', 'RSS Feed'),
        ('api', 'API Distribution'),
        ('email', 'Email Newsletter'),
        ('partner', 'Partner Site'),
        ('marketplace', 'Marketplace'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    platform_type = models.CharField(max_length=20, choices=PLATFORM_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Platform configuration
    platform_config = models.JSONField(default=dict, blank=True)
    api_endpoint = models.URLField(blank=True)
    authentication_data = models.JSONField(default=dict, blank=True)
    
    # Content filtering
    content_filters = models.JSONField(default=dict, blank=True)
    categories = models.ManyToManyField(ContentCategory, blank=True)
    tags = models.ManyToManyField(ContentTag, blank=True)
    
    # Scheduling
    auto_sync = models.BooleanField(default=False)
    sync_frequency = models.PositiveIntegerField(default=60, help_text="Sync frequency in minutes")
    last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'auto_sync']),
        ]

    def __str__(self):
        return self.name


class ContentCollaboration(BaseModel):
    """
    Content collaboration and team editing.
    """
    ROLE_TYPES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('reviewer', 'Reviewer'),
        ('viewer', 'Viewer'),
        ('commenter', 'Commenter'),
    ]

    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='collaborations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_TYPES)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Permissions
    can_edit_content = models.BooleanField(default=False)
    can_edit_metadata = models.BooleanField(default=False)
    can_publish = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_invite_others = models.BooleanField(default=False)

    class Meta:
        unique_together = ['content_page', 'user']
        indexes = [
            models.Index(fields=['content_page', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role} on {self.content_page.title}"


class ContentComment(BaseModel):
    """
    Comments and feedback on content.
    """
    content_page = models.ForeignKey(AdvancedContentPage, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Comment metadata
    is_resolved = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_comments')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Position in content (for inline comments)
    content_position = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_page', 'is_resolved']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.content_page.title}"