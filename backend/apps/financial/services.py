from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from .models import (
    FinancialTransaction, AccountingPeriod, Budget, FinancialKPI, 
    CashFlowStatement, CostCenter, FinancialReport
)


class FinancialAnalyticsService:
    """Service for financial analytics and P&L calculations"""

    def __init__(self):
        self.current_period = self.get_current_accounting_period()

    def get_current_accounting_period(self) -> Optional[AccountingPeriod]:
        """Get the current accounting period"""
        today = timezone.now().date()
        return AccountingPeriod.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='open'
        ).first()

    def generate_profit_loss_statement(self, start_date: datetime, end_date: datetime, 
                                     cost_center_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive P&L statement"""
        
        # Base query filters
        filters = Q(transaction_date__gte=start_date, transaction_date__lte=end_date)
        if cost_center_id:
            filters &= Q(cost_center_id=cost_center_id)

        # Revenue calculations
        revenue_data = self._calculate_revenue(filters)
        
        # Cost of Goods Sold
        cogs_data = self._calculate_cogs(filters)
        
        # Operating Expenses
        operating_expenses = self._calculate_operating_expenses(filters)
        
        # Other Income/Expenses
        other_income = self._calculate_other_income(filters)
        other_expenses = self._calculate_other_expenses(filters)
        
        # Tax calculations
        tax_data = self._calculate_taxes(filters)

        # Calculate key metrics
        gross_profit = revenue_data['total'] - cogs_data['total']
        operating_income = gross_profit - operating_expenses['total']
        ebitda = operating_income + self._calculate_depreciation(filters)
        net_income_before_tax = operating_income + other_income['total'] - other_expenses['total']
        net_income = net_income_before_tax - tax_data['total']

        # Calculate margins
        gross_margin = (gross_profit / revenue_data['total'] * 100) if revenue_data['total'] > 0 else 0
        operating_margin = (operating_income / revenue_data['total'] * 100) if revenue_data['total'] > 0 else 0
        net_margin = (net_income / revenue_data['total'] * 100) if revenue_data['total'] > 0 else 0

        return {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'cost_center': cost_center_id
            },
            'revenue': revenue_data,
            'cost_of_goods_sold': cogs_data,
            'gross_profit': {
                'amount': float(gross_profit),
                'margin_percentage': float(gross_margin)
            },
            'operating_expenses': operating_expenses,
            'operating_income': {
                'amount': float(operating_income),
                'margin_percentage': float(operating_margin)
            },
            'ebitda': float(ebitda),
            'other_income': other_income,
            'other_expenses': other_expenses,
            'net_income_before_tax': float(net_income_before_tax),
            'taxes': tax_data,
            'net_income': {
                'amount': float(net_income),
                'margin_percentage': float(net_margin)
            },
            'key_metrics': {
                'gross_margin': float(gross_margin),
                'operating_margin': float(operating_margin),
                'net_margin': float(net_margin),
                'revenue_growth': self._calculate_revenue_growth(start_date, end_date),
                'expense_ratio': float((operating_expenses['total'] / revenue_data['total'] * 100)) if revenue_data['total'] > 0 else 0
            }
        }

    def _calculate_revenue(self, filters: Q) -> Dict[str, Any]:
        """Calculate revenue breakdown"""
        revenue_transactions = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='revenue')
        )
        
        total_revenue = revenue_transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Revenue by product/category breakdown
        revenue_breakdown = revenue_transactions.values('product_id').annotate(
            amount=Sum('amount')
        ).order_by('-amount')[:10]

        # Monthly revenue trend
        monthly_trend = revenue_transactions.annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            amount=Sum('amount')
        ).order_by('month')

        return {
            'total': float(total_revenue),
            'breakdown': list(revenue_breakdown),
            'monthly_trend': [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'amount': float(item['amount'])
                }
                for item in monthly_trend
            ]
        }

    def _calculate_cogs(self, filters: Q) -> Dict[str, Any]:
        """Calculate Cost of Goods Sold"""
        cogs_transactions = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='cost_of_goods')
        )
        
        total_cogs = cogs_transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # COGS by product breakdown
        cogs_breakdown = cogs_transactions.values('product_id').annotate(
            amount=Sum('amount')
        ).order_by('-amount')[:10]

        return {
            'total': float(total_cogs),
            'breakdown': list(cogs_breakdown)
        }

    def _calculate_operating_expenses(self, filters: Q) -> Dict[str, Any]:
        """Calculate operating expenses by category"""
        expense_transactions = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='operating_expense')
        )
        
        total_expenses = expense_transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Expenses by cost center
        expense_by_cost_center = expense_transactions.values(
            'cost_center__name'
        ).annotate(
            amount=Sum('amount')
        ).order_by('-amount')

        return {
            'total': float(total_expenses),
            'by_cost_center': list(expense_by_cost_center)
        }

    def _calculate_other_income(self, filters: Q) -> Dict[str, Any]:
        """Calculate other income"""
        other_income = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='other_income')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {'total': float(other_income)}

    def _calculate_other_expenses(self, filters: Q) -> Dict[str, Any]:
        """Calculate other expenses"""
        other_expenses = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='other_expense')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {'total': float(other_expenses)}

    def _calculate_taxes(self, filters: Q) -> Dict[str, Any]:
        """Calculate tax expenses"""
        tax_expenses = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='tax')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {'total': float(tax_expenses)}

    def _calculate_depreciation(self, filters: Q) -> Decimal:
        """Calculate depreciation expenses"""
        depreciation = FinancialTransaction.objects.filter(
            filters & Q(transaction_type='depreciation')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return depreciation

    def _calculate_revenue_growth(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate revenue growth compared to previous period"""
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date - timedelta(days=1)

        current_revenue = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type='revenue'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        previous_revenue = FinancialTransaction.objects.filter(
            transaction_date__gte=previous_start,
            transaction_date__lte=previous_end,
            transaction_type='revenue'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if previous_revenue > 0:
            growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
            return float(growth)
        return 0.0

    def generate_budget_variance_report(self, accounting_period_id: str) -> Dict[str, Any]:
        """Generate budget vs actual variance report"""
        try:
            period = AccountingPeriod.objects.get(id=accounting_period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValueError("Accounting period not found")

        budgets = Budget.objects.filter(accounting_period=period)
        
        variance_data = []
        total_budgeted = Decimal('0')
        total_actual = Decimal('0')
        total_variance = Decimal('0')

        for budget in budgets:
            # Update actual amounts from transactions
            actual_amount = FinancialTransaction.objects.filter(
                accounting_period=period,
                cost_center=budget.cost_center,
                transaction_type__in=['revenue', 'operating_expense']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            budget.actual_amount = actual_amount
            budget.calculate_variance()

            variance_data.append({
                'budget_name': budget.name,
                'budget_type': budget.budget_type,
                'cost_center': budget.cost_center.name if budget.cost_center else 'General',
                'budgeted_amount': float(budget.budgeted_amount),
                'actual_amount': float(budget.actual_amount),
                'variance_amount': float(budget.variance_amount),
                'variance_percentage': float(budget.variance_percentage),
                'status': 'over_budget' if budget.variance_amount > 0 else 'under_budget'
            })

            total_budgeted += budget.budgeted_amount
            total_actual += budget.actual_amount
            total_variance += budget.variance_amount

        return {
            'accounting_period': {
                'name': period.name,
                'start_date': period.start_date.strftime('%Y-%m-%d'),
                'end_date': period.end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_budgeted': float(total_budgeted),
                'total_actual': float(total_actual),
                'total_variance': float(total_variance),
                'variance_percentage': float((total_variance / total_budgeted * 100)) if total_budgeted > 0 else 0
            },
            'variance_details': variance_data
        }

    def calculate_financial_kpis(self, accounting_period_id: str) -> Dict[str, Any]:
        """Calculate key financial performance indicators"""
        try:
            period = AccountingPeriod.objects.get(id=accounting_period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValueError("Accounting period not found")

        # Get P&L data for the period
        pl_data = self.generate_profit_loss_statement(period.start_date, period.end_date)
        
        revenue = Decimal(str(pl_data['revenue']['total']))
        gross_profit = Decimal(str(pl_data['gross_profit']['amount']))
        operating_income = Decimal(str(pl_data['operating_income']['amount']))
        net_income = Decimal(str(pl_data['net_income']['amount']))

        # Calculate and store KPIs
        kpis = {}
        
        # Profitability ratios
        if revenue > 0:
            kpis['gross_margin'] = float((gross_profit / revenue) * 100)
            kpis['operating_margin'] = float((operating_income / revenue) * 100)
            kpis['net_margin'] = float((net_income / revenue) * 100)
        else:
            kpis['gross_margin'] = 0
            kpis['operating_margin'] = 0
            kpis['net_margin'] = 0

        # Store KPIs in database
        for kpi_type, value in kpis.items():
            FinancialKPI.objects.update_or_create(
                kpi_type=kpi_type,
                accounting_period=period,
                defaults={'value': Decimal(str(value))}
            )

        return {
            'accounting_period': period.name,
            'kpis': kpis,
            'calculated_at': timezone.now().isoformat()
        }

    def generate_cash_flow_statement(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate cash flow statement"""
        # This is a simplified version - in a real implementation,
        # you would need more detailed cash flow tracking
        
        operating_cash_flow = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type__in=['revenue', 'operating_expense']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        investing_cash_flow = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type='other_expense'  # Simplified - would need more categories
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        financing_cash_flow = Decimal('0')  # Would need financing transaction types

        net_cash_flow = operating_cash_flow - investing_cash_flow - financing_cash_flow

        return {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'operating_activities': {
                'net_cash_from_operations': float(operating_cash_flow)
            },
            'investing_activities': {
                'net_cash_from_investing': float(-investing_cash_flow)
            },
            'financing_activities': {
                'net_cash_from_financing': float(financing_cash_flow)
            },
            'net_cash_flow': float(net_cash_flow)
        }

    def get_cost_center_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze performance by cost center"""
        cost_centers = CostCenter.objects.filter(is_active=True)
        analysis_data = []

        for cost_center in cost_centers:
            transactions = FinancialTransaction.objects.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
                cost_center=cost_center
            )

            revenue = transactions.filter(
                transaction_type='revenue'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            expenses = transactions.filter(
                transaction_type__in=['operating_expense', 'cost_of_goods']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            profit = revenue - expenses
            margin = (profit / revenue * 100) if revenue > 0 else 0

            analysis_data.append({
                'cost_center_id': str(cost_center.id),
                'cost_center_name': cost_center.name,
                'cost_center_code': cost_center.code,
                'revenue': float(revenue),
                'expenses': float(expenses),
                'profit': float(profit),
                'margin_percentage': float(margin),
                'transaction_count': transactions.count()
            })

        # Sort by profit descending
        analysis_data.sort(key=lambda x: x['profit'], reverse=True)

        return {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'cost_center_analysis': analysis_data,
            'summary': {
                'total_cost_centers': len(analysis_data),
                'profitable_centers': len([cc for cc in analysis_data if cc['profit'] > 0]),
                'total_revenue': sum(cc['revenue'] for cc in analysis_data),
                'total_expenses': sum(cc['expenses'] for cc in analysis_data),
                'total_profit': sum(cc['profit'] for cc in analysis_data)
            }
        }

    def get_financial_trends(self, months: int = 12) -> Dict[str, Any]:
        """Get financial trends over specified months"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=months * 30)

        # Monthly revenue trend
        monthly_revenue = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type='revenue'
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            amount=Sum('amount')
        ).order_by('month')

        # Monthly expense trend
        monthly_expenses = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type__in=['operating_expense', 'cost_of_goods']
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            amount=Sum('amount')
        ).order_by('month')

        # Combine data
        trends = {}
        for item in monthly_revenue:
            month_key = item['month'].strftime('%Y-%m')
            trends[month_key] = {
                'month': month_key,
                'revenue': float(item['amount']),
                'expenses': 0,
                'profit': 0
            }

        for item in monthly_expenses:
            month_key = item['month'].strftime('%Y-%m')
            if month_key in trends:
                trends[month_key]['expenses'] = float(item['amount'])
            else:
                trends[month_key] = {
                    'month': month_key,
                    'revenue': 0,
                    'expenses': float(item['amount']),
                    'profit': 0
                }

        # Calculate profit for each month
        for month_data in trends.values():
            month_data['profit'] = month_data['revenue'] - month_data['expenses']

        return {
            'period_months': months,
            'trends': list(trends.values())
        }