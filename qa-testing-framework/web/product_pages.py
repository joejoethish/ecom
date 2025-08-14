"""
Product Browsing Page Objects for Web Testing

Page objects for product catalog, search, filtering, and product detail pages
following the Page Object Model pattern for product browsing functionality.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

try:
    from .page_objects import BasePage, BaseListPage
    from ..core.models import TestProduct, ProductVariant
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from web.page_objects import BasePage, BaseListPage
    from core.models import TestProduct, ProductVariant


class ProductCatalogPage(BaseListPage):
    """Product catalog/category page"""
    
    def __init__(self, driver, webdriver_manager):
        super().__init__(driver, webdriver_manager)
        
        # Page identifiers
        self._page_url = "/products"
        self._page_title = "Products"
        self._unique_element = (By.CSS_SELECTOR, ".product-catalog, .products-grid, [data-testid='product-catalog']")
        
        # Product grid elements
        self.products_grid = (By.CSS_SELECTOR, ".products-grid, .product-list, [data-testid='products-grid']")
        self.product_cards = (By.CSS_SELECTOR, ".product-card, .product-item, [data-testid='product-card']")
        self.product_images = (By.CSS_SELECTOR, ".product-image img, .product-card img")
        self.product_names = (By.CSS_SELECTOR, ".product-name, .product-title, [data-testid='product-name']")
        self.product_prices = (By.CSS_SELECTOR, ".product-price, .price, [data-testid='product-price']")
        self.product_ratings = (By.CSS_SELECTOR, ".product-rating, .rating, [data-testid='product-rating']")
        
        # Category navigation
        self.category_menu = (By.CSS_SELECTOR, ".category-menu, .categories, [data-testid='category-menu']")
        self.category_links = (By.CSS_SELECTOR, ".category-link, .category-item a, [data-testid='category-link']")
        self.subcategory_links = (By.CSS_SELECTOR, ".subcategory-link, .subcategory a")
        self.breadcrumb = (By.CSS_SELECTOR, ".breadcrumb, .breadcrumbs, [data-testid='breadcrumb']")
        
        # Filtering elements
        self.filters_panel = (By.CSS_SELECTOR, ".filters, .filter-panel, [data-testid='filters']")
        self.price_filter = (By.CSS_SELECTOR, ".price-filter, [data-testid='price-filter']")
        self.price_min_input = (By.CSS_SELECTOR, "input[name='price_min'], #price_min, [data-testid='price-min']")
        self.price_max_input = (By.CSS_SELECTOR, "input[name='price_max'], #price_max, [data-testid='price-max']")
        self.brand_filter = (By.CSS_SELECTOR, ".brand-filter, [data-testid='brand-filter']")
        self.rating_filter = (By.CSS_SELECTOR, ".rating-filter, [data-testid='rating-filter']")
        self.availability_filter = (By.CSS_SELECTOR, ".availability-filter, [data-testid='availability-filter']")
        self.size_filter = (By.CSS_SELECTOR, ".size-filter, [data-testid='size-filter']")
        self.color_filter = (By.CSS_SELECTOR, ".color-filter, [data-testid='color-filter']")
        self.apply_filters_btn = (By.CSS_SELECTOR, ".apply-filters, [data-testid='apply-filters']")
        self.clear_filters_btn = (By.CSS_SELECTOR, ".clear-filters, [data-testid='clear-filters']")
        
        # Sorting elements
        self.sort_dropdown = (By.CSS_SELECTOR, ".sort-dropdown, select[name='sort'], [data-testid='sort-dropdown']")
        self.sort_options = {
            'price_low_high': 'Price: Low to High',
            'price_high_low': 'Price: High to Low',
            'popularity': 'Popularity',
            'rating': 'Customer Rating',
            'newest': 'Newest Arrivals',
            'alphabetical': 'Alphabetical'
        }
        
        # View options
        self.grid_view_btn = (By.CSS_SELECTOR, ".grid-view, [data-testid='grid-view']")
        self.list_view_btn = (By.CSS_SELECTOR, ".list-view, [data-testid='list-view']")
        self.items_per_page = (By.CSS_SELECTOR, ".items-per-page select, [data-testid='items-per-page']")
        
        # Product actions
        self.add_to_cart_btns = (By.CSS_SELECTOR, ".add-to-cart, [data-testid='add-to-cart']")
        self.add_to_wishlist_btns = (By.CSS_SELECTOR, ".add-to-wishlist, [data-testid='add-to-wishlist']")
        self.quick_view_btns = (By.CSS_SELECTOR, ".quick-view, [data-testid='quick-view']")
        
        # Results info
        self.results_count = (By.CSS_SELECTOR, ".results-count, [data-testid='results-count']")
        self.no_results_message = (By.CSS_SELECTOR, ".no-results, [data-testid='no-results']")
    
    @property
    def page_url(self) -> str:
        return self._page_url
    
    @property
    def page_title(self) -> str:
        return self._page_title
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self._unique_element
    
    def get_product_cards(self) -> List:
        """Get all product cards on the page"""
        return self.find_elements(self.product_cards)
    
    def get_product_count(self) -> int:
        """Get number of products displayed"""
        return len(self.get_product_cards())
    
    def get_product_info(self, product_index: int) -> Dict[str, str]:
        """Get product information from card"""
        products = self.get_product_cards()
        if product_index >= len(products):
            raise IndexError(f"Product index {product_index} out of range")
        
        product = products[product_index]
        
        try:
            name = product.find_element(By.CSS_SELECTOR, ".product-name, .product-title").text.strip()
        except NoSuchElementException:
            name = ""
        
        try:
            price = product.find_element(By.CSS_SELECTOR, ".product-price, .price").text.strip()
        except NoSuchElementException:
            price = ""
        
        try:
            rating = product.find_element(By.CSS_SELECTOR, ".product-rating, .rating").text.strip()
        except NoSuchElementException:
            rating = ""
        
        try:
            image_src = product.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
        except NoSuchElementException:
            image_src = ""
        
        return {
            'name': name,
            'price': price,
            'rating': rating,
            'image_src': image_src
        }
    
    def click_product(self, product_index: int) -> None:
        """Click on a product to view details"""
        products = self.get_product_cards()
        if product_index >= len(products):
            raise IndexError(f"Product index {product_index} out of range")
        
        product = products[product_index]
        self.webdriver_manager.scroll_to_element(self.driver, product)
        product.click()
        self.wait_for_page_load()
    
    def navigate_to_category(self, category_name: str) -> None:
        """Navigate to specific category"""
        category_links = self.find_elements(self.category_links)
        for link in category_links:
            if category_name.lower() in link.text.lower():
                self.webdriver_manager.scroll_to_element(self.driver, link)
                link.click()
                self.wait_for_page_load()
                return
        raise NoSuchElementException(f"Category '{category_name}' not found")
    
    def navigate_to_subcategory(self, subcategory_name: str) -> None:
        """Navigate to specific subcategory"""
        subcategory_links = self.find_elements(self.subcategory_links)
        for link in subcategory_links:
            if subcategory_name.lower() in link.text.lower():
                self.webdriver_manager.scroll_to_element(self.driver, link)
                link.click()
                self.wait_for_page_load()
                return
        raise NoSuchElementException(f"Subcategory '{subcategory_name}' not found")
    
    def get_breadcrumb_text(self) -> str:
        """Get breadcrumb navigation text"""
        try:
            return self.get_element_text(self.breadcrumb)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def apply_price_filter(self, min_price: float = None, max_price: float = None) -> None:
        """Apply price range filter"""
        if min_price is not None:
            if self.is_element_present(self.price_min_input):
                self.send_keys_to_element(self.price_min_input, str(min_price))
        
        if max_price is not None:
            if self.is_element_present(self.price_max_input):
                self.send_keys_to_element(self.price_max_input, str(max_price))
        
        if self.is_element_present(self.apply_filters_btn):
            self.click_element(self.apply_filters_btn)
            self.wait_for_loading_to_complete()
    
    def apply_brand_filter(self, brand_name: str) -> None:
        """Apply brand filter"""
        brand_checkboxes = self.find_elements((By.CSS_SELECTOR, f".brand-filter input[type='checkbox'], .brand-filter .checkbox"))
        for checkbox in brand_checkboxes:
            label_text = checkbox.find_element(By.XPATH, "following-sibling::label | parent::label").text
            if brand_name.lower() in label_text.lower():
                if not checkbox.is_selected():
                    checkbox.click()
                break
        
        if self.is_element_present(self.apply_filters_btn):
            self.click_element(self.apply_filters_btn)
            self.wait_for_loading_to_complete()
    
    def apply_rating_filter(self, min_rating: int) -> None:
        """Apply minimum rating filter"""
        rating_options = self.find_elements((By.CSS_SELECTOR, f".rating-filter input[type='radio'], .rating-filter .radio"))
        for option in rating_options:
            if str(min_rating) in option.get_attribute("value") or str(min_rating) in option.text:
                option.click()
                break
        
        if self.is_element_present(self.apply_filters_btn):
            self.click_element(self.apply_filters_btn)
            self.wait_for_loading_to_complete()
    
    def apply_availability_filter(self, availability: str) -> None:
        """Apply availability filter (in_stock, out_of_stock, etc.)"""
        availability_options = self.find_elements((By.CSS_SELECTOR, f".availability-filter input, .availability-filter .checkbox"))
        for option in availability_options:
            if availability.lower() in option.get_attribute("value").lower():
                if not option.is_selected():
                    option.click()
                break
        
        if self.is_element_present(self.apply_filters_btn):
            self.click_element(self.apply_filters_btn)
            self.wait_for_loading_to_complete()
    
    def clear_all_filters(self) -> None:
        """Clear all applied filters"""
        if self.is_element_present(self.clear_filters_btn):
            self.click_element(self.clear_filters_btn)
            self.wait_for_loading_to_complete()
    
    def sort_products(self, sort_option: str) -> None:
        """Sort products by specified option"""
        if sort_option not in self.sort_options:
            raise ValueError(f"Invalid sort option: {sort_option}")
        
        if self.is_element_present(self.sort_dropdown):
            self.select_dropdown_by_text(self.sort_dropdown, self.sort_options[sort_option])
            self.wait_for_loading_to_complete()
    
    def switch_to_grid_view(self) -> None:
        """Switch to grid view"""
        if self.is_element_present(self.grid_view_btn):
            self.click_element(self.grid_view_btn)
            time.sleep(1)  # Wait for view change
    
    def switch_to_list_view(self) -> None:
        """Switch to list view"""
        if self.is_element_present(self.list_view_btn):
            self.click_element(self.list_view_btn)
            time.sleep(1)  # Wait for view change
    
    def set_items_per_page(self, count: int) -> None:
        """Set number of items per page"""
        if self.is_element_present(self.items_per_page):
            self.select_dropdown_by_value(self.items_per_page, str(count))
            self.wait_for_loading_to_complete()
    
    def add_product_to_cart(self, product_index: int) -> None:
        """Add product to cart from catalog page"""
        products = self.get_product_cards()
        if product_index >= len(products):
            raise IndexError(f"Product index {product_index} out of range")
        
        product = products[product_index]
        add_to_cart_btn = product.find_element(By.CSS_SELECTOR, ".add-to-cart, [data-testid='add-to-cart']")
        self.webdriver_manager.scroll_to_element(self.driver, add_to_cart_btn)
        add_to_cart_btn.click()
        time.sleep(2)  # Wait for cart update
    
    def add_product_to_wishlist(self, product_index: int) -> None:
        """Add product to wishlist from catalog page"""
        products = self.get_product_cards()
        if product_index >= len(products):
            raise IndexError(f"Product index {product_index} out of range")
        
        product = products[product_index]
        wishlist_btn = product.find_element(By.CSS_SELECTOR, ".add-to-wishlist, [data-testid='add-to-wishlist']")
        self.webdriver_manager.scroll_to_element(self.driver, wishlist_btn)
        wishlist_btn.click()
        time.sleep(2)  # Wait for wishlist update
    
    def get_results_count_text(self) -> str:
        """Get results count text"""
        try:
            return self.get_element_text(self.results_count)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def has_no_results(self) -> bool:
        """Check if no results message is displayed"""
        return self.is_element_present(self.no_results_message)
    
    def get_active_filters(self) -> List[str]:
        """Get list of currently active filters"""
        active_filters = []
        
        # Check for active filter tags/chips
        filter_tags = self.find_elements((By.CSS_SELECTOR, ".active-filter, .filter-tag, .applied-filter"))
        for tag in filter_tags:
            active_filters.append(tag.text.strip())
        
        return active_filters


class ProductSearchPage(BasePage):
    """Product search page and functionality"""
    
    def __init__(self, driver, webdriver_manager):
        super().__init__(driver, webdriver_manager)
        
        # Page identifiers
        self._page_url = "/search"
        self._page_title = "Search Results"
        self._unique_element = (By.CSS_SELECTOR, ".search-results, [data-testid='search-results']")
        
        # Search elements
        self.search_input = (By.CSS_SELECTOR, "input[type='search'], .search-input, [data-testid='search-input']")
        self.search_button = (By.CSS_SELECTOR, ".search-button, button[type='submit'], [data-testid='search-button']")
        self.search_suggestions = (By.CSS_SELECTOR, ".search-suggestions, .autocomplete, [data-testid='search-suggestions']")
        self.suggestion_items = (By.CSS_SELECTOR, ".suggestion-item, .autocomplete-item")
        
        # Search results
        self.search_results = (By.CSS_SELECTOR, ".search-results, [data-testid='search-results']")
        self.result_items = (By.CSS_SELECTOR, ".result-item, .search-result-item")
        self.search_query_display = (By.CSS_SELECTOR, ".search-query, [data-testid='search-query']")
        self.results_summary = (By.CSS_SELECTOR, ".results-summary, [data-testid='results-summary']")
        
        # Search filters (similar to catalog filters)
        self.search_filters = (By.CSS_SELECTOR, ".search-filters, [data-testid='search-filters']")
        
        # No results
        self.no_results_message = (By.CSS_SELECTOR, ".no-results, [data-testid='no-results']")
        self.search_suggestions_no_results = (By.CSS_SELECTOR, ".search-suggestions-no-results")
    
    @property
    def page_url(self) -> str:
        return self._page_url
    
    @property
    def page_title(self) -> str:
        return self._page_title
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self._unique_element
    
    def search_products(self, search_term: str) -> None:
        """Search for products with given term"""
        self.send_keys_to_element(self.search_input, search_term)
        self.click_element(self.search_button)
        self.wait_for_page_load()
    
    def search_with_enter_key(self, search_term: str) -> None:
        """Search using Enter key instead of button"""
        self.send_keys_to_element(self.search_input, search_term)
        self.press_key("ENTER")
        self.wait_for_page_load()
    
    def get_search_suggestions(self, partial_term: str) -> List[str]:
        """Get search suggestions for partial term"""
        self.send_keys_to_element(self.search_input, partial_term, clear_first=True)
        time.sleep(1)  # Wait for suggestions to appear
        
        suggestions = []
        if self.is_element_present(self.search_suggestions):
            suggestion_elements = self.find_elements(self.suggestion_items)
            suggestions = [elem.text.strip() for elem in suggestion_elements]
        
        return suggestions
    
    def click_search_suggestion(self, suggestion_text: str) -> None:
        """Click on a specific search suggestion"""
        suggestion_elements = self.find_elements(self.suggestion_items)
        for suggestion in suggestion_elements:
            if suggestion_text.lower() in suggestion.text.lower():
                suggestion.click()
                self.wait_for_page_load()
                return
        raise NoSuchElementException(f"Search suggestion '{suggestion_text}' not found")
    
    def get_search_results_count(self) -> int:
        """Get number of search results"""
        return len(self.find_elements(self.result_items))
    
    def get_search_query_display(self) -> str:
        """Get displayed search query"""
        try:
            return self.get_element_text(self.search_query_display)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def get_results_summary(self) -> str:
        """Get search results summary text"""
        try:
            return self.get_element_text(self.results_summary)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def has_search_results(self) -> bool:
        """Check if search returned results"""
        return self.get_search_results_count() > 0 and not self.has_no_results()
    
    def has_no_results(self) -> bool:
        """Check if no results message is displayed"""
        return self.is_element_present(self.no_results_message)
    
    def clear_search(self) -> None:
        """Clear search input"""
        self.send_keys_to_element(self.search_input, "", clear_first=True)


class ProductDetailPage(BasePage):
    """Product detail page"""
    
    def __init__(self, driver, webdriver_manager):
        super().__init__(driver, webdriver_manager)
        
        # Page identifiers
        self._page_url = "/product/"
        self._page_title = "Product Details"
        self._unique_element = (By.CSS_SELECTOR, ".product-detail, .product-page, [data-testid='product-detail']")
        
        # Product information
        self.product_name = (By.CSS_SELECTOR, ".product-name, h1, [data-testid='product-name']")
        self.product_price = (By.CSS_SELECTOR, ".product-price, .price, [data-testid='product-price']")
        self.product_description = (By.CSS_SELECTOR, ".product-description, [data-testid='product-description']")
        self.product_specifications = (By.CSS_SELECTOR, ".product-specs, .specifications, [data-testid='product-specs']")
        self.product_sku = (By.CSS_SELECTOR, ".product-sku, [data-testid='product-sku']")
        self.stock_status = (By.CSS_SELECTOR, ".stock-status, [data-testid='stock-status']")
        
        # Product images
        self.main_image = (By.CSS_SELECTOR, ".main-image img, .product-image-main img")
        self.thumbnail_images = (By.CSS_SELECTOR, ".thumbnail-images img, .product-thumbnails img")
        self.image_zoom_btn = (By.CSS_SELECTOR, ".zoom-image, [data-testid='zoom-image']")
        self.image_gallery = (By.CSS_SELECTOR, ".image-gallery, [data-testid='image-gallery']")
        
        # Product variants
        self.variant_selectors = (By.CSS_SELECTOR, ".variant-selector, .product-options")
        self.size_selector = (By.CSS_SELECTOR, ".size-selector select, [data-testid='size-selector']")
        self.color_selector = (By.CSS_SELECTOR, ".color-selector, [data-testid='color-selector']")
        self.quantity_input = (By.CSS_SELECTOR, ".quantity-input, input[name='quantity'], [data-testid='quantity']")
        self.quantity_increase = (By.CSS_SELECTOR, ".quantity-increase, [data-testid='quantity-increase']")
        self.quantity_decrease = (By.CSS_SELECTOR, ".quantity-decrease, [data-testid='quantity-decrease']")
        
        # Product actions
        self.add_to_cart_btn = (By.CSS_SELECTOR, ".add-to-cart, [data-testid='add-to-cart']")
        self.add_to_wishlist_btn = (By.CSS_SELECTOR, ".add-to-wishlist, [data-testid='add-to-wishlist']")
        self.buy_now_btn = (By.CSS_SELECTOR, ".buy-now, [data-testid='buy-now']")
        self.share_btn = (By.CSS_SELECTOR, ".share-product, [data-testid='share-product']")
        
        # Reviews and ratings
        self.product_rating = (By.CSS_SELECTOR, ".product-rating, .rating, [data-testid='product-rating']")
        self.reviews_section = (By.CSS_SELECTOR, ".reviews-section, [data-testid='reviews']")
        self.review_items = (By.CSS_SELECTOR, ".review-item, .review")
        self.write_review_btn = (By.CSS_SELECTOR, ".write-review, [data-testid='write-review']")
        
        # Related products
        self.related_products = (By.CSS_SELECTOR, ".related-products, [data-testid='related-products']")
        self.recommended_products = (By.CSS_SELECTOR, ".recommended-products, [data-testid='recommended-products']")
        
        # Seller information
        self.seller_info = (By.CSS_SELECTOR, ".seller-info, [data-testid='seller-info']")
        self.seller_name = (By.CSS_SELECTOR, ".seller-name, [data-testid='seller-name']")
        self.seller_rating = (By.CSS_SELECTOR, ".seller-rating, [data-testid='seller-rating']")
    
    @property
    def page_url(self) -> str:
        return self._page_url
    
    @property
    def page_title(self) -> str:
        return self._page_title
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self._unique_element
    
    def get_product_name(self) -> str:
        """Get product name"""
        return self.get_element_text(self.product_name)
    
    def get_product_price(self) -> str:
        """Get product price"""
        return self.get_element_text(self.product_price)
    
    def get_product_description(self) -> str:
        """Get product description"""
        return self.get_element_text(self.product_description)
    
    def get_product_sku(self) -> str:
        """Get product SKU"""
        try:
            return self.get_element_text(self.product_sku)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def get_stock_status(self) -> str:
        """Get stock availability status"""
        try:
            return self.get_element_text(self.stock_status)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def is_product_in_stock(self) -> bool:
        """Check if product is in stock"""
        stock_text = self.get_stock_status().lower()
        return "in stock" in stock_text or "available" in stock_text
    
    def click_main_image(self) -> None:
        """Click on main product image"""
        self.click_element(self.main_image)
    
    def click_thumbnail_image(self, index: int) -> None:
        """Click on thumbnail image by index"""
        thumbnails = self.find_elements(self.thumbnail_images)
        if index < len(thumbnails):
            thumbnails[index].click()
            time.sleep(1)  # Wait for image change
    
    def zoom_image(self) -> None:
        """Zoom product image"""
        if self.is_element_present(self.image_zoom_btn):
            self.click_element(self.image_zoom_btn)
    
    def select_size(self, size: str) -> None:
        """Select product size"""
        if self.is_element_present(self.size_selector):
            self.select_dropdown_by_text(self.size_selector, size)
    
    def select_color(self, color: str) -> None:
        """Select product color"""
        color_options = self.find_elements((By.CSS_SELECTOR, ".color-option, .color-selector input"))
        for option in color_options:
            if color.lower() in option.get_attribute("value").lower() or color.lower() in option.text.lower():
                option.click()
                break
    
    def set_quantity(self, quantity: int) -> None:
        """Set product quantity"""
        self.send_keys_to_element(self.quantity_input, str(quantity))
    
    def increase_quantity(self) -> None:
        """Increase quantity by 1"""
        if self.is_element_present(self.quantity_increase):
            self.click_element(self.quantity_increase)
    
    def decrease_quantity(self) -> None:
        """Decrease quantity by 1"""
        if self.is_element_present(self.quantity_decrease):
            self.click_element(self.quantity_decrease)
    
    def get_current_quantity(self) -> int:
        """Get current selected quantity"""
        try:
            quantity_text = self.get_element_attribute(self.quantity_input, "value")
            return int(quantity_text) if quantity_text.isdigit() else 1
        except (NoSuchElementException, ValueError):
            return 1
    
    def add_to_cart(self) -> None:
        """Add product to cart"""
        self.click_element(self.add_to_cart_btn)
        time.sleep(2)  # Wait for cart update
    
    def add_to_wishlist(self) -> None:
        """Add product to wishlist"""
        self.click_element(self.add_to_wishlist_btn)
        time.sleep(2)  # Wait for wishlist update
    
    def buy_now(self) -> None:
        """Click buy now button"""
        self.click_element(self.buy_now_btn)
        self.wait_for_page_load()
    
    def share_product(self) -> None:
        """Click share product button"""
        if self.is_element_present(self.share_btn):
            self.click_element(self.share_btn)
    
    def get_product_rating(self) -> str:
        """Get product rating"""
        try:
            return self.get_element_text(self.product_rating)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def get_reviews_count(self) -> int:
        """Get number of reviews"""
        return len(self.find_elements(self.review_items))
    
    def click_write_review(self) -> None:
        """Click write review button"""
        if self.is_element_present(self.write_review_btn):
            self.click_element(self.write_review_btn)
    
    def get_related_products_count(self) -> int:
        """Get number of related products"""
        if self.is_element_present(self.related_products):
            related_items = self.find_elements((By.CSS_SELECTOR, ".related-products .product-item"))
            return len(related_items)
        return 0
    
    def get_seller_name(self) -> str:
        """Get seller name"""
        try:
            return self.get_element_text(self.seller_name)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def get_seller_rating(self) -> str:
        """Get seller rating"""
        try:
            return self.get_element_text(self.seller_rating)
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def validate_product_page(self) -> Dict[str, bool]:
        """Validate product page elements"""
        validation_results = super().validate_page()
        
        # Product-specific validations
        validation_results.update({
            "product_name_present": self.is_element_present(self.product_name),
            "product_price_present": self.is_element_present(self.product_price),
            "main_image_present": self.is_element_present(self.main_image),
            "add_to_cart_present": self.is_element_present(self.add_to_cart_btn),
            "product_description_present": self.is_element_present(self.product_description)
        })
        
        return validation_results


class ProductComparisonPage(BasePage):
    """Product comparison page"""
    
    def __init__(self, driver, webdriver_manager):
        super().__init__(driver, webdriver_manager)
        
        # Page identifiers
        self._page_url = "/compare"
        self._page_title = "Product Comparison"
        self._unique_element = (By.CSS_SELECTOR, ".product-comparison, [data-testid='product-comparison']")
        
        # Comparison elements
        self.comparison_table = (By.CSS_SELECTOR, ".comparison-table, [data-testid='comparison-table']")
        self.compared_products = (By.CSS_SELECTOR, ".compared-product, .comparison-item")
        self.add_product_btn = (By.CSS_SELECTOR, ".add-to-compare, [data-testid='add-to-compare']")
        self.remove_product_btns = (By.CSS_SELECTOR, ".remove-from-compare, [data-testid='remove-from-compare']")
        self.clear_comparison_btn = (By.CSS_SELECTOR, ".clear-comparison, [data-testid='clear-comparison']")
        
        # Product details in comparison
        self.product_names = (By.CSS_SELECTOR, ".comparison-product-name")
        self.product_prices = (By.CSS_SELECTOR, ".comparison-product-price")
        self.product_images = (By.CSS_SELECTOR, ".comparison-product-image img")
        self.product_features = (By.CSS_SELECTOR, ".comparison-features")
    
    @property
    def page_url(self) -> str:
        return self._page_url
    
    @property
    def page_title(self) -> str:
        return self._page_title
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self._unique_element
    
    def get_compared_products_count(self) -> int:
        """Get number of products in comparison"""
        return len(self.find_elements(self.compared_products))
    
    def remove_product_from_comparison(self, product_index: int) -> None:
        """Remove product from comparison by index"""
        remove_buttons = self.find_elements(self.remove_product_btns)
        if product_index < len(remove_buttons):
            remove_buttons[product_index].click()
            time.sleep(1)  # Wait for removal
    
    def clear_all_comparison(self) -> None:
        """Clear all products from comparison"""
        if self.is_element_present(self.clear_comparison_btn):
            self.click_element(self.clear_comparison_btn)
            time.sleep(1)  # Wait for clearing


class WishlistPage(BaseListPage):
    """Wishlist page"""
    
    def __init__(self, driver, webdriver_manager):
        super().__init__(driver, webdriver_manager)
        
        # Page identifiers
        self._page_url = "/wishlist"
        self._page_title = "My Wishlist"
        self._unique_element = (By.CSS_SELECTOR, ".wishlist, [data-testid='wishlist']")
        
        # Wishlist elements
        self.wishlist_items = (By.CSS_SELECTOR, ".wishlist-item, [data-testid='wishlist-item']")
        self.remove_from_wishlist_btns = (By.CSS_SELECTOR, ".remove-from-wishlist, [data-testid='remove-from-wishlist']")
        self.add_to_cart_from_wishlist_btns = (By.CSS_SELECTOR, ".add-to-cart-from-wishlist, [data-testid='add-to-cart-from-wishlist']")
        self.clear_wishlist_btn = (By.CSS_SELECTOR, ".clear-wishlist, [data-testid='clear-wishlist']")
        self.empty_wishlist_message = (By.CSS_SELECTOR, ".empty-wishlist, [data-testid='empty-wishlist']")
    
    @property
    def page_url(self) -> str:
        return self._page_url
    
    @property
    def page_title(self) -> str:
        return self._page_title
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self._unique_element
    
    def get_wishlist_items_count(self) -> int:
        """Get number of items in wishlist"""
        return len(self.find_elements(self.wishlist_items))
    
    def remove_item_from_wishlist(self, item_index: int) -> None:
        """Remove item from wishlist by index"""
        remove_buttons = self.find_elements(self.remove_from_wishlist_btns)
        if item_index < len(remove_buttons):
            remove_buttons[item_index].click()
            time.sleep(1)  # Wait for removal
    
    def add_item_to_cart_from_wishlist(self, item_index: int) -> None:
        """Add item to cart from wishlist"""
        add_to_cart_buttons = self.find_elements(self.add_to_cart_from_wishlist_btns)
        if item_index < len(add_to_cart_buttons):
            add_to_cart_buttons[item_index].click()
            time.sleep(2)  # Wait for cart update
    
    def clear_wishlist(self) -> None:
        """Clear entire wishlist"""
        if self.is_element_present(self.clear_wishlist_btn):
            self.click_element(self.clear_wishlist_btn)
            time.sleep(1)  # Wait for clearing
    
    def is_wishlist_empty(self) -> bool:
        """Check if wishlist is empty"""
        return self.is_element_present(self.empty_wishlist_message) or self.get_wishlist_items_count() == 0