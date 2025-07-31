# Database Administrator Training Guide

## Overview

This comprehensive training guide is designed for database administrators who will be managing the MySQL database infrastructure. It covers essential skills, procedures, and best practices for effective database administration.

## Training Prerequisites

### Required Knowledge
- Basic Linux/Unix system administration
- Understanding of relational database concepts
- SQL query language fundamentals
- Basic networking concepts
- Command line proficiency

### Recommended Experience
- Previous database administration experience (any RDBMS)
- Experience with backup and recovery procedures
- Basic scripting knowledge (Bash, Python)
- Understanding of web application architecture

## Module 1: MySQL Architecture and Installation

### 1.1 MySQL Architecture Overview

#### Core Components
```
MySQL Server Architecture:
┌─────────────────────────────────────┐
│           Connection Layer          │
├─────────────────────────────────────┤
│             SQL Layer               │
│  ┌─────────────┐ ┌─────────────────┐│
│  │   Parser    │ │   Optimizer     ││
│  └─────────────┘ └─────────────────┘│
├─────────────────────────────────────┤
│           Storage Engine Layer      │
│  ┌─────────────┐ ┌─────────────────┐│
│  │   InnoDB    │ │     MyISAM      ││
│  └─────────────┘ └─────────────────┘│
└─────────────────────────────────────┘
```

#### Key Concepts
- **Connection Management**: How MySQL handles client connections
- **Query Processing**: SQL parsing, optimization, and execution
- **Storage Engines**: InnoDB vs MyISAM characteristics
- **Buffer Pool**: Memory management for data caching
- **Transaction Management**: ACID properties and isolation levels

#### Hands-on Exercise 1.1
```sql
-- Explore MySQL architecture
SHOW ENGINES;
SHOW VARIABLES LIKE 'version%';
SHOW STATUS LIKE 'Threads%';
SELECT * FROM information_schema.ENGINES;

-- Check storage engine usage
SELECT 
    ENGINE,
    COUNT(*) as table_count,
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables 
WHERE table_schema = 'ecommerce_db'
GROUP BY ENGINE;
```

### 1.2 Installation and Configuration

#### Installation Process
```bash
# Ubuntu/Debian installation
sudo apt update
sudo apt install mysql-server-8.0

# Secure installation
sudo mysql_secure_installation

# Start and enable service
sudo systemctl start mysql
sudo systemctl enable mysql

# Verify installation
mysql --version
sudo systemctl status mysql
```

#### Initial Configuration
```bash
# Edit main configuration file
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# Key settings to configure:
# - bind-address
# - max_connections
# - innodb_buffer_pool_size
# - log file locations

# Restart after configuration changes
sudo systemctl restart mysql
```

#### Hands-on Exercise 1.2
```bash
# Practice installation on test VM
# Configure basic security settings
# Set up initial user accounts
# Verify configuration parameters
```

## Module 2: User Management and Security

### 2.1 User Account Management

#### Creating Users and Granting Privileges
```sql
-- Create application user
CREATE USER 'ecommerce_app'@'%' IDENTIFIED BY 'SecurePassword123!';

-- Grant specific privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce_db.* TO 'ecommerce_app'@'%';

-- Create read-only user
CREATE USER 'ecommerce_readonly'@'%' IDENTIFIED BY 'ReadOnlyPass456!';
GRANT SELECT ON ecommerce_db.* TO 'ecommerce_readonly'@'%';

-- Create backup user
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'BackupPass789!';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;
```

#### User Management Best Practices
```sql
-- View existing users
SELECT User, Host, authentication_string, password_expired 
FROM mysql.user;

-- Check user privileges
SHOW GRANTS FOR 'ecommerce_app'@'%';

-- Modify user privileges
REVOKE DELETE ON ecommerce_db.* FROM 'ecommerce_app'@'%';
GRANT DELETE ON ecommerce_db.orders_order TO 'ecommerce_app'@'%';

-- Change user password
ALTER USER 'ecommerce_app'@'%' IDENTIFIED BY 'NewSecurePassword123!';

-- Set password expiration
ALTER USER 'ecommerce_app'@'%' PASSWORD EXPIRE INTERVAL 90 DAY;

-- Lock/unlock user account
ALTER USER 'ecommerce_app'@'%' ACCOUNT LOCK;
ALTER USER 'ecommerce_app'@'%' ACCOUNT UNLOCK;
```

