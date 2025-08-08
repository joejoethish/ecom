"""
Comprehensive Order views for the admin panel.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F, Case, When, Value, IntegerField
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
import json
import csv
import io
from decimal import Decimal

from apps.orders.models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.orders.services import OrderService, ReturnService, InvoiceService
from .order_models import (
    OrderSearchFilter, OrderWorkflow, OrderFraudScore, OrderNote, OrderEscalation,
    OrderSLA, OrderAllocation, OrderProfitability, OrderDocument, OrderQualityControl,
    OrderSubscription
)
from .order_serializers import (
    AdminOrderSerializer, OrderSearchFilterSerializer, OrderWorkflowSerializer,
    OrderFraudScoreSerializer, OrderNoteSerializer, OrderEscalationSerializer,
    OrderSLASerializer, OrderAllocationSerializer, OrderProfitabilitySerializer,
    OrderDocumentSerializer, OrderQualityControlSerializer, OrderSubscriptionSerializer,
    OrderAnalyticsSerializer, OrderBulkActionSerializer, OrderModificationSerializer,
    OrderSplitSerializer, OrderMergeSerializer, OrderExportSerializer,
    OrderForecastSerializer, OrderRoutingSerializer, OrderComplianceSerializer
)
from .permissions import IsAdminUser


class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    Comprehensive order management viewset for admin panel.
    """
    serializer_class = AdminOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'payment_status', 'customer', 'shipping_method', 'payment_method'
    ]
    search_fields = [
        'order_number', 'tracking_number', 'customer__email', 'customer__first_name',
        'customer__last_name', 'invoice_number'
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'total_amount', 'status', 'payment_status'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get orders with optimized queries for admin panel."""
        queryset = Order.objects.select_related(
            'customer', 'fraud_score', 'sla_tracking', 'allocation',
            'profitability', 'quality_control', 'subscription'
        ).prefetch_related(
            'items__product', 'timeline_events', 'admin_notes',
            'escalations', 'documents', 'return_requests', 'replacements'
        ).filter(is_deleted=False)
        
        # Apply additional filters
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        amount_min = self.request.query_params.get('amount_min')
        if amount_min:
            queryset = queryset.filter(total_amount__gte=amount_min)
        
        amount_max = self.request.query_params.get('amount_max')
        if amount_max:
            queryset = queryset.filter(total_amount__lte=amount_max)
        
        has_escalations = self.request.query_params.get('has_escalations')
        if has_escalations == 'true':
            queryset = queryset.filter(escalations__isnull=False).distinct()
        
        fraud_risk = self.request.query_params.get('fraud_risk')
        if fraud_risk:
            queryset = queryset.filter(fraud_score__risk_level=fraud_risk)
        
        sla_status = self.request.query_params.get('sla_status')
        if sla_status == 'met':
            queryset = queryset.filter(sla_tracking__overall_sla_met=True)
        elif sla_status == 'missed':
            queryset = queryset.filter(sla_tracking__overall_sla_met=False)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get comprehensive order analytics."""
        # Date range filter
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Basic metrics
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        average_order_value = queryset.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        
        # Orders by status
        orders_by_status = dict(
            queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        # Orders by payment status
        orders_by_payment_status = dict(
            queryset.values('payment_status').annotate(count=Count('id')).values_list('payment_status', 'count')
        )
        
        # Top customers
        top_customers = list(
            queryset.values('customer__email', 'customer__first_name', 'customer__last_name')
            .annotate(
                order_count=Count('id'),
                total_spent=Sum('total_amount')
            )
            .order_by('-total_spent')[:10]
        )
        
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
        
        # Order volume trend
        order_volume_trend = []
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            daily_orders = queryset.filter(created_at__date=date.date()).count()
            order_volume_trend.append({
                'date': date.date().isoformat(),
                'orders': daily_orders
            })
        
        # Processing time average
        processing_times = []
        for order in queryset.filter(status__in=['shipped', 'delivered'])[:100]:
            shipped_event = order.timeline_events.filter(status='shipped').first()
            if shipped_event:
                time_diff = shipped_event.created_at - order.created_at
                processing_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
        
        processing_time_avg = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # SLA compliance rate
        sla_orders = queryset.filter(sla_tracking__isnull=False)
        sla_met_count = sla_orders.filter(sla_tracking__overall_sla_met=True).count()
        sla_compliance_rate = (sla_met_count / sla_orders.count() * 100) if sla_orders.count() > 0 else 0
        
        # Fraud detection stats
        fraud_scores = queryset.filter(fraud_score__isnull=False)
        fraud_detection_stats = {
            'total_scored': fraud_scores.count(),
            'high_risk': fraud_scores.filter(fraud_score__risk_level='high').count(),
            'flagged': fraud_scores.filter(fraud_score__is_flagged=True).count(),
            'average_score': fraud_scores.aggregate(Avg('fraud_score__score'))['fraud_score__score__avg'] or 0
        }
        
        # Profitability summary
        profitable_orders = queryset.filter(profitability__isnull=False)
        profitability_summary = {
            'total_analyzed': profitable_orders.count(),
            'total_profit': profitable_orders.aggregate(Sum('profitability__net_profit'))['profitability__net_profit__sum'] or 0,
            'average_margin': profitable_orders.aggregate(Avg('profitability__profit_margin_percentage'))['profitability__profit_margin_percentage__avg'] or 0,
            'profitable_orders': profitable_orders.filter(profitability__net_profit__gt=0).count()
        }
        
        analytics_data = {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': average_order_value,
            'orders_by_status': orders_by_status,
            'orders_by_payment_status': orders_by_payment_status,
            'top_customers': top_customers,
            'revenue_trend': revenue_trend,
            'order_volume_trend': order_volume_trend,
            'processing_time_avg': processing_time_avg,
            'sla_compliance_rate': sla_compliance_rate,
            'fraud_detection_stats': fraud_detection_stats,
            'profitability_summary': profitability_summary
        }
        
        serializer = OrderAnalyticsSerializer(analytics_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def modify_order(self, request, pk=None):
        """Modify order (add/remove items, change quantities, update addresses)."""
        order = self.get_object()
        serializer = OrderModificationSerializer(data=request.data)
        
        if serializer.is_valid():
            modification_type = serializer.validated_data['modification_type']
            reason = serializer.validated_data['reason']
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    if modification_type == 'add_item':
                        # Add new item to order
                        from apps.products.models import Product
                        product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
                        quantity = serializer.validated_data['quantity']
                        
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            unit_price=product.price,
                            total_price=product.price * quantity
                        )
                        
                        # Update order total
                        order.total_amount += order_item.total_price
                        order.save()
                        
                        # Add timeline event
                        order.add_timeline_event(
                            status=order.status,
                            description=f"Item added: {product.name} (Qty: {quantity}). Reason: {reason}",
                            user=request.user
                        )
                    
                    elif modification_type == 'remove_item':
                        # Remove item from order
                        order_item = get_object_or_404(OrderItem, id=serializer.validated_data['order_item_id'], order=order)
                        
                        # Update order total
                        order.total_amount -= order_item.total_price
                        order.save()
                        
                        # Add timeline event
                        order.add_timeline_event(
                            status=order.status,
                            description=f"Item removed: {order_item.product.name} (Qty: {order_item.quantity}). Reason: {reason}",
                            user=request.user
                        )
                        
                        order_item.delete()
                    
                    elif modification_type == 'update_quantity':
                        # Update item quantity
                        order_item = get_object_or_404(OrderItem, id=serializer.validated_data['order_item_id'], order=order)
                        old_quantity = order_item.quantity
                        new_quantity = serializer.validated_data['quantity']
                        
                        # Update order total
                        old_total = order_item.total_price
                        order_item.quantity = new_quantity
                        order_item.total_price = order_item.unit_price * new_quantity
                        order_item.save()
                        
                        order.total_amount = order.total_amount - old_total + order_item.total_price
                        order.save()
                        
                        # Add timeline event
                        order.add_timeline_event(
                            status=order.status,
                            description=f"Quantity updated for {order_item.product.name}: {old_quantity} -> {new_quantity}. Reason: {reason}",
                            user=request.user
                        )
                    
                    elif modification_type == 'update_address':
                        # Update shipping or billing address
                        if 'shipping_address' in serializer.validated_data:
                            order.shipping_address = serializer.validated_data['shipping_address']
                        if 'billing_address' in serializer.validated_data:
                            order.billing_address = serializer.validated_data['billing_address']
                        order.save()
                        
                        # Add timeline event
                        order.add_timeline_event(
                            status=order.status,
                            description=f"Address updated. Reason: {reason}",
                            user=request.user
                        )
                    
                    elif modification_type == 'update_shipping_method':
                        # Update shipping method
                        old_method = order.shipping_method
                        order.shipping_method = serializer.validated_data['shipping_method']
                        order.save()
                        
                        # Add timeline event
                        order.add_timeline_event(
                            status=order.status,
                            description=f"Shipping method updated: {old_method} -> {order.shipping_method}. Reason: {reason}",
                            user=request.user
                        )
                    
                    # Add admin note
                    OrderNote.objects.create(
                        order=order,
                        note_type='internal',
                        title=f"Order Modified - {modification_type}",
                        content=f"Reason: {reason}\nNotes: {notes}",
                        created_by=request.user
                    )
                
                # Return updated order
                serializer = AdminOrderSerializer(order)
                return Response(serializer.data)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def split_order(self, request, pk=None):
        """Split order into multiple orders for complex fulfillment scenarios."""
        order = self.get_object()
        serializer = OrderSplitSerializer(data=request.data)
        
        if serializer.is_valid():
            split_items = serializer.validated_data['split_items']
            reason = serializer.validated_data['reason']
            shipping_address = serializer.validated_data.get('shipping_address', order.shipping_address)
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    # Create new order for split items
                    new_order = Order.objects.create(
                        customer=order.customer,
                        order_number=f"{order.order_number}-SPLIT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        status='pending',
                        payment_status=order.payment_status,
                        total_amount=0,
                        shipping_amount=0,
                        tax_amount=0,
                        discount_amount=0,
                        shipping_address=shipping_address,
                        billing_address=order.billing_address,
                        shipping_method=order.shipping_method,
                        payment_method=order.payment_method,
                        notes=f"Split from order {order.order_number}. Reason: {reason}"
                    )
                    
                    total_split_amount = Decimal('0')
                    
                    # Move specified items to new order
                    for item_data in split_items:
                        original_item = get_object_or_404(OrderItem, id=item_data['order_item_id'], order=order)
                        split_quantity = item_data['quantity']
                        
                        if split_quantity >= original_item.quantity:
                            # Move entire item
                            original_item.order = new_order
                            original_item.save()
                            total_split_amount += original_item.total_price
                        else:
                            # Split item
                            split_total = original_item.unit_price * split_quantity
                            
                            # Create new item in split order
                            OrderItem.objects.create(
                                order=new_order,
                                product=original_item.product,
                                quantity=split_quantity,
                                unit_price=original_item.unit_price,
                                total_price=split_total,
                                status=original_item.status,
                                is_gift=original_item.is_gift,
                                gift_message=original_item.gift_message
                            )
                            
                            # Update original item
                            original_item.quantity -= split_quantity
                            original_item.total_price -= split_total
                            original_item.save()
                            
                            total_split_amount += split_total
                    
                    # Update order totals
                    new_order.total_amount = total_split_amount
                    new_order.save()
                    
                    order.total_amount -= total_split_amount
                    order.save()
                    
                    # Add timeline events
                    order.add_timeline_event(
                        status=order.status,
                        description=f"Order split. New order created: {new_order.order_number}. Reason: {reason}",
                        user=request.user
                    )
                    
                    new_order.add_timeline_event(
                        status=new_order.status,
                        description=f"Order created from split of {order.order_number}. Reason: {reason}",
                        user=request.user
                    )
                    
                    # Add admin notes
                    OrderNote.objects.create(
                        order=order,
                        note_type='internal',
                        title="Order Split",
                        content=f"Order split into {new_order.order_number}. Reason: {reason}\nNotes: {notes}",
                        created_by=request.user
                    )
                    
                    OrderNote.objects.create(
                        order=new_order,
                        note_type='internal',
                        title="Order Created from Split",
                        content=f"Created from split of {order.order_number}. Reason: {reason}\nNotes: {notes}",
                        created_by=request.user
                    )
                
                return Response({
                    'original_order': AdminOrderSerializer(order).data,
                    'new_order': AdminOrderSerializer(new_order).data,
                    'message': f'Order successfully split. New order: {new_order.order_number}'
                })
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def merge_orders(self, request, pk=None):
        """Merge multiple orders into one for complex fulfillment scenarios."""
        target_order = self.get_object()
        serializer = OrderMergeSerializer(data=request.data)
        
        if serializer.is_valid():
            source_order_ids = serializer.validated_data['source_order_ids']
            reason = serializer.validated_data['reason']
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    source_orders = Order.objects.filter(id__in=source_order_ids, customer=target_order.customer)
                    
                    if source_orders.count() != len(source_order_ids):
                        return Response(
                            {"error": "Some source orders not found or belong to different customer"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    total_merged_amount = Decimal('0')
                    merged_order_numbers = []
                    
                    # Move items from source orders to target order
                    for source_order in source_orders:
                        # Move all items
                        for item in source_order.items.all():
                            item.order = target_order
                            item.save()
                        
                        total_merged_amount += source_order.total_amount
                        merged_order_numbers.append(source_order.order_number)
                        
                        # Add timeline event to source order
                        source_order.add_timeline_event(
                            status='cancelled',
                            description=f"Order merged into {target_order.order_number}. Reason: {reason}",
                            user=request.user
                        )
                        
                        # Update source order status
                        source_order.status = 'cancelled'
                        source_order.save()
                        
                        # Add admin note to source order
                        OrderNote.objects.create(
                            order=source_order,
                            note_type='internal',
                            title="Order Merged",
                            content=f"Order merged into {target_order.order_number}. Reason: {reason}\nNotes: {notes}",
                            created_by=request.user
                        )
                    
                    # Update target order total
                    target_order.total_amount += total_merged_amount
                    target_order.save()
                    
                    # Add timeline event to target order
                    target_order.add_timeline_event(
                        status=target_order.status,
                        description=f"Orders merged: {', '.join(merged_order_numbers)}. Reason: {reason}",
                        user=request.user
                    )
                    
                    # Add admin note to target order
                    OrderNote.objects.create(
                        order=target_order,
                        note_type='internal',
                        title="Orders Merged",
                        content=f"Merged orders: {', '.join(merged_order_numbers)}. Reason: {reason}\nNotes: {notes}",
                        created_by=request.user
                    )
                
                return Response({
                    'merged_order': AdminOrderSerializer(target_order).data,
                    'merged_order_numbers': merged_order_numbers,
                    'message': f'Orders successfully merged into {target_order.order_number}'
                })
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_actions(self, request):
        """Perform bulk actions on multiple orders."""
        serializer = OrderBulkActionSerializer(data=request.data)
        
        if serializer.is_valid():
            order_ids = serializer.validated_data['order_ids']
            action = serializer.validated_data['action']
            parameters = serializer.validated_data.get('parameters', {})
            
            orders = Order.objects.filter(id__in=order_ids)
            results = []
            errors = []
            
            for order in orders:
                try:
                    if action == 'update_status':
                        new_status = parameters.get('status')
                        description = parameters.get('description', '')
                        
                        updated_order = OrderService.update_order_status(
                            order_id=order.id,
                            new_status=new_status,
                            user=request.user,
                            description=description
                        )
                        results.append(str(updated_order.id))
                    
                    elif action == 'assign_to_user':
                        # Create escalation and assign to user
                        assigned_user_id = parameters.get('user_id')
                        title = parameters.get('title', 'Bulk Assignment')
                        description = parameters.get('description', '')
                        
                        escalation = OrderEscalation.objects.create(
                            order=order,
                            escalation_type='manual_review',
                            priority='medium',
                            title=title,
                            description=description,
                            created_by=request.user,
                            assigned_to_id=assigned_user_id
                        )
                        results.append(str(order.id))
                    
                    elif action == 'add_note':
                        note_title = parameters.get('title', 'Bulk Note')
                        note_content = parameters.get('content', '')
                        note_type = parameters.get('type', 'internal')
                        
                        OrderNote.objects.create(
                            order=order,
                            note_type=note_type,
                            title=note_title,
                            content=note_content,
                            created_by=request.user
                        )
                        results.append(str(order.id))
                    
                    elif action == 'calculate_profitability':
                        # Calculate or recalculate profitability
                        profitability, created = OrderProfitability.objects.get_or_create(
                            order=order,
                            defaults={
                                'gross_revenue': order.total_amount,
                                'net_revenue': order.total_amount - order.discount_amount,
                            }
                        )
                        
                        # Set default costs (would be calculated from actual data in production)
                        profitability.product_cost = order.total_amount * Decimal('0.6')  # 60% of revenue
                        profitability.shipping_cost = order.shipping_amount
                        profitability.payment_processing_cost = order.total_amount * Decimal('0.03')  # 3% processing fee
                        profitability.calculate_profitability()
                        results.append(str(order.id))
                    
                    elif action == 'export':
                        # Add to export queue (would be handled by background task)
                        results.append(str(order.id))
                    
                    elif action == 'generate_documents':
                        document_type = parameters.get('document_type', 'invoice')
                        # Generate document (would integrate with document generation service)
                        OrderDocument.objects.create(
                            order=order,
                            document_type=document_type,
                            title=f"{document_type.title()} for Order {order.order_number}",
                            file_path=f"/documents/{order.order_number}_{document_type}.pdf",
                            file_size=1024,  # Mock size
                            mime_type="application/pdf",
                            generated_by=request.user
                        )
                        results.append(str(order.id))
                    
                    elif action == 'allocate_inventory':
                        # Allocate inventory for order
                        allocation, created = OrderAllocation.objects.get_or_create(
                            order=order,
                            defaults={
                                'status': 'allocated',
                                'allocated_at': timezone.now(),
                                'allocated_by': request.user,
                                'allocation_details': {'items': 'allocated'}
                            }
                        )
                        results.append(str(order.id))
                
                except Exception as e:
                    errors.append({'order_id': str(order.id), 'error': str(e)})
            
            return Response({
                'success_count': len(results),
                'error_count': len(errors),
                'successful_orders': results,
                'errors': errors
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def export_orders(self, request):
        """Export orders in various formats."""
        serializer = OrderExportSerializer(data=request.data)
        
        if serializer.is_valid():
            export_format = serializer.validated_data['export_format']
            date_range = serializer.validated_data.get('date_range', {})
            filters = serializer.validated_data.get('filters', {})
            fields = serializer.validated_data.get('fields', [])
            include_items = serializer.validated_data.get('include_items', True)
            
            # Get orders based on filters
            queryset = self.get_queryset()
            
            if date_range.get('start'):
                queryset = queryset.filter(created_at__gte=date_range['start'])
            if date_range.get('end'):
                queryset = queryset.filter(created_at__lte=date_range['end'])
            
            # Apply additional filters
            for field, value in filters.items():
                if hasattr(Order, field):
                    queryset = queryset.filter(**{field: value})
            
            if export_format == 'csv':
                return self._export_csv(queryset, fields, include_items)
            elif export_format == 'excel':
                return self._export_excel(queryset, fields, include_items)
            elif export_format == 'json':
                return self._export_json(queryset, fields, include_items)
            elif export_format == 'pdf':
                return self._export_pdf(queryset, fields, include_items)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _export_csv(self, queryset, fields, include_items):
        """Export orders as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        header = ['Order Number', 'Customer Email', 'Status', 'Total Amount', 'Created At']
        if include_items:
            header.extend(['Product Name', 'Quantity', 'Unit Price'])
        writer.writerow(header)
        
        # Write data
        for order in queryset:
            base_row = [
                order.order_number,
                order.customer.email,
                order.status,
                str(order.total_amount),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            if include_items:
                for item in order.items.all():
                    row = base_row + [
                        item.product.name,
                        item.quantity,
                        str(item.unit_price)
                    ]
                    writer.writerow(row)
            else:
                writer.writerow(base_row)
        
        return response
    
    def _export_excel(self, queryset, fields, include_items):
        """Export orders as Excel."""
        # This would use openpyxl or similar library
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="orders_export.xlsx"'
        
        # Mock Excel export - in production would use openpyxl
        response.write(b'Excel export not implemented in this demo')
        return response
    
    def _export_json(self, queryset, fields, include_items):
        """Export orders as JSON."""
        serializer = AdminOrderSerializer(queryset, many=True)
        response = HttpResponse(
            json.dumps(serializer.data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="orders_export.json"'
        return response
    
    def _export_pdf(self, queryset, fields, include_items):
        """Export orders as PDF report."""
        # This would use reportlab or similar library
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="orders_report.pdf"'
        
        # Mock PDF export - in production would use reportlab
        response.write(b'PDF export not implemented in this demo')
        return response
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get order forecasting and trend analysis."""
        serializer = OrderForecastSerializer(data=request.query_params)
        
        if serializer.is_valid():
            forecast_period = serializer.validated_data['forecast_period']
            forecast_type = serializer.validated_data['forecast_type']
            include_seasonality = serializer.validated_data['include_seasonality']
            confidence_interval = serializer.validated_data['confidence_interval']
            
            # Mock forecast data - in production would use ML models
            forecast_data = {
                'forecast_period': forecast_period,
                'forecast_type': forecast_type,
                'predictions': [
                    {'date': '2024-01-01', 'predicted_orders': 150, 'predicted_revenue': 15000},
                    {'date': '2024-01-02', 'predicted_orders': 160, 'predicted_revenue': 16000},
                    {'date': '2024-01-03', 'predicted_orders': 140, 'predicted_revenue': 14000},
                ],
                'confidence_interval': confidence_interval,
                'model_accuracy': 0.85
            }
            
            return Response(forecast_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderSearchFilterViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved order search filters."""
    serializer_class = OrderSearchFilterSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return OrderSearchFilter.objects.filter(
            Q(admin_user=self.request.user) | Q(is_public=True)
        ).order_by('name')
    
    def perform_create(self, serializer):
        serializer.save(admin_user=self.request.user)


class OrderWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order workflows and automation rules."""
    serializer_class = OrderWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderWorkflow.objects.all()
    
    @action(detail=True, methods=['post'])
    def test_workflow(self, request, pk=None):
        """Test workflow conditions and actions."""
        workflow = self.get_object()
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
            
            # Test conditions
            from .order_services import OrderStatusService
            conditions_met = OrderStatusService._check_workflow_conditions(order, workflow)
            
            return Response({
                'workflow_id': workflow.id,
                'order_id': order_id,
                'conditions_met': conditions_met,
                'conditions': workflow.conditions,
                'actions': workflow.actions
            })
        
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class OrderFraudScoreViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order fraud scores."""
    serializer_class = OrderFraudScoreSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderFraudScore.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['risk_level', 'is_flagged']
    ordering = ['-score', '-created_at']
    
    @action(detail=True, methods=['post'])
    def review_fraud_score(self, request, pk=None):
        """Review and update fraud score."""
        fraud_score = self.get_object()
        
        fraud_score.reviewed_by = request.user
        fraud_score.reviewed_at = timezone.now()
        fraud_score.review_notes = request.data.get('review_notes', '')
        fraud_score.is_flagged = request.data.get('is_flagged', fraud_score.is_flagged)
        fraud_score.save()
        
        # Create order note
        OrderNote.objects.create(
            order=fraud_score.order,
            note_type='internal',
            title='Fraud Score Reviewed',
            content=f'Fraud score reviewed by {request.user.username}. Notes: {fraud_score.review_notes}',
            created_by=request.user,
            is_important=True
        )
        
        serializer = self.get_serializer(fraud_score)
        return Response(serializer.data)


class OrderNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order notes."""
    serializer_class = OrderNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderNote.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'note_type', 'is_important', 'is_customer_visible']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OrderEscalationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order escalations."""
    serializer_class = OrderEscalationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderEscalation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'escalation_type', 'priority', 'status', 'assigned_to']
    ordering = ['-priority', '-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_escalation(self, request, pk=None):
        """Assign escalation to a user."""
        escalation = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        if not assigned_to_id:
            return Response({'error': 'assigned_to is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assigned_user = User.objects.get(id=assigned_to_id)
            escalation.assigned_to = assigned_user
            escalation.status = 'in_progress'
            escalation.save()
            
            # Create order note
            OrderNote.objects.create(
                order=escalation.order,
                note_type='internal',
                title='Escalation Assigned',
                content=f'Escalation assigned to {assigned_user.username} by {request.user.username}',
                created_by=request.user
            )
            
            serializer = self.get_serializer(escalation)
            return Response(serializer.data)
        
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def resolve_escalation(self, request, pk=None):
        """Resolve an escalation."""
        escalation = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        escalation.status = 'resolved'
        escalation.resolved_by = request.user
        escalation.resolved_at = timezone.now()
        escalation.resolution_notes = resolution_notes
        escalation.save()
        
        # Create order note
        OrderNote.objects.create(
            order=escalation.order,
            note_type='internal',
            title='Escalation Resolved',
            content=f'Escalation resolved by {request.user.username}. Resolution: {resolution_notes}',
            created_by=request.user,
            is_important=True
        )
        
        serializer = self.get_serializer(escalation)
        return Response(serializer.data)


class OrderSLAViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order SLA tracking."""
    serializer_class = OrderSLASerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderSLA.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['overall_sla_met', 'processing_sla_met', 'shipping_sla_met', 'delivery_sla_met']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def sla_report(self, request):
        """Get SLA compliance report."""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        total_orders = queryset.count()
        sla_met = queryset.filter(overall_sla_met=True).count()
        sla_missed = queryset.filter(overall_sla_met=False).count()
        
        processing_sla_met = queryset.filter(processing_sla_met=True).count()
        shipping_sla_met = queryset.filter(shipping_sla_met=True).count()
        delivery_sla_met = queryset.filter(delivery_sla_met=True).count()
        
        report = {
            'total_orders': total_orders,
            'overall_sla_compliance': (sla_met / total_orders * 100) if total_orders > 0 else 0,
            'sla_met': sla_met,
            'sla_missed': sla_missed,
            'processing_sla_compliance': (processing_sla_met / total_orders * 100) if total_orders > 0 else 0,
            'shipping_sla_compliance': (shipping_sla_met / total_orders * 100) if total_orders > 0 else 0,
            'delivery_sla_compliance': (delivery_sla_met / total_orders * 100) if total_orders > 0 else 0,
        }
        
        return Response(report)


class OrderAllocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order allocations."""
    serializer_class = OrderAllocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderAllocation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'allocated_by']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def release_allocation(self, request, pk=None):
        """Release inventory allocation."""
        allocation = self.get_object()
        reason = request.data.get('reason', 'Manual release')
        
        allocation.status = 'released'
        allocation.notes = f"Released by {request.user.username}. Reason: {reason}"
        allocation.save()
        
        # Create order note
        OrderNote.objects.create(
            order=allocation.order,
            note_type='internal',
            title='Inventory Allocation Released',
            content=f'Inventory allocation released by {request.user.username}. Reason: {reason}',
            created_by=request.user
        )
        
        serializer = self.get_serializer(allocation)
        return Response(serializer.data)


class OrderProfitabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order profitability analysis."""
    serializer_class = OrderProfitabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderProfitability.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['-profit_margin_percentage', '-net_profit']
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Recalculate profitability metrics."""
        profitability = self.get_object()
        
        # Update costs from request data
        for field in ['product_cost', 'shipping_cost', 'payment_processing_cost', 
                     'packaging_cost', 'handling_cost', 'marketing_cost', 'other_costs']:
            if field in request.data:
                setattr(profitability, field, Decimal(str(request.data[field])))
        
        profitability.calculate_profitability()
        
        serializer = self.get_serializer(profitability)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def profitability_report(self, request):
        """Get profitability analysis report."""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(Sum('net_revenue'))['net_revenue__sum'] or 0
        total_profit = queryset.aggregate(Sum('net_profit'))['net_profit__sum'] or 0
        avg_margin = queryset.aggregate(Avg('profit_margin_percentage'))['profit_margin_percentage__avg'] or 0
        
        profitable_orders = queryset.filter(net_profit__gt=0).count()
        loss_making_orders = queryset.filter(net_profit__lt=0).count()
        
        report = {
            'total_orders_analyzed': total_orders,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'average_profit_margin': avg_margin,
            'profitable_orders': profitable_orders,
            'loss_making_orders': loss_making_orders,
            'profitability_rate': (profitable_orders / total_orders * 100) if total_orders > 0 else 0
        }
        
        return Response(report)


class OrderDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order documents."""
    serializer_class = OrderDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderDocument.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'document_type', 'is_customer_accessible']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file."""
        document = self.get_object()
        
        # Update download tracking
        document.download_count += 1
        document.last_downloaded_at = timezone.now()
        document.save()
        
        # In production, this would serve the actual file
        response = HttpResponse(
            f"Document download: {document.title}",
            content_type=document.mime_type
        )
        response['Content-Disposition'] = f'attachment; filename="{document.title}"'
        return response


class OrderQualityControlViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order quality control."""
    serializer_class = OrderQualityControlSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderQualityControl.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'inspector', 'requires_reinspection']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def complete_inspection(self, request, pk=None):
        """Complete quality control inspection."""
        qc = self.get_object()
        
        qc.status = request.data.get('status', 'passed')
        qc.inspector = request.user
        qc.inspection_date = timezone.now()
        qc.checklist = request.data.get('checklist', {})
        qc.issues_found = request.data.get('issues_found', [])
        qc.corrective_actions = request.data.get('corrective_actions', [])
        qc.notes = request.data.get('notes', '')
        qc.requires_reinspection = request.data.get('requires_reinspection', False)
        qc.save()
        
        # Create order note
        OrderNote.objects.create(
            order=qc.order,
            note_type='internal',
            title='Quality Control Inspection Completed',
            content=f'QC inspection completed by {request.user.username}. Status: {qc.status}',
            created_by=request.user,
            is_important=qc.status == 'failed'
        )
        
        serializer = self.get_serializer(qc)
        return Response(serializer.data)


class OrderSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order subscriptions."""
    serializer_class = OrderSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderSubscription.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'frequency', 'customer']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def pause_subscription(self, request, pk=None):
        """Pause subscription."""
        subscription = self.get_object()
        reason = request.data.get('reason', 'Manual pause')
        
        subscription.status = 'paused'
        subscription.paused_at = timezone.now()
        subscription.paused_by = request.user
        subscription.pause_reason = reason
        subscription.save()
        
        # Create order note
        OrderNote.objects.create(
            order=subscription.original_order,
            note_type='internal',
            title='Subscription Paused',
            content=f'Subscription paused by {request.user.username}. Reason: {reason}',
            created_by=request.user
        )
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume_subscription(self, request, pk=None):
        """Resume paused subscription."""
        subscription = self.get_object()
        
        subscription.status = 'active'
        subscription.paused_at = None
        subscription.paused_by = None
        subscription.pause_reason = ''
        subscription.calculate_next_order_date()
        
        # Create order note
        OrderNote.objects.create(
            order=subscription.original_order,
            note_type='internal',
            title='Subscription Resumed',
            content=f'Subscription resumed by {request.user.username}',
            created_by=request.user
        )
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_next_order(self, request, pk=None):
        """Generate next subscription order."""
        subscription = self.get_object()
        
        if subscription.status != 'active':
            return Response(
                {'error': 'Subscription must be active to generate orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create new order based on subscription
                new_order = Order.objects.create(
                    customer=subscription.customer,
                    order_number=f"SUB-{subscription.id}-{subscription.total_orders_generated + 1}",
                    status='pending',
                    shipping_address=subscription.shipping_address,
                    billing_address=subscription.billing_address,
                    shipping_method=subscription.original_order.shipping_method,
                    payment_method=subscription.payment_method,
                    notes=f"Generated from subscription {subscription.id}"
                )
                
                # Add items from subscription config
                total_amount = Decimal('0.00')
                for item_config in subscription.items_config:
                    from apps.products.models import Product
                    product = Product.objects.get(id=item_config['product_id'])
                    quantity = item_config['quantity']
                    
                    OrderItem.objects.create(
                        order=new_order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price,
                        total_price=product.price * quantity
                    )
                    total_amount += product.price * quantity
                
                new_order.total_amount = total_amount
                new_order.save()
                
                # Update subscription
                subscription.last_order_date = timezone.now().date()
                subscription.total_orders_generated += 1
                subscription.calculate_next_order_date()
                subscription.save()
                
                # Create order note
                OrderNote.objects.create(
                    order=new_order,
                    note_type='system',
                    title='Subscription Order Generated',
                    content=f'Order generated from subscription {subscription.id}',
                    created_by=request.user
                )
                
                return Response({
                    'new_order': AdminOrderSerializer(new_order).data,
                    'subscription': self.get_serializer(subscription).data
                })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def export_orders(self, request):
        """Export orders in various formats."""
        serializer = OrderExportSerializer(data=request.data)
        
        if serializer.is_valid():
            export_format = serializer.validated_data['export_format']
            date_range = serializer.validated_data.get('date_range', {})
            filters = serializer.validated_data.get('filters', {})
            fields = serializer.validated_data.get('fields', [])
            include_items = serializer.validated_data.get('include_items', True)
            include_timeline = serializer.validated_data.get('include_timeline', False)
            include_notes = serializer.validated_data.get('include_notes', False)
            
            # Build queryset
            queryset = self.get_queryset()
            
            # Apply date range
            if date_range.get('start'):
                queryset = queryset.filter(created_at__date__gte=date_range['start'])
            if date_range.get('end'):
                queryset = queryset.filter(created_at__date__lte=date_range['end'])
            
            # Apply additional filters
            for field, value in filters.items():
                if hasattr(Order, field):
                    queryset = queryset.filter(**{field: value})
            
            if export_format == 'csv':
                return self._export_csv(queryset, fields, include_items, include_timeline, include_notes)
            elif export_format == 'json':
                return self._export_json(queryset, fields, include_items, include_timeline, include_notes)
            else:
                return Response({"error": "Export format not supported yet"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _export_csv(self, queryset, fields, include_items, include_timeline, include_notes):
        """Export orders as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Define headers
        headers = [
            'Order Number', 'Customer Email', 'Customer Name', 'Status', 'Payment Status',
            'Total Amount', 'Shipping Amount', 'Tax Amount', 'Discount Amount',
            'Shipping Method', 'Payment Method', 'Created At', 'Updated At'
        ]
        
        if include_items:
            headers.extend(['Items Count', 'Items Details'])
        
        writer.writerow(headers)
        
        # Write data
        for order in queryset:
            row = [
                order.order_number,
                order.customer.email,
                f"{order.customer.first_name} {order.customer.last_name}",
                order.status,
                order.payment_status,
                str(order.total_amount),
                str(order.shipping_amount),
                str(order.tax_amount),
                str(order.discount_amount),
                order.shipping_method,
                order.payment_method,
                order.created_at.isoformat(),
                order.updated_at.isoformat()
            ]
            
            if include_items:
                items_count = order.items.count()
                items_details = '; '.join([
                    f"{item.product.name} (Qty: {item.quantity}, Price: {item.total_price})"
                    for item in order.items.all()
                ])
                row.extend([items_count, items_details])
            
            writer.writerow(row)
        
        return response
    
    def _export_json(self, queryset, fields, include_items, include_timeline, include_notes):
        """Export orders as JSON."""
        orders_data = []
        
        for order in queryset:
            order_data = {
                'order_number': order.order_number,
                'customer_email': order.customer.email,
                'customer_name': f"{order.customer.first_name} {order.customer.last_name}",
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': str(order.total_amount),
                'shipping_amount': str(order.shipping_amount),
                'tax_amount': str(order.tax_amount),
                'discount_amount': str(order.discount_amount),
                'shipping_method': order.shipping_method,
                'payment_method': order.payment_method,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat()
            }
            
            if include_items:
                order_data['items'] = [
                    {
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price),
                        'total_price': str(item.total_price),
                        'status': item.status
                    }
                    for item in order.items.all()
                ]
            
            if include_timeline:
                order_data['timeline'] = [
                    {
                        'status': event.status,
                        'description': event.description,
                        'created_at': event.created_at.isoformat()
                    }
                    for event in order.timeline_events.all()
                ]
            
            if include_notes:
                order_data['notes'] = [
                    {
                        'title': note.title,
                        'content': note.content,
                        'note_type': note.note_type,
                        'created_at': note.created_at.isoformat()
                    }
                    for note in order.admin_notes.all()
                ]
            
            orders_data.append(order_data)
        
        response = HttpResponse(
            json.dumps(orders_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response


class OrderSearchFilterViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved order search filters."""
    serializer_class = OrderSearchFilterSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Get filters for current user and public filters."""
        return OrderSearchFilter.objects.filter(
            Q(admin_user=self.request.user) | Q(is_public=True)
        ).order_by('name')
    
    def perform_create(self, serializer):
        """Set the admin user when creating a filter."""
        serializer.save(admin_user=self.request.user)


class OrderWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order workflows and automation rules."""
    serializer_class = OrderWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderWorkflow.objects.all()


class OrderFraudScoreViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order fraud scores."""
    serializer_class = OrderFraudScoreSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderFraudScore.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['risk_level', 'is_flagged', 'order']
    ordering = ['-score', '-created_at']
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review and update fraud score."""
        fraud_score = self.get_object()
        
        fraud_score.reviewed_by = request.user
        fraud_score.reviewed_at = timezone.now()
        fraud_score.review_notes = request.data.get('review_notes', '')
        fraud_score.is_flagged = request.data.get('is_flagged', fraud_score.is_flagged)
        fraud_score.save()
        
        serializer = self.get_serializer(fraud_score)
        return Response(serializer.data)


class OrderNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order notes."""
    serializer_class = OrderNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderNote.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'note_type', 'is_important', 'created_by']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set the created_by user when creating a note."""
        serializer.save(created_by=self.request.user)


class OrderEscalationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order escalations."""
    serializer_class = OrderEscalationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderEscalation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'escalation_type', 'priority', 'status', 'assigned_to']
    ordering = ['-priority', '-created_at']
    
    def perform_create(self, serializer):
        """Set the created_by user when creating an escalation."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an escalation."""
        escalation = self.get_object()
        
        escalation.status = 'resolved'
        escalation.resolved_by = request.user
        escalation.resolved_at = timezone.now()
        escalation.resolution_notes = request.data.get('resolution_notes', '')
        escalation.save()
        
        serializer = self.get_serializer(escalation)
        return Response(serializer.data)


class OrderSLAViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order SLA tracking."""
    serializer_class = OrderSLASerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderSLA.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'overall_sla_met', 'processing_sla_met', 'shipping_sla_met', 'delivery_sla_met']
    ordering = ['-created_at']


class OrderAllocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order allocations."""
    serializer_class = OrderAllocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderAllocation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'status', 'allocated_by']
    ordering = ['-created_at']


class OrderProfitabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order profitability analysis."""
    serializer_class = OrderProfitabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderProfitability.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order']
    ordering = ['-calculated_at']


class OrderDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order documents."""
    serializer_class = OrderDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderDocument.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'document_type', 'is_customer_accessible']
    ordering = ['-created_at']


class OrderQualityControlViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order quality control."""
    serializer_class = OrderQualityControlSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderQualityControl.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'status', 'inspector', 'requires_reinspection']
    ordering = ['-created_at']


class OrderSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order subscriptions."""
    serializer_class = OrderSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = OrderSubscription.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer', 'frequency', 'status']
    ordering = ['-created_at']