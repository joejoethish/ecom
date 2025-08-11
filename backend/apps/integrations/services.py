import requests
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from celery import shared_task
from .models import (
    Integration, IntegrationLog, IntegrationSync,
    IntegrationWebhook, IntegrationMapping, IntegrationProvider
)


class IntegrationService:
    """Base service for all integrations"""
    
    def __init__(self, integration: Integration):
        self.integration = integration
        self.provider = integration.provider
        self.config = integration.configuration
    
    def log_activity(self, level: str, action_type: str, message: str, 
                    details: Dict = None, request_data: Dict = None, 
                    response_data: Dict = None, execution_time: float = None,
                    status_code: int = None):
        """Log integration activity"""
        IntegrationLog.objects.create(
            integration=self.integration,
            level=level,
            action_type=action_type,
            message=message,
            details=details or {},
            request_data=request_data,
            response_data=response_data,
            execution_time=execution_time,
            status_code=status_code
        )
    
    def make_api_request(self, method: str, url: str, headers: Dict = None,
                        data: Dict = None, params: Dict = None) -> Tuple[bool, Dict]:
        """Make API request with logging"""
        start_time = time.time()
        
        try:
            headers = headers or {}
            headers.update(self.get_auth_headers())
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            self.log_activity(
                level='info' if response.ok else 'error',
                action_type='api_call',
                message=f"{method} {url} - {response.status_code}",
                request_data={'method': method, 'url': url, 'data': data},
                response_data=response.json() if response.content else {},
                execution_time=execution_time,
                status_code=response.status_code
            )
            
            if response.ok:
                self.integration.error_count = 0
                self.integration.save(update_fields=['error_count'])
                return True, response.json() if response.content else {}
            else:
                self.integration.error_count += 1
                self.integration.last_error = f"API Error: {response.status_code} - {response.text}"
                self.integration.save(update_fields=['error_count', 'last_error'])
                return False, {'error': response.text, 'status_code': response.status_code}
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.integration.error_count += 1
            self.integration.last_error = str(e)
            self.integration.save(update_fields=['error_count', 'last_error'])
            
            self.log_activity(
                level='error',
                action_type='api_call',
                message=f"API Request Failed: {str(e)}",
                details={'exception': str(e)},
                execution_time=execution_time
            )
            
            return False, {'error': str(e)}
    
    def get_auth_headers(self) -> Dict:
        """Get authentication headers - override in subclasses"""
        return {}
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test integration connection - override in subclasses"""
        return True, "Connection test not implemented"
    
    def sync_data(self, sync_type: str = 'incremental') -> Dict:
        """Sync data - override in subclasses"""
        return {'status': 'not_implemented', 'message': 'Sync not implemented'}


class PaymentGatewayService(IntegrationService):
    """Service for payment gateway integrations"""
    
    def get_auth_headers(self) -> Dict:
        if self.provider.slug == 'stripe':
            return {'Authorization': f"Bearer {self.config.get('secret_key')}"}
        elif self.provider.slug == 'paypal':
            return self.get_paypal_auth_headers()
        elif self.provider.slug == 'razorpay':
            return self.get_razorpay_auth_headers()
        return {}
    
    def get_paypal_auth_headers(self) -> Dict:
        # PayPal OAuth implementation
        token = self.get_paypal_access_token()
        return {'Authorization': f"Bearer {token}"}
    
    def get_razorpay_auth_headers(self) -> Dict:
        # Razorpay basic auth implementation
        import base64
        key_id = self.config.get('key_id')
        key_secret = self.config.get('key_secret')
        credentials = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
        return {'Authorization': f"Basic {credentials}"}
    
    def get_paypal_access_token(self) -> str:
        # Implementation for PayPal OAuth token
        cache_key = f"paypal_token_{self.integration.id}"
        token = cache.get(cache_key)
        
        if not token:
            # Get new token from PayPal
            client_id = self.config.get('client_id')
            client_secret = self.config.get('client_secret')
            # ... PayPal token request implementation
            pass
        
        return token
    
    def create_payment(self, amount: float, currency: str, customer_data: Dict) -> Tuple[bool, Dict]:
        """Create payment"""
        if self.provider.slug == 'stripe':
            return self.create_stripe_payment(amount, currency, customer_data)
        elif self.provider.slug == 'paypal':
            return self.create_paypal_payment(amount, currency, customer_data)
        elif self.provider.slug == 'razorpay':
            return self.create_razorpay_payment(amount, currency, customer_data)
        
        return False, {'error': 'Payment method not supported'}
    
    def create_stripe_payment(self, amount: float, currency: str, customer_data: Dict) -> Tuple[bool, Dict]:
        """Create Stripe payment intent"""
        url = "https://api.stripe.com/v1/payment_intents"
        data = {
            'amount': int(amount * 100),  # Stripe uses cents
            'currency': currency.lower(),
            'customer': customer_data.get('stripe_customer_id'),
            'metadata': customer_data.get('metadata', {})
        }
        
        return self.make_api_request('POST', url, data=data)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test payment gateway connection"""
        if self.provider.slug == 'stripe':
            success, response = self.make_api_request('GET', 'https://api.stripe.com/v1/account')
            return success, "Stripe connection successful" if success else f"Stripe connection failed: {response.get('error')}"
        
        return True, "Connection test not implemented for this provider"