#### Hands-on Exercise 2.1
```sql
-- Create a complete set of users for the ecommerce application:
-- 1. Application user with appropriate privileges
-- 2. Read-only user for reporting
-- 3. Backup user with minimal required privileges
-- 4. Monitoring user for health checks
-- 5. Replication user for replica setup

-- Test each user's access and verify privilege restrictions
```

### 2.2 Security Configuration

#### SSL/TLS Configuration
```bash
# Generate SSL certificates
sudo mysql_ssl_rsa_setup --uid=mysql

# Verify SSL files
ls -la /var/lib/mysql/*.pem

# Configure SSL in my.cnf
[mysqld]
ssl-ca=/var/lib/mysql/ca.pem
ssl-cert=/var/lib/mysql/server-cert.pem
ssl-key=/var/lib/mysql/server-key.pem
require_secure_transport=ON

# Restart MySQL
sudo systemctl restart mysql
```

#### SSL Connection Testing
```sql
-- Check SSL status
SHOW VARIABLES LIKE '%ssl%';
SHOW STATUS LIKE 'Ssl%';

-- Require SSL for specific users
ALTER USER 'ecommerce_app'@'%' REQUIRE SSL;

-- Test SSL connection
mysql -u ecommerce_app -p --ssl-mode=REQUIRED
```

#### Hands-on Exercise 2.2
```bash
# Configure SSL certificates
# Set up SSL-required users
# Test SSL connections
# Configure firewall rules for MySQL port
```

## Module 3: Backup and Recovery

### 3.1 Backup Strategies

#### Full Backup with mysqldump
```bash
#!/bin/bash
# Full backup script

BACKUP_DIR="/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/full_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
mysqldump -u backup_user -p \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --all-databases \
    --master-data=2 > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}.gz"
else
    echo "Backup failed!"
    exit 1
fi

# Clean up old backups (keep 30 days)
find $BACKUP_DIR -name "full_backup_*.sql.gz" -mtime +30 -delete
```

#### Incremental Backup with Binary Logs
```bash
#!/bin/bash
# Incremental backup script

BINLOG_DIR="/var/log/mysql"
BACKUP_DIR="/backups/mysql/binlogs"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Flush logs to create new binary log
mysql -u root -p -e "FLUSH LOGS;"

# Copy binary logs
cp $BINLOG_DIR/mysql-bin.* $BACKUP_DIR/

# Create index of backed up logs
ls -la $BACKUP_DIR/mysql-bin.* > $BACKUP_DIR/binlog_index_$DATE.txt

echo "Incremental backup completed: $BACKUP_DIR"
```

#### Hands-on Exercise 3.1
```bash
# Create and test full backup script
# Set up incremental backup with binary logs
# Practice backup verification procedures
# Configure automated backup scheduling with cron
```

### 3.2 Recovery Procedures

#### Full Database Recovery
```bash
#!/bin/bash
# Full recovery script

BACKUP_FILE="$1"
RECOVERY_DB="$2"

if [ -z "$BACKUP_FILE" ] || [ -z "$RECOVERY_DB" ]; then
    echo "Usage: $0 <backup_file> <recovery_database>"
    exit 1
fi

echo "Starting recovery from $BACKUP_FILE to $RECOVERY_DB"

# Create recovery database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS $RECOVERY_DB;"

# Restore from backup
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | mysql -u root -p $RECOVERY_DB
else
    mysql -u root -p $RECOVERY_DB < $BACKUP_FILE
fi

if [ $? -eq 0 ]; then
    echo "Recovery completed successfully"
    
    # Verify recovery
    TABLE_COUNT=$(mysql -u root -p -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$RECOVERY_DB';" | tail -1)
    echo "Recovered $TABLE_COUNT tables"
else
    echo "Recovery failed!"
    exit 1
fi
```

#### Point-in-Time Recovery
```bash
#!/bin/bash
# Point-in-time recovery script

BACKUP_FILE="$1"
RECOVERY_TIME="$2"
RECOVERY_DB="$3"

echo "Performing point-in-time recovery to $RECOVERY_TIME"

# 1. Restore from full backup
gunzip -c $BACKUP_FILE | mysql -u root -p $RECOVERY_DB

# 2. Apply binary logs up to recovery point
BINLOG_FILES=$(mysql -u root -p -e "SHOW BINARY LOGS;" | awk 'NR>1 {print $1}')

for binlog in $BINLOG_FILES; do
    echo "Processing binary log: $binlog"
    mysqlbinlog --stop-datetime="$RECOVERY_TIME" /var/log/mysql/$binlog | \
        mysql -u root -p $RECOVERY_DB
done

echo "Point-in-time recovery completed"
```

