"""
Authentication Page Objects for Web Testing

Contains page object classes for authentication-related pages including
login, registration, password reset, and user profile management.
"""

from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .page_objects import BasePage, BaseFormPage
from .webdriver_manager import WebDriverManager
from ..core.interfaces import UserRole


class LoginPage(BaseFormPage):
    """Login page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/login"
    
    @property
    def page_title(self) -> str:
        return "Login"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='login-form'], .login-form, #login-form")
    
    # Page elements
    email_field = (By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email")
    password_field = (By.CSS_SELECTOR, "input[type='password'], input[name='password'], #password")
    login_button = (By.CSS_SELECTOR, "button[type='submit'], .login-btn, [data-testid='login-button']")
    forgot_password_link = (By.CSS_SELECTOR, "a[href*='forgot'], .forgot-password, [data-testid='forgot-password']")
    register_link = (By.CSS_SELECTOR, "a[href*='register'], .register-link, [data-testid='register-link']")
    remember_me_checkbox = (By.CSS_SELECTOR, "input[type='checkbox'][name*='remember'], #remember-me")
    show_password_button = (By.CSS_SELECTOR, ".show-password, [data-testid='show-password']")
    
    # Error/success messages
    login_error = (By.CSS_SELECTOR, ".login-error, .auth-error, [data-testid='login-error']")
    invalid_credentials_error = (By.CSS_SELECTOR, ".invalid-credentials, [data-testid='invalid-credentials']")
    account_locked_error = (By.CSS_SELECTOR, ".account-locked, [data-testid='account-locked']")
    
    def login(self, email: str, password: str, remember_me: bool = False) -> bool:
        """Perform login with given credentials"""
        try:
            self.logger.info(f"Attempting login with email: {email}")
            
            # Fill email field
            self.send_keys_to_element(self.email_field, email)
            
            # Fill password field
            self.send_keys_to_element(self.password_field, password)
            
            # Check remember me if requested
            if remember_me and self.is_element_present(self.remember_me_checkbox):
                checkbox = self.find_element(self.remember_me_checkbox)
                if not checkbox.is_selected():
                    self.click_element(self.remember_me_checkbox)
            
            # Click login button
            self.click_element(self.login_button)
            
            # Wait for page to process login
            self.wait_for_loading_to_complete()
            
            # Check if login was successful (no error messages and URL changed)
            if self.has_login_error():
                self.logger.warning(f"Login failed: {self.get_login_error_message()}")
                return False
            
            # Check if we're still on login page (indicates failure)
            current_url = self.get_current_url()
            if "/login" in current_url:
                self.logger.warning("Login failed: Still on login page")
                return False
            
            self.logger.info("Login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed with exception: {str(e)}")
            return False
    
    def has_login_error(self) -> bool:
        """Check if login error is displayed"""
        return (self.is_element_present(self.login_error, timeout=3) or
                self.is_element_present(self.invalid_credentials_error, timeout=3) or
                self.is_element_present(self.account_locked_error, timeout=3))
    
    def get_login_error_message(self) -> str:
        """Get login error message"""
        if self.is_element_present(self.login_error, timeout=3):
            return self.get_element_text(self.login_error)
        elif self.is_element_present(self.invalid_credentials_error, timeout=3):
            return self.get_element_text(self.invalid_credentials_error)
        elif self.is_element_present(self.account_locked_error, timeout=3):
            return self.get_element_text(self.account_locked_error)
        return ""
    
    def click_forgot_password(self) -> None:
        """Click forgot password link"""
        self.click_element(self.forgot_password_link)
    
    def click_register_link(self) -> None:
        """Click register link"""
        self.click_element(self.register_link)
    
    def toggle_password_visibility(self) -> None:
        """Toggle password visibility"""
        if self.is_element_present(self.show_password_button):
            self.click_element(self.show_password_button)
    
    def is_remember_me_checked(self) -> bool:
        """Check if remember me checkbox is selected"""
        if self.is_element_present(self.remember_me_checkbox):
            checkbox = self.find_element(self.remember_me_checkbox)
            return checkbox.is_selected()
        return False
    
    def get_password_field_type(self) -> str:
        """Get password field type (password or text)"""
        password_element = self.find_element(self.password_field)
        return password_element.get_attribute("type")


class RegistrationPage(BaseFormPage):
    """Registration page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/register"
    
    @property
    def page_title(self) -> str:
        return "Register"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='register-form'], .register-form, #register-form")
    
    # Page elements
    first_name_field = (By.CSS_SELECTOR, "input[name='firstName'], input[name='first_name'], #firstName")
    last_name_field = (By.CSS_SELECTOR, "input[name='lastName'], input[name='last_name'], #lastName")
    email_field = (By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email")
    password_field = (By.CSS_SELECTOR, "input[type='password'][name*='password']:not([name*='confirm']), #password")
    confirm_password_field = (By.CSS_SELECTOR, "input[name*='confirm'], input[name*='confirmPassword'], #confirmPassword")
    phone_field = (By.CSS_SELECTOR, "input[name='phone'], input[type='tel'], #phone")
    terms_checkbox = (By.CSS_SELECTOR, "input[type='checkbox'][name*='terms'], #terms")
    newsletter_checkbox = (By.CSS_SELECTOR, "input[type='checkbox'][name*='newsletter'], #newsletter")
    register_button = (By.CSS_SELECTOR, "button[type='submit'], .register-btn, [data-testid='register-button']")
    login_link = (By.CSS_SELECTOR, "a[href*='login'], .login-link, [data-testid='login-link']")
    
    # Password strength indicator
    password_strength = (By.CSS_SELECTOR, ".password-strength, [data-testid='password-strength']")
    password_requirements = (By.CSS_SELECTOR, ".password-requirements, [data-testid='password-requirements']")
    
    # Error messages
    email_exists_error = (By.CSS_SELECTOR, ".email-exists, [data-testid='email-exists-error']")
    password_mismatch_error = (By.CSS_SELECTOR, ".password-mismatch, [data-testid='password-mismatch']")
    weak_password_error = (By.CSS_SELECTOR, ".weak-password, [data-testid='weak-password']")
    
    def register(self, user_data: Dict[str, Any]) -> bool:
        """Register new user with provided data"""
        try:
            self.logger.info(f"Attempting registration for email: {user_data.get('email')}")
            
            # Fill required fields
            if user_data.get('first_name'):
                self.send_keys_to_element(self.first_name_field, user_data['first_name'])
            
            if user_data.get('last_name'):
                self.send_keys_to_element(self.last_name_field, user_data['last_name'])
            
            self.send_keys_to_element(self.email_field, user_data['email'])
            self.send_keys_to_element(self.password_field, user_data['password'])
            
            if user_data.get('confirm_password'):
                self.send_keys_to_element(self.confirm_password_field, user_data['confirm_password'])
            
            if user_data.get('phone'):
                self.send_keys_to_element(self.phone_field, user_data['phone'])
            
            # Accept terms if checkbox is present
            if self.is_element_present(self.terms_checkbox):
                terms_checkbox = self.find_element(self.terms_checkbox)
                if not terms_checkbox.is_selected():
                    self.click_element(self.terms_checkbox)
            
            # Newsletter subscription (optional)
            if user_data.get('subscribe_newsletter', False) and self.is_element_present(self.newsletter_checkbox):
                newsletter_checkbox = self.find_element(self.newsletter_checkbox)
                if not newsletter_checkbox.is_selected():
                    self.click_element(self.newsletter_checkbox)
            
            # Submit registration
            self.click_element(self.register_button)
            
            # Wait for processing
            self.wait_for_loading_to_complete()
            
            # Check for registration errors
            if self.has_registration_error():
                self.logger.warning(f"Registration failed: {self.get_registration_error_message()}")
                return False
            
            self.logger.info("Registration successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Registration failed with exception: {str(e)}")
            return False
    
    def has_registration_error(self) -> bool:
        """Check if registration error is displayed"""
        return (self.has_form_validation_errors() or
                self.is_element_present(self.email_exists_error, timeout=3) or
                self.is_element_present(self.password_mismatch_error, timeout=3) or
                self.is_element_present(self.weak_password_error, timeout=3))
    
    def get_registration_error_message(self) -> str:
        """Get registration error message"""
        if self.is_element_present(self.email_exists_error, timeout=3):
            return self.get_element_text(self.email_exists_error)
        elif self.is_element_present(self.password_mismatch_error, timeout=3):
            return self.get_element_text(self.password_mismatch_error)
        elif self.is_element_present(self.weak_password_error, timeout=3):
            return self.get_element_text(self.weak_password_error)
        elif self.has_form_validation_errors():
            return "; ".join(self.get_form_validation_errors())
        return ""
    
    def get_password_strength(self) -> str:
        """Get password strength indicator"""
        if self.is_element_present(self.password_strength):
            return self.get_element_text(self.password_strength)
        return ""
    
    def get_password_requirements(self) -> List[str]:
        """Get password requirements list"""
        requirements = []
        if self.is_element_present(self.password_requirements):
            req_elements = self.find_elements((By.CSS_SELECTOR, f"{self.password_requirements[1]} li, {self.password_requirements[1]} .requirement"))
            for element in req_elements:
                if element.is_displayed():
                    requirements.append(element.text.strip())
        return requirements
    
    def click_login_link(self) -> None:
        """Click login link"""
        self.click_element(self.login_link)


class ForgotPasswordPage(BaseFormPage):
    """Forgot password page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/forgot-password"
    
    @property
    def page_title(self) -> str:
        return "Forgot Password"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='forgot-password-form'], .forgot-password-form, #forgot-password-form")
    
    # Page elements
    email_field = (By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email")
    send_reset_button = (By.CSS_SELECTOR, "button[type='submit'], .send-reset-btn, [data-testid='send-reset-button']")
    back_to_login_link = (By.CSS_SELECTOR, "a[href*='login'], .back-to-login, [data-testid='back-to-login']")
    
    # Messages
    reset_sent_message = (By.CSS_SELECTOR, ".reset-sent, [data-testid='reset-sent-message']")
    email_not_found_error = (By.CSS_SELECTOR, ".email-not-found, [data-testid='email-not-found']")
    
    def send_reset_email(self, email: str) -> bool:
        """Send password reset email"""
        try:
            self.logger.info(f"Sending password reset email to: {email}")
            
            # Fill email field
            self.send_keys_to_element(self.email_field, email)
            
            # Click send reset button
            self.click_element(self.send_reset_button)
            
            # Wait for processing
            self.wait_for_loading_to_complete()
            
            # Check for success message
            if self.is_element_present(self.reset_sent_message, timeout=10):
                self.logger.info("Password reset email sent successfully")
                return True
            
            # Check for error
            if self.is_element_present(self.email_not_found_error, timeout=5):
                self.logger.warning(f"Email not found: {self.get_element_text(self.email_not_found_error)}")
                return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to send reset email: {str(e)}")
            return False
    
    def get_reset_sent_message(self) -> str:
        """Get reset sent confirmation message"""
        if self.is_element_present(self.reset_sent_message):
            return self.get_element_text(self.reset_sent_message)
        return ""
    
    def click_back_to_login(self) -> None:
        """Click back to login link"""
        self.click_element(self.back_to_login_link)


class ResetPasswordPage(BaseFormPage):
    """Reset password page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/reset-password"
    
    @property
    def page_title(self) -> str:
        return "Reset Password"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='reset-password-form'], .reset-password-form, #reset-password-form")
    
    # Page elements
    new_password_field = (By.CSS_SELECTOR, "input[type='password'][name*='password']:not([name*='confirm']), #newPassword")
    confirm_password_field = (By.CSS_SELECTOR, "input[name*='confirm'], input[name*='confirmPassword'], #confirmPassword")
    reset_button = (By.CSS_SELECTOR, "button[type='submit'], .reset-btn, [data-testid='reset-button']")
    
    # Messages
    password_reset_success = (By.CSS_SELECTOR, ".password-reset-success, [data-testid='password-reset-success']")
    invalid_token_error = (By.CSS_SELECTOR, ".invalid-token, [data-testid='invalid-token']")
    expired_token_error = (By.CSS_SELECTOR, ".expired-token, [data-testid='expired-token']")
    
    def reset_password(self, new_password: str, confirm_password: str = None) -> bool:
        """Reset password with new password"""
        try:
            if confirm_password is None:
                confirm_password = new_password
            
            self.logger.info("Attempting to reset password")
            
            # Fill password fields
            self.send_keys_to_element(self.new_password_field, new_password)
            self.send_keys_to_element(self.confirm_password_field, confirm_password)
            
            # Click reset button
            self.click_element(self.reset_button)
            
            # Wait for processing
            self.wait_for_loading_to_complete()
            
            # Check for success
            if self.is_element_present(self.password_reset_success, timeout=10):
                self.logger.info("Password reset successful")
                return True
            
            # Check for errors
            if self.has_reset_error():
                self.logger.warning(f"Password reset failed: {self.get_reset_error_message()}")
                return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password reset failed with exception: {str(e)}")
            return False
    
    def has_reset_error(self) -> bool:
        """Check if reset error is displayed"""
        return (self.has_form_validation_errors() or
                self.is_element_present(self.invalid_token_error, timeout=3) or
                self.is_element_present(self.expired_token_error, timeout=3))
    
    def get_reset_error_message(self) -> str:
        """Get reset error message"""
        if self.is_element_present(self.invalid_token_error, timeout=3):
            return self.get_element_text(self.invalid_token_error)
        elif self.is_element_present(self.expired_token_error, timeout=3):
            return self.get_element_text(self.expired_token_error)
        elif self.has_form_validation_errors():
            return "; ".join(self.get_form_validation_errors())
        return ""