class ShippingCarrierService(IntegrationService):
    """Service for shipping carrier integrations"""
    
    def get_auth_headers(self) -> Dict:
        if self.provider.slug == 'fedex':
            return {'Authorization': f"Bearer {self.get_fedex_token()}"}
        elif self.provider.slug == 'ups':
            return self.get_ups_auth_headers()
        elif self.provider.slug == 'dhl':
            return {'DHL-API-Key': self.config.get('api_key')}
        return {}
    
    def get_fedex_token(self) -> str:
        # FedEx OAuth implementation
        cache_key = f"fedex_token_{self.integration.id}"
        token = cache.get(cache_key)
        
        if not token:
            # Get new token from FedEx
            pass
        
        return token
    
    def get_ups_auth_headers(self) -> Dict:
        # UPS authentication
        return {
            'Username': self.config.get('username'),
            'Password': self.config.get('password'),
            'AccessLicenseNumber': self.config.get('access_key')
        }
    
    def create_shipment(self, shipment_data: Dict) -> Tuple[bool, Dict]:
        """Create shipment"""
        if self.provider.slug == 'fedex':
            return self.create_fedex_shipment(shipment_data)
        elif self.provider.slug == 'ups':
            return self.create_ups_shipment(shipment_data)
        elif self.provider.slug == 'dhl':
            return self.create_dhl_shipment(shipment_data)
        
        return False, {'error': 'Shipping carrier not supported'}
    
    def track_shipment(self, tracking_number: str) -> Tuple[bool, Dict]:
        """Track shipment"""
        if self.provider.slug == 'fedex':
            return self.track_fedex_shipment(tracking_number)
        elif self.provider.slug == 'ups':
            return self.track_ups_shipment(tracking_number)
        elif self.provider.slug == 'dhl':
            return self.track_dhl_shipment(tracking_number)
        
        return False, {'error': 'Tracking not supported for this carrier'}


class CRMService(IntegrationService):
    """Service for CRM integrations"""
    
    def get_auth_headers(self) -> Dict:
        if self.provider.slug == 'salesforce':
            return {'Authorization': f"Bearer {self.get_salesforce_token()}"}
        elif self.provider.slug == 'hubspot':
            return {'Authorization': f"Bearer {self.config.get('access_token')}"}
        return {}
    
    def sync_customers(self) -> Dict:
        """Sync customers to CRM"""
        if self.provider.slug == 'salesforce':
            return self.sync_salesforce_customers()
        elif self.provider.slug == 'hubspot':
            return self.sync_hubspot_customers()
        
        return {'status': 'not_supported', 'message': 'CRM sync not supported'}
    
    def create_lead(self, lead_data: Dict) -> Tuple[bool, Dict]:
        """Create lead in CRM"""
        if self.provider.slug == 'salesforce':
            return self.create_salesforce_lead(lead_data)
        elif self.provider.slug == 'hubspot':
            return self.create_hubspot_contact(lead_data)
        
        return False, {'error': 'Lead creation not supported'}


class AccountingService(IntegrationService):
    """Service for accounting system integrations"""
    
    def get_auth_headers(self) -> Dict:
        if self.provider.slug == 'quickbooks':
            return {'Authorization': f"Bearer {self.config.get('access_token')}"}
        elif self.provider.slug == 'xero':
            return {'Authorization': f"Bearer {self.config.get('access_token')}"}
        return {}
    
    def sync_invoices(self) -> Dict:
        """Sync invoices to accounting system"""
        if self.provider.slug == 'quickbooks':
            return self.sync_quickbooks_invoices()
        elif self.provider.slug == 'xero':
            return self.sync_xero_invoices()
        
        return {'status': 'not_supported', 'message': 'Invoice sync not supported'}
    
    def create_invoice(self, invoice_data: Dict) -> Tuple[bool, Dict]:
        """Create invoice in accounting system"""
        if self.provider.slug == 'quickbooks':
            return self.create_quickbooks_invoice(invoice_data)
        elif self.provider.slug == 'xero':
            return self.create_xero_invoice(invoice_data)
        
        return False, {'error': 'Invoice creation not supported'}


class MarketingService(IntegrationService):
    """Service for marketing platform integrations"""
    
    def get_auth_headers(self) -> Dict:
        if self.provider.slug == 'mailchimp':
            return {'Authorization': f"apikey {self.config.get('api_key')}"}
        elif self.provider.slug == 'constant_contact':
            return {'Authorization': f"Bearer {self.config.get('access_token')}"}
        return {}
    
    def sync_subscribers(self) -> Dict:
        """Sync subscribers to marketing platform"""
        if self.provider.slug == 'mailchimp':
            return self.sync_mailchimp_subscribers()
        elif self.provider.slug == 'constant_contact':
            return self.sync_constant_contact_subscribers()
        
        return {'status': 'not_supported', 'message': 'Subscriber sync not supported'}