#### Hands-on Exercise 3.2
```bash
# Practice full database recovery
# Perform point-in-time recovery exercise
# Test recovery procedures with different scenarios
# Document recovery time objectives (RTO)
```

## Module 4: Performance Monitoring and Tuning

### 4.1 Performance Monitoring

#### Key Performance Metrics
```sql
-- Connection metrics
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Threads_connected',
    'Threads_running',
    'Max_used_connections',
    'Connections',
    'Aborted_connects'
);

-- Buffer pool metrics
SELECT 
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME LIKE 'Innodb_buffer_pool%';

-- Query performance metrics
SELECT 
    DIGEST_TEXT,
    COUNT_STAR as executions,
    AVG_TIMER_WAIT/1000000000 as avg_time_sec,
    SUM_TIMER_WAIT/1000000000 as total_time_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

#### Monitoring Script
```bash
#!/bin/bash
# MySQL monitoring script

MONITOR_LOG="/var/log/mysql/monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] MySQL Performance Monitor" | tee -a $MONITOR_LOG

# Check connection usage
CONNECTIONS=$(mysql -u monitor -p${MONITOR_PASSWORD} -e "SHOW STATUS LIKE 'Threads_connected';" | tail -1 | awk '{print $2}')
MAX_CONNECTIONS=$(mysql -u monitor -p${MONITOR_PASSWORD} -e "SHOW VARIABLES LIKE 'max_connections';" | tail -1 | awk '{print $2}')
CONNECTION_PCT=$((CONNECTIONS * 100 / MAX_CONNECTIONS))

echo "[$TIMESTAMP] Connections: $CONNECTIONS/$MAX_CONNECTIONS ($CONNECTION_PCT%)" | tee -a $MONITOR_LOG

# Check buffer pool hit ratio
BP_HIT_RATIO=$(mysql -u monitor -p${MONITOR_PASSWORD} -e "
SELECT ROUND((1 - (bp_reads.VARIABLE_VALUE / bp_read_requests.VARIABLE_VALUE)) * 100, 2) as hit_ratio
FROM 
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') bp_reads,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') bp_read_requests;
" | tail -1)

echo "[$TIMESTAMP] Buffer Pool Hit Ratio: $BP_HIT_RATIO%" | tee -a $MONITOR_LOG

# Check slow queries
SLOW_QUERIES=$(mysql -u monitor -p${MONITOR_PASSWORD} -e "SHOW STATUS LIKE 'Slow_queries';" | tail -1 | awk '{print $2}')
echo "[$TIMESTAMP] Slow Queries: $SLOW_QUERIES" | tee -a $MONITOR_LOG
```

#### Hands-on Exercise 4.1
```bash
# Set up performance monitoring
# Create custom monitoring scripts
# Configure alerting thresholds
# Practice interpreting performance metrics
```

### 4.2 Performance Tuning

#### Configuration Tuning
```ini
# Optimized my.cnf configuration
[mysqld]
# Connection settings
max_connections = 500
thread_cache_size = 50

# Buffer pool settings (70-80% of RAM)
innodb_buffer_pool_size = 8G
innodb_buffer_pool_instances = 8

# Log settings
innodb_log_file_size = 1G
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 2

# Query cache
query_cache_type = 1
query_cache_size = 256M

# Temporary tables
tmp_table_size = 256M
max_heap_table_size = 256M
```

#### Index Optimization
```sql
-- Analyze index usage
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
AND COUNT_FETCH = 0;

