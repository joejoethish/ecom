"""
Utilities for API documentation.

This module provides utilities for documenting API endpoints using drf-spectacular.
It includes decorators for documenting different types of views, helpers for creating
examples, and utilities for handling API versioning in documentation.
"""
from functools import wraps
import inspect
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse, OpenApiTypes
from drf_spectacular.plumbing import build_basic_type
from rest_framework import status
from django.conf import settings


def document_api(
    summary=None,
    description=None,
    responses=None,
    request=None,
    parameters=None,
    examples=None,
    tags=None,
    operation_id=None,
    deprecated=False,
    auth=None,
    versions=None,
):
    """
    Decorator for documenting API views.
    
    Args:
        summary: Short summary of the endpoint
        description: Detailed description of the endpoint
        responses: Dictionary mapping status codes to response serializers
        request: Request serializer
        parameters: List of OpenApiParameter objects
        examples: Dictionary mapping names to OpenApiExample objects
        tags: List of tags for the endpoint
        operation_id: Unique operation ID
        deprecated: Whether the endpoint is deprecated
        auth: Authentication requirements (list of auth types or None for no auth)
        versions: List of API versions that support this endpoint
    
    Returns:
        Decorated function
    """
    # Add version information to description if provided
    if versions:
        version_text = f"\n\n**Supported API Versions:** {', '.join(versions)}"
        if description:
            description = description + version_text
        else:
            description = version_text
    
    # Add deprecation notice if endpoint is deprecated
    if deprecated:
        deprecation_text = "\n\n**DEPRECATED:** This endpoint is deprecated and will be removed in a future version."
        if description:
            description = description + deprecation_text
        else:
            description = deprecation_text
    
    # Add standard error responses if not provided
    if responses is None:
        responses = {}
    
    # Add standard error responses if not already included
    standard_errors = get_standard_error_responses()
    for status_code, response in standard_errors.items():
        if status_code not in responses:
            responses[status_code] = response
    
    def decorator(func):
        return extend_schema(
            summary=summary,
            description=description,
            responses=responses,
            request=request,
            parameters=parameters,
            examples=examples,
            tags=tags,
            operation_id=operation_id,
            deprecated=deprecated,
            auth=auth,
        )(func)
    return decorator


def paginated_response(serializer_class):
    """
    Helper for documenting paginated responses.
    
    Args:
        serializer_class: Serializer class for the paginated items
    
    Returns:
        Dictionary for use with extend_schema responses
    """
    return {
        status.HTTP_200_OK: serializer_class,
    }


def common_parameters():
    """
    Common parameters used across multiple endpoints.
    
    Returns:
        List of OpenApiParameter objects
    """
    return [
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Page number for paginated results",
            required=False,
            examples=[
                OpenApiExample(
                    name="First page",
                    value=1,
                    description="Get the first page of results"
                ),
                OpenApiExample(
                    name="Second page",
                    value=2,
                    description="Get the second page of results"
                ),
            ]
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Number of items per page (max: 100)",
            required=False,
            examples=[
                OpenApiExample(
                    name="Default page size",
                    value=20,
                    description="Default number of items per page"
                ),
                OpenApiExample(
                    name="Maximum page size",
                    value=100,
                    description="Maximum number of items per page"
                ),
            ]
        ),
    ]


def filter_parameters(filters):
    """
    Generate filter parameters for an endpoint.
    
    Args:
        filters: Dictionary mapping filter names to types and descriptions
    
    Returns:
        List of OpenApiParameter objects
    """
    parameters = []
    for name, config in filters.items():
        parameter = OpenApiParameter(
            name=name,
            type=config.get("type", OpenApiTypes.STR),
            location=OpenApiParameter.QUERY,
            description=config.get("description", ""),
            required=config.get("required", False),
        )
        
        # Add examples if provided
        if "examples" in config:
            parameter.examples = [
                OpenApiExample(
                    name=example.get("name", f"Example {i+1}"),
                    value=example.get("value"),
                    description=example.get("description", "")
                )
                for i, example in enumerate(config["examples"])
            ]
        
        parameters.append(parameter)
    
    return parameters


