"""
Custom exception handlers and exceptions for the ecommerce platform.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class EcommerceException(Exception):
    """Base exception class for ecommerce-specific errors."""
    default_message = "An error occurred"
    default_code = "error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class ValidationError(EcommerceException):
    """Exception for validation errors."""
    default_message = "Validation failed"
    default_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundError(EcommerceException):
    """Exception for resource not found errors."""
    default_message = "Resource not found"
    default_code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class PermissionError(EcommerceException):
    """Exception for permission denied errors."""
    default_message = "Permission denied"
    default_code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN


class AuthenticationError(EcommerceException):
    """Exception for authentication errors."""
    default_message = "Authentication failed"
    default_code = "authentication_failed"
    status_code = status.HTTP_401_UNAUTHORIZED


class BusinessLogicError(EcommerceException):
    """Exception for business logic violations."""
    default_message = "Business logic error"
    default_code = "business_logic_error"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class PaymentGatewayError(EcommerceException):
    """Exception for payment gateway errors."""
    default_message = "Payment gateway error"
    default_code = "payment_gateway_error"
    status_code = status.HTTP_502_BAD_GATEWAY


class InsufficientFundsError(EcommerceException):
    """Exception for insufficient funds errors."""
    default_message = "Insufficient funds"
    default_code = "insufficient_funds"
    status_code = status.HTTP_400_BAD_REQUEST


class PaymentProcessingError(EcommerceException):
    """Exception for payment processing errors."""
    default_message = "Payment processing error"
    default_code = "payment_processing_error"
    status_code = status.HTTP_400_BAD_REQUEST


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Check if this is an authentication-related request
    request = context.get('request')
    if request and _is_authentication_request(request):
        # Use authentication-specific error handler
        from apps.authentication.error_handlers import authentication_exception_handler
        auth_response = authentication_exception_handler(exc, context)
        if auth_response:
            return auth_response
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the exception
        logger.error(f"API Exception: {exc}", exc_info=True)
        
        # Customize the response format
        custom_response_data = {
            'error': {
                'message': str(exc),
                'code': getattr(exc, 'code', 'error'),
                'status_code': response.status_code,
                'details': response.data if hasattr(response, 'data') else None
            },
            'success': False
        }
        
        response.data = custom_response_data

    # Handle custom ecommerce exceptions
    elif isinstance(exc, EcommerceException):
        logger.error(f"Ecommerce Exception: {exc}", exc_info=True)
        
        custom_response_data = {
            'error': {
                'message': exc.message,
                'code': exc.code,
                'status_code': exc.status_code
            },
            'success': False
        }
        
        response = Response(custom_response_data, status=exc.status_code)

    return response


def _is_authentication_request(request):
    """Check if the request is authentication-related."""
    auth_paths = [
        '/api/v1/auth/',
        '/api/v1/admin-auth/',
        '/api/v1/users/me/',
        '/api/v1/users/',
    ]
    return any(request.path.startswith(path) for path in auth_paths)