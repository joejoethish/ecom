#!/usr/bin/env python3

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, '/workspaces/comprehensive-admin-panel/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.integrations.models import (
    IntegrationCategory, IntegrationProvider, Integration,
    IntegrationLog, IntegrationMapping, IntegrationWebhook,
    IntegrationSync, IntegrationTemplate
)
from apps.integrations.services import (
    IntegrationService, PaymentGatewayService, ShippingCarrierService,
    CRMService, AccountingService, MarketingService, WebhookService
)


class IntegrationModelTest(TestCase):
    """Test integration models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = IntegrationCategory.objects.create(
            name='Payment Gateways',
            category='payment',
            description='Payment processing integrations'
        )
        
        self.provider = IntegrationProvider.objects.create(
            name='Test Provider',
            slug='test-provider',
            category=self.category,
            description='Test integration provider',
            website_url='https://example.com',
            status='active'
        )
    
    def test_integration_category_creation(self):
        """Test integration category creation"""
        self.assertEqual(self.category.name, 'Payment Gateways')
        self.assertEqual(self.category.category, 'payment')
        self.assertTrue(self.category.is_active)
    
    def test_integration_provider_creation(self):
        """Test integration provider creation"""
        self.assertEqual(self.provider.name, 'Test Provider')
        self.assertEqual(self.provider.slug, 'test-provider')
        self.assertEqual(self.provider.category, self.category)
        self.assertEqual(self.provider.status, 'active')
    
    def test_integration_creation(self):
        """Test integration creation"""
        integration = Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            status='active',
            environment='development',
            configuration={'api_key': 'test_key'},
            created_by=self.user
        )
        
        self.assertEqual(integration.name, 'Test Integration')
        self.assertEqual(integration.provider, self.provider)
        self.assertEqual(integration.status, 'active')
        self.assertEqual(integration.environment, 'development')
        self.assertEqual(integration.created_by, self.user)
    
    def test_integration_log_creation(self):
        """Test integration log creation"""
        integration = Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            created_by=self.user
        )
        
        log = IntegrationLog.objects.create(
            integration=integration,
            level='info',
            action_type='api_call',
            message='Test log message',
            details={'test': 'data'}
        )
        
        self.assertEqual(log.integration, integration)
        self.assertEqual(log.level, 'info')
        self.assertEqual(log.action_type, 'api_call')
        self.assertEqual(log.message, 'Test log message')
    
    def test_integration_mapping_creation(self):
        """Test integration mapping creation"""
        integration = Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            created_by=self.user
        )
        
        mapping = IntegrationMapping.objects.create(
            integration=integration,
            mapping_type='field',
            source_field='email',
            target_field='customer_email',
            is_required=True
        )
        
        self.assertEqual(mapping.integration, integration)
        self.assertEqual(mapping.mapping_type, 'field')
        self.assertEqual(mapping.source_field, 'email')
        self.assertEqual(mapping.target_field, 'customer_email')
        self.assertTrue(mapping.is_required)


class IntegrationAPITest(APITestCase):
    """Test integration API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = IntegrationCategory.objects.create(
            name='Payment Gateways',
            category='payment',
            description='Payment processing integrations'
        )
        
        self.provider = IntegrationProvider.objects.create(
            name='Test Provider',
            slug='test-provider',
            category=self.category,
            description='Test integration provider',
            website_url='https://example.com',
            status='active'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_list_categories(self):
        """Test listing integration categories"""
        url = '/api/integrations/categories/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Payment Gateways')
    
    def test_list_providers(self):
        """Test listing integration providers"""
        url = '/api/integrations/providers/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Provider')
    
    def test_create_integration(self):
        """Test creating an integration"""
        url = '/api/integrations/integrations/'
        data = {
            'name': 'Test Integration',
            'provider': str(self.provider.id),
            'status': 'active',
            'environment': 'development',
            'configuration': {'api_key': 'test_key'}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Integration')
        self.assertEqual(response.data['status'], 'active')
    
    def test_list_integrations(self):
        """Test listing integrations"""
        Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            status='active',
            created_by=self.user
        )
        
        url = '/api/integrations/integrations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Integration')
    
    def test_integration_stats(self):
        """Test integration statistics endpoint"""
        Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            status='active',
            created_by=self.user
        )
        
        url = '/api/integrations/integrations/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_integrations', response.data)
        self.assertIn('active_integrations', response.data)
        self.assertEqual(response.data['total_integrations'], 1)
        self.assertEqual(response.data['active_integrations'], 1)
    
    def test_integration_test_connection(self):
        """Test integration connection test"""
        integration = Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            status='active',
            created_by=self.user
        )
        
        url = f'/api/integrations/integrations/{integration.id}/test_connection/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('task_id', response.data)
    
    def test_integration_sync_data(self):
        """Test integration data sync"""
        integration = Integration.objects.create(
            name='Test Integration',
            provider=self.provider,
            status='active',
            created_by=self.user
        )
        
        url = f'/api/integrations/integrations/{integration.id}/sync_data/'
        data = {'sync_type': 'manual'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('task_id', response.data)


class IntegrationServiceTest(TestCase):
    """Test integration services"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = IntegrationCategory.objects.create(
            name='Payment Gateways',
            category='payment',
            description='Payment processing integrations'
        )
        
        self.provider = IntegrationProvider.objects.create(
            name='Stripe',
            slug='stripe',
            category=self.category,
            description='Stripe payment processor',
            website_url='https://stripe.com',
            status='active'
        )
        
        self.integration = Integration.objects.create(
            name='Stripe Integration',
            provider=self.provider,
            status='active',
            configuration={
                'secret_key': 'sk_test_123',
                'publishable_key': 'pk_test_123'
            },
            created_by=self.user
        )
    
    def test_integration_service_initialization(self):
        """Test integration service initialization"""
        service = IntegrationService(self.integration)
        
        self.assertEqual(service.integration, self.integration)
        self.assertEqual(service.provider, self.provider)
        self.assertEqual(service.config, self.integration.configuration)
    
    def test_payment_gateway_service(self):
        """Test payment gateway service"""
        service = PaymentGatewayService(self.integration)
        
        self.assertIsInstance(service, PaymentGatewayService)
        self.assertEqual(service.integration, self.integration)
        
        # Test auth headers
        headers = service.get_auth_headers()
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Bearer'))
    
    def test_log_activity(self):
        """Test activity logging"""
        service = IntegrationService(self.integration)
        
        service.log_activity(
            level='info',
            action_type='test',
            message='Test log message',
            details={'test': 'data'}
        )
        
        log = IntegrationLog.objects.filter(integration=self.integration).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.level, 'info')
        self.assertEqual(log.action_type, 'test')
        self.assertEqual(log.message, 'Test log message')
    
    def test_webhook_signature_verification(self):
        """Test webhook signature verification"""
        payload = '{"test": "data"}'
        secret = 'test_secret'
        
        # Test Stripe signature verification
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        stripe_signature = f'sha256={signature}'
        
        result = WebhookService.verify_webhook_signature(
            payload, stripe_signature, secret, 'stripe'
        )
        
        self.assertTrue(result)


class IntegrationWebhookTest(TestCase):
    """Test webhook functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = IntegrationCategory.objects.create(
            name='Payment Gateways',
            category='payment',
            description='Payment processing integrations'
        )
        
        self.provider = IntegrationProvider.objects.create(
            name='Stripe',
            slug='stripe',
            category=self.category,
            description='Stripe payment processor',
            website_url='https://stripe.com',
            status='active'
        )
        
        self.integration = Integration.objects.create(
            name='Stripe Integration',
            provider=self.provider,
            status='active',
            webhook_secret='test_secret',
            created_by=self.user
        )
        
        self.client = Client()
    
    def test_webhook_receiver(self):
        """Test webhook receiver endpoint"""
        payload = json.dumps({'type': 'payment_intent.succeeded', 'data': {}})
        
        # Create signature
        import hmac
        import hashlib
        
        signature = hmac.new(
            'test_secret'.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = f'/api/integrations/webhooks/{self.integration.id}/'
        response = self.client.post(
            url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=f'sha256={signature}'
        )
        
        # Should return 200 OK for valid webhook
        self.assertEqual(response.status_code, 200)


def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Integration System Tests...")
    print("=" * 50)
    
    # Test Models
    print("\n📊 Testing Integration Models...")
    model_test = IntegrationModelTest()
    model_test.setUp()
    
    try:
        model_test.test_integration_category_creation()
        print("✅ Integration category creation test passed")
        
        model_test.test_integration_provider_creation()
        print("✅ Integration provider creation test passed")
        
        model_test.test_integration_creation()
        print("✅ Integration creation test passed")
        
        model_test.test_integration_log_creation()
        print("✅ Integration log creation test passed")
        
        model_test.test_integration_mapping_creation()
        print("✅ Integration mapping creation test passed")
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
    
    # Test Services
    print("\n🔧 Testing Integration Services...")
    service_test = IntegrationServiceTest()
    service_test.setUp()
    
    try:
        service_test.test_integration_service_initialization()
        print("✅ Integration service initialization test passed")
        
        service_test.test_payment_gateway_service()
        print("✅ Payment gateway service test passed")
        
        service_test.test_log_activity()
        print("✅ Activity logging test passed")
        
        service_test.test_webhook_signature_verification()
        print("✅ Webhook signature verification test passed")
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
    
    # Test Database Operations
    print("\n💾 Testing Database Operations...")
    try:
        # Test category creation
        category = IntegrationCategory.objects.create(
            name='Test Category',
            category='test',
            description='Test category'
        )
        print("✅ Category creation successful")
        
        # Test provider creation
        provider = IntegrationProvider.objects.create(
            name='Test Provider',
            slug='test-provider-db',
            category=category,
            description='Test provider',
            website_url='https://example.com'
        )
        print("✅ Provider creation successful")
        
        # Test integration creation
        user = User.objects.create_user(
            username='testuser_db',
            email='test_db@example.com',
            password='testpass123'
        )
        
        integration = Integration.objects.create(
            name='Test Integration DB',
            provider=provider,
            status='active',
            created_by=user
        )
        print("✅ Integration creation successful")
        
        # Test log creation
        log = IntegrationLog.objects.create(
            integration=integration,
            level='info',
            action_type='test',
            message='Database test log'
        )
        print("✅ Log creation successful")
        
        # Test sync record creation
        sync = IntegrationSync.objects.create(
            integration=integration,
            sync_type='manual',
            status='completed',
            records_processed=100,
            records_created=50,
            records_updated=30,
            records_failed=20
        )
        print("✅ Sync record creation successful")
        
        # Test template creation
        template = IntegrationTemplate.objects.create(
            name='Test Template',
            provider=provider,
            description='Test template',
            configuration_template={'test': 'config'},
            created_by=user
        )
        print("✅ Template creation successful")
        
    except Exception as e:
        print(f"❌ Database operation failed: {str(e)}")
    
    # Test Statistics
    print("\n📈 Testing Statistics...")
    try:
        total_integrations = Integration.objects.count()
        active_integrations = Integration.objects.filter(status='active').count()
        total_logs = IntegrationLog.objects.count()
        total_syncs = IntegrationSync.objects.count()
        
        print(f"✅ Total integrations: {total_integrations}")
        print(f"✅ Active integrations: {active_integrations}")
        print(f"✅ Total logs: {total_logs}")
        print(f"✅ Total syncs: {total_syncs}")
        
    except Exception as e:
        print(f"❌ Statistics test failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Integration System Tests Completed!")
    print("=" * 50)


if __name__ == '__main__':
    run_integration_tests()