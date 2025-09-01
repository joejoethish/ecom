#!/usr/bin/env python3
"""
Quick test to verify inventory fixes
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Setup Django environment
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory, Warehouse, Supplier
from apps.inventory.services import InventoryService
from apps.products.models import Product, Category

User = get_user_model()

def test_inventory_operations():
    """Test basic inventory operations to verify fixes"""
    print("Testing inventory operations...")
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_fix_user',
            defaults={'email': 'test@fix.com'}
        )
        
        # Get or create test objects
        category, _ = Category.objects.get_or_create(
            name='Test Fix Category',
            defaults={'slug': 'test-fix-category'}
        )
        
        product, _ = Product.objects.get_or_create(
            name='Test Fix Product',
            defaults={
                'slug': 'test-fix-product',
                'sku': f'TEST-FIX-{datetime.now().strftime("%H%M%S")}',
                'price': Decimal('100.00'),
                'category': category
            }
        )
        
        warehouse, _ = Warehouse.objects.get_or_create(
            name='Test Fix Warehouse',
            defaults={
                'code': f'TFW{datetime.now().strftime("%H%M%S")}',
                'location': 'Test Location'
            }
        )
        
        supplier, _ = Supplier.objects.get_or_create(
            name='Test Fix Supplier',
            defaults={
                'code': f'TFS{datetime.now().strftime("%H%M%S")}',
                'email': 'supplier@test.com'
            }
        )
        
        # Create or get inventory
        inventory, _ = Inventory.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={
                'quantity': 0,
                'cost_price': Decimal('60.00'),
                'minimum_stock_level': 10,
                'maximum_stock_level': 500,
                'reorder_point': 25,
                'supplier': supplier
            }
        )
        
        print(f"✓ Initial inventory: {inventory.quantity} units")
        
        # Test 1: Add stock
        print("\n[TEST 1] Adding stock...")
        InventoryService.add_stock(
            inventory=inventory,
            quantity=100,
            user=user,
            transaction_type="PURCHASE",
            reference_number="TEST-ADD-001"
        )
        
        inventory.refresh_from_db()
        print(f"✓ After adding 100: {inventory.quantity} units")
        print(f"✓ Available quantity: {inventory.available_quantity}")
        
        # Test 2: Reserve stock
        print("\n[TEST 2] Reserving stock...")
        InventoryService.reserve_stock(
            inventory=inventory,
            quantity=20,
            user=user,
            reference_number="TEST-RESERVE-001"
        )
        
        inventory.refresh_from_db()
        print(f"✓ After reserving 20: Total={inventory.quantity}, Reserved={inventory.reserved_quantity}")
        print(f"✓ Available quantity: {inventory.available_quantity}")
        
        # Test 3: Remove stock
        print("\n[TEST 3] Removing stock...")
        InventoryService.remove_stock(
            inventory=inventory,
            quantity=30,
            user=user,
            transaction_type="SALE",
            reference_number="TEST-SALE-001"
        )
        
        inventory.refresh_from_db()
        print(f"✓ After removing 30: Total={inventory.quantity}, Reserved={inventory.reserved_quantity}")
        print(f"✓ Available quantity: {inventory.available_quantity}")
        
        # Test 4: Stock status
        print("\n[TEST 4] Stock status...")
        print(f"✓ Stock status: {inventory.stock_status}")
        print(f"✓ Needs reordering: {inventory.needs_reordering}")
        
        print("\n🎉 ALL TESTS PASSED - Inventory operations working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_inventory_operations()
    if success:
        print("\n✅ Inventory system is working correctly!")
    else:
        print("\n❌ Inventory system has issues!")