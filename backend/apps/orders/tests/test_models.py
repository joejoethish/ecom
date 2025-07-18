"""
Tests for the order models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.orders.models import Order, OrderItem, OrderTracking, ReturnRequest, Replacement, Invoice
from apps.products.models import Product, Category

User = get_user_model()


class OrderModelTest(TestCase):
    """Test the Order model."""

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
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('18.00'),
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            shipping_method='standard',
            payment_method='credit_card'
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('99.99'),
            total_price=Decimal('99.99')
        )
        
        # Create an order tracking event
        self.tracking_event = OrderTracking.objects.create(
            order=self.order,
            status='pending',
            description='Order created successfully'
        )

    def test_order_creation(self):
        """Test that an order can be created."""
        self.assertEqual(self.order.order_number, 'ORD-20250718-12345')
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.total_amount, Decimal('99.99'))
        self.assertEqual(self.order.customer, self.user)
        self.assertEqual(self.order.shipping_method, 'standard')
        self.assertEqual(self.order.payment_method, 'credit_card')
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

    def test_order_string_representation(self):
        """Test the string representation of an order."""
        self.assertEqual(str(self.order), f"Order {self.order.order_number}")

    def test_get_total_items(self):
        """Test the get_total_items method."""
        # Add another item to the order
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('99.99'),
            total_price=Decimal('199.98')
        )
        
        self.assertEqual(self.order.get_total_items(), 3)  # 1 + 2 = 3

    def test_get_order_timeline(self):
        """Test the get_order_timeline method."""
        # Add another tracking event
        OrderTracking.objects.create(
            order=self.order,
            status='confirmed',
            description='Order confirmed'
        )
        
        timeline = self.order.get_order_timeline()
        self.assertEqual(timeline.count(), 2)
        self.assertEqual(timeline.first().status, 'confirmed')  # Most recent first

    def test_add_timeline_event(self):
        """Test the add_timeline_event method."""
        event = self.order.add_timeline_event(
            status='processing',
            description='Order is being processed',
            user=self.user
        )
        
        self.assertEqual(event.status, 'processing')
        self.assertEqual(event.description, 'Order is being processed')
        self.assertEqual(event.created_by, self.user)
        self.assertEqual(event.order, self.order)

    def test_can_cancel(self):
        """Test the can_cancel method."""
        # Order should be cancellable when pending
        self.assertTrue(self.order.can_cancel())
        
        # Order should not be cancellable when shipped
        self.order.status = 'shipped'
        self.order.save()
        self.assertFalse(self.order.can_cancel())

    def test_can_return(self):
        """Test the can_return method."""
        # Order should not be returnable when not delivered
        self.assertFalse(self.order.can_return())
        
        # Order should be returnable when delivered within 30 days
        self.order.status = 'delivered'
        self.order.actual_delivery_date = timezone.now().date()
        self.order.save()
        self.assertTrue(self.order.can_return())
        
        # Order should not be returnable when delivered more than 30 days ago
        self.order.actual_delivery_date = timezone.now().date() - timedelta(days=31)
        self.order.save()
        self.assertFalse(self.order.can_return())


class OrderItemModelTest(TestCase):
    """Test the OrderItem model."""

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
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('18.00'),
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'}
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('99.99'),
            total_price=Decimal('199.98')
        )

    def test_order_item_creation(self):
        """Test that an order item can be created."""
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, Decimal('99.99'))
        self.assertEqual(self.order_item.total_price, Decimal('199.98'))
        self.assertEqual(self.order_item.status, 'pending')
        self.assertEqual(self.order_item.returned_quantity, 0)
        self.assertEqual(self.order_item.refunded_amount, Decimal('0'))

    def test_order_item_string_representation(self):
        """Test the string representation of an order item."""
        self.assertEqual(str(self.order_item), f"{self.product.name} x 2")

    def test_can_return(self):
        """Test the can_return method."""
        # Item should not be returnable when order is not delivered
        self.assertFalse(self.order_item.can_return())
        
        # Item should be returnable when order is delivered
        self.order.status = 'delivered'
        self.order.actual_delivery_date = timezone.now().date()
        self.order.save()
        self.assertTrue(self.order_item.can_return())
        
        # Item should not be returnable when fully returned
        self.order_item.returned_quantity = 2
        self.order_item.save()
        self.assertFalse(self.order_item.can_return())
        
        # Item should be partially returnable
        self.order_item.returned_quantity = 1
        self.order_item.save()
        self.assertTrue(self.order_item.can_return())


class OrderTrackingModelTest(TestCase):
    """Test the OrderTracking model."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create an order
        self.order = Order.objects.create(
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='pending',
            payment_status='pending',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'}
        )
        
        # Create an order tracking event
        self.tracking_event = OrderTracking.objects.create(
            order=self.order,
            status='pending',
            description='Order created successfully',
            location='Warehouse A',
            created_by=self.user
        )

    def test_order_tracking_creation(self):
        """Test that an order tracking event can be created."""
        self.assertEqual(self.tracking_event.order, self.order)
        self.assertEqual(self.tracking_event.status, 'pending')
        self.assertEqual(self.tracking_event.description, 'Order created successfully')
        self.assertEqual(self.tracking_event.location, 'Warehouse A')
        self.assertEqual(self.tracking_event.created_by, self.user)
        self.assertIsNotNone(self.tracking_event.created_at)

    def test_order_tracking_string_representation(self):
        """Test the string representation of an order tracking event."""
        expected = f"{self.order.order_number} - {self.tracking_event.status} at {self.tracking_event.created_at}"
        self.assertEqual(str(self.tracking_event), expected)


