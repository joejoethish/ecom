"""
Product models for the ecommerce platform.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from core.models import BaseModel


class Category(BaseModel):
    """
    Product category model with hierarchical structure.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        """Return full category path for hierarchical display."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    def get_descendants(self):
        """Get all descendant categories."""
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Product(BaseModel):
    """
    Product model with comprehensive fields for e-commerce.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Weight in kg"
    )
    dimensions = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Dimensions as JSON: {'length': 0, 'width': 0, 'height': 0}"
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    
    # Additional fields for better product management
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('out_of_stock', 'Out of Stock'),
        ],
        default='draft'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        """Return the effective price (discount price if available, otherwise regular price)."""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage if discount price is set."""
        if self.discount_price and self.price > 0:
            return round(((self.price - self.discount_price) / self.price) * 100, 2)
        return 0

    @property
    def primary_image(self):
        """Get the primary product image."""
        return self.images.filter(is_primary=True).first()

    def get_tags_list(self):
        """Return tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def update_rating_aggregation(self):
        """Update product rating aggregation based on approved reviews."""
        from django.db.models import Avg, Count
        from apps.reviews.models import Review
        
        approved_reviews = Review.objects.filter(
            product=self, 
            status='approved'
        )
        
        aggregation = approved_reviews.aggregate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
        )
        
        # Update or create ProductRating
        rating, created = ProductRating.objects.get_or_create(
            product=self,
            defaults={
                'average_rating': aggregation['avg_rating'] or 0,
                'total_reviews': aggregation['review_count'] or 0,
            }
        )
        
        if not created:
            rating.average_rating = aggregation['avg_rating'] or 0
            rating.total_reviews = aggregation['review_count'] or 0
            rating.save()
        
        return rating

    @property
    def average_rating(self):
        """Get the average rating for this product."""
        try:
            return self.rating.average_rating
        except ProductRating.DoesNotExist:
            return 0

    @property
    def total_reviews(self):
        """Get the total number of approved reviews for this product."""
        try:
            return self.rating.total_reviews
        except ProductRating.DoesNotExist:
            return 0


class ProductImage(BaseModel):
    """
    Product image model for multiple product images.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'sort_order']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_product'
            )
        ]

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # Set alt_text if not provided
        if not self.alt_text:
            self.alt_text = f"{self.product.name} - Image {self.sort_order}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"


class ProductRating(BaseModel):
    """
    Product rating aggregation model.
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Rating distribution
    rating_1_count = models.PositiveIntegerField(default=0)
    rating_2_count = models.PositiveIntegerField(default=0)
    rating_3_count = models.PositiveIntegerField(default=0)
    rating_4_count = models.PositiveIntegerField(default=0)
    rating_5_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['average_rating']),
            models.Index(fields=['total_reviews']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.average_rating}/5 ({self.total_reviews} reviews)"

    def update_rating_distribution(self):
        """Update the rating distribution counts."""
        from apps.reviews.models import Review
        from django.db.models import Count, Q
        
        distribution = Review.objects.filter(
            product=self.product,
            status='approved'
        ).aggregate(
            rating_1=Count('id', filter=Q(rating=1)),
            rating_2=Count('id', filter=Q(rating=2)),
            rating_3=Count('id', filter=Q(rating=3)),
            rating_4=Count('id', filter=Q(rating=4)),
            rating_5=Count('id', filter=Q(rating=5)),
        )
        
        self.rating_1_count = distribution['rating_1']
        self.rating_2_count = distribution['rating_2']
        self.rating_3_count = distribution['rating_3']
        self.rating_4_count = distribution['rating_4']
        self.rating_5_count = distribution['rating_5']
        self.save()

    @property
    def rating_distribution(self):
        """Get rating distribution as percentages."""
        if self.total_reviews == 0:
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        return {
            5: round((self.rating_5_count / self.total_reviews) * 100, 1),
            4: round((self.rating_4_count / self.total_reviews) * 100, 1),
            3: round((self.rating_3_count / self.total_reviews) * 100, 1),
            2: round((self.rating_2_count / self.total_reviews) * 100, 1),
            1: round((self.rating_1_count / self.total_reviews) * 100, 1),
        }