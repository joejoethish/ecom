"""
Mobile testing configuration management.

Handles device configurations, capabilities, and environment settings
for mobile testing across different platforms and devices.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import os

try:
    from core.config import ConfigManager
except ImportError:
    # Fallback for testing
    class ConfigManager:
        def get_value(self, key, default=None):
            return default


class Platform(Enum):
    """Mobile platform enumeration."""
    ANDROID = "Android"
    IOS = "iOS"


class DeviceType(Enum):
    """Device type enumeration."""
    REAL_DEVICE = "real"
    EMULATOR = "emulator"
    SIMULATOR = "simulator"


class MobileConfig:
    """Configuration manager for mobile testing."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.base_config = self._load_base_config()
        
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base mobile configuration."""
        return {
            'appium': {
                'server_url': self.config.get_value('appium.server_url', 'http://localhost:4723'),
                'implicit_wait': self.config.get_value('appium.implicit_wait', 10),
                'explicit_wait': self.config.get_value('appium.explicit_wait', 30),
                'command_timeout': self.config.get_value('appium.command_timeout', 300),
                'new_command_timeout': self.config.get_value('appium.new_command_timeout', 300)
            },
            'screenshots': {
                'enabled': self.config.get_value('screenshots.enabled', True),
                'on_failure': self.config.get_value('screenshots.on_failure', True),
                'directory': self.config.get_value('screenshots.directory', 'screenshots/mobile')
            },
            'timeouts': {
                'app_launch': self.config.get_value('timeouts.app_launch', 30),
                'page_load': self.config.get_value('timeouts.page_load', 30),
                'element_wait': self.config.get_value('timeouts.element_wait', 10),
                'gesture_wait': self.config.get_value('timeouts.gesture_wait', 2)
            }
        }
    
    def get_android_config(self, device_name: str = "Android Emulator") -> Dict[str, Any]:
        """Get Android device configuration."""
        base_android = {
            'platformName': Platform.ANDROID.value,
            'automationName': 'UiAutomator2',
            'deviceName': device_name,
            'platformVersion': self.config.get_value('android.platform_version', '11.0'),
            'noReset': self.config.get_value('android.no_reset', True),
            'fullReset': self.config.get_value('android.full_reset', False),
            'autoGrantPermissions': self.config.get_value('android.auto_grant_permissions', True),
            'skipServerInstallation': self.config.get_value('android.skip_server_installation', True),
            'skipDeviceInitialization': self.config.get_value('android.skip_device_initialization', True),
            'unicodeKeyboard': self.config.get_value('android.unicode_keyboard', True),
            'resetKeyboard': self.config.get_value('android.reset_keyboard', True),
            'newCommandTimeout': self.base_config['appium']['new_command_timeout']
        }
        
        # Add app configuration if available
        app_path = self.config.get_value('android.app_path')
        if app_path and os.path.exists(app_path):
            base_android['app'] = app_path
        else:
            # Use package and activity for installed apps
            app_package = self.config.get_value('android.app_package')
            app_activity = self.config.get_value('android.app_activity')
            if app_package and app_activity:
                base_android['appPackage'] = app_package
                base_android['appActivity'] = app_activity
        
        return base_android
    
    def get_ios_config(self, device_name: str = "iPhone Simulator") -> Dict[str, Any]:
        """Get iOS device configuration."""
        base_ios = {
            'platformName': Platform.IOS.value,
            'automationName': 'XCUITest',
            'deviceName': device_name,
            'platformVersion': self.config.get_value('ios.platform_version', '15.0'),
            'noReset': self.config.get_value('ios.no_reset', True),
            'fullReset': self.config.get_value('ios.full_reset', False),
            'newCommandTimeout': self.base_config['appium']['new_command_timeout']
        }
        
        # Add app configuration if available
        app_path = self.config.get_value('ios.app_path')
        if app_path and os.path.exists(app_path):
            base_ios['app'] = app_path
        else:
            # Use bundle ID for installed apps
            bundle_id = self.config.get_value('ios.bundle_id')
            if bundle_id:
                base_ios['bundleId'] = bundle_id
        
        # Add iOS-specific signing configuration
        xcode_org_id = self.config.get_value('ios.xcode_org_id')
        if xcode_org_id:
            base_ios['xcodeOrgId'] = xcode_org_id
            
        xcode_signing_id = self.config.get_value('ios.xcode_signing_id')
        if xcode_signing_id:
            base_ios['xcodeSigningId'] = xcode_signing_id
            
        update_wda_bundleid = self.config.get_value('ios.update_wda_bundleid')
        if update_wda_bundleid:
            base_ios['updatedWDABundleId'] = update_wda_bundleid
        
        return base_ios
    
    def get_device_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured device configurations."""
        devices = {}
        
        # Android devices
        android_devices = self.config.get_value('devices.android', [])
        for device in android_devices:
            device_name = device.get('name', 'Android Device')
            config = self.get_android_config(device.get('device_name', device_name))
            
            # Override with device-specific settings
            if 'platform_version' in device:
                config['platformVersion'] = device['platform_version']
            if 'udid' in device:
                config['udid'] = device['udid']
            if 'system_port' in device:
                config['systemPort'] = device['system_port']
                
            devices[device_name] = config
        
        # iOS devices
        ios_devices = self.config.get_value('devices.ios', [])
        for device in ios_devices:
            device_name = device.get('name', 'iOS Device')
            config = self.get_ios_config(device.get('device_name', device_name))
            
            # Override with device-specific settings
            if 'platform_version' in device:
                config['platformVersion'] = device['platform_version']
            if 'udid' in device:
                config['udid'] = device['udid']
            if 'wda_local_port' in device:
                config['wdaLocalPort'] = device['wda_local_port']
                
            devices[device_name] = config
        
        # Add default devices if none configured
        if not devices:
            devices['Android Emulator'] = self.get_android_config()
            devices['iPhone Simulator'] = self.get_ios_config()
        
        return devices
    
    def get_app_config(self, platform: Platform) -> Dict[str, Any]:
        """Get application-specific configuration."""
        if platform == Platform.ANDROID:
            return {
                'package': self.config.get_value('android.app_package', 'com.ecommerce.app'),
                'activity': self.config.get_value('android.app_activity', '.MainActivity'),
                'wait_activity': self.config.get_value('android.wait_activity', '.MainActivity'),
                'app_path': self.config.get_value('android.app_path'),
                'install_timeout': self.config.get_value('android.install_timeout', 60000)
            }
        elif platform == Platform.IOS:
            return {
                'bundle_id': self.config.get_value('ios.bundle_id', 'com.ecommerce.app'),
                'app_path': self.config.get_value('ios.app_path'),
                'install_timeout': self.config.get_value('ios.install_timeout', 60000)
            }
        else:
            return {}
    
    def get_test_data_config(self) -> Dict[str, Any]:
        """Get test data configuration for mobile testing."""
        return {
            'users': {
                'test_user_email': self.config.get_value('test_data.mobile.user_email', 'mobile.test@example.com'),
                'test_user_password': self.config.get_value('test_data.mobile.user_password', 'TestPass123!'),
                'guest_user_email': self.config.get_value('test_data.mobile.guest_email', 'guest.mobile@example.com')
            },
            'products': {
                'test_product_id': self.config.get_value('test_data.mobile.product_id', 'TEST_PRODUCT_001'),
                'test_category': self.config.get_value('test_data.mobile.category', 'Electronics')
            },
            'payment': {
                'test_card_number': self.config.get_value('test_data.mobile.card_number', '4111111111111111'),
                'test_card_expiry': self.config.get_value('test_data.mobile.card_expiry', '12/25'),
                'test_card_cvv': self.config.get_value('test_data.mobile.card_cvv', '123')
            }
        }
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        env_config = {
            'base_url': self.config.get_value(f'environments.{environment}.mobile_url', 'http://localhost:3000'),
            'api_base_url': self.config.get_value(f'environments.{environment}.api_url', 'http://localhost:8000/api'),
            'deep_link_scheme': self.config.get_value(f'environments.{environment}.deep_link_scheme', 'ecommerce'),
            'push_notification_config': {
                'enabled': self.config.get_value(f'environments.{environment}.push_notifications', True),
                'test_token': self.config.get_value(f'environments.{environment}.push_test_token')
            }
        }
        
        return env_config
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance testing configuration."""
        return {
            'app_launch_timeout': self.config.get_value('performance.app_launch_timeout', 30),
            'page_load_timeout': self.config.get_value('performance.page_load_timeout', 10),
            'animation_timeout': self.config.get_value('performance.animation_timeout', 5),
            'network_timeout': self.config.get_value('performance.network_timeout', 30),
            'memory_threshold_mb': self.config.get_value('performance.memory_threshold_mb', 512),
            'cpu_threshold_percent': self.config.get_value('performance.cpu_threshold_percent', 80)
        }
    
    def get_accessibility_config(self) -> Dict[str, Any]:
        """Get accessibility testing configuration."""
        return {
            'enabled': self.config.get_value('accessibility.enabled', True),
            'check_labels': self.config.get_value('accessibility.check_labels', True),
            'check_contrast': self.config.get_value('accessibility.check_contrast', True),
            'check_touch_targets': self.config.get_value('accessibility.check_touch_targets', True),
            'min_touch_target_size': self.config.get_value('accessibility.min_touch_target_size', 44)
        }
    
    def validate_config(self, platform: Platform, device_config: Dict[str, Any]) -> List[str]:
        """Validate device configuration and return list of issues."""
        issues = []
        
        # Common validations
        if not device_config.get('platformName'):
            issues.append("Platform name is required")
            
        if not device_config.get('deviceName'):
            issues.append("Device name is required")
            
        if not device_config.get('platformVersion'):
            issues.append("Platform version is required")
        
        # Platform-specific validations
        if platform == Platform.ANDROID:
            if not device_config.get('app') and not (
                device_config.get('appPackage') and device_config.get('appActivity')
            ):
                issues.append("Android requires either app path or package/activity")
                
        elif platform == Platform.IOS:
            if not device_config.get('app') and not device_config.get('bundleId'):
                issues.append("iOS requires either app path or bundle ID")
        
        return issues


class DevicePool:
    """Manages a pool of available devices for parallel testing."""
    
    def __init__(self, mobile_config: MobileConfig):
        self.mobile_config = mobile_config
        self.available_devices = []
        self.in_use_devices = []
        self._initialize_device_pool()
    
    def _initialize_device_pool(self) -> None:
        """Initialize the device pool with configured devices."""
        device_configs = self.mobile_config.get_device_configs()
        
        for device_name, config in device_configs.items():
            device_info = {
                'name': device_name,
                'config': config,
                'platform': config['platformName'],
                'available': True
            }
            self.available_devices.append(device_info)
    
    def get_available_device(self, platform: Optional[Platform] = None) -> Optional[Dict[str, Any]]:
        """Get an available device from the pool."""
        for device in self.available_devices:
            if device['available']:
                if platform is None or device['platform'] == platform.value:
                    device['available'] = False
                    self.in_use_devices.append(device)
                    self.available_devices.remove(device)
                    return device
        
        return None
    
    def release_device(self, device_name: str) -> bool:
        """Release a device back to the pool."""
        for device in self.in_use_devices:
            if device['name'] == device_name:
                device['available'] = True
                self.in_use_devices.remove(device)
                self.available_devices.append(device)
                return True
        
        return False
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device pool status."""
        return {
            'total_devices': len(self.available_devices) + len(self.in_use_devices),
            'available_devices': len(self.available_devices),
            'in_use_devices': len(self.in_use_devices),
            'available_android': len([d for d in self.available_devices if d['platform'] == 'Android']),
            'available_ios': len([d for d in self.available_devices if d['platform'] == 'iOS']),
            'devices': {
                'available': [d['name'] for d in self.available_devices],
                'in_use': [d['name'] for d in self.in_use_devices]
            }
        }
    
    def reset_pool(self) -> None:
        """Reset the device pool, marking all devices as available."""
        all_devices = self.available_devices + self.in_use_devices
        
        for device in all_devices:
            device['available'] = True
        
        self.available_devices = all_devices
        self.in_use_devices = []