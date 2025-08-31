# Test Inventory - Essential Tests Only

This document lists all essential test files kept after cleanup.

## Backend Tests


## Frontend Tests


## QA Framework Tests

- `__init__.py` - Essential test file
- `api/test_api_client.py` - API client connectivity
- `api/test_authentication.py` - API authentication endpoints
- `api/test_product_order_management.py` - API product and order management
- `config/development.yaml` - Essential test file
- `config/production.yaml` - Essential test file
- `config/staging.yaml` - Essential test file
- `core/__init__.py` - Essential test file
- `core/config.py` - Essential test file
- `core/models.py` - Essential test file
- `core/utils.py` - Essential test file
- `mobile/test_mobile_auth.py` - Mobile authentication
- `mobile/test_mobile_shopping.py` - Mobile shopping flow
- `requirements.txt` - Essential test file
- `web/test_authentication.py` - E2E authentication flow
- `web/test_payment_processing.py` - E2E payment processing
- `web/test_product_browsing.py` - E2E product browsing
- `web/test_shopping_cart_checkout.py` - E2E shopping and checkout

## Summary

- **Total Essential Tests**: 18
- **Removed Redundant Tests**: 16
- **Space Saved**: Approximately 800KB
