"""
Management command to test the customer management system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from apps.customers.models import CustomerProfile
from apps.admin_panel.models import AdminUser
from apps.admin_panel.customer_models import (
    CustomerSegment, CustomerSegmentMembership, CustomerLifecycleStage,
    CustomerCommunicationHistory, CustomerSupportTicket, CustomerAnalytics,
    CustomerLoyaltyProgram, CustomerRiskAssessment, CustomerGDPRCompliance,
    CustomerSocialMediaIntegration, CustomerWinBackCampaign,
    CustomerAccountHealthScore, CustomerPreferenceCenter,
    CustomerComplaintManagement, CustomerChurnPrediction
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the customer management system functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Customer Management System...'))
        
        try:
            # Create test admin user
            admin_user, created = AdminUser.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'role': 'admin',
                    'is_admin_active': True
                }
            )
            if created:
                admin_user.set_password('testpass123')
                admin_user.save()
            
            self.stdout.write('✓ Admin user created/retrieved')
            
            # Create test customer
            user, created = User.objects.get_or_create(
                username='test_customer',
                defaults={
                    'email': 'customer@test.com',
                    'first_name': 'Test',
                    'last_name': 'Customer'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            customer, created = CustomerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': '+1234567890',
                    'account_status': 'ACTIVE'
                }
            )
            
            self.stdout.write('✓ Test customer created/retrieved')
            
            # Test Customer Segment
            segment, created = CustomerSegment.objects.get_or_create(
                name='Test VIP Segment',
                defaults={
                    'description': 'Test VIP customers',
                    'segment_type': 'value_based',
                    'criteria': {'total_spent__gte': 1000},
                    'created_by': admin_user
                }
            )
            
            membership, created = CustomerSegmentMembership.objects.get_or_create(
                customer=customer,
                segment=segment,
                defaults={'confidence_score': 0.9}
            )
            
            self.stdout.write('✓ Customer segment and membership created')
            
            # Test Customer Lifecycle Stage
            lifecycle, created = CustomerLifecycleStage.objects.get_or_create(
                customer=customer,
                defaults={'current_stage': 'active'}
            )
            
            if not created:
                lifecycle.update_stage('loyal', 'Test stage update')
            
            self.stdout.write('✓ Customer lifecycle stage created/updated')
            
            # Test Customer Communication History
            communication, created = CustomerCommunicationHistory.objects.get_or_create(
                customer=customer,
                communication_type='email',
                direction='outbound',
                subject='Test Email',
                defaults={
                    'content': 'This is a test email',
                    'sender': admin_user
                }
            )
            
            self.stdout.write('✓ Customer communication history created')
            
            # Test Customer Support Ticket
            ticket, created = CustomerSupportTicket.objects.get_or_create(
                customer=customer,
                subject='Test Support Ticket',
                defaults={
                    'description': 'This is a test support ticket',
                    'category': 'general_inquiry',
                    'priority': 'normal'
                }
            )
            
            self.stdout.write('✓ Customer support ticket created')
            
            # Test Customer Analytics
            analytics, created = CustomerAnalytics.objects.get_or_create(
                customer=customer,
                defaults={
                    'lifetime_value': Decimal('500.00'),
                    'total_orders': 5,
                    'average_order_value': Decimal('100.00')
                }
            )
            
            analytics.calculate_metrics()
            self.stdout.write('✓ Customer analytics created and calculated')
            
            # Test Customer Loyalty Program
            loyalty, created = CustomerLoyaltyProgram.objects.get_or_create(
                customer=customer,
                defaults={
                    'current_points': 100,
                    'current_tier': 'bronze'
                }
            )
            
            if created:
                loyalty.add_points(50, 'Test points addition')
            
            self.stdout.write('✓ Customer loyalty program created')
            
            # Test Customer Risk Assessment
            risk, created = CustomerRiskAssessment.objects.get_or_create(
                customer=customer,
                defaults={
                    'overall_risk_score': 25.0,
                    'fraud_risk_score': 10.0,
                    'overall_risk_level': 'low'
                }
            )
            
            self.stdout.write('✓ Customer risk assessment created')
            
            # Test Customer GDPR Compliance
            gdpr, created = CustomerGDPRCompliance.objects.get_or_create(
                customer=customer,
                defaults={
                    'marketing_consent': True,
                    'analytics_consent': False
                }
            )
            
            self.stdout.write('✓ Customer GDPR compliance created')
            
            # Test Customer Social Media Integration
            social, created = CustomerSocialMediaIntegration.objects.get_or_create(
                customer=customer,
                platform='facebook',
                username='testuser123',
                defaults={
                    'profile_url': 'https://facebook.com/testuser123',
                    'followers_count': 500
                }
            )
            
            self.stdout.write('✓ Customer social media integration created')
            
            # Test Customer Win-Back Campaign
            campaign, created = CustomerWinBackCampaign.objects.get_or_create(
                customer=customer,
                name='Test Win-Back Campaign',
                defaults={
                    'trigger_type': 'inactive_period',
                    'scheduled_date': timezone.now(),
                    'discount_percentage': 20.0
                }
            )
            
            self.stdout.write('✓ Customer win-back campaign created')
            
            # Test Customer Account Health Score
            health, created = CustomerAccountHealthScore.objects.get_or_create(
                customer=customer,
                defaults={
                    'engagement_score': 75.0,
                    'satisfaction_score': 80.0,
                    'loyalty_score': 70.0,
                    'payment_score': 90.0,
                    'support_score': 85.0
                }
            )
            
            health.calculate_health_score()
            self.stdout.write('✓ Customer health score created and calculated')
            
            # Test Customer Preference Center
            preferences, created = CustomerPreferenceCenter.objects.get_or_create(
                customer=customer,
                defaults={
                    'email_marketing': True,
                    'sms_marketing': False,
                    'push_notifications': True,
                    'email_frequency': 'weekly'
                }
            )
            
            self.stdout.write('✓ Customer preference center created')
            
            # Test Customer Complaint Management
            complaint, created = CustomerComplaintManagement.objects.get_or_create(
                customer=customer,
                complaint_type='product_quality',
                subject='Test Complaint',
                defaults={
                    'description': 'This is a test complaint',
                    'severity': 'medium'
                }
            )
            
            self.stdout.write('✓ Customer complaint created')
            
            # Test Customer Churn Prediction
            prediction, created = CustomerChurnPrediction.objects.get_or_create(
                customer=customer,
                defaults={
                    'churn_probability': 0.3,
                    'churn_risk_level': 'medium',
                    'model_used': 'logistic_regression',
                    'model_version': '1.0',
                    'prediction_confidence': 0.85
                }
            )
            
            self.stdout.write('✓ Customer churn prediction created')
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Customer Management System Test Summary ==='))
            self.stdout.write(f'Customer: {customer.get_full_name()} ({customer.user.email})')
            self.stdout.write(f'Segments: {customer.segment_memberships.count()}')
            self.stdout.write(f'Support Tickets: {customer.support_tickets.count()}')
            self.stdout.write(f'Communications: {customer.communication_history.count()}')
            self.stdout.write(f'Complaints: {customer.complaints.count()}')
            self.stdout.write(f'Social Media Accounts: {customer.social_media_accounts.count()}')
            self.stdout.write(f'Win-back Campaigns: {customer.winback_campaigns.count()}')
            
            if hasattr(customer, 'admin_analytics'):
                self.stdout.write(f'Lifetime Value: ${customer.admin_analytics.lifetime_value}')
            
            if hasattr(customer, 'health_score'):
                self.stdout.write(f'Health Score: {customer.health_score.overall_score:.1f} ({customer.health_score.health_level})')
            
            if hasattr(customer, 'churn_prediction'):
                self.stdout.write(f'Churn Risk: {customer.churn_prediction.churn_probability:.1%} ({customer.churn_prediction.churn_risk_level})')
            
            self.stdout.write(self.style.SUCCESS('\n✅ All customer management system components tested successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing customer management system: {str(e)}'))
            raise e