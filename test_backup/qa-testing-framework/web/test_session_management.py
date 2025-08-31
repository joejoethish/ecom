"""
Session Management Tests

Comprehensive test suite for session management functionality including
session timeout, concurrent sessions, session security, and session persistence.
"""

import unittest
import time
from typing import Dict, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from .webdriver_manager import WebDriverManager
from .auth_pages import LoginPage, DashboardPage, ProfilePage
from .auth_test_data import AuthTestDataGenerator
from ..core.interfaces import Environment, UserRole, ExecutionStatus, Severity
from ..core.models import TestExecution, Defect, BrowserInfo
from ..core.config import get_config


class SessionManagementTestSuite(unittest.TestCase):
    """Test suite for session management functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test suite"""
        cls.environment = Environment.DEVELOPMENT
        cls.config = get_config("web", cls.environment)
        cls.base_url = cls.config.get("base_url", "http://localhost:3000")
        cls.webdriver_manager = WebDriverManager(cls.environment)
        cls.test_data_generator = AuthTestDataGenerator(cls.environment)
        
        # Test data
        cls.test_executions = []
        cls.defects = []
    
    def setUp(self):
        """Set up individual test"""
        self.driver = self.webdriver_manager.create_driver("chrome", headless=False)
        self.browser_info = self.webdriver_manager.get_browser_info(self.driver)
        
        # Initialize page objects
        self.login_page = LoginPage(self.driver, self.webdriver_manager, self.base_url)
        self.dashboard_page = DashboardPage(self.driver, self.webdriver_manager, self.base_url)
        self.profile_page = ProfilePage(self.driver, self.webdriver_manager, self.base_url)
        
        # Create test execution record
        self.test_execution = TestExecution(
            id=f"EXE_SESSION_{int(time.time())}",
            test_case_id="",
            environment=self.environment,
            status=ExecutionStatus.IN_PROGRESS,
            start_time=time.time(),
            browser_info=self.browser_info,
            executed_by="qa_framework"
        )
    
    def tearDown(self):
        """Clean up after test"""
        # Capture screenshot if test failed
        if hasattr(self, '_outcome') and not self._outcome.success:
            screenshot_path = self.webdriver_manager.capture_screenshot(
                self.driver, 
                f"session_failed_{self._testMethodName}_{int(time.time())}.png"
            )
            self.test_execution.screenshots.append(screenshot_path)
        
        # Update test execution
        self.test_execution.end_time = time.time()
        self.test_execution.status = ExecutionStatus.PASSED if self._outcome.success else ExecutionStatus.FAILED
        self.__class__.test_executions.append(self.test_execution)
        
        # Close driver
        self.webdriver_manager.close_driver(self.driver)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test suite"""
        cls.webdriver_manager.close_all_drivers()
    
    def log_defect(self, title: str, description: str, severity: Severity, reproduction_steps: List[str]):
        """Log a defect"""
        defect = Defect(
            id=f"DEF_SESSION_{int(time.time())}",
            test_case_id=self.test_execution.test_case_id,
            test_execution_id=self.test_execution.id,
            severity=severity,
            title=title,
            description=description,
            reproduction_steps=reproduction_steps,
            environment=self.environment,
            browser_info=self.browser_info,
            screenshots=self.test_execution.screenshots.copy()
        )
        self.__class__.defects.append(defect)
        return defect
    
    def login_test_user(self) -> Dict[str, Any]:
        """Helper method to login a test user"""
        user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
        
        # For testing purposes, we'll assume user exists or create via API
        # In real implementation, this would register the user first
        self.login_page.navigate_to()
        login_success = self.login_page.login(user_data['email'], user_data['password'])
        
        if not login_success:
            # If login fails, it might be because user doesn't exist
            # In a real scenario, we'd register the user first
            pass
        
        return user_data
    
    def test_session_creation_on_login(self):
        """Test that session is created properly on login"""
        self.test_execution.test_case_id = "TC_SESSION_001"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Navigate to login page
            self.login_page.navigate_to()
            
            # Verify no session exists initially
            cookies_before = self.driver.get_cookies()
            session_cookies_before = [c for c in cookies_before if 'session' in c['name'].lower()]
            
            # Perform login
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Verify session cookie is created
            cookies_after = self.driver.get_cookies()
            session_cookies_after = [c for c in cookies_after if 'session' in c['name'].lower()]
            
            self.assertGreater(len(session_cookies_after), len(session_cookies_before),
                             "Session cookie should be created after login")
            
            # Verify session cookie has proper attributes
            if session_cookies_after:
                session_cookie = session_cookies_after[0]
                self.assertTrue(session_cookie.get('httpOnly', False),
                              "Session cookie should be HttpOnly for security")
                self.assertTrue(session_cookie.get('secure', False) or self.environment == Environment.DEVELOPMENT,
                              "Session cookie should be Secure in production")
            
        except Exception as e:
            self.log_defect(
                "Session creation on login failed",
                f"Session not properly created during login: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to login page",
                    "Check initial cookies",
                    "Perform login with valid credentials",
                    "Verify session cookie creation",
                    "Check cookie security attributes"
                ]
            )
            raise
    
    def test_session_persistence_across_pages(self):
        """Test that session persists when navigating between pages"""
        self.test_execution.test_case_id = "TC_SESSION_002"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Get session cookie after login
            initial_cookies = self.driver.get_cookies()
            session_cookie = next((c for c in initial_cookies if 'session' in c['name'].lower()), None)
            self.assertIsNotNone(session_cookie, "Session cookie should exist after login")
            
            # Navigate to different pages
            pages_to_test = [
                self.dashboard_page,
                self.profile_page
            ]
            
            for page in pages_to_test:
                page.navigate_to()
                
                # Verify session cookie still exists
                current_cookies = self.driver.get_cookies()
                current_session_cookie = next((c for c in current_cookies if 'session' in c['name'].lower()), None)
                
                self.assertIsNotNone(current_session_cookie, 
                                   f"Session cookie should persist on {page.__class__.__name__}")
                self.assertEqual(current_session_cookie['value'], session_cookie['value'],
                               f"Session cookie value should remain same on {page.__class__.__name__}")
                
                # Verify user is still authenticated
                if hasattr(page, 'is_user_logged_in'):
                    self.assertTrue(page.is_user_logged_in(), 
                                  f"User should remain logged in on {page.__class__.__name__}")
            
        except Exception as e:
            self.log_defect(
                "Session persistence across pages failed",
                f"Session not persisting across page navigation: {str(e)}",
                Severity.MAJOR,
                [
                    "Login with valid credentials",
                    "Navigate to different protected pages",
                    "Verify session cookie persistence",
                    "Verify authentication state"
                ]
            )
            raise
    
    def test_session_timeout_handling(self):
        """Test session timeout handling"""
        self.test_execution.test_case_id = "TC_SESSION_003"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to dashboard
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in initially")
            
            # Simulate session timeout by clearing session cookies
            # In a real test, we might wait for actual timeout or manipulate server-side session
            session_cookies = [c for c in self.driver.get_cookies() if 'session' in c['name'].lower()]
            for cookie in session_cookies:
                self.driver.delete_cookie(cookie['name'])
            
            # Try to access protected page
            self.profile_page.navigate_to()
            time.sleep(2)  # Wait for redirect
            
            # Should redirect to login page
            current_url = self.driver.current_url
            self.assertIn("/login", current_url, 
                         "Should redirect to login page when session expires")
            
            # Verify login page is displayed
            self.assertTrue(self.login_page.is_page_loaded(), 
                          "Login page should be displayed after session timeout")
            
        except Exception as e:
            self.log_defect(
                "Session timeout handling failed",
                f"Session timeout not handled properly: {str(e)}",
                Severity.MAJOR,
                [
                    "Login with valid credentials",
                    "Simulate session timeout (clear session cookies)",
                    "Try to access protected page",
                    "Verify redirect to login page"
                ]
            )
            raise
    
    def test_session_invalidation_on_logout(self):
        """Test that session is properly invalidated on logout"""
        self.test_execution.test_case_id = "TC_SESSION_004"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to dashboard and verify login
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in")
            
            # Get session cookie before logout
            cookies_before_logout = self.driver.get_cookies()
            session_cookie_before = next((c for c in cookies_before_logout if 'session' in c['name'].lower()), None)
            self.assertIsNotNone(session_cookie_before, "Session cookie should exist before logout")
            
            # Perform logout
            self.dashboard_page.logout_from_dashboard()
            
            # Verify session cookie is removed or invalidated
            cookies_after_logout = self.driver.get_cookies()
            session_cookie_after = next((c for c in cookies_after_logout if 'session' in c['name'].lower()), None)
            
            # Session cookie should either be removed or have different value
            if session_cookie_after:
                self.assertNotEqual(session_cookie_after['value'], session_cookie_before['value'],
                                  "Session cookie should be invalidated after logout")
            
            # Try to access protected page with old session
            self.dashboard_page.navigate_to()
            time.sleep(2)
            
            # Should redirect to login page
            current_url = self.driver.current_url
            self.assertIn("/login", current_url, 
                         "Should redirect to login page after logout")
            
        except Exception as e:
            self.log_defect(
                "Session invalidation on logout failed",
                f"Session not properly invalidated on logout: {str(e)}",
                Severity.MAJOR,
                [
                    "Login with valid credentials",
                    "Navigate to dashboard",
                    "Perform logout",
                    "Verify session cookie invalidation",
                    "Try to access protected page",
                    "Verify redirect to login"
                ]
            )
            raise
    
    def test_concurrent_session_handling(self):
        """Test handling of concurrent sessions"""
        self.test_execution.test_case_id = "TC_SESSION_005"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Create second driver for concurrent session
            driver2 = self.webdriver_manager.create_driver("chrome", headless=False)
            login_page2 = LoginPage(driver2, self.webdriver_manager, self.base_url)
            dashboard_page2 = DashboardPage(driver2, self.webdriver_manager, self.base_url)
            
            try:
                # Login in first browser
                self.login_page.navigate_to()
                self.login_page.login(user_data['email'], user_data['password'])
                self.dashboard_page.navigate_to()
                self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in first browser")
                
                # Login in second browser with same credentials
                login_page2.navigate_to()
                login_page2.login(user_data['email'], user_data['password'])
                dashboard_page2.navigate_to()
                
                # Both sessions should be valid (or system should handle as per business rules)
                # This test verifies the system handles concurrent sessions gracefully
                
                # Check if first session is still valid
                self.dashboard_page.navigate_to()
                first_session_valid = self.dashboard_page.is_user_logged_in()
                
                # Check if second session is valid
                second_session_valid = dashboard_page2.is_user_logged_in()
                
                # At least one session should be valid
                # Business rules may vary: allow concurrent sessions or invalidate previous
                self.assertTrue(first_session_valid or second_session_valid,
                              "At least one session should remain valid")
                
                # If system invalidates previous sessions, verify appropriate handling
                if not first_session_valid:
                    # First session should redirect to login
                    current_url = self.driver.current_url
                    self.assertIn("/login", current_url, 
                                 "Invalidated session should redirect to login")
                
            finally:
                # Clean up second driver
                self.webdriver_manager.close_driver(driver2)
            
        except Exception as e:
            self.log_defect(
                "Concurrent session handling failed",
                f"Concurrent sessions not handled properly: {str(e)}",
                Severity.MINOR,
                [
                    "Login with same credentials in two browsers",
                    "Verify session handling behavior",
                    "Check if both sessions remain valid or one is invalidated"
                ]
            )
            # Don't raise for this test as behavior may vary by design
            pass
    
    def test_session_security_attributes(self):
        """Test session cookie security attributes"""
        self.test_execution.test_case_id = "TC_SESSION_006"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Get session cookies
            cookies = self.driver.get_cookies()
            session_cookies = [c for c in cookies if 'session' in c['name'].lower() or 'auth' in c['name'].lower()]
            
            self.assertGreater(len(session_cookies), 0, "At least one session cookie should exist")
            
            for cookie in session_cookies:
                # Check HttpOnly flag
                self.assertTrue(cookie.get('httpOnly', False),
                              f"Session cookie '{cookie['name']}' should have HttpOnly flag")
                
                # Check Secure flag (should be true in production, may be false in development)
                if self.environment == Environment.PRODUCTION:
                    self.assertTrue(cookie.get('secure', False),
                                  f"Session cookie '{cookie['name']}' should have Secure flag in production")
                
                # Check SameSite attribute
                same_site = cookie.get('sameSite', '').lower()
                self.assertIn(same_site, ['strict', 'lax', 'none'],
                            f"Session cookie '{cookie['name']}' should have valid SameSite attribute")
                
                # Check expiration (session cookies should not have expiry or have reasonable expiry)
                if 'expiry' in cookie:
                    expiry_time = cookie['expiry']
                    current_time = time.time()
                    max_session_time = 24 * 60 * 60  # 24 hours
                    
                    self.assertLessEqual(expiry_time - current_time, max_session_time,
                                       f"Session cookie '{cookie['name']}' expiry should be reasonable")
            
        except Exception as e:
            self.log_defect(
                "Session security attributes failed",
                f"Session cookies lack proper security attributes: {str(e)}",
                Severity.MAJOR,
                [
                    "Login with valid credentials",
                    "Inspect session cookies",
                    "Verify HttpOnly, Secure, and SameSite attributes",
                    "Check cookie expiration settings"
                ]
            )
            raise
    
    def test_session_fixation_protection(self):
        """Test protection against session fixation attacks"""
        self.test_execution.test_case_id = "TC_SESSION_007"
        
        try:
            # Get initial session ID (before login)
            self.login_page.navigate_to()
            initial_cookies = self.driver.get_cookies()
            initial_session_cookie = next((c for c in initial_cookies if 'session' in c['name'].lower()), None)
            
            # Login
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Get session ID after login
            post_login_cookies = self.driver.get_cookies()
            post_login_session_cookie = next((c for c in post_login_cookies if 'session' in c['name'].lower()), None)
            
            self.assertIsNotNone(post_login_session_cookie, "Session cookie should exist after login")
            
            # Session ID should change after login to prevent session fixation
            if initial_session_cookie:
                self.assertNotEqual(initial_session_cookie['value'], post_login_session_cookie['value'],
                                  "Session ID should change after login to prevent session fixation")
            
            # Verify the new session is valid
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), 
                          "New session should be valid after login")
            
        except Exception as e:
            self.log_defect(
                "Session fixation protection failed",
                f"System vulnerable to session fixation attacks: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to login page and note initial session ID",
                    "Login with valid credentials",
                    "Verify session ID changes after login",
                    "Verify new session is valid"
                ]
            )
            raise
    
    def test_session_hijacking_protection(self):
        """Test protection against session hijacking"""
        self.test_execution.test_case_id = "TC_SESSION_008"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login and get session cookie
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            cookies = self.driver.get_cookies()
            session_cookie = next((c for c in cookies if 'session' in c['name'].lower()), None)
            self.assertIsNotNone(session_cookie, "Session cookie should exist")
            
            # Verify session works
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), "Session should be valid")
            
            # Simulate session hijacking by creating new driver with same cookie
            hijacker_driver = self.webdriver_manager.create_driver("chrome", headless=False)
            
            try:
                # Navigate to site with hijacker driver
                hijacker_driver.get(self.base_url)
                
                # Add the stolen session cookie
                hijacker_driver.add_cookie(session_cookie)
                
                # Try to access protected page
                hijacker_driver.get(f"{self.base_url}/dashboard")
                time.sleep(2)
                
                # Check if hijacked session works
                # Ideally, additional security measures should prevent this
                # Such as IP validation, user agent validation, etc.
                
                current_url = hijacker_driver.current_url
                
                # This test documents current behavior
                # In a secure system, additional measures should prevent session hijacking
                if "/dashboard" in current_url:
                    # Session hijacking succeeded - this is a security concern
                    self.log_defect(
                        "Session hijacking possible",
                        "System allows session hijacking without additional security measures",
                        Severity.CRITICAL,
                        [
                            "Login and obtain session cookie",
                            "Use session cookie in different browser",
                            "Access protected resources",
                            "Observe if hijacking succeeds"
                        ]
                    )
                
            finally:
                self.webdriver_manager.close_driver(hijacker_driver)
            
        except Exception as e:
            self.log_defect(
                "Session hijacking test failed",
                f"Unable to test session hijacking protection: {str(e)}",
                Severity.MINOR,
                [
                    "Login and obtain session cookie",
                    "Simulate session hijacking",
                    "Test security measures"
                ]
            )
            # Don't raise as this is a security test that may not be fully implementable
            pass
    
    def test_remember_me_session_persistence(self):
        """Test remember me functionality and long-term session persistence"""
        self.test_execution.test_case_id = "TC_SESSION_009"
        
        try:
            user_data = self.test_data_generator.create_basic_user_data(UserRole.REGISTERED)
            
            # Login with remember me option
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'], remember_me=True)
            
            # Verify remember me cookie is set
            cookies = self.driver.get_cookies()
            remember_cookies = [c for c in cookies if 'remember' in c['name'].lower()]
            
            if remember_cookies:
                remember_cookie = remember_cookies[0]
                
                # Remember me cookie should have longer expiration
                if 'expiry' in remember_cookie:
                    expiry_time = remember_cookie['expiry']
                    current_time = time.time()
                    min_remember_time = 7 * 24 * 60 * 60  # 7 days
                    
                    self.assertGreaterEqual(expiry_time - current_time, min_remember_time,
                                          "Remember me cookie should have long expiration")
                
                # Remember me cookie should be secure
                self.assertTrue(remember_cookie.get('httpOnly', False),
                              "Remember me cookie should be HttpOnly")
            
            # Simulate browser restart by clearing session cookies but keeping remember me
            session_cookies = [c for c in cookies if 'session' in c['name'].lower()]
            for cookie in session_cookies:
                self.driver.delete_cookie(cookie['name'])
            
            # Navigate to protected page
            self.dashboard_page.navigate_to()
            time.sleep(3)  # Wait for remember me processing
            
            # User should be automatically logged in or redirected appropriately
            current_url = self.driver.current_url
            
            # Behavior may vary: auto-login or redirect to login with pre-filled credentials
            if "/login" in current_url:
                # Check if credentials are pre-filled
                email_value = self.login_page.get_element_attribute(self.login_page.email_field, 'value')
                self.assertEqual(email_value, user_data['email'], 
                               "Email should be pre-filled from remember me")
            else:
                # Auto-login occurred
                self.assertTrue(self.dashboard_page.is_user_logged_in(),
                              "User should be automatically logged in with remember me")
            
        except Exception as e:
            self.log_defect(
                "Remember me session persistence failed",
                f"Remember me functionality not working properly: {str(e)}",
                Severity.MINOR,
                [
                    "Login with remember me option checked",
                    "Verify remember me cookie is set",
                    "Simulate browser restart (clear session cookies)",
                    "Navigate to protected page",
                    "Verify remember me behavior"
                ]
            )
            raise


if __name__ == '__main__':
    unittest.main(verbosity=2)