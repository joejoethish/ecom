"""
Comprehensive Order services for the admin panel.
"""
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F, Case, When, Value
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from datetime import datetime, timedelta

from apps.orders.models import Order, OrderItem, OrderTracking
from .order_models import (
    OrderSearchFilter, OrderWorkflow, OrderFraudScore, OrderNote,
    OrderEscalation, OrderSLA, OrderAllocation, OrderProfitability,
    OrderDocument, OrderQualityControl, OrderSubscription
)

User = get_user_model()
logger = logging.getLogger(__name__)


class OrderSearchService:
    """Service for advanced order search and filtering capabilities."""
    
    @staticmethod
    def search_orders(filters: Dict[str, Any], user: User = None) -> Dict[str, Any]:
        """
        Advanced order search with multiple criteria and saved searches.
        """
        queryset = Order.objects.select_related(
            'customer', 'shipping_address', 'billing_address'
        ).prefetch_related('items', 'tracking', 'admin_notes')
        
        # Apply filters
        if filters.get('order_number'):
            queryset = queryset.filter(order_number__icontains=filters['order_number'])
        
        if filters.get('customer_email'):
            queryset = queryset.filter(customer__email__icontains=filters['customer_email'])
        
        if filters.get('status'):
            if isinstance(filters['status'], list):
                queryset = queryset.filter(status__in=filters['status'])
            else:
                queryset = queryset.filter(status=filters['status'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        if filters.get('total_min'):
            queryset = queryset.filter(total_amount__gte=filters['total_min'])
        
        if filters.get('total_max'):
            queryset = queryset.filter(total_amount__lte=filters['total_max'])
        
        if filters.get('payment_status'):
            queryset = queryset.filter(payment_status=filters['payment_status'])
        
        if filters.get('shipping_method'):
            queryset = queryset.filter(shipping_method=filters['shipping_method'])
        
        if filters.get('has_fraud_alert'):
            queryset = queryset.filter(fraud_score__is_flagged=True)
        
        if filters.get('has_escalation'):
            queryset = queryset.filter(escalations__status__in=['open', 'in_progress'])
        
        if filters.get('sla_breached'):
            queryset = queryset.filter(sla_tracking__overall_sla_met=False)
        
        # Advanced text search across multiple fields
        if filters.get('search_text'):
            search_text = filters['search_text']
            queryset = queryset.filter(
                Q(order_number__icontains=search_text) |
                Q(customer__email__icontains=search_text) |
                Q(customer__first_name__icontains=search_text) |
                Q(customer__last_name__icontains=search_text) |
                Q(shipping_address__city__icontains=search_text) |
                Q(items__product__name__icontains=search_text)
            ).distinct()
        
        # Sorting
        sort_by = filters.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        # Pagination
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 25)
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        orders = list(queryset[start:end])
        
        return {
            'orders': orders,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    
    @staticmethod
    def save_search_filter(name: str, filters: Dict[str, Any], user: User, is_public: bool = False) -> OrderSearchFilter:
        """Save search filters for quick access."""
        search_filter, created = OrderSearchFilter.objects.update_or_create(
            name=name,
            admin_user=user,
            defaults={
                'filters': filters,
                'is_public': is_public
            }
        )
        return search_filter
    
    @staticmethod
    def get_saved_filters(user: User) -> List[OrderSearchFilter]:
        """Get saved search filters for user."""
        return OrderSearchFilter.objects.filter(
            Q(admin_user=user) | Q(is_public=True)
        ).order_by('name')


class OrderStatusService:
    """Service for order status management with custom workflows."""
    
    @staticmethod
    def update_order_status(order: Order, new_status: str, user: User, notes: str = "") -> bool:
        """
        Update order status with workflow validation and automation.
        """
        try:
            with transaction.atomic():
                old_status = order.status
                
                # Check if status change is allowed
                if not OrderStatusService._is_status_change_allowed(old_status, new_status):
                    raise ValidationError(f"Status change from {old_status} to {new_status} is not allowed")
                
                # Apply workflow rules
                workflows = OrderWorkflow.objects.filter(
                    from_status=old_status,
                    to_status=new_status,
                    is_active=True
                ).order_by('-priority')
                
                for workflow in workflows:
                    if OrderStatusService._check_workflow_conditions(order, workflow):
                        OrderStatusService._execute_workflow_actions(order, workflow, user)
                
                # Update order status
                order.status = new_status
                order.save()
                
                # Create status change note
                if notes or old_status != new_status:
                    OrderNote.objects.create(
                        order=order,
                        note_type='system',
                        title=f'Status changed from {old_status} to {new_status}',
                        content=notes or f'Status automatically changed by workflow',
                        created_by=user
                    )
                
                # Update SLA tracking
                if hasattr(order, 'sla_tracking'):
                    order.sla_tracking.calculate_sla_status()
                
                logger.info(f"Order {order.order_number} status changed from {old_status} to {new_status} by {user.username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update order {order.order_number} status: {str(e)}")
            raise
    
    @staticmethod
    def _is_status_change_allowed(from_status: str, to_status: str) -> bool:
        """Check if status change is allowed based on business rules."""
        # Define allowed status transitions
        allowed_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled', 'on_hold'],
            'shipped': ['delivered', 'returned'],
            'delivered': ['returned', 'completed'],
            'on_hold': ['processing', 'cancelled'],
            'cancelled': [],  # Cannot change from cancelled
            'returned': ['refunded', 'exchanged'],
            'refunded': [],
            'exchanged': ['completed'],
            'completed': []
        }
        
        return to_status in allowed_transitions.get(from_status, [])
    
    @staticmethod
    def _check_workflow_conditions(order: Order, workflow: OrderWorkflow) -> bool:
        """Check if workflow conditions are met."""
        conditions = workflow.conditions
        
        # Example condition checks
        if 'min_amount' in conditions:
            if order.total_amount < Decimal(str(conditions['min_amount'])):
                return False
        
        if 'payment_required' in conditions:
            if conditions['payment_required'] and order.payment_status != 'paid':
                return False
        
        if 'inventory_available' in conditions:
            if conditions['inventory_available']:
                # Check if all items have sufficient inventory
                for item in order.items.all():
                    if item.product.stock_quantity < item.quantity:
                        return False
        
        return True
    
    @staticmethod
    def _execute_workflow_actions(order: Order, workflow: OrderWorkflow, user: User):
        """Execute workflow actions."""
        actions = workflow.actions
        
        for action in actions:
            action_type = action.get('type')
            
            if action_type == 'send_email':
                # Send email notification
                OrderNotificationService.send_status_change_email(order, action.get('template'))
            
            elif action_type == 'create_note':
                OrderNote.objects.create(
                    order=order,
                    note_type='system',
                    title=action.get('title', 'Workflow Action'),
                    content=action.get('content', ''),
                    created_by=user
                )
            
            elif action_type == 'allocate_inventory':
                OrderAllocationService.allocate_order_inventory(order)
            
            elif action_type == 'create_escalation':
                OrderEscalationService.create_escalation(
                    order=order,
                    escalation_type=action.get('escalation_type', 'manual_review'),
                    title=action.get('title', 'Workflow Escalation'),
                    description=action.get('description', ''),
                    priority=action.get('priority', 'medium'),
                    created_by=user
                )


class OrderModificationService:
    """Service for order modification capabilities."""
    
    @staticmethod
    def add_item_to_order(order: Order, product_id: int, quantity: int, user: User) -> OrderItem:
        """Add item to existing order."""
        try:
            with transaction.atomic():
                from apps.products.models import Product
                
                product = Product.objects.get(id=product_id)
                
                # Check if item already exists in order
                existing_item = order.items.filter(product=product).first()
                if existing_item:
                    existing_item.quantity += quantity
                    existing_item.save()
                    item = existing_item
                else:
                    item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                
                # Recalculate order totals
                OrderModificationService._recalculate_order_totals(order)
                
                # Create modification note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Item Added to Order',
                    content=f'Added {quantity}x {product.name} to order',
                    created_by=user
                )
                
                logger.info(f"Added item {product.name} to order {order.order_number}")
                return item
                
        except Exception as e:
            logger.error(f"Failed to add item to order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def remove_item_from_order(order: Order, item_id: int, user: User) -> bool:
        """Remove item from order."""
        try:
            with transaction.atomic():
                item = order.items.get(id=item_id)
                product_name = item.product.name
                quantity = item.quantity
                
                item.delete()
                
                # Recalculate order totals
                OrderModificationService._recalculate_order_totals(order)
                
                # Create modification note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Item Removed from Order',
                    content=f'Removed {quantity}x {product_name} from order',
                    created_by=user
                )
                
                logger.info(f"Removed item {product_name} from order {order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove item from order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def update_item_quantity(order: Order, item_id: int, new_quantity: int, user: User) -> OrderItem:
        """Update item quantity in order."""
        try:
            with transaction.atomic():
                item = order.items.get(id=item_id)
                old_quantity = item.quantity
                
                if new_quantity <= 0:
                    return OrderModificationService.remove_item_from_order(order, item_id, user)
                
                item.quantity = new_quantity
                item.save()
                
                # Recalculate order totals
                OrderModificationService._recalculate_order_totals(order)
                
                # Create modification note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Item Quantity Updated',
                    content=f'Updated {item.product.name} quantity from {old_quantity} to {new_quantity}',
                    created_by=user
                )
                
                logger.info(f"Updated item quantity in order {order.order_number}")
                return item
                
        except Exception as e:
            logger.error(f"Failed to update item quantity in order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def update_shipping_address(order: Order, new_address: Dict[str, Any], user: User) -> bool:
        """Update order shipping address."""
        try:
            with transaction.atomic():
                old_address = {
                    'street': order.shipping_address.street_address,
                    'city': order.shipping_address.city,
                    'state': order.shipping_address.state,
                    'postal_code': order.shipping_address.postal_code,
                    'country': order.shipping_address.country
                }
                
                # Update address fields
                for field, value in new_address.items():
                    if hasattr(order.shipping_address, field):
                        setattr(order.shipping_address, field, value)
                
                order.shipping_address.save()
                
                # Create modification note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Shipping Address Updated',
                    content=f'Shipping address updated from {old_address} to {new_address}',
                    created_by=user
                )
                
                logger.info(f"Updated shipping address for order {order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update shipping address for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def _recalculate_order_totals(order: Order):
        """Recalculate order totals after modifications."""
        subtotal = sum(item.quantity * item.price for item in order.items.all())
        
        # Calculate tax (assuming tax rate is stored somewhere)
        tax_rate = Decimal('0.08')  # 8% tax rate - should come from settings
        tax_amount = subtotal * tax_rate
        
        # Add shipping cost (if any)
        shipping_cost = order.shipping_cost or Decimal('0.00')
        
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.total_amount = subtotal + tax_amount + shipping_cost
        order.save()


class OrderCancellationService:
    """Service for order cancellation and refund processing."""
    
    @staticmethod
    def cancel_order(order: Order, reason: str, user: User, refund_amount: Decimal = None) -> bool:
        """Cancel order with automated refund processing."""
        try:
            with transaction.atomic():
                if order.status in ['delivered', 'completed', 'cancelled']:
                    raise ValidationError(f"Cannot cancel order with status: {order.status}")
                
                old_status = order.status
                order.status = 'cancelled'
                order.cancelled_at = timezone.now()
                order.cancelled_by = user
                order.cancellation_reason = reason
                order.save()
                
                # Process refund if payment was made
                if order.payment_status == 'paid' and refund_amount is not None:
                    OrderRefundService.process_refund(order, refund_amount, user, reason)
                
                # Release allocated inventory
                if hasattr(order, 'allocation'):
                    OrderAllocationService.release_allocation(order.allocation)
                
                # Create cancellation note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Order Cancelled',
                    content=f'Order cancelled by {user.username}. Reason: {reason}',
                    created_by=user,
                    is_important=True
                )
                
                # Send cancellation notification
                OrderNotificationService.send_cancellation_email(order)
                
                logger.info(f"Order {order.order_number} cancelled by {user.username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel order {order.order_number}: {str(e)}")
            raise


