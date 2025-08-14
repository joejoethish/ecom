"""
Mobile-specific utilities for gestures, device rotation, and notifications.

Provides utility functions for mobile testing including touch gestures,
device management, and notification handling.
"""

import time
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
try:
    from appium.webdriver.webdriver import WebDriver
    # Try new import path first, then fallback to old path
    try:
        from appium.webdriver.common.touch_action import TouchAction
        from appium.webdriver.common.multi_action import MultiAction
    except ImportError:
        try:
            from appium.webdriver.extensions.action_helpers import TouchAction
            from appium.webdriver.extensions.multi_action import MultiAction
        except ImportError:
            # Mock for testing when Appium is not available
            class TouchAction:
                def __init__(self, driver): pass
                def tap(self, **kwargs): return self
                def press(self, **kwargs): return self
                def move_to(self, **kwargs): return self
                def release(self): return self
                def perform(self): pass
                def long_press(self, **kwargs): return self
                def wait(self, duration): return self
            
            class MultiAction:
                def __init__(self, driver): pass
                def add(self, action): return self
                def perform(self): pass
except ImportError:
    # Fallback when appium is not installed
    class WebDriver: pass
    class TouchAction:
        def __init__(self, driver): pass
        def tap(self, **kwargs): return self
        def press(self, **kwargs): return self
        def move_to(self, **kwargs): return self
        def release(self): return self
        def perform(self): pass
        def long_press(self, **kwargs): return self
        def wait(self, duration): return self
    
    class MultiAction:
        def __init__(self, driver): pass
        def add(self, action): return self
        def perform(self): pass
from selenium.common.exceptions import WebDriverException

try:
    from core.utils import Logger
except ImportError:
    # Fallback for testing
    class Logger:
        def __init__(self, name):
            self.name = name
        def info(self, msg): pass
        def error(self, msg): pass
        def warning(self, msg): pass


class DeviceOrientation(Enum):
    """Device orientation enumeration."""
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"
    PORTRAIT_UPSIDE_DOWN = "UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN"
    LANDSCAPE_LEFT = "UIA_DEVICE_ORIENTATION_LANDSCAPELEFT"
    LANDSCAPE_RIGHT = "UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT"


