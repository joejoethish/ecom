#!/usr/bin/env python3
"""
End-to-End Inventory Flow Testing
Complete inventory management workflow testing
"""

import os
import sys
import django
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

class InventoryE2ETest:
    """End-to-end inventory testing"""
    
    def __init__(self):
        self.test_results = []
        self.created_objects = {
            'users': [],
            'categories': [],
            'products': [],
            'warehouses': [],
            'suppliers': [],
            'inventories': [],
            'purchase_orders': []
        }
    
    def log_result(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{status_icon} [{test_name}] {message}")
        if details:
            print(f"    {details}")
    
    def setup_test_environment(self):
        """Setup complete test environment"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create test user
            user = User.objects.create_user(
                username=f'inventory_e2e_user_{timestamp}',
                email=f'e2e_test_{timestamp}@inventory.com',
                first_name='E2E',
                last_name='Test'
            )
            self.created_objects['users'].append(user)
            self.test_user = user
            
            # Create test category
            category = Category.objects.create(
                name=f'E2E Test Electronics {timestamp}',
                slug=f'e2e-test-electronics-{timestamp}'
            )
            self.created_objects['categories'].append(category)
            
            # Create test products
            products = []
            for i in range(5):
                product = Product.objects.create(
                    name=f'E2E Test Product {i+1}',
                    slug=f'e2e-test-product-{i+1}-{timestamp}',
                    sku=f'E2E-SKU-{i+1:03d}-{timestamp}',
                    description=f'E2E test product {i+1} for inventory testing',
                    price=Decimal('50.00') + (i * 25),
                    category=category,
                    is_active=True
                )
                products.append(product)
                self.created_objects['products'].append(product)
            
            # Create test warehouses
            warehouses = []
            for i in range(2):
                warehouse = Warehouse.objects.create(
                    name=f'E2E Test Warehouse {i+1}',
                    code=f'E2E-WH-{i+1}-{timestamp}',
                    location=f'Test City {i+1}',
                    address=f'{100 + i*100} Test Street',
                    capacity=5000 + (i * 2500)
                )
                warehouses.append(warehouse)
                self.created_objects['warehouses'].append(warehouse)
            
            # Create test suppliers
            suppliers = []
            for i in range(2):
                supplier = Supplier.objects.create(
                    name=f'E2E Test Supplier {i+1}',
                    code=f'E2E-SUP-{i+1}-{timestamp}',
                    email=f'supplier{i+1}@e2etest.com',
                    phone=f'+123456789{i}',
                    lead_time_days=7 + i,
                    reliability_rating=Decimal('4.5') + Decimal(str(i * 0.3))
                )
                suppliers.append(supplier)
                self.created_objects['suppliers'].append(supplier)
            
            self.test_products = products
            self.test_warehouses = warehouses
            self.test_suppliers = suppliers
            
            self.log_result("Environment Setup", "PASS", 
                          f"Created {len(products)} products, {len(warehouses)} warehouses, {len(suppliers)} suppliers")
            return True
            
        except Exception as e:
            self.log_result("Environment Setup", "FAIL", f"Setup failed: {str(e)}")
            return False
    
    def test_inventory_initialization(self):
        """Test inventory initialization for all products"""
        try:
            inventories_created = 0
            
            for warehouse in self.test_warehouses:
                for product in self.test_products:
                    # Assign supplier based on product index (handle UUID)
                    supplier_index = hash(str(product.id)) % len(self.test_suppliers)
                    supplier = self.test_suppliers[supplier_index]
                    
                    # Use get_or_create to avoid duplicates
                    inventory, created = Inventory.objects.get_or_create(
                        product=product,
                        warehouse=warehouse,
                        defaults={
                            'quantity': 0,  # Start with zero stock
                            'cost_price': product.price * Decimal('0.6'),  # 60% of selling price
                            'minimum_stock_level': 10,
                            'maximum_stock_level': 500,
                            'reorder_point': 25,
                            'supplier': supplier
                        }
                    )
                    if created:
                        self.created_objects['inventories'].append(inventory)
                        inventories_created += 1
            
            self.log_result("Inventory Initialization", "PASS", 
                          f"Created {inventories_created} inventory records")
            return True
            
        except Exception as e:
            self.log_result("Inventory Initialization", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_purchase_order_workflow(self):
        """Test complete purchase order workflow"""
        try:
            # Ensure we have inventory items first
            if not Inventory.objects.exists():
                self.log_result("Purchase Order Workflow", "SKIP", "No inventory items available")
                return True
                
            # Create purchase orders for each supplier
            purchase_orders = []
            
            for supplier in self.test_suppliers:
                # Get products for this supplier
                supplier_inventories = Inventory.objects.filter(supplier=supplier)
                
                if not supplier_inventories.exists():
                    continue
                
                # Create PO items
                po_items = []
                for inventory in supplier_inventories[:3]:  # First 3 products per supplier
                    po_items.append({
                        'product_id': inventory.product.id,
                        'quantity': 100,
                        'unit_price': inventory.cost_price
                    })
                
                # Create purchase order
                po = PurchaseOrderService.create_purchase_order(
                    supplier_id=supplier.id,
                    warehouse_id=self.test_warehouses[0].id,  # Use first warehouse
                    items=po_items,
                    user=self.test_user,
                    notes=f"E2E test purchase order for {supplier.name}",
                    expected_delivery_date=datetime.now().date() + timedelta(days=supplier.lead_time_days)
                )
                
                purchase_orders.append(po)
                self.created_objects['purchase_orders'].append(po)
                
                # Receive the purchase order (simulate delivery)
                received_items = {}
                for item in po.items.all():
                    received_items[item.id] = item.quantity_ordered
                
                updated_po = PurchaseOrderService.receive_purchase_order(
                    purchase_order_id=po.id,
                    received_items=received_items,
                    user=self.test_user,
                    notes="E2E test - full delivery received"
                )
                
                assert updated_po.status == "RECEIVED"
            
            self.log_result("Purchase Order Workflow", "PASS", 
                          f"Created and received {len(purchase_orders)} purchase orders")
            return True
            
        except Exception as e:
            self.log_result("Purchase Order Workflow", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_stock_operations(self):
        """Test various stock operations"""
        try:
            operations_count = 0
            
            # Get inventories with stock
            inventories_with_stock = Inventory.objects.filter(quantity__gt=0)
            
            for inventory in inventories_with_stock[:3]:  # Test with first 3
                # Test stock removal (sale)
                sale_quantity = min(20, inventory.quantity // 2)
                if sale_quantity > 0:
                    InventoryService.remove_stock(
                        inventory=inventory,
                        quantity=sale_quantity,
                        user=self.test_user,
                        transaction_type="SALE",
                        reference_number=f"E2E-SALE-{operations_count + 1}",
                        notes="E2E test sale"
                    )
                    operations_count += 1
                
                # Test stock reservation
                reserve_quantity = min(10, inventory.available_quantity)
                if reserve_quantity > 0:
                    InventoryService.reserve_stock(
                        inventory=inventory,
                        quantity=reserve_quantity,
                        user=self.test_user,
                        reference_number=f"E2E-RESERVE-{operations_count + 1}",
                        notes="E2E test reservation"
                    )
                    operations_count += 1
                
                # Test stock adjustment
                InventoryService.adjust_inventory(
                    inventory=inventory,
                    adjustment_quantity=-5,  # Small reduction for damaged goods
                    user=self.test_user,
                    reason="E2E test - damaged goods",
                    reference_number=f"E2E-ADJUST-{operations_count + 1}"
                )
                operations_count += 1
            
            self.log_result("Stock Operations", "PASS", 
                          f"Completed {operations_count} stock operations")
            return True
            
        except Exception as e:
            self.log_result("Stock Operations", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_stock_transfer(self):
        """Test stock transfer between warehouses"""
        try:
            if len(self.test_warehouses) < 2:
                self.log_result("Stock Transfer", "SKIP", "Need at least 2 warehouses")
                return True
            
            transfers_completed = 0
            
            # Find products that exist in both warehouses
            for product in self.test_products[:2]:  # Test with first 2 products
                try:
                    source_inventory = Inventory.objects.get(
                        product=product, 
                        warehouse=self.test_warehouses[0]
                    )
                    dest_inventory = Inventory.objects.get(
                        product=product, 
                        warehouse=self.test_warehouses[1]
                    )
                    
                    # Transfer stock if source has enough
                    transfer_quantity = min(15, source_inventory.available_quantity)
                    if transfer_quantity > 0:
                        InventoryService.transfer_stock(
                            source_inventory=source_inventory,
                            destination_inventory=dest_inventory,
                            quantity=transfer_quantity,
                            user=self.test_user,
                            reference_number=f"E2E-TRANSFER-{transfers_completed + 1}",
                            notes="E2E test transfer"
                        )
                        transfers_completed += 1
                
                except Inventory.DoesNotExist:
                    continue  # Skip if inventory doesn't exist in both warehouses
            
            self.log_result("Stock Transfer", "PASS", 
                          f"Completed {transfers_completed} stock transfers")
            return True
            
        except Exception as e:
            self.log_result("Stock Transfer", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_inventory_alerts(self):
        """Test inventory alert system"""
        try:
            # Force some inventories to low stock
            low_stock_created = 0
            
            for inventory in Inventory.objects.all()[:2]:
                if inventory.quantity > inventory.reorder_point:
                    # Adjust to create low stock situation
                    adjustment = inventory.reorder_point - inventory.quantity - 5
                    InventoryService.adjust_inventory(
                        inventory=inventory,
                        adjustment_quantity=adjustment,
                        user=self.test_user,
                        reason="E2E test - create low stock scenario",
                        reference_number=f"E2E-LOW-STOCK-{low_stock_created + 1}"
                    )
                    low_stock_created += 1
            
            # Test alert detection
            low_stock_items = InventoryService.get_low_stock_items()
            overstock_items = InventoryService.get_overstock_items()
            
            self.log_result("Inventory Alerts", "PASS", 
                          f"Low stock: {low_stock_items.count()}, Overstock: {overstock_items.count()}")
            return True
            
        except Exception as e:
            self.log_result("Inventory Alerts", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_inventory_reporting(self):
        """Test inventory reporting functionality"""
        try:
            reports_generated = 0
            
            # Test stock levels report
            stock_report = InventoryService.generate_inventory_report(
                report_type='stock_levels',
                warehouse_id=self.test_warehouses[0].id
            )
            assert 'summary' in stock_report
            reports_generated += 1
            
            # Test movements report
            movements_report = InventoryService.generate_inventory_report(
                report_type='movements',
                start_date=datetime.now().date() - timedelta(days=1),
                end_date=datetime.now().date()
            )
            assert 'summary' in movements_report
            reports_generated += 1
            
            # Test valuation report
            valuation_report = InventoryService.generate_inventory_report(
                report_type='valuation'
            )
            assert 'summary' in valuation_report
            reports_generated += 1
            
            self.log_result("Inventory Reporting", "PASS", 
                          f"Generated {reports_generated} reports successfully")
            return True
            
        except Exception as e:
            self.log_result("Inventory Reporting", "FAIL", f"Failed: {str(e)}")
            return False
    
    def test_data_integrity(self):
        """Test data integrity and business rules"""
        try:
            integrity_checks = 0
            
            # Check transaction audit trail
            total_transactions = InventoryTransaction.objects.count()
            transactions_with_user = InventoryTransaction.objects.filter(created_by__isnull=False).count()
            
            assert transactions_with_user == total_transactions, "All transactions should have a user"
            integrity_checks += 1
            
            # Check inventory consistency
            for inventory in Inventory.objects.all():
                # Available quantity should never be negative
                assert inventory.available_quantity >= 0, f"Negative available quantity: {inventory}"
                
                # Reserved quantity should not exceed total quantity
                assert inventory.reserved_quantity <= inventory.quantity, f"Over-reservation: {inventory}"
                
                integrity_checks += 1
            
            # Check purchase order consistency
            for po in PurchaseOrder.objects.all():
                calculated_total = sum(item.total_price for item in po.items.all())
                assert abs(po.total_amount - calculated_total) < Decimal('0.01'), f"PO total mismatch: {po}"
                integrity_checks += 1
            
            self.log_result("Data Integrity", "PASS", 
                          f"Completed {integrity_checks} integrity checks")
            return True
            
        except Exception as e:
            self.log_result("Data Integrity", "FAIL", f"Failed: {str(e)}")
            return False
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "=" * 80)
        print("INVENTORY E2E TEST FINAL REPORT")
        print("=" * 80)
        
        # Test summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        
        print(f"\nTEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / (total_tests - skipped_tests)) * 100 if (total_tests - skipped_tests) > 0 else 0
            print(f"  Success Rate: {success_rate:.1f}%")
        
        # Inventory statistics
        print(f"\nINVENTORY STATISTICS:")
        print(f"  Products: {len(self.created_objects['products'])}")
        print(f"  Warehouses: {len(self.created_objects['warehouses'])}")
        print(f"  Suppliers: {len(self.created_objects['suppliers'])}")
        print(f"  Inventories: {len(self.created_objects['inventories'])}")
        print(f"  Purchase Orders: {len(self.created_objects['purchase_orders'])}")
        print(f"  Transactions: {InventoryTransaction.objects.count()}")
        
        # Current stock status
        total_stock_value = InventoryService.get_stock_value()['total_value']
        low_stock_count = InventoryService.get_low_stock_items().count()
        overstock_count = InventoryService.get_overstock_items().count()
        
        print(f"\nCURRENT STOCK STATUS:")
        print(f"  Total Stock Value: ${total_stock_value}")
        print(f"  Low Stock Items: {low_stock_count}")
        print(f"  Overstock Items: {overstock_count}")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  ✗ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        if failed_tests == 0:
            print("🎉 INVENTORY SYSTEM: ALL TESTS PASSED")
            print("✓ Complete inventory workflow is functional")
            print("✓ All business rules are working correctly")
            print("✓ Data integrity is maintained")
        else:
            print("⚠️  INVENTORY SYSTEM: SOME ISSUES DETECTED")
            print(f"✗ {failed_tests} test(s) failed")
        
        print("=" * 80)
        
        return success_rate if total_tests > 0 else 0
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Delete in reverse order of creation to handle dependencies
            for po in self.created_objects['purchase_orders']:
                po.delete()
            
            for inventory in self.created_objects['inventories']:
                inventory.delete()
            
            for supplier in self.created_objects['suppliers']:
                supplier.delete()
            
            for warehouse in self.created_objects['warehouses']:
                warehouse.delete()
            
            for product in self.created_objects['products']:
                product.delete()
            
            for category in self.created_objects['categories']:
                category.delete()
            
            for user in self.created_objects['users']:
                user.delete()
            
            print("✓ Test data cleaned up successfully")
            
        except Exception as e:
            print(f"⚠ Cleanup warning: {str(e)}")
    
    def run_all_tests(self):
        """Run all E2E tests"""
        print("=" * 80)
        print("INVENTORY END-TO-END TESTING")
        print("=" * 80)
        
        try:
            # Setup
            if not self.setup_test_environment():
                return 0
            
            # Run tests
            test_methods = [
                self.test_inventory_initialization,
                self.test_purchase_order_workflow,
                self.test_stock_operations,
                self.test_stock_transfer,
                self.test_inventory_alerts,
                self.test_inventory_reporting,
                self.test_data_integrity
            ]
            
            for test_method in test_methods:
                try:
                    test_method()
                except Exception as e:
                    self.log_result(test_method.__name__, "ERROR", f"Unexpected error: {str(e)}")
            
            # Generate report
            success_rate = self.generate_final_report()
            
            return success_rate
            
        finally:
            # Always cleanup
            self.cleanup_test_data()


if __name__ == "__main__":
    tester = InventoryE2ETest()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if success_rate >= 90 else 1
    sys.exit(exit_code)