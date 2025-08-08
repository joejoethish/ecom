"""
Tests for the Promotion and Coupon Management System
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta
import json
import uuid

from .models import (
    Promotion, Coupon, PromotionUsage, PromotionAnalytics,
    PromotionApproval, PromotionAuditLog, PromotionTemplate,
    PromotionSchedule, PromotionProduct, PromotionCategory,
    PromotionType, PromotionStatus, TargetType, PromotionChannel
)
from .serializers import (
    PromotionListSerializer, PromotionDetailSerializer, PromotionCreateSerializer,
    CouponSerializer, PromotionUsageSerializer, PromotionAnalyticsSerializer
)

User = get_user_model()


class PromotionModelTests(TestCase):
    """Test cases for Promotion model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion_data = {
            'name': 'Test Promotion',
            'description': 'Test promotion description',
            'promotion_type': PromotionType.PERCENTAGE,
            'discount_value': Decimal('20.00'),
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'target_type': TargetType.ALL_CUSTOMERS,
            'created_by': self.user
        }
    
    def test_create_promotion(self):
        """Test creating a basic promotion"""
        promotion = Promotion.objects.create(**self.promotion_data)
        
        self.assertEqual(promotion.name, 'Test Promotion')
        self.assertEqual(promotion.promotion_type, PromotionType.PERCENTAGE)
        self.assertEqual(promotion.discount_value, Decimal('20.00'))
        self.assertEqual(promotion.status, PromotionStatus.DRAFT)
        self.assertEqual(promotion.usage_count, 0)
        self.assertEqual(promotion.budget_spent, 0)
        self.assertIsNotNone(promotion.id)
    
    def test_promotion_str_representation(self):
        """Test string representation of promotion"""
        promotion = Promotion.objects.create(**self.promotion_data)
        expected_str = f"{promotion.name} ({promotion.get_promotion_type_display()})"
        self.assertEqual(str(promotion), expected_str)
    
    def test_promotion_is_active_property(self):
        """Test is_active property logic"""
        # Create active promotion
        promotion = Promotion.objects.create(
            **self.promotion_data,
            status=PromotionStatus.ACTIVE
        )
        self.assertTrue(promotion.is_active)
        
        # Test expired promotion
        promotion.end_date = timezone.now() - timedelta(days=1)
        promotion.save()
        self.assertFalse(promotion.is_active)
        
        # Test future promotion
        promotion.start_date = timezone.now() + timedelta(days=1)
        promotion.end_date = timezone.now() + timedelta(days=30)
        promotion.save()
        self.assertFalse(promotion.is_active)
        
        # Test usage limit exceeded
        promotion.start_date = timezone.now() - timedelta(days=1)
        promotion.end_date = timezone.now() + timedelta(days=30)
        promotion.usage_limit_total = 10
        promotion.usage_count = 10
        promotion.save()
        self.assertFalse(promotion.is_active)
        
        # Test budget limit exceeded
        promotion.usage_count = 5
        promotion.budget_limit = Decimal('100.00')
        promotion.budget_spent = Decimal('100.00')
        promotion.save()
        self.assertFalse(promotion.is_active)
    
    def test_promotion_days_remaining_property(self):
        """Test days_remaining property"""
        promotion = Promotion.objects.create(
            **self.promotion_data,
            end_date=timezone.now() + timedelta(days=5)
        )
        self.assertEqual(promotion.days_remaining, 5)
        
        # Test expired promotion
        promotion.end_date = timezone.now() - timedelta(days=1)
        promotion.save()
        self.assertEqual(promotion.days_remaining, 0)
    
    def test_bogo_promotion_creation(self):
        """Test creating BOGO promotion"""
        bogo_data = self.promotion_data.copy()
        bogo_data.update({
            'promotion_type': PromotionType.BOGO,
            'buy_quantity': 2,
            'get_quantity': 1,
            'get_discount_percentage': Decimal('100.00')
        })
        
        promotion = Promotion.objects.create(**bogo_data)
        self.assertEqual(promotion.promotion_type, PromotionType.BOGO)
        self.assertEqual(promotion.buy_quantity, 2)
        self.assertEqual(promotion.get_quantity, 1)
        self.assertEqual(promotion.get_discount_percentage, Decimal('100.00'))
    
    def test_promotion_with_usage_limits(self):
        """Test promotion with usage limits"""
        promotion_data = self.promotion_data.copy()
        promotion_data.update({
            'usage_limit_total': 100,
            'usage_limit_per_customer': 5
        })
        
        promotion = Promotion.objects.create(**promotion_data)
        self.assertEqual(promotion.usage_limit_total, 100)
        self.assertEqual(promotion.usage_limit_per_customer, 5)
    
    def test_promotion_with_budget_limit(self):
        """Test promotion with budget constraints"""
        promotion_data = self.promotion_data.copy()
        promotion_data.update({
            'budget_limit': Decimal('1000.00')
        })
        
        promotion = Promotion.objects.create(**promotion_data)
        self.assertEqual(promotion.budget_limit, Decimal('1000.00'))
        self.assertEqual(promotion.budget_spent, Decimal('0.00'))
    
    def test_ab_test_promotion(self):
        """Test A/B test promotion configuration"""
        promotion_data = self.promotion_data.copy()
        promotion_data.update({
            'is_ab_test': True,
            'ab_test_group': 'A',
            'ab_test_traffic_percentage': Decimal('50.00')
        })
        
        promotion = Promotion.objects.create(**promotion_data)
        self.assertTrue(promotion.is_ab_test)
        self.assertEqual(promotion.ab_test_group, 'A')
        self.assertEqual(promotion.ab_test_traffic_percentage, Decimal('50.00'))


