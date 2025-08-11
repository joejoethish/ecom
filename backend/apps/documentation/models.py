from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.utils.text import slugify
from django.urls import reverse
import uuid

User = get_user_model()


class DocumentationCategory(models.Model):
    """Categories for organizing documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Documentation Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class DocumentationTemplate(models.Model):
    """Templates for creating documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_template = models.TextField()
    metadata_schema = JSONField(default=dict)  # JSON schema for metadata
    category = models.ForeignKey(DocumentationCategory, on_delete=models.CASCADE, related_name='templates')
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Documentation(models.Model):
    """Main documentation model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('private', 'Private'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, max_length=500)
    category = models.ForeignKey(DocumentationCategory, on_delete=models.CASCADE, related_name='documents')
    template = models.ForeignKey(DocumentationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='internal')
    
    # Metadata
    metadata = JSONField(default=dict)
    tags = models.ManyToManyField('DocumentationTag', blank=True)
    
    # Authoring
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_docs')
    contributors = models.ManyToManyField(User, through='DocumentationContributor', related_name='contributed_docs')
    
    # Versioning
    version = models.CharField(max_length=20, default='1.0')
    parent_version = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versions')
    
    # SEO and search
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True, max_length=300)
    search_vector = SearchVectorField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['status', 'visibility']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            # Auto-generate excerpt from content
            self.excerpt = self.content[:500] + '...' if len(self.content) > 500 else self.content
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('documentation:detail', kwargs={'slug': self.slug})


class DocumentationTag(models.Model):
    """Tags for documentation"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    color = models.CharField(max_length=7, default='#6B7280')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DocumentationContributor(models.Model):
    """Through model for documentation contributors"""
    ROLE_CHOICES = [
        ('author', 'Author'),
        ('editor', 'Editor'),
        ('reviewer', 'Reviewer'),
        ('translator', 'Translator'),
    ]

    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='editor')
    contributed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['documentation', 'user', 'role']


class DocumentationVersion(models.Model):
    """Version history for documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='version_history')
    version_number = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    content = models.TextField()
    metadata = JSONField(default=dict)
    changes_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['documentation', 'version_number']

    def __str__(self):
        return f"{self.documentation.title} v{self.version_number}"


class DocumentationComment(models.Model):
    """Comments on documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.documentation.title}"


class DocumentationReview(models.Model):
    """Review workflow for documentation"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doc_reviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['documentation', 'reviewer']

    def __str__(self):
        return f"Review of {self.documentation.title} by {self.reviewer.username}"


class DocumentationAnalytics(models.Model):
    """Analytics for documentation usage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='analytics')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Event data
    event_type = models.CharField(max_length=50)  # view, like, share, download, etc.
    event_data = JSONField(default=dict)
    
    # Time tracking
    time_spent = models.PositiveIntegerField(default=0)  # seconds
    scroll_depth = models.FloatField(default=0.0)  # percentage
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['documentation', 'event_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} on {self.documentation.title}"


class DocumentationFeedback(models.Model):
    """User feedback on documentation"""
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    is_helpful = models.BooleanField(null=True, blank=True)
    suggestions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['documentation', 'user']

    def __str__(self):
        return f"Feedback on {self.documentation.title}"


class DocumentationBookmark(models.Model):
    """User bookmarks for documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doc_bookmarks')
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='bookmarks')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'documentation']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.documentation.title}"


class DocumentationTranslation(models.Model):
    """Translations for documentation"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('ar', 'Arabic'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    title = models.CharField(max_length=300)
    content = models.TextField()
    excerpt = models.TextField(blank=True, max_length=500)
    translator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='translations')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['documentation', 'language']

    def __str__(self):
        return f"{self.documentation.title} ({self.get_language_display()})"