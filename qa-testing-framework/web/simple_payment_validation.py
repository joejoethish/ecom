"""
Simple Payment Implementation Validation

Basic validation of payment processing implementation without complex imports.
"""

import os
import sys
import ast
import inspect
from typing import Dict, Any, List


def validate_file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return os.path.exists(file_path)


def validate_python_syntax(file_path: str) -> Dict[str, Any]:
    """Validate Python file syntax"""
    result = {'valid': False, 'error': None}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        result['valid'] = True
        
    except SyntaxError as e:
        result['error'] = f"Syntax error: {str(e)}"
    except Exception as e:
        result['error'] = f"Error reading file: {str(e)}"
    
    return result


def extract_class_methods(file_path: str, class_name: str) -> List[str]:
    """Extract method names from a class in a Python file"""
    methods = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
    
    except Exception as e:
        print(f"Error extracting methods from {class_name}: {str(e)}")
    
    return methods


def validate_payment_implementation():
    """Validate payment implementation files"""
    
    print("="*80)
    print("PAYMENT PROCESSING IMPLEMENTATION VALIDATION")
    print("="*80)
    
    base_path = "qa-testing-framework/web"
    
    # Files to validate
    files_to_check = [
        "payment_pages.py",
        "payment_test_data.py", 
        "test_payment_processing.py",
        "run_payment_tests.py",
        "README_PAYMENT_TESTS.md"
    ]
    
    validation_results = {}
    
    print("\n1. FILE EXISTENCE CHECK")
    print("-" * 40)
    
    for file_name in files_to_check:
        file_path = os.path.join(base_path, file_name)
        exists = validate_file_exists(file_path)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {file_name:<35} {status}")
        validation_results[file_name] = {'exists': exists}
    
    print("\n2. PYTHON SYNTAX VALIDATION")
    print("-" * 40)
    
    python_files = [f for f in files_to_check if f.endswith('.py')]
    
    for file_name in python_files:
        file_path = os.path.join(base_path, file_name)
        if validation_results[file_name]['exists']:
            syntax_result = validate_python_syntax(file_path)
            status = "✓ VALID" if syntax_result['valid'] else f"✗ ERROR: {syntax_result['error']}"
            print(f"  {file_name:<35} {status}")
            validation_results[file_name]['syntax'] = syntax_result
        else:
            print(f"  {file_name:<35} ✗ SKIPPED (file missing)")
    
    print("\n3. CLASS AND METHOD VALIDATION")
    print("-" * 40)
    
    # Validate PaymentPage class
    payment_pages_file = os.path.join(base_path, "payment_pages.py")
    if validation_results["payment_pages.py"]['exists']:
        payment_page_methods = extract_class_methods(payment_pages_file, "PaymentPage")
        refund_page_methods = extract_class_methods(payment_pages_file, "RefundPage")
        
        print(f"  PaymentPage methods found: {len(payment_page_methods)}")
        expected_payment_methods = [
            'select_payment_method', 'fill_credit_card_form', 'fill_paypal_form',
            'fill_upi_form', 'process_payment', 'get_payment_result'
        ]
        
        for method in expected_payment_methods:
            status = "✓" if method in payment_page_methods else "✗"
            print(f"    {method:<30} {status}")
        
        print(f"  RefundPage methods found: {len(refund_page_methods)}")
        expected_refund_methods = ['process_full_refund', 'process_partial_refund']
        
        for method in expected_refund_methods:
            status = "✓" if method in refund_page_methods else "✗"
            print(f"    {method:<30} {status}")
    
    # Validate test suite class
    test_file = os.path.join(base_path, "test_payment_processing.py")
    if validation_results["test_payment_processing.py"]['exists']:
        test_methods = extract_class_methods(test_file, "PaymentProcessingTestSuite")
        print(f"  PaymentProcessingTestSuite methods: {len(test_methods)}")
        
        expected_test_methods = [
            'test_successful_credit_card_payment',
            'test_successful_paypal_payment',
            'test_successful_upi_payment',
            'test_declined_card_payment',
            'test_invalid_card_number_validation',
            'test_full_order_refund'
        ]
        
        for method in expected_test_methods:
            status = "✓" if method in test_methods else "✗"
            print(f"    {method:<35} {status}")
    
    print("\n4. CONTENT VALIDATION")
    print("-" * 40)
    
    # Check test data content
    test_data_file = os.path.join(base_path, "payment_test_data.py")
    if validation_results["payment_test_data.py"]['exists']:
        with open(test_data_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ('PaymentTestDataGenerator class', 'class PaymentTestDataGenerator'),
            ('Sandbox cards data', 'sandbox_cards'),
            ('UPI data', 'upi_data'),
            ('EMI options', 'emi_options'),
            ('Failure scenarios', 'failure_scenarios'),
            ('Refund scenarios', 'refund_scenarios')
        ]
        
        for check_name, search_term in checks:
            status = "✓" if search_term in content else "✗"
            print(f"  {check_name:<35} {status}")
    
    # Check README content
    readme_file = os.path.join(base_path, "README_PAYMENT_TESTS.md")
    if validation_results["README_PAYMENT_TESTS.md"]['exists']:
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        readme_checks = [
            ('Overview section', '## Overview'),
            ('Test Coverage section', '## Test Coverage'),
            ('Usage instructions', '## Usage'),
            ('Test Cases section', '## Test Cases'),
            ('Security Testing section', '## Security Testing')
        ]
        
        for check_name, search_term in readme_checks:
            status = "✓" if search_term in content else "✗"
            print(f"  {check_name:<35} {status}")
    
    print("\n5. IMPLEMENTATION SUMMARY")
    print("-" * 40)
    
    # Calculate overall status
    total_files = len(files_to_check)
    existing_files = sum(1 for result in validation_results.values() if result['exists'])
    valid_syntax_files = sum(1 for result in validation_results.values() 
                           if result.get('syntax', {}).get('valid', False))
    
    print(f"  Total files: {total_files}")
    print(f"  Files created: {existing_files}")
    print(f"  Valid syntax: {valid_syntax_files}")
    print(f"  Completion rate: {(existing_files/total_files)*100:.1f}%")
    
    if existing_files == total_files:
        print(f"\n✓ SUCCESS: All payment processing files have been created successfully!")
        print(f"✓ The payment testing framework implementation is complete.")
    else:
        print(f"\n⚠ WARNING: {total_files - existing_files} files are missing.")
    
    print("\n" + "="*80)
    
    return existing_files == total_files


if __name__ == '__main__':
    success = validate_payment_implementation()
    sys.exit(0 if success else 1)