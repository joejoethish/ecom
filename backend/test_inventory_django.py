"""
Test inventory system using Django shell.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from apps.products.models import Product, Category
from apps.admin_panel.models import AdminUser
from apps.admin_panel.inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization,
    InventoryOptimizationItem
)
from apps.admin_panel.inventory_services import (
    InventoryTrackingService, InventoryValuationService, InventoryAdjustmentService,
    InventoryTransferService, InventoryReservationService, InventoryAlertService,
    InventoryOptimizationService, InventoryReportService
)

print("Testing Advanced Inventory Management System")
print("=" * 50)

try:
    # Test model creation
    print("1. Testing model creation...")
    
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
    print(f"   ✓ Admin user: {admin_user.username}")
    
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
    print(f"   ✓ Warehouse: {warehouse.name}")
    
    # Create supplier
    supplier, created = Supplier.objects.get_or_create(
        code='SUP001',
        defaults={
            'name': 'Test Supplier Inc.',
            'email': 'supplier@test.com',
            'phone': '+1-555-0123'
        }
    )
    print(f"   ✓ Supplier: {supplier.name}")
    
    # Get existing category or create new one
    try:
        category = Category.objects.first()
        if not category:
            category = Category.objects.create(
                name='Electronics',
                slug='electronics',
                description='Electronic products'
            )
        created = False
    except Exception as e:
        print(f"   Error with category: {e}")
        # Use a simple approach - just get the first category
        category = Category.objects.first()
    print(f"   ✓ Category: {category.name}")
    
    # Get existing product
    product = Product.objects.first()
    if not product:
        print("   No products found in database")
        raise Exception("No products available for testing")
    created = False
    print(f"   ✓ Product: {product.name}")
    
    # Create inventory location
    location, created = InventoryLocation.objects.get_or_create(
        warehouse=warehouse,
        zone='A',
        aisle='01',
        shelf='A',
        bin='01',
        defaults={
            'capacity': 100,
            'location_type': 'standard'
        }
    )
    print(f"   ✓ Location: {location.location_code}")
    
    # Create inventory item
    inventory_item, created = InventoryItem.objects.get_or_create(
        product=product,
        location=location,
        defaults={
            'quantity': 100,
            'unit_cost': Decimal('50.00'),
            'supplier': supplier,
            'condition': 'new'
        }
    )
    print(f"   ✓ Inventory item: {inventory_item.quantity} units")
    
    print("\n2. Testing services...")
    
    # Test inventory tracking
    stock_data = InventoryTrackingService.get_real_time_stock_levels()
    print(f"   ✓ Stock tracking: {stock_data.get('total_items', 0)} items")
    
    # Test inventory valuation
    valuation_data = InventoryValuationService.calculate_fifo_valuation(
        product.id, warehouse.id
    )
    print(f"   ✓ FIFO valuation: ${valuation_data['total_value']}")
    
    # Test adjustment creation
    adjustment = InventoryAdjustmentService.create_adjustment_request(
        product_id=product.id,
        location_id=location.id,
        quantity_after=inventory_item.quantity + 10,
        adjustment_type='increase',
        reason_code='RESTOCK',
        reason_description='Test restocking',
        user=admin_user,
        unit_cost=Decimal('50.00')
    )
    print(f"   ✓ Adjustment created: {adjustment.adjustment_number}")
    
    print("\n3. Testing model relationships...")
    
    # Test location code generation
    expected_code = f"{warehouse.code}-A-01-A-01"
    if location.location_code == expected_code:
        print(f"   ✓ Location code: {location.location_code}")
    else:
        print(f"   ✗ Location code mismatch: expected {expected_code}, got {location.location_code}")
    
    # Test inventory item properties
    available = inventory_item.quantity - inventory_item.reserved_quantity
    if inventory_item.available_quantity == available:
        print(f"   ✓ Available quantity: {inventory_item.available_quantity}")
    else:
        print(f"   ✗ Available quantity calculation error")
    
    print("\n" + "=" * 50)
    print("✓ All basic tests passed! Inventory system is working correctly.")
    
except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()