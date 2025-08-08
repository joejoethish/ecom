"""
Views for Comprehensive Supplier and Vendor Management System
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, SupplierDocument,
    PurchaseOrder, PurchaseOrderItem, SupplierPerformanceMetric,
    SupplierCommunication, SupplierContract, SupplierAudit,
    SupplierRiskAssessment, SupplierQualification, SupplierPayment
)
from .supplier_serializers import (
    SupplierCategorySerializer, SupplierSerializer, SupplierListSerializer,
    SupplierContactSerializer, SupplierDocumentSerializer,
    PurchaseOrderSerializer, PurchaseOrderListSerializer, PurchaseOrderItemSerializer,
    SupplierPerformanceMetricSerializer, SupplierCommunicationSerializer,
    SupplierContractSerializer, SupplierAuditSerializer,
    SupplierRiskAssessmentSerializer, SupplierQualificationSerializer,
    SupplierPaymentSerializer, SupplierAnalyticsSerializer,
    SupplierDashboardSerializer, SupplierReportSerializer
)
from .permissions import AdminPermissionRequired


class SupplierCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier categories."""
    queryset = SupplierCategory.objects.all()
    serializer_class = SupplierCategorySerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view', 'suppliers.manage']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get hierarchical tree of categories."""
        def build_tree(parent=None):
            categories = self.queryset.filter(parent=parent, is_active=True)
            tree = []
            for category in categories:
                node = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'suppliers_count': category.supplier_set.filter(status='active').count(),
                    'children': build_tree(category)
                }
                tree.append(node)
            return tree
        
        tree = build_tree()
        return Response(tree)


