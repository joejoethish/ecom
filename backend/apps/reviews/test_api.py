"""
API tests for the reviews app.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from .models import Review, ReviewHelpfulness, ReviewReport

User = get_user_model()


class ReviewAPITest(APITestCase):
    """
    Test cases for Review API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            user_type='admin'
        )
        
        # Create product
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        
        # Create order for verified purchase
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD001',
            total_amount=99.99,
            status='delivered'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=99.99,
            total_price=99.99
        )
    
    def test_create_review_success(self):
        """Test successful review creation."""
        self.client.force_authenticate(user=self.customer)
        
        data = {
            'product': str(self.product.id),
            'rating': 5,
            'title': 'Great product!',
            'comment': 'I love this product.',
            'pros': 'Good quality',
            'cons': 'A bit expensive'
        }
        
        url = reverse('reviews:review-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        
        review = Review.objects.first()
        self.assertEqual(review.user, self.customer)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_verified_purchase)
        self.assertEqual(review.status, 'pending')
    
    def test_create_review_without_purchase(self):
        """Test review creation without purchase should fail."""
        # Create another user without purchase
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)
        
        data = {
            'product': str(self.product.id),
            'rating': 5,
            'title': 'Great product!',
            'comment': 'I love this product.'
        }
        
        url = reverse('reviews:review-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You can only review products you have purchased', str(response.data))
    
    def test_create_duplicate_review(self):
        """Test that users cannot create duplicate reviews."""
        # Create first review
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='First review',
            comment='Great product'
        )
        
        self.client.force_authenticate(user=self.customer)
        
        data = {
            'product': str(self.product.id),
            'rating': 4,
            'title': 'Second review',
            'comment': 'Another review'
        }
        
        url = reverse('reviews:review-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You have already reviewed this product', str(response.data))
    
    def test_list_reviews(self):
        """Test listing reviews."""
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='pending'
        )
        
        url = reverse('reviews:review-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only approved reviews should be visible to unauthenticated users
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_reviews_as_admin(self):
        """Test listing reviews as admin (can see all statuses)."""
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('reviews:review-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin should see all reviews
        self.assertEqual(len(response.data['results']), 2)
    
    def test_update_review(self):
        """Test updating a review."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.customer)
        
        data = {
            'rating': 4,
            'title': 'Updated title',
            'comment': 'Updated comment'
        }
        
        url = reverse('reviews:review-detail', kwargs={'pk': review.id})
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.title, 'Updated title')
        self.assertEqual(review.comment, 'Updated comment')
    
    def test_update_approved_review_fails(self):
        """Test that approved reviews cannot be updated."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        self.client.force_authenticate(user=self.customer)
        
        data = {
            'rating': 4,
            'title': 'Updated title'
        }
        
        url = reverse('reviews:review-detail', kwargs={'pk': review.id})
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot update an approved review', str(response.data))
    
    def test_vote_helpful(self):
        """Test voting on review helpfulness."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        # Create another user to vote
        voter = User.objects.create_user(
            username='voter',
            email='voter@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=voter)
        
        url = reverse('reviews:review-vote-helpful', kwargs={'pk': review.id})
        response = self.client.post(url, {'vote': 'helpful'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        review.refresh_from_db()
        self.assertEqual(review.helpful_count, 1)
        self.assertEqual(review.not_helpful_count, 0)
    
    def test_vote_own_review_fails(self):
        """Test that users cannot vote on their own reviews."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        self.client.force_authenticate(user=self.customer)
        
        url = reverse('reviews:review-vote-helpful', kwargs={'pk': review.id})
        response = self.client.post(url, {'vote': 'helpful'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot vote on your own review', str(response.data))
    
    def test_report_review(self):
        """Test reporting a review."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        # Create another user to report
        reporter = User.objects.create_user(
            username='reporter',
            email='reporter@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=reporter)
        
        data = {
            'reason': 'spam',
            'description': 'This looks like spam'
        }
        
        url = reverse('reviews:review-report', kwargs={'pk': review.id})
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReviewReport.objects.count(), 1)
        
        report = ReviewReport.objects.first()
        self.assertEqual(report.reporter, reporter)
        self.assertEqual(report.review, review)
        self.assertEqual(report.reason, 'spam')
    
    def test_moderate_review(self):
        """Test moderating a review."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'action': 'approve',
            'notes': 'Looks good'
        }
        
        url = reverse('reviews:review-moderate', kwargs={'pk': review.id})
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        review.refresh_from_db()
        self.assertEqual(review.status, 'approved')
        self.assertEqual(review.moderated_by, self.admin)
        self.assertEqual(review.moderation_notes, 'Looks good')
    
    def test_moderate_review_non_admin_fails(self):
        """Test that non-admin users cannot moderate reviews."""
        review = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.customer)
        
        data = {
            'action': 'approve',
            'notes': 'Looks good'
        }
        
        url = reverse('reviews:review-moderate', kwargs={'pk': review.id})
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_bulk_moderate_reviews(self):
        """Test bulk moderating reviews."""
        review1 = Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        review2 = Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='pending'
        )
        
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'review_ids': [str(review1.id), str(review2.id)],
            'action': 'approve',
            'notes': 'Bulk approval'
        }
        
        url = reverse('reviews:review-bulk-moderate')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 2)
        self.assertEqual(response.data['failed'], 0)
        
        review1.refresh_from_db()
        review2.refresh_from_db()
        
        self.assertEqual(review1.status, 'approved')
        self.assertEqual(review2.status, 'approved')


