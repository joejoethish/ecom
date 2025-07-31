# MySQL Performance Tuning Guide

## Overview

This comprehensive guide covers MySQL performance optimization techniques, from basic configuration tuning to advanced query optimization strategies.

## System-Level Performance Tuning

### 1. Hardware Considerations

#### CPU Optimization
```bash
# Check CPU information
lscpu
cat /proc/cpuinfo | grep processor | wc -l

# Monitor CPU usage during peak times
top -p $(pgrep mysqld)
iostat -x 1 10

# Optimize CPU affinity for MySQL
taskset -cp 0-3 $(pgrep mysqld)  # Bind MySQL to specific CPU cores
```

#### Memory Configuration
```bash
# Check available memory
free -h
cat /proc/meminfo | grep -E "(MemTotal|MemAvailable|Buffers|Cached)"

# Monitor MySQL memory usage
ps aux | grep mysqld
pmap -d $(pgrep mysqld)

# Check for memory pressure
dmesg | grep -i "killed process"  # Look for OOM killer activity
```

#### Storage Optimization
```bash
# Check disk I/O performance
iostat -x 1 10
iotop -o -d 1

# Test disk performance
dd if=/dev/zero of=/var/lib/mysql/test_file bs=1M count=1000 oflag=direct
rm /var/lib/mysql/test_file

# Optimize filesystem for MySQL
# Use XFS or ext4 with appropriate mount options
# /dev/sdb1 /var/lib/mysql xfs defaults,noatime,nodiratime 0 0
```

### 2. Operating System Tuning

#### Kernel Parameters
```bash
# /etc/sysctl.conf optimizations for MySQL
vm.swappiness = 1                    # Minimize swapping
vm.dirty_ratio = 15                  # Percentage of memory for dirty pages
vm.dirty_background_ratio = 5        # Background writeback threshold
net.core.somaxconn = 65535          # Maximum socket connections
net.ipv4.tcp_max_syn_backlog = 65535 # TCP SYN backlog
fs.file-max = 2097152               # Maximum file descriptors

# Apply changes
sysctl -p
```

#### File System Limits
```bash
# /etc/security/limits.conf
mysql soft nofile 65535
mysql hard nofile 65535
mysql soft nproc 65535
mysql hard nproc 65535

# Verify limits
su - mysql -c "ulimit -n"
su - mysql -c "ulimit -u"
```

## MySQL Configuration Tuning

### 1. Core Configuration Parameters

#### my.cnf Optimization
```ini
[mysqld]
# Basic Settings
user = mysql
pid-file = /var/run/mysqld/mysqld.pid
socket = /var/run/mysqld/mysqld.sock
port = 3306
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp

# Connection Settings
max_connections = 500
max_connect_errors = 1000000
max_user_connections = 450
thread_cache_size = 50
open_files_limit = 65535
table_open_cache = 4000
table_definition_cache = 1000

# Buffer Pool Settings (Most Important)
# Set to 70-80% of available RAM for dedicated MySQL server
innodb_buffer_pool_size = 8G
innodb_buffer_pool_instances = 8
innodb_buffer_pool_chunk_size = 128M

# InnoDB Settings
innodb_log_file_size = 1G
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1
innodb_open_files = 4000

# Query Cache (Use with caution in high-write environments)
query_cache_type = 1
query_cache_size = 256M
query_cache_limit = 2M

# Temporary Tables
tmp_table_size = 256M
max_heap_table_size = 256M

# MyISAM Settings (if using MyISAM tables)
key_buffer_size = 256M
myisam_sort_buffer_size = 128M

# Logging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 2
log_queries_not_using_indexes = 1
log_slow_admin_statements = 1

# Binary Logging
log_bin = /var/log/mysql/mysql-bin.log
binlog_format = ROW
expire_logs_days = 7
max_binlog_size = 100M

# Replication Settings
server_id = 1
read_only = 0
sync_binlog = 1

# Performance Schema
performance_schema = ON
performance_schema_max_table_instances = 12500
performance_schema_max_table_handles = 4000
```

### 2. Dynamic Configuration Tuning

