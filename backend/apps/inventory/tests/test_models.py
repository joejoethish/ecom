from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from apps.inventory.models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)
from apps.products.models import Product, Category

User = get_user_model()


class SupplierModelTest(TestCase):
    """Test cases for the Supplier model."""
    
    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="SUP001",
            contact_person="John Doe",
            email="john@supplier.com",
            phone="1234567890",
            lead_time_days=5,
            reliability_rating=4.5
        )
    
    def test_supplier_creation(self):
        """Test that a supplier can be created with all fields."""
        self.assertEqual(self.supplier.name, "Test Supplier")
        self.assertEqual(self.supplier.code, "SUP001")
        self.assertEqual(self.supplier.contact_person, "John Doe")
        self.assertEqual(self.supplier.email, "john@supplier.com")
        self.assertEqual(self.supplier.phone, "1234567890")
        self.assertEqual(self.supplier.lead_time_days, 5)
        self.assertEqual(self.supplier.reliability_rating, Decimal('4.5'))
        self.assertTrue(self.supplier.is_active)
    
    def test_supplier_str_representation(self):
        """Test the string representation of a supplier."""
        self.assertEqual(str(self.supplier), "Test Supplier")


class WarehouseModelTest(TestCase):
    """Test cases for the Warehouse model."""
    
    def setUp(self):
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="WH001",
            location="New York",
            address="123 Storage St, NY",
            capacity=10000
        )
    
    def test_warehouse_creation(self):
        """Test that a warehouse can be created with all fields."""
        self.assertEqual(self.warehouse.name, "Main Warehouse")
        self.assertEqual(self.warehouse.code, "WH001")
        self.assertEqual(self.warehouse.location, "New York")
        self.assertEqual(self.warehouse.address, "123 Storage St, NY")
        self.assertEqual(self.warehouse.capacity, 10000)
        self.assertTrue(self.warehouse.is_active)
    
    def test_warehouse_str_representation(self):
        """Test the string representation of a warehouse."""
        self.assertEqual(str(self.warehouse), "Main Warehouse")


class InventoryModelTest(TestCase):
    """Test cases for the Inventory model."""
    
    def setUp(self):
        # Create required related objects
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            category=self.category
        )
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="WH001",
            location="New York"
        )
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            code="SUP001"
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
    
    def test_inventory_creation(self):
        """Test that inventory can be created with all fields."""
        self.assertEqual(self.inventory.product, self.product)
        self.assertEqual(self.inventory.warehouse, self.warehouse)
        self.assertEqual(self.inventory.quantity, 100)
        self.assertEqual(self.inventory.reserved_quantity, 10)
        self.assertEqual(self.inventory.minimum_stock_level, 20)
        self.assertEqual(self.inventory.maximum_stock_level, 200)
        self.assertEqual(self.inventory.reorder_point, 50)
        self.assertEqual(self.inventory.cost_price, Decimal('50.00'))
        self.assertEqual(self.inventory.supplier, self.supplier)
    
    def test_available_quantity_property(self):
        """Test the available_quantity property."""
        self.assertEqual(self.inventory.available_quantity, 90)  # 100 - 10
        
        # Test with reserved quantity greater than quantity
        self.inventory.reserved_quantity = 150
        self.assertEqual(self.inventory.available_quantity, 0)
    
    def test_needs_reordering_property(self):
        """Test the needs_reordering property."""
        self.assertFalse(self.inventory.needs_reordering)  # 100 > 50
        
        self.inventory.quantity = 40
        self.assertTrue(self.inventory.needs_reordering)  # 40 < 50
    
    def test_stock_status_property(self):
        """Test the stock_status property."""
        self.assertEqual(self.inventory.stock_status, "IN_STOCK")  # 100 is between reorder and max
        
        self.inventory.quantity = 0
        self.assertEqual(self.inventory.stock_status, "OUT_OF_STOCK")
        
        self.inventory.quantity = 30
        self.assertEqual(self.inventory.stock_status, "LOW_STOCK")  # 30 < 50 (reorder point)
        
        self.inventory.quantity = 250
        self.assertEqual(self.inventory.stock_status, "OVERSTOCK")  # 250 > 200 (max)
    
    def test_inventory_str_representation(self):
        """Test the string representation of inventory."""
        expected = f"Test Product - Main Warehouse (100)"
        self.assertEqual(str(self.inventory), expected)


