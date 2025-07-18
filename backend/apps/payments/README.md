# Payment API Documentation

This document provides details about the Payment API endpoints and functionality for the e-commerce platform.

## Overview

The Payment API provides endpoints for processing payments, managing refunds, wallets, and gift cards. It supports multiple payment gateways (Stripe and Razorpay) and various payment methods including credit/debit cards, UPI, digital wallets, and more.

## API Endpoints

### Currencies

- `GET /api/v1/payments/currencies/` - List all available currencies
- `GET /api/v1/payments/currencies/{id}/` - Get currency details
- `POST /api/v1/payments/currencies/` - Create a new currency (admin only)
- `PUT /api/v1/payments/currencies/{id}/` - Update a currency (admin only)
- `DELETE /api/v1/payments/currencies/{id}/` - Delete a currency (admin only)

### Payment Methods

- `GET /api/v1/payments/methods/` - List all available payment methods
- `GET /api/v1/payments/methods/{id}/` - Get payment method details
- `POST /api/v1/payments/methods/` - Create a new payment method (admin only)
- `PUT /api/v1/payments/methods/{id}/` - Update a payment method (admin only)
- `DELETE /api/v1/payments/methods/{id}/` - Delete a payment method (admin only)

### Payments

- `GET /api/v1/payments/payments/` - List all payments for the current user
- `GET /api/v1/payments/payments/{id}/` - Get payment details
- `POST /api/v1/payments/payments/create_payment/` - Create a new payment
- `POST /api/v1/payments/payments/verify_payment/` - Verify a payment
- `GET /api/v1/payments/payments/{id}/status/` - Get payment status
- `POST /api/v1/payments/payments/generate_payment_link/` - Generate a payment link

### Refunds

- `GET /api/v1/payments/refunds/` - List all refunds for the current user
- `GET /api/v1/payments/refunds/{id}/` - Get refund details
- `POST /api/v1/payments/refunds/create_refund/` - Create a new refund

### Wallet

- `GET /api/v1/payments/wallets/my_wallet/` - Get the current user's wallet
- `GET /api/v1/payments/wallets/transactions/` - List wallet transactions
- `POST /api/v1/payments/wallets/add_funds/` - Add funds to wallet
- `POST /api/v1/payments/wallets/complete_add_funds/` - Complete adding funds to wallet

### Gift Cards

- `GET /api/v1/payments/gift-cards/` - List all gift cards for the current user
- `GET /api/v1/payments/gift-cards/{id}/` - Get gift card details
- `POST /api/v1/payments/gift-cards/check/` - Check gift card details
- `POST /api/v1/payments/gift-cards/purchase/` - Purchase a gift card
- `POST /api/v1/payments/gift-cards/complete_purchase/` - Complete gift card purchase
- `GET /api/v1/payments/gift-cards/{id}/transactions/` - List gift card transactions

## Request/Response Examples

### Create Payment

**Request:**
```json
POST /api/v1/payments/payments/create_payment/
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": "100.00",
  "currency_code": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174000",
  "metadata": {
    "customer_name": "John Doe",
    "customer_email": "john@example.com"
  }
}
```

**Response:**
```json
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "PENDING",
  "amount": 100.0,
  "currency": "USD",
  "payment_method": "CARD",
  "gateway_data": {
    "gateway_payment_id": "pi_12345",
    "client_secret": "cs_12345"
  }
}
```

### Verify Payment

**Request:**
```json
POST /api/v1/payments/payments/verify_payment/
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "gateway_payment_id": "pi_12345",
  "gateway_signature": "sig_12345",
  "metadata": {
    "razorpay_order_id": "order_12345"
  }
}
```

**Response:**
```json
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "COMPLETED",
  "verified": true
}
```

### Generate Payment Link

**Request:**
```json
POST /api/v1/payments/payments/generate_payment_link/
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": "100.00",
  "currency_code": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174000",
  "success_url": "https://example.com/success",
  "cancel_url": "https://example.com/cancel"
}
```

**Response:**
```json
{
  "payment_link": "https://checkout.stripe.com/pay/cs_test_12345"
}
```

### Create Refund

**Request:**
```json
POST /api/v1/payments/refunds/create_refund/
{
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": "50.00",
  "reason": "Customer request"
}
```

**Response:**
```json
{
  "refund_id": "123e4567-e89b-12d3-a456-426614174000",
  "payment_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": 50.0,
  "status": "COMPLETED"
}
```

### Add Funds to Wallet

**Request:**
```json
POST /api/v1/payments/wallets/add_funds/
{
  "amount": "100.00",
  "currency_code": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**
```json
{
  "wallet_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_balance": 500.0,
  "payment": {
    "payment_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "PENDING",
    "amount": 100.0,
    "currency": "USD",
    "payment_method": "CARD"
  }
}
```

### Purchase Gift Card

**Request:**
```json
POST /api/v1/payments/gift-cards/purchase/
{
  "amount": "100.00",
  "currency_code": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174000",
  "recipient_email": "recipient@example.com",
  "expiry_days": 180
}
```

**Response:**
```json
{
  "payment": {
    "payment_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "PENDING",
    "amount": 100.0,
    "currency": "USD",
    "payment_method": "CARD"
  },
  "expiry_date": "2025-01-14"
}
```

## Payment Flow

### Standard Payment Flow

1. Create a payment using the `create_payment` endpoint
2. For redirect-based gateways, redirect the user to the payment page
3. After payment completion, verify the payment using the `verify_payment` endpoint
4. Check the payment status using the `status` endpoint

### Payment Link Flow

1. Generate a payment link using the `generate_payment_link` endpoint
2. Redirect the user to the payment link
3. After payment completion, the user will be redirected to the success or cancel URL
4. Verify the payment using the webhook or by checking the payment status

## Supported Payment Methods

- Credit/Debit Cards (via Stripe and Razorpay)
- UPI (via Razorpay)
- Digital Wallets (platform wallet)
- Net Banking (via Razorpay)
- Cash on Delivery (internal processing)
- Gift Cards (internal processing)
- IMPS, RTGS, NEFT (via Razorpay)

## Supported Currencies

- USD (US Dollar)
- INR (Indian Rupee)
- AED (United Arab Emirates Dirham)
- EUR (Euro)
- SGD (Singapore Dollar)

## Error Handling

All API endpoints return appropriate HTTP status codes and error messages in case of failures. Common error responses include:

- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Business logic error
- `502 Bad Gateway` - Payment gateway error

Example error response:
```json
{
  "error": {
    "message": "Insufficient funds in wallet",
    "code": "insufficient_funds",
    "status_code": 400
  },
  "success": false
}
```

## Webhook Integration

For asynchronous payment status updates, configure webhooks in your payment gateway dashboard to point to:

- Stripe: `/api/v1/webhooks/stripe/`
- Razorpay: `/api/v1/webhooks/razorpay/`

These endpoints will be implemented in a separate webhook handling module.

## Security Considerations

- All API endpoints require authentication
- Payment method creation and management is restricted to admin users
- Users can only access their own payments, refunds, wallet, and gift cards
- Payment verification uses cryptographic signatures to prevent tampering
- Sensitive payment data is never stored on the server