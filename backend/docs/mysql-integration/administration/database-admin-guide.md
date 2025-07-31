# Database Administration Guide

## Daily Administration Tasks

### 1. Health Checks

#### Morning Health Check Routine
```bash
#!/bin/bash
# Daily health check script

echo "=== MySQL Health Check - $(date) ==="

# Check MySQL service status
systemctl is-active mysql && echo "✓ MySQL service is running" || echo "✗ MySQL service is down"

# Check disk space
df -h /var/lib/mysql | tail -1 | awk '{print "Disk usage: " $5 " of " $2}'

# Check connection count
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';" | tail -1 | awk '{print "Active connections: " $2}'

# Check slow queries
mysql -u root -p -e "SHOW STATUS LIKE 'Slow_queries';" | tail -1 | awk '{print "Slow queries: " $2}'

# Check replication status
mysql -u root -p -e "SHOW SLAVE STATUS\G" | grep -E "(Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master)"

echo "=== Health Check Complete ==="
```

#### Performance Monitoring
```sql
-- Check current performance metrics
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status 
WHERE VARIABLE_NAME IN (
    'Threads_connected',
    'Threads_running',
    'Queries',
    'Slow_queries',
    'Innodb_buffer_pool_hit_rate'
);

-- Monitor connection usage
SELECT 
    USER,
    HOST,
    DB,
    COMMAND,
    TIME,
    STATE,
    INFO
FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep'
ORDER BY TIME DESC;
```

### 2. User Management

#### Creating Database Users
```sql
-- Create application user
CREATE USER 'ecommerce_app'@'%' IDENTIFIED BY 'secure_password_123';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce_db.* TO 'ecommerce_app'@'%';

-- Create read-only user for reporting
CREATE USER 'ecommerce_readonly'@'%' IDENTIFIED BY 'readonly_password_456';
GRANT SELECT ON ecommerce_db.* TO 'ecommerce_readonly'@'%';

-- Create backup user
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'backup_password_789';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'localhost';

FLUSH PRIVILEGES;
```

#### User Audit and Cleanup
```sql
-- List all users and their privileges
SELECT 
    User,
    Host,
    authentication_string,
    password_expired,
    password_last_changed,
    account_locked
FROM mysql.user;

-- Check user privileges
SHOW GRANTS FOR 'ecommerce_app'@'%';

-- Remove inactive users (be careful!)
-- DROP USER 'old_user'@'localhost';
```

### 3. Database Maintenance

#### Index Maintenance
```sql
-- Analyze table statistics
ANALYZE TABLE auth_user, products_product, orders_order, reviews_review;

-- Optimize tables (rebuilds indexes)
OPTIMIZE TABLE auth_user, products_product, orders_order, reviews_review;

-- Check index usage
SELECT 
    OBJECT_SCHEMA,
    OBJECT_NAME,
    INDEX_NAME,
    COUNT_FETCH,
    COUNT_INSERT,
    COUNT_UPDATE,
    COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'ecommerce_db'
ORDER BY COUNT_FETCH DESC;
```

#### Table Maintenance
```sql
-- Check table sizes
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)',
    table_rows AS 'Rows'
FROM information_schema.tables 
WHERE table_schema = 'ecommerce_db'
ORDER BY (data_length + index_length) DESC;

-- Check for table corruption
CHECK TABLE auth_user, products_product, orders_order;

-- Repair tables if needed (use with caution)
-- REPAIR TABLE table_name;
```

### 4. Log Management

#### Error Log Monitoring
```bash
# Monitor MySQL error log
tail -f /var/log/mysql/error.log

# Check for recent errors
grep -i error /var/log/mysql/error.log | tail -20

# Monitor slow query log
tail -f /var/log/mysql/mysql-slow.log
```

#### Log Rotation Configuration
```bash
# Configure logrotate for MySQL logs
cat > /etc/logrotate.d/mysql << EOF
/var/log/mysql/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 mysql mysql
    postrotate
        /usr/bin/mysqladmin flush-logs
    endscript
}
EOF
```

### 5. Backup Verification

