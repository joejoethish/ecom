from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationPreference
from .services import NotificationService

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_notification_preferences(sender, instance, created, **kwargs):
    """
    Create default notification preferences when a new user is created
    """
    if created:
        # Default notification preferences for new users
        default_preferences = [
            # Order updates - all channels enabled
            ('ORDER_UPDATES', 'EMAIL', True),
            ('ORDER_UPDATES', 'SMS', True),
            ('ORDER_UPDATES', 'IN_APP', True),
            ('ORDER_UPDATES', 'PUSH', True),
            
            # Payment updates - email and in-app enabled
            ('PAYMENT_UPDATES', 'EMAIL', True),
            ('PAYMENT_UPDATES', 'SMS', False),
            ('PAYMENT_UPDATES', 'IN_APP', True),
            ('PAYMENT_UPDATES', 'PUSH', False),
            
            # Shipping updates - all channels enabled
            ('SHIPPING_UPDATES', 'EMAIL', True),
            ('SHIPPING_UPDATES', 'SMS', True),
            ('SHIPPING_UPDATES', 'IN_APP', True),
            ('SHIPPING_UPDATES', 'PUSH', True),
            
            # Promotional - email and push only
            ('PROMOTIONAL', 'EMAIL', True),
            ('PROMOTIONAL', 'SMS', False),
            ('PROMOTIONAL', 'IN_APP', False),
            ('PROMOTIONAL', 'PUSH', True),
            
            # Security - all channels enabled
            ('SECURITY', 'EMAIL', True),
            ('SECURITY', 'SMS', True),
            ('SECURITY', 'IN_APP', True),
            ('SECURITY', 'PUSH', True),
            
            # Account updates - email and in-app
            ('ACCOUNT', 'EMAIL', True),
            ('ACCOUNT', 'SMS', False),
            ('ACCOUNT', 'IN_APP', True),
            ('ACCOUNT', 'PUSH', False),
            
            # Reviews - email only
            ('REVIEWS', 'EMAIL', True),
            ('REVIEWS', 'SMS', False),
            ('REVIEWS', 'IN_APP', False),
            ('REVIEWS', 'PUSH', False),
            
            # General notifications - in-app only
            ('GENERAL', 'EMAIL', False),
            ('GENERAL', 'SMS', False),
            ('GENERAL', 'IN_APP', True),
            ('GENERAL', 'PUSH', False),
        ]
        
        preferences_to_create = []
        for notification_type, channel, is_enabled in default_preferences:
            preferences_to_create.append(
                NotificationPreference(
                    user=instance,
                    notification_type=notification_type,
                    channel=channel,
                    is_enabled=is_enabled
                )
            )
        
        NotificationPreference.objects.bulk_create(preferences_to_create, ignore_conflicts=True)


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """
    Send welcome notification to new users
    """
    if created:
        notification_service = NotificationService()
        
        context_data = {
            'user_name': instance.get_full_name() or instance.username,
            'user_email': instance.email,
            'platform_name': 'E-Commerce Platform',
            'support_email': 'support@ecommerce.com',
        }
        
        # Send welcome notification via email
        notification_service.send_notification(
            user=instance,
            template_type='WELCOME',
            context_data=context_data,
            channels=['EMAIL'],
            priority='NORMAL'
        )


# Import order-related signals
try:
    from apps.orders.models import Order
    
    @receiver(post_save, sender=Order)
    def send_order_notifications(sender, instance, created, **kwargs):
        """
        Send notifications when order status changes
        """
        notification_service = NotificationService()
        
        context_data = {
            'user_name': instance.user.get_full_name() or instance.user.username,
            'order_number': instance.order_number,
            'order_total': str(instance.total_amount),
            'order_status': instance.get_status_display(),
            'order_date': instance.created_at.strftime('%B %d, %Y'),
            'tracking_url': f'/orders/{instance.order_number}/track',
        }
        
        if created:
            # Order confirmation
            notification_service.send_notification(
                user=instance.user,
                template_type='ORDER_CONFIRMATION',
                context_data=context_data,
                related_object=instance,
                priority='HIGH'
            )
        else:
            # Order status update
            notification_service.send_notification(
                user=instance.user,
                template_type='ORDER_STATUS_UPDATE',
                context_data=context_data,
                related_object=instance,
                priority='HIGH'
            )

except ImportError:
    pass


# Import payment-related signals
try:
    from apps.payments.models import Payment
    
    @receiver(post_save, sender=Payment)
    def send_payment_notifications(sender, instance, created, **kwargs):
        """
        Send notifications when payment status changes
        """
        if not created:  # Only for status updates
            notification_service = NotificationService()
            
            context_data = {
                'user_name': instance.order.user.get_full_name() or instance.order.user.username,
                'order_number': instance.order.order_number,
                'payment_amount': str(instance.amount),
                'payment_method': instance.payment_method,
                'payment_status': instance.get_status_display(),
                'transaction_id': instance.payment_id,
            }
            
            if instance.status == 'COMPLETED':
                template_type = 'PAYMENT_SUCCESS'
                priority = 'HIGH'
            elif instance.status == 'FAILED':
                template_type = 'PAYMENT_FAILED'
                priority = 'URGENT'
            else:
                return  # Don't send notifications for other statuses
            
            notification_service.send_notification(
                user=instance.order.user,
                template_type=template_type,
                context_data=context_data,
                related_object=instance,
                priority=priority
            )

