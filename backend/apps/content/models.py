"""
Content management models for banners, carousels, and promotional content.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel


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