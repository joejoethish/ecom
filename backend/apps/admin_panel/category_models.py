"""
Comprehensive Category Management Models for Admin Panel.
"""
import uuid
import json
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import TimestampedModel
from .models import AdminUser


class CategoryTemplate(TimestampedModel):
    """
    Template system for consistent category creation.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template configuration
    default_attributes = models.JSONField(default=dict, blank=True)
    seo_template = models.JSONField(default=dict, blank=True)
    image_requirements = models.JSONField(default=dict, blank=True)
    
    # Template properties
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'category_templates'
        verbose_name = 'Category Template'
        verbose_name_plural = 'Category Templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return self.name


class EnhancedCategory(TimestampedModel):
    """
    Enhanced category model with comprehensive admin features.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
        ('scheduled', 'Scheduled'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('restricted', 'Restricted'),
        ('hidden', 'Hidden'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    
    # Hierarchical Structure (Modified Preorder Tree Traversal)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    level = models.PositiveIntegerField(default=0)
    lft = models.PositiveIntegerField(default=0)  # Left boundary
    rght = models.PositiveIntegerField(default=0)  # Right boundary
    tree_id = models.PositiveIntegerField(default=0)
    
    # Visual and Media
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    banner = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True)  # CSS class or icon name
    color_scheme = models.JSONField(default=dict, blank=True)  # Primary, secondary colors
    
    # SEO Management
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    canonical_url = models.URLField(blank=True)
    og_title = models.CharField(max_length=200, blank=True)
    og_description = models.TextField(max_length=500, blank=True)
    og_image = models.ImageField(upload_to='categories/og/', blank=True, null=True)
    
    # Status and Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Publishing and Scheduling
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_publish_at = models.DateTimeField(null=True, blank=True)
    scheduled_unpublish_at = models.DateTimeField(null=True, blank=True)
    
    # Performance and Analytics
    view_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Localization
    language = models.CharField(max_length=10, default='en')
    translations = models.JSONField(default=dict, blank=True)
    
    # Template and Configuration
    template = models.ForeignKey(CategoryTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    custom_attributes = models.JSONField(default=dict, blank=True)
    display_settings = models.JSONField(default=dict, blank=True)
    
    # Access Control
    access_roles = models.ManyToManyField('AdminRole', blank=True, related_name='accessible_categories')
    restricted_users = models.ManyToManyField(AdminUser, blank=True, related_name='restricted_categories')
    
    # Audit and Management
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_categories')
    last_modified_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_categories')
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_categories')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # External Integration
    external_id = models.CharField(max_length=100, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'enhanced_categories'
        verbose_name = 'Enhanced Category'
        verbose_name_plural = 'Enhanced Categories'
        ordering = ['tree_id', 'lft']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'status']),
            models.Index(fields=['status', 'visibility']),
            models.Index(fields=['tree_id', 'lft', 'rght']),
            models.Index(fields=['level']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['language']),
            models.Index(fields=['created_by']),
            models.Index(fields=['published_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'language'],
                name='unique_slug_per_language'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-publish if scheduled
        if self.scheduled_publish_at and timezone.now() >= self.scheduled_publish_at:
            self.status = 'active'
            self.published_at = timezone.now()
            self.scheduled_publish_at = None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Return full category path for hierarchical display."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def breadcrumb(self):
        """Return breadcrumb list for navigation."""
        breadcrumb = []
        current = self
        while current:
            breadcrumb.insert(0, {
                'id': str(current.id),
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        return breadcrumb

    def get_descendants(self, include_self=False):
        """Get all descendant categories using tree structure."""
        if include_self:
            return EnhancedCategory.objects.filter(
                tree_id=self.tree_id,
                lft__gte=self.lft,
                rght__lte=self.rght
            )
        else:
            return EnhancedCategory.objects.filter(
                tree_id=self.tree_id,
                lft__gt=self.lft,
                rght__lt=self.rght
            )

    def get_ancestors(self, include_self=False):
        """Get all ancestor categories."""
        if include_self:
            return EnhancedCategory.objects.filter(
                tree_id=self.tree_id,
                lft__lte=self.lft,
                rght__gte=self.rght
            )
        else:
            return EnhancedCategory.objects.filter(
                tree_id=self.tree_id,
                lft__lt=self.lft,
                rght__gt=self.rght
            )

    def get_siblings(self, include_self=False):
        """Get sibling categories."""
        siblings = EnhancedCategory.objects.filter(parent=self.parent)
        if not include_self:
            siblings = siblings.exclude(pk=self.pk)
        return siblings

    def move_to(self, target, position='last-child'):
        """Move category to new position in tree."""
        # This would implement the tree restructuring logic
        # For now, we'll update the parent relationship
        if position == 'last-child':
            self.parent = target
            self.level = target.level + 1 if target else 0
        self.save()

    def is_ancestor_of(self, other):
        """Check if this category is an ancestor of another."""
        return (self.tree_id == other.tree_id and 
                self.lft < other.lft and 
                self.rght > other.rght)

    def is_descendant_of(self, other):
        """Check if this category is a descendant of another."""
        return other.is_ancestor_of(self)


class CategoryAttribute(TimestampedModel):
    """
    Category-specific attributes for product filtering.
    """
    ATTRIBUTE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('select', 'Select'),
        ('multiselect', 'Multi-Select'),
        ('range', 'Range'),
        ('color', 'Color'),
        ('size', 'Size'),
        ('date', 'Date'),
    ]
    
    category = models.ForeignKey(EnhancedCategory, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    
    # Attribute Configuration
    attribute_type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPE_CHOICES)
    is_required = models.BooleanField(default=False)
    is_filterable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=False)
    is_comparable = models.BooleanField(default=False)
    
    # Options and Validation
    options = models.JSONField(default=list, blank=True)  # For select/multiselect
    validation_rules = models.JSONField(default=dict, blank=True)
    default_value = models.CharField(max_length=500, blank=True)
    
    # Display Settings
    display_order = models.PositiveIntegerField(default=0)
    display_name = models.CharField(max_length=100, blank=True)
    help_text = models.CharField(max_length=500, blank=True)
    unit = models.CharField(max_length=20, blank=True)  # kg, cm, etc.
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'category_attributes'
        verbose_name = 'Category Attribute'
        verbose_name_plural = 'Category Attributes'
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['attribute_type']),
            models.Index(fields=['is_filterable']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_attribute_per_category'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class CategoryPerformanceMetric(TimestampedModel):
    """
    Category performance analytics with sales metrics and conversion rates.
    """
    category = models.ForeignKey(EnhancedCategory, on_delete=models.CASCADE, related_name='performance_metrics')
    date = models.DateField()
    
    # Traffic Metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_time_on_page = models.DurationField(null=True, blank=True)
    
    # Sales Metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Product Metrics
    products_viewed = models.PositiveIntegerField(default=0)
    products_added_to_cart = models.PositiveIntegerField(default=0)
    products_purchased = models.PositiveIntegerField(default=0)
    
    # Search and Filter Metrics
    search_queries = models.PositiveIntegerField(default=0)
    filter_usage = models.JSONField(default=dict, blank=True)
    
    # Engagement Metrics
    social_shares = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'category_performance_metrics'
        verbose_name = 'Category Performance Metric'
        verbose_name_plural = 'Category Performance Metrics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['category', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['conversion_rate']),
            models.Index(fields=['total_revenue']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'date'],
                name='unique_metric_per_category_per_date'
            )
        ]

    def __str__(self):
        return f"{self.category.name} - {self.date}"


class CategoryMerchandising(TimestampedModel):
    """
    Category merchandising tools for featured products and promotions.
    """
    MERCHANDISING_TYPE_CHOICES = [
        ('featured_products', 'Featured Products'),
        ('banner_promotion', 'Banner Promotion'),
        ('product_spotlight', 'Product Spotlight'),
        ('seasonal_display', 'Seasonal Display'),
        ('cross_sell', 'Cross-sell'),
        ('up_sell', 'Up-sell'),
        ('new_arrivals', 'New Arrivals'),
        ('best_sellers', 'Best Sellers'),
    ]
    
    category = models.ForeignKey(EnhancedCategory, on_delete=models.CASCADE, related_name='merchandising')
    name = models.CharField(max_length=200)
    merchandising_type = models.CharField(max_length=30, choices=MERCHANDISING_TYPE_CHOICES)
    
    # Configuration
    configuration = models.JSONField(default=dict)
    display_rules = models.JSONField(default=dict)
    targeting_rules = models.JSONField(default=dict)
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Display Settings
    position = models.CharField(max_length=50, default='top')
    priority = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Performance Tracking
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    
    # Management
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'category_merchandising'
        verbose_name = 'Category Merchandising'
        verbose_name_plural = 'Category Merchandising'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['merchandising_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    @property
    def is_currently_active(self):
        """Check if merchandising is currently active."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    @property
    def click_through_rate(self):
        """Calculate click-through rate."""
        if self.impressions > 0:
            return round((self.clicks / self.impressions) * 100, 2)
        return 0

    @property
    def conversion_rate(self):
        """Calculate conversion rate."""
        if self.clicks > 0:
            return round((self.conversions / self.clicks) * 100, 2)
        return 0


class CategoryAuditLog(TimestampedModel):
    """
    Category audit trail with change history and rollback capabilities.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('move', 'Move'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ('archive', 'Archive'),
        ('restore', 'Restore'),
        ('bulk_update', 'Bulk Update'),
        ('import', 'Import'),
        ('export', 'Export'),
    ]
    
    category = models.ForeignKey(EnhancedCategory, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Change Details
    field_changes = models.JSONField(default=dict, blank=True)  # Before/after values
    previous_state = models.JSONField(default=dict, blank=True)  # Full previous state
    additional_data = models.JSONField(default=dict, blank=True)  # Extra context
    
    # User and Session
    user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Metadata
    reason = models.TextField(blank=True)
    batch_id = models.UUIDField(null=True, blank=True)  # For bulk operations
    
    class Meta:
        db_table = 'category_audit_logs'
        verbose_name = 'Category Audit Log'
        verbose_name_plural = 'Category Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['batch_id']),
        ]

    def __str__(self):
        user = self.user.username if self.user else 'System'
        return f"{user} - {self.action} - {self.category.name} - {self.created_at}"


class CategoryRelationship(TimestampedModel):
    """
    Category relationship management (parent-child, cross-references).
    """
    RELATIONSHIP_TYPE_CHOICES = [
        ('parent_child', 'Parent-Child'),
        ('related', 'Related'),
        ('similar', 'Similar'),
        ('cross_sell', 'Cross-sell'),
        ('substitute', 'Substitute'),
        ('complement', 'Complement'),
        ('seasonal', 'Seasonal'),
        ('trending', 'Trending'),
    ]
    
    from_category = models.ForeignKey(
        EnhancedCategory, 
        on_delete=models.CASCADE, 
        related_name='outgoing_relationships'
    )
    to_category = models.ForeignKey(
        EnhancedCategory, 
        on_delete=models.CASCADE, 
        related_name='incoming_relationships'
    )
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPE_CHOICES)
    
    # Relationship Properties
    strength = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)  # 0.0 to 1.0
    is_bidirectional = models.BooleanField(default=False)
    weight = models.PositiveIntegerField(default=0)  # For ordering
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'category_relationships'
        verbose_name = 'Category Relationship'
        verbose_name_plural = 'Category Relationships'
        ordering = ['-weight', '-created_at']
        indexes = [
            models.Index(fields=['from_category', 'relationship_type']),
            models.Index(fields=['to_category', 'relationship_type']),
            models.Index(fields=['relationship_type', 'is_active']),
            models.Index(fields=['strength']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['from_category', 'to_category', 'relationship_type'],
                name='unique_category_relationship'
            )
        ]

    def __str__(self):
        return f"{self.from_category.name} -> {self.to_category.name} ({self.relationship_type})"