#### Daily Backup Check
```bash
#!/bin/bash
# Verify backup integrity

BACKUP_DIR="/var/backups/mysql"
LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.sql.gz | head -1)

echo "Checking backup: $LATEST_BACKUP"

# Check if backup file exists and is not empty
if [ -s "$LATEST_BACKUP" ]; then
    echo "✓ Backup file exists and is not empty"
    
    # Check if backup can be decompressed
    if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
        echo "✓ Backup file is valid gzip"
        
        # Get backup size
        SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
        echo "Backup size: $SIZE"
        
        # Check backup age
        AGE=$(find "$LATEST_BACKUP" -mtime +1)
        if [ -z "$AGE" ]; then
            echo "✓ Backup is recent (less than 24 hours old)"
        else
            echo "⚠ Backup is older than 24 hours"
        fi
    else
        echo "✗ Backup file is corrupted"
    fi
else
    echo "✗ Backup file is missing or empty"
fi
```

## Weekly Administration Tasks

### 1. Performance Review

#### Weekly Performance Report
```sql
-- Generate weekly performance summary
SELECT 
    'Connections' as Metric,
    MAX(VARIABLE_VALUE) as Max_Value,
    AVG(VARIABLE_VALUE) as Avg_Value
FROM performance_schema.global_status_history 
WHERE VARIABLE_NAME = 'Threads_connected'
AND TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY)

UNION ALL

SELECT 
    'Slow Queries' as Metric,
    MAX(VARIABLE_VALUE) as Max_Value,
    AVG(VARIABLE_VALUE) as Avg_Value
FROM performance_schema.global_status_history 
WHERE VARIABLE_NAME = 'Slow_queries'
AND TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY);
```

#### Query Performance Analysis
```sql
-- Top 10 slowest queries from last week
SELECT 
    DIGEST_TEXT,
    COUNT_STAR as Executions,
    AVG_TIMER_WAIT/1000000000 as Avg_Time_Seconds,
    MAX_TIMER_WAIT/1000000000 as Max_Time_Seconds,
    SUM_TIMER_WAIT/1000000000 as Total_Time_Seconds
FROM performance_schema.events_statements_summary_by_digest
WHERE LAST_SEEN >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;
```

### 2. Security Audit

#### User Access Review
```sql
-- Review user accounts and last login
SELECT 
    u.User,
    u.Host,
    u.password_expired,
    u.password_last_changed,
    u.account_locked,
    COALESCE(l.last_login, 'Never') as last_login
FROM mysql.user u
LEFT JOIN (
    SELECT 
        USER,
        HOST,
        MAX(EVENT_TIME) as last_login
    FROM performance_schema.events_statements_history_long
    WHERE EVENT_NAME = 'statement/sql/connect'
    GROUP BY USER, HOST
) l ON u.User = l.USER AND u.Host = l.HOST;
```

#### Privilege Audit
```bash
#!/bin/bash
# Generate privilege report for all users

mysql -u root -p -e "
SELECT DISTINCT User, Host FROM mysql.user;
" | while read user host; do
    if [ "$user" != "User" ]; then
        echo "=== Privileges for $user@$host ==="
        mysql -u root -p -e "SHOW GRANTS FOR '$user'@'$host';"
        echo ""
    fi
done
```

### 3. Capacity Planning

#### Storage Growth Analysis
```sql
-- Analyze table growth over time
SELECT 
    table_name,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
    table_rows,
    ROUND((data_length + index_length) / table_rows, 2) AS avg_row_size
FROM information_schema.tables
WHERE table_schema = 'ecommerce_db'
AND table_rows > 0
ORDER BY size_mb DESC;
```

## Monthly Administration Tasks

### 1. Configuration Review

#### MySQL Configuration Audit
```bash
#!/bin/bash
# Review MySQL configuration

echo "=== MySQL Configuration Review ==="
echo "MySQL Version:"
mysql -V

echo -e "\nKey Configuration Parameters:"
mysql -u root -p -e "
SHOW VARIABLES WHERE Variable_name IN (
    'innodb_buffer_pool_size',
    'max_connections',
    'query_cache_size',
    'innodb_log_file_size',
    'slow_query_log',
    'long_query_time'
);
"

echo -e "\nBuffer Pool Usage:"
mysql -u root -p -e "
SHOW STATUS WHERE Variable_name IN (
    'Innodb_buffer_pool_pages_total',
    'Innodb_buffer_pool_pages_free',
    'Innodb_buffer_pool_pages_data'
);
"
```

### 2. Index Optimization

