from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DocumentationCategory, DocumentationTemplate, Documentation,
    DocumentationTag, DocumentationContributor, DocumentationVersion,
    DocumentationComment, DocumentationReview, DocumentationAnalytics,
    DocumentationFeedback, DocumentationBookmark, DocumentationTranslation
)


@admin.register(DocumentationCategory)
class DocumentationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'document_count', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']

    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'


@admin.register(DocumentationTemplate)
class DocumentationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'is_default', 'created_at']
    list_filter = ['category', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentationTag)
class DocumentationTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'usage_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def usage_count(self, obj):
        return obj.documentation_set.count()
    usage_count.short_description = 'Usage Count'


class DocumentationContributorInline(admin.TabularInline):
    model = DocumentationContributor
    extra = 0


class DocumentationVersionInline(admin.TabularInline):
    model = DocumentationVersion
    extra = 0
    readonly_fields = ['created_by', 'created_at']


@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'author', 'status', 'visibility',
        'view_count', 'like_count', 'created_at'
    ]
    list_filter = [
        'status', 'visibility', 'category', 'created_at', 'updated_at'
    ]
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['author', 'view_count', 'like_count', 'search_vector']
    filter_horizontal = ['tags']
    inlines = [DocumentationContributorInline, DocumentationVersionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'template', 'tags')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'metadata')
        }),
        ('Publishing', {
            'fields': ('status', 'visibility', 'version', 'parent_version')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'like_count', 'published_at'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('author', 'search_vector', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields


@admin.register(DocumentationVersion)
class DocumentationVersionAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'version_number', 'created_by', 'created_at'
    ]
    list_filter = ['created_at', 'documentation__category']
    search_fields = ['documentation__title', 'version_number', 'changes_summary']
    readonly_fields = ['created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentationComment)
class DocumentationCommentAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'author', 'is_resolved', 'created_at'
    ]
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['documentation__title', 'author__username', 'content']
    readonly_fields = ['author', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentationReview)
class DocumentationReviewAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'reviewer', 'status', 'reviewed_at', 'created_at'
    ]
    list_filter = ['status', 'reviewed_at', 'created_at']
    search_fields = ['documentation__title', 'reviewer__username']
    readonly_fields = ['reviewer', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.reviewer = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentationAnalytics)
class DocumentationAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'user', 'event_type', 'time_spent', 'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['documentation__title', 'user__username', 'event_type']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False  # Analytics are created automatically

    def has_change_permission(self, request, obj=None):
        return False  # Analytics should not be modified


@admin.register(DocumentationFeedback)
class DocumentationFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'user', 'rating', 'is_helpful', 'created_at'
    ]
    list_filter = ['rating', 'is_helpful', 'created_at']
    search_fields = ['documentation__title', 'user__username', 'comment']
    readonly_fields = ['user', 'created_at']


@admin.register(DocumentationBookmark)
class DocumentationBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'documentation', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'documentation__title']
    readonly_fields = ['user', 'created_at']


@admin.register(DocumentationTranslation)
class DocumentationTranslationAdmin(admin.ModelAdmin):
    list_display = [
        'documentation', 'language', 'translator', 'is_approved', 'created_at'
    ]
    list_filter = ['language', 'is_approved', 'created_at']
    search_fields = ['documentation__title', 'translator__username', 'title']
    readonly_fields = ['translator', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.translator = request.user
        super().save_model(request, obj, form, change)