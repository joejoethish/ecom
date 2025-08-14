"""
Product Browsing Implementation Validation Script

Validates that the product browsing test implementation is working correctly
by running basic functionality checks and test structure validation.
"""

import sys
import os
from pathlib import Path
import importlib.util

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

def validate_imports():
    """Validate that all required modules can be imported"""
    print("Validating imports...")
    
    try:
        # Test core imports
        from core.interfaces import Environment, TestModule, Priority, UserRole
        from core.models import TestCase, TestStep, TestProduct
        from core.data_manager import TestDataManager
        print("✓ Core modules imported successfully")
        
        # Test web module imports
        from web.product_pages import (
            ProductCatalogPage, ProductSearchPage, ProductDetailPage,
            ProductComparisonPage, WishlistPage
        )
        print("✓ Product page objects imported successfully")
        
        from web.product_test_data import ProductTestDataManager
        print("✓ Product test data manager imported successfully")
        
        from web.webdriver_manager import WebDriverManager
        print("✓ WebDriver manager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def validate_page_objects():
    """Validate page object structure and methods"""
    print("\nValidating page object structure...")
    
    try:
        from web.product_pages import ProductCatalogPage
        from web.webdriver_manager import WebDriverManager
        from core.interfaces import Environment
        
        # Create a mock driver for validation (won't actually start browser)
        webdriver_manager = WebDriverManager(Environment.DEVELOPMENT)
        
        # Validate ProductCatalogPage structure
        page = ProductCatalogPage(None, webdriver_manager)  # None driver for structure check
        
        # Check required properties
        required_properties = ['page_url', 'page_title', 'unique_element']
        for prop in required_properties:
            if hasattr(page, prop):
                print(f"✓ ProductCatalogPage has {prop} property")
            else:
                print(f"✗ ProductCatalogPage missing {prop} property")
                return False
        
        # Check key methods
        required_methods = [
            'get_product_cards', 'navigate_to_category', 'apply_price_filter',
            'sort_products', 'add_product_to_cart'
        ]
        for method in required_methods:
            if hasattr(page, method) and callable(getattr(page, method)):
                print(f"✓ ProductCatalogPage has {method} method")
            else:
                print(f"✗ ProductCatalogPage missing {method} method")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Page object validation error: {e}")
        return False

def validate_test_data_manager():
    """Validate test data manager functionality"""
    print("\nValidating test data manager...")
    
    try:
        from web.product_test_data import ProductTestDataManager
        from core.data_manager import TestDataManager
        from core.interfaces import Environment
        
        # Create test data manager
        base_manager = TestDataManager()
        product_manager = ProductTestDataManager(base_manager)
        
        # Test category creation
        categories = product_manager.create_test_categories()
        if len(categories) > 0:
            print(f"✓ Created {len(categories)} test categories")
        else:
            print("✗ No test categories created")
            return False
        
        # Test product creation
        products = product_manager.create_test_products(5)  # Create 5 test products
        if len(products) == 5:
            print(f"✓ Created {len(products)} test products")
        else:
            print(f"✗ Expected 5 products, got {len(products)}")
            return False
        
        # Test search scenarios
        search_scenarios = product_manager.create_search_test_scenarios()
        if len(search_scenarios) > 0:
            print(f"✓ Created {len(search_scenarios)} search test scenarios")
        else:
            print("✗ No search test scenarios created")
            return False
        
        # Test filter scenarios
        filter_scenarios = product_manager.create_filter_test_scenarios()
        if len(filter_scenarios) > 0:
            print(f"✓ Created {len(filter_scenarios)} filter test scenarios")
        else:
            print("✗ No filter test scenarios created")
            return False
        
        # Test cleanup
        product_manager.cleanup_test_data()
        print("✓ Test data cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Test data manager validation error: {e}")
        return False

def validate_test_cases():
    """Validate test case structure"""
    print("\nValidating test case structure...")
    
    try:
        from web.test_product_browsing import TestProductBrowsing
        
        # Get test class
        test_class = TestProductBrowsing()
        
        # Check for required test methods
        required_test_methods = [
            'test_homepage_navigation_links',
            'test_product_categories_navigation',
            'test_product_search_functionality',
            'test_product_filters',
            'test_product_sorting',
            'test_product_detail_page_validation',
            'test_pagination_functionality',
            'test_product_comparison_functionality',
            'test_wishlist_functionality',
            'test_product_discovery_workflow'
        ]
        
        for method_name in required_test_methods:
            if hasattr(test_class, method_name) and callable(getattr(test_class, method_name)):
                print(f"✓ Test method {method_name} exists")
            else:
                print(f"✗ Test method {method_name} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Test case validation error: {e}")
        return False

def validate_test_runner():
    """Validate test runner functionality"""
    print("\nValidating test runner...")
    
    try:
        from web.run_product_browsing_tests import ProductBrowsingTestRunner
        from core.interfaces import Environment
        
        # Create test runner
        runner = ProductBrowsingTestRunner(Environment.DEVELOPMENT)
        
        # Check required methods
        required_methods = [
            'run_single_test', 'run_all_tests', 'run_specific_tests',
            'generate_report', 'print_summary'
        ]
        
        for method_name in required_methods:
            if hasattr(runner, method_name) and callable(getattr(runner, method_name)):
                print(f"✓ Test runner has {method_name} method")
            else:
                print(f"✗ Test runner missing {method_name} method")
                return False
        
        # Check reports directory creation
        if runner.reports_dir.exists():
            print("✓ Reports directory created successfully")
        else:
            print("✗ Reports directory not created")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Test runner validation error: {e}")
        return False

def validate_file_structure():
    """Validate that all required files exist"""
    print("\nValidating file structure...")
    
    web_dir = Path(__file__).parent
    required_files = [
        'product_pages.py',
        'test_product_browsing.py',
        'run_product_browsing_tests.py',
        'product_test_data.py',
        'README_PRODUCT_BROWSING_TESTS.md'
    ]
    
    all_files_exist = True
    for file_name in required_files:
        file_path = web_dir / file_name
        if file_path.exists():
            print(f"✓ {file_name} exists")
        else:
            print(f"✗ {file_name} missing")
            all_files_exist = False
    
    return all_files_exist

def validate_test_case_ids():
    """Validate that test case IDs are properly defined"""
    print("\nValidating test case IDs...")
    
    try:
        # Read the test file and check for test case IDs
        test_file = Path(__file__).parent / 'test_product_browsing.py'
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        expected_test_ids = [
            'TC_PROD_001', 'TC_PROD_002', 'TC_PROD_003', 'TC_PROD_004',
            'TC_PROD_005', 'TC_PROD_006', 'TC_PROD_007', 'TC_PROD_008',
            'TC_PROD_009', 'TC_PROD_010'
        ]
        
        for test_id in expected_test_ids:
            if test_id in content:
                print(f"✓ Test case {test_id} found")
            else:
                print(f"✗ Test case {test_id} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Test case ID validation error: {e}")
        return False

def main():
    """Main validation function"""
    print("=" * 60)
    print("PRODUCT BROWSING TESTS IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    validation_functions = [
        validate_file_structure,
        validate_imports,
        validate_page_objects,
        validate_test_data_manager,
        validate_test_cases,
        validate_test_runner,
        validate_test_case_ids
    ]
    
    results = []
    for validation_func in validation_functions:
        try:
            result = validation_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Validation function {validation_func.__name__} failed: {e}")
            results.append(False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total validations: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n✓ All validations passed! Implementation is ready for testing.")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)