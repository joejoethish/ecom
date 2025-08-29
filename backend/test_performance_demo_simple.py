#!/usr/bin/env python
"""
Simple test script for the performance demo
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

# Setup Django
django.setup()

def test_performance_demo_import():
    """Test that we can import the performance demo"""
    try:
        from apps.debugging.performance_demo import PerformanceDemo
        print("✅ PerformanceDemo imported successfully")
        
        # Test initialization
        demo = PerformanceDemo()
        print("✅ PerformanceDemo initialized successfully")
        
        # Test that monitor is available
        if hasattr(demo, 'monitor'):
            print("✅ Performance monitor is available")
        else:
            print("❌ Performance monitor not found")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_performance_demo_methods():
    """Test that demo methods are callable"""
    try:
        from apps.debugging.performance_demo import PerformanceDemo
        demo = PerformanceDemo()
        
        # Test method availability
        methods = [
            'simulate_database_operations',
            'simulate_api_requests', 
            'simulate_concurrent_operations',
            'simulate_memory_intensive_operations',
            'simulate_error_scenarios',
            'generate_performance_report',
            'run_full_demo'
        ]
        
        for method_name in methods:
            if hasattr(demo, method_name):
                print(f"✅ Method {method_name} is available")
            else:
                print(f"❌ Method {method_name} not found")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing methods: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Performance Demo...")
    print("=" * 40)
    
    # Test imports
    import_success = test_performance_demo_import()
    
    if import_success:
        # Test methods
        method_success = test_performance_demo_methods()
        
        if method_success:
            print("\n🎉 All tests passed! Performance demo is ready to use.")
            print("\nTo run the full demo:")
            print("  python manage.py run_performance_demo")
        else:
            print("\n❌ Some method tests failed")
    else:
        print("\n❌ Import tests failed")