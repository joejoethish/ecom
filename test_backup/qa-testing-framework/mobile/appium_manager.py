"""
Appium Manager for mobile driver lifecycle management.

Handles Appium server configuration, device management, and driver lifecycle
for both iOS and Android platforms.
"""

import os
import time
import subprocess
from typing import Dict, Optional, Any, List
try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.options.ios import XCUITestOptions
except ImportError:
    # Fallback when appium is not installed
    class webdriver:
        class Remote:
            def __init__(self, *args, **kwargs): pass
            def quit(self): pass
            def implicitly_wait(self, timeout): pass
    
    class UiAutomator2Options:
        def __init__(self): pass
    
    class XCUITestOptions:
        def __init__(self): pass
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

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


class AppiumManager:
    """Manages Appium server and mobile driver lifecycle."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = Logger(__name__)
        self.driver: Optional[webdriver.Remote] = None
        self.server_process: Optional[subprocess.Popen] = None
        self.server_url = config.get_value('mobile.appium_server', 'http://localhost:4723')
        self.implicit_wait = config.get_value('mobile.timeout', 10)
        self.explicit_wait = config.get_value('mobile.timeout', 30)
        
    def start_appium_server(self, port: int = 4723) -> bool:
        """Start Appium server on specified port."""
        try:
            # Check if server is already running
            if self._is_server_running(port):
                self.logger.info(f"Appium server already running on port {port}")
                return True
                
            # Start Appium server
            cmd = [
                'appium',
                '--port', str(port),
                '--log-level', 'info',
                '--session-override'
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for server to start
            max_attempts = 30
            for attempt in range(max_attempts):
                if self._is_server_running(port):
                    self.logger.info(f"Appium server started successfully on port {port}")
                    return True
                time.sleep(1)
                
            self.logger.error("Failed to start Appium server within timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting Appium server: {str(e)}")
            return False
    
    def stop_appium_server(self) -> None:
        """Stop the Appium server."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.logger.info("Appium server stopped successfully")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.logger.warning("Appium server forcefully killed")
            except Exception as e:
                self.logger.error(f"Error stopping Appium server: {str(e)}")
            finally:
                self.server_process = None
    
    def create_android_driver(self, device_config: Dict[str, Any]) -> webdriver.Remote:
        """Create Android driver with specified configuration."""
        try:
            options = UiAutomator2Options()
            
            # Required capabilities
            options.platform_name = "Android"
            options.device_name = device_config.get('device_name', 'Android Emulator')
            options.platform_version = device_config.get('platform_version', '11.0')
            options.automation_name = "UiAutomator2"
            
            # App configuration
            if 'app_path' in device_config:
                options.app = device_config['app_path']
            elif 'app_package' in device_config and 'app_activity' in device_config:
                options.app_package = device_config['app_package']
                options.app_activity = device_config['app_activity']
            
            # Additional capabilities
            options.no_reset = device_config.get('no_reset', True)
            options.full_reset = device_config.get('full_reset', False)
            options.new_command_timeout = device_config.get('new_command_timeout', 300)
            options.auto_grant_permissions = device_config.get('auto_grant_permissions', True)
            
            # Performance settings
            options.skip_server_installation = device_config.get('skip_server_installation', True)
            options.skip_device_initialization = device_config.get('skip_device_initialization', True)
            
            self.driver = webdriver.Remote(self.server_url, options=options)
            self.driver.implicitly_wait(self.implicit_wait)
            
            self.logger.info(f"Android driver created successfully for device: {device_config.get('device_name')}")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"Failed to create Android driver: {str(e)}")
            raise
    
    def create_ios_driver(self, device_config: Dict[str, Any]) -> webdriver.Remote:
        """Create iOS driver with specified configuration."""
        try:
            options = XCUITestOptions()
            
            # Required capabilities
            options.platform_name = "iOS"
            options.device_name = device_config.get('device_name', 'iPhone Simulator')
            options.platform_version = device_config.get('platform_version', '15.0')
            options.automation_name = "XCUITest"
            
            # App configuration
            if 'app_path' in device_config:
                options.app = device_config['app_path']
            elif 'bundle_id' in device_config:
                options.bundle_id = device_config['bundle_id']
            
            # Additional capabilities
            options.no_reset = device_config.get('no_reset', True)
            options.full_reset = device_config.get('full_reset', False)
            options.new_command_timeout = device_config.get('new_command_timeout', 300)
            
            # iOS specific settings
            options.xcodeorg_id = device_config.get('xcodeorg_id')
            options.xcode_signing_id = device_config.get('xcode_signing_id')
            options.update_wda_bundleid = device_config.get('update_wda_bundleid')
            
            self.driver = webdriver.Remote(self.server_url, options=options)
            self.driver.implicitly_wait(self.implicit_wait)
            
            self.logger.info(f"iOS driver created successfully for device: {device_config.get('device_name')}")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"Failed to create iOS driver: {str(e)}")
            raise
    
    def quit_driver(self) -> None:
        """Quit the current driver session."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Mobile driver session ended successfully")
            except Exception as e:
                self.logger.error(f"Error quitting driver: {str(e)}")
            finally:
                self.driver = None
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get current device information."""
        if not self.driver:
            return {}
            
        try:
            return {
                'platform_name': self.driver.capabilities.get('platformName'),
                'platform_version': self.driver.capabilities.get('platformVersion'),
                'device_name': self.driver.capabilities.get('deviceName'),
                'device_udid': self.driver.capabilities.get('udid'),
                'app_package': self.driver.capabilities.get('appPackage'),
                'app_activity': self.driver.capabilities.get('appActivity'),
                'bundle_id': self.driver.capabilities.get('bundleId')
            }
        except Exception as e:
            self.logger.error(f"Error getting device info: {str(e)}")
            return {}
    
    def reset_app(self) -> None:
        """Reset the current application."""
        if self.driver:
            try:
                self.driver.reset()
                self.logger.info("Application reset successfully")
            except Exception as e:
                self.logger.error(f"Error resetting app: {str(e)}")
    
    def install_app(self, app_path: str) -> bool:
        """Install application on device."""
        if not self.driver:
            return False
            
        try:
            self.driver.install_app(app_path)
            self.logger.info(f"App installed successfully: {app_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error installing app: {str(e)}")
            return False
    
    def remove_app(self, app_id: str) -> bool:
        """Remove application from device."""
        if not self.driver:
            return False
            
        try:
            self.driver.remove_app(app_id)
            self.logger.info(f"App removed successfully: {app_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error removing app: {str(e)}")
            return False
    
    def is_app_installed(self, app_id: str) -> bool:
        """Check if application is installed on device."""
        if not self.driver:
            return False
            
        try:
            return self.driver.is_app_installed(app_id)
        except Exception as e:
            self.logger.error(f"Error checking app installation: {str(e)}")
            return False
    
    def activate_app(self, app_id: str) -> None:
        """Activate (bring to foreground) the specified app."""
        if self.driver:
            try:
                self.driver.activate_app(app_id)
                self.logger.info(f"App activated: {app_id}")
            except Exception as e:
                self.logger.error(f"Error activating app: {str(e)}")
    
    def terminate_app(self, app_id: str) -> None:
        """Terminate the specified app."""
        if self.driver:
            try:
                self.driver.terminate_app(app_id)
                self.logger.info(f"App terminated: {app_id}")
            except Exception as e:
                self.logger.error(f"Error terminating app: {str(e)}")
    
    def get_app_state(self, app_id: str) -> int:
        """Get the state of the specified app."""
        if not self.driver:
            return 0
            
        try:
            return self.driver.query_app_state(app_id)
        except Exception as e:
            self.logger.error(f"Error getting app state: {str(e)}")
            return 0
    
    def _is_server_running(self, port: int) -> bool:
        """Check if Appium server is running on specified port."""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def wait_for_element(self, locator: tuple, timeout: Optional[int] = None) -> Any:
        """Wait for element to be present and return it."""
        if not self.driver:
            raise RuntimeError("Driver not initialized")
            
        wait_time = timeout or self.explicit_wait
        wait = WebDriverWait(self.driver, wait_time)
        
        try:
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            self.logger.error(f"Element not found within {wait_time} seconds: {locator}")
            raise
    
    def wait_for_element_clickable(self, locator: tuple, timeout: Optional[int] = None) -> Any:
        """Wait for element to be clickable and return it."""
        if not self.driver:
            raise RuntimeError("Driver not initialized")
            
        wait_time = timeout or self.explicit_wait
        wait = WebDriverWait(self.driver, wait_time)
        
        try:
            return wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            self.logger.error(f"Element not clickable within {wait_time} seconds: {locator}")
            raise