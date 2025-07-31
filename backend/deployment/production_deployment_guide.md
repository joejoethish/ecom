# MySQL Production Deployment Guide

## Overview

This guide provides comprehensive procedures for deploying MySQL database integration to production environments, ensuring zero-downtime migration, security, and reliability.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: SSD with at least 100GB free space
- **Network**: Stable internet connection with firewall access
- **Backup Storage**: External storage for backups (AWS S3, Google Cloud, etc.)

### Software Requirements
- MySQL 8.0+
- Python 3.9+
- Django 4.2+
- Redis 6.0+ (for caching)
- Nginx 1.18+
- SSL certificates

### Access Requirements
- Root/sudo access to production servers
- Database administrator credentials
- SSL certificate files
- Backup storage credentials

## Pre-Deployment Checklist

### 1. Environment Preparation
- [ ] Production server provisioned and accessible
- [ ] MySQL 8.0 installed and configured
- [ ] SSL certificates obtained and validated
- [ ] Firewall rules configured
- [ ] Backup storage configured
- [ ] Monitoring tools installed

### 2. Security Validation
- [ ] Database user accounts created with minimal privileges
- [ ] SSL/TLS encryption enabled
- [ ] Firewall rules restricting database access
- [ ] Audit logging enabled
- [ ] Security patches applied

### 3. Performance Optimization
- [ ] MySQL configuration optimized for production
- [ ] Indexes created and validated
- [ ] Connection pooling configured
- [ ] Query performance tested
- [ ] Resource monitoring enabled

### 4. Backup and Recovery
- [ ] Backup procedures tested
- [ ] Recovery procedures validated
- [ ] Backup storage accessible
- [ ] Retention policies configured
- [ ] Monitoring alerts configured

## Deployment Procedures

### Phase 1: MySQL Server Setup

#### 1.1 Install MySQL 8.0
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server-8.0

# CentOS/RHEL
sudo dnf install mysql-server
sudo systemctl enable mysqld
sudo systemctl start mysqld
```

#### 1.2 Secure MySQL Installation
```bash
sudo mysql_secure_installation
```

#### 1.3 Configure MySQL for Production
```bash
# Create production configuration
sudo cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

**Production MySQL Configuration:**
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
lc-messages-dir = /usr/share/mysql

# Performance Settings
innodb_buffer_pool_size = 4G
innodb_log_file_size = 512M
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1
innodb_open_files = 400

# Connection Settings
max_connections = 500
max_connect_errors = 1000
connect_timeout = 60
wait_timeout = 28800
interactive_timeout = 28800
max_allowed_packet = 64M

# Query Cache (if needed)
query_cache_type = 1
query_cache_size = 256M
query_cache_limit = 2M

# Logging
general_log = 1
general_log_file = /var/log/mysql/mysql.log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 2
log_queries_not_using_indexes = 1

# Security Settings
ssl-ca = /etc/mysql/ssl/ca-cert.pem
ssl-cert = /etc/mysql/ssl/server-cert.pem
ssl-key = /etc/mysql/ssl/server-key.pem
require_secure_transport = ON
local_infile = 0

# Binary Logging (for replication and backups)
log-bin = mysql-bin
binlog_format = ROW
expire_logs_days = 7
max_binlog_size = 100M

# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
```

#### 1.4 Create SSL Certificates
```bash
# Create SSL directory
sudo mkdir -p /etc/mysql/ssl
cd /etc/mysql/ssl

# Generate CA key and certificate
sudo openssl genrsa 2048 > ca-key.pem
sudo openssl req -new -x509 -nodes -days 3600 -key ca-key.pem -out ca-cert.pem

# Generate server key and certificate
sudo openssl req -newkey rsa:2048 -days 3600 -nodes -keyout server-key.pem -out server-req.pem
sudo openssl rsa -in server-key.pem -out server-key.pem
sudo openssl x509 -req -in server-req.pem -days 3600 -CA ca-cert.pem -CAkey ca-key.pem -set_serial 01 -out server-cert.pem

