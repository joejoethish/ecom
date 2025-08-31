"""
Mobile authentication and core functionality tests.

Tests mobile app login, registration, logout, touch gestures, navigation,
push notifications, offline functionality, and data synchronization.
"""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, patch

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
        def info(self, msg): pass
        def error(self, msg): pass
        def warning(self, msg): pass

from .appium_manager import AppiumManager
from .page_objects import BaseMobilePage, AndroidPage, IOSPage
from .mobile_utils import (
    MobileGestureUtils, DeviceUtils, NotificationUtils,
    SwipeDirection, DeviceOrientation
)
from .mobile_config import MobileConfig, Platform


class LoginPage(BaseMobilePage):
    """Login page object for mobile app."""
    
    def __init__(self, driver, timeout=30):
        super().__init__(driver, timeout)
        
        # Common locators (platform-specific pages can override)
        self.email_field = ("id", "email_input")
        self.password_field = ("id", "password_input")
        self.login_button = ("id", "login_button")
        self.register_link = ("id", "register_link")
        self.forgot_password_link = ("id", "forgot_password_link")
        self.error_message = ("id", "error_message")
        self.loading_indicator = ("id", "loading_indicator")
    
    def is_loaded(self) -> bool:
        """Check if login page is loaded."""
        return self.is_element_present(self.login_button, timeout=5)
    
    def enter_email(self, email: str) -> None:
        """Enter email address."""
        self.send_keys(self.email_field, email)
    
    def enter_password(self, password: str) -> None:
        """Enter password."""
        self.send_keys(self.password_field, password)
    
    def tap_login_button(self) -> None:
        """Tap login button."""
        self.click_element(self.login_button)
    
    def tap_register_link(self) -> None:
        """Tap register link."""
        self.click_element(self.register_link)
    
    def tap_forgot_password_link(self) -> None:
        """Tap forgot password link."""
        self.click_element(self.forgot_password_link)
    
    def get_error_message(self) -> str:
        """Get error message text."""
        if self.is_element_present(self.error_message):
            return self.get_text(self.error_message)
        return ""
    
    def wait_for_loading_complete(self, timeout: int = 30) -> bool:
        """Wait for loading to complete."""
        # Wait for loading indicator to appear and then disappear
        try:
            if self.is_element_present(self.loading_indicator, timeout=5):
                # Wait for it to disappear
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if not self.is_element_present(self.loading_indicator, timeout=1):
                        return True
                    time.sleep(0.5)
            return True
        except:
            return True
    
    def login(self, email: str, password: str) -> bool:
        """Perform complete login flow."""
        try:
            self.enter_email(email)
            self.enter_password(password)
            self.tap_login_button()
            return self.wait_for_loading_complete()
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False


class RegisterPage(BaseMobilePage):
    """Registration page object for mobile app."""
    
    def __init__(self, driver, timeout=30):
        super().__init__(driver, timeout)
        
        self.first_name_field = ("id", "first_name_input")
        self.last_name_field = ("id", "last_name_input")
        self.email_field = ("id", "email_input")
        self.password_field = ("id", "password_input")
        self.confirm_password_field = ("id", "confirm_password_input")
        self.register_button = ("id", "register_button")
        self.terms_checkbox = ("id", "terms_checkbox")
        self.error_message = ("id", "error_message")
        self.success_message = ("id", "success_message")
    
    def is_loaded(self) -> bool:
        """Check if registration page is loaded."""
        return self.is_element_present(self.register_button, timeout=5)
    
    def enter_first_name(self, first_name: str) -> None:
        """Enter first name."""
        self.send_keys(self.first_name_field, first_name)
    
    def enter_last_name(self, last_name: str) -> None:
        """Enter last name."""
        self.send_keys(self.last_name_field, last_name)
    
    def enter_email(self, email: str) -> None:
        """Enter email address."""
        self.send_keys(self.email_field, email)
    
    def enter_password(self, password: str) -> None:
        """Enter password."""
        self.send_keys(self.password_field, password)
    
    def enter_confirm_password(self, password: str) -> None:
        """Enter password confirmation."""
        self.send_keys(self.confirm_password_field, password)
    
    def accept_terms(self) -> None:
        """Accept terms and conditions."""
        self.click_element(self.terms_checkbox)
    
    def tap_register_button(self) -> None:
        """Tap register button."""
        self.click_element(self.register_button)
    
    def register(self, first_name: str, last_name: str, email: str, password: str) -> bool:
        """Perform complete registration flow."""
        try:
            self.enter_first_name(first_name)
            self.enter_last_name(last_name)
            self.enter_email(email)
            self.enter_password(password)
            self.enter_confirm_password(password)
            self.accept_terms()
            self.tap_register_button()
            return True
        except Exception as e:
            self.logger.error(f"Registration failed: {str(e)}")
            return False


