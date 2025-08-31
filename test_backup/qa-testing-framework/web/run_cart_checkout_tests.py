"""
Test Runner for Shopping Cart and Checkout Tests

Executes the shopping cart and checkout test suite with proper reporting
and error handling.
"""

import sys
import os
import unittest
import time
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_shopping_cart_checkout import ShoppingCartCheckoutTestSuite
from ..core.interfaces import Environment
from ..core.config import get_config


class CartCheckoutTestRunner:
    """Test runner for shopping cart and checkout tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.start_time = None
        self.end_time = None
        self.results = None
    
    def run_all_tests(self, verbosity: int = 2) -> bool:
        """Run all shopping cart and checkout tests"""
        print(f"\n{'='*80}")
        print(f"SHOPPING CART AND CHECKOUT TEST EXECUTION")
        print(f"Environment: {self.environment.value}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        self.start_time = time.time()
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(ShoppingCartCheckoutTestSuite)
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            stream=sys.stdout,
            buffer=True
        )
        
        self.results = runner.run(suite)
        self.end_time = time.time()
        
        # Print summary
        self._print_test_summary()
        
        return self.results.wasSuccessful()
    
    def run_specific_tests(self, test_methods: list, verbosity: int = 2) -> bool:
        """Run specific test methods"""
        print(f"\n{'='*80}")
        print(f"RUNNING SPECIFIC CART AND CHECKOUT TESTS")
        print(f"Tests: {', '.join(test_methods)}")
        print(f"Environment: {self.environment.value}")
        print(f"{'='*80}\n")
        
        self.start_time = time.time()
        
        # Create test suite with specific methods
        suite = unittest.TestSuite()
        for test_method in test_methods:
            suite.addTest(ShoppingCartCheckoutTestSuite(test_method))
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            stream=sys.stdout,
            buffer=True
        )
        
        self.results = runner.run(suite)
        self.end_time = time.time()
        
        # Print summary
        self._print_test_summary()
        
        return self.results.wasSuccessful()
    
    def _print_test_summary(self):
        """Print test execution summary"""
        duration = self.end_time - self.start_time
        
        print(f"\n{'='*80}")
        print(f"TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests Run: {self.results.testsRun}")
        print(f"Successful: {self.results.testsRun - len(self.results.failures) - len(self.results.errors)}")
        print(f"Failures: {len(self.results.failures)}")
        print(f"Errors: {len(self.results.errors)}")
        print(f"Execution Time: {duration:.2f} seconds")
        print(f"Success Rate: {((self.results.testsRun - len(self.results.failures) - len(self.results.errors)) / self.results.testsRun * 100):.1f}%")
        
        if self.results.failures:
            print(f"\nFAILURES ({len(self.results.failures)}):")
            for i, (test, traceback) in enumerate(self.results.failures, 1):
                print(f"{i}. {test}")
                print(f"   {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See full traceback above'}")
        
        if self.results.errors:
            print(f"\nERRORS ({len(self.results.errors)}):")
            for i, (test, traceback) in enumerate(self.results.errors, 1):
                print(f"{i}. {test}")
                print(f"   {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See full traceback above'}")
        
        print(f"\n{'='*80}")
        
        # Print defects if any were logged
        if hasattr(ShoppingCartCheckoutTestSuite, 'defects') and ShoppingCartCheckoutTestSuite.defects:
            print(f"DEFECTS LOGGED: {len(ShoppingCartCheckoutTestSuite.defects)}")
            for i, defect in enumerate(ShoppingCartCheckoutTestSuite.defects, 1):
                print(f"{i}. [{defect.severity.value.upper()}] {defect.title}")
                print(f"   Test Case: {defect.test_case_id}")
                print(f"   Description: {defect.description}")
            print(f"{'='*80}")


def main():
    """Main function to run cart and checkout tests"""
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run Shopping Cart and Checkout Tests')
    parser.add_argument('--env', choices=['development', 'staging', 'production'], 
                       default='development', help='Test environment')
    parser.add_argument('--tests', nargs='*', help='Specific test methods to run')
    parser.add_argument('--verbose', '-v', action='count', default=1, 
                       help='Increase verbosity')
    
    args = parser.parse_args()
    
    # Set environment
    env_map = {
        'development': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'production': Environment.PRODUCTION
    }
    environment = env_map[args.env]
    
    # Create test runner
    runner = CartCheckoutTestRunner(environment)
    
    try:
        # Run tests
        if args.tests:
            success = runner.run_specific_tests(args.tests, args.verbose)
        else:
            success = runner.run_all_tests(args.verbose)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest execution failed with error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()