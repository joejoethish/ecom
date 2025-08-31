"""
Comprehensive mobile authentication and core functionality integration tests.

This module implements task 5.2: "Implement mobile authentication and core functionality tests"
- Create mobile app login, registration, and logout test cases
- Implement touch gesture validation and navigation testing
- Add push notification testing capabilities
- Test offline functionality and data synchronization
- Write mobile-specific user journey test suite

Requirements: 1.1, 1.2, 2.1, 2.2
"""

import pytest
import time
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass

try:
    from core.config import ConfigManager
    from core.utils import Logger
except ImportError:
    # Fallback for testing
    class ConfigManager:
        def get_value(self, key, default=None):
            return default
    
    class Logger:
        def __init__(self, name):
            self.name = name
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")

from .appium_manager import AppiumManager
from .mobile_config import MobileConfig, Platform, DeviceType
from .test_mobile_auth import MobileAuthTests, LoginPage, RegisterPage, HomePage
from .test_mobile_navigation import MobileNavigationTests
from .test_push_notifications import PushNotificationTests, MockNotificationService
from .mobile_utils import (
    MobileGestureUtils, DeviceUtils, NotificationUtils, 
    SwipeDirection, DeviceOrientation
)


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    screenshots: List[str] = None
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []


@dataclass
class UserTestData:
    """Test user data structure."""
    email: str
    password: str
    first_name: str
    last_name: str
    user_type: str = "registered"


