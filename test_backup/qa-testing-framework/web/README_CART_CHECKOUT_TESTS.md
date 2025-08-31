# Shopping Cart and Checkout Tests

This document describes the comprehensive test suite for shopping cart functionality and checkout process testing.

## Overview

The shopping cart and checkout test suite validates all aspects of the e-commerce cart and purchase flow, including:

- Shopping cart operations (add, update, remove items)
- Quantity management and validation
- Coupon code application and validation
- Guest and registered user checkout flows
- Address management and validation
- Shipping option selection and cost calculation
- Payment method selection and validation
- Tax calculation accuracy
- Order review and confirmation
- Navigation and error handling

## Test Coverage

### Shopping Cart Tests (Requirements: 1.1, 2.2, 2.3)

#### Cart Operations
- **TC_CART_001**: Add single item to cart
- **TC_CART_002**: Add multiple items to cart
- **TC_CART_003**: Update item quantity in cart
- **TC_CART_004**: Increase item quantity with plus button
- **TC_CART_005**: Decrease item quantity with minus button
- **TC_CART_006**: Remove item from cart

#### Coupon Management
- **TC_CART_007**: Apply valid coupon code
- **TC_CART_008**: Apply invalid coupon code
- **TC_CART_009**: Remove applied coupon

### Checkout Process Tests (Requirements: 1.1, 2.2, 2.3, 3.2)

#### Guest Checkout Flow
- **TC_CHECKOUT_001**: Complete guest checkout flow
- **TC_CHECKOUT_002**: Address validation in guest checkout
- **TC_CHECKOUT_003**: Shipping option selection and cost calculation
- **TC_CHECKOUT_004**: Payment method selection
- **TC_CHECKOUT_005**: Credit card payment validation
- **TC_CHECKOUT_006**: Order review and confirmation
- **TC_CHECKOUT_007**: Tax calculation accuracy
- **TC_CHECKOUT_008**: Navigation back to cart from checkout

## Test Data

### Products
- Electronics (Headphones, Smartphone Case)
- Clothing (T-Shirts)
- Home & Kitchen (Coffee Maker)
- Sports (Running Shoes)
- High-value items for tax testing

### Addresses
- Multiple US addresses with different states
- Valid and invalid address formats
- International addresses (if supported)

### Payment Methods
- Credit Cards (Visa, Mastercard, Amex test cards)
- PayPal
- Cash on Delivery (COD)
- Invalid payment data for negative testing

### Coupon Codes
- Percentage discounts (10% off)
- Fixed amount discounts ($20 off)
- Free shipping coupons
- Expired/invalid coupons

## Page Objects

### ShoppingCartPage
Handles all shopping cart interactions:
- Item management (add, update, remove)
- Quantity controls
- Coupon application
- Cart summary display
- Navigation to checkout

### CheckoutPage
Manages the checkout process:
- Guest/registered user selection
- Address form handling
- Shipping option selection
- Payment method selection
- Credit card form validation
- Order review and confirmation

## Test Execution

### Running All Tests
```bash
cd qa-testing-framework/web
python run_cart_checkout_tests.py
```

### Running Specific Tests
```bash
python run_cart_checkout_tests.py --tests test_add_single_item_to_cart test_guest_checkout_complete_flow
```

### Environment Selection
```bash
python run_cart_checkout_tests.py --env staging
```

### Verbose Output
```bash
python run_cart_checkout_tests.py --verbose
```

## Test Scenarios

### Basic Cart Operations
1. **Single Item Addition**
   - Add one product to cart
   - Verify cart contains item
   - Check cart summary

2. **Multiple Item Management**
   - Add multiple different products
   - Update quantities
   - Remove specific items
   - Verify cart state after each operation

3. **Quantity Controls**
   - Use plus/minus buttons
   - Direct quantity input
   - Validate minimum/maximum quantities
   - Handle zero quantity (item removal)

### Coupon Testing
1. **Valid Coupon Application**
   - Apply percentage discount coupon
   - Apply fixed amount discount coupon
   - Apply free shipping coupon
   - Verify discount calculations

2. **Invalid Coupon Handling**
   - Expired coupons
   - Non-existent coupon codes
   - Coupons below minimum order value
   - Multiple coupon restrictions

### Guest Checkout Flow
1. **Complete Purchase Process**
   - Add items to cart
   - Proceed to checkout
   - Fill shipping address
   - Select shipping method
   - Choose payment method
   - Enter payment details
   - Review order
   - Place order
   - Verify confirmation

2. **Address Validation**
   - Required field validation
   - Format validation (email, phone, postal code)
   - State/country selection
   - Address line length limits

3. **Payment Processing**
   - Credit card validation
   - Expiry date validation
   - CVV validation
   - Cardholder name validation
   - Alternative payment methods

### Calculation Accuracy
1. **Tax Calculations**
   - Verify tax rates by location
   - Tax on discounted amounts
   - Tax exemptions (if applicable)
   - Rounding accuracy

2. **Shipping Costs**
   - Standard shipping rates
   - Express shipping premiums
   - Free shipping thresholds
   - International shipping (if supported)

3. **Total Calculations**
   - Subtotal accuracy
   - Discount applications
   - Tax additions
   - Shipping additions
   - Final total verification

## Error Handling

### Cart Errors
- Out of stock items
- Quantity exceeding stock
- Invalid product data
- Session timeout handling

### Checkout Errors
- Invalid address formats
- Payment processing failures
- Network timeouts
- Server errors during order placement

### Validation Errors
- Missing required fields
- Invalid email formats
- Invalid phone numbers
- Invalid payment card data

## Browser Compatibility

Tests are executed across multiple browsers:
- Chrome (primary)
- Firefox
- Safari
- Edge

## Test Data Management

### Dynamic Test Data
- Unique email addresses for each test run
- Random product selections
- Timestamp-based order numbers
- Isolated test environments

### Data Cleanup
- Cart clearing after tests
- Test user cleanup
- Order data isolation
- Payment sandbox usage

## Reporting

### Test Results
- Pass/fail status for each test
- Execution time tracking
- Screenshot capture on failures
- Detailed error logs

### Defect Tracking
- Automatic defect logging
- Severity classification
- Reproduction steps
- Browser and environment details

### Coverage Metrics
- Feature coverage percentage
- User journey completion rates
- Payment method coverage
- Shipping option coverage

## Integration Points

### Backend API Testing
- Cart API endpoints
- Order creation APIs
- Payment processing APIs
- Inventory management APIs

### Database Validation
- Order data persistence
- Cart state management
- User session handling
- Transaction integrity

### Third-party Services
- Payment gateway integration
- Shipping provider APIs
- Tax calculation services
- Email notification services

## Performance Considerations

### Load Testing Scenarios
- Multiple users adding to cart simultaneously
- High-volume checkout processing
- Payment gateway response times
- Database query performance

### Optimization Validation
- Page load times during checkout
- Cart update response times
- Payment processing delays
- Order confirmation speed

## Security Testing

### Data Protection
- Credit card data handling
- Personal information encryption
- Session security
- HTTPS enforcement

### Input Validation
- SQL injection prevention
- XSS protection
- CSRF token validation
- Input sanitization

## Maintenance

### Test Updates
- Regular test data refresh
- New payment method additions
- Shipping option updates
- Tax rate changes

### Environment Sync
- Development environment setup
- Staging environment validation
- Production monitoring
- Test data synchronization

This comprehensive test suite ensures reliable shopping cart and checkout functionality across all supported user scenarios and edge cases.