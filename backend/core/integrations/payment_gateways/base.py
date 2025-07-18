"""
Base payment gateway integration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePaymentGateway(ABC):
    """
    Abstract base class for payment gateway integrations.
    """
    
    @abstractmethod
    def create_payment(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment in the payment gateway.
        
        Args:
            amount: The payment amount
            currency: The currency code (e.g., USD, INR)
            order_id: The order identifier
            metadata: Additional data for the payment
            
        Returns:
            Dict containing payment details including gateway payment ID
        """
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id: str, signature: str, metadata: Dict[str, Any]) -> bool:
        """
        Verify a payment using gateway-specific verification.
        
        Args:
            payment_id: The payment ID from the gateway
            signature: The signature or token for verification
            metadata: Additional data for verification
            
        Returns:
            Boolean indicating if payment is valid
        """
        pass
    
    @abstractmethod
    def process_refund(self, payment_id: str, amount: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund for a payment.
        
        Args:
            payment_id: The payment ID to refund
            amount: The refund amount
            metadata: Additional data for the refund
            
        Returns:
            Dict containing refund details
        """
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the current status of a payment.
        
        Args:
            payment_id: The payment ID to check
            
        Returns:
            Dict containing payment status details
        """
        pass
    
    @abstractmethod
    def generate_payment_link(self, amount: float, currency: str, order_id: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a payment link for the customer.
        
        Args:
            amount: The payment amount
            currency: The currency code
            order_id: The order identifier
            metadata: Additional data for the payment link
            
        Returns:
            String URL for the payment
        """
        pass