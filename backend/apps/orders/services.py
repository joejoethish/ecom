"""
Order services for the ecommerce platform.
"""
import uuid
import random
import string
import os
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice


class OrderService:
    """
    Service class for handling order operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_order(customer, cart_items, shipping_address, billing_address, 
                    shipping_method, payment_method, notes=""):
        """
        Create a new order from cart items.
        
        Args:
            customer: User placing the order
            cart_items: List of cart items
            shipping_address: Shipping address
            billing_address: Billing address
            shipping_method: Shipping method
            payment_method: Payment method
            notes: Additional notes
            
        Returns:
            Order: The created order
        """
        if not cart_items:
            raise ValidationError("Cannot create order with empty cart")
        
        # Generate unique order number
        order_number = OrderService._generate_order_number()
        
        # Calculate order totals
        subtotal = sum(item.quantity * item.product.price for item in cart_items)
        shipping_amount = Decimal('0.00')  # This would be calculated based on shipping method
        tax_amount = subtotal * Decimal('0.18')  # Example tax calculation (18%)
        discount_amount = Decimal('0.00')  # This would come from applied coupons
        total_amount = subtotal + shipping_amount + tax_amount - discount_amount
        
        # Create order
        order = Order.objects.create(
            customer=customer,
            order_number=order_number,
            status='pending',
            payment_status='pending',
            total_amount=total_amount,
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_method=shipping_method,
            payment_method=payment_method,
            estimated_delivery_date=timezone.now().date() + timedelta(days=5),
            notes=notes
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                total_price=cart_item.quantity * cart_item.product.price,
                status='pending',
                is_gift=cart_item.is_gift if hasattr(cart_item, 'is_gift') else False,
                gift_message=cart_item.gift_message if hasattr(cart_item, 'gift_message') else ''
            )
        
        # Create initial order tracking event
        order.add_timeline_event(
            status='pending',
            description='Order placed successfully',
            user=customer
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, new_status, user=None, description=None, location=None):
        """
        Update order status and create tracking event.
        
        Args:
            order_id: ID of the order to update
            new_status: New status value
            user: User making the update
            description: Description of the status change
            location: Location information
            
        Returns:
            Order: The updated order
        """
        try:
            order = Order.objects.get(id=order_id)
            
            # Validate status transition
            if not OrderService._is_valid_status_transition(order.status, new_status):
                raise ValidationError(f"Invalid status transition from {order.status} to {new_status}")
            
            # Update order status
            old_status = order.status
            order.status = new_status
            
            # Update delivery date if status is 'delivered'
            if new_status == 'delivered' and not order.actual_delivery_date:
                order.actual_delivery_date = timezone.now().date()
            
            order.save()
            
            # Create tracking event
            if not description:
                description = f"Order status changed from {old_status} to {new_status}"
                
            OrderTracking.objects.create(
                order=order,
                status=new_status,
                description=description,
                location=location or '',
                created_by=user
            )
            
            # If order is confirmed, generate invoice
            if new_status == 'confirmed' and not hasattr(order, 'invoice'):
                InvoiceService.generate_invoice(order)
            
            return order
            
        except Order.DoesNotExist:
            raise ValidationError(f"Order with ID {order_id} does not exist")
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id, reason, user):
        """
        Cancel an order if it hasn't been shipped.
        
        Args:
            order_id: ID of the order to cancel
            reason: Reason for cancellation
            user: User cancelling the order
            
        Returns:
            Order: The cancelled order
        """
        try:
            order = Order.objects.get(id=order_id)
            
            if not order.can_cancel():
                raise ValidationError("This order cannot be cancelled")
            
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            # Update all order items status
            order.items.all().update(status='cancelled')
            
            # Create tracking event
            OrderTracking.objects.create(
                order=order,
                status='cancelled',
                description=f"Order cancelled: {reason}",
                created_by=user
            )
            
            return order
            
        except Order.DoesNotExist:
            raise ValidationError(f"Order with ID {order_id} does not exist")
    
    @staticmethod
    def get_order_by_number(order_number):
        """
        Get order by order number.
        
        Args:
            order_number: Order number to search for
            
        Returns:
            Order: The found order or None
        """
        try:
            return Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return None
    
    @staticmethod
    def get_customer_orders(customer, status=None):
        """
        Get all orders for a customer with optional status filter.
        
        Args:
            customer: Customer user
            status: Optional status filter
            
        Returns:
            QuerySet: Filtered orders
        """
        orders = Order.objects.filter(customer=customer)
        
        if status:
            orders = orders.filter(status=status)
            
        return orders
    
    @staticmethod
    def _generate_order_number():
        """
        Generate a unique order number.
        
        Returns:
            str: Unique order number
        """
        # Format: ORD-YYYYMMDD-XXXXX (where XXXXX is a random string)
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        order_number = f"ORD-{date_part}-{random_part}"
        
        # Ensure uniqueness
        while Order.objects.filter(order_number=order_number).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            order_number = f"ORD-{date_part}-{random_part}"
        
        return order_number
    
    @staticmethod
    def _is_valid_status_transition(current_status, new_status):
        """
        Check if a status transition is valid.
        
        Args:
            current_status: Current order status
            new_status: New order status
            
        Returns:
            bool: True if transition is valid
        """
        # Define valid status transitions
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['out_for_delivery'],
            'out_for_delivery': ['delivered'],
            'delivered': ['returned', 'partially_returned'],
            'returned': ['refunded'],
            'partially_returned': ['partially_refunded'],
        }
        
        # Check if transition is valid
        return new_status in valid_transitions.get(current_status, [])


class ReturnService:
    """
    Service class for handling order returns and replacements.
    """
    
    @staticmethod
    @transaction.atomic
    def create_return_request(order_item_id, quantity, reason, description, customer):
        """
        Create a return request for an order item.
        
        Args:
            order_item_id: ID of the order item to return
            quantity: Quantity to return
            reason: Reason for return
            description: Detailed description
            customer: Customer making the request
            
        Returns:
            ReturnRequest: The created return request
        """
        try:
            order_item = OrderItem.objects.get(id=order_item_id)
            
            # Validate return eligibility
            if not order_item.can_return():
                raise ValidationError("This item is not eligible for return")
            
            if quantity <= 0 or quantity > (order_item.quantity - order_item.returned_quantity):
                raise ValidationError(f"Invalid return quantity. Available: {order_item.quantity - order_item.returned_quantity}")
            
            # Calculate refund amount
            refund_amount = order_item.unit_price * Decimal(quantity)
            
            # Create return request
            return_request = ReturnRequest.objects.create(
                order=order_item.order,
                order_item=order_item,
                quantity=quantity,
                reason=reason,
                description=description,
                refund_amount=refund_amount,
                refund_method='original'  # Default to original payment method
            )
            
            # Create order tracking event
            OrderTracking.objects.create(
                order=order_item.order,
                status=order_item.order.status,
                description=f"Return request created for {quantity} x {order_item.product.name}",
                created_by=customer
            )
            
            return return_request
            
        except OrderItem.DoesNotExist:
            raise ValidationError(f"Order item with ID {order_item_id} does not exist")
    
    @staticmethod
    @transaction.atomic
    def process_return_request(return_request_id, status, processed_by, notes=""):
        """
        Process a return request (approve, reject, complete).
        
        Args:
            return_request_id: ID of the return request
            status: New status ('approved', 'rejected', 'completed')
            processed_by: Admin user processing the request
            notes: Processing notes
            
        Returns:
            ReturnRequest: The processed return request
        """
        try:
            return_request = ReturnRequest.objects.get(id=return_request_id)
            
            # Validate status transition
            if return_request.status == 'completed':
                raise ValidationError("This return request has already been completed")
            
            if return_request.status == 'rejected' and status != 'pending':
                raise ValidationError("Cannot change status of a rejected return request")
            
            # Update return request
            return_request.status = status
            return_request.processed_by = processed_by
            return_request.notes = notes
            
            if status == 'completed':
                return_request.return_received_date = timezone.now().date()
                return_request.refund_processed_date = timezone.now().date()
                
                # Update order item
                order_item = return_request.order_item
                order_item.returned_quantity += return_request.quantity
                order_item.refunded_amount += return_request.refund_amount
                
                if order_item.returned_quantity == order_item.quantity:
                    order_item.status = 'returned'
                else:
                    order_item.status = 'partially_returned'
                
                order_item.save()
                
                # Update order status if all items are returned
                order = return_request.order
                all_items_returned = all(
                    item.returned_quantity == item.quantity 
                    for item in order.items.all()
                )
                
                if all_items_returned:
                    order.status = 'returned'
                else:
                    order.status = 'partially_returned'
                
                order.save()
                
                # Create order tracking event
                OrderTracking.objects.create(
                    order=order,
                    status=order.status,
                    description=f"Return completed for {return_request.quantity} x {return_request.order_item.product.name}",
                    created_by=processed_by
                )
            
            return_request.save()
            return return_request
            
        except ReturnRequest.DoesNotExist:
            raise ValidationError(f"Return request with ID {return_request_id} does not exist")
    
    @staticmethod
    @transaction.atomic
    def create_replacement(return_request_id, replacement_product_id, quantity, processed_by, notes=""):
        """
        Create a replacement for a return request.
        
        Args:
            return_request_id: ID of the return request
            replacement_product_id: ID of the replacement product
            quantity: Quantity to replace
            processed_by: Admin user processing the replacement
            notes: Additional notes
            
        Returns:
            Replacement: The created replacement
        """
        try:
            return_request = ReturnRequest.objects.get(id=return_request_id)
            
            # Validate return request status
            if return_request.status not in ['approved', 'completed']:
                raise ValidationError("Return request must be approved or completed to create replacement")
            
            # Validate quantity
            if quantity <= 0 or quantity > return_request.quantity:
                raise ValidationError(f"Invalid replacement quantity. Maximum: {return_request.quantity}")
            
            # Create replacement
            replacement = Replacement.objects.create(
                return_request=return_request,
                order=return_request.order,
                order_item=return_request.order_item,
                replacement_product_id=replacement_product_id,
                quantity=quantity,
                shipping_address=return_request.order.shipping_address,
                processed_by=processed_by,
                notes=notes
            )
            
            # Create order tracking event
            OrderTracking.objects.create(
                order=return_request.order,
                status=return_request.order.status,
                description=f"Replacement created for return request {return_request.id}",
                created_by=processed_by
            )
            
            return replacement
            
        except ReturnRequest.DoesNotExist:
            raise ValidationError(f"Return request with ID {return_request_id} does not exist")
    
    @staticmethod
    @transaction.atomic
    def update_replacement_status(replacement_id, status, processed_by, tracking_number=None, notes=None):
        """
        Update replacement status.
        
        Args:
            replacement_id: ID of the replacement
            status: New status
            processed_by: User updating the status
            tracking_number: Optional tracking number
            notes: Optional notes
            
        Returns:
            Replacement: The updated replacement
        """
        try:
            replacement = Replacement.objects.get(id=replacement_id)
            
            # Update replacement
            replacement.status = status
            
            if tracking_number:
                replacement.tracking_number = tracking_number
            
            if notes:
                replacement.notes = notes
            
            # Update dates based on status
            if status == 'shipped' and not replacement.shipped_date:
                replacement.shipped_date = timezone.now().date()
            
            if status == 'delivered' and not replacement.delivered_date:
                replacement.delivered_date = timezone.now().date()
            
            replacement.save()
            
            # Create order tracking event
            OrderTracking.objects.create(
                order=replacement.order,
                status=replacement.order.status,
                description=f"Replacement status updated to {status}",
                created_by=processed_by
            )
            
            return replacement
            
        except Replacement.DoesNotExist:
            raise ValidationError(f"Replacement with ID {replacement_id} does not exist")


class InvoiceService:
    """
    Service class for handling order invoices.
    """
    
    @staticmethod
    @transaction.atomic
    def generate_invoice(order):
        """
        Generate an invoice for an order.
        
        Args:
            order: Order to generate invoice for
            
        Returns:
            Invoice: The generated invoice
        """
        # Check if invoice already exists
        if hasattr(order, 'invoice'):
            return order.invoice
        
        # Generate invoice number
        invoice_number = InvoiceService._generate_invoice_number()
        
        # Calculate invoice amounts
        subtotal = sum(item.total_price for item in order.items.all())
        
        # Create invoice
        invoice = Invoice.objects.create(
            order=order,
            invoice_number=invoice_number,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),  # For prepaid orders, due date is same as invoice date
            billing_address=order.billing_address,
            shipping_address=order.shipping_address,
            subtotal=subtotal,
            tax_amount=order.tax_amount,
            shipping_amount=order.shipping_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            terms_and_conditions=InvoiceService._get_default_terms()
        )
        
        # Generate PDF file (this would be implemented separately)
        file_path = InvoiceService._generate_invoice_pdf(invoice)
        invoice.file_path = file_path
        invoice.save()
        
        # Update order with invoice number
        order.invoice_number = invoice_number
        order.save()
        
        return invoice
    
    @staticmethod
    def regenerate_invoice(invoice):
        """
        Regenerate an invoice PDF.
        
        Args:
            invoice: Invoice to regenerate
            
        Returns:
            Invoice: The updated invoice
        """
        # Generate new PDF file
        file_path = InvoiceService._generate_invoice_pdf(invoice)
        invoice.file_path = file_path
        invoice.save()
        
        return invoice
    
    @staticmethod
    def get_invoice_by_number(invoice_number):
        """
        Get invoice by invoice number.
        
        Args:
            invoice_number: Invoice number to search for
            
        Returns:
            Invoice: The found invoice or None
        """
        try:
            return Invoice.objects.get(invoice_number=invoice_number)
        except Invoice.DoesNotExist:
            return None
    
    @staticmethod
    def _generate_invoice_number():
        """
        Generate a unique invoice number.
        
        Returns:
            str: Unique invoice number
        """
        # Format: INV-YYYYMMDD-XXXXX (where XXXXX is a random string)
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        invoice_number = f"INV-{date_part}-{random_part}"
        
        # Ensure uniqueness
        while Invoice.objects.filter(invoice_number=invoice_number).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            invoice_number = f"INV-{date_part}-{random_part}"
        
        return invoice_number
    
    @staticmethod
    def _generate_invoice_pdf(invoice):
        """
        Generate PDF file for invoice.
        
        Args:
            invoice: Invoice to generate PDF for
            
        Returns:
            str: Path to generated PDF file
        """
        # This would be implemented with a PDF generation library
        # For now, just return a placeholder path
        invoice_dir = "invoices"
        os.makedirs(invoice_dir, exist_ok=True)
        return f"{invoice_dir}/{invoice.invoice_number}.pdf"
    
    @staticmethod
    def _get_default_terms():
        """
        Get default terms and conditions for invoices.
        
        Returns:
            str: Default terms and conditions
        """
        return """
        1. All prices are in USD unless otherwise specified.
        2. Payment is due immediately for online orders.
        3. Returns are accepted within 30 days of delivery.
        4. Shipping and handling fees are non-refundable.
        5. Please retain this invoice for warranty purposes.
        """