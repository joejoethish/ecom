"""
Basic mobile testing utilities test without relative imports.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the core modules to avoid import issues
sys.modules['core'] = Mock()
sys.modules['core.config'] = Mock()
sys.modules['core.utils'] = Mock()

# Create mock classes
class MockConfigManager:
    def get_value(self, key, default=None):
        config_map = {
            'mobile.appium_server': 'http://localhost:4723',
            'mobile.timeout': 10
        }
        return config_map.get(key, default)

class MockLogger:
    def __init__(self, name):
        self.name = name
    
    def info(self, msg):
        pass
    
    def error(self, msg):
        pass
    
    def warning(self, msg):
        pass

# Set up mocks
sys.modules['core.config'].ConfigManager = MockConfigManager
sys.modules['core.utils'].Logger = MockLogger


def test_mobile_imports():
    """Test that mobile module components can be imported."""
    try:
        from mobile.mobile_utils import MobileGestureUtils, DeviceUtils, SwipeDirection
        from mobile.mobile_config import Platform, DeviceType
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import mobile modules: {e}")


def test_swipe_direction_enum():
    """Test SwipeDirection enumeration."""
    from mobile.mobile_utils import SwipeDirection
    
    assert SwipeDirection.UP.value == "up"
    assert SwipeDirection.DOWN.value == "down"
    assert SwipeDirection.LEFT.value == "left"
    assert SwipeDirection.RIGHT.value == "right"


def test_platform_enum():
    """Test Platform enumeration."""
    from mobile.mobile_config import Platform
    
    assert Platform.ANDROID.value == "Android"
    assert Platform.IOS.value == "iOS"


def test_device_type_enum():
    """Test DeviceType enumeration."""
    from mobile.mobile_config import DeviceType
    
    assert DeviceType.REAL_DEVICE.value == "real"
    assert DeviceType.EMULATOR.value == "emulator"
    assert DeviceType.SIMULATOR.value == "simulator"


@patch('mobile.mobile_utils.TouchAction')
def test_mobile_gesture_utils_init(mock_touch_action):
    """Test MobileGestureUtils initialization."""
    from mobile.mobile_utils import MobileGestureUtils
    
    mock_driver = Mock()
    mock_driver.get_window_size.return_value = {'width': 375, 'height': 667}
    
    gesture_utils = MobileGestureUtils(mock_driver)
    
    assert gesture_utils.driver == mock_driver
    assert gesture_utils.screen_size == {'width': 375, 'height': 667}


def test_device_utils_init():
    """Test DeviceUtils initialization."""
    from mobile.mobile_utils import DeviceUtils
    
    mock_driver = Mock()
    device_utils = DeviceUtils(mock_driver)
    
    assert device_utils.driver == mock_driver


def test_mobile_config_init():
    """Test MobileConfig initialization."""
    from mobile.mobile_config import MobileConfig
    
    config_manager = MockConfigManager()
    mobile_config = MobileConfig(config_manager)
    
    assert mobile_config.config == config_manager
    assert mobile_config.base_config is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])