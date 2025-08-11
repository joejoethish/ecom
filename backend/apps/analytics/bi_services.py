"""
Advanced Business Intelligence Services for comprehensive analytics platform.
"""
from django.db.models import Sum, Count, Avg, Q, F, Max, Min, StdDev, Variance
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union
import json
# import numpy as np
# import pandas as pd
# Note: numpy and pandas would be imported in production
# For demo purposes, we'll simulate their functionality
from django.db import models, transaction
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio

from .bi_models import (
    BIDashboard, BIWidget, BIDataSource, BIReport, BIInsight, BIMLModel,
    BIDataCatalog, BIAnalyticsSession, BIPerformanceMetric, BIAlert
)
from .models import SalesMetrics, ProductSalesAnalytics, CustomerAnalytics

logger = logging.getLogger(__name__)


class BIDashboardService:
    """Service for BI Dashboard management and data aggregation"""

    @staticmethod
    def create_executive_dashboard(user, name: str = "Executive Dashboard") -> BIDashboard:
        """Create a comprehensive executive dashboard with key widgets"""
        dashboard = BIDashboard.objects.create(
            name=name,
            description="Executive summary with key business metrics and insights",
            dashboard_type='executive',
            created_by=user,
            layout_config={
                'grid_size': 12,
                'row_height': 60,
                'margin': [10, 10],
                'theme': 'executive'
            },
            filters_config={
                'date_range': {'default': '30d', 'options': ['7d', '30d', '90d', '1y']},
                'business_unit': {'default': 'all', 'options': []},
                'region': {'default': 'all', 'options': []}
            }
        )

        # Create executive widgets
        widgets_config = [
            {
                'name': 'Revenue Overview',
                'widget_type': 'metric',
                'data_source': 'sales_revenue_summary',
                'position_x': 0, 'position_y': 0, 'width': 3, 'height': 2,
                'visualization_config': {
                    'metric_type': 'currency',
                    'show_trend': True,
                    'comparison_period': 'previous_month'
                }
            },
            {
                'name': 'Profit Margin',
                'widget_type': 'gauge',
                'data_source': 'profit_margin_analysis',
                'position_x': 3, 'position_y': 0, 'width': 3, 'height': 2,
                'visualization_config': {
                    'gauge_type': 'semi_circle',
                    'min_value': 0, 'max_value': 100,
                    'thresholds': [{'value': 20, 'color': 'red'}, {'value': 40, 'color': 'yellow'}, {'value': 60, 'color': 'green'}]
                }
            },
            {
                'name': 'Customer Acquisition',
                'widget_type': 'chart',
                'data_source': 'customer_acquisition_trends',
                'position_x': 6, 'position_y': 0, 'width': 6, 'height': 3,
                'visualization_config': {
                    'chart_type': 'line',
                    'x_axis': 'date',
                    'y_axis': 'new_customers',
                    'show_trend_line': True
                }
            },
            {
                'name': 'Sales Performance by Region',
                'widget_type': 'map',
                'data_source': 'regional_sales_performance',
                'position_x': 0, 'position_y': 3, 'width': 6, 'height': 4,
                'visualization_config': {
                    'map_type': 'choropleth',
                    'metric': 'revenue',
                    'color_scale': 'blues'
                }
            },
            {
                'name': 'Top Products',
                'widget_type': 'table',
                'data_source': 'top_performing_products',
                'position_x': 6, 'position_y': 3, 'width': 6, 'height': 4,
                'visualization_config': {
                    'columns': ['product_name', 'revenue', 'units_sold', 'profit_margin'],
                    'sortable': True,
                    'pagination': True
                }
            }
        ]

        for widget_config in widgets_config:
            BIWidget.objects.create(
                dashboard=dashboard,
                **widget_config
            )

        return dashboard

    @staticmethod
    def get_dashboard_data(dashboard_id: str, filters: Dict = None) -> Dict:
        """Get complete dashboard data with all widgets"""
        try:
            dashboard = BIDashboard.objects.get(id=dashboard_id)
            widgets = dashboard.widgets.filter(is_active=True)
            
            dashboard_data = {
                'id': str(dashboard.id),
                'name': dashboard.name,
                'description': dashboard.description,
                'dashboard_type': dashboard.dashboard_type,
                'layout_config': dashboard.layout_config,
                'filters_config': dashboard.filters_config,
                'widgets': []
            }

            # Get data for each widget
            for widget in widgets:
                widget_data = BIDashboardService._get_widget_data(widget, filters)
                dashboard_data['widgets'].append(widget_data)

            return dashboard_data
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise

    @staticmethod
    def _get_widget_data(widget: BIWidget, filters: Dict = None) -> Dict:
        """Get data for a specific widget"""
        widget_data = {
            'id': str(widget.id),
            'name': widget.name,
            'widget_type': widget.widget_type,
            'position_x': widget.position_x,
            'position_y': widget.position_y,
            'width': widget.width,
            'height': widget.height,
            'visualization_config': widget.visualization_config,
            'data': None,
            'last_updated': timezone.now().isoformat()
        }

        try:
            # Get data based on data source
            data_service = BIDataService()
            widget_data['data'] = data_service.get_data_by_source(
                widget.data_source, 
                widget.query_config, 
                filters
            )
        except Exception as e:
            logger.error(f"Error getting widget data for {widget.name}: {str(e)}")
            widget_data['error'] = str(e)

        return widget_data

    @staticmethod
    def update_widget_position(widget_id: str, position_x: int, position_y: int, width: int, height: int):
        """Update widget position and size"""
        try:
            widget = BIWidget.objects.get(id=widget_id)
            widget.position_x = position_x
            widget.position_y = position_y
            widget.width = width
            widget.height = height
            widget.save()
            return True
        except Exception as e:
            logger.error(f"Error updating widget position: {str(e)}")
            return False