class WebhookService:
    """Service for handling webhooks"""
    
    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str, 
                                provider: str) -> bool:
        """Verify webhook signature"""
        if provider == 'stripe':
            return WebhookService.verify_stripe_signature(payload, signature, secret)
        elif provider == 'paypal':
            return WebhookService.verify_paypal_signature(payload, signature, secret)
        elif provider == 'shopify':
            return WebhookService.verify_shopify_signature(payload, signature, secret)
        
        return False
    
    @staticmethod
    def verify_stripe_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception:
            return False
    
    @staticmethod
    def verify_paypal_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify PayPal webhook signature"""
        # PayPal signature verification implementation
        return True  # Placeholder
    
    @staticmethod
    def verify_shopify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify Shopify webhook signature"""
        try:
            expected_signature = base64.b64encode(
                hmac.new(
                    secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    @staticmethod
    def process_webhook(integration: Integration, event_type: str, payload: Dict) -> bool:
        """Process incoming webhook"""
        try:
            # Log webhook receipt
            IntegrationLog.objects.create(
                integration=integration,
                level='info',
                action_type='webhook',
                message=f"Webhook received: {event_type}",
                details={'event_type': event_type, 'payload': payload}
            )
            
            # Process based on event type
            if event_type.startswith('payment.'):
                return WebhookService.process_payment_webhook(integration, event_type, payload)
            elif event_type.startswith('order.'):
                return WebhookService.process_order_webhook(integration, event_type, payload)
            elif event_type.startswith('inventory.'):
                return WebhookService.process_inventory_webhook(integration, event_type, payload)
            
            return True
            
        except Exception as e:
            IntegrationLog.objects.create(
                integration=integration,
                level='error',
                action_type='webhook',
                message=f"Webhook processing failed: {str(e)}",
                details={'event_type': event_type, 'error': str(e)}
            )
            return False
    
    @staticmethod
    def process_payment_webhook(integration: Integration, event_type: str, payload: Dict) -> bool:
        """Process payment-related webhooks"""
        # Implementation for payment webhook processing
        return True
    
    @staticmethod
    def process_order_webhook(integration: Integration, event_type: str, payload: Dict) -> bool:
        """Process order-related webhooks"""
        # Implementation for order webhook processing
        return True
    
    @staticmethod
    def process_inventory_webhook(integration: Integration, event_type: str, payload: Dict) -> bool:
        """Process inventory-related webhooks"""
        # Implementation for inventory webhook processing
        return True


class IntegrationFactory:
    """Factory for creating integration services"""
    
    SERVICE_MAP = {
        'payment': PaymentGatewayService,
        'shipping': ShippingCarrierService,
        'crm': CRMService,
        'accounting': AccountingService,
        'marketing': MarketingService,
    }
    
    @classmethod
    def create_service(cls, integration: Integration) -> IntegrationService:
        """Create appropriate service for integration"""
        category = integration.provider.category.category
        service_class = cls.SERVICE_MAP.get(category, IntegrationService)
        return service_class(integration)


# Celery tasks for background processing
@shared_task
def sync_integration_data(integration_id: str, sync_type: str = 'incremental'):
    """Background task for syncing integration data"""
    try:
        integration = Integration.objects.get(id=integration_id)
        service = IntegrationFactory.create_service(integration)
        
        # Create sync record
        sync_record = IntegrationSync.objects.create(
            integration=integration,
            sync_type=sync_type,
            status='running',
            started_at=timezone.now()
        )
        
        # Perform sync
        result = service.sync_data(sync_type)
        
        # Update sync record
        sync_record.status = 'completed' if result.get('success') else 'failed'
        sync_record.completed_at = timezone.now()
        sync_record.records_processed = result.get('records_processed', 0)
        sync_record.records_created = result.get('records_created', 0)
        sync_record.records_updated = result.get('records_updated', 0)
        sync_record.records_failed = result.get('records_failed', 0)
        sync_record.error_message = result.get('error_message', '')
        sync_record.save()
        
        # Update integration last sync time
        integration.last_sync_at = timezone.now()
        integration.save(update_fields=['last_sync_at'])
        
        return result
        
    except Exception as e:
        # Update sync record with error
        if 'sync_record' in locals():
            sync_record.status = 'failed'
            sync_record.completed_at = timezone.now()
            sync_record.error_message = str(e)
            sync_record.save()
        
        raise e


@shared_task
def test_integration_connection(integration_id: str):
    """Background task for testing integration connection"""
    try:
        integration = Integration.objects.get(id=integration_id)
        service = IntegrationFactory.create_service(integration)
        
        success, message = service.test_connection()
        
        # Log test result
        service.log_activity(
            level='info' if success else 'error',
            action_type='test',
            message=f"Connection test: {message}",
            details={'success': success}
        )
        
        return {'success': success, 'message': message}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}


@shared_task
def process_webhook_async(integration_id: str, event_type: str, payload: dict):
    """Background task for processing webhooks"""
    try:
        integration = Integration.objects.get(id=integration_id)
        return WebhookService.process_webhook(integration, event_type, payload)
    except Exception as e:
        return False