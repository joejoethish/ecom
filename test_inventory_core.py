#!/usr/bin/env python3
"""
Core Inventory Flow Testing - Database Operations Only
Tests the inventory system without API dependencies
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from apps.inventory.models import Inventory, InventoryTransaction, Warehouse, Supplier, PurchaseOrder, PurchaseOrderItem
from apps.inventory.services import InventoryService, PurchaseOrderService
from apps.products.models import Product, Category

User = get_user_model()

class InventoryCoreTest:
    """Core inventory testing without API dependencies"""
    
    def __init__(self):
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
            # Clean up existing test data
            User.objects.filter(username='inventory_test_user').delete()
            Category.objects.filter(name='Test Electronics').delete()
            
            # Create test user
            self.test_user = User.objects.create_user(
                username='inventory_test_user',
                email='test@inventory.com',
                first_name='Test',
                last_name='User'
            )
            
            # Create test category
            self.test_category = Category.objects.create(
                name='Test Electronics',
                slug='test-electronics'
            )
            
            # Create test products with unique SKUs
            self.test_products = []
            for i in range(3):
                product = Product.objects.create(
                    name=f'Test Product {i+1}',
                    slug=f'test-product-{i+1}',
                    sku=f'TEST-SKU-{i+1:03d}-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    description=f'Test product {i+1} description',
                    price=Decimal('100.00') + (i * 50),
                    category=self.test_category,
                    is_active=True
                )
                self.test_products.append(product)
            
            # Create test warehouse
            self.test_warehouse = Warehouse.objects.create(
                name=f'Test Warehouse {datetime.now().strftime("%Y%m%d%H%M%S")}',
                code=f'TW{datetime.now().strftime("%Y%m%d%H%M%S")}',
                location='Test City',
                address='123 Test Street',
                capacity=10000
            )
            
            # Create test supplier
            self.test_supplier = Supplier.objects.create(
                name=f'Test Supplier {datetime.now().strftime("%Y%m%d%H%M%S")}',
                code=f'TS{datetime.now().strftime("%Y%m%d%H%M%S")}',
                email='supplier@test.com',
                phone='+1234567890'
            )
            
            self.log_test("Setup Test Data", "PASS", f"Created {len(self.test_products)} products, 1 warehouse, 1 supplier")
            
        except Exception as e:
            self.log_test("Setup Test Data", "FAIL", f"Failed to setup test data: {str(e)}")
            self.test_products = []
            self.test_warehouse = None
            self.test_supplier = None
    
    def test_inventory_creation(self):
        """Test inventory creation for products"""
        try:
            if not self.test_products or not self.test_warehouse or not self.test_supplier:
                self.log_test("Inventory Creation", "SKIP", "Skipping due to setup failure")
                return
            
            inventories_created = 0
            for product in self.test_products:
                inventory = Inventory.objects.create(
                    product=product,
                    warehouse=self.test_warehouse,
                    quantity=0,
                    cost_price=product.price * Decimal('0.7'),
                    minimum_stock_level=10,
                    maximum_stock_level=1000,
                    reorder_point=20,
                    supplier=self.test_supplier
                )
                
                assert inventory is not None
                assert inventory.product == product
                assert inventory.warehouse == self.test_warehouse
                inventories_created += 1
                
            self.log_test("Inventory Creation", "PASS", f"Created inventory for {inventories_created} products")
            
        except Exception as e:
            self.log_test("Inventory Creation", "FAIL", f"Failed to create inventory: {str(e)}")
    
    def test_stock_operations(self):
        """Test basic stock operations"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Stock Operations", "SKIP", "Skipping due to setup failure")
                return
            
            product = self.test_products[0]
            inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            
            # Test stock addition
            initial_quantity = inventory.quantity
            transaction_add = InventoryService.add_stock(
                inventory=inventory,
                quantity=100,
                user=self.test_user,
                transaction_type="PURCHASE",
                reference_number="TEST-ADD-001",
                unit_cost=inventory.cost_price,
                notes="Test stock addition"
            )
            
            inventory.refresh_from_db()
            assert inventory.quantity == initial_quantity + 100
            assert transaction_add.quantity == 100
            
            # Test stock removal
            current_quantity = inventory.quantity
            transaction_remove = InventoryService.remove_stock(
                inventory=inventory,
                quantity=25,
                user=self.test_user,
                transaction_type="SALE",
                reference_number="TEST-REMOVE-001",
                notes="Test stock removal"
            )
            
            inventory.refresh_from_db()
            assert inventory.quantity == current_quantity - 25
            assert transaction_remove.quantity == -25
            
            # Test stock reservation
            current_reserved = inventory.reserved_quantity
            success = InventoryService.reserve_stock(
                inventory=inventory,
                quantity=10,
                user=self.test_user,
                reference_number="TEST-RESERVE-001",
                notes="Test stock reservation"
            )
            
            inventory.refresh_from_db()
            assert success is True
            assert inventory.reserved_quantity == current_reserved + 10
            
            self.log_test("Stock Operations", "PASS", "All basic stock operations completed successfully")
            
        except Exception as e:
            self.log_test("Stock Operations", "FAIL", f"Failed stock operations: {str(e)}")
    
    def test_inventory_constraints(self):
        """Test inventory business constraints"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Inventory Constraints", "SKIP", "Skipping due to setup failure")
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
                self.log_test("Inventory Constraints", "FAIL", "Should have prevented negative stock")
                return
            except Exception:
                pass  # Expected to fail
            
            # Test over-reservation prevention
            try:
                InventoryService.reserve_stock(
                    inventory=inventory,
                    quantity=inventory.available_quantity + 100,  # More than available
                    user=self.test_user
                )
                self.log_test("Inventory Constraints", "FAIL", "Should have prevented over-reservation")
                return
            except Exception:
                pass  # Expected to fail
            
            self.log_test("Inventory Constraints", "PASS", "All business constraints working correctly")
            
        except Exception as e:
            self.log_test("Inventory Constraints", "FAIL", f"Failed constraint test: {str(e)}")
    
    def test_stock_levels_and_alerts(self):
        """Test stock level monitoring and alerts"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Stock Levels and Alerts", "SKIP", "Skipping due to setup failure")
                return
            
            product = self.test_products[0]
            inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            
            # Set inventory to low stock level
            target_quantity = 5  # Below reorder point of 20
            adjustment_needed = target_quantity - inventory.quantity
            
            if adjustment_needed != 0:
                InventoryService.adjust_inventory(
                    inventory=inventory,
                    adjustment_quantity=adjustment_needed,
                    user=self.test_user,
                    reason="Test low stock scenario",
                    reference_number="TEST-LOW-STOCK-001"
                )
            
            inventory.refresh_from_db()
            
            # Test stock status
            assert inventory.needs_reordering is True
            assert inventory.stock_status in ["LOW_STOCK", "OUT_OF_STOCK"]
            
            # Test low stock detection
            low_stock_items = InventoryService.get_low_stock_items()
            assert inventory in low_stock_items
            
            self.log_test("Stock Levels and Alerts", "PASS", f"Stock level monitoring working - Status: {inventory.stock_status}")
            
        except Exception as e:
            self.log_test("Stock Levels and Alerts", "FAIL", f"Failed stock level test: {str(e)}")
    
    def test_purchase_order_basic(self):
        """Test basic purchase order functionality"""
        try:
            if not self.test_products or not self.test_warehouse or not self.test_supplier:
                self.log_test("Purchase Order Basic", "SKIP", "Skipping due to setup failure")
                return
            
            # Create purchase order
            po_items = []
            for product in self.test_products[:2]:  # Use first 2 products
                po_items.append({
                    'product_id': product.id,
                    'quantity': 50,
                    'unit_price': product.price * Decimal('0.6')
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
            assert purchase_order.items.count() == 2
            assert purchase_order.total_amount > 0
            
            self.log_test("Purchase Order Basic", "PASS", f"Created PO {purchase_order.po_number} with {purchase_order.items.count()} items")
            
        except Exception as e:
            self.log_test("Purchase Order Basic", "FAIL", f"Failed purchase order test: {str(e)}")
    
    def test_inventory_reports_basic(self):
        """Test basic inventory reporting"""
        try:
            if not self.test_warehouse:
                self.log_test("Inventory Reports Basic", "SKIP", "Skipping due to setup failure")
                return
            
            # Generate stock levels report
            stock_report = InventoryService.generate_inventory_report(
                report_type='stock_levels',
                warehouse_id=self.test_warehouse.id
            )
            
            assert 'summary' in stock_report
            assert 'details' in stock_report
            assert isinstance(stock_report['summary']['total_items'], int)
            assert isinstance(stock_report['summary']['total_quantity'], int)
            
            # Generate movements report
            movements_report = InventoryService.generate_inventory_report(
                report_type='movements',
                start_date=datetime.now().date() - timedelta(days=1),
                end_date=datetime.now().date()
            )
            
            assert 'summary' in movements_report
            assert 'details' in movements_report
            
            self.log_test("Inventory Reports Basic", "PASS", "Generated stock levels and movements reports successfully")
            
        except Exception as e:
            self.log_test("Inventory Reports Basic", "FAIL", f"Failed inventory reports: {str(e)}")
    
    def test_transaction_audit_trail(self):
        """Test transaction audit trail"""
        try:
            if not self.test_products or not self.test_warehouse:
                self.log_test("Transaction Audit Trail", "SKIP", "Skipping due to setup failure")
                return
            
            product = self.test_products[0]
            inventory = Inventory.objects.get(product=product, warehouse=self.test_warehouse)
            
            # Get initial transaction count
            initial_count = InventoryTransaction.objects.filter(inventory=inventory).count()
            
            # Perform some operations
            InventoryService.add_stock(
                inventory=inventory,
                quantity=50,
                user=self.test_user,
                transaction_type="PURCHASE",
                reference_number="AUDIT-TEST-001"
            )
            
            InventoryService.remove_stock(
                inventory=inventory,
                quantity=10,
                user=self.test_user,
                transaction_type="SALE",
                reference_number="AUDIT-TEST-002"
            )
            
            # Check transaction count increased
            final_count = InventoryTransaction.objects.filter(inventory=inventory).count()
            assert final_count >= initial_count + 2
            
            # Verify transaction details
            transactions = InventoryTransaction.objects.filter(
                inventory=inventory,
                reference_number__startswith="AUDIT-TEST"
            ).order_by('-created_at')
            
            assert transactions.count() >= 2
            
            for tx in transactions:
                assert tx.created_by == self.test_user
                assert tx.created_at is not None
                assert tx.transaction_type in ['PURCHASE', 'SALE']
            
            self.log_test("Transaction Audit Trail", "PASS", f"Audit trail working - {final_count - initial_count} new transactions recorded")
            
        except Exception as e:
            self.log_test("Transaction Audit Trail", "FAIL", f"Failed audit trail test: {str(e)}")
    
    def run_all_tests(self):
        """Run all core inventory tests"""
        print("=" * 60)
        print("INVENTORY CORE FLOW TESTING")
        print("=" * 60)
        
        test_methods = [
            self.test_inventory_creation,
            self.test_stock_operations,
            self.test_inventory_constraints,
            self.test_stock_levels_and_alerts,
            self.test_purchase_order_basic,
            self.test_inventory_reports_basic,
            self.test_transaction_audit_trail
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
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / (total_tests - skipped_tests)) * 100 if (total_tests - skipped_tests) > 0 else 0
            print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print("\nFAILED/ERROR TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # Save detailed report
        report_file = f"inventory_core_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'errors': error_tests,
            'skipped': skipped_tests,
            'success_rate': success_rate if total_tests > 0 else 0
        }


if __name__ == "__main__":
    # Run the core inventory tests
    tester = InventoryCoreTest()
    tester.run_all_tests()