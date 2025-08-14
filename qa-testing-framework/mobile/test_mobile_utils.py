"""
Unit tests for mobile testing utilities.

Tests the AppiumManager, page objects, and mobile utilities to ensure
proper functionality and error handling.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch
from selenium.common.exceptions import TimeoutException, WebDriverException

from .appium_manager import AppiumManager
from .page_objects import BaseMobilePage, AndroidPage, IOSPage, MobileElementActions
from .mobile_utils import (
    MobileGestureUtils, DeviceUtils, NotificationUtils, 
    KeyboardUtils, ScreenUtils, DeviceOrientation, SwipeDirection
)
from ..core.config import ConfigManager


class TestAppiumManager:
    """Test cases for AppiumManager class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Mock(spec=ConfigManager)
        config.get_value.side_effect = lambda key, default=None: {
            'mobile.appium_server': 'http://localhost:4723',
            'mobile.timeout': 10
        }.get(key, default)
        return config
    
    @pytest.fixture
    def appium_manager(self, config):
        """Create AppiumManager instance."""
        return AppiumManager(config)
    
    def test_init(self, appium_manager, config):
        """Test AppiumManager initialization."""
        assert appium_manager.config == config
        assert appium_manager.server_url == 'http://localhost:4723'
        assert appium_manager.implicit_wait == 10
        assert appium_manager.explicit_wait == 30
        assert appium_manager.driver is None
        assert appium_manager.server_process is None
    
    @patch('qa_testing_framework.mobile.appium_manager.subprocess.Popen')
    @patch.object(AppiumManager, '_is_server_running')
    def test_start_appium_server_success(self, mock_is_running, mock_popen, appium_manager):
        """Test successful Appium server start."""
        mock_is_running.side_effect = [False, True]  # Not running, then running
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        result = appium_manager.start_appium_server(4723)
        
        assert result is True
        assert appium_manager.server_process == mock_process
        mock_popen.assert_called_once()
    
    @patch.object(AppiumManager, '_is_server_running')
    def test_start_appium_server_already_running(self, mock_is_running, appium_manager):
        """Test Appium server start when already running."""
        mock_is_running.return_value = True
        
        result = appium_manager.start_appium_server(4723)
        
        assert result is True
    
    @patch('qa_testing_framework.mobile.appium_manager.subprocess.Popen')
    @patch.object(AppiumManager, '_is_server_running')
    def test_start_appium_server_timeout(self, mock_is_running, mock_popen, appium_manager):
        """Test Appium server start timeout."""
        mock_is_running.return_value = False  # Never starts
        mock_popen.return_value = Mock()
        
        result = appium_manager.start_appium_server(4723)
        
        assert result is False
    
    def test_stop_appium_server(self, appium_manager):
        """Test Appium server stop."""
        mock_process = Mock()
        appium_manager.server_process = mock_process
        
        appium_manager.stop_appium_server()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=10)
        assert appium_manager.server_process is None
    
    @patch('qa_testing_framework.mobile.appium_manager.webdriver.Remote')
    def test_create_android_driver(self, mock_webdriver, appium_manager):
        """Test Android driver creation."""
        mock_driver = Mock()
        mock_webdriver.return_value = mock_driver
        
        device_config = {
            'device_name': 'Test Device',
            'platform_version': '11.0',
            'app_package': 'com.test.app',
            'app_activity': '.MainActivity'
        }
        
        result = appium_manager.create_android_driver(device_config)
        
        assert result == mock_driver
        assert appium_manager.driver == mock_driver
        mock_driver.implicitly_wait.assert_called_once_with(10)
    
    @patch('qa_testing_framework.mobile.appium_manager.webdriver.Remote')
    def test_create_ios_driver(self, mock_webdriver, appium_manager):
        """Test iOS driver creation."""
        mock_driver = Mock()
        mock_webdriver.return_value = mock_driver
        
        device_config = {
            'device_name': 'iPhone Simulator',
            'platform_version': '15.0',
            'bundle_id': 'com.test.app'
        }
        
        result = appium_manager.create_ios_driver(device_config)
        
        assert result == mock_driver
        assert appium_manager.driver == mock_driver
        mock_driver.implicitly_wait.assert_called_once_with(10)
    
    def test_quit_driver(self, appium_manager):
        """Test driver quit."""
        mock_driver = Mock()
        appium_manager.driver = mock_driver
        
        appium_manager.quit_driver()
        
        mock_driver.quit.assert_called_once()
        assert appium_manager.driver is None
    
    def test_get_device_info(self, appium_manager):
        """Test getting device information."""
        mock_driver = Mock()
        mock_driver.capabilities = {
            'platformName': 'Android',
            'platformVersion': '11.0',
            'deviceName': 'Test Device'
        }
        appium_manager.driver = mock_driver
        
        info = appium_manager.get_device_info()
        
        assert info['platform_name'] == 'Android'
        assert info['platform_version'] == '11.0'
        assert info['device_name'] == 'Test Device'
    
    def test_is_server_running(self, appium_manager):
        """Test server running check."""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 0  # Success
            
            result = appium_manager._is_server_running(4723)
            
            assert result is True
            mock_sock.connect_ex.assert_called_once_with(('localhost', 4723))
            mock_sock.close.assert_called_once()