class CouponModelTests(TestCase):
    """Test cases for Coupon model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            status=PromotionStatus.ACTIVE,
            created_by=self.user
        )
    
    def test_create_coupon(self):
        """Test creating a coupon"""
        coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='TEST20',
            usage_limit=100
        )
        
        self.assertEqual(coupon.code, 'TEST20')
        self.assertEqual(coupon.promotion, self.promotion)
        self.assertEqual(coupon.usage_limit, 100)
        self.assertEqual(coupon.usage_count, 0)
        self.assertTrue(coupon.is_active)
    
    def test_coupon_str_representation(self):
        """Test string representation of coupon"""
        coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='TEST20'
        )
        self.assertEqual(str(coupon), 'Coupon: TEST20')
    
    def test_coupon_can_be_used(self):
        """Test coupon usage validation"""
        coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='TEST20',
            usage_limit=10
        )
        
        # Should be usable initially
        self.assertTrue(coupon.can_be_used())
        
        # Test usage limit exceeded
        coupon.usage_count = 10
        coupon.save()
        self.assertFalse(coupon.can_be_used())
        
        # Test inactive coupon
        coupon.usage_count = 5
        coupon.is_active = False
        coupon.save()
        self.assertFalse(coupon.can_be_used())
        
        # Test inactive promotion
        coupon.is_active = True
        self.promotion.status = PromotionStatus.PAUSED
        self.promotion.save()
        self.assertFalse(coupon.can_be_used())
    
    def test_single_use_coupon(self):
        """Test single-use coupon functionality"""
        coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='SINGLE20',
            is_single_use=True
        )
        
        self.assertTrue(coupon.is_single_use)
        self.assertTrue(coupon.can_be_used())
        
        # After one use, should not be usable
        coupon.usage_count = 1
        coupon.save()
        self.assertFalse(coupon.can_be_used())


class PromotionUsageModelTests(TestCase):
    """Test cases for PromotionUsage model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            status=PromotionStatus.ACTIVE,
            created_by=self.user
        )
        
        self.coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='TEST20'
        )
    
    def test_create_promotion_usage(self):
        """Test creating promotion usage record"""
        usage = PromotionUsage.objects.create(
            promotion=self.promotion,
            coupon=self.coupon,
            customer=self.customer,
            discount_amount=Decimal('20.00'),
            original_amount=Decimal('100.00'),
            final_amount=Decimal('80.00'),
            channel=PromotionChannel.WEBSITE
        )
        
        self.assertEqual(usage.promotion, self.promotion)
        self.assertEqual(usage.coupon, self.coupon)
        self.assertEqual(usage.customer, self.customer)
        self.assertEqual(usage.discount_amount, Decimal('20.00'))
        self.assertEqual(usage.original_amount, Decimal('100.00'))
        self.assertEqual(usage.final_amount, Decimal('80.00'))
        self.assertEqual(usage.channel, PromotionChannel.WEBSITE)
        self.assertFalse(usage.is_suspicious)
    
    def test_suspicious_usage_tracking(self):
        """Test fraud detection in usage tracking"""
        usage = PromotionUsage.objects.create(
            promotion=self.promotion,
            customer=self.customer,
            discount_amount=Decimal('20.00'),
            original_amount=Decimal('100.00'),
            final_amount=Decimal('80.00'),
            channel=PromotionChannel.WEBSITE,
            is_suspicious=True,
            fraud_reasons=['multiple_rapid_uses', 'unusual_pattern']
        )
        
        self.assertTrue(usage.is_suspicious)
        self.assertIn('multiple_rapid_uses', usage.fraud_reasons)
        self.assertIn('unusual_pattern', usage.fraud_reasons)