class SupplierViewSet(viewsets.ModelViewSet):
    """Comprehensive ViewSet for managing suppliers."""
    queryset = SupplierProfile.objects.select_related('category', 'created_by', 'last_modified_by').prefetch_related('contacts', 'documents')
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'supplier_type', 'category', 'risk_level', 'is_preferred',
        'is_certified', 'is_minority_owned', 'is_woman_owned', 'is_veteran_owned'
    ]
    search_fields = [
        'supplier_code', 'name', 'legal_name', 'primary_contact_name',
        'primary_contact_email', 'city', 'country'
    ]
    ordering_fields = [
        'name', 'supplier_code', 'overall_rating', 'created_at',
        'last_audit_date', 'total_spent'
    ]
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update']:
            permissions[-1].required_permissions = ['suppliers.create', 'suppliers.edit']
        elif self.action == 'destroy':
            permissions[-1].required_permissions = ['suppliers.delete']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)

    @action(detail=True, methods=['get'])
    def performance_history(self, request, pk=None):
        """Get supplier performance history."""
        supplier = self.get_object()
        metrics = supplier.performance_metrics.order_by('-measurement_date')[:50]
        serializer = SupplierPerformanceMetricSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def purchase_orders(self, request, pk=None):
        """Get supplier's purchase orders."""
        supplier = self.get_object()
        orders = supplier.purchase_orders.order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        # Pagination
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = PurchaseOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def communications(self, request, pk=None):
        """Get supplier communications."""
        supplier = self.get_object()
        communications = supplier.communications.order_by('-created_at')
        
        # Apply filters
        comm_type = request.query_params.get('type')
        if comm_type:
            communications = communications.filter(communication_type=comm_type)
        
        page = self.paginate_queryset(communications)
        if page is not None:
            serializer = SupplierCommunicationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SupplierCommunicationSerializer(communications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def contracts(self, request, pk=None):
        """Get supplier contracts."""
        supplier = self.get_object()
        contracts = supplier.contracts.order_by('-created_at')
        serializer = SupplierContractSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def risk_assessments(self, request, pk=None):
        """Get supplier risk assessments."""
        supplier = self.get_object()
        assessments = supplier.risk_assessments.order_by('-assessment_date')
        serializer = SupplierRiskAssessmentSerializer(assessments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def audits(self, request, pk=None):
        """Get supplier audits."""
        supplier = self.get_object()
        audits = supplier.audits.order_by('-planned_date')
        serializer = SupplierAuditSerializer(audits, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_rating(self, request, pk=None):
        """Update supplier ratings."""
        supplier = self.get_object()
        
        # Check permissions
        if not request.user.has_perm('suppliers.edit'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        ratings = request.data
        
        if 'overall_rating' in ratings:
            supplier.overall_rating = ratings['overall_rating']
        if 'quality_rating' in ratings:
            supplier.quality_rating = ratings['quality_rating']
        if 'delivery_rating' in ratings:
            supplier.delivery_rating = ratings['delivery_rating']
        if 'service_rating' in ratings:
            supplier.service_rating = ratings['service_rating']
        
        supplier.last_modified_by = request.user
        supplier.save()
        
        serializer = self.get_serializer(supplier)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change supplier status."""
        supplier = self.get_object()
        
        # Check permissions
        if not request.user.has_perm('suppliers.edit'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if new_status not in dict(SupplierProfile.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = supplier.status
        supplier.status = new_status
        supplier.last_modified_by = request.user
        supplier.save()
        
        # Log the status change
        SupplierCommunication.objects.create(
            supplier=supplier,
            communication_type='message',
            direction='outbound',
            subject=f'Status changed from {old_status} to {new_status}',
            content=f'Status changed by {request.user.get_full_name()}. Reason: {reason}',
            admin_user=request.user
        )
        
        serializer = self.get_serializer(supplier)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get supplier analytics data."""
        # Basic counts
        total_suppliers = self.queryset.count()
        active_suppliers = self.queryset.filter(status='active').count()
        preferred_suppliers = self.queryset.filter(is_preferred=True).count()
        high_risk_suppliers = self.queryset.filter(risk_level='high').count()
        
        # Purchase order metrics
        total_pos = PurchaseOrder.objects.count()
        total_spent = PurchaseOrder.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Performance metrics
        avg_delivery_time = self.queryset.aggregate(
            avg=Avg('average_delivery_time')
        )['avg'] or 0
        
        quality_avg = self.queryset.aggregate(
            avg=Avg('quality_rating')
        )['avg'] or 0
        
        # Top suppliers by volume
        top_by_volume = self.queryset.annotate(
            total_orders=Count('purchase_orders'),
            total_value=Sum('purchase_orders__total_amount')
        ).filter(total_orders__gt=0).order_by('-total_value')[:10]
        
        top_volume_data = [
            {
                'id': supplier.id,
                'name': supplier.name,
                'total_orders': supplier.total_orders,
                'total_value': float(supplier.total_value or 0)
            }
            for supplier in top_by_volume
        ]
        
        # Top suppliers by rating
        top_by_rating = self.queryset.filter(
            overall_rating__gt=0
        ).order_by('-overall_rating')[:10]
        
        top_rating_data = [
            {
                'id': supplier.id,
                'name': supplier.name,
                'overall_rating': float(supplier.overall_rating)
            }
            for supplier in top_by_rating
        ]
        
        # Risk distribution
        risk_distribution = dict(
            self.queryset.values('risk_level').annotate(
                count=Count('id')
            ).values_list('risk_level', 'count')
        )
        
        analytics_data = {
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'preferred_suppliers': preferred_suppliers,
            'high_risk_suppliers': high_risk_suppliers,
            'total_purchase_orders': total_pos,
            'total_spent': total_spent,
            'average_delivery_time': avg_delivery_time,
            'on_time_delivery_rate': 85.5,  # This would be calculated from actual data
            'quality_score_average': float(quality_avg),
            'top_suppliers_by_volume': top_volume_data,
            'top_suppliers_by_rating': top_rating_data,
            'risk_distribution': risk_distribution,
            'performance_trends': []  # This would include time-series data
        }
        
        serializer = SupplierAnalyticsSerializer(analytics_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get supplier dashboard data."""
        # Key metrics
        total_suppliers = self.queryset.count()
        active_pos = PurchaseOrder.objects.filter(
            status__in=['approved', 'sent', 'acknowledged', 'in_progress']
        ).count()
        pending_approvals = PurchaseOrder.objects.filter(
            status='pending_approval'
        ).count()
        
        # Overdue payments
        overdue_payments = SupplierPayment.objects.filter(
            status__in=['pending', 'approved'],
            due_date__lt=timezone.now().date()
        ).count()
        
        # Expiring contracts
        expiring_contracts = SupplierContract.objects.filter(
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=30)
        ).count()
        
        # Recent activities
        recent_orders = PurchaseOrder.objects.order_by('-created_at')[:5]
        recent_comms = SupplierCommunication.objects.order_by('-created_at')[:5]
        upcoming_audits = SupplierAudit.objects.filter(
            planned_date__gte=timezone.now().date()
        ).order_by('planned_date')[:5]
        
        # Alerts
        alerts = []
        
        # High risk suppliers
        high_risk_count = self.queryset.filter(risk_level='high').count()
        if high_risk_count > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{high_risk_count} suppliers are marked as high risk',
                'action_url': '/admin/suppliers?risk_level=high'
            })
        
        # Expiring contracts
        if expiring_contracts > 0:
            alerts.append({
                'type': 'info',
                'message': f'{expiring_contracts} contracts are expiring within 30 days',
                'action_url': '/admin/contracts?expiring=true'
            })
        
        dashboard_data = {
            'total_suppliers': total_suppliers,
            'active_purchase_orders': active_pos,
            'pending_approvals': pending_approvals,
            'overdue_payments': overdue_payments,
            'expiring_contracts': expiring_contracts,
            'recent_orders': PurchaseOrderListSerializer(recent_orders, many=True).data,
            'recent_communications': SupplierCommunicationSerializer(recent_comms, many=True).data,
            'upcoming_audits': SupplierAuditSerializer(upcoming_audits, many=True).data,
            'alerts': alerts,
            'performance_summary': {
                'average_rating': float(self.queryset.aggregate(avg=Avg('overall_rating'))['avg'] or 0),
                'on_time_delivery': 85.5,
                'quality_score': float(self.queryset.aggregate(avg=Avg('quality_rating'))['avg'] or 0)
            }
        }
        
        serializer = SupplierDashboardSerializer(dashboard_data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update suppliers."""
        if not request.user.has_perm('suppliers.edit'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        supplier_ids = request.data.get('supplier_ids', [])
        updates = request.data.get('updates', {})
        
        if not supplier_ids or not updates:
            return Response(
                {'error': 'supplier_ids and updates are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        suppliers = self.queryset.filter(id__in=supplier_ids)
        updated_count = suppliers.update(
            last_modified_by=request.user,
            updated_at=timezone.now(),
            **updates
        )
        
        return Response({
            'message': f'{updated_count} suppliers updated successfully',
            'updated_count': updated_count
        })


class SupplierContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier contacts."""
    queryset = SupplierContact.objects.select_related('supplier')
    serializer_class = SupplierContactSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['supplier', 'contact_type', 'is_active']
    search_fields = ['name', 'email', 'phone', 'title']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions


class SupplierDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier documents."""
    queryset = SupplierDocument.objects.select_related('supplier', 'reviewed_by', 'uploaded_by')
    serializer_class = SupplierDocumentSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['supplier', 'document_type', 'status', 'is_required', 'is_confidential']
    search_fields = ['title', 'description']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a document."""
        document = self.get_object()
        
        if not request.user.has_perm('suppliers.approve'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.status = 'approved'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.review_notes = request.data.get('notes', '')
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a document."""
        document = self.get_object()
        
        if not request.user.has_perm('suppliers.approve'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.status = 'rejected'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.review_notes = request.data.get('notes', '')
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing purchase orders."""
    queryset = PurchaseOrder.objects.select_related(
        'supplier', 'created_by', 'approved_by', 'supplier_contact'
    ).prefetch_related('items')
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['purchase_orders.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status', 'priority', 'created_by']
    search_fields = ['po_number', 'supplier__name']
    ordering_fields = ['po_number', 'order_date', 'required_date', 'total_amount', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update']:
            permissions[-1].required_permissions = ['purchase_orders.create', 'purchase_orders.edit']
        elif self.action == 'destroy':
            permissions[-1].required_permissions = ['purchase_orders.delete']
        elif self.action in ['approve', 'cancel']:
            permissions[-1].required_permissions = ['purchase_orders.approve']
        else:
            permissions[-1].required_permissions = ['purchase_orders.view']
        
        return permissions

    def perform_create(self, serializer):
        # Generate PO number
        last_po = PurchaseOrder.objects.order_by('-created_at').first()
        if last_po:
            last_number = int(last_po.po_number.split('-')[-1])
            po_number = f"PO-{last_number + 1:06d}"
        else:
            po_number = "PO-000001"
        
        serializer.save(
            created_by=self.request.user,
            po_number=po_number
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase order."""
        po = self.get_object()
        
        if po.status != 'pending_approval':
            return Response(
                {'error': 'Purchase order is not pending approval'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'approved'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_to_supplier(self, request, pk=None):
        """Send purchase order to supplier."""
        po = self.get_object()
        
        if po.status != 'approved':
            return Response(
                {'error': 'Purchase order must be approved first'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'sent'
        po.save()
        
        # Create communication record
        SupplierCommunication.objects.create(
            supplier=po.supplier,
            communication_type='email',
            direction='outbound',
            subject=f'Purchase Order {po.po_number}',
            content=f'Purchase order {po.po_number} has been sent to supplier.',
            admin_user=request.user,
            purchase_order=po
        )
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a purchase order."""
        po = self.get_object()
        
        if po.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled order'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'cancelled'
        po.save()
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def receive_items(self, request, pk=None):
        """Receive items for a purchase order."""
        po = self.get_object()
        received_items = request.data.get('items', [])
        
        for item_data in received_items:
            try:
                item = po.items.get(id=item_data['id'])
                quantity_received = Decimal(str(item_data['quantity_received']))
                
                item.quantity_received += quantity_received
                item.received_date = timezone.now().date()
                
                if item_data.get('quality_approved'):
                    item.quality_approved = True
                
                if item_data.get('inspection_notes'):
                    item.inspection_notes = item_data['inspection_notes']
                
                item.save()
                
            except PurchaseOrderItem.DoesNotExist:
                continue
        
        # Update PO status if all items received
        all_items_received = all(
            item.quantity_received >= item.quantity_ordered
            for item in po.items.all()
        )
        
        if all_items_received:
            po.status = 'completed'
            po.delivered_date = timezone.now().date()
        else:
            po.status = 'partially_received'
        
        po.save()
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)


class SupplierPerformanceMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier performance metrics."""
    queryset = SupplierPerformanceMetric.objects.select_related('supplier', 'measured_by', 'purchase_order')
    serializer_class = SupplierPerformanceMetricSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['supplier', 'metric_type', 'measurement_period']
    ordering_fields = ['measurement_date', 'value']
    ordering = ['-measurement_date']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        serializer.save(measured_by=self.request.user)


class SupplierCommunicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier communications."""
    queryset = SupplierCommunication.objects.select_related(
        'supplier', 'admin_user', 'supplier_contact', 'purchase_order'
    )
    serializer_class = SupplierCommunicationSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'communication_type', 'direction', 'is_important', 'requires_follow_up']
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'follow_up_date']
    ordering = ['-created_at']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        serializer.save(admin_user=self.request.user)


class SupplierContractViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier contracts."""
    queryset = SupplierContract.objects.select_related('supplier', 'created_by', 'approved_by')
    serializer_class = SupplierContractSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'contract_type', 'status', 'auto_renewal']
    search_fields = ['contract_number', 'title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update']:
            permissions[-1].required_permissions = ['suppliers.edit']
        elif self.action == 'destroy':
            permissions[-1].required_permissions = ['suppliers.delete']
        elif self.action == 'approve':
            permissions[-1].required_permissions = ['suppliers.approve']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        # Generate contract number
        last_contract = SupplierContract.objects.order_by('-created_at').first()
        if last_contract:
            last_number = int(last_contract.contract_number.split('-')[-1])
            contract_number = f"SC-{last_number + 1:06d}"
        else:
            contract_number = "SC-000001"
        
        serializer.save(
            created_by=self.request.user,
            contract_number=contract_number
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a contract."""
        contract = self.get_object()
        
        contract.status = 'approved'
        contract.approved_by = request.user
        contract.approved_at = timezone.now()
        contract.save()
        
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """Get contracts expiring soon."""
        days = int(request.query_params.get('days', 30))
        expiring_contracts = self.queryset.filter(
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=days)
        ).order_by('end_date')
        
        serializer = self.get_serializer(expiring_contracts, many=True)
        return Response(serializer.data)


class SupplierAuditViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier audits."""
    queryset = SupplierAudit.objects.select_related('supplier', 'lead_auditor').prefetch_related('audit_team')
    serializer_class = SupplierAuditSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'audit_type', 'status', 'lead_auditor']
    search_fields = ['audit_number', 'title', 'description']
    ordering_fields = ['planned_date', 'actual_date', 'overall_score']
    ordering = ['-planned_date']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        # Generate audit number
        last_audit = SupplierAudit.objects.order_by('-created_at').first()
        if last_audit:
            last_number = int(last_audit.audit_number.split('-')[-1])
            audit_number = f"SA-{last_number + 1:06d}"
        else:
            audit_number = "SA-000001"
        
        serializer.save(audit_number=audit_number)


class SupplierRiskAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier risk assessments."""
    queryset = SupplierRiskAssessment.objects.select_related('supplier', 'assessed_by', 'reviewed_by')
    serializer_class = SupplierRiskAssessmentSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['supplier', 'overall_risk_level', 'assessment_period']
    ordering_fields = ['assessment_date', 'overall_risk_score']
    ordering = ['-assessment_date']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permissions[-1].required_permissions = ['suppliers.edit']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        serializer.save(assessed_by=self.request.user)


class SupplierQualificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier qualifications."""
    queryset = SupplierQualification.objects.select_related('supplier', 'assessor', 'approver')
    serializer_class = SupplierQualificationSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'qualification_type', 'status', 'assessor']
    search_fields = ['qualification_number']
    ordering_fields = ['start_date', 'completion_date', 'overall_score']
    ordering = ['-start_date']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update']:
            permissions[-1].required_permissions = ['suppliers.edit']
        elif self.action == 'destroy':
            permissions[-1].required_permissions = ['suppliers.delete']
        elif self.action == 'approve':
            permissions[-1].required_permissions = ['suppliers.approve']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        # Generate qualification number
        last_qual = SupplierQualification.objects.order_by('-created_at').first()
        if last_qual:
            last_number = int(last_qual.qualification_number.split('-')[-1])
            qual_number = f"SQ-{last_number + 1:06d}"
        else:
            qual_number = "SQ-000001"
        
        serializer.save(
            qualification_number=qual_number,
            assessor=self.request.user
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a qualification."""
        qualification = self.get_object()
        
        qualification.status = 'qualified'
        qualification.approver = request.user
        qualification.approved_at = timezone.now()
        qualification.completion_date = timezone.now().date()
        qualification.save()
        
        serializer = self.get_serializer(qualification)
        return Response(serializer.data)


class SupplierPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing supplier payments."""
    queryset = SupplierPayment.objects.select_related('supplier', 'purchase_order', 'approved_by', 'processed_by')
    serializer_class = SupplierPaymentSerializer
    permission_classes = [IsAuthenticated, AdminPermissionRequired]
    required_permissions = ['suppliers.view']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status', 'payment_method', 'approved_by']
    search_fields = ['payment_number', 'invoice_number']
    ordering_fields = ['due_date', 'payment_date', 'invoice_amount']
    ordering = ['-created_at']

    def get_permissions(self):
        """Set permissions based on action."""
        permissions = [IsAuthenticated(), AdminPermissionRequired()]
        
        if self.action in ['create', 'update', 'partial_update']:
            permissions[-1].required_permissions = ['suppliers.edit']
        elif self.action == 'destroy':
            permissions[-1].required_permissions = ['suppliers.delete']
        elif self.action in ['approve', 'process_payment']:
            permissions[-1].required_permissions = ['suppliers.approve']
        else:
            permissions[-1].required_permissions = ['suppliers.view']
        
        return permissions

    def perform_create(self, serializer):
        # Generate payment number
        last_payment = SupplierPayment.objects.order_by('-created_at').first()
        if last_payment:
            last_number = int(last_payment.payment_number.split('-')[-1])
            payment_number = f"SP-{last_number + 1:06d}"
        else:
            payment_number = "SP-000001"
        
        serializer.save(payment_number=payment_number)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a payment."""
        payment = self.get_object()
        
        payment.status = 'approved'
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process a payment."""
        payment = self.get_object()
        
        if payment.status != 'approved':
            return Response(
                {'error': 'Payment must be approved first'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'paid'
        payment.processed_by = request.user
        payment.payment_date = timezone.now().date()
        payment.payment_method = request.data.get('payment_method', payment.payment_method)
        payment.payment_reference = request.data.get('payment_reference', '')
        payment.paid_amount = payment.net_amount
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue payments."""
        overdue_payments = self.queryset.filter(
            status__in=['pending', 'approved'],
            due_date__lt=timezone.now().date()
        ).order_by('due_date')
        
        serializer = self.get_serializer(overdue_payments, many=True)
        return Response(serializer.data)