class ProfilePage(BasePage):
    """User profile page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/profile"
    
    @property
    def page_title(self) -> str:
        return "Profile"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='profile-page'], .profile-page, #profile")
    
    # Navigation elements
    profile_info_tab = (By.CSS_SELECTOR, "[data-testid='profile-info-tab'], .profile-info-tab")
    change_password_tab = (By.CSS_SELECTOR, "[data-testid='change-password-tab'], .change-password-tab")
    account_settings_tab = (By.CSS_SELECTOR, "[data-testid='account-settings-tab'], .account-settings-tab")
    
    # Profile info elements
    first_name_field = (By.CSS_SELECTOR, "input[name='firstName'], #firstName")
    last_name_field = (By.CSS_SELECTOR, "input[name='lastName'], #lastName")
    email_field = (By.CSS_SELECTOR, "input[name='email'], #email")
    phone_field = (By.CSS_SELECTOR, "input[name='phone'], #phone")
    save_profile_button = (By.CSS_SELECTOR, ".save-profile-btn, [data-testid='save-profile']")
    
    # Change password elements
    current_password_field = (By.CSS_SELECTOR, "input[name='currentPassword'], #currentPassword")
    new_password_field = (By.CSS_SELECTOR, "input[name='newPassword'], #newPassword")
    confirm_new_password_field = (By.CSS_SELECTOR, "input[name='confirmNewPassword'], #confirmNewPassword")
    change_password_button = (By.CSS_SELECTOR, ".change-password-btn, [data-testid='change-password']")
    
    # Account settings elements
    deactivate_account_button = (By.CSS_SELECTOR, ".deactivate-account-btn, [data-testid='deactivate-account']")
    logout_button = (By.CSS_SELECTOR, ".logout-btn, [data-testid='logout-button']")
    
    # Messages
    profile_updated_message = (By.CSS_SELECTOR, ".profile-updated, [data-testid='profile-updated']")
    password_changed_message = (By.CSS_SELECTOR, ".password-changed, [data-testid='password-changed']")
    
    def update_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information"""
        try:
            self.logger.info("Updating user profile")
            
            # Navigate to profile info tab if needed
            if self.is_element_present(self.profile_info_tab):
                self.click_element(self.profile_info_tab)
            
            # Update fields
            if profile_data.get('first_name'):
                self.send_keys_to_element(self.first_name_field, profile_data['first_name'])
            
            if profile_data.get('last_name'):
                self.send_keys_to_element(self.last_name_field, profile_data['last_name'])
            
            if profile_data.get('phone'):
                self.send_keys_to_element(self.phone_field, profile_data['phone'])
            
            # Save changes
            self.click_element(self.save_profile_button)
            
            # Wait for processing
            self.wait_for_loading_to_complete()
            
            # Check for success message
            if self.is_element_present(self.profile_updated_message, timeout=10):
                self.logger.info("Profile updated successfully")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Profile update failed: {str(e)}")
            return False
    
    def change_password(self, current_password: str, new_password: str, confirm_password: str = None) -> bool:
        """Change user password"""
        try:
            if confirm_password is None:
                confirm_password = new_password
            
            self.logger.info("Changing user password")
            
            # Navigate to change password tab
            if self.is_element_present(self.change_password_tab):
                self.click_element(self.change_password_tab)
            
            # Fill password fields
            self.send_keys_to_element(self.current_password_field, current_password)
            self.send_keys_to_element(self.new_password_field, new_password)
            self.send_keys_to_element(self.confirm_new_password_field, confirm_password)
            
            # Submit password change
            self.click_element(self.change_password_button)
            
            # Wait for processing
            self.wait_for_loading_to_complete()
            
            # Check for success message
            if self.is_element_present(self.password_changed_message, timeout=10):
                self.logger.info("Password changed successfully")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password change failed: {str(e)}")
            return False
    
    def logout(self) -> bool:
        """Logout from user account"""
        try:
            self.logger.info("Logging out user")
            
            # Navigate to account settings if needed
            if self.is_element_present(self.account_settings_tab):
                self.click_element(self.account_settings_tab)
            
            # Click logout button
            self.click_element(self.logout_button)
            
            # Wait for redirect
            self.wait_for_loading_to_complete()
            
            # Check if redirected to login page
            current_url = self.get_current_url()
            if "/login" in current_url or "/home" in current_url:
                self.logger.info("Logout successful")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Logout failed: {str(e)}")
            return False
    
    def get_user_info(self) -> Dict[str, str]:
        """Get current user information from profile"""
        user_info = {}
        
        try:
            # Navigate to profile info tab if needed
            if self.is_element_present(self.profile_info_tab):
                self.click_element(self.profile_info_tab)
            
            # Get field values
            if self.is_element_present(self.first_name_field):
                user_info['first_name'] = self.get_element_attribute(self.first_name_field, 'value')
            
            if self.is_element_present(self.last_name_field):
                user_info['last_name'] = self.get_element_attribute(self.last_name_field, 'value')
            
            if self.is_element_present(self.email_field):
                user_info['email'] = self.get_element_attribute(self.email_field, 'value')
            
            if self.is_element_present(self.phone_field):
                user_info['phone'] = self.get_element_attribute(self.phone_field, 'value')
            
        except Exception as e:
            self.logger.error(f"Failed to get user info: {str(e)}")
        
        return user_info