#### Runtime Configuration Changes
```sql
-- Check current configuration
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'max_connections';

-- Dynamic changes (no restart required)
SET GLOBAL max_connections = 600;
SET GLOBAL query_cache_size = 512*1024*1024;
SET GLOBAL tmp_table_size = 512*1024*1024;
SET GLOBAL max_heap_table_size = 512*1024*1024;

-- Changes requiring restart
-- innodb_buffer_pool_size (MySQL 5.7.5+ supports dynamic resize)
-- innodb_log_file_size
-- innodb_buffer_pool_instances
```

#### Configuration Validation
```sql
-- Check if configuration changes are effective
SHOW STATUS LIKE 'Created_tmp_disk_tables';
SHOW STATUS LIKE 'Created_tmp_tables';

-- Temporary table efficiency (should be < 25%)
SELECT 
    (Created_tmp_disk_tables / Created_tmp_tables) * 100 as tmp_disk_table_pct
FROM (
    SELECT 
        VARIABLE_VALUE as Created_tmp_disk_tables
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Created_tmp_disk_tables'
) a,
(
    SELECT 
        VARIABLE_VALUE as Created_tmp_tables
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Created_tmp_tables'
) b;
```

## Query Performance Optimization

### 1. Query Analysis Tools

#### Using EXPLAIN
```sql
-- Basic EXPLAIN
EXPLAIN SELECT * FROM products_product WHERE category_id = 1;

-- Extended EXPLAIN with execution stats
EXPLAIN FORMAT=JSON SELECT 
    p.name, p.price, c.name as category_name
FROM products_product p
JOIN products_category c ON p.category_id = c.id
WHERE p.price BETWEEN 100 AND 500;

-- EXPLAIN ANALYZE (MySQL 8.0+)
EXPLAIN ANALYZE SELECT 
    u.username, COUNT(o.id) as order_count
FROM auth_user u
LEFT JOIN orders_order o ON u.id = o.user_id
GROUP BY u.id, u.username
HAVING order_count > 5;
```

#### Performance Schema Queries
```sql
-- Find slowest queries
SELECT 
    DIGEST_TEXT,
    COUNT_STAR as exec_count,
    AVG_TIMER_WAIT/1000000000 as avg_time_sec,
    MAX_TIMER_WAIT/1000000000 as max_time_sec,
    SUM_TIMER_WAIT/1000000000 as total_time_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;

-- Find queries with high temporary table usage
SELECT 
    DIGEST_TEXT,
    COUNT_STAR,
    SUM_CREATED_TMP_TABLES,
    SUM_CREATED_TMP_DISK_TABLES,
    ROUND((SUM_CREATED_TMP_DISK_TABLES / SUM_CREATED_TMP_TABLES) * 100, 2) as disk_tmp_pct
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_CREATED_TMP_TABLES > 0
ORDER BY disk_tmp_pct DESC
LIMIT 10;

-- Find queries causing table scans
SELECT 
    DIGEST_TEXT,
    COUNT_STAR,
    SUM_SELECT_SCAN,
    SUM_SELECT_FULL_JOIN,
    SUM_NO_INDEX_USED,
    SUM_NO_GOOD_INDEX_USED
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_NO_INDEX_USED > 0 OR SUM_NO_GOOD_INDEX_USED > 0
ORDER BY SUM_NO_INDEX_USED DESC
LIMIT 10;
```

### 2. Index Optimization

#### Index Analysis
```sql
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

-- Check index cardinality
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    CARDINALITY,
    CASE 
        WHEN CARDINALITY = 0 THEN 'No data or no unique values'
        WHEN CARDINALITY = 1 THEN 'All values are the same'
        WHEN CARDINALITY < 10 THEN 'Low cardinality - consider composite index'
        ELSE 'Good cardinality'
    END as recommendation
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'ecommerce_db'
ORDER BY TABLE_NAME, INDEX_NAME;
```

