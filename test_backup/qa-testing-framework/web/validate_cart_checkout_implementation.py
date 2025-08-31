"""
Validation Script for Shopping Cart and Checkout Implementation

Validates that all required components are properly implemented
and can be imported without errors.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add qa-testing-framework to path
qa_framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(qa_framework_root))


def validate_imports():
    """Validate all imports work correctly"""
    print("Validating imports...")
    
    try:
        # Test core imports
        from qa_testing_framework.core.interfaces import Environment, UserRole, TestModule, Priority, ExecutionStatus, Severity
        from qa_testing_framework.core.models import TestCase, TestStep, TestExecution, Defect, BrowserInfo, Address, PaymentMethod
        from qa_testing_framework.core.data_manager import TestDataManager
        from qa_testing_framework.core.error_handling import ErrorHandler
        from qa_testing_framework.core.config import get_config
        print("✓ Core module imports successful")
        
        # Test web module imports
        from qa_testing_framework.web.webdriver_manager import WebDriverManager
        from qa_testing_framework.web.page_objects import BasePage, BaseFormPage
        print("✓ Web base module imports successful")
        
        # Test cart and checkout specific imports
        from qa_testing_framework.web.cart_pages import ShoppingCartPage, CheckoutPage
        from qa_testing_framework.web.cart_test_data import CartTestDataGenerator, cart_test_data
        from qa_testing_framework.web.test_shopping_cart_checkout import ShoppingCartCheckoutTestSuite
        print("✓ Cart and checkout module imports successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Unexpected error during imports: {str(e)}")
        traceback.print_exc()
        return False


def validate_page_objects():
    """Validate page object implementations"""
    print("\nValidating page object implementations...")
    
    try:
        from qa_testing_framework.web.cart_pages import ShoppingCartPage, CheckoutPage
        from qa_testing_framework.web.webdriver_manager import WebDriverManager
        
        # Test page object instantiation (without actual driver)
        webdriver_manager = WebDriverManager()
        base_url = "http://localhost:3000"
        
        # Mock driver for testing
        class MockDriver:
            def __init__(self):
                self.current_url = base_url
                self.title = "Test Page"
            
            def get(self, url):
                pass
            
            def find_element(self, by, value):
                pass
            
            def find_elements(self, by, value):
                return []
        
        mock_driver = MockDriver()
        
        # Test ShoppingCartPage
        cart_page = ShoppingCartPage(mock_driver, webdriver_manager, base_url)
        assert hasattr(cart_page, 'get_cart_items'), "ShoppingCartPage missing get_cart_items method"
        assert hasattr(cart_page, 'apply_coupon'), "ShoppingCartPage missing apply_coupon method"
        assert hasattr(cart_page, 'proceed_to_checkout'), "ShoppingCartPage missing proceed_to_checkout method"
        print("✓ ShoppingCartPage validation successful")
        
        # Test CheckoutPage
        checkout_page = CheckoutPage(mock_driver, webdriver_manager, base_url)
        assert hasattr(checkout_page, 'fill_shipping_address'), "CheckoutPage missing fill_shipping_address method"
        assert hasattr(checkout_page, 'select_payment_method'), "CheckoutPage missing select_payment_method method"
        assert hasattr(checkout_page, 'place_order'), "CheckoutPage missing place_order method"
        print("✓ CheckoutPage validation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Page object validation error: {str(e)}")
        traceback.print_exc()
        return False


def validate_test_data():
    """Validate test data generation"""
    print("\nValidating test data generation...")
    
    try:
        from qa_testing_framework.web.cart_test_data import CartTestDataGenerator, cart_test_data
        
        # Test data generator instantiation
        generator = CartTestDataGenerator()
        
        # Test product data
        product = generator.get_test_product()
        assert 'id' in product, "Product data missing id field"
        assert 'name' in product, "Product data missing name field"
        assert 'price' in product, "Product data missing price field"
        print("✓ Product test data generation successful")
        
        # Test address data
        address = generator.get_test_address()
        assert 'street' in address, "Address data missing street field"
        assert 'city' in address, "Address data missing city field"
        assert 'postal_code' in address, "Address data missing postal_code field"
        print("✓ Address test data generation successful")
        
        # Test payment data
        payment = generator.get_test_payment_method()
        assert 'type' in payment, "Payment data missing type field"
        print("✓ Payment test data generation successful")
        
        # Test coupon data
        coupon = generator.get_test_coupon()
        assert 'code' in coupon, "Coupon data missing code field"
        assert 'valid' in coupon, "Coupon data missing valid field"
        print("✓ Coupon test data generation successful")
        
        # Test scenario data
        scenario = generator.create_cart_scenario_data("single_item")
        assert 'products' in scenario, "Scenario data missing products"
        assert 'address' in scenario, "Scenario data missing address"
        assert 'payment' in scenario, "Scenario data missing payment"
        print("✓ Scenario test data generation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Test data validation error: {str(e)}")
        traceback.print_exc()
        return False


def validate_test_suite():
    """Validate test suite structure"""
    print("\nValidating test suite structure...")
    
    try:
        from qa_testing_framework.web.test_shopping_cart_checkout import ShoppingCartCheckoutTestSuite
        import unittest
        
        # Get all test methods
        test_methods = [method for method in dir(ShoppingCartCheckoutTestSuite) 
                       if method.startswith('test_')]
        
        print(f"Found {len(test_methods)} test methods:")
        
        # Validate cart tests
        cart_tests = [method for method in test_methods if 'cart' in method.lower()]
        print(f"  - Cart tests: {len(cart_tests)}")
        for test in cart_tests:
            print(f"    • {test}")
        
        # Validate checkout tests
        checkout_tests = [method for method in test_methods if 'checkout' in method.lower()]
        print(f"  - Checkout tests: {len(checkout_tests)}")
        for test in checkout_tests:
            print(f"    • {test}")
        
        # Validate required test methods exist
        required_tests = [
            'test_add_single_item_to_cart',
            'test_update_item_quantity_in_cart',
            'test_remove_item_from_cart',
            'test_apply_valid_coupon_code',
            'test_guest_checkout_complete_flow',
            'test_payment_method_selection',
            'test_tax_calculation_accuracy'
        ]
        
        missing_tests = [test for test in required_tests if test not in test_methods]
        if missing_tests:
            print(f"✗ Missing required tests: {missing_tests}")
            return False
        
        print("✓ All required test methods present")
        
        # Validate test suite can be loaded
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(ShoppingCartCheckoutTestSuite)
        test_count = suite.countTestCases()
        print(f"✓ Test suite loaded successfully with {test_count} test cases")
        
        return True
        
    except Exception as e:
        print(f"✗ Test suite validation error: {str(e)}")
        traceback.print_exc()
        return False


def validate_file_structure():
    """Validate all required files exist"""
    print("\nValidating file structure...")
    
    web_dir = Path(__file__).parent
    required_files = [
        'cart_pages.py',
        'cart_test_data.py',
        'test_shopping_cart_checkout.py',
        'run_cart_checkout_tests.py',
        'README_CART_CHECKOUT_TESTS.md'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = web_dir / file
        if file_path.exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True


def main():
    """Main validation function"""
    print("="*60)
    print("SHOPPING CART AND CHECKOUT IMPLEMENTATION VALIDATION")
    print("="*60)
    
    validations = [
        ("File Structure", validate_file_structure),
        ("Imports", validate_imports),
        ("Page Objects", validate_page_objects),
        ("Test Data", validate_test_data),
        ("Test Suite", validate_test_suite)
    ]
    
    results = {}
    
    for name, validation_func in validations:
        try:
            results[name] = validation_func()
        except Exception as e:
            print(f"✗ {name} validation failed with exception: {str(e)}")
            results[name] = False
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{name:<20}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} validations passed")
    
    if passed == total:
        print("✓ All validations successful - Implementation is ready for testing!")
        return True
    else:
        print("✗ Some validations failed - Please fix issues before proceeding")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)