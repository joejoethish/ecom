# Payment Processing Tests

This module provides comprehensive testing for payment processing functionality including all supported payment methods, gateway integration testing in sandbox mode, payment failure and retry scenarios, refund and partial payment processing, and payment security validation.

## Overview

The payment processing test suite validates 100% of payment-related user journeys and ensures robust payment handling across all supported payment methods and scenarios.

## Test Coverage

### Payment Methods Tested

1. **Credit Cards**
   - Visa, Mastercard, American Express
   - Valid card processing
   - Declined card handling
   - Insufficient funds scenarios

2. **Debit Cards**
   - All major debit card networks
   - PIN and signature verification
   - Daily limit validation

3. **Digital Wallets**
   - PayPal integration
   - Google Pay processing
   - Apple Pay functionality

4. **UPI Payments**
   - UPI ID validation
   - Multiple UPI app support
   - Real-time payment processing

5. **EMI Options**
   - Multiple tenure options (3, 6, 12, 24 months)
   - Interest rate calculations
   - Bank-specific EMI processing

6. **Cash on Delivery (COD)**
   - COD availability validation
   - Location-based restrictions
   - Order confirmation flow

### Test Scenarios

#### Success Scenarios
- Valid payment processing for all methods
- High-value transaction handling
- International card processing
- Multi-currency support

#### Failure Scenarios
- Invalid card number validation
- Expired card handling
- Invalid CVV validation
- Insufficient funds processing
- Network timeout handling
- Gateway error responses

#### Security Testing
- SSL/TLS encryption validation
- PCI compliance verification
- Input sanitization testing
- CSRF protection validation
- Rate limiting verification

#### Refund Processing
- Full order refunds
- Partial refunds
- Multiple partial refunds
- Refund validation rules

## File Structure

```
qa-testing-framework/web/
├── payment_pages.py              # Page objects for payment processing
├── payment_test_data.py          # Test data generator for payment scenarios
├── test_payment_processing.py    # Main test suite
├── run_payment_tests.py          # Test runner with reporting
└── README_PAYMENT_TESTS.md       # This documentation
```

## Test Data

### Sandbox Credit Cards

The test suite uses sandbox credit card numbers that simulate different scenarios:

```python
# Valid Test Cards
'4111111111111111'  # Visa - Success
'5555555555554444'  # Mastercard - Success
'378282246310005'   # Amex - Success

# Failure Test Cards
'4000000000000002'  # Visa - Declined
'4000000000009995'  # Visa - Insufficient Funds
'4000000000000119'  # Visa - Processing Error
```

### UPI Test Data

```python
# Valid UPI IDs
'testuser@paytm'
'testuser@googlepay'
'testuser@phonepe'

# Invalid UPI ID
'invalid@upi'
```

### EMI Configuration

```python
# EMI Options
{
    'tenure': 3,
    'bank': 'HDFC Bank',
    'interest_rate': 12.0,
    'processing_fee': 99.0
}
```

## Usage

### Running All Payment Tests

```bash
cd qa-testing-framework
python -m web.run_payment_tests --test-type all
```

### Running Specific Payment Method Tests

```bash
# Test specific payment methods
python -m web.run_payment_tests --test-type methods --payment-methods credit_card paypal upi

# Test only validation scenarios
python -m web.run_payment_tests --test-type validation

# Test failure scenarios
python -m web.run_payment_tests --test-type failures

# Test refund processing
python -m web.run_payment_tests --test-type refunds

# Test security features
python -m web.run_payment_tests --test-type security
```

### Environment-Specific Testing

```bash
# Development environment (default)
python -m web.run_payment_tests --environment development

# Staging environment
python -m web.run_payment_tests --environment staging

# Production environment (limited tests)
python -m web.run_payment_tests --environment production
```

## Test Cases

### TC_PAY_001: Successful Credit Card Payment
**Objective**: Verify successful credit card payment processing
**Steps**:
1. Navigate to payment page
2. Select credit card payment method
3. Fill valid credit card details
4. Verify security indicators
5. Process payment
6. Verify payment success and transaction ID

**Expected Result**: Payment processes successfully with transaction confirmation

### TC_PAY_002: Successful Debit Card Payment
**Objective**: Verify successful debit card payment processing
**Steps**:
1. Navigate to payment page
2. Select debit card payment method
3. Fill valid debit card details
4. Process payment
5. Verify payment success

**Expected Result**: Debit card payment processes successfully

### TC_PAY_003: Successful PayPal Payment
**Objective**: Verify successful PayPal payment processing
**Steps**:
1. Navigate to payment page
2. Select PayPal payment method
3. Fill PayPal account details
4. Process payment through PayPal gateway
5. Handle gateway redirect
6. Verify payment success

**Expected Result**: PayPal payment processes successfully through gateway

### TC_PAY_006: Successful UPI Payment
**Objective**: Verify successful UPI payment processing
**Steps**:
1. Navigate to payment page
2. Select UPI payment method
3. Fill valid UPI ID
4. Verify UPI ID format validation
5. Process payment
6. Verify payment success

**Expected Result**: UPI payment processes successfully

### TC_PAY_007: Successful EMI Payment
**Objective**: Verify successful EMI payment processing
**Steps**:
1. Navigate to payment page (high-value order)
2. Select EMI payment method
3. Configure EMI tenure and bank
4. Verify EMI calculations
5. Process payment
6. Verify payment success

**Expected Result**: EMI payment processes with correct calculations

