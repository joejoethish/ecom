"""
Payment services for the ecommerce platform.
"""
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from core.integrations.payment_gateways.factory import PaymentGatewayFactory
from core.exceptions import PaymentGatewayError, InsufficientFundsError
from .models import (
    Payment, Refund, Wallet, WalletTransaction, 
    GiftCard, GiftCardTransaction, Currency, PaymentMethod
)

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Service for currency-related operations.
    """
    
    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
        """
        Get the exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Decimal exchange rate
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        try:
            from_curr = Currency.objects.get(code=from_currency)
            to_curr = Currency.objects.get(code=to_currency)
            
            # Calculate exchange rate via USD (base currency)
            # from_currency -> USD -> to_currency
            return to_curr.exchange_rate / from_curr.exchange_rate
        except Currency.DoesNotExist:
            logger.error(f"Currency not found: {from_currency} or {to_currency}")
            return Decimal('1.0')  # Default to 1:1 if currency not found
    
    @staticmethod
    def convert_amount(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: The amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount in target currency
        """
        exchange_rate = CurrencyService.get_exchange_rate(from_currency, to_currency)
        return amount * exchange_rate


class PaymentService:
    """
    Service for payment processing operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_payment(
        order_id: str,
        user_id: uuid.UUID,
        amount: Decimal,
        currency_code: str,
        payment_method_id: uuid.UUID,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new payment for an order.
        
        Args:
            order_id: The order ID
            user_id: The user ID
            amount: The payment amount
            currency_code: The currency code
            payment_method_id: The payment method ID
            metadata: Additional payment metadata
            
        Returns:
            Dict containing payment details and gateway response
        """
        try:
            # Get the payment method
            payment_method = PaymentMethod.objects.get(id=payment_method_id)
            
            # Get the currency
            currency = Currency.objects.get(code=currency_code)
            
            # Create payment record
            payment = Payment.objects.create(
                order_id=order_id,
                user_id=user_id,
                payment_method=payment_method,
                amount=amount,
                currency=currency,
                status='PENDING'
            )
            
            # If payment method is wallet or gift card, process internally
            if payment_method.method_type == 'WALLET':
                return PaymentService._process_wallet_payment(payment, metadata or {})
            elif payment_method.method_type == 'GIFT_CARD':
                return PaymentService._process_gift_card_payment(payment, metadata or {})
            
            # Otherwise, use external payment gateway
            gateway = PaymentGatewayFactory.get_gateway(payment_method.gateway)
            
            # Prepare metadata for gateway
            gateway_metadata = metadata or {}
            gateway_metadata.update({
                'payment_id': str(payment.id),
                'user_id': str(user_id)
            })
            
            # Create payment in gateway
            gateway_response = gateway.create_payment(
                float(amount),
                currency_code,
                str(order_id),
                gateway_metadata
            )
            
            # Update payment with gateway information
            payment.gateway_payment_id = gateway_response.get('gateway_payment_id', '')
            payment.gateway_order_id = gateway_response.get('gateway_order_id', '')
            payment.gateway_response = gateway_response.get('gateway_data', {})
            payment.save()
            
            return {
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': float(payment.amount),
                'currency': currency_code,
                'payment_method': payment_method.method_type,
                'gateway_data': gateway_response
            }
        except Currency.DoesNotExist:
            logger.error(f"Currency not found: {currency_code}")
            raise PaymentGatewayError(f"Unsupported currency: {currency_code}")
        except PaymentMethod.DoesNotExist:
            logger.error(f"Payment method not found: {payment_method_id}")
            raise PaymentGatewayError(f"Invalid payment method")
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            raise PaymentGatewayError(f"Failed to create payment: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def _process_wallet_payment(payment: Payment, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using the user's wallet.
        
        Args:
            payment: The payment object
            metadata: Additional payment metadata
            
        Returns:
            Dict containing payment details
        """
        try:
            # Get user's wallet
            wallet, created = Wallet.objects.get_or_create(
                user_id=payment.user_id,
                defaults={
                    'balance': Decimal('0.0'),
                    'currency_id': payment.currency_id,
                    'is_active': True
                }
            )
            
            # Check if wallet has sufficient balance
            if wallet.balance < payment.amount:
                payment.status = 'FAILED'
                payment.failure_reason = 'Insufficient wallet balance'
                payment.save()
                raise InsufficientFundsError("Insufficient wallet balance")
            
            # Deduct amount from wallet
            wallet.balance -= payment.amount
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=payment.amount,
                transaction_type='DEBIT',
                description=f"Payment for order {payment.order.order_number}",
                balance_after_transaction=wallet.balance,
                reference_id=str(payment.id),
                payment=payment
            )
            
            # Update payment status
            payment.status = 'COMPLETED'
            payment.payment_date = timezone.now()
            payment.save()
            
            return {
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': float(payment.amount),
                'currency': payment.currency.code,
                'payment_method': 'WALLET',
                'wallet_balance': float(wallet.balance)
            }
        except InsufficientFundsError:
            raise
        except Exception as e:
            logger.error(f"Wallet payment error: {str(e)}")
            payment.status = 'FAILED'
            payment.failure_reason = str(e)
            payment.save()
            raise PaymentGatewayError(f"Failed to process wallet payment: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def _process_gift_card_payment(payment: Payment, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using a gift card.
        
        Args:
            payment: The payment object
            metadata: Additional payment metadata including gift card code
            
        Returns:
            Dict containing payment details
        """
        try:
            # Get gift card code from metadata
            gift_card_code = metadata.get('gift_card_code')
            if not gift_card_code:
                payment.status = 'FAILED'
                payment.failure_reason = 'Gift card code not provided'
                payment.save()
                raise PaymentGatewayError("Gift card code not provided")
            
            # Get gift card
            gift_card = GiftCard.objects.get(
                code=gift_card_code,
                status='ACTIVE',
                expiry_date__gte=timezone.now().date()
            )
            
            # Check if gift card has sufficient balance
            if gift_card.current_balance < payment.amount:
                payment.status = 'FAILED'
                payment.failure_reason = 'Insufficient gift card balance'
                payment.save()
                raise InsufficientFundsError("Insufficient gift card balance")
            
            # Deduct amount from gift card
            gift_card.current_balance -= payment.amount
            if gift_card.current_balance == 0:
                gift_card.status = 'USED'
            gift_card.save()
            
            # Create gift card transaction
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                amount=payment.amount,
                payment=payment,
                balance_after_transaction=gift_card.current_balance,
                description=f"Payment for order {payment.order.order_number}"
            )
            
            # Update payment status
            payment.status = 'COMPLETED'
            payment.payment_date = timezone.now()
            payment.save()
            
            return {
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': float(payment.amount),
                'currency': payment.currency.code,
                'payment_method': 'GIFT_CARD',
                'gift_card_balance': float(gift_card.current_balance)
            }
        except GiftCard.DoesNotExist:
            payment.status = 'FAILED'
            payment.failure_reason = 'Invalid or expired gift card'
            payment.save()
            raise PaymentGatewayError("Invalid or expired gift card")
        except InsufficientFundsError:
            raise
        except Exception as e:
            logger.error(f"Gift card payment error: {str(e)}")
            payment.status = 'FAILED'
            payment.failure_reason = str(e)
            payment.save()
            raise PaymentGatewayError(f"Failed to process gift card payment: {str(e)}")
    
    @staticmethod
    def verify_payment(
        payment_id: uuid.UUID,
        gateway_payment_id: str,
        gateway_signature: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Verify a payment with the payment gateway.
        
        Args:
            payment_id: The internal payment ID
            gateway_payment_id: The payment ID from the gateway
            gateway_signature: The signature from the gateway
            metadata: Additional verification metadata
            
        Returns:
            Dict containing verification result
        """
        try:
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # If payment is already completed or failed, return current status
            if payment.status in ['COMPLETED', 'FAILED']:
                return {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'verified': payment.status == 'COMPLETED'
                }
            
            # Get the gateway
            gateway = PaymentGatewayFactory.get_gateway(payment.payment_method.gateway)
            
            # Prepare metadata for verification
            verification_metadata = metadata or {}
            if payment.gateway_order_id:
                verification_metadata['razorpay_order_id'] = payment.gateway_order_id
            
            # Verify the payment
            is_verified = gateway.verify_payment(
                gateway_payment_id,
                gateway_signature,
                verification_metadata
            )
            
            # Update payment status based on verification
            if is_verified:
                payment.status = 'COMPLETED'
                payment.payment_date = timezone.now()
            else:
                payment.status = 'FAILED'
                payment.failure_reason = 'Payment verification failed'
            
            payment.gateway_payment_id = gateway_payment_id
            payment.gateway_signature = gateway_signature
            payment.save()
            
            return {
                'payment_id': str(payment.id),
                'status': payment.status,
                'verified': is_verified
            }
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            raise PaymentGatewayError("Invalid payment ID")
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            raise PaymentGatewayError(f"Failed to verify payment: {str(e)}")
    
    @staticmethod
    def get_payment_status(payment_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get the current status of a payment.
        
        Args:
            payment_id: The payment ID
            
        Returns:
            Dict containing payment status details
        """
        try:
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # For internal payment methods, return current status
            if payment.payment_method.gateway == 'INTERNAL':
                return {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'amount': float(payment.amount),
                    'currency': payment.currency.code,
                    'payment_method': payment.payment_method.method_type
                }
            
            # For external gateways, sync status if not completed or failed
            if payment.status not in ['COMPLETED', 'FAILED'] and payment.gateway_payment_id:
                gateway = PaymentGatewayFactory.get_gateway(payment.payment_method.gateway)
                gateway_status = gateway.get_payment_status(payment.gateway_payment_id)
                
                # Update payment status if changed
                if gateway_status['status'] != payment.status:
                    payment.status = gateway_status['status']
                    payment.save()
            
            return {
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': float(payment.amount),
                'currency': payment.currency.code,
                'payment_method': payment.payment_method.method_type,
                'payment_date': payment.payment_date
            }
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            raise PaymentGatewayError("Invalid payment ID")
        except Exception as e:
            logger.error(f"Get payment status error: {str(e)}")
            raise PaymentGatewayError(f"Failed to get payment status: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def process_refund(
        payment_id: uuid.UUID,
        amount: Decimal,
        reason: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment.
        
        Args:
            payment_id: The payment ID to refund
            amount: The refund amount
            reason: The reason for the refund
            metadata: Additional refund metadata
            
        Returns:
            Dict containing refund details
        """
        try:
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # Check if payment is completed
            if payment.status != 'COMPLETED':
                raise PaymentGatewayError("Cannot refund a payment that is not completed")
            
            # Check if refund amount is valid
            if amount <= 0 or amount > payment.amount:
                raise PaymentGatewayError("Invalid refund amount")
            
            # Create refund record
            refund = Refund.objects.create(
                payment=payment,
                amount=amount,
                reason=reason,
                status='PENDING'
            )
            
            # Process refund based on payment method
            if payment.payment_method.method_type == 'WALLET':
                return PaymentService._process_wallet_refund(payment, refund, metadata or {})
            elif payment.payment_method.method_type == 'GIFT_CARD':
                return PaymentService._process_gift_card_refund(payment, refund, metadata or {})
            
            # For external gateways
            gateway = PaymentGatewayFactory.get_gateway(payment.payment_method.gateway)
            
            # Process refund through gateway
            gateway_response = gateway.process_refund(
                payment.gateway_payment_id,
                float(amount),
                {
                    'refund_id': str(refund.id),
                    'reason': reason,
                    **(metadata or {})
                }
            )
            
            # Update refund with gateway information
            refund.status = 'COMPLETED'
            refund.transaction_id = gateway_response.get('refund_id', '')
            refund.gateway_response = gateway_response.get('gateway_data', {})
            refund.refund_date = timezone.now()
            refund.save()
            
            # Update payment status if fully refunded
            total_refunded = Refund.objects.filter(
                payment=payment, 
                status='COMPLETED'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.0')
            
            if total_refunded >= payment.amount:
                payment.status = 'REFUNDED'
            elif total_refunded > 0:
                payment.status = 'PARTIALLY_REFUNDED'
            payment.save()
            
            return {
                'refund_id': str(refund.id),
                'payment_id': str(payment.id),
                'amount': float(refund.amount),
                'status': refund.status,
                'gateway_data': gateway_response
            }
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            raise PaymentGatewayError("Invalid payment ID")
        except Exception as e:
            logger.error(f"Refund processing error: {str(e)}")
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def _process_wallet_refund(payment: Payment, refund: Refund, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund for a wallet payment.
        
        Args:
            payment: The payment object
            refund: The refund object
            metadata: Additional refund metadata
            
        Returns:
            Dict containing refund details
        """
        try:
            # Get user's wallet
            wallet = Wallet.objects.get(user_id=payment.user_id)
            
            # Add refund amount to wallet
            wallet.balance += refund.amount
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=refund.amount,
                transaction_type='REFUND',
                description=f"Refund for order {payment.order.order_number}: {refund.reason}",
                balance_after_transaction=wallet.balance,
                reference_id=str(refund.id),
                payment=payment
            )
            
            # Update refund status
            refund.status = 'COMPLETED'
            refund.refund_date = timezone.now()
            refund.save()
            
            # Update payment status
            if refund.amount >= payment.amount:
                payment.status = 'REFUNDED'
            else:
                payment.status = 'PARTIALLY_REFUNDED'
            payment.save()
            
            return {
                'refund_id': str(refund.id),
                'payment_id': str(payment.id),
                'amount': float(refund.amount),
                'status': refund.status,
                'wallet_balance': float(wallet.balance)
            }
        except Wallet.DoesNotExist:
            # Create wallet if it doesn't exist
            wallet = Wallet.objects.create(
                user_id=payment.user_id,
                balance=refund.amount,
                currency_id=payment.currency_id,
                is_active=True
            )
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=refund.amount,
                transaction_type='REFUND',
                description=f"Refund for order {payment.order.order_number}: {refund.reason}",
                balance_after_transaction=wallet.balance,
                reference_id=str(refund.id),
                payment=payment
            )
            
            # Update refund status
            refund.status = 'COMPLETED'
            refund.refund_date = timezone.now()
            refund.save()
            
            # Update payment status
            if refund.amount >= payment.amount:
                payment.status = 'REFUNDED'
            else:
                payment.status = 'PARTIALLY_REFUNDED'
            payment.save()
            
            return {
                'refund_id': str(refund.id),
                'payment_id': str(payment.id),
                'amount': float(refund.amount),
                'status': refund.status,
                'wallet_balance': float(wallet.balance)
            }
        except Exception as e:
            logger.error(f"Wallet refund error: {str(e)}")
            refund.status = 'FAILED'
            refund.save()
            raise PaymentGatewayError(f"Failed to process wallet refund: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def _process_gift_card_refund(payment: Payment, refund: Refund, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund for a gift card payment.
        
        Args:
            payment: The payment object
            refund: The refund object
            metadata: Additional refund metadata including gift card code
            
        Returns:
            Dict containing refund details
        """
        try:
            # Get gift card code from original payment metadata
            gift_card_code = metadata.get('gift_card_code')
            if not gift_card_code:
                # Try to find gift card from transactions
                gift_card_tx = GiftCardTransaction.objects.filter(payment=payment).first()
                if gift_card_tx:
                    gift_card = gift_card_tx.gift_card
                else:
                    raise PaymentGatewayError("Gift card information not found")
            else:
                gift_card = GiftCard.objects.get(code=gift_card_code)
            
            # Add refund amount to gift card
            gift_card.current_balance += refund.amount
            if gift_card.status == 'USED' and gift_card.current_balance > 0:
                gift_card.status = 'ACTIVE'
            gift_card.save()
            
            # Create gift card transaction
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                amount=refund.amount,
                payment=payment,
                balance_after_transaction=gift_card.current_balance,
                description=f"Refund for order {payment.order.order_number}: {refund.reason}"
            )
            
            # Update refund status
            refund.status = 'COMPLETED'
            refund.refund_date = timezone.now()
            refund.save()
            
            # Update payment status
            if refund.amount >= payment.amount:
                payment.status = 'REFUNDED'
            else:
                payment.status = 'PARTIALLY_REFUNDED'
            payment.save()
            
            return {
                'refund_id': str(refund.id),
                'payment_id': str(payment.id),
                'amount': float(refund.amount),
                'status': refund.status,
                'gift_card_balance': float(gift_card.current_balance)
            }
        except GiftCard.DoesNotExist:
            logger.error(f"Gift card not found")
            refund.status = 'FAILED'
            refund.save()
            raise PaymentGatewayError("Gift card not found")
        except Exception as e:
            logger.error(f"Gift card refund error: {str(e)}")
            refund.status = 'FAILED'
            refund.save()
            raise PaymentGatewayError(f"Failed to process gift card refund: {str(e)}")


class WalletService:
    """
    Service for wallet operations.
    """
    
    @staticmethod
    @transaction.atomic
    def add_funds(
        user_id: uuid.UUID,
        amount: Decimal,
        currency_code: str,
        payment_method_id: uuid.UUID,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Add funds to a user's wallet.
        
        Args:
            user_id: The user ID
            amount: The amount to add
            currency_code: The currency code
            payment_method_id: The payment method ID
            metadata: Additional metadata
            
        Returns:
            Dict containing wallet details
        """
        try:
            # Get the currency
            currency = Currency.objects.get(code=currency_code)
            
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'balance': Decimal('0.0'),
                    'currency': currency,
                    'is_active': True
                }
            )
            
            # If wallet currency is different, convert amount
            if wallet.currency.code != currency_code:
                amount = CurrencyService.convert_amount(
                    amount,
                    currency_code,
                    wallet.currency.code
                )
            
            # Create a payment for the wallet funding
            payment_service = PaymentService()
            payment_result = payment_service.create_payment(
                order_id=None,  # No order for wallet funding
                user_id=user_id,
                amount=amount,
                currency_code=currency_code,
                payment_method_id=payment_method_id,
                metadata={
                    'wallet_funding': True,
                    **(metadata or {})
                }
            )
            
            # Return payment details
            return {
                'wallet_id': str(wallet.id),
                'current_balance': float(wallet.balance),
                'payment': payment_result
            }
        except Currency.DoesNotExist:
            logger.error(f"Currency not found: {currency_code}")
            raise PaymentGatewayError(f"Unsupported currency: {currency_code}")
        except Exception as e:
            logger.error(f"Add wallet funds error: {str(e)}")
            raise PaymentGatewayError(f"Failed to add funds to wallet: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def complete_add_funds(
        payment_id: uuid.UUID,
        gateway_payment_id: str,
        gateway_signature: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Complete the process of adding funds to a wallet after payment verification.
        
        Args:
            payment_id: The payment ID
            gateway_payment_id: The payment ID from the gateway
            gateway_signature: The signature from the gateway
            metadata: Additional verification metadata
            
        Returns:
            Dict containing wallet details
        """
        try:
            # Verify the payment
            payment_service = PaymentService()
            verification = payment_service.verify_payment(
                payment_id,
                gateway_payment_id,
                gateway_signature,
                metadata
            )
            
            if not verification['verified']:
                return {
                    'success': False,
                    'message': 'Payment verification failed'
                }
            
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # Get the wallet
            wallet = Wallet.objects.get(user_id=payment.user_id)
            
            # Add funds to wallet
            wallet.balance += payment.amount
            wallet.save()
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=payment.amount,
                transaction_type='CREDIT',
                description='Wallet funding',
                balance_after_transaction=wallet.balance,
                reference_id=str(payment.id),
                payment=payment
            )
            
            return {
                'success': True,
                'wallet_id': str(wallet.id),
                'new_balance': float(wallet.balance),
                'added_amount': float(payment.amount)
            }
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            raise PaymentGatewayError("Invalid payment ID")
        except Wallet.DoesNotExist:
            logger.error(f"Wallet not found for user: {payment.user_id}")
            raise PaymentGatewayError("Wallet not found")
        except Exception as e:
            logger.error(f"Complete add wallet funds error: {str(e)}")
            raise PaymentGatewayError(f"Failed to complete wallet funding: {str(e)}")


class GiftCardService:
    """
    Service for gift card operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_gift_card(
        initial_balance: Decimal,
        currency_code: str,
        expiry_date,
        purchased_by_id: uuid.UUID = None,
        issued_to_id: uuid.UUID = None
    ) -> Dict[str, Any]:
        """
        Create a new gift card.
        
        Args:
            initial_balance: The initial balance of the gift card
            currency_code: The currency code
            expiry_date: The expiry date
            purchased_by_id: The ID of the user who purchased the gift card
            issued_to_id: The ID of the user to whom the gift card is issued
            
        Returns:
            Dict containing gift card details
        """
        try:
            # Get the currency
            currency = Currency.objects.get(code=currency_code)
            
            # Generate a unique code
            code = GiftCardService._generate_gift_card_code()
            
            # Create the gift card
            gift_card = GiftCard.objects.create(
                code=code,
                initial_balance=initial_balance,
                current_balance=initial_balance,
                currency=currency,
                purchased_by_id=purchased_by_id,
                issued_to_id=issued_to_id,
                status='ACTIVE',
                expiry_date=expiry_date
            )
            
            return {
                'gift_card_id': str(gift_card.id),
                'code': gift_card.code,
                'balance': float(gift_card.current_balance),
                'currency': currency_code,
                'expiry_date': gift_card.expiry_date.isoformat()
            }
        except Currency.DoesNotExist:
            logger.error(f"Currency not found: {currency_code}")
            raise PaymentGatewayError(f"Unsupported currency: {currency_code}")
        except Exception as e:
            logger.error(f"Create gift card error: {str(e)}")
            raise PaymentGatewayError(f"Failed to create gift card: {str(e)}")
    
    @staticmethod
    def _generate_gift_card_code() -> str:
        """
        Generate a unique gift card code.
        
        Returns:
            Unique gift card code
        """
        import random
        import string
        
        # Generate a random code
        code_length = 16
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters) for _ in range(code_length))
        
        # Format as XXXX-XXXX-XXXX-XXXX
        formatted_code = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
        
        # Check if code already exists
        if GiftCard.objects.filter(code=formatted_code).exists():
            return GiftCardService._generate_gift_card_code()
        
        return formatted_code
    
    @staticmethod
    def get_gift_card_details(code: str) -> Dict[str, Any]:
        """
        Get details of a gift card.
        
        Args:
            code: The gift card code
            
        Returns:
            Dict containing gift card details
        """
        try:
            # Get the gift card
            gift_card = GiftCard.objects.get(
                code=code,
                status='ACTIVE',
                expiry_date__gte=timezone.now().date()
            )
            
            return {
                'gift_card_id': str(gift_card.id),
                'code': gift_card.code,
                'balance': float(gift_card.current_balance),
                'currency': gift_card.currency.code,
                'expiry_date': gift_card.expiry_date.isoformat()
            }
        except GiftCard.DoesNotExist:
            logger.error(f"Gift card not found or expired: {code}")
            raise PaymentGatewayError("Invalid or expired gift card")
        except Exception as e:
            logger.error(f"Get gift card details error: {str(e)}")
            raise PaymentGatewayError(f"Failed to get gift card details: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def purchase_gift_card(
        user_id: uuid.UUID,
        amount: Decimal,
        currency_code: str,
        payment_method_id: uuid.UUID,
        recipient_email: str = None,
        expiry_days: int = 365,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Purchase a gift card.
        
        Args:
            user_id: The user ID of the purchaser
            amount: The gift card amount
            currency_code: The currency code
            payment_method_id: The payment method ID
            recipient_email: The email of the recipient (optional)
            expiry_days: The number of days until expiry
            metadata: Additional metadata
            
        Returns:
            Dict containing gift card and payment details
        """
        try:
            # Calculate expiry date
            expiry_date = timezone.now().date() + timezone.timedelta(days=expiry_days)
            
            # Create a payment for the gift card purchase
            payment_service = PaymentService()
            payment_result = payment_service.create_payment(
                order_id=None,  # No order for gift card purchase
                user_id=user_id,
                amount=amount,
                currency_code=currency_code,
                payment_method_id=payment_method_id,
                metadata={
                    'gift_card_purchase': True,
                    'recipient_email': recipient_email,
                    'expiry_days': expiry_days,
                    **(metadata or {})
                }
            )
            
            # Return payment details
            return {
                'payment': payment_result,
                'expiry_date': expiry_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Purchase gift card error: {str(e)}")
            raise PaymentGatewayError(f"Failed to purchase gift card: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def complete_gift_card_purchase(
        payment_id: uuid.UUID,
        gateway_payment_id: str,
        gateway_signature: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Complete the process of purchasing a gift card after payment verification.
        
        Args:
            payment_id: The payment ID
            gateway_payment_id: The payment ID from the gateway
            gateway_signature: The signature from the gateway
            metadata: Additional verification metadata
            
        Returns:
            Dict containing gift card details
        """
        try:
            # Verify the payment
            payment_service = PaymentService()
            verification = payment_service.verify_payment(
                payment_id,
                gateway_payment_id,
                gateway_signature,
                metadata
            )
            
            if not verification['verified']:
                return {
                    'success': False,
                    'message': 'Payment verification failed'
                }
            
            # Get the payment
            payment = Payment.objects.get(id=payment_id)
            
            # Get recipient user if email provided
            recipient_email = payment.gateway_response.get('metadata', {}).get('recipient_email')
            recipient_id = None
            if recipient_email:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    recipient = User.objects.get(email=recipient_email)
                    recipient_id = recipient.id
                except User.DoesNotExist:
                    pass
            
            # Calculate expiry date
            expiry_days = payment.gateway_response.get('metadata', {}).get('expiry_days', 365)
            expiry_date = timezone.now().date() + timezone.timedelta(days=int(expiry_days))
            
            # Create the gift card
            gift_card = GiftCardService.create_gift_card(
                initial_balance=payment.amount,
                currency_code=payment.currency.code,
                expiry_date=expiry_date,
                purchased_by_id=payment.user_id,
                issued_to_id=recipient_id
            )
            
            return {
                'success': True,
                'gift_card': gift_card
            }
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            raise PaymentGatewayError("Invalid payment ID")
        except Exception as e:
            logger.error(f"Complete gift card purchase error: {str(e)}")
            raise PaymentGatewayError(f"Failed to complete gift card purchase: {str(e)}")