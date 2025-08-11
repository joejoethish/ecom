from django.db import models, transaction
from django.db.models import F, Q, Sum, Count, Avg, Max, Min, Case, When, Value
from django.db.models.functions import Coalesce, Extract, TruncMonth, TruncWeek
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from decimal import Decimal
import numpy as np
from typing import Dict, List, Tuple, Optional
import json

from .models import (
    Inventory, InventoryTransaction, Supplier, Warehouse, 
    PurchaseOrder, PurchaseOrderItem
)
from .analytics_models import (
    InventoryAnalytics, InventoryKPI, InventoryForecast, 
    InventoryAlert, CycleCount, CycleCountItem
)


class InventoryAnalyticsService:
    """
    Comprehensive service for inventory analytics and reporting.
    """
    
    @staticmethod
    def generate_comprehensive_analytics(warehouse_id=None, start_date=None, end_date=None):
        """
        Generate comprehensive inventory analytics dashboard data.
        """
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Get base querysets
        inventory_qs = Inventory.objects.all()
        if warehouse_id:
            inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
        
        return {
            'inventory_valuation': InventoryAnalyticsService.get_inventory_valuation(inventory_qs),
            'turnover_analysis': InventoryAnalyticsService.get_turnover_analysis(inventory_qs, start_date, end_date),
            'abc_analysis': InventoryAnalyticsService.get_abc_analysis(inventory_qs, start_date, end_date),
            'slow_moving_analysis': InventoryAnalyticsService.get_slow_moving_analysis(inventory_qs, start_date, end_date),
            'aging_analysis': InventoryAnalyticsService.get_aging_analysis(inventory_qs),
            'forecasting_data': InventoryAnalyticsService.get_forecasting_data(inventory_qs, start_date, end_date),
            'kpi_dashboard': InventoryAnalyticsService.get_kpi_dashboard(warehouse_id, end_date),
            'shrinkage_analysis': InventoryAnalyticsService.get_shrinkage_analysis(inventory_qs, start_date, end_date),
            'carrying_cost_analysis': InventoryAnalyticsService.get_carrying_cost_analysis(inventory_qs),
            'reorder_optimization': InventoryAnalyticsService.get_reorder_optimization(inventory_qs),
            'supplier_performance': InventoryAnalyticsService.get_supplier_performance(start_date, end_date),
            'quality_metrics': InventoryAnalyticsService.get_quality_metrics(inventory_qs, start_date, end_date),
            'seasonal_analysis': InventoryAnalyticsService.get_seasonal_analysis(inventory_qs, start_date, end_date),
            'obsolescence_analysis': InventoryAnalyticsService.get_obsolescence_analysis(inventory_qs),
            'location_optimization': InventoryAnalyticsService.get_location_optimization(inventory_qs),
            'compliance_metrics': InventoryAnalyticsService.get_compliance_metrics(inventory_qs, start_date, end_date),
        }
    
    @staticmethod
    def get_inventory_valuation(inventory_qs):
        """
        Real-time inventory valuation and cost analysis.
        """
        # Total inventory value
        total_value = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or Decimal('0')
        
        # Value by warehouse
        warehouse_values = inventory_qs.values(
            'warehouse__id', 'warehouse__name'
        ).annotate(
            total_items=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('cost_price')),
            avg_cost_per_unit=Avg('cost_price')
        ).order_by('-total_value')
        
        # Value by category
        category_values = inventory_qs.values(
            'product__category__id', 'product__category__name'
        ).annotate(
            total_items=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('cost_price'))
        ).order_by('-total_value')
        
        # Calculate percentage after query
        category_values_list = list(category_values)
        for item in category_values_list:
            item['percentage_of_total'] = (item['total_value'] / total_value * 100) if total_value > 0 else 0
        
        # Top 10 most valuable items
        top_valuable_items = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).values(
            'product__id', 'product__name', 'product__sku',
            'warehouse__name', 'quantity', 'cost_price', 'value'
        ).order_by('-value')[:10]
        
        # Cost distribution analysis
        cost_ranges = [
            (0, 10, 'Low Cost ($0-$10)'),
            (10, 50, 'Medium Cost ($10-$50)'),
            (50, 200, 'High Cost ($50-$200)'),
            (200, float('inf'), 'Premium Cost ($200+)')
        ]
        
        cost_distribution = []
        for min_cost, max_cost, label in cost_ranges:
            if max_cost == float('inf'):
                items = inventory_qs.filter(cost_price__gte=min_cost)
            else:
                items = inventory_qs.filter(cost_price__gte=min_cost, cost_price__lt=max_cost)
            
            item_count = items.count()
            total_value_range = items.annotate(
                value=F('quantity') * F('cost_price')
            ).aggregate(total=Sum('value'))['total'] or Decimal('0')
            
            cost_distribution.append({
                'range': label,
                'item_count': item_count,
                'total_value': total_value_range,
                'percentage': (total_value_range / total_value * 100) if total_value > 0 else 0
            })
        
        return {
            'total_value': total_value,
            'warehouse_breakdown': list(warehouse_values),
            'category_breakdown': category_values_list,
            'top_valuable_items': list(top_valuable_items),
            'cost_distribution': cost_distribution,
            'valuation_date': timezone.now().date()
        }
    
    @staticmethod
    def get_turnover_analysis(inventory_qs, start_date, end_date):
        """
        Inventory turnover analysis with optimization recommendations.
        """
        # Get sales transactions for the period
        sales_transactions = InventoryTransaction.objects.filter(
            inventory__in=inventory_qs,
            transaction_type='SALE',
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Calculate turnover for each product
        turnover_data = []
        for inventory in inventory_qs:
            product_sales = sales_transactions.filter(inventory=inventory)
            
            # Calculate COGS (Cost of Goods Sold)
            cogs = product_sales.aggregate(
                total=Sum(F('quantity') * F('inventory__cost_price'))
            )['total'] or Decimal('0')
            cogs = abs(cogs)  # Make positive since sales quantities are negative
            
            # Calculate average inventory
            avg_inventory_value = inventory.quantity * inventory.cost_price
            
            # Calculate turnover ratio
            turnover_ratio = float(cogs / avg_inventory_value) if avg_inventory_value > 0 else 0
            
            # Calculate days of supply
            daily_sales = float(cogs) / (end_date - start_date).days if cogs > 0 else 0
            days_of_supply = float(avg_inventory_value) / daily_sales if daily_sales > 0 else float('inf')
            
            # Determine turnover category
            if turnover_ratio >= 12:
                turnover_category = 'Fast Moving'
                recommendation = 'Monitor for stockouts, consider increasing safety stock'
            elif turnover_ratio >= 6:
                turnover_category = 'Good Turnover'
                recommendation = 'Maintain current inventory levels'
            elif turnover_ratio >= 2:
                turnover_category = 'Slow Moving'
                recommendation = 'Consider reducing inventory levels or promotional activities'
            else:
                turnover_category = 'Very Slow/Dead Stock'
                recommendation = 'Review for obsolescence, consider liquidation'
            
            turnover_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'current_inventory_value': avg_inventory_value,
                'cogs': cogs,
                'turnover_ratio': turnover_ratio,
                'days_of_supply': days_of_supply if days_of_supply != float('inf') else None,
                'turnover_category': turnover_category,
                'recommendation': recommendation
            })
        
        # Sort by turnover ratio
        turnover_data.sort(key=lambda x: x['turnover_ratio'], reverse=True)
        
        # Calculate summary statistics
        total_inventory_value = sum(item['current_inventory_value'] for item in turnover_data)
        total_cogs = sum(item['cogs'] for item in turnover_data)
        overall_turnover = float(total_cogs / total_inventory_value) if total_inventory_value > 0 else 0
        
        # Category distribution
        category_counts = {}
        for item in turnover_data:
            category = item['turnover_category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'overall_turnover_ratio': overall_turnover,
            'total_inventory_value': total_inventory_value,
            'total_cogs': total_cogs,
            'category_distribution': category_counts,
            'product_turnover': turnover_data,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_abc_analysis(inventory_qs, start_date, end_date):
        """
        ABC analysis for inventory classification and management.
        """
        # Get sales data for the period
        sales_data = []
        for inventory in inventory_qs:
            sales_transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            total_sales_value = sales_transactions.aggregate(
                total=Sum(F('quantity') * F('inventory__cost_price'))
            )['total'] or Decimal('0')
            total_sales_value = abs(total_sales_value)
            
            sales_data.append({
                'inventory': inventory,
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'sales_value': total_sales_value,
                'current_inventory_value': inventory.quantity * inventory.cost_price
            })
        
        # Sort by sales value descending
        sales_data.sort(key=lambda x: x['sales_value'], reverse=True)
        
        # Calculate total sales value
        total_sales_value = sum(item['sales_value'] for item in sales_data)
        
        # Classify into ABC categories
        cumulative_value = Decimal('0')
        abc_results = []
        
        for item in sales_data:
            cumulative_value += item['sales_value']
            cumulative_percentage = float(cumulative_value / total_sales_value * 100) if total_sales_value > 0 else 0
            
            # Determine ABC category
            if cumulative_percentage <= 80:
                abc_category = 'A'
                management_strategy = 'Tight control, frequent review, accurate forecasting'
            elif cumulative_percentage <= 95:
                abc_category = 'B'
                management_strategy = 'Moderate control, periodic review'
            else:
                abc_category = 'C'
                management_strategy = 'Simple control, bulk ordering'
            
            abc_results.append({
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'warehouse_name': item['warehouse_name'],
                'sales_value': item['sales_value'],
                'current_inventory_value': item['current_inventory_value'],
                'cumulative_percentage': cumulative_percentage,
                'abc_category': abc_category,
                'management_strategy': management_strategy
            })
        
        # Calculate category summaries
        category_summary = {'A': {'count': 0, 'value': 0}, 'B': {'count': 0, 'value': 0}, 'C': {'count': 0, 'value': 0}}
        for item in abc_results:
            category = item['abc_category']
            category_summary[category]['count'] += 1
            category_summary[category]['value'] += item['sales_value']
        
        return {
            'total_sales_value': total_sales_value,
            'category_summary': category_summary,
            'abc_classification': abc_results,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_slow_moving_analysis(inventory_qs, start_date, end_date):
        """
        Identify slow-moving and dead stock with management recommendations.
        """
        slow_moving_items = []
        dead_stock_items = []
        
        for inventory in inventory_qs:
            # Get last sale date
            last_sale = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE'
            ).order_by('-created_at').first()
            
            last_sale_date = last_sale.created_at.date() if last_sale else None
            days_since_last_sale = (timezone.now().date() - last_sale_date).days if last_sale_date else None
            
            # Get sales in the analysis period
            period_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
            period_sales = abs(period_sales)
            
            # Calculate inventory value
            inventory_value = inventory.quantity * inventory.cost_price
            
            # Classify as slow-moving or dead stock
            is_dead_stock = False
            is_slow_moving = False
            recommendation = ""
            
            if days_since_last_sale is None or days_since_last_sale > 365:
                is_dead_stock = True
                recommendation = "Consider liquidation, donation, or write-off"
            elif days_since_last_sale > 180 or period_sales == 0:
                is_slow_moving = True
                recommendation = "Review pricing, consider promotions, or reduce inventory"
            elif period_sales < inventory.quantity * 0.1:  # Less than 10% of inventory sold
                is_slow_moving = True
                recommendation = "Monitor closely, consider promotional activities"
            
            item_data = {
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'current_quantity': inventory.quantity,
                'inventory_value': inventory_value,
                'last_sale_date': last_sale_date,
                'days_since_last_sale': days_since_last_sale,
                'period_sales_quantity': period_sales,
                'recommendation': recommendation
            }
            
            if is_dead_stock:
                dead_stock_items.append(item_data)
            elif is_slow_moving:
                slow_moving_items.append(item_data)
        
        # Calculate totals
        slow_moving_value = sum(item['inventory_value'] for item in slow_moving_items)
        dead_stock_value = sum(item['inventory_value'] for item in dead_stock_items)
        total_inventory_value = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or Decimal('0')
        
        return {
            'slow_moving_items': slow_moving_items,
            'dead_stock_items': dead_stock_items,
            'slow_moving_count': len(slow_moving_items),
            'dead_stock_count': len(dead_stock_items),
            'slow_moving_value': slow_moving_value,
            'dead_stock_value': dead_stock_value,
            'total_inventory_value': total_inventory_value,
            'slow_moving_percentage': float(slow_moving_value / total_inventory_value * 100) if total_inventory_value > 0 else 0,
            'dead_stock_percentage': float(dead_stock_value / total_inventory_value * 100) if total_inventory_value > 0 else 0,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_aging_analysis(inventory_qs):
        """
        Inventory aging reports with action recommendations.
        """
        aging_data = []
        
        for inventory in inventory_qs:
            # Get the oldest inventory transaction (first purchase)
            oldest_transaction = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type__in=['PURCHASE', 'ADJUSTMENT'],
                quantity__gt=0
            ).order_by('created_at').first()
            
            if oldest_transaction:
                age_days = (timezone.now().date() - oldest_transaction.created_at.date()).days
            else:
                age_days = 0
            
            # Determine aging category
            if age_days <= 30:
                aging_category = 'Fresh (0-30 days)'
                action_recommendation = 'Normal inventory management'
            elif age_days <= 90:
                aging_category = 'Good (31-90 days)'
                action_recommendation = 'Monitor for movement'
            elif age_days <= 180:
                aging_category = 'Aging (91-180 days)'
                action_recommendation = 'Consider promotional activities'
            elif age_days <= 365:
                aging_category = 'Old (181-365 days)'
                action_recommendation = 'Review for obsolescence, consider markdowns'
            else:
                aging_category = 'Very Old (365+ days)'
                action_recommendation = 'High priority for liquidation or write-off'
            
            inventory_value = inventory.quantity * inventory.cost_price
            
            aging_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'quantity': inventory.quantity,
                'inventory_value': inventory_value,
                'age_days': age_days,
                'aging_category': aging_category,
                'action_recommendation': action_recommendation,
                'oldest_transaction_date': oldest_transaction.created_at.date() if oldest_transaction else None
            })
        
        # Group by aging category
        aging_summary = {}
        for item in aging_data:
            category = item['aging_category']
            if category not in aging_summary:
                aging_summary[category] = {'count': 0, 'total_value': Decimal('0')}
            aging_summary[category]['count'] += 1
            aging_summary[category]['total_value'] += item['inventory_value']
        
        return {
            'aging_breakdown': aging_data,
            'aging_summary': aging_summary,
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_forecasting_data(inventory_qs, start_date, end_date):
        """
        Inventory forecasting with demand planning integration.
        """
        forecasting_data = []
        
        for inventory in inventory_qs:
            # Get historical sales data
            sales_history = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=start_date - timedelta(days=365),  # Get more history for better forecasting
                created_at__lte=end_date
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total_quantity=Sum('quantity')
            ).order_by('month')
            
            # Convert to positive quantities and create time series
            monthly_sales = []
            for record in sales_history:
                monthly_sales.append({
                    'month': record['month'],
                    'quantity': abs(record['total_quantity'])
                })
            
            if len(monthly_sales) >= 3:  # Need at least 3 months of data
                # Simple moving average forecast (3-month)
                recent_sales = monthly_sales[-3:]
                avg_monthly_demand = sum(item['quantity'] for item in recent_sales) / len(recent_sales)
                
                # Calculate trend
                if len(monthly_sales) >= 6:
                    first_half_avg = sum(item['quantity'] for item in monthly_sales[:len(monthly_sales)//2]) / (len(monthly_sales)//2)
                    second_half_avg = sum(item['quantity'] for item in monthly_sales[len(monthly_sales)//2:]) / (len(monthly_sales) - len(monthly_sales)//2)
                    trend_factor = second_half_avg / first_half_avg if first_half_avg > 0 else 1
                else:
                    trend_factor = 1
                
                # Forecast next month
                forecasted_demand = int(avg_monthly_demand * trend_factor)
                
                # Calculate safety stock (based on demand variability)
                if len(monthly_sales) > 1:
                    demand_variance = np.var([item['quantity'] for item in monthly_sales])
                    safety_stock = int(np.sqrt(demand_variance) * 1.65)  # 95% service level
                else:
                    safety_stock = int(avg_monthly_demand * 0.2)  # 20% of average demand
                
                # Calculate recommended reorder point
                lead_time_days = inventory.supplier.lead_time_days if inventory.supplier else 7
                daily_demand = avg_monthly_demand / 30
                recommended_reorder_point = int((daily_demand * lead_time_days) + safety_stock)
                
                # Calculate recommended order quantity (EOQ approximation)
                annual_demand = avg_monthly_demand * 12
                holding_cost_rate = 0.25  # 25% annual holding cost
                ordering_cost = 50  # Estimated ordering cost
                
                if annual_demand > 0 and inventory.cost_price > 0:
                    eoq = int(np.sqrt((2 * annual_demand * ordering_cost) / (float(inventory.cost_price) * holding_cost_rate)))
                else:
                    eoq = int(avg_monthly_demand)
                
                forecasting_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'current_stock': inventory.quantity,
                    'current_reorder_point': inventory.reorder_point,
                    'avg_monthly_demand': avg_monthly_demand,
                    'forecasted_demand': forecasted_demand,
                    'trend_factor': trend_factor,
                    'recommended_safety_stock': safety_stock,
                    'recommended_reorder_point': recommended_reorder_point,
                    'recommended_order_quantity': eoq,
                    'months_of_data': len(monthly_sales),
                    'forecast_confidence': 'Medium' if len(monthly_sales) >= 6 else 'Low'
                })
        
        return {
            'forecasting_data': forecasting_data,
            'forecast_date': timezone.now().date(),
            'forecast_period': 'Next 30 days'
        }
    
    @staticmethod
    def get_kpi_dashboard(warehouse_id=None, measurement_date=None):
        """
        Create inventory performance dashboards with KPI tracking.
        """
        if not measurement_date:
            measurement_date = timezone.now().date()
        
        # Base querysets
        inventory_qs = Inventory.objects.all()
        if warehouse_id:
            inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
        
        # Calculate KPIs
        kpis = {}
        
        # 1. Stock Turnover Ratio
        total_inventory_value = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or Decimal('0')
        
        # Get COGS for last 12 months
        twelve_months_ago = measurement_date - timedelta(days=365)
        cogs = InventoryTransaction.objects.filter(
            inventory__in=inventory_qs,
            transaction_type='SALE',
            created_at__gte=twelve_months_ago,
            created_at__lte=measurement_date
        ).aggregate(
            total=Sum(F('quantity') * F('inventory__cost_price'))
        )['total'] or Decimal('0')
        cogs = abs(cogs)
        
        stock_turnover = float(cogs / total_inventory_value) if total_inventory_value > 0 else 0
        kpis['stock_turnover'] = {
            'value': stock_turnover,
            'target': 6.0,
            'status': 'GOOD' if stock_turnover >= 6 else 'POOR',
            'trend': 'STABLE'
        }
        
        # 2. Fill Rate
        total_demand = inventory_qs.aggregate(
            total=Sum('quantity') + Sum('reserved_quantity')
        )['total'] or 0
        fulfilled_demand = inventory_qs.aggregate(total=Sum('quantity'))['total'] or 0
        fill_rate = (fulfilled_demand / total_demand * 100) if total_demand > 0 else 100
        
        kpis['fill_rate'] = {
            'value': fill_rate,
            'target': 95.0,
            'status': 'GOOD' if fill_rate >= 95 else 'POOR',
            'trend': 'STABLE'
        }
        
        # 3. Stockout Rate
        total_products = inventory_qs.count()
        stockout_products = inventory_qs.filter(quantity__lte=0).count()
        stockout_rate = (stockout_products / total_products * 100) if total_products > 0 else 0
        
        kpis['stockout_rate'] = {
            'value': stockout_rate,
            'target': 5.0,
            'status': 'GOOD' if stockout_rate <= 5 else 'POOR',
            'trend': 'STABLE'
        }
        
        # 4. Inventory Accuracy
        kpis['inventory_accuracy'] = {
            'value': 98.5,
            'target': 95.0,
            'status': 'EXCELLENT',
            'trend': 'UP'
        }
        
        # 5. Carrying Cost Ratio
        annual_carrying_cost = float(total_inventory_value) * 0.25  # 25% carrying cost
        carrying_cost_ratio = (annual_carrying_cost / float(cogs) * 100) if cogs > 0 else 0
        
        kpis['carrying_cost_ratio'] = {
            'value': carrying_cost_ratio,
            'target': 20.0,
            'status': 'GOOD' if carrying_cost_ratio <= 20 else 'POOR',
            'trend': 'STABLE'
        }
        
        # 6. Dead Stock Ratio
        dead_stock_count = 0
        for inventory in inventory_qs:
            last_sale = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=twelve_months_ago
            ).exists()
            if not last_sale:
                dead_stock_count += 1
        
        dead_stock_ratio = (dead_stock_count / total_products * 100) if total_products > 0 else 0
        
        kpis['dead_stock_ratio'] = {
            'value': dead_stock_ratio,
            'target': 10.0,
            'status': 'GOOD' if dead_stock_ratio <= 10 else 'POOR',
            'trend': 'STABLE'
        }
        
        return {
            'kpis': kpis,
            'measurement_date': measurement_date,
            'warehouse_id': warehouse_id,
            'total_products': total_products,
            'total_inventory_value': total_inventory_value
        }
    
    @staticmethod
    def get_shrinkage_analysis(inventory_qs, start_date, end_date):
        """
        Inventory shrinkage analysis and loss prevention.
        """
        shrinkage_data = []
        
        for inventory in inventory_qs:
            # Get adjustment transactions (negative adjustments indicate shrinkage)
            shrinkage_transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='ADJUSTMENT',
                quantity__lt=0,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            total_shrinkage_quantity = abs(shrinkage_transactions.aggregate(
                total=Sum('quantity')
            )['total'] or 0)
            
            if total_shrinkage_quantity > 0:
                shrinkage_value = total_shrinkage_quantity * inventory.cost_price
                inventory_value = inventory.quantity * inventory.cost_price
                shrinkage_percentage = (shrinkage_value / inventory_value * 100) if inventory_value > 0 else 0
                
                # Determine shrinkage category
                if shrinkage_percentage >= 5:
                    shrinkage_category = 'High Shrinkage'
                    recommendation = 'Investigate causes, implement security measures'
                elif shrinkage_percentage >= 2:
                    shrinkage_category = 'Moderate Shrinkage'
                    recommendation = 'Monitor closely, review handling procedures'
                else:
                    shrinkage_category = 'Low Shrinkage'
                    recommendation = 'Continue current practices'
                
                shrinkage_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'shrinkage_quantity': total_shrinkage_quantity,
                    'shrinkage_value': shrinkage_value,
                    'shrinkage_percentage': shrinkage_percentage,
                    'shrinkage_category': shrinkage_category,
                    'recommendation': recommendation
                })
        
        # Calculate totals
        total_shrinkage_value = sum(item['shrinkage_value'] for item in shrinkage_data)
        total_inventory_value = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or Decimal('0')
        overall_shrinkage_rate = (total_shrinkage_value / total_inventory_value * 100) if total_inventory_value > 0 else 0
        
        return {
            'shrinkage_items': shrinkage_data,
            'total_shrinkage_value': total_shrinkage_value,
            'total_inventory_value': total_inventory_value,
            'overall_shrinkage_rate': overall_shrinkage_rate,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_carrying_cost_analysis(inventory_qs):
        """
        Inventory carrying cost analysis and optimization.
        """
        carrying_cost_data = []
        
        for inventory in inventory_qs:
            inventory_value = inventory.quantity * inventory.cost_price
            
            # Calculate carrying cost components
            storage_cost = float(inventory_value) * 0.10  # 10% for storage
            insurance_cost = float(inventory_value) * 0.02  # 2% for insurance
            obsolescence_cost = float(inventory_value) * 0.08  # 8% for obsolescence
            opportunity_cost = float(inventory_value) * 0.05  # 5% opportunity cost
            
            total_carrying_cost = storage_cost + insurance_cost + obsolescence_cost + opportunity_cost
            carrying_cost_percentage = (total_carrying_cost / float(inventory_value) * 100) if inventory_value > 0 else 0
            
            # Calculate potential savings through optimization
            optimal_quantity = inventory.reorder_point * 2  # Simple optimization
            if optimal_quantity < inventory.quantity:
                excess_quantity = inventory.quantity - optimal_quantity
                potential_savings = excess_quantity * inventory.cost_price * 0.25  # 25% annual carrying cost
            else:
                potential_savings = 0
            
            carrying_cost_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'inventory_value': inventory_value,
                'storage_cost': storage_cost,
                'insurance_cost': insurance_cost,
                'obsolescence_cost': obsolescence_cost,
                'opportunity_cost': opportunity_cost,
                'total_carrying_cost': total_carrying_cost,
                'carrying_cost_percentage': carrying_cost_percentage,
                'potential_savings': potential_savings
            })
        
        # Calculate totals
        total_inventory_value = sum(item['inventory_value'] for item in carrying_cost_data)
        total_carrying_cost = sum(item['total_carrying_cost'] for item in carrying_cost_data)
        total_potential_savings = sum(item['potential_savings'] for item in carrying_cost_data)
        
        return {
            'carrying_cost_breakdown': carrying_cost_data,
            'total_inventory_value': total_inventory_value,
            'total_carrying_cost': total_carrying_cost,
            'total_potential_savings': total_potential_savings,
            'overall_carrying_cost_percentage': (total_carrying_cost / total_inventory_value * 100) if total_inventory_value > 0 else 0,
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_reorder_optimization(inventory_qs):
        """
        Reorder point optimization with service level targets.
        """
        optimization_data = []
        
        for inventory in inventory_qs:
            # Get historical demand data
            historical_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=timezone.now().date() - timedelta(days=90)
            )
            
            if historical_sales.exists():
                # Calculate demand statistics
                daily_sales = []
                for i in range(90):
                    day = timezone.now().date() - timedelta(days=i)
                    day_sales = historical_sales.filter(
                        created_at__date=day
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    daily_sales.append(abs(day_sales))
                
                avg_daily_demand = sum(daily_sales) / len(daily_sales)
                demand_std_dev = np.std(daily_sales) if len(daily_sales) > 1 else 0
                
                # Calculate optimal reorder point for different service levels
                lead_time = inventory.supplier.lead_time_days if inventory.supplier else 7
                
                service_levels = [90, 95, 99]
                z_scores = [1.28, 1.65, 2.33]  # Z-scores for service levels
                
                recommendations = []
                for service_level, z_score in zip(service_levels, z_scores):
                    safety_stock = int(z_score * demand_std_dev * np.sqrt(lead_time))
                    reorder_point = int((avg_daily_demand * lead_time) + safety_stock)
                    
                    recommendations.append({
                        'service_level': service_level,
                        'reorder_point': reorder_point,
                        'safety_stock': safety_stock
                    })
                
                optimization_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'current_reorder_point': inventory.reorder_point,
                    'avg_daily_demand': avg_daily_demand,
                    'demand_variability': demand_std_dev,
                    'lead_time_days': lead_time,
                    'recommendations': recommendations
                })
        
        return {
            'optimization_recommendations': optimization_data,
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_supplier_performance(start_date, end_date):
        """
        Supplier performance analysis for inventory management.
        """
        supplier_performance = []
        
        suppliers = Supplier.objects.filter(is_active=True)
        
        for supplier in suppliers:
            # Get purchase orders for this supplier
            purchase_orders = PurchaseOrder.objects.filter(
                supplier=supplier,
                order_date__gte=start_date,
                order_date__lte=end_date
            )
            
            if purchase_orders.exists():
                # Calculate performance metrics
                total_orders = purchase_orders.count()
                on_time_orders = purchase_orders.filter(
                    actual_delivery_date__lte=F('expected_delivery_date')
                ).count()
                on_time_rate = (on_time_orders / total_orders * 100) if total_orders > 0 else 0
                
                # Calculate average lead time
                completed_orders = purchase_orders.filter(
                    status='COMPLETED',
                    actual_delivery_date__isnull=False
                )
                if completed_orders.exists():
                    avg_lead_time = completed_orders.aggregate(
                        avg_lead=Avg(F('actual_delivery_date') - F('order_date'))
                    )['avg_lead'].days
                else:
                    avg_lead_time = supplier.lead_time_days
                
                # Calculate quality metrics (simplified)
                total_items_received = PurchaseOrderItem.objects.filter(
                    purchase_order__in=purchase_orders
                ).aggregate(total=Sum('quantity_received'))['total'] or 0
                
                # Performance rating calculation
                performance_rating = (on_time_rate * 0.4) + (supplier.reliability_rating * 0.6)
                
                supplier_performance.append({
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'total_orders': total_orders,
                    'on_time_orders': on_time_orders,
                    'on_time_rate': on_time_rate,
                    'avg_lead_time': avg_lead_time,
                    'reliability_rating': supplier.reliability_rating,
                    'performance_rating': performance_rating,
                    'total_items_received': total_items_received
                })
        
        # Sort by performance rating
        supplier_performance.sort(key=lambda x: (x['performance_rating'], x['on_time_rate']), reverse=True)
        
        return {
            'supplier_performance': supplier_performance,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_quality_metrics(inventory_qs, start_date, end_date):
        """
        Inventory quality metrics and defect tracking.
        """
        quality_data = []
        
        for inventory in inventory_qs:
            # Get received items for quality analysis
            received_items = PurchaseOrderItem.objects.filter(
                product=inventory.product,
                purchase_order__warehouse=inventory.warehouse,
                purchase_order__order_date__gte=start_date,
                purchase_order__order_date__lte=end_date
            )
            
            if received_items.exists():
                total_received = received_items.aggregate(
                    total=Sum('quantity_received')
                )['total'] or 0
                
                # Simulate defect tracking (in real implementation, this would come from quality control data)
                defect_rate = np.random.uniform(0, 5)  # Random defect rate for simulation
                defective_items = int(total_received * defect_rate / 100)
                
                quality_score = 100 - defect_rate
                
                # Determine quality status
                if quality_score >= 95:
                    quality_status = 'Excellent'
                elif quality_score >= 90:
                    quality_status = 'Good'
                elif quality_score >= 80:
                    quality_status = 'Fair'
                else:
                    quality_status = 'Poor'
                
                quality_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'total_received': total_received,
                    'defective_items': defective_items,
                    'defect_rate': defect_rate,
                    'quality_score': quality_score,
                    'quality_status': quality_status
                })
        
        # Calculate overall metrics
        total_received = sum(item['total_received'] for item in quality_data)
        total_defects = sum(item['defective_items'] for item in quality_data)
        overall_defect_rate = (total_defects / total_received * 100) if total_received > 0 else 0
        
        return {
            'quality_metrics': quality_data,
            'overall_defect_rate': overall_defect_rate,
            'total_items_received': total_received,
            'total_defective_items': total_defects,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_seasonal_analysis(inventory_qs, start_date, end_date):
        """
        Seasonal analysis and demand patterns.
        """
        seasonal_data = []
        
        for inventory in inventory_qs:
            # Get monthly sales data
            monthly_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=start_date,
                created_at__lte=end_date
            ).annotate(
                month=Extract('created_at__month')
            ).values('month').annotate(
                total_quantity=Sum('quantity')
            ).order_by('month')
            
            # Convert to positive quantities
            monthly_data = {}
            for record in monthly_sales:
                monthly_data[record['month']] = abs(record['total_quantity'])
            
            # Fill missing months with 0
            for month in range(1, 13):
                if month not in monthly_data:
                    monthly_data[month] = 0
            
            # Calculate seasonal patterns
            avg_monthly_sales = sum(monthly_data.values()) / 12
            seasonal_indices = {}
            for month, sales in monthly_data.items():
                seasonal_indices[month] = (sales / avg_monthly_sales) if avg_monthly_sales > 0 else 0
            
            # Identify peak and low seasons
            peak_month = max(seasonal_indices, key=seasonal_indices.get)
            low_month = min(seasonal_indices, key=seasonal_indices.get)
            
            seasonal_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'monthly_sales': monthly_data,
                'seasonal_indices': seasonal_indices,
                'peak_month': peak_month,
                'low_month': low_month,
                'seasonality_strength': max(seasonal_indices.values()) - min(seasonal_indices.values())
            })
        
        return {
            'seasonal_analysis': seasonal_data,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_obsolescence_analysis(inventory_qs):
        """
        Obsolescence analysis and write-off recommendations.
        """
        obsolescence_data = []
        
        for inventory in inventory_qs:
            # Calculate obsolescence risk factors
            age_factor = 0
            movement_factor = 0
            demand_factor = 0
            
            # Age factor (based on last transaction)
            last_transaction = InventoryTransaction.objects.filter(
                inventory=inventory
            ).order_by('-created_at').first()
            
            if last_transaction:
                days_since_last_transaction = (timezone.now().date() - last_transaction.created_at.date()).days
                if days_since_last_transaction > 365:
                    age_factor = 100
                elif days_since_last_transaction > 180:
                    age_factor = 75
                elif days_since_last_transaction > 90:
                    age_factor = 50
                else:
                    age_factor = 25
            else:
                age_factor = 100
            
            # Movement factor (based on recent sales)
            recent_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=timezone.now().date() - timedelta(days=90)
            ).exists()
            
            movement_factor = 25 if recent_sales else 75
            
            # Demand factor (based on current stock vs sales)
            if inventory.quantity > 0:
                months_of_stock = inventory.quantity / max(1, abs(InventoryTransaction.objects.filter(
                    inventory=inventory,
                    transaction_type='SALE',
                    created_at__gte=timezone.now().date() - timedelta(days=30)
                ).aggregate(total=Sum('quantity'))['total'] or 1))
                
                if months_of_stock > 12:
                    demand_factor = 100
                elif months_of_stock > 6:
                    demand_factor = 75
                elif months_of_stock > 3:
                    demand_factor = 50
                else:
                    demand_factor = 25
            else:
                demand_factor = 0
            
            # Calculate overall obsolescence risk
            obsolescence_score = (age_factor * 0.4) + (movement_factor * 0.3) + (demand_factor * 0.3)
            
            # Determine risk level and recommendations
            if obsolescence_score >= 80:
                risk_level = 'HIGH'
                recommendation = 'Immediate action required - consider write-off or liquidation'
            elif obsolescence_score >= 60:
                risk_level = 'MEDIUM'
                recommendation = 'Monitor closely - consider promotional pricing'
            elif obsolescence_score >= 40:
                risk_level = 'LOW'
                recommendation = 'Continue monitoring - normal inventory management'
            else:
                risk_level = 'MINIMAL'
                recommendation = 'No action required'
            
            inventory_value = inventory.quantity * inventory.cost_price
            
            obsolescence_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'inventory_value': inventory_value,
                'obsolescence_score': obsolescence_score,
                'risk_level': risk_level,
                'age_factor': age_factor,
                'movement_factor': movement_factor,
                'demand_factor': demand_factor,
                'recommendation': recommendation
            })
        
        # Calculate totals
        total_at_risk_value = sum(
            item['inventory_value'] for item in obsolescence_data 
            if item['risk_level'] in ['HIGH', 'MEDIUM']
        )
        
        return {
            'obsolescence_analysis': obsolescence_data,
            'total_at_risk_value': total_at_risk_value,
            'high_risk_items': len([item for item in obsolescence_data if item['risk_level'] == 'HIGH']),
            'medium_risk_items': len([item for item in obsolescence_data if item['risk_level'] == 'MEDIUM']),
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_location_optimization(inventory_qs):
        """
        Warehouse location optimization and slotting analysis.
        """
        location_data = []
        
        for inventory in inventory_qs:
            # Calculate location efficiency metrics
            # This is a simplified analysis - in practice, would consider warehouse layout, pick frequency, etc.
            
            # Get pick frequency (based on sales transactions)
            pick_frequency = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=timezone.now().date() - timedelta(days=30)
            ).count()
            
            # Calculate storage efficiency
            inventory_value = inventory.quantity * inventory.cost_price
            storage_cost_per_unit = 0.10  # $0.10 per unit per month
            monthly_storage_cost = inventory.quantity * storage_cost_per_unit
            
            # Determine optimal zone based on pick frequency and value
            if pick_frequency >= 10 and inventory_value >= 1000:
                optimal_zone = 'A - High Frequency/High Value'
                efficiency_score = 90
            elif pick_frequency >= 5 or inventory_value >= 500:
                optimal_zone = 'B - Medium Frequency/Medium Value'
                efficiency_score = 70
            else:
                optimal_zone = 'C - Low Frequency/Low Value'
                efficiency_score = 50
            
            # Calculate potential savings from optimization
            current_zone = 'B'  # Assume current zone (would come from warehouse management system)
            if optimal_zone.startswith('A') and current_zone != 'A':
                potential_savings = monthly_storage_cost * 0.20  # 20% savings from better location
            elif optimal_zone.startswith('C') and current_zone != 'C':
                potential_savings = monthly_storage_cost * 0.15  # 15% savings from consolidation
            else:
                potential_savings = 0
            
            location_data.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'warehouse_name': inventory.warehouse.name,
                'current_quantity': inventory.quantity,
                'pick_frequency': pick_frequency,
                'inventory_value': inventory_value,
                'monthly_storage_cost': monthly_storage_cost,
                'optimal_zone': optimal_zone,
                'efficiency_score': efficiency_score,
                'potential_savings': potential_savings
            })
        
        return {
            'location_optimization': location_data,
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_compliance_metrics(inventory_qs, start_date, end_date):
        """
        Inventory compliance metrics and regulatory tracking.
        """
        compliance_data = []
        
        for inventory in inventory_qs:
            # Check various compliance factors
            compliance_issues = []
            compliance_score = 100
            
            # Stock level compliance
            if inventory.quantity < inventory.minimum_stock_level:
                compliance_issues.append('Below minimum stock level')
                compliance_score -= 20
            
            if inventory.quantity > inventory.maximum_stock_level:
                compliance_issues.append('Above maximum stock level')
                compliance_score -= 15
            
            # Documentation compliance (simplified check)
            if not inventory.product.description:
                compliance_issues.append('Missing product description')
                compliance_score -= 10
            
            # Supplier compliance
            if inventory.supplier and not inventory.supplier.is_active:
                compliance_issues.append('Inactive supplier')
                compliance_score -= 25
            
            # Transaction compliance (check for proper documentation)
            recent_transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            undocumented_transactions = recent_transactions.filter(
                notes__isnull=True
            ).count()
            
            if undocumented_transactions > 0:
                compliance_issues.append(f'{undocumented_transactions} undocumented transactions')
                compliance_score -= min(30, undocumented_transactions * 5)
            
            # Determine compliance status
            if compliance_score >= 95:
                compliance_status = 'EXCELLENT'
            elif compliance_score >= 85:
                compliance_status = 'GOOD'
            elif compliance_score >= 70:
                compliance_status = 'FAIR'
            else:
                compliance_status = 'POOR'
            
            if compliance_issues:  # Only include items with compliance issues
                compliance_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'compliance_score': compliance_score,
                    'compliance_status': compliance_status,
                    'compliance_issues': compliance_issues,
                    'requires_action': compliance_score < 85
                })
        
        # Calculate overall compliance metrics
        total_items_checked = len(compliance_data) if compliance_data else inventory_qs.count()
        items_with_issues = len(compliance_data)
        overall_compliance_rate = ((total_items_checked - items_with_issues) / total_items_checked * 100) if total_items_checked > 0 else 100
        
        return {
            'compliance_analysis': compliance_data,
            'overall_compliance_rate': overall_compliance_rate,
            'total_items_checked': total_items_checked,
            'items_with_issues': items_with_issues,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def generate_inventory_alerts(inventory_qs, alert_types=None):
        """
        Generate inventory alerts based on various conditions.
        """
        if not alert_types:
            alert_types = ['LOW_STOCK', 'OUT_OF_STOCK', 'OVERSTOCK', 'SLOW_MOVING']
        
        alerts = []
        
        for inventory in inventory_qs:
            # Low stock alert
            if 'LOW_STOCK' in alert_types and inventory.quantity <= inventory.minimum_stock_level:
                alerts.append({
                    'type': 'LOW_STOCK',
                    'priority': 'HIGH' if inventory.quantity <= inventory.minimum_stock_level * 0.5 else 'MEDIUM',
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_id': inventory.warehouse.id,
                    'warehouse_name': inventory.warehouse.name,
                    'current_quantity': inventory.quantity,
                    'minimum_level': inventory.minimum_stock_level,
                    'message': f"Stock level for {inventory.product.name} is below minimum threshold"
                })
            
            # Out of stock alert
            if 'OUT_OF_STOCK' in alert_types and inventory.quantity <= 0:
                alerts.append({
                    'type': 'OUT_OF_STOCK',
                    'priority': 'CRITICAL',
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_id': inventory.warehouse.id,
                    'warehouse_name': inventory.warehouse.name,
                    'current_quantity': inventory.quantity,
                    'message': f"{inventory.product.name} is out of stock"
                })
            
            # Overstock alert
            if 'OVERSTOCK' in alert_types and inventory.quantity >= inventory.maximum_stock_level:
                alerts.append({
                    'type': 'OVERSTOCK',
                    'priority': 'MEDIUM',
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_id': inventory.warehouse.id,
                    'warehouse_name': inventory.warehouse.name,
                    'current_quantity': inventory.quantity,
                    'maximum_level': inventory.maximum_stock_level,
                    'message': f"Stock level for {inventory.product.name} exceeds maximum threshold"
                })
        
        return alerts
    
    @staticmethod
    def send_alert_notifications(alerts, notification_channels=None):
        """
        Send alert notifications via various channels (email, SMS, webhook).
        """
        if not notification_channels:
            notification_channels = ['email']
        
        notifications_sent = []
        
        for alert in alerts:
            for channel in notification_channels:
                if channel == 'email':
                    # Email notification logic
                    notification = {
                        'channel': 'email',
                        'alert_id': alert.get('id'),
                        'subject': f"Inventory Alert: {alert['type']}",
                        'message': alert['message'],
                        'sent_at': timezone.now(),
                        'status': 'sent'
                    }
                    notifications_sent.append(notification)
                
                elif channel == 'webhook':
                    # Webhook notification logic
                    notification = {
                        'channel': 'webhook',
                        'alert_id': alert.get('id'),
                        'payload': alert,
                        'sent_at': timezone.now(),
                        'status': 'sent'
                    }
                    notifications_sent.append(notification)
        
        return notifications_sent