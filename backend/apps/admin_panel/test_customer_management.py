"""
Tests for the Advanced Customer Management System.
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.customers.models import CustomerProfile
from apps.orders.models import Order
from .models import AdminUser
from .customer_models import (
    CustomerSegment, CustomerSegmentMembership, CustomerLifecycleStage,
    CustomerCommunicationHistory, CustomerSupportTicket, CustomerAnalytics,
    CustomerLoyaltyProgram, CustomerRiskAssessment, CustomerGDPRCompliance,
    CustomerSocialMediaIntegration, CustomerWinBackCampaign,
    CustomerAccountHealthScore, CustomerPreferenceCenter,
    CustomerComplaintManagement, CustomerChurnPrediction
)

User = get_user_model()


class CustomerModelTests(TestCase):
    """Test customer management models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            account_status='ACTIVE'
        )
        self.admin_user = AdminUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )

    def test_customer_segment_creation(self):
        """Test customer segment creation."""
        segment = CustomerSegment.objects.create(
            name='VIP Customers',
            description='High-value customers',
            segment_type='value_based',
            criteria={'total_spent__gte': 1000},
            created_by=self.admin_user
        )
        
        self.assertEqual(segment.name, 'VIP Customers')
        self.assertEqual(segment.segment_type, 'value_based')
        self.assertEqual(segment.customer_count, 0)

    def test_customer_segment_membership(self):
        """Test customer segment membership."""
        segment = CustomerSegment.objects.create(
            name='Active Customers',
            segment_type='behavioral',
            created_by=self.admin_user
        )
        
        membership = CustomerSegmentMembership.objects.create(
            customer=self.customer,
            segment=segment,
            confidence_score=0.9
        )
        
        self.assertEqual(membership.customer, self.customer)
        self.assertEqual(membership.segment, segment)
        self.assertEqual(membership.confidence_score, 0.9)
        self.assertTrue(membership.is_active)

    def test_customer_lifecycle_stage(self):
        """Test customer lifecycle stage management."""
        lifecycle = CustomerLifecycleStage.objects.create(
            customer=self.customer,
            current_stage='active'
        )
        
        self.assertEqual(lifecycle.current_stage, 'active')
        self.assertEqual(lifecycle.total_stage_changes, 0)
        
        # Test stage update
        lifecycle.update_stage('at_risk', 'Decreased activity')
        lifecycle.refresh_from_db()
        
        self.assertEqual(lifecycle.current_stage, 'at_risk')
        self.assertEqual(lifecycle.previous_stage, 'active')
        self.assertEqual(lifecycle.total_stage_changes, 1)

    def test_customer_communication_history(self):
        """Test customer communication history."""
        communication = CustomerCommunicationHistory.objects.create(
            customer=self.customer,
            communication_type='email',
            direction='outbound',
            subject='Welcome Email',
            content='Welcome to our platform!',
            sender=self.admin_user
        )
        
        self.assertEqual(communication.customer, self.customer)
        self.assertEqual(communication.communication_type, 'email')
        self.assertEqual(communication.status, 'sent')

    def test_customer_support_ticket(self):
        """Test customer support ticket creation."""
        ticket = CustomerSupportTicket.objects.create(
            customer=self.customer,
            subject='Product Issue',
            description='Having trouble with my order',
            category='product_issue',
            priority='normal'
        )
        
        self.assertTrue(ticket.ticket_number)
        self.assertEqual(ticket.status, 'open')
        self.assertEqual(ticket.priority, 'normal')

    def test_customer_analytics(self):
        """Test customer analytics."""
        analytics = CustomerAnalytics.objects.create(
            customer=self.customer,
            lifetime_value=Decimal('500.00'),
            total_orders=5,
            average_order_value=Decimal('100.00')
        )
        
        self.assertEqual(analytics.lifetime_value, Decimal('500.00'))
        self.assertEqual(analytics.total_orders, 5)
        
        # Test metrics calculation
        analytics.calculate_metrics()
        self.assertIsNotNone(analytics.last_calculated)

    def test_customer_loyalty_program(self):
        """Test customer loyalty program."""
        loyalty = CustomerLoyaltyProgram.objects.create(
            customer=self.customer,
            current_points=100,
            current_tier='bronze'
        )
        
        self.assertEqual(loyalty.current_points, 100)
        self.assertEqual(loyalty.current_tier, 'bronze')
        
        # Test adding points
        loyalty.add_points(50, 'Purchase reward')
        loyalty.refresh_from_db()
        
        self.assertEqual(loyalty.current_points, 150)
        self.assertEqual(loyalty.lifetime_points, 50)

    def test_customer_risk_assessment(self):
        """Test customer risk assessment."""
        risk = CustomerRiskAssessment.objects.create(
            customer=self.customer,
            overall_risk_score=25.0,
            fraud_risk_score=10.0,
            overall_risk_level='low'
        )
        
        self.assertEqual(risk.overall_risk_score, 25.0)
        self.assertEqual(risk.overall_risk_level, 'low')

    def test_customer_gdpr_compliance(self):
        """Test GDPR compliance."""
        gdpr = CustomerGDPRCompliance.objects.create(
            customer=self.customer,
            marketing_consent=True,
            analytics_consent=False
        )
        
        self.assertTrue(gdpr.marketing_consent)
        self.assertFalse(gdpr.analytics_consent)
        self.assertFalse(gdpr.deletion_requested)

    def test_customer_social_media_integration(self):
        """Test social media integration."""
        social = CustomerSocialMediaIntegration.objects.create(
            customer=self.customer,
            platform='facebook',
            username='testuser123',
            profile_url='https://facebook.com/testuser123',
            followers_count=500
        )
        
        self.assertEqual(social.platform, 'facebook')
        self.assertEqual(social.followers_count, 500)

    def test_customer_winback_campaign(self):
        """Test win-back campaign."""
        campaign = CustomerWinBackCampaign.objects.create(
            customer=self.customer,
            name='Win Back Campaign',
            trigger_type='inactive_period',
            scheduled_date=timezone.now(),
            discount_percentage=20.0
        )
        
        self.assertEqual(campaign.name, 'Win Back Campaign')
        self.assertEqual(campaign.discount_percentage, 20.0)
        self.assertEqual(campaign.status, 'scheduled')

    def test_customer_health_score(self):
        """Test customer health score."""
        health = CustomerAccountHealthScore.objects.create(
            customer=self.customer,
            engagement_score=75.0,
            satisfaction_score=80.0,
            loyalty_score=70.0,
            payment_score=90.0,
            support_score=85.0
        )
        
        # Test health score calculation
        health.calculate_health_score()
        health.refresh_from_db()
        
        self.assertGreater(health.overall_score, 0)
        self.assertIn(health.health_level, ['excellent', 'good', 'fair', 'poor', 'critical'])

    def test_customer_preference_center(self):
        """Test customer preference center."""
        preferences = CustomerPreferenceCenter.objects.create(
            customer=self.customer,
            email_marketing=True,
            sms_marketing=False,
            push_notifications=True,
            email_frequency='weekly'
        )
        
        self.assertTrue(preferences.email_marketing)
        self.assertFalse(preferences.sms_marketing)
        self.assertEqual(preferences.email_frequency, 'weekly')

    def test_customer_complaint_management(self):
        """Test customer complaint management."""
        complaint = CustomerComplaintManagement.objects.create(
            customer=self.customer,
            complaint_type='product_quality',
            subject='Defective Product',
            description='The product arrived damaged',
            severity='medium'
        )
        
        self.assertTrue(complaint.complaint_number)
        self.assertEqual(complaint.status, 'received')
        self.assertEqual(complaint.severity, 'medium')

    def test_customer_churn_prediction(self):
        """Test customer churn prediction."""
        prediction = CustomerChurnPrediction.objects.create(
            customer=self.customer,
            churn_probability=0.3,
            churn_risk_level='medium',
            model_used='logistic_regression',
            model_version='1.0',
            prediction_confidence=0.85
        )
        
        self.assertEqual(prediction.churn_probability, 0.3)
        self.assertEqual(prediction.churn_risk_level, 'medium')
        self.assertEqual(prediction.prediction_confidence, 0.85)


