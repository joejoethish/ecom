from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import json


class InventoryAnalytics(models.Model):
    """
    Model for storing inventory analytics data and KPIs.
    """
    ANALYSIS_TYPES = [
        ('ABC', _('ABC Analysis')),
        ('TURNOVER', _('Turnover Analysis')),
        ('SEASONAL', _('Seasonal Analysis')),
        ('DEMAND_FORECAST', _('Demand Forecasting')),
        ('SHRINKAGE', _('Shrinkage Analysis')),
        ('CARRYING_COST', _('Carrying Cost Analysis')),
        ('REORDER_OPTIMIZATION', _('Reorder Point Optimization')),
        ('SUPPLIER_PERFORMANCE', _('Supplier Performance')),
        ('QUALITY_METRICS', _('Quality Metrics')),
        ('OBSOLESCENCE', _('Obsolescence Analysis')),
    ]
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name=_('Product')
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name=_('Warehouse')
    )
    analysis_type = models.CharField(_('Analysis Type'), max_length=20, choices=ANALYSIS_TYPES)
    analysis_date = models.DateField(_('Analysis Date'))
    
    # ABC Analysis fields
    abc_category = models.CharField(_('ABC Category'), max_length=1, blank=True, null=True)
    revenue_contribution = models.DecimalField(
        _('Revenue Contribution %'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Turnover Analysis fields
    turnover_ratio = models.DecimalField(
        _('Turnover Ratio'), 
        max_digits=10, 
        decimal_places=4, 
        blank=True, 
        null=True
    )
    days_of_supply = models.IntegerField(_('Days of Supply'), blank=True, null=True)
    
    # Demand Forecasting fields
    forecasted_demand = models.IntegerField(_('Forecasted Demand'), blank=True, null=True)
    forecast_accuracy = models.DecimalField(
        _('Forecast Accuracy %'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Shrinkage Analysis fields
    shrinkage_quantity = models.IntegerField(_('Shrinkage Quantity'), blank=True, null=True)
    shrinkage_value = models.DecimalField(
        _('Shrinkage Value'), 
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    shrinkage_percentage = models.DecimalField(
        _('Shrinkage Percentage'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Carrying Cost Analysis fields
    carrying_cost = models.DecimalField(
        _('Carrying Cost'), 
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    carrying_cost_percentage = models.DecimalField(
        _('Carrying Cost %'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Reorder Optimization fields
    optimal_reorder_point = models.IntegerField(_('Optimal Reorder Point'), blank=True, null=True)
    optimal_order_quantity = models.IntegerField(_('Optimal Order Quantity'), blank=True, null=True)
    service_level = models.DecimalField(
        _('Service Level %'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Quality Metrics fields
    defect_rate = models.DecimalField(
        _('Defect Rate %'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    quality_score = models.DecimalField(
        _('Quality Score'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Obsolescence Analysis fields
    obsolescence_risk = models.CharField(
        _('Obsolescence Risk'), 
        max_length=10, 
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        blank=True, 
        null=True
    )
    days_since_last_sale = models.IntegerField(_('Days Since Last Sale'), blank=True, null=True)
    
    # Additional metrics stored as JSON
    additional_metrics = models.JSONField(_('Additional Metrics'), default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Inventory Analytics')
        verbose_name_plural = _('Inventory Analytics')
        unique_together = ['product', 'warehouse', 'analysis_type', 'analysis_date']
        indexes = [
            models.Index(fields=['analysis_type', 'analysis_date']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['abc_category']),
            models.Index(fields=['turnover_ratio']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.get_analysis_type_display()} ({self.analysis_date})"


class InventoryKPI(models.Model):
    """
    Model for storing inventory KPIs and performance metrics.
    """
    KPI_TYPES = [
        ('STOCK_TURNOVER', _('Stock Turnover')),
        ('FILL_RATE', _('Fill Rate')),
        ('STOCKOUT_RATE', _('Stockout Rate')),
        ('INVENTORY_ACCURACY', _('Inventory Accuracy')),
        ('CARRYING_COST_RATIO', _('Carrying Cost Ratio')),
        ('GROSS_MARGIN_RETURN', _('Gross Margin Return on Investment')),
        ('DEAD_STOCK_RATIO', _('Dead Stock Ratio')),
        ('BACKORDER_RATE', _('Backorder Rate')),
        ('SUPPLIER_LEAD_TIME', _('Supplier Lead Time')),
        ('INVENTORY_VELOCITY', _('Inventory Velocity')),
    ]
    
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='kpis',
        verbose_name=_('Warehouse'),
        null=True,
        blank=True
    )
    kpi_type = models.CharField(_('KPI Type'), max_length=30, choices=KPI_TYPES)
    measurement_date = models.DateField(_('Measurement Date'))
    
    # KPI Values
    value = models.DecimalField(_('Value'), max_digits=15, decimal_places=4)
    target_value = models.DecimalField(
        _('Target Value'), 
        max_digits=15, 
        decimal_places=4, 
        blank=True, 
        null=True
    )
    
    # Performance indicators
    performance_status = models.CharField(
        _('Performance Status'),
        max_length=10,
        choices=[
            ('EXCELLENT', _('Excellent')),
            ('GOOD', _('Good')),
            ('AVERAGE', _('Average')),
            ('POOR', _('Poor')),
            ('CRITICAL', _('Critical')),
        ],
        blank=True,
        null=True
    )
    
    # Trend analysis
    previous_value = models.DecimalField(
        _('Previous Value'), 
        max_digits=15, 
        decimal_places=4, 
        blank=True, 
        null=True
    )
    trend_direction = models.CharField(
        _('Trend Direction'),
        max_length=10,
        choices=[
            ('UP', _('Improving')),
            ('DOWN', _('Declining')),
            ('STABLE', _('Stable')),
        ],
        blank=True,
        null=True
    )
    
    # Additional context
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Inventory KPI')
        verbose_name_plural = _('Inventory KPIs')
        unique_together = ['warehouse', 'kpi_type', 'measurement_date']
        indexes = [
            models.Index(fields=['kpi_type', 'measurement_date']),
            models.Index(fields=['warehouse', 'measurement_date']),
        ]
    
    def __str__(self):
        warehouse_name = self.warehouse.name if self.warehouse else "All Warehouses"
        return f"{warehouse_name} - {self.get_kpi_type_display()} ({self.measurement_date})"


class InventoryForecast(models.Model):
    """
    Model for storing inventory demand forecasts.
    """
    FORECAST_METHODS = [
        ('MOVING_AVERAGE', _('Moving Average')),
        ('EXPONENTIAL_SMOOTHING', _('Exponential Smoothing')),
        ('LINEAR_REGRESSION', _('Linear Regression')),
        ('SEASONAL_DECOMPOSITION', _('Seasonal Decomposition')),
        ('ARIMA', _('ARIMA')),
        ('MACHINE_LEARNING', _('Machine Learning')),
    ]
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='forecasts',
        verbose_name=_('Product')
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='forecasts',
        verbose_name=_('Warehouse')
    )
    
    # Forecast details
    forecast_date = models.DateField(_('Forecast Date'))
    forecast_period_start = models.DateField(_('Forecast Period Start'))
    forecast_period_end = models.DateField(_('Forecast Period End'))
    forecast_method = models.CharField(_('Forecast Method'), max_length=30, choices=FORECAST_METHODS)
    
    # Forecast values
    forecasted_demand = models.IntegerField(_('Forecasted Demand'))
    confidence_interval_lower = models.IntegerField(_('Confidence Interval Lower'), blank=True, null=True)
    confidence_interval_upper = models.IntegerField(_('Confidence Interval Upper'), blank=True, null=True)
    confidence_level = models.DecimalField(
        _('Confidence Level %'), 
        max_digits=5, 
        decimal_places=2, 
        default=95.00
    )
    
    # Accuracy tracking
    actual_demand = models.IntegerField(_('Actual Demand'), blank=True, null=True)
    forecast_error = models.IntegerField(_('Forecast Error'), blank=True, null=True)
    absolute_percentage_error = models.DecimalField(
        _('Absolute Percentage Error'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Model parameters (stored as JSON)
    model_parameters = models.JSONField(_('Model Parameters'), default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Inventory Forecast')
        verbose_name_plural = _('Inventory Forecasts')
        unique_together = ['product', 'warehouse', 'forecast_period_start', 'forecast_period_end']
        indexes = [
            models.Index(fields=['forecast_date', 'forecast_method']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['forecast_period_start', 'forecast_period_end']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name} ({self.forecast_period_start} to {self.forecast_period_end})"


class InventoryAlert(models.Model):
    """
    Model for inventory alerts and notifications.
    """
    ALERT_TYPES = [
        ('LOW_STOCK', _('Low Stock')),
        ('OUT_OF_STOCK', _('Out of Stock')),
        ('OVERSTOCK', _('Overstock')),
        ('SLOW_MOVING', _('Slow Moving')),
        ('DEAD_STOCK', _('Dead Stock')),
        ('EXPIRY_WARNING', _('Expiry Warning')),
        ('QUALITY_ISSUE', _('Quality Issue')),
        ('SUPPLIER_DELAY', _('Supplier Delay')),
        ('COST_VARIANCE', _('Cost Variance')),
        ('FORECAST_DEVIATION', _('Forecast Deviation')),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', _('Low')),
        ('MEDIUM', _('Medium')),
        ('HIGH', _('High')),
        ('CRITICAL', _('Critical')),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('ACKNOWLEDGED', _('Acknowledged')),
        ('RESOLVED', _('Resolved')),
        ('DISMISSED', _('Dismissed')),
    ]
    
    # Alert details
    alert_type = models.CharField(_('Alert Type'), max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_LEVELS)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Related entities
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Product'),
        null=True,
        blank=True
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Warehouse'),
        null=True,
        blank=True
    )
    inventory = models.ForeignKey(
        'inventory.Inventory',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Inventory'),
        null=True,
        blank=True
    )
    
    # Alert content
    title = models.CharField(_('Title'), max_length=200)
    message = models.TextField(_('Message'))
    threshold_value = models.DecimalField(
        _('Threshold Value'), 
        max_digits=15, 
        decimal_places=4, 
        blank=True, 
        null=True
    )
    current_value = models.DecimalField(
        _('Current Value'), 
        max_digits=15, 
        decimal_places=4, 
        blank=True, 
        null=True
    )
    
    # Action tracking
    recommended_action = models.TextField(_('Recommended Action'), blank=True)
    action_taken = models.TextField(_('Action Taken'), blank=True)
    
    # User tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_inventory_alerts',
        verbose_name=_('Created By')
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_inventory_alerts',
        verbose_name=_('Acknowledged By')
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_inventory_alerts',
        verbose_name=_('Resolved By')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    acknowledged_at = models.DateTimeField(_('Acknowledged At'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Inventory Alert')
        verbose_name_plural = _('Inventory Alerts')
        indexes = [
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['product', 'warehouse']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title}"


class CycleCount(models.Model):
    """
    Model for managing cycle counting activities.
    """
    STATUS_CHOICES = [
        ('PLANNED', _('Planned')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    # Count details
    count_name = models.CharField(_('Count Name'), max_length=200)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.CASCADE,
        related_name='cycle_counts',
        verbose_name=_('Warehouse')
    )
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='PLANNED')
    
    # Scheduling
    scheduled_date = models.DateField(_('Scheduled Date'))
    started_at = models.DateTimeField(_('Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    
    # Count criteria
    count_all_products = models.BooleanField(_('Count All Products'), default=False)
    product_categories = models.ManyToManyField(
        'products.Category',
        blank=True,
        verbose_name=_('Product Categories')
    )
    specific_products = models.ManyToManyField(
        'products.Product',
        blank=True,
        verbose_name=_('Specific Products')
    )
    
    # Results summary
    total_items_counted = models.IntegerField(_('Total Items Counted'), default=0)
    items_with_variances = models.IntegerField(_('Items with Variances'), default=0)
    total_variance_value = models.DecimalField(
        _('Total Variance Value'), 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    accuracy_percentage = models.DecimalField(
        _('Accuracy Percentage'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # User tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cycle_counts',
        verbose_name=_('Created By')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cycle_counts',
        verbose_name=_('Assigned To')
    )
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Cycle Count')
        verbose_name_plural = _('Cycle Counts')
        indexes = [
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['warehouse', 'status']),
        ]
    
    def __str__(self):
        return f"{self.count_name} - {self.warehouse.name} ({self.scheduled_date})"


class CycleCountItem(models.Model):
    """
    Model for individual items in a cycle count.
    """
    cycle_count = models.ForeignKey(
        CycleCount,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Cycle Count')
    )
    inventory = models.ForeignKey(
        'inventory.Inventory',
        on_delete=models.CASCADE,
        related_name='cycle_count_items',
        verbose_name=_('Inventory')
    )
    
    # Count data
    system_quantity = models.IntegerField(_('System Quantity'))
    counted_quantity = models.IntegerField(_('Counted Quantity'), null=True, blank=True)
    variance_quantity = models.IntegerField(_('Variance Quantity'), default=0)
    variance_value = models.DecimalField(
        _('Variance Value'), 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    
    # Count details
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counted_items',
        verbose_name=_('Counted By')
    )
    counted_at = models.DateTimeField(_('Counted At'), null=True, blank=True)
    
    # Variance handling
    variance_reason = models.TextField(_('Variance Reason'), blank=True)
    adjustment_made = models.BooleanField(_('Adjustment Made'), default=False)
    adjustment_transaction = models.ForeignKey(
        'inventory.InventoryTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cycle_count_adjustments',
        verbose_name=_('Adjustment Transaction')
    )
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Cycle Count Item')
        verbose_name_plural = _('Cycle Count Items')
        unique_together = ['cycle_count', 'inventory']
    
    def __str__(self):
        return f"{self.cycle_count.count_name} - {self.inventory.product.name}"
    
    def save(self, *args, **kwargs):
        """Calculate variance when saving."""
        if self.counted_quantity is not None:
            self.variance_quantity = self.counted_quantity - self.system_quantity
            self.variance_value = self.variance_quantity * self.inventory.cost_price
        super().save(*args, **kwargs)