# Set permissions
sudo chown mysql:mysql /etc/mysql/ssl/*
sudo chmod 600 /etc/mysql/ssl/*-key.pem
sudo chmod 644 /etc/mysql/ssl/*-cert.pem
```

#### 1.5 Restart MySQL and Verify
```bash
sudo systemctl restart mysql
sudo systemctl status mysql

# Verify SSL
mysql -u root -p -e "SHOW VARIABLES LIKE '%ssl%';"
```

### Phase 2: Database and User Setup

#### 2.1 Create Production Database
```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE ecommerce_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create application user
CREATE USER 'ecommerce_app'@'%' IDENTIFIED BY 'STRONG_PASSWORD_HERE' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce_prod.* TO 'ecommerce_app'@'%';

-- Create read-only user for replicas
CREATE USER 'ecommerce_read'@'%' IDENTIFIED BY 'STRONG_READ_PASSWORD_HERE' REQUIRE SSL;
GRANT SELECT ON ecommerce_prod.* TO 'ecommerce_read'@'%';

-- Create backup user
CREATE USER 'ecommerce_backup'@'localhost' IDENTIFIED BY 'STRONG_BACKUP_PASSWORD_HERE';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON ecommerce_prod.* TO 'ecommerce_backup'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;
```

#### 2.2 Configure Firewall
```bash
# Ubuntu/Debian
sudo ufw allow from YOUR_APP_SERVER_IP to any port 3306
sudo ufw allow from YOUR_BACKUP_SERVER_IP to any port 3306

# CentOS/RHEL
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='YOUR_APP_SERVER_IP' port protocol='tcp' port='3306' accept"
sudo firewall-cmd --reload
```

### Phase 3: Application Configuration

#### 3.1 Update Django Settings
Create production settings file:

```python
# settings/production.py
import os
from .base import *

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ecommerce_prod'),
        'USER': os.environ.get('DB_USER', 'ecommerce_app'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
            'ssl': {
                'ca': '/etc/mysql/ssl/ca-cert.pem',
                'cert': '/etc/mysql/ssl/client-cert.pem',
                'key': '/etc/mysql/ssl/client-key.pem',
            },
        },
        'CONN_MAX_AGE': 3600,
        'CONN_HEALTH_CHECKS': True,
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ecommerce_prod'),
        'USER': os.environ.get('DB_READ_USER', 'ecommerce_read'),
        'PASSWORD': os.environ.get('DB_READ_PASSWORD'),
        'HOST': os.environ.get('DB_READ_HOST', 'localhost'),
        'PORT': os.environ.get('DB_READ_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
            'ssl': {
                'ca': '/etc/mysql/ssl/ca-cert.pem',
            },
        },
        'CONN_MAX_AGE': 3600,
    }
}

# Security Settings
DEBUG = False
ALLOWED_HOSTS = [
    'your-domain.com',
    'www.your-domain.com',
    'your-server-ip',
]

# SSL/HTTPS Settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/ecommerce.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'db_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/database.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['db_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

#### 3.2 Environment Variables
Create `.env.production` file:

```bash
# Database Configuration
DB_NAME=ecommerce_prod
DB_USER=ecommerce_app
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=3306
DB_READ_USER=ecommerce_read
DB_READ_PASSWORD=your_read_password_here
DB_READ_HOST=localhost
DB_READ_PORT=3306

# Django Settings
DJANGO_SETTINGS_MODULE=ecommerce_project.settings.production
SECRET_KEY=your_secret_key_here
DEBUG=False

# Security
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Backup Configuration
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key_here
BACKUP_STORAGE_PATH=/var/backups/mysql
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_ACCESS_KEY=your_s3_access_key
BACKUP_S3_SECRET_KEY=your_s3_secret_key
```

### Phase 4: Migration and Data Transfer

#### 4.1 Pre-Migration Backup
```bash
# Backup existing SQLite database
cp /path/to/your/db.sqlite3 /backup/location/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
```

#### 4.2 Run Django Migrations
```bash
# Set environment
export DJANGO_SETTINGS_MODULE=ecommerce_project.settings.production

# Run migrations
python manage.py migrate --database=default

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

#### 4.3 Data Migration (if needed)
```bash
# If migrating from SQLite, use the migration scripts created in previous tasks
python manage.py migrate_to_mysql --source=sqlite --target=mysql --verify
```

### Phase 5: Backup System Setup

#### 5.1 Create Backup Scripts
```bash
# Create backup directory
sudo mkdir -p /opt/mysql-backup/scripts
sudo mkdir -p /var/backups/mysql
sudo mkdir -p /var/log/mysql-backup
```

**Full Backup Script** (`/opt/mysql-backup/scripts/full_backup.sh`):
```bash
#!/bin/bash

# Configuration
DB_NAME="ecommerce_prod"
DB_USER="ecommerce_backup"
DB_PASSWORD="your_backup_password"
BACKUP_DIR="/var/backups/mysql"
LOG_FILE="/var/log/mysql-backup/backup.log"
RETENTION_DAYS=30
S3_BUCKET="your-backup-bucket"

# Create timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/full_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

log "Starting full backup"

# Create backup
mysqldump -u $DB_USER -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --hex-blob \
    --opt \
    $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    log "Database dump completed successfully"
    
    # Compress backup
    gzip $BACKUP_FILE
    log "Backup compressed: $COMPRESSED_FILE"
    
    # Upload to S3 (if configured)
    if [ ! -z "$S3_BUCKET" ]; then
        aws s3 cp $COMPRESSED_FILE s3://$S3_BUCKET/mysql-backups/
        log "Backup uploaded to S3"
    fi
    
    # Clean old backups
    find $BACKUP_DIR -name "full_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    log "Old backups cleaned up"
    
    log "Full backup completed successfully"
else
    log "ERROR: Database dump failed"
    exit 1
fi
```

**Incremental Backup Script** (`/opt/mysql-backup/scripts/incremental_backup.sh`):
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/mysql"
LOG_FILE="/var/log/mysql-backup/incremental.log"
BINLOG_DIR="/var/lib/mysql"
S3_BUCKET="your-backup-bucket"

# Create timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
INCREMENTAL_DIR="$BACKUP_DIR/incremental_$TIMESTAMP"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

log "Starting incremental backup"

# Create incremental backup directory
mkdir -p $INCREMENTAL_DIR

# Flush logs to create new binary log
mysql -u ecommerce_backup -pyour_backup_password -e "FLUSH LOGS;"

# Copy binary logs
cp $BINLOG_DIR/mysql-bin.* $INCREMENTAL_DIR/

# Compress incremental backup
tar -czf "$INCREMENTAL_DIR.tar.gz" -C $BACKUP_DIR "incremental_$TIMESTAMP"
rm -rf $INCREMENTAL_DIR

# Upload to S3 (if configured)
if [ ! -z "$S3_BUCKET" ]; then
    aws s3 cp "$INCREMENTAL_DIR.tar.gz" s3://$S3_BUCKET/mysql-backups/incremental/
    log "Incremental backup uploaded to S3"
fi

log "Incremental backup completed"
```

#### 5.2 Set Up Cron Jobs
```bash
# Edit crontab
sudo crontab -e

# Add backup schedules
# Full backup daily at 2 AM
0 2 * * * /opt/mysql-backup/scripts/full_backup.sh

# Incremental backup every 4 hours
0 */4 * * * /opt/mysql-backup/scripts/incremental_backup.sh
```

### Phase 6: Monitoring and Alerting

#### 6.1 Install Monitoring Tools
```bash
# Install Prometheus MySQL Exporter
wget https://github.com/prometheus/mysqld_exporter/releases/download/v0.14.0/mysqld_exporter-0.14.0.linux-amd64.tar.gz
tar xvf mysqld_exporter-0.14.0.linux-amd64.tar.gz
sudo mv mysqld_exporter-0.14.0.linux-amd64/mysqld_exporter /usr/local/bin/
```

#### 6.2 Configure Monitoring User
```sql
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'monitoring_password' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;
```

#### 6.3 Create Monitoring Configuration
```bash
# Create monitoring config
sudo mkdir -p /etc/mysqld_exporter
sudo tee /etc/mysqld_exporter/.my.cnf << EOF
[client]
user=exporter
password=monitoring_password
host=localhost
port=3306
EOF

