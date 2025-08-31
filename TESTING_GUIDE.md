# E-Commerce Platform - Essential Testing Guide

## 🎯 Quick Start - Essential Tests Only

This guide provides the **minimum essential tests** you need to run to verify your entire e-commerce platform is working correctly.

## 📋 Test Categories & Priority

### 🔴 **CRITICAL TESTS** (Must Pass - Run These First)
These tests verify core functionality that would break the entire platform:

```bash
# 1. Backend Core Functionality
cd backend
python manage.py test tests.integration.test_system_integration --verbosity=2

# 2. Frontend Core Components  
cd frontend
npm test -- --testPathPattern="components/(Dashboard|AdminLogin)" --watchAll=false

# 3. End-to-End User Journeys
cd qa-testing-framework
python -m pytest web/test_authentication.py web/test_shopping_cart_checkout.py -v
```

### 🟡 **IMPORTANT TESTS** (Should Pass - Run After Critical)
These tests verify important features and integrations:

```bash
# 4. API Integration Tests
cd backend
python manage.py test tests.integration.test_api_integration --verbosity=2

# 5. Payment & Order Processing
cd qa-testing-framework  
python -m pytest web/test_payment_processing.py api/test_product_order_management.py -v

# 6. Authentication & Security
cd backend
python manage.py test tests.security.test_security --verbosity=2
```

### 🟢 **OPTIONAL TESTS** (Nice to Have - Run When Time Permits)
These tests verify advanced features and performance:

```bash
# 7. Performance & Load Testing
cd backend
python manage.py test tests.performance.test_load_testing --verbosity=2

# 8. Debugging System (if enabled)
cd backend
python manage.py test tests.e2e.test_workflow_debugging_e2e --verbosity=2

# 9. Mobile Testing (if mobile app exists)
cd qa-testing-framework
python -m pytest mobile/test_mobile_auth.py -v
```

## 🚀 **ONE-COMMAND FULL TEST** (Recommended)

Run this single command to execute all essential tests:

```bash
# Linux/Mac
./run_essential_tests.sh --full

# Windows
run_essential_tests.bat --full

# Quick health check (2 minutes)
python check_test_status.py
```

## 📝 **Individual Test Commands with Usage**

### Backend Tests

```bash
cd backend

# Test all core models and database operations
python manage.py test tests.unit.test_models --verbosity=2
# Usage: Verifies all Django models, relationships, and database constraints

# Test all API endpoints and views  
python manage.py test tests.unit.test_views --verbosity=2
# Usage: Verifies all REST API endpoints return correct responses

# Test complete system integration
python manage.py test tests.integration.test_system_integration --verbosity=2
# Usage: Verifies all backend components work together correctly

# Test user authentication and permissions
python manage.py test tests.integration.test_user_journey --verbosity=2  
# Usage: Verifies user registration, login, logout, and permissions

# Test payment processing integration
python manage.py test tests.integration.test_payment_integrations --verbosity=2
# Usage: Verifies payment gateways and transaction processing

# Test security vulnerabilities
python manage.py test tests.security.test_security --verbosity=2
# Usage: Checks for common security issues and vulnerabilities

# Test database migrations
python manage.py test tests.test_migration_comprehensive --verbosity=2
# Usage: Verifies database migrations work correctly
```

### Frontend Tests

```bash
cd frontend

# Test core dashboard functionality
npm test -- --testPathPattern="Dashboard.test.tsx" --watchAll=false
# Usage: Verifies main dashboard loads and displays data correctly

# Test authentication components
npm test -- --testPathPattern="AdminLogin.test.tsx" --watchAll=false  
# Usage: Verifies login/logout functionality works in UI

# Test API service integration
npm test -- --testPathPattern="services/apiClient.test.ts" --watchAll=false
# Usage: Verifies frontend can communicate with backend APIs

# Test correlation ID functionality (debugging)
npm test -- --testPathPattern="hooks/useCorrelationId.test.ts" --watchAll=false
# Usage: Verifies request tracking works for debugging

# Run all frontend tests
npm test -- --watchAll=false --coverage
# Usage: Runs complete frontend test suite with coverage report
```

### QA Framework Tests (End-to-End)

