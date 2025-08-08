from rest_framework import serializers
from .models import (
    CostCenter, AccountingPeriod, FinancialTransaction, 
    Budget, FinancialKPI, CashFlowStatement, FinancialReport
)


class CostCenterSerializer(serializers.ModelSerializer):
    """Serializer for cost centers"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = CostCenter
        fields = [
            'id', 'name', 'code', 'description', 'parent', 'parent_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AccountingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for accounting periods"""
    
    class Meta:
        model = AccountingPeriod
        fields = [
            'id', 'name', 'period_type', 'start_date', 'end_date', 
            'status', 'fiscal_year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate that end_date is after start_date"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class FinancialTransactionSerializer(serializers.ModelSerializer):
    """Serializer for financial transactions"""
    cost_center_name = serializers.CharField(source='cost_center.name', read_only=True)
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id', 'transaction_date', 'transaction_type', 'amount', 'description',
            'reference_number', 'cost_center', 'cost_center_name', 
            'accounting_period', 'accounting_period_name', 'order_id', 
            'product_id', 'customer_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for budgets"""
    cost_center_name = serializers.CharField(source='cost_center.name', read_only=True)
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'budget_type', 'accounting_period', 'accounting_period_name',
            'cost_center', 'cost_center_name', 'budgeted_amount', 'actual_amount',
            'variance_amount', 'variance_percentage', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'actual_amount', 'variance_amount', 'variance_percentage',
            'created_at', 'updated_at'
        ]


class FinancialKPISerializer(serializers.ModelSerializer):
    """Serializer for financial KPIs"""
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    kpi_type_display = serializers.CharField(source='get_kpi_type_display', read_only=True)
    
    class Meta:
        model = FinancialKPI
        fields = [
            'id', 'kpi_type', 'kpi_type_display', 'accounting_period', 
            'accounting_period_name', 'value', 'target_value', 'previous_period_value',
            'calculation_date', 'notes'
        ]
        read_only_fields = ['id', 'calculation_date']


class CashFlowStatementSerializer(serializers.ModelSerializer):
    """Serializer for cash flow statements"""
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = CashFlowStatement
        fields = [
            'id', 'accounting_period', 'accounting_period_name', 'category',
            'category_display', 'line_item', 'amount', 'order_sequence',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FinancialReportSerializer(serializers.ModelSerializer):
    """Serializer for financial reports"""
    accounting_period_name = serializers.CharField(source='accounting_period.name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = FinancialReport
        fields = [
            'id', 'report_type', 'report_type_display', 'name', 'accounting_period',
            'accounting_period_name', 'start_date', 'end_date', 'status',
            'file_path', 'parameters', 'generated_by', 'generated_by_username',
            'generated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'generated_by', 'generated_at', 'completed_at'
        ]


# Custom serializers for analytics responses
class ProfitLossStatementSerializer(serializers.Serializer):
    """Serializer for P&L statement response"""
    period = serializers.DictField()
    revenue = serializers.DictField()
    cost_of_goods_sold = serializers.DictField()
    gross_profit = serializers.DictField()
    operating_expenses = serializers.DictField()
    operating_income = serializers.DictField()
    ebitda = serializers.DecimalField(max_digits=15, decimal_places=2)
    other_income = serializers.DictField()
    other_expenses = serializers.DictField()
    net_income_before_tax = serializers.DecimalField(max_digits=15, decimal_places=2)
    taxes = serializers.DictField()
    net_income = serializers.DictField()
    key_metrics = serializers.DictField()


class BudgetVarianceReportSerializer(serializers.Serializer):
    """Serializer for budget variance report response"""
    accounting_period = serializers.DictField()
    summary = serializers.DictField()
    variance_details = serializers.ListField()


class FinancialKPIDashboardSerializer(serializers.Serializer):
    """Serializer for KPI dashboard response"""
    accounting_period = serializers.CharField()
    kpis = serializers.DictField()
    calculated_at = serializers.DateTimeField()


class CashFlowStatementResponseSerializer(serializers.Serializer):
    """Serializer for cash flow statement response"""
    period = serializers.DictField()
    operating_activities = serializers.DictField()
    investing_activities = serializers.DictField()
    financing_activities = serializers.DictField()
    net_cash_flow = serializers.DecimalField(max_digits=15, decimal_places=2)


class CostCenterAnalysisSerializer(serializers.Serializer):
    """Serializer for cost center analysis response"""
    period = serializers.DictField()
    cost_center_analysis = serializers.ListField()
    summary = serializers.DictField()


class FinancialTrendsSerializer(serializers.Serializer):
    """Serializer for financial trends response"""
    period_months = serializers.IntegerField()
    trends = serializers.ListField()


# Request serializers for API endpoints
class ProfitLossRequestSerializer(serializers.Serializer):
    """Serializer for P&L statement request parameters"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    cost_center_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class BudgetVarianceRequestSerializer(serializers.Serializer):
    """Serializer for budget variance request parameters"""
    accounting_period_id = serializers.UUIDField()


class CashFlowRequestSerializer(serializers.Serializer):
    """Serializer for cash flow statement request parameters"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class CostCenterAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for cost center analysis request parameters"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class FinancialTrendsRequestSerializer(serializers.Serializer):
    """Serializer for financial trends request parameters"""
    months = serializers.IntegerField(min_value=1, max_value=60, default=12)


class ReportGenerationRequestSerializer(serializers.Serializer):
    """Serializer for report generation request"""
    report_type = serializers.ChoiceField(choices=FinancialReport.REPORT_TYPES)
    name = serializers.CharField(max_length=200)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    accounting_period_id = serializers.UUIDField(required=False, allow_null=True)
    parameters = serializers.JSONField(default=dict)

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data