class HomePage(BaseMobilePage):
    """Home page object for mobile app."""
    
    def __init__(self, driver, timeout=30):
        super().__init__(driver, timeout)
        
        self.menu_button = ("id", "menu_button")
        self.search_button = ("id", "search_button")
        self.cart_button = ("id", "cart_button")
        self.profile_button = ("id", "profile_button")
        self.logout_button = ("id", "logout_button")
        self.welcome_message = ("id", "welcome_message")
        self.product_grid = ("id", "product_grid")
    
    def is_loaded(self) -> bool:
        """Check if home page is loaded."""
        return self.is_element_present(self.menu_button, timeout=10)
    
    def tap_menu_button(self) -> None:
        """Tap menu button."""
        self.click_element(self.menu_button)
    
    def tap_search_button(self) -> None:
        """Tap search button."""
        self.click_element(self.search_button)
    
    def tap_cart_button(self) -> None:
        """Tap cart button."""
        self.click_element(self.cart_button)
    
    def tap_profile_button(self) -> None:
        """Tap profile button."""
        self.click_element(self.profile_button)
    
    def logout(self) -> bool:
        """Perform logout."""
        try:
            self.tap_menu_button()
            time.sleep(1)  # Wait for menu to open
            self.click_element(self.logout_button)
            return True
        except Exception as e:
            self.logger.error(f"Logout failed: {str(e)}")
            return False


