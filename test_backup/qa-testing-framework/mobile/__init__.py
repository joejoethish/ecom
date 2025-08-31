"""
Mobile Testing Module

Handles React Native mobile application testing using Appium.
Supports iOS and Android platform testing, touch gesture validation,
and push notification testing.
"""

from .appium_manager import AppiumManager
from .page_objects import (
    BaseMobilePage, AndroidPage, IOSPage, 
    MobilePageFactory, MobileElementActions
)
from .mobile_utils import (
    MobileGestureUtils, DeviceUtils, NotificationUtils,
    KeyboardUtils, ScreenUtils, DeviceOrientation, SwipeDirection
)
from .mobile_config import MobileConfig, DevicePool, Platform, DeviceType
from .test_mobile_auth import MobileAuthTests, LoginPage, RegisterPage, HomePage
from .test_mobile_navigation import MobileNavigationTests, NavigationTestPage
from .test_mobile_shopping import (
    MobileShoppingTests, ProductListPage, ProductDetailPage, 
    ShoppingCartPage, CheckoutPage
)
from .test_push_notifications import (
    PushNotificationTests, PushNotificationPage, MockNotificationService,
    NotificationType, NotificationPriority
)
from .mobile_ecommerce_suite import MobileEcommerceTestSuite, create_test_config
from .test_mobile_auth_integration import MobileAuthIntegrationTests, TestResult, UserTestData
from .test_mobile_user_journeys import (
    MobileUserJourneyTests, UserJourneyType, JourneyStep, UserJourney,
    ProductListPage as JourneyProductListPage, ProductDetailPage as JourneyProductDetailPage,
    ShoppingCartPage as JourneyShoppingCartPage, CheckoutPage as JourneyCheckoutPage,
    OrderConfirmationPage
)
from .test_offline_functionality import (
    MobileOfflineFunctionalityTests, NetworkManager, OfflineDataManager,
    NetworkState, OfflineAction, OfflineActionData, SyncResult, OfflinePage
)

__all__ = [
    # Core components
    'AppiumManager',
    'BaseMobilePage',
    'AndroidPage', 
    'IOSPage',
    'MobilePageFactory',
    'MobileElementActions',
    'MobileGestureUtils',
    'DeviceUtils',
    'NotificationUtils',
    'KeyboardUtils',
    'ScreenUtils',
    'DeviceOrientation',
    'SwipeDirection',
    'MobileConfig',
    'DevicePool',
    'Platform',
    'DeviceType',
    
    # Test suites
    'MobileAuthTests',
    'MobileNavigationTests',
    'MobileShoppingTests',
    'PushNotificationTests',
    'MobileEcommerceTestSuite',
    'MobileAuthIntegrationTests',
    'MobileUserJourneyTests',
    'MobileOfflineFunctionalityTests',
    
    # Page objects
    'LoginPage',
    'RegisterPage',
    'HomePage',
    'NavigationTestPage',
    'ProductListPage',
    'ProductDetailPage',
    'ShoppingCartPage',
    'CheckoutPage',
    'PushNotificationPage',
    'JourneyProductListPage',
    'JourneyProductDetailPage',
    'JourneyShoppingCartPage',
    'JourneyCheckoutPage',
    'OrderConfirmationPage',
    'OfflinePage',
    
    # Data structures
    'TestResult',
    'UserTestData',
    'JourneyStep',
    'UserJourney',
    'OfflineActionData',
    'SyncResult',
    
    # Enums
    'UserJourneyType',
    'NetworkState',
    'OfflineAction',
    
    # Utilities
    'MockNotificationService',
    'NotificationType',
    'NotificationPriority',
    'NetworkManager',
    'OfflineDataManager',
    'create_test_config'
]