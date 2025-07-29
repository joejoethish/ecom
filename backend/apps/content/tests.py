"""
Tests for content management app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.products.models import Category
from .models import Banner, Carousel, CarouselItem, ContentPage, Announcement
from .services import (
    BannerService, CarouselService, ContentPageService,
    AnnouncementService, ContentManagementService
)

User = get_user_model()

class BannerModelTest(TestCase):
    """
    Test cases for Banner model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category')
    
    def test_create_banner(self):
        """Test creating a banner."""
        banner = Banner.objects.create(
            title='Test Banner',
            subtitle='Test Subtitle',
            description='Test Description',
            banner_type='hero',
            position='top',
            is_active=True,
            sort_order=1
        )
        
        self.assertEqual(banner.title, 'Test Banner')
        self.assertEqual(banner.banner_type, 'hero')
        self.assertEqual(banner.position, 'top')
        self.assertTrue(banner.is_active)
        self.assertEqual(banner.sort_order, 1)
    
    def test_banner_with_scheduling(self):
        """Test banner with start and end dates."""
        now = timezone.now()
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        
        banner = Banner.objects.create(
            title='Scheduled Banner',
            banner_type='promotional',
            position='middle',
            is_active=True,
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertEqual(banner.start_date, start_date)
        self.assertEqual(banner.end_date, end_date)
        self.assertTrue(banner.is_currently_active)
    
    def test_banner_click_through_rate(self):
        """Test banner click-through rate calculation."""
        banner = Banner.objects.create(
            title='CTR Banner',
            banner_type='hero',
            position='top',
            view_count=1000,
            click_count=50
        )
        
        self.assertEqual(banner.click_through_rate, 0.05)  # 5%
    
    def test_banner_soft_delete(self):
        """Test banner soft delete functionality."""
        banner = Banner.objects.create(
            title='Delete Test Banner',
            banner_type='hero',
            position='top'
        )
        
        # Soft delete
        banner.is_deleted = True
        banner.save()
        
        # Should still exist in database
        self.assertTrue(Banner.objects.filter(id=banner.id).exists())
        # But not in default queryset
        self.assertFalse(Banner.objects.filter(id=banner.id, is_deleted=False).exists())

class CarouselModelTest(TestCase):
    """
    Test cases for Carousel model.
    """
    
    def test_create_carousel(self):
        """Test creating a carousel."""
        carousel = Carousel.objects.create(
            name='Test Carousel',
            description='Test Description',
            carousel_type='hero',
            is_active=True,
            auto_play=True,
            auto_play_speed=3000
        )
        
        self.assertEqual(carousel.name, 'Test Carousel')
        self.assertEqual(carousel.carousel_type, 'hero')
        self.assertTrue(carousel.is_active)
        self.assertTrue(carousel.auto_play)
        self.assertEqual(carousel.auto_play_speed, 3000)
    
    def test_active_items_count(self):
        """Test active items count property."""
        carousel = Carousel.objects.create(
            name='Items Count Test',
            carousel_type='hero'
        )
        
        # Create carousel items
        CarouselItem.objects.create(
            carousel=carousel,
            title='Item 1',
            is_active=True
        )
        CarouselItem.objects.create(
            carousel=carousel,
            title='Item 2',
            is_active=True
        )
        CarouselItem.objects.create(
            carousel=carousel,
            title='Item 3',
            is_active=False
        )
        
        self.assertEqual(carousel.active_items_count, 2)

class CarouselItemModelTest(TestCase):
    """
    Test cases for CarouselItem model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.carousel = Carousel.objects.create(
            name='Test Carousel',
            carousel_type='hero'
        )
    
    def test_create_carousel_item(self):
        """Test creating a carousel item."""
        item = CarouselItem.objects.create(
            carousel=self.carousel,
            title='Test Item',
            subtitle='Test Subtitle',
            description='Test Description',
            is_active=True,
            sort_order=1
        )
        
        self.assertEqual(item.carousel, self.carousel)
        self.assertEqual(item.title, 'Test Item')
        self.assertTrue(item.is_active)
        self.assertEqual(item.sort_order, 1)
    
    def test_carousel_item_click_through_rate(self):
        """Test carousel item click-through rate calculation."""
        item = CarouselItem.objects.create(
            carousel=self.carousel,
            title='CTR Item',
            view_count=500,
            click_count=25
        )
        
        self.assertEqual(item.click_through_rate, 0.05)  # 5%

class ContentPageModelTest(TestCase):
    """
    Test cases for ContentPage model.
    """
    
    def test_create_content_page(self):
        """Test creating a content page."""
        page = ContentPage.objects.create(
            title='Test Page',
            slug='test-page',
            page_type='static',
            content='<h1>Test Content</h1>',
            is_active=True
        )
        
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.slug, 'test-page')
        self.assertEqual(page.page_type, 'static')
        self.assertTrue(page.is_active)
    
    def test_content_page_unique_slug(self):
        """Test that content page slugs are unique."""
        ContentPage.objects.create(
            title='Page 1',
            slug='unique-slug',
            page_type='static'
        )
        
        # Creating another page with same slug should raise error
        with self.assertRaises(Exception):
            ContentPage.objects.create(
                title='Page 2',
                slug='unique-slug',
                page_type='static'
            )

class AnnouncementModelTest(TestCase):
    """
    Test cases for Announcement model.
    """
    
    def test_create_announcement(self):
        """Test creating an announcement."""
        announcement = Announcement.objects.create(
            title='Test Announcement',
            message='This is a test announcement',
            announcement_type='info',
            is_active=True,
            is_dismissible=True
        )
        
        self.assertEqual(announcement.title, 'Test Announcement')
        self.assertEqual(announcement.announcement_type, 'info')
        self.assertTrue(announcement.is_active)
        self.assertTrue(announcement.is_dismissible)
    
    def test_announcement_with_scheduling(self):
        """Test announcement with start and end dates."""
        now = timezone.now()
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        
        announcement = Announcement.objects.create(
            title='Scheduled Announcement',
            message='This is scheduled',
            announcement_type='warning',
            is_active=True,
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertTrue(announcement.is_currently_active)

class BannerServiceTest(TestCase):
    """
    Test cases for BannerService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category')
        self.banner = Banner.objects.create(
            title='Test Banner',
            banner_type='hero',
            position='top',
            is_active=True
        )
    
    def test_get_active_banners(self):
        """Test getting active banners."""
        banners = BannerService.get_active_banners(
            banner_type='hero',
            position='top'
        )
        
        self.assertIn(self.banner, banners)
    
    def test_track_banner_view(self):
        """Test tracking banner view."""
        initial_count = self.banner.view_count
        
        BannerService.track_banner_view(self.banner.id)
        self.banner.refresh_from_db()
        
        self.assertEqual(self.banner.view_count, initial_count + 1)
    
    def test_track_banner_click(self):
        """Test tracking banner click."""
        initial_count = self.banner.click_count
        
        BannerService.track_banner_click(self.banner.id)
        self.banner.refresh_from_db()
        
        self.assertEqual(self.banner.click_count, initial_count + 1)
    
    @patch('apps.content.services.Banner.objects')
    def test_get_banner_analytics(self, mock_banners):
        """Test getting banner analytics."""
        mock_banners.filter.return_value.values.return_value = [
            {
                'id': 1,
                'title': 'Test Banner',
                'banner_type': 'hero',
                'position': 'top',
                'view_count': 1000,
                'click_count': 50,
                'is_active': True
            }
        ]
        
        analytics = BannerService.get_banner_analytics()
        
        self.assertIsInstance(analytics, list)
        if analytics:
            self.assertIn('ctr', analytics[0])

class CarouselServiceTest(TestCase):
    """
    Test cases for CarouselService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.carousel = Carousel.objects.create(
            name='Test Carousel',
            carousel_type='hero',
            is_active=True
        )
        self.item = CarouselItem.objects.create(
            carousel=self.carousel,
            title='Test Item',
            is_active=True
        )
    
    def test_get_carousel_with_items(self):
        """Test getting carousel with items."""
        result = CarouselService.get_carousel_with_items(self.carousel.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], self.carousel.id)
        self.assertIn('items', result)
    
    def test_track_carousel_item_view(self):
        """Test tracking carousel item view."""
        initial_count = self.item.view_count
        
        CarouselService.track_carousel_item_view(self.item.id)
        self.item.refresh_from_db()
        
        self.assertEqual(self.item.view_count, initial_count + 1)
    
    def test_track_carousel_item_click(self):
        """Test tracking carousel item click."""
        initial_count = self.item.click_count
        
        CarouselService.track_carousel_item_click(self.item.id)
        self.item.refresh_from_db()
        
        self.assertEqual(self.item.click_count, initial_count + 1)

class ContentManagementServiceTest(TestCase):
    """
    Test cases for ContentManagementService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.banner = Banner.objects.create(
            title='Homepage Banner',
            banner_type='hero',
            position='top',
            is_active=True
        )
        self.carousel = Carousel.objects.create(
            name='Homepage Carousel',
            carousel_type='hero',
            is_active=True
        )
        self.announcement = Announcement.objects.create(
            title='Homepage Announcement',
            message='Welcome!',
            announcement_type='info',
            is_active=True
        )
    
    @patch('apps.content.services.BannerService.get_active_banners')
    @patch('apps.content.services.CarouselService.get_carousel_with_items')
    @patch('apps.content.services.AnnouncementService.get_active_announcements')
    def test_get_homepage_content(self, mock_announcements, mock_carousel, mock_banners):
        """Test getting homepage content."""
        mock_banners.return_value = [self.banner]
        mock_carousel.return_value = {'id': self.carousel.id, 'items': []}
        mock_announcements.return_value = [self.announcement]
        
        content = ContentManagementService.get_homepage_content()
        
        self.assertIn('hero_banners', content)
        self.assertIn('hero_carousel', content)
        self.assertIn('announcements', content)

class ContentAPITest(APITestCase):
    """
    Test cases for Content API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )
        self.banner = Banner.objects.create(
            title='Test Banner',
            banner_type='hero',
            position='top',
            is_active=True
        )
    
    def test_banner_list_requires_admin(self):
        """Test that banner list requires admin access."""
        url = reverse('content:banners-list')
        
        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test regular user access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test admin access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_banner(self):
        """Test creating a banner."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-list')
        
        data = {
            'title': 'New Banner',
            'subtitle': 'New Subtitle',
            'banner_type': 'promotional',
            'position': 'middle',
            'is_active': True,
            'sort_order': 1
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Banner')
    
    def test_update_banner(self):
        """Test updating a banner."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-detail', args=[self.banner.id])
        
        data = {
            'title': 'Updated Banner',
            'banner_type': 'hero',
            'position': 'top',
            'is_active': False
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Banner')
        self.assertFalse(response.data['is_active'])
    
    def test_delete_banner(self):
        """Test deleting a banner (soft delete)."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-detail', args=[self.banner.id])
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        self.banner.refresh_from_db()
        self.assertTrue(self.banner.is_deleted)
    
    def test_banner_analytics(self):
        """Test banner analytics endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-analytics')
        
        with patch('apps.content.services.BannerService.get_banner_analytics') as mock_analytics:
            mock_analytics.return_value = [
                {
                    'id': self.banner.id,
                    'title': self.banner.title,
                    'views': 1000,
                    'clicks': 50,
                    'ctr': 0.05
                }
            ]
            
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(response.data, list)
    
    def test_track_banner_view(self):
        """Test tracking banner view."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-track')
        
        data = {
            'banner_id': self.banner.id,
            'action': 'view'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify view count increased
        self.banner.refresh_from_db()
        self.assertEqual(self.banner.view_count, 1)
    
    def test_bulk_update_banner_status(self):
        """Test bulk updating banner status."""
        # Create additional banner
        banner2 = Banner.objects.create(
            title='Banner 2',
            banner_type='promotional',
            position='bottom',
            is_active=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:banners-bulk-update-status')
        
        data = {
            'banner_ids': [self.banner.id, banner2.id],
            'is_active': False
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)
        
        # Verify banners were updated
        self.banner.refresh_from_db()
        banner2.refresh_from_db()
        self.assertFalse(self.banner.is_active)
        self.assertFalse(banner2.is_active)

class CarouselAPITest(APITestCase):
    """
    Test cases for Carousel API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.carousel = Carousel.objects.create(
            name='Test Carousel',
            carousel_type='hero',
            is_active=True
        )
    
    def test_create_carousel(self):
        """Test creating a carousel."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:carousels-list')
        
        data = {
            'name': 'New Carousel',
            'description': 'New Description',
            'carousel_type': 'promotional',
            'is_active': True,
            'auto_play': True,
            'auto_play_speed': 5000
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Carousel')
    
    def test_get_carousel_with_items(self):
        """Test getting carousel with items."""
        # Create carousel item
        CarouselItem.objects.create(
            carousel=self.carousel,
            title='Test Item',
            is_active=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:carousels-with-items', args=[self.carousel.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.carousel.id)
        self.assertIn('items', response.data)

class ContentPageAPITest(APITestCase):
    """
    Test cases for ContentPage API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.page = ContentPage.objects.create(
            title='Test Page',
            slug='test-page',
            page_type='static',
            content='<h1>Test Content</h1>',
            is_active=True
        )
    
    def test_create_content_page(self):
        """Test creating a content page."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:content-pages-list')
        
        data = {
            'title': 'New Page',
            'slug': 'new-page',
            'page_type': 'static',
            'content': '<h1>New Content</h1>',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Page')
    
    def test_get_pages_by_type(self):
        """Test getting pages by type."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:content-pages-by-type')
        
        response = self.client.get(url, {'page_type': 'static'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

class AnnouncementAPITest(APITestCase):
    """
    Test cases for Announcement API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.announcement = Announcement.objects.create(
            title='Test Announcement',
            message='Test Message',
            announcement_type='info',
            is_active=True
        )
    
    def test_create_announcement(self):
        """Test creating an announcement."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:announcements-list')
        
        data = {
            'title': 'New Announcement',
            'message': 'New Message',
            'announcement_type': 'warning',
            'is_active': True,
            'is_dismissible': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Announcement')
    
    def test_get_active_announcements(self):
        """Test getting active announcements."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('content:announcements-active-announcements')
        
        response = self.client.get(url, {'user_type': 'all'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)