def create_examples(examples_dict):
    """
    Create OpenApiExample objects from a dictionary.
    
    Args:
        examples_dict: Dictionary mapping names to example configurations
    
    Returns:
        Dictionary mapping names to OpenApiExample objects
    """
    result = {}
    for name, config in examples_dict.items():
        result[name] = OpenApiExample(
            name=name,
            value=config.get("value"),
            summary=config.get("summary", ""),
            description=config.get("description", ""),
            request_only=config.get("request_only", False),
            response_only=config.get("response_only", False),
        )
    return result


def auto_schema(view_class=None, **kwargs):
    """
    Decorator for automatically documenting API views based on class attributes.
    
    This decorator examines the view class and automatically generates documentation
    based on serializers, permissions, and other attributes.
    
    Args:
        view_class: View class to document (optional, defaults to decorated class)
        **kwargs: Additional arguments to pass to extend_schema
    
    Returns:
        Decorated class
    """
    def decorator(cls):
        # Get view methods that need documentation
        methods = ['get', 'post', 'put', 'patch', 'delete']
        
        # Document each method if it exists
        for method_name in methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                
                # Get method-specific documentation
                method_kwargs = {}
                
                # Add summary based on method name and class name
                if 'summary' not in kwargs:
                    action = getattr(cls, 'action', method_name)
                    resource = cls.__name__.replace('ViewSet', '').replace('View', '')
                    
                    if action == 'list':
                        method_kwargs['summary'] = f"List {resource}s"
                    elif action == 'retrieve':
                        method_kwargs['summary'] = f"Get {resource} details"
                    elif action == 'create':
                        method_kwargs['summary'] = f"Create a new {resource}"
                    elif action == 'update':
                        method_kwargs['summary'] = f"Update {resource}"
                    elif action == 'partial_update':
                        method_kwargs['summary'] = f"Partially update {resource}"
                    elif action == 'destroy':
                        method_kwargs['summary'] = f"Delete {resource}"
                
                # Merge with provided kwargs
                method_kwargs.update(kwargs)
                
                # Apply documentation
                setattr(cls, method_name, extend_schema(**method_kwargs)(method))
        
        return cls
    
    # Handle case where decorator is used without parentheses
    if view_class is not None:
        return decorator(view_class)
    
    return decorator


def get_standard_error_responses():
    """
    Get standard error responses for API documentation.
    
    Returns:
        Dictionary mapping status codes to OpenApiResponse objects
    """
    return {
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad request - validation error",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "code": {"type": "string"},
                            "fields": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            examples=[
                OpenApiExample(
                    name="Validation Error",
                    value={
                        "error": {
                            "message": "Validation error",
                            "code": "validation_error",
                            "fields": {
                                "name": ["This field is required."],
                                "price": ["Ensure this value is greater than or equal to 0.01."]
                            }
                        }
                    },
                    response_only=True,
                )
            ]
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Unauthorized - authentication required",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "code": {"type": "string"}
                        }
                    }
                }
            },
            examples=[
                OpenApiExample(
                    name="Authentication Required",
                    value={
                        "error": {
                            "message": "Authentication credentials were not provided.",
                            "code": "authentication_required"
                        }
                    },
                    response_only=True,
                )
            ]
        ),
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Forbidden - insufficient permissions",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "code": {"type": "string"}
                        }
                    }
                }
            },
            examples=[
                OpenApiExample(
                    name="Permission Denied",
                    value={
                        "error": {
                            "message": "You do not have permission to perform this action.",
                            "code": "permission_denied"
                        }
                    },
                    response_only=True,
                )
            ]
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="Not found - resource does not exist",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "code": {"type": "string"}
                        }
                    }
                }
            },
            examples=[
                OpenApiExample(
                    name="Resource Not Found",
                    value={
                        "error": {
                            "message": "The requested resource was not found.",
                            "code": "not_found"
                        }
                    },
                    response_only=True,
                )
            ]
        ),
        status.HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
            description="Too many requests - rate limit exceeded",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "code": {"type": "string"},
                            "retry_after": {"type": "integer"}
                        }
                    }
                }
            },
            examples=[
                OpenApiExample(
                    name="Rate Limit Exceeded",
                    value={
                        "error": {
                            "message": "Rate limit exceeded",
                            "code": "rate_limit_exceeded",
                            "retry_after": 60
                        }
                    },
                    response_only=True,
                )
            ]
        ),
    }


