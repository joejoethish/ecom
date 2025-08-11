# Test reporting and analytics utilities
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytest
from django.conf import settings
from django.test import TestCase
import sqlite3
import csv

class TestReporter:
    """Comprehensive test reporting and analytics"""
    
    def __init__(self, report_dir: str = 'test_reports'):
        self.report_dir = report_dir
        self.ensure_report_dir()
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def ensure_report_dir(self):
        """Ensure report directory exists"""
        os.makedirs(self.report_dir, exist_ok=True)
    
    def start_test_session(self):
        """Start test session tracking"""
        self.start_time = datetime.now()
        self.test_results = []
    
    def end_test_session(self):
        """End test session and generate reports"""
        self.end_time = datetime.now()
        self.generate_summary_report()
        self.generate_detailed_report()
        self.generate_performance_report()
        self.generate_coverage_report()
    
    def record_test_result(self, test_name: str, status: str, duration: float, 
                          error_message: str = None, test_type: str = 'unit'):
        """Record individual test result"""
        result = {
            'test_name': test_name,
            'status': status,  # passed, failed, skipped, error
            'duration': duration,
            'error_message': error_message,
            'test_type': test_type,
            'timestamp': datetime.now().isoformat(),
        }
        self.test_results.append(result)
    
    def generate_summary_report(self):
        """Generate summary test report"""
        if not self.test_results:
            return
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'passed'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'failed'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'skipped'])
        error_tests = len([r for r in self.test_results if r['status'] == 'error'])
        
        total_duration = sum(r['duration'] for r in self.test_results)
        session_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        summary = {
            'test_session': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'session_duration': session_duration,
            },
            'test_counts': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'errors': error_tests,
            },
            'test_percentages': {
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'fail_rate': (failed_tests / total_tests * 100) if total_tests > 0 else 0,
                'skip_rate': (skipped_tests / total_tests * 100) if total_tests > 0 else 0,
                'error_rate': (error_tests / total_tests * 100) if total_tests > 0 else 0,
            },
            'performance': {
                'total_test_duration': total_duration,
                'average_test_duration': total_duration / total_tests if total_tests > 0 else 0,
                'slowest_tests': sorted(self.test_results, key=lambda x: x['duration'], reverse=True)[:10],
            },
            'test_types': self._get_test_type_breakdown(),
        }
        
        # Save summary report
        with open(os.path.join(self.report_dir, 'test_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Generate HTML summary
        self._generate_html_summary(summary)
    
    def generate_detailed_report(self):
        """Generate detailed test report"""
        detailed_report = {
            'test_results': self.test_results,
            'failed_tests': [r for r in self.test_results if r['status'] == 'failed'],
            'error_tests': [r for r in self.test_results if r['status'] == 'error'],
            'slow_tests': [r for r in self.test_results if r['duration'] > 5.0],
        }
        
        with open(os.path.join(self.report_dir, 'test_detailed.json'), 'w') as f:
            json.dump(detailed_report, f, indent=2, default=str)
        
        # Generate CSV report
        self._generate_csv_report()
    
    def generate_performance_report(self):
        """Generate performance analysis report"""
        if not self.test_results:
            return
        
        performance_data = {
            'duration_analysis': {
                'min_duration': min(r['duration'] for r in self.test_results),
                'max_duration': max(r['duration'] for r in self.test_results),
                'avg_duration': sum(r['duration'] for r in self.test_results) / len(self.test_results),
                'median_duration': self._calculate_median([r['duration'] for r in self.test_results]),
            },
            'performance_by_type': self._get_performance_by_type(),
            'slow_test_analysis': self._analyze_slow_tests(),
            'performance_trends': self._get_performance_trends(),
        }
        
        with open(os.path.join(self.report_dir, 'performance_report.json'), 'w') as f:
            json.dump(performance_data, f, indent=2, default=str)
    
    def generate_coverage_report(self):
        """Generate test coverage report"""
        try:
            import coverage
            
            cov = coverage.Coverage()
            cov.load()
            
            coverage_data = {
                'total_coverage': cov.report(),
                'missing_lines': {},
                'branch_coverage': {},
            }
            
            # Get detailed coverage information
            for filename in cov.get_data().measured_files():
                analysis = cov.analysis2(filename)
                coverage_data['missing_lines'][filename] = analysis[3]  # Missing lines
            
            with open(os.path.join(self.report_dir, 'coverage_report.json'), 'w') as f:
                json.dump(coverage_data, f, indent=2, default=str)
        
        except ImportError:
            print("Coverage.py not available, skipping coverage report")
    
    def _get_test_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of tests by type"""
        breakdown = {}
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            breakdown[test_type] = breakdown.get(test_type, 0) + 1
        return breakdown
    
    def _get_performance_by_type(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics by test type"""
        by_type = {}
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(result['duration'])
        
        performance_by_type = {}
        for test_type, durations in by_type.items():
            performance_by_type[test_type] = {
                'count': len(durations),
                'total_duration': sum(durations),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
            }
        
        return performance_by_type
    
    def _analyze_slow_tests(self) -> Dict[str, Any]:
        """Analyze slow running tests"""
        slow_threshold = 5.0  # seconds
        slow_tests = [r for r in self.test_results if r['duration'] > slow_threshold]
        
        return {
            'slow_test_count': len(slow_tests),
            'slow_test_percentage': (len(slow_tests) / len(self.test_results) * 100) if self.test_results else 0,
            'slowest_tests': sorted(slow_tests, key=lambda x: x['duration'], reverse=True)[:20],
            'slow_test_types': self._get_slow_test_types(slow_tests),
        }
    
    def _get_slow_test_types(self, slow_tests: List[Dict]) -> Dict[str, int]:
        """Get breakdown of slow tests by type"""
        breakdown = {}
        for test in slow_tests:
            test_type = test.get('test_type', 'unknown')
            breakdown[test_type] = breakdown.get(test_type, 0) + 1
        return breakdown
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends over time"""
        # This would compare with historical data
        # For now, return basic trend analysis
        return {
            'trend_analysis': 'Historical trend analysis would go here',
            'performance_regression': [],
            'performance_improvements': [],
        }
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median value"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def _generate_html_summary(self, summary: Dict):
        """Generate HTML summary report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Summary Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .passed {{ background-color: #d4edda; }}
                .failed {{ background-color: #f8d7da; }}
                .skipped {{ background-color: #fff3cd; }}
                .error {{ background-color: #f5c6cb; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Summary Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Session Duration: {summary['test_session'].get('session_duration', 0):.2f} seconds</p>
            </div>
            
            <div class="stats">
                <div class="stat-box passed">
                    <h3>{summary['test_counts']['passed']}</h3>
                    <p>Passed ({summary['test_percentages']['pass_rate']:.1f}%)</p>
                </div>
                <div class="stat-box failed">
                    <h3>{summary['test_counts']['failed']}</h3>
                    <p>Failed ({summary['test_percentages']['fail_rate']:.1f}%)</p>
                </div>
                <div class="stat-box skipped">
                    <h3>{summary['test_counts']['skipped']}</h3>
                    <p>Skipped ({summary['test_percentages']['skip_rate']:.1f}%)</p>
                </div>
                <div class="stat-box error">
                    <h3>{summary['test_counts']['errors']}</h3>
                    <p>Errors ({summary['test_percentages']['error_rate']:.1f}%)</p>
                </div>
            </div>
            
            <h2>Performance Summary</h2>
            <p>Total Test Duration: {summary['performance']['total_test_duration']:.2f} seconds</p>
            <p>Average Test Duration: {summary['performance']['average_test_duration']:.2f} seconds</p>
            
            <h2>Slowest Tests</h2>
            <table>
                <tr><th>Test Name</th><th>Duration (s)</th><th>Type</th></tr>
        """
        
        for test in summary['performance']['slowest_tests']:
            html_content += f"""
                <tr>
                    <td>{test['test_name']}</td>
                    <td>{test['duration']:.2f}</td>
                    <td>{test.get('test_type', 'unknown')}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(os.path.join(self.report_dir, 'test_summary.html'), 'w') as f:
            f.write(html_content)
    
    def _generate_csv_report(self):
        """Generate CSV report for data analysis"""
        csv_file = os.path.join(self.report_dir, 'test_results.csv')
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'test_name', 'status', 'duration', 'test_type', 'timestamp', 'error_message'
            ])
            writer.writeheader()
            writer.writerows(self.test_results)

class TestMetrics:
    """Test metrics collection and analysis"""
    
    def __init__(self, db_path: str = 'test_metrics.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                skipped_tests INTEGER,
                error_tests INTEGER,
                total_duration REAL,
                pass_rate REAL,
                commit_hash TEXT,
                branch_name TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                test_name TEXT,
                test_type TEXT,
                status TEXT,
                duration REAL,
                error_message TEXT,
                FOREIGN KEY (run_id) REFERENCES test_runs (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_test_run(self, summary: Dict) -> int:
        """Record test run summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_runs (
                run_date, total_tests, passed_tests, failed_tests, 
                skipped_tests, error_tests, total_duration, pass_rate,
                commit_hash, branch_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            summary['test_counts']['total'],
            summary['test_counts']['passed'],
            summary['test_counts']['failed'],
            summary['test_counts']['skipped'],
            summary['test_counts']['errors'],
            summary['performance']['total_test_duration'],
            summary['test_percentages']['pass_rate'],
            self._get_commit_hash(),
            self._get_branch_name(),
        ))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return run_id
    
    def record_test_results(self, run_id: int, test_results: List[Dict]):
        """Record individual test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in test_results:
            cursor.execute('''
                INSERT INTO test_results (
                    run_id, test_name, test_type, status, duration, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                run_id,
                result['test_name'],
                result.get('test_type', 'unknown'),
                result['status'],
                result['duration'],
                result.get('error_message'),
            ))
        
        conn.commit()
        conn.close()
    
    def get_test_trends(self, days: int = 30) -> Dict:
        """Get test trends over specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT run_date, total_tests, pass_rate, total_duration
            FROM test_runs
            WHERE run_date >= ?
            ORDER BY run_date
        ''', (since_date,))
        
        trends = cursor.fetchall()
        conn.close()
        
        return {
            'trend_data': trends,
            'analysis': self._analyze_trends(trends),
        }
    
    def get_flaky_tests(self, min_runs: int = 10) -> List[Dict]:
        """Identify flaky tests (tests that sometimes pass, sometimes fail)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_name, 
                   COUNT(*) as total_runs,
                   SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_runs,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs
            FROM test_results
            GROUP BY test_name
            HAVING total_runs >= ? AND passed_runs > 0 AND failed_runs > 0
            ORDER BY (failed_runs * 1.0 / total_runs) DESC
        ''', (min_runs,))
        
        flaky_tests = []
        for row in cursor.fetchall():
            test_name, total_runs, passed_runs, failed_runs = row
            flaky_tests.append({
                'test_name': test_name,
                'total_runs': total_runs,
                'passed_runs': passed_runs,
                'failed_runs': failed_runs,
                'failure_rate': failed_runs / total_runs,
                'flakiness_score': self._calculate_flakiness_score(passed_runs, failed_runs, total_runs),
            })
        
        conn.close()
        return flaky_tests
    
    def _get_commit_hash(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def _get_branch_name(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def _analyze_trends(self, trends: List) -> Dict:
        """Analyze test trends"""
        if len(trends) < 2:
            return {'analysis': 'Insufficient data for trend analysis'}
        
        # Calculate trend direction
        recent_pass_rates = [trend[2] for trend in trends[-5:]]  # Last 5 runs
        older_pass_rates = [trend[2] for trend in trends[-10:-5]]  # Previous 5 runs
        
        if older_pass_rates:
            recent_avg = sum(recent_pass_rates) / len(recent_pass_rates)
            older_avg = sum(older_pass_rates) / len(older_pass_rates)
            
            if recent_avg > older_avg + 5:
                trend_direction = 'improving'
            elif recent_avg < older_avg - 5:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'trend_direction': trend_direction,
            'recent_average_pass_rate': sum(recent_pass_rates) / len(recent_pass_rates),
            'total_runs_analyzed': len(trends),
        }
    
    def _calculate_flakiness_score(self, passed: int, failed: int, total: int) -> float:
        """Calculate flakiness score (0-1, higher = more flaky)"""
        if total == 0:
            return 0
        
        # Flakiness is highest when pass/fail ratio is close to 50/50
        pass_rate = passed / total
        return 1 - abs(pass_rate - 0.5) * 2

# Pytest plugin for automatic reporting
class TestReportingPlugin:
    """Pytest plugin for automatic test reporting"""
    
    def __init__(self):
        self.reporter = TestReporter()
        self.metrics = TestMetrics()
    
    def pytest_sessionstart(self, session):
        """Called after the Session object has been created"""
        self.reporter.start_test_session()
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called after whole test run finished"""
        self.reporter.end_test_session()
        
        # Record metrics
        summary_file = os.path.join(self.reporter.report_dir, 'test_summary.json')
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            run_id = self.metrics.record_test_run(summary)
            self.metrics.record_test_results(run_id, self.reporter.test_results)
    
    def pytest_runtest_logreport(self, report):
        """Called for each test result"""
        if report.when == 'call':
            status = 'passed' if report.passed else 'failed' if report.failed else 'skipped'
            error_message = str(report.longrepr) if report.failed else None
            
            self.reporter.record_test_result(
                test_name=report.nodeid,
                status=status,
                duration=report.duration,
                error_message=error_message,
                test_type=self._determine_test_type(report.nodeid)
            )
    
    def _determine_test_type(self, nodeid: str) -> str:
        """Determine test type from node ID"""
        if 'unit' in nodeid:
            return 'unit'
        elif 'integration' in nodeid:
            return 'integration'
        elif 'e2e' in nodeid:
            return 'e2e'
        elif 'performance' in nodeid:
            return 'performance'
        elif 'security' in nodeid:
            return 'security'
        else:
            return 'unknown'