sudo chmod 600 /etc/mysqld_exporter/.my.cnf
```

### Phase 7: Performance Optimization

#### 7.1 Create Indexes
```sql
-- Connect to production database
USE ecommerce_prod;

-- User table indexes
CREATE INDEX idx_users_email ON auth_user(email);
CREATE INDEX idx_users_active ON auth_user(is_active, date_joined);
CREATE INDEX idx_users_last_login ON auth_user(last_login);

-- Product table indexes (adjust based on your actual schema)
-- CREATE INDEX idx_products_category ON products_product(category_id, is_active);
-- CREATE INDEX idx_products_price ON products_product(price, is_active);
-- CREATE INDEX idx_products_search ON products_product(name, description);

-- Add more indexes based on your query patterns
```

#### 7.2 Optimize MySQL Configuration
```bash
# Run MySQL Tuner
wget http://mysqltuner.pl/ -O mysqltuner.pl
perl mysqltuner.pl

# Apply recommended optimizations to /etc/mysql/mysql.conf.d/mysqld.cnf
```

### Phase 8: Security Hardening

#### 8.1 Additional Security Measures
```bash
# Disable MySQL history
export MYSQL_HISTFILE=/dev/null

# Set secure file permissions
sudo chmod 600 /etc/mysql/mysql.conf.d/mysqld.cnf
sudo chown mysql:mysql /var/lib/mysql -R

