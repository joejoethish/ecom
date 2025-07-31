# Migration Troubleshooting Guide

## Common Migration Issues and Solutions

### 1. Connection Issues

#### Problem: Cannot connect to MySQL server
```
Error: (2003, "Can't connect to MySQL server on 'localhost' (10061)")
```

**Solution:**
```bash
# Check MySQL service status
sudo systemctl status mysql

# Start MySQL if not running
sudo systemctl start mysql

# Verify connection parameters
mysql -u root -p -h localhost -P 3306

# Check firewall settings
sudo ufw status
sudo ufw allow 3306/tcp
```

#### Problem: Access denied for user
```
Error: (1045, "Access denied for user 'ecommerce_user'@'localhost' (using password: YES)")
```

**Solution:**
```sql
-- Create user with proper privileges
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;

-- Verify user exists
SELECT User, Host FROM mysql.user WHERE User = 'ecommerce_user';
```

### 2. Schema Migration Issues

#### Problem: Table already exists error
```
Error: (1050, "Table 'auth_user' already exists")
```

**Solution:**
```bash
# Drop existing tables if safe to do so
python manage.py dbshell --database=mysql
DROP DATABASE ecommerce_db;
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Re-run migrations
python manage.py migrate --database=mysql
```

#### Problem: Column type mismatch
```
Error: Data truncated for column 'email' at row 1
```

**Solution:**
```sql
-- Increase column size
ALTER TABLE auth_user MODIFY COLUMN email VARCHAR(254);

-- Check column definitions
DESCRIBE auth_user;
```

### 3. Data Migration Issues

#### Problem: Foreign key constraint fails
```
Error: (1452, 'Cannot add or update a child row: a foreign key constraint fails')
```

**Solution:**
```python
# Temporarily disable foreign key checks
from django.db import connection
cursor = connection.cursor()
cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

# Perform migration
# ... migration code ...

# Re-enable foreign key checks
cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
```

#### Problem: Duplicate entry error
```
Error: (1062, "Duplicate entry '1' for key 'PRIMARY'")
```

**Solution:**
```sql
-- Check for duplicates
SELECT id, COUNT(*) FROM auth_user GROUP BY id HAVING COUNT(*) > 1;

-- Remove duplicates (be careful!)
DELETE t1 FROM auth_user t1
INNER JOIN auth_user t2 
WHERE t1.id = t2.id AND t1.date_joined < t2.date_joined;
```

### 4. Character Encoding Issues

#### Problem: Incorrect string value
```
Error: (1366, "Incorrect string value: '\\xF0\\x9F\\x98\\x80' for column 'description'")
```

**Solution:**
```sql
-- Convert table to utf8mb4
ALTER TABLE products_product CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Update Django settings
DATABASES = {
    'default': {
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

### 5. Performance Issues

#### Problem: Migration taking too long
```
Migration has been running for over 2 hours...
```

**Solution:**
```python
# Use batch processing
def migrate_in_batches(model, batch_size=1000):
    total = model.objects.count()
    for i in range(0, total, batch_size):
        batch = model.objects.all()[i:i+batch_size]
        # Process batch
        print(f"Processed {i+len(batch)}/{total} records")
```

#### Problem: MySQL server has gone away
```
Error: (2006, 'MySQL server has gone away')
```

**Solution:**
```sql
-- Increase timeout values
SET GLOBAL wait_timeout = 28800;
SET GLOBAL interactive_timeout = 28800;
SET GLOBAL max_allowed_packet = 1073741824;
```

### 6. Memory Issues

#### Problem: Out of memory during migration
```
MemoryError: Unable to allocate array
```

**Solution:**
```python
# Use iterator instead of loading all data
for obj in Model.objects.iterator(chunk_size=100):
    # Process individual object
    migrate_object(obj)

# Clear Django query cache periodically
from django.db import reset_queries
reset_queries()
```

### 7. SSL/TLS Issues

#### Problem: SSL connection error
```
Error: SSL connection error: SSL_CTX_set_tmp_dh failed
```

**Solution:**
```bash
# Generate new SSL certificates
sudo mysql_ssl_rsa_setup --uid=mysql

# Update MySQL configuration
[mysqld]
ssl-ca=/var/lib/mysql/ca.pem
ssl-cert=/var/lib/mysql/server-cert.pem
ssl-key=/var/lib/mysql/server-key.pem

# Restart MySQL
sudo systemctl restart mysql
```

## Diagnostic Commands

### Check Migration Status
```bash
# View migration history
python manage.py showmigrations

# Check current database
python manage.py dbshell
SELECT DATABASE();

# Verify table structure
SHOW CREATE TABLE auth_user;
```

### Monitor Migration Progress
```bash
# Watch migration logs
tail -f logs/migration.log

# Monitor MySQL processes
mysql -u root -p -e "SHOW PROCESSLIST;"

# Check table sizes
mysql -u root -p -e "
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'ecommerce_db'
ORDER BY (data_length + index_length) DESC;
"
```

### Performance Diagnostics
```sql
-- Check slow queries
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- Monitor connection usage
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- Check buffer pool usage
SHOW STATUS LIKE 'Innodb_buffer_pool%';
```

## Recovery Procedures

### Partial Migration Failure
```bash
# 1. Stop migration process
pkill -f "migrate_to_mysql"

# 2. Assess current state
python manage.py migration_status

# 3. Clean up partial data
python manage.py cleanup_partial_migration

# 4. Restart from last checkpoint
python manage.py resume_migration --from-checkpoint=last
```

### Complete Migration Failure
```bash
# 1. Stop all services
sudo systemctl stop gunicorn celery

# 2. Restore from backup
mysql -u root -p ecommerce_db < backup_before_migration.sql

# 3. Switch back to SQLite temporarily
cp settings/sqlite_backup.py settings/production.py

# 4. Restart services
sudo systemctl start gunicorn celery

# 5. Investigate and fix issues
python manage.py analyze_migration_failure
```

## Prevention Strategies

### Pre-Migration Testing
```bash
# Test migration on copy of production data
cp db.sqlite3 db_test.sqlite3
python manage.py test_migration --database=test

# Validate schema compatibility
python manage.py validate_mysql_schema

# Performance baseline
python manage.py benchmark_current_performance
```

### Monitoring During Migration
```python
# Set up migration monitoring
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

# Monitor system resources
import psutil
def log_system_stats():
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    logging.info(f"CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%")
```

## Emergency Contacts

| Issue Type | Contact | Phone | Email |
|------------|---------|-------|-------|
| Database Issues | DBA Team | ext. 1234 | dba@company.com |
| Application Issues | Dev Team | ext. 5678 | dev@company.com |
| Infrastructure | Ops Team | ext. 9012 | ops@company.com |
| Critical Issues | On-call Engineer | +1-555-0123 | oncall@company.com |

## Escalation Procedures

1. **Level 1**: Self-service using this guide (0-30 minutes)
2. **Level 2**: Contact team lead or senior developer (30-60 minutes)
3. **Level 3**: Escalate to DBA team (1-2 hours)
4. **Level 4**: Emergency escalation to on-call engineer (2+ hours)

## Post-Issue Documentation

After resolving any migration issue:

1. Document the problem and solution in the team wiki
2. Update this troubleshooting guide if needed
3. Consider adding automated checks to prevent recurrence
4. Conduct post-mortem if the issue caused significant downtime