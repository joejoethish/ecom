# End-to-end tests for admin workflows
import pytest
from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import os

User = get_user_model()

class BaseE2ETestCase(LiveServerTestCase):
    """Base class for end-to-end tests"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize WebDriver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.wait = WebDriverWait(cls.driver, 10)
    
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin_e2e',
            email='admin@e2e.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def login_as_admin(self):
        """Login as admin user"""
        self.driver.get(f'{self.live_server_url}/admin/login/')
        
        # Fill login form
        username_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_input = self.driver.find_element(By.NAME, 'password')
        
        username_input.send_keys('admin_e2e')
        password_input.send_keys('testpass123')
        
        # Submit form
        login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        
        # Wait for dashboard to load
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )
    
    def take_screenshot(self, name):
        """Take screenshot for debugging"""
        screenshot_dir = 'test_screenshots'
        os.makedirs(screenshot_dir, exist_ok=True)
        self.driver.save_screenshot(f'{screenshot_dir}/{name}.png')

class AdminLoginE2ETest(BaseE2ETestCase):
    """End-to-end tests for admin login"""
    
    def test_successful_admin_login(self):
        """Test successful admin login workflow"""
        self.driver.get(f'{self.live_server_url}/admin/login/')
        
        # Verify login page elements
        self.assertIn('Admin Login', self.driver.title)
        
        username_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_input = self.driver.find_element(By.NAME, 'password')
        login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        
        # Fill and submit login form
        username_input.send_keys('admin_e2e')
        password_input.send_keys('testpass123')
        login_button.click()
        
        # Verify successful login
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )
        self.assertIn('Dashboard', self.driver.title)
    
    def test_failed_admin_login(self):
        """Test failed admin login with invalid credentials"""
        self.driver.get(f'{self.live_server_url}/admin/login/')
        
        username_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_input = self.driver.find_element(By.NAME, 'password')
        login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        
        # Try invalid credentials
        username_input.send_keys('admin_e2e')
        password_input.send_keys('wrongpassword')
        login_button.click()
        
        # Verify error message
        error_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'error-message'))
        )
        self.assertIn('Invalid credentials', error_message.text)
    
    def test_admin_logout(self):
        """Test admin logout workflow"""
        self.login_as_admin()
        
        # Find and click logout button
        logout_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'logout-button'))
        )
        logout_button.click()
        
        # Verify redirect to login page
        self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        self.assertIn('login', self.driver.current_url.lower())

class DashboardE2ETest(BaseE2ETestCase):
    """End-to-end tests for admin dashboard"""
    
    def test_dashboard_loading(self):
        """Test dashboard loading and elements"""
        self.login_as_admin()
        
        # Verify dashboard elements
        stats_widgets = self.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'stat-widget'))
        )
        self.assertGreaterEqual(len(stats_widgets), 4)  # At least 4 stat widgets
        
        # Verify charts are present
        charts = self.driver.find_elements(By.CLASS_NAME, 'chart-container')
        self.assertGreater(len(charts), 0)
        
        # Verify navigation menu
        nav_menu = self.driver.find_element(By.CLASS_NAME, 'nav-menu')
        self.assertTrue(nav_menu.is_displayed())
    
    def test_dashboard_stats_update(self):
        """Test dashboard stats update"""
        self.login_as_admin()
        
        # Get initial stats
        total_orders_element = self.wait.until(
            EC.presence_of_element_located((By.ID, 'total-orders'))
        )
        initial_orders = int(total_orders_element.text)
        
        # Create a new order (this would require navigating to order creation)
        # For now, we'll just verify the element exists
        self.assertTrue(total_orders_element.is_displayed())

class ProductManagementE2ETest(BaseE2ETestCase):
    """End-to-end tests for product management"""
    
    def test_product_creation_workflow(self):
        """Test complete product creation workflow"""
        self.login_as_admin()
        
        # Navigate to products page
        products_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Products'))
        )
        products_link.click()
        
        # Click add product button
        add_product_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'add-product-btn'))
        )
        add_product_button.click()
        
        # Fill product form
        name_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'name'))
        )
        description_input = self.driver.find_element(By.NAME, 'description')
        price_input = self.driver.find_element(By.NAME, 'price')
        sku_input = self.driver.find_element(By.NAME, 'sku')
        
        name_input.send_keys('E2E Test Product')
        description_input.send_keys('Product created during E2E testing')
        price_input.send_keys('99.99')
        sku_input.send_keys('E2E-TEST-001')
        
        # Submit form
        save_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        save_button.click()
        
        # Verify success message
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('Product created successfully', success_message.text)
        
        # Verify product appears in list
        product_list = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-list'))
        )
        self.assertIn('E2E Test Product', product_list.text)
    
    def test_product_editing_workflow(self):
        """Test product editing workflow"""
        # First create a product
        self.test_product_creation_workflow()
        
        # Find and click edit button for the product
        edit_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'edit-product-btn'))
        )
        edit_button.click()
        
        # Update product name
        name_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'name'))
        )
        name_input.clear()
        name_input.send_keys('Updated E2E Test Product')
        
        # Save changes
        save_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        save_button.click()
        
        # Verify update success
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('Product updated successfully', success_message.text)
    
    def test_product_deletion_workflow(self):
        """Test product deletion workflow"""
        # First create a product
        self.test_product_creation_workflow()
        
        # Find and click delete button
        delete_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'delete-product-btn'))
        )
        delete_button.click()
        
        # Confirm deletion in modal
        confirm_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-delete-btn'))
        )
        confirm_button.click()
        
        # Verify deletion success
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('Product deleted successfully', success_message.text)

class OrderManagementE2ETest(BaseE2ETestCase):
    """End-to-end tests for order management"""
    
    def setUp(self):
        super().setUp()
        # Create a customer for orders
        self.customer = User.objects.create_user(
            username='customer_e2e',
            email='customer@e2e.com',
            password='testpass123'
        )
    
    def test_order_status_update_workflow(self):
        """Test order status update workflow"""
        self.login_as_admin()
        
        # Navigate to orders page
        orders_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Orders'))
        )
        orders_link.click()
        
        # Find an order and click to view details
        order_row = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'order-row'))
        )
        order_row.click()
        
        # Update order status
        status_dropdown = self.wait.until(
            EC.element_to_be_clickable((By.NAME, 'status'))
        )
        status_dropdown.click()
        
        # Select new status
        confirmed_option = self.driver.find_element(By.XPATH, '//option[@value="confirmed"]')
        confirmed_option.click()
        
        # Save changes
        save_button = self.driver.find_element(By.CLASS_NAME, 'save-status-btn')
        save_button.click()
        
        # Verify success
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('Order status updated', success_message.text)

class UserManagementE2ETest(BaseE2ETestCase):
    """End-to-end tests for user management"""
    
    def test_admin_user_creation_workflow(self):
        """Test admin user creation workflow"""
        self.login_as_admin()
        
        # Navigate to users page
        users_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Users'))
        )
        users_link.click()
        
        # Click add user button
        add_user_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'add-user-btn'))
        )
        add_user_button.click()
        
        # Fill user form
        username_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        email_input = self.driver.find_element(By.NAME, 'email')
        password_input = self.driver.find_element(By.NAME, 'password')
        
        username_input.send_keys('new_admin_e2e')
        email_input.send_keys('newadmin@e2e.com')
        password_input.send_keys('newadminpass123')
        
        # Set as staff
        is_staff_checkbox = self.driver.find_element(By.NAME, 'is_staff')
        if not is_staff_checkbox.is_selected():
            is_staff_checkbox.click()
        
        # Submit form
        save_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        save_button.click()
        
        # Verify success
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('User created successfully', success_message.text)

class ReportsE2ETest(BaseE2ETestCase):
    """End-to-end tests for reports"""
    
    def test_sales_report_generation(self):
        """Test sales report generation workflow"""
        self.login_as_admin()
        
        # Navigate to reports page
        reports_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Reports'))
        )
        reports_link.click()
        
        # Click on sales report
        sales_report_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Sales Report'))
        )
        sales_report_link.click()
        
        # Set date range
        start_date_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'start_date'))
        )
        end_date_input = self.driver.find_element(By.NAME, 'end_date')
        
        start_date_input.send_keys('2024-01-01')
        end_date_input.send_keys('2024-12-31')
        
        # Generate report
        generate_button = self.driver.find_element(By.CLASS_NAME, 'generate-report-btn')
        generate_button.click()
        
        # Wait for report to load
        report_content = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'report-content'))
        )
        self.assertTrue(report_content.is_displayed())
        
        # Verify report elements
        charts = self.driver.find_elements(By.CLASS_NAME, 'chart')
        self.assertGreater(len(charts), 0)

class SettingsE2ETest(BaseE2ETestCase):
    """End-to-end tests for settings management"""
    
    def test_settings_update_workflow(self):
        """Test settings update workflow"""
        self.login_as_admin()
        
        # Navigate to settings page
        settings_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Settings'))
        )
        settings_link.click()
        
        # Update site name
        site_name_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, 'site_name'))
        )
        site_name_input.clear()
        site_name_input.send_keys('Updated E2E Test Site')
        
        # Save settings
        save_button = self.driver.find_element(By.CLASS_NAME, 'save-settings-btn')
        save_button.click()
        
        # Verify success
        success_message = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
        self.assertIn('Settings updated successfully', success_message.text)

class ResponsiveDesignE2ETest(BaseE2ETestCase):
    """End-to-end tests for responsive design"""
    
    def test_mobile_responsive_design(self):
        """Test mobile responsive design"""
        self.login_as_admin()
        
        # Set mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        # Verify mobile navigation
        mobile_menu_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'mobile-menu-btn'))
        )
        self.assertTrue(mobile_menu_button.is_displayed())
        
        # Test mobile menu functionality
        mobile_menu_button.click()
        
        mobile_nav = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'mobile-nav'))
        )
        self.assertTrue(mobile_nav.is_displayed())
    
    def test_tablet_responsive_design(self):
        """Test tablet responsive design"""
        self.login_as_admin()
        
        # Set tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad size
        
        # Verify layout adapts to tablet size
        dashboard_grid = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard-grid'))
        )
        self.assertTrue(dashboard_grid.is_displayed())

class AccessibilityE2ETest(BaseE2ETestCase):
    """End-to-end tests for accessibility"""
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation"""
        self.login_as_admin()
        
        # Test tab navigation
        from selenium.webdriver.common.keys import Keys
        
        body = self.driver.find_element(By.TAG_NAME, 'body')
        
        # Tab through elements
        for _ in range(10):
            body.send_keys(Keys.TAB)
            time.sleep(0.1)
        
        # Verify focus is visible
        focused_element = self.driver.switch_to.active_element
        self.assertIsNotNone(focused_element)
    
    def test_aria_labels(self):
        """Test ARIA labels and accessibility attributes"""
        self.login_as_admin()
        
        # Check for ARIA labels on important elements
        buttons = self.driver.find_elements(By.TAG_NAME, 'button')
        for button in buttons:
            # Verify button has accessible name
            aria_label = button.get_attribute('aria-label')
            text_content = button.text
            self.assertTrue(aria_label or text_content, 
                          f"Button without accessible name: {button.get_attribute('outerHTML')}")

