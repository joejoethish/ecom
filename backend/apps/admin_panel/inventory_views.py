"""
Advanced Inventory Management System views for comprehensive admin panel.
"""
import io
import csv
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, F, Sum, Count, Avg
from django.http import HttpResponse
from django.utils import timezone
from django.core.files.storage import default_storage
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from apps.products.models import Product
from .inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization,
    InventoryOptimizationItem, InventoryReport
)
from .inventory_serializers import (
    InventoryLocationSerializer, InventoryItemSerializer, InventoryValuationSerializer,
    InventoryAdjustmentSerializer, InventoryTransferSerializer, InventoryReservationSerializer,
    InventoryAlertSerializer, InventoryAuditSerializer, InventoryAuditItemSerializer,
    InventoryForecastSerializer, InventoryOptimizationSerializer, InventoryReportSerializer,
    InventoryDashboardSerializer, BulkInventoryActionSerializer, InventoryImportSerializer,
    InventoryExportSerializer
)
from .inventory_services import (
    InventoryTrackingService, InventoryValuationService, InventoryAdjustmentService,
    InventoryTransferService, InventoryReservationService, InventoryAlertService,
    InventoryOptimizationService, InventoryReportService, InventoryImportExportService
)
from .permissions import AdminPermissionRequired
from .models import AdminUser


class InventoryLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing inventory locations."""
    
    queryset = InventoryLocation.objects.select_related('warehouse').all()
    serializer_class = InventoryLocationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.manage']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['warehouse', 'location_type', 'is_active', 'is_blocked']
    search_fields = ['location_code', 'zone', 'aisle', 'shelf']
    ordering_fields = ['location_code', 'warehouse', 'capacity', 'current_utilization']
    ordering = ['location_code']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Add any additional filtering based on user role
        if hasattr(self.request.user, 'role'):
            if self.request.user.role in ['viewer', 'analyst']:
                queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def block_location(self, request, pk=None):
        """Block a location from use."""
        location = self.get_object()
        reason = request.data.get('reason', 'Manual block')
        
        location.is_blocked = True
        location.blocked_reason = reason
        location.save()
        
        return Response({
            'message': 'Location blocked successfully',
            'location_code': location.location_code,
            'reason': reason
        })
    
    @action(detail=True, methods=['post'])
    def unblock_location(self, request, pk=None):
        """Unblock a location."""
        location = self.get_object()
        
        location.is_blocked = False
        location.blocked_reason = ''
        location.save()
        
        return Response({
            'message': 'Location unblocked successfully',
            'location_code': location.location_code
        })
    
    @action(detail=True, methods=['get'])
    def utilization_report(self, request, pk=None):
        """Get detailed utilization report for a location."""
        location = self.get_object()
        
        items = InventoryItem.objects.filter(location=location, is_available=True)
        
        report = {
            'location_code': location.location_code,
            'capacity': location.capacity,
            'current_utilization': location.current_utilization,
            'utilization_percentage': location.utilization_percentage,
            'items_count': items.count(),
            'total_quantity': items.aggregate(total=Sum('quantity'))['total'] or 0,
            'total_value': items.aggregate(
                total=Sum(F('quantity') * F('unit_cost'))
            )['total'] or Decimal('0'),
            'items_by_condition': items.values('condition').annotate(
                count=Count('id'),
                quantity=Sum('quantity')
            ),
        }
        
        return Response(report)


class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual inventory items."""
    
    queryset = InventoryItem.objects.select_related(
        'product', 'location__warehouse', 'supplier'
    ).all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.manage']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'product', 'location', 'condition', 'quality_grade',
        'is_available', 'is_quarantined'
    ]
    search_fields = ['product__name', 'product__sku', 'serial_number', 'lot_number', 'batch_number']
    ordering_fields = ['product__name', 'quantity', 'unit_cost', 'expiry_date', 'received_date']
    ordering = ['-received_date']
    
    def get_queryset(self):
        """Filter queryset with additional parameters."""
        queryset = super().get_queryset()
        
        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)
        
        # Filter by expiry status
        expiry_filter = self.request.query_params.get('expiry_status')
        if expiry_filter == 'expired':
            queryset = queryset.filter(expiry_date__lt=date.today())
        elif expiry_filter == 'expiring_soon':
            soon_date = date.today() + timedelta(days=30)
            queryset = queryset.filter(
                expiry_date__gte=date.today(),
                expiry_date__lte=soon_date
            )
        
        # Filter by stock level
        stock_filter = self.request.query_params.get('stock_level')
        if stock_filter == 'low':
            queryset = queryset.filter(quantity__lte=F('product__inventory__reorder_point'))
        elif stock_filter == 'out':
            queryset = queryset.filter(quantity=0)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def quarantine(self, request, pk=None):
        """Quarantine an inventory item."""
        item = self.get_object()
        reason = request.data.get('reason', 'Quality issue')
        
        item.is_quarantined = True
        item.quarantine_reason = reason
        item.is_available = False
        item.save()
        
        # Create alert
        InventoryAlertService.create_alert(
            product=item.product,
            location=item.location,
            alert_type='quality_issue',
            severity='high',
            title=f'Item Quarantined: {item.product.name}',
            description=f'Item quarantined due to: {reason}',
            current_value=1,
            threshold_value=0
        )
        
        return Response({
            'message': 'Item quarantined successfully',
            'reason': reason
        })
    
    @action(detail=True, methods=['post'])
    def release_quarantine(self, request, pk=None):
        """Release an item from quarantine."""
        item = self.get_object()
        
        item.is_quarantined = False
        item.quarantine_reason = ''
        item.is_available = True
        item.save()
        
        return Response({'message': 'Item released from quarantine'})
    
    @action(detail=False, methods=['get'])
    def expiring_items(self, request):
        """Get items expiring within specified days."""
        days = int(request.query_params.get('days', 30))
        expiry_date = date.today() + timedelta(days=days)
        
        items = self.get_queryset().filter(
            expiry_date__lte=expiry_date,
            expiry_date__gte=date.today(),
            is_available=True
        )
        
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'days_threshold': days,
            'items': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_update_condition(self, request):
        """Bulk update condition of multiple items."""
        item_ids = request.data.get('item_ids', [])
        new_condition = request.data.get('condition')
        reason = request.data.get('reason', 'Bulk condition update')
        
        if not item_ids or not new_condition:
            return Response(
                {'error': 'item_ids and condition are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = InventoryItem.objects.filter(
            id__in=item_ids
        ).update(condition=new_condition)
        
        return Response({
            'message': f'Updated condition for {updated_count} items',
            'new_condition': new_condition,
            'reason': reason
        })


class InventoryValuationViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory valuations."""
    
    queryset = InventoryValuation.objects.select_related(
        'product', 'warehouse', 'calculated_by'
    ).all()
    serializer_class = InventoryValuationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.valuation']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'warehouse', 'costing_method', 'valuation_date']
    search_fields = ['product__name', 'product__sku']
    ordering_fields = ['valuation_date', 'total_value', 'unit_cost']
    ordering = ['-valuation_date']
    
    @action(detail=False, methods=['post'])
    def calculate_valuation(self, request):
        """Calculate inventory valuation for a product."""
        product_id = request.data.get('product_id')
        warehouse_id = request.data.get('warehouse_id')
        costing_method = request.data.get('costing_method', 'weighted_average')
        
        if not product_id or not warehouse_id:
            return Response(
                {'error': 'product_id and warehouse_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            valuation = InventoryValuationService.create_valuation_record(
                product_id=product_id,
                warehouse_id=warehouse_id,
                costing_method=costing_method,
                user=request.user
            )
            
            serializer = self.get_serializer(valuation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_calculate(self, request):
        """Calculate valuations for multiple products."""
        warehouse_id = request.data.get('warehouse_id')
        costing_method = request.data.get('costing_method', 'weighted_average')
        product_ids = request.data.get('product_ids', [])
        
        if not warehouse_id:
            return Response(
                {'error': 'warehouse_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not product_ids:
            # Calculate for all products in warehouse
            product_ids = InventoryItem.objects.filter(
                location__warehouse_id=warehouse_id
            ).values_list('product_id', flat=True).distinct()
        
        results = []
        errors = []
        
        for product_id in product_ids:
            try:
                valuation = InventoryValuationService.create_valuation_record(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    costing_method=costing_method,
                    user=request.user
                )
                results.append(valuation.id)
            except Exception as e:
                errors.append(f"Product {product_id}: {str(e)}")
        
        return Response({
            'calculated': len(results),
            'errors': len(errors),
            'valuation_ids': results,
            'error_details': errors
        })


class InventoryAdjustmentViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory adjustments."""
    
    queryset = InventoryAdjustment.objects.select_related(
        'product', 'location', 'requested_by', 'approved_by', 'applied_by'
    ).all()
    serializer_class = InventoryAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.adjust']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'location', 'adjustment_type', 'status', 'requested_by']
    search_fields = ['adjustment_number', 'product__name', 'reason_description']
    ordering_fields = ['requested_date', 'adjustment_quantity', 'total_cost_impact']
    ordering = ['-requested_date']
    
    def perform_create(self, serializer):
        """Set the requesting user when creating adjustment."""
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an adjustment request."""
        adjustment = self.get_object()
        notes = request.data.get('notes', '')
        
        if adjustment.status != 'pending':
            return Response(
                {'error': 'Only pending adjustments can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            approved_adjustment = InventoryAdjustmentService.approve_adjustment(
                adjustment.id, request.user, notes
            )
            serializer = self.get_serializer(approved_adjustment)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an adjustment request."""
        adjustment = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        if adjustment.status != 'pending':
            return Response(
                {'error': 'Only pending adjustments can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        adjustment.status = 'rejected'
        adjustment.approved_by = request.user
        adjustment.approved_date = timezone.now()
        adjustment.notes = f"Rejected: {reason}"
        adjustment.save()
        
        serializer = self.get_serializer(adjustment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply an approved adjustment."""
        adjustment = self.get_object()
        
        if adjustment.status != 'approved':
            return Response(
                {'error': 'Only approved adjustments can be applied'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            applied_adjustment = InventoryAdjustmentService.apply_adjustment(
                adjustment.id, request.user
            )
            serializer = self.get_serializer(applied_adjustment)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get adjustments pending approval."""
        pending = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response({
            'count': pending.count(),
            'adjustments': serializer.data
        })


class InventoryTransferViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory transfers."""
    
    queryset = InventoryTransfer.objects.select_related(
        'product', 'source_location', 'destination_location',
        'requested_by', 'shipped_by', 'received_by'
    ).all()
    serializer_class = InventoryTransferSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.transfer']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'source_location', 'destination_location', 'status']
    search_fields = ['transfer_number', 'product__name', 'tracking_number']
    ordering_fields = ['requested_date', 'shipped_date', 'received_date']
    ordering = ['-requested_date']
    
    def perform_create(self, serializer):
        """Set the requesting user when creating transfer."""
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark transfer as shipped."""
        transfer = self.get_object()
        tracking_number = request.data.get('tracking_number', '')
        
        if transfer.status != 'pending':
            return Response(
                {'error': 'Only pending transfers can be shipped'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            shipped_transfer = InventoryTransferService.ship_transfer(
                transfer.id, request.user, tracking_number
            )
            serializer = self.get_serializer(shipped_transfer)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Receive transfer."""
        transfer = self.get_object()
        quantity_received = request.data.get('quantity_received')
        
        if transfer.status != 'in_transit':
            return Response(
                {'error': 'Only in-transit transfers can be received'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not quantity_received:
            return Response(
                {'error': 'quantity_received is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            received_transfer = InventoryTransferService.receive_transfer(
                transfer.id, int(quantity_received), request.user
            )
            serializer = self.get_serializer(received_transfer)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def in_transit(self, request):
        """Get transfers currently in transit."""
        in_transit = self.get_queryset().filter(status='in_transit')
        serializer = self.get_serializer(in_transit, many=True)
        return Response({
            'count': in_transit.count(),
            'transfers': serializer.data
        })


class InventoryReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory reservations."""
    
    queryset = InventoryReservation.objects.select_related(
        'product', 'location', 'reserved_by'
    ).all()
    serializer_class = InventoryReservationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.reserve']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'location', 'reservation_type', 'status', 'priority']
    search_fields = ['reservation_number', 'product__name']
    ordering_fields = ['reserved_date', 'expiry_date', 'priority']
    ordering = ['-reserved_date']
    
    def perform_create(self, serializer):
        """Set the reserving user when creating reservation."""
        serializer.save(reserved_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def fulfill(self, request, pk=None):
        """Fulfill a reservation."""
        reservation = self.get_object()
        quantity_fulfilled = request.data.get('quantity_fulfilled')
        
        if reservation.status not in ['active', 'partial']:
            return Response(
                {'error': 'Only active reservations can be fulfilled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not quantity_fulfilled:
            return Response(
                {'error': 'quantity_fulfilled is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fulfilled_reservation = InventoryReservationService.fulfill_reservation(
                reservation.id, int(quantity_fulfilled), request.user
            )
            serializer = self.get_serializer(fulfilled_reservation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a reservation."""
        reservation = self.get_object()
        
        if reservation.status not in ['active', 'partial']:
            return Response(
                {'error': 'Only active reservations can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cancelled_reservation = InventoryReservationService.cancel_reservation(
                reservation.id, request.user
            )
            serializer = self.get_serializer(cancelled_reservation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get reservations expiring within specified hours."""
        hours = int(request.query_params.get('hours', 24))
        expiry_time = timezone.now() + timedelta(hours=hours)
        
        expiring = self.get_queryset().filter(
            status='active',
            expiry_date__lte=expiry_time
        )
        
        serializer = self.get_serializer(expiring, many=True)
        return Response({
            'count': expiring.count(),
            'hours_threshold': hours,
            'reservations': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def cleanup_expired(self, request):
        """Clean up expired reservations."""
        count = InventoryReservationService.cleanup_expired_reservations()
        return Response({
            'message': f'Cleaned up {count} expired reservations'
        })


class InventoryAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory alerts."""
    
    queryset = InventoryAlert.objects.select_related(
        'product', 'location', 'acknowledged_by', 'resolved_by'
    ).all()
    serializer_class = InventoryAlertSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.alerts']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'location', 'alert_type', 'severity', 'status']
    search_fields = ['alert_number', 'title', 'product__name']
    ordering_fields = ['triggered_date', 'severity', 'current_value']
    ordering = ['-triggered_date']
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        
        if alert.status != 'active':
            return Response(
                {'error': 'Only active alerts can be acknowledged'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        acknowledged_alert = InventoryAlertService.acknowledge_alert(
            alert.id, request.user, notes
        )
        serializer = self.get_serializer(acknowledged_alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        
        if alert.status not in ['active', 'acknowledged']:
            return Response(
                {'error': 'Only active or acknowledged alerts can be resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resolved_alert = InventoryAlertService.resolve_alert(
            alert.id, request.user, notes
        )
        serializer = self.get_serializer(resolved_alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """Get all active alerts."""
        active = self.get_queryset().filter(status='active')
        
        # Group by severity
        alerts_by_severity = {}
        for alert in active:
            if alert.severity not in alerts_by_severity:
                alerts_by_severity[alert.severity] = []
            alerts_by_severity[alert.severity].append(alert)
        
        serialized_alerts = {}
        for severity, alerts in alerts_by_severity.items():
            serialized_alerts[severity] = self.get_serializer(alerts, many=True).data
        
        return Response({
            'total_active': active.count(),
            'by_severity': serialized_alerts
        })
    
    @action(detail=False, methods=['post'])
    def bulk_acknowledge(self, request):
        """Bulk acknowledge multiple alerts."""
        alert_ids = request.data.get('alert_ids', [])
        notes = request.data.get('notes', 'Bulk acknowledgment')
        
        if not alert_ids:
            return Response(
                {'error': 'alert_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        acknowledged_count = 0
        for alert_id in alert_ids:
            try:
                InventoryAlertService.acknowledge_alert(alert_id, request.user, notes)
                acknowledged_count += 1
            except:
                continue
        
        return Response({
            'message': f'Acknowledged {acknowledged_count} alerts',
            'total_requested': len(alert_ids)
        })


class InventoryAuditViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory audits."""
    
    queryset = InventoryAudit.objects.select_related('warehouse', 'supervisor').all()
    serializer_class = InventoryAuditSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.audit']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['warehouse', 'audit_type', 'status', 'supervisor']
    search_fields = ['audit_number']
    ordering_fields = ['planned_date', 'start_date', 'accuracy_percentage']
    ordering = ['-planned_date']
    
    @action(detail=True, methods=['post'])
    def start_audit(self, request, pk=None):
        """Start an audit."""
        audit = self.get_object()
        
        if audit.status != 'planned':
            return Response(
                {'error': 'Only planned audits can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        audit.status = 'in_progress'
        audit.start_date = timezone.now()
        audit.save()
        
        serializer = self.get_serializer(audit)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_audit(self, request, pk=None):
        """Complete an audit and calculate results."""
        audit = self.get_object()
        
        if audit.status != 'in_progress':
            return Response(
                {'error': 'Only in-progress audits can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate audit results
        audit_items = audit.audit_items.all()
        total_items = audit_items.count()
        items_with_variances = audit_items.filter(variance_quantity__ne=0).count()
        total_variance_value = audit_items.aggregate(
            total=Sum('variance_value')
        )['total'] or Decimal('0')
        
        accuracy_percentage = ((total_items - items_with_variances) / total_items * 100) if total_items > 0 else 100
        
        # Update audit
        audit.status = 'completed'
        audit.end_date = timezone.now()
        audit.total_items_counted = total_items
        audit.items_with_variances = items_with_variances
        audit.total_variance_value = total_variance_value
        audit.accuracy_percentage = accuracy_percentage
        audit.save()
        
        serializer = self.get_serializer(audit)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def variance_report(self, request, pk=None):
        """Get variance report for an audit."""
        audit = self.get_object()
        
        variances = audit.audit_items.filter(
            variance_quantity__ne=0
        ).select_related('product', 'location')
        
        variance_data = []
        for item in variances:
            variance_data.append({
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'location_code': item.location.location_code,
                'system_quantity': item.system_quantity,
                'counted_quantity': item.counted_quantity,
                'variance_quantity': item.variance_quantity,
                'variance_percentage': item.variance_percentage,
                'variance_value': item.variance_value,
                'discrepancy_reason': item.discrepancy_reason,
            })
        
        return Response({
            'audit_number': audit.audit_number,
            'total_variances': len(variance_data),
            'total_variance_value': audit.total_variance_value,
            'accuracy_percentage': audit.accuracy_percentage,
            'variances': variance_data
        })


class InventoryOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet for inventory optimization analysis."""
    
    queryset = InventoryOptimization.objects.select_related('warehouse', 'analyzed_by').all()
    serializer_class = InventoryOptimizationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.optimize']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['warehouse', 'analysis_type', 'analyzed_by']
    search_fields = ['analysis_number']
    ordering_fields = ['analysis_date', 'total_value_analyzed']
    ordering = ['-analysis_date']
    
    @action(detail=False, methods=['post'])
    def run_abc_analysis(self, request):
        """Run ABC analysis for a warehouse."""
        warehouse_id = request.data.get('warehouse_id')
        period_days = request.data.get('period_days', 365)
        
        if not warehouse_id:
            return Response(
                {'error': 'warehouse_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            optimization = InventoryOptimizationService.perform_abc_analysis(
                warehouse_id=warehouse_id,
                user=request.user,
                period_days=period_days
            )
            
            serializer = self.get_serializer(optimization)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def identify_slow_moving(self, request):
        """Identify slow-moving items."""
        warehouse_id = request.data.get('warehouse_id')
        days_threshold = request.data.get('days_threshold', 90)
        
        if not warehouse_id:
            return Response(
                {'error': 'warehouse_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slow_moving_items = InventoryOptimizationService.identify_slow_moving_items(
            warehouse_id=warehouse_id,
            days_threshold=days_threshold
        )
        
        return Response({
            'warehouse_id': warehouse_id,
            'days_threshold': days_threshold,
            'slow_moving_count': len(slow_moving_items),
            'items': slow_moving_items
        })
    
    @action(detail=True, methods=['get'])
    def category_breakdown(self, request, pk=None):
        """Get detailed breakdown by ABC category."""
        optimization = self.get_object()
        
        if optimization.analysis_type != 'abc':
            return Response(
                {'error': 'This endpoint is only for ABC analysis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        breakdown = {
            'A': {
                'count': optimization.category_a_count,
                'value': optimization.category_a_value,
                'percentage_of_items': (optimization.category_a_count / optimization.total_products_analyzed * 100) if optimization.total_products_analyzed > 0 else 0,
                'percentage_of_value': (optimization.category_a_value / optimization.total_value_analyzed * 100) if optimization.total_value_analyzed > 0 else 0,
            },
            'B': {
                'count': optimization.category_b_count,
                'value': optimization.category_b_value,
                'percentage_of_items': (optimization.category_b_count / optimization.total_products_analyzed * 100) if optimization.total_products_analyzed > 0 else 0,
                'percentage_of_value': (optimization.category_b_value / optimization.total_value_analyzed * 100) if optimization.total_value_analyzed > 0 else 0,
            },
            'C': {
                'count': optimization.category_c_count,
                'value': optimization.category_c_value,
                'percentage_of_items': (optimization.category_c_count / optimization.total_products_analyzed * 100) if optimization.total_products_analyzed > 0 else 0,
                'percentage_of_value': (optimization.category_c_value / optimization.total_value_analyzed * 100) if optimization.total_value_analyzed > 0 else 0,
            }
        }
        
        return Response({
            'analysis_number': optimization.analysis_number,
            'total_products': optimization.total_products_analyzed,
            'total_value': optimization.total_value_analyzed,
            'breakdown': breakdown
        })


class InventoryDashboardViewSet(viewsets.ViewSet):
    """ViewSet for inventory dashboard data."""
    
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view']
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get inventory dashboard overview."""
        warehouse_id = request.query_params.get('warehouse_id')
        
        # Get real-time stock levels
        stock_data = InventoryTrackingService.get_real_time_stock_levels(warehouse_id)
        
        # Get active alerts
        active_alerts = InventoryAlert.objects.filter(status='active')
        if warehouse_id:
            active_alerts = active_alerts.filter(location__warehouse_id=warehouse_id)
        
        # Get pending adjustments
        pending_adjustments = InventoryAdjustment.objects.filter(status='pending')
        if warehouse_id:
            pending_adjustments = pending_adjustments.filter(location__warehouse_id=warehouse_id)
        
        # Get active transfers
        active_transfers = InventoryTransfer.objects.filter(status__in=['pending', 'in_transit'])
        if warehouse_id:
            active_transfers = active_transfers.filter(
                Q(source_location__warehouse_id=warehouse_id) |
                Q(destination_location__warehouse_id=warehouse_id)
            )
        
        # Get active reservations
        active_reservations = InventoryReservation.objects.filter(status='active')
        if warehouse_id:
            active_reservations = active_reservations.filter(location__warehouse_id=warehouse_id)
        
        # Recent activity
        recent_adjustments = InventoryAdjustment.objects.filter(
            status='applied',
            applied_date__gte=timezone.now() - timedelta(days=7)
        ).select_related('product', 'location', 'requested_by')[:10]
        
        recent_transfers = InventoryTransfer.objects.filter(
            received_date__gte=timezone.now() - timedelta(days=7)
        ).select_related('product', 'source_location', 'destination_location')[:10]
        
        recent_alerts = InventoryAlert.objects.filter(
            triggered_date__gte=timezone.now() - timedelta(days=7)
        ).select_related('product', 'location')[:10]
        
        dashboard_data = {
            'total_products': stock_data.get('total_items', 0),
            'total_locations': InventoryLocation.objects.filter(
                warehouse_id=warehouse_id if warehouse_id else None
            ).count() if warehouse_id else InventoryLocation.objects.count(),
            'total_value': stock_data.get('total_value', 0),
            'low_stock_items': stock_data.get('low_stock_count', 0),
            'out_of_stock_items': stock_data.get('out_of_stock_count', 0),
            'overstock_items': 0,  # Would need additional calculation
            'expired_items': stock_data.get('expired_count', 0),
            'expiring_soon_items': InventoryItem.objects.filter(
                expiry_date__lte=date.today() + timedelta(days=30),
                expiry_date__gte=date.today()
            ).count(),
            'active_alerts': active_alerts.count(),
            'pending_adjustments': pending_adjustments.count(),
            'active_transfers': active_transfers.count(),
            'active_reservations': active_reservations.count(),
            'average_turnover_rate': Decimal('6.5'),  # Simplified
            'slow_moving_items': 0,  # Would need calculation
            'dead_stock_items': 0,  # Would need calculation
            'recent_adjustments': InventoryAdjustmentSerializer(recent_adjustments, many=True).data,
            'recent_transfers': InventoryTransferSerializer(recent_transfers, many=True).data,
            'recent_alerts': InventoryAlertSerializer(recent_alerts, many=True).data,
        }
        
        serializer = InventoryDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """Get stock level summary by warehouse."""
        warehouses = Warehouse.objects.all()
        
        summary = []
        for warehouse in warehouses:
            stock_data = InventoryTrackingService.get_real_time_stock_levels(warehouse.id)
            summary.append({
                'warehouse_id': warehouse.id,
                'warehouse_name': warehouse.name,
                'total_items': stock_data.get('total_items', 0),
                'total_quantity': stock_data.get('total_quantity', 0),
                'total_value': stock_data.get('total_value', 0),
                'low_stock_count': stock_data.get('low_stock_count', 0),
                'out_of_stock_count': stock_data.get('out_of_stock_count', 0),
            })
        
        return Response({
            'warehouses': summary,
            'generated_at': timezone.now()
        })


class InventoryImportExportViewSet(viewsets.ViewSet):
    """ViewSet for inventory import/export operations."""
    
    permission_classes = [permissions.IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['inventory.view', 'inventory.import_export']
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """Import inventory data from file."""
        serializer = InventoryImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        import_type = serializer.validated_data['import_type']
        warehouse = serializer.validated_data['warehouse']
        validate_only = serializer.validated_data['validate_only']
        
        # Save uploaded file temporarily
        file_path = default_storage.save(f'temp/{file.name}', file)
        
        try:
            results = InventoryImportExportService.import_inventory_data(
                file_path=file_path,
                import_type=import_type,
                warehouse_id=warehouse.id,
                user=request.user,
                validate_only=validate_only
            )
            
            return Response(results)
            
        finally:
            # Clean up temporary file
            default_storage.delete(file_path)
    
    @action(detail=False, methods=['post'])
    def export_data(self, request):
        """Export inventory data to file."""
        serializer = InventoryExportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        export_type = serializer.validated_data['export_type']
        format = serializer.validated_data['format']
        filters = serializer.validated_data.get('filters', {})
        
        try:
            file_path = InventoryImportExportService.export_inventory_data(
                export_type=export_type,
                format=format,
                filters=filters
            )
            
            # Return file for download
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
                return response
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_actions(self, request):
        """Perform bulk actions on inventory items."""
        serializer = BulkInventoryActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        items = serializer.validated_data['items']
        parameters = serializer.validated_data.get('parameters', {})
        notes = serializer.validated_data.get('notes', '')
        
        results = {
            'action': action,
            'total_items': len(items),
            'processed': 0,
            'errors': [],
            'warnings': []
        }
        
        # Process bulk action based on type
        if action == 'adjust_stock':
            for item in items:
                try:
                    # Implement stock adjustment logic
                    results['processed'] += 1
                except Exception as e:
                    results['errors'].append(f"Item {item.get('id', 'unknown')}: {str(e)}")
        
        elif action == 'update_locations':
            for item in items:
                try:
                    # Implement location update logic
                    results['processed'] += 1
                except Exception as e:
                    results['errors'].append(f"Item {item.get('id', 'unknown')}: {str(e)}")
        
        # Add more bulk actions as needed
        
        return Response(results)