### TC_PAY_009: Declined Card Payment
**Objective**: Verify declined credit card payment handling
**Steps**:
1. Navigate to payment page
2. Select credit card payment
3. Fill declined card details
4. Process payment
5. Verify payment decline handling
6. Test retry functionality

**Expected Result**: Payment is declined with appropriate error message and retry option

### TC_PAY_011: Invalid Card Number Validation
**Objective**: Verify invalid card number validation
**Steps**:
1. Navigate to payment page
2. Select credit card payment
3. Enter invalid card number
4. Verify validation error appears

**Expected Result**: Invalid card number is rejected with validation error

### TC_PAY_015: Payment Security Indicators
**Objective**: Verify payment security indicators are present
**Steps**:
1. Navigate to payment page
2. Verify SSL indicator presence
3. Verify security badges
4. Verify encryption notice
5. Verify HTTPS connection

**Expected Result**: All security indicators are present and valid

### TC_PAY_016: Full Order Refund
**Objective**: Verify full order refund processing
**Steps**:
1. Navigate to refund page
2. Enter order number
3. Select refund reason
4. Process full refund
5. Verify refund success

**Expected Result**: Full refund processes successfully with refund reference

## Payment Gateway Integration

### Sandbox Configuration

The test suite supports multiple payment gateway sandbox environments:

```python
GATEWAY_CONFIGS = {
    'stripe': {
        'public_key': 'pk_test_123456789',
        'secret_key': 'sk_test_123456789',
        'test_mode': True
    },
    'razorpay': {
        'key_id': 'rzp_test_123456789',
        'key_secret': 'test_secret_123456789',
        'test_mode': True
    },
    'paypal': {
        'client_id': 'test_client_id_123456789',
        'base_url': 'https://api.sandbox.paypal.com',
        'test_mode': True
    }
}
```

### Gateway-Specific Testing

Each payment gateway has specific test scenarios:

1. **Stripe**: Card tokenization, 3D Secure, webhooks
2. **Razorpay**: UPI, EMI, international cards
3. **PayPal**: Express checkout, subscription billing
4. **PayU**: Multi-currency, local payment methods

## Security Testing

### Input Validation Tests

```python
SECURITY_TEST_DATA = {
    'sql_injection_attempts': [
        "'; DROP TABLE payments; --",
        "1' OR '1'='1"
    ],
    'xss_attempts': [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')"
    ]
}
```

### Rate Limiting Tests

```python
RATE_LIMITING_TEST = {
    'max_attempts': 10,
    'time_window': 60,  # seconds
    'description': 'Test payment rate limiting'
}
```

## Error Handling

### Payment Failure Categories

1. **Validation Errors**: Client-side validation failures
2. **Gateway Errors**: Payment gateway rejection
3. **Network Errors**: Timeout and connectivity issues
4. **System Errors**: Internal processing failures

### Retry Mechanisms

The test suite validates retry functionality for:
- Temporary network failures
- Gateway timeouts
- Transient processing errors

## Reporting

### Test Execution Report

```json
{
    "execution_summary": {
        "start_time": "2024-01-15T10:00:00",
        "end_time": "2024-01-15T10:30:00",
        "duration_seconds": 1800,
        "environment": "development",
        "test_results": {
            "total_tests": 19,
            "passed": 17,
            "failed": 2,
            "errors": 0,
            "success_rate": 89.5
        }
    },
    "defects_summary": {
        "total_defects": 2,
        "critical_defects": 0,
        "major_defects": 2
    }
}
```

### Defect Classification

- **Critical**: Payment processing failures, security vulnerabilities
- **Major**: Validation errors, gateway integration issues
- **Minor**: UI/UX issues, cosmetic problems

## Best Practices

### Test Data Management

1. Use sandbox/test payment methods only
2. Never use real payment credentials
3. Implement proper test data cleanup
4. Maintain separate test datasets per environment

### Security Considerations

1. Validate all payment forms use HTTPS
2. Verify PCI compliance indicators
3. Test input sanitization thoroughly
4. Validate CSRF protection

### Performance Testing

1. Test payment processing under load
2. Validate gateway response times
3. Monitor payment success rates
4. Test concurrent payment processing

## Troubleshooting

### Common Issues

1. **Gateway Connection Failures**
   - Verify sandbox credentials
   - Check network connectivity
   - Validate SSL certificates

2. **Test Data Issues**
   - Ensure using valid test card numbers
   - Verify test account configurations
   - Check sandbox environment status

3. **Validation Failures**
   - Review form field selectors
   - Verify validation message elements
   - Check JavaScript execution timing

### Debug Mode

Enable debug logging for detailed payment flow analysis:

```python
import logging
logging.getLogger('payment_tests').setLevel(logging.DEBUG)
```

## Integration with CI/CD

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Payment Tests') {
            steps {
                script {
                    sh 'python -m qa_testing_framework.web.run_payment_tests --test-type all'
                }
            }
        }
    }
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'payment_test_report.html',
                reportName: 'Payment Test Report'
            ])
        }
    }
}
```

### GitHub Actions

```yaml
name: Payment Tests
on: [push, pull_request]
jobs:
  payment-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Payment Tests
        run: python -m qa_testing_framework.web.run_payment_tests --test-type all
```

## Maintenance

### Regular Updates

1. Update sandbox credentials quarterly
2. Review and update test card numbers
3. Validate gateway API changes
4. Update security test scenarios

### Performance Monitoring

1. Track payment test execution times
2. Monitor gateway response times
3. Analyze payment success rates
4. Review error patterns and trends

This comprehensive payment testing framework ensures robust validation of all payment processing functionality while maintaining security and reliability standards.