"""
Enhanced product models for the comprehensive admin panel.
"""
import uuid
import json
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.utils.text import slugify
from core.models import TimestampedModel
from apps.products.models import Product, Category
from apps.admin_panel.models import AdminUser


class ProductVariant(TimestampedModel):
    """
    Product variant management with attributes, options, and SKU generation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant identification
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Variant attributes (JSON field for flexible attributes)
    attributes = models.JSONField(default=dict, help_text="Variant attributes like size, color, etc.")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Physical properties
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'product_variants'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_default']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_default=True),
                name='unique_default_variant_per_product'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def available_quantity(self):
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        
        # Ensure only one default variant per product
        if self.is_default:
            ProductVariant.objects.filter(
                product=self.product, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)

    def generate_sku(self):
        """Generate SKU based on product and variant attributes."""
        base_sku = self.product.sku or self.product.name[:10].upper().replace(' ', '')
        variant_code = ''.join([str(v)[:3].upper() for v in self.attributes.values()])
        return f"{base_sku}-{variant_code}-{uuid.uuid4().hex[:6].upper()}"


class ProductAttribute(TimestampedModel):
    """
    Product attributes for variant management.
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    attribute_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('color', 'Color'),
            ('size', 'Size'),
            ('boolean', 'Boolean'),
            ('select', 'Select'),
        ],
        default='text'
    )
    is_required = models.BooleanField(default=False)
    is_variant_attribute = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'product_attributes'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.display_name


class ProductAttributeValue(TimestampedModel):
    """
    Predefined values for product attributes.
    """
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200)
    display_value = models.CharField(max_length=200)
    color_code = models.CharField(max_length=7, blank=True, help_text="Hex color code for color attributes")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_attribute_values'
        ordering = ['sort_order', 'value']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.display_value}"