except ImportError:
    pass


# Import shipping-related signals
try:
    from apps.shipping.models import ShipmentTracking
    
    @receiver(post_save, sender=ShipmentTracking)
    def send_shipping_notifications(sender, instance, created, **kwargs):
        """
        Send notifications when shipping status changes
        """
        notification_service = NotificationService()
        
        context_data = {
            'user_name': instance.order.user.get_full_name() or instance.order.user.username,
            'order_number': instance.order.order_number,
            'tracking_number': instance.tracking_number,
            'shipping_status': instance.status,
            'estimated_delivery': instance.estimated_delivery_date.strftime('%B %d, %Y') if instance.estimated_delivery_date else 'TBD',
            'tracking_url': f'/orders/{instance.order.order_number}/track',
        }
        
        # Send notification for significant status changes
        if instance.status in ['SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED']:
            if instance.status == 'DELIVERED':
                template_type = 'DELIVERY_CONFIRMATION'
                priority = 'HIGH'
            else:
                template_type = 'SHIPPING_UPDATE'
                priority = 'NORMAL'
            
            notification_service.send_notification(
                user=instance.order.user,
                template_type=template_type,
                context_data=context_data,
                related_object=instance,
                priority=priority
            )

except ImportError:
    pass


# Import inventory-related signals
try:
    from apps.inventory.models import Inventory
    
    @receiver(post_save, sender=Inventory)
    def send_inventory_alerts(sender, instance, created, **kwargs):
        """
        Send low inventory alerts to administrators
        """
        # Refresh instance to get actual values after F() expressions
        if not created:
            instance.refresh_from_db()
            if instance.quantity <= instance.minimum_stock_level:
                notification_service = NotificationService()
                
                # Get admin users
                admin_users = User.objects.filter(is_staff=True, is_active=True)
                
                context_data = {
                    'product_name': instance.product.name,
                    'product_sku': instance.product.sku,
                    'current_stock': instance.quantity,
                    'minimum_stock': instance.minimum_stock_level,
                    'reorder_point': instance.reorder_point,
                    'product_url': f'/admin/products/{instance.product.id}',
                }
                
                for admin_user in admin_users:
                    notification_service.send_notification(
                        user=admin_user,
                        template_type='INVENTORY_LOW',
                        context_data=context_data,
                        channels=['EMAIL', 'IN_APP'],
                        related_object=instance,
                        priority='HIGH'
                    )

except ImportError:
    pass


# Import seller-related signals
try:
    from apps.sellers.models import Seller, SellerPayout
    
    @receiver(post_save, sender=Seller)
    def send_seller_verification_notifications(sender, instance, created, **kwargs):
        """
        Send seller verification notifications
        """
        if not created and instance.verification_status == 'VERIFIED':
            notification_service = NotificationService()
            
            context_data = {
                'seller_name': instance.business_name or instance.user.get_full_name(),
                'verification_date': timezone.now().strftime('%B %d, %Y'),
                'dashboard_url': '/seller/dashboard',
                'support_email': 'seller-support@ecommerce.com',
            }
            
            notification_service.send_notification(
                user=instance.user,
                template_type='SELLER_VERIFICATION',
                context_data=context_data,
                related_object=instance,
                priority='HIGH'
            )
    
    @receiver(post_save, sender=SellerPayout)
    def send_seller_payout_notifications(sender, instance, created, **kwargs):
        """
        Send seller payout notifications
        """
        if instance.status == 'COMPLETED':
            notification_service = NotificationService()
            
            context_data = {
                'seller_name': instance.seller.business_name or instance.seller.user.get_full_name(),
                'payout_amount': str(instance.amount),
                'payout_date': instance.processed_at.strftime('%B %d, %Y') if instance.processed_at else 'Processing',
                'transaction_id': instance.transaction_id,
                'dashboard_url': '/seller/payouts',
            }
            
            notification_service.send_notification(
                user=instance.seller.user,
                template_type='SELLER_PAYOUT',
                context_data=context_data,
                related_object=instance,
                priority='HIGH'
            )

except ImportError:
    pass


@receiver(post_save, sender=Notification)
def log_notification_creation(sender, instance, created, **kwargs):
    """
    Log notification creation for analytics
    """
    if created:
        from .models import NotificationLog
        NotificationLog.objects.create(
            notification=instance,
            action='created',
            details={
                'channel': instance.channel,
                'priority': instance.priority,
                'template_type': instance.template.template_type if instance.template else 'CUSTOM'
            }
        )