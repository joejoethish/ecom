"""
Product Browsing Tests Runner

Executes product browsing and search functionality tests with proper
configuration, reporting, and error handling.
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from .test_product_browsing import TestProductBrowsing
    from ..core.interfaces import Environment
    from ..core.config import get_config
    from ..core.error_handling import ErrorHandler
    from ..core.models import TestExecution, BrowserInfo, ExecutionStatus
except ImportError:
    # Fallback for direct execution
    from test_product_browsing import TestProductBrowsing
    from core.interfaces import Environment
    from core.config import get_config
    from core.error_handling import ErrorHandler
    from core.models import TestExecution, BrowserInfo, ExecutionStatus


class ProductBrowsingTestRunner:
    """Test runner for product browsing functionality"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.error_handler = ErrorHandler()
        self.results = []
        
        # Create reports directory
        self.reports_dir = Path("reports/product_browsing")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def run_single_test(self, test_method_name: str, browser: str = "chrome") -> dict:
        """Run a single test method"""
        test_class = TestProductBrowsing()
        
        try:
            # Setup test environment
            test_class.setup(browser, self.environment)
            
            # Get the test method
            test_method = getattr(test_class, test_method_name)
            
            # Execute test
            start_time = datetime.now()
            test_method()
            end_time = datetime.now()
            
            # Create test execution record
            execution = TestExecution(
                id=f"exec_{test_method_name}_{int(start_time.timestamp())}",
                test_case_id=test_method_name,
                environment=self.environment,
                status=ExecutionStatus.PASSED,
                start_time=start_time,
                end_time=end_time,
                actual_result="Test completed successfully",
                browser_info=test_class.webdriver_manager.get_browser_info(test_class.driver)
            )
            
            return {
                "test_name": test_method_name,
                "status": "PASSED",
                "duration": execution.duration,
                "browser": browser,
                "execution": execution
            }
            
        except Exception as e:
            end_time = datetime.now()
            
            # Create failed execution record
            execution = TestExecution(
                id=f"exec_{test_method_name}_{int(start_time.timestamp())}",
                test_case_id=test_method_name,
                environment=self.environment,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                actual_result=f"Test failed: {str(e)}"
            )
            
            return {
                "test_name": test_method_name,
                "status": "FAILED",
                "error": str(e),
                "duration": execution.duration,
                "browser": browser,
                "execution": execution
            }
        
        finally:
            # Cleanup is handled in the test class fixture
            pass
    
    def run_all_tests(self, browser: str = "chrome") -> list:
        """Run all product browsing tests"""
        test_methods = [
            "test_homepage_navigation_links",
            "test_product_categories_navigation", 
            "test_product_search_functionality",
            "test_product_filters",
            "test_product_sorting",
            "test_product_detail_page_validation",
            "test_pagination_functionality",
            "test_product_comparison_functionality",
            "test_wishlist_functionality",
            "test_product_discovery_workflow"
        ]
        
        results = []
        
        print(f"Running {len(test_methods)} product browsing tests with {browser} browser...")
        print(f"Environment: {self.environment.value}")
        print("=" * 60)
        
        for i, test_method in enumerate(test_methods, 1):
            print(f"\n[{i}/{len(test_methods)}] Running {test_method}...")
            
            result = self.run_single_test(test_method, browser)
            results.append(result)
            
            # Print result
            status_symbol = "✓" if result["status"] == "PASSED" else "✗"
            duration = result.get("duration", 0)
            print(f"{status_symbol} {test_method} - {result['status']} ({duration:.2f}s)")
            
            if result["status"] == "FAILED":
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.results = results
        return results
    
    def run_specific_tests(self, test_names: list, browser: str = "chrome") -> list:
        """Run specific tests by name"""
        results = []
        
        print(f"Running {len(test_names)} specific tests with {browser} browser...")
        print(f"Environment: {self.environment.value}")
        print("=" * 60)
        
        for i, test_name in enumerate(test_names, 1):
            print(f"\n[{i}/{len(test_names)}] Running {test_name}...")
            
            result = self.run_single_test(test_name, browser)
            results.append(result)
            
            # Print result
            status_symbol = "✓" if result["status"] == "PASSED" else "✗"
            duration = result.get("duration", 0)
            print(f"{status_symbol} {test_name} - {result['status']} ({duration:.2f}s)")
            
            if result["status"] == "FAILED":
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.results = results
        return results
    
    def generate_report(self, results: list = None) -> str:
        """Generate test execution report"""
        if results is None:
            results = self.results
        
        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = len([r for r in results if r["status"] == "PASSED"])
        failed_tests = len([r for r in results if r["status"] == "FAILED"])
        total_duration = sum([r.get("duration", 0) for r in results])
        
        # Create report
        report = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "environment": self.environment.value,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration
            },
            "test_results": results
        }
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"product_browsing_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_file)
    
    def print_summary(self, results: list = None):
        """Print test execution summary"""
        if results is None:
            results = self.results
        
        total_tests = len(results)
        passed_tests = len([r for r in results if r["status"] == "PASSED"])
        failed_tests = len([r for r in results if r["status"] == "FAILED"])
        total_duration = sum([r.get("duration", 0) for r in results])
        
        print("\n" + "=" * 60)
        print("PRODUCT BROWSING TESTS SUMMARY")
        print("=" * 60)
        print(f"Environment: {self.environment.value}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "N/A")
        print(f"Total Duration: {total_duration:.2f} seconds")
        
        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for result in results:
                if result["status"] == "FAILED":
                    print(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)


def main():
    """Main function for command line execution"""
    parser = argparse.ArgumentParser(description="Run Product Browsing Tests")
    parser.add_argument(
        "--browser", 
        choices=["chrome", "firefox", "edge", "safari"],
        default="chrome",
        help="Browser to use for testing (default: chrome)"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to test against (default: development)"
    )
    parser.add_argument(
        "--tests",
        nargs="+",
        help="Specific tests to run (space-separated list)"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    
    args = parser.parse_args()
    
    # Convert environment string to enum
    env_map = {
        "development": Environment.DEVELOPMENT,
        "staging": Environment.STAGING,
        "production": Environment.PRODUCTION
    }
    environment = env_map[args.environment]
    
    # Create test runner
    runner = ProductBrowsingTestRunner(environment)
    
    try:
        # Run tests
        if args.tests:
            results = runner.run_specific_tests(args.tests, args.browser)
        else:
            results = runner.run_all_tests(args.browser)
        
        # Print summary
        runner.print_summary(results)
        
        # Generate report if requested
        if args.report:
            report_file = runner.generate_report(results)
            print(f"\nDetailed report saved to: {report_file}")
        
        # Exit with appropriate code
        failed_count = len([r for r in results if r["status"] == "FAILED"])
        sys.exit(1 if failed_count > 0 else 0)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()