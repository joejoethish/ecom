from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json


class SalesMetrics(models.Model):
    """Daily sales metrics aggregation"""
    date = models.DateField()
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    total_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_margin = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['date']
        ordering = ['-date']


class ProductSalesAnalytics(models.Model):
    """Product-level sales analytics"""
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=200)
    category_id = models.IntegerField(null=True, blank=True)
    category_name = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField()
    units_sold = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product_id', 'date']
        ordering = ['-date', '-revenue']


class CustomerAnalytics(models.Model):
    """Customer analytics and cohort data"""
    customer_id = models.IntegerField()
    customer_email = models.EmailField()
    acquisition_date = models.DateField()
    acquisition_channel = models.CharField(max_length=50, null=True, blank=True)
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_order_date = models.DateField(null=True, blank=True)
    days_since_last_order = models.IntegerField(default=0)
    churn_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    customer_segment = models.CharField(max_length=50, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['customer_id']


class SalesForecast(models.Model):
    """Sales forecasting data"""
    forecast_date = models.DateField()
    forecast_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ])
    predicted_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    predicted_orders = models.IntegerField()
    confidence_interval_lower = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_interval_upper = models.DecimalField(max_digits=12, decimal_places=2)
    model_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    seasonal_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    trend_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['forecast_date', 'forecast_type']
        ordering = ['forecast_date']


class SalesGoal(models.Model):
    """Sales goals and targets"""
    name = models.CharField(max_length=100)
    goal_type = models.CharField(max_length=20, choices=[
        ('revenue', 'Revenue'),
        ('orders', 'Orders'),
        ('customers', 'New Customers'),
        ('margin', 'Gross Margin')
    ])
    target_value = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=50, null=True, blank=True)
    region = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        if self.target_value > 0:
            return min((self.current_value / self.target_value) * 100, 100)
        return 0

    @property
    def is_achieved(self):
        return self.current_value >= self.target_value


class SalesCommission(models.Model):
    """Sales commission tracking"""
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_commissions')
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['sales_rep', 'period_start', 'period_end']


class SalesTerritory(models.Model):
    """Sales territory management"""
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    state_province = models.CharField(max_length=50, null=True, blank=True)
    cities = models.JSONField(default=list)
    postal_codes = models.JSONField(default=list)
    assigned_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    target_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    customer_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def revenue_achievement(self):
        if self.target_revenue > 0:
            return (self.current_revenue / self.target_revenue) * 100
        return 0


class SalesPipeline(models.Model):
    """Sales pipeline and opportunity tracking"""
    opportunity_name = models.CharField(max_length=200)
    customer_id = models.IntegerField(null=True, blank=True)
    customer_name = models.CharField(max_length=200)
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stage = models.CharField(max_length=20, choices=[
        ('lead', 'Lead'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost')
    ])
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expected_close_date = models.DateField()
    actual_close_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def weighted_value(self):
        return self.estimated_value * (self.probability / 100)

    @property
    def is_overdue(self):
        return self.expected_close_date < timezone.now().date() and self.stage not in ['closed_won', 'closed_lost']


class SalesReport(models.Model):
    """Scheduled sales reports"""
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily Sales'),
        ('weekly', 'Weekly Summary'),
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('custom', 'Custom Report')
    ])
    recipients = models.JSONField(default=list)
    schedule = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ])
    filters = models.JSONField(default=dict)
    last_sent = models.DateTimeField(null=True, blank=True)
    next_send = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class SalesAnomalyDetection(models.Model):
    """Sales anomaly detection and alerts"""
    date = models.DateField()
    metric_type = models.CharField(max_length=20, choices=[
        ('revenue', 'Revenue'),
        ('orders', 'Orders'),
        ('conversion', 'Conversion Rate'),
        ('aov', 'Average Order Value')
    ])
    actual_value = models.DecimalField(max_digits=12, decimal_places=2)
    expected_value = models.DecimalField(max_digits=12, decimal_places=2)
    deviation_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    severity = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-severity']