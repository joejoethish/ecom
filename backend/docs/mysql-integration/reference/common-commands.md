# Common Commands Reference

## Quick Reference Guide

This reference provides commonly used commands for MySQL database administration, Django management, and troubleshooting.

## MySQL Administration Commands

### Connection and Basic Operations

#### Connect to MySQL
```bash
# Connect as root
mysql -u root -p

# Connect to specific database
mysql -u username -p database_name

# Connect with SSL
mysql -u username -p --ssl-mode=REQUIRED

# Connect to remote server
mysql -h hostname -u username -p database_name

# Connect with specific port
mysql -h hostname -P 3306 -u username -p
```

#### Database Operations
```sql
-- Show all databases
SHOW DATABASES;

-- Create database
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use database
USE ecommerce_db;

-- Drop database (be careful!)
DROP DATABASE database_name;

-- Show current database
SELECT DATABASE();
```

#### Table Operations
```sql
-- Show all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE table_name;
DESC table_name;

-- Show table creation statement
SHOW CREATE TABLE table_name;

-- Show table status
SHOW TABLE STATUS LIKE 'table_name';

-- Show indexes for table
SHOW INDEX FROM table_name;
```

### User Management

#### User Operations
```sql
-- Create user
CREATE USER 'username'@'host' IDENTIFIED BY 'password';

-- Grant privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON database_name.* TO 'username'@'host';
GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'host';

-- Show user privileges
SHOW GRANTS FOR 'username'@'host';

-- Revoke privileges
REVOKE DELETE ON database_name.* FROM 'username'@'host';

-- Change user password
ALTER USER 'username'@'host' IDENTIFIED BY 'new_password';

-- Drop user
DROP USER 'username'@'host';

-- Show all users
SELECT User, Host FROM mysql.user;

-- Apply privilege changes
FLUSH PRIVILEGES;
```

### Performance and Monitoring

#### Status and Variables
```sql
-- Show server status
SHOW STATUS;

-- Show specific status variables
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Slow_queries';
SHOW STATUS LIKE 'Innodb_buffer_pool%';

-- Show server variables
SHOW VARIABLES;

-- Show specific variables
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- Show process list
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;

-- Kill process
KILL process_id;
```

#### Performance Schema Queries
```sql
-- Top 10 slowest queries
SELECT 
    DIGEST_TEXT,
    COUNT_STAR as executions,
    AVG_TIMER_WAIT/1000000000 as avg_time_sec,
    SUM_TIMER_WAIT/1000000000 as total_time_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;

-- Index usage statistics
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

-- Connection statistics
SELECT 
    USER,
    HOST,
    CURRENT_CONNECTIONS,
    TOTAL_CONNECTIONS
FROM performance_schema.hosts;
```

### Backup and Recovery

#### Backup Commands
```bash
# Full database backup
mysqldump -u username -p database_name > backup.sql

# Backup with compression
mysqldump -u username -p database_name | gzip > backup.sql.gz

# Backup all databases
mysqldump -u root -p --all-databases > all_databases.sql

# Backup with additional options
mysqldump -u username -p \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    database_name > backup.sql

# Backup specific tables
mysqldump -u username -p database_name table1 table2 > tables_backup.sql

# Backup structure only (no data)
mysqldump -u username -p --no-data database_name > structure.sql

# Backup data only (no structure)
mysqldump -u username -p --no-create-info database_name > data.sql
```

#### Restore Commands
```bash
# Restore database
mysql -u username -p database_name < backup.sql

# Restore compressed backup
gunzip -c backup.sql.gz | mysql -u username -p database_name

# Restore all databases
mysql -u root -p < all_databases.sql

# Create database and restore
mysql -u root -p -e "CREATE DATABASE new_database;"
mysql -u username -p new_database < backup.sql
```

### Replication Commands

#### Master Configuration
```sql
-- Show master status
SHOW MASTER STATUS;

-- Show binary logs
SHOW BINARY LOGS;

-- Purge binary logs
PURGE BINARY LOGS TO 'mysql-bin.000010';
PURGE BINARY LOGS BEFORE '2024-01-01 00:00:00';

-- Reset master (be careful!)
RESET MASTER;
```

