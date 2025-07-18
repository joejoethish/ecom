"""
Razorpay payment gateway integration.
"""
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from django.conf import settings
import razorpay

from .base import BasePaymentGateway
from core.exceptions import PaymentGatewayError

logger = logging.getLogger(__name__)


class RazorpayGateway(BasePaymentGateway):
    """
    Razorpay payment gateway implementation.
    """
    
    def __init__(self):
        """
        Initialize Razorpay client with API credentials.
        """
        try:
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
            raise PaymentGatewayError("Failed to initialize payment gateway")
    
    def create_payment(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment order in Razorpay.
        
        Args:
            amount: The payment amount (in smallest currency unit, e.g., paise for INR)
            currency: The currency code (e.g., INR)
            order_id: The order identifier
            metadata: Additional data for the payment
            
        Returns:
            Dict containing payment details including gateway payment ID
        """
        try:
            # Razorpay expects amount in smallest currency unit (paise for INR)
            amount_in_smallest_unit = int(amount * 100)
            
            receipt = f"order_{order_id}"
            notes = {
                "order_id": order_id,
                **metadata
            }
            
            order_data = {
                'amount': amount_in_smallest_unit,
                'currency': currency,
                'receipt': receipt,
                'notes': notes,
            }
            
            razorpay_order = self.client.order.create(data=order_data)
            
            return {
                'gateway_order_id': razorpay_order['id'],
                'amount': amount,
                'currency': currency,
                'gateway_data': razorpay_order
            }
        except Exception as e:
            logger.error(f"Razorpay create payment error: {str(e)}")
            raise PaymentGatewayError(f"Failed to create payment: {str(e)}")
    
    def verify_payment(self, payment_id: str, signature: str, metadata: Dict[str, Any]) -> bool:
        """
        Verify a Razorpay payment using signature verification.
        
        Args:
            payment_id: The payment ID from Razorpay
            signature: The Razorpay signature
            metadata: Additional data including order_id
            
        Returns:
            Boolean indicating if payment is valid
        """
        try:
            order_id = metadata.get('razorpay_order_id')
            if not order_id:
                logger.error("Missing order_id in metadata for payment verification")
                return False
            
            # Create parameters dict for signature verification
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            # Verify the payment signature
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            logger.error(f"Razorpay payment verification error: {str(e)}")
            return False
    
    def process_refund(self, payment_id: str, amount: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund for a Razorpay payment.
        
        Args:
            payment_id: The Razorpay payment ID to refund
            amount: The refund amount
            metadata: Additional data for the refund
            
        Returns:
            Dict containing refund details
        """
        try:
            # Convert amount to smallest currency unit
            amount_in_smallest_unit = int(amount * 100)
            
            refund_data = {
                'amount': amount_in_smallest_unit,
                'notes': metadata
            }
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'refund_id': refund['id'],
                'amount': amount,
                'status': refund['status'],
                'gateway_data': refund
            }
        except Exception as e:
            logger.error(f"Razorpay refund error: {str(e)}")
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the current status of a Razorpay payment.
        
        Args:
            payment_id: The Razorpay payment ID to check
            
        Returns:
            Dict containing payment status details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            
            # Map Razorpay status to our internal status
            status_mapping = {
                'created': 'PENDING',
                'authorized': 'PROCESSING',
                'captured': 'COMPLETED',
                'refunded': 'REFUNDED',
                'failed': 'FAILED'
            }
            
            internal_status = status_mapping.get(payment['status'], 'PENDING')
            
            return {
                'payment_id': payment_id,
                'status': internal_status,
                'amount': float(payment['amount']) / 100,  # Convert from smallest unit
                'currency': payment['currency'],
                'gateway_data': payment
            }
        except Exception as e:
            logger.error(f"Razorpay get payment status error: {str(e)}")
            raise PaymentGatewayError(f"Failed to get payment status: {str(e)}")
    
    def generate_payment_link(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a Razorpay payment link for the customer.
        
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
            
            # Create a payment link
            customer_data = metadata.get('customer', {})
            
            payment_link_data = {
                'amount': amount_in_smallest_unit,
                'currency': currency,
                'accept_partial': False,
                'description': f"Payment for Order #{order_id}",
                'customer': {
                    'name': customer_data.get('name', ''),
                    'email': customer_data.get('email', ''),
                    'contact': customer_data.get('phone', '')
                },
                'notify': {
                    'sms': True,
                    'email': True
                },
                'reminder_enable': True,
                'notes': {
                    'order_id': order_id,
                    **metadata
                }
            }
            
            payment_link = self.client.payment_link.create(payment_link_data)
            
            return payment_link['short_url']
        except Exception as e:
            logger.error(f"Razorpay generate payment link error: {str(e)}")
            raise PaymentGatewayError(f"Failed to generate payment link: {str(e)}")