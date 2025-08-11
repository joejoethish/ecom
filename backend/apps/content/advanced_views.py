"""
Advanced Content Management System views for admin panel.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
import json
import csv
import io

from core.permissions import IsAdminUser
from .models import (
    ContentTemplate, AdvancedContentPage, ContentVersion, ContentWorkflow,
    ContentWorkflowInstance, ContentAsset, ContentCategory, ContentTag,
    ContentAnalytics, ContentSchedule, ContentSyndication
)
from .serializers import (
    ContentTemplateSerializer, AdvancedContentPageSerializer,
    AdvancedContentPageCreateUpdateSerializer, ContentVersionSerializer,
    ContentWorkflowSerializer, ContentWorkflowInstanceSerializer,
    ContentAssetSerializer, ContentCategorySerializer, ContentTagSerializer,
    ContentScheduleSerializer, ContentSyndicationSerializer,
    PageBuilderDataSerializer, ContentDashboardSerializer,
    WorkflowActionSerializer, ContentExportSerializer, ContentImportSerializer
)
from .services import (
    AdvancedContentService, ContentWorkflowService, ContentAssetService,
    PageBuilderService, ContentAnalyticsService
)


class ContentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content template management.
    """
    queryset = ContentTemplate.objects.filter(is_deleted=False).order_by('-usage_count', 'name')
    serializer_class = ContentTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        template_type = self.request.query_params.get('template_type')
        is_active = self.request.query_params.get('is_active')
        is_system = self.request.query_params.get('is_system')
        
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_system is not None:
            queryset = queryset.filter(is_system_template=is_system.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating template."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete template."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a template."""
        template = self.get_object()
        
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.is_system_template = False
        template.created_by = request.user
        template.usage_count = 0
        template.save()
        
        serializer = ContentTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Mark template as used and increment usage count."""
        template = self.get_object()
        template.increment_usage()
        
        return Response({'message': 'Template usage recorded'})


class AdvancedContentPageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for advanced content page management with versioning and workflow.
    """
    queryset = AdvancedContentPage.objects.filter(is_deleted=False).order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return AdvancedContentPageCreateUpdateSerializer
        return AdvancedContentPageSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        page_type = self.request.query_params.get('page_type')
        status_filter = self.request.query_params.get('status')
        category = self.request.query_params.get('category')
        author = self.request.query_params.get('author')
        language = self.request.query_params.get('language')
        is_published = self.request.query_params.get('is_published')
        
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category:
            queryset = queryset.filter(category_id=category)
        if author:
            queryset = queryset.filter(author_id=author)
        if language:
            queryset = queryset.filter(language=language)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set author when creating content page."""
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete content page."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def versions(self, request, slug=None):
        """Get all versions of a content page."""
        content_page = self.get_object()
        versions = content_page.versions.all().order_by('-version_number')
        
        serializer = ContentVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_version(self, request, slug=None):
        """Create a new version of the content page."""
        content_page = self.get_object()
        change_summary = request.data.get('change_summary', '')
        
        try:
            version = AdvancedContentService.create_version(
                content_page, request.user, change_summary
            )
            serializer = ContentVersionSerializer(version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to create version: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def revert_to_version(self, request, slug=None):
        """Revert content page to a specific version."""
        content_page = self.get_object()
        version_number = request.data.get('version_number')
        
        if not version_number:
            return Response(
                {'error': 'version_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            AdvancedContentService.revert_to_version(
                content_page, version_number, request.user
            )
            return Response({'message': f'Reverted to version {version_number}'})
        except Exception as e:
            return Response(
                {'error': f'Failed to revert to version: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, slug=None):
        """Submit content page for workflow review."""
        content_page = self.get_object()
        workflow_id = request.data.get('workflow_id')
        
        try:
            workflow_instance = ContentWorkflowService.submit_for_review(
                content_page, workflow_id, request.user
            )
            serializer = ContentWorkflowInstanceSerializer(workflow_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to submit for review: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def publish(self, request, slug=None):
        """Publish content page."""
        content_page = self.get_object()
        publish_date = request.data.get('publish_date')
        
        try:
            AdvancedContentService.publish_content(
                content_page, request.user, publish_date
            )
            return Response({'message': 'Content published successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to publish content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def unpublish(self, request, slug=None):
        """Unpublish content page."""
        content_page = self.get_object()
        
        try:
            AdvancedContentService.unpublish_content(content_page, request.user)
            return Response({'message': 'Content unpublished successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to unpublish content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, slug=None):
        """Duplicate a content page."""
        content_page = self.get_object()
        
        try:
            duplicated_page = AdvancedContentService.duplicate_content(
                content_page, request.user
            )
            serializer = AdvancedContentPageSerializer(duplicated_page)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to duplicate content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def analytics(self, request, slug=None):
        """Get analytics for content page."""
        content_page = self.get_object()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        try:
            analytics = ContentAnalyticsService.get_page_analytics(
                content_page.id, date_from, date_to
            )
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get content management dashboard data."""
        try:
            dashboard_data = AdvancedContentService.get_dashboard_data()
            serializer = ContentDashboardSerializer(dashboard_data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentWorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content workflow management.
    """
    queryset = ContentWorkflow.objects.filter(is_deleted=False).order_by('name')
    serializer_class = ContentWorkflowSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        workflow_type = self.request.query_params.get('workflow_type')
        is_active = self.request.query_params.get('is_active')
        is_default = self.request.query_params.get('is_default')
        
        if workflow_type:
            queryset = queryset.filter(workflow_type=workflow_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete workflow."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set workflow as default."""
        workflow = self.get_object()
        
        # Remove default from other workflows
        ContentWorkflow.objects.filter(is_default=True).update(is_default=False)
        
        # Set this workflow as default
        workflow.is_default = True
        workflow.save()
        
        return Response({'message': 'Workflow set as default'})


class ContentWorkflowInstanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content workflow instance management.
    """
    queryset = ContentWorkflowInstance.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ContentWorkflowInstanceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status')
        workflow = self.request.query_params.get('workflow')
        content_page = self.request.query_params.get('content_page')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if workflow:
            queryset = queryset.filter(workflow_id=workflow)
        if content_page:
            queryset = queryset.filter(content_page_id=content_page)
            
        return queryset

    @action(detail=True, methods=['post'])
    def process_workflow(self, request, pk=None):
        """Process workflow step (approve, reject, etc.)."""
        workflow_instance = self.get_object()
        
        serializer = WorkflowActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action_data = serializer.validated_data
        
        try:
            result = ContentWorkflowService.process_workflow_step(
                workflow_instance, request.user, action_data
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to process workflow: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentAssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content asset management (digital asset library).
    """
    queryset = ContentAsset.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ContentAssetSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        asset_type = self.request.query_params.get('asset_type')
        category = self.request.query_params.get('category')
        is_public = self.request.query_params.get('is_public')
        uploaded_by = self.request.query_params.get('uploaded_by')
        
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        if category:
            queryset = queryset.filter(category_id=category)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        if uploaded_by:
            queryset = queryset.filter(uploaded_by_id=uploaded_by)
            
        return queryset

    def perform_create(self, serializer):
        """Set uploaded_by when creating asset."""
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete asset."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def use_asset(self, request, pk=None):
        """Mark asset as used and increment usage count."""
        asset = self.get_object()
        asset.increment_usage()
        
        return Response({'message': 'Asset usage recorded'})

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Bulk upload assets."""
        files = request.FILES.getlist('files')
        category_id = request.data.get('category_id')
        is_public = request.data.get('is_public', True)
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uploaded_assets = ContentAssetService.bulk_upload_assets(
                files, request.user, category_id, is_public
            )
            serializer = ContentAssetSerializer(uploaded_assets, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to bulk upload assets: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content category management.
    """
    queryset = ContentCategory.objects.filter(is_deleted=False).order_by('sort_order', 'name')
    serializer_class = ContentCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        parent = self.request.query_params.get('parent')
        is_active = self.request.query_params.get('is_active')
        
        if parent:
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete category."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure."""
        try:
            tree = AdvancedContentService.get_category_tree()
            return Response(tree)
        except Exception as e:
            return Response(
                {'error': f'Failed to get category tree: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentTagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content tag management.
    """
    queryset = ContentTag.objects.filter(is_deleted=False).order_by('-usage_count', 'name')
    serializer_class = ContentTagSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        is_featured = self.request.query_params.get('is_featured')
        
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete tag."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular tags."""
        limit = int(request.query_params.get('limit', 20))
        tags = self.get_queryset()[:limit]
        
        serializer = ContentTagSerializer(tags, many=True)
        return Response(serializer.data)


class PageBuilderViewSet(viewsets.ViewSet):
    """
    ViewSet for page builder functionality.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def save_page_data(self, request):
        """Save page builder data."""
        page_id = request.data.get('page_id')
        page_data = request.data.get('page_data')
        
        if not page_id or not page_data:
            return Response(
                {'error': 'page_id and page_data are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PageBuilderDataSerializer(data=page_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            PageBuilderService.save_page_data(page_id, serializer.validated_data)
            return Response({'message': 'Page data saved successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to save page data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def get_page_data(self, request):
        """Get page builder data."""
        page_id = request.query_params.get('page_id')
        
        if not page_id:
            return Response(
                {'error': 'page_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            page_data = PageBuilderService.get_page_data(page_id)
            return Response(page_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get page data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def components(self, request):
        """Get available page builder components."""
        try:
            components = PageBuilderService.get_available_components()
            return Response(components)
        except Exception as e:
            return Response(
                {'error': f'Failed to get components: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentManagementAdvancedViewSet(viewsets.ViewSet):
    """
    ViewSet for advanced content management operations.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def export_content(self, request):
        """Export content in various formats."""
        serializer = ContentExportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        export_data = serializer.validated_data
        
        try:
            export_result = AdvancedContentService.export_content(export_data)
            
            if export_data['export_format'] == 'json':
                response = HttpResponse(
                    json.dumps(export_result, indent=2),
                    content_type='application/json'
                )
                response['Content-Disposition'] = 'attachment; filename="content_export.json"'
            elif export_data['export_format'] == 'csv':
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=export_result[0].keys())
                writer.writeheader()
                writer.writerows(export_result)
                
                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="content_export.csv"'
            else:  # xml
                response = HttpResponse(export_result, content_type='application/xml')
                response['Content-Disposition'] = 'attachment; filename="content_export.xml"'
            
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to export content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def import_content(self, request):
        """Import content from various formats."""
        serializer = ContentImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        import_data = serializer.validated_data
        
        try:
            import_result = AdvancedContentService.import_content(
                import_data, request.user
            )
            return Response(import_result)
        except Exception as e:
            return Response(
                {'error': f'Failed to import content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on content."""
        operation = request.data.get('operation')
        content_ids = request.data.get('content_ids', [])
        operation_data = request.data.get('operation_data', {})
        
        if not operation or not content_ids:
            return Response(
                {'error': 'operation and content_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = AdvancedContentService.bulk_operations(
                operation, content_ids, operation_data, request.user
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to perform bulk operation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def content_analytics(self, request):
        """Get comprehensive content analytics."""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        content_type = request.query_params.get('content_type')
        
        try:
            analytics = ContentAnalyticsService.get_comprehensive_analytics(
                date_from, date_to, content_type
            )
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def schedule_content_action(self, request):
        """Schedule content actions (publish, unpublish, etc.)."""
        content_id = request.data.get('content_id')
        action_type = request.data.get('action_type')
        scheduled_time = request.data.get('scheduled_time')
        action_data = request.data.get('action_data', {})
        
        if not all([content_id, action_type, scheduled_time]):
            return Response(
                {'error': 'content_id, action_type, and scheduled_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            schedule = AdvancedContentService.schedule_content_action(
                content_id, action_type, scheduled_time, action_data, request.user
            )
            serializer = ContentScheduleSerializer(schedule)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to schedule content action: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )