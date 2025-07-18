from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from apps.inventory.models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)
from apps.inventory.services import InventoryService, PurchaseOrderService
from apps.products.models import Product, Category

User = get_user_model()


class InventoryServiceTest(TestCase):
    """Test cases for the InventoryService."""
    
    def setUp(self):
        # Create required related objects
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            category=self.category
        )
        
        self.product2 = Product.objects.create(
            name="Second Product",
            description="Another Description",
            price=Decimal('149.99'),
            category=self.category
        )
        
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="WH001",
            location="New York"
        )
        
        self.warehouse2 = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="WH002",
            location="Los Angeles"
        )
        
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="SUP001"
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Create inventory
        self.inventory = Inventory.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=100,
            reserved_quantity=10,
            minimum_stock_level=20,
            maximum_stock_level=200,
            reorder_point=50,
            cost_price=Decimal('50.00'),
            supplier=self.supplier
        )
        
        # Create second inventory
        self.inventory2 = Inventory.objects.create(
            product=self.product2,
            warehouse=self.warehouse,
            quantity=50,
            reserved_quantity=5,
            minimum_stock_level=10,
            maximum_stock_level=100,
            reorder_point=25,
            cost_price=Decimal('75.00'),
            supplier=self.supplier
        )
    
    def test_add_stock(self):
        """Test adding stock to inventory."""
        # Add 50 units to inventory
        transaction = InventoryService.add_stock(
            inventory=self.inventory,
            quantity=50,
            user=self.user,
            transaction_type="PURCHASE",
            reference_number="REF001",
            batch_number="BATCH001",
            unit_cost=Decimal('48.00'),
            notes="Test stock addition"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check inventory quantity was updated
        self.assertEqual(self.inventory.quantity, 150)  # 100 + 50
        
        # Check transaction was created correctly
        self.assertEqual(transaction.inventory, self.inventory)
        self.assertEqual(transaction.transaction_type, "PURCHASE")
        self.assertEqual(transaction.quantity, 50)
        self.assertEqual(transaction.reference_number, "REF001")
        self.assertEqual(transaction.batch_number, "BATCH001")
        self.assertEqual(transaction.unit_cost, Decimal('48.00'))
        self.assertEqual(transaction.notes, "Test stock addition")
        self.assertEqual(transaction.created_by, self.user)
    
    def test_add_stock_with_negative_quantity(self):
        """Test adding stock with negative quantity raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.add_stock(
                inventory=self.inventory,
                quantity=-50,
                user=self.user
            )
    
    def test_remove_stock(self):
        """Test removing stock from inventory."""
        # Remove 30 units from inventory
        transaction = InventoryService.remove_stock(
            inventory=self.inventory,
            quantity=30,
            user=self.user,
            transaction_type="SALE",
            reference_number="ORDER001",
            notes="Test stock removal"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check inventory quantity was updated
        self.assertEqual(self.inventory.quantity, 70)  # 100 - 30
        
        # Check transaction was created correctly
        self.assertEqual(transaction.inventory, self.inventory)
        self.assertEqual(transaction.transaction_type, "SALE")
        self.assertEqual(transaction.quantity, -30)  # Negative for removals
        self.assertEqual(transaction.reference_number, "ORDER001")
        self.assertEqual(transaction.notes, "Test stock removal")
        self.assertEqual(transaction.created_by, self.user)
    
    def test_remove_stock_with_negative_quantity(self):
        """Test removing stock with negative quantity raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.remove_stock(
                inventory=self.inventory,
                quantity=-30,
                user=self.user
            )
    
    def test_remove_stock_with_insufficient_quantity(self):
        """Test removing more stock than available raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.remove_stock(
                inventory=self.inventory,
                quantity=100,  # Available is 90 (100 - 10 reserved)
                user=self.user
            )
    
    def test_reserve_stock(self):
        """Test reserving stock."""
        # Reserve 20 units
        result = InventoryService.reserve_stock(
            inventory=self.inventory,
            quantity=20,
            user=self.user,
            reference_number="ORDER002",
            notes="Test stock reservation"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check reservation was successful
        self.assertTrue(result)
        
        # Check reserved quantity was updated
        self.assertEqual(self.inventory.reserved_quantity, 30)  # 10 + 20
        
        # Check total quantity remains unchanged
        self.assertEqual(self.inventory.quantity, 100)
        
        # Check available quantity was updated
        self.assertEqual(self.inventory.available_quantity, 70)  # 100 - 30
        
        # Check transaction was created for audit trail
        transaction = InventoryTransaction.objects.filter(
            inventory=self.inventory,
            transaction_type="ADJUSTMENT",
            reference_number="ORDER002"
        ).latest('created_at')
        
        self.assertEqual(transaction.quantity, 0)  # Net quantity change is 0
        self.assertIn("Reserved 20 units", transaction.notes)
    
    def test_reserve_stock_with_insufficient_quantity(self):
        """Test reserving more stock than available raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.reserve_stock(
                inventory=self.inventory,
                quantity=100,  # Available is 90 (100 - 10 reserved)
                user=self.user
            )
    
    def test_release_reserved_stock(self):
        """Test releasing reserved stock."""
        # Release 5 units from the 10 reserved
        result = InventoryService.release_reserved_stock(
            inventory=self.inventory,
            quantity=5,
            user=self.user,
            reference_number="ORDER003",
            notes="Test release reservation"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check release was successful
        self.assertTrue(result)
        
        # Check reserved quantity was updated
        self.assertEqual(self.inventory.reserved_quantity, 5)  # 10 - 5
        
        # Check total quantity remains unchanged
        self.assertEqual(self.inventory.quantity, 100)
        
        # Check available quantity was updated
        self.assertEqual(self.inventory.available_quantity, 95)  # 100 - 5
        
        # Check transaction was created for audit trail
        transaction = InventoryTransaction.objects.filter(
            inventory=self.inventory,
            transaction_type="ADJUSTMENT",
            reference_number="ORDER003"
        ).latest('created_at')
        
        self.assertEqual(transaction.quantity, 0)  # Net quantity change is 0
        self.assertIn("Released 5 reserved units", transaction.notes)
    
    def test_release_more_than_reserved(self):
        """Test releasing more stock than reserved raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.release_reserved_stock(
                inventory=self.inventory,
                quantity=20,  # Only 10 are reserved
                user=self.user
            )
    
    def test_transfer_stock(self):
        """Test transferring stock between warehouses."""
        # Create second warehouse and inventory
        warehouse2 = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="WH002",
            location="Los Angeles"
        )
        
        inventory2 = Inventory.objects.create(
            product=self.product,
            warehouse=warehouse2,
            quantity=50,
            cost_price=Decimal('52.00')
        )
        
        # Transfer 30 units from inventory1 to inventory2
        source_transaction, dest_transaction = InventoryService.transfer_stock(
            source_inventory=self.inventory,
            destination_inventory=inventory2,
            quantity=30,
            user=self.user,
            reference_number="TRANSFER001",
            notes="Test stock transfer"
        )
        
        # Refresh inventories from database
        self.inventory.refresh_from_db()
        inventory2.refresh_from_db()
        
        # Check quantities were updated
        self.assertEqual(self.inventory.quantity, 70)  # 100 - 30
        self.assertEqual(inventory2.quantity, 80)  # 50 + 30
        
        # Check transactions were created correctly
        self.assertEqual(source_transaction.inventory, self.inventory)
        self.assertEqual(source_transaction.transaction_type, "TRANSFER")
        self.assertEqual(source_transaction.quantity, -30)
        self.assertEqual(source_transaction.reference_number, "TRANSFER001")
        self.assertEqual(source_transaction.source_warehouse, self.warehouse)
        self.assertEqual(source_transaction.destination_warehouse, warehouse2)
        
        self.assertEqual(dest_transaction.inventory, inventory2)
        self.assertEqual(dest_transaction.transaction_type, "TRANSFER")
        self.assertEqual(dest_transaction.quantity, 30)
        self.assertEqual(dest_transaction.reference_number, "TRANSFER001")
        self.assertEqual(dest_transaction.source_warehouse, self.warehouse)
        self.assertEqual(dest_transaction.destination_warehouse, warehouse2)
    
    def test_transfer_with_insufficient_stock(self):
        """Test transferring more stock than available raises error."""
        warehouse2 = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="WH002",
            location="Los Angeles"
        )
        
        inventory2 = Inventory.objects.create(
            product=self.product,
            warehouse=warehouse2,
            quantity=50,
            cost_price=Decimal('52.00')
        )
        
        with self.assertRaises(ValidationError):
            InventoryService.transfer_stock(
                source_inventory=self.inventory,
                destination_inventory=inventory2,
                quantity=100,  # Available is 90 (100 - 10 reserved)
                user=self.user
            )
    
    def test_transfer_between_different_products(self):
        """Test transferring between different products raises error."""
        # Create second product and inventory
        product2 = Product.objects.create(
            name="Another Product",
            description="Another Description",
            price=Decimal('149.99'),
            category=self.category
        )
        
        inventory2 = Inventory.objects.create(
            product=product2,
            warehouse=self.warehouse,
            quantity=50,
            cost_price=Decimal('100.00')
        )
        
        with self.assertRaises(ValidationError):
            InventoryService.transfer_stock(
                source_inventory=self.inventory,
                destination_inventory=inventory2,
                quantity=30,
                user=self.user
            )
    
    def test_adjust_inventory(self):
        """Test adjusting inventory."""
        # Adjust inventory by +20 units
        transaction = InventoryService.adjust_inventory(
            inventory=self.inventory,
            adjustment_quantity=20,
            user=self.user,
            reason="Found additional stock during audit",
            reference_number="ADJUST001",
            notes="Test adjustment"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check quantity was updated
        self.assertEqual(self.inventory.quantity, 120)  # 100 + 20
        
        # Check transaction was created correctly
        self.assertEqual(transaction.inventory, self.inventory)
        self.assertEqual(transaction.transaction_type, "ADJUSTMENT")
        self.assertEqual(transaction.quantity, 20)
        self.assertEqual(transaction.reference_number, "ADJUST001")
        self.assertIn("Found additional stock during audit", transaction.notes)
        
        # Test negative adjustment
        transaction = InventoryService.adjust_inventory(
            inventory=self.inventory,
            adjustment_quantity=-10,
            user=self.user,
            reason="Damaged goods",
            reference_number="ADJUST002"
        )
        
        # Refresh inventory from database
        self.inventory.refresh_from_db()
        
        # Check quantity was updated
        self.assertEqual(self.inventory.quantity, 110)  # 120 - 10
        
        # Check transaction was created correctly
        self.assertEqual(transaction.quantity, -10)
        self.assertIn("Damaged goods", transaction.notes)
    
    def test_adjust_inventory_with_zero_quantity(self):
        """Test adjusting inventory with zero quantity raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.adjust_inventory(
                inventory=self.inventory,
                adjustment_quantity=0,
                user=self.user,
                reason="No change"
            )
    
    def test_adjust_inventory_with_excessive_negative_quantity(self):
        """Test adjusting inventory with excessive negative quantity raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.adjust_inventory(
                inventory=self.inventory,
                adjustment_quantity=-150,  # More than available 100
                user=self.user,
                reason="Too much reduction"
            )
    
    def test_get_low_stock_items(self):
        """Test getting low stock items."""
        # Create additional inventory items with different stock levels
        product2 = Product.objects.create(
            name="Low Stock Product",
            description="Description",
            price=Decimal('79.99'),
            category=self.category
        )
        
        low_inventory = Inventory.objects.create(
            product=product2,
            warehouse=self.warehouse,
            quantity=10,  # Below reorder point
            reorder_point=20,
            cost_price=Decimal('40.00')
        )
        
        # Get low stock items
        low_stock_items = InventoryService.get_low_stock_items()
        
        # Check only the low stock item is returned
        self.assertEqual(low_stock_items.count(), 1)
        self.assertEqual(low_stock_items.first(), low_inventory)
    
    def test_get_overstock_items(self):
        """Test getting overstock items."""
        # Create additional inventory item with overstock
        product3 = Product.objects.create(
            name="Overstock Product",
            description="Description",
            price=Decimal('59.99'),
            category=self.category
        )
        
        overstock_inventory = Inventory.objects.create(
            product=product3,
            warehouse=self.warehouse,
            quantity=300,  # Above maximum stock level
            maximum_stock_level=250,
            cost_price=Decimal('30.00')
        )
        
        # Get overstock items
        overstock_items = InventoryService.get_overstock_items()
        
        # Check only the overstock item is returned
        self.assertEqual(overstock_items.count(), 1)
        self.assertEqual(overstock_items.first(), overstock_inventory)
    
    def test_get_stock_value(self):
        """Test calculating stock value."""
        # Create additional inventory in another warehouse
        warehouse2 = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="WH002",
            location="Los Angeles"
        )
        
        Inventory.objects.create(
            product=self.product,
            warehouse=warehouse2,
            quantity=200,
            cost_price=Decimal('55.00')
        )
        
        # Calculate stock value
        stock_value = InventoryService.get_stock_value()
        
        # Expected values:
        # Warehouse 1: 100 * 50.00 = 5000.00
        # Warehouse 2: 200 * 55.00 = 11000.00
        # Total: 16000.00
        
        self.assertEqual(stock_value['total_value'], Decimal('16000.00'))
        
        # Check warehouse breakdown
        warehouse_values = {w['name']: w['inventory_value'] for w in stock_value['warehouse_breakdown']}
        self.assertEqual(warehouse_values['Main Warehouse'], Decimal('5000.00'))
        self.assertEqual(warehouse_values['Secondary Warehouse'], Decimal('11000.00'))
    
    def test_bulk_update_inventory(self):
        """Test bulk updating inventory."""
        # Define inventory updates
        inventory_updates = [
            {
                'inventory_id': self.inventory.id,
                'quantity': 20  # Add 20 units
            },
            {
                'inventory_id': self.inventory2.id,
                'quantity': -10  # Remove 10 units
            }
        ]
        
        # Perform bulk update
        transactions = InventoryService.bulk_update_inventory(
            inventory_updates=inventory_updates,
            user=self.user,
            reference_number="BULK001",
            notes="Test bulk update"
        )
        
        # Check transactions were created
        self.assertEqual(len(transactions), 2)
        
        # Check first transaction (addition)
        self.assertEqual(transactions[0].inventory, self.inventory)
        self.assertEqual(transactions[0].quantity, 20)
        self.assertEqual(transactions[0].reference_number, "BULK001")
        self.assertIn("Test bulk update", transactions[0].notes)
        
        # Check second transaction (removal)
        self.assertEqual(transactions[1].inventory, self.inventory2)
        self.assertEqual(transactions[1].quantity, -10)
        self.assertEqual(transactions[1].reference_number, "BULK001")
        self.assertIn("Test bulk update", transactions[1].notes)
        
        # Refresh inventories from database
        self.inventory.refresh_from_db()
        self.inventory2.refresh_from_db()
        
        # Check quantities were updated
        self.assertEqual(self.inventory.quantity, 120)  # 100 + 20
        self.assertEqual(self.inventory2.quantity, 40)  # 50 - 10
    
    def test_bulk_update_with_invalid_inventory_id(self):
        """Test bulk update with invalid inventory ID raises error."""
        # Define inventory updates with invalid ID
        inventory_updates = [
            {
                'inventory_id': 9999,  # Non-existent ID
                'quantity': 20
            }
        ]
        
        # Attempt bulk update with invalid ID
        with self.assertRaises(ValidationError):
            InventoryService.bulk_update_inventory(
                inventory_updates=inventory_updates,
                user=self.user
            )
    
    def test_update_alert_settings(self):
        """Test updating inventory alert settings."""
        # Update alert settings
        updated_inventory = InventoryService.update_alert_settings(
            inventory_id=self.inventory.id,
            minimum_stock_level=30,
            maximum_stock_level=250,
            reorder_point=60
        )
        
        # Check settings were updated
        self.assertEqual(updated_inventory.minimum_stock_level, 30)
        self.assertEqual(updated_inventory.maximum_stock_level, 250)
        self.assertEqual(updated_inventory.reorder_point, 60)
        
        # Refresh from database to confirm persistence
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.minimum_stock_level, 30)
        self.assertEqual(self.inventory.maximum_stock_level, 250)
        self.assertEqual(self.inventory.reorder_point, 60)
    
    def test_update_alert_settings_partial(self):
        """Test partial update of inventory alert settings."""
        # Update only reorder point
        updated_inventory = InventoryService.update_alert_settings(
            inventory_id=self.inventory.id,
            reorder_point=75
        )
        
        # Check only reorder point was updated
        self.assertEqual(updated_inventory.minimum_stock_level, 20)  # Unchanged
        self.assertEqual(updated_inventory.maximum_stock_level, 200)  # Unchanged
        self.assertEqual(updated_inventory.reorder_point, 75)  # Updated
    
    def test_update_alert_settings_invalid_id(self):
        """Test updating alert settings with invalid inventory ID raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.update_alert_settings(
                inventory_id=9999,  # Non-existent ID
                minimum_stock_level=30
            )
    
    def test_generate_inventory_report_stock_levels(self):
        """Test generating stock levels report."""
        # Generate stock levels report
        report = InventoryService.generate_inventory_report(report_type='stock_levels')
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('details', report)
        
        # Check summary data
        summary = report['summary']
        self.assertEqual(summary['total_items'], 2)
        self.assertEqual(summary['total_quantity'], 150)  # 100 + 50
        self.assertEqual(summary['total_reserved'], 15)  # 10 + 5
        self.assertEqual(summary['available_quantity'], 135)  # 150 - 15
        
        # Check details data
        self.assertEqual(len(report['details']), 2)
    
    def test_generate_inventory_report_valuation(self):
        """Test generating inventory valuation report."""
        # Generate valuation report
        report = InventoryService.generate_inventory_report(report_type='valuation')
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('details', report)
        
        # Check summary data
        summary = report['summary']
        # Expected total value: (100 * 50.00) + (50 * 75.00) = 5000 + 3750 = 8750
        self.assertEqual(summary['total_value'], Decimal('8750.00'))
        
        # Check warehouse values
        warehouse_values = {w['warehouse__name']: w['total_value'] for w in summary['warehouse_values']}
        self.assertEqual(warehouse_values['Main Warehouse'], Decimal('8750.00'))
        
        # Check details data
        self.assertEqual(len(report['details']), 2)
    
    def test_generate_inventory_report_with_filters(self):
        """Test generating inventory report with filters."""
        # Generate report filtered by warehouse
        report = InventoryService.generate_inventory_report(
            report_type='stock_levels',
            warehouse_id=self.warehouse.id
        )
        
        # Check filtered data
        self.assertEqual(report['summary']['total_items'], 2)
        
        # Generate report filtered by product
        report = InventoryService.generate_inventory_report(
            report_type='stock_levels',
            product_id=self.product.id
        )
        
        # Check filtered data
        self.assertEqual(report['summary']['total_items'], 1)
        self.assertEqual(report['summary']['total_quantity'], 100)
    
    def test_generate_inventory_report_invalid_type(self):
        """Test generating report with invalid type raises error."""
        with self.assertRaises(ValidationError):
            InventoryService.generate_inventory_report(report_type='invalid_type')


class PurchaseOrderServiceTest(TestCase):
    """Test cases for the PurchaseOrderService."""
    
    def setUp(self):
        # Create required related objects
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="SUP001"
        )
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="WH001",
            location="New York"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Create products
        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(
            name="Product 1",
            description="Description 1",
            price=Decimal('100.00'),
            category=self.category
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            description="Description 2",
            price=Decimal('200.00'),
            category=self.category
        )
    
    def test_create_purchase_order(self):
        """Test creating a purchase order."""
        # Create purchase order items
        items = [
            {
                'product_id': self.product1.id,
                'quantity': 5,
                'unit_price': Decimal('80.00')
            },
            {
                'product_id': self.product2.id,
                'quantity': 3,
                'unit_price': Decimal('150.00')
            }
        ]
        
        # Create purchase order
        purchase_order = PurchaseOrderService.create_purchase_order(
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            items=items,
            user=self.user,
            notes="Test purchase order",
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=7)
        )
        
        # Check purchase order was created correctly
        self.assertEqual(purchase_order.supplier, self.supplier)
        self.assertEqual(purchase_order.warehouse, self.warehouse)
        self.assertEqual(purchase_order.status, "DRAFT")
        self.assertEqual(purchase_order.notes, "Test purchase order")
        self.assertEqual(purchase_order.created_by, self.user)
        
        # Check PO number was generated
        self.assertTrue(purchase_order.po_number.startswith("PO-"))
        
        # Check total amount was calculated correctly
        # Expected: (5 * 80.00) + (3 * 150.00) = 400.00 + 450.00 = 850.00
        self.assertEqual(purchase_order.total_amount, Decimal('850.00'))
        
        # Check purchase order items were created
        self.assertEqual(purchase_order.items.count(), 2)
        
        # Check first item
        po_item1 = purchase_order.items.get(product=self.product1)
        self.assertEqual(po_item1.quantity_ordered, 5)
        self.assertEqual(po_item1.unit_price, Decimal('80.00'))
        self.assertEqual(po_item1.quantity_received, 0)
        self.assertFalse(po_item1.is_completed)
        
        # Check second item
        po_item2 = purchase_order.items.get(product=self.product2)
        self.assertEqual(po_item2.quantity_ordered, 3)
        self.assertEqual(po_item2.unit_price, Decimal('150.00'))
        self.assertEqual(po_item2.quantity_received, 0)
        self.assertFalse(po_item2.is_completed)
    
    def test_receive_purchase_order(self):
        """Test receiving items for a purchase order."""
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="SUBMITTED",
            created_by=self.user
        )
        
        # Create purchase order items
        po_item1 = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=self.product1,
            quantity_ordered=5,
            quantity_received=0,
            unit_price=Decimal('80.00')
        )
        
        po_item2 = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=self.product2,
            quantity_ordered=3,
            quantity_received=0,
            unit_price=Decimal('150.00')
        )
        
        # Receive partial items
        received_items = {
            str(po_item1.id): 3,  # Receive 3 of 5
            str(po_item2.id): 0   # Receive none
        }
        
        updated_po = PurchaseOrderService.receive_purchase_order(
            purchase_order_id=purchase_order.id,
            received_items=received_items,
            user=self.user,
            notes="Partial receipt"
        )
        
        # Check purchase order status was updated
        self.assertEqual(updated_po.status, "PARTIAL")
        
        # Check purchase order items were updated
        po_item1.refresh_from_db()
        po_item2.refresh_from_db()
        
        self.assertEqual(po_item1.quantity_received, 3)
        self.assertFalse(po_item1.is_completed)
        
        self.assertEqual(po_item2.quantity_received, 0)
        self.assertFalse(po_item2.is_completed)
        
        # Check inventory was created and updated
        inventory = Inventory.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(inventory.quantity, 3)
        self.assertEqual(inventory.supplier, self.supplier)
        
        # Check inventory transaction was created
        transaction = InventoryTransaction.objects.get(
            inventory=inventory,
            transaction_type="PURCHASE"
        )
        self.assertEqual(transaction.quantity, 3)
        self.assertEqual(transaction.reference_number, "PO-TEST-001")
        
        # Receive remaining items
        received_items = {
            str(po_item1.id): 2,  # Receive remaining 2
            str(po_item2.id): 3   # Receive all 3
        }
        
        updated_po = PurchaseOrderService.receive_purchase_order(
            purchase_order_id=purchase_order.id,
            received_items=received_items,
            user=self.user,
            notes="Complete receipt"
        )
        
        # Check purchase order status was updated
        self.assertEqual(updated_po.status, "RECEIVED")
        self.assertIsNotNone(updated_po.actual_delivery_date)
        
        # Check purchase order items were updated
        po_item1.refresh_from_db()
        po_item2.refresh_from_db()
        
        self.assertEqual(po_item1.quantity_received, 5)
        self.assertTrue(po_item1.is_completed)
        
        self.assertEqual(po_item2.quantity_received, 3)
        self.assertTrue(po_item2.is_completed)
        
        # Check inventories were updated
        inventory1 = Inventory.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(inventory1.quantity, 5)  # 3 + 2
        
        inventory2 = Inventory.objects.get(product=self.product2, warehouse=self.warehouse)
        self.assertEqual(inventory2.quantity, 3)
    
    def test_receive_more_than_ordered(self):
        """Test receiving more items than ordered raises error."""
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-002",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="SUBMITTED",
            created_by=self.user
        )
        
        # Create purchase order item
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=self.product1,
            quantity_ordered=5,
            quantity_received=0,
            unit_price=Decimal('80.00')
        )
        
        # Try to receive more than ordered
        received_items = {
            str(po_item.id): 6  # Ordered 5
        }
        
        with self.assertRaises(ValidationError):
            PurchaseOrderService.receive_purchase_order(
                purchase_order_id=purchase_order.id,
                received_items=received_items,
                user=self.user
            )
    
    def test_receive_cancelled_purchase_order(self):
        """Test receiving items for a cancelled purchase order raises error."""
        # Create cancelled purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-003",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="CANCELLED",
            created_by=self.user
        )
        
        # Create purchase order item
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=self.product1,
            quantity_ordered=5,
            quantity_received=0,
            unit_price=Decimal('80.00')
        )
        
        # Try to receive items
        received_items = {
            str(po_item.id): 3
        }
        
        with self.assertRaises(ValidationError):
            PurchaseOrderService.receive_purchase_order(
                purchase_order_id=purchase_order.id,
                received_items=received_items,
                user=self.user
            )
    
    def test_cancel_purchase_order(self):
        """Test cancelling a purchase order."""
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-004",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="SUBMITTED",
            created_by=self.user
        )
        
        # Cancel purchase order
        cancelled_po = PurchaseOrderService.cancel_purchase_order(
            purchase_order_id=purchase_order.id,
            user=self.user,
            reason="Items no longer needed"
        )
        
        # Check purchase order status was updated
        self.assertEqual(cancelled_po.status, "CANCELLED")
        
        # Check cancellation notes were added
        self.assertIn("Items no longer needed", cancelled_po.notes)
    
    def test_cancel_received_purchase_order(self):
        """Test cancelling a received purchase order raises error."""
        # Create received purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-005",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="RECEIVED",
            created_by=self.user
        )
        
        # Try to cancel purchase order
        with self.assertRaises(ValidationError):
            PurchaseOrderService.cancel_purchase_order(
                purchase_order_id=purchase_order.id,
                user=self.user,
                reason="Trying to cancel received order"
            )