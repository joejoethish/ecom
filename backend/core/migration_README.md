# Database Migration Utilities

This module provides comprehensive utilities for migrating data from SQLite to MySQL with advanced features including batch processing, progress tracking, data validation, and rollback capabilities.

## Features

- **Automated Schema Conversion**: Converts SQLite schemas to MySQL-optimized structures
- **Batch Data Migration**: Processes large datasets in configurable batches with progress tracking
- **Data Integrity Validation**: Comprehensive validation to ensure data consistency
- **Rollback Capabilities**: Create rollback points and restore data if migration fails
- **Progress Tracking**: Real-time progress monitoring with detailed statistics
- **Error Handling**: Robust error handling with retry mechanisms
- **Logging**: Detailed logging and migration reports

## Components

### DatabaseMigrationService

The main migration service that handles the complete migration process.

```python
from core.migration import DatabaseMigrationService

# Create migration service
service = DatabaseMigrationService(
    sqlite_path='path/to/database.sqlite3',
    mysql_config={
        'host': 'localhost',
        'port': 3306,
        'user': 'username',
        'password': 'password',
        'database': 'database_name'
    }
)

# Connect to databases
service.connect_databases()

# Migrate all tables
results = service.migrate_all_tables(batch_size=1000, create_rollback=True)

# Disconnect
service.disconnect_databases()
```

### MigrationValidator

Advanced validation utilities for ensuring migration integrity.

```python
from core.migration import MigrationValidator

validator = MigrationValidator(migration_service)

# Validate schema compatibility
schema_result = validator.validate_schema_compatibility('table_name')

# Validate data integrity
data_result = validator.validate_data_integrity('table_name', sample_size=100)
```

## Usage

### 1. Django Management Command

The easiest way to run migrations is using the Django management command:

```bash
# Migrate all tables
python manage.py migrate_to_mysql --action migrate

# Migrate specific table
python manage.py migrate_to_mysql --action migrate --table products_product

# Validate migration results
python manage.py migrate_to_mysql --action validate

# Check migration status
python manage.py migrate_to_mysql --action status

# Rollback a table
python manage.py migrate_to_mysql --action rollback --table products_product

# Dry run (validation only)
python manage.py migrate_to_mysql --action migrate --dry-run

# Custom batch size
python manage.py migrate_to_mysql --action migrate --batch-size 500

# Skip rollback points
python manage.py migrate_to_mysql --action migrate --no-rollback

# JSON output
python manage.py migrate_to_mysql --action status --output-format json
```

### 2. Batch Migration Script

For automated migrations with advanced configuration:

```bash
# Run batch migration with default config
python scripts/batch_migration.py

# Use custom configuration file
python scripts/batch_migration.py --config migration_config.json

# Generate report from existing progress
python scripts/batch_migration.py --report-only

# Start fresh migration (ignore previous progress)
python scripts/batch_migration.py --clean-start
```

### 3. Programmatic Usage

```python
from core.migration import create_migration_service, run_full_migration

# Simple migration
results = run_full_migration(batch_size=1000, create_rollback=True)

# Custom migration service
service = create_migration_service(
    sqlite_path='/path/to/db.sqlite3',
    mysql_config={'host': 'custom_host', ...}
)

# Connect and migrate specific table
service.connect_databases()
try:
    # Create rollback point
    service.create_rollback_point('my_table')
    
    # Get schema and create MySQL table
    columns = service.get_table_schema('my_table')
    service.create_mysql_table('my_table', columns)
    
    # Migrate data
    progress = service.migrate_table_data('my_table', batch_size=500)
    
    # Validate migration
    validation = service.validate_migration('my_table')
    
    if not validation.is_valid:
        # Rollback if validation fails
        service.rollback_table('my_table')
    
finally:
    service.disconnect_databases()
```

## Configuration

### Batch Migration Configuration

Create a `migration_config.json` file to customize the migration process:

```json
{
  "batch_size": 1000,
  "create_rollback": true,
  "max_retries": 3,
  "retry_delay": 5,
  "validation_sample_size": 100,
  "skip_tables": [
    "django_migrations",
    "django_session"
  ],
  "priority_tables": [
    "auth_user",
    "products_category",
    "products_product"
  ],
  "log_level": "INFO",
  "save_progress": true,
  "progress_file": "migration_progress.json"
}
```

### MySQL Configuration

The migration service uses Django's database configuration by default, but you can provide custom MySQL settings:

```python
mysql_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'migration_user',
    'password': 'secure_password',
    'database': 'target_database',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False,
    'raise_on_warnings': True,
    'connection_timeout': 60,
    'read_timeout': 300,
    'write_timeout': 300
}
```

## Data Type Mapping

The migration service automatically converts SQLite data types to MySQL equivalents:

| SQLite Type | MySQL Type |
|-------------|------------|
| INTEGER | INT |
| TEXT | TEXT |
| REAL | DOUBLE |
| BLOB | LONGBLOB |
| NUMERIC | DECIMAL(10,2) |
| VARCHAR(n) | VARCHAR(n) |
| BOOLEAN | TINYINT(1) |
| DATETIME | DATETIME |
| TIMESTAMP | TIMESTAMP |

## Progress Tracking

The migration service provides detailed progress tracking:

```python
# Access progress information
progress = service.migration_progress['table_name']
print(f"Progress: {progress.progress_percentage:.1f}%")
print(f"Records: {progress.migrated_records}/{progress.total_records}")
print(f"Status: {progress.status}")
print(f"Duration: {progress.duration_seconds:.2f}s")
```

## Validation

### Schema Validation

Validates that MySQL tables match the expected schema from SQLite:

```python
validator = MigrationValidator(migration_service)
result = validator.validate_schema_compatibility('table_name')

if not result['is_compatible']:
    for issue in result['issues']:
        print(f"Schema issue: {issue}")
```

### Data Validation

Validates data integrity by comparing records between databases:

```python
validation = service.validate_migration('table_name')

if not validation.is_valid:
    print(f"Source count: {validation.source_count}")
    print(f"Target count: {validation.target_count}")
    print(f"Missing records: {len(validation.missing_records)}")
    print(f"Extra records: {len(validation.extra_records)}")
```

## Rollback

Create rollback points before migration and restore if needed:

```python
# Create rollback point
service.create_rollback_point('table_name')

# Perform migration
# ... migration code ...

# Rollback if needed
if migration_failed:
    service.rollback_table('table_name')

# Clean up rollback points when done
service.cleanup_rollback_points('table_name')
```

## Error Handling

The migration service includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Data Type Conversion**: Fallback to compatible types
- **Foreign Key Constraints**: Dependency resolution
- **Large Data Sets**: Memory-efficient batch processing
- **Transaction Management**: Atomic operations with rollback

## Logging

Migration activities are logged with different levels:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('core.migration')

# Log levels used:
# DEBUG: Detailed operation information
# INFO: General progress and status
# WARNING: Non-critical issues
# ERROR: Migration failures
# CRITICAL: System-level failures
```

## Testing

Run the integration tests to verify functionality:

```bash
# Run integration tests
python scripts/test_migration.py

# Run unit tests
python manage.py test core.tests.test_migration
```

## Performance Considerations

### Batch Size

- **Small batches (100-500)**: Better for memory usage, slower overall
- **Medium batches (1000-5000)**: Good balance for most use cases
- **Large batches (10000+)**: Faster but requires more memory

### Indexing

The migration service creates optimized indexes for MySQL:

```sql
-- Example indexes created automatically
CREATE INDEX idx_products_category ON products_product(category_id, is_active);
CREATE INDEX idx_orders_user_date ON orders_order(user_id, created_at);
CREATE FULLTEXT INDEX idx_products_search ON products_product(name, description);
```

### Connection Pooling

Configure connection pooling for better performance:

```python
mysql_config = {
    # ... other config ...
    'pool_name': 'migration_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'pool_pre_ping': True
}
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   ```python
   mysql_config['connection_timeout'] = 120
   mysql_config['read_timeout'] = 600
   ```

2. **Memory Issues with Large Tables**
   ```python
   # Reduce batch size
   service.migrate_table_data('large_table', batch_size=100)
   ```

3. **Character Encoding Issues**
   ```python
   mysql_config['charset'] = 'utf8mb4'
   mysql_config['use_unicode'] = True
   ```

4. **Foreign Key Constraint Errors**
   ```python
   # Migrate tables in dependency order
   priority_tables = ['parent_table', 'child_table']
   ```

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.getLogger('core.migration').setLevel(logging.DEBUG)
```

## Security Considerations

- Store database credentials securely (environment variables)
- Use dedicated migration user with minimal privileges
- Enable SSL/TLS for database connections
- Validate data integrity after migration
- Create secure backups before migration

## Best Practices

1. **Pre-Migration**
   - Test migration on a copy of production data
   - Verify MySQL server configuration and performance
   - Plan for downtime and rollback procedures
   - Create full database backup

2. **During Migration**
   - Monitor system resources (CPU, memory, disk)
   - Watch for error logs and warnings
   - Validate critical tables immediately after migration
   - Keep rollback points for important tables

3. **Post-Migration**
   - Run comprehensive validation tests
   - Update application configuration
   - Monitor application performance
   - Clean up rollback points after verification

## Support

For issues or questions:

1. Check the migration logs for detailed error information
2. Run validation tests to identify specific problems
3. Use the test migration script to verify functionality
4. Review the troubleshooting section above