#!/bin/bash

# MySQL Disaster Recovery Scripts
# Collection of scripts for disaster recovery procedures

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/recovery_config.conf"
LOG_FILE="/var/log/mysql-recovery.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log_message "INFO" "${GREEN}$1${NC}"
}

log_warn() {
    log_message "WARN" "${YELLOW}$1${NC}"
}

log_error() {
    log_message "ERROR" "${RED}$1${NC}"
}

log_debug() {
    log_message "DEBUG" "${BLUE}$1${NC}"
}

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
        log_info "Configuration loaded from $CONFIG_FILE"
    else
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
}

# Check if MySQL is running
check_mysql_status() {
    local host=${1:-localhost}
    local port=${2:-3306}
    
    if mysql -h "$host" -P "$port" -e "SELECT 1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Wait for MySQL to be available
wait_for_mysql() {
    local host=${1:-localhost}
    local port=${2:-3306}
    local timeout=${3:-300}
    local interval=5
    local elapsed=0
    
    log_info "Waiting for MySQL to be available on $host:$port..."
    
    while [[ $elapsed -lt $timeout ]]; do
        if check_mysql_status "$host" "$port"; then
            log_info "MySQL is available on $host:$port"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        log_debug "Waiting... ($elapsed/$timeout seconds)"
    done
    
    log_error "MySQL not available after $timeout seconds"
    return 1
}

# Promote read replica to primary
promote_replica_to_primary() {
    local replica_host=${1:-$REPLICA_HOST}
    local replica_port=${2:-$REPLICA_PORT}
    
    log_info "Promoting replica $replica_host:$replica_port to primary..."
    
    # Stop slave replication
    mysql -h "$replica_host" -P "$replica_port" -u "$DB_USER" -p"$DB_PASSWORD" << EOF
STOP SLAVE;
RESET SLAVE ALL;
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;
EOF

    if [[ $? -eq 0 ]]; then
        log_info "Replica promoted to primary successfully"
        
        # Update application configuration
        update_database_endpoints "$replica_host" "$replica_port"
        
        return 0
    else
        log_error "Failed to promote replica to primary"
        return 1
    fi
}

# Update database endpoints in application configuration
update_database_endpoints() {
    local new_host=$1
    local new_port=$2
    
    log_info "Updating database endpoints to $new_host:$new_port..."
    
    # Update Django settings
    if [[ -f "$DJANGO_SETTINGS_FILE" ]]; then
        sed -i "s/'HOST': '.*'/'HOST': '$new_host'/g" "$DJANGO_SETTINGS_FILE"
        sed -i "s/'PORT': '.*'/'PORT': '$new_port'/g" "$DJANGO_SETTINGS_FILE"
        log_info "Django settings updated"
    fi
    
    # Update environment variables
    if [[ -f "$ENV_FILE" ]]; then
        sed -i "s/DB_HOST=.*/DB_HOST=$new_host/g" "$ENV_FILE"
        sed -i "s/DB_PORT=.*/DB_PORT=$new_port/g" "$ENV_FILE"
        log_info "Environment file updated"
    fi
    
    # Restart application services
    restart_application_services
}

# Restart application services
restart_application_services() {
    log_info "Restarting application services..."
    
    # Restart Django application
    if systemctl is-active --quiet gunicorn; then
        systemctl restart gunicorn
        log_info "Gunicorn restarted"
    fi
    
    # Restart Celery workers
    if systemctl is-active --quiet celery; then
        systemctl restart celery
        log_info "Celery restarted"
    fi
    
    # Restart Nginx
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        log_info "Nginx reloaded"
    fi
    
    log_info "Application services restarted"
}

# Enable maintenance mode
enable_maintenance_mode() {
    log_info "Enabling maintenance mode..."
    
    # Create maintenance mode file
    touch "$MAINTENANCE_MODE_FILE"
    
    # Update load balancer to show maintenance page
    if [[ -n "$LOAD_BALANCER_SCRIPT" ]]; then
        "$LOAD_BALANCER_SCRIPT" maintenance on
    fi
    
    # Set database to read-only
    mysql -h "$PRIMARY_HOST" -P "$PRIMARY_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \
        -e "SET GLOBAL read_only = ON; SET GLOBAL super_read_only = ON;" 2>/dev/null || true
    
    log_info "Maintenance mode enabled"
}

# Disable maintenance mode
disable_maintenance_mode() {
    log_info "Disabling maintenance mode..."
    
    # Remove maintenance mode file
    rm -f "$MAINTENANCE_MODE_FILE"
    
    # Update load balancer to resume normal operation
    if [[ -n "$LOAD_BALANCER_SCRIPT" ]]; then
        "$LOAD_BALANCER_SCRIPT" maintenance off
    fi
    
    # Disable read-only mode
    mysql -h "$PRIMARY_HOST" -P "$PRIMARY_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \
        -e "SET GLOBAL read_only = OFF; SET GLOBAL super_read_only = OFF;" 2>/dev/null || true
    
    log_info "Maintenance mode disabled"
}

# Restore from backup
restore_from_backup() {
    local backup_file=$1
    local target_database=${2:-$DB_NAME}
    
    if [[ -z "$backup_file" ]]; then
        log_error "Backup file not specified"
        return 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring database from backup: $backup_file"
    
    # Stop MySQL service
    systemctl stop mysql
    
    # Create backup of current data
    local current_backup="/tmp/mysql_current_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$current_backup" /var/lib/mysql/
    log_info "Current data backed up to: $current_backup"
    
    # Remove current data directory
    rm -rf /var/lib/mysql/*
    
    # Start MySQL in recovery mode
    systemctl start mysql
    
    # Wait for MySQL to be available
    wait_for_mysql
    
    # Restore from backup
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | mysql -u root -p"$DB_ROOT_PASSWORD"
    else
        mysql -u root -p"$DB_ROOT_PASSWORD" < "$backup_file"
    fi
    
    if [[ $? -eq 0 ]]; then
        log_info "Database restored successfully from backup"
        return 0
    else
        log_error "Failed to restore database from backup"
        
        # Attempt to restore current backup
        log_info "Attempting to restore previous state..."
        systemctl stop mysql
        rm -rf /var/lib/mysql/*
        tar -xzf "$current_backup" -C /
        systemctl start mysql
        
        return 1
    fi
}

# Apply binary logs for point-in-time recovery
apply_binary_logs() {
    local start_datetime=$1
    local stop_datetime=$2
    local binlog_dir=${3:-/var/lib/mysql}
    
    log_info "Applying binary logs from $start_datetime to $stop_datetime"
    
    # Find binary log files in the time range
    local binlog_files=$(find "$binlog_dir" -name "mysql-bin.*" -type f | sort)
    
    for binlog_file in $binlog_files; do
        log_info "Processing binary log: $binlog_file"
        
        # Apply binary log with time constraints
        mysqlbinlog \
            --start-datetime="$start_datetime" \
            --stop-datetime="$stop_datetime" \
            "$binlog_file" | mysql -u root -p"$DB_ROOT_PASSWORD"
        
        if [[ $? -ne 0 ]]; then
            log_error "Failed to apply binary log: $binlog_file"
            return 1
        fi
    done
    
    log_info "Binary logs applied successfully"
    return 0
}

# Verify data integrity
verify_data_integrity() {
    local database=${1:-$DB_NAME}
    
    log_info "Verifying data integrity for database: $database"
    
    # Check all tables in the database
    local check_result=$(mysqlcheck -u "$DB_USER" -p"$DB_PASSWORD" --check --all-databases)
    
    if echo "$check_result" | grep -q "error\|corrupt"; then
        log_error "Data integrity issues found:"
        echo "$check_result" | grep -E "error|corrupt"
        return 1
    else
        log_info "Data integrity verification passed"
        return 0
    fi
}

# Test application functionality
test_application_functionality() {
    log_info "Testing application functionality..."
    
    # Test database connectivity
    if ! check_mysql_status "$PRIMARY_HOST" "$PRIMARY_PORT"; then
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test basic queries
    local test_query="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME'"
    local result=$(mysql -h "$PRIMARY_HOST" -P "$PRIMARY_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -sN -e "$test_query")
    
    if [[ -n "$result" && "$result" -gt 0 ]]; then
        log_info "Database query test passed ($result tables found)"
    else
        log_error "Database query test failed"
        return 1
    fi
    
    # Test application endpoints (if available)
    if [[ -n "$APP_HEALTH_URL" ]]; then
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" "$APP_HEALTH_URL")
        if [[ "$http_status" == "200" ]]; then
            log_info "Application health check passed"
        else
            log_error "Application health check failed (HTTP $http_status)"
            return 1
        fi
    fi
    
    log_info "Application functionality tests completed successfully"
    return 0
}

# Setup new replica
setup_new_replica() {
    local replica_host=$1
    local master_host=${2:-$PRIMARY_HOST}
    local master_port=${3:-$PRIMARY_PORT}
    
    if [[ -z "$replica_host" ]]; then
        log_error "Replica host not specified"
        return 1
    fi
    
    log_info "Setting up new replica on $replica_host..."
    
    # Get master status
    local master_status=$(mysql -h "$master_host" -P "$master_port" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW MASTER STATUS\G")
    local master_log_file=$(echo "$master_status" | grep "File:" | awk '{print $2}')
    local master_log_pos=$(echo "$master_status" | grep "Position:" | awk '{print $2}')
    
    log_info "Master log file: $master_log_file, Position: $master_log_pos"
    
    # Configure replica
    mysql -h "$replica_host" -u "$DB_USER" -p"$DB_PASSWORD" << EOF
STOP SLAVE;
CHANGE MASTER TO
    MASTER_HOST='$master_host',
    MASTER_PORT=$master_port,
    MASTER_USER='$REPLICATION_USER',
    MASTER_PASSWORD='$REPLICATION_PASSWORD',
    MASTER_LOG_FILE='$master_log_file',
    MASTER_LOG_POS=$master_log_pos,
    MASTER_SSL=1;
START SLAVE;
EOF

    # Check slave status
    sleep 5
    local slave_status=$(mysql -h "$replica_host" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW SLAVE STATUS\G")
    
    if echo "$slave_status" | grep -q "Slave_IO_Running: Yes" && echo "$slave_status" | grep -q "Slave_SQL_Running: Yes"; then
        log_info "New replica setup completed successfully"
        return 0
    else
        log_error "New replica setup failed"
        echo "$slave_status"
        return 1
    fi
}

# Activate disaster recovery site
activate_dr_site() {
    local dr_host=${1:-$DR_HOST}
    local dr_port=${2:-$DR_PORT}
    
    log_info "Activating disaster recovery site: $dr_host:$dr_port"
    
    # Check DR site availability
    if ! check_mysql_status "$dr_host" "$dr_port"; then
        log_error "DR site is not available"
        return 1
    fi
    
    # Stop replication on DR site
    mysql -h "$dr_host" -P "$dr_port" -u "$DB_USER" -p"$DB_PASSWORD" << EOF
STOP SLAVE;
RESET SLAVE ALL;
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;
EOF

    # Update DNS to point to DR site
    if [[ -n "$DNS_UPDATE_SCRIPT" ]]; then
        "$DNS_UPDATE_SCRIPT" "$dr_host"
        log_info "DNS updated to point to DR site"
    fi
    
    # Update application configuration
    update_database_endpoints "$dr_host" "$dr_port"
    
    log_info "Disaster recovery site activated successfully"
    return 0
}

# Failback to primary site
failback_to_primary() {
    local primary_host=${1:-$PRIMARY_HOST}
    local primary_port=${2:-$PRIMARY_PORT}
    local dr_host=${3:-$DR_HOST}
    
    log_info "Failing back to primary site: $primary_host:$primary_port"
    
    # Check primary site availability
    if ! check_mysql_status "$primary_host" "$primary_port"; then
        log_error "Primary site is not available for failback"
        return 1
    fi
    
    # Setup reverse replication from DR to primary
    log_info "Setting up reverse replication..."
    
    # Get DR master status
    local dr_status=$(mysql -h "$dr_host" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW MASTER STATUS\G")
    local dr_log_file=$(echo "$dr_status" | grep "File:" | awk '{print $2}')
    local dr_log_pos=$(echo "$dr_status" | grep "Position:" | awk '{print $2}')
    
    # Configure primary as slave of DR
    mysql -h "$primary_host" -P "$primary_port" -u "$DB_USER" -p"$DB_PASSWORD" << EOF
CHANGE MASTER TO
    MASTER_HOST='$dr_host',
    MASTER_USER='$REPLICATION_USER',
    MASTER_PASSWORD='$REPLICATION_PASSWORD',
    MASTER_LOG_FILE='$dr_log_file',
    MASTER_LOG_POS=$dr_log_pos;
START SLAVE;
EOF

    # Wait for synchronization
    log_info "Waiting for synchronization to complete..."
    local sync_timeout=1800  # 30 minutes
    local sync_interval=30
    local sync_elapsed=0
    
    while [[ $sync_elapsed -lt $sync_timeout ]]; do
        local slave_status=$(mysql -h "$primary_host" -P "$primary_port" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW SLAVE STATUS\G")
        local seconds_behind=$(echo "$slave_status" | grep "Seconds_Behind_Master:" | awk '{print $2}')
        
        if [[ "$seconds_behind" == "0" ]]; then
            log_info "Synchronization completed"
            break
        fi
        
        log_info "Synchronization in progress... ($seconds_behind seconds behind)"
        sleep $sync_interval
        sync_elapsed=$((sync_elapsed + sync_interval))
    done
    
    if [[ $sync_elapsed -ge $sync_timeout ]]; then
        log_error "Synchronization timeout reached"
        return 1
    fi
    
    # Stop applications temporarily
    enable_maintenance_mode
    
    # Stop replication on primary
    mysql -h "$primary_host" -P "$primary_port" -u "$DB_USER" -p"$DB_PASSWORD" << EOF
STOP SLAVE;
RESET SLAVE ALL;
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;
EOF

    # Update DNS back to primary
    if [[ -n "$DNS_UPDATE_SCRIPT" ]]; then
        "$DNS_UPDATE_SCRIPT" "$primary_host"
        log_info "DNS updated back to primary site"
    fi
    
    # Update application configuration
    update_database_endpoints "$primary_host" "$primary_port"
    
    # Disable maintenance mode
    disable_maintenance_mode
    
    log_info "Failback to primary site completed successfully"
    return 0
}

# Send notification
send_notification() {
    local subject=$1
    local message=$2
    local severity=${3:-info}
    
    # Send email notification
    if [[ -n "$NOTIFICATION_EMAIL" ]]; then
        echo "$message" | mail -s "$subject" "$NOTIFICATION_EMAIL"
    fi
    
    # Send Slack notification
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        case $severity in
            error|critical) color="danger" ;;
            warning) color="warning" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$subject\",\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK"
    fi
    
    log_info "Notification sent: $subject"
}

# Main recovery orchestrator
recovery_orchestrator() {
    local scenario=$1
    local start_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    log_info "Starting recovery orchestrator for scenario: $scenario"
    send_notification "Recovery Started" "Recovery procedure started for scenario: $scenario" "warning"
    
    case $scenario in
        "primary_failure")
            if promote_replica_to_primary; then
                log_info "Primary failure recovery completed successfully"
                send_notification "Recovery Completed" "Primary failure recovery completed successfully" "good"
            else
                log_error "Primary failure recovery failed"
                send_notification "Recovery Failed" "Primary failure recovery failed" "danger"
                return 1
            fi
            ;;
        
        "data_corruption")
            enable_maintenance_mode
            if restore_from_backup "$LATEST_BACKUP"; then
                verify_data_integrity
                disable_maintenance_mode
                log_info "Data corruption recovery completed successfully"
                send_notification "Recovery Completed" "Data corruption recovery completed successfully" "good"
            else
                log_error "Data corruption recovery failed"
                send_notification "Recovery Failed" "Data corruption recovery failed" "danger"
                return 1
            fi
            ;;
        
        "datacenter_outage")
            if activate_dr_site; then
                log_info "Datacenter outage recovery completed successfully"
                send_notification "Recovery Completed" "Datacenter outage recovery completed successfully" "good"
            else
                log_error "Datacenter outage recovery failed"
                send_notification "Recovery Failed" "Datacenter outage recovery failed" "danger"
                return 1
            fi
            ;;
        
        *)
            log_error "Unknown recovery scenario: $scenario"
            return 1
            ;;
    esac
    
    local end_time=$(date '+%Y-%m-%d %H:%M:%S')
    local duration=$(( $(date -d "$end_time" +%s) - $(date -d "$start_time" +%s) ))
    
    log_info "Recovery orchestrator completed in $duration seconds"
    return 0
}

# Display usage information
usage() {
    cat << EOF
MySQL Disaster Recovery Scripts

Usage: $0 <command> [options]

Commands:
    promote-replica [host] [port]     - Promote read replica to primary
    enable-maintenance               - Enable maintenance mode
    disable-maintenance              - Disable maintenance mode
    restore-backup <file>            - Restore from backup file
    apply-binlogs <start> <stop>     - Apply binary logs for point-in-time recovery
    verify-integrity [database]      - Verify data integrity
    test-functionality               - Test application functionality
    setup-replica <host> [master]   - Setup new replica
    activate-dr [host] [port]        - Activate disaster recovery site
    failback-primary [host] [port]   - Failback to primary site
    orchestrate <scenario>           - Run recovery orchestrator

Scenarios for orchestrate:
    primary_failure                  - Primary database server failure
    data_corruption                  - Data corruption recovery
    datacenter_outage               - Complete datacenter outage

Examples:
    $0 promote-replica replica.db.com 3306
    $0 restore-backup /backups/mysql_backup_20240101.sql.gz
    $0 apply-binlogs "2024-01-01 10:00:00" "2024-01-01 12:00:00"
    $0 orchestrate primary_failure

EOF
}

# Main function
main() {
    # Load configuration
    load_config
    
    # Check if command is provided
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    local command=$1
    shift
    
    case $command in
        "promote-replica")
            promote_replica_to_primary "$@"
            ;;
        "enable-maintenance")
            enable_maintenance_mode
            ;;
        "disable-maintenance")
            disable_maintenance_mode
            ;;
        "restore-backup")
            restore_from_backup "$@"
            ;;
        "apply-binlogs")
            apply_binary_logs "$@"
            ;;
        "verify-integrity")
            verify_data_integrity "$@"
            ;;
        "test-functionality")
            test_application_functionality
            ;;
        "setup-replica")
            setup_new_replica "$@"
            ;;
        "activate-dr")
            activate_dr_site "$@"
            ;;
        "failback-primary")
            failback_to_primary "$@"
            ;;
        "orchestrate")
            recovery_orchestrator "$@"
            ;;
        *)
            echo "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi