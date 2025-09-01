#!/usr/bin/env python3
"""
Comprehensive Automated Testing for Inventory Flow
Tests the complete inventory management system end-to-end
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.inventory.models import Inventory, InventoryTransaction, Warehouse, Supplier, PurchaseOrder, PurchaseOrderItem
from apps.inventory.services import InventoryService, PurchaseOrderService
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem

User = get_user_model()

class InventoryFlowAutomationTest:
    """Automated testing class for inventory flow"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_results = []
        self.setup_test_data()
    
    def log_test(self, test_name, status, message="", details=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def setup_test_data(self):
        """Setup test data for inventory testing"""
        try:
            # Create test user
            self.test_user, created = User.objects.get_or_create(
                username='inventory_test_user',
                defaults={
                    'email': 'test@inventory.com',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            # Create test category
            self.test_category, created = Category.objects.get_or_create(
                name='Test Electronics',
                defaults={'slug': 'test-electronics'}
            )
            
            # Create test products with unique SKUs
            self.test_products = []
            for i in range(3):
                product, created = Product.objects.get_or_create(
                    name=f'Test Product {i+1}',
                    defaults={
                        'slug': f'test-product-{i+1}',
                        'sku': f'TEST-SKU-{i+1:03d}',  # Add unique SKU
                        'description': f'Test product {i+1} description',
                        'price': Decimal('100.00') + (i * 50),
                        'category': self.test_category,
                        'is_active': True
                    }
                )
                self.test_products.append(product)
            
            # Create test warehouse
            self.test_warehouse, created = Warehouse.objects.get_or_create(
                name='Test Warehouse',
                defaults={
                    'code': 'TW001',
                    'location': 'Test City',
                    'address': '123 Test Street',
                    'capacity': 10000
                }
            )
            
            # Create test supplier
            self.test_supplier, created = Supplier.objects.get_or_create(
                name='Test Supplier',
                defaults={
                    'code': 'TS001',
                    'email': 'supplier@test.com',
                    'phone': '+1234567890'
                }
            )
            
            self.log_test("Setup Test Data", "PASS", f"Test data created successfully - {len(self.test_products)} products")
            
        except Exception as e:
            self.log_test("Setup Test Data", "FAIL", f"Failed to setup test data: {str(e)}")
            # Initialize empty lists to prevent attribute errors
            self.test_products = []
            self.test_warehouse = None
            self.test_supplier = None
    
    def test_inventory_creation(self):
        """Test inventory creation for products"""
        try:
            for product in self.test_products:
                inventory, created = Inventory.objects.get_or_create(
                    product=product,
                    warehouse=self.test_warehouse,
                    defaults={
                        'quantity': 0,
                        'cost_price': product.price * Decimal('0.7'),  # 70% of selling price
                        'minimum_stock_level': 10,
                        'maximum_stock_level': 1000,
                        'reorder_point': 20,
                        'supplier': self.test_supplier
                    }
                )
                
                assert inventory is not None
                assert inventory.product == product
                assert inventory.warehouse == self.test_warehouse
                
            self.log_test("Inventory Creation", "PASS", f"Created inventory for {len(self.test_products)} products")
            
        except Exception as e:
            self.log_test("Inventory Creation", "FAIL", f"Failed to create inventory: {str(e)}")
    
    def test_stock_addition(self):
        """Test adding stock to inventory"""
        try:
            for product in self.test_products:
                inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
                initial_quantity = inventory.quantity
                
                # Add stock using service
                transaction = InventoryService.add_stock(
                    inventory=inventory,
                    quantity=100,
                    user=self.test_user,
                    transaction_type="PURCHASE",
                    reference_number="TEST-ADD-001",
                    unit_cost=inventory.cost_price,
                    notes="Test stock addition"
                )
                
                # Refresh inventory
                inventory.refresh_from_db()
                
                assert inventory.quantity == initial_quantity + 100
                assert transaction.quantity == 100
                assert transaction.transaction_type == "PURCHASE"
                
            self.log_test("Stock Addition", "PASS", "Successfully added stock to all test products")
            
        except Exception as e:
            self.log_test("Stock Addition", "FAIL", f"Failed to add stock: {str(e)}")
    
    def test_stock_removal(self):
        """Test removing stock from inventory"""
        try:
            for product in self.test_products:
                inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
                initial_quantity = inventory.quantity
                
                # Remove stock using service
                transaction = InventoryService.remove_stock(
                    inventory=inventory,
                    quantity=25,
                    user=self.test_user,
                    transaction_type="SALE",
                    reference_number="TEST-REMOVE-001",
                    notes="Test stock removal"
                )
                
                # Refresh inventory
                inventory.refresh_from_db()
                
                assert inventory.quantity == initial_quantity - 25
                assert transaction.quantity == -25  # Negative for removals
                assert transaction.transaction_type == "SALE"
                
            self.log_test("Stock Removal", "PASS", "Successfully removed stock from all test products")
            
        except Exception as e:
            self.log_test("Stock Removal", "FAIL", f"Failed to remove stock: {str(e)}")
    
    def test_stock_reservation(self):
        """Test stock reservation functionality"""
        try:
            for product in self.test_products:
                inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
                initial_reserved = inventory.reserved_quantity
                
                # Reserve stock
                success = InventoryService.reserve_stock(
                    inventory=inventory,
                    quantity=10,
                    user=self.test_user,
                    reference_number="TEST-RESERVE-001",
                    notes="Test stock reservation"
                )
                
                # Refresh inventory
                inventory.refresh_from_db()
                
                assert success is True
                assert inventory.reserved_quantity == initial_reserved + 10
                assert inventory.available_quantity == inventory.quantity - inventory.reserved_quantity
                
            self.log_test("Stock Reservation", "PASS", "Successfully reserved stock for all test products")
            
        except Exception as e:
            self.log_test("Stock Reservation", "FAIL", f"Failed to reserve stock: {str(e)}")
    
    def test_stock_transfer(self):
        """Test stock transfer between warehouses"""
        try:
            if not self.test_products or not self.test_warehouse or not self.test_supplier:
                self.log_test("Stock Transfer", "SKIP", "Skipping due to setup failure")
                return
                
            # Create second warehouse
            warehouse2, created = Warehouse.objects.get_or_create(
                name='Test Warehouse 2',
                defaults={
                    'code': 'TW002',
                    'location': 'Test City 2',
                    'address': '456 Test Avenue',
                    'capacity': 5000
                }
            )
            
            product = self.test_products[0]
            
            # Create inventory in second warehouse
            inventory2, created = Inventory.objects.get_or_create(
                product=product,
                warehouse=warehouse2,
                defaults={
                    'quantity': 0,
                    'cost_price': product.price * Decimal('0.7'),
                    'minimum_stock_level': 5,
                    'maximum_stock_level': 500,
                    'reorder_point': 10,
                    'supplier': self.test_supplier
                }
            )
            
            # Get source inventory
            inventory1 = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            initial_qty1 = inventory1.quantity
            initial_qty2 = inventory2.quantity
            
            # Transfer stock
            source_tx, dest_tx = InventoryService.transfer_stock(
                source_inventory=inventory1,
                destination_inventory=inventory2,
                quantity=20,
                user=self.test_user,
                reference_number="TEST-TRANSFER-001",
                notes="Test stock transfer"
            )
            
            # Refresh inventories
            inventory1.refresh_from_db()
            inventory2.refresh_from_db()
            
            assert inventory1.quantity == initial_qty1 - 20
            assert inventory2.quantity == initial_qty2 + 20
            assert source_tx.quantity == -20
            assert dest_tx.quantity == 20
            
            self.log_test("Stock Transfer", "PASS", "Successfully transferred stock between warehouses")
            
        except Exception as e:
            self.log_test("Stock Transfer", "FAIL", f"Failed to transfer stock: {str(e)}")
    
    def test_purchase_order_flow(self):
        """Test complete purchase order flow"""
        try:
            if not self.test_products or not self.test_warehouse or not self.test_supplier:
                self.log_test("Purchase Order Flow", "SKIP", "Skipping due to setup failure")
                return
                
            # Create purchase order
            po_items = []
            for product in self.test_products:
                po_items.append({
                    'product_id': product.id,
                    'quantity': 50,
                    'unit_price': product.price * Decimal('0.6')  # 60% of selling price
                })
            
            purchase_order = PurchaseOrderService.create_purchase_order(
                supplier_id=self.test_supplier.id,
                warehouse_id=self.test_warehouse.id,
                items=po_items,
                user=self.test_user,
                notes="Test purchase order",
                expected_delivery_date=datetime.now().date() + timedelta(days=7)
            )
            
            assert purchase_order is not None
            assert purchase_order.status == "DRAFT"
            assert purchase_order.items.count() == len(self.test_products)
            
            # Receive purchase order
            received_items = {}
            for item in purchase_order.items.all():
                received_items[item.id] = item.quantity_ordered
            
            updated_po = PurchaseOrderService.receive_purchase_order(
                purchase_order_id=purchase_order.id,
                received_items=received_items,
                user=self.test_user,
                notes="Test PO receipt"
            )
            
            assert updated_po.status == "RECEIVED"
            
            self.log_test("Purchase Order Flow", "PASS", "Successfully completed purchase order flow")
            
        except Exception as e:
            self.log_test("Purchase Order Flow", "FAIL", f"Failed purchase order flow: {str(e)}")
    
    def test_low_stock_alerts(self):
        """Test low stock alert functionality"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Low Stock Alerts", "SKIP", "Skipping due to setup failure")
                return
                
            # Set one product to low stock
            product = self.test_products[0]
            inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            
            # Adjust to low stock level
            InventoryService.adjust_inventory(
                inventory=inventory,
                adjustment_quantity=-(inventory.quantity - 5),  # Set to 5 units
                user=self.test_user,
                reason="Test low stock scenario",
                reference_number="TEST-LOW-STOCK-001"
            )
            
            # Check low stock items
            low_stock_items = InventoryService.get_low_stock_items()
            
            assert inventory in low_stock_items
            assert inventory.needs_reordering is True
            assert inventory.stock_status in ["LOW_STOCK", "OUT_OF_STOCK"]
            
            self.log_test("Low Stock Alerts", "PASS", "Low stock detection working correctly")
            
        except Exception as e:
            self.log_test("Low Stock Alerts", "FAIL", f"Failed low stock test: {str(e)}")
    
    def test_inventory_reports(self):
        """Test inventory reporting functionality"""
        try:
            if not self.test_warehouse:
                self.log_test("Inventory Reports", "SKIP", "Skipping due to setup failure")
                return
                
            # Generate stock levels report
            stock_report = InventoryService.generate_inventory_report(
                report_type='stock_levels',
                warehouse_id=self.test_warehouse.id
            )
            
            assert 'summary' in stock_report
            assert 'details' in stock_report
            assert stock_report['summary']['total_items'] > 0
            
            # Generate movements report
            movements_report = InventoryService.generate_inventory_report(
                report_type='movements',
                start_date=datetime.now().date() - timedelta(days=1),
                end_date=datetime.now().date()
            )
            
            assert 'summary' in movements_report
            assert 'details' in movements_report
            
            # Generate valuation report
            valuation_report = InventoryService.generate_inventory_report(
                report_type='valuation',
                warehouse_id=self.test_warehouse.id
            )
            
            assert 'summary' in valuation_report
            assert valuation_report['summary']['total_value'] >= 0
            
            self.log_test("Inventory Reports", "PASS", "All inventory reports generated successfully")
            
        except Exception as e:
            self.log_test("Inventory Reports", "FAIL", f"Failed inventory reports: {str(e)}")
    
    def test_api_endpoints(self):
        """Test inventory API endpoints"""
        try:
            # Test inventory list endpoint
            response = requests.get(f"{self.base_url}/inventory/")
            if response.status_code == 200:
                data = response.json()
                assert 'results' in data or isinstance(data, list)
                self.log_test("API - Inventory List", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("API - Inventory List", "FAIL", f"Status: {response.status_code}")
            
            # Test inventory stock summary
            response = requests.get(f"{self.base_url}/inventory/stock-summary/")
            if response.status_code == 200:
                data = response.json()
                assert 'total_products' in data
                self.log_test("API - Stock Summary", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("API - Stock Summary", "FAIL", f"Status: {response.status_code}")
            
            # Test low stock endpoint
            response = requests.get(f"{self.base_url}/inventory/low-stock/")
            if response.status_code == 200:
                self.log_test("API - Low Stock", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("API - Low Stock", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("API Endpoints", "FAIL", f"API test failed: {str(e)}")
    
    def test_data_integrity(self):
        """Test data integrity and constraints"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Data Integrity", "SKIP", "Skipping due to setup failure")
                return
                
            product = self.test_products[0]
            inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            
            # Test negative stock prevention
            try:
                InventoryService.remove_stock(
                    inventory=inventory,
                    quantity=inventory.quantity + 100,  # More than available
                    user=self.test_user,
                    transaction_type="SALE"
                )
                self.log_test("Data Integrity - Negative Stock", "FAIL", "Should have prevented negative stock")
            except Exception:
                self.log_test("Data Integrity - Negative Stock", "PASS", "Correctly prevented negative stock")
            
            # Test over-reservation prevention
            try:
                InventoryService.reserve_stock(
                    inventory=inventory,
                    quantity=inventory.available_quantity + 100,  # More than available
                    user=self.test_user
                )
                self.log_test("Data Integrity - Over Reservation", "FAIL", "Should have prevented over-reservation")
            except Exception:
                self.log_test("Data Integrity - Over Reservation", "PASS", "Correctly prevented over-reservation")
            
            # Test transaction audit trail
            transactions = InventoryTransaction.objects.filter(inventory=inventory)
            assert transactions.count() > 0
            
            # Verify all transactions have required fields
            for tx in transactions:
                assert tx.created_by is not None
                assert tx.created_at is not None
                assert tx.transaction_type in [choice[0] for choice in InventoryTransaction.TRANSACTION_TYPES]
            
            self.log_test("Data Integrity - Audit Trail", "PASS", "Transaction audit trail is complete")
            
        except Exception as e:
            self.log_test("Data Integrity", "FAIL", f"Data integrity test failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all inventory flow tests"""
        print("=" * 60)
        print("INVENTORY FLOW AUTOMATION TESTING")
        print("=" * 60)
        
        test_methods = [
            self.test_inventory_creation,
            self.test_stock_addition,
            self.test_stock_removal,
            self.test_stock_reservation,
            self.test_stock_transfer,
            self.test_purchase_order_flow,
            self.test_low_stock_alerts,
            self.test_inventory_reports,
            self.test_api_endpoints,
            self.test_data_integrity
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, "ERROR", f"Unexpected error: {str(e)}")
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate test summary report"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print("\nFAILED/ERROR TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # Save detailed report
        report_file = f"inventory_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'errors': error_tests,
            'success_rate': (passed_tests/total_tests)*100
        }


if __name__ == "__main__":
    # Run the automated inventory flow tests
    tester = InventoryFlowAutomationTest()
    tester.run_all_tests()