-- Create optimized indexes
CREATE INDEX idx_product_category_price ON products_product(category_id, price);
CREATE INDEX idx_order_user_date ON orders_order(user_id, created_at);
```

#### Hands-on Exercise 4.2
```bash
# Tune MySQL configuration parameters
# Optimize database indexes
# Analyze and improve slow queries
# Measure performance improvements
```

## Module 5: Replication and High Availability

### 5.1 MySQL Replication Setup

#### Master Configuration
```ini
# Master server configuration
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog-format = ROW
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1
```

#### Replica Configuration
```ini
# Replica server configuration
[mysqld]
server-id = 2
relay-log = mysql-relay-bin
read_only = 1
```

#### Replication Setup Commands
```sql
-- On master: Create replication user
CREATE USER 'replication_user'@'%' IDENTIFIED BY 'ReplicationPass123!';
GRANT REPLICATION SLAVE ON *.* TO 'replication_user'@'%';
FLUSH PRIVILEGES;

-- Get master status
SHOW MASTER STATUS;

-- On replica: Configure replication
CHANGE MASTER TO
    MASTER_HOST='master_server_ip',
    MASTER_USER='replication_user',
    MASTER_PASSWORD='ReplicationPass123!',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=154;

-- Start replication
START SLAVE;

-- Check replication status
SHOW SLAVE STATUS\G
```

#### Hands-on Exercise 5.1
```bash
# Set up master-replica replication
# Configure multiple replicas
# Test replication functionality
# Practice replication troubleshooting
```

### 5.2 High Availability Configuration

#### Automated Failover Script
```bash
#!/bin/bash
# Automated failover script

MASTER_HOST="mysql-master.company.com"
REPLICA_HOST="mysql-replica.company.com"
VIP="192.168.1.100"

# Check master health
if ! mysql -h $MASTER_HOST -u monitor -p${MONITOR_PASSWORD} -e "SELECT 1;" &>/dev/null; then
    echo "Master is down, initiating failover"
    
    # Promote replica to master
    ssh $REPLICA_HOST "
        mysql -u root -p${ROOT_PASSWORD} -e 'STOP SLAVE;'
        mysql -u root -p${ROOT_PASSWORD} -e 'RESET SLAVE ALL;'
        mysql -u root -p${ROOT_PASSWORD} -e 'SET GLOBAL read_only = OFF;'
    "
    
    # Move VIP to replica
    ssh $REPLICA_HOST "sudo ip addr add $VIP/24 dev eth0"
    
    # Update DNS or load balancer configuration
    # Send notifications
    
    echo "Failover completed"
else
    echo "Master is healthy"
fi
```

#### Hands-on Exercise 5.2
```bash
# Configure high availability setup
# Test automated failover procedures
# Practice manual failover scenarios
# Document recovery procedures
```

## Module 6: Troubleshooting and Maintenance

### 6.1 Common Issues and Solutions

#### Connection Issues
```bash
# Check MySQL service status
sudo systemctl status mysql

# Check MySQL error log
sudo tail -f /var/log/mysql/error.log

# Check connection limits
mysql -u root -p -e "SHOW VARIABLES LIKE 'max_connections';"
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Check for blocked connections
mysql -u root -p -e "SHOW PROCESSLIST;"
```

#### Performance Issues
```sql
-- Identify slow queries
SELECT 
    DIGEST_TEXT,
    COUNT_STAR,
    AVG_TIMER_WAIT/1000000000 as avg_time_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;

-- Check for table locks
SHOW OPEN TABLES WHERE In_use > 0;

-- Check InnoDB status
SHOW ENGINE INNODB STATUS;
```

#### Hands-on Exercise 6.1
```bash
# Practice troubleshooting common MySQL issues
# Use diagnostic tools and commands
# Interpret error messages and logs
# Develop troubleshooting methodology
```

### 6.2 Maintenance Procedures

#### Regular Maintenance Tasks
```bash
#!/bin/bash
# Weekly maintenance script

echo "Starting weekly MySQL maintenance"

# Analyze tables
mysql -u root -p -e "
ANALYZE TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.orders_order;
"

# Optimize tables
mysql -u root -p -e "
OPTIMIZE TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.orders_order;
"

# Check for corruption
mysql -u root -p -e "
CHECK TABLE 
    ecommerce_db.auth_user,
    ecommerce_db.products_product,
    ecommerce_db.orders_order;
"

# Clean up old logs
find /var/log/mysql -name "*.log" -mtime +30 -delete

