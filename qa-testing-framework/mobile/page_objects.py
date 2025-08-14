"""
Mobile Page Object Model base classes.

Provides base classes and utilities for implementing page object pattern
in mobile testing with Appium.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
try:
    from appium.webdriver.common.appiumby import AppiumBy
    from appium.webdriver.webdriver import WebDriver
except ImportError:
    # Fallback when appium is not installed
    class AppiumBy:
        ID = "id"
        ACCESSIBILITY_ID = "accessibility id"
        XPATH = "xpath"
        CLASS_NAME = "class name"
        ANDROID_UIAUTOMATOR = "android uiautomator"
        IOS_PREDICATE = "ios predicate string"
        IOS_CLASS_CHAIN = "ios class chain"
    
    class WebDriver: pass

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


class BaseMobilePage(ABC):
    """Base class for all mobile page objects."""
    
    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.logger = Logger(self.__class__.__name__)
        
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if the page is loaded."""
        pass
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> bool:
        """Wait for the page to load."""
        wait_time = timeout or self.timeout
        try:
            WebDriverWait(self.driver, wait_time).until(lambda driver: self.is_loaded())
            return True
        except TimeoutException:
            self.logger.error(f"Page {self.__class__.__name__} did not load within {wait_time} seconds")
            return False
    
    def find_element(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """Find element with explicit wait."""
        wait_time = timeout or self.timeout
        try:
            wait = WebDriverWait(self.driver, wait_time)
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            self.logger.error(f"Element not found: {locator}")
            raise
    
    def find_elements(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> List[Any]:
        """Find multiple elements with explicit wait."""
        wait_time = timeout or self.timeout
        try:
            wait = WebDriverWait(self.driver, wait_time)
            wait.until(EC.presence_of_element_located(locator))
            return self.driver.find_elements(*locator)
        except TimeoutException:
            self.logger.warning(f"Elements not found: {locator}")
            return []
    
    def is_element_present(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Check if element is present without throwing exception."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def is_element_visible(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Check if element is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_element_clickable(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """Wait for element to be clickable."""
        wait_time = timeout or self.timeout
        try:
            wait = WebDriverWait(self.driver, wait_time)
            return wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            self.logger.error(f"Element not clickable: {locator}")
            raise
    
    def click_element(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> None:
        """Click element with wait."""
        element = self.wait_for_element_clickable(locator, timeout)
        element.click()
        self.logger.info(f"Clicked element: {locator}")
    
    def send_keys(self, locator: Tuple[str, str], text: str, clear_first: bool = True) -> None:
        """Send keys to element."""
        element = self.find_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        self.logger.info(f"Sent keys to element {locator}: {text}")
    
    def get_text(self, locator: Tuple[str, str]) -> str:
        """Get text from element."""
        element = self.find_element(locator)
        text = element.text
        self.logger.info(f"Got text from element {locator}: {text}")
        return text
    
    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> str:
        """Get attribute value from element."""
        element = self.find_element(locator)
        value = element.get_attribute(attribute)
        self.logger.info(f"Got attribute {attribute} from element {locator}: {value}")
        return value
    
    def scroll_to_element(self, locator: Tuple[str, str]) -> None:
        """Scroll to element."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        self.logger.info(f"Scrolled to element: {locator}")
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take screenshot of current screen."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{self.__class__.__name__}_{timestamp}.png"
        
        screenshot_path = f"screenshots/{filename}"
        self.driver.save_screenshot(screenshot_path)
        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path


class AndroidPage(BaseMobilePage):
    """Base class for Android-specific page objects."""
    
    def __init__(self, driver: WebDriver, timeout: int = 30):
        super().__init__(driver, timeout)
        
    def find_by_id(self, resource_id: str, timeout: Optional[int] = None) -> Any:
        """Find element by Android resource ID."""
        locator = (AppiumBy.ID, resource_id)
        return self.find_element(locator, timeout)
    
    def find_by_accessibility_id(self, accessibility_id: str, timeout: Optional[int] = None) -> Any:
        """Find element by accessibility ID."""
        locator = (AppiumBy.ACCESSIBILITY_ID, accessibility_id)
        return self.find_element(locator, timeout)
    
    def find_by_xpath(self, xpath: str, timeout: Optional[int] = None) -> Any:
        """Find element by XPath."""
        locator = (AppiumBy.XPATH, xpath)
        return self.find_element(locator, timeout)
    
    def find_by_class_name(self, class_name: str, timeout: Optional[int] = None) -> Any:
        """Find element by class name."""
        locator = (AppiumBy.CLASS_NAME, class_name)
        return self.find_element(locator, timeout)
    
    def find_by_android_uiautomator(self, uiautomator: str, timeout: Optional[int] = None) -> Any:
        """Find element using Android UIAutomator."""
        locator = (AppiumBy.ANDROID_UIAUTOMATOR, uiautomator)
        return self.find_element(locator, timeout)
    
    def press_back_button(self) -> None:
        """Press Android back button."""
        self.driver.back()
        self.logger.info("Pressed Android back button")
    
    def press_home_button(self) -> None:
        """Press Android home button."""
        self.driver.press_keycode(3)  # KEYCODE_HOME
        self.logger.info("Pressed Android home button")
    
    def press_menu_button(self) -> None:
        """Press Android menu button."""
        self.driver.press_keycode(82)  # KEYCODE_MENU
        self.logger.info("Pressed Android menu button")
    
    def open_notifications(self) -> None:
        """Open Android notification panel."""
        self.driver.open_notifications()
        self.logger.info("Opened Android notifications")
    
    def get_current_activity(self) -> str:
        """Get current Android activity."""
        activity = self.driver.current_activity
        self.logger.info(f"Current activity: {activity}")
        return activity
    
    def get_current_package(self) -> str:
        """Get current Android package."""
        package = self.driver.current_package
        self.logger.info(f"Current package: {package}")
        return package


class IOSPage(BaseMobilePage):
    """Base class for iOS-specific page objects."""
    
    def __init__(self, driver: WebDriver, timeout: int = 30):
        super().__init__(driver, timeout)
        
    def find_by_accessibility_id(self, accessibility_id: str, timeout: Optional[int] = None) -> Any:
        """Find element by accessibility ID."""
        locator = (AppiumBy.ACCESSIBILITY_ID, accessibility_id)
        return self.find_element(locator, timeout)
    
    def find_by_xpath(self, xpath: str, timeout: Optional[int] = None) -> Any:
        """Find element by XPath."""
        locator = (AppiumBy.XPATH, xpath)
        return self.find_element(locator, timeout)
    
    def find_by_class_name(self, class_name: str, timeout: Optional[int] = None) -> Any:
        """Find element by class name."""
        locator = (AppiumBy.CLASS_NAME, class_name)
        return self.find_element(locator, timeout)
    
    def find_by_ios_predicate(self, predicate: str, timeout: Optional[int] = None) -> Any:
        """Find element using iOS predicate string."""
        locator = (AppiumBy.IOS_PREDICATE, predicate)
        return self.find_element(locator, timeout)
    
    def find_by_ios_class_chain(self, class_chain: str, timeout: Optional[int] = None) -> Any:
        """Find element using iOS class chain."""
        locator = (AppiumBy.IOS_CLASS_CHAIN, class_chain)
        return self.find_element(locator, timeout)
    
    def shake_device(self) -> None:
        """Shake the iOS device."""
        self.driver.shake()
        self.logger.info("Shook iOS device")
    
    def lock_device(self, duration: int = 5) -> None:
        """Lock iOS device for specified duration."""
        self.driver.lock(duration)
        self.logger.info(f"Locked iOS device for {duration} seconds")
    
    def background_app(self, duration: int = 5) -> None:
        """Put app in background for specified duration."""
        self.driver.background_app(duration)
        self.logger.info(f"Put app in background for {duration} seconds")
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get iOS device battery information."""
        try:
            battery_info = self.driver.battery_info
            self.logger.info(f"Battery info: {battery_info}")
            return battery_info
        except Exception as e:
            self.logger.error(f"Error getting battery info: {str(e)}")
            return {}


class MobilePageFactory:
    """Factory class for creating platform-specific page objects."""
    
    @staticmethod
    def create_page(page_class, driver: WebDriver, timeout: int = 30):
        """Create page object based on platform."""
        platform = driver.capabilities.get('platformName', '').lower()
        
        if platform == 'android':
            # Create Android-specific page if available
            android_class_name = f"Android{page_class.__name__}"
            if hasattr(page_class.__module__, android_class_name):
                android_class = getattr(page_class.__module__, android_class_name)
                return android_class(driver, timeout)
            else:
                return page_class(driver, timeout)
                
        elif platform == 'ios':
            # Create iOS-specific page if available
            ios_class_name = f"IOS{page_class.__name__}"
            if hasattr(page_class.__module__, ios_class_name):
                ios_class = getattr(page_class.__module__, ios_class_name)
                return ios_class(driver, timeout)
            else:
                return page_class(driver, timeout)
        else:
            return page_class(driver, timeout)


class MobileElementActions:
    """Utility class for common mobile element actions."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = Logger(self.__class__.__name__)
    
    def long_press(self, element, duration: int = 1000) -> None:
        """Perform long press on element."""
        from appium.webdriver.common.touch_action import TouchAction
        
        action = TouchAction(self.driver)
        action.long_press(element, duration=duration).release().perform()
        self.logger.info(f"Long pressed element for {duration}ms")
    
    def double_tap(self, element) -> None:
        """Perform double tap on element."""
        from appium.webdriver.common.touch_action import TouchAction
        
        action = TouchAction(self.driver)
        action.tap(element).tap(element).perform()
        self.logger.info("Double tapped element")
    
    def swipe_element(self, element, direction: str, distance: int = 100) -> None:
        """Swipe element in specified direction."""
        from appium.webdriver.common.touch_action import TouchAction
        
        size = element.size
        location = element.location
        
        start_x = location['x'] + size['width'] // 2
        start_y = location['y'] + size['height'] // 2
        
        if direction.lower() == 'left':
            end_x = start_x - distance
            end_y = start_y
        elif direction.lower() == 'right':
            end_x = start_x + distance
            end_y = start_y
        elif direction.lower() == 'up':
            end_x = start_x
            end_y = start_y - distance
        elif direction.lower() == 'down':
            end_x = start_x
            end_y = start_y + distance
        else:
            raise ValueError(f"Invalid direction: {direction}")
        
        action = TouchAction(self.driver)
        action.press(x=start_x, y=start_y).move_to(x=end_x, y=end_y).release().perform()
        self.logger.info(f"Swiped element {direction} by {distance} pixels")
    
    def pinch_zoom(self, element, scale: float = 2.0) -> None:
        """Perform pinch zoom on element."""
        try:
            self.driver.pinch(element=element)
            self.logger.info(f"Pinch zoomed element with scale {scale}")
        except Exception as e:
            self.logger.error(f"Error performing pinch zoom: {str(e)}")
    
    def zoom(self, element, scale: float = 2.0) -> None:
        """Perform zoom on element."""
        try:
            self.driver.zoom(element=element)
            self.logger.info(f"Zoomed element with scale {scale}")
        except Exception as e:
            self.logger.error(f"Error performing zoom: {str(e)}")