class ProductBundle(TimestampedModel):
    """
    Product bundle and kit management with dynamic pricing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Bundle configuration
    bundle_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixed Bundle'),
            ('dynamic', 'Dynamic Bundle'),
            ('kit', 'Product Kit'),
        ],
        default='fixed'
    )
    
    # Pricing
    pricing_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixed Price'),
            ('sum', 'Sum of Products'),
            ('discount', 'Discount from Sum'),
        ],
        default='sum'
    )
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_bundles'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def calculated_price(self):
        """Calculate bundle price based on pricing type."""
        if self.pricing_type == 'fixed' and self.fixed_price:
            return self.fixed_price
        
        total_price = sum(item.product.price * item.quantity for item in self.items.all())
        
        if self.pricing_type == 'discount':
            discount_amount = total_price * (self.discount_percentage / 100)
            return total_price - discount_amount
        
        return total_price


class ProductBundleItem(TimestampedModel):
    """
    Items within a product bundle.
    """
    bundle = models.ForeignKey(ProductBundle, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    is_optional = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'product_bundle_items'
        ordering = ['sort_order']
        unique_together = ['bundle', 'product', 'variant']

    def __str__(self):
        variant_name = f" ({self.variant.name})" if self.variant else ""
        return f"{self.bundle.name} - {self.product.name}{variant_name} x{self.quantity}"


class ProductRelationship(TimestampedModel):
    """
    Product relationship management (related, cross-sell, up-sell products).
    """
    RELATIONSHIP_TYPES = [
        ('related', 'Related Products'),
        ('cross_sell', 'Cross-sell'),
        ('up_sell', 'Up-sell'),
        ('alternative', 'Alternative'),
        ('accessory', 'Accessory'),
        ('replacement', 'Replacement'),
    ]
    
    source_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='relationships_from')
    target_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='relationships_to')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    priority = models.IntegerField(default=0, help_text="Higher priority items appear first")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_relationships'
        ordering = ['-priority', 'created_at']
        unique_together = ['source_product', 'target_product', 'relationship_type']

    def __str__(self):
        return f"{self.source_product.name} -> {self.target_product.name} ({self.get_relationship_type_display()})"


class ProductLifecycle(TimestampedModel):
    """
    Product lifecycle management (draft, active, discontinued, archived).
    """
    LIFECYCLE_STAGES = [
        ('concept', 'Concept'),
        ('development', 'Development'),
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('active', 'Active'),
        ('featured', 'Featured'),
        ('sale', 'On Sale'),
        ('discontinued', 'Discontinued'),
        ('archived', 'Archived'),
        ('recalled', 'Recalled'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='lifecycle')
    current_stage = models.CharField(max_length=20, choices=LIFECYCLE_STAGES, default='draft')
    previous_stage = models.CharField(max_length=20, choices=LIFECYCLE_STAGES, blank=True)
    
    # Stage dates
    concept_date = models.DateTimeField(null=True, blank=True)
    development_date = models.DateTimeField(null=True, blank=True)
    draft_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    active_date = models.DateTimeField(null=True, blank=True)
    discontinued_date = models.DateTimeField(null=True, blank=True)
    archived_date = models.DateTimeField(null=True, blank=True)
    
    # Lifecycle metadata
    stage_notes = models.JSONField(default=dict, blank=True)
    automated_transitions = models.BooleanField(default=False)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'product_lifecycles'

    def __str__(self):
        return f"{self.product.name} - {self.get_current_stage_display()}"

    def transition_to_stage(self, new_stage, user=None, notes=""):
        """Transition product to a new lifecycle stage."""
        if new_stage not in dict(self.LIFECYCLE_STAGES):
            raise ValueError(f"Invalid stage: {new_stage}")
        
        self.previous_stage = self.current_stage
        self.current_stage = new_stage
        
        # Set stage date
        stage_date_field = f"{new_stage}_date"
        if hasattr(self, stage_date_field):
            setattr(self, stage_date_field, timezone.now())
        
        # Add notes
        if notes:
            if new_stage not in self.stage_notes:
                self.stage_notes[new_stage] = []
            self.stage_notes[new_stage].append({
                'date': timezone.now().isoformat(),
                'user': user.username if user else 'system',
                'notes': notes
            })
        
        self.save()


class ProductVersion(TimestampedModel):
    """
    Product versioning and change history tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    
    # Versioned data (JSON snapshot of product data)
    product_data = models.JSONField()
    variant_data = models.JSONField(default=list)
    image_data = models.JSONField(default=list)
    
    # Change information
    change_summary = models.TextField()
    change_details = models.JSONField(default=dict)
    changed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    
    # Version status
    is_current = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'product_versions'
        ordering = ['-created_at']
        unique_together = ['product', 'version_number']

    def __str__(self):
        return f"{self.product.name} v{self.version_number}"

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one current version per product
            ProductVersion.objects.filter(
                product=self.product,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        
        super().save(*args, **kwargs)


class ProductTemplate(TimestampedModel):
    """
    Product template system for quick product creation with predefined attributes.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='templates')
    
    # Template data
    template_data = models.JSONField(help_text="Default product data structure")
    required_attributes = models.JSONField(default=list)
    optional_attributes = models.JSONField(default=list)
    
    # Template configuration
    auto_generate_sku = models.BooleanField(default=True)
    sku_pattern = models.CharField(max_length=100, blank=True)
    default_pricing_rules = models.JSONField(default=dict)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'product_templates'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def create_product_from_template(self, product_data, user=None):
        """Create a new product using this template."""
        # Merge template data with provided data
        merged_data = {**self.template_data, **product_data}
        
        # Create product
        product = Product.objects.create(**merged_data)
        
        # Track usage
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        
        return product


class ProductQuality(TimestampedModel):
    """
    Product quality management with defect tracking and recalls.
    """
    QUALITY_STATUS_CHOICES = [
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('pending', 'Quality Pending'),
        ('recalled', 'Recalled'),
        ('quarantined', 'Quarantined'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='quality')
    quality_status = models.CharField(max_length=20, choices=QUALITY_STATUS_CHOICES, default='pending')
    
    # Quality metrics
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    defect_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    return_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    # Quality checks
    last_quality_check = models.DateTimeField(null=True, blank=True)
    next_quality_check = models.DateTimeField(null=True, blank=True)
    quality_check_frequency = models.IntegerField(default=30, help_text="Days between quality checks")
    
    # Compliance and certifications
    certifications = models.JSONField(default=list)
    compliance_status = models.JSONField(default=dict)
    
    # Recall information
    is_recalled = models.BooleanField(default=False)
    recall_date = models.DateTimeField(null=True, blank=True)
    recall_reason = models.TextField(blank=True)
    recall_severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        blank=True
    )
    
    class Meta:
        db_table = 'product_quality'

    def __str__(self):
        return f"{self.product.name} - {self.get_quality_status_display()}"


class ProductWarranty(TimestampedModel):
    """
    Product warranty and service management.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='warranty')
    
    # Warranty terms
    warranty_period_months = models.IntegerField(default=12)
    warranty_type = models.CharField(
        max_length=20,
        choices=[
            ('manufacturer', 'Manufacturer Warranty'),
            ('extended', 'Extended Warranty'),
            ('service', 'Service Warranty'),
            ('replacement', 'Replacement Warranty'),
        ],
        default='manufacturer'
    )
    
    # Warranty coverage
    coverage_details = models.JSONField(default=dict)
    exclusions = models.JSONField(default=list)
    
    # Service information
    service_provider = models.CharField(max_length=200, blank=True)
    service_contact = models.JSONField(default=dict)
    
    # Terms and conditions
    terms_and_conditions = models.TextField(blank=True)
    warranty_document = models.FileField(upload_to='warranties/', blank=True)
    
    class Meta:
        db_table = 'product_warranties'

    def __str__(self):
        return f"{self.product.name} - {self.warranty_period_months} months"


