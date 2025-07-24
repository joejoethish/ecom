"""
Content management API views for admin panel.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.permissions import IsAdminUser
from .models import Banner, Carousel, CarouselItem, ContentPage, Announcement
from .serializers import (
    BannerSerializer, BannerCreateUpdateSerializer,
    CarouselSerializer, CarouselCreateUpdateSerializer,
    CarouselItemSerializer, CarouselItemCreateUpdateSerializer,
    ContentPageSerializer, AnnouncementSerializer,
    BannerAnalyticsSerializer, CarouselAnalyticsSerializer,
    ContentAnalyticsSerializer, HomepageContentSerializer,
    CategoryContentSerializer, BannerTrackingSerializer,
    CarouselTrackingSerializer, ContentFilterSerializer
)
from .services import (
    BannerService, CarouselService, ContentPageService,
    AnnouncementService, ContentManagementService
)


class BannerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for banner management.
    """
    queryset = Banner.objects.filter(is_deleted=False).order_by('sort_order', '-created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return BannerCreateUpdateSerializer
        return BannerSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        banner_type = self.request.query_params.get('banner_type')
        position = self.request.query_params.get('position')
        is_active = self.request.query_params.get('is_active')
        
        if banner_type:
            queryset = queryset.filter(banner_type=banner_type)
        if position:
            queryset = queryset.filter(position=position)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete banner."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'])
    def active_banners(self, request):
        """
        Get active banners based on criteria.
        """
        filter_serializer = ContentFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filters = filter_serializer.validated_data
        
        try:
            banners = BannerService.get_active_banners(
                banner_type=filters.get('banner_type'),
                position=filters.get('position'),
                page_path=filters.get('page_path'),
                category_id=filters.get('category_id')
            )
            
            serializer = BannerSerializer(banners, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get active banners: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get banner performance analytics.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))

        try:
            analytics = BannerService.get_banner_analytics(date_from, date_to)
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get banner analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def track(self, request):
        """
        Track banner views and clicks.
        """
        serializer = BannerTrackingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        banner_id = data['banner_id']
        action = data['action']

        try:
            if action == 'view':
                BannerService.track_banner_view(banner_id)
            elif action == 'click':
                BannerService.track_banner_click(banner_id)
            
            return Response({'message': f'Banner {action} tracked successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to track banner {action}: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a banner.
        """
        banner = self.get_object()
        
        # Create a copy
        banner.pk = None
        banner.title = f"{banner.title} (Copy)"
        banner.is_active = False
        banner.save()
        
        serializer = BannerSerializer(banner)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        Bulk update banner status.
        """
        banner_ids = request.data.get('banner_ids', [])
        is_active = request.data.get('is_active', True)
        
        if not banner_ids:
            return Response(
                {'error': 'banner_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_count = Banner.objects.filter(
                id__in=banner_ids,
                is_deleted=False
            ).update(is_active=is_active)
            
            return Response({
                'message': f'Updated {updated_count} banners',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to bulk update banners: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarouselViewSet(viewsets.ModelViewSet):
    """
    ViewSet for carousel management.
    """
    queryset = Carousel.objects.filter(is_deleted=False).order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return CarouselCreateUpdateSerializer
        return CarouselSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        carousel_type = self.request.query_params.get('carousel_type')
        is_active = self.request.query_params.get('is_active')
        
        if carousel_type:
            queryset = queryset.filter(carousel_type=carousel_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete carousel."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def with_items(self, request, pk=None):
        """
        Get carousel with its items.
        """
        carousel = self.get_object()
        
        try:
            carousel_data = CarouselService.get_carousel_with_items(carousel.id)
            if carousel_data:
                return Response(carousel_data)
            else:
                return Response(
                    {'error': 'Carousel not found or inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to get carousel with items: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get carousel performance analytics.
        """
        carousel_id = request.query_params.get('carousel_id')
        
        try:
            analytics = CarouselService.get_carousel_analytics(carousel_id)
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get carousel analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarouselItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for carousel item management.
    """
    queryset = CarouselItem.objects.filter(is_deleted=False).order_by('sort_order', 'created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return CarouselItemCreateUpdateSerializer
        return CarouselItemSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        carousel_id = self.request.query_params.get('carousel_id')
        is_active = self.request.query_params.get('is_active')
        
        if carousel_id:
            queryset = queryset.filter(carousel_id=carousel_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete carousel item."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['post'])
    def track(self, request):
        """
        Track carousel item views and clicks.
        """
        serializer = CarouselTrackingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        item_id = data['item_id']
        action = data['action']

        try:
            if action == 'view':
                CarouselService.track_carousel_item_view(item_id)
            elif action == 'click':
                CarouselService.track_carousel_item_click(item_id)
            
            return Response({'message': f'Carousel item {action} tracked successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to track carousel item {action}: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a carousel item.
        """
        item = self.get_object()
        
        # Create a copy
        item.pk = None
        item.title = f"{item.title} (Copy)"
        item.is_active = False
        item.save()
        
        serializer = CarouselItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder carousel items.
        """
        item_orders = request.data.get('item_orders', [])
        
        if not item_orders:
            return Response(
                {'error': 'item_orders is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            for item_order in item_orders:
                item_id = item_order.get('id')
                sort_order = item_order.get('sort_order')
                
                if item_id and sort_order is not None:
                    CarouselItem.objects.filter(
                        id=item_id,
                        is_deleted=False
                    ).update(sort_order=sort_order)
            
            return Response({'message': 'Carousel items reordered successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to reorder carousel items: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentPageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content page management.
    """
    queryset = ContentPage.objects.filter(is_deleted=False).order_by('sort_order', 'title')
    serializer_class = ContentPageSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        page_type = self.request.query_params.get('page_type')
        is_active = self.request.query_params.get('is_active')
        show_in_footer = self.request.query_params.get('show_in_footer')
        show_in_header = self.request.query_params.get('show_in_header')
        
        if page_type:
            queryset = queryset.filter(page_type=page_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if show_in_footer is not None:
            queryset = queryset.filter(show_in_footer=show_in_footer.lower() == 'true')
        if show_in_header is not None:
            queryset = queryset.filter(show_in_header=show_in_header.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete content page."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get content pages by type.
        """
        page_type = request.query_params.get('page_type')
        if not page_type:
            return Response(
                {'error': 'page_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pages = ContentPageService.get_pages_by_type(page_type)
            serializer = ContentPageSerializer(pages, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get pages by type: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for announcement management.
    """
    queryset = Announcement.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        announcement_type = self.request.query_params.get('announcement_type')
        is_active = self.request.query_params.get('is_active')
        
        if announcement_type:
            queryset = queryset.filter(announcement_type=announcement_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete announcement."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['get'])
    def active_announcements(self, request):
        """
        Get active announcements for specific user type and page.
        """
        user_type = request.query_params.get('user_type', 'all')
        page_path = request.query_params.get('page_path')

        try:
            announcements = AnnouncementService.get_active_announcements(user_type, page_path)
            serializer = AnnouncementSerializer(announcements, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get active announcements: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentManagementViewSet(viewsets.ViewSet):
    """
    ViewSet for unified content management operations.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def homepage_content(self, request):
        """
        Get all content for homepage.
        """
        user_type = request.query_params.get('user_type', 'all')

        try:
            content = ContentManagementService.get_homepage_content(user_type)
            serializer = HomepageContentSerializer(content)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get homepage content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def category_content(self, request):
        """
        Get content for category page.
        """
        category_id = request.query_params.get('category_id')
        user_type = request.query_params.get('user_type', 'all')
        
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            content = ContentManagementService.get_category_content(
                int(category_id), user_type
            )
            serializer = CategoryContentSerializer(content)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get category content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """
        Get overall content performance summary.
        """
        try:
            summary = ContentManagementService.get_content_performance_summary()
            serializer = ContentAnalyticsSerializer(summary)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get content performance summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def schedule_activation(self, request):
        """
        Manually trigger scheduled activation of banners and announcements.
        """
        try:
            BannerService.schedule_banner_activation()
            AnnouncementService.schedule_announcement_activation()
            
            return Response({
                'message': 'Content activation scheduling completed successfully'
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to schedule content activation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )      
          {'error': f'Failed to get category content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def content_analytics(self, request):
        """
        Get comprehensive content analytics.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        try:
            analytics = ContentManagementService.get_content_analytics(date_from, date_to)
            serializer = ContentAnalyticsSerializer(analytics)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get content analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_content_update(self, request):
        """
        Bulk update content status.
        """
        content_type = request.data.get('content_type')  # 'banner', 'carousel', 'announcement'
        content_ids = request.data.get('content_ids', [])
        updates = request.data.get('updates', {})
        
        if not content_type or not content_ids:
            return Response(
                {'error': 'content_type and content_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_count = 0
            if content_type == 'banner':
                updated_count = Banner.objects.filter(
                    id__in=content_ids,
                    is_deleted=False
                ).update(**updates)
            elif content_type == 'carousel':
                updated_count = Carousel.objects.filter(
                    id__in=content_ids,
                    is_deleted=False
                ).update(**updates)
            elif content_type == 'announcement':
                updated_count = Announcement.objects.filter(
                    id__in=content_ids,
                    is_deleted=False
                ).update(**updates)
            else:
                return Response(
                    {'error': 'Invalid content_type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': f'Updated {updated_count} {content_type}s',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to bulk update content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def schedule_content(self, request):
        """
        Schedule content activation/deactivation.
        """
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not all([content_type, content_id, start_date]):
            return Response(
                {'error': 'content_type, content_id, and start_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # This would typically use a task scheduler like Celery
            # For now, we'll just update the dates
            updates = {'start_date': start_date}
            if end_date:
                updates['end_date'] = end_date
            
            if content_type == 'banner':
                Banner.objects.filter(id=content_id, is_deleted=False).update(**updates)
            elif content_type == 'announcement':
                Announcement.objects.filter(id=content_id, is_deleted=False).update(**updates)
            else:
                return Response(
                    {'error': 'Invalid content_type for scheduling'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({'message': f'{content_type.title()} scheduled successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to schedule content: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )