"""
Tests for the reviews app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from .models import Review, ReviewHelpfulness, ReviewImage, ReviewReport
from .services import ReviewService, ReviewModerationService

User = get_user_model()


class ReviewModelTest(TestCase):
    """
    Test cases for Review model.
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
        self.order = Order.objects.create(
            customer=self.user,
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
    
    def test_review_creation(self):
        """Test creating a review."""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            order_item=self.order_item,
            rating=5,
            title='Great product!',
            comment='I love this product.',
            is_verified_purchase=True
        )
        
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Great product!')
        self.assertTrue(review.is_verified_purchase)
        self.assertEqual(review.status, 'pending')
    
    def test_review_unique_constraint(self):
        """Test that a user can only review a product once."""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                product=self.product,
                user=self.user,
                rating=4,
                title='Another review',
                comment='This should fail.'
            )
    
    def test_review_rating_validation(self):
        """Test rating validation."""
        # Valid rating
        review = Review(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        review.full_clean()  # Should not raise ValidationError
        
        # Invalid rating (too low)
        review.rating = 0
        with self.assertRaises(ValidationError):
            review.full_clean()
        
        # Invalid rating (too high)
        review.rating = 6
        with self.assertRaises(ValidationError):
            review.full_clean()
    
    def test_review_moderation_methods(self):
        """Test review moderation methods."""
        moderator = User.objects.create_user(
            username='moderator',
            email='mod@example.com',
            password='modpass123',
            is_staff=True
        )
        
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        # Test approve
        review.approve(moderator)
        self.assertEqual(review.status, 'approved')
        self.assertEqual(review.moderated_by, moderator)
        self.assertIsNotNone(review.moderated_at)
        
        # Test reject
        review.reject(moderator, 'Inappropriate content')
        self.assertEqual(review.status, 'rejected')
        self.assertEqual(review.moderation_notes, 'Inappropriate content')
        
        # Test flag
        review.flag(moderator, 'Needs review')
        self.assertEqual(review.status, 'flagged')
        self.assertEqual(review.moderation_notes, 'Needs review')
    
    def test_helpfulness_score(self):
        """Test helpfulness score calculation."""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        # No votes
        self.assertEqual(review.helpfulness_score, 0)
        
        # Add some votes
        review.helpful_count = 8
        review.not_helpful_count = 2
        review.save()
        
        self.assertEqual(review.helpfulness_score, 80.0)


class ReviewHelpfulnessTest(TestCase):
    """
    Test cases for ReviewHelpfulness model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
        self.review = Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
    
    def test_helpfulness_vote_creation(self):
        """Test creating a helpfulness vote."""
        vote = ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.user2,
            vote='helpful'
        )
        
        self.assertEqual(vote.review, self.review)
        self.assertEqual(vote.user, self.user2)
        self.assertEqual(vote.vote, 'helpful')
        
        # Check that review counts were updated
        self.review.refresh_from_db()
        self.assertEqual(self.review.helpful_count, 1)
        self.assertEqual(self.review.not_helpful_count, 0)
    
    def test_helpfulness_vote_update(self):
        """Test updating a helpfulness vote."""
        vote = ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.user2,
            vote='helpful'
        )
        
        # Change vote
        vote.vote = 'not_helpful'
        vote.save()
        
        # Check that counts were updated
        self.review.refresh_from_db()
        self.assertEqual(self.review.helpful_count, 0)
        self.assertEqual(self.review.not_helpful_count, 1)
    
    def test_helpfulness_unique_constraint(self):
        """Test that a user can only vote once per review."""
        ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.user2,
            vote='helpful'
        )
        
        with self.assertRaises(IntegrityError):
            ReviewHelpfulness.objects.create(
                review=self.review,
                user=self.user2,
                vote='not_helpful'
            )


class ReviewServiceTest(TestCase):
    """
    Test cases for ReviewService.
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
        self.order = Order.objects.create(
            customer=self.user,
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
    
    def test_can_user_review_product_success(self):
        """Test successful review permission check."""
        can_review, reason, order_item = ReviewService.can_user_review_product(
            self.user, self.product
        )
        
        self.assertTrue(can_review)
        self.assertEqual(reason, "Can review")
        self.assertEqual(order_item, self.order_item)
    
    def test_can_user_review_product_no_purchase(self):
        """Test review permission check without purchase."""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        can_review, reason, order_item = ReviewService.can_user_review_product(
            user2, self.product
        )
        
        self.assertFalse(can_review)
        self.assertEqual(reason, "You can only review products you have purchased")
        self.assertIsNone(order_item)
    
    def test_can_user_review_product_already_reviewed(self):
        """Test review permission check when already reviewed."""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        can_review, reason, order_item = ReviewService.can_user_review_product(
            self.user, self.product
        )
        
        self.assertFalse(can_review)
        self.assertEqual(reason, "You have already reviewed this product")
        self.assertIsNone(order_item)
    
    def test_create_review_success(self):
        """Test successful review creation."""
        review = ReviewService.create_review(
            user=self.user,
            product=self.product,
            rating=5,
            title='Great product!',
            comment='I love this product.',
            pros='Good quality',
            cons='A bit expensive'
        )
        
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Great product!')
        self.assertEqual(review.comment, 'I love this product.')
        self.assertEqual(review.pros, 'Good quality')
        self.assertEqual(review.cons, 'A bit expensive')
        self.assertTrue(review.is_verified_purchase)
        self.assertEqual(review.status, 'pending')
    
    def test_create_review_validation_errors(self):
        """Test review creation validation errors."""
        # Invalid rating
        with self.assertRaises(ValidationError):
            ReviewService.create_review(
                user=self.user,
                product=self.product,
                rating=6,
                title='Great product!',
                comment='I love this product.'
            )
        
        # Empty title
        with self.assertRaises(ValidationError):
            ReviewService.create_review(
                user=self.user,
                product=self.product,
                rating=5,
                title='',
                comment='I love this product.'
            )
        
        # Empty comment
        with self.assertRaises(ValidationError):
            ReviewService.create_review(
                user=self.user,
                product=self.product,
                rating=5,
                title='Great product!',
                comment=''
            )
    
    def test_vote_review_helpfulness(self):
        """Test voting on review helpfulness."""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Vote helpful
        vote = ReviewService.vote_review_helpfulness(user2, review, 'helpful')
        self.assertEqual(vote.vote, 'helpful')
        
        review.refresh_from_db()
        self.assertEqual(review.helpful_count, 1)
        
        # Change vote
        vote = ReviewService.vote_review_helpfulness(user2, review, 'not_helpful')
        self.assertEqual(vote.vote, 'not_helpful')
        
        review.refresh_from_db()
        self.assertEqual(review.helpful_count, 0)
        self.assertEqual(review.not_helpful_count, 1)
    
    def test_vote_own_review_error(self):
        """Test that users cannot vote on their own reviews."""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        with self.assertRaises(ValidationError):
            ReviewService.vote_review_helpfulness(self.user, review, 'helpful')
    
    def test_report_review(self):
        """Test reporting a review."""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product!',
            comment='I love this product.'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        report = ReviewService.report_review(
            reporter=user2,
            review=review,
            reason='spam',
            description='This looks like spam'
        )
        
        self.assertEqual(report.reporter, user2)
        self.assertEqual(report.review, review)
        self.assertEqual(report.reason, 'spam')
        self.assertEqual(report.description, 'This looks like spam')
        self.assertEqual(report.status, 'pending')
    
    def test_get_review_analytics(self):
        """Test review analytics."""
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great!',
            comment='Love it',
            status='approved'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        Review.objects.create(
            product=self.product,
            user=user2,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='approved'
        )
        
        analytics = ReviewService.get_review_analytics(product=self.product)
        
        self.assertEqual(analytics['total_reviews'], 2)
        self.assertEqual(analytics['average_rating'], 4.5)
        self.assertEqual(analytics['rating_counts'][5], 1)
        self.assertEqual(analytics['rating_counts'][4], 1)


class ReviewModerationServiceTest(TestCase):
    """
    Test cases for ReviewModerationService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='mod@example.com',
            password='modpass123',
            is_staff=True
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=99.99,
            sku='TEST001'
        )
    
    def test_get_pending_reviews(self):
        """Test getting pending reviews."""
        # Create some reviews
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='approved'
        )
        
        result = ReviewModerationService.get_pending_reviews()
        
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(len(result['reviews']), 1)
        self.assertEqual(result['reviews'][0].status, 'pending')
    
    def test_bulk_moderate_reviews(self):
        """Test bulk moderation of reviews."""
        review1 = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great!',
            comment='Love it',
            status='pending'
        )
        
        review2 = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Good',
            comment='Pretty good',
            status='pending'
        )
        
        result = ReviewModerationService.bulk_moderate_reviews(
            review_ids=[review1.id, review2.id],
            moderator=self.moderator,
            action='approve'
        )
        
        self.assertEqual(result['success'], 2)
        self.assertEqual(result['failed'], 0)
        
        review1.refresh_from_db()
        review2.refresh_from_db()
        
        self.assertEqual(review1.status, 'approved')
        self.assertEqual(review2.status, 'approved')
    
    def test_get_moderation_stats(self):
        """Test getting moderation statistics."""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Pending',
            comment='Pending review',
            status='pending'
        )
        
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Approved',
            comment='Approved review',
            status='approved'
        )
        
        stats = ReviewModerationService.get_moderation_stats()
        
        self.assertEqual(stats['pending_reviews'], 1)
        self.assertEqual(stats['approved_reviews'], 1)
        self.assertEqual(stats['flagged_reviews'], 0)
        self.assertEqual(stats['rejected_reviews'], 0)