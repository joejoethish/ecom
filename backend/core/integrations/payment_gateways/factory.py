"""
Payment gateway factory for selecting the appropriate gateway.
"""
from typing import Dict, Any, Optional

from .base import BasePaymentGateway
from .razorpay_gateway import RazorpayGateway
from .stripe_gateway import StripeGateway
from core.exceptions import PaymentGatewayError


class PaymentGatewayFactory:
    """
    Factory class for creating payment gateway instances.
    """
    
    @staticmethod
    def get_gateway(gateway_name: str) -> BasePaymentGateway:
        """
        Get the appropriate payment gateway instance based on the name.
        
        Args:
            gateway_name: The name of the payment gateway ('RAZORPAY', 'STRIPE')
            
        Returns:
            An instance of the requested payment gateway
            
        Raises:
            PaymentGatewayError: If the requested gateway is not supported
        """
        gateway_name = gateway_name.upper()
        
        if gateway_name == 'RAZORPAY':
            return RazorpayGateway()
        elif gateway_name == 'STRIPE':
            return StripeGateway()
        else:
            raise PaymentGatewayError(f"Unsupported payment gateway: {gateway_name}")