```bash
cd qa-testing-framework

# Test complete user authentication flow
python -m pytest web/test_authentication.py -v
# Usage: Verifies users can register, login, reset passwords end-to-end

# Test complete shopping experience  
python -m pytest web/test_shopping_cart_checkout.py -v
# Usage: Verifies users can browse products, add to cart, and checkout

# Test payment processing end-to-end
python -m pytest web/test_payment_processing.py -v  
# Usage: Verifies complete payment flow with different payment methods

# Test product browsing and search
python -m pytest web/test_product_browsing.py -v
# Usage: Verifies product catalog, search, and filtering works

# Test API endpoints directly
python -m pytest api/test_authentication.py api/test_product_order_management.py -v
# Usage: Verifies backend APIs work correctly without UI

# Test mobile app functionality (if applicable)
python -m pytest mobile/test_mobile_auth.py mobile/test_mobile_shopping.py -v
# Usage: Verifies mobile app core functionality works

# Run complete QA test suite
python -m pytest tests/ -v --tb=short
# Usage: Runs all QA framework tests (web, mobile, API, database)
```

## ⚡ **Quick Health Check** (2 minutes)

Run this minimal set to quickly verify the platform is working:

```bash
# 1. Backend health check
cd backend && python manage.py test tests.integration.test_system_integration.SystemIntegrationTestCase.test_basic_system_health --verbosity=2

# 2. Frontend build check  
cd frontend && npm run build

# 3. Database connectivity
cd backend && python manage.py check --database default

# 4. Basic API test
cd qa-testing-framework && python -m pytest api/test_api_client.py::TestAPIClient::test_api_connectivity -v
```

## 🔧 **Test Environment Setup**

Before running tests, ensure your environment is properly configured:

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend setup  
cd frontend
npm install

# QA Framework setup
cd qa-testing-framework  
pip install -r requirements.txt
```

## 📊 **Test Results Interpretation**

### ✅ **All Tests Pass**
- Platform is fully functional
- Safe to deploy to production
- All features working as expected

### ⚠️ **Some Tests Fail**
- Check failed test details
- Critical tests failing = DO NOT DEPLOY
- Optional tests failing = Deploy with caution

### ❌ **Many Tests Fail**  
- Major issues with platform
- Review recent changes
- Fix issues before deployment

## 🚨 **Emergency Test Commands**

If the platform is down or having issues:

```bash
# 1. Check if backend is responding
cd backend && python manage.py runserver --settings=ecommerce_project.settings.testing &
curl http://localhost:8000/api/health/

# 2. Check database connectivity
cd backend && python manage.py dbshell

# 3. Check if frontend builds
cd frontend && npm run build

# 4. Run minimal smoke test
cd qa-testing-framework && python -m pytest web/simple_validation.py -v
```

## 📁 **Test File Organization**

### Essential Files (Keep These):
- `backend/tests/integration/test_system_integration.py` - Core system tests
- `backend/tests/unit/test_models.py` - Database model tests  
- `backend/tests/unit/test_views.py` - API endpoint tests
- `frontend/src/__tests__/components/Dashboard.test.tsx` - UI tests
- `qa-testing-framework/web/test_authentication.py` - E2E auth tests
- `qa-testing-framework/web/test_shopping_cart_checkout.py` - E2E shopping tests

### Optional Files (Can Remove If Needed):
- `backend/tests/test_versioning*.py` - API versioning tests
- `backend/tests/test_migration_edge_cases.py` - Edge case migration tests
- `frontend/src/__tests__/integration/` - Advanced integration tests
- `qa-testing-framework/mobile/` - Mobile tests (if no mobile app)

## 🎯 **Recommended Testing Strategy**

### Before You Start:
```bash
# Check if environment is ready for testing (30 seconds)
python check_test_status.py
```

### Daily Development:
```bash
# Quick check (2 minutes)
./run_essential_tests.sh --quick

# Full check (5 minutes)  
./run_essential_tests.sh --full
```

### Before Deployment:
```bash
# Complete test suite (15 minutes)
./run_essential_tests.sh --complete
```

### Clean Up Redundant Tests (One-time):
```bash
# Remove redundant test files to streamline testing
python cleanup_redundant_tests.py
```

---

## 💡 **Pro Tips**

1. **Start with Critical Tests**: Always run critical tests first
2. **Use Parallel Testing**: Run frontend and backend tests simultaneously  
3. **Focus on Failures**: Don't worry about optional test failures
4. **Test Locally First**: Run tests locally before CI/CD
5. **Keep Tests Updated**: Remove obsolete tests regularly

## 🆘 **Need Help?**

- Check test logs in `backend/logs/` and `qa-testing-framework/logs/`
- Review test configuration in `backend/ecommerce_project/settings/testing.py`
- Ensure all environment variables are set correctly
- Verify database and Redis are running for integration tests