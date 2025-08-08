"""
Tests for Advanced Inventory Management System.
"""
import json
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Product, Category
from .models import AdminUser
from .inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization,
    InventoryOptimizationItem, InventoryReport
)
from .inventory_services import (
    InventoryTrackingService, InventoryValuationService, InventoryAdjustmentService,
    InventoryTransferService, InventoryReservationService, InventoryAlertService,
    InventoryOptimizationService
)


class InventoryModelsTestCase(TestCase):
    """Test cases for inventory models."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass',
            role='admin'
        )
        
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            location='New York',
            address='123 Main St'
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            code='SUP001',
            email='supplier@test.com'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TEST001',
            price=Decimal('99.99'),
            category=self.category
        )
        
        self.location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='A',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
    
    def test_inventory_location_creation(self):
        """Test inventory location creation."""
        self.assertEqual(self.location.location_code, 'WH001-A-01-A-01')
        self.assertEqual(self.location.utilization_percentage, 0)
        self.assertTrue(self.location.is_active)
        self.assertFalse(self.location.is_blocked)
    
    def test_inventory_item_creation(self):
        """Test inventory item creation."""
        item = InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=50,
            unit_cost=Decimal('75.00'),
            serial_number='SN001',
            condition='new'
        )
        
        self.assertEqual(item.available_quantity, 50)
        self.assertFalse(item.is_expired)
        self.assertTrue(item.is_available)
        self.assertFalse(item.is_quarantined)
    
    def test_inventory_item_with_expiry(self):
        """Test inventory item with expiry date."""
        # Item expiring tomorrow
        item = InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=25,
            unit_cost=Decimal('75.00'),
            expiry_date=date.today() + timedelta(days=1)
        )
        
        self.assertFalse(item.is_expired)
        self.assertEqual(item.days_until_expiry, 1)
        
        # Expired item
        expired_item = InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=10,
            unit_cost=Decimal('75.00'),
            expiry_date=date.today() - timedelta(days=1)
        )
        
        self.assertTrue(expired_item.is_expired)
        self.assertEqual(expired_item.days_until_expiry, -1)
    
    def test_inventory_adjustment_creation(self):
        """Test inventory adjustment creation."""
        adjustment = InventoryAdjustment.objects.create(
            product=self.product,
            location=self.location,
            adjustment_type='increase',
            quantity_before=50,
            quantity_after=75,
            reason_code='RESTOCK',
            reason_description='Restocking from supplier',
            unit_cost=Decimal('75.00'),
            requested_by=self.admin_user
        )
        
        self.assertEqual(adjustment.adjustment_quantity, 25)
        self.assertEqual(adjustment.total_cost_impact, Decimal('1875.00'))
        self.assertEqual(adjustment.status, 'pending')
    
    def test_inventory_transfer_creation(self):
        """Test inventory transfer creation."""
        destination_location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='B',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
        
        transfer = InventoryTransfer.objects.create(
            product=self.product,
            source_location=self.location,
            destination_location=destination_location,
            quantity_requested=25,
            reason='Rebalancing stock',
            requested_by=self.admin_user
        )
        
        self.assertEqual(transfer.status, 'pending')
        self.assertFalse(transfer.is_complete)
        self.assertEqual(transfer.quantity_requested, 25)
    
    def test_inventory_reservation_creation(self):
        """Test inventory reservation creation."""
        expiry_date = timezone.now() + timedelta(hours=24)
        
        reservation = InventoryReservation.objects.create(
            product=self.product,
            location=self.location,
            reservation_type='order',
            quantity_reserved=10,
            expiry_date=expiry_date,
            reserved_by=self.admin_user,
            priority=1
        )
        
        self.assertEqual(reservation.status, 'active')
        self.assertEqual(reservation.remaining_quantity, 10)
        self.assertFalse(reservation.is_expired)
    
    def test_inventory_alert_creation(self):
        """Test inventory alert creation."""
        alert = InventoryAlert.objects.create(
            product=self.product,
            location=self.location,
            alert_type='low_stock',
            severity='medium',
            title='Low Stock Alert',
            description='Stock level is below reorder point',
            current_value=Decimal('5'),
            threshold_value=Decimal('10')
        )
        
        self.assertEqual(alert.status, 'active')
        self.assertEqual(alert.alert_type, 'low_stock')
        self.assertEqual(alert.severity, 'medium')


class InventoryServicesTestCase(TestCase):
    """Test cases for inventory services."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass',
            role='admin'
        )
        
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            location='New York',
            address='123 Main St'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TEST001',
            price=Decimal('99.99'),
            category=self.category
        )
        
        self.location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='A',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
        
        self.inventory_item = InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=100,
            unit_cost=Decimal('75.00')
        )
    
    def test_inventory_tracking_service(self):
        """Test inventory tracking service."""
        # Get real-time stock levels
        stock_data = InventoryTrackingService.get_real_time_stock_levels(self.warehouse.id)
        
        self.assertIn('total_items', stock_data)
        self.assertIn('total_quantity', stock_data)
        self.assertIn('total_value', stock_data)
        
        # Update stock level
        updated_item = InventoryTrackingService.update_stock_level(
            product_id=self.product.id,
            location_id=self.location.id,
            quantity_change=25,
            transaction_type='RESTOCK',
            user=self.admin_user,
            notes='Test restock'
        )
        
        self.assertEqual(updated_item.quantity, 125)
    
    def test_inventory_valuation_service(self):
        """Test inventory valuation service."""
        # Test FIFO valuation
        fifo_valuation = InventoryValuationService.calculate_fifo_valuation(
            product_id=self.product.id,
            warehouse_id=self.warehouse.id
        )
        
        self.assertEqual(fifo_valuation['total_quantity'], 100)
        self.assertEqual(fifo_valuation['total_value'], Decimal('7500.00'))
        self.assertEqual(fifo_valuation['unit_cost'], Decimal('75.00'))
        
        # Test weighted average valuation
        wa_valuation = InventoryValuationService.calculate_weighted_average_valuation(
            product_id=self.product.id,
            warehouse_id=self.warehouse.id
        )
        
        self.assertEqual(wa_valuation['method'], 'weighted_average')
        
        # Create valuation record
        valuation_record = InventoryValuationService.create_valuation_record(
            product_id=self.product.id,
            warehouse_id=self.warehouse.id,
            costing_method='fifo',
            user=self.admin_user
        )
        
        self.assertEqual(valuation_record.costing_method, 'fifo')
        self.assertEqual(valuation_record.total_quantity, 100)
    
    def test_inventory_adjustment_service(self):
        """Test inventory adjustment service."""
        # Create adjustment request
        adjustment = InventoryAdjustmentService.create_adjustment_request(
            product_id=self.product.id,
            location_id=self.location.id,
            quantity_after=125,
            adjustment_type='increase',
            reason_code='RESTOCK',
            reason_description='Restocking from supplier',
            user=self.admin_user,
            unit_cost=Decimal('75.00')
        )
        
        self.assertEqual(adjustment.status, 'pending')
        self.assertEqual(adjustment.quantity_before, 100)
        self.assertEqual(adjustment.quantity_after, 125)
        self.assertEqual(adjustment.adjustment_quantity, 25)
        
        # Approve adjustment
        approved_adjustment = InventoryAdjustmentService.approve_adjustment(
            adjustment.id, self.admin_user, 'Approved for restocking'
        )
        
        self.assertEqual(approved_adjustment.status, 'approved')
        self.assertEqual(approved_adjustment.approved_by, self.admin_user)
        
        # Apply adjustment
        applied_adjustment = InventoryAdjustmentService.apply_adjustment(
            adjustment.id, self.admin_user
        )
        
        self.assertEqual(applied_adjustment.status, 'applied')
        
        # Check inventory item was updated
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 125)
    
    def test_inventory_transfer_service(self):
        """Test inventory transfer service."""
        # Create destination location
        destination_location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='B',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
        
        # Create transfer request
        transfer = InventoryTransferService.create_transfer_request(
            product_id=self.product.id,
            source_location_id=self.location.id,
            destination_location_id=destination_location.id,
            quantity=25,
            reason='Rebalancing stock',
            user=self.admin_user
        )
        
        self.assertEqual(transfer.status, 'pending')
        self.assertEqual(transfer.quantity_requested, 25)
        
        # Ship transfer
        shipped_transfer = InventoryTransferService.ship_transfer(
            transfer.id, self.admin_user, 'TRK123'
        )
        
        self.assertEqual(shipped_transfer.status, 'in_transit')
        self.assertEqual(shipped_transfer.tracking_number, 'TRK123')
        
        # Check source item reserved quantity
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.reserved_quantity, 25)
        
        # Receive transfer
        received_transfer = InventoryTransferService.receive_transfer(
            transfer.id, 25, self.admin_user
        )
        
        self.assertEqual(received_transfer.status, 'completed')
        self.assertEqual(received_transfer.quantity_received, 25)
    
    def test_inventory_reservation_service(self):
        """Test inventory reservation service."""
        # Create reservation
        reservation = InventoryReservationService.create_reservation(
            product_id=self.product.id,
            location_id=self.location.id,
            quantity=20,
            reservation_type='order',
            expiry_hours=24,
            user=self.admin_user,
            priority=1
        )
        
        self.assertEqual(reservation.status, 'active')
        self.assertEqual(reservation.quantity_reserved, 20)
        
        # Check inventory item reserved quantity
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.reserved_quantity, 20)
        
        # Fulfill reservation
        fulfilled_reservation = InventoryReservationService.fulfill_reservation(
            reservation.id, 15, self.admin_user
        )
        
        self.assertEqual(fulfilled_reservation.status, 'partial')
        self.assertEqual(fulfilled_reservation.quantity_fulfilled, 15)
        self.assertEqual(fulfilled_reservation.remaining_quantity, 5)
        
        # Check inventory item quantities
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 85)  # 100 - 15
        self.assertEqual(self.inventory_item.reserved_quantity, 5)  # 20 - 15
    
    def test_inventory_alert_service(self):
        """Test inventory alert service."""
        # Create alert
        alert = InventoryAlertService.create_alert(
            product=self.product,
            location=self.location,
            alert_type='low_stock',
            severity='medium',
            title='Low Stock Alert',
            description='Stock level is below reorder point',
            current_value=Decimal('5'),
            threshold_value=Decimal('10')
        )
        
        self.assertEqual(alert.status, 'active')
        self.assertEqual(alert.alert_type, 'low_stock')
        
        # Acknowledge alert
        acknowledged_alert = InventoryAlertService.acknowledge_alert(
            alert.id, self.admin_user, 'Acknowledged by admin'
        )
        
        self.assertEqual(acknowledged_alert.status, 'acknowledged')
        self.assertEqual(acknowledged_alert.acknowledged_by, self.admin_user)
        
        # Resolve alert
        resolved_alert = InventoryAlertService.resolve_alert(
            alert.id, self.admin_user, 'Stock replenished'
        )
        
        self.assertEqual(resolved_alert.status, 'resolved')
        self.assertEqual(resolved_alert.resolved_by, self.admin_user)
    
    def test_inventory_optimization_service(self):
        """Test inventory optimization service."""
        # Create additional test data for ABC analysis
        for i in range(5):
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                sku=f'PROD{i:03d}',
                price=Decimal('50.00'),
                category=self.category
            )
            
            InventoryItem.objects.create(
                product=product,
                location=self.location,
                quantity=50 + i * 10,
                unit_cost=Decimal('40.00')
            )
        
        # Perform ABC analysis
        optimization = InventoryOptimizationService.perform_abc_analysis(
            warehouse_id=self.warehouse.id,
            user=self.admin_user,
            period_days=365
        )
        
        self.assertEqual(optimization.analysis_type, 'abc')
        self.assertGreater(optimization.total_products_analyzed, 0)
        self.assertGreater(optimization.total_value_analyzed, 0)
        
        # Check optimization items were created
        optimization_items = optimization.optimization_items.all()
        self.assertGreater(optimization_items.count(), 0)
        
        # Test slow-moving items identification
        slow_moving_items = InventoryOptimizationService.identify_slow_moving_items(
            warehouse_id=self.warehouse.id,
            days_threshold=90
        )
        
        self.assertIsInstance(slow_moving_items, list)


