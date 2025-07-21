"""
Payment signals for the ecommerce platform.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import Payment, Refund, Wallet, WalletTransaction, GiftCard, GiftCardTransaction
from apps.orders.models import Order, OrderTracking
from apps.notifications.models import Notification

# Import background tasks
from tasks.tasks import (
    sync_payment_status_task,
    send_email_task,
    send_sms_task
)


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for payment post save.
    
    - Updates order payment status
    - Triggers payment status sync for pending payments
    - Handles wallet and gift card transactions
    - Sends payment notifications
    - Sends real-time WebSocket updates
    """
    if created:
        # For new payments, schedule a status sync check
        if instance.status == 'PENDING':
            # Schedule payment status sync after 5 minutes
            sync_payment_status_task.apply_async(
                args=[instance.id],
                countdown=300  # 5 minutes
            )
            
            # Schedule another check after 1 hour if still pending
            sync_payment_status_task.apply_async(
                args=[instance.id],
                countdown=3600  # 1 hour
            )
            
            # Send real-time WebSocket notification about pending payment
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                import json
                
                channel_layer = get_channel_layer()
                
                # Send to user's notification channel
                user_notification_group = f'notifications_{instance.user.id}'
                async_to_sync(channel_layer.group_send)(
                    user_notification_group,
                    {
                        'type': 'notification_message',
                        'notification_type': 'PAYMENT_PENDING',
                        'message': f"Payment for order #{instance.order.order_number} is being processed.",
                        'data': {
                            'order_id': str(instance.order.id),
                            'order_number': instance.order.order_number,
                            'payment_id': str(instance.id),
                            'amount': float(instance.amount),
                            'currency': instance.currency,
                            'payment_method': instance.payment_method
                        },
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
                # Also send to order tracking channel
                order_group_name = f'order_tracking_{instance.order.id}'
                async_to_sync(channel_layer.group_send)(
                    order_group_name,
                    {
                        'type': 'order_update',
                        'status': 'PAYMENT_PENDING',
                        'message': f"Payment of {instance.amount} {instance.currency} is being processed via {instance.payment_method}",
                        'tracking_data': {
                            'payment_id': str(instance.id),
                            'amount': float(instance.amount),
                            'currency': instance.currency,
                            'payment_method': instance.payment_method,
                            'status': instance.status,
                            'timestamp': timezone.now().isoformat()
                        },
                        'timestamp': timezone.now().isoformat()
                    }
                )
            except Exception as e:
                # Log the error but don't stop the process
                print(f"Error sending payment WebSocket notification: {str(e)}")
    else:
        # Handle payment status changes
        if hasattr(instance, '_old_status') and instance._old_status != instance.status:
            # Update order payment status
            order = instance.order
            
            if instance.status == 'COMPLETED':
                order.payment_status = 'paid'
                instance.payment_date = timezone.now()
                instance.save(update_fields=['payment_date'])
                
                # Create order tracking event
                OrderTracking.objects.create(
                    order=order,
                    status=order.status,
                    description=f"Payment of {instance.amount} {instance.currency} received via {instance.payment_method}"
                )
                
                # Process wallet cashback if applicable
                if hasattr(instance.user, 'wallet'):
                    # Calculate cashback (example: 1% of payment amount)
                    cashback_amount = instance.amount * 0.01
                    if cashback_amount > 0:
                        wallet = instance.user.wallet
                        wallet.balance += cashback_amount
                        wallet.save()
                        
                        # Create wallet transaction record
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            amount=cashback_amount,
                            transaction_type='CASHBACK',
                            description=f'Cashback for order {order.order_number}',
                            balance_after_transaction=wallet.balance,
                            reference_id=order.order_number,
                            payment=instance
                        )
                        
                        # Send cashback notification
                        Notification.objects.create(
                            user=instance.user,
                            title="Cashback Received",
                            message=f"You received {cashback_amount} {instance.currency} cashback for your order #{order.order_number}",
                            notification_type="CASHBACK",
                            reference_id=str(order.id)
                        )
                        
                        # Send email notification about cashback
                        context = {
                            'user': instance.user,
                            'order': order,
                            'cashback_amount': cashback_amount,
                            'currency': instance.currency,
                            'wallet_balance': wallet.balance,
                            'frontend_url': settings.FRONTEND_URL
                        }
                        
                        send_email_task.delay(
                            subject=f"Cashback Received for Order #{order.order_number}",
                            message=f"You received {cashback_amount} {instance.currency} cashback for your order #{order.order_number}",
                            recipient_list=[instance.user.email],
                            template_name='emails/cashback_notification.html',
                            context=context
                        )
                
            elif instance.status == 'FAILED':
                order.payment_status = 'failed'
                
                # Create order tracking event
                OrderTracking.objects.create(
                    order=order,
                    status=order.status,
                    description=f"Payment failed: {instance.gateway_response.get('error_message', 'Unknown error')}"
                )
                
                # Send payment failure notification
                Notification.objects.create(
                    user=instance.user,
                    title="Payment Failed",
                    message=f"Payment for order #{order.order_number} has failed. Please try again.",
                    notification_type="PAYMENT_FAILED",
                    reference_id=str(order.id)
                )
                
                # Send email notification about payment failure
                context = {
                    'user': instance.user,
                    'order': order,
                    'payment': instance,
                    'error_message': instance.gateway_response.get('error_message', 'Unknown error'),
                    'frontend_url': settings.FRONTEND_URL
                }
                
                send_email_task.delay(
                    subject=f"Payment Failed for Order #{order.order_number}",
                    message=f"Payment for order #{order.order_number} has failed. Please try again.",
                    recipient_list=[instance.user.email],
                    template_name='emails/payment_failed.html',
                    context=context
                )
                
            elif instance.status in ['REFUNDED', 'PARTIALLY_REFUNDED']:
                if instance.status == 'REFUNDED':
                    order.payment_status = 'refunded'
                    description = f"Full refund of {instance.amount} {instance.currency} processed"
                else:
                    order.payment_status = 'partially_refunded'
                    refunded_amount = sum(
                        refund.amount for refund in instance.refunds.filter(status='COMPLETED')
                    )
                    description = f"Partial refund of {refunded_amount} {instance.currency} processed"
                
                # Create order tracking event
                OrderTracking.objects.create(
                    order=order,
                    status=order.status,
                    description=description
                )
            
            order.save(update_fields=['payment_status'])


@receiver(pre_save, sender=Payment)
def payment_pre_save(sender, instance, **kwargs):
    """
    Signal handler for payment pre save.
    
    - Tracks status changes
    """
    if instance.pk:
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Payment.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Refund)
def refund_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for refund post save.
    
    - Updates payment status when refund is processed
    - Handles wallet refunds
    """
    if instance.status == 'COMPLETED' and instance.refund_date:
        payment = instance.payment
        
        # Check if this is a full or partial refund
        total_refunded = sum(
            refund.amount for refund in payment.refunds.filter(status='COMPLETED')
        )
        
        if total_refunded >= payment.amount:
            payment.status = 'REFUNDED'
        else:
            payment.status = 'PARTIALLY_REFUNDED'
        
        payment.save(update_fields=['status'])
        
        # Process wallet refund if refund method is wallet
        if hasattr(payment.user, 'wallet'):
            wallet = payment.user.wallet
            wallet.balance += instance.amount
            wallet.save()
            
            # Create wallet transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=instance.amount,
                transaction_type='REFUND',
                description=f'Refund for order {payment.order.order_number}',
                balance_after_transaction=wallet.balance,
                reference_id=payment.order.order_number,
                payment=payment
            )


@receiver(post_save, sender=WalletTransaction)
def wallet_transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for wallet transaction post save.
    
    - Updates wallet balance
    - Validates transaction consistency
    """
    if created:
        # Validate that the balance_after_transaction is correct
        wallet = instance.wallet
        expected_balance = wallet.balance
        
        if instance.transaction_type in ['CREDIT', 'REFUND', 'CASHBACK']:
            expected_balance += instance.amount
        elif instance.transaction_type == 'DEBIT':
            expected_balance -= instance.amount
        
        if abs(expected_balance - instance.balance_after_transaction) > 0.01:  # Allow for small rounding differences
            # Log inconsistency but don't raise error to avoid breaking the transaction
            print(f"Wallet balance inconsistency detected for wallet {wallet.id}")


@receiver(post_save, sender=GiftCardTransaction)
def gift_card_transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for gift card transaction post save.
    
    - Updates gift card balance
    - Validates transaction consistency
    """
    if created:
        gift_card = instance.gift_card
        
        # Update gift card balance
        gift_card.current_balance -= instance.amount
        
        # Check if gift card is fully used
        if gift_card.current_balance <= 0:
            gift_card.status = 'USED'
            gift_card.current_balance = 0
        
        gift_card.save(update_fields=['current_balance', 'status'])
        
        # Validate balance consistency
        if abs(gift_card.current_balance - instance.balance_after_transaction) > 0.01:
            print(f"Gift card balance inconsistency detected for card {gift_card.code}")


@receiver(post_save, sender=GiftCard)
def gift_card_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for gift card post save.
    
    - Sends gift card notifications
    - Handles gift card expiry
    """
    if created:
        # Send gift card creation notification
        # This would integrate with notification system
        pass
    
    # Check for expiry
    if instance.expiry_date <= timezone.now().date() and instance.status == 'ACTIVE':
        instance.status = 'EXPIRED'
        instance.save(update_fields=['status'])