# Configure log rotation
sudo tee /etc/logrotate.d/mysql << EOF
/var/log/mysql/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 mysql mysql
    postrotate
        /usr/bin/mysqladmin --defaults-file=/etc/mysql/debian.cnf flush-logs
    endscript
}
EOF
```

#### 8.2 Enable Audit Logging
```sql
-- Install audit plugin
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configure audit settings
SET GLOBAL audit_log_policy = 'ALL';
SET GLOBAL audit_log_format = 'JSON';
```

## Post-Deployment Validation

### 1. Connection Testing
```bash
# Test application database connection
python manage.py dbshell

# Test SSL connection
mysql -u ecommerce_app -p -h localhost --ssl-ca=/etc/mysql/ssl/ca-cert.pem
```

### 2. Performance Testing
```bash
# Run application tests
python manage.py test

# Run load testing (if available)
# locust -f load_test.py --host=https://your-domain.com
```

### 3. Backup Testing
```bash
# Test backup script
sudo /opt/mysql-backup/scripts/full_backup.sh

# Test restore procedure
# mysql -u root -p ecommerce_test < /var/backups/mysql/full_backup_TIMESTAMP.sql
```

### 4. Monitoring Validation
```bash
# Check MySQL status
sudo systemctl status mysql

# Check monitoring metrics
curl http://localhost:9104/metrics

# Check log files
tail -f /var/log/mysql/mysql.log
tail -f /var/log/django/ecommerce.log
```

## Rollback Procedures

### Emergency Rollback to SQLite
If critical issues occur, follow these steps:

1. **Stop Application**
   ```bash
   sudo systemctl stop your-app-service
   ```

2. **Switch Database Configuration**
   ```bash
   # Update environment variables to use SQLite
   export DJANGO_SETTINGS_MODULE=ecommerce_project.settings.development
   ```

3. **Restore SQLite Database**
   ```bash
   cp /backup/location/db.sqlite3.backup.TIMESTAMP /path/to/your/db.sqlite3
   ```

4. **Restart Application**
   ```bash
   sudo systemctl start your-app-service
   ```

### Partial Rollback (Read-Only Mode)
```python
# Temporarily disable writes in Django settings
DATABASES['default']['OPTIONS']['read_only'] = True
```

## Maintenance Procedures

### Daily Tasks
- [ ] Check backup completion
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Check connection pool status

### Weekly Tasks
- [ ] Review slow query log
- [ ] Analyze performance metrics
- [ ] Update security patches
- [ ] Test backup restoration

### Monthly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Capacity planning assessment
- [ ] Disaster recovery testing

## Troubleshooting Guide

### Common Issues

#### Connection Refused
```bash
# Check MySQL status
sudo systemctl status mysql

# Check port binding
sudo netstat -tlnp | grep 3306

# Check firewall
sudo ufw status
```

#### SSL Connection Issues
```bash
# Verify SSL certificates
openssl x509 -in /etc/mysql/ssl/server-cert.pem -text -noout

# Test SSL connection
mysql --ssl-ca=/etc/mysql/ssl/ca-cert.pem -h localhost -u root -p
```

#### Performance Issues
```bash
# Check slow queries
sudo tail -f /var/log/mysql/mysql-slow.log

# Monitor connections
mysql -u root -p -e "SHOW PROCESSLIST;"

# Check buffer pool usage
mysql -u root -p -e "SHOW ENGINE INNODB STATUS\G" | grep -A 20 "BUFFER POOL"
```

## Support and Documentation

### Log Locations
- MySQL Error Log: `/var/log/mysql/error.log`
- MySQL Slow Query Log: `/var/log/mysql/mysql-slow.log`
- Django Application Log: `/var/log/django/ecommerce.log`
- Backup Logs: `/var/log/mysql-backup/`

### Configuration Files
- MySQL Configuration: `/etc/mysql/mysql.conf.d/mysqld.cnf`
- Django Settings: `settings/production.py`
- Environment Variables: `.env.production`

### Monitoring Endpoints
- MySQL Metrics: `http://localhost:9104/metrics`
- Application Health: `https://your-domain.com/health/`
- Admin Interface: `https://your-domain.com/admin/`

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-31  
**Next Review**: 2025-08-31