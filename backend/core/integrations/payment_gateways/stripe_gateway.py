"""
Stripe payment gateway integration.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

from .base import BasePaymentGateway
from core.exceptions import PaymentGatewayError

logger = logging.getLogger(__name__)


class StripeGateway(BasePaymentGateway):
    """
    Stripe payment gateway implementation.
    """
    
    def __init__(self):
        """
        Initialize Stripe client with API key.
        """
        if not STRIPE_AVAILABLE:
            logger.warning("Stripe package not installed. Install with: pip install stripe")
            raise PaymentGatewayError("Stripe package not available")
        
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.public_key = settings.STRIPE_PUBLIC_KEY
        except Exception as e:
            logger.error(f"Failed to initialize Stripe client: {str(e)}")
            raise PaymentGatewayError("Failed to initialize payment gateway")
    
    def create_payment(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment intent in Stripe.
        
        Args:
            amount: The payment amount
            currency: The currency code (e.g., USD)
            order_id: The order identifier
            metadata: Additional data for the payment
            
        Returns:
            Dict containing payment details including gateway payment ID
        """
        try:
            # Stripe expects amount in smallest currency unit (cents for USD)
            amount_in_smallest_unit = int(amount * 100)
            
            # Create a payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_in_smallest_unit,
                currency=currency.lower(),
                metadata={
                    'order_id': order_id,
                    **metadata
                },
                description=f"Payment for Order #{order_id}"
            )
            
            return {
                'gateway_payment_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency,
                'gateway_data': {
                    'id': intent.id,
                    'status': intent.status
                }
            }
        except Exception as e:
            logger.error(f"Stripe create payment error: {str(e)}")
            raise PaymentGatewayError(f"Failed to create payment: {str(e)}")
    
    def verify_payment(self, payment_id: str, signature: str, metadata: Dict[str, Any]) -> bool:
        """
        Verify a Stripe payment.
        
        Args:
            payment_id: The Stripe payment intent ID
            signature: Not used for Stripe (use empty string)
            metadata: Additional data (not required for Stripe verification)
            
        Returns:
            Boolean indicating if payment is valid
        """
        try:
            # Retrieve the payment intent to check its status
            intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # Payment is successful if status is 'succeeded'
            return intent.status == 'succeeded'
        except Exception as e:
            logger.error(f"Stripe payment verification error: {str(e)}")
            return False
    
    def process_refund(self, payment_id: str, amount: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund for a Stripe payment.
        
        Args:
            payment_id: The Stripe payment intent ID to refund
            amount: The refund amount
            metadata: Additional data for the refund
            
        Returns:
            Dict containing refund details
        """
        try:
            # Convert amount to smallest currency unit
            amount_in_smallest_unit = int(amount * 100)
            
            # Create a refund
            refund = stripe.Refund.create(
                payment_intent=payment_id,
                amount=amount_in_smallest_unit,
                metadata=metadata
            )
            
            return {
                'refund_id': refund.id,
                'amount': amount,
                'status': refund.status,
                'gateway_data': {
                    'id': refund.id,
                    'status': refund.status
                }
            }
        except Exception as e:
            logger.error(f"Stripe refund error: {str(e)}")
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the current status of a Stripe payment.
        
        Args:
            payment_id: The Stripe payment intent ID to check
            
        Returns:
            Dict containing payment status details
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # Map Stripe status to our internal status
            status_mapping = {
                'requires_payment_method': 'PENDING',
                'requires_confirmation': 'PENDING',
                'requires_action': 'PENDING',
                'processing': 'PROCESSING',
                'requires_capture': 'PROCESSING',
                'succeeded': 'COMPLETED',
                'canceled': 'CANCELLED'
            }
            
            internal_status = status_mapping.get(intent.status, 'PENDING')
            
            return {
                'payment_id': payment_id,
                'status': internal_status,
                'amount': float(intent.amount) / 100,  # Convert from smallest unit
                'currency': intent.currency.upper(),
                'gateway_data': {
                    'id': intent.id,
                    'status': intent.status
                }
            }
        except Exception as e:
            logger.error(f"Stripe get payment status error: {str(e)}")
            raise PaymentGatewayError(f"Failed to get payment status: {str(e)}")
    
    def generate_payment_link(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a Stripe checkout session URL.
        
        Args:
            amount: The payment amount
            currency: The currency code
            order_id: The order identifier
            metadata: Additional data for the payment link
            
        Returns:
            String URL for the payment
        """
        try:
            # Convert amount to smallest currency unit
            amount_in_smallest_unit = int(amount * 100)
            
            # Get success and cancel URLs from metadata
            success_url = metadata.get('success_url', settings.PAYMENT_SUCCESS_URL)
            cancel_url = metadata.get('cancel_url', settings.PAYMENT_CANCEL_URL)
            
            # Create a checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': f"Order #{order_id}",
                            'description': metadata.get('description', f"Payment for Order #{order_id}")
                        },
                        'unit_amount': amount_in_smallest_unit,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'order_id': order_id,
                    **metadata
                }
            )
            
            return session.url
        except Exception as e:
            logger.error(f"Stripe generate payment link error: {str(e)}")
            raise PaymentGatewayError(f"Failed to generate payment link: {str(e)}")