class BIDataService:
    """Service for BI data retrieval and processing"""

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes default cache

    def get_data_by_source(self, data_source: str, query_config: Dict, filters: Dict = None) -> Dict:
        """Get data from various sources based on configuration"""
        cache_key = f"bi_data_{data_source}_{hash(str(query_config))}_{hash(str(filters))}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            if data_source == 'sales_revenue_summary':
                data = self._get_sales_revenue_summary(filters)
            elif data_source == 'profit_margin_analysis':
                data = self._get_profit_margin_analysis(filters)
            elif data_source == 'customer_acquisition_trends':
                data = self._get_customer_acquisition_trends(filters)
            elif data_source == 'regional_sales_performance':
                data = self._get_regional_sales_performance(filters)
            elif data_source == 'top_performing_products':
                data = self._get_top_performing_products(filters)
            elif data_source == 'real_time_metrics':
                data = self._get_real_time_metrics(filters)
            else:
                data = self._get_custom_data_source(data_source, query_config, filters)

            cache.set(cache_key, data, self.cache_timeout)
            return data
        except Exception as e:
            logger.error(f"Error getting data from source {data_source}: {str(e)}")
            raise

    def _get_sales_revenue_summary(self, filters: Dict = None) -> Dict:
        """Get sales revenue summary with trends"""
        date_range = self._get_date_range(filters)
        
        current_period = SalesMetrics.objects.filter(
            date__range=date_range
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
            avg_order_value=Avg('average_order_value')
        )

        # Previous period for comparison
        period_length = (date_range[1] - date_range[0]).days
        previous_start = date_range[0] - timedelta(days=period_length)
        previous_end = date_range[0]

        previous_period = SalesMetrics.objects.filter(
            date__range=[previous_start, previous_end]
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
            avg_order_value=Avg('average_order_value')
        )

        # Calculate trends
        revenue_trend = self._calculate_trend(
            current_period['total_revenue'] or 0,
            previous_period['total_revenue'] or 0
        )

        return {
            'current_revenue': float(current_period['total_revenue'] or 0),
            'current_orders': current_period['total_orders'] or 0,
            'avg_order_value': float(current_period['avg_order_value'] or 0),
            'revenue_trend': revenue_trend,
            'period': f"{date_range[0]} to {date_range[1]}"
        }

    def _get_profit_margin_analysis(self, filters: Dict = None) -> Dict:
        """Get profit margin analysis"""
        date_range = self._get_date_range(filters)
        
        metrics = SalesMetrics.objects.filter(
            date__range=date_range
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            gross_margin=Sum('gross_margin'),
            net_profit=Sum('net_profit')
        )

        total_revenue = float(metrics['total_revenue'] or 0)
        gross_margin = float(metrics['gross_margin'] or 0)
        net_profit = float(metrics['net_profit'] or 0)

        gross_margin_percent = (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
        net_margin_percent = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            'gross_margin_percent': round(gross_margin_percent, 2),
            'net_margin_percent': round(net_margin_percent, 2),
            'total_revenue': total_revenue,
            'gross_margin': gross_margin,
            'net_profit': net_profit
        }

    def _get_customer_acquisition_trends(self, filters: Dict = None) -> Dict:
        """Get customer acquisition trends over time"""
        date_range = self._get_date_range(filters)
        
        daily_metrics = SalesMetrics.objects.filter(
            date__range=date_range
        ).values('date').annotate(
            new_customers=Sum('new_customers')
        ).order_by('date')

        trend_data = [
            {
                'date': metric['date'].strftime('%Y-%m-%d'),
                'new_customers': metric['new_customers'] or 0
            }
            for metric in daily_metrics
        ]

        return {
            'trend_data': trend_data,
            'total_new_customers': sum(item['new_customers'] for item in trend_data)
        }

    def _get_regional_sales_performance(self, filters: Dict = None) -> Dict:
        """Get regional sales performance (simplified implementation)"""
        # This would typically integrate with geographic data
        # For now, return mock regional data
        regions = [
            {'region': 'North America', 'revenue': 1250000, 'orders': 3200, 'growth': 12.5},
            {'region': 'Europe', 'revenue': 980000, 'orders': 2800, 'growth': 8.3},
            {'region': 'Asia Pacific', 'revenue': 750000, 'orders': 2100, 'growth': 15.7},
            {'region': 'Latin America', 'revenue': 420000, 'orders': 1200, 'growth': 6.2},
            {'region': 'Middle East & Africa', 'revenue': 280000, 'orders': 800, 'growth': 9.8}
        ]

        return {
            'regional_data': regions,
            'total_revenue': sum(r['revenue'] for r in regions),
            'total_orders': sum(r['orders'] for r in regions)
        }

    def _get_top_performing_products(self, filters: Dict = None) -> Dict:
        """Get top performing products"""
        date_range = self._get_date_range(filters)
        
        top_products = ProductSalesAnalytics.objects.filter(
            date__range=date_range
        ).values(
            'product_id', 'product_name', 'category_name'
        ).annotate(
            total_revenue=Sum('revenue'),
            total_units=Sum('units_sold'),
            total_profit=Sum('profit'),
            avg_profit_margin=Avg('profit_margin')
        ).order_by('-total_revenue')[:10]

        products_data = [
            {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'category': product['category_name'],
                'revenue': float(product['total_revenue'] or 0),
                'units_sold': product['total_units'] or 0,
                'profit': float(product['total_profit'] or 0),
                'profit_margin': round(float(product['avg_profit_margin'] or 0), 2)
            }
            for product in top_products
        ]

        return {
            'products': products_data,
            'total_products': len(products_data)
        }

    def _get_real_time_metrics(self, filters: Dict = None) -> Dict:
        """Get real-time business metrics"""
        # This would typically connect to real-time data streams
        # For now, return recent data with simulated real-time updates
        today = timezone.now().date()
        
        today_metrics = SalesMetrics.objects.filter(date=today).first()
        
        if not today_metrics:
            # Create today's metrics if they don't exist
            today_metrics = SalesMetrics.objects.create(
                date=today,
                total_revenue=0,
                total_orders=0,
                total_customers=0
            )

        return {
            'current_revenue': float(today_metrics.total_revenue),
            'current_orders': today_metrics.total_orders,
            'active_customers': today_metrics.total_customers,
            'conversion_rate': float(today_metrics.conversion_rate),
            'last_updated': timezone.now().isoformat()
        }

    def _get_custom_data_source(self, data_source: str, query_config: Dict, filters: Dict = None) -> Dict:
        """Handle custom data sources"""
        try:
            # Look up custom data source configuration
            data_source_obj = BIDataSource.objects.get(name=data_source, is_active=True)
            
            if data_source_obj.source_type == 'database':
                return self._execute_database_query(data_source_obj, query_config, filters)
            elif data_source_obj.source_type == 'api':
                return self._fetch_api_data(data_source_obj, query_config, filters)
            else:
                raise ValueError(f"Unsupported data source type: {data_source_obj.source_type}")
                
        except BIDataSource.DoesNotExist:
            raise ValueError(f"Data source not found: {data_source}")

    def _execute_database_query(self, data_source: BIDataSource, query_config: Dict, filters: Dict = None) -> Dict:
        """Execute database query for custom data source"""
        # This would execute custom SQL queries
        # For security, this should use parameterized queries and proper validation
        return {'message': 'Custom database queries not implemented in this demo'}

    def _fetch_api_data(self, data_source: BIDataSource, query_config: Dict, filters: Dict = None) -> Dict:
        """Fetch data from external API"""
        # This would make HTTP requests to external APIs
        return {'message': 'External API integration not implemented in this demo'}

    def _get_date_range(self, filters: Dict = None) -> Tuple[date, date]:
        """Get date range from filters or default to last 30 days"""
        if filters and 'date_range' in filters:
            date_range = filters['date_range']
            if date_range == '7d':
                days = 7
            elif date_range == '90d':
                days = 90
            elif date_range == '1y':
                days = 365
            else:
                days = 30
        else:
            days = 30

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date

    def _calculate_trend(self, current: float, previous: float) -> Dict:
        """Calculate trend percentage and direction"""
        if previous == 0:
            return {'percentage': 100.0 if current > 0 else 0.0, 'direction': 'up' if current > 0 else 'neutral'}
        
        percentage = ((current - previous) / previous) * 100
        direction = 'up' if percentage > 0 else 'down' if percentage < 0 else 'neutral'
        
        return {'percentage': round(percentage, 2), 'direction': direction}


