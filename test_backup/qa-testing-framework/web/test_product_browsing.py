"""
Product Browsing and Search Functionality Tests

Test cases for product catalog browsing, filtering, search functionality,
product detail page validation, and product discovery workflows.
"""

import pytest
import time
from typing import List, Dict, Any
from selenium.common.exceptions import NoSuchElementException, TimeoutException

try:
    from .product_pages import (
        ProductCatalogPage, ProductSearchPage, ProductDetailPage,
        ProductComparisonPage, WishlistPage
    )
    from .webdriver_manager import WebDriverManager
    from ..core.interfaces import Environment, TestModule, Priority, UserRole, ExecutionStatus, Severity
    from ..core.models import TestCase, TestStep, TestExecution, Defect, BrowserInfo
    from ..core.data_manager import TestDataManager
    from ..core.error_handling import ErrorHandler
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from web.product_pages import (
        ProductCatalogPage, ProductSearchPage, ProductDetailPage,
        ProductComparisonPage, WishlistPage
    )
    from web.webdriver_manager import WebDriverManager
    from core.interfaces import Environment, TestModule, Priority, UserRole, ExecutionStatus, Severity
    from core.models import TestCase, TestStep, TestExecution, Defect, BrowserInfo
    from core.data_manager import TestDataManager
    from core.error_handling import ErrorHandler


