"""
Shopping Cart and Checkout Page Objects

Page object models for shopping cart functionality, checkout process,
address management, payment processing, and order completion.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .page_objects import BasePage, BaseFormPage
from .webdriver_manager import WebDriverManager
from ..core.models import Address, PaymentMethod


class ShoppingCartPage(BasePage):
    """Shopping cart page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
        
        # Cart page elements
        self.cart_items_container = (By.CSS_SELECTOR, ".cart-items, .shopping-cart-items, [data-testid='cart-items']")
        self.cart_item = (By.CSS_SELECTOR, ".cart-item, .item, [data-testid='cart-item']")
        self.item_name = (By.CSS_SELECTOR, ".item-name, .product-name, h3, [data-testid='item-name']")
        self.item_price = (By.CSS_SELECTOR, ".item-price, .price, [data-testid='item-price']")
        self.item_quantity_input = (By.CSS_SELECTOR, ".quantity-input, input[type='number'], [data-testid='quantity']")
        self.quantity_increase_btn = (By.CSS_SELECTOR, ".qty-increase, .plus-btn, [data-testid='increase-qty']")
        self.quantity_decrease_btn = (By.CSS_SELECTOR, ".qty-decrease, .minus-btn, [data-testid='decrease-qty']")
        self.remove_item_btn = (By.CSS_SELECTOR, ".remove-item, .delete-btn, [data-testid='remove-item']")
        
        # Cart summary elements
        self.subtotal = (By.CSS_SELECTOR, ".subtotal, [data-testid='subtotal']")
        self.tax_amount = (By.CSS_SELECTOR, ".tax, .tax-amount, [data-testid='tax']")
        self.shipping_cost = (By.CSS_SELECTOR, ".shipping, .shipping-cost, [data-testid='shipping']")
        self.discount_amount = (By.CSS_SELECTOR, ".discount, .discount-amount, [data-testid='discount']")
        self.total_amount = (By.CSS_SELECTOR, ".total, .grand-total, [data-testid='total']")
        
        # Coupon elements
        self.coupon_input = (By.CSS_SELECTOR, ".coupon-input, input[name='coupon'], [data-testid='coupon-input']")
        self.apply_coupon_btn = (By.CSS_SELECTOR, ".apply-coupon, .coupon-btn, [data-testid='apply-coupon']")
        self.remove_coupon_btn = (By.CSS_SELECTOR, ".remove-coupon, [data-testid='remove-coupon']")
        self.coupon_message = (By.CSS_SELECTOR, ".coupon-message, .coupon-status, [data-testid='coupon-message']")
        
        # Action buttons
        self.continue_shopping_btn = (By.CSS_SELECTOR, ".continue-shopping, [data-testid='continue-shopping']")
        self.checkout_btn = (By.CSS_SELECTOR, ".checkout-btn, .proceed-checkout, [data-testid='checkout']")
        self.clear_cart_btn = (By.CSS_SELECTOR, ".clear-cart, [data-testid='clear-cart']")
        
        # Empty cart elements
        self.empty_cart_message = (By.CSS_SELECTOR, ".empty-cart, .cart-empty, [data-testid='empty-cart']")
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/cart"
    
    @property
    def page_title(self) -> str:
        return "Shopping Cart"
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self.cart_items_container
    
    def get_cart_items(self) -> List[Dict[str, Any]]:
        """Get all items in cart with their details"""
        items = []
        cart_item_elements = self.find_elements(self.cart_item)
        
        for item_element in cart_item_elements:
            try:
                # Get item details from within the item element
                name_element = item_element.find_element(*self.item_name)
                price_element = item_element.find_element(*self.item_price)
                quantity_element = item_element.find_element(*self.item_quantity_input)
                
                item_data = {
                    'name': name_element.text.strip(),
                    'price': price_element.text.strip(),
                    'quantity': int(quantity_element.get_attribute('value') or '0'),
                    'element': item_element
                }
                items.append(item_data)
            except (NoSuchElementException, ValueError) as e:
                self.logger.warning(f"Could not parse cart item: {str(e)}")
                continue
        
        return items
    
    def get_cart_item_count(self) -> int:
        """Get total number of items in cart"""
        return len(self.get_cart_items())
    
    def is_cart_empty(self) -> bool:
        """Check if cart is empty"""
        return self.is_element_present(self.empty_cart_message) or self.get_cart_item_count() == 0
    
    def update_item_quantity(self, item_name: str, new_quantity: int) -> bool:
        """Update quantity of specific item"""
        try:
            items = self.get_cart_items()
            for item in items:
                if item_name.lower() in item['name'].lower():
                    quantity_input = item['element'].find_element(*self.item_quantity_input)
                    quantity_input.clear()
                    quantity_input.send_keys(str(new_quantity))
                    
                    # Trigger update (may need to click update button or press enter)
                    quantity_input.send_keys("\n")
                    time.sleep(2)  # Wait for update
                    return True
            
            self.logger.error(f"Item '{item_name}' not found in cart")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update item quantity: {str(e)}")
            return False
    
    def increase_item_quantity(self, item_name: str) -> bool:
        """Increase quantity of specific item by 1"""
        try:
            items = self.get_cart_items()
            for item in items:
                if item_name.lower() in item['name'].lower():
                    increase_btn = item['element'].find_element(*self.quantity_increase_btn)
                    increase_btn.click()
                    time.sleep(1)  # Wait for update
                    return True
            
            self.logger.error(f"Item '{item_name}' not found in cart")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to increase item quantity: {str(e)}")
            return False
    
    def decrease_item_quantity(self, item_name: str) -> bool:
        """Decrease quantity of specific item by 1"""
        try:
            items = self.get_cart_items()
            for item in items:
                if item_name.lower() in item['name'].lower():
                    decrease_btn = item['element'].find_element(*self.quantity_decrease_btn)
                    decrease_btn.click()
                    time.sleep(1)  # Wait for update
                    return True
            
            self.logger.error(f"Item '{item_name}' not found in cart")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to decrease item quantity: {str(e)}")
            return False
    
    def remove_item(self, item_name: str) -> bool:
        """Remove specific item from cart"""
        try:
            items = self.get_cart_items()
            for item in items:
                if item_name.lower() in item['name'].lower():
                    remove_btn = item['element'].find_element(*self.remove_item_btn)
                    remove_btn.click()
                    
                    # Handle confirmation dialog if present
                    try:
                        self.webdriver_manager.handle_alert(self.driver, "accept")
                    except:
                        pass  # No alert present
                    
                    time.sleep(2)  # Wait for removal
                    return True
            
            self.logger.error(f"Item '{item_name}' not found in cart")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove item: {str(e)}")
            return False
    
    def apply_coupon(self, coupon_code: str) -> bool:
        """Apply coupon code"""
        try:
            if not self.is_element_present(self.coupon_input):
                self.logger.error("Coupon input field not found")
                return False
            
            self.send_keys_to_element(self.coupon_input, coupon_code)
            self.click_element(self.apply_coupon_btn)
            
            time.sleep(3)  # Wait for coupon processing
            
            # Check for success or error message
            if self.is_element_present(self.coupon_message):
                message = self.get_element_text(self.coupon_message)
                return "applied" in message.lower() or "success" in message.lower()
            
            return True  # Assume success if no error message
            
        except Exception as e:
            self.logger.error(f"Failed to apply coupon: {str(e)}")
            return False
    
    def remove_coupon(self) -> bool:
        """Remove applied coupon"""
        try:
            if self.is_element_present(self.remove_coupon_btn):
                self.click_element(self.remove_coupon_btn)
                time.sleep(2)  # Wait for removal
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove coupon: {str(e)}")
            return False
    
    def get_coupon_message(self) -> str:
        """Get coupon application message"""
        try:
            return self.get_element_text(self.coupon_message)
        except:
            return ""
    
    def get_cart_summary(self) -> Dict[str, str]:
        """Get cart summary with all amounts"""
        summary = {}
        
        try:
            if self.is_element_present(self.subtotal):
                summary['subtotal'] = self.get_element_text(self.subtotal)
            
            if self.is_element_present(self.tax_amount):
                summary['tax'] = self.get_element_text(self.tax_amount)
            
            if self.is_element_present(self.shipping_cost):
                summary['shipping'] = self.get_element_text(self.shipping_cost)
            
            if self.is_element_present(self.discount_amount):
                summary['discount'] = self.get_element_text(self.discount_amount)
            
            if self.is_element_present(self.total_amount):
                summary['total'] = self.get_element_text(self.total_amount)
                
        except Exception as e:
            self.logger.error(f"Failed to get cart summary: {str(e)}")
        
        return summary
    
    def proceed_to_checkout(self) -> bool:
        """Proceed to checkout"""
        try:
            if self.is_cart_empty():
                self.logger.error("Cannot checkout with empty cart")
                return False
            
            self.click_element(self.checkout_btn)
            time.sleep(3)  # Wait for navigation
            
            # Verify navigation to checkout
            current_url = self.get_current_url()
            return "/checkout" in current_url
            
        except Exception as e:
            self.logger.error(f"Failed to proceed to checkout: {str(e)}")
            return False
    
    def continue_shopping(self) -> bool:
        """Continue shopping (go back to products)"""
        try:
            self.click_element(self.continue_shopping_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to continue shopping: {str(e)}")
            return False
    
    def clear_cart(self) -> bool:
        """Clear all items from cart"""
        try:
            if self.is_element_present(self.clear_cart_btn):
                self.click_element(self.clear_cart_btn)
                
                # Handle confirmation dialog
                try:
                    self.webdriver_manager.handle_alert(self.driver, "accept")
                except:
                    pass
                
                time.sleep(2)  # Wait for clearing
                return self.is_cart_empty()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to clear cart: {str(e)}")
            return False


class CheckoutPage(BaseFormPage):
    """Checkout page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
        
        # Checkout steps/sections
        self.shipping_section = (By.CSS_SELECTOR, ".shipping-section, [data-testid='shipping']")
        self.payment_section = (By.CSS_SELECTOR, ".payment-section, [data-testid='payment']")
        self.review_section = (By.CSS_SELECTOR, ".review-section, [data-testid='review']")
        
        # Guest checkout
        self.guest_checkout_option = (By.CSS_SELECTOR, ".guest-checkout, [data-testid='guest-checkout']")
        self.login_option = (By.CSS_SELECTOR, ".login-option, [data-testid='login-option']")
        
        # Shipping address elements
        self.shipping_address_form = (By.CSS_SELECTOR, ".shipping-form, [data-testid='shipping-form']")
        self.first_name_input = (By.CSS_SELECTOR, "input[name='firstName'], [data-testid='first-name']")
        self.last_name_input = (By.CSS_SELECTOR, "input[name='lastName'], [data-testid='last-name']")
        self.email_input = (By.CSS_SELECTOR, "input[name='email'], [data-testid='email']")
        self.phone_input = (By.CSS_SELECTOR, "input[name='phone'], [data-testid='phone']")
        self.address_line1_input = (By.CSS_SELECTOR, "input[name='address1'], [data-testid='address1']")
        self.address_line2_input = (By.CSS_SELECTOR, "input[name='address2'], [data-testid='address2']")
        self.city_input = (By.CSS_SELECTOR, "input[name='city'], [data-testid='city']")
        self.state_select = (By.CSS_SELECTOR, "select[name='state'], [data-testid='state']")
        self.postal_code_input = (By.CSS_SELECTOR, "input[name='postalCode'], [data-testid='postal-code']")
        self.country_select = (By.CSS_SELECTOR, "select[name='country'], [data-testid='country']")
        
        # Saved addresses
        self.saved_addresses = (By.CSS_SELECTOR, ".saved-address, [data-testid='saved-address']")
        self.add_new_address_btn = (By.CSS_SELECTOR, ".add-address, [data-testid='add-address']")
        
        # Shipping options
        self.shipping_options = (By.CSS_SELECTOR, ".shipping-option, [data-testid='shipping-option']")
        self.standard_shipping = (By.CSS_SELECTOR, "input[value='standard'], [data-testid='standard-shipping']")
        self.express_shipping = (By.CSS_SELECTOR, "input[value='express'], [data-testid='express-shipping']")
        self.overnight_shipping = (By.CSS_SELECTOR, "input[value='overnight'], [data-testid='overnight-shipping']")
        
        # Payment elements
        self.payment_methods = (By.CSS_SELECTOR, ".payment-method, [data-testid='payment-method']")
        self.credit_card_option = (By.CSS_SELECTOR, "input[value='credit_card'], [data-testid='credit-card']")
        self.paypal_option = (By.CSS_SELECTOR, "input[value='paypal'], [data-testid='paypal']")
        self.cod_option = (By.CSS_SELECTOR, "input[value='cod'], [data-testid='cod']")
        
        # Credit card form
        self.card_number_input = (By.CSS_SELECTOR, "input[name='cardNumber'], [data-testid='card-number']")
        self.expiry_month_select = (By.CSS_SELECTOR, "select[name='expiryMonth'], [data-testid='expiry-month']")
        self.expiry_year_select = (By.CSS_SELECTOR, "select[name='expiryYear'], [data-testid='expiry-year']")
        self.cvv_input = (By.CSS_SELECTOR, "input[name='cvv'], [data-testid='cvv']")
        self.cardholder_name_input = (By.CSS_SELECTOR, "input[name='cardholderName'], [data-testid='cardholder-name']")
        
        # Billing address
        self.billing_same_as_shipping = (By.CSS_SELECTOR, "input[name='billingSameAsShipping'], [data-testid='billing-same']")
        self.billing_address_form = (By.CSS_SELECTOR, ".billing-form, [data-testid='billing-form']")
        
        # Order review
        self.order_items = (By.CSS_SELECTOR, ".order-item, [data-testid='order-item']")
        self.order_summary = (By.CSS_SELECTOR, ".order-summary, [data-testid='order-summary']")
        
        # Navigation buttons
        self.continue_to_payment_btn = (By.CSS_SELECTOR, ".continue-payment, [data-testid='continue-payment']")
        self.continue_to_review_btn = (By.CSS_SELECTOR, ".continue-review, [data-testid='continue-review']")
        self.place_order_btn = (By.CSS_SELECTOR, ".place-order, [data-testid='place-order']")
        self.back_to_cart_btn = (By.CSS_SELECTOR, ".back-to-cart, [data-testid='back-to-cart']")
        
        # Order confirmation
        self.order_confirmation = (By.CSS_SELECTOR, ".order-confirmation, [data-testid='order-confirmation']")
        self.order_number = (By.CSS_SELECTOR, ".order-number, [data-testid='order-number']")
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/checkout"
    
    @property
    def page_title(self) -> str:
        return "Checkout"
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self.shipping_section
    
    def select_guest_checkout(self) -> bool:
        """Select guest checkout option"""
        try:
            if self.is_element_present(self.guest_checkout_option):
                self.click_element(self.guest_checkout_option)
                time.sleep(1)
                return True
            return True  # Already in guest mode
            
        except Exception as e:
            self.logger.error(f"Failed to select guest checkout: {str(e)}")
            return False
    
    def fill_shipping_address(self, address_data: Dict[str, Any]) -> bool:
        """Fill shipping address form"""
        try:
            # Fill personal information
            if 'first_name' in address_data:
                self.send_keys_to_element(self.first_name_input, address_data['first_name'])
            
            if 'last_name' in address_data:
                self.send_keys_to_element(self.last_name_input, address_data['last_name'])
            
            if 'email' in address_data:
                self.send_keys_to_element(self.email_input, address_data['email'])
            
            if 'phone' in address_data:
                self.send_keys_to_element(self.phone_input, address_data['phone'])
            
            # Fill address information
            self.send_keys_to_element(self.address_line1_input, address_data['street'])
            
            if 'address_line2' in address_data:
                self.send_keys_to_element(self.address_line2_input, address_data['address_line2'])
            
            self.send_keys_to_element(self.city_input, address_data['city'])
            
            # Select state and country
            if self.is_element_present(self.state_select):
                self.select_dropdown_by_text(self.state_select, address_data['state'])
            
            if self.is_element_present(self.country_select):
                self.select_dropdown_by_text(self.country_select, address_data['country'])
            
            self.send_keys_to_element(self.postal_code_input, address_data['postal_code'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill shipping address: {str(e)}")
            return False
    
    def select_shipping_option(self, shipping_type: str = "standard") -> bool:
        """Select shipping option"""
        try:
            shipping_map = {
                "standard": self.standard_shipping,
                "express": self.express_shipping,
                "overnight": self.overnight_shipping
            }
            
            if shipping_type in shipping_map:
                self.click_element(shipping_map[shipping_type])
                time.sleep(1)  # Wait for price update
                return True
            
            self.logger.error(f"Unknown shipping type: {shipping_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to select shipping option: {str(e)}")
            return False
    
    def continue_to_payment(self) -> bool:
        """Continue to payment step"""
        try:
            self.click_element(self.continue_to_payment_btn)
            time.sleep(2)
            
            # Verify payment section is visible
            return self.is_element_visible(self.payment_section)
            
        except Exception as e:
            self.logger.error(f"Failed to continue to payment: {str(e)}")
            return False
    
    def select_payment_method(self, payment_type: str) -> bool:
        """Select payment method"""
        try:
            payment_map = {
                "credit_card": self.credit_card_option,
                "paypal": self.paypal_option,
                "cod": self.cod_option
            }
            
            if payment_type in payment_map:
                self.click_element(payment_map[payment_type])
                time.sleep(1)
                return True
            
            self.logger.error(f"Unknown payment type: {payment_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to select payment method: {str(e)}")
            return False
    
    def fill_credit_card_details(self, card_data: Dict[str, Any]) -> bool:
        """Fill credit card payment details"""
        try:
            self.send_keys_to_element(self.card_number_input, card_data['card_number'])
            
            if self.is_element_present(self.expiry_month_select):
                self.select_dropdown_by_value(self.expiry_month_select, str(card_data['expiry_month']))
            
            if self.is_element_present(self.expiry_year_select):
                self.select_dropdown_by_value(self.expiry_year_select, str(card_data['expiry_year']))
            
            self.send_keys_to_element(self.cvv_input, card_data['cvv'])
            
            if 'cardholder_name' in card_data:
                self.send_keys_to_element(self.cardholder_name_input, card_data['cardholder_name'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill credit card details: {str(e)}")
            return False
    
    def set_billing_same_as_shipping(self, same_as_shipping: bool = True) -> bool:
        """Set billing address same as shipping"""
        try:
            checkbox = self.find_element(self.billing_same_as_shipping)
            if checkbox.is_selected() != same_as_shipping:
                checkbox.click()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set billing address option: {str(e)}")
            return False
    
    def continue_to_review(self) -> bool:
        """Continue to order review step"""
        try:
            self.click_element(self.continue_to_review_btn)
            time.sleep(2)
            
            # Verify review section is visible
            return self.is_element_visible(self.review_section)
            
        except Exception as e:
            self.logger.error(f"Failed to continue to review: {str(e)}")
            return False
    
    def get_order_summary(self) -> Dict[str, Any]:
        """Get order summary details"""
        summary = {}
        
        try:
            # Get order items
            items = []
            item_elements = self.find_elements(self.order_items)
            for item_element in item_elements:
                item_text = item_element.text
                items.append(item_text)
            summary['items'] = items
            
            # Get order totals (similar to cart summary)
            if self.is_element_present(self.order_summary):
                summary_text = self.get_element_text(self.order_summary)
                summary['summary_text'] = summary_text
                
        except Exception as e:
            self.logger.error(f"Failed to get order summary: {str(e)}")
        
        return summary
    
    def place_order(self) -> bool:
        """Place the order"""
        try:
            self.click_element(self.place_order_btn)
            time.sleep(5)  # Wait for order processing
            
            # Check for order confirmation
            return self.is_element_present(self.order_confirmation)
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {str(e)}")
            return False
    
    def get_order_number(self) -> str:
        """Get order confirmation number"""
        try:
            if self.is_element_present(self.order_number):
                return self.get_element_text(self.order_number)
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get order number: {str(e)}")
            return ""
    
    def back_to_cart(self) -> bool:
        """Go back to shopping cart"""
        try:
            self.click_element(self.back_to_cart_btn)
            time.sleep(2)
            
            current_url = self.get_current_url()
            return "/cart" in current_url
            
        except Exception as e:
            self.logger.error(f"Failed to go back to cart: {str(e)}")
            return False
    
    def complete_guest_checkout(self, address_data: Dict[str, Any], payment_data: Dict[str, Any], 
                               shipping_type: str = "standard") -> Dict[str, Any]:
        """Complete entire guest checkout process"""
        result = {
            'success': False,
            'order_number': '',
            'error': ''
        }
        
        try:
            # Step 1: Select guest checkout
            if not self.select_guest_checkout():
                result['error'] = "Failed to select guest checkout"
                return result
            
            # Step 2: Fill shipping address
            if not self.fill_shipping_address(address_data):
                result['error'] = "Failed to fill shipping address"
                return result
            
            # Step 3: Select shipping option
            if not self.select_shipping_option(shipping_type):
                result['error'] = "Failed to select shipping option"
                return result
            
            # Step 4: Continue to payment
            if not self.continue_to_payment():
                result['error'] = "Failed to continue to payment"
                return result
            
            # Step 5: Select payment method and fill details
            payment_type = payment_data.get('type', 'credit_card')
            if not self.select_payment_method(payment_type):
                result['error'] = "Failed to select payment method"
                return result
            
            if payment_type == 'credit_card':
                if not self.fill_credit_card_details(payment_data):
                    result['error'] = "Failed to fill credit card details"
                    return result
            
            # Step 6: Set billing address
            self.set_billing_same_as_shipping(True)
            
            # Step 7: Continue to review
            if not self.continue_to_review():
                result['error'] = "Failed to continue to review"
                return result
            
            # Step 8: Place order
            if not self.place_order():
                result['error'] = "Failed to place order"
                return result
            
            # Step 9: Get order number
            order_number = self.get_order_number()
            
            result['success'] = True
            result['order_number'] = order_number
            
        except Exception as e:
            result['error'] = f"Checkout process failed: {str(e)}"
        
        return result