class BIInsightService:
    """Service for automated insight generation and anomaly detection"""

    @staticmethod
    def generate_automated_insights(data_source_id: str = None) -> List[Dict]:
        """Generate automated insights from data analysis"""
        insights = []
        
        try:
            # Anomaly detection in sales data
            sales_anomalies = BIInsightService._detect_sales_anomalies()
            insights.extend(sales_anomalies)
            
            # Trend analysis
            trend_insights = BIInsightService._analyze_trends()
            insights.extend(trend_insights)
            
            # Customer behavior insights
            customer_insights = BIInsightService._analyze_customer_behavior()
            insights.extend(customer_insights)
            
            # Product performance insights
            product_insights = BIInsightService._analyze_product_performance()
            insights.extend(product_insights)
            
            return insights
        except Exception as e:
            logger.error(f"Error generating automated insights: {str(e)}")
            return []

    @staticmethod
    def _detect_sales_anomalies() -> List[Dict]:
        """Detect anomalies in sales data"""
        insights = []
        
        # Get recent sales data
        recent_data = SalesMetrics.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('date')
        
        if recent_data.count() < 7:
            return insights
        
        # Calculate moving average and standard deviation (simplified)
        revenues = [float(metric.total_revenue) for metric in recent_data]
        
        # Simple moving average calculation
        for i, metric in enumerate(recent_data):
            if i >= 6:  # Need at least 7 data points for 7-day moving average
                window_revenues = revenues[i-6:i+1]
                moving_avg = sum(window_revenues) / len(window_revenues)
                moving_std = (sum((x - moving_avg) ** 2 for x in window_revenues) / len(window_revenues)) ** 0.5
                
                current_revenue = revenues[i]
                if abs(current_revenue - moving_avg) > 2 * moving_std:
                    severity = 'high' if abs(current_revenue - moving_avg) > 3 * moving_std else 'medium'
                    
                    insight = {
                        'title': f'Sales Anomaly Detected on {metric.date}',
                        'description': f'Revenue of ${current_revenue:,.2f} is significantly different from expected ${moving_avg:,.2f}',
                        'insight_type': 'anomaly',
                        'severity': severity,
                        'current_value': current_revenue,
                        'expected_value': moving_avg,
                        'deviation_percentage': abs((current_revenue - moving_avg) / moving_avg * 100),
                        'confidence_score': 85.0,
                        'action_items': [
                            'Investigate potential causes for revenue deviation',
                            'Check for data quality issues',
                            'Review marketing campaigns or external factors'
                        ]
                    }
                    insights.append(insight)
        
        return insights

    @staticmethod
    def _analyze_trends() -> List[Dict]:
        """Analyze trends in business metrics"""
        insights = []
        
        # Analyze revenue trend
        last_30_days = SalesMetrics.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).aggregate(
            avg_revenue=Avg('total_revenue'),
            total_revenue=Sum('total_revenue')
        )
        
        previous_30_days = SalesMetrics.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=60),
            date__lt=timezone.now().date() - timedelta(days=30)
        ).aggregate(
            avg_revenue=Avg('total_revenue'),
            total_revenue=Sum('total_revenue')
        )
        
        if last_30_days['total_revenue'] and previous_30_days['total_revenue']:
            growth_rate = ((last_30_days['total_revenue'] - previous_30_days['total_revenue']) / 
                          previous_30_days['total_revenue'] * 100)
            
            if abs(growth_rate) > 10:  # Significant trend
                trend_direction = 'positive' if growth_rate > 0 else 'negative'
                severity = 'high' if abs(growth_rate) > 25 else 'medium'
                
                insight = {
                    'title': f'Significant Revenue Trend Detected',
                    'description': f'Revenue has {"increased" if growth_rate > 0 else "decreased"} by {abs(growth_rate):.1f}% over the last 30 days',
                    'insight_type': 'trend',
                    'severity': severity,
                    'current_value': float(last_30_days['total_revenue']),
                    'expected_value': float(previous_30_days['total_revenue']),
                    'deviation_percentage': abs(growth_rate),
                    'confidence_score': 90.0,
                    'action_items': [
                        f'Investigate factors contributing to revenue {"growth" if growth_rate > 0 else "decline"}',
                        'Adjust forecasting models based on trend',
                        'Consider scaling operations accordingly'
                    ]
                }
                insights.append(insight)
        
        return insights

    @staticmethod
    def _analyze_customer_behavior() -> List[Dict]:
        """Analyze customer behavior patterns"""
        insights = []
        
        # Analyze customer lifetime value trends
        recent_customers = CustomerAnalytics.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(
            avg_ltv=Avg('lifetime_value'),
            avg_orders=Avg('total_orders'),
            high_value_customers=Count('id', filter=Q(lifetime_value__gt=1000))
        )
        
        if recent_customers['avg_ltv']:
            insight = {
                'title': 'Customer Value Analysis',
                'description': f'Average customer lifetime value is ${recent_customers["avg_ltv"]:.2f} with {recent_customers["high_value_customers"]} high-value customers',
                'insight_type': 'pattern',
                'severity': 'medium',
                'confidence_score': 75.0,
                'metadata': {
                    'avg_lifetime_value': float(recent_customers['avg_ltv']),
                    'avg_orders_per_customer': float(recent_customers['avg_orders'] or 0),
                    'high_value_customer_count': recent_customers['high_value_customers']
                },
                'action_items': [
                    'Develop retention strategies for high-value customers',
                    'Create targeted campaigns for customer segments',
                    'Implement loyalty programs'
                ]
            }
            insights.append(insight)
        
        return insights

    @staticmethod
    def _analyze_product_performance() -> List[Dict]:
        """Analyze product performance patterns"""
        insights = []
        
        # Find top and bottom performing products
        last_30_days = timezone.now().date() - timedelta(days=30)
        
        product_performance = ProductSalesAnalytics.objects.filter(
            date__gte=last_30_days
        ).values('product_id', 'product_name').annotate(
            total_revenue=Sum('revenue'),
            total_units=Sum('units_sold'),
            avg_margin=Avg('profit_margin')
        ).order_by('-total_revenue')
        
        if product_performance.count() > 0:
            top_product = product_performance.first()
            
            insight = {
                'title': f'Top Performing Product: {top_product["product_name"]}',
                'description': f'Generated ${top_product["total_revenue"]:.2f} in revenue with {top_product["total_units"]} units sold',
                'insight_type': 'recommendation',
                'severity': 'medium',
                'confidence_score': 80.0,
                'metadata': {
                    'product_id': top_product['product_id'],
                    'revenue': float(top_product['total_revenue']),
                    'units_sold': top_product['total_units'],
                    'profit_margin': float(top_product['avg_margin'] or 0)
                },
                'action_items': [
                    'Increase inventory for top-performing products',
                    'Analyze success factors for replication',
                    'Consider expanding product line'
                ]
            }
            insights.append(insight)
        
        return insights


