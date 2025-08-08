"""
Comprehensive tests for the Order Management System.
"""
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category
from .order_models import (
    OrderSearchFilter, OrderWorkflow, OrderFraudScore, OrderNote,
    OrderEscalation, OrderSLA, OrderAllocation, OrderProfitability,
    OrderDocument, OrderQualityControl, OrderSubscription
)
from .order_services import (
    OrderSearchService, OrderStatusService, OrderModificationService,
    OrderFraudDetectionService, OrderEscalationService, OrderAllocationService
)

User = get_user_model()


class OrderModelsTestCase(TestCase):
    """Test cases for order management models."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('99.99'),
            category=self.category,
            stock_quantity=100
        )
        
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='TEST-001',
            status='pending',
            total_amount=Decimal('99.99')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            total_price=self.product.price
        )
    
    def test_order_search_filter_creation(self):
        """Test creating order search filter."""
        filter_data = {
            'status': 'pending',
            'date_from': '2024-01-01',
            'total_min': 50
        }
        
        search_filter = OrderSearchFilter.objects.create(
            name='Pending Orders',
            admin_user=self.admin_user,
            filters=filter_data,
            is_public=True
        )
        
        self.assertEqual(search_filter.name, 'Pending Orders')
        self.assertEqual(search_filter.filters['status'], 'pending')
        self.assertTrue(search_filter.is_public)
    
    def test_order_workflow_creation(self):
        """Test creating order workflow."""
        workflow = OrderWorkflow.objects.create(
            name='Auto Ship on Payment',
            description='Automatically ship order when payment is confirmed',
            from_status='pending',
            to_status='processing',
            conditions={'payment_required': True},
            actions=[{'type': 'send_email', 'template': 'order_processing'}],
            is_automatic=True,
            priority=10
        )
        
        self.assertEqual(workflow.name, 'Auto Ship on Payment')
        self.assertEqual(workflow.from_status, 'pending')
        self.assertEqual(workflow.to_status, 'processing')
        self.assertTrue(workflow.is_automatic)
    
    def test_order_fraud_score_creation(self):
        """Test creating order fraud score."""
        fraud_score = OrderFraudScore.objects.create(
            order=self.order,
            score=Decimal('75.50'),
            risk_level='high',
            risk_factors=['High value order', 'New customer'],
            is_flagged=True
        )
        
        self.assertEqual(fraud_score.order, self.order)
        self.assertEqual(fraud_score.score, Decimal('75.50'))
        self.assertEqual(fraud_score.risk_level, 'high')
        self.assertTrue(fraud_score.is_flagged)
    
    def test_order_note_creation(self):
        """Test creating order note."""
        note = OrderNote.objects.create(
            order=self.order,
            note_type='internal',
            title='Customer called',
            content='Customer called to confirm shipping address',
            created_by=self.admin_user,
            is_important=True
        )
        
        self.assertEqual(note.order, self.order)
        self.assertEqual(note.title, 'Customer called')
        self.assertEqual(note.created_by, self.admin_user)
        self.assertTrue(note.is_important)
    
    def test_order_escalation_creation(self):
        """Test creating order escalation."""
        escalation = OrderEscalation.objects.create(
            order=self.order,
            escalation_type='payment_issue',
            priority='high',
            title='Payment failed',
            description='Customer payment was declined',
            created_by=self.admin_user,
            sla_deadline=timezone.now() + timedelta(hours=8)
        )
        
        self.assertEqual(escalation.order, self.order)
        self.assertEqual(escalation.escalation_type, 'payment_issue')
        self.assertEqual(escalation.priority, 'high')
        self.assertFalse(escalation.is_overdue())
    
    def test_order_sla_tracking(self):
        """Test order SLA tracking."""
        sla = OrderSLA.objects.create(
            order=self.order,
            processing_deadline=timezone.now() + timedelta(hours=24),
            shipping_deadline=timezone.now() + timedelta(days=2),
            delivery_deadline=timezone.now() + timedelta(days=7)
        )
        
        self.assertEqual(sla.order, self.order)
        self.assertIsNotNone(sla.processing_deadline)
        self.assertIsNone(sla.overall_sla_met)
        
        # Test SLA calculation
        sla.calculate_sla_status()
        # Since order is still pending, SLA status should remain None
        self.assertIsNone(sla.overall_sla_met)
    
    def test_order_allocation_creation(self):
        """Test creating order allocation."""
        allocation_details = {
            str(self.order_item.id): {
                'product_id': self.product.id,
                'required_quantity': 1,
                'allocated_quantity': 1,
                'status': 'fully_allocated'
            }
        }
        
        allocation = OrderAllocation.objects.create(
            order=self.order,
            status='allocated',
            allocated_at=timezone.now(),
            allocated_by=self.admin_user,
            allocation_details=allocation_details
        )
        
        self.assertEqual(allocation.order, self.order)
        self.assertEqual(allocation.status, 'allocated')
        self.assertEqual(allocation.allocated_by, self.admin_user)
    
    def test_order_profitability_calculation(self):
        """Test order profitability calculation."""
        profitability = OrderProfitability.objects.create(
            order=self.order,
            gross_revenue=Decimal('99.99'),
            net_revenue=Decimal('99.99'),
            product_cost=Decimal('60.00'),
            shipping_cost=Decimal('10.00'),
            payment_processing_cost=Decimal('3.00')
        )
        
        profitability.calculate_profitability()
        
        self.assertEqual(profitability.gross_profit, Decimal('39.99'))
        self.assertEqual(profitability.total_cost, Decimal('73.00'))
        self.assertEqual(profitability.net_profit, Decimal('26.99'))
        self.assertGreater(profitability.profit_margin_percentage, 0)
    
    def test_order_subscription_creation(self):
        """Test creating order subscription."""
        subscription = OrderSubscription.objects.create(
            original_order=self.order,
            customer=self.customer,
            frequency='monthly',
            next_order_date=timezone.now().date() + timedelta(days=30),
            subscription_start_date=timezone.now().date(),
            items_config=[{
                'product_id': self.product.id,
                'quantity': 1
            }],
            shipping_address={'street': '123 Main St', 'city': 'Test City'},
            billing_address={'street': '123 Main St', 'city': 'Test City'},
            payment_method='credit_card'
        )
        
        self.assertEqual(subscription.original_order, self.order)
        self.assertEqual(subscription.frequency, 'monthly')
        self.assertEqual(subscription.status, 'active')
        
        # Test next order date calculation
        subscription.calculate_next_order_date()
        self.assertIsNotNone(subscription.next_order_date)


class OrderServicesTestCase(TestCase):
    """Test cases for order management services."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('99.99'),
            category=self.category,
            stock_quantity=100
        )
        
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='TEST-001',
            status='pending',
            total_amount=Decimal('99.99')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            total_price=self.product.price
        )
    
    def test_order_search_service(self):
        """Test order search service."""
        filters = {
            'status': 'pending',
            'total_min': 50,
            'customer_email': 'customer@test.com'
        }
        
        result = OrderSearchService.search_orders(filters, self.admin_user)
        
        self.assertIn('orders', result)
        self.assertIn('total_count', result)
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(len(result['orders']), 1)
        self.assertEqual(result['orders'][0].id, self.order.id)
    
    def test_save_search_filter(self):
        """Test saving search filter."""
        filters = {'status': 'pending', 'total_min': 50}
        
        search_filter = OrderSearchService.save_search_filter(
            name='My Filter',
            filters=filters,
            user=self.admin_user,
            is_public=False
        )
        
        self.assertEqual(search_filter.name, 'My Filter')
        self.assertEqual(search_filter.admin_user, self.admin_user)
        self.assertEqual(search_filter.filters, filters)
        self.assertFalse(search_filter.is_public)
    
    def test_order_status_update(self):
        """Test order status update service."""
        # Create a workflow
        workflow = OrderWorkflow.objects.create(
            name='Process Order',
            from_status='pending',
            to_status='processing',
            conditions={},
            actions=[{'type': 'create_note', 'title': 'Order Processing', 'content': 'Order moved to processing'}],
            is_active=True
        )
        
        success = OrderStatusService.update_order_status(
            order=self.order,
            new_status='processing',
            user=self.admin_user,
            notes='Manual status update'
        )
        
        self.assertTrue(success)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
        
        # Check if note was created
        notes = OrderNote.objects.filter(order=self.order)
        self.assertGreater(notes.count(), 0)
    
    def test_order_modification_add_item(self):
        """Test adding item to order."""
        # Create another product
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=50
        )
        
        item = OrderModificationService.add_item_to_order(
            order=self.order,
            product_id=product2.id,
            quantity=2,
            user=self.admin_user
        )
        
        self.assertEqual(item.product, product2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.order, self.order)
        
        # Check if order total was updated
        self.order.refresh_from_db()
        expected_total = Decimal('99.99') + (Decimal('49.99') * 2)
        self.assertEqual(self.order.total_amount, expected_total)
    
    def test_order_modification_remove_item(self):
        """Test removing item from order."""
        success = OrderModificationService.remove_item_from_order(
            order=self.order,
            item_id=self.order_item.id,
            user=self.admin_user
        )
        
        self.assertTrue(success)
        
        # Check if item was removed
        with self.assertRaises(OrderItem.DoesNotExist):
            OrderItem.objects.get(id=self.order_item.id)
        
        # Check if order total was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal('0.00'))
    
    def test_fraud_detection_service(self):
        """Test fraud detection service."""
        # Create a high-value order
        high_value_order = Order.objects.create(
            customer=self.customer,
            order_number='TEST-002',
            status='pending',
            total_amount=Decimal('1500.00')
        )
        
        fraud_score = OrderFraudDetectionService.calculate_fraud_score(high_value_order)
        
        self.assertIsNotNone(fraud_score)
        self.assertGreater(fraud_score.score, 0)
        self.assertIn('High value order', fraud_score.risk_factors)
        
        # Check if escalation was created for high-risk order
        if fraud_score.score >= 50:
            escalations = OrderEscalation.objects.filter(order=high_value_order)
            self.assertGreater(escalations.count(), 0)
    
    def test_escalation_service(self):
        """Test escalation service."""
        escalation = OrderEscalationService.create_escalation(
            order=self.order,
            escalation_type='payment_issue',
            title='Payment Failed',
            description='Customer payment was declined',
            priority='high',
            created_by=self.admin_user
        )
        
        self.assertEqual(escalation.order, self.order)
        self.assertEqual(escalation.escalation_type, 'payment_issue')
        self.assertEqual(escalation.priority, 'high')
        self.assertEqual(escalation.created_by, self.admin_user)
        self.assertIsNotNone(escalation.sla_deadline)
        
        # Test assigning escalation
        assignee = User.objects.create_user(
            username='assignee',
            email='assignee@test.com',
            password='testpass123'
        )
        
        OrderEscalationService.assign_escalation(
            escalation=escalation,
            assigned_to=assignee,
            assigned_by=self.admin_user
        )
        
        escalation.refresh_from_db()
        self.assertEqual(escalation.assigned_to, assignee)
        self.assertEqual(escalation.status, 'in_progress')
        
        # Test resolving escalation
        OrderEscalationService.resolve_escalation(
            escalation=escalation,
            resolved_by=assignee,
            resolution_notes='Issue resolved by contacting customer'
        )
        
        escalation.refresh_from_db()
        self.assertEqual(escalation.status, 'resolved')
        self.assertEqual(escalation.resolved_by, assignee)
        self.assertIsNotNone(escalation.resolved_at)
    
    def test_allocation_service(self):
        """Test allocation service."""
        allocation = OrderAllocationService.allocate_order_inventory(
            order=self.order,
            user=self.admin_user
        )
        
        self.assertEqual(allocation.order, self.order)
        self.assertEqual(allocation.status, 'allocated')
        self.assertEqual(allocation.allocated_by, self.admin_user)
        self.assertIsNotNone(allocation.allocation_details)
        
        # Test releasing allocation
        OrderAllocationService.release_allocation(
            allocation=allocation,
            user=self.admin_user
        )
        
        allocation.refresh_from_db()
        self.assertEqual(allocation.status, 'released')


