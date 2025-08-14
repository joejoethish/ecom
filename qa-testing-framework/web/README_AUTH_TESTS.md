# Authentication and User Management Tests

This module provides comprehensive testing for authentication and user management functionality in the QA Testing Framework. It covers all aspects of user authentication, session management, and security testing.

## Overview

The authentication test suite validates:
- User registration and account creation
- Login and logout functionality
- Password reset and recovery
- Profile management and updates
- Role-based access control
- Session management and security
- Security vulnerabilities (SQL injection, XSS, session hijacking)

## Test Structure

### Core Components

1. **Page Objects** (`auth_pages.py`)
   - `LoginPage`: Login form interactions
   - `RegistrationPage`: User registration functionality
   - `ForgotPasswordPage`: Password reset requests
   - `ResetPasswordPage`: Password reset completion
   - `ProfilePage`: User profile management
   - `DashboardPage`: User dashboard interactions

2. **Test Suites**
   - `AuthenticationTestSuite` (`test_authentication.py`): Core authentication tests
   - `SessionManagementTestSuite` (`test_session_management.py`): Session security tests

3. **Test Data Generation** (`auth_test_data.py`)
   - User data generation for different roles
   - Invalid data scenarios for negative testing
   - Security test payloads

4. **Test Runners**
   - `run_auth_tests.py`: Basic authentication test runner
   - `run_complete_auth_tests.py`: Comprehensive test runner with reporting

## Test Categories

### 1. User Registration Tests
- Valid registration with all required fields
- Duplicate email validation
- Password strength validation
- Password confirmation matching
- Required field validation
- Input sanitization (XSS protection)

### 2. User Login Tests
- Valid credentials login
- Invalid credentials handling
- Empty credentials validation
- Remember me functionality
- Account lockout protection
- SQL injection protection

### 3. User Logout Tests
- Logout from dashboard
- Logout from profile page
- Session invalidation verification
- Redirect behavior validation

### 4. Password Reset Tests
- Valid email password reset request
- Invalid/non-existent email handling
- Reset token validation
- New password setting
- Password change confirmation

### 5. Profile Management Tests
- Profile information updates
- Password change functionality
- Data validation and sanitization
- Profile data persistence

### 6. Role-Based Access Control Tests
- Guest user access restrictions
- Registered user permissions
- Premium user access levels
- Admin user capabilities
- Unauthorized access prevention

### 7. Session Management Tests
- Session creation on login
- Session persistence across pages
- Session timeout handling
- Session invalidation on logout
- Concurrent session management
- Session security attributes
- Session fixation protection
- Session hijacking protection
- Remember me functionality

### 8. Security Tests
- SQL injection protection in login forms
- XSS protection in registration forms
- Session cookie security attributes
- CSRF protection validation
- Input sanitization verification

## Running Tests

### Prerequisites
- Python 3.8+
- Selenium WebDriver
- Chrome/Firefox browser installed
- Web application running on configured URL

### Basic Usage

```bash
# Run all authentication tests
python qa-testing-framework/web/run_complete_auth_tests.py

# Run specific test suite
python qa-testing-framework/web/run_complete_auth_tests.py --suite authentication
python qa-testing-framework/web/run_complete_auth_tests.py --suite session

# Run in different environment
python qa-testing-framework/web/run_complete_auth_tests.py --environment staging

# Use different browser
python qa-testing-framework/web/run_complete_auth_tests.py --browser firefox
```

### Advanced Usage

```bash
# Run specific test method
python -m unittest qa_testing_framework.web.test_authentication.AuthenticationTestSuite.test_user_login_valid_credentials

# Run with verbose output
python qa-testing-framework/web/run_complete_auth_tests.py -v

# Generate detailed reports
python qa-testing-framework/web/run_complete_auth_tests.py --environment production
```

## Test Data

### User Roles Tested
- **Guest**: Unauthenticated users
- **Registered**: Basic authenticated users
- **Premium**: Users with premium features
- **Seller**: Vendor users with selling capabilities
- **Admin**: Administrative users
- **Super Admin**: Full system access users

### Test Scenarios
- **Positive Tests**: Valid data and expected workflows
- **Negative Tests**: Invalid data and error conditions
- **Edge Cases**: Boundary conditions and unusual inputs
- **Security Tests**: Malicious inputs and attack scenarios

