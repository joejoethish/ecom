# Database Maintenance Procedures

## Overview

This guide outlines regular maintenance procedures to ensure optimal MySQL database performance, reliability, and security.

## Daily Maintenance Tasks

### 1. Automated Health Checks

#### System Health Monitor Script
```bash
#!/bin/bash
# /usr/local/bin/mysql_health_check.sh

LOG_FILE="/var/log/mysql/health_check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting MySQL health check" >> $LOG_FILE

# Check MySQL service status
if systemctl is-active --quiet mysql; then
    echo "[$DATE] ✓ MySQL service is running" >> $LOG_FILE
else
    echo "[$DATE] ✗ MySQL service is down - attempting restart" >> $LOG_FILE
    systemctl restart mysql
    sleep 10
    if systemctl is-active --quiet mysql; then
        echo "[$DATE] ✓ MySQL service restarted successfully" >> $LOG_FILE
    else
        echo "[$DATE] ✗ Failed to restart MySQL service - ALERT REQUIRED" >> $LOG_FILE
        # Send alert to administrators
        echo "MySQL service failed to restart on $(hostname)" | mail -s "CRITICAL: MySQL Down" admin@company.com
    fi
fi

# Check disk space
DISK_USAGE=$(df /var/lib/mysql | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "[$DATE] ⚠ High disk usage: ${DISK_USAGE}%" >> $LOG_FILE
    if [ $DISK_USAGE -gt 95 ]; then
        echo "[$DATE] ✗ Critical disk usage: ${DISK_USAGE}% - ALERT REQUIRED" >> $LOG_FILE
        echo "Critical disk usage ${DISK_USAGE}% on MySQL server $(hostname)" | mail -s "CRITICAL: Disk Space" admin@company.com
    fi
else
    echo "[$DATE] ✓ Disk usage normal: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check connection count
CONNECTIONS=$(mysql -u monitoring_user -p${MONITORING_PASSWORD} -e "SHOW STATUS LIKE 'Threads_connected';" | tail -1 | awk '{print $2}')
MAX_CONNECTIONS=$(mysql -u monitoring_user -p${MONITORING_PASSWORD} -e "SHOW VARIABLES LIKE 'max_connections';" | tail -1 | awk '{print $2}')
CONNECTION_PERCENT=$((CONNECTIONS * 100 / MAX_CONNECTIONS))

if [ $CONNECTION_PERCENT -gt 80 ]; then
    echo "[$DATE] ⚠ High connection usage: ${CONNECTION_PERCENT}% (${CONNECTIONS}/${MAX_CONNECTIONS})" >> $LOG_FILE
else
    echo "[$DATE] ✓ Connection usage normal: ${CONNECTION_PERCENT}% (${CONNECTIONS}/${MAX_CONNECTIONS})" >> $LOG_FILE
fi

echo "[$DATE] Health check completed" >> $LOG_FILE
```

#### Cron Job Configuration
```bash
# Add to crontab for automated execution
# Run health check every 15 minutes
*/15 * * * * /usr/local/bin/mysql_health_check.sh

# Run detailed performance check daily at 6 AM
0 6 * * * /usr/local/bin/mysql_performance_check.sh
```

### 2. Log Monitoring and Rotation

