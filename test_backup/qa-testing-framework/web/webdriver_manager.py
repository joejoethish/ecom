"""
WebDriver Manager for QA Testing Framework

Manages WebDriver lifecycle for Chrome, Firefox, Safari, and Edge browsers
with proper configuration, error handling, and resource cleanup.
"""

import os
import time
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException, TimeoutException
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    # Fallback for environments where webdriver-manager is not available
    ChromeDriverManager = None
    GeckoDriverManager = None
    EdgeChromiumDriverManager = None
import logging
from pathlib import Path

from ..core.interfaces import Environment
from ..core.config import get_config, get_value
from ..core.models import BrowserInfo
from ..core.error_handling import ErrorHandler


class WebDriverManager:
    """Manages WebDriver instances for different browsers"""
    
    SUPPORTED_BROWSERS = ["chrome", "firefox", "edge", "safari"]
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.active_drivers: Dict[str, WebDriver] = {}
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
        # Create screenshots directory
        self.screenshot_dir = Path(get_value("reporting.output_dir", "reports/screenshots", environment)) / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def create_driver(self, browser: str, headless: bool = False, **kwargs) -> WebDriver:
        """Create WebDriver instance for specified browser"""
        browser = browser.lower()
        
        if browser not in self.SUPPORTED_BROWSERS:
            raise ValueError(f"Unsupported browser: {browser}. Supported browsers: {self.SUPPORTED_BROWSERS}")
        
        try:
            if browser == "chrome":
                driver = self._create_chrome_driver(headless, **kwargs)
            elif browser == "firefox":
                driver = self._create_firefox_driver(headless, **kwargs)
            elif browser == "edge":
                driver = self._create_edge_driver(headless, **kwargs)
            elif browser == "safari":
                driver = self._create_safari_driver(**kwargs)
            else:
                raise ValueError(f"Browser {browser} not implemented")
            
            # Configure driver settings
            self._configure_driver(driver, browser)
            
            # Store active driver
            driver_id = f"{browser}_{int(time.time())}"
            self.active_drivers[driver_id] = driver
            
            self.logger.info(f"Created {browser} WebDriver with ID: {driver_id}")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create {browser} WebDriver: {str(e)}")
            raise WebDriverException(f"Failed to create {browser} WebDriver: {str(e)}")
    
    def _create_chrome_driver(self, headless: bool = False, **kwargs) -> WebDriver:
        """Create Chrome WebDriver instance"""
        options = ChromeOptions()
        
        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        
        # Headless mode
        if headless:
            options.add_argument("--headless")
        
        # Window size
        window_size = kwargs.get("window_size", self.config.get("window_size", "1920,1080"))
        options.add_argument(f"--window-size={window_size}")
        
        # User agent
        user_agent = kwargs.get("user_agent")
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")
        
        # Download directory
        download_dir = kwargs.get("download_dir", str(Path.cwd() / "downloads"))
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # Additional Chrome options
        additional_options = kwargs.get("chrome_options", [])
        for option in additional_options:
            options.add_argument(option)
        
        # Create service
        if ChromeDriverManager:
            service = ChromeService(ChromeDriverManager().install())
        else:
            service = ChromeService()  # Use system chromedriver
        
        return webdriver.Chrome(service=service, options=options)
    
    def _create_firefox_driver(self, headless: bool = False, **kwargs) -> WebDriver:
        """Create Firefox WebDriver instance"""
        options = FirefoxOptions()
        
        # Headless mode
        if headless:
            options.add_argument("--headless")
        
        # Window size
        window_size = kwargs.get("window_size", self.config.get("window_size", "1920,1080"))
        width, height = window_size.split(",")
        options.add_argument(f"--width={width}")
        options.add_argument(f"--height={height}")
        
        # Download directory
        download_dir = kwargs.get("download_dir", str(Path.cwd() / "downloads"))
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", download_dir)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                             "application/pdf,application/octet-stream,text/csv,application/vnd.ms-excel")
        
        # Additional Firefox preferences
        additional_prefs = kwargs.get("firefox_prefs", {})
        for key, value in additional_prefs.items():
            options.set_preference(key, value)
        
        # Create service
        if GeckoDriverManager:
            service = FirefoxService(GeckoDriverManager().install())
        else:
            service = FirefoxService()  # Use system geckodriver
        
        return webdriver.Firefox(service=service, options=options)
    
    def _create_edge_driver(self, headless: bool = False, **kwargs) -> WebDriver:
        """Create Edge WebDriver instance"""
        options = EdgeOptions()
        
        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        
        # Headless mode
        if headless:
            options.add_argument("--headless")
        
        # Window size
        window_size = kwargs.get("window_size", self.config.get("window_size", "1920,1080"))
        options.add_argument(f"--window-size={window_size}")
        
        # User agent
        user_agent = kwargs.get("user_agent")
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")
        
        # Download directory
        download_dir = kwargs.get("download_dir", str(Path.cwd() / "downloads"))
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # Create service
        if EdgeChromiumDriverManager:
            service = EdgeService(EdgeChromiumDriverManager().install())
        else:
            service = EdgeService()  # Use system edgedriver
        
        return webdriver.Edge(service=service, options=options)
    
    def _create_safari_driver(self, **kwargs) -> WebDriver:
        """Create Safari WebDriver instance"""
        # Safari doesn't support headless mode or many customization options
        options = SafariOptions()
        
        # Additional Safari options (limited)
        additional_options = kwargs.get("safari_options", {})
        for key, value in additional_options.items():
            setattr(options, key, value)
        
        return webdriver.Safari(options=options)
    
    def _configure_driver(self, driver: WebDriver, browser: str) -> None:
        """Configure WebDriver with common settings"""
        # Set timeouts
        timeout = self.config.get("timeout", 30)
        implicit_wait = self.config.get("implicit_wait", 10)
        
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(implicit_wait)
        
        # Maximize window (except for Safari which has limitations)
        if browser != "safari":
            try:
                driver.maximize_window()
            except Exception as e:
                self.logger.warning(f"Could not maximize window for {browser}: {str(e)}")
    
    def get_browser_info(self, driver: WebDriver) -> BrowserInfo:
        """Get browser information from WebDriver"""
        try:
            capabilities = driver.capabilities
            
            browser_name = capabilities.get("browserName", "unknown")
            browser_version = capabilities.get("browserVersion", capabilities.get("version", "unknown"))
            platform = capabilities.get("platformName", capabilities.get("platform", "unknown"))
            
            # Get user agent
            user_agent = driver.execute_script("return navigator.userAgent;")
            
            # Get viewport size
            viewport_size = driver.execute_script(
                "return {width: window.innerWidth, height: window.innerHeight};"
            )
            
            return BrowserInfo(
                name=browser_name,
                version=browser_version,
                platform=platform,
                user_agent=user_agent,
                viewport_size=viewport_size
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get browser info: {str(e)}")
            return BrowserInfo(
                name="unknown",
                version="unknown",
                platform="unknown",
                user_agent="unknown"
            )
    
    def capture_screenshot(self, driver: WebDriver, filename: Optional[str] = None) -> str:
        """Capture screenshot and return file path"""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            if not filename.endswith('.png'):
                filename += '.png'
            
            screenshot_path = self.screenshot_dir / filename
            
            # Capture screenshot
            driver.save_screenshot(str(screenshot_path))
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")
            return ""
    
    def wait_for_element(self, driver: WebDriver, locator: tuple, timeout: int = None) -> Any:
        """Wait for element to be present and return it"""
        timeout = timeout or self.config.get("timeout", 30)
        
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            return element
        except TimeoutException:
            self.logger.error(f"Element not found within {timeout} seconds: {locator}")
            raise
    
    def wait_for_element_clickable(self, driver: WebDriver, locator: tuple, timeout: int = None) -> Any:
        """Wait for element to be clickable and return it"""
        timeout = timeout or self.config.get("timeout", 30)
        
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.element_to_be_clickable(locator))
            return element
        except TimeoutException:
            self.logger.error(f"Element not clickable within {timeout} seconds: {locator}")
            raise
    
    def wait_for_page_load(self, driver: WebDriver, timeout: int = None) -> bool:
        """Wait for page to fully load"""
        timeout = timeout or self.config.get("timeout", 30)
        
        try:
            wait = WebDriverWait(driver, timeout)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            return True
        except TimeoutException:
            self.logger.error(f"Page did not load within {timeout} seconds")
            return False
    
    def scroll_to_element(self, driver: WebDriver, element) -> None:
        """Scroll to element to make it visible"""
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Small delay for smooth scrolling
        except Exception as e:
            self.logger.error(f"Failed to scroll to element: {str(e)}")
    
    def highlight_element(self, driver: WebDriver, element, duration: float = 1.0) -> None:
        """Highlight element for debugging purposes"""
        try:
            # Store original style
            original_style = element.get_attribute("style")
            
            # Apply highlight style
            driver.execute_script(
                "arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';",
                element
            )
            
            time.sleep(duration)
            
            # Restore original style
            driver.execute_script(f"arguments[0].style='{original_style}';", element)
            
        except Exception as e:
            self.logger.error(f"Failed to highlight element: {str(e)}")
    
    def execute_javascript(self, driver: WebDriver, script: str, *args) -> Any:
        """Execute JavaScript code in browser"""
        try:
            return driver.execute_script(script, *args)
        except Exception as e:
            self.logger.error(f"Failed to execute JavaScript: {str(e)}")
            raise
    
    def switch_to_frame(self, driver: WebDriver, frame_locator: tuple) -> None:
        """Switch to iframe"""
        try:
            frame = self.wait_for_element(driver, frame_locator)
            driver.switch_to.frame(frame)
        except Exception as e:
            self.logger.error(f"Failed to switch to frame: {str(e)}")
            raise
    
    def switch_to_default_content(self, driver: WebDriver) -> None:
        """Switch back to default content from iframe"""
        try:
            driver.switch_to.default_content()
        except Exception as e:
            self.logger.error(f"Failed to switch to default content: {str(e)}")
    
    def handle_alert(self, driver: WebDriver, action: str = "accept") -> Optional[str]:
        """Handle JavaScript alerts"""
        try:
            wait = WebDriverWait(driver, 5)
            alert = wait.until(EC.alert_is_present())
            
            alert_text = alert.text
            
            if action == "accept":
                alert.accept()
            elif action == "dismiss":
                alert.dismiss()
            else:
                raise ValueError(f"Invalid alert action: {action}")
            
            return alert_text
            
        except TimeoutException:
            self.logger.debug("No alert present")
            return None
        except Exception as e:
            self.logger.error(f"Failed to handle alert: {str(e)}")
            raise
    
    def get_driver_logs(self, driver: WebDriver, log_type: str = "browser") -> List[Dict[str, Any]]:
        """Get browser logs"""
        try:
            logs = driver.get_log(log_type)
            return logs
        except Exception as e:
            self.logger.error(f"Failed to get {log_type} logs: {str(e)}")
            return []
    
    def close_driver(self, driver: WebDriver) -> None:
        """Close specific WebDriver instance"""
        try:
            driver.quit()
            
            # Remove from active drivers
            driver_id = None
            for did, d in self.active_drivers.items():
                if d == driver:
                    driver_id = did
                    break
            
            if driver_id:
                del self.active_drivers[driver_id]
                self.logger.info(f"Closed WebDriver with ID: {driver_id}")
                
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {str(e)}")
    
    def close_all_drivers(self) -> None:
        """Close all active WebDriver instances"""
        for driver_id, driver in list(self.active_drivers.items()):
            try:
                driver.quit()
                self.logger.info(f"Closed WebDriver with ID: {driver_id}")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver {driver_id}: {str(e)}")
        
        self.active_drivers.clear()
    
    def get_active_drivers(self) -> Dict[str, WebDriver]:
        """Get all active WebDriver instances"""
        return self.active_drivers.copy()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close_all_drivers()