#### Index Usage Analysis
```sql
-- Find unused indexes
SELECT 
    OBJECT_SCHEMA,
    OBJECT_NAME,
    INDEX_NAME
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'ecommerce_db'
AND INDEX_NAME IS NOT NULL
AND INDEX_NAME != 'PRIMARY'
AND COUNT_FETCH = 0
AND COUNT_INSERT = 0
AND COUNT_UPDATE = 0
AND COUNT_DELETE = 0;

-- Find duplicate indexes
SELECT 
    table_name,
    GROUP_CONCAT(index_name) as duplicate_indexes,
    GROUP_CONCAT(column_name) as columns
FROM information_schema.statistics
WHERE table_schema = 'ecommerce_db'
GROUP BY table_name, column_name
HAVING COUNT(*) > 1;
```

### 3. Disaster Recovery Testing

#### Monthly DR Test
```bash
#!/bin/bash
# Monthly disaster recovery test

echo "=== Disaster Recovery Test - $(date) ==="

# 1. Create test backup
echo "Creating test backup..."
mysqldump -u backup_user -p ecommerce_db > /tmp/dr_test_backup.sql

# 2. Create test database
echo "Creating test database..."
mysql -u root -p -e "CREATE DATABASE dr_test_db;"

# 3. Restore backup to test database
echo "Restoring backup..."
mysql -u root -p dr_test_db < /tmp/dr_test_backup.sql

# 4. Verify data integrity
echo "Verifying data integrity..."
ORIGINAL_COUNT=$(mysql -u root -p -e "SELECT COUNT(*) FROM ecommerce_db.auth_user;" | tail -1)
RESTORED_COUNT=$(mysql -u root -p -e "SELECT COUNT(*) FROM dr_test_db.auth_user;" | tail -1)

if [ "$ORIGINAL_COUNT" = "$RESTORED_COUNT" ]; then
    echo "✓ Data integrity verified"
else
    echo "✗ Data integrity check failed"
fi

# 5. Cleanup
echo "Cleaning up..."
mysql -u root -p -e "DROP DATABASE dr_test_db;"
rm /tmp/dr_test_backup.sql

echo "=== DR Test Complete ==="
```

## Emergency Procedures

### Database Server Down
```bash
# 1. Check system resources
df -h
free -m
ps aux | grep mysql

# 2. Check MySQL error log
tail -50 /var/log/mysql/error.log

# 3. Attempt to start MySQL
sudo systemctl start mysql
sudo systemctl status mysql

# 4. If start fails, check for corruption
sudo mysqld --user=mysql --skip-grant-tables --skip-networking &
mysql -u root
CHECK TABLE mysql.user;

# 5. If corruption found, restore from backup
sudo systemctl stop mysql
sudo cp /var/backups/mysql/latest_backup.sql /tmp/
sudo mysql < /tmp/latest_backup.sql
```

### High CPU Usage
```sql
-- Identify resource-intensive queries
SELECT 
    DIGEST_TEXT,
    COUNT_STAR,
    AVG_TIMER_WAIT/1000000000 as avg_seconds,
    SUM_TIMER_WAIT/1000000000 as total_seconds
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 5;

-- Kill long-running queries if necessary
-- KILL [CONNECTION_ID];
```

### Replication Failure
```sql
-- Check replication status
SHOW SLAVE STATUS\G

-- Common fixes for replication issues
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- Or reset replication if needed
RESET SLAVE;
CHANGE MASTER TO 
    MASTER_HOST='master_server',
    MASTER_USER='replication_user',
    MASTER_PASSWORD='replication_password',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=0;
START SLAVE;
```

## Monitoring and Alerting

### Key Metrics to Monitor
- Connection count (alert if > 80% of max_connections)
- Disk space (alert if > 85% full)
- Replication lag (alert if > 60 seconds)
- Slow query count (alert if increasing rapidly)
- Buffer pool hit rate (alert if < 95%)
- CPU usage (alert if > 80% for 5+ minutes)

### Alert Configuration
```bash
# Example Nagios check for MySQL
define service {
    use                     generic-service
    host_name               mysql-server
    service_description     MySQL Connection Count
    check_command           check_mysql_connections!80!90
    notifications_enabled   1
}
```

## Best Practices

1. **Always test changes in staging first**
2. **Take backups before making configuration changes**
3. **Monitor performance after any changes**
4. **Document all administrative actions**
5. **Keep MySQL and OS updated with security patches**
6. **Use strong passwords and rotate them regularly**
7. **Limit database access to necessary users only**
8. **Monitor logs regularly for suspicious activity**
9. **Test disaster recovery procedures monthly**
10. **Maintain up-to-date documentation**