class TestBaseMobilePage:
    """Test cases for BaseMobilePage class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        driver = Mock()
        driver.capabilities = {'platformName': 'Android'}
        return driver
    
    @pytest.fixture
    def mobile_page(self, mock_driver):
        """Create test mobile page."""
        class TestMobilePage(BaseMobilePage):
            def is_loaded(self):
                return True
        
        return TestMobilePage(mock_driver)
    
    def test_init(self, mobile_page, mock_driver):
        """Test BaseMobilePage initialization."""
        assert mobile_page.driver == mock_driver
        assert mobile_page.timeout == 30
    
    def test_wait_for_page_load_success(self, mobile_page):
        """Test successful page load wait."""
        result = mobile_page.wait_for_page_load()
        assert result is True
    
    def test_wait_for_page_load_timeout(self, mobile_page):
        """Test page load timeout."""
        mobile_page.is_loaded = Mock(return_value=False)
        
        result = mobile_page.wait_for_page_load(timeout=1)
        assert result is False
    
    @patch('qa_testing_framework.mobile.page_objects.WebDriverWait')
    def test_find_element_success(self, mock_wait, mobile_page):
        """Test successful element finding."""
        mock_element = Mock()
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = mock_element
        
        locator = ('id', 'test_id')
        result = mobile_page.find_element(locator)
        
        assert result == mock_element
    
    @patch('qa_testing_framework.mobile.page_objects.WebDriverWait')
    def test_find_element_timeout(self, mock_wait, mobile_page):
        """Test element finding timeout."""
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException()
        
        locator = ('id', 'test_id')
        
        with pytest.raises(TimeoutException):
            mobile_page.find_element(locator)
    
    def test_is_element_present_true(self, mobile_page):
        """Test element presence check - present."""
        with patch.object(mobile_page, 'find_element'):
            result = mobile_page.is_element_present(('id', 'test_id'))
            assert result is True
    
    def test_is_element_present_false(self, mobile_page):
        """Test element presence check - not present."""
        with patch.object(mobile_page, 'find_element', side_effect=TimeoutException()):
            result = mobile_page.is_element_present(('id', 'test_id'))
            assert result is False


class TestMobileGestureUtils:
    """Test cases for MobileGestureUtils class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        driver = Mock()
        driver.get_window_size.return_value = {'width': 375, 'height': 667}
        return driver
    
    @pytest.fixture
    def gesture_utils(self, mock_driver):
        """Create MobileGestureUtils instance."""
        return MobileGestureUtils(mock_driver)
    
    def test_init(self, gesture_utils, mock_driver):
        """Test MobileGestureUtils initialization."""
        assert gesture_utils.driver == mock_driver
        assert gesture_utils.screen_size == {'width': 375, 'height': 667}
    
    @patch('qa_testing_framework.mobile.mobile_utils.TouchAction')
    def test_tap(self, mock_touch_action, gesture_utils):
        """Test tap gesture."""
        mock_action = Mock()
        mock_touch_action.return_value = mock_action
        
        gesture_utils.tap(100, 200)
        
        mock_touch_action.assert_called_once_with(gesture_utils.driver)
        mock_action.tap.assert_called_once_with(x=100, y=200)
        mock_action.perform.assert_called_once()
    
    @patch('qa_testing_framework.mobile.mobile_utils.TouchAction')
    def test_long_press(self, mock_touch_action, gesture_utils):
        """Test long press gesture."""
        mock_action = Mock()
        mock_touch_action.return_value = mock_action
        
        gesture_utils.long_press(100, 200, 1500)
        
        mock_action.long_press.assert_called_once_with(x=100, y=200, duration=1500)
        mock_action.release.assert_called_once()
        mock_action.perform.assert_called_once()
    
    @patch('qa_testing_framework.mobile.mobile_utils.TouchAction')
    def test_swipe(self, mock_touch_action, gesture_utils):
        """Test swipe gesture."""
        mock_action = Mock()
        mock_touch_action.return_value = mock_action
        
        gesture_utils.swipe(100, 200, 300, 400, 1000)
        
        mock_action.press.assert_called_once_with(x=100, y=200)
        mock_action.wait.assert_called_once_with(1000)
        mock_action.move_to.assert_called_once_with(x=300, y=400)
        mock_action.release.assert_called_once()
        mock_action.perform.assert_called_once()
    
    def test_swipe_screen_up(self, gesture_utils):
        """Test screen swipe up."""
        with patch.object(gesture_utils, 'swipe') as mock_swipe:
            gesture_utils.swipe_screen(SwipeDirection.UP)
            
            # Should swipe from bottom to top
            mock_swipe.assert_called_once()
            args = mock_swipe.call_args[0]
            assert args[1] > args[3]  # start_y > end_y
    
    def test_swipe_screen_down(self, gesture_utils):
        """Test screen swipe down."""
        with patch.object(gesture_utils, 'swipe') as mock_swipe:
            gesture_utils.swipe_screen(SwipeDirection.DOWN)
            
            # Should swipe from top to bottom
            mock_swipe.assert_called_once()
            args = mock_swipe.call_args[0]
            assert args[1] < args[3]  # start_y < end_y