#### Index Optimization Strategies
```sql
-- Create composite indexes for common query patterns
-- For queries filtering by category and price
CREATE INDEX idx_product_category_price ON products_product(category_id, price);

-- For queries filtering by user and date
CREATE INDEX idx_order_user_date ON orders_order(user_id, created_at);

-- For queries with ORDER BY and WHERE clauses
CREATE INDEX idx_product_category_created ON products_product(category_id, created_at DESC);

-- Covering indexes (include all columns needed by query)
CREATE INDEX idx_product_list_covering ON products_product(category_id, is_active, name, price, image_url);

-- Partial indexes for specific conditions
CREATE INDEX idx_active_products ON products_product(category_id, price) WHERE is_active = 1;

-- Full-text indexes for search functionality
CREATE FULLTEXT INDEX idx_product_search ON products_product(name, description);
```

### 3. Query Rewriting Techniques

#### Subquery Optimization
```sql
-- Inefficient subquery
SELECT * FROM products_product 
WHERE category_id IN (
    SELECT id FROM products_category WHERE name LIKE '%electronics%'
);

-- Optimized with JOIN
SELECT p.* FROM products_product p
JOIN products_category c ON p.category_id = c.id
WHERE c.name LIKE '%electronics%';

-- Correlated subquery (slow)
SELECT u.username,
    (SELECT COUNT(*) FROM orders_order o WHERE o.user_id = u.id) as order_count
FROM auth_user u;

-- Optimized with LEFT JOIN
SELECT u.username, COUNT(o.id) as order_count
FROM auth_user u
LEFT JOIN orders_order o ON u.id = o.user_id
GROUP BY u.id, u.username;
```

#### LIMIT Optimization
```sql
-- Inefficient pagination (gets slower with higher offsets)
SELECT * FROM products_product ORDER BY id LIMIT 10000, 20;

-- Optimized pagination using cursor-based approach
SELECT * FROM products_product 
WHERE id > 10000 
ORDER BY id 
LIMIT 20;

-- For complex ORDER BY, use covering index
SELECT id FROM products_product 
WHERE category_id = 1 
ORDER BY created_at DESC 
LIMIT 1000, 20;
-- Then join back to get full data
```

#### JOIN Optimization
```sql
-- Ensure proper JOIN order (smaller table first)
SELECT p.name, c.name as category_name
FROM products_category c  -- Smaller table first
JOIN products_product p ON c.id = p.category_id
WHERE c.is_active = 1;

-- Use appropriate JOIN types
-- INNER JOIN when you need matching records only
-- LEFT JOIN when you need all records from left table
-- Avoid RIGHT JOIN (use LEFT JOIN instead for clarity)

-- Optimize JOIN conditions
-- Use indexed columns in JOIN conditions
-- Avoid functions in JOIN conditions
SELECT p.name, u.username
FROM products_product p
JOIN auth_user u ON p.seller_id = u.id  -- Good: direct column comparison
-- Avoid: JOIN auth_user u ON UPPER(p.seller_name) = UPPER(u.username)
```

## Buffer Pool Optimization

### 1. Buffer Pool Sizing
```sql
-- Check buffer pool usage
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE,
    CASE VARIABLE_NAME
        WHEN 'Innodb_buffer_pool_pages_total' THEN ROUND(VARIABLE_VALUE * 16 / 1024, 2)
        WHEN 'Innodb_buffer_pool_pages_free' THEN ROUND(VARIABLE_VALUE * 16 / 1024, 2)
        WHEN 'Innodb_buffer_pool_pages_data' THEN ROUND(VARIABLE_VALUE * 16 / 1024, 2)
        ELSE NULL
    END as size_mb
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Innodb_buffer_pool_pages_total',
    'Innodb_buffer_pool_pages_free',
    'Innodb_buffer_pool_pages_data',
    'Innodb_buffer_pool_pages_dirty'
);

-- Calculate buffer pool hit ratio (should be > 99%)
SELECT 
    ROUND(
        (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100, 2
    ) as buffer_pool_hit_ratio_pct
FROM (
    SELECT 
        VARIABLE_VALUE as Innodb_buffer_pool_reads
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
) a,
(
    SELECT 
        VARIABLE_VALUE as Innodb_buffer_pool_read_requests
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
) b;
```