#### Error Log Analysis
```bash
#!/bin/bash
# /usr/local/bin/mysql_log_analysis.sh

ERROR_LOG="/var/log/mysql/error.log"
SLOW_LOG="/var/log/mysql/mysql-slow.log"
REPORT_FILE="/var/log/mysql/daily_report_$(date +%Y%m%d).txt"

echo "MySQL Daily Log Analysis - $(date)" > $REPORT_FILE
echo "================================================" >> $REPORT_FILE

# Check for errors in the last 24 hours
echo -e "\nERRORS IN LAST 24 HOURS:" >> $REPORT_FILE
grep "$(date --date='1 day ago' '+%Y-%m-%d')\|$(date '+%Y-%m-%d')" $ERROR_LOG | grep -i error >> $REPORT_FILE

# Check for warnings
echo -e "\nWARNINGS IN LAST 24 HOURS:" >> $REPORT_FILE
grep "$(date --date='1 day ago' '+%Y-%m-%d')\|$(date '+%Y-%m-%d')" $ERROR_LOG | grep -i warning >> $REPORT_FILE

# Analyze slow queries
echo -e "\nSLOW QUERY SUMMARY:" >> $REPORT_FILE
if [ -f "$SLOW_LOG" ]; then
    SLOW_COUNT=$(grep -c "Query_time" $SLOW_LOG)
    echo "Total slow queries today: $SLOW_COUNT" >> $REPORT_FILE
    
    # Top 5 slowest queries
    echo -e "\nTop 5 slowest queries:" >> $REPORT_FILE
    grep -A 1 "Query_time" $SLOW_LOG | head -10 >> $REPORT_FILE
fi

# Check binary log size
echo -e "\nBINARY LOG STATUS:" >> $REPORT_FILE
mysql -u monitoring_user -p${MONITORING_PASSWORD} -e "SHOW BINARY LOGS;" >> $REPORT_FILE

echo -e "\nReport generated: $(date)" >> $REPORT_FILE
```

## Weekly Maintenance Tasks

### 1. Index Optimization

#### Index Analysis and Optimization
```sql
-- Weekly index optimization script
-- Save as /usr/local/bin/weekly_index_optimization.sql

-- Analyze all tables to update statistics
ANALYZE TABLE 
    auth_user,
    products_product,
    products_category,
    orders_order,
    orders_orderitem,
    reviews_review,
    customers_customer,
    customers_address;

-- Check for unused indexes
SELECT 
    OBJECT_SCHEMA as 'Database',
    OBJECT_NAME as 'Table',
    INDEX_NAME as 'Index',
    COUNT_FETCH as 'Fetches',
    COUNT_INSERT as 'Inserts',
    COUNT_UPDATE as 'Updates',
    COUNT_DELETE as 'Deletes'
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'ecommerce_db'
AND INDEX_NAME IS NOT NULL
AND INDEX_NAME != 'PRIMARY'
AND COUNT_FETCH = 0
AND COUNT_INSERT = 0
AND COUNT_UPDATE = 0
AND COUNT_DELETE = 0
ORDER BY OBJECT_NAME, INDEX_NAME;

-- Check index cardinality
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    CARDINALITY,
    CASE 
        WHEN CARDINALITY = 0 THEN 'No unique values'
        WHEN CARDINALITY = 1 THEN 'All values same'
        WHEN CARDINALITY < 10 THEN 'Low cardinality'
        ELSE 'Good cardinality'
    END as 'Status'
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'ecommerce_db'
ORDER BY TABLE_NAME, INDEX_NAME;
```

#### Index Optimization Script
```bash
#!/bin/bash
# /usr/local/bin/weekly_index_optimization.sh

echo "Starting weekly index optimization - $(date)"

# Run index analysis
mysql -u admin_user -p${ADMIN_PASSWORD} ecommerce_db < /usr/local/bin/weekly_index_optimization.sql > /tmp/index_analysis.txt

# Optimize tables (rebuilds indexes and reclaims space)
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
OPTIMIZE TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.orders_order,
    ecommerce_db.reviews_review;
"

# Check fragmentation levels
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
SELECT 
    TABLE_NAME,
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)',
    ROUND(DATA_FREE / 1024 / 1024, 2) AS 'Free Space (MB)',
    ROUND((DATA_FREE / (DATA_LENGTH + INDEX_LENGTH)) * 100, 2) AS 'Fragmentation %'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ecommerce_db'
AND DATA_FREE > 0
ORDER BY \`Fragmentation %\` DESC;
" > /tmp/fragmentation_report.txt

echo "Index optimization completed - $(date)"

# Email report if fragmentation is high
if grep -q "Fragmentation %" /tmp/fragmentation_report.txt; then
    HIGH_FRAG=$(awk 'NR>1 && $4>20 {print}' /tmp/fragmentation_report.txt)
    if [ ! -z "$HIGH_FRAG" ]; then
        echo "Tables with high fragmentation found:" | cat - /tmp/fragmentation_report.txt | mail -s "Weekly Index Report - High Fragmentation Detected" admin@company.com
    fi
fi
```

### 2. Performance Analysis