def get_api_versions():
    """
    Get list of API versions from settings.
    
    Returns:
        List of API versions
    """
    return getattr(settings, 'API_VERSIONS', ['v1', 'v2'])


def get_current_api_version():
    """
    Get current recommended API version from settings.
    
    Returns:
        Current API version
    """
    return getattr(settings, 'RECOMMENDED_API_VERSION', 'v2')


def get_deprecated_api_versions():
    """
    Get list of deprecated API versions from settings.
    
    Returns:
        List of deprecated API versions
    """
    return getattr(settings, 'DEPRECATED_API_VERSIONS', [])


def document_auth_view(view_func):
    """
    Decorator for documenting authentication views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add authentication tag
    wrapper = extend_schema(tags=["Authentication"])(wrapper)
    
    return wrapper


def document_product_view(view_func):
    """
    Decorator for documenting product views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add product tag
    wrapper = extend_schema(tags=["Products"])(wrapper)
    
    return wrapper


def document_order_view(view_func):
    """
    Decorator for documenting order views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add order tag
    wrapper = extend_schema(tags=["Orders"])(wrapper)
    
    return wrapper


def document_cart_view(view_func):
    """
    Decorator for documenting cart views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add cart tag
    wrapper = extend_schema(tags=["Cart"])(wrapper)
    
    return wrapper


def document_payment_view(view_func):
    """
    Decorator for documenting payment views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add payment tag
    wrapper = extend_schema(tags=["Payments"])(wrapper)
    
    return wrapper


def document_shipping_view(view_func):
    """
    Decorator for documenting shipping views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add shipping tag
    wrapper = extend_schema(tags=["Shipping"])(wrapper)
    
    return wrapper


def document_customer_view(view_func):
    """
    Decorator for documenting customer views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add customer tag
    wrapper = extend_schema(tags=["Customers"])(wrapper)
    
    return wrapper


def document_seller_view(view_func):
    """
    Decorator for documenting seller views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add seller tag
    wrapper = extend_schema(tags=["Sellers"])(wrapper)
    
    return wrapper


def document_analytics_view(view_func):
    """
    Decorator for documenting analytics views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add analytics tag
    wrapper = extend_schema(tags=["Analytics"])(wrapper)
    
    return wrapper


def document_content_view(view_func):
    """
    Decorator for documenting content views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add content tag
    wrapper = extend_schema(tags=["Content"])(wrapper)
    
    return wrapper


def document_review_view(view_func):
    """
    Decorator for documenting review views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add review tag
    wrapper = extend_schema(tags=["Reviews"])(wrapper)
    
    return wrapper


def document_search_view(view_func):
    """
    Decorator for documenting search views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add search tag
    wrapper = extend_schema(tags=["Search"])(wrapper)
    
    return wrapper


def document_notification_view(view_func):
    """
    Decorator for documenting notification views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add notification tag
    wrapper = extend_schema(tags=["Notifications"])(wrapper)
    
    return wrapper


def document_versioning_view(view_func):
    """
    Decorator for documenting versioning views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add versioning tag
    wrapper = extend_schema(tags=["Versioning"])(wrapper)
    
    return wrapper


def document_inventory_view(view_func):
    """
    Decorator for documenting inventory views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add inventory tag
    wrapper = extend_schema(tags=["Inventory"])(wrapper)
    
    return wrapper


def document_webhook_view(view_func):
    """
    Decorator for documenting webhook views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add webhook tag
    wrapper = extend_schema(tags=["Webhooks"])(wrapper)
    
    return wrapper


def document_admin_view(view_func):
    """
    Decorator for documenting admin views.
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    # Add admin tag
    wrapper = extend_schema(tags=["Admin"])(wrapper)
    
    return wrapper