class OrderRefundService:
    """Service for processing refunds."""
    
    @staticmethod
    def process_refund(order: Order, refund_amount: Decimal, user: User, reason: str) -> bool:
        """Process order refund."""
        try:
            with transaction.atomic():
                # Create refund record (assuming there's a refund model)
                # This would integrate with payment gateway
                
                # Update order payment status
                if refund_amount >= order.total_amount:
                    order.payment_status = 'refunded'
                else:
                    order.payment_status = 'partially_refunded'
                
                order.refunded_amount = (order.refunded_amount or Decimal('0.00')) + refund_amount
                order.save()
                
                # Create refund note
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Refund Processed',
                    content=f'Refund of ${refund_amount} processed by {user.username}. Reason: {reason}',
                    created_by=user,
                    is_important=True
                )
                
                # Send refund notification
                OrderNotificationService.send_refund_email(order, refund_amount)
                
                logger.info(f"Refund of ${refund_amount} processed for order {order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to process refund for order {order.order_number}: {str(e)}")
            raise

class OrderSplittingService:
    """Service for order splitting and merging."""
    
    @staticmethod
    def split_order(order: Order, split_items: List[Dict[str, Any]], user: User) -> Order:
        """Split order into multiple orders."""
        try:
            with transaction.atomic():
                # Create new order for split items
                new_order = Order.objects.create(
                    customer=order.customer,
                    status='pending',
                    shipping_address=order.shipping_address,
                    billing_address=order.billing_address,
                    shipping_method=order.shipping_method,
                    payment_method=order.payment_method,
                    notes=f"Split from order {order.order_number}"
                )
                
                total_split_amount = Decimal('0.00')
                
                # Move specified items to new order
                for split_item in split_items:
                    original_item = order.items.get(id=split_item['item_id'])
                    split_quantity = split_item['quantity']
                    
                    if split_quantity >= original_item.quantity:
                        # Move entire item
                        original_item.order = new_order
                        original_item.save()
                    else:
                        # Split item
                        original_item.quantity -= split_quantity
                        original_item.save()
                        
                        # Create new item in split order
                        OrderItem.objects.create(
                            order=new_order,
                            product=original_item.product,
                            quantity=split_quantity,
                            price=original_item.price
                        )
                    
                    total_split_amount += split_quantity * original_item.price
                
                # Recalculate totals for both orders
                OrderModificationService._recalculate_order_totals(order)
                OrderModificationService._recalculate_order_totals(new_order)
                
                # Create notes for both orders
                OrderNote.objects.create(
                    order=order,
                    note_type='internal',
                    title='Order Split',
                    content=f'Order split by {user.username}. New order: {new_order.order_number}',
                    created_by=user
                )
                
                OrderNote.objects.create(
                    order=new_order,
                    note_type='internal',
                    title='Order Created from Split',
                    content=f'Order created from split of {order.order_number} by {user.username}',
                    created_by=user
                )
                
                logger.info(f"Order {order.order_number} split into {new_order.order_number}")
                return new_order
                
        except Exception as e:
            logger.error(f"Failed to split order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def merge_orders(primary_order: Order, secondary_orders: List[Order], user: User) -> Order:
        """Merge multiple orders into one."""
        try:
            with transaction.atomic():
                for secondary_order in secondary_orders:
                    # Move all items from secondary order to primary order
                    for item in secondary_order.items.all():
                        # Check if item already exists in primary order
                        existing_item = primary_order.items.filter(product=item.product).first()
                        if existing_item:
                            existing_item.quantity += item.quantity
                            existing_item.save()
                        else:
                            item.order = primary_order
                            item.save()
                    
                    # Cancel secondary order
                    secondary_order.status = 'cancelled'
                    secondary_order.cancellation_reason = f'Merged into order {primary_order.order_number}'
                    secondary_order.save()
                    
                    # Create merge note
                    OrderNote.objects.create(
                        order=secondary_order,
                        note_type='internal',
                        title='Order Merged',
                        content=f'Order merged into {primary_order.order_number} by {user.username}',
                        created_by=user
                    )
                
                # Recalculate primary order totals
                OrderModificationService._recalculate_order_totals(primary_order)
                
                # Create merge note for primary order
                merged_order_numbers = [order.order_number for order in secondary_orders]
                OrderNote.objects.create(
                    order=primary_order,
                    note_type='internal',
                    title='Orders Merged',
                    content=f'Orders {", ".join(merged_order_numbers)} merged into this order by {user.username}',
                    created_by=user
                )
                
                logger.info(f"Orders merged into {primary_order.order_number}")
                return primary_order
                
        except Exception as e:
            logger.error(f"Failed to merge orders: {str(e)}")
            raise


class OrderTrackingService:
    """Service for order tracking integration."""
    
    @staticmethod
    def update_tracking_info(order: Order, carrier: str, tracking_number: str, user: User) -> OrderTracking:
        """Update order tracking information."""
        try:
            tracking, created = OrderTracking.objects.update_or_create(
                order=order,
                defaults={
                    'carrier': carrier,
                    'tracking_number': tracking_number,
                    'status': 'in_transit',
                    'updated_by': user
                }
            )
            
            # Update order status if not already shipped
            if order.status != 'shipped':
                OrderStatusService.update_order_status(order, 'shipped', user, 
                    f"Tracking info added: {carrier} - {tracking_number}")
            
            # Send tracking notification
            OrderNotificationService.send_tracking_email(order, tracking)
            
            logger.info(f"Tracking info updated for order {order.order_number}")
            return tracking
            
        except Exception as e:
            logger.error(f"Failed to update tracking for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def get_tracking_updates(order: Order) -> List[Dict[str, Any]]:
        """Get real-time tracking updates from carrier."""
        # This would integrate with carrier APIs (FedEx, UPS, USPS, etc.)
        # For now, return mock data
        if not hasattr(order, 'tracking') or not order.tracking:
            return []
        
        tracking = order.tracking
        
        # Mock tracking events
        mock_events = [
            {
                'timestamp': timezone.now() - timedelta(days=2),
                'status': 'picked_up',
                'description': 'Package picked up by carrier',
                'location': 'Origin facility'
            },
            {
                'timestamp': timezone.now() - timedelta(days=1),
                'status': 'in_transit',
                'description': 'Package in transit',
                'location': 'Sorting facility'
            },
            {
                'timestamp': timezone.now(),
                'status': 'out_for_delivery',
                'description': 'Out for delivery',
                'location': 'Local delivery facility'
            }
        ]
        
        return mock_events


class OrderAnalyticsService:
    """Service for order analytics and reporting."""
    
    @staticmethod
    def get_order_metrics(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Get comprehensive order metrics."""
        queryset = Order.objects.all()
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Basic metrics
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        average_order_value = queryset.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        
        # Orders by status
        orders_by_status = dict(
            queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        # Processing time analysis
        processing_times = []
        for order in queryset.filter(status__in=['shipped', 'delivered'])[:100]:
            shipped_event = order.timeline_events.filter(status='shipped').first()
            if shipped_event:
                time_diff = shipped_event.created_at - order.created_at
                processing_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Revenue trend (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        revenue_trend = []
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            daily_revenue = queryset.filter(
                created_at__date=date.date()
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            revenue_trend.append({
                'date': date.date().isoformat(),
                'revenue': float(daily_revenue)
            })
        
        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': average_order_value,
            'orders_by_status': orders_by_status,
            'avg_processing_time_hours': avg_processing_time,
            'revenue_trend': revenue_trend
        }
    
    @staticmethod
    def get_performance_metrics(date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Get order performance metrics and KPIs."""
        queryset = Order.objects.all()
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # SLA compliance
        sla_orders = queryset.filter(sla_tracking__isnull=False)
        sla_met = sla_orders.filter(sla_tracking__overall_sla_met=True).count()
        sla_compliance_rate = (sla_met / sla_orders.count() * 100) if sla_orders.count() > 0 else 0
        
        # Fraud detection stats
        fraud_orders = queryset.filter(fraud_score__isnull=False)
        high_risk_orders = fraud_orders.filter(fraud_score__risk_level='high').count()
        flagged_orders = fraud_orders.filter(fraud_score__is_flagged=True).count()
        
        # Escalation stats
        escalated_orders = queryset.filter(escalations__isnull=False).distinct().count()
        open_escalations = OrderEscalation.objects.filter(
            order__in=queryset,
            status__in=['open', 'in_progress']
        ).count()
        
        # Profitability stats
        profitable_orders = queryset.filter(profitability__isnull=False)
        total_profit = profitable_orders.aggregate(Sum('profitability__net_profit'))['profitability__net_profit__sum'] or 0
        avg_margin = profitable_orders.aggregate(Avg('profitability__profit_margin_percentage'))['profitability__profit_margin_percentage__avg'] or 0
        
        return {
            'sla_compliance_rate': sla_compliance_rate,
            'high_risk_orders': high_risk_orders,
            'flagged_orders': flagged_orders,
            'escalated_orders': escalated_orders,
            'open_escalations': open_escalations,
            'total_profit': total_profit,
            'average_profit_margin': avg_margin
        }


class OrderFraudDetectionService:
    """Service for order fraud detection and risk assessment."""
    
    @staticmethod
    def calculate_fraud_score(order: Order) -> OrderFraudScore:
        """Calculate fraud score for an order."""
        risk_factors = []
        score = 0
        
        # Check for high-value orders
        if order.total_amount > Decimal('1000'):
            risk_factors.append('High value order')
            score += 20
        
        # Check for multiple orders from same customer in short time
        recent_orders = Order.objects.filter(
            customer=order.customer,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        if recent_orders > 3:
            risk_factors.append('Multiple orders in 24 hours')
            score += 30
        
        # Check for shipping/billing address mismatch
        if (order.shipping_address and order.billing_address and 
            order.shipping_address != order.billing_address):
            risk_factors.append('Address mismatch')
            score += 15
        
        # Check for new customer with high-value order
        if (order.customer.date_joined > timezone.now() - timedelta(days=7) and 
            order.total_amount > Decimal('500')):
            risk_factors.append('New customer with high-value order')
            score += 25
        
        # Determine risk level
        if score >= 70:
            risk_level = 'critical'
        elif score >= 50:
            risk_level = 'high'
        elif score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Create or update fraud score
        fraud_score, created = OrderFraudScore.objects.update_or_create(
            order=order,
            defaults={
                'score': score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'is_flagged': score >= 50
            }
        )
        
        # Create escalation for high-risk orders
        if score >= 50:
            OrderEscalationService.create_escalation(
                order=order,
                escalation_type='fraud_alert',
                title=f'High fraud risk detected (Score: {score})',
                description=f'Risk factors: {", ".join(risk_factors)}',
                priority='high' if score >= 70 else 'medium'
            )
        
        return fraud_score
    
    @staticmethod
    def review_fraud_score(fraud_score: OrderFraudScore, user: User, notes: str, is_flagged: bool = None):
        """Review and update fraud score."""
        fraud_score.reviewed_by = user
        fraud_score.reviewed_at = timezone.now()
        fraud_score.review_notes = notes
        
        if is_flagged is not None:
            fraud_score.is_flagged = is_flagged
        
        fraud_score.save()
        
        # Create order note
        OrderNote.objects.create(
            order=fraud_score.order,
            note_type='internal',
            title='Fraud Score Reviewed',
            content=f'Fraud score reviewed by {user.username}. Notes: {notes}',
            created_by=user,
            is_important=True
        )


class OrderEscalationService:
    """Service for order escalation management."""
    
    @staticmethod
    def create_escalation(order: Order, escalation_type: str, title: str, 
                         description: str, priority: str = 'medium', 
                         created_by: User = None) -> OrderEscalation:
        """Create order escalation."""
        # Calculate SLA deadline based on priority
        sla_hours = {
            'critical': 2,
            'high': 8,
            'medium': 24,
            'low': 72
        }
        
        sla_deadline = timezone.now() + timedelta(hours=sla_hours.get(priority, 24))
        
        escalation = OrderEscalation.objects.create(
            order=order,
            escalation_type=escalation_type,
            priority=priority,
            title=title,
            description=description,
            created_by=created_by,
            sla_deadline=sla_deadline
        )
        
        # Create order note
        if created_by:
            OrderNote.objects.create(
                order=order,
                note_type='escalation',
                title=f'Escalation Created: {title}',
                content=description,
                created_by=created_by,
                is_important=True
            )
        
        logger.info(f"Escalation created for order {order.order_number}: {title}")
        return escalation
    
    @staticmethod
    def assign_escalation(escalation: OrderEscalation, assigned_to: User, assigned_by: User):
        """Assign escalation to a user."""
        escalation.assigned_to = assigned_to
        escalation.status = 'in_progress'
        escalation.save()
        
        # Create order note
        OrderNote.objects.create(
            order=escalation.order,
            note_type='internal',
            title='Escalation Assigned',
            content=f'Escalation assigned to {assigned_to.username} by {assigned_by.username}',
            created_by=assigned_by
        )
        
        logger.info(f"Escalation {escalation.id} assigned to {assigned_to.username}")
    
    @staticmethod
    def resolve_escalation(escalation: OrderEscalation, resolved_by: User, resolution_notes: str):
        """Resolve an escalation."""
        escalation.status = 'resolved'
        escalation.resolved_by = resolved_by
        escalation.resolved_at = timezone.now()
        escalation.resolution_notes = resolution_notes
        escalation.save()
        
        # Create order note
        OrderNote.objects.create(
            order=escalation.order,
            note_type='internal',
            title='Escalation Resolved',
            content=f'Escalation resolved by {resolved_by.username}. Resolution: {resolution_notes}',
            created_by=resolved_by,
            is_important=True
        )
        
        logger.info(f"Escalation {escalation.id} resolved by {resolved_by.username}")


class OrderAllocationService:
    """Service for order allocation and inventory reservation."""
    
    @staticmethod
    def allocate_order_inventory(order: Order, user: User = None) -> OrderAllocation:
        """Allocate inventory for order items."""
        try:
            with transaction.atomic():
                allocation_details = {}
                all_allocated = True
                
                for item in order.items.all():
                    product = item.product
                    required_quantity = item.quantity
                    
                    # Check available inventory
                    available_quantity = product.stock_quantity
                    
                    if available_quantity >= required_quantity:
                        # Full allocation
                        allocation_details[str(item.id)] = {
                            'product_id': product.id,
                            'product_name': product.name,
                            'required_quantity': required_quantity,
                            'allocated_quantity': required_quantity,
                            'status': 'fully_allocated'
                        }
                        
                        # Reserve inventory (in production, this would update actual inventory)
                        # product.reserved_quantity += required_quantity
                        # product.save()
                        
                    else:
                        # Partial or no allocation
                        allocation_details[str(item.id)] = {
                            'product_id': product.id,
                            'product_name': product.name,
                            'required_quantity': required_quantity,
                            'allocated_quantity': available_quantity,
                            'status': 'partially_allocated' if available_quantity > 0 else 'not_allocated'
                        }
                        all_allocated = False
                
                # Determine overall allocation status
                if all_allocated:
                    status = 'allocated'
                elif any(item['allocated_quantity'] > 0 for item in allocation_details.values()):
                    status = 'partially_allocated'
                else:
                    status = 'failed'
                
                # Create or update allocation
                allocation, created = OrderAllocation.objects.update_or_create(
                    order=order,
                    defaults={
                        'status': status,
                        'allocated_at': timezone.now() if status != 'failed' else None,
                        'allocated_by': user,
                        'allocation_details': allocation_details,
                        'reservation_expires_at': timezone.now() + timedelta(hours=24) if status != 'failed' else None
                    }
                )
                
                # Create order note
                if user:
                    OrderNote.objects.create(
                        order=order,
                        note_type='internal',
                        title='Inventory Allocation',
                        content=f'Inventory allocation {status} by {user.username}',
                        created_by=user
                    )
                
                logger.info(f"Inventory allocation {status} for order {order.order_number}")
                return allocation
                
        except Exception as e:
            logger.error(f"Failed to allocate inventory for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def release_allocation(allocation: OrderAllocation, user: User = None):
        """Release inventory allocation."""
        try:
            with transaction.atomic():
                # Release reserved inventory (in production)
                for item_data in allocation.allocation_details.values():
                    if item_data['allocated_quantity'] > 0:
                        # product = Product.objects.get(id=item_data['product_id'])
                        # product.reserved_quantity -= item_data['allocated_quantity']
                        # product.save()
                        pass
                
                allocation.status = 'released'
                allocation.save()
                
                # Create order note
                if user:
                    OrderNote.objects.create(
                        order=allocation.order,
                        note_type='internal',
                        title='Inventory Allocation Released',
                        content=f'Inventory allocation released by {user.username}',
                        created_by=user
                    )
                
                logger.info(f"Inventory allocation released for order {allocation.order.order_number}")
                
        except Exception as e:
            logger.error(f"Failed to release allocation for order {allocation.order.order_number}: {str(e)}")
            raise


class OrderNotificationService:
    """Service for order notifications and communications."""
    
    @staticmethod
    def send_status_change_email(order: Order, template: str = None):
        """Send email notification for order status change."""
        # This would integrate with email service
        logger.info(f"Sending status change email for order {order.order_number} - Status: {order.status}")
        
        # Mock email sending
        email_data = {
            'to': order.customer.email,
            'subject': f'Order {order.order_number} Status Update',
            'template': template or 'order_status_change',
            'context': {
                'order': order,
                'customer': order.customer,
                'status': order.status
            }
        }
        
        # In production, this would send actual email
        return True
    
    @staticmethod
    def send_cancellation_email(order: Order):
        """Send order cancellation email."""
        logger.info(f"Sending cancellation email for order {order.order_number}")
        
        email_data = {
            'to': order.customer.email,
            'subject': f'Order {order.order_number} Cancelled',
            'template': 'order_cancellation',
            'context': {
                'order': order,
                'customer': order.customer,
                'cancellation_reason': getattr(order, 'cancellation_reason', 'Order cancelled')
            }
        }
        
        return True
    
    @staticmethod
    def send_refund_email(order: Order, refund_amount: Decimal):
        """Send refund notification email."""
        logger.info(f"Sending refund email for order {order.order_number} - Amount: ${refund_amount}")
        
        email_data = {
            'to': order.customer.email,
            'subject': f'Refund Processed for Order {order.order_number}',
            'template': 'order_refund',
            'context': {
                'order': order,
                'customer': order.customer,
                'refund_amount': refund_amount
            }
        }
        
        return True
    
    @staticmethod
    def send_tracking_email(order: Order, tracking: OrderTracking):
        """Send tracking information email."""
        logger.info(f"Sending tracking email for order {order.order_number} - Tracking: {tracking.tracking_number}")
        
        email_data = {
            'to': order.customer.email,
            'subject': f'Tracking Information for Order {order.order_number}',
            'template': 'order_tracking',
            'context': {
                'order': order,
                'customer': order.customer,
                'tracking': tracking
            }
        }
        
        return True


class OrderDocumentService:
    """Service for order document generation and management."""
    
    @staticmethod
    def generate_invoice(order: Order, user: User = None) -> OrderDocument:
        """Generate invoice document for order."""
        try:
            # In production, this would use a PDF generation library
            file_path = f"/documents/invoices/{order.order_number}_invoice.pdf"
            
            document = OrderDocument.objects.create(
                order=order,
                document_type='invoice',
                title=f'Invoice for Order {order.order_number}',
                file_path=file_path,
                file_size=1024,  # Mock size
                mime_type='application/pdf',
                generated_by=user,
                is_customer_accessible=True
            )
            
            logger.info(f"Invoice generated for order {order.order_number}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to generate invoice for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def generate_shipping_label(order: Order, user: User = None) -> OrderDocument:
        """Generate shipping label for order."""
        try:
            file_path = f"/documents/shipping_labels/{order.order_number}_label.pdf"
            
            document = OrderDocument.objects.create(
                order=order,
                document_type='shipping_label',
                title=f'Shipping Label for Order {order.order_number}',
                file_path=file_path,
                file_size=512,  # Mock size
                mime_type='application/pdf',
                generated_by=user,
                is_customer_accessible=False
            )
            
            logger.info(f"Shipping label generated for order {order.order_number}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to generate shipping label for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def generate_packing_slip(order: Order, user: User = None) -> OrderDocument:
        """Generate packing slip for order."""
        try:
            file_path = f"/documents/packing_slips/{order.order_number}_packing_slip.pdf"
            
            document = OrderDocument.objects.create(
                order=order,
                document_type='packing_slip',
                title=f'Packing Slip for Order {order.order_number}',
                file_path=file_path,
                file_size=256,  # Mock size
                mime_type='application/pdf',
                generated_by=user,
                is_customer_accessible=False
            )
            
            logger.info(f"Packing slip generated for order {order.order_number}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to generate packing slip for order {order.order_number}: {str(e)}")
            raise


class OrderExportService:
    """Service for order data export functionality."""
    
    @staticmethod
    def export_orders_csv(orders: List[Order], include_items: bool = True) -> str:
        """Export orders to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = [
            'Order Number', 'Customer Email', 'Customer Name', 'Status', 
            'Payment Status', 'Total Amount', 'Created At', 'Updated At'
        ]
        
        if include_items:
            header.extend(['Product Name', 'Quantity', 'Unit Price', 'Total Price'])
        
        writer.writerow(header)
        
        # Write data
        for order in orders:
            base_row = [
                order.order_number,
                order.customer.email,
                f"{order.customer.first_name} {order.customer.last_name}",
                order.status,
                order.payment_status,
                str(order.total_amount),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            if include_items:
                for item in order.items.all():
                    row = base_row + [
                        item.product.name,
                        item.quantity,
                        str(item.unit_price),
                        str(item.total_price)
                    ]
                    writer.writerow(row)
            else:
                writer.writerow(base_row)
        
        return output.getvalue()
    
    @staticmethod
    def export_orders_json(orders: List[Order]) -> str:
        """Export orders to JSON format."""
        from .order_serializers import AdminOrderSerializer
        
        serializer = AdminOrderSerializer(orders, many=True)
        return json.dumps(serializer.data, indent=2, default=str)


class OrderComplianceService:
    """Service for order compliance tracking and validation."""
    
    @staticmethod
    def check_tax_compliance(order: Order, region: str) -> Dict[str, Any]:
        """Check tax compliance for order."""
        compliance_result = {
            'compliant': True,
            'issues': [],
            'requirements_met': [],
            'region': region
        }
        
        # Mock tax compliance checks
        if order.tax_amount <= 0:
            compliance_result['compliant'] = False
            compliance_result['issues'].append('No tax calculated for taxable order')
        else:
            compliance_result['requirements_met'].append('Tax calculated correctly')
        
        # Check for tax exemption documentation if applicable
        if hasattr(order, 'tax_exempt') and order.tax_exempt:
            if not hasattr(order, 'tax_exemption_certificate'):
                compliance_result['compliant'] = False
                compliance_result['issues'].append('Tax exemption claimed but no certificate on file')
        
        return compliance_result
    
    @staticmethod
    def check_shipping_compliance(order: Order, region: str) -> Dict[str, Any]:
        """Check shipping compliance for order."""
        compliance_result = {
            'compliant': True,
            'issues': [],
            'requirements_met': [],
            'region': region
        }
        
        # Mock shipping compliance checks
        if not order.shipping_address:
            compliance_result['compliant'] = False
            compliance_result['issues'].append('No shipping address provided')
        else:
            compliance_result['requirements_met'].append('Shipping address provided')
        
        # Check for restricted items/destinations
        for item in order.items.all():
            # Mock restricted item check
            if 'restricted' in item.product.name.lower():
                compliance_result['compliant'] = False
                compliance_result['issues'].append(f'Restricted item: {item.product.name}')
        
        return compliance_result
    
    @staticmethod
    def get_order_trends(days: int = 30) -> List[Dict[str, Any]]:
        """Get order trends over specified period."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            day_orders = Order.objects.filter(
                created_at__date=current_date
            ).aggregate(
                count=Count('id'),
                revenue=Sum('total_amount')
            )
            
            trends.append({
                'date': current_date,
                'order_count': day_orders['count'] or 0,
                'revenue': day_orders['revenue'] or Decimal('0.00')
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def get_top_products_by_orders(limit: int = 10) -> List[Dict[str, Any]]:
        """Get top products by order frequency."""
        from django.db.models import Count
        
        top_products = OrderItem.objects.values(
            'product__name', 'product__id'
        ).annotate(
            order_count=Count('order', distinct=True),
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-order_count')[:limit]
        
        return list(top_products)


class OrderFraudService:
    """Service for order fraud detection and risk assessment."""
    
    @staticmethod
    def calculate_fraud_score(order: Order) -> OrderFraudScore:
        """Calculate fraud risk score for order."""
        try:
            score = 0
            risk_factors = []
            
            # Check for high-risk indicators
            
            # 1. Large order amount
            if order.total_amount > Decimal('1000.00'):
                score += 20
                risk_factors.append('High order value')
            
            # 2. Multiple orders from same IP in short time
            recent_orders = Order.objects.filter(
                customer=order.customer,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            if recent_orders > 3:
                score += 30
                risk_factors.append('Multiple recent orders')
            
            # 3. Shipping and billing address mismatch
            if (order.shipping_address.country != order.billing_address.country):
                score += 25
                risk_factors.append('Address country mismatch')
            
            # 4. New customer with large order
            if (order.customer.date_joined >= timezone.now() - timedelta(days=7) and 
                order.total_amount > Decimal('500.00')):
                score += 35
                risk_factors.append('New customer with high-value order')
            
            # 5. Unusual shipping method for order value
            if order.shipping_method == 'express' and order.total_amount < Decimal('50.00'):
                score += 15
                risk_factors.append('Unusual shipping method')
            
            # Determine risk level
            if score >= 80:
                risk_level = 'critical'
                is_flagged = True
            elif score >= 60:
                risk_level = 'high'
                is_flagged = True
            elif score >= 40:
                risk_level = 'medium'
                is_flagged = False
            else:
                risk_level = 'low'
                is_flagged = False
            
            # Create or update fraud score
            fraud_score, created = OrderFraudScore.objects.update_or_create(
                order=order,
                defaults={
                    'score': score,
                    'risk_level': risk_level,
                    'risk_factors': risk_factors,
                    'is_flagged': is_flagged
                }
            )
            
            # Create escalation for high-risk orders
            if is_flagged:
                OrderEscalationService.create_escalation(
                    order=order,
                    escalation_type='fraud_alert',
                    title=f'High fraud risk detected - Score: {score}',
                    description=f'Risk factors: {", ".join(risk_factors)}',
                    priority='high' if risk_level == 'critical' else 'medium'
                )
            
            logger.info(f"Fraud score calculated for order {order.order_number}: {score} ({risk_level})")
            return fraud_score
            
        except Exception as e:
            logger.error(f"Failed to calculate fraud score for order {order.order_number}: {str(e)}")
            raise


class OrderEscalationService:
    """Service for order escalations and exception handling."""
    
    @staticmethod
    def create_escalation(order: Order, escalation_type: str, title: str, 
                         description: str, priority: str = 'medium', 
                         created_by: User = None, assigned_to: User = None) -> OrderEscalation:
        """Create order escalation."""
        try:
            # Calculate SLA deadline based on priority
            sla_hours = {
                'critical': 2,
                'high': 8,
                'medium': 24,
                'low': 72
            }
            
            sla_deadline = timezone.now() + timedelta(hours=sla_hours.get(priority, 24))
            
            escalation = OrderEscalation.objects.create(
                order=order,
                escalation_type=escalation_type,
                priority=priority,
                title=title,
                description=description,
                created_by=created_by,
                assigned_to=assigned_to,
                sla_deadline=sla_deadline
            )
            
            # Create escalation note
            OrderNote.objects.create(
                order=order,
                note_type='escalation',
                title=f'Escalation Created: {title}',
                content=description,
                created_by=created_by,
                is_important=True
            )
            
            # Send escalation notification
            if assigned_to:
                OrderNotificationService.send_escalation_email(escalation)
            
            logger.info(f"Escalation created for order {order.order_number}: {title}")
            return escalation
            
        except Exception as e:
            logger.error(f"Failed to create escalation for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def resolve_escalation(escalation: OrderEscalation, resolution_notes: str, 
                          resolved_by: User) -> bool:
        """Resolve order escalation."""
        try:
            escalation.status = 'resolved'
            escalation.resolution_notes = resolution_notes
            escalation.resolved_by = resolved_by
            escalation.resolved_at = timezone.now()
            escalation.save()
            
            # Create resolution note
            OrderNote.objects.create(
                order=escalation.order,
                note_type='escalation',
                title=f'Escalation Resolved: {escalation.title}',
                content=resolution_notes,
                created_by=resolved_by,
                is_important=True
            )
            
            logger.info(f"Escalation {escalation.id} resolved for order {escalation.order.order_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve escalation {escalation.id}: {str(e)}")
            raise
    
    @staticmethod
    def get_overdue_escalations() -> List[OrderEscalation]:
        """Get all overdue escalations."""
        return OrderEscalation.objects.filter(
            status__in=['open', 'in_progress'],
            sla_deadline__lt=timezone.now()
        ).order_by('sla_deadline')


class OrderAllocationService:
    """Service for order allocation and inventory reservation."""
    
    @staticmethod
    def allocate_order_inventory(order: Order) -> OrderAllocation:
        """Allocate inventory for order items."""
        try:
            with transaction.atomic():
                allocation_details = {}
                all_allocated = True
                
                for item in order.items.all():
                    product = item.product
                    required_quantity = item.quantity
                    
                    if product.stock_quantity >= required_quantity:
                        # Reserve inventory
                        product.stock_quantity -= required_quantity
                        product.reserved_quantity = (product.reserved_quantity or 0) + required_quantity
                        product.save()
                        
                        allocation_details[str(item.id)] = {
                            'product_id': product.id,
                            'requested': required_quantity,
                            'allocated': required_quantity,
                            'status': 'allocated'
                        }
                    else:
                        # Partial or no allocation
                        available_quantity = max(0, product.stock_quantity)
                        if available_quantity > 0:
                            product.stock_quantity = 0
                            product.reserved_quantity = (product.reserved_quantity or 0) + available_quantity
                            product.save()
                        
                        allocation_details[str(item.id)] = {
                            'product_id': product.id,
                            'requested': required_quantity,
                            'allocated': available_quantity,
                            'status': 'partially_allocated' if available_quantity > 0 else 'failed'
                        }
                        all_allocated = False
                
                # Determine overall allocation status
                if all_allocated:
                    status = 'allocated'
                elif any(detail['allocated'] > 0 for detail in allocation_details.values()):
                    status = 'partially_allocated'
                else:
                    status = 'failed'
                
                # Create allocation record
                allocation = OrderAllocation.objects.create(
                    order=order,
                    status=status,
                    allocated_at=timezone.now() if status != 'failed' else None,
                    allocation_details=allocation_details,
                    reservation_expires_at=timezone.now() + timedelta(hours=24)
                )
                
                # Create escalation for failed allocations
                if status in ['failed', 'partially_allocated']:
                    OrderEscalationService.create_escalation(
                        order=order,
                        escalation_type='inventory_shortage',
                        title='Inventory Allocation Failed',
                        description=f'Order allocation {status}. Check inventory levels.',
                        priority='high'
                    )
                
                logger.info(f"Inventory allocated for order {order.order_number}: {status}")
                return allocation
                
        except Exception as e:
            logger.error(f"Failed to allocate inventory for order {order.order_number}: {str(e)}")
            raise
    
    @staticmethod
    def release_allocation(allocation: OrderAllocation) -> bool:
        """Release allocated inventory."""
        try:
            with transaction.atomic():
                for item_id, details in allocation.allocation_details.items():
                    if details['allocated'] > 0:
                        from apps.products.models import Product
                        product = Product.objects.get(id=details['product_id'])
                        
                        # Return inventory to available stock
                        product.stock_quantity += details['allocated']
                        product.reserved_quantity = max(0, (product.reserved_quantity or 0) - details['allocated'])
                        product.save()
                
                allocation.status = 'released'
                allocation.save()
                
                logger.info(f"Allocation released for order {allocation.order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to release allocation for order {allocation.order.order_number}: {str(e)}")
            raise


class OrderNotificationService:
    """Service for order notifications and communications."""
    
    @staticmethod
    def send_status_change_email(order: Order, template: str = None):
        """Send order status change notification."""
        # This would integrate with email service
        logger.info(f"Status change email sent for order {order.order_number}")
    
    @staticmethod
    def send_cancellation_email(order: Order):
        """Send order cancellation notification."""
        logger.info(f"Cancellation email sent for order {order.order_number}")
    
    @staticmethod
    def send_refund_email(order: Order, refund_amount: Decimal):
        """Send refund notification."""
        logger.info(f"Refund email sent for order {order.order_number}: ${refund_amount}")
    
    @staticmethod
    def send_tracking_email(order: Order, tracking: OrderTracking):
        """Send tracking information notification."""
        logger.info(f"Tracking email sent for order {order.order_number}")
    
    @staticmethod
    def send_escalation_email(escalation: OrderEscalation):
        """Send escalation notification."""
        logger.info(f"Escalation email sent for order {escalation.order.order_number}")


class OrderProfitabilityService:
    """Service for order profitability analysis."""
    
    @staticmethod
    def calculate_order_profitability(order: Order) -> OrderProfitability:
        """Calculate comprehensive order profitability."""
        try:
            # Calculate revenue
            gross_revenue = order.total_amount
            net_revenue = gross_revenue - (order.discount_amount or Decimal('0.00'))
            
            # Calculate costs
            product_cost = sum(
                item.quantity * (item.product.cost_price or Decimal('0.00'))
                for item in order.items.all()
            )
            
            shipping_cost = order.shipping_cost or Decimal('0.00')
            
            # Estimate other costs (these would come from settings or calculations)
            payment_processing_cost = net_revenue * Decimal('0.029')  # 2.9% processing fee
            packaging_cost = Decimal('2.50')  # Flat packaging cost
            handling_cost = Decimal('1.00') * order.items.count()  # Per item handling
            
            profitability, created = OrderProfitability.objects.update_or_create(
                order=order,
                defaults={
                    'gross_revenue': gross_revenue,
                    'net_revenue': net_revenue,
                    'product_cost': product_cost,
                    'shipping_cost': shipping_cost,
                    'payment_processing_cost': payment_processing_cost,
                    'packaging_cost': packaging_cost,
                    'handling_cost': handling_cost
                }
            )
            
            # Calculate profitability metrics
            profitability.calculate_profitability()
            
            logger.info(f"Profitability calculated for order {order.order_number}")
            return profitability
            
        except Exception as e:
            logger.error(f"Failed to calculate profitability for order {order.order_number}: {str(e)}")
            raise


class OrderExportService:
    """Service for order data export."""
    
    @staticmethod
    def export_orders_csv(orders: List[Order]) -> str:
        """Export orders to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order Number', 'Customer Email', 'Status', 'Total Amount',
            'Created Date', 'Shipping Address', 'Items'
        ])
        
        # Write data
        for order in orders:
            items_str = '; '.join([
                f"{item.product.name} (x{item.quantity})"
                for item in order.items.all()
            ])
            
            writer.writerow([
                order.order_number,
                order.customer.email,
                order.status,
                str(order.total_amount),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                f"{order.shipping_address.city}, {order.shipping_address.state}",
                items_str
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_orders_excel(orders: List[Order]) -> bytes:
        """Export orders to Excel format."""
        # This would use openpyxl or similar library
        # For now, return CSV as bytes
        csv_data = OrderExportService.export_orders_csv(orders)
        return csv_data.encode('utf-8')


class OrderBatchService:
    """Service for batch order operations."""
    
    @staticmethod
    def batch_update_status(order_ids: List[int], new_status: str, user: User) -> Dict[str, Any]:
        """Update status for multiple orders."""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        for order_id in order_ids:
            try:
                order = Order.objects.get(id=order_id)
                OrderStatusService.update_order_status(order, new_status, user)
                results['success_count'] += 1
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'order_id': order_id,
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def batch_cancel_orders(order_ids: List[int], reason: str, user: User) -> Dict[str, Any]:
        """Cancel multiple orders."""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        for order_id in order_ids:
            try:
                order = Order.objects.get(id=order_id)
                OrderCancellationService.cancel_order(order, reason, user)
                results['success_count'] += 1
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'order_id': order_id,
                    'error': str(e)
                })
        
        return results