class InventoryTransactionModelTest(TestCase):
    """Test cases for the InventoryTransaction model."""
    
    def setUp(self):
        # Create required related objects
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            category=self.category
        )
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="WH001",
            location="New York"
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=100,
            cost_price=Decimal('50.00')
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Create transaction
        self.transaction = InventoryTransaction.objects.create(
            inventory=self.inventory,
            transaction_type="PURCHASE",
            quantity=50,
            reference_number="REF001",
            batch_number="BATCH001",
            unit_cost=Decimal('48.00'),
            notes="Initial stock purchase",
            created_by=self.user
        )
    
    def test_transaction_creation(self):
        """Test that a transaction can be created with all fields."""
        self.assertEqual(self.transaction.inventory, self.inventory)
        self.assertEqual(self.transaction.transaction_type, "PURCHASE")
        self.assertEqual(self.transaction.quantity, 50)
        self.assertEqual(self.transaction.reference_number, "REF001")
        self.assertEqual(self.transaction.batch_number, "BATCH001")
        self.assertEqual(self.transaction.unit_cost, Decimal('48.00'))
        self.assertEqual(self.transaction.total_cost, Decimal('2400.00'))  # 50 * 48.00
        self.assertEqual(self.transaction.notes, "Initial stock purchase")
        self.assertEqual(self.transaction.created_by, self.user)
    
    def test_transaction_str_representation(self):
        """Test the string representation of a transaction."""
        expected = "Purchase - Test Product (50)"
        self.assertEqual(str(self.transaction), expected)
    
    def test_total_cost_calculation(self):
        """Test that total_cost is calculated correctly on save."""
        # Create a new transaction with different values
        transaction = InventoryTransaction.objects.create(
            inventory=self.inventory,
            transaction_type="ADJUSTMENT",
            quantity=-10,  # Negative quantity
            unit_cost=Decimal('52.00'),
            created_by=self.user
        )
        
        # Total cost should be absolute value of quantity * unit_cost
        self.assertEqual(transaction.total_cost, Decimal('520.00'))  # |-10| * 52.00


class PurchaseOrderModelTest(TestCase):
    """Test cases for the PurchaseOrder model."""
    
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
        
        # Create purchase order
        self.purchase_order = PurchaseOrder.objects.create(
            po_number="PO-20250101-1",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="DRAFT",
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=7),
            total_amount=Decimal('1000.00'),
            tax_amount=Decimal('100.00'),
            shipping_cost=Decimal('50.00'),
            notes="Test purchase order",
            created_by=self.user
        )
        
        # Create category and products for order items
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
        
        # Create purchase order items
        self.po_item1 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product1,
            quantity_ordered=5,
            quantity_received=0,
            unit_price=Decimal('80.00')
        )
        self.po_item2 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product2,
            quantity_ordered=3,
            quantity_received=0,
            unit_price=Decimal('150.00')
        )
    
    def test_purchase_order_creation(self):
        """Test that a purchase order can be created with all fields."""
        self.assertEqual(self.purchase_order.po_number, "PO-20250101-1")
        self.assertEqual(self.purchase_order.supplier, self.supplier)
        self.assertEqual(self.purchase_order.warehouse, self.warehouse)
        self.assertEqual(self.purchase_order.status, "DRAFT")
        self.assertEqual(self.purchase_order.total_amount, Decimal('1000.00'))
        self.assertEqual(self.purchase_order.tax_amount, Decimal('100.00'))
        self.assertEqual(self.purchase_order.shipping_cost, Decimal('50.00'))
        self.assertEqual(self.purchase_order.notes, "Test purchase order")
        self.assertEqual(self.purchase_order.created_by, self.user)
    
    def test_purchase_order_str_representation(self):
        """Test the string representation of a purchase order."""
        expected = f"PO-PO-20250101-1 - Test Supplier"
        self.assertEqual(str(self.purchase_order), expected)


class PurchaseOrderItemModelTest(TestCase):
    """Test cases for the PurchaseOrderItem model."""
    
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
        self.purchase_order = PurchaseOrder.objects.create(
            po_number="PO-20250101-1",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="DRAFT"
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create purchase order item
        self.po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity_ordered=10,
            quantity_received=5,
            unit_price=Decimal('80.00')
        )
    
    def test_purchase_order_item_creation(self):
        """Test that a purchase order item can be created with all fields."""
        self.assertEqual(self.po_item.purchase_order, self.purchase_order)
        self.assertEqual(self.po_item.product, self.product)
        self.assertEqual(self.po_item.quantity_ordered, 10)
        self.assertEqual(self.po_item.quantity_received, 5)
        self.assertEqual(self.po_item.unit_price, Decimal('80.00'))
        self.assertFalse(self.po_item.is_completed)
    
    def test_purchase_order_item_str_representation(self):
        """Test the string representation of a purchase order item."""
        expected = "Test Product - 10 units"
        self.assertEqual(str(self.po_item), expected)
    
    def test_total_price_property(self):
        """Test the total_price property."""
        self.assertEqual(self.po_item.total_price, Decimal('800.00'))  # 10 * 80.00
    
    def test_remaining_quantity_property(self):
        """Test the remaining_quantity property."""
        self.assertEqual(self.po_item.remaining_quantity, 5)  # 10 - 5
        
        # Test with received quantity greater than ordered
        self.po_item.quantity_received = 15
        self.assertEqual(self.po_item.remaining_quantity, 0)