class ProductReviewAPITest(APITestCase):
    """
    Test cases for product-specific review endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Excellent!',
            comment='Love it',
            status='approved',
            is_verified_purchase=True
        )
        
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='approved',
            is_verified_purchase=False
        )
    
    def test_get_product_reviews(self):
        """Test getting reviews for a specific product."""
        url = reverse('reviews:product-reviews', kwargs={'product_id': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_product_reviews_verified_only(self):
        """Test getting only verified purchase reviews."""
        url = reverse('reviews:product-reviews', kwargs={'product_id': self.product.id})
        response = self.client.get(url, {'verified_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['is_verified_purchase'])
    
    def test_get_product_reviews_by_rating(self):
        """Test filtering reviews by rating."""
        url = reverse('reviews:product-reviews', kwargs={'product_id': self.product.id})
        response = self.client.get(url, {'rating': '5'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['rating'], 5)
    
    def test_get_product_review_summary(self):
        """Test getting product review summary."""
        url = reverse('reviews:product-review-summary', kwargs={'product_id': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reviews'], 2)
        self.assertEqual(float(response.data['average_rating']), 4.5)
        self.assertEqual(len(response.data['recent_reviews']), 2)
        self.assertEqual(float(response.data['verified_purchase_percentage']), 50.0)


class ModerationAPITest(APITestCase):
    """
    Test cases for moderation endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            user_type='admin'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        
        # Create reviews with different statuses
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=5,
            title='Pending review',
            comment='This is pending',
            status='pending'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=4,
            title='Approved review',
            comment='This is approved',
            status='approved'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.customer,
            rating=3,
            title='Flagged review',
            comment='This is flagged',
            status='flagged'
        )
    
    def test_moderation_dashboard(self):
        """Test getting moderation dashboard data."""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('reviews:moderation-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check stats
        stats = response.data['stats']
        self.assertEqual(stats['pending_reviews'], 1)
        self.assertEqual(stats['approved_reviews'], 1)
        self.assertEqual(stats['flagged_reviews'], 1)
        
        # Check pending reviews
        self.assertEqual(len(response.data['pending_reviews']['results']), 1)
        self.assertEqual(response.data['pending_reviews']['count'], 1)
        
        # Check flagged reviews
        self.assertEqual(len(response.data['flagged_reviews']['results']), 1)
        self.assertEqual(response.data['flagged_reviews']['count'], 1)
    
    def test_moderation_dashboard_non_admin_fails(self):
        """Test that non-admin users cannot access moderation dashboard."""
        self.client.force_authenticate(user=self.customer)
        
        url = reverse('reviews:moderation-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_review_analytics(self):
        """Test getting review analytics."""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('reviews:review-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include all approved reviews
        self.assertEqual(response.data['total_reviews'], 1)  # Only approved reviews
        self.assertEqual(float(response.data['average_rating']), 4.0)
    
    def test_review_analytics_with_product_filter(self):
        """Test getting review analytics filtered by product."""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('reviews:review-analytics')
        response = self.client.get(url, {'product': str(self.product.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reviews'], 1)  # Only approved reviews for this product