class OrderAPITestCase(APITestCase):
    """Test cases for order management API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('99.99'),
            category=self.category,
            stock_quantity=100
        )
        
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='TEST-001',
            status='pending',
            total_amount=Decimal('99.99')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            total_price=self.product.price
        )
        
        # Authenticate as admin user
        self.client.force_authenticate(user=self.admin_user)
    
    def test_order_list_api(self):
        """Test order list API endpoint."""
        url = reverse('admin_panel:admin-orders-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_number'], 'TEST-001')
    
    def test_order_detail_api(self):
        """Test order detail API endpoint."""
        url = reverse('admin_panel:admin-orders-detail', kwargs={'pk': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'TEST-001')
        self.assertEqual(response.data['status'], 'pending')
        self.assertIn('items', response.data)
    
    def test_order_analytics_api(self):
        """Test order analytics API endpoint."""
        url = reverse('admin_panel:admin-orders-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orders', response.data)
        self.assertIn('total_revenue', response.data)
        self.assertIn('average_order_value', response.data)
        self.assertEqual(response.data['total_orders'], 1)
    
    def test_order_modification_api(self):
        """Test order modification API endpoint."""
        url = reverse('admin_panel:admin-orders-modify-order', kwargs={'pk': self.order.id})
        
        # Test adding item
        data = {
            'modification_type': 'add_item',
            'product_id': self.product.id,
            'quantity': 2,
            'reason': 'Customer requested additional items'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if order was updated
        self.order.refresh_from_db()
        self.assertGreater(self.order.total_amount, Decimal('99.99'))
    
    def test_order_split_api(self):
        """Test order split API endpoint."""
        # Add another item to the order first
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
            total_price=self.product.price * 2
        )
        
        url = reverse('admin_panel:admin-orders-split-order', kwargs={'pk': self.order.id})
        
        data = {
            'split_items': [
                {
                    'order_item_id': str(self.order_item.id),
                    'quantity': 1
                }
            ],
            'reason': 'Split for different shipping addresses',
            'notes': 'Customer requested split delivery'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_order', response.data)
        self.assertIn('original_order', response.data)
    
    def test_bulk_actions_api(self):
        """Test bulk actions API endpoint."""
        # Create another order
        order2 = Order.objects.create(
            customer=self.customer,
            order_number='TEST-002',
            status='pending',
            total_amount=Decimal('149.99')
        )
        
        url = reverse('admin_panel:admin-orders-bulk-actions')
        
        data = {
            'order_ids': [str(self.order.id), str(order2.id)],
            'action': 'add_note',
            'parameters': {
                'title': 'Bulk Note',
                'content': 'This is a bulk note added to multiple orders',
                'type': 'internal'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 2)
        
        # Check if notes were created
        notes = OrderNote.objects.filter(order__in=[self.order, order2], title='Bulk Note')
        self.assertEqual(notes.count(), 2)
    
    def test_order_export_api(self):
        """Test order export API endpoint."""
        url = reverse('admin_panel:admin-orders-export-orders')
        
        data = {
            'export_format': 'csv',
            'include_items': True,
            'fields': ['order_number', 'status', 'total_amount']
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_fraud_score_api(self):
        """Test fraud score API endpoints."""
        # Create fraud score
        fraud_score = OrderFraudScore.objects.create(
            order=self.order,
            score=Decimal('75.00'),
            risk_level='high',
            risk_factors=['High value order'],
            is_flagged=True
        )
        
        # Test list endpoint
        url = reverse('admin_panel:admin-order-fraud-scores-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test review endpoint
        url = reverse('admin_panel:admin-order-fraud-scores-review-fraud-score', kwargs={'pk': fraud_score.id})
        data = {
            'review_notes': 'Reviewed and approved',
            'is_flagged': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        fraud_score.refresh_from_db()
        self.assertEqual(fraud_score.reviewed_by, self.admin_user)
        self.assertFalse(fraud_score.is_flagged)
    
    def test_escalation_api(self):
        """Test escalation API endpoints."""
        # Create escalation
        escalation = OrderEscalation.objects.create(
            order=self.order,
            escalation_type='payment_issue',
            priority='high',
            title='Payment Failed',
            description='Customer payment was declined',
            created_by=self.admin_user
        )
        
        # Test list endpoint
        url = reverse('admin_panel:admin-order-escalations-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test assign endpoint
        assignee = User.objects.create_user(
            username='assignee',
            email='assignee@test.com',
            password='testpass123'
        )
        
        url = reverse('admin_panel:admin-order-escalations-assign-escalation', kwargs={'pk': escalation.id})
        data = {'assigned_to': assignee.id}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        escalation.refresh_from_db()
        self.assertEqual(escalation.assigned_to, assignee)
        
        # Test resolve endpoint
        url = reverse('admin_panel:admin-order-escalations-resolve-escalation', kwargs={'pk': escalation.id})
        data = {'resolution_notes': 'Issue resolved successfully'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        escalation.refresh_from_db()
        self.assertEqual(escalation.status, 'resolved')
    
    def test_sla_report_api(self):
        """Test SLA report API endpoint."""
        # Create SLA tracking
        OrderSLA.objects.create(
            order=self.order,
            processing_deadline=timezone.now() + timedelta(hours=24),
            overall_sla_met=True
        )
        
        url = reverse('admin_panel:admin-order-sla-sla-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orders', response.data)
        self.assertIn('overall_sla_compliance', response.data)
        self.assertEqual(response.data['total_orders'], 1)
    
    def test_profitability_report_api(self):
        """Test profitability report API endpoint."""
        # Create profitability data
        OrderProfitability.objects.create(
            order=self.order,
            gross_revenue=Decimal('99.99'),
            net_revenue=Decimal('99.99'),
            product_cost=Decimal('60.00'),
            net_profit=Decimal('39.99'),
            profit_margin_percentage=Decimal('40.00')
        )
        
        url = reverse('admin_panel:admin-order-profitability-profitability-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orders_analyzed', response.data)
        self.assertIn('total_profit', response.data)
        self.assertIn('average_profit_margin', response.data)
        self.assertEqual(response.data['total_orders_analyzed'], 1)
    
    def test_subscription_api(self):
        """Test subscription API endpoints."""
        # Create subscription
        subscription = OrderSubscription.objects.create(
            original_order=self.order,
            customer=self.customer,
            frequency='monthly',
            next_order_date=timezone.now().date() + timedelta(days=30),
            subscription_start_date=timezone.now().date(),
            items_config=[{'product_id': self.product.id, 'quantity': 1}],
            shipping_address={'street': '123 Main St'},
            billing_address={'street': '123 Main St'},
            payment_method='credit_card'
        )
        
        # Test list endpoint
        url = reverse('admin_panel:admin-order-subscriptions-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test pause endpoint
        url = reverse('admin_panel:admin-order-subscriptions-pause-subscription', kwargs={'pk': subscription.id})
        data = {'reason': 'Customer requested pause'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'paused')
        
        # Test resume endpoint
        url = reverse('admin_panel:admin-order-subscriptions-resume-subscription', kwargs={'pk': subscription.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'active')


class OrderIntegrationTestCase(TestCase):
    """Integration tests for the complete order management workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('99.99'),
            category=self.category,
            stock_quantity=100
        )
    
    def test_complete_order_workflow(self):
        """Test complete order management workflow."""
        # 1. Create order
        order = Order.objects.create(
            customer=self.customer,
            order_number='WORKFLOW-001',
            status='pending',
            total_amount=Decimal('99.99')
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            total_price=self.product.price
        )
        
        # 2. Calculate fraud score
        fraud_score = OrderFraudDetectionService.calculate_fraud_score(order)
        self.assertIsNotNone(fraud_score)
        
        # 3. Allocate inventory
        allocation = OrderAllocationService.allocate_order_inventory(order, self.admin_user)
        self.assertEqual(allocation.status, 'allocated')
        
        # 4. Create SLA tracking
        sla = OrderSLA.objects.create(
            order=order,
            processing_deadline=timezone.now() + timedelta(hours=24),
            shipping_deadline=timezone.now() + timedelta(days=2),
            delivery_deadline=timezone.now() + timedelta(days=7)
        )
        
        # 5. Update order status
        success = OrderStatusService.update_order_status(
            order=order,
            new_status='processing',
            user=self.admin_user,
            notes='Order approved and processing'
        )
        self.assertTrue(success)
        
        # 6. Add order note
        note = OrderNote.objects.create(
            order=order,
            note_type='internal',
            title='Order Processing Started',
            content='Order has been approved and moved to processing',
            created_by=self.admin_user
        )
        
        # 7. Calculate profitability
        profitability = OrderProfitability.objects.create(
            order=order,
            gross_revenue=order.total_amount,
            net_revenue=order.total_amount,
            product_cost=Decimal('60.00'),
            shipping_cost=Decimal('10.00'),
            payment_processing_cost=Decimal('3.00')
        )
        profitability.calculate_profitability()
        
        # 8. Verify complete workflow
        order.refresh_from_db()
        self.assertEqual(order.status, 'processing')
        self.assertTrue(hasattr(order, 'fraud_score'))
        self.assertTrue(hasattr(order, 'allocation'))
        self.assertTrue(hasattr(order, 'sla_tracking'))
        self.assertTrue(hasattr(order, 'profitability'))
        self.assertGreater(order.admin_notes.count(), 0)
        
        # 9. Test order modification
        product2 = Product.objects.create(
            name='Additional Product',
            slug='additional-product',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=50
        )
        
        OrderModificationService.add_item_to_order(
            order=order,
            product_id=product2.id,
            quantity=1,
            user=self.admin_user
        )
        
        order.refresh_from_db()
        self.assertEqual(order.items.count(), 2)
        self.assertGreater(order.total_amount, Decimal('99.99'))
        
        # 10. Complete order
        OrderStatusService.update_order_status(
            order=order,
            new_status='shipped',
            user=self.admin_user,
            notes='Order shipped successfully'
        )
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'shipped')
        
        print(f"✅ Complete order workflow test passed for order {order.order_number}")