class DashboardPage(BasePage):
    """User dashboard page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str = "http://localhost:3000"):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/dashboard"
    
    @property
    def page_title(self) -> str:
        return "Dashboard"
    
    @property
    def unique_element(self) -> tuple:
        return (By.CSS_SELECTOR, "[data-testid='dashboard'], .dashboard, #dashboard")
    
    # Navigation elements
    user_menu = (By.CSS_SELECTOR, ".user-menu, [data-testid='user-menu']")
    profile_link = (By.CSS_SELECTOR, "a[href*='profile'], [data-testid='profile-link']")
    logout_link = (By.CSS_SELECTOR, "a[href*='logout'], [data-testid='logout-link']")
    
    # User info elements
    welcome_message = (By.CSS_SELECTOR, ".welcome-message, [data-testid='welcome-message']")
    user_name_display = (By.CSS_SELECTOR, ".user-name, [data-testid='user-name']")
    user_role_display = (By.CSS_SELECTOR, ".user-role, [data-testid='user-role']")
    
    def is_user_logged_in(self) -> bool:
        """Check if user is logged in by verifying dashboard elements"""
        return (self.is_page_loaded() and 
                (self.is_element_present(self.welcome_message, timeout=5) or
                 self.is_element_present(self.user_menu, timeout=5)))
    
    def get_welcome_message(self) -> str:
        """Get welcome message text"""
        if self.is_element_present(self.welcome_message):
            return self.get_element_text(self.welcome_message)
        return ""
    
    def get_user_name(self) -> str:
        """Get displayed user name"""
        if self.is_element_present(self.user_name_display):
            return self.get_element_text(self.user_name_display)
        return ""
    
    def get_user_role(self) -> str:
        """Get displayed user role"""
        if self.is_element_present(self.user_role_display):
            return self.get_element_text(self.user_role_display)
        return ""
    
    def navigate_to_profile(self) -> None:
        """Navigate to user profile"""
        if self.is_element_present(self.user_menu):
            self.click_element(self.user_menu)
        
        self.click_element(self.profile_link)
    
    def logout_from_dashboard(self) -> None:
        """Logout from dashboard"""
        if self.is_element_present(self.user_menu):
            self.click_element(self.user_menu)
        
        self.click_element(self.logout_link)