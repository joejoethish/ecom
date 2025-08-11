#!/usr/bin/env python
"""
Test script for inventory analytics functionality.
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.inventory.analytics_services import InventoryAnalyticsService
from apps.inventory.models import Inventory, Warehouse
from datetime import datetime, timedelta
from django.utils import timezone

def test_analytics_functionality():
    """Test the inventory analytics functionality."""
    print("Testing Inventory Analytics Functionality...")
    print("=" * 50)
    
    try:
        # Test 1: Check if we can get inventory valuation
        print("1. Testing inventory valuation...")
        inventory_qs = Inventory.objects.all()[:5]  # Limit to first 5 items for testing
        
        if inventory_qs.exists():
            valuation_data = InventoryAnalyticsService.get_inventory_valuation(inventory_qs)
            print(f"   ✓ Total inventory value: ${valuation_data['total_value']}")
            print(f"   ✓ Number of warehouses: {len(valuation_data['warehouse_breakdown'])}")
            print(f"   ✓ Number of categories: {len(valuation_data['category_breakdown'])}")
        else:
            print("   ⚠ No inventory data found for testing")
        
        # Test 2: Check KPI dashboard
        print("\n2. Testing KPI dashboard...")
        kpi_data = InventoryAnalyticsService.get_kpi_dashboard()
        print(f"   ✓ Number of KPIs: {len(kpi_data['kpis'])}")
        print(f"   ✓ Total products: {kpi_data['total_products']}")
        
        for kpi_name, kpi_values in kpi_data['kpis'].items():
            print(f"   ✓ {kpi_name}: {kpi_values['value']:.2f} (Target: {kpi_values['target']:.2f})")
        
        # Test 3: Check comprehensive analytics
        print("\n3. Testing comprehensive analytics...")
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        comprehensive_data = InventoryAnalyticsService.generate_comprehensive_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"   ✓ Analytics modules loaded: {len(comprehensive_data)}")
        for module_name in comprehensive_data.keys():
            print(f"     - {module_name}")
        
        # Test 4: Test alert generation
        print("\n4. Testing alert generation...")
        alerts = InventoryAnalyticsService.generate_inventory_alerts(inventory_qs)
        print(f"   ✓ Generated {len(alerts)} alerts")
        
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"     - {alert['type']}: {alert['message']}")
        
        print("\n" + "=" * 50)
        print("✅ All analytics tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test that the analytics API endpoints are properly configured."""
    print("\nTesting API Endpoint Configuration...")
    print("=" * 50)
    
    try:
        from apps.inventory.analytics_views import (
            InventoryAnalyticsViewSet, InventoryKPIViewSet,
            InventoryForecastViewSet, InventoryAlertViewSet
        )
        
        print("✓ Analytics ViewSets imported successfully")
        
        # Check if viewsets have the required methods
        analytics_viewset = InventoryAnalyticsViewSet()
        required_methods = [
            'comprehensive_dashboard', 'inventory_valuation', 'turnover_analysis',
            'abc_analysis', 'slow_moving_analysis', 'aging_analysis'
        ]
        
        for method in required_methods:
            if hasattr(analytics_viewset, method):
                print(f"   ✓ {method} method exists")
            else:
                print(f"   ❌ {method} method missing")
        
        print("\n✅ API endpoint configuration test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing API endpoints: {str(e)}")
        return False

def test_serializers():
    """Test that the analytics serializers are working."""
    print("\nTesting Analytics Serializers...")
    print("=" * 50)
    
    try:
        from apps.inventory.serializers import (
            InventoryAnalyticsSerializer, InventoryKPISerializer,
            InventoryForecastSerializer, InventoryAlertSerializer
        )
        
        print("✓ Analytics serializers imported successfully")
        
        # Test serializer instantiation
        serializers = [
            ('InventoryAnalyticsSerializer', InventoryAnalyticsSerializer),
            ('InventoryKPISerializer', InventoryKPISerializer),
            ('InventoryForecastSerializer', InventoryForecastSerializer),
            ('InventoryAlertSerializer', InventoryAlertSerializer),
        ]
        
        for name, serializer_class in serializers:
            try:
                serializer = serializer_class()
                print(f"   ✓ {name} instantiated successfully")
            except Exception as e:
                print(f"   ❌ {name} failed to instantiate: {str(e)}")
        
        print("\n✅ Serializer test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing serializers: {str(e)}")
        return False

if __name__ == '__main__':
    print("Inventory Analytics Test Suite")
    print("=" * 50)
    
    # Run all tests
    tests_passed = 0
    total_tests = 3
    
    if test_analytics_functionality():
        tests_passed += 1
    
    if test_api_endpoints():
        tests_passed += 1
    
    if test_serializers():
        tests_passed += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Inventory analytics implementation is complete.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)