class BIMLService:
    """Service for Machine Learning model management and predictions"""

    @staticmethod
    def create_forecasting_model(name: str, user, data_source_id: str) -> BIMLModel:
        """Create a sales forecasting ML model"""
        try:
            data_source = BIDataSource.objects.get(id=data_source_id)
            
            model = BIMLModel.objects.create(
                name=name,
                description="Sales forecasting model using time series analysis",
                model_type='forecasting',
                algorithm='ARIMA',
                training_data_source=data_source,
                feature_config={
                    'features': ['date', 'revenue', 'orders', 'seasonality'],
                    'target': 'revenue',
                    'time_column': 'date',
                    'frequency': 'daily'
                },
                hyperparameters={
                    'p': 1, 'd': 1, 'q': 1,
                    'seasonal_p': 1, 'seasonal_d': 1, 'seasonal_q': 1,
                    'seasonal_periods': 7
                },
                created_by=user
            )
            
            return model
        except Exception as e:
            logger.error(f"Error creating forecasting model: {str(e)}")
            raise

    @staticmethod
    def train_model(model_id: str) -> Dict:
        """Train a machine learning model"""
        try:
            model = BIMLModel.objects.get(id=model_id)
            
            # Simulate model training process
            # In a real implementation, this would:
            # 1. Fetch training data from the data source
            # 2. Preprocess and feature engineer the data
            # 3. Train the ML model using the specified algorithm
            # 4. Evaluate model performance
            # 5. Save the trained model
            
            # Mock training results
            performance_metrics = {
                'mae': 1250.50,  # Mean Absolute Error
                'rmse': 1850.75,  # Root Mean Square Error
                'mape': 8.5,      # Mean Absolute Percentage Error
                'r2_score': 0.85,  # R-squared score
                'training_samples': 365,
                'validation_samples': 90
            }
            
            model.performance_metrics = performance_metrics
            model.last_trained = timezone.now()
            model.is_deployed = True
            model.save()
            
            return {
                'status': 'success',
                'model_id': str(model.id),
                'performance_metrics': performance_metrics,
                'message': 'Model trained successfully'
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @staticmethod
    def generate_predictions(model_id: str, prediction_periods: int = 30) -> Dict:
        """Generate predictions using a trained ML model"""
        try:
            model = BIMLModel.objects.get(id=model_id, is_deployed=True)
            
            # Simulate prediction generation
            # In a real implementation, this would:
            # 1. Load the trained model
            # 2. Prepare input data
            # 3. Generate predictions
            # 4. Calculate confidence intervals
            
            base_date = timezone.now().date()
            predictions = []
            
            # Generate mock predictions with trend and seasonality
            base_value = 50000  # Base daily revenue
            trend = 100  # Daily trend increase
            
            for i in range(prediction_periods):
                prediction_date = base_date + timedelta(days=i+1)
                
                # Add trend and seasonal variation
                import math
                seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * i / 7)  # Weekly seasonality
                predicted_value = (base_value + trend * i) * seasonal_factor
                
                # Add confidence intervals
                confidence_interval = predicted_value * 0.15  # 15% confidence interval
                
                predictions.append({
                    'date': prediction_date.strftime('%Y-%m-%d'),
                    'predicted_value': round(predicted_value, 2),
                    'lower_bound': round(predicted_value - confidence_interval, 2),
                    'upper_bound': round(predicted_value + confidence_interval, 2),
                    'confidence': 85.0
                })
            
            model.last_prediction = timezone.now()
            model.save()
            
            return {
                'model_id': str(model.id),
                'model_name': model.name,
                'predictions': predictions,
                'prediction_periods': prediction_periods,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            raise


class BIRealtimeService:
    """Service for real-time analytics and streaming data processing"""

    @staticmethod
    def get_realtime_metrics() -> Dict:
        """Get real-time business metrics"""
        try:
            # Simulate real-time metrics
            # In a real implementation, this would connect to:
            # - WebSocket streams
            # - Message queues (Redis, RabbitMQ)
            # - Real-time databases
            # - Event streaming platforms (Kafka)
            
            current_time = timezone.now()
            
            import random
            metrics = {
                'timestamp': current_time.isoformat(),
                'active_users': random.randint(150, 300),
                'current_revenue': round(random.uniform(45000, 55000), 2),
                'orders_today': random.randint(80, 120),
                'conversion_rate': round(random.uniform(2.5, 4.5), 2),
                'cart_abandonment_rate': round(random.uniform(65, 75), 2),
                'page_views': random.randint(2000, 4000),
                'bounce_rate': round(random.uniform(35, 45), 2),
                'average_session_duration': round(random.uniform(180, 300), 0),
                'top_products_realtime': [
                    {'name': 'Product A', 'views': random.randint(50, 100)},
                    {'name': 'Product B', 'views': random.randint(40, 90)},
                    {'name': 'Product C', 'views': random.randint(30, 80)}
                ],
                'geographic_activity': [
                    {'country': 'US', 'active_users': random.randint(50, 100)},
                    {'country': 'UK', 'active_users': random.randint(20, 50)},
                    {'country': 'CA', 'active_users': random.randint(15, 40)},
                    {'country': 'DE', 'active_users': random.randint(10, 30)}
                ]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {str(e)}")
            raise

    @staticmethod
    def process_streaming_event(event_data: Dict) -> bool:
        """Process incoming streaming events"""
        try:
            # Process different types of events
            event_type = event_data.get('type')
            
            if event_type == 'order_placed':
                BIRealtimeService._process_order_event(event_data)
            elif event_type == 'user_activity':
                BIRealtimeService._process_user_activity(event_data)
            elif event_type == 'product_view':
                BIRealtimeService._process_product_view(event_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing streaming event: {str(e)}")
            return False

    @staticmethod
    def _process_order_event(event_data: Dict):
        """Process order placement events"""
        # Update real-time metrics
        # Trigger alerts if needed
        # Update dashboards
        pass

    @staticmethod
    def _process_user_activity(event_data: Dict):
        """Process user activity events"""
        # Track user behavior
        # Update engagement metrics
        pass

    @staticmethod
    def _process_product_view(event_data: Dict):
        """Process product view events"""
        # Update product popularity metrics
        # Track conversion funnels
        pass


class BIDataGovernanceService:
    """Service for data governance and quality management"""

    @staticmethod
    def assess_data_quality(data_source_id: str) -> Dict:
        """Assess data quality for a data source"""
        try:
            data_source = BIDataSource.objects.get(id=data_source_id)
            
            # Simulate data quality assessment
            import random
            quality_metrics = {
                'completeness': round(random.uniform(85, 98), 2),
                'accuracy': round(random.uniform(90, 99), 2),
                'consistency': round(random.uniform(88, 96), 2),
                'timeliness': round(random.uniform(92, 99), 2),
                'validity': round(random.uniform(89, 97), 2),
                'uniqueness': round(random.uniform(95, 99.5), 2)
            }
            
            # Calculate overall score
            overall_score = sum(quality_metrics.values()) / len(quality_metrics)
            
            # Identify issues
            issues = []
            if quality_metrics['completeness'] < 90:
                issues.append('Missing data detected in some records')
            if quality_metrics['accuracy'] < 95:
                issues.append('Data accuracy concerns identified')
            if quality_metrics['consistency'] < 90:
                issues.append('Inconsistent data formats found')
            
            return {
                'data_source_id': str(data_source.id),
                'data_source_name': data_source.name,
                'overall_score': round(overall_score, 2),
                'quality_metrics': quality_metrics,
                'issues': issues,
                'recommendations': [
                    'Implement data validation rules',
                    'Set up automated data quality monitoring',
                    'Establish data cleansing procedures'
                ],
                'assessed_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {str(e)}")
            raise

    @staticmethod
    def create_data_lineage(data_source_id: str) -> Dict:
        """Create data lineage mapping"""
        try:
            data_source = BIDataSource.objects.get(id=data_source_id)
            
            # Simulate data lineage creation
            lineage = {
                'source_id': str(data_source.id),
                'source_name': data_source.name,
                'upstream_sources': [
                    {'name': 'Orders Database', 'type': 'database', 'last_updated': '2024-01-15T10:30:00Z'},
                    {'name': 'Customer API', 'type': 'api', 'last_updated': '2024-01-15T11:00:00Z'}
                ],
                'transformations': [
                    {'step': 1, 'operation': 'Data Extraction', 'description': 'Extract raw data from source systems'},
                    {'step': 2, 'operation': 'Data Cleaning', 'description': 'Remove duplicates and invalid records'},
                    {'step': 3, 'operation': 'Data Transformation', 'description': 'Apply business rules and calculations'},
                    {'step': 4, 'operation': 'Data Loading', 'description': 'Load processed data into analytics store'}
                ],
                'downstream_consumers': [
                    {'name': 'Executive Dashboard', 'type': 'dashboard'},
                    {'name': 'Sales Report', 'type': 'report'},
                    {'name': 'ML Forecasting Model', 'type': 'ml_model'}
                ],
                'impact_analysis': {
                    'affected_dashboards': 3,
                    'affected_reports': 5,
                    'affected_models': 2
                }
            }
            
            return lineage
            
        except Exception as e:
            logger.error(f"Error creating data lineage: {str(e)}")
            raise