from django.db.models import Q, Avg, Sum, Count, F
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse

from .models import (
    SupplierCategory, Supplier, SupplierDocument, SupplierContact,
    SupplierPerformanceMetric, PurchaseOrder, PurchaseOrderItem,
    SupplierAudit, SupplierCommunication, SupplierContract
)
from .serializers import (
    SupplierCategorySerializer, SupplierSerializer, SupplierListSerializer,
    SupplierDocumentSerializer, SupplierContactSerializer,
    SupplierPerformanceMetricSerializer, PurchaseOrderSerializer,
    PurchaseOrderListSerializer, PurchaseOrderItemSerializer,
    SupplierAuditSerializer, SupplierCommunicationSerializer,
    SupplierContractSerializer, SupplierAnalyticsSerializer,
    SupplierPerformanceReportSerializer, SupplierRiskAssessmentSerializer,
    SupplierDiversityReportSerializer
)


class SupplierCategoryViewSet(viewsets.ModelViewSet):
    queryset = SupplierCategory.objects.all()
    serializer_class = SupplierCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.select_related('category').prefetch_related(
        'documents', 'contacts', 'performance_history'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'supplier_type', 'risk_level', 'category',
        'is_minority_owned', 'is_women_owned', 'is_veteran_owned',
        'is_small_business', 'esg_compliance'
    ]
    search_fields = [
        'supplier_code', 'company_name', 'legal_name',
        'primary_contact_name', 'primary_contact_email'
    ]
    ordering_fields = [
        'company_name', 'supplier_code', 'performance_score',
        'quality_score', 'delivery_score', 'created_at'
    ]
    ordering = ['company_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierSerializer
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get supplier analytics dashboard data"""
        suppliers = self.get_queryset()
        
        # Basic counts
        total_suppliers = suppliers.count()
        active_suppliers = suppliers.filter(status='active').count()
        pending_suppliers = suppliers.filter(status='pending').count()
        high_risk_suppliers = suppliers.filter(risk_level='high').count()
        
        # Performance metrics
        performance_avg = suppliers.aggregate(
            avg_performance=Avg('performance_score'),
            avg_quality=Avg('quality_score'),
            avg_delivery=Avg('delivery_score')
        )
        
        # Purchase order metrics
        po_metrics = PurchaseOrder.objects.aggregate(
            total_pos=Count('id'),
            total_value=Sum('total_amount'),
            avg_value=Avg('total_amount')
        )
        
        # Diversity metrics
        diversity_counts = suppliers.aggregate(
            minority_owned=Count('id', filter=Q(is_minority_owned=True)),
            women_owned=Count('id', filter=Q(is_women_owned=True)),
            veteran_owned=Count('id', filter=Q(is_veteran_owned=True)),
            small_business=Count('id', filter=Q(is_small_business=True))
        )
        
        analytics_data = {
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'pending_suppliers': pending_suppliers,
            'high_risk_suppliers': high_risk_suppliers,
            'average_performance_score': performance_avg['avg_performance'] or 0,
            'average_quality_score': performance_avg['avg_quality'] or 0,
            'average_delivery_score': performance_avg['avg_delivery'] or 0,
            'total_purchase_orders': po_metrics['total_pos'] or 0,
            'total_purchase_value': po_metrics['total_value'] or 0,
            'average_order_value': po_metrics['avg_value'] or 0,
            'minority_owned_count': diversity_counts['minority_owned'],
            'women_owned_count': diversity_counts['women_owned'],
            'veteran_owned_count': diversity_counts['veteran_owned'],
            'small_business_count': diversity_counts['small_business']
        }
        
        serializer = SupplierAnalyticsSerializer(analytics_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def performance_report(self, request):
        """Generate supplier performance report"""
        suppliers = self.get_queryset()
        
        report_data = []
        for supplier in suppliers:
            # Get recent performance metrics
            recent_metrics = supplier.performance_history.filter(
                metric_date__gte=timezone.now().date() - timedelta(days=90)
            ).aggregate(
                avg_on_time=Avg('on_time_delivery_rate'),
                avg_delivery_days=Avg('average_delivery_days'),
                avg_defect_rate=Avg('defect_rate'),
                avg_return_rate=Avg('return_rate')
            )
            
            # Get order statistics
            order_stats = supplier.purchase_orders.aggregate(
                total_orders=Count('id'),
                completed_orders=Count('id', filter=Q(status='completed')),
                cancelled_orders=Count('id', filter=Q(status='cancelled')),
                total_value=Sum('total_amount', filter=Q(status='completed'))
            )
            
            report_data.append({
                'supplier_id': supplier.id,
                'supplier_name': supplier.company_name,
                'supplier_code': supplier.supplier_code,
                'performance_score': supplier.performance_score,
                'quality_score': supplier.quality_score,
                'delivery_score': supplier.delivery_score,
                'reliability_score': supplier.reliability_score,
                'total_orders': order_stats['total_orders'] or 0,
                'completed_orders': order_stats['completed_orders'] or 0,
                'cancelled_orders': order_stats['cancelled_orders'] or 0,
                'total_value': order_stats['total_value'] or 0,
                'on_time_delivery_rate': recent_metrics['avg_on_time'] or 0,
                'average_delivery_days': recent_metrics['avg_delivery_days'] or 0,
                'defect_rate': recent_metrics['avg_defect_rate'] or 0,
                'return_rate': recent_metrics['avg_return_rate'] or 0
            })
        
        serializer = SupplierPerformanceReportSerializer(report_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def risk_assessment(self, request):
        """Generate supplier risk assessment report"""
        suppliers = self.get_queryset()
        
        risk_data = []
        for supplier in suppliers:
            # Calculate risk indicators
            overdue_payments = 0  # This would be calculated based on payment history
            quality_issues = supplier.performance_history.filter(
                defect_rate__gt=5.0
            ).count()
            delivery_delays = supplier.performance_history.filter(
                on_time_delivery_rate__lt=90.0
            ).count()
            contract_violations = 0  # This would be calculated based on contract compliance
            
            # Generate risk mitigation actions
            risk_actions = []
            if supplier.risk_level == 'high':
                risk_actions.append('Conduct immediate audit')
                risk_actions.append('Review contract terms')
            if supplier.performance_score < 3.0:
                risk_actions.append('Performance improvement plan required')
            if supplier.financial_stability_score < 3.0:
                risk_actions.append('Financial review recommended')
            
            risk_data.append({
                'supplier_id': supplier.id,
                'supplier_name': supplier.company_name,
                'risk_level': supplier.risk_level,
                'financial_stability_score': supplier.financial_stability_score,
                'compliance_score': supplier.compliance_score,
                'performance_score': supplier.performance_score,
                'overdue_payments': overdue_payments,
                'quality_issues': quality_issues,
                'delivery_delays': delivery_delays,
                'contract_violations': contract_violations,
                'risk_mitigation_actions': risk_actions,
                'next_audit_date': supplier.next_audit_date
            })
        
        serializer = SupplierRiskAssessmentSerializer(risk_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def diversity_report(self, request):
        """Generate supplier diversity report"""
        suppliers = self.get_queryset()
        
        # Basic counts
        total_suppliers = suppliers.count()
        diversity_counts = suppliers.aggregate(
            minority_owned=Count('id', filter=Q(is_minority_owned=True)),
            women_owned=Count('id', filter=Q(is_women_owned=True)),
            veteran_owned=Count('id', filter=Q(is_veteran_owned=True)),
            small_business=Count('id', filter=Q(is_small_business=True))
        )
        
        # Spending analysis
        total_spending = PurchaseOrder.objects.filter(
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        minority_spending = PurchaseOrder.objects.filter(
            status='completed',
            supplier__is_minority_owned=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        women_spending = PurchaseOrder.objects.filter(
            status='completed',
            supplier__is_women_owned=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        veteran_spending = PurchaseOrder.objects.filter(
            status='completed',
            supplier__is_veteran_owned=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        small_business_spending = PurchaseOrder.objects.filter(
            status='completed',
            supplier__is_small_business=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate percentages
        minority_percentage = (minority_spending / total_spending * 100) if total_spending > 0 else 0
        women_percentage = (women_spending / total_spending * 100) if total_spending > 0 else 0
        veteran_percentage = (veteran_spending / total_spending * 100) if total_spending > 0 else 0
        small_business_percentage = (small_business_spending / total_spending * 100) if total_spending > 0 else 0
        
        diversity_data = {
            'total_suppliers': total_suppliers,
            'minority_owned': diversity_counts['minority_owned'],
            'women_owned': diversity_counts['women_owned'],
            'veteran_owned': diversity_counts['veteran_owned'],
            'small_business': diversity_counts['small_business'],
            'total_spending': total_spending,
            'minority_owned_spending': minority_spending,
            'women_owned_spending': women_spending,
            'veteran_owned_spending': veteran_spending,
            'small_business_spending': small_business_spending,
            'minority_owned_percentage': round(minority_percentage, 2),
            'women_owned_percentage': round(women_percentage, 2),
            'veteran_owned_percentage': round(veteran_percentage, 2),
            'small_business_percentage': round(small_business_percentage, 2)
        }
        
        serializer = SupplierDiversityReportSerializer(diversity_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export suppliers to CSV"""
        suppliers = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Supplier Code', 'Company Name', 'Type', 'Status', 'Contact Name',
            'Contact Email', 'Phone', 'Performance Score', 'Quality Score',
            'Delivery Score', 'Risk Level', 'Created Date'
        ])
        
        for supplier in suppliers:
            writer.writerow([
                supplier.supplier_code,
                supplier.company_name,
                supplier.get_supplier_type_display(),
                supplier.get_status_display(),
                supplier.primary_contact_name,
                supplier.primary_contact_email,
                supplier.primary_contact_phone,
                supplier.performance_score,
                supplier.quality_score,
                supplier.delivery_score,
                supplier.get_risk_level_display(),
                supplier.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    
    @action(detail=True, methods=['post'])
    def update_performance(self, request, pk=None):
        """Update supplier performance metrics"""
        supplier = self.get_object()
        
        # Create new performance metric record
        metric_data = request.data
        metric_data['supplier'] = supplier.id
        metric_data['metric_date'] = timezone.now().date()
        
        serializer = SupplierPerformanceMetricSerializer(data=metric_data)
        if serializer.is_valid():
            serializer.save()
            
            # Update supplier's overall scores
            recent_metrics = supplier.performance_history.filter(
                metric_date__gte=timezone.now().date() - timedelta(days=90)
            )
            
            if recent_metrics.exists():
                avg_metrics = recent_metrics.aggregate(
                    avg_delivery=Avg('on_time_delivery_rate'),
                    avg_quality=Avg(100 - F('defect_rate')),  # Convert defect rate to quality score
                    avg_response=Avg('response_time_hours')
                )
                
                # Update supplier scores (simplified calculation)
                supplier.delivery_score = min(5.0, (avg_metrics['avg_delivery'] or 0) / 20)
                supplier.quality_score = min(5.0, (avg_metrics['avg_quality'] or 0) / 20)
                supplier.performance_score = (supplier.delivery_score + supplier.quality_score) / 2
                supplier.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierDocumentViewSet(viewsets.ModelViewSet):
    queryset = SupplierDocument.objects.select_related('supplier', 'verified_by')
    serializer_class = SupplierDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['supplier', 'document_type', 'is_verified']
    search_fields = ['title', 'supplier__company_name']
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a supplier document"""
        document = self.get_object()
        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class SupplierContactViewSet(viewsets.ModelViewSet):
    queryset = SupplierContact.objects.select_related('supplier')
    serializer_class = SupplierContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['supplier', 'contact_type', 'is_primary']
    search_fields = ['name', 'email', 'supplier__company_name']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related(
        'supplier', 'created_by', 'approved_by'
    ).prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status', 'priority', 'created_by']
    search_fields = ['po_number', 'supplier__company_name']
    ordering_fields = ['po_number', 'order_date', 'total_amount', 'required_date']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer
    
    def perform_create(self, serializer):
        # Generate PO number
        last_po = PurchaseOrder.objects.order_by('-created_at').first()
        if last_po:
            last_number = int(last_po.po_number.split('-')[-1])
            po_number = f"PO-{last_number + 1:06d}"
        else:
            po_number = "PO-000001"
        
        serializer.save(
            po_number=po_number,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase order"""
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
        """Send purchase order to supplier"""
        po = self.get_object()
        
        if po.status != 'approved':
            return Response(
                {'error': 'Purchase order must be approved first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'sent'
        po.save()
        
        # Here you would implement email sending logic
        # send_po_email(po)
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)


class SupplierAuditViewSet(viewsets.ModelViewSet):
    queryset = SupplierAudit.objects.select_related('supplier', 'auditor')
    serializer_class = SupplierAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'audit_type', 'status', 'auditor']
    search_fields = ['supplier__company_name', 'findings', 'recommendations']
    ordering_fields = ['scheduled_date', 'completed_date', 'overall_score']
    ordering = ['-scheduled_date']
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete an audit"""
        audit = self.get_object()
        
        audit.status = 'completed'
        audit.completed_date = timezone.now().date()
        audit.overall_score = request.data.get('overall_score')
        audit.findings = request.data.get('findings', '')
        audit.recommendations = request.data.get('recommendations', '')
        audit.corrective_actions = request.data.get('corrective_actions', '')
        audit.save()
        
        # Update supplier's last audit date
        audit.supplier.last_audit_date = audit.completed_date
        audit.supplier.save()
        
        serializer = self.get_serializer(audit)
        return Response(serializer.data)


class SupplierCommunicationViewSet(viewsets.ModelViewSet):
    queryset = SupplierCommunication.objects.select_related(
        'supplier', 'internal_contact', 'supplier_contact'
    )
    serializer_class = SupplierCommunicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'supplier', 'communication_type', 'internal_contact',
        'requires_follow_up', 'is_resolved'
    ]
    search_fields = ['subject', 'content', 'supplier__company_name']
    ordering_fields = ['created_at', 'follow_up_date']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(internal_contact=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark communication as resolved"""
        communication = self.get_object()
        communication.is_resolved = True
        communication.save()
        
        serializer = self.get_serializer(communication)
        return Response(serializer.data)


class SupplierContractViewSet(viewsets.ModelViewSet):
    queryset = SupplierContract.objects.select_related('supplier')
    serializer_class = SupplierContractSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'contract_type', 'status', 'auto_renewal']
    search_fields = ['contract_number', 'title', 'supplier__company_name']
    ordering_fields = ['start_date', 'end_date', 'contract_value']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get contracts expiring within 30 days"""
        expiry_date = timezone.now().date() + timedelta(days=30)
        expiring_contracts = self.get_queryset().filter(
            end_date__lte=expiry_date,
            status='active'
        )
        
        serializer = self.get_serializer(expiring_contracts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a contract"""
        contract = self.get_object()
        
        # Create new contract based on existing one
        new_contract_data = request.data
        new_contract_data['supplier'] = contract.supplier.id
        new_contract_data['status'] = 'draft'
        
        # Generate new contract number
        last_contract = SupplierContract.objects.order_by('-created_at').first()
        if last_contract:
            last_number = int(last_contract.contract_number.split('-')[-1])
            contract_number = f"CON-{last_number + 1:06d}"
        else:
            contract_number = "CON-000001"
        
        new_contract_data['contract_number'] = contract_number
        
        serializer = self.get_serializer(data=new_contract_data)
        if serializer.is_valid():
            new_contract = serializer.save()
            
            # Mark old contract as renewed
            contract.status = 'renewed'
            contract.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)