class PromotionAnalyticsModelTests(TestCase):
    """Test cases for PromotionAnalytics model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            status=PromotionStatus.ACTIVE,
            created_by=self.user
        )
    
    def test_create_promotion_analytics(self):
        """Test creating promotion analytics record"""
        analytics = PromotionAnalytics.objects.create(
            promotion=self.promotion,
            date=timezone.now().date(),
            total_uses=50,
            unique_customers=30,
            total_discount_given=Decimal('1000.00'),
            total_revenue_generated=Decimal('4000.00'),
            average_order_value=Decimal('133.33'),
            conversion_rate=Decimal('15.50'),
            click_through_rate=Decimal('8.25'),
            channel_breakdown={
                'website': 30,
                'mobile_app': 15,
                'email': 5
            }
        )
        
        self.assertEqual(analytics.promotion, self.promotion)
        self.assertEqual(analytics.total_uses, 50)
        self.assertEqual(analytics.unique_customers, 30)
        self.assertEqual(analytics.total_discount_given, Decimal('1000.00'))
        self.assertEqual(analytics.total_revenue_generated, Decimal('4000.00'))
        self.assertEqual(analytics.conversion_rate, Decimal('15.50'))
        self.assertIn('website', analytics.channel_breakdown)
        self.assertEqual(analytics.channel_breakdown['website'], 30)


class PromotionApprovalModelTests(TestCase):
    """Test cases for PromotionApproval model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.approver = User.objects.create_user(
            username='approver',
            email='approver@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            status=PromotionStatus.PENDING_APPROVAL,
            requires_approval=True,
            created_by=self.user
        )
    
    def test_create_promotion_approval(self):
        """Test creating promotion approval record"""
        approval = PromotionApproval.objects.create(
            promotion=self.promotion,
            approver=self.approver,
            status='approved',
            comments='Looks good, approved for activation'
        )
        
        self.assertEqual(approval.promotion, self.promotion)
        self.assertEqual(approval.approver, self.approver)
        self.assertEqual(approval.status, 'approved')
        self.assertEqual(approval.comments, 'Looks good, approved for activation')
    
    def test_promotion_approval_rejection(self):
        """Test promotion rejection workflow"""
        approval = PromotionApproval.objects.create(
            promotion=self.promotion,
            approver=self.approver,
            status='rejected',
            comments='Discount too high, please revise'
        )
        
        self.assertEqual(approval.status, 'rejected')
        self.assertEqual(approval.comments, 'Discount too high, please revise')


