"""
Content management services for banners, carousels, and promotional content.
"""
from django.utils import timezone
from django.db.models import Q
from typing import List, Dict, Optional
from .models import Banner, Carousel, CarouselItem, ContentPage, Announcement

# Import advanced services
try:
    from .advanced_services import (
        AdvancedContentService, ContentWorkflowService, ContentAssetService,
        PageBuilderService, ContentAnalyticsService
    )
except ImportError:
    # Advanced services not available yet
    pass


class BannerService:
    """
    Service for managing promotional banners.
    """

    @staticmethod
    def get_active_banners(banner_type: str = None, position: str = None, 
                          page_path: str = None, category_id: int = None) -> List[Banner]:
        """
        Get active banners based on criteria.
        """
        now = timezone.now()
        
        queryset = Banner.objects.filter(
            is_active=True,
            is_deleted=False,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )

        if banner_type:
            queryset = queryset.filter(banner_type=banner_type)
        
        if position:
            queryset = queryset.filter(position=position)
        
        if page_path:
            queryset = queryset.filter(
                Q(target_pages__contains=[page_path]) | 
                Q(target_pages=[])  # Empty list means show on all pages
            )
        
        if category_id:
            queryset = queryset.filter(
                Q(target_categories=category_id) |
                Q(target_categories__isnull=True)
            )

        return queryset.order_by('sort_order', '-created_at')

    @staticmethod
    def track_banner_view(banner_id: int):
        """
        Track banner view for analytics.
        """
        try:
            banner = Banner.objects.get(id=banner_id, is_deleted=False)
            banner.increment_views()
        except Banner.DoesNotExist:
            pass

    @staticmethod
    def track_banner_click(banner_id: int):
        """
        Track banner click for analytics.
        """
        try:
            banner = Banner.objects.get(id=banner_id, is_deleted=False)
            banner.increment_clicks()
        except Banner.DoesNotExist:
            pass

    @staticmethod
    def get_banner_analytics(date_from=None, date_to=None) -> Dict:
        """
        Get banner performance analytics.
        """
        queryset = Banner.objects.filter(is_deleted=False)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        banners = queryset.order_by('-view_count')
        
        analytics = []
        for banner in banners:
            analytics.append({
                'id': banner.id,
                'title': banner.title,
                'banner_type': banner.banner_type,
                'position': banner.position,
                'views': banner.view_count,
                'clicks': banner.click_count,
                'ctr': banner.click_through_rate,
                'is_active': banner.is_currently_active
            })

        return {
            'banners': analytics,
            'summary': {
                'total_banners': queryset.count(),
                'active_banners': queryset.filter(is_active=True).count(),
                'total_views': sum(b.view_count for b in banners),
                'total_clicks': sum(b.click_count for b in banners),
            }
        }

    @staticmethod
    def schedule_banner_activation():
        """
        Activate/deactivate banners based on their schedule.
        This should be called periodically (e.g., via Celery).
        """
        now = timezone.now()
        
        # Activate banners that should start now
        Banner.objects.filter(
            is_active=False,
            start_date__lte=now,
            is_deleted=False
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).update(is_active=True)
        
        # Deactivate expired banners
        Banner.objects.filter(
            is_active=True,
            end_date__lt=now,
            is_deleted=False
        ).update(is_active=False)


class CarouselService:
    """
    Service for managing carousels and carousel items.
    """

    @staticmethod
    def get_active_carousel(carousel_type: str, page_path: str = None) -> Optional[Carousel]:
        """
        Get active carousel for a specific type and page.
        """
        queryset = Carousel.objects.filter(
            carousel_type=carousel_type,
            is_active=True,
            is_deleted=False
        )

        if page_path:
            queryset = queryset.filter(
                Q(target_pages__contains=[page_path]) | 
                Q(target_pages=[])  # Empty list means show on all pages
            )

        return queryset.first()

    @staticmethod
    def get_carousel_with_items(carousel_id: int) -> Optional[Dict]:
        """
        Get carousel with its active items.
        """
        try:
            carousel = Carousel.objects.get(
                id=carousel_id,
                is_active=True,
                is_deleted=False
            )
            
            items = CarouselItem.objects.filter(
                carousel=carousel,
                is_active=True,
                is_deleted=False
            ).order_by('sort_order')

            return {
                'carousel': carousel,
                'items': items,
                'config': {
                    'auto_play': carousel.auto_play,
                    'auto_play_speed': carousel.auto_play_speed,
                    'show_indicators': carousel.show_indicators,
                    'show_navigation': carousel.show_navigation,
                    'infinite_loop': carousel.infinite_loop,
                    'items_per_view': carousel.items_per_view,
                    'items_per_view_mobile': carousel.items_per_view_mobile,
                }
            }
        except Carousel.DoesNotExist:
            return None

    @staticmethod
    def track_carousel_item_view(item_id: int):
        """
        Track carousel item view for analytics.
        """
        try:
            item = CarouselItem.objects.get(id=item_id, is_deleted=False)
            item.increment_views()
        except CarouselItem.DoesNotExist:
            pass

    @staticmethod
    def track_carousel_item_click(item_id: int):
        """
        Track carousel item click for analytics.
        """
        try:
            item = CarouselItem.objects.get(id=item_id, is_deleted=False)
            item.increment_clicks()
        except CarouselItem.DoesNotExist:
            pass

    @staticmethod
    def get_carousel_analytics(carousel_id: int = None) -> Dict:
        """
        Get carousel performance analytics.
        """
        if carousel_id:
            items = CarouselItem.objects.filter(
                carousel_id=carousel_id,
                is_deleted=False
            ).order_by('-view_count')
        else:
            items = CarouselItem.objects.filter(
                is_deleted=False
            ).order_by('-view_count')

        analytics = []
        for item in items:
            analytics.append({
                'id': item.id,
                'title': item.title,
                'carousel_name': item.carousel.name,
                'carousel_type': item.carousel.carousel_type,
                'views': item.view_count,
                'clicks': item.click_count,
                'ctr': item.click_through_rate,
                'is_active': item.is_active
            })

        return {
            'items': analytics,
            'summary': {
                'total_items': len(analytics),
                'total_views': sum(item['views'] for item in analytics),
                'total_clicks': sum(item['clicks'] for item in analytics),
            }
        }


