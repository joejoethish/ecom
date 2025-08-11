from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterFilter
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
import json
import csv
from io import StringIO

from .models import (
    DocumentationCategory, DocumentationTemplate, Documentation,
    DocumentationTag, DocumentationVersion, DocumentationComment,
    DocumentationReview, DocumentationAnalytics, DocumentationFeedback,
    DocumentationBookmark, DocumentationTranslation
)
from .serializers import (
    DocumentationCategorySerializer, DocumentationTemplateSerializer,
    DocumentationListSerializer, DocumentationDetailSerializer,
    DocumentationCreateUpdateSerializer, DocumentationTagSerializer,
    DocumentationVersionSerializer, DocumentationCommentSerializer,
    DocumentationReviewSerializer, DocumentationAnalyticsSerializer,
    DocumentationFeedbackSerializer, DocumentationBookmarkSerializer,
    DocumentationTranslationSerializer
)
from .filters import DocumentationFilter
from .permissions import DocumentationPermission


class DocumentationCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation categories"""
    queryset = DocumentationCategory.objects.filter(is_active=True)
    serializer_class = DocumentationCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure"""
        categories = self.queryset.filter(parent=None).prefetch_related('children')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get documents in a category"""
        category = self.get_object()
        documents = Documentation.objects.filter(
            category=category,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')
        
        serializer = DocumentationListSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation templates"""
    queryset = DocumentationTemplate.objects.all()
    serializer_class = DocumentationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get templates by category"""
        category_id = request.query_params.get('category')
        if category_id:
            templates = self.queryset.filter(category_id=category_id)
            serializer = self.get_serializer(templates, many=True)
            return Response(serializer.data)
        return Response([])


class DocumentationTagViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation tags"""
    queryset = DocumentationTag.objects.all()
    serializer_class = DocumentationTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular tags"""
        tags = self.queryset.annotate(
            usage_count=Count('documentation')
        ).order_by('-usage_count')[:20]
        
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class DocumentationViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation"""
    queryset = Documentation.objects.select_related(
        'author', 'category', 'template'
    ).prefetch_related('tags', 'contributors')
    permission_classes = [DocumentationPermission]
    filter_backends = [DjangoFilterFilter, SearchFilter, OrderingFilter]
    filterset_class = DocumentationFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['title', 'created_at', 'updated_at', 'view_count', 'like_count']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DocumentationCreateUpdateSerializer
        return DocumentationDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by visibility and permissions
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(visibility='public') |
                Q(visibility='internal', author=self.request.user) |
                Q(visibility='restricted', contributors=self.request.user)
            ).distinct()
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Track view analytics
        self.track_analytics(instance, 'view')
        
        # Increment view count
        instance.view_count = F('view_count') + 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def track_analytics(self, documentation, event_type, event_data=None):
        """Track analytics for documentation"""
        DocumentationAnalytics.objects.create(
            documentation=documentation,
            user=self.request.user if self.request.user.is_authenticated else None,
            session_id=self.request.session.session_key or '',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            event_type=event_type,
            event_data=event_data or {}
        )

    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with full-text search"""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])

        # Use PostgreSQL full-text search
        search_query = SearchQuery(query)
        search_vector = SearchVector('title', weight='A') + SearchVector('content', weight='B')
        
        queryset = self.get_queryset().annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DocumentationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentationListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike documentation"""
        documentation = self.get_object()
        
        # Track analytics
        self.track_analytics(documentation, 'like')
        
        # Update like count
        documentation.like_count = F('like_count') + 1
        documentation.save(update_fields=['like_count'])
        
        return Response({'status': 'liked', 'like_count': documentation.like_count})

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark/unbookmark documentation"""
        documentation = self.get_object()
        bookmark, created = DocumentationBookmark.objects.get_or_create(
            user=request.user,
            documentation=documentation,
            defaults={'notes': request.data.get('notes', '')}
        )
        
        if not created:
            bookmark.delete()
            return Response({'status': 'unbookmarked'})
        
        return Response({'status': 'bookmarked'})

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history"""
        documentation = self.get_object()
        versions = documentation.version_history.all()
        serializer = DocumentationVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create new version"""
        documentation = self.get_object()
        
        # Create version from current state
        DocumentationVersion.objects.create(
            documentation=documentation,
            version_number=request.data.get('version_number', documentation.version),
            title=documentation.title,
            content=documentation.content,
            metadata=documentation.metadata,
            changes_summary=request.data.get('changes_summary', ''),
            created_by=request.user
        )
        
        return Response({'status': 'version_created'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for documentation"""
        documentation = self.get_object()
        comments = documentation.comments.filter(parent=None)
        serializer = DocumentationCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to documentation"""
        documentation = self.get_object()
        
        comment = DocumentationComment.objects.create(
            documentation=documentation,
            author=request.user,
            content=request.data.get('content', ''),
            parent_id=request.data.get('parent_id')
        )
        
        serializer = DocumentationCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_feedback(self, request, pk=None):
        """Submit feedback for documentation"""
        documentation = self.get_object()
        
        feedback, created = DocumentationFeedback.objects.update_or_create(
            documentation=documentation,
            user=request.user,
            defaults={
                'rating': request.data.get('rating'),
                'comment': request.data.get('comment', ''),
                'is_helpful': request.data.get('is_helpful'),
                'suggestions': request.data.get('suggestions', '')
            }
        )
        
        serializer = DocumentationFeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for documentation"""
        documentation = self.get_object()
        
        # Basic analytics
        analytics_data = {
            'view_count': documentation.view_count,
            'like_count': documentation.like_count,
            'comment_count': documentation.comments.count(),
            'bookmark_count': documentation.bookmarks.count(),
            'average_rating': documentation.feedback.aggregate(
                avg_rating=Avg('rating')
            )['avg_rating'] or 0,
            'feedback_count': documentation.feedback.count()
        }
        
        # Time-based analytics
        from datetime import datetime, timedelta
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        recent_analytics = documentation.analytics.filter(
            created_at__gte=last_30_days
        )
        
        analytics_data.update({
            'recent_views': recent_analytics.filter(event_type='view').count(),
            'recent_likes': recent_analytics.filter(event_type='like').count(),
            'average_time_spent': recent_analytics.filter(
                event_type='view'
            ).aggregate(avg_time=Avg('time_spent'))['avg_time'] or 0,
            'average_scroll_depth': recent_analytics.filter(
                event_type='view'
            ).aggregate(avg_scroll=Avg('scroll_depth'))['avg_scroll'] or 0
        })
        
        return Response(analytics_data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export documentation to various formats"""
        format_type = request.query_params.get('format', 'json')
        queryset = self.filter_queryset(self.get_queryset())
        
        if format_type == 'csv':
            return self.export_csv(queryset)
        elif format_type == 'json':
            return self.export_json(queryset)
        else:
            return Response({'error': 'Unsupported format'}, status=400)

    def export_csv(self, queryset):
        """Export to CSV format"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Title', 'Category', 'Author', 'Status', 'Created', 'Updated',
            'View Count', 'Like Count'
        ])
        
        # Write data
        for doc in queryset:
            writer.writerow([
                doc.title,
                doc.category.name,
                doc.author.username,
                doc.status,
                doc.created_at.strftime('%Y-%m-%d'),
                doc.updated_at.strftime('%Y-%m-%d'),
                doc.view_count,
                doc.like_count
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="documentation.csv"'
        return response

    def export_json(self, queryset):
        """Export to JSON format"""
        serializer = DocumentationListSerializer(queryset, many=True)
        response = HttpResponse(
            json.dumps(serializer.data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="documentation.json"'
        return response


class DocumentationAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for documentation analytics"""
    queryset = DocumentationAnalytics.objects.all()
    serializer_class = DocumentationAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterFilter, OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by documentation if specified
        doc_id = self.request.query_params.get('documentation')
        if doc_id:
            queryset = queryset.filter(documentation_id=doc_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get analytics summary"""
        queryset = self.get_queryset()
        
        summary = {
            'total_events': queryset.count(),
            'unique_users': queryset.filter(user__isnull=False).values('user').distinct().count(),
            'event_types': queryset.values('event_type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'top_documents': queryset.values(
                'documentation__title'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
        }
        
        return Response(summary)


class DocumentationReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for documentation reviews"""
    queryset = DocumentationReview.objects.all()
    serializer_class = DocumentationReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterFilter, OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by documentation if specified
        doc_id = self.request.query_params.get('documentation')
        if doc_id:
            queryset = queryset.filter(documentation_id=doc_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve documentation review"""
        review = self.get_object()
        review.status = 'approved'
        review.reviewed_at = timezone.now()
        review.save()
        
        # Update documentation status if all reviews are approved
        documentation = review.documentation
        if documentation.reviews.filter(status='pending').count() == 0:
            documentation.status = 'approved'
            documentation.save()
        
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject documentation review"""
        review = self.get_object()
        review.status = 'rejected'
        review.feedback = request.data.get('feedback', '')
        review.reviewed_at = timezone.now()
        review.save()
        
        return Response({'status': 'rejected'})