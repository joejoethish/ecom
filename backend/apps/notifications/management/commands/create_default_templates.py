from django.core.management.base import BaseCommand
from apps.notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create default notification templates'
    
    def handle(self, *args, **options):
        templates = [
            # Order Confirmation Templates
            {
                'name': 'Order Confirmation Email',
                'template_type': 'ORDER_CONFIRMATION',
                'channel': 'EMAIL',
                'subject_template': 'Order Confirmation - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Thank you for your order! Your order {{ order_number }} has been confirmed.

Order Details:
- Order Number: {{ order_number }}
- Order Total: ${{ order_total }}
- Order Date: {{ order_date }}

You can track your order at: {{ tracking_url }}

Thank you for shopping with us!

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Order Confirmation</h2>
<p>Hello {{ user_name }},</p>
<p>Thank you for your order! Your order <strong>{{ order_number }}</strong> has been confirmed.</p>
<h3>Order Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Order Total: ${{ order_total }}</li>
<li>Order Date: {{ order_date }}</li>
</ul>
<p><a href="{{ tracking_url }}">Track your order</a></p>
<p>Thank you for shopping with us!</p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            {
                'name': 'Order Confirmation SMS',
                'template_type': 'ORDER_CONFIRMATION',
                'channel': 'SMS',
                'subject_template': 'Order Confirmed',
                'body_template': 'Order {{ order_number }} confirmed! Total: ${{ order_total }}. Track at {{ tracking_url }}'
            },
            {
                'name': 'Order Confirmation In-App',
                'template_type': 'ORDER_CONFIRMATION',
                'channel': 'IN_APP',
                'subject_template': 'Order Confirmed',
                'body_template': 'Your order {{ order_number }} has been confirmed. Total: ${{ order_total }}'
            },
            
            # Order Status Update Templates
            {
                'name': 'Order Status Update Email',
                'template_type': 'ORDER_STATUS_UPDATE',
                'channel': 'EMAIL',
                'subject_template': 'Order Update - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Your order {{ order_number }} status has been updated to: {{ order_status }}

Order Details:
- Order Number: {{ order_number }}
- Current Status: {{ order_status }}
- Order Total: ${{ order_total }}

You can track your order at: {{ tracking_url }}

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Order Status Update</h2>
<p>Hello {{ user_name }},</p>
<p>Your order <strong>{{ order_number }}</strong> status has been updated to: <strong>{{ order_status }}</strong></p>
<h3>Order Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Current Status: {{ order_status }}</li>
<li>Order Total: ${{ order_total }}</li>
</ul>
<p><a href="{{ tracking_url }}">Track your order</a></p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            {
                'name': 'Order Status Update SMS',
                'template_type': 'ORDER_STATUS_UPDATE',
                'channel': 'SMS',
                'subject_template': 'Order Update',
                'body_template': 'Order {{ order_number }} is now {{ order_status }}. Track at {{ tracking_url }}'
            },
            
            # Payment Templates
            {
                'name': 'Payment Success Email',
                'template_type': 'PAYMENT_SUCCESS',
                'channel': 'EMAIL',
                'subject_template': 'Payment Successful - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Your payment for order {{ order_number }} has been processed successfully.

Payment Details:
- Order Number: {{ order_number }}
- Amount: ${{ payment_amount }}
- Payment Method: {{ payment_method }}
- Transaction ID: {{ transaction_id }}

Thank you for your payment!

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Payment Successful</h2>
<p>Hello {{ user_name }},</p>
<p>Your payment for order <strong>{{ order_number }}</strong> has been processed successfully.</p>
<h3>Payment Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Amount: ${{ payment_amount }}</li>
<li>Payment Method: {{ payment_method }}</li>
<li>Transaction ID: {{ transaction_id }}</li>
</ul>
<p>Thank you for your payment!</p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            {
                'name': 'Payment Failed Email',
                'template_type': 'PAYMENT_FAILED',
                'channel': 'EMAIL',
                'subject_template': 'Payment Failed - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Unfortunately, your payment for order {{ order_number }} could not be processed.

Payment Details:
- Order Number: {{ order_number }}
- Amount: ${{ payment_amount }}
- Payment Method: {{ payment_method }}

Please try again or contact our support team.

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Payment Failed</h2>
<p>Hello {{ user_name }},</p>
<p>Unfortunately, your payment for order <strong>{{ order_number }}</strong> could not be processed.</p>
<h3>Payment Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Amount: ${{ payment_amount }}</li>
<li>Payment Method: {{ payment_method }}</li>
</ul>
<p>Please try again or contact our support team.</p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            
            # Shipping Templates
            {
                'name': 'Shipping Update Email',
                'template_type': 'SHIPPING_UPDATE',
                'channel': 'EMAIL',
                'subject_template': 'Shipping Update - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Your order {{ order_number }} shipping status has been updated.

Shipping Details:
- Order Number: {{ order_number }}
- Tracking Number: {{ tracking_number }}
- Status: {{ shipping_status }}
- Estimated Delivery: {{ estimated_delivery }}

Track your shipment at: {{ tracking_url }}

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Shipping Update</h2>
<p>Hello {{ user_name }},</p>
<p>Your order <strong>{{ order_number }}</strong> shipping status has been updated.</p>
<h3>Shipping Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Tracking Number: {{ tracking_number }}</li>
<li>Status: {{ shipping_status }}</li>
<li>Estimated Delivery: {{ estimated_delivery }}</li>
</ul>
<p><a href="{{ tracking_url }}">Track your shipment</a></p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            {
                'name': 'Delivery Confirmation Email',
                'template_type': 'DELIVERY_CONFIRMATION',
                'channel': 'EMAIL',
                'subject_template': 'Order Delivered - {{ order_number }}',
                'body_template': '''Hello {{ user_name }},

Great news! Your order {{ order_number }} has been delivered successfully.

Order Details:
- Order Number: {{ order_number }}
- Tracking Number: {{ tracking_number }}
- Delivered on: {{ estimated_delivery }}

We hope you enjoy your purchase! Please consider leaving a review.

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Order Delivered</h2>
<p>Hello {{ user_name }},</p>
<p>Great news! Your order <strong>{{ order_number }}</strong> has been delivered successfully.</p>
<h3>Order Details:</h3>
<ul>
<li>Order Number: {{ order_number }}</li>
<li>Tracking Number: {{ tracking_number }}</li>
<li>Delivered on: {{ estimated_delivery }}</li>
</ul>
<p>We hope you enjoy your purchase! Please consider leaving a review.</p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            
            # Welcome Template
            {
                'name': 'Welcome Email',
                'template_type': 'WELCOME',
                'channel': 'EMAIL',
                'subject_template': 'Welcome to {{ platform_name }}!',
                'body_template': '''Hello {{ user_name }},

Welcome to {{ platform_name }}! We're excited to have you join our community.

Your account has been created successfully with email: {{ user_email }}

Start exploring our products and enjoy shopping with us!

If you have any questions, feel free to contact us at {{ support_email }}

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Welcome to {{ platform_name }}!</h2>
<p>Hello {{ user_name }},</p>
<p>Welcome to <strong>{{ platform_name }}</strong>! We're excited to have you join our community.</p>
<p>Your account has been created successfully with email: <strong>{{ user_email }}</strong></p>
<p>Start exploring our products and enjoy shopping with us!</p>
<p>If you have any questions, feel free to contact us at <a href="mailto:{{ support_email }}">{{ support_email }}</a></p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            
            # Inventory Alert Template
            {
                'name': 'Low Inventory Alert Email',
                'template_type': 'INVENTORY_LOW',
                'channel': 'EMAIL',
                'subject_template': 'Low Inventory Alert - {{ product_name }}',
                'body_template': '''Hello,

This is an automated alert for low inventory levels.

Product Details:
- Product Name: {{ product_name }}
- SKU: {{ product_sku }}
- Current Stock: {{ current_stock }}
- Minimum Stock Level: {{ minimum_stock }}
- Reorder Point: {{ reorder_point }}

Please restock this product soon to avoid stockouts.

View product: {{ product_url }}

Best regards,
Inventory Management System''',
                'html_template': '''<h2>Low Inventory Alert</h2>
<p>This is an automated alert for low inventory levels.</p>
<h3>Product Details:</h3>
<ul>
<li>Product Name: {{ product_name }}</li>
<li>SKU: {{ product_sku }}</li>
<li>Current Stock: {{ current_stock }}</li>
<li>Minimum Stock Level: {{ minimum_stock }}</li>
<li>Reorder Point: {{ reorder_point }}</li>
</ul>
<p>Please restock this product soon to avoid stockouts.</p>
<p><a href="{{ product_url }}">View product</a></p>
<p>Best regards,<br>Inventory Management System</p>'''
            },
            
            # Seller Templates
            {
                'name': 'Seller Verification Email',
                'template_type': 'SELLER_VERIFICATION',
                'channel': 'EMAIL',
                'subject_template': 'Seller Account Verified',
                'body_template': '''Hello {{ seller_name }},

Congratulations! Your seller account has been verified successfully.

Verification Details:
- Business Name: {{ seller_name }}
- Verification Date: {{ verification_date }}

You can now start selling on our platform. Access your seller dashboard at: {{ dashboard_url }}

If you need any assistance, contact us at {{ support_email }}

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Seller Account Verified</h2>
<p>Hello {{ seller_name }},</p>
<p>Congratulations! Your seller account has been verified successfully.</p>
<h3>Verification Details:</h3>
<ul>
<li>Business Name: {{ seller_name }}</li>
<li>Verification Date: {{ verification_date }}</li>
</ul>
<p>You can now start selling on our platform. <a href="{{ dashboard_url }}">Access your seller dashboard</a></p>
<p>If you need any assistance, contact us at <a href="mailto:{{ support_email }}">{{ support_email }}</a></p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
            {
                'name': 'Seller Payout Email',
                'template_type': 'SELLER_PAYOUT',
                'channel': 'EMAIL',
                'subject_template': 'Payout Processed - ${{ payout_amount }}',
                'body_template': '''Hello {{ seller_name }},

Your payout has been processed successfully.

Payout Details:
- Amount: ${{ payout_amount }}
- Payout Date: {{ payout_date }}
- Transaction ID: {{ transaction_id }}

You can view your payout history at: {{ dashboard_url }}

Best regards,
{{ platform_name }} Team''',
                'html_template': '''<h2>Payout Processed</h2>
<p>Hello {{ seller_name }},</p>
<p>Your payout has been processed successfully.</p>
<h3>Payout Details:</h3>
<ul>
<li>Amount: ${{ payout_amount }}</li>
<li>Payout Date: {{ payout_date }}</li>
<li>Transaction ID: {{ transaction_id }}</li>
</ul>
<p><a href="{{ dashboard_url }}">View your payout history</a></p>
<p>Best regards,<br>{{ platform_name }} Team</p>'''
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                channel=template_data['channel'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created: {template.name}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated: {template.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(templates)} templates: '
                f'{created_count} created, {updated_count} updated'
            )
        )