#!/usr/bin/env python3

import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, '/workspaces/comprehensive-admin-panel/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def test_integration_models():
    """Test integration models can be imported"""
    try:
        from apps.integrations.models import (
            IntegrationCategory, IntegrationProvider, Integration,
            IntegrationLog, IntegrationMapping, IntegrationWebhook,
            IntegrationSync, IntegrationTemplate
        )
        print("✅ Integration models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Integration models import failed: {e}")
        return False

def test_integration_services():
    """Test integration services can be imported"""
    try:
        from apps.integrations.services import (
            IntegrationService, PaymentGatewayService, ShippingCarrierService,
            CRMService, AccountingService, MarketingService, WebhookService,
            IntegrationFactory
        )
        print("✅ Integration services imported successfully")
        return True
    except Exception as e:
        print(f"❌ Integration services import failed: {e}")
        return False

def test_integration_serializers():
    """Test integration serializers can be imported"""
    try:
        from apps.integrations.serializers import (
            IntegrationCategorySerializer, IntegrationProviderSerializer,
            IntegrationSerializer, IntegrationLogSerializer,
            IntegrationMappingSerializer, IntegrationWebhookSerializer,
            IntegrationSyncSerializer, IntegrationTemplateSerializer
        )
        print("✅ Integration serializers imported successfully")
        return True
    except Exception as e:
        print(f"❌ Integration serializers import failed: {e}")
        return False

def test_integration_views():
    """Test integration views can be imported"""
    try:
        from apps.integrations.views import (
            IntegrationCategoryViewSet, IntegrationProviderViewSet,
            IntegrationViewSet, IntegrationTemplateViewSet,
            IntegrationLogViewSet, IntegrationSyncViewSet
        )
        print("✅ Integration views imported successfully")
        return True
    except Exception as e:
        print(f"❌ Integration views import failed: {e}")
        return False

def test_webhook_views():
    """Test webhook views can be imported"""
    try:
        from apps.integrations.webhook_views import (
            WebhookReceiver, stripe_webhook, paypal_webhook,
            shopify_webhook, mailchimp_webhook, github_webhook
        )
        print("✅ Webhook views imported successfully")
        return True
    except Exception as e:
        print(f"❌ Webhook views import failed: {e}")
        return False

def test_integration_admin():
    """Test integration admin can be imported"""
    try:
        from apps.integrations.admin import (
            IntegrationCategoryAdmin, IntegrationProviderAdmin,
            IntegrationAdmin, IntegrationLogAdmin
        )
        print("✅ Integration admin imported successfully")
        return True
    except Exception as e:
        print(f"❌ Integration admin import failed: {e}")
        return False

def test_service_functionality():
    """Test basic service functionality"""
    try:
        from apps.integrations.services import WebhookService
        
        # Test webhook signature verification
        payload = '{"test": "data"}'
        secret = 'test_secret'
        
        # This should return False for invalid signature
        result = WebhookService.verify_webhook_signature(
            payload, 'invalid_signature', secret, 'stripe'
        )
        
        if result == False:
            print("✅ Webhook signature verification working")
            return True
        else:
            print("❌ Webhook signature verification not working properly")
            return False
            
    except Exception as e:
        print(f"❌ Service functionality test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Integration System Tests...")
    print("=" * 50)
    
    tests = [
        test_integration_models,
        test_integration_services,
        test_integration_serializers,
        test_integration_views,
        test_webhook_views,
        test_integration_admin,
        test_service_functionality,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎉 Integration System Tests Completed!")
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Integration system is working correctly.")
    else:
        print(f"❌ {total - passed} tests failed. Please check the errors above.")
    
    print("=" * 50)
    
    return passed == total

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)