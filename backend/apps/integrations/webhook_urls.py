from django.urls import path
from . import webhook_views

urlpatterns = [
    # Generic webhook receiver
    path('<uuid:integration_id>/', webhook_views.WebhookReceiver.as_view(), name='webhook_receiver'),
    
    # Provider-specific webhook endpoints
    path('stripe/<uuid:integration_id>/', webhook_views.stripe_webhook, name='stripe_webhook'),
    path('paypal/<uuid:integration_id>/', webhook_views.paypal_webhook, name='paypal_webhook'),
    path('shopify/<uuid:integration_id>/', webhook_views.shopify_webhook, name='shopify_webhook'),
    path('mailchimp/<uuid:integration_id>/', webhook_views.mailchimp_webhook, name='mailchimp_webhook'),
    path('github/<uuid:integration_id>/', webhook_views.github_webhook, name='github_webhook'),
    
    # Test webhook endpoint
    path('test/<uuid:integration_id>/', webhook_views.webhook_test, name='webhook_test'),
]