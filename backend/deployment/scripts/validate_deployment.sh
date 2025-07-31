#!/bin/bash

# MySQL Production Deployment Validation Script
# This script validates that the MySQL deployment is working correctly

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/mysql-deployment-validation.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    log "INFO" "Running test: $test_name"
    
    if eval "$test_command" &>/dev/null; then
        log "SUCCESS" "✓ $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log "ERROR" "✗ $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Load environment variables if available
load_environment() {
    if [[ -f "/opt/ecommerce/.env.production" ]]; then
        source /opt/ecommerce/.env.production
    elif [[ -f ".env.production" ]]; then
        source .env.production
    else
        log "WARNING" "Production environment file not found"
    fi
}

# Test MySQL service status
test_mysql_service() {
    run_test "MySQL service is running" "systemctl is-active --quiet mysql"
}

# Test MySQL connection
test_mysql_connection() {
    run_test "MySQL connection test" "mysql -u root -e 'SELECT 1;'"
}

# Test database exists
test_database_exists() {
    run_test "Production database exists" "mysql -u root -e 'USE ecommerce_prod; SELECT 1;'"
}

# Test application user connection
test_app_user_connection() {
    if [[ -n "$DB_PASSWORD" ]]; then
        run_test "Application user connection" "mysql -u ecommerce_app -p'$DB_PASSWORD' -e 'SELECT 1;' ecommerce_prod"
    else
        log "WARNING" "DB_PASSWORD not set, skipping application user test"
    fi
}

# Test SSL connection
test_ssl_connection() {
    run_test "SSL connection test" "mysql -u root --ssl-ca=/etc/mysql/ssl/ca-cert.pem -e 'SHOW STATUS LIKE \"Ssl_cipher\";' | grep -q AES"
}

# Test read-only user
test_readonly_user() {
    if [[ -n "$DB_READ_PASSWORD" ]]; then
        run_test "Read-only user connection" "mysql -u ecommerce_read -p'$DB_READ_PASSWORD' -e 'SELECT 1;' ecommerce_prod"
    else
        log "WARNING" "DB_READ_PASSWORD not set, skipping read-only user test"
    fi
}

# Test backup user
test_backup_user() {
    if [[ -n "$BACKUP_DB_PASSWORD" ]]; then
        run_test "Backup user connection" "mysql -u ecommerce_backup -p'$BACKUP_DB_PASSWORD' -e 'SELECT 1;' ecommerce_prod"
    else
        log "WARNING" "BACKUP_DB_PASSWORD not set, skipping backup user test"
    fi
}

# Test MySQL configuration
test_mysql_configuration() {
    run_test "InnoDB buffer pool size" "mysql -u root -e 'SHOW VARIABLES LIKE \"innodb_buffer_pool_size\";' | grep -q '[0-9]'"
    run_test "Character set is utf8mb4" "mysql -u root -e 'SHOW VARIABLES LIKE \"character_set_server\";' | grep -q utf8mb4"
    run_test "SSL is enabled" "mysql -u root -e 'SHOW VARIABLES LIKE \"have_ssl\";' | grep -q YES"
    run_test "Binary logging is enabled" "mysql -u root -e 'SHOW VARIABLES LIKE \"log_bin\";' | grep -q ON"
}

# Test file permissions
test_file_permissions() {
    run_test "MySQL SSL directory permissions" "[[ -d /etc/mysql/ssl && $(stat -c %a /etc/mysql/ssl) == '755' ]]"
    run_test "MySQL SSL key file permissions" "[[ -f /etc/mysql/ssl/server-key.pem && $(stat -c %a /etc/mysql/ssl/server-key.pem) == '600' ]]"
    run_test "Backup directory exists" "[[ -d /var/backups/mysql ]]"
    run_test "Log directory exists" "[[ -d /var/log/mysql-backup ]]"
}

# Test backup script
test_backup_script() {
    run_test "Backup script exists" "[[ -f /opt/mysql-backup/scripts/full_backup.sh ]]"
    run_test "Backup script is executable" "[[ -x /opt/mysql-backup/scripts/full_backup.sh ]]"
}

# Test cron jobs
test_cron_jobs() {
    run_test "Backup cron job exists" "crontab -l | grep -q full_backup.sh"
}

# Test log rotation
test_log_rotation() {
    run_test "MySQL log rotation config exists" "[[ -f /etc/logrotate.d/mysql-ecommerce ]]"
}

# Test Django application
test_django_application() {
    if command -v python3 &> /dev/null && [[ -f "manage.py" ]]; then
        run_test "Django can connect to database" "python3 manage.py dbshell --database=default -c 'SELECT 1;'"
        run_test "Django migrations are up to date" "python3 manage.py showmigrations --database=default | grep -v '\\[ \\]'"
    else
        log "WARNING" "Django application not found or Python not available"
    fi
}

# Test network connectivity
test_network_connectivity() {
    run_test "MySQL port is listening" "netstat -tlnp | grep -q ':3306'"
    run_test "MySQL accepts connections" "timeout 5 bash -c '</dev/tcp/localhost/3306'"
}

# Test performance
test_performance() {
    # Simple performance test - create and query a test table
    local test_db="mysql_test_$(date +%s)"
    
    mysql -u root -e "CREATE DATABASE $test_db;" 2>/dev/null || true
    
    run_test "Database performance test" "
        mysql -u root $test_db -e '
            CREATE TABLE test_performance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO test_performance (data) VALUES (\"test1\"), (\"test2\"), (\"test3\");
            SELECT COUNT(*) FROM test_performance;
        ' | grep -q '3'
    "
    
    mysql -u root -e "DROP DATABASE IF EXISTS $test_db;" 2>/dev/null || true
}

# Test monitoring
test_monitoring() {
    run_test "MySQL error log exists" "[[ -f /var/log/mysql/error.log ]]"
    run_test "MySQL slow query log exists" "[[ -f /var/log/mysql/mysql-slow.log ]]"
    run_test "Django log directory exists" "[[ -d /var/log/django ]]"
}

# Generate summary report
generate_summary() {
    echo
    echo "=================================="
    echo "DEPLOYMENT VALIDATION SUMMARY"
    echo "=================================="
    echo "Total tests: $TESTS_TOTAL"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
    echo
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log "SUCCESS" "All tests passed! Deployment is ready for production."
        return 0
    else
        log "ERROR" "$TESTS_FAILED tests failed. Please review and fix issues before going to production."
        return 1
    fi
}

# Main validation function
main() {
    log "INFO" "Starting MySQL deployment validation..."
    log "INFO" "Validation started at $(date)"
    
    # Load environment variables
    load_environment
    
    # Run all tests
    echo "Running MySQL service tests..."
    test_mysql_service
    test_mysql_connection
    test_network_connectivity
    
    echo
    echo "Running database tests..."
    test_database_exists
    test_app_user_connection
    test_readonly_user
    test_backup_user
    
    echo
    echo "Running configuration tests..."
    test_mysql_configuration
    test_ssl_connection
    
    echo
    echo "Running file system tests..."
    test_file_permissions
    test_backup_script
    test_cron_jobs
    test_log_rotation
    
    echo
    echo "Running application tests..."
    test_django_application
    
    echo
    echo "Running performance tests..."
    test_performance
    
    echo
    echo "Running monitoring tests..."
    test_monitoring
    
    # Generate summary
    generate_summary
    
    log "INFO" "Validation finished at $(date)"
}

# Show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo
    echo "This script validates the MySQL production deployment."
    echo "It runs various tests to ensure the system is properly configured."
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