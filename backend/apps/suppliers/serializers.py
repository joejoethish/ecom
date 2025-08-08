from rest_framework import serializers
from .models import (
    SupplierCategory, Supplier, SupplierDocument, SupplierContact,
    SupplierPerformanceMetric, PurchaseOrder, PurchaseOrderItem,
    SupplierAudit, SupplierCommunication, SupplierContract
)


class SupplierCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierCategory
        fields = '__all__'


class SupplierDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDocument
        fields = '__all__'


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = '__all__'


class SupplierPerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPerformanceMetric
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    documents = SupplierDocumentSerializer(many=True, read_only=True)
    contacts = SupplierContactSerializer(many=True, read_only=True)
    performance_history = SupplierPerformanceMetricSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    # Calculated fields
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = '__all__'
    
    def get_total_orders(self, obj):
        return obj.purchase_orders.count()
    
    def get_total_spent(self, obj):
        return sum(po.total_amount for po in obj.purchase_orders.filter(status='completed'))
    
    def get_last_order_date(self, obj):
        last_order = obj.purchase_orders.order_by('-order_date').first()
        return last_order.order_date if last_order else None


class SupplierListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_orders = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'supplier_code', 'company_name', 'supplier_type', 'status',
            'category_name', 'performance_score', 'quality_score', 'delivery_score',
            'risk_level', 'total_orders', 'created_at'
        ]
    
    def get_total_orders(self, obj):
        return obj.purchase_orders.count()


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier_name', 'status', 'priority',
            'total_amount', 'order_date', 'required_date', 'items_count'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class SupplierAuditSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    auditor_name = serializers.CharField(source='auditor.get_full_name', read_only=True)
    
    class Meta:
        model = SupplierAudit
        fields = '__all__'


class SupplierCommunicationSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    internal_contact_name = serializers.CharField(source='internal_contact.get_full_name', read_only=True)
    supplier_contact_name = serializers.CharField(source='supplier_contact.name', read_only=True)
    
    class Meta:
        model = SupplierCommunication
        fields = '__all__'


class SupplierContractSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierContract
        fields = '__all__'
    
    def get_days_until_expiry(self, obj):
        from datetime import date
        if obj.end_date:
            delta = obj.end_date - date.today()
            return delta.days
        return None


# Analytics Serializers
class SupplierAnalyticsSerializer(serializers.Serializer):
    """Serializer for supplier analytics data"""
    total_suppliers = serializers.IntegerField()
    active_suppliers = serializers.IntegerField()
    pending_suppliers = serializers.IntegerField()
    high_risk_suppliers = serializers.IntegerField()
    
    # Performance metrics
    average_performance_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    average_quality_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    average_delivery_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Financial metrics
    total_purchase_orders = serializers.IntegerField()
    total_purchase_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Diversity metrics
    minority_owned_count = serializers.IntegerField()
    women_owned_count = serializers.IntegerField()
    veteran_owned_count = serializers.IntegerField()
    small_business_count = serializers.IntegerField()


class SupplierPerformanceReportSerializer(serializers.Serializer):
    """Serializer for supplier performance reports"""
    supplier_id = serializers.UUIDField()
    supplier_name = serializers.CharField()
    supplier_code = serializers.CharField()
    
    # Performance metrics
    performance_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    quality_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    delivery_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    reliability_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Order metrics
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Delivery metrics
    on_time_delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_delivery_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Quality metrics
    defect_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    return_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class SupplierRiskAssessmentSerializer(serializers.Serializer):
    """Serializer for supplier risk assessment"""
    supplier_id = serializers.UUIDField()
    supplier_name = serializers.CharField()
    risk_level = serializers.CharField()
    
    # Risk factors
    financial_stability_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    compliance_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    performance_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Risk indicators
    overdue_payments = serializers.IntegerField()
    quality_issues = serializers.IntegerField()
    delivery_delays = serializers.IntegerField()
    contract_violations = serializers.IntegerField()
    
    # Recommendations
    risk_mitigation_actions = serializers.ListField(child=serializers.CharField())
    next_audit_date = serializers.DateField()


class SupplierDiversityReportSerializer(serializers.Serializer):
    """Serializer for supplier diversity reporting"""
    total_suppliers = serializers.IntegerField()
    
    # Diversity breakdown
    minority_owned = serializers.IntegerField()
    women_owned = serializers.IntegerField()
    veteran_owned = serializers.IntegerField()
    small_business = serializers.IntegerField()
    
    # Spending breakdown
    total_spending = serializers.DecimalField(max_digits=15, decimal_places=2)
    minority_owned_spending = serializers.DecimalField(max_digits=15, decimal_places=2)
    women_owned_spending = serializers.DecimalField(max_digits=15, decimal_places=2)
    veteran_owned_spending = serializers.DecimalField(max_digits=15, decimal_places=2)
    small_business_spending = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Percentages
    minority_owned_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    women_owned_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    veteran_owned_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    small_business_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)