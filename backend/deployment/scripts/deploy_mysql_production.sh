#!/bin/bash

# MySQL Production Deployment Script
# This script automates the deployment of MySQL database integration to production

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="/var/log/mysql-deployment.log"
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
    log "ERROR" "Deployment failed: $1"
    log "ERROR" "Check the log file at $LOG_FILE for details"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root (use sudo)"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if MySQL is installed
    if ! command -v mysql &> /dev/null; then
        error_exit "MySQL is not installed. Please install MySQL 8.0+ first."
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is not installed."
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        error_exit "pip3 is not installed."
    fi
    
    # Check if Django project exists
    if [[ ! -f "$PROJECT_ROOT/manage.py" ]]; then
        error_exit "Django project not found at $PROJECT_ROOT"
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log "INFO" "Creating necessary directories..."
    
    mkdir -p /var/log/django
    mkdir -p /var/log/mysql-backup
    mkdir -p /var/backups/mysql
    mkdir -p /opt/mysql-backup/scripts
    mkdir -p /etc/mysql/ssl
    
    # Set permissions
    chown mysql:mysql /var/log/mysql-backup
    chown mysql:mysql /var/backups/mysql
    chown www-data:www-data /var/log/django
    
    log "SUCCESS" "Directories created successfully"
}

# Install required packages
install_packages() {
    log "INFO" "Installing required packages..."
    
    # Update package list
    apt update
    
    # Install required packages
    apt install -y \
        mysql-client \
        python3-dev \
        python3-pip \
        python3-venv \
        libmysqlclient-dev \
        pkg-config \
        openssl \
        awscli \
        logrotate
    
    log "SUCCESS" "Required packages installed"
}

