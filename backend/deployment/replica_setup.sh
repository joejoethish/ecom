#!/bin/bash

# MySQL Read Replica Setup Script
# This script sets up MySQL read replicas for load distribution

set -e

# Configuration variables
MASTER_HOST=${MASTER_HOST}
MASTER_USER=${MASTER_USER:-replication}
MASTER_PASSWORD=${MASTER_PASSWORD}
REPLICA_ID=${REPLICA_ID:-2}
DB_NAME=${DB_NAME:-ecommerce_db}

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

# Validate required environment variables
validate_env() {
    if [[ -z "$MASTER_HOST" ]]; then
        log_error "MASTER_HOST environment variable is required"
        exit 1
    fi
    
    if [[ -z "$MASTER_PASSWORD" ]]; then
        log_error "MASTER_PASSWORD environment variable is required"
        exit 1
    fi
}

# Configure replica-specific settings
configure_replica() {
    log_info "Configuring MySQL replica settings..."
    
    # Create replica-specific configuration
    cat > /etc/mysql/mysql.conf.d/replica.cnf << EOF
[mysqld]
# Replica-specific settings
server-id = ${REPLICA_ID}
read_only = 1
super_read_only = 1

# Relay log settings
relay-log = mysql-relay-bin
relay-log-index = mysql-relay-bin.index
relay_log_purge = 1
relay_log_recovery = 1

# Replication settings
slave_skip_errors = 1062,1053,1146
slave_net_timeout = 60
slave_compressed_protocol = 1

# Performance settings for read replica
innodb_buffer_pool_size = 1G
innodb_flush_log_at_trx_commit = 0
sync_binlog = 0

# Disable binary logging on replica (optional)
# log-bin = 
# binlog_format = 
EOF

    log_info "Replica configuration created"
}

# Setup replication
setup_replication() {
    log_info "Setting up replication from master ${MASTER_HOST}..."
    
    # Stop slave if running
    mysql -e "STOP SLAVE;" 2>/dev/null || true
    
    # Get master status
    log_info "Getting master binary log position..."
    MASTER_STATUS=$(mysql -h ${MASTER_HOST} -u ${MASTER_USER} -p${MASTER_PASSWORD} -e "SHOW MASTER STATUS\G")
    MASTER_LOG_FILE=$(echo "$MASTER_STATUS" | grep "File:" | awk '{print $2}')
    MASTER_LOG_POS=$(echo "$MASTER_STATUS" | grep "Position:" | awk '{print $2}')
    
    log_info "Master log file: ${MASTER_LOG_FILE}"
    log_info "Master log position: ${MASTER_LOG_POS}"
    
    # Configure slave
    mysql << EOF
CHANGE MASTER TO
    MASTER_HOST='${MASTER_HOST}',
    MASTER_USER='${MASTER_USER}',
    MASTER_PASSWORD='${MASTER_PASSWORD}',
    MASTER_LOG_FILE='${MASTER_LOG_FILE}',
    MASTER_LOG_POS=${MASTER_LOG_POS},
    MASTER_SSL=1,
    MASTER_SSL_VERIFY_SERVER_CERT=0;
EOF

    # Start slave
    mysql -e "START SLAVE;"
    
    # Check slave status
    sleep 5
    SLAVE_STATUS=$(mysql -e "SHOW SLAVE STATUS\G")
    
    if echo "$SLAVE_STATUS" | grep -q "Slave_IO_Running: Yes" && echo "$SLAVE_STATUS" | grep -q "Slave_SQL_Running: Yes"; then
        log_info "Replication started successfully"
    else
        log_error "Replication failed to start"
        echo "$SLAVE_STATUS"
        exit 1
    fi
}

# Create monitoring user for replica
create_monitoring_user() {
    log_info "Creating monitoring user for replica..."
    
    mysql << EOF
CREATE USER IF NOT EXISTS 'monitor'@'localhost' IDENTIFIED BY 'monitor_password';
GRANT REPLICATION CLIENT ON *.* TO 'monitor'@'localhost';
GRANT PROCESS ON *.* TO 'monitor'@'localhost';
GRANT SELECT ON performance_schema.* TO 'monitor'@'localhost';
FLUSH PRIVILEGES;
EOF

    log_info "Monitoring user created"
}

# Setup replica monitoring script
setup_monitoring() {
    log_info "Setting up replica monitoring..."
    
    cat > /usr/local/bin/check_replica_health.sh << 'EOF'
#!/bin/bash

# MySQL Replica Health Check Script

MYSQL_USER="monitor"
MYSQL_PASSWORD="monitor_password"
LAG_THRESHOLD=300  # 5 minutes in seconds
ERROR_LOG="/var/log/mysql/replica_health.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $ERROR_LOG
}

# Check if MySQL is running
if ! systemctl is-active --quiet mysql; then
    log_message "ERROR: MySQL service is not running"
    exit 1
fi

# Get slave status
SLAVE_STATUS=$(mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SHOW SLAVE STATUS\G" 2>/dev/null)

if [ $? -ne 0 ]; then
    log_message "ERROR: Unable to connect to MySQL or get slave status"
    exit 1
fi

# Check if replication is running
IO_RUNNING=$(echo "$SLAVE_STATUS" | grep "Slave_IO_Running:" | awk '{print $2}')
SQL_RUNNING=$(echo "$SLAVE_STATUS" | grep "Slave_SQL_Running:" | awk '{print $2}')

if [ "$IO_RUNNING" != "Yes" ] || [ "$SQL_RUNNING" != "Yes" ]; then
    log_message "ERROR: Replication is not running - IO: $IO_RUNNING, SQL: $SQL_RUNNING"
    
    # Try to restart replication
    mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "STOP SLAVE; START SLAVE;" 2>/dev/null
    log_message "INFO: Attempted to restart replication"
    exit 1
fi

# Check replication lag
SECONDS_BEHIND=$(echo "$SLAVE_STATUS" | grep "Seconds_Behind_Master:" | awk '{print $2}')

if [ "$SECONDS_BEHIND" != "NULL" ] && [ "$SECONDS_BEHIND" -gt "$LAG_THRESHOLD" ]; then
    log_message "WARNING: Replication lag is $SECONDS_BEHIND seconds (threshold: $LAG_THRESHOLD)"
    exit 1
fi

# Check for replication errors
LAST_ERROR=$(echo "$SLAVE_STATUS" | grep "Last_Error:" | cut -d' ' -f2-)
if [ -n "$LAST_ERROR" ] && [ "$LAST_ERROR" != "" ]; then
    log_message "ERROR: Replication error - $LAST_ERROR"
    exit 1
fi

log_message "INFO: Replica health check passed - Lag: ${SECONDS_BEHIND}s"
exit 0
EOF

    chmod +x /usr/local/bin/check_replica_health.sh
    
    # Add cron job for health checks
    echo "*/5 * * * * root /usr/local/bin/check_replica_health.sh" >> /etc/crontab
    
    log_info "Replica monitoring configured"
}

# Main execution
main() {
    log_info "Starting MySQL replica setup..."
    
    validate_env
    configure_replica
    
    # Restart MySQL to apply configuration
    systemctl restart mysql
    
    setup_replication
    create_monitoring_user
    setup_monitoring
    
    log_info "MySQL replica setup completed successfully!"
    log_info "Replica ID: ${REPLICA_ID}"
    log_info "Master Host: ${MASTER_HOST}"
    
    # Display replication status
    log_info "Current replication status:"
    mysql -e "SHOW SLAVE STATUS\G" | grep -E "(Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master|Master_Host)"
}

# Run main function
main "$@"