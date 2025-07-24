"""
Business metrics logging utilities for the ecommerce platform.
"""
import logging
import json
from django.utils import timezone
from django.conf import settings

# Create a dedicated metrics logger
metrics_logger = logging.getLogger('metrics')


def log_order_placed(order_id, user_id, total_amount, item_count, payment_method, 
                    coupon_applied=False, dimensions=None):
    """
    Log an order placement metric.
    
    Args:
        order_id: ID of the order
        user_id: ID of the user who placed the order
        total_amount: Total order amount
        item_count: Number of items in the order
        payment_method: Payment method used
        coupon_applied: Whether a coupon was applied
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'order_placed',
        'metric_value': float(total_amount),
        'dimensions': dimensions or {},
        'order_id': order_id,
        'user_id': user_id,
        'item_count': item_count,
        'payment_method': payment_method,
        'coupon_applied': coupon_applied,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Order placed: #{order_id} for {total_amount} with {item_count} items",
        extra=extra
    )


def log_product_view(product_id, user_id, category_id, source=None, dimensions=None):
    """
    Log a product view metric.
    
    Args:
        product_id: ID of the product viewed
        user_id: ID of the user (or None for anonymous)
        category_id: ID of the product's category
        source: Source of the view (search, category, recommendation, etc.)
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'product_view',
        'metric_value': 1,
        'dimensions': dimensions or {},
        'product_id': product_id,
        'user_id': user_id,
        'category_id': category_id,
        'source': source,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Product viewed: #{product_id} by user {user_id or 'anonymous'} from {source or 'direct'}",
        extra=extra
    )


def log_cart_action(action, user_id, product_id=None, quantity=None, cart_value=None, dimensions=None):
    """
    Log a cart action metric.
    
    Args:
        action: The action (add, remove, update, clear)
        user_id: ID of the user
        product_id: ID of the product (for add, remove, update)
        quantity: Quantity (for add, update)
        cart_value: Total cart value after the action
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': f'cart_{action}',
        'metric_value': quantity or 1,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'product_id': product_id,
        'cart_value': float(cart_value) if cart_value is not None else None,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Cart {action}: User {user_id} {action}ed" + 
        (f" product #{product_id}" if product_id else "") + 
        (f" (quantity: {quantity})" if quantity else ""),
        extra=extra
    )


def log_search(query, user_id, results_count, filters=None, dimensions=None):
    """
    Log a search metric.
    
    Args:
        query: Search query
        user_id: ID of the user (or None for anonymous)
        results_count: Number of search results
        filters: Filters applied to the search
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'search',
        'metric_value': results_count,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'query': query,
        'filters': filters or {},
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Search: User {user_id or 'anonymous'} searched for '{query}' with {results_count} results",
        extra=extra
    )


def log_checkout_step(step, user_id, cart_value, completed=True, dimensions=None):
    """
    Log a checkout step metric.
    
    Args:
        step: Checkout step name (address, shipping, payment, review)
        user_id: ID of the user
        cart_value: Cart value
        completed: Whether the step was completed successfully
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'checkout_step',
        'metric_value': 1,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'step': step,
        'cart_value': float(cart_value),
        'completed': completed,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Checkout step: User {user_id} {step} step {'completed' if completed else 'abandoned'}",
        extra=extra
    )


def log_user_registration(user_id, source=None, dimensions=None):
    """
    Log a user registration metric.
    
    Args:
        user_id: ID of the newly registered user
        source: Registration source (direct, social, referral, etc.)
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'user_registration',
        'metric_value': 1,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'source': source,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"User registration: New user {user_id} registered via {source or 'direct'}",
        extra=extra
    )


def log_revenue(amount, order_id, user_id, category=None, dimensions=None):
    """
    Log a revenue metric.
    
    Args:
        amount: Revenue amount
        order_id: ID of the order
        user_id: ID of the user
        category: Revenue category (product, shipping, tax, etc.)
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'revenue',
        'metric_value': float(amount),
        'dimensions': dimensions or {},
        'order_id': order_id,
        'user_id': user_id,
        'category': category or 'product',
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Revenue: {amount} from order #{order_id} ({category or 'product'})",
        extra=extra
    )


def log_inventory_change(product_id, quantity_change, reason, current_stock, dimensions=None):
    """
    Log an inventory change metric.
    
    Args:
        product_id: ID of the product
        quantity_change: Change in quantity (positive for additions, negative for reductions)
        reason: Reason for the change (order, restock, adjustment, etc.)
        current_stock: Current stock level after the change
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'inventory_change',
        'metric_value': quantity_change,
        'dimensions': dimensions or {},
        'product_id': product_id,
        'reason': reason,
        'current_stock': current_stock,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Inventory change: Product #{product_id} {quantity_change:+d} ({reason}), current stock: {current_stock}",
        extra=extra
    )


def log_page_view(page, user_id, session_id, referrer=None, dimensions=None):
    """
    Log a page view metric.
    
    Args:
        page: Page path
        user_id: ID of the user (or None for anonymous)
        session_id: Session ID
        referrer: Referrer URL
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'page_view',
        'metric_value': 1,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'page': page,
        'session_id': session_id,
        'referrer': referrer,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"Page view: {page} by user {user_id or 'anonymous'}",
        extra=extra
    )


def log_api_request(endpoint, method, user_id, response_time, status_code, dimensions=None):
    """
    Log an API request metric.
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        user_id: ID of the user (or None for anonymous)
        response_time: Response time in milliseconds
        status_code: HTTP status code
        dimensions: Additional dimensions for the metric
    """
    extra = {
        'metric_name': 'api_request',
        'metric_value': response_time,
        'dimensions': dimensions or {},
        'user_id': user_id,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'timestamp': timezone.now().isoformat(),
    }
    
    metrics_logger.info(
        f"API request: {method} {endpoint} responded {status_code} in {response_time}ms",
        extra=extra
    )