from rest_framework import serializers
from .models import (
    SalesMetrics, ProductSalesAnalytics, CustomerAnalytics, SalesForecast,
    SalesGoal, SalesCommission, SalesTerritory, SalesPipeline, SalesReport,
    SalesAnomalyDetection
)


class SalesMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesMetrics
        fields = '__all__'


class ProductSalesAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSalesAnalytics
        fields = '__all__'


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAnalytics
        fields = '__all__'


class SalesForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesForecast
        fields = '__all__'


class SalesGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    is_achieved = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesGoal
        fields = '__all__'


class SalesCommissionSerializer(serializers.ModelSerializer):
    sales_rep_name = serializers.CharField(source='sales_rep.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = SalesCommission
        fields = '__all__'


class SalesTerritorySerializer(serializers.ModelSerializer):
    assigned_rep_name = serializers.CharField(source='assigned_rep.get_full_name', read_only=True)
    revenue_achievement = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesTerritory
        fields = '__all__'


class SalesPipelineSerializer(serializers.ModelSerializer):
    sales_rep_name = serializers.CharField(source='sales_rep.get_full_name', read_only=True)
    weighted_value = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesPipeline
        fields = '__all__'


class SalesReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = SalesReport
        fields = '__all__'


class SalesAnomalyDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAnomalyDetection
        fields = '__all__'


class SalesDashboardSerializer(serializers.Serializer):
    """Serializer for sales dashboard data"""
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    revenue_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    order_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    top_products = ProductSalesAnalyticsSerializer(many=True)
    recent_anomalies = SalesAnomalyDetectionSerializer(many=True)
    active_goals = SalesGoalSerializer(many=True)


class SalesChartDataSerializer(serializers.Serializer):
    """Serializer for chart data"""
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())


class SalesRevenueAnalysisSerializer(serializers.Serializer):
    """Serializer for revenue analysis"""
    period = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders = serializers.IntegerField()
    customers = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    gross_margin = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit_margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class CustomerCohortAnalysisSerializer(serializers.Serializer):
    """Serializer for customer cohort analysis"""
    cohort_month = serializers.CharField()
    customers_count = serializers.IntegerField()
    retention_rates = serializers.DictField()
    revenue_per_cohort = serializers.DictField()


class SalesFunnelAnalysisSerializer(serializers.Serializer):
    """Serializer for sales funnel analysis"""
    stage = serializers.CharField()
    count = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    drop_off_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class SalesPerformanceComparisonSerializer(serializers.Serializer):
    """Serializer for sales performance comparison"""
    current_period = SalesRevenueAnalysisSerializer()
    previous_period = SalesRevenueAnalysisSerializer()
    growth_metrics = serializers.DictField()


class SalesAttributionAnalysisSerializer(serializers.Serializer):
    """Serializer for sales attribution analysis"""
    channel = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders = serializers.IntegerField()
    customers = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    cost_per_acquisition = serializers.DecimalField(max_digits=10, decimal_places=2)
    return_on_investment = serializers.DecimalField(max_digits=5, decimal_places=2)


class SalesSeasonalityAnalysisSerializer(serializers.Serializer):
    """Serializer for seasonality analysis"""
    month = serializers.CharField()
    seasonal_index = serializers.DecimalField(max_digits=5, decimal_places=2)
    trend_factor = serializers.DecimalField(max_digits=5, decimal_places=2)
    predicted_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    confidence_interval = serializers.DictField()