class PromotionAuditLogModelTests(TestCase):
    """Test cases for PromotionAuditLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            created_by=self.user
        )
    
    def test_create_audit_log(self):
        """Test creating audit log entry"""
        audit_log = PromotionAuditLog.objects.create(
            promotion=self.promotion,
            user=self.user,
            action='created',
            changes={'promotion_created': True},
            old_values={},
            new_values={'name': 'Test Promotion'},
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test Browser'
        )
        
        self.assertEqual(audit_log.promotion, self.promotion)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'created')
        self.assertEqual(audit_log.changes['promotion_created'], True)
        self.assertEqual(audit_log.ip_address, '192.168.1.1')
        self.assertIn('Mozilla', audit_log.user_agent)
    
    def test_audit_log_update_tracking(self):
        """Test audit log for updates"""
        audit_log = PromotionAuditLog.objects.create(
            promotion=self.promotion,
            user=self.user,
            action='updated',
            changes={
                'name': {'old': 'Old Name', 'new': 'New Name'},
                'discount_value': {'old': '10.00', 'new': '20.00'}
            },
            old_values={'name': 'Old Name', 'discount_value': '10.00'},
            new_values={'name': 'New Name', 'discount_value': '20.00'}
        )
        
        self.assertEqual(audit_log.action, 'updated')
        self.assertIn('name', audit_log.changes)
        self.assertEqual(audit_log.changes['name']['old'], 'Old Name')
        self.assertEqual(audit_log.changes['name']['new'], 'New Name')


class PromotionTemplateModelTests(TestCase):
    """Test cases for PromotionTemplate model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_promotion_template(self):
        """Test creating promotion template"""
        template_data = {
            'promotion_type': PromotionType.PERCENTAGE,
            'discount_value': 20.00,
            'target_type': TargetType.ALL_CUSTOMERS,
            'allowed_channels': [PromotionChannel.WEBSITE, PromotionChannel.MOBILE_APP]
        }
        
        template = PromotionTemplate.objects.create(
            name='20% Off Template',
            description='Standard 20% discount template',
            category='discount',
            template_data=template_data,
            created_by=self.user
        )
        
        self.assertEqual(template.name, '20% Off Template')
        self.assertEqual(template.category, 'discount')
        self.assertEqual(template.template_data['promotion_type'], PromotionType.PERCENTAGE)
        self.assertEqual(template.template_data['discount_value'], 20.00)
        self.assertEqual(template.usage_count, 0)
        self.assertTrue(template.is_active)


