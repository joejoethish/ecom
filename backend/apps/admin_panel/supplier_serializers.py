"""
Serializers for Supplier and Vendor Management System
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, SupplierDocument,
    PurchaseOrder, PurchaseOrderItem, SupplierPerformanceMetric,
    SupplierCommunication, SupplierContract, SupplierAudit,
    SupplierRiskAssessment, SupplierQualification, SupplierPayment
)


class SupplierCategorySerializer(serializers.ModelSerializer):
    """Serializer for supplier categories."""
    children_count = serializers.SerializerMethodField()
    suppliers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierCategory
        fields = [
            'id', 'name', 'description', 'parent', 'is_active',
            'children_count', 'suppliers_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()
    
    def get_suppliers_count(self, obj):
        return obj.supplier_set.filter(status='active').count()


class SupplierContactSerializer(serializers.ModelSerializer):
    """Serializer for supplier contacts."""
    
    class Meta:
        model = SupplierContact
        fields = [
            'id', 'supplier', 'contact_type', 'name', 'title', 'email',
            'phone', 'mobile', 'department', 'is_active', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupplierDocumentSerializer(serializers.ModelSerializer):
    """Serializer for supplier documents."""
    file_url = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierDocument
        fields = [
            'id', 'supplier', 'document_type', 'title', 'description',
            'file', 'file_url', 'file_size', 'mime_type', 'status',
            'is_required', 'is_confidential', 'issue_date', 'expiry_date',
            'reviewed_by', 'reviewed_at', 'review_notes', 'uploaded_by',
            'version', 'is_expired', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'file_size', 'mime_type', 'is_expired']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_days_until_expiry(self, obj):
        if obj.expiry_date:
            days = (obj.expiry_date - timezone.now().date()).days
            return days if days >= 0 else 0
        return None


class SupplierSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for suppliers."""
    contacts = SupplierContactSerializer(many=True, read_only=True)
    documents = SupplierDocumentSerializer(many=True, read_only=True)
    total_orders = serializers.ReadOnlyField()
    total_spent = serializers.ReadOnlyField()
    average_delivery_time = serializers.ReadOnlyField()
    
    # Performance metrics
    recent_performance = serializers.SerializerMethodField()
    risk_status = serializers.SerializerMethodField()
    contract_status = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'supplier_code', 'name', 'legal_name', 'supplier_type', 'category',
            'primary_contact_name', 'primary_contact_email', 'primary_contact_phone',
            'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country',
            'tax_id', 'business_license', 'website', 'established_date', 'employee_count', 'annual_revenue',
            'status', 'risk_level', 'is_preferred', 'is_certified', 'is_minority_owned',
            'is_woman_owned', 'is_veteran_owned', 'overall_rating', 'quality_rating',
            'delivery_rating', 'service_rating', 'credit_limit', 'current_balance',
            'payment_terms_days', 'discount_percentage', 'lead_time_days', 'minimum_order_value',
            'capacity_rating', 'iso_certified', 'iso_certifications', 'compliance_status',
            'last_audit_date', 'next_audit_date', 'sustainability_rating', 'carbon_footprint_score',
            'social_responsibility_score', 'created_by', 'last_modified_by', 'notes', 'tags',
            'contacts', 'documents', 'total_orders', 'total_spent', 'average_delivery_time',
            'recent_performance', 'risk_status', 'contract_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'total_orders', 'total_spent', 'average_delivery_time'
        ]
    
    def get_recent_performance(self, obj):
        """Get recent performance metrics."""
        recent_metrics = obj.performance_metrics.filter(
            measurement_date__gte=timezone.now().date() - timezone.timedelta(days=90)
        ).order_by('-measurement_date')[:5]
        
        return [
            {
                'metric_type': metric.metric_type,
                'value': float(metric.value),
                'target_value': float(metric.target_value) if metric.target_value else None,
                'measurement_date': metric.measurement_date
            }
            for metric in recent_metrics
        ]
    
    def get_risk_status(self, obj):
        """Get latest risk assessment status."""
        latest_risk = obj.risk_assessments.order_by('-assessment_date').first()
        if latest_risk:
            return {
                'risk_level': latest_risk.overall_risk_level,
                'risk_score': float(latest_risk.overall_risk_score),
                'assessment_date': latest_risk.assessment_date
            }
        return None
    
    def get_contract_status(self, obj):
        """Get active contract information."""
        active_contracts = obj.contracts.filter(status='active').count()
        expiring_contracts = obj.contracts.filter(
            status='active',
            end_date__lte=timezone.now().date() + timezone.timedelta(days=30)
        ).count()
        
        return {
            'active_contracts': active_contracts,
            'expiring_contracts': expiring_contracts
        }


