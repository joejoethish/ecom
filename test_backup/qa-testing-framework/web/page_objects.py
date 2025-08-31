"""
Page Object Model Base Classes for Web Testing

Provides base classes and utilities for implementing the Page Object Model pattern
with common functionality for web element interactions and page validation.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException,
    StaleElementReferenceException
)
import logging
from abc import ABC, abstractmethod

from .webdriver_manager import WebDriverManager


class BasePage(ABC):
    """Base class for all page objects"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager):
        self.driver = driver
        self.webdriver_manager = webdriver_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.wait = WebDriverWait(driver, 30)
        
        # Common page elements
        self.loading_spinner = (By.CSS_SELECTOR, ".loading, .spinner, [data-testid='loading']")
        self.error_message = (By.CSS_SELECTOR, ".error, .alert-danger, [data-testid='error']")
        self.success_message = (By.CSS_SELECTOR, ".success, .alert-success, [data-testid='success']")
    
    @property
    @abstractmethod
    def page_url(self) -> str:
        """URL pattern for this page"""
        pass
    
    @property
    @abstractmethod
    def page_title(self) -> str:
        """Expected page title"""
        pass
    
    @property
    @abstractmethod
    def unique_element(self) -> Tuple[str, str]:
        """Unique element that identifies this page"""
        pass
    
    def navigate_to(self, url: str = None) -> None:
        """Navigate to the page"""
        target_url = url or self.page_url
        self.logger.info(f"Navigating to: {target_url}")
        self.driver.get(target_url)
        self.wait_for_page_load()
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for page to fully load"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for unique element to be present
            self.wait_for_element(self.unique_element, timeout)
            
            # Wait for any loading spinners to disappear
            self.wait_for_loading_to_complete()
            
            return True
        except TimeoutException:
            self.logger.error(f"Page did not load within {timeout} seconds")
            return False
    
    def wait_for_loading_to_complete(self, timeout: int = 10) -> None:
        """Wait for loading spinners to disappear"""
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self.loading_spinner)
            )
        except TimeoutException:
            # Loading spinner might not be present, which is fine
            pass
    
    def is_page_loaded(self) -> bool:
        """Check if page is fully loaded"""
        try:
            # Check if unique element is present
            self.find_element(self.unique_element)
            
            # Check if page title matches (if not empty)
            if self.page_title and self.page_title.strip():
                current_title = self.driver.title
                if self.page_title not in current_title:
                    return False
            
            return True
        except NoSuchElementException:
            return False
    
    def find_element(self, locator: Tuple[str, str], timeout: int = 10) -> WebElement:
        """Find single element with wait"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {locator}")
            raise NoSuchElementException(f"Element not found: {locator}")
    
    def find_elements(self, locator: Tuple[str, str], timeout: int = 10) -> List[WebElement]:
        """Find multiple elements with wait"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return self.driver.find_elements(*locator)
        except TimeoutException:
            self.logger.warning(f"No elements found: {locator}")
            return []
    
    def find_clickable_element(self, locator: Tuple[str, str], timeout: int = 10) -> WebElement:
        """Find clickable element with wait"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            self.logger.error(f"Element not clickable: {locator}")
            raise ElementNotInteractableException(f"Element not clickable: {locator}")
    
    def click_element(self, locator: Tuple[str, str], timeout: int = 10) -> None:
        """Click element with retry logic"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                element = self.find_clickable_element(locator, timeout)
                self.webdriver_manager.scroll_to_element(self.driver, element)
                element.click()
                return
            except (StaleElementReferenceException, ElementNotInteractableException) as e:
                if attempt == max_attempts - 1:
                    self.logger.error(f"Failed to click element after {max_attempts} attempts: {locator}")
                    raise
                self.logger.warning(f"Retry clicking element (attempt {attempt + 1}): {str(e)}")
                time.sleep(1)
    
    def send_keys_to_element(self, locator: Tuple[str, str], text: str, clear_first: bool = True, timeout: int = 10) -> None:
        """Send keys to element"""
        element = self.find_element(locator, timeout)
        self.webdriver_manager.scroll_to_element(self.driver, element)
        
        if clear_first:
            element.clear()
        
        element.send_keys(text)
    
    def get_element_text(self, locator: Tuple[str, str], timeout: int = 10) -> str:
        """Get text from element"""
        element = self.find_element(locator, timeout)
        return element.text.strip()
    
    def get_element_attribute(self, locator: Tuple[str, str], attribute: str, timeout: int = 10) -> str:
        """Get attribute value from element"""
        element = self.find_element(locator, timeout)
        return element.get_attribute(attribute) or ""
    
    def is_element_present(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Check if element is present"""
        try:
            self.find_element(locator, timeout)
            return True
        except (NoSuchElementException, TimeoutException):
            return False
    
    def is_element_visible(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Check if element is visible"""
        try:
            element = self.find_element(locator, timeout)
            return element.is_displayed()
        except (NoSuchElementException, TimeoutException):
            return False
    
    def is_element_enabled(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """Check if element is enabled"""
        try:
            element = self.find_element(locator, timeout)
            return element.is_enabled()
        except (NoSuchElementException, TimeoutException):
            return False
    
    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 10) -> WebElement:
        """Wait for element to be visible"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException:
            self.logger.error(f"Element not visible within {timeout} seconds: {locator}")
            raise
    
    def wait_for_element_invisible(self, locator: Tuple[str, str], timeout: int = 10) -> bool:
        """Wait for element to become invisible"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            self.logger.error(f"Element still visible after {timeout} seconds: {locator}")
            return False
    
    def wait_for_text_in_element(self, locator: Tuple[str, str], text: str, timeout: int = 10) -> bool:
        """Wait for specific text to appear in element"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator, text)
            )
            return True
        except TimeoutException:
            self.logger.error(f"Text '{text}' not found in element within {timeout} seconds: {locator}")
            return False
    
    def select_dropdown_by_text(self, locator: Tuple[str, str], text: str, timeout: int = 10) -> None:
        """Select dropdown option by visible text"""
        element = self.find_element(locator, timeout)
        select = Select(element)
        select.select_by_visible_text(text)
    
    def select_dropdown_by_value(self, locator: Tuple[str, str], value: str, timeout: int = 10) -> None:
        """Select dropdown option by value"""
        element = self.find_element(locator, timeout)
        select = Select(element)
        select.select_by_value(value)
    
    def get_dropdown_options(self, locator: Tuple[str, str], timeout: int = 10) -> List[str]:
        """Get all dropdown options"""
        element = self.find_element(locator, timeout)
        select = Select(element)
        return [option.text for option in select.options]
    
    def hover_over_element(self, locator: Tuple[str, str], timeout: int = 10) -> None:
        """Hover over element"""
        element = self.find_element(locator, timeout)
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
    
    def double_click_element(self, locator: Tuple[str, str], timeout: int = 10) -> None:
        """Double click element"""
        element = self.find_clickable_element(locator, timeout)
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
    
    def right_click_element(self, locator: Tuple[str, str], timeout: int = 10) -> None:
        """Right click element"""
        element = self.find_element(locator, timeout)
        actions = ActionChains(self.driver)
        actions.context_click(element).perform()
    
    def drag_and_drop(self, source_locator: Tuple[str, str], target_locator: Tuple[str, str], timeout: int = 10) -> None:
        """Drag and drop element"""
        source = self.find_element(source_locator, timeout)
        target = self.find_element(target_locator, timeout)
        actions = ActionChains(self.driver)
        actions.drag_and_drop(source, target).perform()
    
    def scroll_to_top(self) -> None:
        """Scroll to top of page"""
        self.driver.execute_script("window.scrollTo(0, 0);")
    
    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    def scroll_by_pixels(self, x: int, y: int) -> None:
        """Scroll by specific pixel amount"""
        self.driver.execute_script(f"window.scrollBy({x}, {y});")
    
    def press_key(self, key: str) -> None:
        """Press keyboard key"""
        actions = ActionChains(self.driver)
        actions.send_keys(getattr(Keys, key.upper())).perform()
    
    def press_key_combination(self, *keys) -> None:
        """Press key combination (e.g., Ctrl+C)"""
        actions = ActionChains(self.driver)
        for key in keys[:-1]:
            actions.key_down(getattr(Keys, key.upper()))
        actions.send_keys(getattr(Keys, keys[-1].upper()))
        for key in reversed(keys[:-1]):
            actions.key_up(getattr(Keys, key.upper()))
        actions.perform()
    
    def switch_to_new_window(self) -> str:
        """Switch to newly opened window/tab"""
        current_window = self.driver.current_window_handle
        all_windows = self.driver.window_handles
        
        for window in all_windows:
            if window != current_window:
                self.driver.switch_to.window(window)
                return window
        
        raise Exception("No new window found")
    
    def close_current_window(self) -> None:
        """Close current window and switch to previous"""
        self.driver.close()
        if len(self.driver.window_handles) > 0:
            self.driver.switch_to.window(self.driver.window_handles[0])
    
    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """Get current page title"""
        return self.driver.title
    
    def get_page_source(self) -> str:
        """Get page source"""
        return self.driver.page_source
    
    def refresh_page(self) -> None:
        """Refresh current page"""
        self.driver.refresh()
        self.wait_for_page_load()
    
    def go_back(self) -> None:
        """Navigate back in browser history"""
        self.driver.back()
        self.wait_for_page_load()
    
    def go_forward(self) -> None:
        """Navigate forward in browser history"""
        self.driver.forward()
        self.wait_for_page_load()
    
    def execute_javascript(self, script: str, *args) -> Any:
        """Execute JavaScript code"""
        return self.webdriver_manager.execute_javascript(self.driver, script, *args)
    
    def capture_screenshot(self, filename: str = None) -> str:
        """Capture screenshot of current page"""
        return self.webdriver_manager.capture_screenshot(self.driver, filename)
    
    def get_error_message(self) -> str:
        """Get error message if present"""
        try:
            return self.get_element_text(self.error_message, timeout=5)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def get_success_message(self) -> str:
        """Get success message if present"""
        try:
            return self.get_element_text(self.success_message, timeout=5)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def has_error_message(self) -> bool:
        """Check if error message is present"""
        return self.is_element_present(self.error_message, timeout=5)
    
    def has_success_message(self) -> bool:
        """Check if success message is present"""
        return self.is_element_present(self.success_message, timeout=5)
    
    def wait_for_ajax_complete(self, timeout: int = 30) -> bool:
        """Wait for AJAX requests to complete"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return jQuery.active == 0") if 
                d.execute_script("return typeof jQuery !== 'undefined'") else True
            )
            return True
        except TimeoutException:
            self.logger.warning("AJAX requests may still be pending")
            return False
    
    def get_browser_logs(self) -> List[Dict[str, Any]]:
        """Get browser console logs"""
        return self.webdriver_manager.get_driver_logs(self.driver, "browser")
    
    def clear_browser_logs(self) -> None:
        """Clear browser console logs"""
        self.driver.get_log("browser")  # Getting logs clears them
    
    def validate_page(self) -> Dict[str, bool]:
        """Validate page is loaded correctly"""
        validation_results = {
            "page_loaded": self.is_page_loaded(),
            "unique_element_present": self.is_element_present(self.unique_element),
            "no_javascript_errors": len([log for log in self.get_browser_logs() 
                                       if log.get("level") == "SEVERE"]) == 0
        }
        
        if self.page_title:
            validation_results["title_correct"] = self.page_title in self.get_page_title()
        
        return validation_results