echo "Weekly maintenance completed"
```

#### Hands-on Exercise 6.2
```bash
# Create maintenance procedures
# Schedule automated maintenance tasks
# Practice table optimization and repair
# Develop maintenance checklists
```

## Module 7: Security and Compliance

### 7.1 Security Best Practices

#### Security Checklist
- [ ] Remove anonymous users
- [ ] Remove test databases
- [ ] Set strong root password
- [ ] Disable remote root login
- [ ] Use SSL/TLS for connections
- [ ] Implement proper user privileges
- [ ] Enable audit logging
- [ ] Regular security updates

#### Audit Logging Configuration
```sql
-- Enable audit logging
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configure audit settings
SET GLOBAL audit_log_policy = ALL;
SET GLOBAL audit_log_format = JSON;

-- Check audit log status
SHOW VARIABLES LIKE 'audit_log%';
```

#### Hands-on Exercise 7.1
```bash
# Implement security hardening measures
# Configure audit logging
# Practice security assessment procedures
# Create security monitoring scripts
```

## Module 8: Automation and Scripting

### 8.1 Administrative Scripts

#### Database Health Check Script
```bash
#!/bin/bash
# Comprehensive health check script

HEALTH_LOG="/var/log/mysql/health_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting MySQL health check" | tee -a $HEALTH_LOG

# Check service status
if systemctl is-active --quiet mysql; then
    echo "[$TIMESTAMP] ✓ MySQL service is running" | tee -a $HEALTH_LOG
else
    echo "[$TIMESTAMP] ✗ MySQL service is down" | tee -a $HEALTH_LOG
    exit 1
fi

# Check disk space
DISK_USAGE=$(df /var/lib/mysql | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 85 ]; then
    echo "[$TIMESTAMP] ✓ Disk usage is normal ($DISK_USAGE%)" | tee -a $HEALTH_LOG
else
    echo "[$TIMESTAMP] ⚠ High disk usage ($DISK_USAGE%)" | tee -a $HEALTH_LOG
fi

# Check replication status
SLAVE_STATUS=$(mysql -u monitor -p${MONITOR_PASSWORD} -e "SHOW SLAVE STATUS\G" | grep "Slave_SQL_Running" | awk '{print $2}')
if [ "$SLAVE_STATUS" = "Yes" ]; then
    echo "[$TIMESTAMP] ✓ Replication is running" | tee -a $HEALTH_LOG
else
    echo "[$TIMESTAMP] ⚠ Replication issues detected" | tee -a $HEALTH_LOG
fi

echo "[$TIMESTAMP] Health check completed" | tee -a $HEALTH_LOG
```

#### Hands-on Exercise 8.1
```bash
# Create comprehensive administrative scripts
# Automate routine maintenance tasks
# Develop monitoring and alerting scripts
# Practice script testing and deployment
```

## Assessment and Certification

### Practical Assessment Tasks

#### Task 1: Database Setup and Configuration
- Install MySQL server
- Configure security settings
- Create user accounts with appropriate privileges
- Set up SSL connections

#### Task 2: Backup and Recovery
- Create full backup procedures
- Implement incremental backup strategy
- Perform point-in-time recovery
- Test backup integrity

#### Task 3: Performance Tuning
- Analyze database performance
- Optimize configuration parameters
- Create and optimize indexes
- Monitor performance improvements

#### Task 4: Replication Setup
- Configure master-replica replication
- Test replication functionality
- Implement failover procedures
- Monitor replication health

#### Task 5: Troubleshooting
- Diagnose and resolve connection issues
- Identify and fix performance problems
- Handle replication failures
- Recover from data corruption

### Certification Requirements

#### Knowledge Areas
- MySQL architecture and components
- Installation and configuration
- User management and security
- Backup and recovery procedures
- Performance monitoring and tuning
- Replication and high availability
- Troubleshooting and maintenance

#### Practical Skills
- Command-line proficiency
- SQL query optimization
- Script development
- Problem-solving methodology
- Documentation skills

## Ongoing Learning and Development

### Advanced Topics
- MySQL 8.0 new features
- MySQL Cluster (NDB)
- MySQL in cloud environments
- Advanced replication topologies
- Database sharding strategies

### Resources for Continued Learning
- MySQL official documentation
- MySQL certification programs
- Database administration communities
- Performance tuning guides
- Security best practices updates

### Regular Training Updates
- Quarterly security updates
- Annual performance tuning review
- New feature training as released
- Best practices workshops
- Disaster recovery drills

This comprehensive training guide provides database administrators with the knowledge and skills needed to effectively manage MySQL database infrastructure in production environments.