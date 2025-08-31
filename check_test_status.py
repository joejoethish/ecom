#!/usr/bin/env python3
"""
Quick Test Status Checker

This script provides a quick overview of test status without running all tests.
Useful for checking if the platform is likely to pass tests before running the full suite.
"""

import os
import subprocess
import sys
from pathlib import Path

class TestStatusChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.issues = []
        self.warnings = []
        
    def check_environment(self):
        """Check if the test environment is properly set up"""
        print("🔍 Checking test environment...")
        
        # Check project structure
        required_dirs = ['backend', 'frontend', 'qa-testing-framework']
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                self.issues.append(f"Missing directory: {dir_name}")
        
        # Check backend setup
        backend_dir = self.project_root / 'backend'
        if backend_dir.exists():
            if not (backend_dir / 'manage.py').exists():
                self.issues.append("Backend: manage.py not found")
            
            if not (backend_dir / 'venv').exists() and not os.environ.get('VIRTUAL_ENV'):
                self.warnings.append("Backend: No Python virtual environment detected")
            
            # Check if migrations are up to date
            try:
                os.chdir(backend_dir)
                result = subprocess.run(['python', 'manage.py', 'showmigrations', '--plan'], 
                                      capture_output=True, text=True, timeout=10)
                if '[ ]' in result.stdout:
                    self.warnings.append("Backend: Unapplied migrations detected")
            except Exception as e:
                self.warnings.append(f"Backend: Could not check migrations - {e}")
            finally:
                os.chdir(self.project_root)
        
        # Check frontend setup
        frontend_dir = self.project_root / 'frontend'
        if frontend_dir.exists():
            if not (frontend_dir / 'package.json').exists():
                self.issues.append("Frontend: package.json not found")
            
            if not (frontend_dir / 'node_modules').exists():
                self.warnings.append("Frontend: node_modules not found - run 'npm install'")
        
        # Check QA framework setup
        qa_dir = self.project_root / 'qa-testing-framework'
        if qa_dir.exists():
            if not (qa_dir / 'requirements.txt').exists():
                self.issues.append("QA Framework: requirements.txt not found")
    
    def check_database_connectivity(self):
        """Check if database is accessible"""
        print("🗄️  Checking database connectivity...")
        
        backend_dir = self.project_root / 'backend'
        if not backend_dir.exists():
            return
        
        try:
            os.chdir(backend_dir)
            result = subprocess.run(['python', 'manage.py', 'check', '--database', 'default'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                self.issues.append(f"Database connectivity failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.issues.append("Database check timed out - database may be slow or unavailable")
        except Exception as e:
            self.issues.append(f"Could not check database: {e}")
        finally:
            os.chdir(self.project_root)
    
    def check_test_files_exist(self):
        """Check if essential test files exist"""
        print("📋 Checking essential test files...")
        
        essential_files = [
            # Backend
            'backend/tests/unit/test_models.py',
            'backend/tests/unit/test_views.py',
            'backend/tests/integration/test_system_integration.py',
            
            # Frontend
            'frontend/src/__tests__/components/Dashboard.test.tsx',
            'frontend/src/__tests__/components/AdminLogin.test.tsx',
            
            # QA Framework
            'qa-testing-framework/web/test_authentication.py',
            'qa-testing-framework/web/test_shopping_cart_checkout.py',
        ]
        
        missing_files = []
        for file_path in essential_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.issues.append(f"Missing essential test files: {', '.join(missing_files)}")
    
    def check_syntax_errors(self):
        """Check for basic syntax errors in test files"""
        print("🔧 Checking for syntax errors...")
        
        # Check Python files
        python_test_dirs = [
            'backend/tests',
            'qa-testing-framework'
        ]
        
        for test_dir in python_test_dirs:
            dir_path = self.project_root / test_dir
            if not dir_path.exists():
                continue
                
            for py_file in dir_path.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        compile(f.read(), str(py_file), 'exec')
                except SyntaxError as e:
                    self.issues.append(f"Syntax error in {py_file}: {e}")
                except Exception as e:
                    self.warnings.append(f"Could not check {py_file}: {e}")
        
        # Check TypeScript/JavaScript files
        frontend_test_dir = self.project_root / 'frontend' / 'src' / '__tests__'
        if frontend_test_dir.exists():
            try:
                os.chdir(self.project_root / 'frontend')
                result = subprocess.run(['npx', 'tsc', '--noEmit'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self.warnings.append("TypeScript compilation issues detected")
            except Exception as e:
                self.warnings.append(f"Could not check TypeScript: {e}")
            finally:
                os.chdir(self.project_root)
    
    def estimate_test_duration(self):
        """Estimate how long tests will take to run"""
        print("⏱️  Estimating test duration...")
        
        # Count test files
        backend_tests = len(list((self.project_root / 'backend' / 'tests').rglob('test_*.py'))) if (self.project_root / 'backend' / 'tests').exists() else 0
        frontend_tests = len(list((self.project_root / 'frontend' / 'src' / '__tests__').rglob('*.test.*'))) if (self.project_root / 'frontend' / 'src' / '__tests__').exists() else 0
        qa_tests = len(list((self.project_root / 'qa-testing-framework').rglob('test_*.py'))) if (self.project_root / 'qa-testing-framework').exists() else 0
        
        # Rough estimates (in minutes)
        backend_time = backend_tests * 0.5  # 30 seconds per test file
        frontend_time = frontend_tests * 0.3  # 18 seconds per test file
        qa_time = qa_tests * 1.0  # 1 minute per test file
        
        total_time = backend_time + frontend_time + qa_time
        
        print(f"   Backend tests: {backend_tests} files (~{backend_time:.1f} min)")
        print(f"   Frontend tests: {frontend_tests} files (~{frontend_time:.1f} min)")
        print(f"   QA tests: {qa_tests} files (~{qa_time:.1f} min)")
        print(f"   Total estimated time: ~{total_time:.1f} minutes")
        
        return total_time
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🚨 Fix critical issues before running tests")
            for issue in self.issues:
                recommendations.append(f"   - {issue}")
        
        if self.warnings:
            recommendations.append("⚠️  Address warnings for better test reliability")
            for warning in self.warnings:
                recommendations.append(f"   - {warning}")
        
        if not self.issues and not self.warnings:
            recommendations.append("✅ Environment looks good for testing")
            recommendations.append("   - Run: ./run_essential_tests.sh --full")
        elif not self.issues:
            recommendations.append("⚠️  Minor issues detected but tests should run")
            recommendations.append("   - Run: ./run_essential_tests.sh --quick")
        
        return recommendations
    
    def run_check(self):
        """Run all checks and provide summary"""
        print("🚀 E-Commerce Platform - Test Status Check")
        print("=" * 50)
        
        # Run all checks
        self.check_environment()
        self.check_database_connectivity()
        self.check_test_files_exist()
        self.check_syntax_errors()
        estimated_time = self.estimate_test_duration()
        
        # Print summary
        print("\n📊 Summary")
        print("=" * 50)
        
        if self.issues:
            print(f"❌ Critical Issues: {len(self.issues)}")
            for issue in self.issues:
                print(f"   - {issue}")
        else:
            print("✅ No critical issues found")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        # Generate recommendations
        print(f"\n💡 Recommendations")
        print("=" * 50)
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            print(rec)
        
        # Return status
        if self.issues:
            print(f"\n🔴 Status: NOT READY FOR TESTING")
            return False
        elif self.warnings:
            print(f"\n🟡 Status: READY WITH WARNINGS")
            return True
        else:
            print(f"\n🟢 Status: READY FOR TESTING")
            return True


def main():
    """Main entry point"""
    checker = TestStatusChecker()
    
    try:
        ready = checker.run_check()
        sys.exit(0 if ready else 1)
    except KeyboardInterrupt:
        print("\n❌ Check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Check failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()