from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.integrations.models import (
    IntegrationCategory, IntegrationProvider, IntegrationTemplate
)


class Command(BaseCommand):
    help = 'Set up default integration categories, providers, and templates'

    def handle(self, *args, **options):
        self.stdout.write('Setting up integration defaults...')
        
        # Create categories
        self.create_categories()
        
        # Create providers
        self.create_providers()
        
        # Create templates
        self.create_templates()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up integration defaults')
        )

    def create_categories(self):
        """Create integration categories"""
        categories = [
            {
                'name': 'Payment Gateways',
                'category': 'payment',
                'description': 'Payment processing and gateway integrations',
                'icon': 'credit-card'
            },
            {
                'name': 'Shipping Carriers',
                'category': 'shipping',
                'description': 'Shipping and logistics provider integrations',
                'icon': 'truck'
            },
            {
                'name': 'CRM Systems',
                'category': 'crm',
                'description': 'Customer relationship management integrations',
                'icon': 'users'
            },
            {
                'name': 'Accounting Systems',
                'category': 'accounting',
                'description': 'Financial and accounting software integrations',
                'icon': 'calculator'
            },
            {
                'name': 'Marketing Platforms',
                'category': 'marketing',
                'description': 'Email marketing and campaign management',
                'icon': 'mail'
            },
            {
                'name': 'Social Media',
                'category': 'social',
                'description': 'Social media platform integrations',
                'icon': 'share-2'
            },
            {
                'name': 'Analytics Platforms',
                'category': 'analytics',
                'description': 'Web analytics and tracking integrations',
                'icon': 'bar-chart'
            },
            {
                'name': 'Inventory Management',
                'category': 'inventory',
                'description': 'Inventory and warehouse management systems',
                'icon': 'package'
            },
        ]
        
        for cat_data in categories:
            category, created = IntegrationCategory.objects.get_or_create(
                category=cat_data['category'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_providers(self):
        """Create integration providers"""
        providers = [
            # Payment Gateways
            {
                'name': 'Stripe',
                'slug': 'stripe',
                'category': 'payment',
                'description': 'Online payment processing platform',
                'website_url': 'https://stripe.com',
                'documentation_url': 'https://stripe.com/docs',
                'logo_url': 'https://stripe.com/img/v3/home/social.png',
                'supported_features': ['payments', 'subscriptions', 'webhooks'],
                'is_popular': True
            },
            {
                'name': 'PayPal',
                'slug': 'paypal',
                'category': 'payment',
                'description': 'Digital payment platform',
                'website_url': 'https://paypal.com',
                'documentation_url': 'https://developer.paypal.com',
                'supported_features': ['payments', 'express_checkout'],
                'is_popular': True
            },
            # Shipping Carriers
            {
                'name': 'FedEx',
                'slug': 'fedex',
                'category': 'shipping',
                'description': 'Global shipping and logistics',
                'website_url': 'https://fedex.com',
                'documentation_url': 'https://developer.fedex.com',
                'supported_features': ['shipping', 'tracking', 'rates']
            },
            {
                'name': 'UPS',
                'slug': 'ups',
                'category': 'shipping',
                'description': 'Package delivery and supply chain',
                'website_url': 'https://ups.com',
                'documentation_url': 'https://developer.ups.com',
                'supported_features': ['shipping', 'tracking', 'rates']
            },
            # CRM Systems
            {
                'name': 'Salesforce',
                'slug': 'salesforce',
                'category': 'crm',
                'description': 'Customer relationship management platform',
                'website_url': 'https://salesforce.com',
                'documentation_url': 'https://developer.salesforce.com',
                'supported_features': ['contacts', 'leads', 'opportunities'],
                'is_popular': True
            },
            {
                'name': 'HubSpot',
                'slug': 'hubspot',
                'category': 'crm',
                'description': 'Inbound marketing and CRM platform',
                'website_url': 'https://hubspot.com',
                'documentation_url': 'https://developers.hubspot.com',
                'supported_features': ['contacts', 'deals', 'marketing'],
                'is_popular': True
            },
        ]
        
        for provider_data in providers:
            category = IntegrationCategory.objects.get(
                category=provider_data.pop('category')
            )
            provider_data['category'] = category
            
            provider, created = IntegrationProvider.objects.get_or_create(
                slug=provider_data['slug'],
                defaults=provider_data
            )
            if created:
                self.stdout.write(f'Created provider: {provider.name}')

    def create_templates(self):
        """Create integration templates"""
        # Get admin user for template creation
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write('No admin user found, skipping template creation')
            return
        
        templates = [
            {
                'name': 'Stripe Standard Setup',
                'provider_slug': 'stripe',
                'description': 'Standard Stripe payment integration',
                'configuration_template': {
                    'publishable_key': '',
                    'secret_key': '',
                    'webhook_endpoint_secret': '',
                    'currency': 'usd'
                },
                'mapping_template': {
                    'mappings': [
                        {
                            'mapping_type': 'field',
                            'source_field': 'customer_email',
                            'target_field': 'email',
                            'is_required': True
                        }
                    ]
                },
                'webhook_template': {
                    'webhooks': [
                        {
                            'event_type': 'payment.completed',
                            'is_active': True
                        }
                    ]
                },
                'is_official': True
            }
        ]
        
        for template_data in templates:
            provider = IntegrationProvider.objects.get(
                slug=template_data.pop('provider_slug')
            )
            template_data['provider'] = provider
            template_data['created_by'] = admin_user
            
            template, created = IntegrationTemplate.objects.get_or_create(
                name=template_data['name'],
                provider=provider,
                defaults=template_data
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')