### 2. Buffer Pool Warming
```sql
-- Save buffer pool state before shutdown
SET GLOBAL innodb_buffer_pool_dump_at_shutdown = ON;

-- Load buffer pool state at startup
SET GLOBAL innodb_buffer_pool_load_at_startup = ON;

-- Manually dump buffer pool
SET GLOBAL innodb_buffer_pool_dump_now = ON;

-- Manually load buffer pool
SET GLOBAL innodb_buffer_pool_load_now = ON;

-- Check dump/load progress
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Innodb_buffer_pool_dump_status',
    'Innodb_buffer_pool_load_status'
);
```

## Connection and Thread Optimization

### 1. Connection Pool Tuning
```sql
-- Monitor connection usage
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Threads_connected',
    'Threads_running',
    'Max_used_connections',
    'Connections',
    'Aborted_connects',
    'Aborted_clients'
);

-- Check connection efficiency
SELECT 
    ROUND((Aborted_connects / Connections) * 100, 2) as aborted_connect_pct
FROM (
    SELECT VARIABLE_VALUE as Aborted_connects
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Aborted_connects'
) a,
(
    SELECT VARIABLE_VALUE as Connections
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Connections'
) b;
```

### 2. Thread Cache Optimization
```sql
-- Check thread cache efficiency
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Threads_created',
    'Connections'
);

-- Thread cache hit ratio (should be > 90%)
SELECT 
    ROUND((1 - (Threads_created / Connections)) * 100, 2) as thread_cache_hit_ratio_pct
FROM (
    SELECT VARIABLE_VALUE as Threads_created
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Threads_created'
) a,
(
    SELECT VARIABLE_VALUE as Connections
    FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Connections'
) b;

-- Adjust thread cache size if hit ratio is low
SET GLOBAL thread_cache_size = 100;
```

## Monitoring and Alerting

### 1. Key Performance Metrics
```sql
-- Create performance monitoring view
CREATE VIEW performance_metrics AS
SELECT 
    'Buffer Pool Hit Ratio' as metric,
    CONCAT(
        ROUND((1 - (bp_reads.VARIABLE_VALUE / bp_read_requests.VARIABLE_VALUE)) * 100, 2),
        '%'
    ) as value,
    CASE 
        WHEN (1 - (bp_reads.VARIABLE_VALUE / bp_read_requests.VARIABLE_VALUE)) * 100 >= 99 THEN 'Good'
        WHEN (1 - (bp_reads.VARIABLE_VALUE / bp_read_requests.VARIABLE_VALUE)) * 100 >= 95 THEN 'Warning'
        ELSE 'Critical'
    END as status
FROM 
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') bp_reads,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') bp_read_requests

UNION ALL

SELECT 
    'Connection Usage' as metric,
    CONCAT(
        ROUND((connected.VARIABLE_VALUE / max_conn.VARIABLE_VALUE) * 100, 2),
        '%'
    ) as value,
    CASE 
        WHEN (connected.VARIABLE_VALUE / max_conn.VARIABLE_VALUE) * 100 < 70 THEN 'Good'
        WHEN (connected.VARIABLE_VALUE / max_conn.VARIABLE_VALUE) * 100 < 85 THEN 'Warning'
        ELSE 'Critical'
    END as status
FROM 
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected') connected,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') max_conn;

-- Query the performance metrics
SELECT * FROM performance_metrics;
```

