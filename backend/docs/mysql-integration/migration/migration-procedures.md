# MySQL Migration Procedures Guide

## Overview

This guide provides detailed procedures for migrating from SQLite to MySQL, ensuring data integrity and minimal downtime.

## Pre-Migration Checklist

### 1. Environment Preparation
- [ ] MySQL server installed and configured
- [ ] SSL certificates generated and installed
- [ ] Database users created with appropriate permissions
- [ ] Backup of existing SQLite database created
- [ ] Migration scripts tested in staging environment

### 2. System Requirements Verification
- [ ] Sufficient disk space for migration (3x current database size)
- [ ] Network connectivity between source and target databases
- [ ] Required Python packages installed (mysql-connector-python, PyMySQL)
- [ ] Django MySQL backend dependencies installed

## Migration Process

### Phase 1: Schema Migration

```bash
# 1. Export SQLite schema
python manage.py dumpdata --format=json --indent=2 > sqlite_backup.json

# 2. Create MySQL database
mysql -u root -p -e "CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Run Django migrations for MySQL
python manage.py migrate --database=mysql

# 4. Verify schema creation
python manage.py dbshell --database=mysql
SHOW TABLES;
DESCRIBE auth_user;
```

### Phase 2: Data Migration

```python
# Run the migration script
python manage.py migrate_to_mysql --batch-size=1000 --verify-data

# Monitor migration progress
tail -f logs/migration.log
```

### Phase 3: Data Validation

```bash
# Compare record counts
python manage.py validate_migration --compare-counts

# Verify data integrity
python manage.py validate_migration --check-integrity

# Test application functionality
python manage.py test --settings=settings.mysql_test
```

### Phase 4: Cutover Process

```bash
# 1. Stop application services
sudo systemctl stop gunicorn
sudo systemctl stop celery

# 2. Final data sync
python manage.py sync_final_changes

# 3. Update Django settings
cp settings/mysql_production.py settings/production.py

# 4. Restart services
sudo systemctl start gunicorn
sudo systemctl start celery

# 5. Verify application functionality
curl -f http://localhost:8000/api/health/
```

## Post-Migration Tasks

### 1. Performance Optimization
```sql
-- Analyze tables for optimization
ANALYZE TABLE auth_user, products_product, orders_order;

-- Update table statistics
OPTIMIZE TABLE auth_user, products_product, orders_order;
```

### 2. Index Creation
```bash
# Create additional indexes
python manage.py create_mysql_indexes

# Verify index usage
python manage.py analyze_query_performance
```

### 3. Monitoring Setup
```bash
# Enable performance monitoring
python manage.py setup_performance_monitoring

# Configure alerts
python manage.py configure_database_alerts
```

## Rollback Procedures

### Emergency Rollback
```bash
# 1. Stop services
sudo systemctl stop gunicorn celery

# 2. Restore SQLite settings
cp settings/sqlite_backup.py settings/production.py

# 3. Restore SQLite database
cp db_backup.sqlite3 db.sqlite3

# 4. Restart services
sudo systemctl start gunicorn celery
```

### Planned Rollback
```bash
# 1. Create MySQL backup before rollback
mysqldump -u root -p ecommerce_db > rollback_backup.sql

# 2. Follow emergency rollback procedures

# 3. Document rollback reasons
echo "Rollback reason: [REASON]" >> logs/rollback.log
```

## Migration Validation

### Data Integrity Checks
```python
# Verify record counts match
python -c "
from django.db import connections
sqlite_cursor = connections['sqlite'].cursor()
mysql_cursor = connections['mysql'].cursor()

tables = ['auth_user', 'products_product', 'orders_order']
for table in tables:
    sqlite_cursor.execute(f'SELECT COUNT(*) FROM {table}')
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    mysql_cursor.execute(f'SELECT COUNT(*) FROM {table}')
    mysql_count = mysql_cursor.fetchone()[0]
    
    print(f'{table}: SQLite={sqlite_count}, MySQL={mysql_count}')
"
```

### Performance Validation
```bash
# Run performance benchmarks
python manage.py benchmark_database_performance

# Compare query execution times
python manage.py compare_query_performance --before=sqlite --after=mysql
```

## Common Migration Issues

### Character Encoding Issues
```sql
-- Fix character encoding
ALTER TABLE products_product CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Foreign Key Constraint Violations
```python
# Disable foreign key checks temporarily
cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
# Perform migration
cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
```

### Large Table Migration Timeouts
```python
# Use chunked migration for large tables
python manage.py migrate_large_table --table=orders_order --chunk-size=5000
```

## Migration Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-migration | 2-4 hours | Environment setup and validation |
| Schema migration | 30 minutes | Create MySQL schema |
| Data migration | 2-8 hours | Transfer data (depends on size) |
| Validation | 1-2 hours | Verify data integrity |
| Cutover | 15 minutes | Switch to MySQL |
| Post-migration | 1 hour | Optimization and monitoring |

## Success Criteria

- [ ] All data migrated without loss
- [ ] Application functionality verified
- [ ] Performance meets or exceeds baseline
- [ ] Monitoring and alerting operational
- [ ] Backup procedures validated
- [ ] Team trained on new procedures