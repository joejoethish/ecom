#!/bin/bash

# MySQL Production Deployment Rollback Script
# This script provides rollback procedures for MySQL deployment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="/var/log/mysql-rollback.log"
BACKUP_DIR="/var/backups/mysql-deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
    
    case $level in
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${message}" >&2
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} ${message}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} ${message}"
            ;;
        "INFO")
            echo -e "${BLUE}[INFO]${NC} ${message}"
            ;;
    esac
}

# Error handler
error_exit() {
    log "ERROR" "Rollback failed: $1"
    log "ERROR" "Check the log file at $LOG_FILE for details"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root (use sudo)"
    fi
}

# Show rollback options
show_rollback_options() {
    echo "MySQL Deployment Rollback Options:"
    echo
    echo "1. Complete rollback to SQLite"
    echo "2. Rollback MySQL configuration only"
    echo "3. Rollback database users only"
    echo "4. Rollback backup configuration only"
    echo "5. Emergency read-only mode"
    echo "6. Cancel rollback"
    echo
    read -p "Select rollback option (1-6): " ROLLBACK_OPTION
}

# Backup current state before rollback
backup_current_state() {
    log "INFO" "Backing up current state before rollback..."
    
    local rollback_backup_dir="/var/backups/rollback-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$rollback_backup_dir"
    
    # Backup MySQL configuration
    if [[ -f /etc/mysql/mysql.conf.d/mysqld.cnf ]]; then
        cp /etc/mysql/mysql.conf.d/mysqld.cnf "$rollback_backup_dir/mysqld.cnf"
    fi
    
    # Backup SSL certificates
    if [[ -d /etc/mysql/ssl ]]; then
        cp -r /etc/mysql/ssl "$rollback_backup_dir/"
    fi
    
    # Backup database (if possible)
    if systemctl is-active --quiet mysql; then
        mysqldump --all-databases > "$rollback_backup_dir/all_databases.sql" 2>/dev/null || true
    fi
    
    # Backup cron jobs
    crontab -l > "$rollback_backup_dir/crontab.backup" 2>/dev/null || true
    
    log "SUCCESS" "Current state backed up to $rollback_backup_dir"
}

# Complete rollback to SQLite
complete_rollback_to_sqlite() {
    log "INFO" "Starting complete rollback to SQLite..."
    
    # Stop application services
    log "INFO" "Stopping application services..."
    systemctl stop nginx 2>/dev/null || true
    systemctl stop gunicorn 2>/dev/null || true
    systemctl stop celery 2>/dev/null || true
    
    # Stop MySQL
    log "INFO" "Stopping MySQL service..."
    systemctl stop mysql
    systemctl disable mysql
    
    # Restore SQLite database if backup exists
    if [[ -f "$BACKUP_DIR/db.sqlite3.backup" ]]; then
        log "INFO" "Restoring SQLite database..."
        cp "$BACKUP_DIR/db.sqlite3.backup" "$PROJECT_ROOT/db.sqlite3"
        chown www-data:www-data "$PROJECT_ROOT/db.sqlite3"
    else
        log "WARNING" "SQLite backup not found. You may need to restore from another backup."
    fi
    
    # Update Django settings to use SQLite
    log "INFO" "Updating Django settings..."
    cd "$PROJECT_ROOT"
    
    # Create rollback settings file
    cat > settings/rollback.py << 'EOF'
from .base import *

# Use SQLite database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable SSL requirements
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Enable debug for troubleshooting
DEBUG = True
ALLOWED_HOSTS = ['*']
EOF
    
    # Update environment to use rollback settings
    export DJANGO_SETTINGS_MODULE=ecommerce_project.settings.rollback
    
    # Run migrations on SQLite
    if [[ -f "manage.py" ]]; then
        python3 manage.py migrate 2>/dev/null || true
    fi
    
    # Remove MySQL-related cron jobs
    crontab -l | grep -v "mysql-backup" | crontab - 2>/dev/null || true
    
    # Start application services
    systemctl start nginx 2>/dev/null || true
    systemctl start gunicorn 2>/dev/null || true
    
    log "SUCCESS" "Complete rollback to SQLite completed"
}

# Rollback MySQL configuration only
rollback_mysql_configuration() {
    log "INFO" "Rolling back MySQL configuration..."
    
    # Stop MySQL
    systemctl stop mysql
    
    # Restore original MySQL configuration
    if [[ -f /etc/mysql/mysql.conf.d/mysqld.cnf.backup ]]; then
        cp /etc/mysql/mysql.conf.d/mysqld.cnf.backup /etc/mysql/mysql.conf.d/mysqld.cnf
        log "SUCCESS" "MySQL configuration restored from backup"
    else
        # Use default configuration
        cat > /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'
[mysqld]
user = mysql
pid-file = /var/run/mysqld/mysqld.pid
socket = /var/run/mysqld/mysqld.sock
port = 3306
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
skip-external-locking
bind-address = 127.0.0.1
key_buffer_size = 16M
max_allowed_packet = 16M
thread_stack = 192K
thread_cache_size = 8
myisam_recover_options = BACKUP
query_cache_limit = 1M
query_cache_size = 16M
log_error = /var/log/mysql/error.log
expire_logs_days = 10
max_binlog_size = 100M
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
EOF
        log "SUCCESS" "MySQL configuration reset to default"
    fi
    
    # Remove SSL certificates
    rm -rf /etc/mysql/ssl 2>/dev/null || true
    
    # Start MySQL
    systemctl start mysql
    
    log "SUCCESS" "MySQL configuration rollback completed"
}