#### Weekly Performance Report
```sql
-- Weekly performance analysis
-- Save as /usr/local/bin/weekly_performance_analysis.sql

-- Connection statistics
SELECT 
    'Max Connections Used' as Metric,
    MAX(VARIABLE_VALUE) as Value
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Max_used_connections'

UNION ALL

SELECT 
    'Current Connections' as Metric,
    VARIABLE_VALUE as Value
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Threads_connected'

UNION ALL

SELECT 
    'Total Queries This Week' as Metric,
    VARIABLE_VALUE as Value
FROM performance_schema.global_status
WHERE VARIABLE_NAME = 'Queries';

-- Top 10 most executed queries
SELECT 
    LEFT(DIGEST_TEXT, 100) as Query_Sample,
    COUNT_STAR as Executions,
    ROUND(AVG_TIMER_WAIT/1000000000, 3) as Avg_Time_Sec,
    ROUND(SUM_TIMER_WAIT/1000000000, 3) as Total_Time_Sec
FROM performance_schema.events_statements_summary_by_digest
WHERE LAST_SEEN >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY COUNT_STAR DESC
LIMIT 10;

-- Slowest queries
SELECT 
    LEFT(DIGEST_TEXT, 100) as Query_Sample,
    COUNT_STAR as Executions,
    ROUND(MAX_TIMER_WAIT/1000000000, 3) as Max_Time_Sec,
    ROUND(AVG_TIMER_WAIT/1000000000, 3) as Avg_Time_Sec
FROM performance_schema.events_statements_summary_by_digest
WHERE LAST_SEEN >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY MAX_TIMER_WAIT DESC
LIMIT 10;

-- Buffer pool statistics
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Innodb_buffer_pool_hit_rate',
    'Innodb_buffer_pool_pages_total',
    'Innodb_buffer_pool_pages_free',
    'Innodb_buffer_pool_pages_data',
    'Innodb_buffer_pool_pages_dirty'
);
```

### 3. Data Cleanup

#### Old Data Archival
```sql
-- Archive old data (run weekly)
-- Save as /usr/local/bin/weekly_data_cleanup.sql

-- Archive orders older than 2 years to archive table
INSERT INTO orders_order_archive 
SELECT * FROM orders_order 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 2 YEAR);

-- Archive old log entries (older than 90 days)
DELETE FROM admin_activity_logs 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Archive old session data (older than 30 days)
DELETE FROM django_session 
WHERE expire_date < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Clean up old password reset tokens (older than 24 hours)
DELETE FROM auth_password_reset_tokens 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);

-- Update table statistics after cleanup
ANALYZE TABLE orders_order, admin_activity_logs, django_session;
```

## Monthly Maintenance Tasks

### 1. Full Database Optimization

#### Monthly Optimization Script
```bash
#!/bin/bash
# /usr/local/bin/monthly_optimization.sh

echo "Starting monthly database optimization - $(date)"

# Create maintenance log
MAINTENANCE_LOG="/var/log/mysql/monthly_maintenance_$(date +%Y%m).log"
exec > >(tee -a $MAINTENANCE_LOG)
exec 2>&1

# 1. Check and repair all tables
echo "Checking table integrity..."
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
CHECK TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.products_category,
    ecommerce_db.orders_order,
    ecommerce_db.orders_orderitem,
    ecommerce_db.reviews_review,
    ecommerce_db.customers_customer;
"

# 2. Optimize all tables
echo "Optimizing all tables..."
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
OPTIMIZE TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.products_category,
    ecommerce_db.orders_order,
    ecommerce_db.orders_orderitem,
    ecommerce_db.reviews_review,
    ecommerce_db.customers_customer;
"

# 3. Update all table statistics
echo "Updating table statistics..."
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
ANALYZE TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.products_category,
    ecommerce_db.orders_order,
    ecommerce_db.orders_orderitem,
    ecommerce_db.reviews_review,
    ecommerce_db.customers_customer;
"

# 4. Flush query cache and reset statistics
echo "Flushing caches and resetting statistics..."
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
FLUSH QUERY CACHE;
FLUSH STATUS;
RESET QUERY CACHE;
"

# 5. Generate monthly report
echo "Generating monthly report..."
mysql -u admin_user -p${ADMIN_PASSWORD} -e "
SELECT 
    TABLE_NAME as 'Table',
    TABLE_ROWS as 'Rows',
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)',
    ROUND(DATA_FREE / 1024 / 1024, 2) AS 'Free Space (MB)',
    ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ecommerce_db'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;
"

echo "Monthly optimization completed - $(date)"

# Email completion report
echo "Monthly database optimization completed successfully on $(hostname)" | mail -s "Monthly DB Maintenance Complete" admin@company.com
```

### 2. Security Audit

#### Monthly Security Check
```bash
#!/bin/bash
# /usr/local/bin/monthly_security_audit.sh

SECURITY_LOG="/var/log/mysql/security_audit_$(date +%Y%m).log"
exec > >(tee -a $SECURITY_LOG)
exec 2>&1

echo "Starting monthly security audit - $(date)"

# 1. Check for users without passwords
echo "Checking for users without passwords..."
mysql -u root -p -e "
SELECT User, Host, authentication_string 
FROM mysql.user 
WHERE authentication_string = '' OR authentication_string IS NULL;
"

# 2. Check for users with excessive privileges
echo "Checking for users with excessive privileges..."
mysql -u root -p -e "
SELECT User, Host 
FROM mysql.user 
WHERE Super_priv = 'Y' OR Grant_priv = 'Y';
"

# 3. Check for expired passwords
echo "Checking for expired passwords..."
mysql -u root -p -e "
SELECT User, Host, password_expired, password_last_changed
FROM mysql.user 
WHERE password_expired = 'Y' 
OR password_last_changed < DATE_SUB(NOW(), INTERVAL 90 DAY);
"

# 4. Check SSL configuration
echo "Checking SSL configuration..."
mysql -u root -p -e "
SHOW VARIABLES LIKE '%ssl%';
"

# 5. Review recent login attempts
echo "Reviewing recent connection attempts..."
mysql -u root -p -e "
SELECT 
    USER,
    HOST,
    EVENT_TIME,
    CURRENT_SCHEMA
FROM performance_schema.events_statements_history_long
WHERE EVENT_NAME = 'statement/sql/connect'
AND EVENT_TIME >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY EVENT_TIME DESC
LIMIT 20;
"

echo "Security audit completed - $(date)"
```

### 3. Capacity Planning

#### Monthly Capacity Report
```sql
-- Monthly capacity planning analysis
-- Save as /usr/local/bin/monthly_capacity_analysis.sql

-- Database growth analysis
SELECT 
    TABLE_SCHEMA as 'Database',
    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)',
    COUNT(*) as 'Tables'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
GROUP BY TABLE_SCHEMA
ORDER BY SUM(DATA_LENGTH + INDEX_LENGTH) DESC;

-- Table growth analysis
SELECT 
    TABLE_NAME as 'Table',
    TABLE_ROWS as 'Rows',
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)',
    ROUND(DATA_LENGTH / TABLE_ROWS, 2) AS 'Avg Row Size (bytes)',
    CREATE_TIME,
    UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ecommerce_db'
AND TABLE_ROWS > 0
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;

-- Connection usage trends
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Max_used_connections',
    'Threads_connected',
    'Threads_created',
    'Connections',
    'Aborted_connects'
);

-- Query cache effectiveness
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Qcache_hits',
    'Qcache_inserts',
    'Qcache_not_cached',
    'Qcache_queries_in_cache'
);
```

## Automated Maintenance Scripts