class ContentPageService:
    """
    Service for managing static content pages.
    """

    @staticmethod
    def get_active_pages(show_in_footer: bool = None, show_in_header: bool = None) -> List[ContentPage]:
        """
        Get active content pages.
        """
        queryset = ContentPage.objects.filter(
            is_active=True,
            is_deleted=False
        )

        if show_in_footer is not None:
            queryset = queryset.filter(show_in_footer=show_in_footer)
        
        if show_in_header is not None:
            queryset = queryset.filter(show_in_header=show_in_header)

        return queryset.order_by('sort_order', 'title')

    @staticmethod
    def get_page_by_slug(slug: str) -> Optional[ContentPage]:
        """
        Get content page by slug.
        """
        try:
            return ContentPage.objects.get(
                slug=slug,
                is_active=True,
                is_deleted=False
            )
        except ContentPage.DoesNotExist:
            return None

    @staticmethod
    def get_pages_by_type(page_type: str) -> List[ContentPage]:
        """
        Get content pages by type.
        """
        return ContentPage.objects.filter(
            page_type=page_type,
            is_active=True,
            is_deleted=False
        ).order_by('sort_order', 'title')


class AnnouncementService:
    """
    Service for managing site-wide announcements.
    """

    @staticmethod
    def get_active_announcements(user_type: str = 'all', page_path: str = None) -> List[Announcement]:
        """
        Get active announcements for specific user type and page.
        """
        now = timezone.now()
        
        queryset = Announcement.objects.filter(
            is_active=True,
            is_deleted=False,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )

        # Filter by user type
        queryset = queryset.filter(
            Q(target_user_types__contains=[user_type]) |
            Q(target_user_types__contains=['all']) |
            Q(target_user_types=[])  # Empty list means show to all
        )

        # Filter by page path
        if page_path:
            queryset = queryset.filter(
                Q(target_pages__contains=[page_path]) |
                Q(target_pages=[])  # Empty list means show on all pages
            )

        return queryset.order_by('-created_at')

    @staticmethod
    def schedule_announcement_activation():
        """
        Activate/deactivate announcements based on their schedule.
        This should be called periodically (e.g., via Celery).
        """
        now = timezone.now()
        
        # Activate announcements that should start now
        Announcement.objects.filter(
            is_active=False,
            start_date__lte=now,
            is_deleted=False
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).update(is_active=True)
        
        # Deactivate expired announcements
        Announcement.objects.filter(
            is_active=True,
            end_date__lt=now,
            is_deleted=False
        ).update(is_active=False)


class ContentManagementService:
    """
    Unified service for content management operations.
    """

    @staticmethod
    def get_homepage_content(user_type: str = 'all') -> Dict:
        """
        Get all content for homepage including banners, carousels, and announcements.
        """
        # Get hero banners
        hero_banners = BannerService.get_active_banners(
            banner_type='hero',
            page_path='/'
        )

        # Get hero carousel
        hero_carousel = CarouselService.get_active_carousel(
            carousel_type='hero',
            page_path='/'
        )
        hero_carousel_data = None
        if hero_carousel:
            hero_carousel_data = CarouselService.get_carousel_with_items(hero_carousel.id)

        # Get promotional banners
        promotional_banners = BannerService.get_active_banners(
            banner_type='promotional',
            page_path='/'
        )

        # Get announcements
        announcements = AnnouncementService.get_active_announcements(
            user_type=user_type,
            page_path='/'
        )

        return {
            'hero_banners': hero_banners,
            'hero_carousel': hero_carousel_data,
            'promotional_banners': promotional_banners,
            'announcements': announcements
        }

    @staticmethod
    def get_category_content(category_id: int, user_type: str = 'all') -> Dict:
        """
        Get content specific to a category page.
        """
        page_path = f'/category/{category_id}'
        
        # Get category banners
        category_banners = BannerService.get_active_banners(
            banner_type='category',
            page_path=page_path,
            category_id=category_id
        )

        # Get category carousel
        category_carousel = CarouselService.get_active_carousel(
            carousel_type='category',
            page_path=page_path
        )
        category_carousel_data = None
        if category_carousel:
            category_carousel_data = CarouselService.get_carousel_with_items(category_carousel.id)

        # Get announcements
        announcements = AnnouncementService.get_active_announcements(
            user_type=user_type,
            page_path=page_path
        )

        return {
            'category_banners': category_banners,
            'category_carousel': category_carousel_data,
            'announcements': announcements
        }

    @staticmethod
    def get_content_performance_summary() -> Dict:
        """
        Get overall content performance summary.
        """
        banner_analytics = BannerService.get_banner_analytics()
        carousel_analytics = CarouselService.get_carousel_analytics()

        return {
            'banners': banner_analytics['summary'],
            'carousels': carousel_analytics['summary'],
            'total_content_views': (
                banner_analytics['summary']['total_views'] +
                carousel_analytics['summary']['total_views']
            ),
            'total_content_clicks': (
                banner_analytics['summary']['total_clicks'] +
                carousel_analytics['summary']['total_clicks']
            )
        }