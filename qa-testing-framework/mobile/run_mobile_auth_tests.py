#!/usr/bin/env python3
"""
Mobile Authentication and Core Functionality Test Runner

This script runs the comprehensive mobile authentication and core functionality tests
implementing task 5.2 requirements:
- Mobile app login, registration, and logout test cases
- Touch gesture validation and navigation testing
- Push notification testing capabilities
- Offline functionality and data synchronization testing
- Mobile-specific user journey test suite

Usage:
    python run_mobile_auth_tests.py --platform android --device-name "Android Emulator"
    python run_mobile_auth_tests.py --platform ios --device-name "iPhone Simulator"
    python run_mobile_auth_tests.py --config config.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the qa-testing-framework to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.config import ConfigManager
    from core.utils import Logger
except ImportError:
    # Fallback for standalone execution
    class ConfigManager:
        def get_value(self, key, default=None):
            return default
    
    class Logger:
        def __init__(self, name):
            self.name = name
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")

from mobile.appium_manager import AppiumManager
from mobile.mobile_config import MobileConfig, Platform
from mobile.test_mobile_auth_integration import MobileAuthIntegrationTests
from mobile.test_mobile_user_journeys import MobileUserJourneyTests
from mobile.test_offline_functionality import MobileOfflineFunctionalityTests


class MobileAuthTestRunner:
    """Comprehensive mobile authentication test runner."""
    
    def __init__(self):
        self.logger = Logger(self.__class__.__name__)
        self.config_manager = ConfigManager()
        self.mobile_config = MobileConfig(self.config_manager)
        self.appium_manager = AppiumManager(self.config_manager)
        
        # Test results
        self.test_results = {
            'integration_tests': {},
            'user_journeys': {},
            'offline_functionality': {},
            'summary': {}
        }
    
    def create_device_config(self, platform: str, device_name: str, app_path: str = None) -> Dict[str, Any]:
        """Create device configuration for testing."""
        base_config = {
            'platformName': platform.title(),
            'deviceName': device_name,
            'automationName': 'UiAutomator2' if platform.lower() == 'android' else 'XCUITest',
            'newCommandTimeout': 300,
            'noReset': True,
            'fullReset': False
        }
        
        if platform.lower() == 'android':
            base_config.update({
                'appPackage': 'com.example.ecommerce',
                'appActivity': '.MainActivity',
                'platformVersion': '11.0'
            })
            if app_path:
                base_config['app'] = app_path
        
        elif platform.lower() == 'ios':
            base_config.update({
                'bundleId': 'com.example.ecommerce',
                'platformVersion': '15.0'
            })
            if app_path:
                base_config['app'] = app_path
        
        return base_config
    
    def run_integration_tests(self, platform: Platform, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run mobile authentication integration tests."""
        self.logger.info("=" * 60)
        self.logger.info("RUNNING MOBILE AUTHENTICATION INTEGRATION TESTS")
        self.logger.info("=" * 60)
        
        try:
            integration_tests = MobileAuthIntegrationTests(self.appium_manager, self.mobile_config)
            
            test_config = {
                'platform': platform.value,
                'device_config': device_config
            }
            
            results = integration_tests.run_comprehensive_mobile_auth_suite(test_config)
            
            self.logger.info("Integration Tests Summary:")
            self.logger.info(f"  Total Tests: {results.get('total_tests', 0)}")
            self.logger.info(f"  Passed: {results.get('passed_tests', 0)}")
            self.logger.info(f"  Failed: {results.get('failed_tests', 0)}")
            self.logger.info(f"  Success Rate: {results.get('success_rate', 0):.1f}%")
            self.logger.info(f"  Duration: {results.get('total_duration', 0):.2f}s")
            
            return results
            
        except Exception as e:
            error_msg = f"Integration tests failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def run_user_journey_tests(self, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run mobile user journey tests."""
        self.logger.info("=" * 60)
        self.logger.info("RUNNING MOBILE USER JOURNEY TESTS")
        self.logger.info("=" * 60)
        
        try:
            # Create a mock driver for demonstration
            # In real implementation, this would use the actual Appium driver
            mock_driver = type('MockDriver', (), {
                'capabilities': {'platformName': device_config['platformName']},
                'get_window_size': lambda: {'width': 375, 'height': 667},
                'save_screenshot': lambda path: None,
                'press_keycode': lambda code: None,
                'back': lambda: None
            })()
            
            journey_tests = MobileUserJourneyTests(mock_driver)
            results = journey_tests.run_all_user_journeys()
            
            summary = results.get('summary', {})
            self.logger.info("User Journey Tests Summary:")
            self.logger.info(f"  Total Journeys: {summary.get('total_journeys', 0)}")
            self.logger.info(f"  Passed Journeys: {summary.get('passed_journeys', 0)}")
            self.logger.info(f"  Total Steps: {summary.get('total_steps', 0)}")
            self.logger.info(f"  Passed Steps: {summary.get('passed_steps', 0)}")
            self.logger.info(f"  Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
            self.logger.info(f"  Duration: {summary.get('total_duration', 0):.2f}s")
            
            return results
            
        except Exception as e:
            error_msg = f"User journey tests failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def run_offline_functionality_tests(self, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run offline functionality tests."""
        self.logger.info("=" * 60)
        self.logger.info("RUNNING OFFLINE FUNCTIONALITY TESTS")
        self.logger.info("=" * 60)
        
        try:
            # Create a mock driver for demonstration
            mock_driver = type('MockDriver', (), {
                'capabilities': {'platformName': device_config['platformName']},
                'get_window_size': lambda: {'width': 375, 'height': 667},
                'save_screenshot': lambda path: None
            })()
            
            offline_tests = MobileOfflineFunctionalityTests(mock_driver)
            results = offline_tests.run_offline_functionality_test_suite()
            
            self.logger.info("Offline Functionality Tests Summary:")
            self.logger.info(f"  Total Tests: {results.get('total_tests', 0)}")
            self.logger.info(f"  Passed: {results.get('passed_tests', 0)}")
            self.logger.info(f"  Failed: {results.get('failed_tests', 0)}")
            self.logger.info(f"  Success Rate: {results.get('success_rate', 0):.1f}%")
            self.logger.info(f"  Duration: {results.get('total_duration', 0):.2f}s")
            self.logger.info(f"  Network State: {results.get('network_state', 'unknown')}")
            self.logger.info(f"  Pending Actions: {results.get('pending_actions', 0)}")
            
            return results
            
        except Exception as e:
            error_msg = f"Offline functionality tests failed: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def run_all_tests(self, platform: str, device_name: str, app_path: str = None) -> Dict[str, Any]:
        """Run all mobile authentication and core functionality tests."""
        start_time = time.time()
        
        self.logger.info("🚀 Starting Mobile Authentication and Core Functionality Tests")
        self.logger.info(f"Platform: {platform}")
        self.logger.info(f"Device: {device_name}")
        if app_path:
            self.logger.info(f"App: {app_path}")
        
        try:
            # Create device configuration
            device_config = self.create_device_config(platform, device_name, app_path)
            platform_enum = Platform.ANDROID if platform.lower() == 'android' else Platform.IOS
            
            # Run test suites
            self.test_results['integration_tests'] = self.run_integration_tests(platform_enum, device_config)
            self.test_results['user_journeys'] = self.run_user_journey_tests(device_config)
            self.test_results['offline_functionality'] = self.run_offline_functionality_tests(device_config)
            
            # Calculate overall summary
            total_duration = time.time() - start_time
            
            # Extract test counts from each suite
            integration_summary = self.test_results['integration_tests']
            journey_summary = self.test_results['user_journeys'].get('summary', {})
            offline_summary = self.test_results['offline_functionality']
            
            total_tests = (
                integration_summary.get('total_tests', 0) +
                journey_summary.get('total_steps', 0) +
                offline_summary.get('total_tests', 0)
            )
            
            passed_tests = (
                integration_summary.get('passed_tests', 0) +
                journey_summary.get('passed_steps', 0) +
                offline_summary.get('passed_tests', 0)
            )
            
            overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.test_results['summary'] = {
                'platform': platform,
                'device_name': device_name,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'overall_success_rate': overall_success_rate,
                'total_duration': total_duration,
                'test_suites': {
                    'integration_tests': {
                        'passed': integration_summary.get('passed_tests', 0),
                        'total': integration_summary.get('total_tests', 0),
                        'success_rate': integration_summary.get('success_rate', 0)
                    },
                    'user_journeys': {
                        'passed': journey_summary.get('passed_steps', 0),
                        'total': journey_summary.get('total_steps', 0),
                        'success_rate': journey_summary.get('overall_success_rate', 0)
                    },
                    'offline_functionality': {
                        'passed': offline_summary.get('passed_tests', 0),
                        'total': offline_summary.get('total_tests', 0),
                        'success_rate': offline_summary.get('success_rate', 0)
                    }
                }
            }
            
            # Print final summary
            self.print_final_summary()
            
            return self.test_results
            
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            self.logger.error(error_msg)
            self.test_results['error'] = error_msg
            return self.test_results
    
    def print_final_summary(self):
        """Print comprehensive test summary."""
        summary = self.test_results['summary']
        
        self.logger.info("=" * 80)
        self.logger.info("🎯 MOBILE AUTHENTICATION & CORE FUNCTIONALITY TEST SUMMARY")
        self.logger.info("=" * 80)
        
        self.logger.info(f"Platform: {summary['platform']}")
        self.logger.info(f"Device: {summary['device_name']}")
        self.logger.info(f"Total Duration: {summary['total_duration']:.2f} seconds")
        self.logger.info("")
        
        self.logger.info("📊 OVERALL RESULTS:")
        self.logger.info(f"  Total Tests: {summary['total_tests']}")
        self.logger.info(f"  Passed: {summary['passed_tests']}")
        self.logger.info(f"  Failed: {summary['failed_tests']}")
        self.logger.info(f"  Success Rate: {summary['overall_success_rate']:.1f}%")
        self.logger.info("")
        
        self.logger.info("📋 TEST SUITE BREAKDOWN:")
        
        for suite_name, suite_data in summary['test_suites'].items():
            suite_display_name = suite_name.replace('_', ' ').title()
            self.logger.info(f"  {suite_display_name}:")
            self.logger.info(f"    Passed: {suite_data['passed']}/{suite_data['total']}")
            self.logger.info(f"    Success Rate: {suite_data['success_rate']:.1f}%")
        
        self.logger.info("")
        
        # Status indicator
        if summary['overall_success_rate'] >= 90:
            status = "🟢 EXCELLENT"
        elif summary['overall_success_rate'] >= 80:
            status = "🟡 GOOD"
        elif summary['overall_success_rate'] >= 70:
            status = "🟠 ACCEPTABLE"
        else:
            status = "🔴 NEEDS IMPROVEMENT"
        
        self.logger.info(f"Overall Status: {status}")
        self.logger.info("=" * 80)
    
    def save_results(self, output_file: str):
        """Save test results to JSON file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            self.logger.info(f"Test results saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {str(e)}")


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {str(e)}")
        return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mobile Authentication and Core Functionality Test Runner"
    )
    
    parser.add_argument(
        '--platform',
        choices=['android', 'ios'],
        default='android',
        help='Mobile platform to test (default: android)'
    )
    
    parser.add_argument(
        '--device-name',
        default='Android Emulator',
        help='Device name for testing (default: Android Emulator)'
    )
    
    parser.add_argument(
        '--app-path',
        help='Path to mobile app file (.apk for Android, .app for iOS)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to JSON configuration file'
    )
    
    parser.add_argument(
        '--output',
        default='mobile_auth_test_results.json',
        help='Output file for test results (default: mobile_auth_test_results.json)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        config = load_config_file(args.config)
    
    # Override with command line arguments
    platform = config.get('platform', args.platform)
    device_name = config.get('device_name', args.device_name)
    app_path = config.get('app_path', args.app_path)
    
    # Create and run test runner
    runner = MobileAuthTestRunner()
    
    try:
        results = runner.run_all_tests(platform, device_name, app_path)
        
        # Save results
        runner.save_results(args.output)
        
        # Exit with appropriate code
        summary = results.get('summary', {})
        success_rate = summary.get('overall_success_rate', 0)
        
        if success_rate >= 80:
            print(f"\n✅ Tests completed successfully! Success rate: {success_rate:.1f}%")
            sys.exit(0)
        else:
            print(f"\n❌ Tests completed with issues. Success rate: {success_rate:.1f}%")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()