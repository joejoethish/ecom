from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json

from apps.inventory.models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)
from apps.products.models import Product, Category

User = get_user_model()


class InventoryAPITest(TestCase):
    """Test cases for the Inventory API endpoints."""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass123"
        )
        
        # Set up API client
        self.client = APIClient()
        
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
    
    def test_inventory_list_requires_authentication(self):
        """Test that inventory list endpoint requires authentication."""
        url = reverse('inventory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_list_requires_admin_permission(self):
        """Test that inventory list endpoint requires admin permission."""
        url = reverse('inventory-list')
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_inventory_list_admin_access(self):
        """Test that admin can access inventory list."""
        url = reverse('inventory-list')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_inventory_detail(self):
        """Test retrieving inventory detail."""
        url = reverse('inventory-detail', args=[self.inventory.id])
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product'], self.product.id)
        self.assertEqual(response.data['warehouse'], self.warehouse.id)
        self.assertEqual(response.data['quantity'], 100)
        self.assertEqual(response.data['available_quantity'], 90)
    
    def test_inventory_create(self):
        """Test creating inventory."""
        url = reverse('inventory-list')
        self.client.force_authenticate(user=self.admin_user)
        
        # Create another product
        product2 = Product.objects.create(
            name="Another Product",
            description="Another Description",
            price=Decimal('149.99'),
            category=self.category
        )
        
        data = {
            'product': product2.id,
            'warehouse': self.warehouse.id,
            'quantity': 50,
            'minimum_stock_level': 10,
            'maximum_stock_level': 100,
            'reorder_point': 20,
            'cost_price': '60.00',
            'supplier': self.supplier.id
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check inventory was created
        inventory = Inventory.objects.get(product=product2)
        self.assertEqual(inventory.quantity, 50)
        self.assertEqual(inventory.cost_price, Decimal('60.00'))
    
    def test_inventory_update(self):
        """Test updating inventory."""
        url = reverse('inventory-detail', args=[self.inventory.id])
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'product': self.product.id,
            'warehouse': self.warehouse.id,
            'quantity': 120,
            'minimum_stock_level': 30,
            'cost_price': '55.00'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventory was updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 120)
        self.assertEqual(self.inventory.minimum_stock_level, 30)
        self.assertEqual(self.inventory.cost_price, Decimal('55.00'))
    
    def test_inventory_delete(self):
        """Test deleting inventory."""
        url = reverse('inventory-detail', args=[self.inventory.id])
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check inventory was deleted
        with self.assertRaises(Inventory.DoesNotExist):
            Inventory.objects.get(id=self.inventory.id)
    
    def test_inventory_stock_summary(self):
        """Test inventory stock summary endpoint."""
        url = reverse('inventory-stock-summary')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check summary data
        self.assertEqual(response.data['total_products'], 1)
        self.assertEqual(response.data['total_quantity'], 100)
        self.assertEqual(response.data['total_stock_value'], '5000.00')
        
        # Check warehouse summary
        warehouse_summary = response.data['warehouse_summary'][0]
        self.assertEqual(warehouse_summary['name'], 'Main Warehouse')
        self.assertEqual(warehouse_summary['product_count'], 1)
        self.assertEqual(warehouse_summary['total_quantity'], 100)
    
    def test_inventory_low_stock(self):
        """Test inventory low stock endpoint."""
        # Create low stock inventory
        product2 = Product.objects.create(
            name="Low Stock Product",
            description="Description",
            price=Decimal('79.99'),
            category=self.category
        )
        
        Inventory.objects.create(
            product=product2,
            warehouse=self.warehouse,
            quantity=10,  # Below reorder point
            reorder_point=20,
            cost_price=Decimal('40.00')
        )
        
        url = reverse('inventory-low-stock')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check only low stock item is returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Low Stock Product')
    
    def test_inventory_adjust(self):
        """Test inventory adjust endpoint."""
        url = reverse('inventory-adjust', args=[self.inventory.id])
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'inventory_id': self.inventory.id,
            'adjustment_quantity': 20,
            'reason': 'Found additional stock',
            'reference_number': 'ADJ001',
            'notes': 'Test adjustment'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventory was updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 120)  # 100 + 20
        
        # Check transaction was created
        transaction = InventoryTransaction.objects.latest('created_at')
        self.assertEqual(transaction.transaction_type, 'ADJUSTMENT')
        self.assertEqual(transaction.quantity, 20)
        self.assertEqual(transaction.reference_number, 'ADJ001')
        self.assertIn('Found additional stock', transaction.notes)
    
    def test_inventory_transfer(self):
        """Test inventory transfer endpoint."""
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
        
        url = reverse('inventory-transfer')
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'source_inventory_id': self.inventory.id,
            'destination_inventory_id': inventory2.id,
            'quantity': 30,
            'reference_number': 'TRANSFER001',
            'notes': 'Test transfer'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventories were updated
        self.inventory.refresh_from_db()
        inventory2.refresh_from_db()
        
        self.assertEqual(self.inventory.quantity, 70)  # 100 - 30
        self.assertEqual(inventory2.quantity, 80)  # 50 + 30
        
        # Check transactions were created
        source_transaction = response.data['source_transaction']
        dest_transaction = response.data['destination_transaction']
        
        self.assertEqual(source_transaction['quantity'], -30)
        self.assertEqual(dest_transaction['quantity'], 30)
        self.assertEqual(source_transaction['reference_number'], 'TRANSFER001')
        self.assertEqual(dest_transaction['reference_number'], 'TRANSFER001')
    
    def test_inventory_bulk_update(self):
        """Test bulk inventory update endpoint."""
        url = reverse('inventory-bulk-update')
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'inventory_updates': [
                {
                    'inventory_id': self.inventory.id,
                    'quantity': 20  # Add 20 units
                },
                {
                    'inventory_id': self.inventory2.id,
                    'quantity': -10  # Remove 10 units
                }
            ],
            'reference_number': 'BULK001',
            'notes': 'Test bulk update'
        }
        
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventories were updated
        self.inventory.refresh_from_db()
        self.inventory2.refresh_from_db()
        
        self.assertEqual(self.inventory.quantity, 120)  # 100 + 20
        self.assertEqual(self.inventory2.quantity, 40)  # 50 - 10
        
        # Check transactions were created
        transactions = response.data
        self.assertEqual(len(transactions), 2)
        
        # First transaction (addition)
        self.assertEqual(transactions[0]['quantity'], 20)
        self.assertEqual(transactions[0]['reference_number'], 'BULK001')
        self.assertIn('Test bulk update', transactions[0]['notes'])
        
        # Second transaction (removal)
        self.assertEqual(transactions[1]['quantity'], -10)
        self.assertEqual(transactions[1]['reference_number'], 'BULK001')
        self.assertIn('Test bulk update', transactions[1]['notes'])
    
    def test_inventory_update_alert_settings(self):
        """Test updating inventory alert settings."""
        url = reverse('inventory-update-alert-settings')
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'inventory_id': self.inventory.id,
            'minimum_stock_level': 30,
            'maximum_stock_level': 250,
            'reorder_point': 60
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check inventory settings were updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.minimum_stock_level, 30)
        self.assertEqual(self.inventory.maximum_stock_level, 250)
        self.assertEqual(self.inventory.reorder_point, 60)
    
    def test_inventory_update_alert_settings_validation(self):
        """Test validation for updating inventory alert settings."""
        url = reverse('inventory-update-alert-settings')
        self.client.force_authenticate(user=self.admin_user)
        
        # Test invalid settings (minimum > reorder)
        data = {
            'inventory_id': self.inventory.id,
            'minimum_stock_level': 70,
            'reorder_point': 60
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid settings (reorder > maximum)
        data = {
            'inventory_id': self.inventory.id,
            'reorder_point': 250,
            'maximum_stock_level': 200
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_inventory_overstock(self):
        """Test inventory overstock endpoint."""
        # Create overstock inventory
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
        
        url = reverse('inventory-overstock')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check only overstock item is returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Overstock Product')
    
    def test_inventory_generate_report(self):
        """Test generating inventory reports."""
        url = reverse('inventory-generate-report')
        self.client.force_authenticate(user=self.admin_user)
        
        # Test stock levels report
        data = {
            'report_type': 'stock_levels'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('details', response.data)
        self.assertEqual(response.data['summary']['total_items'], 2)
        
        # Test valuation report
        data = {
            'report_type': 'valuation'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('details', response.data)
        
        # Expected total value: (100 * 50.00) + (50 * 75.00) = 5000 + 3750 = 8750
        self.assertEqual(response.data['summary']['total_value'], 8750)
    
    def test_inventory_export_csv(self):
        """Test exporting inventory to CSV."""
        url = reverse('inventory-export-csv')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="inventory_export.csv"', response['Content-Disposition'])


class PurchaseOrderAPITest(TestCase):
    """Test cases for the Purchase Order API endpoints."""
    
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
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
        
        # Create purchase order
        self.purchase_order = PurchaseOrder.objects.create(
            po_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="DRAFT",
            total_amount=Decimal('850.00'),
            created_by=self.admin_user
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
    
    def test_purchase_order_list(self):
        """Test retrieving purchase order list."""
        url = reverse('purchase-order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_purchase_order_detail(self):
        """Test retrieving purchase order detail."""
        url = reverse('purchase-order-detail', args=[self.purchase_order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['po_number'], 'PO-TEST-001')
        self.assertEqual(response.data['status'], 'DRAFT')
        self.assertEqual(len(response.data['items']), 2)
    
    def test_create_purchase_order(self):
        """Test creating a purchase order."""
        url = reverse('purchase-order-list')
        
        data = {
            'supplier_id': self.supplier.id,
            'warehouse_id': self.warehouse.id,
            'notes': 'New purchase order',
            'items': [
                {
                    'product_id': self.product1.id,
                    'quantity': 10,
                    'unit_price': '75.00'
                },
                {
                    'product_id': self.product2.id,
                    'quantity': 5,
                    'unit_price': '140.00'
                }
            ]
        }
        
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check purchase order was created
        po_id = response.data['id']
        purchase_order = PurchaseOrder.objects.get(id=po_id)
        
        self.assertEqual(purchase_order.supplier, self.supplier)
        self.assertEqual(purchase_order.warehouse, self.warehouse)
        self.assertEqual(purchase_order.status, 'DRAFT')
        self.assertEqual(purchase_order.notes, 'New purchase order')
        
        # Check purchase order items were created
        self.assertEqual(purchase_order.items.count(), 2)
        
        # Check total amount was calculated correctly
        # Expected: (10 * 75.00) + (5 * 140.00) = 750.00 + 700.00 = 1450.00
        self.assertEqual(purchase_order.total_amount, Decimal('1450.00'))
    
    def test_receive_purchase_order(self):
        """Test receiving items for a purchase order."""
        # Update purchase order status to SUBMITTED
        self.purchase_order.status = 'SUBMITTED'
        self.purchase_order.save()
        
        url = reverse('purchase-order-receive', args=[self.purchase_order.id])
        
        data = {
            'received_items': {
                str(self.po_item1.id): 3,  # Receive 3 of 5
                str(self.po_item2.id): 2   # Receive 2 of 3
            },
            'notes': 'Partial receipt'
        }
        
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check purchase order status was updated
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, 'PARTIAL')
        
        # Check purchase order items were updated
        self.po_item1.refresh_from_db()
        self.po_item2.refresh_from_db()
        
        self.assertEqual(self.po_item1.quantity_received, 3)
        self.assertFalse(self.po_item1.is_completed)
        
        self.assertEqual(self.po_item2.quantity_received, 2)
        self.assertFalse(self.po_item2.is_completed)
        
        # Check inventory was created
        inventory1 = Inventory.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(inventory1.quantity, 3)
        
        inventory2 = Inventory.objects.get(product=self.product2, warehouse=self.warehouse)
        self.assertEqual(inventory2.quantity, 2)
        
        # Receive remaining items
        data = {
            'received_items': {
                str(self.po_item1.id): 2,  # Receive remaining 2
                str(self.po_item2.id): 1   # Receive remaining 1
            },
            'notes': 'Complete receipt'
        }
        
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check purchase order status was updated
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, 'RECEIVED')
        
        # Check purchase order items were updated
        self.po_item1.refresh_from_db()
        self.po_item2.refresh_from_db()
        
        self.assertEqual(self.po_item1.quantity_received, 5)
        self.assertTrue(self.po_item1.is_completed)
        
        self.assertEqual(self.po_item2.quantity_received, 3)
        self.assertTrue(self.po_item2.is_completed)
        
        # Check inventory was updated
        inventory1.refresh_from_db()
        self.assertEqual(inventory1.quantity, 5)
        
        inventory2.refresh_from_db()
        self.assertEqual(inventory2.quantity, 3)
    
    def test_cancel_purchase_order(self):
        """Test cancelling a purchase order."""
        url = reverse('purchase-order-cancel', args=[self.purchase_order.id])
        
        data = {
            'reason': 'Items no longer needed'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check purchase order status was updated
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, 'CANCELLED')
        
        # Check cancellation notes were added
        self.assertIn('Items no longer needed', self.purchase_order.notes)
    
    def test_cancel_received_purchase_order_fails(self):
        """Test cancelling a received purchase order fails."""
        # Update purchase order status to RECEIVED
        self.purchase_order.status = 'RECEIVED'
        self.purchase_order.save()
        
        url = reverse('purchase-order-cancel', args=[self.purchase_order.id])
        
        data = {
            'reason': 'Trying to cancel received order'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check purchase order status was not updated
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, 'RECEIVED')