### 2. Automated Performance Alerts
```bash
#!/bin/bash
# /usr/local/bin/mysql_performance_alerts.sh

# Configuration
MYSQL_USER="monitoring_user"
MYSQL_PASS="monitoring_password"
ALERT_EMAIL="admin@company.com"
HOSTNAME=$(hostname)

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject - $HOSTNAME" "$ALERT_EMAIL"
}

# Check buffer pool hit ratio
BP_HIT_RATIO=$(mysql -u $MYSQL_USER -p$MYSQL_PASS -e "
SELECT ROUND((1 - (bp_reads.VARIABLE_VALUE / bp_read_requests.VARIABLE_VALUE)) * 100, 2) as hit_ratio
FROM 
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') bp_reads,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') bp_read_requests;
" | tail -1)

if (( $(echo "$BP_HIT_RATIO < 95" | bc -l) )); then
    send_alert "Low Buffer Pool Hit Ratio" "Buffer pool hit ratio is $BP_HIT_RATIO%. Consider increasing innodb_buffer_pool_size."
fi

# Check connection usage
CONN_USAGE=$(mysql -u $MYSQL_USER -p$MYSQL_PASS -e "
SELECT ROUND((connected.VARIABLE_VALUE / max_conn.VARIABLE_VALUE) * 100, 2) as usage_pct
FROM 
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected') connected,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') max_conn;
" | tail -1)

if (( $(echo "$CONN_USAGE > 80" | bc -l) )); then
    send_alert "High Connection Usage" "Connection usage is $CONN_USAGE%. Consider increasing max_connections or optimizing connection pooling."
fi

# Check for slow queries
SLOW_QUERIES=$(mysql -u $MYSQL_USER -p$MYSQL_PASS -e "
SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Slow_queries';
" | tail -1)

# Store previous count and compare
PREV_SLOW_FILE="/tmp/mysql_slow_queries_prev"
if [ -f "$PREV_SLOW_FILE" ]; then
    PREV_SLOW=$(cat $PREV_SLOW_FILE)
    SLOW_DIFF=$((SLOW_QUERIES - PREV_SLOW))
    if [ $SLOW_DIFF -gt 10 ]; then
        send_alert "High Slow Query Rate" "Detected $SLOW_DIFF new slow queries in the last check interval."
    fi
fi
echo $SLOW_QUERIES > $PREV_SLOW_FILE
```

## Performance Testing and Benchmarking

### 1. Benchmarking Tools
```bash
# Install sysbench for MySQL benchmarking
sudo apt-get install sysbench

# Prepare test data
sysbench oltp_read_write \
    --mysql-host=localhost \
    --mysql-user=test_user \
    --mysql-password=test_password \
    --mysql-db=test_db \
    --tables=10 \
    --table-size=100000 \
    prepare

# Run read-write benchmark
sysbench oltp_read_write \
    --mysql-host=localhost \
    --mysql-user=test_user \
    --mysql-password=test_password \
    --mysql-db=test_db \
    --tables=10 \
    --table-size=100000 \
    --threads=16 \
    --time=300 \
    --report-interval=10 \
    run

# Cleanup test data
sysbench oltp_read_write \
    --mysql-host=localhost \
    --mysql-user=test_user \
    --mysql-password=test_password \
    --mysql-db=test_db \
    --tables=10 \
    cleanup
```

### 2. Application-Specific Benchmarking
```python
# Django management command for performance testing
# management/commands/benchmark_performance.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
import time
import statistics

class Command(BaseCommand):
    help = 'Benchmark database performance'
    
    def add_arguments(self, parser):
        parser.add_argument('--iterations', type=int, default=100)
        parser.add_argument('--query-type', choices=['select', 'insert', 'update'], default='select')
    
    def handle(self, *args, **options):
        iterations = options['iterations']
        query_type = options['query_type']
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            if query_type == 'select':
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM products_product LIMIT 100")
                    cursor.fetchall()
            elif query_type == 'insert':
                # Implement insert benchmark
                pass
            elif query_type == 'update':
                # Implement update benchmark
                pass
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        self.stdout.write(f"Performance Results for {query_type} queries:")
        self.stdout.write(f"Iterations: {iterations}")
        self.stdout.write(f"Average time: {statistics.mean(times):.4f} seconds")
        self.stdout.write(f"Median time: {statistics.median(times):.4f} seconds")
        self.stdout.write(f"Min time: {min(times):.4f} seconds")
        self.stdout.write(f"Max time: {max(times):.4f} seconds")
        self.stdout.write(f"Standard deviation: {statistics.stdev(times):.4f} seconds")
```

This comprehensive performance tuning guide provides the foundation for optimizing MySQL performance across all levels, from hardware and OS configuration to query-level optimizations.