class BaseFormPage(BasePage):
    """Base class for pages with forms"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager):
        super().__init__(driver, webdriver_manager)
        
        # Common form elements
        self.submit_button = (By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .submit-btn")
        self.cancel_button = (By.CSS_SELECTOR, ".cancel-btn, .btn-cancel, [data-testid='cancel']")
        self.form_container = (By.CSS_SELECTOR, "form, .form-container, [data-testid='form']")
    
    def fill_form_field(self, field_locator: Tuple[str, str], value: str, clear_first: bool = True) -> None:
        """Fill form field with value"""
        self.send_keys_to_element(field_locator, value, clear_first)
    
    def submit_form(self) -> None:
        """Submit the form"""
        self.click_element(self.submit_button)
    
    def cancel_form(self) -> None:
        """Cancel form submission"""
        self.click_element(self.cancel_button)
    
    def get_form_validation_errors(self) -> List[str]:
        """Get form validation error messages"""
        error_selectors = [
            ".field-error", ".form-error", ".validation-error",
            ".error", ".invalid-feedback", "[data-testid*='error']"
        ]
        
        errors = []
        for selector in error_selectors:
            error_elements = self.find_elements((By.CSS_SELECTOR, selector), timeout=2)
            for element in error_elements:
                if element.is_displayed():
                    error_text = element.text.strip()
                    if error_text:
                        errors.append(error_text)
        
        return errors
    
    def has_form_validation_errors(self) -> bool:
        """Check if form has validation errors"""
        return len(self.get_form_validation_errors()) > 0
    
    def is_form_field_required(self, field_locator: Tuple[str, str]) -> bool:
        """Check if form field is required"""
        try:
            element = self.find_element(field_locator)
            return (element.get_attribute("required") is not None or
                   "required" in element.get_attribute("class") or "")
        except NoSuchElementException:
            return False
    
    def get_form_field_value(self, field_locator: Tuple[str, str]) -> str:
        """Get current value of form field"""
        element = self.find_element(field_locator)
        return element.get_attribute("value") or ""


class BaseListPage(BasePage):
    """Base class for pages with lists/tables"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager):
        super().__init__(driver, webdriver_manager)
        
        # Common list elements
        self.list_container = (By.CSS_SELECTOR, ".list-container, table, .data-table")
        self.list_items = (By.CSS_SELECTOR, ".list-item, tr, .item")
        self.pagination_container = (By.CSS_SELECTOR, ".pagination, .pager")
        self.next_page_button = (By.CSS_SELECTOR, ".next, .page-next, [aria-label='Next']")
        self.previous_page_button = (By.CSS_SELECTOR, ".prev, .page-prev, [aria-label='Previous']")
        self.search_box = (By.CSS_SELECTOR, ".search-input, input[type='search'], [placeholder*='search']")
    
    def get_list_items(self) -> List[WebElement]:
        """Get all list items"""
        return self.find_elements(self.list_items)
    
    def get_list_item_count(self) -> int:
        """Get count of list items"""
        return len(self.get_list_items())
    
    def search_list(self, search_term: str) -> None:
        """Search in list"""
        if self.is_element_present(self.search_box):
            self.send_keys_to_element(self.search_box, search_term)
            self.press_key("ENTER")
            self.wait_for_loading_to_complete()
    
    def go_to_next_page(self) -> bool:
        """Go to next page if available"""
        if self.is_element_present(self.next_page_button) and self.is_element_enabled(self.next_page_button):
            self.click_element(self.next_page_button)
            self.wait_for_loading_to_complete()
            return True
        return False
    
    def go_to_previous_page(self) -> bool:
        """Go to previous page if available"""
        if self.is_element_present(self.previous_page_button) and self.is_element_enabled(self.previous_page_button):
            self.click_element(self.previous_page_button)
            self.wait_for_loading_to_complete()
            return True
        return False
    
    def has_pagination(self) -> bool:
        """Check if pagination is present"""
        return self.is_element_present(self.pagination_container)