#### Slave Configuration
```sql
-- Show slave status
SHOW SLAVE STATUS\G

-- Start/stop slave
START SLAVE;
STOP SLAVE;

-- Reset slave
RESET SLAVE;
RESET SLAVE ALL;

-- Change master
CHANGE MASTER TO
    MASTER_HOST='master_host',
    MASTER_USER='replication_user',
    MASTER_PASSWORD='password',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=154;

-- Skip replication error
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;
```

## Django Management Commands

### Database Management

#### Migration Commands
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Migrate specific app
python manage.py migrate app_name

# Migrate to specific migration
python manage.py migrate app_name 0001

# Reverse migration
python manage.py migrate app_name zero

# Show SQL for migration
python manage.py sqlmigrate app_name 0001

# Create empty migration
python manage.py makemigrations --empty app_name
```

#### Database Shell and Inspection
```bash
# Open database shell
python manage.py dbshell

# Open Django shell
python manage.py shell

# Show SQL for model creation
python manage.py sqlmigrate app_name migration_name

# Inspect database
python manage.py inspectdb

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### Custom Management Commands

#### Database Utilities
```bash
# Backup database (custom command)
python manage.py backup_database

# Restore database (custom command)
python manage.py restore_database backup_file.sql

# Optimize database (custom command)
python manage.py optimize_database

# Check database health (custom command)
python manage.py check_database_health

# Migrate to MySQL (custom command)
python manage.py migrate_to_mysql

# Validate migration (custom command)
python manage.py validate_migration
```

## System Administration Commands

### Service Management

#### MySQL Service
```bash
# Start MySQL service
sudo systemctl start mysql
sudo service mysql start

# Stop MySQL service
sudo systemctl stop mysql
sudo service mysql stop

# Restart MySQL service
sudo systemctl restart mysql
sudo service mysql restart

# Check MySQL service status
sudo systemctl status mysql
sudo service mysql status

# Enable MySQL to start on boot
sudo systemctl enable mysql

# Disable MySQL from starting on boot
sudo systemctl disable mysql
```

#### Process Management
```bash
# Check MySQL processes
ps aux | grep mysql
pgrep mysql

# Kill MySQL process (if needed)
sudo pkill mysql
sudo killall mysql

# Check MySQL port
netstat -tlnp | grep 3306
ss -tlnp | grep 3306

# Check MySQL connections
netstat -an | grep 3306 | wc -l
```

### Log Management

#### MySQL Logs
```bash
# View error log
sudo tail -f /var/log/mysql/error.log

# View slow query log
sudo tail -f /var/log/mysql/mysql-slow.log

# View general query log
sudo tail -f /var/log/mysql/mysql.log

# View binary logs
mysqlbinlog /var/log/mysql/mysql-bin.000001

# Rotate logs
sudo logrotate /etc/logrotate.d/mysql

# Check log sizes
du -sh /var/log/mysql/*
```

#### Application Logs
```bash
# View Django logs
tail -f /var/log/django/django.log

# View application logs
tail -f /var/log/ecommerce/application.log

# View access logs
tail -f /var/log/nginx/access.log

# View error logs
tail -f /var/log/nginx/error.log
```

### File System Operations

#### MySQL Data Directory
```bash
# Check MySQL data directory
mysql -u root -p -e "SHOW VARIABLES LIKE 'datadir';"

# Check disk usage
df -h /var/lib/mysql

# Check MySQL file sizes
du -sh /var/lib/mysql/*

# Backup MySQL data directory
sudo cp -r /var/lib/mysql /backup/mysql_data_$(date +%Y%m%d)

# Check MySQL configuration files
ls -la /etc/mysql/
cat /etc/mysql/mysql.conf.d/mysqld.cnf
```

## Troubleshooting Commands

### Connection Issues

#### Network Diagnostics
```bash
# Test MySQL connection
telnet hostname 3306
nc -zv hostname 3306

# Check firewall rules
sudo ufw status
sudo iptables -L

# Check DNS resolution
nslookup mysql-server.company.com
dig mysql-server.company.com

# Test SSL connection
mysql -h hostname -u username -p --ssl-mode=REQUIRED
```

#### MySQL Diagnostics
```sql
-- Check connection limits
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- Check for locked tables
SHOW OPEN TABLES WHERE In_use > 0;

-- Check for long-running queries
SELECT * FROM information_schema.PROCESSLIST 
WHERE COMMAND != 'Sleep' 
ORDER BY TIME DESC;

-- Check InnoDB status
SHOW ENGINE INNODB STATUS;
```

### Performance Issues

#### System Resources
```bash
# Check CPU usage
top -p $(pgrep mysql)
htop -p $(pgrep mysql)

# Check memory usage
free -h
ps aux | grep mysql | awk '{print $6}'

# Check disk I/O
iostat -x 1 5
iotop -o

# Check network usage
iftop
nethogs
```

#### MySQL Performance
```sql
-- Check buffer pool usage
SHOW STATUS LIKE 'Innodb_buffer_pool%';

-- Check query cache
SHOW STATUS LIKE 'Qcache%';

-- Check slow queries
SHOW STATUS LIKE 'Slow_queries';

-- Check table locks
SHOW STATUS LIKE 'Table_locks%';

-- Check temporary tables
SHOW STATUS LIKE 'Created_tmp%';
```

### Data Issues

#### Table Maintenance
```sql
-- Check table for errors
CHECK TABLE table_name;

-- Repair table
REPAIR TABLE table_name;

-- Optimize table
OPTIMIZE TABLE table_name;

-- Analyze table
ANALYZE TABLE table_name;

-- Show table size
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'database_name'
ORDER BY (data_length + index_length) DESC;
```

#### Data Validation
```sql
-- Check for orphaned records
SELECT COUNT(*) FROM child_table c
LEFT JOIN parent_table p ON c.parent_id = p.id
WHERE p.id IS NULL;

-- Check data consistency
SELECT 
    (SELECT COUNT(*) FROM table1) as table1_count,
    (SELECT COUNT(*) FROM table2) as table2_count;

-- Find duplicate records
SELECT column_name, COUNT(*) 
FROM table_name 
GROUP BY column_name 
HAVING COUNT(*) > 1;
```

## Emergency Procedures

### Quick Recovery Commands

#### Service Recovery
```bash
# Emergency MySQL restart
sudo systemctl stop mysql
sudo systemctl start mysql

# Force MySQL restart
sudo pkill mysql
sudo systemctl start mysql

# Start MySQL in safe mode
sudo mysqld_safe --skip-grant-tables &

# Reset MySQL root password
sudo mysql -u root
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

#### Data Recovery
```bash
# Quick backup before changes
mysqldump -u root -p --single-transaction database_name > emergency_backup.sql

# Quick restore
mysql -u root -p database_name < emergency_backup.sql

# Copy table data
CREATE TABLE backup_table AS SELECT * FROM original_table;

# Restore table from backup
DROP TABLE original_table;
RENAME TABLE backup_table TO original_table;
```

### Monitoring Commands

#### Health Checks
```bash
# Quick health check script
#!/bin/bash
echo "=== MySQL Health Check ==="
systemctl is-active mysql && echo "✓ Service running" || echo "✗ Service down"
mysql -u root -p -e "SELECT 1;" &>/dev/null && echo "✓ Database accessible" || echo "✗ Database inaccessible"
df -h /var/lib/mysql | tail -1 | awk '{print "Disk usage: " $5}'
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';" | tail -1 | awk '{print "Connections: " $2}'
```

#### Performance Monitoring
```bash
# Monitor MySQL in real-time
watch -n 1 'mysql -u root -p -e "SHOW PROCESSLIST;" | head -20'

# Monitor system resources
watch -n 1 'ps aux | grep mysql | head -5'

# Monitor disk usage
watch -n 5 'df -h /var/lib/mysql'
```

## Configuration Files

### Important File Locations

#### MySQL Configuration
```bash
# Main configuration file
/etc/mysql/mysql.conf.d/mysqld.cnf

# Client configuration
/etc/mysql/mysql.conf.d/mysql.cnf

# User-specific configuration
~/.my.cnf

# Check configuration file locations
mysql --help | grep "Default options" -A 1
```

#### Log File Locations
```bash
# Error log
/var/log/mysql/error.log

# Slow query log
/var/log/mysql/mysql-slow.log

# General query log
/var/log/mysql/mysql.log

# Binary logs
/var/log/mysql/mysql-bin.*

# Relay logs (on slaves)
/var/log/mysql/mysql-relay-bin.*
```

#### Data Directory
```bash
# Default data directory
/var/lib/mysql/

# Socket file
/var/run/mysqld/mysqld.sock

# PID file
/var/run/mysqld/mysqld.pid
```

This comprehensive command reference provides quick access to the most commonly used commands for MySQL database administration, Django management, and system troubleshooting.