class InventoryAPITestCase(APITestCase):
    """Test cases for inventory API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass',
            role='admin'
        )
        
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            location='New York',
            address='123 Main St'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TEST001',
            price=Decimal('99.99'),
            category=self.category
        )
        
        self.location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='A',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.admin_user)
    
    def test_inventory_location_crud(self):
        """Test inventory location CRUD operations."""
        # List locations
        url = reverse('admin_panel:admin-inventory-locations-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Create location
        data = {
            'warehouse': self.warehouse.id,
            'zone': 'B',
            'aisle': '02',
            'shelf': 'B',
            'bin': '01',
            'capacity': 150,
            'location_type': 'standard'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location_code'], 'WH001-B-02-B-01')
        
        # Retrieve location
        location_id = response.data['id']
        url = reverse('admin_panel:admin-inventory-locations-detail', args=[location_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update location
        data = {'capacity': 200}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['capacity'], 200)
        
        # Block location
        url = reverse('admin_panel:admin-inventory-locations-block-location', args=[location_id])
        data = {'reason': 'Maintenance required'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Unblock location
        url = reverse('admin_panel:admin-inventory-locations-unblock-location', args=[location_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_inventory_item_crud(self):
        """Test inventory item CRUD operations."""
        # Create inventory item
        url = reverse('admin_panel:admin-inventory-items-list')
        data = {
            'product': self.product.id,
            'location': self.location.id,
            'quantity': 100,
            'unit_cost': '75.00',
            'serial_number': 'SN001',
            'condition': 'new'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        item_id = response.data['id']
        
        # List items
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Quarantine item
        url = reverse('admin_panel:admin-inventory-items-quarantine', args=[item_id])
        data = {'reason': 'Quality issue detected'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Release from quarantine
        url = reverse('admin_panel:admin-inventory-items-release-quarantine', args=[item_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get expiring items
        url = reverse('admin_panel:admin-inventory-items-expiring-items')
        response = self.client.get(url, {'days': 30})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_inventory_adjustment_workflow(self):
        """Test inventory adjustment workflow."""
        # Create inventory item first
        inventory_item = InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=100,
            unit_cost=Decimal('75.00')
        )
        
        # Create adjustment request
        url = reverse('admin_panel:admin-inventory-adjustments-list')
        data = {
            'product': self.product.id,
            'location': self.location.id,
            'adjustment_type': 'increase',
            'quantity_before': 100,
            'quantity_after': 125,
            'reason_code': 'RESTOCK',
            'reason_description': 'Restocking from supplier',
            'unit_cost': '75.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        adjustment_id = response.data['id']
        
        # Approve adjustment
        url = reverse('admin_panel:admin-inventory-adjustments-approve', args=[adjustment_id])
        data = {'notes': 'Approved for restocking'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Apply adjustment
        url = reverse('admin_panel:admin-inventory-adjustments-apply', args=[adjustment_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventory was updated
        inventory_item.refresh_from_db()
        self.assertEqual(inventory_item.quantity, 125)
    
    def test_inventory_dashboard(self):
        """Test inventory dashboard endpoint."""
        # Create some test data
        InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=50,
            unit_cost=Decimal('75.00')
        )
        
        # Get dashboard overview
        url = reverse('admin_panel:admin-inventory-dashboard-overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check dashboard data structure
        self.assertIn('total_products', response.data)
        self.assertIn('total_locations', response.data)
        self.assertIn('total_value', response.data)
        self.assertIn('active_alerts', response.data)
        
        # Get stock summary
        url = reverse('admin_panel:admin-inventory-dashboard-stock-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('warehouses', response.data)
    
    def test_inventory_valuation_calculation(self):
        """Test inventory valuation calculation."""
        # Create inventory item
        InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=100,
            unit_cost=Decimal('75.00')
        )
        
        # Calculate valuation
        url = reverse('admin_panel:admin-inventory-valuations-calculate-valuation')
        data = {
            'product_id': self.product.id,
            'warehouse_id': self.warehouse.id,
            'costing_method': 'fifo'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['costing_method'], 'fifo')
        self.assertEqual(response.data['total_quantity'], 100)
    
    def test_inventory_optimization_abc_analysis(self):
        """Test ABC analysis endpoint."""
        # Create test inventory items
        for i in range(3):
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                sku=f'PROD{i:03d}',
                price=Decimal('50.00'),
                category=self.category
            )
            
            InventoryItem.objects.create(
                product=product,
                location=self.location,
                quantity=50 + i * 20,
                unit_cost=Decimal('40.00')
            )
        
        # Run ABC analysis
        url = reverse('admin_panel:admin-inventory-optimizations-run-abc-analysis')
        data = {
            'warehouse_id': self.warehouse.id,
            'period_days': 365
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['analysis_type'], 'abc')
        
        # Get category breakdown
        optimization_id = response.data['id']
        url = reverse('admin_panel:admin-inventory-optimizations-category-breakdown', args=[optimization_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('breakdown', response.data)
    
    def test_inventory_alerts_management(self):
        """Test inventory alerts management."""
        # Create alert
        alert = InventoryAlert.objects.create(
            product=self.product,
            location=self.location,
            alert_type='low_stock',
            severity='medium',
            title='Low Stock Alert',
            description='Stock level is below reorder point',
            current_value=Decimal('5'),
            threshold_value=Decimal('10')
        )
        
        # List alerts
        url = reverse('admin_panel:admin-inventory-alerts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Acknowledge alert
        url = reverse('admin_panel:admin-inventory-alerts-acknowledge', args=[alert.id])
        data = {'notes': 'Acknowledged by admin'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Resolve alert
        url = reverse('admin_panel:admin-inventory-alerts-resolve', args=[alert.id])
        data = {'notes': 'Stock replenished'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get active alerts
        url = reverse('admin_panel:admin-inventory-alerts-active-alerts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_inventory_transfer_workflow(self):
        """Test inventory transfer workflow."""
        # Create inventory item and destination location
        InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=100,
            unit_cost=Decimal('75.00')
        )
        
        destination_location = InventoryLocation.objects.create(
            warehouse=self.warehouse,
            zone='B',
            aisle='01',
            shelf='A',
            bin='01',
            capacity=100
        )
        
        # Create transfer request
        url = reverse('admin_panel:admin-inventory-transfers-list')
        data = {
            'product': self.product.id,
            'source_location': self.location.id,
            'destination_location': destination_location.id,
            'quantity_requested': 25,
            'reason': 'Rebalancing stock'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        transfer_id = response.data['id']
        
        # Ship transfer
        url = reverse('admin_panel:admin-inventory-transfers-ship', args=[transfer_id])
        data = {'tracking_number': 'TRK123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Receive transfer
        url = reverse('admin_panel:admin-inventory-transfers-receive', args=[transfer_id])
        data = {'quantity_received': 25}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_inventory_reservation_workflow(self):
        """Test inventory reservation workflow."""
        # Create inventory item
        InventoryItem.objects.create(
            product=self.product,
            location=self.location,
            quantity=100,
            unit_cost=Decimal('75.00')
        )
        
        # Create reservation
        url = reverse('admin_panel:admin-inventory-reservations-list')
        data = {
            'product': self.product.id,
            'location': self.location.id,
            'reservation_type': 'order',
            'quantity_reserved': 20,
            'expiry_date': (timezone.now() + timedelta(hours=24)).isoformat(),
            'priority': 1
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        reservation_id = response.data['id']
        
        # Fulfill reservation
        url = reverse('admin_panel:admin-inventory-reservations-fulfill', args=[reservation_id])
        data = {'quantity_fulfilled': 15}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cancel remaining reservation
        url = reverse('admin_panel:admin-inventory-reservations-cancel', args=[reservation_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)