#!/bin/bash

# MySQL Production Setup Script
# This script sets up MySQL server with production-ready configuration

set -e

# Configuration variables
MYSQL_VERSION=${MYSQL_VERSION:-8.0}
DB_NAME=${DB_NAME:-ecommerce_db}
DB_USER=${DB_USER:-ecommerce_user}
DB_PASSWORD=${DB_PASSWORD}
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
ENVIRONMENT=${ENVIRONMENT:-production}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Validate required environment variables
validate_env() {
    if [[ -z "$DB_PASSWORD" ]]; then
        log_error "DB_PASSWORD environment variable is required"
        exit 1
    fi
    
    if [[ -z "$DB_ROOT_PASSWORD" ]]; then
        log_error "DB_ROOT_PASSWORD environment variable is required"
        exit 1
    fi
}

# Install MySQL server
install_mysql() {
    log_info "Installing MySQL ${MYSQL_VERSION}..."
    
    # Update package list
    apt-get update
    
    # Install MySQL server
    DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server-${MYSQL_VERSION}
    
    # Start and enable MySQL service
    systemctl start mysql
    systemctl enable mysql
    
    log_info "MySQL installation completed"
}

# Configure MySQL for production
configure_mysql() {
    log_info "Configuring MySQL for production..."
    
    # Create production configuration
    cat > /etc/mysql/mysql.conf.d/production.cnf << EOF
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
skip-external-locking

# Performance Settings
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
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

# Query Cache (if using MySQL < 8.0)
query_cache_type = 0
query_cache_size = 0

# Logging
general_log = 0
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
log_queries_not_using_indexes = 1

# Security Settings
local_infile = 0
skip_show_database

# SSL Configuration
ssl-ca = /etc/mysql/ssl/ca-cert.pem
ssl-cert = /etc/mysql/ssl/server-cert.pem
ssl-key = /etc/mysql/ssl/server-key.pem
require_secure_transport = ON

# Binary Logging for Replication
server-id = 1
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

    log_info "MySQL configuration created"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    mkdir -p /etc/mysql/ssl
    cd /etc/mysql/ssl
    
    # Generate CA private key
    openssl genrsa 2048 > ca-key.pem
    
    # Generate CA certificate
    openssl req -new -x509 -nodes -days 3600 -key ca-key.pem -out ca-cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=MySQL-CA"
    
    # Generate server private key
    openssl req -newkey rsa:2048 -days 3600 -nodes -keyout server-key.pem -out server-req.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=MySQL-Server"
    
    # Generate server certificate
    openssl rsa -in server-key.pem -out server-key.pem
    openssl x509 -req -in server-req.pem -days 3600 -CA ca-cert.pem -CAkey ca-key.pem -set_serial 01 -out server-cert.pem
    
    # Generate client private key
    openssl req -newkey rsa:2048 -days 3600 -nodes -keyout client-key.pem -out client-req.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=MySQL-Client"
    
    # Generate client certificate
    openssl rsa -in client-key.pem -out client-key.pem
    openssl x509 -req -in client-req.pem -days 3600 -CA ca-cert.pem -CAkey ca-key.pem -set_serial 01 -out client-cert.pem
    
    # Set proper permissions
    chown -R mysql:mysql /etc/mysql/ssl
    chmod 600 /etc/mysql/ssl/*-key.pem
    chmod 644 /etc/mysql/ssl/*-cert.pem
    
    # Clean up temporary files
    rm server-req.pem client-req.pem
    
    log_info "SSL certificates generated and configured"
}

# Secure MySQL installation
secure_mysql() {
    log_info "Securing MySQL installation..."
    
    # Set root password and secure installation
    mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASSWORD}';"
    mysql -u root -p${DB_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='';"
    mysql -u root -p${DB_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
    mysql -u root -p${DB_ROOT_PASSWORD} -e "DROP DATABASE IF EXISTS test;"
    mysql -u root -p${DB_ROOT_PASSWORD} -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
    mysql -u root -p${DB_ROOT_PASSWORD} -e "FLUSH PRIVILEGES;"
    
    log_info "MySQL installation secured"
}

# Create application database and user
create_database() {
    log_info "Creating application database and user..."
    
    mysql -u root -p${DB_ROOT_PASSWORD} << EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';

-- Create read-only user for replicas
CREATE USER IF NOT EXISTS '${DB_USER}_read'@'localhost' IDENTIFIED BY '${DB_PASSWORD}_read';
CREATE USER IF NOT EXISTS '${DB_USER}_read'@'%' IDENTIFIED BY '${DB_PASSWORD}_read';
GRANT SELECT ON ${DB_NAME}.* TO '${DB_USER}_read'@'localhost';
GRANT SELECT ON ${DB_NAME}.* TO '${DB_USER}_read'@'%';

-- Create replication user
CREATE USER IF NOT EXISTS 'replication'@'%' IDENTIFIED BY '${DB_PASSWORD}_repl';
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%';

FLUSH PRIVILEGES;
EOF

    log_info "Database and users created successfully"
}

# Setup firewall rules
setup_firewall() {
    log_info "Configuring firewall rules..."
    
    # Allow MySQL port (3306) from specific networks only
    ufw allow from 10.0.0.0/8 to any port 3306
    ufw allow from 172.16.0.0/12 to any port 3306
    ufw allow from 192.168.0.0/16 to any port 3306
    
    # Enable firewall if not already enabled
    ufw --force enable
    
    log_info "Firewall rules configured"
}

# Setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/mysql-server << EOF
/var/log/mysql/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 mysql adm
    sharedscripts
    postrotate
        if test -x /usr/bin/mysqladmin && \
           /usr/bin/mysqladmin ping &>/dev/null
        then
           /usr/bin/mysqladmin flush-logs
        fi
    endscript
}
EOF

    log_info "Log rotation configured"
}

# Main execution
main() {
    log_info "Starting MySQL production setup..."
    
    check_root
    validate_env
    install_mysql
    configure_mysql
    setup_ssl
    
    # Restart MySQL to apply configuration
    systemctl restart mysql
    
    secure_mysql
    create_database
    setup_firewall
    setup_log_rotation
    
    log_info "MySQL production setup completed successfully!"
    log_info "Database: ${DB_NAME}"
    log_info "User: ${DB_USER}"
    log_info "SSL certificates location: /etc/mysql/ssl/"
    
    # Display connection test
    log_info "Testing database connection..."
    mysql -u ${DB_USER} -p${DB_PASSWORD} -e "SELECT 'Connection successful!' as status;"
}

# Run main function
main "$@"