class SupplierListSerializer(serializers.ModelSerializer):
    """Simplified serializer for supplier lists."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_orders = serializers.ReadOnlyField()
    total_spent = serializers.ReadOnlyField()
    
    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'supplier_code', 'name', 'supplier_type', 'category_name',
            'primary_contact_email', 'primary_contact_phone', 'status', 'risk_level',
            'is_preferred', 'overall_rating', 'total_orders', 'total_spent',
            'created_at', 'updated_at'
        ]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for purchase order items."""
    quantity_pending = serializers.ReadOnlyField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'line_number', 'product_code', 'product_name',
            'description', 'specifications', 'quantity_ordered', 'quantity_received',
            'unit_price', 'total_price', 'expected_date', 'received_date',
            'quality_approved', 'inspection_notes', 'quantity_pending',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'quantity_pending']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders."""
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name', 'status', 'priority',
            'order_date', 'required_date', 'expected_delivery_date', 'delivered_date',
            'subtotal', 'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount',
            'delivery_address', 'shipping_method', 'tracking_number', 'payment_terms',
            'delivery_terms', 'warranty_terms', 'special_instructions', 'created_by',
            'created_by_name', 'approved_by', 'approved_by_name', 'approved_at',
            'supplier_contact', 'last_communication_date', 'notes', 'attachments',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for purchase order lists."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier_name', 'status', 'priority',
            'order_date', 'required_date', 'total_amount', 'items_count',
            'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class SupplierPerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for supplier performance metrics."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    measured_by_name = serializers.CharField(source='measured_by.get_full_name', read_only=True)
    variance_from_target = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierPerformanceMetric
        fields = [
            'id', 'supplier', 'supplier_name', 'metric_type', 'value', 'target_value',
            'measurement_date', 'measurement_period', 'purchase_order', 'notes',
            'measured_by', 'measured_by_name', 'variance_from_target',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_variance_from_target(self, obj):
        if obj.target_value:
            return float(obj.value - obj.target_value)
        return None


class SupplierCommunicationSerializer(serializers.ModelSerializer):
    """Serializer for supplier communications."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    admin_user_name = serializers.CharField(source='admin_user.get_full_name', read_only=True)
    supplier_contact_name = serializers.CharField(source='supplier_contact.name', read_only=True)
    
    class Meta:
        model = SupplierCommunication
        fields = [
            'id', 'supplier', 'supplier_name', 'communication_type', 'direction',
            'subject', 'content', 'admin_user', 'admin_user_name', 'supplier_contact',
            'supplier_contact_name', 'purchase_order', 'attachments', 'is_important',
            'requires_follow_up', 'follow_up_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupplierContractSerializer(serializers.ModelSerializer):
    """Serializer for supplier contracts."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    is_expiring_soon = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = SupplierContract
        fields = [
            'id', 'supplier', 'supplier_name', 'contract_type', 'contract_number',
            'title', 'description', 'start_date', 'end_date', 'auto_renewal',
            'renewal_period_months', 'notice_period_days', 'contract_value',
            'payment_terms', 'currency', 'status', 'compliance_status',
            'last_review_date', 'next_review_date', 'contract_file', 'signed_file',
            'created_by', 'created_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'terms_and_conditions', 'special_clauses', 'notes',
            'is_expiring_soon', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_expiring_soon', 'days_until_expiry']


class SupplierAuditSerializer(serializers.ModelSerializer):
    """Serializer for supplier audits."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    lead_auditor_name = serializers.CharField(source='lead_auditor.get_full_name', read_only=True)
    audit_team_names = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierAudit
        fields = [
            'id', 'supplier', 'supplier_name', 'audit_type', 'audit_number',
            'title', 'description', 'planned_date', 'actual_date', 'duration_hours',
            'status', 'overall_score', 'pass_fail_result', 'lead_auditor',
            'lead_auditor_name', 'audit_team', 'audit_team_names', 'supplier_participants',
            'audit_checklist', 'findings', 'recommendations', 'corrective_actions',
            'follow_up_required', 'follow_up_date', 'next_audit_date',
            'audit_report', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_audit_team_names(self, obj):
        return [user.get_full_name() for user in obj.audit_team.all()]


class SupplierRiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for supplier risk assessments."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    assessed_by_name = serializers.CharField(source='assessed_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    
    class Meta:
        model = SupplierRiskAssessment
        fields = [
            'id', 'supplier', 'supplier_name', 'assessment_date', 'assessment_period',
            'overall_risk_level', 'overall_risk_score', 'financial_risk_score',
            'operational_risk_score', 'compliance_risk_score', 'quality_risk_score',
            'delivery_risk_score', 'risk_factors', 'mitigation_strategies',
            'monitoring_requirements', 'credit_rating', 'financial_stability_score',
            'debt_to_equity_ratio', 'regulatory_compliance_status', 'certification_status',
            'assessed_by', 'assessed_by_name', 'reviewed_by', 'reviewed_by_name',
            'next_assessment_date', 'action_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupplierQualificationSerializer(serializers.ModelSerializer):
    """Serializer for supplier qualifications."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    assessor_name = serializers.CharField(source='assessor.get_full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SupplierQualification
        fields = [
            'id', 'supplier', 'supplier_name', 'qualification_type', 'qualification_number',
            'start_date', 'completion_date', 'expiry_date', 'status',
            'technical_capability_score', 'quality_system_score', 'financial_stability_score',
            'delivery_performance_score', 'overall_score', 'requirements_checklist',
            'required_documents', 'submitted_documents', 'assessor', 'assessor_name',
            'approver', 'approver_name', 'approved_at', 'assessment_notes',
            'conditions', 'recommendations', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_expired']


class SupplierPaymentSerializer(serializers.ModelSerializer):
    """Serializer for supplier payments."""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = SupplierPayment
        fields = [
            'id', 'supplier', 'supplier_name', 'purchase_order', 'payment_number',
            'invoice_number', 'invoice_date', 'invoice_amount', 'discount_amount',
            'tax_amount', 'net_amount', 'paid_amount', 'payment_terms', 'due_date',
            'payment_date', 'payment_method', 'payment_reference', 'status',
            'approved_by', 'approved_by_name', 'approved_at', 'processed_by',
            'processed_by_name', 'invoice_file', 'payment_receipt', 'notes',
            'currency', 'is_overdue', 'days_overdue', 'outstanding_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_overdue', 'days_overdue', 'outstanding_amount']


# Analytics and Dashboard Serializers

class SupplierAnalyticsSerializer(serializers.Serializer):
    """Serializer for supplier analytics data."""
    total_suppliers = serializers.IntegerField()
    active_suppliers = serializers.IntegerField()
    preferred_suppliers = serializers.IntegerField()
    high_risk_suppliers = serializers.IntegerField()
    total_purchase_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_delivery_time = serializers.FloatField()
    on_time_delivery_rate = serializers.FloatField()
    quality_score_average = serializers.FloatField()
    
    # Top performers
    top_suppliers_by_volume = serializers.ListField()
    top_suppliers_by_rating = serializers.ListField()
    
    # Risk distribution
    risk_distribution = serializers.DictField()
    
    # Performance trends
    performance_trends = serializers.ListField()


class SupplierDashboardSerializer(serializers.Serializer):
    """Serializer for supplier dashboard data."""
    # Key metrics
    total_suppliers = serializers.IntegerField()
    active_purchase_orders = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    overdue_payments = serializers.IntegerField()
    expiring_contracts = serializers.IntegerField()
    
    # Recent activities
    recent_orders = PurchaseOrderListSerializer(many=True)
    recent_communications = SupplierCommunicationSerializer(many=True)
    upcoming_audits = SupplierAuditSerializer(many=True)
    
    # Alerts and notifications
    alerts = serializers.ListField()
    
    # Performance summary
    performance_summary = serializers.DictField()


class SupplierReportSerializer(serializers.Serializer):
    """Serializer for supplier reports."""
    report_type = serializers.CharField()
    generated_at = serializers.DateTimeField()
    parameters = serializers.DictField()
    data = serializers.DictField()
    summary = serializers.DictField()