class ProductDigitalAsset(TimestampedModel):
    """
    Product digital asset management (videos, documents, 3D models).
    """
    ASSET_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('3d_model', '3D Model'),
        ('audio', 'Audio'),
        ('manual', 'Manual'),
        ('specification', 'Specification'),
        ('certificate', 'Certificate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='digital_assets')
    
    # Asset information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    
    # File information
    file = models.FileField(upload_to='product_assets/')
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Asset metadata
    metadata = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    
    # Access control
    is_public = models.BooleanField(default=True)
    requires_authentication = models.BooleanField(default=False)
    
    # Organization
    sort_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'product_digital_assets'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.get_asset_type_display()})"


class ProductSyndication(TimestampedModel):
    """
    Product syndication for external marketplaces and channels.
    """
    CHANNEL_TYPES = [
        ('marketplace', 'Marketplace'),
        ('social', 'Social Media'),
        ('affiliate', 'Affiliate Network'),
        ('comparison', 'Price Comparison'),
        ('feed', 'Product Feed'),
        ('api', 'API Integration'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('synced', 'Synced'),
        ('error', 'Error'),
        ('disabled', 'Disabled'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='syndications')
    
    # Channel information
    channel_name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    channel_url = models.URLField(blank=True)
    
    # Syndication configuration
    sync_enabled = models.BooleanField(default=True)
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('manual', 'Manual'),
        ],
        default='daily'
    )
    
    # Mapping and transformation
    field_mapping = models.JSONField(default=dict)
    transformation_rules = models.JSONField(default=dict)
    
    # Status and tracking
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    last_sync_date = models.DateTimeField(null=True, blank=True)
    next_sync_date = models.DateTimeField(null=True, blank=True)
    sync_error_message = models.TextField(blank=True)
    
    # External references
    external_id = models.CharField(max_length=200, blank=True)
    external_url = models.URLField(blank=True)
    
    class Meta:
        db_table = 'product_syndications'
        unique_together = ['product', 'channel_name']

    def __str__(self):
        return f"{self.product.name} -> {self.channel_name}"


class ProductAnalytics(TimestampedModel):
    """
    Product analytics with performance metrics, sales data, and profitability analysis.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='admin_analytics')
    
    # Sales metrics
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance metrics
    view_count = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    # Time-based metrics
    sales_last_30_days = models.IntegerField(default=0)
    revenue_last_30_days = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    views_last_30_days = models.IntegerField(default=0)
    
    # Ranking and popularity
    popularity_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category_rank = models.IntegerField(null=True, blank=True)
    overall_rank = models.IntegerField(null=True, blank=True)
    
    # Forecasting data
    demand_forecast = models.JSONField(default=dict)
    seasonal_trends = models.JSONField(default=dict)
    
    # Last update
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_analytics'

    def __str__(self):
        return f"{self.product.name} - Analytics"

    def calculate_metrics(self):
        """Calculate and update product metrics."""
        # This would contain logic to calculate various metrics
        # from orders, views, and other data sources
        pass