class SwipeDirection(Enum):
    """Swipe direction enumeration."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class MobileGestureUtils:
    """Utility class for mobile gestures and touch actions."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
        self.screen_size = self._get_screen_size()
    
    def _get_screen_size(self) -> Dict[str, int]:
        """Get device screen size."""
        try:
            size = self.driver.get_window_size()
            self.logger.info(f"Screen size: {size}")
            return size
        except Exception as e:
            self.logger.error(f"Error getting screen size: {str(e)}")
            return {'width': 375, 'height': 667}  # Default iPhone size
    
    def tap(self, x: int, y: int, duration: int = 100) -> None:
        """Perform tap gesture at coordinates."""
        try:
            action = TouchAction(self.driver)
            action.tap(x=x, y=y).perform()
            self.logger.info(f"Tapped at coordinates ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error performing tap: {str(e)}")
    
    def tap_element(self, element, duration: int = 100) -> None:
        """Perform tap gesture on element."""
        try:
            action = TouchAction(self.driver)
            action.tap(element).perform()
            self.logger.info("Tapped element")
        except Exception as e:
            self.logger.error(f"Error tapping element: {str(e)}")
    
    def double_tap(self, x: int, y: int) -> None:
        """Perform double tap gesture at coordinates."""
        try:
            action = TouchAction(self.driver)
            action.tap(x=x, y=y).tap(x=x, y=y).perform()
            self.logger.info(f"Double tapped at coordinates ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error performing double tap: {str(e)}")
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> None:
        """Perform long press gesture at coordinates."""
        try:
            action = TouchAction(self.driver)
            action.long_press(x=x, y=y, duration=duration).release().perform()
            self.logger.info(f"Long pressed at coordinates ({x}, {y}) for {duration}ms")
        except Exception as e:
            self.logger.error(f"Error performing long press: {str(e)}")
    
    def long_press_element(self, element, duration: int = 1000) -> None:
        """Perform long press gesture on element."""
        try:
            action = TouchAction(self.driver)
            action.long_press(element, duration=duration).release().perform()
            self.logger.info(f"Long pressed element for {duration}ms")
        except Exception as e:
            self.logger.error(f"Error long pressing element: {str(e)}")
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000) -> None:
        """Perform swipe gesture between coordinates."""
        try:
            action = TouchAction(self.driver)
            action.press(x=start_x, y=start_y).wait(duration).move_to(x=end_x, y=end_y).release().perform()
            self.logger.info(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        except Exception as e:
            self.logger.error(f"Error performing swipe: {str(e)}")
    
    def swipe_screen(self, direction: SwipeDirection, distance_ratio: float = 0.8, duration: int = 1000) -> None:
        """Perform swipe gesture across screen in specified direction."""
        width = self.screen_size['width']
        height = self.screen_size['height']
        
        center_x = width // 2
        center_y = height // 2
        
        if direction == SwipeDirection.UP:
            start_x, start_y = center_x, int(height * 0.8)
            end_x, end_y = center_x, int(height * (1 - distance_ratio))
        elif direction == SwipeDirection.DOWN:
            start_x, start_y = center_x, int(height * 0.2)
            end_x, end_y = center_x, int(height * distance_ratio)
        elif direction == SwipeDirection.LEFT:
            start_x, start_y = int(width * 0.8), center_y
            end_x, end_y = int(width * (1 - distance_ratio)), center_y
        elif direction == SwipeDirection.RIGHT:
            start_x, start_y = int(width * 0.2), center_y
            end_x, end_y = int(width * distance_ratio), center_y
        else:
            raise ValueError(f"Invalid swipe direction: {direction}")
        
        self.swipe(start_x, start_y, end_x, end_y, duration)
    
    def scroll_to_element(self, element_locator: Tuple[str, str], max_scrolls: int = 10, 
                         direction: SwipeDirection = SwipeDirection.DOWN) -> bool:
        """Scroll to find element."""
        for i in range(max_scrolls):
            try:
                element = self.driver.find_element(*element_locator)
                if element.is_displayed():
                    self.logger.info(f"Found element after {i} scrolls")
                    return True
            except:
                pass
            
            self.swipe_screen(direction)
            time.sleep(0.5)
        
        self.logger.warning(f"Element not found after {max_scrolls} scrolls")
        return False
    
    def pinch_zoom(self, center_x: int, center_y: int, scale: float = 2.0) -> None:
        """Perform pinch zoom gesture."""
        try:
            offset = int(50 * scale)
            
            # First finger
            action1 = TouchAction(self.driver)
            action1.press(x=center_x - offset, y=center_y - offset).move_to(
                x=center_x - offset * 2, y=center_y - offset * 2).release()
            
            # Second finger
            action2 = TouchAction(self.driver)
            action2.press(x=center_x + offset, y=center_y + offset).move_to(
                x=center_x + offset * 2, y=center_y + offset * 2).release()
            
            # Perform multi-touch
            multi_action = MultiAction(self.driver)
            multi_action.add(action1).add(action2).perform()
            
            self.logger.info(f"Performed pinch zoom at ({center_x}, {center_y}) with scale {scale}")
        except Exception as e:
            self.logger.error(f"Error performing pinch zoom: {str(e)}")
    
    def zoom_in(self, center_x: int, center_y: int, scale: float = 2.0) -> None:
        """Perform zoom in gesture."""
        try:
            offset = int(20 / scale)
            
            # First finger
            action1 = TouchAction(self.driver)
            action1.press(x=center_x - offset, y=center_y - offset).move_to(
                x=center_x - offset * 2, y=center_y - offset * 2).release()
            
            # Second finger
            action2 = TouchAction(self.driver)
            action2.press(x=center_x + offset, y=center_y + offset).move_to(
                x=center_x + offset * 2, y=center_y + offset * 2).release()
            
            # Perform multi-touch
            multi_action = MultiAction(self.driver)
            multi_action.add(action1).add(action2).perform()
            
            self.logger.info(f"Performed zoom in at ({center_x}, {center_y}) with scale {scale}")
        except Exception as e:
            self.logger.error(f"Error performing zoom in: {str(e)}")
    
    def drag_and_drop(self, start_element, end_element, duration: int = 1000) -> None:
        """Perform drag and drop between elements."""
        try:
            action = TouchAction(self.driver)
            action.long_press(start_element).move_to(end_element).release().perform()
            self.logger.info("Performed drag and drop")
        except Exception as e:
            self.logger.error(f"Error performing drag and drop: {str(e)}")


class DeviceUtils:
    """Utility class for device management and operations."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
    
    def rotate_device(self, orientation: DeviceOrientation) -> None:
        """Rotate device to specified orientation."""
        try:
            self.driver.orientation = orientation.value
            self.logger.info(f"Rotated device to {orientation.value}")
            time.sleep(1)  # Wait for rotation to complete
        except Exception as e:
            self.logger.error(f"Error rotating device: {str(e)}")
    
    def get_orientation(self) -> str:
        """Get current device orientation."""
        try:
            orientation = self.driver.orientation
            self.logger.info(f"Current orientation: {orientation}")
            return orientation
        except Exception as e:
            self.logger.error(f"Error getting orientation: {str(e)}")
            return "UNKNOWN"
    
    def lock_device(self, duration: int = 5) -> None:
        """Lock device for specified duration."""
        try:
            self.driver.lock(duration)
            self.logger.info(f"Locked device for {duration} seconds")
        except Exception as e:
            self.logger.error(f"Error locking device: {str(e)}")
    
    def unlock_device(self) -> None:
        """Unlock device."""
        try:
            if self.driver.is_locked():
                self.driver.unlock()
                self.logger.info("Unlocked device")
        except Exception as e:
            self.logger.error(f"Error unlocking device: {str(e)}")
    
    def is_device_locked(self) -> bool:
        """Check if device is locked."""
        try:
            locked = self.driver.is_locked()
            self.logger.info(f"Device locked: {locked}")
            return locked
        except Exception as e:
            self.logger.error(f"Error checking lock status: {str(e)}")
            return False
    
    def shake_device(self) -> None:
        """Shake the device (iOS only)."""
        try:
            self.driver.shake()
            self.logger.info("Shook device")
        except Exception as e:
            self.logger.error(f"Error shaking device: {str(e)}")
    
    def background_app(self, duration: int = 5) -> None:
        """Put app in background for specified duration."""
        try:
            self.driver.background_app(duration)
            self.logger.info(f"Put app in background for {duration} seconds")
        except Exception as e:
            self.logger.error(f"Error backgrounding app: {str(e)}")
    
    def get_device_time(self) -> str:
        """Get device time."""
        try:
            device_time = self.driver.device_time
            self.logger.info(f"Device time: {device_time}")
            return device_time
        except Exception as e:
            self.logger.error(f"Error getting device time: {str(e)}")
            return ""
    
    def set_network_connection(self, connection_type: int) -> None:
        """Set network connection type (Android only)."""
        try:
            self.driver.set_network_connection(connection_type)
            self.logger.info(f"Set network connection to type {connection_type}")
        except Exception as e:
            self.logger.error(f"Error setting network connection: {str(e)}")
    
    def get_network_connection(self) -> int:
        """Get current network connection type (Android only)."""
        try:
            connection = self.driver.network_connection
            self.logger.info(f"Network connection type: {connection}")
            return connection
        except Exception as e:
            self.logger.error(f"Error getting network connection: {str(e)}")
            return 0
    
    def toggle_wifi(self) -> None:
        """Toggle WiFi connection (Android only)."""
        try:
            self.driver.toggle_wifi()
            self.logger.info("Toggled WiFi")
        except Exception as e:
            self.logger.error(f"Error toggling WiFi: {str(e)}")
    
    def toggle_data(self) -> None:
        """Toggle mobile data connection (Android only)."""
        try:
            self.driver.toggle_data()
            self.logger.info("Toggled mobile data")
        except Exception as e:
            self.logger.error(f"Error toggling mobile data: {str(e)}")


class NotificationUtils:
    """Utility class for handling mobile notifications."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
    
    def open_notifications(self) -> None:
        """Open notification panel (Android only)."""
        try:
            self.driver.open_notifications()
            self.logger.info("Opened notification panel")
        except Exception as e:
            self.logger.error(f"Error opening notifications: {str(e)}")
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get list of notifications (Android only)."""
        try:
            # This is a simplified implementation
            # In practice, you'd need to parse the notification elements
            notifications = []
            
            # Open notifications first
            self.open_notifications()
            time.sleep(2)
            
            # Find notification elements (this would need platform-specific locators)
            notification_elements = self.driver.find_elements("class name", "android.widget.TextView")
            
            for element in notification_elements:
                try:
                    text = element.text
                    if text and len(text.strip()) > 0:
                        notifications.append({
                            'text': text,
                            'element': element
                        })
                except:
                    continue
            
            self.logger.info(f"Found {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            self.logger.error(f"Error getting notifications: {str(e)}")
            return []
    
    def clear_notifications(self) -> None:
        """Clear all notifications (Android only)."""
        try:
            self.open_notifications()
            time.sleep(1)
            
            # Look for clear all button (platform-specific implementation needed)
            try:
                clear_button = self.driver.find_element("id", "dismiss_text")
                clear_button.click()
                self.logger.info("Cleared all notifications")
            except:
                # Alternative method - swipe notifications away
                notifications = self.get_notifications()
                gesture_utils = MobileGestureUtils(self.driver)
                
                for notification in notifications:
                    try:
                        gesture_utils.swipe_screen(SwipeDirection.RIGHT)
                        time.sleep(0.5)
                    except:
                        continue
                
                self.logger.info("Attempted to clear notifications by swiping")
                
        except Exception as e:
            self.logger.error(f"Error clearing notifications: {str(e)}")
    
    def wait_for_notification(self, expected_text: str, timeout: int = 30) -> bool:
        """Wait for notification with specific text."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            notifications = self.get_notifications()
            
            for notification in notifications:
                if expected_text.lower() in notification['text'].lower():
                    self.logger.info(f"Found expected notification: {expected_text}")
                    return True
            
            time.sleep(2)
        
        self.logger.warning(f"Notification not found within {timeout} seconds: {expected_text}")
        return False
    
    def tap_notification(self, notification_text: str) -> bool:
        """Tap on notification containing specific text."""
        try:
            notifications = self.get_notifications()
            
            for notification in notifications:
                if notification_text.lower() in notification['text'].lower():
                    notification['element'].click()
                    self.logger.info(f"Tapped notification: {notification_text}")
                    return True
            
            self.logger.warning(f"Notification not found: {notification_text}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error tapping notification: {str(e)}")
            return False


class KeyboardUtils:
    """Utility class for keyboard operations."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
    
    def is_keyboard_shown(self) -> bool:
        """Check if keyboard is currently shown."""
        try:
            return self.driver.is_keyboard_shown()
        except Exception as e:
            self.logger.error(f"Error checking keyboard status: {str(e)}")
            return False
    
    def hide_keyboard(self) -> None:
        """Hide the keyboard."""
        try:
            if self.is_keyboard_shown():
                self.driver.hide_keyboard()
                self.logger.info("Hid keyboard")
        except Exception as e:
            self.logger.error(f"Error hiding keyboard: {str(e)}")
    
    def press_key(self, key_code: int) -> None:
        """Press key by key code (Android only)."""
        try:
            self.driver.press_keycode(key_code)
            self.logger.info(f"Pressed key code: {key_code}")
        except Exception as e:
            self.logger.error(f"Error pressing key: {str(e)}")
    
    def long_press_key(self, key_code: int) -> None:
        """Long press key by key code (Android only)."""
        try:
            self.driver.long_press_keycode(key_code)
            self.logger.info(f"Long pressed key code: {key_code}")
        except Exception as e:
            self.logger.error(f"Error long pressing key: {str(e)}")


class ScreenUtils:
    """Utility class for screen operations."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
    
    def get_screen_size(self) -> Dict[str, int]:
        """Get screen size."""
        try:
            size = self.driver.get_window_size()
            self.logger.info(f"Screen size: {size}")
            return size
        except Exception as e:
            self.logger.error(f"Error getting screen size: {str(e)}")
            return {'width': 0, 'height': 0}
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take screenshot."""
        try:
            if not filename:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mobile_screenshot_{timestamp}.png"
            
            screenshot_path = f"screenshots/{filename}"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return ""
    
    def get_page_source(self) -> str:
        """Get current page source."""
        try:
            source = self.driver.page_source
            self.logger.info("Retrieved page source")
            return source
        except Exception as e:
            self.logger.error(f"Error getting page source: {str(e)}")
            return ""