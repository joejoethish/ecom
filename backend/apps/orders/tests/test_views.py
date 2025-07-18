"""
Tests for the order views.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json
from unittest.mock import patch

from apps.orders.models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.products.models import Product, Category
from apps.cart.models import Cart, CartItem

User = get_user_model()


class OrderViewSetTest(TestCase):
    """Test the OrderViewSet."""

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
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create a cart for the customer
        self.cart = Cart.objects.create(user=self.customer)
        
        # Create a cart item
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        # Create an order for the customer
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('18.00'),
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'}
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('99.99'),
            total_price=Decimal('199.98')
        )
        
        # Create an order tracking event
        self.tracking_event = OrderTracking.objects.create(
            order=self.order,
            status='pending',
            description='Order created successfully'
        )
        
        # Create API client
        self.client = APIClient()

    def test_list_orders_customer(self):
        """Test that a customer can list their own orders."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Create another order for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'}
        )
        
        # Get orders
        url = reverse('order-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['order_number'], self.order.order_number)

    def test_list_orders_admin(self):
        """Test that an admin can list all orders."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Create another order for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'}
        )
        
        # Get orders
        url = reverse('order-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both orders

    def test_retrieve_order(self):
        """Test retrieving a single order."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Get order
        url = reverse('order-detail', args=[self.order.id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], self.order.order_number)
        self.assertEqual(response.data['status'], self.order.status)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(len(response.data['timeline']), 1)

    @patch('apps.orders.views.OrderService.create_order')
    def test_create_order(self, mock_create_order):
        """Test creating an order."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Mock order creation
        mock_order = Order(
            id=999,
            customer=self.customer,
            order_number='ORD-20250718-99999',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('199.98')
        )
        mock_create_order.return_value = mock_order
        
        # Create order
        url = reverse('order-list')
        data = {
            'cart_items': [self.cart_item.id],
            'shipping_address': {'address': '123 Test St'},
            'billing_address': {'address': '123 Test St'},
            'shipping_method': 'standard',
            'payment_method': 'credit_card',
            'notes': 'Test order'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_create_order.assert_called_once()

    def test_update_order_status(self):
        """Test updating an order's status."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Update order status
        url = reverse('order-update-status', args=[self.order.id])
        data = {
            'status': 'confirmed',
            'description': 'Order confirmed by admin'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')
        
        # Check that order was updated in database
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')

    def test_cancel_order(self):
        """Test cancelling an order."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Cancel order
        url = reverse('order-cancel', args=[self.order.id])
        data = {
            'reason': 'Changed my mind'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')
        
        # Check that order was updated in database
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

    def test_get_order_timeline(self):
        """Test getting an order's timeline."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Add another tracking event
        OrderTracking.objects.create(
            order=self.order,
            status='confirmed',
            description='Order confirmed'
        )
        
        # Get timeline
        url = reverse('order-timeline', args=[self.order.id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['status'], 'confirmed')


class ReturnRequestViewSetTest(TestCase):
    """Test the ReturnRequestViewSet."""

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
        
        # Create a product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
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
            actual_delivery_date='2025-07-15'
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
        
        # Create a return request
        self.return_request = ReturnRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Create API client
        self.client = APIClient()

    def test_list_return_requests_customer(self):
        """Test that a customer can list their own return requests."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Create another return request for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'},
            actual_delivery_date='2025-07-15'
        )
        
        other_order_item = OrderItem.objects.create(
            order=other_order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('99.99'),
            total_price=Decimal('99.99'),
            status='delivered'
        )
        
        other_return_request = ReturnRequest.objects.create(
            order=other_order,
            order_item=other_order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Get return requests
        url = reverse('returnrequest-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.return_request.id))

    def test_list_return_requests_admin(self):
        """Test that an admin can list all return requests."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Create another return request for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'},
            actual_delivery_date='2025-07-15'
        )
        
        other_order_item = OrderItem.objects.create(
            order=other_order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('99.99'),
            total_price=Decimal('99.99'),
            status='delivered'
        )
        
        other_return_request = ReturnRequest.objects.create(
            order=other_order,
            order_item=other_order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        # Get return requests
        url = reverse('returnrequest-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both return requests

    @patch('apps.orders.views.ReturnService.create_return_request')
    def test_create_return_request(self, mock_create_return_request):
        """Test creating a return request."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Mock return request creation
        mock_return_request = ReturnRequest(
            id=999,
            order=self.order,
            order_item=self.order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        mock_create_return_request.return_value = mock_return_request
        
        # Create return request
        url = reverse('returnrequest-list')
        data = {
            'order_item_id': str(self.order_item.id),
            'quantity': 1,
            'reason': 'defective',
            'description': 'Product is defective'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_create_return_request.assert_called_once()

    def test_process_return_request(self):
        """Test processing a return request."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Process return request
        url = reverse('returnrequest-process', args=[self.return_request.id])
        data = {
            'status': 'approved',
            'notes': 'Approved by admin'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        
        # Check that return request was updated in database
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.status, 'approved')
        self.assertEqual(self.return_request.notes, 'Approved by admin')
        self.assertEqual(self.return_request.processed_by, self.admin)

    def test_process_return_request_customer_forbidden(self):
        """Test that a customer cannot process a return request."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Try to process return request
        url = reverse('returnrequest-process', args=[self.return_request.id])
        data = {
            'status': 'approved',
            'notes': 'Approved'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReplacementViewSetTest(TestCase):
    """Test the ReplacementViewSet."""

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
            actual_delivery_date='2025-07-15'
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
        
        # Create a return request
        self.return_request = ReturnRequest.objects.create(
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
        self.replacement = Replacement.objects.create(
            return_request=self.return_request,
            order=self.order,
            order_item=self.order_item,
            replacement_product=self.replacement_product,
            quantity=1,
            shipping_address=self.order.shipping_address,
            processed_by=self.admin
        )
        
        # Create API client
        self.client = APIClient()

    def test_list_replacements_customer(self):
        """Test that a customer can list their own replacements."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Create another replacement for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'},
            actual_delivery_date='2025-07-15'
        )
        
        other_order_item = OrderItem.objects.create(
            order=other_order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('99.99'),
            total_price=Decimal('99.99'),
            status='delivered'
        )
        
        other_return_request = ReturnRequest.objects.create(
            order=other_order,
            order_item=other_order_item,
            quantity=1,
            reason='defective',
            description='Product is defective',
            status='approved',
            refund_amount=Decimal('99.99'),
            refund_method='original'
        )
        
        other_replacement = Replacement.objects.create(
            return_request=other_return_request,
            order=other_order,
            order_item=other_order_item,
            replacement_product=self.replacement_product,
            quantity=1,
            shipping_address=other_order.shipping_address,
            processed_by=self.admin
        )
        
        # Get replacements
        url = reverse('replacement-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.replacement.id))

    @patch('apps.orders.views.ReturnService.create_replacement')
    def test_create_replacement(self, mock_create_replacement):
        """Test creating a replacement."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Mock replacement creation
        mock_replacement = Replacement(
            id=999,
            return_request=self.return_request,
            order=self.order,
            order_item=self.order_item,
            replacement_product=self.replacement_product,
            quantity=1,
            shipping_address=self.order.shipping_address,
            processed_by=self.admin
        )
        mock_create_replacement.return_value = mock_replacement
        
        # Create replacement
        url = reverse('replacement-list')
        data = {
            'return_request_id': str(self.return_request.id),
            'replacement_product_id': self.replacement_product.id,
            'quantity': 1,
            'notes': 'Replacement for defective product'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_create_replacement.assert_called_once()

    def test_create_replacement_customer_forbidden(self):
        """Test that a customer cannot create a replacement."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Try to create replacement
        url = reverse('replacement-list')
        data = {
            'return_request_id': str(self.return_request.id),
            'replacement_product_id': self.replacement_product.id,
            'quantity': 1,
            'notes': 'Replacement for defective product'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_replacement_status(self):
        """Test updating a replacement's status."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Update replacement status
        url = reverse('replacement-update-status', args=[self.replacement.id])
        data = {
            'status': 'shipped',
            'tracking_number': 'TRK123456789',
            'notes': 'Shipped via Express'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'shipped')
        self.assertEqual(response.data['tracking_number'], 'TRK123456789')
        
        # Check that replacement was updated in database
        self.replacement.refresh_from_db()
        self.assertEqual(self.replacement.status, 'shipped')
        self.assertEqual(self.replacement.tracking_number, 'TRK123456789')
        self.assertEqual(self.replacement.notes, 'Shipped via Express')

    def test_update_replacement_status_customer_forbidden(self):
        """Test that a customer cannot update a replacement's status."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Try to update replacement status
        url = reverse('replacement-update-status', args=[self.replacement.id])
        data = {
            'status': 'shipped',
            'tracking_number': 'TRK123456789',
            'notes': 'Shipped'
        }
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvoiceViewSetTest(TestCase):
    """Test the InvoiceViewSet."""

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
        
        # Create an order
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-20250718-12345',
            status='confirmed',
            payment_status='paid',
            total_amount=Decimal('127.99'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('18.00'),
            shipping_address={'address': '123 Test St'},
            billing_address={'address': '123 Test St'}
        )
        
        # Create an invoice
        self.invoice = Invoice.objects.create(
            order=self.order,
            invoice_number='INV-20250718-12345',
            invoice_date='2025-07-18',
            due_date='2025-07-18',
            billing_address=self.order.billing_address,
            shipping_address=self.order.shipping_address,
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('18.00'),
            shipping_amount=Decimal('10.00'),
            total_amount=Decimal('127.99'),
            terms_and_conditions='Standard terms and conditions apply.',
            file_path='invoices/INV-20250718-12345.pdf'
        )
        
        # Create API client
        self.client = APIClient()

    def test_list_invoices_customer(self):
        """Test that a customer can list their own invoices."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Create another invoice for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='confirmed',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'}
        )
        
        other_invoice = Invoice.objects.create(
            order=other_order,
            invoice_number='INV-20250718-67890',
            invoice_date='2025-07-18',
            due_date='2025-07-18',
            billing_address=other_order.billing_address,
            shipping_address=other_order.shipping_address,
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('0.00'),
            shipping_amount=Decimal('0.00'),
            total_amount=Decimal('99.99'),
            terms_and_conditions='Standard terms and conditions apply.',
            file_path='invoices/INV-20250718-67890.pdf'
        )
        
        # Get invoices
        url = reverse('invoice-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], self.invoice.invoice_number)

    def test_list_invoices_admin(self):
        """Test that an admin can list all invoices."""
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin)
        
        # Create another invoice for a different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_order = Order.objects.create(
            customer=other_user,
            order_number='ORD-20250718-67890',
            status='confirmed',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '456 Test St'},
            billing_address={'address': '456 Test St'}
        )
        
        other_invoice = Invoice.objects.create(
            order=other_order,
            invoice_number='INV-20250718-67890',
            invoice_date='2025-07-18',
            due_date='2025-07-18',
            billing_address=other_order.billing_address,
            shipping_address=other_order.shipping_address,
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('0.00'),
            shipping_amount=Decimal('0.00'),
            total_amount=Decimal('99.99'),
            terms_and_conditions='Standard terms and conditions apply.',
            file_path='invoices/INV-20250718-67890.pdf'
        )
        
        # Get invoices
        url = reverse('invoice-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both invoices

    def test_retrieve_invoice(self):
        """Test retrieving a single invoice."""
        # Authenticate as customer
        self.client.force_authenticate(user=self.customer)
        
        # Get invoice
        url = reverse('invoice-detail', args=[self.invoice.id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice_number'], self.invoice.invoice_number)
        self.assertEqual(response.data['order_number'], self.order.order_number)
        self.assertEqual(response.data['total_amount'], '127.99')