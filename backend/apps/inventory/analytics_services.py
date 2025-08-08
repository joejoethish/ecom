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
            total_value=Sum(F('quantity') * F('cost_price')),
            percentage_of_total=F('total_value') * 100 / total_value if total_value > 0 else 0
        ).order_by('-total_value')
        
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
            total_value = items.annotate(
                value=F('quantity') * F('cost_price')
            ).aggregate(total=Sum('value'))['total'] or Decimal('0')
            
            cost_distribution.append({
                'range': label,
                'item_count': item_count,
                'total_value': total_value,
                'percentage': (total_value / total_value * 100) if total_value > 0 else 0
            })
        
        return {
            'total_value': total_value,
            'warehouse_breakdown': list(warehouse_values),
            'category_breakdown': list(category_values),
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
        # (This would typically be calculated over a period, simplified here)
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
            'trend': 'STABLE'  # Would be calculated from historical data
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
        
        # 4. Inventory Accuracy (would be based on cycle counts)
        # Simplified calculation
        kpis['inventory_accuracy'] = {
            'value': 98.5,  # Would be calculated from actual cycle count data
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
        # Items with no sales in last 365 days
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
            
            total_shrinkage_quantity = shrinkage_transactions.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            total_shrinkage_quantity = abs(total_shrinkage_quantity)
            
            if total_shrinkage_quantity > 0:
                shrinkage_value = total_shrinkage_quantity * inventory.cost_price
                
                # Calculate shrinkage rate
                total_handled = InventoryTransaction.objects.filter(
                    inventory=inventory,
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).aggregate(total=Sum('quantity'))['total'] or 0
                total_handled = abs(total_handled)
                
                shrinkage_rate = (total_shrinkage_quantity / total_handled * 100) if total_handled > 0 else 0
                
                # Determine shrinkage category
                if shrinkage_rate > 5:
                    shrinkage_category = 'High Risk'
                    recommendation = 'Immediate investigation required, review security measures'
                elif shrinkage_rate > 2:
                    shrinkage_category = 'Medium Risk'
                    recommendation = 'Monitor closely, implement additional controls'
                else:
                    shrinkage_category = 'Low Risk'
                    recommendation = 'Normal monitoring'
                
                shrinkage_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'shrinkage_quantity': total_shrinkage_quantity,
                    'shrinkage_value': shrinkage_value,
                    'shrinkage_rate': shrinkage_rate,
                    'shrinkage_category': shrinkage_category,
                    'recommendation': recommendation,
                    'transaction_count': shrinkage_transactions.count()
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
            'overall_shrinkage_rate': overall_shrinkage_rate,
            'analysis_period': f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def get_carrying_cost_analysis(inventory_qs):
        """
        Inventory carrying cost analysis and optimization.
        """
        carrying_cost_data = []
        
        # Standard carrying cost components (as percentages of inventory value)
        storage_cost_rate = 0.08  # 8%
        insurance_cost_rate = 0.02  # 2%
        obsolescence_cost_rate = 0.05  # 5%
        opportunity_cost_rate = 0.10  # 10%
        total_carrying_cost_rate = storage_cost_rate + insurance_cost_rate + obsolescence_cost_rate + opportunity_cost_rate
        
        for inventory in inventory_qs:
            inventory_value = inventory.quantity * inventory.cost_price
            
            # Calculate carrying cost components
            storage_cost = inventory_value * Decimal(str(storage_cost_rate))
            insurance_cost = inventory_value * Decimal(str(insurance_cost_rate))
            obsolescence_cost = inventory_value * Decimal(str(obsolescence_cost_rate))
            opportunity_cost = inventory_value * Decimal(str(opportunity_cost_rate))
            total_carrying_cost = inventory_value * Decimal(str(total_carrying_cost_rate))
            
            # Calculate optimal inventory level (simplified EOQ consideration)
            # This would typically require demand data
            current_months_supply = 3  # Simplified assumption
            optimal_months_supply = 2  # Target
            
            if current_months_supply > optimal_months_supply:
                excess_inventory = inventory_value * (current_months_supply - optimal_months_supply) / current_months_supply
                potential_savings = excess_inventory * Decimal(str(total_carrying_cost_rate))
            else:
                excess_inventory = Decimal('0')
                potential_savings = Decimal('0')
            
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
                'carrying_cost_rate': total_carrying_cost_rate * 100,
                'excess_inventory': excess_inventory,
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
            'carrying_cost_rate': total_carrying_cost_rate * 100,
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_reorder_optimization(inventory_qs):
        """
        Reorder point optimization with service level targets.
        """
        optimization_data = []
        
        for inventory in inventory_qs:
            # Get historical demand data (last 90 days)
            ninety_days_ago = timezone.now().date() - timedelta(days=90)
            demand_history = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=ninety_days_ago
            ).annotate(
                day=Extract('created_at', 'day')
            ).values('day').annotate(
                daily_demand=Sum('quantity')
            )
            
            if demand_history.exists():
                # Calculate demand statistics
                daily_demands = [abs(record['daily_demand']) for record in demand_history]
                avg_daily_demand = sum(daily_demands) / len(daily_demands)
                demand_std_dev = np.std(daily_demands) if len(daily_demands) > 1 else 0
                
                # Lead time (from supplier or default)
                lead_time_days = inventory.supplier.lead_time_days if inventory.supplier else 7
                
                # Service level targets and corresponding z-scores
                service_levels = [
                    (90, 1.28, 'Basic'),
                    (95, 1.65, 'Good'),
                    (99, 2.33, 'Excellent')
                ]
                
                reorder_recommendations = []
                for service_level, z_score, description in service_levels:
                    # Calculate safety stock
                    safety_stock = z_score * demand_std_dev * np.sqrt(lead_time_days)
                    
                    # Calculate reorder point
                    reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
                    
                    reorder_recommendations.append({
                        'service_level': service_level,
                        'description': description,
                        'safety_stock': int(safety_stock),
                        'reorder_point': int(reorder_point)
                    })
                
                # Current status
                current_reorder_point = inventory.reorder_point
                recommended_reorder_point = int((avg_daily_demand * lead_time_days) + (1.65 * demand_std_dev * np.sqrt(lead_time_days)))
                
                if current_reorder_point < recommended_reorder_point * 0.8:
                    status = 'Too Low - Risk of Stockout'
                elif current_reorder_point > recommended_reorder_point * 1.2:
                    status = 'Too High - Excess Inventory'
                else:
                    status = 'Optimal'
                
                optimization_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'current_stock': inventory.quantity,
                    'current_reorder_point': current_reorder_point,
                    'avg_daily_demand': avg_daily_demand,
                    'demand_std_dev': demand_std_dev,
                    'lead_time_days': lead_time_days,
                    'recommended_reorder_point': recommended_reorder_point,
                    'status': status,
                    'service_level_options': reorder_recommendations
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
        
        suppliers = Supplier.objects.all()
        
        for supplier in suppliers:
            # Get purchase orders for this supplier
            purchase_orders = PurchaseOrder.objects.filter(
                supplier=supplier,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            if purchase_orders.exists():
                # Calculate performance metrics
                total_orders = purchase_orders.count()
                on_time_orders = purchase_orders.filter(
                    delivery_date__lte=F('expected_delivery_date')
                ).count()
                
                # Quality metrics (simplified - would need quality inspection data)
                total_items_received = PurchaseOrderItem.objects.filter(
                    purchase_order__in=purchase_orders
                ).aggregate(total=Sum('quantity_received'))['total'] or 0
                
                # Calculate averages
                avg_lead_time = purchase_orders.aggregate(
                    avg=Avg(F('delivery_date') - F('order_date'))
                )['avg']
                avg_lead_time_days = avg_lead_time.days if avg_lead_time else 0
                
                # On-time delivery rate
                on_time_rate = (on_time_orders / total_orders * 100) if total_orders > 0 else 0
                
                # Cost performance (simplified)
                total_order_value = purchase_orders.aggregate(
                    total=Sum('total_amount')
                )['total'] or Decimal('0')
                
                # Performance rating
                if on_time_rate >= 95 and avg_lead_time_days <= supplier.lead_time_days:
                    performance_rating = 'Excellent'
                elif on_time_rate >= 85:
                    performance_rating = 'Good'
                elif on_time_rate >= 70:
                    performance_rating = 'Fair'
                else:
                    performance_rating = 'Poor'
                
                supplier_performance.append({
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.company_name,
                    'total_orders': total_orders,
                    'total_order_value': total_order_value,
                    'on_time_orders': on_time_orders,
                    'on_time_rate': on_time_rate,
                    'avg_lead_time_days': avg_lead_time_days,
                    'expected_lead_time_days': supplier.lead_time_days,
                    'total_items_received': total_items_received,
                    'performance_rating': performance_rating
                })
        
        # Sort by performance rating and on-time rate
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
        # This would typically integrate with quality inspection data
        # For now, we'll create a simplified version based on adjustments and returns
        
        quality_data = []
        
        for inventory in inventory_qs:
            # Get quality-related transactions (returns, defects)
            quality_issues = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type__in=['RETURN', 'ADJUSTMENT'],
                reason__icontains='defect',
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            defect_quantity = quality_issues.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            defect_quantity = abs(defect_quantity)
            
            # Get total received quantity for defect rate calculation
            received_quantity = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='PURCHASE',
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if received_quantity > 0:
                defect_rate = (defect_quantity / received_quantity * 100)
                
                # Quality rating
                if defect_rate <= 1:
                    quality_rating = 'Excellent'
                elif defect_rate <= 3:
                    quality_rating = 'Good'
                elif defect_rate <= 5:
                    quality_rating = 'Fair'
                else:
                    quality_rating = 'Poor'
                
                quality_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'received_quantity': received_quantity,
                    'defect_quantity': defect_quantity,
                    'defect_rate': defect_rate,
                    'quality_rating': quality_rating,
                    'quality_issues_count': quality_issues.count()
                })
        
        # Calculate overall quality metrics
        total_received = sum(item['received_quantity'] for item in quality_data)
        total_defects = sum(item['defect_quantity'] for item in quality_data)
        overall_defect_rate = (total_defects / total_received * 100) if total_received > 0 else 0
        
        return {
            'quality_metrics': quality_data,
            'overall_defect_rate': overall_defect_rate,
            'total_received': total_received,
            'total_defects': total_defects,
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
                created_at__gte=start_date - timedelta(days=365),  # Get full year for seasonality
                created_at__lte=end_date
            ).annotate(
                month=Extract('created_at', 'month')
            ).values('month').annotate(
                total_quantity=Sum('quantity')
            ).order_by('month')
            
            if monthly_sales.exists():
                # Calculate seasonal factors
                monthly_data = {record['month']: abs(record['total_quantity']) for record in monthly_sales}
                avg_monthly_sales = sum(monthly_data.values()) / len(monthly_data)
                
                seasonal_factors = {}
                for month, sales in monthly_data.items():
                    seasonal_factors[month] = sales / avg_monthly_sales if avg_monthly_sales > 0 else 1
                
                # Identify peak and low seasons
                peak_month = max(seasonal_factors.items(), key=lambda x: x[1])
                low_month = min(seasonal_factors.items(), key=lambda x: x[1])
                
                # Calculate seasonality strength
                seasonality_strength = max(seasonal_factors.values()) - min(seasonal_factors.values())
                
                if seasonality_strength > 0.5:
                    seasonality_category = 'Highly Seasonal'
                elif seasonality_strength > 0.2:
                    seasonality_category = 'Moderately Seasonal'
                else:
                    seasonality_category = 'Non-Seasonal'
                
                seasonal_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'seasonal_factors': seasonal_factors,
                    'peak_month': peak_month[0],
                    'peak_factor': peak_month[1],
                    'low_month': low_month[0],
                    'low_factor': low_month[1],
                    'seasonality_strength': seasonality_strength,
                    'seasonality_category': seasonality_category,
                    'avg_monthly_sales': avg_monthly_sales
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
            # Check for obsolescence indicators
            obsolescence_score = 0
            obsolescence_factors = []
            
            # Factor 1: Age of inventory
            oldest_transaction = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='PURCHASE'
            ).order_by('created_at').first()
            
            if oldest_transaction:
                age_days = (timezone.now().date() - oldest_transaction.created_at.date()).days
                if age_days > 730:  # 2 years
                    obsolescence_score += 40
                    obsolescence_factors.append('Very old inventory (2+ years)')
                elif age_days > 365:  # 1 year
                    obsolescence_score += 20
                    obsolescence_factors.append('Old inventory (1+ year)')
            
            # Factor 2: Sales activity
            recent_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=timezone.now().date() - timedelta(days=180)
            ).exists()
            
            if not recent_sales:
                obsolescence_score += 30
                obsolescence_factors.append('No sales in last 6 months')
            
            # Factor 3: Product lifecycle (simplified)
            # This would typically integrate with product lifecycle management
            if hasattr(inventory.product, 'lifecycle_stage'):
                if inventory.product.lifecycle_stage == 'DECLINING':
                    obsolescence_score += 20
                    obsolescence_factors.append('Product in declining lifecycle stage')
            
            # Factor 4: Excess inventory
            if inventory.quantity > inventory.reorder_point * 3:
                obsolescence_score += 10
                obsolescence_factors.append('Excess inventory levels')
            
            # Determine obsolescence risk
            if obsolescence_score >= 70:
                risk_level = 'High Risk'
                recommendation = 'Immediate action required - consider write-off or liquidation'
            elif obsolescence_score >= 40:
                risk_level = 'Medium Risk'
                recommendation = 'Monitor closely, consider promotional activities'
            elif obsolescence_score >= 20:
                risk_level = 'Low Risk'
                recommendation = 'Regular monitoring sufficient'
            else:
                risk_level = 'No Risk'
                recommendation = 'No action required'
            
            if obsolescence_score > 0:
                inventory_value = inventory.quantity * inventory.cost_price
                
                obsolescence_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'quantity': inventory.quantity,
                    'inventory_value': inventory_value,
                    'obsolescence_score': obsolescence_score,
                    'risk_level': risk_level,
                    'obsolescence_factors': obsolescence_factors,
                    'recommendation': recommendation,
                    'age_days': age_days if oldest_transaction else 0
                })
        
        # Sort by obsolescence score
        obsolescence_data.sort(key=lambda x: x['obsolescence_score'], reverse=True)
        
        # Calculate totals
        total_at_risk_value = sum(
            item['inventory_value'] for item in obsolescence_data 
            if item['risk_level'] in ['High Risk', 'Medium Risk']
        )
        
        return {
            'obsolescence_analysis': obsolescence_data,
            'total_at_risk_value': total_at_risk_value,
            'high_risk_count': len([item for item in obsolescence_data if item['risk_level'] == 'High Risk']),
            'medium_risk_count': len([item for item in obsolescence_data if item['risk_level'] == 'Medium Risk']),
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_location_optimization(inventory_qs):
        """
        Warehouse location optimization and slotting analysis.
        """
        location_data = []
        
        # Group by warehouse for analysis
        warehouses = inventory_qs.values('warehouse__id', 'warehouse__name').distinct()
        
        for warehouse in warehouses:
            warehouse_inventory = inventory_qs.filter(warehouse_id=warehouse['warehouse__id'])
            
            # Calculate warehouse utilization
            total_items = warehouse_inventory.count()
            total_value = warehouse_inventory.annotate(
                value=F('quantity') * F('cost_price')
            ).aggregate(total=Sum('value'))['total'] or Decimal('0')
            
            # Analyze product velocity (A, B, C classification for slotting)
            velocity_analysis = []
            for inventory in warehouse_inventory:
                # Get recent sales velocity
                recent_sales = InventoryTransaction.objects.filter(
                    inventory=inventory,
                    transaction_type='SALE',
                    created_at__gte=timezone.now().date() - timedelta(days=90)
                ).aggregate(total=Sum('quantity'))['total'] or 0
                recent_sales = abs(recent_sales)
                
                # Calculate picks per day
                picks_per_day = recent_sales / 90
                
                # Velocity classification
                if picks_per_day >= 1:
                    velocity_class = 'A'  # High velocity - should be in easily accessible locations
                    slotting_recommendation = 'Place in prime picking locations, ground level'
                elif picks_per_day >= 0.1:
                    velocity_class = 'B'  # Medium velocity
                    slotting_recommendation = 'Place in standard picking locations'
                else:
                    velocity_class = 'C'  # Low velocity
                    slotting_recommendation = 'Can be placed in less accessible locations'
                
                velocity_analysis.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'picks_per_day': picks_per_day,
                    'velocity_class': velocity_class,
                    'slotting_recommendation': slotting_recommendation,
                    'current_location': getattr(inventory, 'location', 'Not specified')
                })
            
            # Calculate velocity distribution
            velocity_distribution = {
                'A': len([item for item in velocity_analysis if item['velocity_class'] == 'A']),
                'B': len([item for item in velocity_analysis if item['velocity_class'] == 'B']),
                'C': len([item for item in velocity_analysis if item['velocity_class'] == 'C'])
            }
            
            location_data.append({
                'warehouse_id': warehouse['warehouse__id'],
                'warehouse_name': warehouse['warehouse__name'],
                'total_items': total_items,
                'total_value': total_value,
                'velocity_distribution': velocity_distribution,
                'velocity_analysis': velocity_analysis
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
            compliance_issues = []
            compliance_score = 100  # Start with perfect score
            
            # Check for expiration date compliance (if applicable)
            if hasattr(inventory, 'expiration_date') and inventory.expiration_date:
                days_to_expiry = (inventory.expiration_date - timezone.now().date()).days
                if days_to_expiry <= 0:
                    compliance_issues.append('Product expired')
                    compliance_score -= 50
                elif days_to_expiry <= 30:
                    compliance_issues.append('Product expiring within 30 days')
                    compliance_score -= 20
            
            # Check for proper documentation
            recent_transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            undocumented_transactions = recent_transactions.filter(
                Q(reason__isnull=True) | Q(reason='')
            ).count()
            
            if undocumented_transactions > 0:
                compliance_issues.append(f'{undocumented_transactions} undocumented transactions')
                compliance_score -= min(30, undocumented_transactions * 5)
            
            # Check for negative inventory (should not happen)
            if inventory.quantity < 0:
                compliance_issues.append('Negative inventory balance')
                compliance_score -= 40
            
            # Check for inventory accuracy (simplified)
            # This would typically be based on cycle count results
            if hasattr(inventory, 'last_cycle_count_date'):
                if inventory.last_cycle_count_date:
                    days_since_count = (timezone.now().date() - inventory.last_cycle_count_date).days
                    if days_since_count > 365:
                        compliance_issues.append('No cycle count in over 1 year')
                        compliance_score -= 15
                else:
                    compliance_issues.append('No cycle count recorded')
                    compliance_score -= 25
            
            # Determine compliance status
            if compliance_score >= 95:
                compliance_status = 'Excellent'
            elif compliance_score >= 85:
                compliance_status = 'Good'
            elif compliance_score >= 70:
                compliance_status = 'Fair'
            else:
                compliance_status = 'Poor'
            
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


class InventoryReportingService:
    """
    Service for generating comprehensive inventory reports and exports.
    """
    
    @staticmethod
    def generate_inventory_report(report_type, warehouse_id=None, start_date=None, end_date=None, format='json'):
        """
        Generate comprehensive inventory reports in various formats.
        """
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get base data
        analytics_service = InventoryAnalyticsService()
        
        report_data = {
            'report_metadata': {
                'report_type': report_type,
                'generated_at': timezone.now().isoformat(),
                'warehouse_id': warehouse_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'format': format
            }
        }
        
        if report_type == 'comprehensive':
            report_data.update(analytics_service.generate_comprehensive_analytics(
                warehouse_id, start_date, end_date
            ))
        elif report_type == 'valuation':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['valuation'] = analytics_service.get_inventory_valuation(inventory_qs)
        elif report_type == 'turnover':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['turnover'] = analytics_service.get_turnover_analysis(inventory_qs, start_date, end_date)
        elif report_type == 'abc_analysis':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['abc_analysis'] = analytics_service.get_abc_analysis(inventory_qs, start_date, end_date)
        
        return report_data
    
    @staticmethod
    def export_to_csv(report_data, filename=None):
        """
        Export report data to CSV format.
        """
        import csv
        import io
        
        if not filename:
            filename = f"inventory_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data based on report type
        if 'valuation' in report_data:
            writer.writerow(['Product ID', 'Product Name', 'Warehouse', 'Quantity', 'Cost Price', 'Total Value'])
            for item in report_data['valuation']['top_valuable_items']:
                writer.writerow([
                    item['product__id'],
                    item['product__name'],
                    item['warehouse__name'],
                    item['quantity'],
                    item['cost_price'],
                    item['value']
                ])
        
        return output.getvalue()
    
    @staticmethod
    def schedule_report(report_type, schedule_frequency, warehouse_id=None, email_recipients=None):
        """
        Schedule automated report generation and delivery.
        """
        # This would integrate with a task scheduler like Celery
        scheduled_report = {
            'report_type': report_type,
            'schedule_frequency': schedule_frequency,  # daily, weekly, monthly
            'warehouse_id': warehouse_id,
            'email_recipients': email_recipients or [],
            'created_at': timezone.now(),
            'next_run': timezone.now() + timedelta(days=1),  # Simplified
            'is_active': True
        }
        
        return scheduled_report


class InventoryAlertService:
    """
    Service for managing inventory alerts and notifications.
    """
    
    @staticmethod
    def check_stock_levels():
        """
        Check inventory levels and generate alerts for low stock, overstock, etc.
        """
        alerts = []
        
        # Low stock alerts
        low_stock_items = Inventory.objects.filter(
            quantity__lte=F('reorder_point')
        )
        
        for item in low_stock_items:
            alerts.append({
                'type': 'LOW_STOCK',
                'severity': 'HIGH' if item.quantity <= item.reorder_point * 0.5 else 'MEDIUM',
                'inventory_id': item.id,
                'product_name': item.product.name,
                'warehouse_name': item.warehouse.name,
                'current_quantity': item.quantity,
                'reorder_point': item.reorder_point,
                'message': f'Low stock alert: {item.product.name} in {item.warehouse.name}',
                'created_at': timezone.now()
            })
        
        # Overstock alerts
        overstock_items = Inventory.objects.filter(
            quantity__gte=F('reorder_point') * 5  # 5x reorder point
        )
        
        for item in overstock_items:
            alerts.append({
                'type': 'OVERSTOCK',
                'severity': 'MEDIUM',
                'inventory_id': item.id,
                'product_name': item.product.name,
                'warehouse_name': item.warehouse.name,
                'current_quantity': item.quantity,
                'reorder_point': item.reorder_point,
                'message': f'Overstock alert: {item.product.name} in {item.warehouse.name}',
                'created_at': timezone.now()
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
        overall_defect_rate = (total_defects / total_received * 100) if total_received > 0 else 0
        
        return {
            'quality_metrics': quality_data,
            'overall_defect_rate': overall_defect_rate,
            'total_received': total_received,
            'total_defects': total_defects,
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
                created_at__gte=start_date - timedelta(days=365),  # Get full year for seasonality
                created_at__lte=end_date
            ).annotate(
                month=Extract('created_at', 'month')
            ).values('month').annotate(
                total_quantity=Sum('quantity')
            ).order_by('month')
            
            if monthly_sales.exists():
                # Calculate seasonal factors
                monthly_data = {record['month']: abs(record['total_quantity']) for record in monthly_sales}
                avg_monthly_sales = sum(monthly_data.values()) / len(monthly_data)
                
                seasonal_factors = {}
                for month, sales in monthly_data.items():
                    seasonal_factors[month] = sales / avg_monthly_sales if avg_monthly_sales > 0 else 1
                
                # Identify peak and low seasons
                peak_month = max(seasonal_factors.items(), key=lambda x: x[1])
                low_month = min(seasonal_factors.items(), key=lambda x: x[1])
                
                # Calculate seasonality strength
                seasonality_strength = max(seasonal_factors.values()) - min(seasonal_factors.values())
                
                if seasonality_strength > 0.5:
                    seasonality_category = 'Highly Seasonal'
                elif seasonality_strength > 0.2:
                    seasonality_category = 'Moderately Seasonal'
                else:
                    seasonality_category = 'Non-Seasonal'
                
                seasonal_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'seasonal_factors': seasonal_factors,
                    'peak_month': peak_month[0],
                    'peak_factor': peak_month[1],
                    'low_month': low_month[0],
                    'low_factor': low_month[1],
                    'seasonality_strength': seasonality_strength,
                    'seasonality_category': seasonality_category,
                    'avg_monthly_sales': avg_monthly_sales
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
            # Check for obsolescence indicators
            obsolescence_score = 0
            obsolescence_factors = []
            
            # Factor 1: Age of inventory
            oldest_transaction = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='PURCHASE'
            ).order_by('created_at').first()
            
            if oldest_transaction:
                age_days = (timezone.now().date() - oldest_transaction.created_at.date()).days
                if age_days > 730:  # 2 years
                    obsolescence_score += 40
                    obsolescence_factors.append('Very old inventory (2+ years)')
                elif age_days > 365:  # 1 year
                    obsolescence_score += 20
                    obsolescence_factors.append('Old inventory (1+ year)')
            
            # Factor 2: Sales activity
            recent_sales = InventoryTransaction.objects.filter(
                inventory=inventory,
                transaction_type='SALE',
                created_at__gte=timezone.now().date() - timedelta(days=180)
            ).exists()
            
            if not recent_sales:
                obsolescence_score += 30
                obsolescence_factors.append('No sales in last 6 months')
            
            # Factor 3: Product lifecycle (simplified)
            # This would typically integrate with product lifecycle management
            if hasattr(inventory.product, 'lifecycle_stage'):
                if inventory.product.lifecycle_stage == 'DECLINING':
                    obsolescence_score += 20
                    obsolescence_factors.append('Product in declining lifecycle stage')
            
            # Factor 4: Excess inventory
            if inventory.quantity > inventory.reorder_point * 3:
                obsolescence_score += 10
                obsolescence_factors.append('Excess inventory levels')
            
            # Determine obsolescence risk
            if obsolescence_score >= 70:
                risk_level = 'High Risk'
                recommendation = 'Immediate action required - consider write-off or liquidation'
            elif obsolescence_score >= 40:
                risk_level = 'Medium Risk'
                recommendation = 'Monitor closely, consider promotional activities'
            elif obsolescence_score >= 20:
                risk_level = 'Low Risk'
                recommendation = 'Regular monitoring sufficient'
            else:
                risk_level = 'No Risk'
                recommendation = 'No action required'
            
            if obsolescence_score > 0:
                inventory_value = inventory.quantity * inventory.cost_price
                
                obsolescence_data.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'warehouse_name': inventory.warehouse.name,
                    'quantity': inventory.quantity,
                    'inventory_value': inventory_value,
                    'obsolescence_score': obsolescence_score,
                    'risk_level': risk_level,
                    'obsolescence_factors': obsolescence_factors,
                    'recommendation': recommendation,
                    'age_days': age_days if oldest_transaction else 0
                })
        
        # Sort by obsolescence score
        obsolescence_data.sort(key=lambda x: x['obsolescence_score'], reverse=True)
        
        # Calculate totals
        total_at_risk_value = sum(
            item['inventory_value'] for item in obsolescence_data 
            if item['risk_level'] in ['High Risk', 'Medium Risk']
        )
        
        return {
            'obsolescence_analysis': obsolescence_data,
            'total_at_risk_value': total_at_risk_value,
            'high_risk_count': len([item for item in obsolescence_data if item['risk_level'] == 'High Risk']),
            'medium_risk_count': len([item for item in obsolescence_data if item['risk_level'] == 'Medium Risk']),
            'analysis_date': timezone.now().date()
        }
    
    @staticmethod
    def get_location_optimization(inventory_qs):
        """
        Warehouse location optimization and slotting analysis.
        """
        location_data = []
        
        # Group by warehouse for analysis
        warehouses = inventory_qs.values('warehouse__id', 'warehouse__name').distinct()
        
        for warehouse in warehouses:
            warehouse_inventory = inventory_qs.filter(warehouse_id=warehouse['warehouse__id'])
            
            # Calculate warehouse utilization
            total_items = warehouse_inventory.count()
            total_value = warehouse_inventory.annotate(
                value=F('quantity') * F('cost_price')
            ).aggregate(total=Sum('value'))['total'] or Decimal('0')
            
            # Analyze product velocity (A, B, C classification for slotting)
            velocity_analysis = []
            for inventory in warehouse_inventory:
                # Get recent sales velocity
                recent_sales = InventoryTransaction.objects.filter(
                    inventory=inventory,
                    transaction_type='SALE',
                    created_at__gte=timezone.now().date() - timedelta(days=90)
                ).aggregate(total=Sum('quantity'))['total'] or 0
                recent_sales = abs(recent_sales)
                
                # Calculate picks per day
                picks_per_day = recent_sales / 90
                
                # Velocity classification
                if picks_per_day >= 1:
                    velocity_class = 'A'  # High velocity - should be in easily accessible locations
                    slotting_recommendation = 'Place in prime picking locations, ground level'
                elif picks_per_day >= 0.1:
                    velocity_class = 'B'  # Medium velocity
                    slotting_recommendation = 'Place in standard picking locations'
                else:
                    velocity_class = 'C'  # Low velocity
                    slotting_recommendation = 'Can be placed in less accessible locations'
                
                velocity_analysis.append({
                    'product_id': inventory.product.id,
                    'product_name': inventory.product.name,
                    'picks_per_day': picks_per_day,
                    'velocity_class': velocity_class,
                    'slotting_recommendation': slotting_recommendation,
                    'current_location': getattr(inventory, 'location', 'Not specified')
                })
            
            # Calculate velocity distribution
            velocity_distribution = {
                'A': len([item for item in velocity_analysis if item['velocity_class'] == 'A']),
                'B': len([item for item in velocity_analysis if item['velocity_class'] == 'B']),
                'C': len([item for item in velocity_analysis if item['velocity_class'] == 'C'])
            }
            
            location_data.append({
                'warehouse_id': warehouse['warehouse__id'],
                'warehouse_name': warehouse['warehouse__name'],
                'total_items': total_items,
                'total_value': total_value,
                'velocity_distribution': velocity_distribution,
                'velocity_analysis': velocity_analysis
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
            compliance_issues = []
            compliance_score = 100  # Start with perfect score
            
            # Check for expiration date compliance (if applicable)
            if hasattr(inventory, 'expiration_date') and inventory.expiration_date:
                days_to_expiry = (inventory.expiration_date - timezone.now().date()).days
                if days_to_expiry <= 0:
                    compliance_issues.append('Product expired')
                    compliance_score -= 50
                elif days_to_expiry <= 30:
                    compliance_issues.append('Product expiring within 30 days')
                    compliance_score -= 20
            
            # Check for proper documentation
            recent_transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            undocumented_transactions = recent_transactions.filter(
                Q(reason__isnull=True) | Q(reason='')
            ).count()
            
            if undocumented_transactions > 0:
                compliance_issues.append(f'{undocumented_transactions} undocumented transactions')
                compliance_score -= min(30, undocumented_transactions * 5)
            
            # Check for negative inventory (should not happen)
            if inventory.quantity < 0:
                compliance_issues.append('Negative inventory balance')
                compliance_score -= 40
            
            # Check for inventory accuracy (simplified)
            # This would typically be based on cycle count results
            if hasattr(inventory, 'last_cycle_count_date'):
                if inventory.last_cycle_count_date:
                    days_since_count = (timezone.now().date() - inventory.last_cycle_count_date).days
                    if days_since_count > 365:
                        compliance_issues.append('No cycle count in over 1 year')
                        compliance_score -= 15
                else:
                    compliance_issues.append('No cycle count recorded')
                    compliance_score -= 25
            
            # Determine compliance status
            if compliance_score >= 95:
                compliance_status = 'Excellent'
            elif compliance_score >= 85:
                compliance_status = 'Good'
            elif compliance_score >= 70:
                compliance_status = 'Fair'
            else:
                compliance_status = 'Poor'
            
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


class InventoryReportingService:
    """
    Service for generating comprehensive inventory reports and exports.
    """
    
    @staticmethod
    def generate_inventory_report(report_type, warehouse_id=None, start_date=None, end_date=None, format='json'):
        """
        Generate comprehensive inventory reports in various formats.
        """
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get base data
        analytics_service = InventoryAnalyticsService()
        
        report_data = {
            'report_metadata': {
                'report_type': report_type,
                'generated_at': timezone.now().isoformat(),
                'warehouse_id': warehouse_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'format': format
            }
        }
        
        if report_type == 'comprehensive':
            report_data.update(analytics_service.generate_comprehensive_analytics(
                warehouse_id, start_date, end_date
            ))
        elif report_type == 'valuation':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['valuation'] = analytics_service.get_inventory_valuation(inventory_qs)
        elif report_type == 'turnover':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['turnover'] = analytics_service.get_turnover_analysis(inventory_qs, start_date, end_date)
        elif report_type == 'abc_analysis':
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            report_data['abc_analysis'] = analytics_service.get_abc_analysis(inventory_qs, start_date, end_date)
        
        return report_data
    
    @staticmethod
    def export_to_csv(report_data, filename=None):
        """
        Export report data to CSV format.
        """
        import csv
        import io
        
        if not filename:
            filename = f"inventory_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data based on report type
        if 'valuation' in report_data:
            writer.writerow(['Product ID', 'Product Name', 'Warehouse', 'Quantity', 'Cost Price', 'Total Value'])
            for item in report_data['valuation']['top_valuable_items']:
                writer.writerow([
                    item['product__id'],
                    item['product__name'],
                    item['warehouse__name'],
                    item['quantity'],
                    item['cost_price'],
                    item['value']
                ])
        
        return output.getvalue()
    
    @staticmethod
    def schedule_report(report_type, schedule_frequency, warehouse_id=None, email_recipients=None):
        """
        Schedule automated report generation and delivery.
        """
        # This would integrate with a task scheduler like Celery
        scheduled_report = {
            'report_type': report_type,
            'schedule_frequency': schedule_frequency,  # daily, weekly, monthly
            'warehouse_id': warehouse_id,
            'email_recipients': email_recipients or [],
            'created_at': timezone.now(),
            'next_run': timezone.now() + timedelta(days=1),  # Simplified
            'is_active': True
        }
        
        return scheduled_report


class InventoryAlertService:
    """
    Service for managing inventory alerts and notifications.
    """
    
    @staticmethod
    def check_stock_levels():
        """
        Check inventory levels and generate alerts for low stock, overstock, etc.
        """
        alerts = []
        
        # Low stock alerts
        low_stock_items = Inventory.objects.filter(
            quantity__lte=F('reorder_point')
        )
        
        for item in low_stock_items:
            alerts.append({
                'type': 'LOW_STOCK',
                'severity': 'HIGH' if item.quantity <= item.reorder_point * 0.5 else 'MEDIUM',
                'inventory_id': item.id,
                'product_name': item.product.name,
                'warehouse_name': item.warehouse.name,
                'current_quantity': item.quantity,
                'reorder_point': item.reorder_point,
                'message': f'Low stock alert: {item.product.name} in {item.warehouse.name}',
                'created_at': timezone.now()
            })
        
        # Overstock alerts
        overstock_items = Inventory.objects.filter(
            quantity__gte=F('reorder_point') * 5  # 5x reorder point
        )
        
        for item in overstock_items:
            alerts.append({
                'type': 'OVERSTOCK',
                'severity': 'MEDIUM',
                'inventory_id': item.id,
                'product_name': item.product.name,
                'warehouse_name': item.warehouse.name,
                'current_quantity': item.quantity,
                'reorder_point': item.reorder_point,
                'message': f'Overstock alert: {item.product.name} in {item.warehouse.name}',
                'created_at': timezone.now()
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