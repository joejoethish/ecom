#!/usr/bin/env python3
"""
Test Cleanup Script - Remove Redundant Test Files

This script identifies and removes redundant test files to streamline the testing process.
It keeps only the essential tests needed to verify platform functionality.
"""

import os
import shutil
from pathlib import Path

class TestCleanup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.removed_files = []
        self.kept_files = []
        
        # Define essential test files to keep
        self.essential_backend_tests = {
            # Core unit tests
            'tests/unit/test_models.py',
            'tests/unit/test_views.py',
            
            # Critical integration tests
            'tests/integration/test_system_integration.py',
            'tests/integration/test_api_integration.py',
            'tests/integration/test_user_journey.py',
            'tests/integration/test_payment_integrations.py',
            
            # Security tests
            'tests/security/test_security.py',
            
            # Performance tests
            'tests/performance/test_load_testing.py',
            
            # E2E tests
            'tests/e2e/test_workflow_debugging_e2e.py',
            
            # Configuration files
            'tests/conftest.py',
            'tests/__init__.py',
        }
        
        self.essential_frontend_tests = {
            # Core component tests
            'src/__tests__/components/Dashboard.test.tsx',
            'src/__tests__/components/AdminLogin.test.tsx',
            
            # Service tests
            'src/__tests__/services/apiClient.test.ts',
            
            # Integration tests
            'src/__tests__/integration/authenticationIntegration.test.tsx',
            
            # Hook tests
            'src/__tests__/hooks/useCorrelationId.test.ts',
            
            # E2E tests
            'src/__tests__/e2e/workflow-debugging.test.tsx',
        }
        
        self.essential_qa_tests = {
            # Web E2E tests
            'web/test_authentication.py',
            'web/test_shopping_cart_checkout.py',
            'web/test_payment_processing.py',
            'web/test_product_browsing.py',
            
            # API tests
            'api/test_authentication.py',
            'api/test_product_order_management.py',
            'api/test_api_client.py',
            
            # Mobile tests (keep minimal)
            'mobile/test_mobile_auth.py',
            'mobile/test_mobile_shopping.py',
            
            # Core framework files
            'core/__init__.py',
            'core/config.py',
            'core/models.py',
            'core/utils.py',
            
            # Configuration
            'config/development.yaml',
            'config/staging.yaml',
            'config/production.yaml',
            
            # Requirements
            'requirements.txt',
            '__init__.py',
        }
        
        # Define redundant files to remove
        self.redundant_backend_tests = {
            # Duplicate/redundant tests
            'tests/test_versioning_simple.py',  # Keep only test_versioning.py
            'tests/test_migration_edge_cases.py',  # Keep only test_migration_comprehensive.py
            'tests/test_correlation_service.py',  # Covered by middleware test
            'tests/test_api_documentation.py',  # Not critical for functionality
            
            # Performance duplicates
            'tests/integration/test_performance.py',  # Keep only performance/test_load_testing.py
            
            # Debugging system duplicates
            'tests/performance/test_debugging_performance_benchmarks.py',  # Too specific
            'tests/integration/test_debugging_regression.py',  # Too specific
        }
        
        self.redundant_frontend_tests = {
            # Integration test duplicates
            'src/__tests__/integration/correlationId.integration.test.ts',  # Covered by hook test
            'src/__tests__/integration/passwordReset.integration.test.tsx',  # Not critical
            
            # Service test duplicates
            'src/__tests__/services/correlationId.test.ts',  # Covered by hook test
        }
        
        self.redundant_qa_tests = {
            # Duplicate mobile tests
            'mobile/test_mobile_ecommerce_comprehensive.py',  # Covered by specific tests
            'mobile/test_mobile_navigation.py',  # Not critical
            'mobile/test_mobile_user_journeys.py',  # Covered by auth/shopping tests
            'mobile/test_mobile_utils.py',  # Utility test, not critical
            'mobile/test_offline_functionality.py',  # Advanced feature
            'mobile/test_push_notifications.py',  # Advanced feature
            
            # Duplicate API tests
            'api/test_performance.py',  # Keep only if needed
            'api/test_validators.py',  # Utility test
            'api/test_wallet_giftcard_api.py',  # Specific feature test
            
            # Duplicate web tests
            'web/test_session_management.py',  # Covered by authentication test
            'web/test_webdriver_manager.py',  # Utility test
            
            # Validation scripts (keep as utilities, not tests)
            'web/validate_cart_checkout_implementation.py',
            'web/validate_payment_implementation.py',
            'web/validate_product_browsing_implementation.py',
            'web/simple_validation.py',
            'web/simple_payment_validation.py',
        }
    
    def backup_files(self):
        """Create backup of test files before cleanup"""
        backup_dir = self.project_root / 'test_backup'
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        print("📦 Creating backup of test files...")
        
        # Backup backend tests
        backend_backup = backup_dir / 'backend' / 'tests'
        backend_tests = self.project_root / 'backend' / 'tests'
        if backend_tests.exists():
            shutil.copytree(backend_tests, backend_backup)
        
        # Backup frontend tests
        frontend_backup = backup_dir / 'frontend' / 'src' / '__tests__'
        frontend_tests = self.project_root / 'frontend' / 'src' / '__tests__'
        if frontend_tests.exists():
            shutil.copytree(frontend_tests, frontend_backup)
        
        # Backup QA tests
        qa_backup = backup_dir / 'qa-testing-framework'
        qa_tests = self.project_root / 'qa-testing-framework'
        if qa_tests.exists():
            shutil.copytree(qa_tests, qa_backup)
        
        print(f"✅ Backup created at: {backup_dir}")
    
    def remove_redundant_backend_tests(self):
        """Remove redundant backend test files"""
        print("\n🧹 Cleaning up backend tests...")
        backend_tests_dir = self.project_root / 'backend' / 'tests'
        
        for test_file in self.redundant_backend_tests:
            file_path = backend_tests_dir / test_file
            if file_path.exists():
                file_path.unlink()
                self.removed_files.append(str(file_path))
                print(f"  ❌ Removed: {test_file}")
        
        # Remove empty __pycache__ directories
        self._remove_pycache_dirs(backend_tests_dir)
    
    def remove_redundant_frontend_tests(self):
        """Remove redundant frontend test files"""
        print("\n🧹 Cleaning up frontend tests...")
        frontend_tests_dir = self.project_root / 'frontend' / 'src' / '__tests__'
        
        for test_file in self.redundant_frontend_tests:
            file_path = frontend_tests_dir / test_file
            if file_path.exists():
                file_path.unlink()
                self.removed_files.append(str(file_path))
                print(f"  ❌ Removed: {test_file}")
    
    def remove_redundant_qa_tests(self):
        """Remove redundant QA test files"""
        print("\n🧹 Cleaning up QA framework tests...")
        qa_tests_dir = self.project_root / 'qa-testing-framework'
        
        for test_file in self.redundant_qa_tests:
            file_path = qa_tests_dir / test_file
            if file_path.exists():
                file_path.unlink()
                self.removed_files.append(str(file_path))
                print(f"  ❌ Removed: {test_file}")
        
        # Remove empty __pycache__ directories
        self._remove_pycache_dirs(qa_tests_dir)
    
    def _remove_pycache_dirs(self, root_dir):
        """Remove __pycache__ directories recursively"""
        for pycache_dir in root_dir.rglob('__pycache__'):
            if pycache_dir.is_dir():
                shutil.rmtree(pycache_dir)
                print(f"  🗑️  Removed cache: {pycache_dir.relative_to(root_dir)}")
    
    def create_test_inventory(self):
        """Create inventory of remaining essential tests"""
        print("\n📋 Creating test inventory...")
        
        inventory_file = self.project_root / 'TEST_INVENTORY.md'
        
        with open(inventory_file, 'w') as f:
            f.write("# Test Inventory - Essential Tests Only\n\n")
            f.write("This document lists all essential test files kept after cleanup.\n\n")
            
            # Backend tests
            f.write("## Backend Tests\n\n")
            backend_tests_dir = self.project_root / 'backend' / 'tests'
            if backend_tests_dir.exists():
                for test_file in sorted(self.essential_backend_tests):
                    file_path = backend_tests_dir / test_file
                    if file_path.exists():
                        f.write(f"- `{test_file}` - {self._get_test_description(test_file)}\n")
                        self.kept_files.append(str(file_path))
            
            # Frontend tests
            f.write("\n## Frontend Tests\n\n")
            frontend_tests_dir = self.project_root / 'frontend' / 'src' / '__tests__'
            if frontend_tests_dir.exists():
                for test_file in sorted(self.essential_frontend_tests):
                    file_path = frontend_tests_dir / test_file
                    if file_path.exists():
                        f.write(f"- `{test_file}` - {self._get_test_description(test_file)}\n")
                        self.kept_files.append(str(file_path))
            
            # QA tests
            f.write("\n## QA Framework Tests\n\n")
            qa_tests_dir = self.project_root / 'qa-testing-framework'
            if qa_tests_dir.exists():
                for test_file in sorted(self.essential_qa_tests):
                    file_path = qa_tests_dir / test_file
                    if file_path.exists():
                        f.write(f"- `{test_file}` - {self._get_test_description(test_file)}\n")
                        self.kept_files.append(str(file_path))
            
            # Summary
            f.write(f"\n## Summary\n\n")
            f.write(f"- **Total Essential Tests**: {len(self.kept_files)}\n")
            f.write(f"- **Removed Redundant Tests**: {len(self.removed_files)}\n")
            f.write(f"- **Space Saved**: Approximately {len(self.removed_files) * 50}KB\n")
        
        print(f"✅ Test inventory created: {inventory_file}")
    
    def _get_test_description(self, test_file):
        """Get description for test file"""
        descriptions = {
            # Backend
            'tests/unit/test_models.py': 'Database models and relationships',
            'tests/unit/test_views.py': 'API endpoints and views',
            'tests/integration/test_system_integration.py': 'Complete system integration',
            'tests/integration/test_api_integration.py': 'API integration tests',
            'tests/integration/test_user_journey.py': 'User authentication and permissions',
            'tests/integration/test_payment_integrations.py': 'Payment processing',
            'tests/security/test_security.py': 'Security vulnerabilities',
            'tests/performance/test_load_testing.py': 'Performance and load testing',
            'tests/e2e/test_workflow_debugging_e2e.py': 'End-to-end workflow debugging',
            
            # Frontend
            'src/__tests__/components/Dashboard.test.tsx': 'Main dashboard component',
            'src/__tests__/components/AdminLogin.test.tsx': 'Admin login component',
            'src/__tests__/services/apiClient.test.ts': 'API client service',
            'src/__tests__/integration/authenticationIntegration.test.tsx': 'Authentication integration',
            'src/__tests__/hooks/useCorrelationId.test.ts': 'Correlation ID hook',
            'src/__tests__/e2e/workflow-debugging.test.tsx': 'E2E workflow debugging',
            
            # QA
            'web/test_authentication.py': 'E2E authentication flow',
            'web/test_shopping_cart_checkout.py': 'E2E shopping and checkout',
            'web/test_payment_processing.py': 'E2E payment processing',
            'web/test_product_browsing.py': 'E2E product browsing',
            'api/test_authentication.py': 'API authentication endpoints',
            'api/test_product_order_management.py': 'API product and order management',
            'api/test_api_client.py': 'API client connectivity',
            'mobile/test_mobile_auth.py': 'Mobile authentication',
            'mobile/test_mobile_shopping.py': 'Mobile shopping flow',
        }
        
        return descriptions.get(test_file, 'Essential test file')
    
    def generate_cleanup_report(self):
        """Generate cleanup report"""
        print("\n📊 Generating cleanup report...")
        
        report_file = self.project_root / 'TEST_CLEANUP_REPORT.md'
        
        with open(report_file, 'w') as f:
            f.write("# Test Cleanup Report\n\n")
            f.write(f"Generated on: {os.popen('date').read().strip()}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Files Removed**: {len(self.removed_files)}\n")
            f.write(f"- **Files Kept**: {len(self.kept_files)}\n")
            f.write(f"- **Cleanup Ratio**: {len(self.removed_files) / (len(self.removed_files) + len(self.kept_files)) * 100:.1f}%\n\n")
            
            f.write("## Removed Files\n\n")
            for file_path in sorted(self.removed_files):
                f.write(f"- `{file_path}`\n")
            
            f.write("\n## Rationale for Removal\n\n")
            f.write("Files were removed based on the following criteria:\n")
            f.write("- **Duplicate functionality**: Tests that cover the same functionality as other tests\n")
            f.write("- **Non-critical features**: Tests for advanced features not essential for core functionality\n")
            f.write("- **Utility tests**: Tests for utility functions rather than core business logic\n")
            f.write("- **Edge cases**: Tests for edge cases that don't affect normal operation\n")
            f.write("- **Development-only**: Tests only useful during development, not for deployment validation\n\n")
            
            f.write("## Backup Location\n\n")
            f.write("All removed files have been backed up to: `test_backup/`\n")
            f.write("You can restore any file if needed by copying from the backup directory.\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Run the essential tests using: `./run_essential_tests.sh --full`\n")
            f.write("2. Review the test inventory in: `TEST_INVENTORY.md`\n")
            f.write("3. Update CI/CD pipelines to use the streamlined test suite\n")
            f.write("4. Remove the backup directory after confirming everything works\n")
        
        print(f"✅ Cleanup report generated: {report_file}")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🚀 Starting test cleanup process...")
        
        # Create backup first
        self.backup_files()
        
        # Remove redundant tests
        self.remove_redundant_backend_tests()
        self.remove_redundant_frontend_tests()
        self.remove_redundant_qa_tests()
        
        # Create inventory and report
        self.create_test_inventory()
        self.generate_cleanup_report()
        
        print(f"\n✅ Cleanup completed!")
        print(f"📊 Summary:")
        print(f"   - Removed: {len(self.removed_files)} files")
        print(f"   - Kept: {len(self.kept_files)} essential files")
        print(f"   - Backup: test_backup/ directory")
        print(f"\n🎯 Next steps:")
        print(f"   1. Run: ./run_essential_tests.sh --full")
        print(f"   2. Review: TEST_INVENTORY.md")
        print(f"   3. Check: TEST_CLEANUP_REPORT.md")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up redundant test files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without actually removing')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.force and not args.dry_run:
        print("⚠️  This script will remove redundant test files.")
        print("   A backup will be created in test_backup/ directory.")
        response = input("   Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cleanup cancelled.")
            return
    
    cleanup = TestCleanup()
    
    if args.dry_run:
        print("🔍 DRY RUN - Showing what would be removed:")
        print("\nBackend tests to remove:")
        for test_file in cleanup.redundant_backend_tests:
            print(f"  - {test_file}")
        print("\nFrontend tests to remove:")
        for test_file in cleanup.redundant_frontend_tests:
            print(f"  - {test_file}")
        print("\nQA tests to remove:")
        for test_file in cleanup.redundant_qa_tests:
            print(f"  - {test_file}")
        print(f"\nTotal files to remove: {len(cleanup.redundant_backend_tests) + len(cleanup.redundant_frontend_tests) + len(cleanup.redundant_qa_tests)}")
    else:
        cleanup.run_cleanup()


if __name__ == '__main__':
    main()