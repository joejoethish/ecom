#!/usr/bin/env python
"""
Simple test script for inventory system.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

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

def test_basic_functionality():
    """Test basic inventory functionality."""
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
        
        # Create category
        category, created = Category.objects.get_or_create(
            slug='electronics',
            defaults={
                'name': 'Electronics',
                'description': 'Electronic products'
            }
        )
        print(f"   ✓ Category: {category.name}")
        
        # Create product
        product, created = Product.objects.get_or_create(
            sku='PROD001',
            defaults={
                'name': 'Test Product',
                'slug': 'test-product',
                'price': Decimal('99.99'),
                'category': category,
                'description': 'Test product description'
            }
        )
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
        assert location.location_code == f"{warehouse.code}-A-01-A-01"
        print(f"   ✓ Location code: {location.location_code}")
        
        # Test inventory item properties
        assert inventory_item.available_quantity == inventory_item.quantity - inventory_item.reserved_quantity
        print(f"   ✓ Available quantity: {inventory_item.available_quantity}")
        
        print("\n" + "=" * 50)
        print("✓ All basic tests passed! Inventory system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_basic_functionality()
    exit(0 if success else 1)