class TestDeviceUtils:
    """Test cases for DeviceUtils class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        return Mock()
    
    @pytest.fixture
    def device_utils(self, mock_driver):
        """Create DeviceUtils instance."""
        return DeviceUtils(mock_driver)
    
    def test_rotate_device(self, device_utils):
        """Test device rotation."""
        device_utils.rotate_device(DeviceOrientation.LANDSCAPE)
        
        device_utils.driver.orientation = DeviceOrientation.LANDSCAPE.value
    
    def test_get_orientation(self, device_utils):
        """Test getting device orientation."""
        device_utils.driver.orientation = 'PORTRAIT'
        
        result = device_utils.get_orientation()
        
        assert result == 'PORTRAIT'
    
    def test_lock_device(self, device_utils):
        """Test device lock."""
        device_utils.lock_device(10)
        
        device_utils.driver.lock.assert_called_once_with(10)
    
    def test_is_device_locked(self, device_utils):
        """Test device lock status check."""
        device_utils.driver.is_locked.return_value = True
        
        result = device_utils.is_device_locked()
        
        assert result is True
        device_utils.driver.is_locked.assert_called_once()
    
    def test_background_app(self, device_utils):
        """Test putting app in background."""
        device_utils.background_app(5)
        
        device_utils.driver.background_app.assert_called_once_with(5)


class TestNotificationUtils:
    """Test cases for NotificationUtils class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        driver = Mock()
        driver.find_elements.return_value = [
            Mock(text="Test notification 1"),
            Mock(text="Test notification 2"),
            Mock(text="")  # Empty text should be filtered
        ]
        return driver
    
    @pytest.fixture
    def notification_utils(self, mock_driver):
        """Create NotificationUtils instance."""
        return NotificationUtils(mock_driver)
    
    def test_open_notifications(self, notification_utils):
        """Test opening notification panel."""
        notification_utils.open_notifications()
        
        notification_utils.driver.open_notifications.assert_called_once()
    
    @patch('time.sleep')
    def test_get_notifications(self, mock_sleep, notification_utils):
        """Test getting notifications."""
        with patch.object(notification_utils, 'open_notifications'):
            notifications = notification_utils.get_notifications()
            
            assert len(notifications) == 2  # Empty text filtered out
            assert notifications[0]['text'] == "Test notification 1"
            assert notifications[1]['text'] == "Test notification 2"
    
    @patch('time.sleep')
    def test_wait_for_notification_found(self, mock_sleep, notification_utils):
        """Test waiting for notification - found."""
        with patch.object(notification_utils, 'get_notifications') as mock_get:
            mock_get.return_value = [{'text': 'Expected notification'}]
            
            result = notification_utils.wait_for_notification('Expected', timeout=5)
            
            assert result is True
    
    @patch('time.sleep')
    def test_wait_for_notification_timeout(self, mock_sleep, notification_utils):
        """Test waiting for notification - timeout."""
        with patch.object(notification_utils, 'get_notifications') as mock_get:
            mock_get.return_value = [{'text': 'Different notification'}]
            
            result = notification_utils.wait_for_notification('Expected', timeout=1)
            
            assert result is False


