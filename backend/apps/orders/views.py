"""
Order views for the ecommerce platform.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import os

from .models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from .serializers import (
    OrderSerializer, OrderDetailSerializer, OrderItemSerializer, OrderTrackingSerializer,
    ReturnRequestSerializer, ReplacementSerializer, InvoiceSerializer,
    OrderCreateSerializer, OrderStatusUpdateSerializer, OrderCancelSerializer,
    ReturnRequestCreateSerializer, ReturnRequestProcessSerializer,
    ReplacementCreateSerializer, ReplacementUpdateSerializer,
    OrderBulkUpdateSerializer, OrderItemUpdateSerializer, ReturnRequestBulkProcessSerializer
)
from .services import OrderService, ReturnService, InvoiceService
from apps.cart.models import CartItem


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for orders.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status']
    search_fields = ['order_number', 'tracking_number']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'retrieve' or self.action == 'detail':
            return OrderDetailSerializer
        return OrderSerializer

    def get_queryset(self):
        """Get orders for the current user or all orders for admin."""
        user = self.request.user
        
        # Admin can see all orders
        if user.is_staff:
            queryset = Order.objects.filter(is_deleted=False)
            
            # Filter by customer if provided
            customer_id = self.request.query_params.get('customer_id')
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
                
            return queryset
        
        # Regular users can only see their own orders
        return Order.objects.filter(customer=user, is_deleted=False)
    
    def create(self, request, *args, **kwargs):
        """Create a new order from cart items."""
        serializer = OrderCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Get cart items
            cart_item_ids = serializer.validated_data['cart_items']
            cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart__user=request.user)
            
            if not cart_items:
                return Response(
                    {"error": "No valid cart items found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Create order
                order = OrderService.create_order(
                    customer=request.user,
                    cart_items=cart_items,
                    shipping_address=serializer.validated_data['shipping_address'],
                    billing_address=serializer.validated_data['billing_address'],
                    shipping_method=serializer.validated_data['shipping_method'],
                    payment_method=serializer.validated_data['payment_method'],
                    notes=serializer.validated_data.get('notes', '')
                )
                
                # Clear cart items
                cart_items.delete()
                
                # Return order data
                order_serializer = OrderSerializer(order)
                return Response(order_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_order = OrderService.update_order_status(
                    order_id=order.id,
                    new_status=serializer.validated_data['status'],
                    user=request.user,
                    description=serializer.validated_data.get('description'),
                    location=serializer.validated_data.get('location')
                )
                
                order_serializer = OrderSerializer(updated_order)
                return Response(order_serializer.data)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order."""
        order = self.get_object()
        serializer = OrderCancelSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                cancelled_order = OrderService.cancel_order(
                    order_id=order.id,
                    reason=serializer.validated_data['reason'],
                    user=request.user
                )
                
                order_serializer = OrderSerializer(cancelled_order)
                return Response(order_serializer.data)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get order timeline events."""
        order = self.get_object()
        timeline_events = order.get_order_timeline()
        serializer = OrderTrackingSerializer(timeline_events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        """Get order invoice."""
        order = self.get_object()
        
        try:
            invoice = Invoice.objects.get(order=order)
            serializer = InvoiceSerializer(invoice)
            return Response(serializer.data)
        except Invoice.DoesNotExist:
            return Response(
                {"error": "Invoice not found for this order"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def download_invoice(self, request, pk=None):
        """Download order invoice PDF."""
        order = self.get_object()
        
        try:
            invoice = Invoice.objects.get(order=order)
            
            # Check if file exists
            if not invoice.file_path or not os.path.exists(invoice.file_path):
                # Generate invoice if file doesn't exist
                invoice = InvoiceService.generate_invoice(order)
            
            # Serve file
            with open(invoice.file_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
                return response
                
        except Invoice.DoesNotExist:
            return Response(
                {"error": "Invoice not found for this order"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed order information including returns and replacements."""
        order = self.get_object()
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Bulk update order statuses (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can perform bulk updates"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrderBulkUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            order_ids = serializer.validated_data['order_ids']
            new_status = serializer.validated_data['status']
            description = serializer.validated_data.get('description', '')
            
            updated_orders = []
            errors = []
            
            for order_id in order_ids:
                try:
                    updated_order = OrderService.update_order_status(
                        order_id=order_id,
                        new_status=new_status,
                        user=request.user,
                        description=description
                    )
                    updated_orders.append(str(updated_order.id))
                except Exception as e:
                    errors.append({"order_id": str(order_id), "error": str(e)})
            
            return Response({
                "updated_orders": updated_orders,
                "errors": errors,
                "total_updated": len(updated_orders),
                "total_errors": len(errors)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        """Generate or regenerate invoice for an order."""
        order = self.get_object()
        
        try:
            # Check if invoice already exists
            try:
                invoice = Invoice.objects.get(order=order)
                # Regenerate invoice
                invoice = InvoiceService.regenerate_invoice(invoice)
            except Invoice.DoesNotExist:
                # Generate new invoice
                invoice = InvoiceService.generate_invoice(order)
            
            serializer = InvoiceSerializer(invoice)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for return requests.
    """
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'order', 'order_item']
    search_fields = ['order__order_number']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get return requests for the current user or all for admin."""
        user = self.request.user
        
        # Admin can see all return requests
        if user.is_staff:
            return ReturnRequest.objects.filter(is_deleted=False)
        
        # Regular users can only see their own return requests
        return ReturnRequest.objects.filter(order__customer=user, is_deleted=False)
    
    def create(self, request, *args, **kwargs):
        """Create a new return request."""
        serializer = ReturnRequestCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                return_request = ReturnService.create_return_request(
                    order_item_id=serializer.validated_data['order_item_id'],
                    quantity=serializer.validated_data['quantity'],
                    reason=serializer.validated_data['reason'],
                    description=serializer.validated_data['description'],
                    customer=request.user
                )
                
                return_serializer = ReturnRequestSerializer(return_request)
                return Response(return_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process a return request (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can process return requests"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return_request = self.get_object()
        serializer = ReturnRequestProcessSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                processed_request = ReturnService.process_return_request(
                    return_request_id=return_request.id,
                    status=serializer.validated_data['status'],
                    processed_by=request.user,
                    notes=serializer.validated_data.get('notes', '')
                )
                
                return_serializer = ReturnRequestSerializer(processed_request)
                return Response(return_serializer.data)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        """Bulk process return requests (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can bulk process return requests"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReturnRequestBulkProcessSerializer(data=request.data)
        
        if serializer.is_valid():
            return_request_ids = serializer.validated_data['return_request_ids']
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            processed_requests = []
            errors = []
            
            for return_request_id in return_request_ids:
                try:
                    processed_request = ReturnService.process_return_request(
                        return_request_id=return_request_id,
                        status=new_status,
                        processed_by=request.user,
                        notes=notes
                    )
                    processed_requests.append(str(processed_request.id))
                except Exception as e:
                    errors.append({"return_request_id": str(return_request_id), "error": str(e)})
            
            return Response({
                "processed_requests": processed_requests,
                "errors": errors,
                "total_processed": len(processed_requests),
                "total_errors": len(errors)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def eligible_products_for_replacement(self, request, pk=None):
        """Get eligible products for replacement (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return_request = self.get_object()
        
        # Get products in the same category as the original product
        category = return_request.order_item.product.category
        eligible_products = Product.objects.filter(
            category=category,
            is_active=True
        ).exclude(id=return_request.order_item.product.id)
        
        from apps.products.serializers import ProductMinimalSerializer
        serializer = ProductMinimalSerializer(eligible_products, many=True)
        return Response(serializer.data)


class ReplacementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for replacements.
    """
    serializer_class = ReplacementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'order', 'return_request']
    search_fields = ['order__order_number', 'tracking_number']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get replacements for the current user or all for admin."""
        user = self.request.user
        
        # Admin can see all replacements
        if user.is_staff:
            return Replacement.objects.filter(is_deleted=False)
        
        # Regular users can only see their own replacements
        return Replacement.objects.filter(order__customer=user, is_deleted=False)
    
    def create(self, request, *args, **kwargs):
        """Create a new replacement (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can create replacements"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReplacementCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                replacement = ReturnService.create_replacement(
                    return_request_id=serializer.validated_data['return_request_id'],
                    replacement_product_id=serializer.validated_data['replacement_product_id'],
                    quantity=serializer.validated_data['quantity'],
                    processed_by=request.user,
                    notes=serializer.validated_data.get('notes', '')
                )
                
                replacement_serializer = ReplacementSerializer(replacement)
                return Response(replacement_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update replacement status (admin only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can update replacement status"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        replacement = self.get_object()
        serializer = ReplacementUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_replacement = ReturnService.update_replacement_status(
                    replacement_id=replacement.id,
                    status=serializer.validated_data['status'],
                    processed_by=request.user,
                    tracking_number=serializer.validated_data.get('tracking_number'),
                    notes=serializer.validated_data.get('notes')
                )
                
                replacement_serializer = ReplacementSerializer(updated_replacement)
                return Response(replacement_serializer.data)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for invoices (read-only).
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order']
    search_fields = ['invoice_number', 'order__order_number']
    ordering_fields = ['created_at', 'invoice_date', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get invoices for the current user or all for admin."""
        user = self.request.user
        
        # Admin can see all invoices
        if user.is_staff:
            return Invoice.objects.filter(is_deleted=False)
        
        # Regular users can only see their own invoices
        return Invoice.objects.filter(order__customer=user, is_deleted=False)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download invoice PDF."""
        invoice = self.get_object()
        
        try:
            # Check if file exists
            if not invoice.file_path or not os.path.exists(invoice.file_path):
                # Generate invoice if file doesn't exist
                invoice = InvoiceService.generate_invoice(invoice.order)
            
            # Serve file
            with open(invoice.file_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
                return response
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)