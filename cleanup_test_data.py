#!/usr/bin/env python3
"""
Clean up test data from inventory tests
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory, InventoryTransaction, Warehouse, Supplier, PurchaseOrder
from apps.products.models import Product, Category

User = get_user_model()

def cleanup_test_data():
    """Clean up all test data"""
    print("Cleaning up test data...")
    
    try:
        # Delete test transactions
        deleted_transactions = InventoryTransaction.objects.filter(
            reference_number__startswith='TEST'
        ).delete()
        print(f"✓ Deleted {deleted_transactions[0]} test transactions")
        
        deleted_transactions = InventoryTransaction.objects.filter(
            reference_number__startswith='E2E'
        ).delete()
        print(f"✓ Deleted {deleted_transactions[0]} E2E transactions")
        
        deleted_transactions = InventoryTransaction.objects.filter(
            reference_number__startswith='AUDIT'
        ).delete()
        print(f"✓ Deleted {deleted_transactions[0]} audit transactions")
        
        # Delete test purchase orders
        deleted_pos = PurchaseOrder.objects.filter(
            notes__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_pos[0]} test purchase orders")
        
        # Delete test inventories
        deleted_inventories = Inventory.objects.filter(
            product__name__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_inventories[0]} test inventories")
        
        # Delete test products
        deleted_products = Product.objects.filter(
            name__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_products[0]} test products")
        
        # Delete test categories
        deleted_categories = Category.objects.filter(
            name__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_categories[0]} test categories")
        
        # Delete test warehouses
        deleted_warehouses = Warehouse.objects.filter(
            name__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_warehouses[0]} test warehouses")
        
        # Delete test suppliers
        deleted_suppliers = Supplier.objects.filter(
            name__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_suppliers[0]} test suppliers")
        
        # Delete test users
        deleted_users = User.objects.filter(
            username__icontains='test'
        ).delete()
        print(f"✓ Deleted {deleted_users[0]} test users")
        
        print("\n🎉 Test data cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")

if __name__ == "__main__":
    cleanup_test_data()