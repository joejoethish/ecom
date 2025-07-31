#!/usr/bin/env python3
"""
Validation script for migration testing suite.
Performs basic validation to ensure all test files are properly structured.
"""
import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()


class MigrationTestValidator:
    """Validator for migration test files"""
    
    def __init__(self):
        self.test_files = [
            'tests/test_migration_comprehensive.py',
            'tests/test_migration_edge_cases.py',
            'tests/integration/test_migration_workflow.py',
            'core/tests/test_migration.py'
        ]
        
        self.validation_results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'total_test_classes': 0,
            'total_test_methods': 0,
            'file_details': {}
        }
    
    def validate_file_syntax(self, file_path: str) -> Dict[str, Any]:
        """Validate Python syntax of test file"""
        result = {
            'file_path': file_path,
            'syntax_valid': False,
            'imports_valid': False,
            'test_classes': [],
            'test_methods': [],
            'errors': []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['errors'].append(f"File does not exist: {file_path}")
                return result
            
            # Parse file syntax
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
                result['syntax_valid'] = True
            except SyntaxError as e:
                result['errors'].append(f"Syntax error: {e}")
                return result
            
            # Analyze AST for test classes and methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a test class
                    if (node.name.startswith('Test') or 
                        any(base.id == 'TestCase' for base in node.bases if isinstance(base, ast.Name)) or
                        any(base.id == 'TransactionTestCase' for base in node.bases if isinstance(base, ast.Name))):
                        
                        result['test_classes'].append(node.name)
                        
                        # Find test methods in this class
                        for item in node.body:
                            if (isinstance(item, ast.FunctionDef) and 
                                item.name.startswith('test_')):
                                result['test_methods'].append(f"{node.name}.{item.name}")
            
            # Try to import the module to check imports
            try:
                spec = importlib.util.spec_from_file_location("test_module", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result['imports_valid'] = True
            except Exception as e:
                result['errors'].append(f"Import error: {e}")
            
        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
        
        return result
    
    def validate_test_coverage(self, file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate test coverage across all files"""
        coverage_result = {
            'required_components': [
                'DatabaseMigrationService',
                'MigrationValidator', 
                'MigrationProgress',
                'ValidationResult',
                'rollback',
                'data_integrity',
                'schema_compatibility',
                'batch_processing',
                'error_handling',
                'edge_cases',
                'integration_workflow'
            ],
            'covered_components': set(),
            'missing_components': [],
            'coverage_percentage': 0
        }
        
        # Analyze test method names to determine coverage
        all_test_methods = []
        for file_result in file_results:
            all_test_methods.extend(file_result['test_methods'])
        
        # Check coverage based on test method names
        test_methods_text = ' '.join(all_test_methods).lower()
        
        for component in coverage_result['required_components']:
            if component.lower() in test_methods_text:
                coverage_result['covered_components'].add(component)
            else:
                coverage_result['missing_components'].append(component)
        
        coverage_result['coverage_percentage'] = (
            len(coverage_result['covered_components']) / 
            len(coverage_result['required_components']) * 100
        )
        
        return coverage_result
    
    def validate_all_files(self) -> Dict[str, Any]:
        """Validate all migration test files"""
        print("MIGRATION TEST VALIDATION")
        print("=" * 50)
        
        file_results = []
        
        for file_path in self.test_files:
            print(f"\nValidating: {file_path}")
            print("-" * 30)
            
            result = self.validate_file_syntax(file_path)
            file_results.append(result)
            
            self.validation_results['total_files'] += 1
            
            if result['syntax_valid'] and result['imports_valid'] and not result['errors']:
                self.validation_results['valid_files'] += 1
                print("✓ File validation passed")
            else:
                self.validation_results['invalid_files'] += 1
                print("✗ File validation failed")
            
            print(f"  Syntax valid: {'✓' if result['syntax_valid'] else '✗'}")
            print(f"  Imports valid: {'✓' if result['imports_valid'] else '✗'}")
            print(f"  Test classes: {len(result['test_classes'])}")
            print(f"  Test methods: {len(result['test_methods'])}")
            
            if result['errors']:
                print("  Errors:")
                for error in result['errors']:
                    print(f"    - {error}")
            
            if result['test_classes']:
                print("  Test classes found:")
                for class_name in result['test_classes']:
                    print(f"    - {class_name}")
            
            self.validation_results['total_test_classes'] += len(result['test_classes'])
            self.validation_results['total_test_methods'] += len(result['test_methods'])
            self.validation_results['file_details'][file_path] = result
        
        # Validate test coverage
        coverage_result = self.validate_test_coverage(file_results)
        
        print(f"\nTEST COVERAGE ANALYSIS")
        print("-" * 30)
        print(f"Coverage: {coverage_result['coverage_percentage']:.1f}%")
        print(f"Covered components: {len(coverage_result['covered_components'])}/{len(coverage_result['required_components'])}")
        
        if coverage_result['covered_components']:
            print("✓ Covered components:")
            for component in sorted(coverage_result['covered_components']):
                print(f"    - {component}")
        
        if coverage_result['missing_components']:
            print("✗ Missing components:")
            for component in coverage_result['missing_components']:
                print(f"    - {component}")
        
        self.validation_results['coverage'] = coverage_result
        
        return self.validation_results
    
    def generate_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate validation report"""
        report_lines = [
            "=" * 60,
            "MIGRATION TEST VALIDATION REPORT",
            "=" * 60,
            "",
            "SUMMARY:",
            f"  Total files validated: {results['total_files']}",
            f"  Valid files: {results['valid_files']}",
            f"  Invalid files: {results['invalid_files']}",
            f"  Total test classes: {results['total_test_classes']}",
            f"  Total test methods: {results['total_test_methods']}",
            "",
            "FILE VALIDATION DETAILS:",
        ]
        
        for file_path, file_result in results['file_details'].items():
            status = "PASS" if (file_result['syntax_valid'] and 
                              file_result['imports_valid'] and 
                              not file_result['errors']) else "FAIL"
            
            report_lines.extend([
                f"  {file_path}: {status}",
                f"    Test classes: {len(file_result['test_classes'])}",
                f"    Test methods: {len(file_result['test_methods'])}",
            ])
            
            if file_result['errors']:
                report_lines.append("    Errors:")
                for error in file_result['errors']:
                    report_lines.append(f"      - {error}")
            
            report_lines.append("")
        
        # Coverage details
        coverage = results['coverage']
        report_lines.extend([
            "TEST COVERAGE ANALYSIS:",
            f"  Overall coverage: {coverage['coverage_percentage']:.1f}%",
            f"  Covered: {len(coverage['covered_components'])}/{len(coverage['required_components'])} components",
            ""
        ])
        
        if coverage['covered_components']:
            report_lines.append("  Covered components:")
            for component in sorted(coverage['covered_components']):
                report_lines.append(f"    ✓ {component}")
            report_lines.append("")
        
        if coverage['missing_components']:
            report_lines.append("  Missing components:")
            for component in coverage['missing_components']:
                report_lines.append(f"    ✗ {component}")
            report_lines.append("")
        
        # Recommendations
        if results['invalid_files'] > 0:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "  ⚠️  Some test files have validation issues.",
                "  🔧 Fix syntax errors and import issues.",
                "  📋 Review error messages for specific problems.",
                ""
            ])
        elif coverage['coverage_percentage'] < 80:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "  ⚠️  Test coverage is below 80%.",
                "  📝 Add tests for missing components.",
                "  🧪 Ensure comprehensive test coverage.",
                ""
            ])
        else:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "  ✅ All test files are valid!",
                "  ✅ Test coverage is comprehensive!",
                "  🚀 Migration test suite is ready for use.",
                ""
            ])
        
        report_lines.extend([
            "=" * 60,
            "VALIDATION COMPLETE",
            "=" * 60
        ])
        
        return "\n".join(report_lines)


def main():
    """Main entry point for validation script"""
    try:
        validator = MigrationTestValidator()
        results = validator.validate_all_files()
        report = validator.generate_validation_report(results)
        
        print("\n" + report)
        
        # Save validation report
        with open('migration_test_validation_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nValidation report saved to: migration_test_validation_report.txt")
        
        # Exit with appropriate code
        if results['invalid_files'] > 0:
            print(f"\n❌ Validation failed: {results['invalid_files']} invalid files found.")
            sys.exit(1)
        elif results['coverage']['coverage_percentage'] < 80:
            print(f"\n⚠️  Validation warning: Test coverage is {results['coverage']['coverage_percentage']:.1f}% (below 80%).")
            sys.exit(0)
        else:
            print(f"\n✅ Validation passed: All {results['total_files']} test files are valid with {results['coverage']['coverage_percentage']:.1f}% coverage!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\nValidation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()