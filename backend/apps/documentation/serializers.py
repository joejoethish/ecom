from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DocumentationCategory, DocumentationTemplate, Documentation,
    DocumentationTag, DocumentationContributor, DocumentationVersion,
    DocumentationComment, DocumentationReview, DocumentationAnalytics,
    DocumentationFeedback, DocumentationBookmark, DocumentationTranslation
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for documentation"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DocumentationCategorySerializer(serializers.ModelSerializer):
    """Serializer for documentation categories"""
    children = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentationCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'icon', 'color',
            'sort_order', 'is_active', 'children', 'document_count',
            'created_at', 'updated_at'
        ]

    def get_children(self, obj):
        if hasattr(obj, 'children'):
            return DocumentationCategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []

    def get_document_count(self, obj):
        return obj.documents.filter(status='published').count()


class DocumentationTagSerializer(serializers.ModelSerializer):
    """Serializer for documentation tags"""
    class Meta:
        model = DocumentationTag
        fields = ['id', 'name', 'slug', 'color', 'created_at']


class DocumentationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for documentation templates"""
    created_by = UserBasicSerializer(read_only=True)
    category = DocumentationCategorySerializer(read_only=True)

    class Meta:
        model = DocumentationTemplate
        fields = [
            'id', 'name', 'description', 'content_template', 'metadata_schema',
            'category', 'is_default', 'created_by', 'created_at', 'updated_at'
        ]


class DocumentationContributorSerializer(serializers.ModelSerializer):
    """Serializer for documentation contributors"""
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationContributor
        fields = ['user', 'role', 'contributed_at']


class DocumentationVersionSerializer(serializers.ModelSerializer):
    """Serializer for documentation versions"""
    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationVersion
        fields = [
            'id', 'version_number', 'title', 'content', 'metadata',
            'changes_summary', 'created_by', 'created_at'
        ]


class DocumentationCommentSerializer(serializers.ModelSerializer):
    """Serializer for documentation comments"""
    author = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = DocumentationComment
        fields = [
            'id', 'parent', 'author', 'content', 'is_resolved',
            'replies', 'created_at', 'updated_at'
        ]

    def get_replies(self, obj):
        if hasattr(obj, 'replies'):
            return DocumentationCommentSerializer(obj.replies.all(), many=True).data
        return []


class DocumentationReviewSerializer(serializers.ModelSerializer):
    """Serializer for documentation reviews"""
    reviewer = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationReview
        fields = [
            'id', 'reviewer', 'status', 'feedback', 'reviewed_at', 'created_at'
        ]


class DocumentationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for documentation feedback"""
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationFeedback
        fields = [
            'id', 'user', 'rating', 'comment', 'is_helpful',
            'suggestions', 'created_at'
        ]


class DocumentationBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for documentation bookmarks"""
    user = UserBasicSerializer(read_only=True)
    documentation = serializers.StringRelatedField()

    class Meta:
        model = DocumentationBookmark
        fields = ['id', 'user', 'documentation', 'notes', 'created_at']


class DocumentationTranslationSerializer(serializers.ModelSerializer):
    """Serializer for documentation translations"""
    translator = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationTranslation
        fields = [
            'id', 'language', 'title', 'content', 'excerpt',
            'translator', 'is_approved', 'created_at', 'updated_at'
        ]


class DocumentationListSerializer(serializers.ModelSerializer):
    """Serializer for documentation list view"""
    author = UserBasicSerializer(read_only=True)
    category = DocumentationCategorySerializer(read_only=True)
    tags = DocumentationTagSerializer(many=True, read_only=True)
    contributor_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Documentation
        fields = [
            'id', 'title', 'slug', 'excerpt', 'category', 'status', 'visibility',
            'author', 'tags', 'version', 'view_count', 'like_count',
            'contributor_count', 'comment_count', 'average_rating',
            'published_at', 'created_at', 'updated_at'
        ]

    def get_contributor_count(self, obj):
        return obj.contributors.count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_average_rating(self, obj):
        feedback = obj.feedback.all()
        if feedback:
            return sum(f.rating for f in feedback) / len(feedback)
        return 0


class DocumentationDetailSerializer(serializers.ModelSerializer):
    """Serializer for documentation detail view"""
    author = UserBasicSerializer(read_only=True)
    category = DocumentationCategorySerializer(read_only=True)
    template = DocumentationTemplateSerializer(read_only=True)
    tags = DocumentationTagSerializer(many=True, read_only=True)
    contributors = DocumentationContributorSerializer(many=True, read_only=True)
    comments = DocumentationCommentSerializer(many=True, read_only=True)
    reviews = DocumentationReviewSerializer(many=True, read_only=True)
    feedback = DocumentationFeedbackSerializer(many=True, read_only=True)
    translations = DocumentationTranslationSerializer(many=True, read_only=True)
    version_history = DocumentationVersionSerializer(many=True, read_only=True)
    
    # Analytics
    average_rating = serializers.SerializerMethodField()
    total_feedback = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Documentation
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'category', 'template',
            'status', 'visibility', 'metadata', 'tags', 'author', 'contributors',
            'version', 'parent_version', 'meta_title', 'meta_description',
            'view_count', 'like_count', 'comments', 'reviews', 'feedback',
            'translations', 'version_history', 'average_rating', 'total_feedback',
            'is_bookmarked', 'published_at', 'created_at', 'updated_at'
        ]

    def get_average_rating(self, obj):
        feedback = obj.feedback.all()
        if feedback:
            return sum(f.rating for f in feedback) / len(feedback)
        return 0

    def get_total_feedback(self, obj):
        return obj.feedback.count()

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False


class DocumentationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating documentation"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DocumentationTag.objects.all(), required=False
    )

    class Meta:
        model = Documentation
        fields = [
            'title', 'content', 'excerpt', 'category', 'template', 'status',
            'visibility', 'metadata', 'tags', 'version', 'parent_version',
            'meta_title', 'meta_description'
        ]

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        documentation = Documentation.objects.create(**validated_data)
        documentation.tags.set(tags)
        return documentation

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class DocumentationAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for documentation analytics"""
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = DocumentationAnalytics
        fields = [
            'id', 'user', 'session_id', 'event_type', 'event_data',
            'time_spent', 'scroll_depth', 'created_at'
        ]