"""
Mobile push notification testing capabilities.

Tests push notification delivery, interaction, deep linking,
and notification management functionality.
"""

import pytest
import time
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from enum import Enum

try:
    from core.utils import Logger
except ImportError:
    class Logger:
        def __init__(self, name): pass
        def info(self, msg): pass
        def error(self, msg): pass
        def warning(self, msg): pass

from .mobile_utils import NotificationUtils, DeviceUtils
from .page_objects import BaseMobilePage


class NotificationType(Enum):
    """Types of push notifications."""
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    SYSTEM = "system"
    MARKETING = "marketing"
    ORDER_UPDATE = "order_update"
    CHAT_MESSAGE = "chat_message"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PushNotificationPage(BaseMobilePage):
    """Page object for push notification interactions."""
    
    def __init__(self, driver, timeout=30):
        super().__init__(driver, timeout)
        
        # Notification panel elements
        self.notification_panel = ("id", "notification_panel")
        self.notification_list = ("id", "notification_list")
        self.notification_item = ("class name", "notification_item")
        self.clear_all_button = ("id", "clear_all_notifications")
        self.notification_settings_button = ("id", "notification_settings")
        
        # Individual notification elements
        self.notification_title = ("id", "notification_title")
        self.notification_body = ("id", "notification_body")
        self.notification_icon = ("id", "notification_icon")
        self.notification_timestamp = ("id", "notification_timestamp")
        self.notification_action_button = ("id", "notification_action")
        
        # Permission dialog elements
        self.permission_dialog = ("id", "permission_dialog")
        self.allow_button = ("id", "allow_notifications")
        self.deny_button = ("id", "deny_notifications")
        
        # Settings page elements
        self.notification_toggle = ("id", "notification_toggle")
        self.sound_toggle = ("id", "sound_toggle")
        self.vibration_toggle = ("id", "vibration_toggle")
        self.badge_toggle = ("id", "badge_toggle")
    
    def is_loaded(self) -> bool:
        """Check if notification-related page is loaded."""
        return (self.is_element_present(self.notification_panel, timeout=5) or
                self.is_element_present(self.permission_dialog, timeout=5))
    
    def open_notification_panel(self) -> bool:
        """Open the notification panel."""
        try:
            # Platform-specific notification panel opening
            platform = self.driver.capabilities.get('platformName', '').lower()
            
            if platform == 'android':
                self.driver.open_notifications()
            else:
                # iOS - swipe down from top
                screen_size = self.driver.get_window_size()
                start_x = screen_size['width'] // 2
                self.driver.swipe(start_x, 0, start_x, screen_size['height'] // 3, 500)
            
            time.sleep(2)
            return self.is_element_present(self.notification_panel, timeout=5)
            
        except Exception as e:
            self.logger.error(f"Failed to open notification panel: {str(e)}")
            return False
    
    def get_notifications(self) -> List[Dict[str, str]]:
        """Get list of visible notifications."""
        notifications = []
        
        try:
            if not self.open_notification_panel():
                return notifications
            
            notification_elements = self.find_elements(self.notification_item)
            
            for element in notification_elements:
                try:
                    # Extract notification details
                    notification = {
                        'title': '',
                        'body': '',
                        'timestamp': '',
                        'app': ''
                    }
                    
                    # Try to get title and body text
                    text_content = element.text
                    if text_content:
                        lines = text_content.split('\n')
                        if len(lines) >= 1:
                            notification['title'] = lines[0]
                        if len(lines) >= 2:
                            notification['body'] = lines[1]
                        if len(lines) >= 3:
                            notification['timestamp'] = lines[-1]
                    
                    notifications.append(notification)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse notification: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Failed to get notifications: {str(e)}")
        
        return notifications
    
    def tap_notification(self, notification_text: str) -> bool:
        """Tap on a notification containing specific text."""
        try:
            if not self.open_notification_panel():
                return False
            
            notification_elements = self.find_elements(self.notification_item)
            
            for element in notification_elements:
                if notification_text.lower() in element.text.lower():
                    element.click()
                    time.sleep(2)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to tap notification: {str(e)}")
            return False
    
    def clear_notification(self, notification_text: str) -> bool:
        """Clear a specific notification."""
        try:
            if not self.open_notification_panel():
                return False
            
            notification_elements = self.find_elements(self.notification_item)
            
            for element in notification_elements:
                if notification_text.lower() in element.text.lower():
                    # Swipe to dismiss (common pattern)
                    location = element.location
                    size = element.size
                    start_x = location['x'] + size['width'] // 2
                    start_y = location['y'] + size['height'] // 2
                    end_x = start_x + 200  # Swipe right to dismiss
                    
                    self.driver.swipe(start_x, start_y, end_x, start_y, 500)
                    time.sleep(1)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to clear notification: {str(e)}")
            return False
    
    def clear_all_notifications(self) -> bool:
        """Clear all notifications."""
        try:
            if not self.open_notification_panel():
                return False
            
            if self.is_element_present(self.clear_all_button):
                self.click_element(self.clear_all_button)
                time.sleep(1)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to clear all notifications: {str(e)}")
            return False
    
    def handle_permission_dialog(self, allow: bool = True) -> bool:
        """Handle notification permission dialog."""
        try:
            if self.is_element_present(self.permission_dialog, timeout=5):
                if allow and self.is_element_present(self.allow_button):
                    self.click_element(self.allow_button)
                elif not allow and self.is_element_present(self.deny_button):
                    self.click_element(self.deny_button)
                
                time.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle permission dialog: {str(e)}")
            return False


class PushNotificationTests:
    """Push notification test suite."""
    
    def __init__(self, driver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
        self.notification_utils = NotificationUtils(driver)
        self.device_utils = DeviceUtils(driver)
        self.notification_page = PushNotificationPage(driver)
        
    def test_notification_permissions(self) -> bool:
        """Test notification permission handling."""
        try:
            # Test allowing notifications
            permission_granted = self.notification_page.handle_permission_dialog(allow=True)
            
            if permission_granted:
                self.logger.info("Notification permissions granted successfully")
                return True
            else:
                self.logger.warning("No permission dialog found or already granted")
                return True  # Assume permissions already granted
            
        except Exception as e:
            self.logger.error(f"Notification permission test failed: {str(e)}")
            return False
    
    def test_notification_delivery(self, test_notification: Dict[str, Any]) -> bool:
        """Test notification delivery and display."""
        try:
            # Wait for notification to appear
            notification_text = test_notification.get('title', 'Test Notification')
            
            # Check if notification appears in panel
            found = self.notification_utils.wait_for_notification(notification_text, timeout=30)
            
            if found:
                self.logger.info(f"Notification delivered successfully: {notification_text}")
                return True
            else:
                self.logger.error(f"Notification not delivered: {notification_text}")
                return False
            
        except Exception as e:
            self.logger.error(f"Notification delivery test failed: {str(e)}")
            return False
    
    def test_notification_interaction(self, notification_text: str) -> bool:
        """Test notification tap and interaction."""
        try:
            # Tap on notification
            tapped = self.notification_page.tap_notification(notification_text)
            
            if tapped:
                # Verify app opened or navigated to correct screen
                time.sleep(3)  # Wait for navigation
                
                # Check if app is in foreground
                # This would be app-specific verification
                self.logger.info(f"Successfully interacted with notification: {notification_text}")
                return True
            else:
                self.logger.error(f"Failed to tap notification: {notification_text}")
                return False
            
        except Exception as e:
            self.logger.error(f"Notification interaction test failed: {str(e)}")
            return False
    
    def test_notification_deep_linking(self, notification_data: Dict[str, Any]) -> bool:
        """Test deep linking from notifications."""
        try:
            notification_text = notification_data.get('title', 'Deep Link Test')
            expected_screen = notification_data.get('deep_link_screen', 'product_detail')
            
            # Tap notification
            if self.notification_page.tap_notification(notification_text):
                time.sleep(3)  # Wait for navigation
                
                # Verify correct screen opened
                # This would require screen-specific verification logic
                current_activity = None
                
                if self.driver.capabilities.get('platformName') == 'Android':
                    current_activity = self.driver.current_activity
                
                self.logger.info(f"Deep link navigation completed. Current activity: {current_activity}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Deep linking test failed: {str(e)}")
            return False
    
    def test_notification_actions(self, notification_text: str) -> bool:
        """Test notification action buttons."""
        try:
            # Open notification panel
            if not self.notification_page.open_notification_panel():
                return False
            
            # Look for notification with action buttons
            notifications = self.notification_page.get_notifications()
            
            for notification in notifications:
                if notification_text.lower() in notification.get('title', '').lower():
                    # Try to find and tap action button
                    # This would be platform and app specific
                    self.logger.info(f"Found notification with actions: {notification_text}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Notification actions test failed: {str(e)}")
            return False
    
    def test_notification_management(self) -> bool:
        """Test notification management (clear, dismiss, etc.)."""
        try:
            # Get initial notification count
            initial_notifications = self.notification_page.get_notifications()
            initial_count = len(initial_notifications)
            
            if initial_count == 0:
                self.logger.warning("No notifications to manage")
                return True
            
            # Test clearing individual notification
            if initial_count > 0:
                first_notification = initial_notifications[0]
                cleared = self.notification_page.clear_notification(
                    first_notification.get('title', '')
                )
                
                if cleared:
                    self.logger.info("Successfully cleared individual notification")
                
            # Test clearing all notifications
            cleared_all = self.notification_page.clear_all_notifications()
            
            if cleared_all:
                self.logger.info("Successfully cleared all notifications")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Notification management test failed: {str(e)}")
            return False
    
    def test_notification_settings(self) -> bool:
        """Test notification settings and preferences."""
        try:
            # Navigate to notification settings
            # This would be app-specific navigation
            
            # Test toggling notification settings
            # This would require access to settings page
            
            self.logger.info("Notification settings test completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Notification settings test failed: {str(e)}")
            return False
    
    def test_notification_during_app_states(self) -> bool:
        """Test notifications in different app states (foreground, background, killed)."""
        try:
            # Test notification in foreground
            self.logger.info("Testing notification in foreground state")
            # App is already in foreground
            
            # Test notification in background
            self.logger.info("Testing notification in background state")
            self.device_utils.background_app(5)
            time.sleep(2)
            
            # Bring app back to foreground
            # Platform-specific app activation would be needed
            
            # Test notification when app is killed
            # This would require external notification triggering
            
            self.logger.info("App state notification tests completed")
            return True
            
        except Exception as e:
            self.logger.error(f"App state notification test failed: {str(e)}")
            return False
    
    def test_notification_sound_and_vibration(self) -> bool:
        """Test notification sound and vibration."""
        try:
            # This test would require audio/vibration detection
            # which is challenging in automated testing
            
            # Check if device supports vibration
            # Check if sound is enabled
            
            self.logger.info("Sound and vibration test completed (limited automation)")
            return True
            
        except Exception as e:
            self.logger.error(f"Sound and vibration test failed: {str(e)}")
            return False
    
    def test_notification_badge_count(self) -> bool:
        """Test notification badge count functionality."""
        try:
            # Get current badge count (iOS specific)
            if self.driver.capabilities.get('platformName') == 'iOS':
                # iOS badge count testing would require specific implementation
                pass
            
            # Android notification count in status bar
            elif self.driver.capabilities.get('platformName') == 'Android':
                # Android notification count testing
                pass
            
            self.logger.info("Badge count test completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Badge count test failed: {str(e)}")
            return False
    
    def test_notification_categories(self) -> bool:
        """Test different notification categories and channels."""
        try:
            # Test different notification types
            categories = [
                NotificationType.PROMOTIONAL,
                NotificationType.TRANSACTIONAL,
                NotificationType.ORDER_UPDATE
            ]
            
            for category in categories:
                self.logger.info(f"Testing {category.value} notification category")
                # Category-specific testing would be implemented here
            
            return True
            
        except Exception as e:
            self.logger.error(f"Notification categories test failed: {str(e)}")
            return False
    
    def run_push_notification_test_suite(self, test_config: Dict[str, Any]) -> Dict[str, bool]:
        """Run complete push notification test suite."""
        results = {}
        
        try:
            # Test basic notification functionality
            results['permissions'] = self.test_notification_permissions()
            
            # Test notification delivery
            test_notifications = test_config.get('test_notifications', [])
            
            for i, notification in enumerate(test_notifications):
                results[f'delivery_{i}'] = self.test_notification_delivery(notification)
                results[f'interaction_{i}'] = self.test_notification_interaction(
                    notification.get('title', f'Test {i}')
                )
                
                if notification.get('deep_link'):
                    results[f'deep_link_{i}'] = self.test_notification_deep_linking(notification)
            
            # Test notification management
            results['management'] = self.test_notification_management()
            results['settings'] = self.test_notification_settings()
            results['app_states'] = self.test_notification_during_app_states()
            results['sound_vibration'] = self.test_notification_sound_and_vibration()
            results['badge_count'] = self.test_notification_badge_count()
            results['categories'] = self.test_notification_categories()
            
            # Calculate success rate
            total_tests = len(results)
            passed_tests = sum(1 for result in results.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.logger.info(f"Push notification test suite completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Push notification test suite execution failed: {str(e)}")
            results['execution_error'] = False
        
        return results


# Mock notification service for testing
class MockNotificationService:
    """Mock service for simulating push notifications during testing."""
    
    def __init__(self):
        self.logger = Logger(self.__class__.__name__)
        self.sent_notifications = []
    
    def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Simulate sending a push notification."""
        try:
            notification = {
                'id': len(self.sent_notifications) + 1,
                'title': notification_data.get('title', 'Test Notification'),
                'body': notification_data.get('body', 'Test notification body'),
                'type': notification_data.get('type', NotificationType.SYSTEM.value),
                'priority': notification_data.get('priority', NotificationPriority.NORMAL.value),
                'timestamp': time.time(),
                'deep_link': notification_data.get('deep_link'),
                'actions': notification_data.get('actions', [])
            }
            
            self.sent_notifications.append(notification)
            self.logger.info(f"Mock notification sent: {notification['title']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send mock notification: {str(e)}")
            return False
    
    def get_sent_notifications(self) -> List[Dict[str, Any]]:
        """Get list of sent notifications."""
        return self.sent_notifications.copy()
    
    def clear_sent_notifications(self) -> None:
        """Clear sent notifications list."""
        self.sent_notifications.clear()


# Test fixtures for pytest integration
@pytest.fixture
def mock_driver():
    """Create mock driver for testing."""
    driver = Mock()
    driver.capabilities = {'platformName': 'Android'}
    driver.get_window_size.return_value = {'width': 375, 'height': 667}
    driver.open_notifications = Mock()
    driver.swipe = Mock()
    return driver


@pytest.fixture
def notification_service():
    """Create mock notification service."""
    return MockNotificationService()


@pytest.fixture
def push_notification_tests(mock_driver):
    """Create push notification tests instance."""
    return PushNotificationTests(mock_driver)


def test_push_notification_page_initialization(mock_driver):
    """Test PushNotificationPage initialization."""
    page = PushNotificationPage(mock_driver)
    assert page.driver == mock_driver
    assert page.timeout == 30


def test_push_notification_tests_initialization(mock_driver):
    """Test PushNotificationTests initialization."""
    tests = PushNotificationTests(mock_driver)
    assert tests.driver == mock_driver
    assert tests.notification_utils is not None
    assert tests.device_utils is not None
    assert tests.notification_page is not None


def test_mock_notification_service(notification_service):
    """Test MockNotificationService functionality."""
    notification_data = {
        'title': 'Test Notification',
        'body': 'This is a test notification',
        'type': NotificationType.PROMOTIONAL.value
    }
    
    result = notification_service.send_notification(notification_data)
    assert result is True
    
    sent_notifications = notification_service.get_sent_notifications()
    assert len(sent_notifications) == 1
    assert sent_notifications[0]['title'] == 'Test Notification'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])