# Configure MySQL for production
configure_mysql() {
    log "INFO" "Configuring MySQL for production..."
    
    # Backup original configuration
    if [[ -f /etc/mysql/mysql.conf.d/mysqld.cnf ]]; then
        cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copy production configuration
    cat > /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'
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
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
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

# Query Cache
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

# Binary Logging
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
EOF
    
    log "SUCCESS" "MySQL configuration updated"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "INFO" "Generating SSL certificates..."
    
    cd /etc/mysql/ssl
    
    # Generate CA key and certificate
    openssl genrsa 2048 > ca-key.pem
    openssl req -new -x509 -nodes -days 3600 -key ca-key.pem -out ca-cert.pem -subj "/C=US/ST=State/L=City/O=Organization/CN=MySQL-CA"
    
    # Generate server key and certificate
    openssl req -newkey rsa:2048 -days 3600 -nodes -keyout server-key.pem -out server-req.pem -subj "/C=US/ST=State/L=City/O=Organization/CN=MySQL-Server"
    openssl rsa -in server-key.pem -out server-key.pem
    openssl x509 -req -in server-req.pem -days 3600 -CA ca-cert.pem -CAkey ca-key.pem -set_serial 01 -out server-cert.pem
    
    # Generate client certificates
    openssl req -newkey rsa:2048 -days 3600 -nodes -keyout client-key.pem -out client-req.pem -subj "/C=US/ST=State/L=City/O=Organization/CN=MySQL-Client"
    openssl rsa -in client-key.pem -out client-key.pem
    openssl x509 -req -in client-req.pem -days 3600 -CA ca-cert.pem -CAkey ca-key.pem -set_serial 02 -out client-cert.pem
    
    # Set permissions
    chown mysql:mysql /etc/mysql/ssl/*
    chmod 600 /etc/mysql/ssl/*-key.pem
    chmod 644 /etc/mysql/ssl/*-cert.pem
    
    # Clean up temporary files
    rm -f server-req.pem client-req.pem
    
    log "SUCCESS" "SSL certificates generated"
}

# Restart MySQL service
restart_mysql() {
    log "INFO" "Restarting MySQL service..."
    
    systemctl restart mysql
    systemctl enable mysql
    
    # Wait for MySQL to start
    sleep 5
    
    # Verify MySQL is running
    if ! systemctl is-active --quiet mysql; then
        error_exit "MySQL failed to start. Check /var/log/mysql/error.log"
    fi
    
    log "SUCCESS" "MySQL service restarted successfully"
}

# Create database and users
create_database_and_users() {
    log "INFO" "Creating database and users..."
    
    # Prompt for root password if not provided
    if [[ -z "$MYSQL_ROOT_PASSWORD" ]]; then
        read -s -p "Enter MySQL root password: " MYSQL_ROOT_PASSWORD
        echo
    fi
    
    # Prompt for application passwords
    if [[ -z "$APP_DB_PASSWORD" ]]; then
        read -s -p "Enter password for application database user: " APP_DB_PASSWORD
        echo
    fi
    
    if [[ -z "$READ_DB_PASSWORD" ]]; then
        read -s -p "Enter password for read-only database user: " READ_DB_PASSWORD
        echo
    fi
    
    if [[ -z "$BACKUP_DB_PASSWORD" ]]; then
        read -s -p "Enter password for backup database user: " BACKUP_DB_PASSWORD
        echo
    fi
    
    # Create database and users
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- Create database
CREATE DATABASE IF NOT EXISTS ecommerce_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create application user
CREATE USER IF NOT EXISTS 'ecommerce_app'@'%' IDENTIFIED BY '$APP_DB_PASSWORD' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE, DELETE ON ecommerce_prod.* TO 'ecommerce_app'@'%';

-- Create read-only user
CREATE USER IF NOT EXISTS 'ecommerce_read'@'%' IDENTIFIED BY '$READ_DB_PASSWORD' REQUIRE SSL;
GRANT SELECT ON ecommerce_prod.* TO 'ecommerce_read'@'%';

-- Create backup user
CREATE USER IF NOT EXISTS 'ecommerce_backup'@'localhost' IDENTIFIED BY '$BACKUP_DB_PASSWORD';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON ecommerce_prod.* TO 'ecommerce_backup'@'localhost';

-- Create monitoring user
CREATE USER IF NOT EXISTS 'exporter'@'localhost' IDENTIFIED BY 'monitoring_password' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;
EOF
    
    if [[ $? -eq 0 ]]; then
        log "SUCCESS" "Database and users created successfully"
    else
        error_exit "Failed to create database and users"
    fi
}

# Install Python dependencies
install_python_dependencies() {
    log "INFO" "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install MySQL client
    pip install mysqlclient
    
    # Install other requirements if requirements.txt exists
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    log "SUCCESS" "Python dependencies installed"
}

# Run Django migrations
run_migrations() {
    log "INFO" "Running Django migrations..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # Set environment variables
    export DJANGO_SETTINGS_MODULE=ecommerce_project.settings.production
    export DB_NAME=ecommerce_prod
    export DB_USER=ecommerce_app
    export DB_PASSWORD="$APP_DB_PASSWORD"
    export DB_HOST=localhost
    export DB_PORT=3306
    
    # Run migrations
    python manage.py migrate --database=default
    
    if [[ $? -eq 0 ]]; then
        log "SUCCESS" "Django migrations completed"
    else
        error_exit "Django migrations failed"
    fi
}

# Create backup scripts
create_backup_scripts() {
    log "INFO" "Creating backup scripts..."
    
    # Full backup script
    cat > /opt/mysql-backup/scripts/full_backup.sh << EOF
#!/bin/bash

# Configuration
DB_NAME="ecommerce_prod"
DB_USER="ecommerce_backup"
DB_PASSWORD="$BACKUP_DB_PASSWORD"
BACKUP_DIR="/var/backups/mysql"
LOG_FILE="/var/log/mysql-backup/backup.log"
RETENTION_DAYS=30

# Create timestamp
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="\$BACKUP_DIR/full_backup_\${TIMESTAMP}.sql"
COMPRESSED_FILE="\$BACKUP_FILE.gz"

# Log function
log() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> \$LOG_FILE
}

log "Starting full backup"

# Create backup
mysqldump -u \$DB_USER -p\$DB_PASSWORD \\
    --single-transaction \\
    --routines \\
    --triggers \\
    --events \\
    --hex-blob \\
    --opt \\
    \$DB_NAME > \$BACKUP_FILE

if [ \$? -eq 0 ]; then
    log "Database dump completed successfully"
    
    # Compress backup
    gzip \$BACKUP_FILE
    log "Backup compressed: \$COMPRESSED_FILE"
    
    # Clean old backups
    find \$BACKUP_DIR -name "full_backup_*.sql.gz" -mtime +\$RETENTION_DAYS -delete
    log "Old backups cleaned up"
    
    log "Full backup completed successfully"
else
    log "ERROR: Database dump failed"
    exit 1
fi
EOF
    
    # Make backup script executable
    chmod +x /opt/mysql-backup/scripts/full_backup.sh
    chown mysql:mysql /opt/mysql-backup/scripts/full_backup.sh
    
    log "SUCCESS" "Backup scripts created"
}

# Setup cron jobs
setup_cron_jobs() {
    log "INFO" "Setting up cron jobs..."
    
    # Add backup cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/mysql-backup/scripts/full_backup.sh") | crontab -
    
    log "SUCCESS" "Cron jobs configured"
}

# Configure log rotation
configure_log_rotation() {
    log "INFO" "Configuring log rotation..."
    
    cat > /etc/logrotate.d/mysql-ecommerce << 'EOF'
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

/var/log/django/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}

/var/log/mysql-backup/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 644 mysql mysql
}
EOF
    
    log "SUCCESS" "Log rotation configured"
}

# Perform final validation
final_validation() {
    log "INFO" "Performing final validation..."
    
    # Test MySQL connection
    if mysql -u ecommerce_app -p"$APP_DB_PASSWORD" -e "SELECT 1;" ecommerce_prod &>/dev/null; then
        log "SUCCESS" "Application database connection test passed"
    else
        log "ERROR" "Application database connection test failed"
    fi
    
    # Test SSL connection
    if mysql -u ecommerce_app -p"$APP_DB_PASSWORD" --ssl-ca=/etc/mysql/ssl/ca-cert.pem -e "SHOW STATUS LIKE 'Ssl_cipher';" ecommerce_prod | grep -q "AES"; then
        log "SUCCESS" "SSL connection test passed"
    else
        log "WARNING" "SSL connection test failed or not using strong cipher"
    fi
    
    # Test backup script
    if /opt/mysql-backup/scripts/full_backup.sh; then
        log "SUCCESS" "Backup script test passed"
    else
        log "ERROR" "Backup script test failed"
    fi
    
    log "SUCCESS" "Final validation completed"
}

# Main deployment function
main() {
    log "INFO" "Starting MySQL production deployment..."
    log "INFO" "Deployment started at $(date)"
    
    # Create backup directory for this deployment
    mkdir -p "$BACKUP_DIR"
    
    # Run deployment steps
    check_root
    check_prerequisites
    create_directories
    install_packages
    configure_mysql
    generate_ssl_certificates
    restart_mysql
    create_database_and_users
    install_python_dependencies
    run_migrations
    create_backup_scripts
    setup_cron_jobs
    configure_log_rotation
    final_validation
    
    log "SUCCESS" "MySQL production deployment completed successfully!"
    log "INFO" "Deployment finished at $(date)"
    
    echo
    echo "==================================="
    echo "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "==================================="
    echo
    echo "Next steps:"
    echo "1. Update your application's environment variables with the database credentials"
    echo "2. Configure your web server (Nginx/Apache) to serve the application"
    echo "3. Set up monitoring and alerting"
    echo "4. Test the application thoroughly"
    echo
    echo "Important files:"
    echo "- MySQL config: /etc/mysql/mysql.conf.d/mysqld.cnf"
    echo "- SSL certificates: /etc/mysql/ssl/"
    echo "- Backup scripts: /opt/mysql-backup/scripts/"
    echo "- Log files: /var/log/mysql-deployment.log"
    echo
    echo "Database credentials:"
    echo "- Database: ecommerce_prod"
    echo "- App user: ecommerce_app"
    echo "- Read user: ecommerce_read"
    echo "- Backup user: ecommerce_backup"
    echo
}

# Run main function
main "$@"