### Master Maintenance Script
```bash
#!/bin/bash
# /usr/local/bin/mysql_maintenance_master.sh

# Configuration
SCRIPT_DIR="/usr/local/bin"
LOG_DIR="/var/log/mysql"
EMAIL="admin@company.com"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_DIR/maintenance_master.log
}

# Function to send alerts
send_alert() {
    echo "$1" | mail -s "MySQL Maintenance Alert - $(hostname)" $EMAIL
}

# Daily tasks (run every day at 2 AM)
if [ "$1" = "daily" ]; then
    log_message "Starting daily maintenance tasks"
    
    # Health check
    $SCRIPT_DIR/mysql_health_check.sh
    
    # Log analysis
    $SCRIPT_DIR/mysql_log_analysis.sh
    
    # Basic cleanup
    mysql -u admin_user -p${ADMIN_PASSWORD} -e "
        DELETE FROM django_session WHERE expire_date < NOW();
        DELETE FROM auth_password_reset_tokens WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);
    "
    
    log_message "Daily maintenance tasks completed"
fi

# Weekly tasks (run every Sunday at 3 AM)
if [ "$1" = "weekly" ]; then
    log_message "Starting weekly maintenance tasks"
    
    # Index optimization
    $SCRIPT_DIR/weekly_index_optimization.sh
    
    # Performance analysis
    mysql -u admin_user -p${ADMIN_PASSWORD} ecommerce_db < $SCRIPT_DIR/weekly_performance_analysis.sql > $LOG_DIR/weekly_performance_$(date +%Y%m%d).txt
    
    # Data cleanup
    mysql -u admin_user -p${ADMIN_PASSWORD} ecommerce_db < $SCRIPT_DIR/weekly_data_cleanup.sql
    
    log_message "Weekly maintenance tasks completed"
fi

# Monthly tasks (run on 1st of each month at 4 AM)
if [ "$1" = "monthly" ]; then
    log_message "Starting monthly maintenance tasks"
    
    # Full optimization
    $SCRIPT_DIR/monthly_optimization.sh
    
    # Security audit
    $SCRIPT_DIR/monthly_security_audit.sh
    
    # Capacity analysis
    mysql -u admin_user -p${ADMIN_PASSWORD} ecommerce_db < $SCRIPT_DIR/monthly_capacity_analysis.sql > $LOG_DIR/monthly_capacity_$(date +%Y%m).txt
    
    log_message "Monthly maintenance tasks completed"
    send_alert "Monthly MySQL maintenance completed successfully"
fi
```

### Cron Configuration
```bash
# Add to root crontab
# Daily maintenance at 2 AM
0 2 * * * /usr/local/bin/mysql_maintenance_master.sh daily

# Weekly maintenance on Sunday at 3 AM
0 3 * * 0 /usr/local/bin/mysql_maintenance_master.sh weekly

# Monthly maintenance on 1st at 4 AM
0 4 1 * * /usr/local/bin/mysql_maintenance_master.sh monthly

# Health checks every 15 minutes
*/15 * * * * /usr/local/bin/mysql_health_check.sh

# Log rotation daily at 1 AM
0 1 * * * /usr/sbin/logrotate /etc/logrotate.d/mysql
```

## Maintenance Best Practices

### 1. Pre-Maintenance Checklist
- [ ] Verify backup is recent and valid
- [ ] Check system resources (CPU, memory, disk)
- [ ] Notify stakeholders of maintenance window
- [ ] Prepare rollback plan
- [ ] Test maintenance scripts in staging

### 2. During Maintenance
- [ ] Monitor system performance
- [ ] Log all actions taken
- [ ] Watch for error messages
- [ ] Verify each step completes successfully
- [ ] Keep stakeholders informed of progress

### 3. Post-Maintenance Checklist
- [ ] Verify application functionality
- [ ] Check performance metrics
- [ ] Review maintenance logs
- [ ] Update documentation
- [ ] Send completion notification

### 4. Emergency Procedures
If maintenance causes issues:
1. Stop maintenance immediately
2. Assess the situation
3. Implement rollback if necessary
4. Notify stakeholders
5. Document the incident
6. Schedule post-mortem review

## Monitoring Integration

### Nagios Checks
```bash
# Example Nagios configuration for maintenance monitoring
define service {
    use                     generic-service
    host_name               mysql-server
    service_description     MySQL Maintenance Status
    check_command           check_mysql_maintenance
    check_interval          60
    retry_interval          10
    max_check_attempts      3
    notification_interval   120
}
```

### Grafana Dashboard Metrics
- Table sizes and growth rates
- Index usage statistics
- Query performance trends
- Connection usage patterns
- Buffer pool efficiency
- Disk space utilization

This comprehensive maintenance guide ensures your MySQL database remains performant, secure, and reliable through regular automated and manual maintenance procedures.