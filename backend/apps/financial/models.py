from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from decimal import Decimal
import uuid


class CostCenter(models.Model):
    """Cost centers for expense allocation and tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_cost_centers'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountingPeriod(models.Model):
    """Accounting periods for financial reporting"""
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('locked', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    fiscal_year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_accounting_periods'
        ordering = ['-start_date']
        unique_together = ['period_type', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class FinancialTransaction(models.Model):
    """Core financial transactions for P&L tracking"""
    TRANSACTION_TYPES = [
        ('revenue', 'Revenue'),
        ('cost_of_goods', 'Cost of Goods Sold'),
        ('operating_expense', 'Operating Expense'),
        ('other_income', 'Other Income'),
        ('other_expense', 'Other Expense'),
        ('tax', 'Tax'),
        ('depreciation', 'Depreciation'),
        ('interest', 'Interest'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE)
    
    # Reference to related business objects
    order_id = models.CharField(max_length=100, blank=True)  # Link to order
    product_id = models.CharField(max_length=100, blank=True)  # Link to product
    customer_id = models.CharField(max_length=100, blank=True)  # Link to customer
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['accounting_period']),
            models.Index(fields=['cost_center']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.transaction_date})"


class Budget(models.Model):
    """Budget planning and tracking"""
    BUDGET_TYPES = [
        ('revenue', 'Revenue Budget'),
        ('expense', 'Expense Budget'),
        ('capital', 'Capital Budget'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES)
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)
    budgeted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_budgets'
        ordering = ['-accounting_period__start_date']

    def calculate_variance(self):
        """Calculate budget variance"""
        self.variance_amount = self.actual_amount - self.budgeted_amount
        if self.budgeted_amount != 0:
            self.variance_percentage = (self.variance_amount / self.budgeted_amount) * 100
        else:
            self.variance_percentage = 0
        self.save()

    def __str__(self):
        return f"{self.name} - {self.accounting_period}"


class FinancialKPI(models.Model):
    """Key Performance Indicators for financial tracking"""
    KPI_TYPES = [
        ('gross_margin', 'Gross Margin'),
        ('net_margin', 'Net Margin'),
        ('operating_margin', 'Operating Margin'),
        ('roa', 'Return on Assets'),
        ('roe', 'Return on Equity'),
        ('current_ratio', 'Current Ratio'),
        ('debt_ratio', 'Debt Ratio'),
        ('inventory_turnover', 'Inventory Turnover'),
        ('receivables_turnover', 'Receivables Turnover'),
        ('cash_conversion_cycle', 'Cash Conversion Cycle'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kpi_type = models.CharField(max_length=30, choices=KPI_TYPES)
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=15, decimal_places=4)
    target_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    previous_period_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    calculation_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'financial_kpis'
        ordering = ['-accounting_period__start_date', 'kpi_type']
        unique_together = ['kpi_type', 'accounting_period']

    def __str__(self):
        return f"{self.get_kpi_type_display()} - {self.accounting_period}"


class CashFlowStatement(models.Model):
    """Cash flow statement data"""
    CASH_FLOW_CATEGORIES = [
        ('operating', 'Operating Activities'),
        ('investing', 'Investing Activities'),
        ('financing', 'Financing Activities'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CASH_FLOW_CATEGORIES)
    line_item = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    order_sequence = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_cash_flow'
        ordering = ['accounting_period', 'category', 'order_sequence']

    def __str__(self):
        return f"{self.line_item} - {self.accounting_period}"


class FinancialReport(models.Model):
    """Generated financial reports metadata"""
    REPORT_TYPES = [
        ('profit_loss', 'Profit & Loss Statement'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow Statement'),
        ('budget_variance', 'Budget Variance Report'),
        ('kpi_dashboard', 'KPI Dashboard'),
        ('cost_center_analysis', 'Cost Center Analysis'),
        ('financial_ratios', 'Financial Ratios Report'),
    ]

    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    name = models.CharField(max_length=200)
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    file_path = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict)  # Report generation parameters
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'financial_reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} to {self.end_date}"