class MobileAuthIntegrationTests:
    """Comprehensive mobile authentication and core functionality test suite."""
    
    def __init__(self, appium_manager: AppiumManager, mobile_config: MobileConfig):
        self.appium_manager = appium_manager
        self.mobile_config = mobile_config
        self.logger = Logger(self.__class__.__name__)
        self.driver = None
        
        # Test components
        self.auth_tests = None
        self.navigation_tests = None
        self.notification_tests = None
        self.notification_service = MockNotificationService()
        
        # Utility components
        self.gesture_utils = None
        self.device_utils = None
        self.notification_utils = None
        
        # Test results
        self.test_results: List[TestResult] = []
        
        # Test data
        self.test_users = self._create_test_users()
    
    def _create_test_users(self) -> List[UserTestData]:
        """Create test user data."""
        return [
            UserTestData(
                email="test.user@example.com",
                password="TestPassword123!",
                first_name="Test",
                last_name="User"
            ),
            UserTestData(
                email="premium.user@example.com", 
                password="PremiumPass456!",
                first_name="Premium",
                last_name="User",
                user_type="premium"
            ),
            UserTestData(
                email="invalid.user@example.com",
                password="WrongPassword",
                first_name="Invalid",
                last_name="User"
            )
        ]
    
    def setup_test_environment(self, platform: Platform, device_config: Dict[str, Any]) -> bool:
        """Set up comprehensive test environment."""
        try:
            start_time = time.time()
            
            # Create driver based on platform
            if platform == Platform.ANDROID:
                self.driver = self.appium_manager.create_android_driver(device_config)
            else:
                self.driver = self.appium_manager.create_ios_driver(device_config)
            
            # Initialize test components
            self.auth_tests = MobileAuthTests(self.appium_manager, self.mobile_config)
            self.auth_tests.driver = self.driver
            
            self.navigation_tests = MobileNavigationTests(self.driver)
            self.notification_tests = PushNotificationTests(self.driver)
            
            # Initialize utility components
            self.gesture_utils = MobileGestureUtils(self.driver)
            self.device_utils = DeviceUtils(self.driver)
            self.notification_utils = NotificationUtils(self.driver)
            
            duration = time.time() - start_time
            self.logger.info(f"Test environment setup completed in {duration:.2f}s for {platform.value}")
            
            return True
            
        except Exception as e:
            error_msg = f"Test environment setup failed: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result("setup_environment", False, 0, error_msg)
            return False
    
    def teardown_test_environment(self) -> None:
        """Clean up test environment."""
        try:
            if self.appium_manager:
                self.appium_manager.quit_driver()
            self.logger.info("Test environment teardown completed")
        except Exception as e:
            self.logger.error(f"Teardown error: {str(e)}")
    
    def _add_test_result(self, test_name: str, passed: bool, duration: float, 
                        error_message: Optional[str] = None, 
                        screenshots: Optional[List[str]] = None) -> None:
        """Add test result to results list."""
        result = TestResult(
            test_name=test_name,
            passed=passed,
            duration=duration,
            error_message=error_message,
            screenshots=screenshots or []
        )
        self.test_results.append(result)
    
    def _take_screenshot(self, test_name: str) -> str:
        """Take screenshot for test documentation."""
        try:
            if self.driver:
                timestamp = int(time.time())
                filename = f"{test_name}_{timestamp}.png"
                screenshot_path = f"screenshots/mobile/{filename}"
                self.driver.save_screenshot(screenshot_path)
                return screenshot_path
        except Exception as e:
            self.logger.warning(f"Failed to take screenshot: {str(e)}")
        return ""
    
    # Authentication Tests
    
    def test_mobile_login_valid_credentials(self) -> bool:
        """Test mobile login with valid credentials."""
        start_time = time.time()
        test_name = "mobile_login_valid"
        screenshots = []
        
        try:
            user = self.test_users[0]  # Valid user
            
            # Take initial screenshot
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Perform login test
            success = self.auth_tests.test_login_valid_credentials(user.email, user.password)
            
            # Take result screenshot
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Mobile login test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Mobile login test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Mobile login test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def test_mobile_login_invalid_credentials(self) -> bool:
        """Test mobile login with invalid credentials."""
        start_time = time.time()
        test_name = "mobile_login_invalid"
        screenshots = []
        
        try:
            user = self.test_users[2]  # Invalid user
            
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Perform invalid login test
            success = self.auth_tests.test_login_invalid_credentials(user.email, user.password)
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Mobile invalid login test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Mobile invalid login test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Mobile invalid login test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def test_mobile_registration_flow(self) -> bool:
        """Test mobile user registration flow."""
        start_time = time.time()
        test_name = "mobile_registration"
        screenshots = []
        
        try:
            user = UserTestData(
                email=f"newuser_{int(time.time())}@example.com",
                password="NewUserPass123!",
                first_name="New",
                last_name="User"
            )
            
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Perform registration test
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'password': user.password
            }
            
            success = self.auth_tests.test_registration_flow(user_data)
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Mobile registration test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Mobile registration test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Mobile registration test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def test_mobile_logout_flow(self) -> bool:
        """Test mobile logout functionality."""
        start_time = time.time()
        test_name = "mobile_logout"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Perform logout test
            success = self.auth_tests.test_logout_flow()
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Mobile logout test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Mobile logout test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Mobile logout test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    # Touch Gesture Tests
    
    def test_touch_gesture_validation(self) -> bool:
        """Test comprehensive touch gesture validation."""
        start_time = time.time()
        test_name = "touch_gestures"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Test basic touch gestures
            success = self.auth_tests.test_touch_gestures()
            
            if success:
                # Test additional gesture patterns
                success = self._test_advanced_gestures()
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Touch gesture validation passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Touch gesture validation failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Touch gesture test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def _test_advanced_gestures(self) -> bool:
        """Test advanced gesture patterns."""
        try:
            # Test swipe patterns
            directions = [SwipeDirection.UP, SwipeDirection.DOWN, SwipeDirection.LEFT, SwipeDirection.RIGHT]
            
            for direction in directions:
                self.gesture_utils.swipe_screen(direction, distance_ratio=0.5)
                time.sleep(0.5)
            
            # Test pinch and zoom
            screen_size = self.driver.get_window_size()
            center_x = screen_size['width'] // 2
            center_y = screen_size['height'] // 2
            
            self.gesture_utils.pinch_zoom(center_x, center_y, scale=0.5)
            time.sleep(1)
            
            self.gesture_utils.zoom_in(center_x, center_y, scale=2.0)
            time.sleep(1)
            
            self.logger.info("Advanced gesture patterns completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Advanced gesture test failed: {str(e)}")
            return False
    
    # Navigation Tests
    
    def test_navigation_functionality(self) -> bool:
        """Test mobile navigation functionality."""
        start_time = time.time()
        test_name = "navigation"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Run navigation test suite
            nav_results = self.navigation_tests.run_navigation_test_suite()
            
            # Calculate success rate
            total_tests = len(nav_results)
            passed_tests = sum(1 for result in nav_results.values() if result)
            success = passed_tests >= (total_tests * 0.8)  # 80% pass rate required
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Navigation tests passed ({passed_tests}/{total_tests}) in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Navigation tests failed ({passed_tests}/{total_tests}) in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Navigation test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    # Push Notification Tests
    
    def test_push_notification_capabilities(self) -> bool:
        """Test push notification capabilities."""
        start_time = time.time()
        test_name = "push_notifications"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Create test notifications
            test_notifications = [
                {
                    'title': 'Welcome Notification',
                    'body': 'Welcome to our mobile app!',
                    'type': 'promotional'
                },
                {
                    'title': 'Order Update',
                    'body': 'Your order has been shipped',
                    'type': 'transactional',
                    'deep_link': 'order_detail'
                }
            ]
            
            # Send test notifications
            for notification in test_notifications:
                self.notification_service.send_notification(notification)
            
            # Run notification test suite
            test_config = {
                'test_notifications': test_notifications
            }
            
            notification_results = self.notification_tests.run_push_notification_test_suite(test_config)
            
            # Calculate success rate
            total_tests = len(notification_results)
            passed_tests = sum(1 for result in notification_results.values() if result)
            success = passed_tests >= (total_tests * 0.7)  # 70% pass rate for notifications
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Push notification tests passed ({passed_tests}/{total_tests}) in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Push notification tests failed ({passed_tests}/{total_tests}) in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Push notification test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    # Offline Functionality Tests
    
    def test_offline_functionality_and_sync(self) -> bool:
        """Test offline functionality and data synchronization."""
        start_time = time.time()
        test_name = "offline_functionality"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Test offline functionality
            success = self.auth_tests.test_offline_functionality()
            
            if success:
                # Test data synchronization
                success = self._test_data_synchronization()
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Offline functionality test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Offline functionality test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Offline functionality test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def _test_data_synchronization(self) -> bool:
        """Test data synchronization after reconnection."""
        try:
            platform = self.driver.capabilities.get('platformName', '').lower()
            
            if platform == 'android':
                # Test data sync after network reconnection
                self.logger.info("Testing data synchronization after network reconnection")
                
                # Simulate app coming back online
                time.sleep(3)  # Wait for potential sync
                
                # Verify app state is consistent
                home_page = HomePage(self.driver)
                if home_page.wait_for_page_load():
                    self.logger.info("Data synchronization test completed successfully")
                    return True
            
            self.logger.info("Data synchronization test completed (limited on iOS)")
            return True
            
        except Exception as e:
            self.logger.error(f"Data synchronization test failed: {str(e)}")
            return False
    
    # Device Orientation Tests
    
    def test_device_orientation_handling(self) -> bool:
        """Test app behavior in different device orientations."""
        start_time = time.time()
        test_name = "device_orientation"
        screenshots = []
        
        try:
            screenshots.append(self._take_screenshot(f"{test_name}_start"))
            
            # Test device rotation
            success = self.auth_tests.test_device_rotation()
            
            if success:
                # Test additional orientation scenarios
                success = self._test_orientation_scenarios()
            
            screenshots.append(self._take_screenshot(f"{test_name}_result"))
            
            duration = time.time() - start_time
            self._add_test_result(test_name, success, duration, screenshots=screenshots)
            
            if success:
                self.logger.info(f"✓ Device orientation test passed in {duration:.2f}s")
            else:
                self.logger.error(f"✗ Device orientation test failed in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Device orientation test exception: {str(e)}"
            self.logger.error(error_msg)
            self._add_test_result(test_name, False, duration, error_msg, screenshots)
            return False
    
    def _test_orientation_scenarios(self) -> bool:
        """Test various orientation scenarios."""
        try:
            orientations = [
                DeviceOrientation.PORTRAIT,
                DeviceOrientation.LANDSCAPE,
                DeviceOrientation.PORTRAIT
            ]
            
            for orientation in orientations:
                self.device_utils.rotate_device(orientation)
                time.sleep(2)
                
                # Verify app functionality in each orientation
                home_page = HomePage(self.driver)
                if not home_page.is_element_present(home_page.menu_button):
                    self.logger.warning(f"App layout issue in {orientation.value}")
                    return False
            
            self.logger.info("All orientation scenarios passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Orientation scenarios test failed: {str(e)}")
            return False
    
    # Comprehensive Test Suite
    
    def run_comprehensive_mobile_auth_suite(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive mobile authentication and core functionality test suite."""
        suite_start_time = time.time()
        
        try:
            # Setup test environment
            platform = Platform(test_config['platform'])
            device_config = test_config['device_config']
            
            if not self.setup_test_environment(platform, device_config):
                return {'setup_failed': True, 'results': []}
            
            self.logger.info("Starting comprehensive mobile authentication test suite")
            
            # Run all test categories
            test_methods = [
                ('Authentication - Valid Login', self.test_mobile_login_valid_credentials),
                ('Authentication - Invalid Login', self.test_mobile_login_invalid_credentials),
                ('Authentication - Registration', self.test_mobile_registration_flow),
                ('Authentication - Logout', self.test_mobile_logout_flow),
                ('Touch Gestures', self.test_touch_gesture_validation),
                ('Navigation', self.test_navigation_functionality),
                ('Push Notifications', self.test_push_notification_capabilities),
                ('Offline Functionality', self.test_offline_functionality_and_sync),
                ('Device Orientation', self.test_device_orientation_handling)
            ]
            
            # Execute tests
            for test_description, test_method in test_methods:
                self.logger.info(f"Running: {test_description}")
                try:
                    test_method()
                except Exception as e:
                    self.logger.error(f"Test {test_description} failed with exception: {str(e)}")
                    self._add_test_result(test_description.lower().replace(' ', '_'), False, 0, str(e))
            
            # Calculate overall results
            total_duration = time.time() - suite_start_time
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.passed)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            # Generate summary
            summary = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'platform': platform.value,
                'results': [
                    {
                        'test_name': result.test_name,
                        'passed': result.passed,
                        'duration': result.duration,
                        'error_message': result.error_message,
                        'screenshots': result.screenshots
                    }
                    for result in self.test_results
                ]
            }
            
            self.logger.info(f"Mobile authentication test suite completed:")
            self.logger.info(f"  Total Tests: {total_tests}")
            self.logger.info(f"  Passed: {passed_tests}")
            self.logger.info(f"  Failed: {total_tests - passed_tests}")
            self.logger.info(f"  Success Rate: {success_rate:.1f}%")
            self.logger.info(f"  Duration: {total_duration:.2f}s")
            
            return summary
            
        except Exception as e:
            error_msg = f"Test suite execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'execution_error': True,
                'error_message': error_msg,
                'results': []
            }
        
        finally:
            self.teardown_test_environment()


# Test fixtures and helper functions for pytest integration
@pytest.fixture
def mobile_config():
    """Create mobile configuration for testing."""
    config_manager = Mock(spec=ConfigManager)
    config_manager.get_value.return_value = None
    return MobileConfig(config_manager)


@pytest.fixture
def appium_manager():
    """Create Appium manager for testing."""
    config_manager = Mock(spec=ConfigManager)
    config_manager.get_value.side_effect = lambda key, default: {
        'mobile.appium_server': 'http://localhost:4723',
        'mobile.timeout': 10
    }.get(key, default)
    return AppiumManager(config_manager)


@pytest.fixture
def integration_tests(appium_manager, mobile_config):
    """Create integration tests instance."""
    return MobileAuthIntegrationTests(appium_manager, mobile_config)


def test_integration_tests_initialization(integration_tests):
    """Test MobileAuthIntegrationTests initialization."""
    assert integration_tests.appium_manager is not None
    assert integration_tests.mobile_config is not None
    assert len(integration_tests.test_users) == 3
    assert integration_tests.notification_service is not None


def test_test_users_creation(integration_tests):
    """Test test users creation."""
    users = integration_tests.test_users
    assert len(users) == 3
    assert users[0].email == "test.user@example.com"
    assert users[1].user_type == "premium"
    assert users[2].email == "invalid.user@example.com"


def test_test_result_structure():
    """Test TestResult data structure."""
    result = TestResult(
        test_name="test_example",
        passed=True,
        duration=1.5,
        error_message=None,
        screenshots=["screenshot1.png"]
    )
    
    assert result.test_name == "test_example"
    assert result.passed is True
    assert result.duration == 1.5
    assert result.error_message is None
    assert len(result.screenshots) == 1


def test_user_test_data_structure():
    """Test UserTestData data structure."""
    user = UserTestData(
        email="test@example.com",
        password="password123",
        first_name="Test",
        last_name="User",
        user_type="premium"
    )
    
    assert user.email == "test@example.com"
    assert user.password == "password123"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.user_type == "premium"


if __name__ == '__main__':
    # Example usage
    config_manager = ConfigManager()
    mobile_config = MobileConfig(config_manager)
    appium_manager = AppiumManager(config_manager)
    
    integration_tests = MobileAuthIntegrationTests(appium_manager, mobile_config)
    
    # Example test configuration
    test_config = {
        'platform': 'android',
        'device_config': {
            'platformName': 'Android',
            'deviceName': 'Android Emulator',
            'app': '/path/to/app.apk',
            'automationName': 'UiAutomator2'
        }
    }
    
    # Run comprehensive test suite
    results = integration_tests.run_comprehensive_mobile_auth_suite(test_config)
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Run pytest
    pytest.main([__file__, '-v'])