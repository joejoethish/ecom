from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField
from django.utils import timezone
from django.http import HttpResponse
import csv
import io
import json
from datetime import datetime

from .models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)
from .serializers import (
    InventorySerializer, InventoryTransactionSerializer,
    SupplierSerializer, WarehouseSerializer,
    PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    PurchaseOrderCreateSerializer, PurchaseOrderReceiveSerializer,
    InventoryAdjustmentSerializer, InventoryTransferSerializer,
    BulkInventoryUpdateSerializer, InventoryAlertSettingsSerializer,
    InventoryReportSerializer
)
from .services import InventoryService, PurchaseOrderService


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing suppliers.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'contact_person', 'email', 'phone']
    ordering_fields = ['name', 'reliability_rating', 'lead_time_days', 'created_at']
    ordering = ['name']


class WarehouseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing warehouses.
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'location', 'contact_person']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class InventoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['warehouse', 'supplier']
    search_fields = ['product__name', 'product__sku', 'warehouse__name']
    ordering_fields = ['product__name', 'quantity', 'last_restocked', 'created_at']
    ordering = ['product__name']
    
    def get_queryset(self):
        """
        Customize queryset to include additional filters.
        """
        queryset = super().get_queryset()
        
        # Filter by stock status
        stock_status = self.request.query_params.get('stock_status', None)
        if stock_status:
            if stock_status == 'low_stock':
                queryset = queryset.filter(quantity__lte=F('reorder_point'))
            elif stock_status == 'out_of_stock':
                queryset = queryset.filter(quantity__lte=0)
            elif stock_status == 'in_stock':
                queryset = queryset.filter(
                    quantity__gt=F('reorder_point'),
                    quantity__lt=F('maximum_stock_level')
                )
            elif stock_status == 'overstock':
                queryset = queryset.filter(quantity__gte=F('maximum_stock_level'))
        
        # Filter by product
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """
        Get summary of inventory stock levels.
        """
        total_products = Inventory.objects.values('product').distinct().count()
        total_quantity = Inventory.objects.aggregate(total=Sum('quantity'))['total'] or 0
        
        low_stock_count = Inventory.objects.filter(
            quantity__lte=F('reorder_point'),
            quantity__gt=0
        ).count()
        
        out_of_stock_count = Inventory.objects.filter(quantity__lte=0).count()
        
        overstock_count = Inventory.objects.filter(
            quantity__gte=F('maximum_stock_level')
        ).count()
        
        warehouse_summary = Warehouse.objects.annotate(
            product_count=Count('inventories__product', distinct=True),
            total_quantity=Sum('inventories__quantity'),
            low_stock_count=Count(
                Case(
                    When(
                        inventories__quantity__lte=F('inventories__reorder_point'),
                        inventories__quantity__gt=0,
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            out_of_stock_count=Count(
                Case(
                    When(
                        inventories__quantity__lte=0,
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        ).values('id', 'name', 'product_count', 'total_quantity', 'low_stock_count', 'out_of_stock_count')
        
        stock_value = InventoryService.get_stock_value()
        
        return Response({
            'total_products': total_products,
            'total_quantity': total_quantity,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'overstock_count': overstock_count,
            'total_stock_value': stock_value['total_value'],
            'warehouse_summary': warehouse_summary
        })
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get inventory items with low stock levels.
        """
        low_stock_items = InventoryService.get_low_stock_items()
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overstock(self, request):
        """
        Get inventory items with overstock levels.
        """
        overstock_items = InventoryService.get_overstock_items()
        serializer = self.get_serializer(overstock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """
        Adjust inventory quantity.
        """
        inventory = self.get_object()
        serializer = InventoryAdjustmentSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transaction = InventoryService.adjust_inventory(
                    inventory=inventory,
                    adjustment_quantity=serializer.validated_data['adjustment_quantity'],
                    user=request.user,
                    reason=serializer.validated_data['reason'],
                    reference_number=serializer.validated_data.get('reference_number', ''),
                    notes=serializer.validated_data.get('notes', '')
                )
                
                transaction_serializer = InventoryTransactionSerializer(transaction)
                return Response(transaction_serializer.data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def transfer(self, request):
        """
        Transfer inventory between warehouses.
        """
        serializer = InventoryTransferSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                source_inventory = Inventory.objects.get(
                    id=serializer.validated_data['source_inventory_id']
                )
                destination_inventory = Inventory.objects.get(
                    id=serializer.validated_data['destination_inventory_id']
                )
                
                source_transaction, destination_transaction = InventoryService.transfer_stock(
                    source_inventory=source_inventory,
                    destination_inventory=destination_inventory,
                    quantity=serializer.validated_data['quantity'],
                    user=request.user,
                    reference_number=serializer.validated_data.get('reference_number', ''),
                    notes=serializer.validated_data.get('notes', '')
                )
                
                return Response({
                    'source_transaction': InventoryTransactionSerializer(source_transaction).data,
                    'destination_transaction': InventoryTransactionSerializer(destination_transaction).data
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Update multiple inventory items in a single transaction.
        """
        serializer = BulkInventoryUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transactions = InventoryService.bulk_update_inventory(
                    inventory_updates=serializer.validated_data['inventory_updates'],
                    user=request.user,
                    reference_number=serializer.validated_data.get('reference_number', ''),
                    notes=serializer.validated_data.get('notes', '')
                )
                
                transaction_serializer = InventoryTransactionSerializer(transactions, many=True)
                return Response(transaction_serializer.data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_alert_settings(self, request):
        """
        Update inventory alert settings.
        """
        serializer = InventoryAlertSettingsSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                inventory = InventoryService.update_alert_settings(
                    inventory_id=serializer.validated_data['inventory_id'],
                    minimum_stock_level=serializer.validated_data.get('minimum_stock_level'),
                    maximum_stock_level=serializer.validated_data.get('maximum_stock_level'),
                    reorder_point=serializer.validated_data.get('reorder_point')
                )
                
                inventory_serializer = InventorySerializer(inventory)
                return Response(inventory_serializer.data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """
        Generate inventory reports.
        """
        serializer = InventoryReportSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                report_data = InventoryService.generate_inventory_report(
                    report_type=serializer.validated_data['report_type'],
                    start_date=serializer.validated_data.get('start_date'),
                    end_date=serializer.validated_data.get('end_date'),
                    warehouse_id=serializer.validated_data.get('warehouse_id'),
                    product_id=serializer.validated_data.get('product_id')
                )
                
                return Response(report_data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Export inventory data to CSV.
        """
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Product ID', 'Product Name', 'SKU', 'Warehouse', 'Quantity', 
            'Reserved', 'Available', 'Minimum Level', 'Maximum Level', 
            'Reorder Point', 'Cost Price', 'Value', 'Last Restocked'
        ])
        
        # Write data rows
        for inventory in queryset:
            writer.writerow([
                inventory.product.id,
                inventory.product.name,
                inventory.product.sku if hasattr(inventory.product, 'sku') else '',
                inventory.warehouse.name,
                inventory.quantity,
                inventory.reserved_quantity,
                inventory.available_quantity,
                inventory.minimum_stock_level,
                inventory.maximum_stock_level,
                inventory.reorder_point,
                inventory.cost_price,
                inventory.quantity * inventory.cost_price,
                inventory.last_restocked.strftime('%Y-%m-%d %H:%M:%S') if inventory.last_restocked else ''
            ])
        
        return response


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing inventory transactions.
    """
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'inventory', 'created_by']
    search_fields = ['reference_number', 'batch_number', 'notes']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Customize queryset to include additional filters.
        """
        queryset = super().get_queryset()
        
        # Filter by product
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(inventory__product_id=product_id)
        
        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse_id', None)
        if warehouse_id:
            queryset = queryset.filter(inventory__warehouse_id=warehouse_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing purchase orders.
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier', 'warehouse']
    search_fields = ['po_number', 'notes']
    ordering_fields = ['order_date', 'expected_delivery_date', 'total_amount']
    ordering = ['-order_date']
    
    def get_queryset(self):
        """
        Customize queryset to include additional filters.
        """
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new purchase order.
        """
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                purchase_order = PurchaseOrderService.create_purchase_order(
                    supplier_id=serializer.validated_data['supplier_id'],
                    warehouse_id=serializer.validated_data['warehouse_id'],
                    items=serializer.validated_data['items'],
                    user=request.user,
                    notes=serializer.validated_data.get('notes', ''),
                    expected_delivery_date=serializer.validated_data.get('expected_delivery_date')
                )
                
                response_serializer = PurchaseOrderSerializer(purchase_order)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """
        Receive items for a purchase order.
        """
        purchase_order = self.get_object()
        serializer = PurchaseOrderReceiveSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_po = PurchaseOrderService.receive_purchase_order(
                    purchase_order_id=purchase_order.id,
                    received_items=serializer.validated_data['received_items'],
                    user=request.user,
                    notes=serializer.validated_data.get('notes', '')
                )
                
                response_serializer = PurchaseOrderSerializer(updated_po)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a purchase order.
        """
        purchase_order = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({'error': 'Reason for cancellation is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cancelled_po = PurchaseOrderService.cancel_purchase_order(
                purchase_order_id=purchase_order.id,
                user=request.user,
                reason=reason
            )
            
            response_serializer = PurchaseOrderSerializer(cancelled_po)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing purchase order items.
    """
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['purchase_order', 'product', 'is_completed']
    search_fields = ['product__name', 'product__sku']
    ordering_fields = ['quantity_ordered', 'quantity_received', 'unit_price']
    ordering = ['id']