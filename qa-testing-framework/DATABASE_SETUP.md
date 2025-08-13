# Database Setup Guide

This guide explains how to set up MySQL database for the QA Testing Framework.

## Prerequisites

1. **MySQL Server**: Install MySQL Server 8.0 or later
2. **Python Dependencies**: Install required Python packages

```bash
pip install mysql-connector-python PyMySQL
```

## Quick Setup

### Option 1: Using Docker (Recommended)

1. **Start MySQL with Docker:**
```bash
docker run --name qa-mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=qa_test_development \
  -e MYSQL_USER=qa_user \
  -e MYSQL_PASSWORD=qa_password \
  -p 3307:3306 \
  -d mysql:8.0
```

2. **Setup test schema:**
```bash
cd qa-testing-framework
python scripts/setup_database.py --setup-schema
```

### Option 2: Using Existing MySQL Installation

1. **Create user and database (requires root access):**
```bash
cd qa-testing-framework
python scripts/setup_database.py --create-user --root-password YOUR_ROOT_PASSWORD
```

2. **Setup test schema:**
```bash
python scripts/setup_database.py --setup-schema
```

## Configuration

The framework uses these default connection settings:

- **Host**: localhost
- **Port**: 3307 (to avoid conflicts with default MySQL port 3306)
- **Database**: qa_test_development
- **User**: qa_user
- **Password**: qa_password

### Environment-Specific Databases

- **Development**: `qa_test_development`
- **Staging**: `qa_test_staging`
- **Production**: `qa_test_production`

## Manual Setup

If you prefer to set up manually:

### 1. Connect to MySQL as root:
```sql
mysql -u root -p -h localhost -P 3307
```

### 2. Create database and user:
```sql
-- Create database
CREATE DATABASE qa_test_development CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'qa_user'@'%' IDENTIFIED BY 'qa_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON qa_test_development.* TO 'qa_user'@'%';
FLUSH PRIVILEGES;
```

### 3. Setup test schema:
```bash
cd qa-testing-framework
python scripts/setup_database.py --setup-schema
```

## Verification

Run the database tests to verify everything is working:

```bash
cd qa-testing-framework
python -m pytest tests/test_database.py -v
```

## Configuration Files

Database settings are configured in:
- `config/development.yaml`
- `config/staging.yaml`
- `config/production.yaml`

Example configuration:
```yaml
database:
  host: localhost
  port: 3307
  name: qa_test_development
  user: qa_user
  password: qa_password
  charset: utf8mb4
```

## Troubleshooting

### Connection Issues

1. **Port conflicts**: If port 3307 is in use, change it in the configuration files
2. **Authentication**: Ensure the MySQL user has correct permissions
3. **Firewall**: Make sure the MySQL port is accessible

### Common Errors

**Error: "Access denied for user 'qa_user'"**
- Solution: Recreate the user with proper permissions

**Error: "Can't connect to MySQL server"**
- Solution: Check if MySQL is running and port is correct

**Error: "Unknown database"**
- Solution: Create the database first using the setup script

### Reset Database

To completely reset the test database:

```bash
# Drop and recreate database
python scripts/setup_database.py --create-user --root-password YOUR_ROOT_PASSWORD

# Setup fresh schema
python scripts/setup_database.py --setup-schema
```

## Database Schema

The test schema includes these tables:

- `test_users` - Test user accounts
- `test_user_addresses` - User addresses
- `test_user_payment_methods` - Payment methods
- `test_products` - Product catalog
- `test_product_variants` - Product variants
- `test_cases` - Test case definitions
- `test_steps` - Test step details
- `test_executions` - Test execution records
- `test_defects` - Defect tracking

All tables use UTF8MB4 charset for full Unicode support.