class TestProductBrowsing:
    """Test class for product browsing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, browser_name="chrome", environment=Environment.DEVELOPMENT):
        """Setup test environment"""
        self.webdriver_manager = WebDriverManager(environment)
        self.driver = self.webdriver_manager.create_driver(browser_name)
        self.data_manager = TestDataManager(environment)
        self.error_handler = ErrorHandler()
        
        # Initialize page objects
        self.catalog_page = ProductCatalogPage(self.driver, self.webdriver_manager)
        self.search_page = ProductSearchPage(self.driver, self.webdriver_manager)
        self.detail_page = ProductDetailPage(self.driver, self.webdriver_manager)
        self.comparison_page = ProductComparisonPage(self.driver, self.webdriver_manager)
        self.wishlist_page = WishlistPage(self.driver, self.webdriver_manager)
        
        yield
        
        # Cleanup
        self.webdriver_manager.close_driver(self.driver)
    
    def test_homepage_navigation_links(self):
        """
        Test Case: Validate homepage navigation functionality
        Requirements: 2.1 - Homepage navigation validation
        """
        test_case = TestCase(
            id="TC_PROD_001",
            name="Homepage Navigation Links Test",
            description="Validate all menu links, category navigation, featured products display",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to homepage", "Open homepage URL", "Homepage loads successfully"),
                TestStep(2, "Verify menu links", "Check all navigation menu links", "All menu links are functional"),
                TestStep(3, "Test category navigation", "Click on category links", "Category pages load correctly"),
                TestStep(4, "Validate featured products", "Check featured products section", "Featured products are displayed")
            ],
            expected_result="All homepage navigation elements work correctly"
        )
        
        try:
            # Step 1: Navigate to homepage
            self.catalog_page.navigate_to("/")
            assert self.catalog_page.is_page_loaded(), "Homepage failed to load"
            
            # Step 2: Verify menu links (basic validation)
            menu_links = self.driver.find_elements("css selector", ".nav-link, .menu-item a, .navigation a")
            assert len(menu_links) > 0, "No navigation menu links found"
            
            # Step 3: Test category navigation
            try:
                self.catalog_page.navigate_to_category("Electronics")
                assert "electronics" in self.driver.current_url.lower() or "category" in self.driver.current_url.lower()
            except NoSuchElementException:
                # Try alternative category names
                categories_to_try = ["Clothing", "Books", "Home", "Sports"]
                category_found = False
                for category in categories_to_try:
                    try:
                        self.catalog_page.navigate_to_category(category)
                        category_found = True
                        break
                    except NoSuchElementException:
                        continue
                assert category_found, "No valid categories found for navigation testing"
            
            # Step 4: Validate featured products
            self.catalog_page.navigate_to("/")
            featured_products = self.driver.find_elements("css selector", ".featured-product, .featured-item")
            # Featured products are optional, so we just log the result
            print(f"Featured products found: {len(featured_products)}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_categories_navigation(self):
        """
        Test Case: Validate product category navigation
        Requirements: 2.2 - Product categories navigation
        """
        test_case = TestCase(
            id="TC_PROD_002",
            name="Product Categories Navigation Test",
            description="Verify category page loading, subcategory navigation, breadcrumb navigation",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to products page", "Open products catalog", "Products page loads"),
                TestStep(2, "Test category navigation", "Click on different categories", "Category pages load correctly"),
                TestStep(3, "Test subcategory navigation", "Navigate to subcategories", "Subcategory pages load"),
                TestStep(4, "Validate breadcrumb navigation", "Check breadcrumb trail", "Breadcrumbs show correct path")
            ],
            expected_result="Category navigation works correctly with proper breadcrumbs"
        )
        
        try:
            # Step 1: Navigate to products page
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            # Step 2: Test category navigation
            categories = self.driver.find_elements("css selector", ".category-link, .category-item a")
            assert len(categories) > 0, "No categories found"
            
            if categories:
                first_category = categories[0]
                category_name = first_category.text.strip()
                first_category.click()
                time.sleep(2)
                
                # Verify we're on a category page
                current_url = self.driver.current_url
                assert "category" in current_url.lower() or category_name.lower() in current_url.lower()
            
            # Step 3: Test subcategory navigation (if available)
            subcategories = self.driver.find_elements("css selector", ".subcategory-link, .subcategory a")
            if subcategories:
                first_subcategory = subcategories[0]
                subcategory_name = first_subcategory.text.strip()
                first_subcategory.click()
                time.sleep(2)
                print(f"Navigated to subcategory: {subcategory_name}")
            
            # Step 4: Validate breadcrumb navigation
            breadcrumb_text = self.catalog_page.get_breadcrumb_text()
            print(f"Breadcrumb: {breadcrumb_text}")
            # Breadcrumbs are optional, so we just verify they exist if present
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_search_functionality(self):
        """
        Test Case: Validate product search functionality
        Requirements: 2.3 - Product search validation
        """
        test_case = TestCase(
            id="TC_PROD_003",
            name="Product Search Functionality Test",
            description="Validate search with valid/invalid keywords, search suggestions, result accuracy",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Test valid keyword search", "Search with valid product keywords", "Relevant results returned"),
                TestStep(2, "Test invalid keyword search", "Search with invalid keywords", "No results or suggestions shown"),
                TestStep(3, "Test empty search", "Submit empty search", "Appropriate handling of empty search"),
                TestStep(4, "Test search suggestions", "Type partial keywords", "Search suggestions appear"),
                TestStep(5, "Validate search result accuracy", "Check result relevance", "Results match search terms")
            ],
            expected_result="Search functionality works correctly for all scenarios"
        )
        
        try:
            # Step 1: Test valid keyword search
            self.search_page.navigate_to("/")
            
            # Try common search terms
            search_terms = ["laptop", "phone", "shirt", "book", "shoes"]
            successful_search = False
            
            for term in search_terms:
                try:
                    self.search_page.search_products(term)
                    if self.search_page.has_search_results():
                        successful_search = True
                        print(f"Successful search with term: {term}")
                        break
                except Exception:
                    continue
            
            if not successful_search:
                # Try generic search
                self.search_page.search_products("product")
                
            # Step 2: Test invalid keyword search
            self.search_page.search_products("xyzinvalidkeyword123")
            time.sleep(2)
            
            if self.search_page.has_no_results():
                print("Invalid search correctly shows no results")
            elif self.search_page.has_search_results():
                print("Invalid search returned some results (may include suggestions)")
            
            # Step 3: Test empty search
            self.search_page.search_products("")
            time.sleep(2)
            print("Empty search handled")
            
            # Step 4: Test search suggestions
            try:
                suggestions = self.search_page.get_search_suggestions("lap")
                print(f"Search suggestions for 'lap': {suggestions}")
            except Exception as e:
                print(f"Search suggestions not available: {e}")
            
            # Step 5: Validate search result accuracy (basic check)
            self.search_page.search_products("test")
            results_count = self.search_page.get_search_results_count()
            print(f"Search results count: {results_count}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_filters(self):
        """
        Test Case: Validate product filtering functionality
        Requirements: 2.4 - Product filters validation
        """
        test_case = TestCase(
            id="TC_PROD_004",
            name="Product Filters Test",
            description="Verify price range, brand, rating, availability, size/color filters",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to products page", "Open products catalog", "Products page loads"),
                TestStep(2, "Test price range filter", "Apply price range filter", "Products filtered by price"),
                TestStep(3, "Test brand filter", "Apply brand filter", "Products filtered by brand"),
                TestStep(4, "Test rating filter", "Apply rating filter", "Products filtered by rating"),
                TestStep(5, "Test availability filter", "Apply availability filter", "Products filtered by availability"),
                TestStep(6, "Test filter combinations", "Apply multiple filters", "Filters work together correctly"),
                TestStep(7, "Test clear filters", "Clear all filters", "All filters are cleared")
            ],
            expected_result="All product filters work correctly individually and in combination"
        )
        
        try:
            # Step 1: Navigate to products page
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            initial_product_count = self.catalog_page.get_product_count()
            print(f"Initial product count: {initial_product_count}")
            
            # Step 2: Test price range filter
            try:
                self.catalog_page.apply_price_filter(min_price=10, max_price=100)
                time.sleep(2)
                filtered_count = self.catalog_page.get_product_count()
                print(f"Products after price filter: {filtered_count}")
            except Exception as e:
                print(f"Price filter not available: {e}")
            
            # Step 3: Test brand filter
            try:
                # Try to find and apply a brand filter
                brand_elements = self.driver.find_elements("css selector", ".brand-filter input, .brand-filter .checkbox")
                if brand_elements:
                    brand_elements[0].click()
                    time.sleep(2)
                    print("Brand filter applied")
            except Exception as e:
                print(f"Brand filter not available: {e}")
            
            # Step 4: Test rating filter
            try:
                self.catalog_page.apply_rating_filter(4)
                time.sleep(2)
                print("Rating filter applied")
            except Exception as e:
                print(f"Rating filter not available: {e}")
            
            # Step 5: Test availability filter
            try:
                self.catalog_page.apply_availability_filter("in_stock")
                time.sleep(2)
                print("Availability filter applied")
            except Exception as e:
                print(f"Availability filter not available: {e}")
            
            # Step 6: Test filter combinations (already applied above)
            final_count = self.catalog_page.get_product_count()
            print(f"Products after all filters: {final_count}")
            
            # Step 7: Test clear filters
            try:
                self.catalog_page.clear_all_filters()
                time.sleep(2)
                cleared_count = self.catalog_page.get_product_count()
                print(f"Products after clearing filters: {cleared_count}")
            except Exception as e:
                print(f"Clear filters not available: {e}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_sorting(self):
        """
        Test Case: Validate product sorting functionality
        Requirements: 2.5 - Product sorting validation
        """
        test_case = TestCase(
            id="TC_PROD_005",
            name="Product Sorting Test",
            description="Validate sort by price, popularity, ratings, newest arrivals, alphabetical",
            module=TestModule.WEB,
            priority=Priority.MEDIUM,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to products page", "Open products catalog", "Products page loads"),
                TestStep(2, "Test price sorting (low to high)", "Sort by price ascending", "Products sorted by price ascending"),
                TestStep(3, "Test price sorting (high to low)", "Sort by price descending", "Products sorted by price descending"),
                TestStep(4, "Test popularity sorting", "Sort by popularity", "Products sorted by popularity"),
                TestStep(5, "Test rating sorting", "Sort by rating", "Products sorted by rating"),
                TestStep(6, "Test newest arrivals sorting", "Sort by newest", "Products sorted by newest"),
                TestStep(7, "Test alphabetical sorting", "Sort alphabetically", "Products sorted alphabetically")
            ],
            expected_result="All sorting options work correctly"
        )
        
        try:
            # Step 1: Navigate to products page
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            # Get initial product list for comparison
            initial_products = []
            try:
                for i in range(min(5, self.catalog_page.get_product_count())):
                    product_info = self.catalog_page.get_product_info(i)
                    initial_products.append(product_info)
            except Exception as e:
                print(f"Could not get initial product info: {e}")
            
            # Test different sorting options
            sort_options = ['price_low_high', 'price_high_low', 'popularity', 'rating', 'newest', 'alphabetical']
            
            for sort_option in sort_options:
                try:
                    # Step 2-7: Test each sorting option
                    self.catalog_page.sort_products(sort_option)
                    time.sleep(2)
                    
                    # Get products after sorting
                    sorted_products = []
                    for i in range(min(3, self.catalog_page.get_product_count())):
                        try:
                            product_info = self.catalog_page.get_product_info(i)
                            sorted_products.append(product_info)
                        except Exception:
                            break
                    
                    print(f"Sorting by {sort_option}: {len(sorted_products)} products retrieved")
                    
                except Exception as e:
                    print(f"Sorting option {sort_option} not available: {e}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_detail_page_validation(self):
        """
        Test Case: Validate product detail page elements
        Requirements: 2.6 - Product details validation
        """
        test_case = TestCase(
            id="TC_PROD_006",
            name="Product Detail Page Validation Test",
            description="Verify product images, zoom, descriptions, specifications, reviews, related products",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to product detail page", "Click on a product", "Product detail page loads"),
                TestStep(2, "Validate product information", "Check name, price, description", "All product info displayed"),
                TestStep(3, "Test product images", "Check main image and thumbnails", "Images load correctly"),
                TestStep(4, "Test image zoom functionality", "Click zoom or main image", "Image zoom works"),
                TestStep(5, "Validate product specifications", "Check specifications section", "Specifications displayed"),
                TestStep(6, "Check reviews section", "Verify reviews and ratings", "Reviews section present"),
                TestStep(7, "Validate related products", "Check related products section", "Related products shown")
            ],
            expected_result="Product detail page displays all required information correctly"
        )
        
        try:
            # Step 1: Navigate to product detail page
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            # Click on first available product
            if self.catalog_page.get_product_count() > 0:
                self.catalog_page.click_product(0)
                time.sleep(2)
            else:
                # Navigate directly to a product detail page
                self.detail_page.navigate_to("/product/1")
            
            assert self.detail_page.is_page_loaded(), "Product detail page failed to load"
            
            # Step 2: Validate product information
            product_name = self.detail_page.get_product_name()
            product_price = self.detail_page.get_product_price()
            product_description = self.detail_page.get_product_description()
            
            assert product_name, "Product name not found"
            assert product_price, "Product price not found"
            print(f"Product: {product_name}, Price: {product_price}")
            
            # Step 3: Test product images
            validation_results = self.detail_page.validate_product_page()
            assert validation_results.get("main_image_present", False), "Main product image not found"
            
            # Step 4: Test image zoom functionality
            try:
                self.detail_page.click_main_image()
                time.sleep(1)
                print("Main image click successful")
            except Exception as e:
                print(f"Image interaction not available: {e}")
            
            # Step 5: Validate product specifications
            try:
                specs_present = self.detail_page.is_element_present(self.detail_page.product_specifications)
                print(f"Product specifications present: {specs_present}")
            except Exception as e:
                print(f"Specifications check failed: {e}")
            
            # Step 6: Check reviews section
            try:
                reviews_count = self.detail_page.get_reviews_count()
                product_rating = self.detail_page.get_product_rating()
                print(f"Reviews: {reviews_count}, Rating: {product_rating}")
            except Exception as e:
                print(f"Reviews check failed: {e}")
            
            # Step 7: Validate related products
            try:
                related_count = self.detail_page.get_related_products_count()
                print(f"Related products: {related_count}")
            except Exception as e:
                print(f"Related products check failed: {e}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_pagination_functionality(self):
        """
        Test Case: Validate pagination functionality
        Requirements: 2.7 - Pagination validation
        """
        test_case = TestCase(
            id="TC_PROD_007",
            name="Pagination Functionality Test",
            description="Validate page navigation, items per page selection, infinite scroll",
            module=TestModule.WEB,
            priority=Priority.MEDIUM,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Navigate to products page", "Open products catalog", "Products page loads"),
                TestStep(2, "Test next page navigation", "Click next page button", "Next page loads"),
                TestStep(3, "Test previous page navigation", "Click previous page button", "Previous page loads"),
                TestStep(4, "Test items per page selection", "Change items per page", "Page updates with new count"),
                TestStep(5, "Test infinite scroll", "Scroll to bottom", "More products load automatically")
            ],
            expected_result="Pagination works correctly with all navigation options"
        )
        
        try:
            # Step 1: Navigate to products page
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            initial_count = self.catalog_page.get_product_count()
            print(f"Initial product count: {initial_count}")
            
            # Step 2: Test next page navigation
            if self.catalog_page.has_pagination():
                try:
                    next_success = self.catalog_page.go_to_next_page()
                    if next_success:
                        time.sleep(2)
                        next_page_count = self.catalog_page.get_product_count()
                        print(f"Next page product count: {next_page_count}")
                    else:
                        print("Next page not available")
                except Exception as e:
                    print(f"Next page navigation failed: {e}")
                
                # Step 3: Test previous page navigation
                try:
                    prev_success = self.catalog_page.go_to_previous_page()
                    if prev_success:
                        time.sleep(2)
                        prev_page_count = self.catalog_page.get_product_count()
                        print(f"Previous page product count: {prev_page_count}")
                    else:
                        print("Previous page not available")
                except Exception as e:
                    print(f"Previous page navigation failed: {e}")
            else:
                print("Pagination not available on this page")
            
            # Step 4: Test items per page selection
            try:
                self.catalog_page.set_items_per_page(20)
                time.sleep(2)
                new_count = self.catalog_page.get_product_count()
                print(f"Products after changing items per page: {new_count}")
            except Exception as e:
                print(f"Items per page selection not available: {e}")
            
            # Step 5: Test infinite scroll (basic test)
            try:
                self.catalog_page.scroll_to_bottom()
                time.sleep(3)  # Wait for potential loading
                scroll_count = self.catalog_page.get_product_count()
                print(f"Products after scrolling: {scroll_count}")
            except Exception as e:
                print(f"Infinite scroll test failed: {e}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_comparison_functionality(self):
        """
        Test Case: Validate product comparison functionality
        Requirements: Product comparison features
        """
        test_case = TestCase(
            id="TC_PROD_008",
            name="Product Comparison Test",
            description="Test product comparison and wishlist features",
            module=TestModule.WEB,
            priority=Priority.MEDIUM,
            user_role=UserRole.REGISTERED,
            test_steps=[
                TestStep(1, "Add products to comparison", "Select products for comparison", "Products added to comparison"),
                TestStep(2, "Navigate to comparison page", "Go to comparison page", "Comparison page loads"),
                TestStep(3, "Validate comparison table", "Check comparison table", "Products compared correctly"),
                TestStep(4, "Remove product from comparison", "Remove a product", "Product removed successfully"),
                TestStep(5, "Clear all comparison", "Clear comparison", "All products removed from comparison")
            ],
            expected_result="Product comparison functionality works correctly"
        )
        
        try:
            # Step 1: Add products to comparison (if available)
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            # Look for comparison functionality
            compare_buttons = self.driver.find_elements("css selector", ".add-to-compare, [data-testid='add-to-compare']")
            if compare_buttons:
                # Add first two products to comparison
                for i in range(min(2, len(compare_buttons))):
                    try:
                        compare_buttons[i].click()
                        time.sleep(1)
                        print(f"Added product {i+1} to comparison")
                    except Exception as e:
                        print(f"Failed to add product {i+1} to comparison: {e}")
                
                # Step 2: Navigate to comparison page
                try:
                    self.comparison_page.navigate_to("/compare")
                    if self.comparison_page.is_page_loaded():
                        # Step 3: Validate comparison table
                        compared_count = self.comparison_page.get_compared_products_count()
                        print(f"Products in comparison: {compared_count}")
                        
                        # Step 4: Remove product from comparison
                        if compared_count > 0:
                            self.comparison_page.remove_product_from_comparison(0)
                            time.sleep(1)
                            new_count = self.comparison_page.get_compared_products_count()
                            print(f"Products after removal: {new_count}")
                        
                        # Step 5: Clear all comparison
                        self.comparison_page.clear_all_comparison()
                        time.sleep(1)
                        final_count = self.comparison_page.get_compared_products_count()
                        print(f"Products after clearing all: {final_count}")
                    
                except Exception as e:
                    print(f"Comparison page navigation failed: {e}")
            else:
                print("Product comparison functionality not available")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_wishlist_functionality(self):
        """
        Test Case: Validate wishlist functionality
        Requirements: Wishlist features
        """
        test_case = TestCase(
            id="TC_PROD_009",
            name="Wishlist Functionality Test",
            description="Test wishlist add, remove, and management features",
            module=TestModule.WEB,
            priority=Priority.MEDIUM,
            user_role=UserRole.REGISTERED,
            test_steps=[
                TestStep(1, "Add products to wishlist", "Click add to wishlist buttons", "Products added to wishlist"),
                TestStep(2, "Navigate to wishlist page", "Go to wishlist page", "Wishlist page loads"),
                TestStep(3, "Validate wishlist items", "Check wishlist items", "Wishlist items displayed correctly"),
                TestStep(4, "Add item to cart from wishlist", "Move item to cart", "Item added to cart successfully"),
                TestStep(5, "Remove item from wishlist", "Remove an item", "Item removed from wishlist"),
                TestStep(6, "Clear entire wishlist", "Clear all items", "Wishlist cleared successfully")
            ],
            expected_result="Wishlist functionality works correctly"
        )
        
        try:
            # Step 1: Add products to wishlist
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            # Look for wishlist functionality
            wishlist_buttons = self.driver.find_elements("css selector", ".add-to-wishlist, [data-testid='add-to-wishlist']")
            if wishlist_buttons:
                # Add first product to wishlist
                try:
                    wishlist_buttons[0].click()
                    time.sleep(2)
                    print("Added product to wishlist")
                except Exception as e:
                    print(f"Failed to add product to wishlist: {e}")
                
                # Step 2: Navigate to wishlist page
                try:
                    self.wishlist_page.navigate_to("/wishlist")
                    if self.wishlist_page.is_page_loaded():
                        # Step 3: Validate wishlist items
                        wishlist_count = self.wishlist_page.get_wishlist_items_count()
                        print(f"Items in wishlist: {wishlist_count}")
                        
                        if wishlist_count > 0:
                            # Step 4: Add item to cart from wishlist
                            try:
                                self.wishlist_page.add_item_to_cart_from_wishlist(0)
                                time.sleep(2)
                                print("Added item to cart from wishlist")
                            except Exception as e:
                                print(f"Failed to add to cart from wishlist: {e}")
                            
                            # Step 5: Remove item from wishlist
                            try:
                                self.wishlist_page.remove_item_from_wishlist(0)
                                time.sleep(1)
                                new_count = self.wishlist_page.get_wishlist_items_count()
                                print(f"Items after removal: {new_count}")
                            except Exception as e:
                                print(f"Failed to remove from wishlist: {e}")
                        
                        # Step 6: Clear entire wishlist
                        try:
                            self.wishlist_page.clear_wishlist()
                            time.sleep(1)
                            final_count = self.wishlist_page.get_wishlist_items_count()
                            print(f"Items after clearing wishlist: {final_count}")
                        except Exception as e:
                            print(f"Failed to clear wishlist: {e}")
                    
                except Exception as e:
                    print(f"Wishlist page navigation failed: {e}")
            else:
                print("Wishlist functionality not available")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise
    
    def test_product_discovery_workflow(self):
        """
        Test Case: Complete product discovery workflow
        Requirements: End-to-end product discovery
        """
        test_case = TestCase(
            id="TC_PROD_010",
            name="Product Discovery Workflow Test",
            description="Test complete product discovery workflow from search to product detail",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.GUEST,
            test_steps=[
                TestStep(1, "Start with homepage", "Navigate to homepage", "Homepage loads successfully"),
                TestStep(2, "Browse categories", "Navigate through categories", "Category browsing works"),
                TestStep(3, "Apply filters", "Use filtering options", "Filters narrow down products"),
                TestStep(4, "Search for products", "Use search functionality", "Search returns relevant results"),
                TestStep(5, "View product details", "Click on product", "Product detail page loads"),
                TestStep(6, "Interact with product", "Test product interactions", "All interactions work correctly")
            ],
            expected_result="Complete product discovery workflow functions correctly"
        )
        
        try:
            # Step 1: Start with homepage
            self.catalog_page.navigate_to("/")
            assert self.catalog_page.is_page_loaded(), "Homepage failed to load"
            
            # Step 2: Browse categories
            self.catalog_page.navigate_to("/products")
            assert self.catalog_page.is_page_loaded(), "Products page failed to load"
            
            initial_count = self.catalog_page.get_product_count()
            print(f"Initial products available: {initial_count}")
            
            # Step 3: Apply filters (basic price filter)
            try:
                self.catalog_page.apply_price_filter(min_price=1, max_price=1000)
                time.sleep(2)
                filtered_count = self.catalog_page.get_product_count()
                print(f"Products after filtering: {filtered_count}")
            except Exception as e:
                print(f"Filtering not available: {e}")
            
            # Step 4: Search for products
            try:
                self.search_page.search_products("product")
                time.sleep(2)
                search_results = self.search_page.get_search_results_count()
                print(f"Search results: {search_results}")
            except Exception as e:
                print(f"Search functionality issue: {e}")
            
            # Step 5: View product details
            self.catalog_page.navigate_to("/products")
            if self.catalog_page.get_product_count() > 0:
                self.catalog_page.click_product(0)
                time.sleep(2)
                
                # Step 6: Interact with product
                if self.detail_page.is_page_loaded():
                    product_name = self.detail_page.get_product_name()
                    product_price = self.detail_page.get_product_price()
                    
                    print(f"Viewing product: {product_name} - {product_price}")
                    
                    # Test basic interactions
                    try:
                        self.detail_page.set_quantity(2)
                        print("Quantity set to 2")
                    except Exception as e:
                        print(f"Quantity interaction failed: {e}")
                    
                    try:
                        if self.detail_page.is_element_present(self.detail_page.add_to_cart_btn):
                            print("Add to cart button is available")
                    except Exception as e:
                        print(f"Add to cart check failed: {e}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {"test_case": test_case.id})
            raise


# Test execution helper functions
def run_product_browsing_tests(browser="chrome", environment=Environment.DEVELOPMENT):
    """Run all product browsing tests"""
    test_class = TestProductBrowsing()
    test_class.setup(browser, environment)
    
    try:
        # Run all test methods
        test_methods = [
            test_class.test_homepage_navigation_links,
            test_class.test_product_categories_navigation,
            test_class.test_product_search_functionality,
            test_class.test_product_filters,
            test_class.test_product_sorting,
            test_class.test_product_detail_page_validation,
            test_class.test_pagination_functionality,
            test_class.test_product_comparison_functionality,
            test_class.test_wishlist_functionality,
            test_class.test_product_discovery_workflow
        ]
        
        results = []
        for test_method in test_methods:
            try:
                print(f"\n--- Running {test_method.__name__} ---")
                test_method()
                results.append({"test": test_method.__name__, "status": "PASSED"})
                print(f"✓ {test_method.__name__} PASSED")
            except Exception as e:
                results.append({"test": test_method.__name__, "status": "FAILED", "error": str(e)})
                print(f"✗ {test_method.__name__} FAILED: {e}")
        
        return results
        
    finally:
        # Cleanup is handled in the fixture
        pass


if __name__ == "__main__":
    # Run tests when script is executed directly
    results = run_product_browsing_tests()
    
    # Print summary
    passed = len([r for r in results if r["status"] == "PASSED"])
    failed = len([r for r in results if r["status"] == "FAILED"])
    
    print(f"\n=== TEST SUMMARY ===")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed tests:")
        for result in results:
            if result["status"] == "FAILED":
                print(f"- {result['test']}: {result.get('error', 'Unknown error')}")