class PromotionScheduleModelTests(TestCase):
    """Test cases for PromotionSchedule model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            created_by=self.user
        )
    
    def test_create_promotion_schedule(self):
        """Test creating promotion schedule"""
        schedule = PromotionSchedule.objects.create(
            promotion=self.promotion,
            action='activate',
            scheduled_time=timezone.now() + timedelta(hours=1)
        )
        
        self.assertEqual(schedule.promotion, self.promotion)
        self.assertEqual(schedule.action, 'activate')
        self.assertFalse(schedule.is_executed)
        self.assertIsNone(schedule.executed_at)
    
    def test_schedule_execution_tracking(self):
        """Test schedule execution tracking"""
        schedule = PromotionSchedule.objects.create(
            promotion=self.promotion,
            action='activate',
            scheduled_time=timezone.now() - timedelta(hours=1)
        )
        
        # Simulate execution
        schedule.is_executed = True
        schedule.executed_at = timezone.now()
        schedule.execution_result = 'Successfully activated promotion'
        schedule.save()
        
        self.assertTrue(schedule.is_executed)
        self.assertIsNotNone(schedule.executed_at)
        self.assertEqual(schedule.execution_result, 'Successfully activated promotion')


class PromotionAPITests(APITestCase):
    """Test cases for Promotion API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.promotion_data = {
            'name': 'Test Promotion',
            'description': 'Test promotion description',
            'promotion_type': PromotionType.PERCENTAGE,
            'discount_value': '20.00',
            'start_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=30)).isoformat(),
            'target_type': TargetType.ALL_CUSTOMERS,
            'priority': 1
        }
    
    def test_create_promotion_api(self):
        """Test creating promotion via API"""
        response = self.client.post('/api/promotions/', self.promotion_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Promotion')
        self.assertEqual(response.data['promotion_type'], PromotionType.PERCENTAGE)
        self.assertEqual(response.data['status'], PromotionStatus.DRAFT)
    
    def test_list_promotions_api(self):
        """Test listing promotions via API"""
        # Create test promotions
        Promotion.objects.create(**{
            **self.promotion_data,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        response = self.client.get('/api/promotions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_promotion_filtering(self):
        """Test promotion filtering"""
        # Create promotions with different statuses
        active_promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Active Promotion',
            'status': PromotionStatus.ACTIVE,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        draft_promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Draft Promotion',
            'status': PromotionStatus.DRAFT,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        # Filter by status
        response = self.client.get('/api/promotions/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active Promotion')
        
        # Filter by type
        response = self.client.get(f'/api/promotions/?type={PromotionType.PERCENTAGE}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_promotion_search(self):
        """Test promotion search functionality"""
        Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Summer Sale',
            'description': 'Great summer discounts',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Winter Sale',
            'description': 'Winter clearance',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        # Search by name
        response = self.client.get('/api/promotions/?search=Summer')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Summer Sale')
        
        # Search by description
        response = self.client.get('/api/promotions/?search=clearance')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Winter Sale')
    
    def test_promotion_activation(self):
        """Test promotion activation endpoint"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        response = self.client.post(f'/api/promotions/{promotion.id}/activate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activated successfully', response.data['message'])
        
        # Verify promotion is activated
        promotion.refresh_from_db()
        self.assertEqual(promotion.status, PromotionStatus.ACTIVE)
    
    def test_promotion_deactivation(self):
        """Test promotion deactivation endpoint"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'status': PromotionStatus.ACTIVE,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        response = self.client.post(f'/api/promotions/{promotion.id}/deactivate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('deactivated successfully', response.data['message'])
        
        # Verify promotion is deactivated
        promotion.refresh_from_db()
        self.assertEqual(promotion.status, PromotionStatus.PAUSED)
    
    def test_promotion_approval(self):
        """Test promotion approval endpoint"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'status': PromotionStatus.PENDING_APPROVAL,
            'requires_approval': True,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        approval_data = {
            'comments': 'Approved for activation'
        }
        
        response = self.client.post(
            f'/api/promotions/{promotion.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approved successfully', response.data['message'])
        
        # Verify promotion is approved
        promotion.refresh_from_db()
        self.assertEqual(promotion.status, PromotionStatus.APPROVED)
        self.assertEqual(promotion.approved_by, self.user)
        self.assertIsNotNone(promotion.approved_at)
    
    def test_promotion_duplication(self):
        """Test promotion duplication endpoint"""
        original_promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        response = self.client.post(f'/api/promotions/{original_promotion.id}/duplicate/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('(Copy)', response.data['name'])
        self.assertEqual(response.data['status'], PromotionStatus.DRAFT)
        
        # Verify duplicate was created
        self.assertEqual(Promotion.objects.count(), 2)
    
    def test_promotion_analytics(self):
        """Test promotion analytics endpoint"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        # Create analytics data
        PromotionAnalytics.objects.create(
            promotion=promotion,
            date=timezone.now().date(),
            total_uses=50,
            unique_customers=30,
            total_discount_given=Decimal('1000.00'),
            total_revenue_generated=Decimal('4000.00'),
            conversion_rate=Decimal('15.50')
        )
        
        response = self.client.get(f'/api/promotions/{promotion.id}/analytics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analytics', response.data)
        self.assertIn('summary', response.data)
        self.assertEqual(len(response.data['analytics']), 1)
    
    def test_bulk_promotion_actions(self):
        """Test bulk promotion actions"""
        # Create multiple promotions
        promotion1 = Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Promotion 1',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        promotion2 = Promotion.objects.create(**{
            **self.promotion_data,
            'name': 'Promotion 2',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        bulk_data = {
            'promotion_ids': [str(promotion1.id), str(promotion2.id)],
            'action': 'activate'
        }
        
        response = self.client.post('/api/promotions/bulk_action/', bulk_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Bulk activate completed', response.data['message'])
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify promotions were activated
        promotion1.refresh_from_db()
        promotion2.refresh_from_db()
        self.assertEqual(promotion1.status, PromotionStatus.ACTIVE)
        self.assertEqual(promotion2.status, PromotionStatus.ACTIVE)
    
    def test_promotion_dashboard_stats(self):
        """Test promotion dashboard statistics"""
        # Create promotions with different statuses
        Promotion.objects.create(**{
            **self.promotion_data,
            'status': PromotionStatus.ACTIVE,
            'start_date': timezone.now() - timedelta(days=1),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        Promotion.objects.create(**{
            **self.promotion_data,
            'status': PromotionStatus.PENDING_APPROVAL,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'created_by': self.user
        })
        
        response = self.client.get('/api/promotions/dashboard_stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('counts', response.data)
        self.assertIn('performance', response.data)
        self.assertIn('top_promotions', response.data)
        self.assertEqual(response.data['counts']['total_promotions'], 2)
        self.assertEqual(response.data['counts']['active_promotions'], 1)
        self.assertEqual(response.data['counts']['pending_approval'], 1)


class CouponAPITests(APITestCase):
    """Test cases for Coupon API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.promotion = Promotion.objects.create(
            name='Test Promotion',
            description='Test promotion description',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            status=PromotionStatus.ACTIVE,
            created_by=self.user
        )
    
    def test_create_coupon_api(self):
        """Test creating coupon via API"""
        coupon_data = {
            'promotion': str(self.promotion.id),
            'code': 'TEST20',
            'usage_limit': 100,
            'is_single_use': False
        }
        
        response = self.client.post('/api/coupons/', coupon_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'TEST20')
        self.assertEqual(response.data['usage_limit'], 100)
        self.assertFalse(response.data['is_single_use'])
    
    def test_list_coupons_api(self):
        """Test listing coupons via API"""
        Coupon.objects.create(
            promotion=self.promotion,
            code='TEST20',
            usage_limit=100
        )
        
        response = self.client.get('/api/coupons/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'TEST20')
    
    def test_coupon_validation_api(self):
        """Test coupon validation endpoint"""
        coupon = Coupon.objects.create(
            promotion=self.promotion,
            code='VALID20',
            usage_limit=10
        )
        
        response = self.client.get(f'/api/coupons/{coupon.id}/validate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertIn('promotion_details', response.data)
    
    def test_bulk_coupon_generation(self):
        """Test bulk coupon generation"""
        bulk_data = {
            'promotion': str(self.promotion.id),
            'count': 5,
            'prefix': 'BULK',
            'usage_limit': 1
        }
        
        response = self.client.post('/api/coupons/bulk_generate/', bulk_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['coupons']), 5)
        
        # Verify coupons were created
        self.assertEqual(Coupon.objects.filter(promotion=self.promotion).count(), 5)


class PromotionSerializerTests(TestCase):
    """Test cases for Promotion serializers"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.promotion_data = {
            'name': 'Test Promotion',
            'description': 'Test promotion description',
            'promotion_type': PromotionType.PERCENTAGE,
            'discount_value': '20.00',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'target_type': TargetType.ALL_CUSTOMERS
        }
    
    def test_promotion_create_serializer_validation(self):
        """Test promotion creation serializer validation"""
        # Test valid data
        serializer = PromotionCreateSerializer(data=self.promotion_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid date range
        invalid_data = self.promotion_data.copy()
        invalid_data['end_date'] = timezone.now() - timedelta(days=1)
        
        serializer = PromotionCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
        
        # Test invalid percentage discount
        invalid_data = self.promotion_data.copy()
        invalid_data['discount_value'] = '150.00'
        
        serializer = PromotionCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('discount_value', serializer.errors)
    
    def test_promotion_detail_serializer(self):
        """Test promotion detail serializer"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'created_by': self.user
        })
        
        serializer = PromotionDetailSerializer(promotion)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Promotion')
        self.assertEqual(data['promotion_type'], PromotionType.PERCENTAGE)
        self.assertIn('is_active', data)
        self.assertIn('days_remaining', data)
        self.assertIn('usage_percentage', data)
        self.assertIn('performance_metrics', data)
    
    def test_promotion_list_serializer(self):
        """Test promotion list serializer"""
        promotion = Promotion.objects.create(**{
            **self.promotion_data,
            'usage_limit_total': 100,
            'usage_count': 25,
            'budget_limit': Decimal('1000.00'),
            'budget_spent': Decimal('250.00'),
            'created_by': self.user
        })
        
        serializer = PromotionListSerializer(promotion)
        data = serializer.data
        
        self.assertEqual(data['usage_percentage'], 25.0)
        self.assertEqual(data['budget_percentage'], 25.0)
        self.assertIn('promotion_type_display', data)
        self.assertIn('status_display', data)


class PromotionIntegrationTests(TestCase):
    """Integration tests for promotion system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123'
        )
    
    def test_promotion_lifecycle(self):
        """Test complete promotion lifecycle"""
        # 1. Create promotion
        promotion = Promotion.objects.create(
            name='Lifecycle Test Promotion',
            description='Testing complete lifecycle',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('25.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            usage_limit_total=100,
            budget_limit=Decimal('5000.00'),
            requires_approval=True,
            created_by=self.user
        )
        
        self.assertEqual(promotion.status, PromotionStatus.DRAFT)
        
        # 2. Submit for approval
        promotion.status = PromotionStatus.PENDING_APPROVAL
        promotion.save()
        
        # 3. Approve promotion
        approval = PromotionApproval.objects.create(
            promotion=promotion,
            approver=self.user,
            status='approved',
            comments='Approved for testing'
        )
        
        promotion.approved_by = self.user
        promotion.approved_at = timezone.now()
        promotion.status = PromotionStatus.APPROVED
        promotion.save()
        
        # 4. Activate promotion
        promotion.status = PromotionStatus.ACTIVE
        promotion.save()
        
        self.assertTrue(promotion.is_active)
        
        # 5. Create coupon
        coupon = Coupon.objects.create(
            promotion=promotion,
            code='LIFECYCLE25',
            usage_limit=50
        )
        
        self.assertTrue(coupon.can_be_used())
        
        # 6. Use promotion
        usage = PromotionUsage.objects.create(
            promotion=promotion,
            coupon=coupon,
            customer=self.customer,
            discount_amount=Decimal('25.00'),
            original_amount=Decimal('100.00'),
            final_amount=Decimal('75.00'),
            channel=PromotionChannel.WEBSITE
        )
        
        # Update counters
        promotion.usage_count += 1
        promotion.budget_spent += usage.discount_amount
        promotion.save()
        
        coupon.usage_count += 1
        coupon.save()
        
        # 7. Create analytics
        analytics = PromotionAnalytics.objects.create(
            promotion=promotion,
            date=timezone.now().date(),
            total_uses=1,
            unique_customers=1,
            total_discount_given=Decimal('25.00'),
            total_revenue_generated=Decimal('75.00'),
            conversion_rate=Decimal('100.00')
        )
        
        # 8. Create audit log
        audit_log = PromotionAuditLog.objects.create(
            promotion=promotion,
            user=self.user,
            action='used',
            changes={'usage_count': {'old': 0, 'new': 1}},
            ip_address='192.168.1.1'
        )
        
        # Verify complete lifecycle
        self.assertEqual(promotion.usage_count, 1)
        self.assertEqual(promotion.budget_spent, Decimal('25.00'))
        self.assertEqual(coupon.usage_count, 1)
        self.assertEqual(PromotionUsage.objects.filter(promotion=promotion).count(), 1)
        self.assertEqual(PromotionAnalytics.objects.filter(promotion=promotion).count(), 1)
        self.assertEqual(PromotionAuditLog.objects.filter(promotion=promotion).count(), 1)
        self.assertEqual(PromotionApproval.objects.filter(promotion=promotion).count(), 1)
    
    def test_promotion_fraud_detection(self):
        """Test fraud detection in promotion usage"""
        promotion = Promotion.objects.create(
            name='Fraud Test Promotion',
            description='Testing fraud detection',
            promotion_type=PromotionType.FIXED_AMOUNT,
            discount_value=Decimal('50.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            usage_limit_per_customer=1,
            created_by=self.user,
            status=PromotionStatus.ACTIVE
        )
        
        # First usage - should be normal
        usage1 = PromotionUsage.objects.create(
            promotion=promotion,
            customer=self.customer,
            discount_amount=Decimal('50.00'),
            original_amount=Decimal('100.00'),
            final_amount=Decimal('50.00'),
            channel=PromotionChannel.WEBSITE
        )
        
        self.assertFalse(usage1.is_suspicious)
        
        # Second usage by same customer - should be flagged
        usage2 = PromotionUsage.objects.create(
            promotion=promotion,
            customer=self.customer,
            discount_amount=Decimal('50.00'),
            original_amount=Decimal('100.00'),
            final_amount=Decimal('50.00'),
            channel=PromotionChannel.WEBSITE,
            is_suspicious=True,
            fraud_reasons=['exceeds_customer_limit']
        )
        
        self.assertTrue(usage2.is_suspicious)
        self.assertIn('exceeds_customer_limit', usage2.fraud_reasons)
    
    def test_promotion_stacking_rules(self):
        """Test promotion stacking rules"""
        # Create base promotion
        base_promotion = Promotion.objects.create(
            name='Base Promotion',
            description='Base 10% discount',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('10.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            can_stack_with_other_promotions=True,
            stackable_promotion_types=[PromotionType.FREE_SHIPPING],
            created_by=self.user,
            status=PromotionStatus.ACTIVE
        )
        
        # Create stackable promotion
        shipping_promotion = Promotion.objects.create(
            name='Free Shipping',
            description='Free shipping promotion',
            promotion_type=PromotionType.FREE_SHIPPING,
            discount_value=Decimal('10.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            can_stack_with_other_promotions=True,
            created_by=self.user,
            status=PromotionStatus.ACTIVE
        )
        
        # Create non-stackable promotion
        exclusive_promotion = Promotion.objects.create(
            name='Exclusive Promotion',
            description='Exclusive 30% discount',
            promotion_type=PromotionType.PERCENTAGE,
            discount_value=Decimal('30.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            target_type=TargetType.ALL_CUSTOMERS,
            can_stack_with_other_promotions=False,
            excluded_promotion_ids=[str(base_promotion.id)],
            created_by=self.user,
            status=PromotionStatus.ACTIVE
        )
        
        # Test stacking validation
        self.assertTrue(base_promotion.can_stack_with_other_promotions)
        self.assertIn(PromotionType.FREE_SHIPPING, base_promotion.stackable_promotion_types)
        self.assertFalse(exclusive_promotion.can_stack_with_other_promotions)
        self.assertIn(str(base_promotion.id), exclusive_promotion.excluded_promotion_ids)