class CategoryImportExport(TimestampedModel):
    """
    Category import/export functionality with validation and error handling.
    """
    OPERATION_TYPE_CHOICES = [
        ('import', 'Import'),
        ('export', 'Export'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ]
    
    # Operation Details
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Files
    source_file = models.FileField(upload_to='category_imports/', blank=True, null=True)
    result_file = models.FileField(upload_to='category_exports/', blank=True, null=True)
    error_file = models.FileField(upload_to='category_errors/', blank=True, null=True)
    
    # Configuration
    import_config = models.JSONField(default=dict, blank=True)
    field_mapping = models.JSONField(default=dict, blank=True)
    validation_rules = models.JSONField(default=dict, blank=True)
    
    # Results
    total_records = models.PositiveIntegerField(default=0)
    processed_records = models.PositiveIntegerField(default=0)
    successful_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)
    
    # Error Tracking
    errors = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'category_import_export'
        verbose_name = 'Category Import/Export'
        verbose_name_plural = 'Category Import/Export'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operation_type', 'status']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.operation_type.title()} - {self.status} - {self.created_at}"

    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_records > 0:
            return round((self.successful_records / self.total_records) * 100, 2)
        return 0

    @property
    def duration(self):
        """Calculate operation duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class CategoryRecommendation(TimestampedModel):
    """
    Category recommendation system for product placement.
    """
    RECOMMENDATION_TYPE_CHOICES = [
        ('product_placement', 'Product Placement'),
        ('category_merge', 'Category Merge'),
        ('category_split', 'Category Split'),
        ('attribute_addition', 'Attribute Addition'),
        ('seo_optimization', 'SEO Optimization'),
        ('performance_improvement', 'Performance Improvement'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    category = models.ForeignKey(EnhancedCategory, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPE_CHOICES)
    
    # Recommendation Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    rationale = models.TextField()
    expected_impact = models.TextField()
    
    # Configuration
    recommended_changes = models.JSONField(default=dict)
    implementation_steps = models.JSONField(default=list)
    
    # Prioritization
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    potential_impact_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    
    # Status and Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_recommendations')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Implementation
    implemented_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='implemented_recommendations')
    implemented_at = models.DateTimeField(null=True, blank=True)
    implementation_notes = models.TextField(blank=True)
    
    # AI/ML Metadata
    model_version = models.CharField(max_length=50, blank=True)
    training_data_date = models.DateField(null=True, blank=True)
    algorithm_used = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'category_recommendations'
        verbose_name = 'Category Recommendation'
        verbose_name_plural = 'Category Recommendations'
        ordering = ['-priority', '-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['recommendation_type']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['reviewed_by']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.title}"