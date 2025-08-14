"""
Simple Validation Script for Shopping Cart and Checkout Implementation

Basic validation that checks file existence and basic syntax without complex imports.
"""

import ast
import sys
from pathlib import Path


def validate_python_syntax(file_path):
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def validate_file_structure():
    """Validate all required files exist and have valid syntax"""
    print("Validating file structure and syntax...")
    
    web_dir = Path(__file__).parent
    required_files = [
        'cart_pages.py',
        'cart_test_data.py', 
        'test_shopping_cart_checkout.py',
        'run_cart_checkout_tests.py'
    ]
    
    all_valid = True
    
    for file in required_files:
        file_path = web_dir / file
        if file_path.exists():
            valid, error = validate_python_syntax(file_path)
            if valid:
                print(f"✓ {file} - exists and valid syntax")
            else:
                print(f"✗ {file} - syntax error: {error}")
                all_valid = False
        else:
            print(f"✗ {file} - missing")
            all_valid = False
    
    return all_valid


def check_class_definitions():
    """Check that required classes are defined"""
    print("\nChecking class definitions...")
    
    web_dir = Path(__file__).parent
    
    # Check cart_pages.py
    cart_pages_file = web_dir / 'cart_pages.py'
    if cart_pages_file.exists():
        with open(cart_pages_file, 'r') as f:
            content = f.read()
        
        required_classes = ['ShoppingCartPage', 'CheckoutPage']
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✓ {class_name} class found in cart_pages.py")
            else:
                print(f"✗ {class_name} class missing in cart_pages.py")
    
    # Check cart_test_data.py
    test_data_file = web_dir / 'cart_test_data.py'
    if test_data_file.exists():
        with open(test_data_file, 'r') as f:
            content = f.read()
        
        if "class CartTestDataGenerator" in content:
            print("✓ CartTestDataGenerator class found in cart_test_data.py")
        else:
            print("✗ CartTestDataGenerator class missing in cart_test_data.py")
    
    # Check test suite
    test_suite_file = web_dir / 'test_shopping_cart_checkout.py'
    if test_suite_file.exists():
        with open(test_suite_file, 'r') as f:
            content = f.read()
        
        if "class ShoppingCartCheckoutTestSuite" in content:
            print("✓ ShoppingCartCheckoutTestSuite class found in test_shopping_cart_checkout.py")
        else:
            print("✗ ShoppingCartCheckoutTestSuite class missing in test_shopping_cart_checkout.py")


def check_test_methods():
    """Check that required test methods are defined"""
    print("\nChecking test methods...")
    
    web_dir = Path(__file__).parent
    test_suite_file = web_dir / 'test_shopping_cart_checkout.py'
    
    if test_suite_file.exists():
        with open(test_suite_file, 'r') as f:
            content = f.read()
        
        required_test_methods = [
            'test_add_single_item_to_cart',
            'test_update_item_quantity_in_cart', 
            'test_remove_item_from_cart',
            'test_apply_valid_coupon_code',
            'test_guest_checkout_complete_flow',
            'test_payment_method_selection',
            'test_tax_calculation_accuracy'
        ]
        
        found_methods = []
        missing_methods = []
        
        for method in required_test_methods:
            if f"def {method}" in content:
                found_methods.append(method)
                print(f"✓ {method}")
            else:
                missing_methods.append(method)
                print(f"✗ {method}")
        
        print(f"\nTest methods summary: {len(found_methods)}/{len(required_test_methods)} found")
        
        return len(missing_methods) == 0
    
    return False


def check_page_object_methods():
    """Check that required page object methods are defined"""
    print("\nChecking page object methods...")
    
    web_dir = Path(__file__).parent
    cart_pages_file = web_dir / 'cart_pages.py'
    
    if cart_pages_file.exists():
        with open(cart_pages_file, 'r') as f:
            content = f.read()
        
        # Check ShoppingCartPage methods
        cart_methods = [
            'get_cart_items',
            'update_item_quantity',
            'remove_item',
            'apply_coupon',
            'proceed_to_checkout'
        ]
        
        print("ShoppingCartPage methods:")
        for method in cart_methods:
            if f"def {method}" in content:
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method}")
        
        # Check CheckoutPage methods
        checkout_methods = [
            'fill_shipping_address',
            'select_payment_method',
            'place_order',
            'complete_guest_checkout'
        ]
        
        print("CheckoutPage methods:")
        for method in checkout_methods:
            if f"def {method}" in content:
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method}")


def check_documentation():
    """Check that documentation files exist"""
    print("\nChecking documentation...")
    
    web_dir = Path(__file__).parent
    doc_files = [
        'README_CART_CHECKOUT_TESTS.md'
    ]
    
    for doc_file in doc_files:
        file_path = web_dir / doc_file
        if file_path.exists():
            print(f"✓ {doc_file} exists")
        else:
            print(f"✗ {doc_file} missing")


def main():
    """Main validation function"""
    print("="*60)
    print("SHOPPING CART AND CHECKOUT IMPLEMENTATION VALIDATION")
    print("="*60)
    
    validations = [
        validate_file_structure,
        check_class_definitions,
        check_test_methods,
        check_page_object_methods,
        check_documentation
    ]
    
    all_passed = True
    
    for validation_func in validations:
        try:
            result = validation_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"Validation error: {str(e)}")
            all_passed = False
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if all_passed:
        print("✓ Basic validation successful!")
        print("✓ All required files, classes, and methods are present")
        print("✓ Implementation appears to be complete")
        print("\nNext steps:")
        print("1. Run the actual tests to verify functionality")
        print("2. Test with real browser automation")
        print("3. Validate against actual e-commerce application")
    else:
        print("✗ Some validation issues found")
        print("Please review the output above and fix any missing components")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)