class CustomerAPITests(APITestCase):
    """Test customer management API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            account_status='ACTIVE'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_customer_list_api(self):
        """Test customer list API."""
        url = reverse('admin_panel:admin-customers-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_customer_detail_api(self):
        """Test customer detail API."""
        url = reverse('admin_panel:admin-customers-detail', kwargs={'pk': self.customer.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.customer.id)

    def test_customer_dashboard_stats(self):
        """Test customer dashboard stats API."""
        url = reverse('admin_panel:admin-customers-dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_customers', response.data)
        self.assertIn('new_customers_today', response.data)

    def test_customer_analytics_overview(self):
        """Test customer analytics overview API."""
        url = reverse('admin_panel:admin-customers-analytics-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer_growth', response.data)
        self.assertIn('tier_distribution', response.data)

    def test_customer_detailed_profile(self):
        """Test detailed customer profile API."""
        url = reverse('admin_panel:admin-customers-detailed-profile', kwargs={'pk': self.customer.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer', response.data)
        self.assertIn('addresses', response.data)
        self.assertIn('recent_orders', response.data)

    def test_customer_advanced_search(self):
        """Test advanced customer search API."""
        url = reverse('admin_panel:admin-customers-advanced-search')
        data = {
            'query': 'test',
            'account_status': 'ACTIVE',
            'page': 1,
            'page_size': 10
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

    def test_customer_export(self):
        """Test customer export API."""
        url = reverse('admin_panel:admin-customers-export')
        data = {
            'format': 'json',
            'include_addresses': True,
            'include_orders': False
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_segment_creation(self):
        """Test customer segment creation API."""
        url = reverse('admin_panel:admin-customer-segments-list')
        data = {
            'name': 'Test Segment',
            'description': 'Test segment description',
            'segment_type': 'behavioral',
            'criteria': {'total_orders__gte': 5},
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Segment')

    def test_support_ticket_creation(self):
        """Test support ticket creation API."""
        url = reverse('admin_panel:admin-support-tickets-list')
        data = {
            'customer': self.customer.id,
            'subject': 'Test Ticket',
            'description': 'Test ticket description',
            'category': 'general_inquiry',
            'priority': 'normal'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subject'], 'Test Ticket')

    def test_health_score_recalculation(self):
        """Test health score recalculation API."""
        # Create a health score first
        CustomerAccountHealthScore.objects.create(
            customer=self.customer,
            engagement_score=75.0,
            satisfaction_score=80.0,
            loyalty_score=70.0,
            payment_score=90.0,
            support_score=85.0
        )
        
        url = reverse('admin_panel:admin-health-scores-recalculate-all-scores')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_churn_prediction_analytics(self):
        """Test churn prediction analytics API."""
        # Create a churn prediction first
        CustomerChurnPrediction.objects.create(
            customer=self.customer,
            churn_probability=0.3,
            churn_risk_level='medium',
            model_used='logistic_regression',
            model_version='1.0',
            prediction_confidence=0.85
        )
        
        url = reverse('admin_panel:admin-churn-predictions-churn-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_predictions', response.data)
        self.assertIn('high_risk_customers', response.data)

    def test_complaint_resolution(self):
        """Test complaint resolution API."""
        complaint = CustomerComplaintManagement.objects.create(
            customer=self.customer,
            complaint_type='product_quality',
            subject='Test Complaint',
            description='Test complaint description',
            severity='medium'
        )
        
        url = reverse('admin_panel:admin-complaints-resolve-complaint', kwargs={'pk': complaint.pk})
        data = {
            'resolution_description': 'Issue resolved',
            'compensation_offered': 50.00,
            'compensation_type': 'refund'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'resolved')

    def test_winback_campaign_activation(self):
        """Test win-back campaign activation API."""
        campaign = CustomerWinBackCampaign.objects.create(
            customer=self.customer,
            name='Test Campaign',
            trigger_type='inactive_period',
            scheduled_date=timezone.now(),
            discount_percentage=20.0
        )
        
        url = reverse('admin_panel:admin-winback-campaigns-activate-campaign', kwargs={'pk': campaign.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, 'active')
        self.assertIsNotNone(campaign.started_at)


class CustomerIntegrationTests(TestCase):
    """Test customer management system integration."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            account_status='ACTIVE'
        )

    def test_customer_lifecycle_integration(self):
        """Test customer lifecycle stage integration."""
        # Create lifecycle stage
        lifecycle = CustomerLifecycleStage.objects.create(
            customer=self.customer,
            current_stage='prospect'
        )
        
        # Simulate customer making first purchase
        lifecycle.update_stage('new_customer', 'First purchase made')
        
        # Check history was created
        history = lifecycle.customer.lifecycle_history.first()
        self.assertIsNotNone(history)
        self.assertEqual(history.from_stage, 'prospect')
        self.assertEqual(history.to_stage, 'new_customer')

    def test_customer_analytics_integration(self):
        """Test customer analytics integration with orders."""
        analytics = CustomerAnalytics.objects.create(
            customer=self.customer
        )
        
        # Simulate order creation and analytics update
        analytics.calculate_metrics()
        
        self.assertIsNotNone(analytics.last_calculated)

    def test_customer_loyalty_integration(self):
        """Test customer loyalty program integration."""
        loyalty = CustomerLoyaltyProgram.objects.create(
            customer=self.customer,
            current_points=0
        )
        
        # Add points and check transaction creation
        loyalty.add_points(100, 'Welcome bonus')
        
        transaction = loyalty.transactions.first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.points, 100)
        self.assertEqual(transaction.transaction_type, 'earned')

    def test_customer_support_integration(self):
        """Test customer support ticket integration."""
        ticket = CustomerSupportTicket.objects.create(
            customer=self.customer,
            subject='Integration Test',
            description='Testing support integration',
            category='technical_issue'
        )
        
        # Check ticket number was generated
        self.assertIsNotNone(ticket.ticket_number)
        self.assertTrue(len(ticket.ticket_number) > 0)

    def test_customer_gdpr_integration(self):
        """Test GDPR compliance integration."""
        gdpr = CustomerGDPRCompliance.objects.create(
            customer=self.customer,
            marketing_consent=True
        )
        
        # Test consent management
        self.assertTrue(gdpr.marketing_consent)
        self.assertIsNotNone(gdpr.data_processing_consent_date)