class PerformanceE2ETest(BaseE2ETestCase):
    """End-to-end tests for performance"""
    
    def test_page_load_performance(self):
        """Test page load performance"""
        start_time = time.time()
        
        self.login_as_admin()
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Page should load within 5 seconds
        self.assertLess(load_time, 5.0, f"Page load time too slow: {load_time:.2f}s")
    
    def test_large_data_table_performance(self):
        """Test performance with large data tables"""
        self.login_as_admin()
        
        # Navigate to products page (assuming it has pagination)
        products_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Products'))
        )
        
        start_time = time.time()
        products_link.click()
        
        # Wait for table to load
        product_table = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'data-table'))
        )
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Table should load within 3 seconds
        self.assertLess(load_time, 3.0, f"Table load time too slow: {load_time:.2f}s")

@pytest.mark.e2e
class PytestE2ETest:
    """Pytest-based E2E tests"""
    
    @pytest.fixture(scope='class')
    def driver(self):
        """WebDriver fixture"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    def test_admin_workflow_with_pytest(self, driver, live_server):
        """Test admin workflow using pytest"""
        driver.get(f'{live_server.url}/admin/login/')
        
        # Test login
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_input = driver.find_element(By.NAME, 'password')
        
        username_input.send_keys('admin')
        password_input.send_keys('password')
        
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        
        # Verify dashboard loads
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )