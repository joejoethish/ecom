"""
Unit Tests for WebDriver Manager

Tests the WebDriver management functionality including browser
initialization, configuration, and lifecycle management.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

from ..core.interfaces import Environment
from ..core.models import BrowserInfo
from .webdriver_manager import WebDriverManager


class TestWebDriverManager(unittest.TestCase):
    """Test cases for WebDriverManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = WebDriverManager(Environment.TESTING)
        self.mock_driver = Mock(spec=WebDriver)
        
        # Mock driver capabilities
        self.mock_driver.capabilities = {
            "browserName": "chrome",
            "browserVersion": "91.0.4472.124",
            "platformName": "Windows 10"
        }
        
        # Mock driver methods
        self.mock_driver.execute_script.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        self.mock_driver.save_screenshot.return_value = True
        self.mock_driver.quit.return_value = None
    
    def tearDown(self):
        """Clean up after tests"""
        self.manager.close_all_drivers()
    
    def test_init(self):
        """Test WebDriverManager initialization"""
        manager = WebDriverManager(Environment.DEVELOPMENT)
        
        self.assertEqual(manager.environment, Environment.DEVELOPMENT)
        self.assertIsNotNone(manager.config)
        self.assertEqual(manager.active_drivers, {})
        self.assertIsNotNone(manager.logger)
        self.assertIsNotNone(manager.error_handler)
        self.assertTrue(manager.screenshot_dir.exists())
    
    def test_supported_browsers(self):
        """Test supported browsers list"""
        expected_browsers = ["chrome", "firefox", "edge", "safari"]
        self.assertEqual(WebDriverManager.SUPPORTED_BROWSERS, expected_browsers)
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_create_chrome_driver(self, mock_chrome_manager, mock_chrome):
        """Test Chrome WebDriver creation"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_chrome.return_value = self.mock_driver
        
        driver = self.manager.create_driver("chrome")
        
        self.assertEqual(driver, self.mock_driver)
        self.assertTrue(len(self.manager.active_drivers) == 1)
        mock_chrome.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_create_chrome_driver_headless(self, mock_chrome_manager, mock_chrome):
        """Test Chrome WebDriver creation in headless mode"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_chrome.return_value = self.mock_driver
        
        driver = self.manager.create_driver("chrome", headless=True)
        
        self.assertEqual(driver, self.mock_driver)
        mock_chrome.assert_called_once()
        
        # Check that headless argument was added to options
        call_args = mock_chrome.call_args
        options = call_args[1]['options']
        self.assertIn('--headless', options.arguments)
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Firefox')
    @patch('qa_testing_framework.web.webdriver_manager.GeckoDriverManager')
    def test_create_firefox_driver(self, mock_gecko_manager, mock_firefox):
        """Test Firefox WebDriver creation"""
        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"
        mock_firefox.return_value = self.mock_driver
        
        driver = self.manager.create_driver("firefox")
        
        self.assertEqual(driver, self.mock_driver)
        self.assertTrue(len(self.manager.active_drivers) == 1)
        mock_firefox.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Edge')
    @patch('qa_testing_framework.web.webdriver_manager.EdgeChromiumDriverManager')
    def test_create_edge_driver(self, mock_edge_manager, mock_edge):
        """Test Edge WebDriver creation"""
        mock_edge_manager.return_value.install.return_value = "/path/to/edgedriver"
        mock_edge.return_value = self.mock_driver
        
        driver = self.manager.create_driver("edge")
        
        self.assertEqual(driver, self.mock_driver)
        self.assertTrue(len(self.manager.active_drivers) == 1)
        mock_edge.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Safari')
    def test_create_safari_driver(self, mock_safari):
        """Test Safari WebDriver creation"""
        mock_safari.return_value = self.mock_driver
        
        driver = self.manager.create_driver("safari")
        
        self.assertEqual(driver, self.mock_driver)
        self.assertTrue(len(self.manager.active_drivers) == 1)
        mock_safari.assert_called_once()
    
    def test_create_driver_unsupported_browser(self):
        """Test creating driver for unsupported browser"""
        with self.assertRaises(ValueError) as context:
            self.manager.create_driver("internet_explorer")
        
        self.assertIn("Unsupported browser", str(context.exception))
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_create_driver_with_custom_options(self, mock_chrome_manager, mock_chrome):
        """Test creating driver with custom options"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_chrome.return_value = self.mock_driver
        
        custom_options = {
            "window_size": "1366,768",
            "user_agent": "Custom User Agent",
            "download_dir": "/custom/download/path",
            "chrome_options": ["--disable-notifications"]
        }
        
        driver = self.manager.create_driver("chrome", **custom_options)
        
        self.assertEqual(driver, self.mock_driver)
        mock_chrome.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_create_driver_failure(self, mock_chrome_manager, mock_chrome):
        """Test driver creation failure handling"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_chrome.side_effect = Exception("Driver creation failed")
        
        with self.assertRaises(WebDriverException) as context:
            self.manager.create_driver("chrome")
        
        self.assertIn("Failed to create chrome WebDriver", str(context.exception))
    
    def test_get_browser_info(self):
        """Test getting browser information"""
        # Mock viewport size script execution
        self.mock_driver.execute_script.side_effect = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",  # user agent
            {"width": 1920, "height": 1080}  # viewport size
        ]
        
        browser_info = self.manager.get_browser_info(self.mock_driver)
        
        self.assertIsInstance(browser_info, BrowserInfo)
        self.assertEqual(browser_info.name, "chrome")
        self.assertEqual(browser_info.version, "91.0.4472.124")
        self.assertEqual(browser_info.platform, "Windows 10")
        self.assertIsNotNone(browser_info.user_agent)
    
    def test_get_browser_info_failure(self):
        """Test browser info retrieval failure"""
        self.mock_driver.capabilities = {}
        self.mock_driver.execute_script.side_effect = Exception("Script execution failed")
        
        browser_info = self.manager.get_browser_info(self.mock_driver)
        
        self.assertEqual(browser_info.name, "unknown")
        self.assertEqual(browser_info.version, "unknown")
        self.assertEqual(browser_info.platform, "unknown")
    
    def test_capture_screenshot(self):
        """Test screenshot capture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.manager.screenshot_dir = Path(temp_dir)
            
            screenshot_path = self.manager.capture_screenshot(self.mock_driver, "test_screenshot")
            
            self.mock_driver.save_screenshot.assert_called_once()
            self.assertTrue(screenshot_path.endswith("test_screenshot.png"))
    
    def test_capture_screenshot_auto_filename(self):
        """Test screenshot capture with auto-generated filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.manager.screenshot_dir = Path(temp_dir)
            
            screenshot_path = self.manager.capture_screenshot(self.mock_driver)
            
            self.mock_driver.save_screenshot.assert_called_once()
            self.assertTrue(screenshot_path.endswith(".png"))
            self.assertIn("screenshot_", screenshot_path)
    
    def test_capture_screenshot_failure(self):
        """Test screenshot capture failure"""
        self.mock_driver.save_screenshot.side_effect = Exception("Screenshot failed")
        
        screenshot_path = self.manager.capture_screenshot(self.mock_driver)
        
        self.assertEqual(screenshot_path, "")
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_wait_for_element(self, mock_wait):
        """Test waiting for element"""
        mock_element = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_element
        mock_wait.return_value = mock_wait_instance
        
        locator = (By.ID, "test-element")
        element = self.manager.wait_for_element(self.mock_driver, locator)
        
        self.assertEqual(element, mock_element)
        mock_wait.assert_called_once_with(self.mock_driver, 30)  # default timeout
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_wait_for_element_timeout(self, mock_wait):
        """Test waiting for element timeout"""
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException("Element not found")
        mock_wait.return_value = mock_wait_instance
        
        locator = (By.ID, "non-existent-element")
        
        with self.assertRaises(TimeoutException):
            self.manager.wait_for_element(self.mock_driver, locator)
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_wait_for_element_clickable(self, mock_wait):
        """Test waiting for element to be clickable"""
        mock_element = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_element
        mock_wait.return_value = mock_wait_instance
        
        locator = (By.ID, "clickable-element")
        element = self.manager.wait_for_element_clickable(self.mock_driver, locator)
        
        self.assertEqual(element, mock_element)
        mock_wait.assert_called_once_with(self.mock_driver, 30)
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_wait_for_page_load(self, mock_wait):
        """Test waiting for page load"""
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = True
        mock_wait.return_value = mock_wait_instance
        
        result = self.manager.wait_for_page_load(self.mock_driver)
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(self.mock_driver, 30)
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_wait_for_page_load_timeout(self, mock_wait):
        """Test page load timeout"""
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException("Page load timeout")
        mock_wait.return_value = mock_wait_instance
        
        result = self.manager.wait_for_page_load(self.mock_driver)
        
        self.assertFalse(result)
    
    def test_scroll_to_element(self):
        """Test scrolling to element"""
        mock_element = Mock()
        
        self.manager.scroll_to_element(self.mock_driver, mock_element)
        
        self.mock_driver.execute_script.assert_called_once_with(
            "arguments[0].scrollIntoView(true);", mock_element
        )
    
    def test_scroll_to_element_failure(self):
        """Test scroll to element failure"""
        mock_element = Mock()
        self.mock_driver.execute_script.side_effect = Exception("Scroll failed")
        
        # Should not raise exception, just log error
        self.manager.scroll_to_element(self.mock_driver, mock_element)
    
    @patch('time.sleep')
    def test_highlight_element(self, mock_sleep):
        """Test element highlighting"""
        mock_element = Mock()
        mock_element.get_attribute.return_value = "original-style"
        
        self.manager.highlight_element(self.mock_driver, mock_element, duration=0.5)
        
        # Should call execute_script twice (highlight and restore)
        self.assertEqual(self.mock_driver.execute_script.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)
    
    def test_execute_javascript(self):
        """Test JavaScript execution"""
        script = "return document.title;"
        expected_result = "Test Page Title"
        self.mock_driver.execute_script.return_value = expected_result
        
        result = self.manager.execute_javascript(self.mock_driver, script)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_script.assert_called_once_with(script)
    
    def test_execute_javascript_failure(self):
        """Test JavaScript execution failure"""
        script = "invalid script"
        self.mock_driver.execute_script.side_effect = Exception("Script error")
        
        with self.assertRaises(Exception):
            self.manager.execute_javascript(self.mock_driver, script)
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_switch_to_frame(self, mock_wait):
        """Test switching to iframe"""
        mock_frame = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_frame
        mock_wait.return_value = mock_wait_instance
        
        frame_locator = (By.ID, "test-frame")
        self.manager.switch_to_frame(self.mock_driver, frame_locator)
        
        self.mock_driver.switch_to.frame.assert_called_once_with(mock_frame)
    
    def test_switch_to_default_content(self):
        """Test switching to default content"""
        self.manager.switch_to_default_content(self.mock_driver)
        
        self.mock_driver.switch_to.default_content.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_handle_alert_accept(self, mock_wait):
        """Test handling alert with accept action"""
        mock_alert = Mock()
        mock_alert.text = "Test alert message"
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_alert
        mock_wait.return_value = mock_wait_instance
        
        alert_text = self.manager.handle_alert(self.mock_driver, "accept")
        
        self.assertEqual(alert_text, "Test alert message")
        mock_alert.accept.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_handle_alert_dismiss(self, mock_wait):
        """Test handling alert with dismiss action"""
        mock_alert = Mock()
        mock_alert.text = "Test alert message"
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_alert
        mock_wait.return_value = mock_wait_instance
        
        alert_text = self.manager.handle_alert(self.mock_driver, "dismiss")
        
        self.assertEqual(alert_text, "Test alert message")
        mock_alert.dismiss.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.WebDriverWait')
    def test_handle_alert_no_alert(self, mock_wait):
        """Test handling alert when no alert is present"""
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException("No alert")
        mock_wait.return_value = mock_wait_instance
        
        alert_text = self.manager.handle_alert(self.mock_driver)
        
        self.assertIsNone(alert_text)
    
    def test_handle_alert_invalid_action(self):
        """Test handling alert with invalid action"""
        with self.assertRaises(ValueError) as context:
            self.manager.handle_alert(self.mock_driver, "invalid_action")
        
        self.assertIn("Invalid alert action", str(context.exception))
    
    def test_get_driver_logs(self):
        """Test getting driver logs"""
        expected_logs = [
            {"level": "INFO", "message": "Test log message"},
            {"level": "ERROR", "message": "Test error message"}
        ]
        self.mock_driver.get_log.return_value = expected_logs
        
        logs = self.manager.get_driver_logs(self.mock_driver, "browser")
        
        self.assertEqual(logs, expected_logs)
        self.mock_driver.get_log.assert_called_once_with("browser")
    
    def test_get_driver_logs_failure(self):
        """Test getting driver logs failure"""
        self.mock_driver.get_log.side_effect = Exception("Log retrieval failed")
        
        logs = self.manager.get_driver_logs(self.mock_driver)
        
        self.assertEqual(logs, [])
    
    def test_close_driver(self):
        """Test closing specific driver"""
        # Add driver to active drivers
        driver_id = "test_driver_123"
        self.manager.active_drivers[driver_id] = self.mock_driver
        
        self.manager.close_driver(self.mock_driver)
        
        self.mock_driver.quit.assert_called_once()
        self.assertNotIn(driver_id, self.manager.active_drivers)
    
    def test_close_driver_failure(self):
        """Test closing driver failure"""
        self.mock_driver.quit.side_effect = Exception("Close failed")
        
        # Should not raise exception, just log error
        self.manager.close_driver(self.mock_driver)
    
    def test_close_all_drivers(self):
        """Test closing all drivers"""
        # Add multiple drivers
        mock_driver1 = Mock(spec=WebDriver)
        mock_driver2 = Mock(spec=WebDriver)
        
        self.manager.active_drivers = {
            "driver1": mock_driver1,
            "driver2": mock_driver2
        }
        
        self.manager.close_all_drivers()
        
        mock_driver1.quit.assert_called_once()
        mock_driver2.quit.assert_called_once()
        self.assertEqual(len(self.manager.active_drivers), 0)
    
    def test_get_active_drivers(self):
        """Test getting active drivers"""
        mock_driver1 = Mock(spec=WebDriver)
        mock_driver2 = Mock(spec=WebDriver)
        
        self.manager.active_drivers = {
            "driver1": mock_driver1,
            "driver2": mock_driver2
        }
        
        active_drivers = self.manager.get_active_drivers()
        
        self.assertEqual(len(active_drivers), 2)
        self.assertIn("driver1", active_drivers)
        self.assertIn("driver2", active_drivers)
        # Should return a copy, not the original dict
        self.assertIsNot(active_drivers, self.manager.active_drivers)
    
    def test_destructor_cleanup(self):
        """Test cleanup on destruction"""
        # Add mock driver
        mock_driver = Mock(spec=WebDriver)
        self.manager.active_drivers["test_driver"] = mock_driver
        
        # Manually call destructor
        self.manager.__del__()
        
        mock_driver.quit.assert_called_once()