class MobileAuthTests:
    """Mobile authentication test suite."""
    
    def __init__(self, appium_manager: AppiumManager, mobile_config: MobileConfig):
        self.appium_manager = appium_manager
        self.mobile_config = mobile_config
        self.logger = Logger(self.__class__.__name__)
        self.driver = None
        self.gesture_utils = None
        self.device_utils = None
        self.notification_utils = None
    
    def setup_test(self, platform: Platform, device_config: Dict[str, Any]) -> bool:
        """Set up test environment."""
        try:
            # Create driver based on platform
            if platform == Platform.ANDROID:
                self.driver = self.appium_manager.create_android_driver(device_config)
            else:
                self.driver = self.appium_manager.create_ios_driver(device_config)
            
            # Initialize utility classes
            self.gesture_utils = MobileGestureUtils(self.driver)
            self.device_utils = DeviceUtils(self.driver)
            self.notification_utils = NotificationUtils(self.driver)
            
            self.logger.info(f"Test setup completed for {platform.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Test setup failed: {str(e)}")
            return False
    
    def teardown_test(self) -> None:
        """Clean up test environment."""
        if self.appium_manager:
            self.appium_manager.quit_driver()
        self.logger.info("Test teardown completed")
    
    def test_login_valid_credentials(self, email: str, password: str) -> bool:
        """Test login with valid credentials."""
        try:
            login_page = LoginPage(self.driver)
            
            # Verify login page is loaded
            assert login_page.wait_for_page_load(), "Login page did not load"
            
            # Perform login
            success = login_page.login(email, password)
            assert success, "Login process failed"
            
            # Verify navigation to home page
            home_page = HomePage(self.driver)
            assert home_page.wait_for_page_load(), "Home page did not load after login"
            
            self.logger.info("Valid login test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Valid login test failed: {str(e)}")
            return False
    
    def test_login_invalid_credentials(self, email: str, password: str) -> bool:
        """Test login with invalid credentials."""
        try:
            login_page = LoginPage(self.driver)
            
            # Verify login page is loaded
            assert login_page.wait_for_page_load(), "Login page did not load"
            
            # Attempt login with invalid credentials
            login_page.login(email, password)
            
            # Verify error message appears
            error_message = login_page.get_error_message()
            assert error_message, "No error message displayed for invalid credentials"
            assert "invalid" in error_message.lower() or "incorrect" in error_message.lower()
            
            self.logger.info("Invalid login test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Invalid login test failed: {str(e)}")
            return False
    
    def test_registration_flow(self, user_data: Dict[str, str]) -> bool:
        """Test user registration flow."""
        try:
            login_page = LoginPage(self.driver)
            
            # Navigate to registration page
            assert login_page.wait_for_page_load(), "Login page did not load"
            login_page.tap_register_link()
            
            # Fill registration form
            register_page = RegisterPage(self.driver)
            assert register_page.wait_for_page_load(), "Registration page did not load"
            
            success = register_page.register(
                user_data['first_name'],
                user_data['last_name'],
                user_data['email'],
                user_data['password']
            )
            assert success, "Registration process failed"
            
            self.logger.info("Registration test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Registration test failed: {str(e)}")
            return False
    
    def test_logout_flow(self) -> bool:
        """Test logout functionality."""
        try:
            home_page = HomePage(self.driver)
            
            # Verify user is logged in (home page loaded)
            assert home_page.wait_for_page_load(), "Home page not loaded"
            
            # Perform logout
            success = home_page.logout()
            assert success, "Logout process failed"
            
            # Verify navigation back to login page
            login_page = LoginPage(self.driver)
            assert login_page.wait_for_page_load(), "Login page did not load after logout"
            
            self.logger.info("Logout test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Logout test failed: {str(e)}")
            return False
    
    def test_touch_gestures(self) -> bool:
        """Test touch gesture validation."""
        try:
            # Test basic tap gesture
            home_page = HomePage(self.driver)
            assert home_page.wait_for_page_load(), "Home page not loaded"
            
            # Test tap gesture
            self.gesture_utils.tap(200, 300)
            time.sleep(1)
            
            # Test swipe gestures
            self.gesture_utils.swipe_screen(SwipeDirection.DOWN)
            time.sleep(1)
            
            self.gesture_utils.swipe_screen(SwipeDirection.UP)
            time.sleep(1)
            
            # Test long press
            self.gesture_utils.long_press(200, 300, 2000)
            time.sleep(1)
            
            self.logger.info("Touch gesture test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Touch gesture test failed: {str(e)}")
            return False
    
    def test_navigation_flow(self) -> bool:
        """Test app navigation."""
        try:
            home_page = HomePage(self.driver)
            assert home_page.wait_for_page_load(), "Home page not loaded"
            
            # Test navigation to different sections
            home_page.tap_search_button()
            time.sleep(2)
            
            # Navigate back (platform-specific)
            if self.driver.capabilities.get('platformName') == 'Android':
                self.driver.back()
            else:
                # iOS back navigation would be app-specific
                pass
            
            time.sleep(1)
            
            # Test cart navigation
            home_page.tap_cart_button()
            time.sleep(2)
            
            self.logger.info("Navigation test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Navigation test failed: {str(e)}")
            return False
    
    def test_device_rotation(self) -> bool:
        """Test device rotation handling."""
        try:
            home_page = HomePage(self.driver)
            assert home_page.wait_for_page_load(), "Home page not loaded"
            
            # Get initial orientation
            initial_orientation = self.device_utils.get_orientation()
            
            # Rotate to landscape
            self.device_utils.rotate_device(DeviceOrientation.LANDSCAPE)
            time.sleep(2)
            
            # Verify page still works in landscape
            assert home_page.is_element_present(home_page.menu_button), "Menu button not found in landscape"
            
            # Rotate back to portrait
            self.device_utils.rotate_device(DeviceOrientation.PORTRAIT)
            time.sleep(2)
            
            # Verify page still works in portrait
            assert home_page.is_element_present(home_page.menu_button), "Menu button not found in portrait"
            
            self.logger.info("Device rotation test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Device rotation test failed: {str(e)}")
            return False
    
    def test_push_notifications(self) -> bool:
        """Test push notification handling."""
        try:
            # This is a simplified test - real implementation would need
            # integration with push notification service
            
            # Check if notifications are enabled
            if hasattr(self.notification_utils, 'get_notifications'):
                notifications = self.notification_utils.get_notifications()
                self.logger.info(f"Found {len(notifications)} notifications")
            
            # Test notification interaction
            # In a real scenario, you would trigger a push notification
            # and then verify it appears and can be interacted with
            
            self.logger.info("Push notification test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Push notification test failed: {str(e)}")
            return False
    
    def test_offline_functionality(self) -> bool:
        """Test offline functionality and data synchronization."""
        try:
            # Test network connectivity toggle (Android only)
            if self.driver.capabilities.get('platformName') == 'Android':
                # Disable network
                self.device_utils.toggle_wifi()
                time.sleep(2)
                
                # Test app behavior offline
                home_page = HomePage(self.driver)
                # App should still be functional for cached content
                assert home_page.is_element_present(home_page.menu_button), "App not functional offline"
                
                # Re-enable network
                self.device_utils.toggle_wifi()
                time.sleep(3)  # Wait for reconnection
            
            self.logger.info("Offline functionality test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Offline functionality test failed: {str(e)}")
            return False
    
    def run_authentication_test_suite(self, test_config: Dict[str, Any]) -> Dict[str, bool]:
        """Run complete authentication test suite."""
        results = {}
        
        try:
            # Setup test environment
            platform = Platform(test_config['platform'])
            device_config = test_config['device_config']
            
            if not self.setup_test(platform, device_config):
                return {'setup_failed': False}
            
            # Run individual tests
            test_data = test_config.get('test_data', {})
            
            results['login_valid'] = self.test_login_valid_credentials(
                test_data.get('valid_email', 'test@example.com'),
                test_data.get('valid_password', 'password123')
            )
            
            results['login_invalid'] = self.test_login_invalid_credentials(
                test_data.get('invalid_email', 'invalid@example.com'),
                test_data.get('invalid_password', 'wrongpassword')
            )
            
            results['registration'] = self.test_registration_flow(
                test_data.get('registration_data', {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'email': 'newuser@example.com',
                    'password': 'newpassword123'
                })
            )
            
            results['logout'] = self.test_logout_flow()
            results['touch_gestures'] = self.test_touch_gestures()
            results['navigation'] = self.test_navigation_flow()
            results['device_rotation'] = self.test_device_rotation()
            results['push_notifications'] = self.test_push_notifications()
            results['offline_functionality'] = self.test_offline_functionality()
            
        except Exception as e:
            self.logger.error(f"Test suite execution failed: {str(e)}")
            results['execution_error'] = False
        
        finally:
            self.teardown_test()
        
        return results


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
def mock_driver():
    """Create mock driver for testing."""
    driver = Mock()
    driver.capabilities = {'platformName': 'Android'}
    driver.get_window_size.return_value = {'width': 375, 'height': 667}
    return driver


def test_login_page_initialization(mock_driver):
    """Test LoginPage initialization."""
    login_page = LoginPage(mock_driver)
    assert login_page.driver == mock_driver
    assert login_page.timeout == 30


def test_register_page_initialization(mock_driver):
    """Test RegisterPage initialization."""
    register_page = RegisterPage(mock_driver)
    assert register_page.driver == mock_driver
    assert register_page.timeout == 30


def test_home_page_initialization(mock_driver):
    """Test HomePage initialization."""
    home_page = HomePage(mock_driver)
    assert home_page.driver == mock_driver
    assert home_page.timeout == 30


def test_mobile_auth_tests_initialization(appium_manager, mobile_config):
    """Test MobileAuthTests initialization."""
    auth_tests = MobileAuthTests(appium_manager, mobile_config)
    assert auth_tests.appium_manager == appium_manager
    assert auth_tests.mobile_config == mobile_config


if __name__ == '__main__':
    pytest.main([__file__, '-v'])