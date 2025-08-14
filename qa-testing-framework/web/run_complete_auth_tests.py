"""
Complete Authentication Test Suite Runner

Runs all authentication-related tests including basic authentication,
session management, and security tests with comprehensive reporting.
"""

import unittest
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qa_testing_framework.web.test_authentication import AuthenticationTestSuite
from qa_testing_framework.web.test_session_management import SessionManagementTestSuite
from qa_testing_framework.core.interfaces import Environment, ExecutionStatus, Severity
from qa_testing_framework.core.config import get_config


class CompleteAuthTestRunner:
    """Complete authentication test runner with detailed reporting"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.start_time = datetime.now()
        self.results = {
            'environment': environment.value,
            'start_time': self.start_time.isoformat(),
            'end_time': None,
            'test_suites': {
                'authentication': {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'skipped_tests': 0,
                    'test_results': [],
                    'defects': []
                },
                'session_management': {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'skipped_tests': 0,
                    'test_results': [],
                    'defects': []
                }
            },
            'overall_summary': {},
            'security_analysis': {},
            'recommendations': []
        }
    
    def run_all_tests(self, specific_suite: Optional[str] = None) -> Dict[str, Any]:
        """Run all authentication test suites"""
        print("=" * 80)
        print("COMPLETE AUTHENTICATION TEST SUITE")
        print(f"Environment: {self.environment.value}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        suites_to_run = []
        
        if specific_suite is None or specific_suite == 'authentication':
            suites_to_run.append(('authentication', AuthenticationTestSuite))
        
        if specific_suite is None or specific_suite == 'session':
            suites_to_run.append(('session_management', SessionManagementTestSuite))
        
        for suite_name, suite_class in suites_to_run:
            print(f"\n{'='*60}")
            print(f"Running {suite_name.replace('_', ' ').title()} Tests")
            print(f"{'='*60}")
            
            self._run_test_suite(suite_name, suite_class)
        
        # Generate comprehensive report
        self._generate_comprehensive_report()
        
        return self.results
    
    def _run_test_suite(self, suite_name: str, suite_class) -> None:
        """Run individual test suite"""
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
        
        # Run tests with custom result collector
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        test_result = runner.run(suite)
        
        # Collect results
        self._collect_suite_results(suite_name, suite_class, test_result)
    
    def _collect_suite_results(self, suite_name: str, suite_class, test_result: unittest.TestResult):
        """Collect results from test suite"""
        suite_results = self.results['test_suites'][suite_name]
        
        # Basic metrics
        suite_results['total_tests'] = test_result.testsRun
        suite_results['failed_tests'] = len(test_result.failures) + len(test_result.errors)
        suite_results['passed_tests'] = test_result.testsRun - suite_results['failed_tests']
        suite_results['skipped_tests'] = len(test_result.skipped) if hasattr(test_result, 'skipped') else 0
        
        # Collect individual test results
        for test, error in test_result.failures:
            suite_results['test_results'].append({
                'test_name': str(test),
                'status': 'FAILED',
                'error': error,
                'type': 'failure'
            })
        
        for test, error in test_result.errors:
            suite_results['test_results'].append({
                'test_name': str(test),
                'status': 'ERROR',
                'error': error,
                'type': 'error'
            })
        
        # Collect defects from test suite
        if hasattr(suite_class, 'defects'):
            for defect in suite_class.defects:
                suite_results['defects'].append({
                    'id': defect.id,
                    'title': defect.title,
                    'description': defect.description,
                    'severity': defect.severity.value,
                    'test_case_id': defect.test_case_id,
                    'reproduction_steps': defect.reproduction_steps
                })
        
        # Collect test executions
        if hasattr(suite_class, 'test_executions'):
            for execution in suite_class.test_executions:
                suite_results['test_results'].append({
                    'test_name': execution.test_case_id,
                    'status': execution.status.value,
                    'duration': execution.duration,
                    'screenshots': execution.screenshots
                })
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive test report with analysis"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.results['end_time'] = end_time.isoformat()
        
        # Calculate overall summary
        total_tests = sum(suite['total_tests'] for suite in self.results['test_suites'].values())
        total_passed = sum(suite['passed_tests'] for suite in self.results['test_suites'].values())
        total_failed = sum(suite['failed_tests'] for suite in self.results['test_suites'].values())
        total_skipped = sum(suite['skipped_tests'] for suite in self.results['test_suites'].values())
        
        self.results['overall_summary'] = {
            'total_duration_seconds': duration,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'overall_pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'suite_performance': {}
        }
        
        # Suite-specific performance
        for suite_name, suite_data in self.results['test_suites'].items():
            if suite_data['total_tests'] > 0:
                self.results['overall_summary']['suite_performance'][suite_name] = {
                    'pass_rate': (suite_data['passed_tests'] / suite_data['total_tests'] * 100),
                    'total_tests': suite_data['total_tests'],
                    'critical_defects': len([d for d in suite_data['defects'] if d['severity'] == 'critical']),
                    'major_defects': len([d for d in suite_data['defects'] if d['severity'] == 'major'])
                }
        
        # Security analysis
        self._analyze_security_issues()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Print summary
        self._print_comprehensive_summary()
        
        # Save report
        self._save_comprehensive_report()
    
    def _analyze_security_issues(self):
        """Analyze security-related test results"""
        all_defects = []
        for suite_data in self.results['test_suites'].values():
            all_defects.extend(suite_data['defects'])
        
        security_keywords = ['sql', 'xss', 'session', 'hijack', 'fixation', 'injection', 'security']
        
        security_defects = []
        for defect in all_defects:
            if any(keyword in defect['title'].lower() or keyword in defect['description'].lower() 
                   for keyword in security_keywords):
                security_defects.append(defect)
        
        self.results['security_analysis'] = {
            'total_security_defects': len(security_defects),
            'critical_security_defects': len([d for d in security_defects if d['severity'] == 'critical']),
            'major_security_defects': len([d for d in security_defects if d['severity'] == 'major']),
            'security_defects': security_defects,
            'security_categories': {
                'sql_injection': len([d for d in security_defects if 'sql' in d['title'].lower()]),
                'xss': len([d for d in security_defects if 'xss' in d['title'].lower()]),
                'session_security': len([d for d in security_defects if 'session' in d['title'].lower()]),
                'authentication': len([d for d in security_defects if 'auth' in d['title'].lower()])
            }
        }
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Overall pass rate recommendations
        overall_pass_rate = self.results['overall_summary']['overall_pass_rate']
        if overall_pass_rate < 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Quality',
                'recommendation': f'Overall pass rate is {overall_pass_rate:.1f}%. Focus on fixing failing tests to improve authentication reliability.'
            })
        
        # Security recommendations
        security_analysis = self.results['security_analysis']
        if security_analysis['critical_security_defects'] > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Security',
                'recommendation': f'Found {security_analysis["critical_security_defects"]} critical security defects. Address immediately to prevent security vulnerabilities.'
            })
        
        if security_analysis['security_categories']['sql_injection'] > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Security',
                'recommendation': 'SQL injection vulnerabilities detected. Implement proper input sanitization and parameterized queries.'
            })
        
        if security_analysis['security_categories']['xss'] > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Security',
                'recommendation': 'XSS vulnerabilities detected. Implement proper output encoding and input validation.'
            })
        
        if security_analysis['security_categories']['session_security'] > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Security',
                'recommendation': 'Session security issues detected. Review session management implementation and security attributes.'
            })
        
        # Suite-specific recommendations
        for suite_name, performance in self.results['overall_summary']['suite_performance'].items():
            if performance['pass_rate'] < 70:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Quality',
                    'recommendation': f'{suite_name.replace("_", " ").title()} suite has low pass rate ({performance["pass_rate"]:.1f}%). Review and fix failing tests.'
                })
        
        # Environment-specific recommendations
        if self.environment == Environment.DEVELOPMENT:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Process',
                'recommendation': 'Run these tests in staging environment before production deployment to catch environment-specific issues.'
            })
        
        self.results['recommendations'] = recommendations
    
    def _print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUTHENTICATION TEST SUMMARY")
        print("=" * 80)
        
        summary = self.results['overall_summary']
        print(f"Environment: {self.results['environment']}")
        print(f"Total Duration: {summary['total_duration_seconds']:.2f} seconds")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['total_passed']}")
        print(f"Failed: {summary['total_failed']}")
        print(f"Skipped: {summary['total_skipped']}")
        print(f"Overall Pass Rate: {summary['overall_pass_rate']:.1f}%")
        
        print(f"\nSuite Performance:")
        for suite_name, performance in summary['suite_performance'].items():
            print(f"  {suite_name.replace('_', ' ').title()}:")
            print(f"    Tests: {performance['total_tests']}")
            print(f"    Pass Rate: {performance['pass_rate']:.1f}%")
            print(f"    Critical Defects: {performance['critical_defects']}")
            print(f"    Major Defects: {performance['major_defects']}")
        
        # Security Analysis
        security = self.results['security_analysis']
        print(f"\nSecurity Analysis:")
        print(f"  Total Security Defects: {security['total_security_defects']}")
        print(f"  Critical Security Defects: {security['critical_security_defects']}")
        print(f"  Major Security Defects: {security['major_security_defects']}")
        
        if security['security_categories']:
            print(f"  Security Categories:")
            for category, count in security['security_categories'].items():
                if count > 0:
                    print(f"    {category.replace('_', ' ').title()}: {count}")
        
        # Critical Issues
        critical_defects = []
        for suite_data in self.results['test_suites'].values():
            critical_defects.extend([d for d in suite_data['defects'] if d['severity'] == 'critical'])
        
        if critical_defects:
            print(f"\nCritical Issues (Immediate Attention Required):")
            for defect in critical_defects[:5]:  # Show top 5
                print(f"  - {defect['title']}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\nTop Recommendations:")
            high_priority_recs = [r for r in self.results['recommendations'] if r['priority'] in ['CRITICAL', 'HIGH']]
            for rec in high_priority_recs[:3]:  # Show top 3
                print(f"  [{rec['priority']}] {rec['recommendation']}")
        
        print("\n" + "=" * 80)
    
    def _save_comprehensive_report(self):
        """Save comprehensive report to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create reports directory
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Save JSON report
        json_filename = f"complete_auth_test_report_{self.environment.value}_{timestamp}.json"
        json_filepath = os.path.join(reports_dir, json_filename)
        
        with open(json_filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save HTML report
        html_filename = f"complete_auth_test_report_{self.environment.value}_{timestamp}.html"
        html_filepath = os.path.join(reports_dir, html_filename)
        
        self._generate_html_report(html_filepath)
        
        print(f"\nReports saved:")
        print(f"  JSON: {json_filepath}")
        print(f"  HTML: {html_filepath}")
    
    def _generate_html_report(self, filepath: str):
        """Generate HTML report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Test Report - {self.environment.value}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .defect {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b6b; background-color: #fff5f5; }}
        .defect.critical {{ border-left-color: #ff0000; }}
        .defect.major {{ border-left-color: #ff6b00; }}
        .defect.minor {{ border-left-color: #ffaa00; }}
        .recommendation {{ margin: 10px 0; padding: 10px; border-left: 4px solid #4ecdc4; background-color: #f0fffe; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Authentication Test Report</h1>
        <p><strong>Environment:</strong> {self.results['environment']}</p>
        <p><strong>Start Time:</strong> {self.results['start_time']}</p>
        <p><strong>End Time:</strong> {self.results['end_time']}</p>
        <p><strong>Duration:</strong> {self.results['overall_summary']['total_duration_seconds']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Overall Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Tests</td><td>{self.results['overall_summary']['total_tests']}</td></tr>
            <tr><td>Passed</td><td class="pass">{self.results['overall_summary']['total_passed']}</td></tr>
            <tr><td>Failed</td><td class="fail">{self.results['overall_summary']['total_failed']}</td></tr>
            <tr><td>Pass Rate</td><td>{self.results['overall_summary']['overall_pass_rate']:.1f}%</td></tr>
        </table>
    </div>
    
    <div class="security">
        <h2>Security Analysis</h2>
        <table>
            <tr><th>Category</th><th>Count</th></tr>
            <tr><td>Total Security Defects</td><td>{self.results['security_analysis']['total_security_defects']}</td></tr>
            <tr><td>Critical Security Defects</td><td class="fail">{self.results['security_analysis']['critical_security_defects']}</td></tr>
            <tr><td>Major Security Defects</td><td>{self.results['security_analysis']['major_security_defects']}</td></tr>
        </table>
    </div>
"""
        
        # Add suite details
        for suite_name, suite_data in self.results['test_suites'].items():
            html_content += f"""
    <div class="suite">
        <h3>{suite_name.replace('_', ' ').title()} Suite</h3>
        <p>Tests: {suite_data['total_tests']} | Passed: {suite_data['passed_tests']} | Failed: {suite_data['failed_tests']}</p>
        
        <h4>Defects</h4>
"""
            for defect in suite_data['defects']:
                html_content += f"""
        <div class="defect {defect['severity']}">
            <strong>[{defect['severity'].upper()}] {defect['title']}</strong>
            <p>{defect['description']}</p>
        </div>
"""
            
            html_content += "</div>"
        
        # Add recommendations
        html_content += """
    <div class="recommendations">
        <h2>Recommendations</h2>
"""
        for rec in self.results['recommendations']:
            html_content += f"""
        <div class="recommendation">
            <strong>[{rec['priority']}] {rec['category']}</strong>
            <p>{rec['recommendation']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w') as f:
            f.write(html_content)


def main():
    """Main function to run complete authentication tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Complete Authentication Test Suite')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'staging', 'production'],
                       default='development',
                       help='Test environment (default: development)')
    parser.add_argument('--suite', '-s',
                       choices=['authentication', 'session'],
                       help='Specific test suite to run (default: all)')
    parser.add_argument('--browser', '-b',
                       choices=['chrome', 'firefox', 'edge', 'safari'],
                       default='chrome',
                       help='Browser to use for testing (default: chrome)')
    
    args = parser.parse_args()
    
    # Set environment
    env_map = {
        'development': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'production': Environment.PRODUCTION
    }
    environment = env_map[args.environment]
    
    # Create and run test runner
    runner = CompleteAuthTestRunner(environment)
    
    try:
        results = runner.run_all_tests(args.suite)
        
        # Exit with appropriate code
        total_failed = results['overall_summary']['total_failed']
        critical_security_defects = results['security_analysis']['critical_security_defects']
        
        if critical_security_defects > 0:
            print(f"\nCRITICAL: {critical_security_defects} critical security defects found!")
            sys.exit(3)
        elif total_failed > 0:
            print(f"\nTests completed with {total_failed} failures.")
            sys.exit(1)
        else:
            print(f"\nAll tests passed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(2)
    except Exception as e:
        print(f"\nTest execution failed with error: {str(e)}")
        sys.exit(4)


if __name__ == '__main__':
    main()