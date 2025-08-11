from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta, date
import csv
import json

from .models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)
from .analytics_models import (
    InventoryAnalytics, InventoryKPI, InventoryForecast, 
    InventoryAlert, CycleCount, CycleCountItem
)
from .analytics_services import InventoryAnalyticsService
from .serializers import (
    InventorySerializer, InventoryAnalyticsSerializer,
    InventoryKPISerializer, InventoryForecastSerializer,
    InventoryAlertSerializer, CycleCountSerializer
)


class InventoryAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Comprehensive inventory analytics and reporting API.
    """
    queryset = InventoryAnalytics.objects.all()
    serializer_class = InventoryAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['analysis_type', 'warehouse', 'product']
    search_fields = ['product__name', 'warehouse__name']
    ordering_fields = ['analysis_date', 'turnover_ratio', 'revenue_contribution']
    ordering = ['-analysis_date']

    @action(detail=False, methods=['get'])
    def comprehensive_dashboard(self, request):
        """
        Get comprehensive inventory analytics dashboard data.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            analytics_data = InventoryAnalyticsService.generate_comprehensive_analytics(
                warehouse_id=warehouse_id,
                start_date=start_date,
                end_date=end_date
            )
            return Response(analytics_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def inventory_valuation(self, request):
        """
        Real-time inventory valuation and cost analysis.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            valuation_data = InventoryAnalyticsService.get_inventory_valuation(inventory_qs)
            return Response(valuation_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def turnover_analysis(self, request):
        """
        Inventory turnover analysis with optimization recommendations.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            turnover_data = InventoryAnalyticsService.get_turnover_analysis(
                inventory_qs, start_date, end_date
            )
            return Response(turnover_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def abc_analysis(self, request):
        """
        ABC analysis for inventory classification and management.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            abc_data = InventoryAnalyticsService.get_abc_analysis(
                inventory_qs, start_date, end_date
            )
            return Response(abc_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def slow_moving_analysis(self, request):
        """
        Slow-moving and dead stock identification and management.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            slow_moving_data = InventoryAnalyticsService.get_slow_moving_analysis(
                inventory_qs, start_date, end_date
            )
            return Response(slow_moving_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def aging_analysis(self, request):
        """
        Inventory aging reports with action recommendations.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            aging_data = InventoryAnalyticsService.get_aging_analysis(inventory_qs)
            return Response(aging_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def forecasting_data(self, request):
        """
        Inventory forecasting with demand planning integration.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=365)  # Get more history for forecasting
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            forecasting_data = InventoryAnalyticsService.get_forecasting_data(
                inventory_qs, start_date, end_date
            )
            return Response(forecasting_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def kpi_dashboard(self, request):
        """
        Inventory performance dashboards with KPI tracking.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        measurement_date = request.query_params.get('measurement_date')
        
        if measurement_date:
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        
        try:
            kpi_data = InventoryAnalyticsService.get_kpi_dashboard(
                warehouse_id=warehouse_id,
                measurement_date=measurement_date
            )
            return Response(kpi_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def shrinkage_analysis(self, request):
        """
        Inventory shrinkage analysis and loss prevention.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            shrinkage_data = InventoryAnalyticsService.get_shrinkage_analysis(
                inventory_qs, start_date, end_date
            )
            return Response(shrinkage_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def carrying_cost_analysis(self, request):
        """
        Inventory carrying cost analysis and optimization.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            carrying_cost_data = InventoryAnalyticsService.get_carrying_cost_analysis(inventory_qs)
            return Response(carrying_cost_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def reorder_optimization(self, request):
        """
        Inventory reorder point optimization with service level targets.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            reorder_data = InventoryAnalyticsService.get_reorder_optimization(inventory_qs)
            return Response(reorder_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def supplier_performance(self, request):
        """
        Inventory supplier performance analysis.
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            supplier_data = InventoryAnalyticsService.get_supplier_performance(start_date, end_date)
            return Response(supplier_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def quality_metrics(self, request):
        """
        Inventory quality metrics and defect tracking.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            quality_data = InventoryAnalyticsService.get_quality_metrics(
                inventory_qs, start_date, end_date
            )
            return Response(quality_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def seasonal_analysis(self, request):
        """
        Inventory seasonal analysis and planning.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=730)  # 2 years for seasonal analysis
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            seasonal_data = InventoryAnalyticsService.get_seasonal_analysis(
                inventory_qs, start_date, end_date
            )
            return Response(seasonal_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def obsolescence_analysis(self, request):
        """
        Inventory obsolescence management and write-offs.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            obsolescence_data = InventoryAnalyticsService.get_obsolescence_analysis(inventory_qs)
            return Response(obsolescence_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def location_optimization(self, request):
        """
        Inventory location optimization and slotting.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            location_data = InventoryAnalyticsService.get_location_optimization(inventory_qs)
            return Response(location_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def compliance_metrics(self, request):
        """
        Inventory compliance reporting for regulatory requirements.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        try:
            inventory_qs = Inventory.objects.all()
            if warehouse_id:
                inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            
            compliance_data = InventoryAnalyticsService.get_compliance_metrics(
                inventory_qs, start_date, end_date
            )
            return Response(compliance_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def export_analytics_csv(self, request):
        """
        Export inventory analytics data to CSV.
        """
        analysis_type = request.query_params.get('analysis_type', 'comprehensive')
        warehouse_id = request.query_params.get('warehouse_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            # Get analytics data based on type
            if analysis_type == 'comprehensive':
                data = InventoryAnalyticsService.generate_comprehensive_analytics(
                    warehouse_id=warehouse_id,
                    start_date=start_date,
                    end_date=end_date
                )
            elif analysis_type == 'turnover':
                inventory_qs = Inventory.objects.all()
                if warehouse_id:
                    inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
                data = InventoryAnalyticsService.get_turnover_analysis(
                    inventory_qs, start_date or timezone.now().date() - timedelta(days=90), 
                    end_date or timezone.now().date()
                )
            elif analysis_type == 'abc':
                inventory_qs = Inventory.objects.all()
                if warehouse_id:
                    inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
                data = InventoryAnalyticsService.get_abc_analysis(
                    inventory_qs, start_date or timezone.now().date() - timedelta(days=90), 
                    end_date or timezone.now().date()
                )
            else:
                return Response({'error': 'Invalid analysis type'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="inventory_analytics_{analysis_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
            
            # Create CSV writer
            writer = csv.writer(response)
            
            # Write data based on analysis type
            if analysis_type == 'turnover' and 'product_turnover' in data:
                writer.writerow([
                    'Product ID', 'Product Name', 'Warehouse', 'Current Inventory Value',
                    'COGS', 'Turnover Ratio', 'Days of Supply', 'Category', 'Recommendation'
                ])
                for item in data['product_turnover']:
                    writer.writerow([
                        item['product_id'], item['product_name'], item['warehouse_name'],
                        item['current_inventory_value'], item['cogs'], item['turnover_ratio'],
                        item['days_of_supply'], item['turnover_category'], item['recommendation']
                    ])
            elif analysis_type == 'abc' and 'abc_classification' in data:
                writer.writerow([
                    'Product ID', 'Product Name', 'Warehouse', 'Sales Value',
                    'Current Inventory Value', 'Cumulative %', 'ABC Category', 'Management Strategy'
                ])
                for item in data['abc_classification']:
                    writer.writerow([
                        item['product_id'], item['product_name'], item['warehouse_name'],
                        item['sales_value'], item['current_inventory_value'],
                        item['cumulative_percentage'], item['abc_category'], item['management_strategy']
                    ])
            else:
                # Generic JSON export for comprehensive data
                writer.writerow(['Analytics Data'])
                writer.writerow([json.dumps(data, default=str)])
            
            return response
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InventoryKPIViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for inventory KPIs and performance metrics.
    """
    queryset = InventoryKPI.objects.all()
    serializer_class = InventoryKPISerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['kpi_type', 'warehouse', 'performance_status']
    search_fields = ['notes']
    ordering_fields = ['measurement_date', 'value', 'target_value']
    ordering = ['-measurement_date']

    @action(detail=False, methods=['get'])
    def kpi_trends(self, request):
        """
        Get KPI trends over time.
        """
        kpi_type = request.query_params.get('kpi_type')
        warehouse_id = request.query_params.get('warehouse_id')
        days = int(request.query_params.get('days', 30))
        
        if not kpi_type:
            return Response({'error': 'kpi_type parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            kpi_type=kpi_type,
            measurement_date__gte=start_date,
            measurement_date__lte=end_date
        )
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for inventory forecasts.
    """
    queryset = InventoryForecast.objects.all()
    serializer_class = InventoryForecastSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['forecast_method', 'warehouse', 'product']
    search_fields = ['product__name', 'warehouse__name']
    ordering_fields = ['forecast_date', 'forecasted_demand', 'forecast_error']
    ordering = ['-forecast_date']

    @action(detail=False, methods=['get'])
    def accuracy_analysis(self, request):
        """
        Analyze forecast accuracy across different methods and products.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        days = int(request.query_params.get('days', 90))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            forecast_date__gte=start_date,
            forecast_date__lte=end_date,
            actual_demand__isnull=False
        )
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Calculate accuracy by method
        accuracy_by_method = {}
        for forecast in queryset:
            method = forecast.forecast_method
            if method not in accuracy_by_method:
                accuracy_by_method[method] = {'total_error': 0, 'count': 0, 'forecasts': []}
            
            if forecast.absolute_percentage_error:
                accuracy_by_method[method]['total_error'] += float(forecast.absolute_percentage_error)
                accuracy_by_method[method]['count'] += 1
                accuracy_by_method[method]['forecasts'].append({
                    'product_name': forecast.product.name,
                    'forecasted': forecast.forecasted_demand,
                    'actual': forecast.actual_demand,
                    'error': float(forecast.absolute_percentage_error)
                })
        
        # Calculate average accuracy
        for method in accuracy_by_method:
            if accuracy_by_method[method]['count'] > 0:
                accuracy_by_method[method]['average_accuracy'] = 100 - (
                    accuracy_by_method[method]['total_error'] / accuracy_by_method[method]['count']
                )
            else:
                accuracy_by_method[method]['average_accuracy'] = 0
        
        return Response(accuracy_by_method, status=status.HTTP_200_OK)


class InventoryAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint for inventory alerts and notifications.
    """
    queryset = InventoryAlert.objects.all()
    serializer_class = InventoryAlertSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'priority', 'status', 'warehouse', 'product']
    search_fields = ['title', 'message', 'product__name']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Acknowledge an inventory alert.
        """
        alert = self.get_object()
        alert.status = 'ACKNOWLEDGED'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve an inventory alert.
        """
        alert = self.get_object()
        action_taken = request.data.get('action_taken', '')
        
        alert.status = 'RESOLVED'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.action_taken = action_taken
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """
        Get all active alerts with priority sorting.
        """
        priority_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4}
        
        active_alerts = self.get_queryset().filter(status='ACTIVE')
        
        # Sort by priority and creation date
        sorted_alerts = sorted(
            active_alerts,
            key=lambda x: (priority_order.get(x.priority, 5), x.created_at),
            reverse=True
        )
        
        serializer = self.get_serializer(sorted_alerts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CycleCountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for cycle counting and accuracy tracking.
    """
    queryset = CycleCount.objects.all()
    serializer_class = CycleCountSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'warehouse', 'assigned_to']
    search_fields = ['count_name', 'notes']
    ordering_fields = ['scheduled_date', 'created_at', 'accuracy_percentage']
    ordering = ['-scheduled_date']

    @action(detail=True, methods=['post'])
    def start_count(self, request, pk=None):
        """
        Start a cycle count.
        """
        cycle_count = self.get_object()
        
        if cycle_count.status != 'PLANNED':
            return Response(
                {'error': 'Cycle count must be in PLANNED status to start'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cycle_count.status = 'IN_PROGRESS'
        cycle_count.started_at = timezone.now()
        cycle_count.save()
        
        serializer = self.get_serializer(cycle_count)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete_count(self, request, pk=None):
        """
        Complete a cycle count and calculate accuracy.
        """
        cycle_count = self.get_object()
        
        if cycle_count.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Cycle count must be in IN_PROGRESS status to complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate accuracy and variance summary
        count_items = cycle_count.items.all()
        total_items = count_items.count()
        items_with_variances = count_items.exclude(variance_quantity=0).count()
        total_variance_value = sum(item.variance_value for item in count_items)
        
        accuracy_percentage = ((total_items - items_with_variances) / total_items * 100) if total_items > 0 else 100
        
        cycle_count.status = 'COMPLETED'
        cycle_count.completed_at = timezone.now()
        cycle_count.total_items_counted = total_items
        cycle_count.items_with_variances = items_with_variances
        cycle_count.total_variance_value = total_variance_value
        cycle_count.accuracy_percentage = accuracy_percentage
        cycle_count.save()
        
        serializer = self.get_serializer(cycle_count)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def accuracy_trends(self, request):
        """
        Get cycle count accuracy trends over time.
        """
        warehouse_id = request.query_params.get('warehouse_id')
        days = int(request.query_params.get('days', 90))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            status='COMPLETED',
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date
        )
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        accuracy_data = []
        for count in queryset.order_by('completed_at'):
            accuracy_data.append({
                'count_name': count.count_name,
                'completed_date': count.completed_at.date(),
                'accuracy_percentage': float(count.accuracy_percentage) if count.accuracy_percentage else 0,
                'total_items': count.total_items_counted,
                'items_with_variances': count.items_with_variances,
                'total_variance_value': float(count.total_variance_value)
            })
        
        return Response(accuracy_data, status=status.HTTP_200_OK)