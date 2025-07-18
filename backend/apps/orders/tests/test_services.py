"""
Tests for the order services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.orders.models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.orders.services import OrderService, ReturnService, InvoiceService
from apps.products.models import Product, Category
from apps.cart.models import Cart, CartItem

User = get_user_model()


class OrderServiceTest(TestCase):
    """Test the OrderService."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a category
        self.category = Category.objects.create(name='Test Category')
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create a cart
        self.cart = Cart.objects.create(user=self.user)
        
        # Create a cart item
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        # Create shipping and billing addresses
        self.shipping_address = {
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip': '12345',
            'country': 'Test Country',
            'phone': '1234567890'
        }
        
        self.billing_address = {
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip': '12345',
            'country': 'Test Country',
            'phone': '1234567890'
        }

    def test_create_order(self):
        """Test creating an order from cart items."""
        # Create an order
        order = OrderService.create_order(
            customer=self.user,
            cart_items=[self.cart_item],
            shipping_address=self.shipping_address,
            billing_address=self.billing_address,
            shipping_method='standard',
            payment_method='credit_card',
            notes='Test order'
        )
        
        # Check order details
        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_status, 'pending')
        self.assertEqual(order.shipping_method, 'standard')
        self.assertEqual(order.payment_method, 'credit_card')
        self.assertEqual(order.notes, 'Test order')
        self.assertEqual(order.shipping_address, self.shipping_address)
        self.assertEqual(order.billing_address, self.billing_address)
        
        # Check order items
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, self.product.price)
        self.assertEqual(order_item.total_price, self.product.price * 2)
        
        # Check order tracking
        self.assertEqual(order.timeline_events.count(), 1)
        tracking_event = order.timeline_events.first()
        self.assertEqual(tracking_event.status, 'pending')
        self.assertEqual(tracking_event.description, 'Order placed successfully')

    def test_create_order_with_empty_cart(self):
        """Test creating an order with an empty cart."""
        with self.assertRaises(ValidationError):
            OrderService.create_order(
                customer=self.user,
                cart_items=[],
                shipping_address=self.shipping_address,
                billing_address=self.billing_address,
                shipping_method='standard',
                payment_method='credit_card'
            )

    def test_update_order_status(self):
        """Test updating an order's status."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Update order status
        updated_order = OrderService.update_order_status(
            order_id=order.id,
            new_status='confirmed',
            user=self.user,
            description='Order confirmed by admin'
        )
        
        # Check updated order
        self.assertEqual(updated_order.status, 'confirmed')
        
        # Check tracking event
        tracking_event = updated_order.timeline_events.first()
        self.assertEqual(tracking_event.status, 'confirmed')
        self.assertEqual(tracking_event.description, 'Order confirmed by admin')
        self.assertEqual(tracking_event.created_by, self.user)

    def test_update_order_status_invalid_transition(self):
        """Test updating an order's status with an invalid transition."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Try to update with invalid status transition
        with self.assertRaises(ValidationError):
            OrderService.update_order_status(
                order_id=order.id,
                new_status='shipped',  # Invalid transition from pending
                user=self.user
            )

    def test_update_order_status_to_delivered(self):
        """Test updating an order's status to delivered."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='out_for_delivery',
            payment_status='paid',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Update order status to delivered
        updated_order = OrderService.update_order_status(
            order_id=order.id,
            new_status='delivered',
            user=self.user
        )
        
        # Check that actual_delivery_date was set
        self.assertIsNotNone(updated_order.actual_delivery_date)
        self.assertEqual(updated_order.actual_delivery_date, timezone.now().date())

    @patch('apps.orders.services.InvoiceService.generate_invoice')
    def test_update_order_status_to_confirmed_generates_invoice(self, mock_generate_invoice):
        """Test that updating an order's status to confirmed generates an invoice."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Mock invoice generation
        mock_invoice = MagicMock()
        mock_generate_invoice.return_value = mock_invoice
        
        # Update order status to confirmed
        OrderService.update_order_status(
            order_id=order.id,
            new_status='confirmed',
            user=self.user
        )
        
        # Check that invoice was generated
        mock_generate_invoice.assert_called_once_with(order)

    def test_cancel_order(self):
        """Test cancelling an order."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Create order items
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('99.99'),
            total_price=Decimal('199.98')
        )
        
        # Cancel order
        cancelled_order = OrderService.cancel_order(
            order_id=order.id,
            reason='Customer requested cancellation',
            user=self.user
        )
        
        # Check cancelled order
        self.assertEqual(cancelled_order.status, 'cancelled')
        
        # Check that order items were cancelled
        order_item.refresh_from_db()
        self.assertEqual(order_item.status, 'cancelled')
        
        # Check tracking event
        tracking_event = cancelled_order.timeline_events.first()
        self.assertEqual(tracking_event.status, 'cancelled')
        self.assertEqual(tracking_event.description, 'Order cancelled: Customer requested cancellation')
        self.assertEqual(tracking_event.created_by, self.user)

    def test_cancel_order_non_cancellable(self):
        """Test cancelling an order that cannot be cancelled."""
        # Create an order that cannot be cancelled
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='shipped',
            payment_status='paid',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Try to cancel order
        with self.assertRaises(ValidationError):
            OrderService.cancel_order(
                order_id=order.id,
                reason='Customer requested cancellation',
                user=self.user
            )

    def test_get_order_by_number(self):
        """Test getting an order by its number."""
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Get order by number
        found_order = OrderService.get_order_by_number('ORD-20250718-12345')
        self.assertEqual(found_order, order)
        
        # Try to get non-existent order
        not_found_order = OrderService.get_order_by_number('ORD-20250718-99999')
        self.assertIsNone(not_found_order)

    def test_get_customer_orders(self):
        """Test getting a customer's orders."""
        # Create orders for the user
        order1 = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        order2 = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-67890',
            status='confirmed',
            payment_status='paid',
            total_amount=Decimal('299.98'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Create another user and order
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-54321',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        # Get all orders for the user
        user_orders = OrderService.get_customer_orders(self.user)
        self.assertEqual(user_orders.count(), 2)
        self.assertIn(order1, user_orders)
        self.assertIn(order2, user_orders)
        self.assertNotIn(other_order, user_orders)
        
        # Get pending orders for the user
        pending_orders = OrderService.get_customer_orders(self.user, status='pending')
        self.assertEqual(pending_orders.count(), 1)
        self.assertIn(order1, pending_orders)
        self.assertNotIn(order2, pending_orders)


class ReturnServiceTest(TestCase):
    """Test the ReturnService."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create a category
        self.category = Category.objects.create(name='Test Category')
        
        # Create products
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        self.replacement_product = Product.objects.create(
            name='Replacement Product',
            description='Replacement Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create an order
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-20250718-12345',
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('199.98'),
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'},
            actual_delivery_date=timezone.now().date()
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('99.99'),
            total_price=Decimal('199.98'),
            status='delivered'
        )

    def test_create_return_request(self):
        """Test creating a return request."""
        # Create a return request
        return_request = ReturnService.create_return_request(
            order_item_id=self.order_item.id,
            quantity=1,
            reason='defective',
            description='Product is defective',
            customer=self.customer
        )
        
        # Check return request details
        self.assertEqual(return_request.order, self.order)
        self.assertEqual(return_request.order_item, self.order_item)
        self.assertEqual(return_request.quantity, 1)
        self.assertEqual(return_request.reason, 'defective')
        self.assertEqual(return_request.description, 'Product is defective')
        self.assertEqual(return_request.status, 'pending')
        self.assertEqual(return_request.refund_amount, Decimal('99.99'))  # Unit price * quantity
        self.assertEqual(return_request.refund_method, 'original')
        
        # Check that a tracking event was created
        tracking_event = self.order.timeline_events.first()
        self.assertIn('Return request created', tracking_event.description)
        self.assertIn(self.product.name, tracking_event.description)

    def test_create_return_request_ineligible_item(self):
        """Test creating a return request for an ineligible item."""
        # Make the order item ineligible for return
        self.order.status = 'pending'
        self.order.save()
        
        # Try to create a return request
        with self.assertRaises(ValidationError):
            ReturnService.create_return_request(
                order_item_id=self.order_item.id,
                quantity=1,
                reason='defective',
                description='Product is defective',
                customer=self.customer
            )

    def test_create_return_request_invalid_quantity(self):
        """Test creating a return request with an invalid quantity."""
        # Try to create a return request with zero quantity
        with self.assertRaises(ValidationError):
            ReturnService.create_return_request(
                order_item_id=self.order_item.id,
                quantity=0,
                reason='defective',
                description='Product is defective',
                customer=self.customer
            )
        
        # Try to create a return request with quantity greater than ordered
        with self.assertRaises(ValidationError):
            ReturnService.create_return_request(
                order_item_id=self.order_item.id,
                quantity=3,
                reason='defective',
                description='Product is defective',
                customer=self.customer
            )

    def test_process_return_request_approve(self):
        """Test approving a return request."""
        # Create a return request
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Approve the return request
        processed_request = ReturnService.process_return_request(
            return_request_id=return_request.id,
            status='approved',
            processed_by=self.admin,
            notes='Approved by admin'
        )
        
        # Check processed request
        self.assertEqual(processed_request.status, 'approved')
        self.assertEqual(processed_request.processed_by, self.admin)
        self.assertEqual(processed_request.notes, 'Approved by admin')

    def test_process_return_request_complete(self):
        """Test completing a return request."""
        # Create a return request
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Complete the return request
        processed_request = ReturnService.process_return_request(
            return_request_id=return_request.id,
            status='completed',
            processed_by=self.admin,
            notes='Return received and refund processed'
        )
        
        # Check processed request
        self.assertEqual(processed_request.status, 'completed')
        self.assertEqual(processed_request.processed_by, self.admin)
        self.assertEqual(processed_request.notes, 'Return received and refund processed')
        self.assertIsNotNone(processed_request.return_received_date)
        self.assertIsNotNone(processed_request.refund_processed_date)
        
        # Check that order item was updated
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.returned_quantity, 1)
        self.assertEqual(self.order_item.refunded_amount, Decimal('99.99'))
        self.assertEqual(self.order_item.status, 'partially_returned')
        
        # Check that order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'partially_returned')
        
        # Check that a tracking event was created
        tracking_event = self.order.timeline_events.first()
        self.assertIn('Return completed', tracking_event.description)

    def test_process_return_request_complete_full_return(self):
        """Test completing a return request for the full quantity."""
        # Create a return request for the full quantity
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=2,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('199.98'),
            refund_method='original'
        )
        
        # Complete the return request
        processed_request = ReturnService.process_return_request(
            return_request_id=return_request.id,
            status='completed',
            processed_by=self.admin
        )
        
        # Check that order item was updated
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.returned_quantity, 2)
        self.assertEqual(self.order_item.status, 'returned')
        
        # Check that order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'returned')

    def test_create_replacement(self):
        """Test creating a replacement for a return request."""
        # Create a return request
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            status='approved',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Create a replacement
        replacement = ReturnService.create_replacement(
            return_request_id=return_request.id,
            replacement_product_id=self.replacement_product.id,
            quantity=1,
            processed_by=self.admin,
            notes='Replacement for defective product'
        )
        
        # Check replacement details
        self.assertEqual(replacement.return_request, return_request)
        self.assertEqual(replacement.order, self.order)
        self.assertEqual(replacement.order_item, self.order_item)
        self.assertEqual(replacement.replacement_product, self.replacement_product)
        self.assertEqual(replacement.quantity, 1)
        self.assertEqual(replacement.status, 'pending')
        self.assertEqual(replacement.shipping_address, self.order.shipping_address)
        self.assertEqual(replacement.processed_by, self.admin)
        self.assertEqual(replacement.notes, 'Replacement for defective product')
        
        # Check that a tracking event was created
        tracking_event = self.order.timeline_events.first()
        self.assertIn('Replacement created', tracking_event.description)

    def test_create_replacement_invalid_return_request(self):
        """Test creating a replacement for an invalid return request."""
        # Create a pending return request
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            status='pending',  # Not approved yet
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Try to create a replacement
        with self.assertRaises(ValidationError):
            ReturnService.create_replacement(
                return_request_id=return_request.id,
                replacement_product_id=self.replacement_product.id,
                quantity=1,
                processed_by=self.admin
            )

    def test_update_replacement_status(self):
        """Test updating a replacement's status."""
        # Create a return request
        return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            status='approved',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Create a replacement
        replacement = Replacement.objects.create(
            return_request=return_request,
            order=self.order,
            order_item=self.order_item,
            replacement_product=self.replacement_product,
            quantity=1,
            shipping_address=self.order.shipping_address,
            processed_by=self.admin
        )
        
        # Update replacement status to shipped
        updated_replacement = ReturnService.update_replacement_status(
            replacement_id=replacement.id,
            status='shipped',
            processed_by=self.admin,
            tracking_number='TRK123456789',
            notes='Shipped via Express'
        )
        
        # Check updated replacement
        self.assertEqual(updated_replacement.status, 'shipped')
        self.assertEqual(updated_replacement.tracking_number, 'TRK123456789')
        self.assertEqual(updated_replacement.notes, 'Shipped via Express')
        self.assertIsNotNone(updated_replacement.shipped_date)
        self.assertIsNone(updated_replacement.delivered_date)
        
        # Check that a tracking event was created
        tracking_event = self.order.timeline_events.first()
        self.assertIn('Replacement status updated', tracking_event.description)
        
        # Update replacement status to delivered
        updated_replacement = ReturnService.update_replacement_status(
            replacement_id=replacement.id,
            status='delivered',
            processed_by=self.admin
        )
        
        # Check updated replacement
        self.assertEqual(updated_replacement.status, 'delivered')
        self.assertIsNotNone(updated_replacement.delivered_date)


class InvoiceServiceTest(TestCase):
    """Test the InvoiceService."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a category
        self.category = Category.objects.create(name='Test Category')
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create an order
        self.order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='confirmed',
            payment_status='paid',
            total_amount=Decimal('127.99'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('18.00'),
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'}
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('99.99'),
            total_price=Decimal('99.99')
        )

    def test_generate_invoice(self):
        """Test generating an invoice for an order."""
        # Generate an invoice
        invoice = InvoiceService.generate_invoice(self.order)
        
        # Check invoice details
        self.assertEqual(invoice.order, self.order)
        self.assertTrue(invoice.invoice_number.startswith('INV-'))
        self.assertEqual(invoice.invoice_date, timezone.now().date())
        self.assertEqual(invoice.due_date, timezone.now().date())
        self.assertEqual(invoice.billing_address, self.order.billing_address)
        self.assertEqual(invoice.shipping_address, self.order.shipping_address)
        self.assertEqual(invoice.subtotal, Decimal('99.99'))
        self.assertEqual(invoice.tax_amount, self.order.tax_amount)
        self.assertEqual(invoice.shipping_amount, self.order.shipping_amount)
        self.assertEqual(invoice.total_amount, self.order.total_amount)
        self.assertIsNotNone(invoice.terms_and_conditions)
        self.assertIsNotNone(invoice.file_path)
        
        # Check that order was updated with invoice number
        self.order.refresh_from_db()
        self.assertEqual(self.order.invoice_number, invoice.invoice_number)

    def test_generate_invoice_existing(self):
        """Test generating an invoice for an order that already has one."""
        # Generate an invoice
        invoice1 = InvoiceService.generate_invoice(self.order)
        
        # Try to generate another invoice
        invoice2 = InvoiceService.generate_invoice(self.order)
        
        # Check that the same invoice was returned
        self.assertEqual(invoice1, invoice2)