class TestKeyboardUtils:
    """Test cases for KeyboardUtils class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        return Mock()
    
    @pytest.fixture
    def keyboard_utils(self, mock_driver):
        """Create KeyboardUtils instance."""
        return KeyboardUtils(mock_driver)
    
    def test_is_keyboard_shown(self, keyboard_utils):
        """Test keyboard visibility check."""
        keyboard_utils.driver.is_keyboard_shown.return_value = True
        
        result = keyboard_utils.is_keyboard_shown()
        
        assert result is True
        keyboard_utils.driver.is_keyboard_shown.assert_called_once()
    
    def test_hide_keyboard(self, keyboard_utils):
        """Test hiding keyboard."""
        keyboard_utils.driver.is_keyboard_shown.return_value = True
        
        keyboard_utils.hide_keyboard()
        
        keyboard_utils.driver.hide_keyboard.assert_called_once()
    
    def test_press_key(self, keyboard_utils):
        """Test pressing key by code."""
        keyboard_utils.press_key(4)  # Back key
        
        keyboard_utils.driver.press_keycode.assert_called_once_with(4)


class TestScreenUtils:
    """Test cases for ScreenUtils class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        driver = Mock()
        driver.get_window_size.return_value = {'width': 375, 'height': 667}
        driver.page_source = "<xml>test</xml>"
        return driver
    
    @pytest.fixture
    def screen_utils(self, mock_driver):
        """Create ScreenUtils instance."""
        return ScreenUtils(mock_driver)
    
    def test_get_screen_size(self, screen_utils):
        """Test getting screen size."""
        result = screen_utils.get_screen_size()
        
        assert result == {'width': 375, 'height': 667}
        screen_utils.driver.get_window_size.assert_called_once()
    
    def test_take_screenshot(self, screen_utils):
        """Test taking screenshot."""
        screen_utils.driver.save_screenshot.return_value = True
        
        result = screen_utils.take_screenshot("test.png")
        
        assert "test.png" in result
        screen_utils.driver.save_screenshot.assert_called_once()
    
    def test_get_page_source(self, screen_utils):
        """Test getting page source."""
        result = screen_utils.get_page_source()
        
        assert result == "<xml>test</xml>"
        assert screen_utils.driver.page_source == "<xml>test</xml>"


if __name__ == '__main__':
    pytest.main([__file__])