## Configuration

### Environment Configuration
Tests can be configured for different environments:

```python
# Development environment (default)
environment = Environment.DEVELOPMENT
base_url = "http://localhost:3000"

# Staging environment
environment = Environment.STAGING
base_url = "https://staging.example.com"

# Production environment
environment = Environment.PRODUCTION
base_url = "https://production.example.com"
```

### Browser Configuration
Supported browsers:
- Chrome (default)
- Firefox
- Edge
- Safari (macOS only)

### Test Data Configuration
Test data is automatically generated with:
- Unique email addresses per environment
- Strong passwords meeting security requirements
- Valid phone numbers and addresses
- Realistic user profiles

## Reporting

### Report Types

1. **Console Output**: Real-time test execution status
2. **JSON Report**: Detailed machine-readable results
3. **HTML Report**: Human-readable visual report

### Report Contents
- Test execution summary
- Pass/fail statistics
- Defect details with severity classification
- Security analysis
- Performance metrics
- Recommendations for improvement

### Sample Report Structure
```json
{
  "environment": "development",
  "overall_summary": {
    "total_tests": 25,
    "total_passed": 23,
    "total_failed": 2,
    "overall_pass_rate": 92.0
  },
  "security_analysis": {
    "total_security_defects": 1,
    "critical_security_defects": 0,
    "major_security_defects": 1
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "category": "Security",
      "recommendation": "Implement stronger session security measures"
    }
  ]
}
```

## Defect Classification

### Severity Levels
- **Critical**: System crashes, security vulnerabilities, data loss
- **Major**: Feature not working, significant functionality issues
- **Minor**: UI issues, cosmetic problems, minor usability issues

### Common Defect Categories
- Authentication failures
- Session management issues
- Security vulnerabilities
- Validation errors
- UI/UX problems

## Best Practices

### Test Design
1. **Independent Tests**: Each test should be self-contained
2. **Clean State**: Tests should not depend on previous test state
3. **Realistic Data**: Use realistic test data that mimics production
4. **Error Handling**: Properly handle and report test failures

### Security Testing
1. **Input Validation**: Test all input fields for malicious content
2. **Session Security**: Verify proper session management
3. **Access Control**: Validate role-based permissions
4. **Data Protection**: Ensure sensitive data is properly handled

### Maintenance
1. **Regular Updates**: Keep tests updated with application changes
2. **Data Cleanup**: Clean up test data after execution
3. **Environment Sync**: Ensure tests work across all environments
4. **Documentation**: Keep test documentation current

## Troubleshooting

### Common Issues

1. **WebDriver Issues**
   ```bash
   # Update WebDriver
   pip install --upgrade selenium webdriver-manager
   ```

2. **Element Not Found**
   - Check if page selectors have changed
   - Verify page load timing
   - Update page object locators

3. **Test Data Issues**
   - Ensure test users don't already exist
   - Check email domain configuration
   - Verify database cleanup

4. **Environment Issues**
   - Confirm application is running
   - Check network connectivity
   - Verify environment configuration

### Debug Mode
Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration

### CI/CD Integration
Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Authentication Tests
  run: |
    python qa-testing-framework/web/run_complete_auth_tests.py --environment staging
```

### API Integration
Tests can be combined with API tests for comprehensive coverage:

```python
# Example: Verify user creation via API before UI tests
api_client.create_user(user_data)
ui_tests.test_user_login(user_data)
```

## Contributing

### Adding New Tests
1. Create test methods in appropriate test suite
2. Follow naming convention: `test_<functionality>_<scenario>`
3. Include proper assertions and error handling
4. Add defect logging for failures
5. Update documentation

### Extending Page Objects
1. Add new page object classes for new pages
2. Follow existing patterns and conventions
3. Include proper element locators
4. Add validation methods
5. Document new functionality

## Support

For issues or questions:
1. Check existing documentation
2. Review test logs and reports
3. Verify environment configuration
4. Contact QA team for assistance

## Version History

- **v1.0.0**: Initial authentication test suite
- **v1.1.0**: Added session management tests
- **v1.2.0**: Enhanced security testing
- **v1.3.0**: Comprehensive reporting system