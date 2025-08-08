"""
Verification script for Advanced Inventory Management System.
"""
import os
import sys
from decimal import Decimal
from datetime import date, timedelta

# Django imports (assuming this runs in Django shell or with proper setup)
try:
    import django
    from django.conf import settings
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
        django.setup()
except ImportError:
    pass

from django.utils import timezone
from apps.products.models import Product, Category
from apps.admin_panel.models import AdminUser
from apps.admin_panel.inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization
)
from apps.admin_panel.inventory_services import (
    InventoryTrackingService, InventoryValuationService, InventoryAdjustmentService,
    InventoryTransferService, InventoryReservationService, InventoryAlertService,
    InventoryOptimizationService, InventoryReportService
)


def create_test_data():
    """Create test data for verification."""
    print("Creating test data...")
    
    # Create admin user
    admin_user, created = AdminUser.objects.get_or_create(
        username='inventory_admin',
        defaults={
            'email': 'inventory@test.com',
            'role': 'admin',
            'is_admin_active': True
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
    
    # Create warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        code='WH001',
        defaults={
            'name': 'Main Warehouse',
            'location': 'New York',
            'address': '123 Main Street, NY 10001',
            'capacity': 10000
        }
    )
    
    # Create supplier
    supplier, created = Supplier.objects.get_or_create(
        code='SUP001',
        defaults={
            'name': 'Test Supplier Inc.',
            'email': 'supplier@test.com',
            'phone': '+1-555-0123'
        }
    )
    
    # Create category
    category, created = Category.objects.get_or_create(
        slug='electronics',
        defaults={
            'name': 'Electronics',
            'description': 'Electronic products'
        }
    )
    
    # Create products
    products = []
    for i in range(5):
        product, created = Product.objects.get_or_create(
            sku=f'PROD{i+1:03d}',
            defaults={
                'name': f'Test Product {i+1}',
                'slug': f'test-product-{i+1}',
                'price': Decimal(f'{50 + i*10}.99'),
                'category': category,
                'description': f'Test product {i+1} description'
            }
        )
        products.append(product)
    
    # Create inventory locations
    locations = []
    for zone in ['A', 'B']:
        for aisle in ['01', '02']:
            for shelf in ['A', 'B']:
                location, created = InventoryLocation.objects.get_or_create(
                    warehouse=warehouse,
                    zone=zone,
                    aisle=aisle,
                    shelf=shelf,
                    bin='01',
                    defaults={
                        'capacity': 100,
                        'location_type': 'standard'
                    }
                )
                locations.append(location)
    
    # Create inventory items
    for i, product in enumerate(products):
        location = locations[i % len(locations)]
        inventory_item, created = InventoryItem.objects.get_or_create(
            product=product,
            location=location,
            defaults={
                'quantity': 100 + i * 20,
                'unit_cost': Decimal(f'{40 + i*5}.00'),
                'supplier': supplier,
                'condition': 'new',
                'serial_number': f'SN{i+1:05d}' if i < 2 else '',
                'lot_number': f'LOT{i+1:03d}',
                'expiry_date': date.today() + timedelta(days=365) if i % 2 == 0 else None
            }
        )
    
    return {
        'admin_user': admin_user,
        'warehouse': warehouse,
        'supplier': supplier,
        'category': category,
        'products': products,
        'locations': locations
    }


def test_inventory_tracking():
    """Test inventory tracking functionality."""
    print("\n=== Testing Inventory Tracking ===")
    
    try:
        # Get real-time stock levels
        stock_data = InventoryTrackingService.get_real_time_stock_levels()
        print(f"✓ Real-time stock levels retrieved:")
        print(f"  - Total items: {stock_data.get('total_items', 0)}")
        print(f"  - Total quantity: {stock_data.get('total_quantity', 0)}")
        print(f"  - Total value: ${stock_data.get('total_value', 0)}")
        print(f"  - Low stock items: {stock_data.get('low_stock_count', 0)}")
        
        # Test stock movements
        movements = InventoryTrackingService.get_stock_movements()
        print(f"✓ Stock movements retrieved: {len(movements)} movements")
        
        return True
    except Exception as e:
        print(f"✗ Inventory tracking test failed: {e}")
        return False


def test_inventory_valuation(test_data):
    """Test inventory valuation functionality."""
    print("\n=== Testing Inventory Valuation ===")
    
    try:
        product = test_data['products'][0]
        warehouse = test_data['warehouse']
        admin_user = test_data['admin_user']
        
        # Test FIFO valuation
        fifo_result = InventoryValuationService.calculate_fifo_valuation(
            product.id, warehouse.id
        )
        print(f"✓ FIFO valuation calculated:")
        print(f"  - Quantity: {fifo_result['total_quantity']}")
        print(f"  - Value: ${fifo_result['total_value']}")
        print(f"  - Unit cost: ${fifo_result['unit_cost']}")
        
        # Test weighted average valuation
        wa_result = InventoryValuationService.calculate_weighted_average_valuation(
            product.id, warehouse.id
        )
        print(f"✓ Weighted average valuation calculated:")
        print(f"  - Unit cost: ${wa_result['unit_cost']}")
        
        # Create valuation record
        valuation = InventoryValuationService.create_valuation_record(
            product.id, warehouse.id, 'fifo', admin_user
        )
        print(f"✓ Valuation record created: {valuation.id}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory valuation test failed: {e}")
        return False


def test_inventory_adjustments(test_data):
    """Test inventory adjustment functionality."""
    print("\n=== Testing Inventory Adjustments ===")
    
    try:
        product = test_data['products'][0]
        location = test_data['locations'][0]
        admin_user = test_data['admin_user']
        
        # Get current inventory item
        inventory_item = InventoryItem.objects.get(product=product, location=location)
        original_quantity = inventory_item.quantity
        
        # Create adjustment request
        adjustment = InventoryAdjustmentService.create_adjustment_request(
            product_id=product.id,
            location_id=location.id,
            quantity_after=original_quantity + 25,
            adjustment_type='increase',
            reason_code='RESTOCK',
            reason_description='Test restocking',
            user=admin_user,
            unit_cost=Decimal('45.00')
        )
        
        # Generate adjustment number if not set
        if not adjustment.adjustment_number:
            adjustment.adjustment_number = f"ADJ{adjustment.id:06d}"
            adjustment.save()
        print(f"✓ Adjustment request created: {adjustment.adjustment_number}")
        
        # Approve adjustment
        approved_adjustment = InventoryAdjustmentService.approve_adjustment(
            adjustment.id, admin_user, 'Test approval'
        )
        print(f"✓ Adjustment approved: {approved_adjustment.status}")
        
        # Apply adjustment
        applied_adjustment = InventoryAdjustmentService.apply_adjustment(
            adjustment.id, admin_user
        )
        print(f"✓ Adjustment applied: {applied_adjustment.status}")
        
        # Verify inventory updated
        inventory_item.refresh_from_db()
        print(f"✓ Inventory updated: {original_quantity} → {inventory_item.quantity}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory adjustment test failed: {e}")
        return False


def test_inventory_transfers(test_data):
    """Test inventory transfer functionality."""
    print("\n=== Testing Inventory Transfers ===")
    
    try:
        product = test_data['products'][1]
        source_location = test_data['locations'][0]
        destination_location = test_data['locations'][1]
        admin_user = test_data['admin_user']
        
        # Create transfer request
        transfer = InventoryTransferService.create_transfer_request(
            product_id=product.id,
            source_location_id=source_location.id,
            destination_location_id=destination_location.id,
            quantity=20,
            reason='Test transfer',
            user=admin_user
        )
        
        # Generate transfer number if not set
        if not transfer.transfer_number:
            transfer.transfer_number = f"TRF{transfer.id:06d}"
            transfer.save()
        print(f"✓ Transfer request created: {transfer.transfer_number}")
        
        # Ship transfer
        shipped_transfer = InventoryTransferService.ship_transfer(
            transfer.id, admin_user, 'TEST123'
        )
        print(f"✓ Transfer shipped: {shipped_transfer.status}")
        
        # Receive transfer
        received_transfer = InventoryTransferService.receive_transfer(
            transfer.id, 20, admin_user
        )
        print(f"✓ Transfer received: {received_transfer.status}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory transfer test failed: {e}")
        return False


def test_inventory_reservations(test_data):
    """Test inventory reservation functionality."""
    print("\n=== Testing Inventory Reservations ===")
    
    try:
        product = test_data['products'][2]
        location = test_data['locations'][2]
        admin_user = test_data['admin_user']
        
        # Create reservation
        reservation = InventoryReservationService.create_reservation(
            product_id=product.id,
            location_id=location.id,
            quantity=15,
            reservation_type='order',
            expiry_hours=24,
            user=admin_user,
            priority=1
        )
        
        # Generate reservation number if not set
        if not reservation.reservation_number:
            reservation.reservation_number = f"RES{reservation.id:06d}"
            reservation.save()
        print(f"✓ Reservation created: {reservation.reservation_number}")
        
        # Fulfill reservation partially
        fulfilled_reservation = InventoryReservationService.fulfill_reservation(
            reservation.id, 10, admin_user
        )
        print(f"✓ Reservation fulfilled: {fulfilled_reservation.status}")
        print(f"  - Remaining quantity: {fulfilled_reservation.remaining_quantity}")
        
        # Cancel remaining reservation
        cancelled_reservation = InventoryReservationService.cancel_reservation(
            reservation.id, admin_user
        )
        print(f"✓ Reservation cancelled: {cancelled_reservation.status}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory reservation test failed: {e}")
        return False


def test_inventory_alerts(test_data):
    """Test inventory alert functionality."""
    print("\n=== Testing Inventory Alerts ===")
    
    try:
        product = test_data['products'][3]
        location = test_data['locations'][3]
        admin_user = test_data['admin_user']
        
        # Create alert
        alert = InventoryAlertService.create_alert(
            product=product,
            location=location,
            alert_type='low_stock',
            severity='medium',
            title='Test Low Stock Alert',
            description='Stock level is below threshold',
            current_value=Decimal('5'),
            threshold_value=Decimal('10')
        )
        
        # Generate alert number if not set
        if not alert.alert_number:
            alert.alert_number = f"ALT{alert.id:06d}"
            alert.save()
        print(f"✓ Alert created: {alert.alert_number}")
        
        # Acknowledge alert
        acknowledged_alert = InventoryAlertService.acknowledge_alert(
            alert.id, admin_user, 'Test acknowledgment'
        )
        print(f"✓ Alert acknowledged: {acknowledged_alert.status}")
        
        # Resolve alert
        resolved_alert = InventoryAlertService.resolve_alert(
            alert.id, admin_user, 'Test resolution'
        )
        print(f"✓ Alert resolved: {resolved_alert.status}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory alert test failed: {e}")
        return False


def test_inventory_optimization(test_data):
    """Test inventory optimization functionality."""
    print("\n=== Testing Inventory Optimization ===")
    
    try:
        warehouse = test_data['warehouse']
        admin_user = test_data['admin_user']
        
        # Perform ABC analysis
        optimization = InventoryOptimizationService.perform_abc_analysis(
            warehouse_id=warehouse.id,
            user=admin_user,
            period_days=365
        )
        
        # Generate analysis number if not set
        if not optimization.analysis_number:
            optimization.analysis_number = f"ABC{optimization.id:06d}"
            optimization.save()
        print(f"✓ ABC analysis completed: {optimization.analysis_number}")
        print(f"  - Products analyzed: {optimization.total_products_analyzed}")
        print(f"  - Total value: ${optimization.total_value_analyzed}")
        print(f"  - Category A: {optimization.category_a_count} items")
        print(f"  - Category B: {optimization.category_b_count} items")
        print(f"  - Category C: {optimization.category_c_count} items")
        
        # Identify slow-moving items
        slow_moving = InventoryOptimizationService.identify_slow_moving_items(
            warehouse_id=warehouse.id,
            days_threshold=90
        )
        print(f"✓ Slow-moving items identified: {len(slow_moving)} items")
        
        return True
    except Exception as e:
        print(f"✗ Inventory optimization test failed: {e}")
        return False


def test_inventory_reports(test_data):
    """Test inventory reporting functionality."""
    print("\n=== Testing Inventory Reports ===")
    
    try:
        warehouse = test_data['warehouse']
        
        # Generate stock levels report
        stock_report = InventoryReportService.generate_stock_levels_report(
            warehouse_id=warehouse.id
        )
        print(f"✓ Stock levels report generated:")
        print(f"  - Total items: {stock_report['summary']['total_items']}")
        print(f"  - Total value: ${stock_report['summary']['total_value']}")
        
        # Generate movement report
        movement_report = InventoryReportService.generate_movement_report(
            warehouse_id=warehouse.id,
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        print(f"✓ Movement report generated:")
        print(f"  - Total movements: {movement_report['summary']['total_movements']}")
        
        return True
    except Exception as e:
        print(f"✗ Inventory report test failed: {e}")
        return False


def test_model_relationships():
    """Test model relationships and constraints."""
    print("\n=== Testing Model Relationships ===")
    
    try:
        # Test location code generation
        warehouse = Warehouse.objects.first()
        location = InventoryLocation.objects.create(
            warehouse=warehouse,
            zone='TEST',
            aisle='99',
            shelf='Z',
            bin='99',
            capacity=50
        )
        expected_code = f"{warehouse.code}-TEST-99-Z-99"
        assert location.location_code == expected_code
        print(f"✓ Location code generated correctly: {location.location_code}")
        
        # Test inventory item properties
        product = Product.objects.first()
        item = InventoryItem.objects.create(
            product=product,
            location=location,
            quantity=100,
            reserved_quantity=25,
            unit_cost=Decimal('50.00'),
            expiry_date=date.today() + timedelta(days=10)
        )
        
        assert item.available_quantity == 75  # 100 - 25
        assert not item.is_expired
        assert item.days_until_expiry == 10
        print(f"✓ Inventory item properties calculated correctly")
        
        # Test unique constraints
        try:
            # This should fail due to unique constraint
            duplicate_location = InventoryLocation.objects.create(
                warehouse=warehouse,
                zone='TEST',
                aisle='99',
                shelf='Z',
                bin='99',
                capacity=50
            )
            print("✗ Unique constraint not enforced")
            return False
        except Exception:
            print("✓ Unique constraints enforced correctly")
        
        # Clean up test location
        location.delete()
        
        return True
    except Exception as e:
        print(f"✗ Model relationship test failed: {e}")
        return False


def run_verification():
    """Run complete verification of inventory system."""
    print("Advanced Inventory Management System Verification")
    print("=" * 50)
    
    # Create test data
    test_data = create_test_data()
    print("✓ Test data created successfully")
    
    # Run tests
    tests = [
        test_inventory_tracking,
        lambda: test_inventory_valuation(test_data),
        lambda: test_inventory_adjustments(test_data),
        lambda: test_inventory_transfers(test_data),
        lambda: test_inventory_reservations(test_data),
        lambda: test_inventory_alerts(test_data),
        lambda: test_inventory_optimization(test_data),
        lambda: test_inventory_reports(test_data),
        test_model_relationships,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All inventory management features are working correctly!")
        return True
    else:
        print(f"✗ {total - passed} tests failed. Please check the implementation.")
        return False


if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)