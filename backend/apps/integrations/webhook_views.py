import json
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import Integration, IntegrationWebhook
from .services import WebhookService, process_webhook_async

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookReceiver(View):
    """Generic webhook receiver for all integrations"""
    
    def post(self, request, integration_id):
        try:
            # Get integration
            integration = Integration.objects.get(id=integration_id)
            
            # Get request data
            payload = request.body.decode('utf-8')
            headers = dict(request.META)
            
            # Extract signature from headers
            signature = self.get_signature_from_headers(headers, integration.provider.slug)
            
            if not signature:
                logger.warning(f"No signature found for webhook from {integration.provider.name}")
                return HttpResponseBadRequest("Missing signature")
            
            # Verify signature
            if not WebhookService.verify_webhook_signature(
                payload, signature, integration.webhook_secret, integration.provider.slug
            ):
                logger.warning(f"Invalid signature for webhook from {integration.provider.name}")
                return HttpResponseBadRequest("Invalid signature")
            
            # Parse payload
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON payload from {integration.provider.name}")
                return HttpResponseBadRequest("Invalid JSON")
            
            # Extract event type
            event_type = self.extract_event_type(payload_data, integration.provider.slug)
            
            # Process webhook asynchronously
            process_webhook_async.delay(
                str(integration.id),
                event_type,
                payload_data
            )
            
            return HttpResponse("OK")
            
        except Integration.DoesNotExist:
            logger.error(f"Integration not found: {integration_id}")
            return HttpResponseBadRequest("Integration not found")
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return HttpResponseBadRequest("Processing error")
    
    def get_signature_from_headers(self, headers, provider_slug):
        """Extract signature from request headers based on provider"""
        if provider_slug == 'stripe':
            return headers.get('HTTP_STRIPE_SIGNATURE')
        elif provider_slug == 'paypal':
            return headers.get('HTTP_PAYPAL_TRANSMISSION_SIG')
        elif provider_slug == 'shopify':
            return headers.get('HTTP_X_SHOPIFY_HMAC_SHA256')
        elif provider_slug == 'github':
            return headers.get('HTTP_X_HUB_SIGNATURE_256')
        elif provider_slug == 'mailchimp':
            return headers.get('HTTP_X_MAILCHIMP_SIGNATURE')
        
        return None
    
    def extract_event_type(self, payload, provider_slug):
        """Extract event type from payload based on provider"""
        if provider_slug == 'stripe':
            return payload.get('type', 'unknown')
        elif provider_slug == 'paypal':
            return payload.get('event_type', 'unknown')
        elif provider_slug == 'shopify':
            return payload.get('topic', 'unknown')
        elif provider_slug == 'github':
            return payload.get('action', 'unknown')
        elif provider_slug == 'mailchimp':
            return payload.get('type', 'unknown')
        
        return 'unknown'


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request, integration_id):
    """Stripe-specific webhook handler"""
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        signature = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not WebhookService.verify_stripe_signature(
            payload, signature, integration.webhook_secret
        ):
            return HttpResponseBadRequest("Invalid signature")
        
        payload_data = json.loads(payload)
        event_type = payload_data.get('type')
        
        # Process specific Stripe events
        if event_type == 'payment_intent.succeeded':
            # Handle successful payment
            pass
        elif event_type == 'payment_intent.payment_failed':
            # Handle failed payment
            pass
        elif event_type == 'customer.created':
            # Handle new customer
            pass
        
        process_webhook_async.delay(str(integration.id), event_type, payload_data)
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return HttpResponseBadRequest("Processing error")


@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request, integration_id):
    """PayPal-specific webhook handler"""
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        
        # PayPal signature verification
        signature = request.META.get('HTTP_PAYPAL_TRANSMISSION_SIG')
        cert_id = request.META.get('HTTP_PAYPAL_CERT_ID')
        transmission_id = request.META.get('HTTP_PAYPAL_TRANSMISSION_ID')
        timestamp = request.META.get('HTTP_PAYPAL_TRANSMISSION_TIME')
        
        # Verify PayPal webhook (implementation depends on PayPal SDK)
        payload_data = json.loads(payload)
        event_type = payload_data.get('event_type')
        
        process_webhook_async.delay(str(integration.id), event_type, payload_data)
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {str(e)}")
        return HttpResponseBadRequest("Processing error")


@csrf_exempt
@require_http_methods(["POST"])
def shopify_webhook(request, integration_id):
    """Shopify-specific webhook handler"""
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        signature = request.META.get('HTTP_X_SHOPIFY_HMAC_SHA256')
        topic = request.META.get('HTTP_X_SHOPIFY_TOPIC')
        
        if not WebhookService.verify_shopify_signature(
            payload, signature, integration.webhook_secret
        ):
            return HttpResponseBadRequest("Invalid signature")
        
        payload_data = json.loads(payload)
        
        # Process specific Shopify events
        if topic == 'orders/create':
            # Handle new order
            pass
        elif topic == 'orders/updated':
            # Handle order update
            pass
        elif topic == 'products/create':
            # Handle new product
            pass
        
        process_webhook_async.delay(str(integration.id), topic, payload_data)
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"Shopify webhook error: {str(e)}")
        return HttpResponseBadRequest("Processing error")


@csrf_exempt
@require_http_methods(["POST"])
def mailchimp_webhook(request, integration_id):
    """Mailchimp-specific webhook handler"""
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        
        # Mailchimp sends data as form-encoded
        data = request.POST.dict()
        event_type = data.get('type')
        
        process_webhook_async.delay(str(integration.id), event_type, data)
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"Mailchimp webhook error: {str(e)}")
        return HttpResponseBadRequest("Processing error")


@csrf_exempt
@require_http_methods(["POST"])
def github_webhook(request, integration_id):
    """GitHub-specific webhook handler"""
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
        event_type = request.META.get('HTTP_X_GITHUB_EVENT')
        
        # Verify GitHub signature
        import hmac
        import hashlib
        
        expected_signature = 'sha256=' + hmac.new(
            integration.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, signature):
            return HttpResponseBadRequest("Invalid signature")
        
        payload_data = json.loads(payload)
        
        process_webhook_async.delay(str(integration.id), event_type, payload_data)
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"GitHub webhook error: {str(e)}")
        return HttpResponseBadRequest("Processing error")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook_test(request, integration_id):
    """Test webhook endpoint for development"""
    if request.method == 'GET':
        return HttpResponse(f"Webhook endpoint for integration {integration_id} is active")
    
    try:
        integration = Integration.objects.get(id=integration_id)
        payload = request.body.decode('utf-8')
        
        # Log test webhook
        from .models import IntegrationLog
        IntegrationLog.objects.create(
            integration=integration,
            level='info',
            action_type='webhook',
            message='Test webhook received',
            details={'payload': payload, 'headers': dict(request.META)}
        )
        
        return HttpResponse("Test webhook received successfully")
        
    except Exception as e:
        logger.error(f"Test webhook error: {str(e)}")
        return HttpResponseBadRequest("Test webhook error")