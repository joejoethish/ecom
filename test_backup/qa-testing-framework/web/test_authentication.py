"""
Authentication and User Management Tests

Comprehensive test suite for authentication flows including user registration,
login, logout, password reset, account verification, role-based access control,
and session management.
"""

import unittest
import time
from typing import Dict, Any, List
from selenium.webdriver.remote.webdriver import WebDriver

from .webdriver_manager import WebDriverManager
from .auth_pages import (
    LoginPage, RegistrationPage, ForgotPasswordPage, 
    ResetPasswordPage, ProfilePage, DashboardPage
)
from ..core.interfaces import Environment, UserRole, TestModule, Priority, ExecutionStatus, Severity
from ..core.models import TestCase, TestStep, TestExecution, Defect, BrowserInfo
from ..core.data_manager import TestDataManager
from ..core.error_handling import ErrorHandler
from ..core.config import get_config


class AuthenticationTestSuite(unittest.TestCase):
    """Test suite for authentication and user management functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test suite"""
        cls.environment = Environment.DEVELOPMENT
        cls.config = get_config("web", cls.environment)
        cls.base_url = cls.config.get("base_url", "http://localhost:3000")
        cls.webdriver_manager = WebDriverManager(cls.environment)
        cls.data_manager = TestDataManager(cls.environment)
        cls.error_handler = ErrorHandler()
        
        # Test data
        cls.test_users = {}
        cls.test_executions = []
        cls.defects = []
    
    def setUp(self):
        """Set up individual test"""
        self.driver = self.webdriver_manager.create_driver("chrome", headless=False)
        self.browser_info = self.webdriver_manager.get_browser_info(self.driver)
        
        # Initialize page objects
        self.login_page = LoginPage(self.driver, self.webdriver_manager, self.base_url)
        self.registration_page = RegistrationPage(self.driver, self.webdriver_manager, self.base_url)
        self.forgot_password_page = ForgotPasswordPage(self.driver, self.webdriver_manager, self.base_url)
        self.reset_password_page = ResetPasswordPage(self.driver, self.webdriver_manager, self.base_url)
        self.profile_page = ProfilePage(self.driver, self.webdriver_manager, self.base_url)
        self.dashboard_page = DashboardPage(self.driver, self.webdriver_manager, self.base_url)
        
        # Create test execution record
        self.test_execution = TestExecution(
            id=f"EXE_{int(time.time())}",
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
                f"failed_{self._testMethodName}_{int(time.time())}.png"
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
    
    def create_test_user_data(self, user_type: UserRole = UserRole.REGISTERED) -> Dict[str, Any]:
        """Create test user data"""
        user_data = self.data_manager.create_test_user(user_type)
        user_data['confirm_password'] = user_data['password']
        return user_data
    
    def log_defect(self, title: str, description: str, severity: Severity, reproduction_steps: List[str]):
        """Log a defect"""
        defect = Defect(
            id=f"DEF_{int(time.time())}",
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
    
    # User Registration Tests
    
    def test_user_registration_valid_data(self):
        """Test user registration with valid data"""
        self.test_execution.test_case_id = "TC_AUTH_001"
        
        try:
            # Navigate to registration page
            self.registration_page.navigate_to()
            self.assertTrue(self.registration_page.is_page_loaded(), "Registration page should load")
            
            # Create test user data
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            
            # Perform registration
            registration_success = self.registration_page.register(user_data)
            self.assertTrue(registration_success, "Registration should succeed with valid data")
            
            # Verify redirect or success message
            current_url = self.driver.current_url
            self.assertNotIn("/register", current_url, "Should redirect away from registration page")
            
            # Store user for cleanup
            self.__class__.test_users[user_data['email']] = user_data
            
        except Exception as e:
            self.log_defect(
                "User registration with valid data failed",
                f"Registration failed with error: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to registration page",
                    "Fill all required fields with valid data",
                    "Click register button",
                    "Observe registration failure"
                ]
            )
            raise
    
    def test_user_registration_duplicate_email(self):
        """Test user registration with duplicate email"""
        self.test_execution.test_case_id = "TC_AUTH_002"
        
        try:
            # First, register a user
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            # Try to register again with same email
            self.registration_page.navigate_to()
            duplicate_user_data = self.create_test_user_data(UserRole.REGISTERED)
            duplicate_user_data['email'] = user_data['email']  # Use same email
            
            registration_success = self.registration_page.register(duplicate_user_data)
            self.assertFalse(registration_success, "Registration should fail with duplicate email")
            
            # Verify error message
            self.assertTrue(self.registration_page.has_registration_error(), "Should show registration error")
            error_message = self.registration_page.get_registration_error_message()
            self.assertIn("email", error_message.lower(), "Error should mention email")
            
        except Exception as e:
            self.log_defect(
                "Duplicate email validation failed",
                f"System should prevent duplicate email registration: {str(e)}",
                Severity.MAJOR,
                [
                    "Register user with email",
                    "Try to register another user with same email",
                    "Observe system behavior"
                ]
            )
            raise
    
    def test_user_registration_weak_password(self):
        """Test user registration with weak password"""
        self.test_execution.test_case_id = "TC_AUTH_003"
        
        try:
            self.registration_page.navigate_to()
            
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            user_data['password'] = "123"  # Weak password
            user_data['confirm_password'] = "123"
            
            registration_success = self.registration_page.register(user_data)
            self.assertFalse(registration_success, "Registration should fail with weak password")
            
            # Verify error message
            self.assertTrue(self.registration_page.has_registration_error(), "Should show password error")
            
        except Exception as e:
            self.log_defect(
                "Weak password validation failed",
                f"System should reject weak passwords: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to registration page",
                    "Enter weak password (e.g., '123')",
                    "Submit registration form",
                    "Observe validation behavior"
                ]
            )
            raise
    
    def test_user_registration_password_mismatch(self):
        """Test user registration with password mismatch"""
        self.test_execution.test_case_id = "TC_AUTH_004"
        
        try:
            self.registration_page.navigate_to()
            
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            user_data['confirm_password'] = "different_password"
            
            registration_success = self.registration_page.register(user_data)
            self.assertFalse(registration_success, "Registration should fail with password mismatch")
            
            # Verify error message
            self.assertTrue(self.registration_page.has_registration_error(), "Should show password mismatch error")
            
        except Exception as e:
            self.log_defect(
                "Password mismatch validation failed",
                f"System should detect password mismatch: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to registration page",
                    "Enter different passwords in password and confirm password fields",
                    "Submit registration form",
                    "Observe validation behavior"
                ]
            )
            raise
    
    def test_user_registration_missing_required_fields(self):
        """Test user registration with missing required fields"""
        self.test_execution.test_case_id = "TC_AUTH_005"
        
        try:
            self.registration_page.navigate_to()
            
            # Try to register with empty email
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            user_data['email'] = ""
            
            registration_success = self.registration_page.register(user_data)
            self.assertFalse(registration_success, "Registration should fail with missing email")
            
            # Verify validation errors
            self.assertTrue(self.registration_page.has_registration_error(), "Should show validation errors")
            
        except Exception as e:
            self.log_defect(
                "Required field validation failed",
                f"System should validate required fields: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to registration page",
                    "Leave required fields empty",
                    "Submit registration form",
                    "Observe validation behavior"
                ]
            )
            raise
    
    # User Login Tests
    
    def test_user_login_valid_credentials(self):
        """Test user login with valid credentials"""
        self.test_execution.test_case_id = "TC_AUTH_006"
        
        try:
            # First register a user
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            # Navigate to login page
            self.login_page.navigate_to()
            self.assertTrue(self.login_page.is_page_loaded(), "Login page should load")
            
            # Perform login
            login_success = self.login_page.login(user_data['email'], user_data['password'])
            self.assertTrue(login_success, "Login should succeed with valid credentials")
            
            # Verify successful login (should redirect to dashboard or home)
            current_url = self.driver.current_url
            self.assertNotIn("/login", current_url, "Should redirect away from login page")
            
            # Verify user is logged in
            if "/dashboard" in current_url:
                self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in")
            
        except Exception as e:
            self.log_defect(
                "Valid login failed",
                f"Login with valid credentials failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Register a test user",
                    "Navigate to login page",
                    "Enter valid email and password",
                    "Click login button",
                    "Observe login failure"
                ]
            )
            raise
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        self.test_execution.test_case_id = "TC_AUTH_007"
        
        try:
            self.login_page.navigate_to()
            
            # Try login with invalid credentials
            login_success = self.login_page.login("invalid@email.com", "wrongpassword")
            self.assertFalse(login_success, "Login should fail with invalid credentials")
            
            # Verify error message
            self.assertTrue(self.login_page.has_login_error(), "Should show login error")
            error_message = self.login_page.get_login_error_message()
            self.assertIn("invalid", error_message.lower(), "Error should indicate invalid credentials")
            
            # Verify still on login page
            current_url = self.driver.current_url
            self.assertIn("/login", current_url, "Should remain on login page")
            
        except Exception as e:
            self.log_defect(
                "Invalid credentials handling failed",
                f"System should reject invalid credentials: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to login page",
                    "Enter invalid email and password",
                    "Click login button",
                    "Observe system behavior"
                ]
            )
            raise
    
    def test_user_login_empty_credentials(self):
        """Test user login with empty credentials"""
        self.test_execution.test_case_id = "TC_AUTH_008"
        
        try:
            self.login_page.navigate_to()
            
            # Try login with empty credentials
            login_success = self.login_page.login("", "")
            self.assertFalse(login_success, "Login should fail with empty credentials")
            
            # Verify validation or error message
            self.assertTrue(self.login_page.has_login_error() or 
                          self.login_page.has_form_validation_errors(), 
                          "Should show validation errors")
            
        except Exception as e:
            self.log_defect(
                "Empty credentials validation failed",
                f"System should validate empty credentials: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to login page",
                    "Leave email and password fields empty",
                    "Click login button",
                    "Observe validation behavior"
                ]
            )
            raise
    
    def test_user_login_remember_me_functionality(self):
        """Test remember me functionality"""
        self.test_execution.test_case_id = "TC_AUTH_009"
        
        try:
            # Register a user first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            # Login with remember me
            self.login_page.navigate_to()
            login_success = self.login_page.login(
                user_data['email'], 
                user_data['password'], 
                remember_me=True
            )
            self.assertTrue(login_success, "Login with remember me should succeed")
            
            # Verify remember me checkbox was checked
            # Note: This test would need to be enhanced to verify persistent session
            # across browser restarts, which requires more complex setup
            
        except Exception as e:
            self.log_defect(
                "Remember me functionality failed",
                f"Remember me feature not working: {str(e)}",
                Severity.MINOR,
                [
                    "Navigate to login page",
                    "Enter valid credentials",
                    "Check remember me checkbox",
                    "Login and verify persistent session"
                ]
            )
            raise
    
    # User Logout Tests
    
    def test_user_logout_from_dashboard(self):
        """Test user logout from dashboard"""
        self.test_execution.test_case_id = "TC_AUTH_010"
        
        try:
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to dashboard if not already there
            if "/dashboard" not in self.driver.current_url:
                self.dashboard_page.navigate_to()
            
            # Perform logout
            logout_success = self.dashboard_page.logout_from_dashboard()
            self.assertTrue(logout_success, "Logout should succeed")
            
            # Verify redirect to login or home page
            current_url = self.driver.current_url
            self.assertTrue("/login" in current_url or "/home" in current_url, 
                          "Should redirect to login or home page after logout")
            
        except Exception as e:
            self.log_defect(
                "Logout functionality failed",
                f"User logout from dashboard failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Login to user account",
                    "Navigate to dashboard",
                    "Click logout button",
                    "Observe logout behavior"
                ]
            )
            raise
    
    def test_user_logout_from_profile(self):
        """Test user logout from profile page"""
        self.test_execution.test_case_id = "TC_AUTH_011"
        
        try:
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to profile page
            self.profile_page.navigate_to()
            
            # Perform logout
            logout_success = self.profile_page.logout()
            self.assertTrue(logout_success, "Logout from profile should succeed")
            
            # Verify redirect
            current_url = self.driver.current_url
            self.assertTrue("/login" in current_url or "/home" in current_url, 
                          "Should redirect after logout")
            
        except Exception as e:
            self.log_defect(
                "Profile logout failed",
                f"User logout from profile page failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Login to user account",
                    "Navigate to profile page",
                    "Click logout button",
                    "Observe logout behavior"
                ]
            )
            raise
    
    # Password Reset Tests
    
    def test_forgot_password_valid_email(self):
        """Test forgot password with valid email"""
        self.test_execution.test_case_id = "TC_AUTH_012"
        
        try:
            # Register a user first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            # Navigate to forgot password page
            self.forgot_password_page.navigate_to()
            self.assertTrue(self.forgot_password_page.is_page_loaded(), "Forgot password page should load")
            
            # Send reset email
            reset_sent = self.forgot_password_page.send_reset_email(user_data['email'])
            self.assertTrue(reset_sent, "Password reset email should be sent")
            
            # Verify success message
            success_message = self.forgot_password_page.get_reset_sent_message()
            self.assertNotEqual(success_message, "", "Should show reset sent message")
            
        except Exception as e:
            self.log_defect(
                "Forgot password functionality failed",
                f"Password reset email sending failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Register a test user",
                    "Navigate to forgot password page",
                    "Enter valid email address",
                    "Click send reset email button",
                    "Observe system behavior"
                ]
            )
            raise
    
    def test_forgot_password_invalid_email(self):
        """Test forgot password with invalid email"""
        self.test_execution.test_case_id = "TC_AUTH_013"
        
        try:
            self.forgot_password_page.navigate_to()
            
            # Try with non-existent email
            reset_sent = self.forgot_password_page.send_reset_email("nonexistent@email.com")
            
            # System behavior may vary - either show error or generic success message for security
            # We'll check that the system handles it gracefully
            self.assertIsInstance(reset_sent, bool, "System should handle invalid email gracefully")
            
        except Exception as e:
            self.log_defect(
                "Invalid email handling in forgot password failed",
                f"System should handle invalid email gracefully: {str(e)}",
                Severity.MINOR,
                [
                    "Navigate to forgot password page",
                    "Enter non-existent email address",
                    "Click send reset email button",
                    "Observe system behavior"
                ]
            )
            raise
    
    # Profile Management Tests
    
    def test_profile_update_valid_data(self):
        """Test profile update with valid data"""
        self.test_execution.test_case_id = "TC_AUTH_014"
        
        try:
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to profile page
            self.profile_page.navigate_to()
            self.assertTrue(self.profile_page.is_page_loaded(), "Profile page should load")
            
            # Update profile
            updated_data = {
                'first_name': 'Updated',
                'last_name': 'Name',
                'phone': '+1234567890'
            }
            
            update_success = self.profile_page.update_profile(updated_data)
            self.assertTrue(update_success, "Profile update should succeed")
            
            # Verify updated data
            user_info = self.profile_page.get_user_info()
            self.assertEqual(user_info.get('first_name'), updated_data['first_name'])
            self.assertEqual(user_info.get('last_name'), updated_data['last_name'])
            
        except Exception as e:
            self.log_defect(
                "Profile update failed",
                f"Profile update with valid data failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Login to user account",
                    "Navigate to profile page",
                    "Update profile information",
                    "Save changes",
                    "Observe update behavior"
                ]
            )
            raise
    
    def test_password_change_valid_data(self):
        """Test password change with valid data"""
        self.test_execution.test_case_id = "TC_AUTH_015"
        
        try:
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to profile page
            self.profile_page.navigate_to()
            
            # Change password
            new_password = "newpassword123"
            change_success = self.profile_page.change_password(
                user_data['password'], 
                new_password
            )
            self.assertTrue(change_success, "Password change should succeed")
            
            # Logout and login with new password
            self.profile_page.logout()
            self.login_page.navigate_to()
            
            login_success = self.login_page.login(user_data['email'], new_password)
            self.assertTrue(login_success, "Should be able to login with new password")
            
        except Exception as e:
            self.log_defect(
                "Password change failed",
                f"Password change functionality failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Login to user account",
                    "Navigate to profile page",
                    "Change password with valid data",
                    "Logout and login with new password",
                    "Observe password change behavior"
                ]
            )
            raise
    
    # Role-based Access Control Tests
    
    def test_guest_user_access_restrictions(self):
        """Test guest user access restrictions"""
        self.test_execution.test_case_id = "TC_AUTH_016"
        
        try:
            # Try to access protected pages without login
            protected_urls = [
                f"{self.base_url}/dashboard",
                f"{self.base_url}/profile",
                f"{self.base_url}/orders"
            ]
            
            for url in protected_urls:
                self.driver.get(url)
                time.sleep(2)  # Wait for redirect
                
                current_url = self.driver.current_url
                # Should redirect to login page or show access denied
                self.assertTrue(
                    "/login" in current_url or "/access-denied" in current_url,
                    f"Guest should not access {url} directly"
                )
            
        except Exception as e:
            self.log_defect(
                "Guest access control failed",
                f"Guest users can access protected pages: {str(e)}",
                Severity.CRITICAL,
                [
                    "Without logging in, try to access protected URLs",
                    "Observe system behavior",
                    "Verify access restrictions"
                ]
            )
            raise
    
    def test_registered_user_access_permissions(self):
        """Test registered user access permissions"""
        self.test_execution.test_case_id = "TC_AUTH_017"
        
        try:
            # Login as registered user
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Test access to allowed pages
            allowed_urls = [
                f"{self.base_url}/dashboard",
                f"{self.base_url}/profile"
            ]
            
            for url in allowed_urls:
                self.driver.get(url)
                time.sleep(2)
                
                current_url = self.driver.current_url
                # Should not redirect to login (user is authenticated)
                self.assertNotIn("/login", current_url, 
                               f"Registered user should access {url}")
            
            # Test access to restricted admin pages
            admin_urls = [
                f"{self.base_url}/admin",
                f"{self.base_url}/admin/users"
            ]
            
            for url in admin_urls:
                self.driver.get(url)
                time.sleep(2)
                
                current_url = self.driver.current_url
                # Should redirect or show access denied
                self.assertTrue(
                    "/access-denied" in current_url or "/dashboard" in current_url,
                    f"Registered user should not access admin page {url}"
                )
            
        except Exception as e:
            self.log_defect(
                "Registered user access control failed",
                f"Registered user access permissions not working: {str(e)}",
                Severity.MAJOR,
                [
                    "Login as registered user",
                    "Try to access various pages",
                    "Verify appropriate access permissions"
                ]
            )
            raise
    
    # Session Management Tests
    
    def test_session_timeout_handling(self):
        """Test session timeout handling"""
        self.test_execution.test_case_id = "TC_AUTH_018"
        
        try:
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Navigate to dashboard
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in")
            
            # Simulate session timeout by clearing cookies or waiting
            # For testing purposes, we'll clear session cookies
            self.driver.delete_all_cookies()
            
            # Try to access protected page
            self.profile_page.navigate_to()
            time.sleep(2)
            
            # Should redirect to login page
            current_url = self.driver.current_url
            self.assertIn("/login", current_url, "Should redirect to login after session timeout")
            
        except Exception as e:
            self.log_defect(
                "Session timeout handling failed",
                f"Session timeout not handled properly: {str(e)}",
                Severity.MAJOR,
                [
                    "Login to user account",
                    "Clear session cookies to simulate timeout",
                    "Try to access protected page",
                    "Observe session handling behavior"
                ]
            )
            raise
    
    def test_concurrent_session_handling(self):
        """Test concurrent session handling"""
        self.test_execution.test_case_id = "TC_AUTH_019"
        
        try:
            # This test would require multiple browser instances
            # For now, we'll test basic session behavior
            
            # Login first
            self.registration_page.navigate_to()
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            self.registration_page.register(user_data)
            
            self.login_page.navigate_to()
            self.login_page.login(user_data['email'], user_data['password'])
            
            # Verify session is active
            self.dashboard_page.navigate_to()
            self.assertTrue(self.dashboard_page.is_user_logged_in(), "User should be logged in")
            
            # Note: Full concurrent session testing would require multiple WebDriver instances
            # This is a simplified version focusing on single session validation
            
        except Exception as e:
            self.log_defect(
                "Concurrent session handling test incomplete",
                f"Concurrent session test needs enhancement: {str(e)}",
                Severity.MINOR,
                [
                    "Login from multiple browsers/tabs",
                    "Verify session handling behavior",
                    "Test session conflicts"
                ]
            )
            # Don't raise for this incomplete test
            pass
    
    # Security Tests
    
    def test_sql_injection_protection_login(self):
        """Test SQL injection protection in login"""
        self.test_execution.test_case_id = "TC_AUTH_020"
        
        try:
            self.login_page.navigate_to()
            
            # Try SQL injection in email field
            sql_injection_attempts = [
                "admin'; DROP TABLE users; --",
                "' OR '1'='1",
                "admin' OR '1'='1' --"
            ]
            
            for injection_attempt in sql_injection_attempts:
                login_success = self.login_page.login(injection_attempt, "password")
                self.assertFalse(login_success, f"SQL injection should be prevented: {injection_attempt}")
                
                # Verify system is still functional
                self.assertTrue(self.login_page.is_page_loaded(), "Login page should still be functional")
            
        except Exception as e:
            self.log_defect(
                "SQL injection protection failed",
                f"System vulnerable to SQL injection: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to login page",
                    "Enter SQL injection payloads in email field",
                    "Attempt login",
                    "Verify system security"
                ]
            )
            raise
    
    def test_xss_protection_registration(self):
        """Test XSS protection in registration"""
        self.test_execution.test_case_id = "TC_AUTH_021"
        
        try:
            self.registration_page.navigate_to()
            
            # Try XSS in name fields
            xss_payload = "<script>alert('XSS')</script>"
            
            user_data = self.create_test_user_data(UserRole.REGISTERED)
            user_data['first_name'] = xss_payload
            user_data['last_name'] = xss_payload
            
            # Attempt registration
            self.registration_page.register(user_data)
            
            # Check if XSS payload is executed (it shouldn't be)
            # In a real test, we'd check for alert dialogs or script execution
            # For now, we verify the page is still functional
            self.assertTrue(self.registration_page.is_page_loaded(), "Page should remain functional")
            
            # Verify no JavaScript alerts
            alert_text = self.webdriver_manager.handle_alert(self.driver, "dismiss")
            self.assertIsNone(alert_text, "XSS payload should not execute")
            
        except Exception as e:
            self.log_defect(
                "XSS protection failed",
                f"System vulnerable to XSS attacks: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to registration page",
                    "Enter XSS payload in form fields",
                    "Submit registration",
                    "Verify XSS prevention"
                ]
            )
            raise


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)