class ReturnRequestModelTest(TestCase):
    """Test the ReturnRequest model."""

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
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
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

    def test_return_request_creation(self):
        """Test that a return request can be created."""
        self.assertEqual(self.return_request.order, self.order)
        self.assertEqual(self.return_request.order_item, self.order_item)
        self.assertEqual(self.return_request.quantity, 1)
        self.assertEqual(self.return_request.reason, 'defective')
        self.assertEqual(self.return_request.description, 'Product is defective')
        self.assertEqual(self.return_request.status, 'pending')
        self.assertEqual(self.return_request.refund_amount, Decimal('99.99'))
        self.assertEqual(self.return_request.refund_method, 'original')
        self.assertIsNone(self.return_request.return_received_date)
        self.assertIsNone(self.return_request.refund_processed_date)
        self.assertIsNone(self.return_request.processed_by)
        self.assertIsNotNone(self.return_request.created_at)

    def test_return_request_string_representation(self):
        """Test the string representation of a return request."""
        expected = f"Return {self.return_request.id} for Order {self.order.order_number}"
        self.assertEqual(str(self.return_request), expected)


class ReplacementModelTest(TestCase):
    """Test the Replacement model."""

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
            customer=self.user,
            order_number='ORD-20250718-12345',
            status='delivered',
            payment_status='paid',
            total_amount=Decimal('99.99'),
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
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
            processed_by=self.user
        )

    def test_replacement_creation(self):
        """Test that a replacement can be created."""
        self.assertEqual(self.replacement.return_request, self.return_request)
        self.assertEqual(self.replacement.order, self.order)
        self.assertEqual(self.replacement.order_item, self.order_item)
        self.assertEqual(self.replacement.replacement_product, self.replacement_product)
        self.assertEqual(self.replacement.quantity, 1)
        self.assertEqual(self.replacement.status, 'pending')
        self.assertEqual(self.replacement.shipping_address, self.order.shipping_address)
        self.assertEqual(self.replacement.processed_by, self.user)
        self.assertIsNone(self.replacement.shipped_date)
        self.assertIsNone(self.replacement.delivered_date)
        self.assertIsNotNone(self.replacement.created_at)

    def test_replacement_string_representation(self):
        """Test the string representation of a replacement."""
        expected = f"Replacement {self.replacement.id} for Order {self.order.order_number}"
        self.assertEqual(str(self.replacement), expected)


class InvoiceModelTest(TestCase):
    """Test the Invoice model."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
            shipping_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'},
            billing_address={'address': '123 Test St', 'city': 'Test City', 'zip': '12345'}
        )
        
        # Create an invoice
        self.invoice = Invoice.objects.create(
            order=self.order,
            invoice_number='INV-20250718-12345',
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            billing_address=self.order.billing_address,
            shipping_address=self.order.shipping_address,
            subtotal=Decimal('99.99'),
            tax_amount=Decimal('18.00'),
            shipping_amount=Decimal('10.00'),
            total_amount=Decimal('127.99'),
            terms_and_conditions='Standard terms and conditions apply.'
        )

    def test_invoice_creation(self):
        """Test that an invoice can be created."""
        self.assertEqual(self.invoice.order, self.order)
        self.assertEqual(self.invoice.invoice_number, 'INV-20250718-12345')
        self.assertEqual(self.invoice.subtotal, Decimal('99.99'))
        self.assertEqual(self.invoice.tax_amount, Decimal('18.00'))
        self.assertEqual(self.invoice.shipping_amount, Decimal('10.00'))
        self.assertEqual(self.invoice.total_amount, Decimal('127.99'))
        self.assertEqual(self.invoice.billing_address, self.order.billing_address)
        self.assertEqual(self.invoice.shipping_address, self.order.shipping_address)
        self.assertEqual(self.invoice.terms_and_conditions, 'Standard terms and conditions apply.')
        self.assertIsNotNone(self.invoice.created_at)

    def test_invoice_string_representation(self):
        """Test the string representation of an invoice."""
        expected = f"Invoice {self.invoice.invoice_number} for Order {self.order.order_number}"
        self.assertEqual(str(self.invoice), expected)