# Rollback database users only
rollback_database_users() {
    log "INFO" "Rolling back database users..."
    
    # Prompt for root password
    read -s -p "Enter MySQL root password: " MYSQL_ROOT_PASSWORD
    echo
    
    # Remove created users
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << 'EOF'
DROP USER IF EXISTS 'ecommerce_app'@'%';
DROP USER IF EXISTS 'ecommerce_read'@'%';
DROP USER IF EXISTS 'ecommerce_backup'@'localhost';
DROP USER IF EXISTS 'exporter'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    if [[ $? -eq 0 ]]; then
        log "SUCCESS" "Database users removed successfully"
    else
        log "ERROR" "Failed to remove database users"
    fi
}

# Rollback backup configuration
rollback_backup_configuration() {
    log "INFO" "Rolling back backup configuration..."
    
    # Remove backup scripts
    rm -rf /opt/mysql-backup 2>/dev/null || true
    
    # Remove backup directories
    rm -rf /var/backups/mysql 2>/dev/null || true
    rm -rf /var/log/mysql-backup 2>/dev/null || true
    
    # Remove backup cron jobs
    crontab -l | grep -v "mysql-backup" | crontab - 2>/dev/null || true
    
    # Remove log rotation configuration
    rm -f /etc/logrotate.d/mysql-ecommerce 2>/dev/null || true
    
    log "SUCCESS" "Backup configuration rollback completed"
}

# Enable emergency read-only mode
enable_emergency_readonly() {
    log "INFO" "Enabling emergency read-only mode..."
    
    # Set MySQL to read-only
    mysql -u root -e "SET GLOBAL read_only = ON;" 2>/dev/null || true
    mysql -u root -e "SET GLOBAL super_read_only = ON;" 2>/dev/null || true
    
    # Update Django settings for read-only mode
    cd "$PROJECT_ROOT"
    
    cat > settings/emergency.py << 'EOF'
from .production import *

# Enable read-only mode
class ReadOnlyRouter:
    def db_for_read(self, model, **hints):
        return 'default'
    
    def db_for_write(self, model, **hints):
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False

DATABASE_ROUTERS = ['settings.emergency.ReadOnlyRouter']

# Disable admin writes
ADMIN_ENABLED = False
EOF
    
    # Create maintenance page
    cat > /var/www/html/maintenance.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Maintenance Mode</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        .container { max-width: 600px; margin: 0 auto; }
        .message { background: #f0f0f0; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="message">
            <h1>System Maintenance</h1>
            <p>The system is currently in read-only mode due to maintenance.</p>
            <p>We apologize for any inconvenience. Please try again later.</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log "SUCCESS" "Emergency read-only mode enabled"
}

# Validate rollback
validate_rollback() {
    log "INFO" "Validating rollback..."
    
    case $ROLLBACK_OPTION in
        1)
            # Validate SQLite rollback
            if [[ -f "$PROJECT_ROOT/db.sqlite3" ]]; then
                log "SUCCESS" "SQLite database file exists"
            else
                log "ERROR" "SQLite database file not found"
            fi
            ;;
        2)
            # Validate MySQL configuration rollback
            if systemctl is-active --quiet mysql; then
                log "SUCCESS" "MySQL service is running"
            else
                log "ERROR" "MySQL service is not running"
            fi
            ;;
        5)
            # Validate read-only mode
            if mysql -u root -e "SHOW VARIABLES LIKE 'read_only';" | grep -q "ON"; then
                log "SUCCESS" "Read-only mode is enabled"
            else
                log "WARNING" "Read-only mode may not be properly enabled"
            fi
            ;;
    esac
}

# Main rollback function
main() {
    log "INFO" "Starting MySQL deployment rollback..."
    log "INFO" "Rollback started at $(date)"
    
    check_root
    
    # Show warning
    echo -e "${RED}WARNING: This will rollback your MySQL deployment!${NC}"
    echo "This action may result in data loss or service interruption."
    echo
    read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
    
    if [[ "$CONFIRM" != "yes" ]]; then
        log "INFO" "Rollback cancelled by user"
        exit 0
    fi
    
    # Show rollback options
    show_rollback_options
    
    # Backup current state
    backup_current_state
    
    # Execute rollback based on selection
    case $ROLLBACK_OPTION in
        1)
            complete_rollback_to_sqlite
            ;;
        2)
            rollback_mysql_configuration
            ;;
        3)
            rollback_database_users
            ;;
        4)
            rollback_backup_configuration
            ;;
        5)
            enable_emergency_readonly
            ;;
        6)
            log "INFO" "Rollback cancelled by user"
            exit 0
            ;;
        *)
            error_exit "Invalid rollback option selected"
            ;;
    esac
    
    # Validate rollback
    validate_rollback
    
    log "SUCCESS" "Rollback completed successfully!"
    log "INFO" "Rollback finished at $(date)"
    
    echo
    echo "=================================="
    echo "ROLLBACK COMPLETED"
    echo "=================================="
    echo
    echo "Please verify that your application is working correctly."
    echo "Check the application logs and test critical functionality."
    echo
    echo "If you need to restore from the pre-rollback backup, check:"
    echo "/var/backups/rollback-*/"
    echo
}

# Show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo
    echo "This script provides rollback procedures for MySQL deployment."
    echo "It offers various rollback options depending on the issue."
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            set -x
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"