class TestWebDriverManagerIntegration(unittest.TestCase):
    """Integration tests for WebDriverManager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.manager = WebDriverManager(Environment.TESTING)
    
    def tearDown(self):
        """Clean up after integration tests"""
        self.manager.close_all_drivers()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_full_driver_lifecycle(self, mock_chrome_manager, mock_chrome):
        """Test complete driver lifecycle"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock(spec=WebDriver)
        mock_driver.capabilities = {
            "browserName": "chrome",
            "browserVersion": "91.0.4472.124",
            "platformName": "Windows 10"
        }
        mock_driver.execute_script.side_effect = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            {"width": 1920, "height": 1080}
        ]
        mock_chrome.return_value = mock_driver
        
        # Create driver
        driver = self.manager.create_driver("chrome", headless=True)
        self.assertIsNotNone(driver)
        self.assertEqual(len(self.manager.active_drivers), 1)
        
        # Get browser info
        browser_info = self.manager.get_browser_info(driver)
        self.assertEqual(browser_info.name, "chrome")
        
        # Capture screenshot
        screenshot_path = self.manager.capture_screenshot(driver, "integration_test")
        self.assertTrue(screenshot_path.endswith("integration_test.png"))
        
        # Close driver
        self.manager.close_driver(driver)
        self.assertEqual(len(self.manager.active_drivers), 0)
        mock_driver.quit.assert_called_once()
    
    @patch('qa_testing_framework.web.webdriver_manager.webdriver.Chrome')
    @patch('qa_testing_framework.web.webdriver_manager.ChromeDriverManager')
    def test_multiple_drivers_management(self, mock_chrome_manager, mock_chrome):
        """Test managing multiple drivers simultaneously"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Create multiple mock drivers
        mock_drivers = []
        for i in range(3):
            mock_driver = Mock(spec=WebDriver)
            mock_driver.capabilities = {"browserName": "chrome"}
            mock_drivers.append(mock_driver)
        
        mock_chrome.side_effect = mock_drivers
        
        # Create multiple drivers
        drivers = []
        for i in range(3):
            driver = self.manager.create_driver("chrome")
            drivers.append(driver)
        
        self.assertEqual(len(self.manager.active_drivers), 3)
        
        # Close all drivers
        self.manager.close_all_drivers()
        self.assertEqual(len(self.manager.active_drivers), 0)
        
        # Verify all drivers were closed
        for mock_driver in mock_drivers:
            mock_driver.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main() 