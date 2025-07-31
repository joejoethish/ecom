#!/bin/bash

# MySQL Production Deployment Orchestration Script
# This script orchestrates the complete production deployment of MySQL database integration

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_LOG="/var/log/mysql-deployment.log"
ENVIRONMENT=${ENVIRONMENT:-production}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$DEPLOYMENT_LOG"
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "DB_PASSWORD"
        "DB_ROOT_PASSWORD"
        "BACKUP_ENCRYPTION_KEY"
        "SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check available disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local required_space=10485760  # 10GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        log_error "Insufficient disk space. Required: 10GB, Available: $((available_space/1024/1024))GB"
        exit 1
    fi
    
    # Check network connectivity
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        log_warn "Internet connectivity check failed. Some features may not work."
    fi
    
    log_info "Prerequisites check completed successfully"
}

# Backup current system state
backup_current_state() {
    log_info "Creating backup of current system state..."
    
    local backup_dir="/tmp/mysql_deployment_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup current MySQL configuration
    if [[ -d "/etc/mysql" ]]; then
        cp -r /etc/mysql "$backup_dir/"
        log_info "MySQL configuration backed up"
    fi
    
    # Backup current database (if exists)
    if systemctl is-active --quiet mysql; then
        mysqldump --all-databases --single-transaction --routines --triggers > "$backup_dir/current_database.sql"
        log_info "Current database backed up"
    fi
    
    # Backup application configuration
    if [[ -f "/opt/ecommerce/backend/.env" ]]; then
        cp /opt/ecommerce/backend/.env "$backup_dir/"
        log_info "Application configuration backed up"
    fi
    
    echo "$backup_dir" > /tmp/deployment_backup_location
    log_info "System state backup completed: $backup_dir"
}

# Deploy configuration management
deploy_configuration() {
    log_info "Deploying configuration management..."
    
    # Make config manager executable
    chmod +x "$SCRIPT_DIR/config_manager.py"
    
    # Deploy environment-specific configuration
    python3 "$SCRIPT_DIR/config_manager.py" deploy --environment "$ENVIRONMENT"
    
    if [[ $? -eq 0 ]]; then
        log_info "Configuration deployment completed successfully"
    else
        log_error "Configuration deployment failed"
        return 1
    fi
}

# Setup MySQL server
setup_mysql_server() {
    log_info "Setting up MySQL server..."
    
    # Make MySQL setup script executable
    chmod +x "$SCRIPT_DIR/mysql_setup.sh"
    
    # Run MySQL setup
    "$SCRIPT_DIR/mysql_setup.sh"
    
    if [[ $? -eq 0 ]]; then
        log_info "MySQL server setup completed successfully"
    else
        log_error "MySQL server setup failed"
        return 1
    fi
}

# Setup read replicas
setup_read_replicas() {
    log_info "Setting up read replicas..."
    
    if [[ -n "$REPLICA_HOSTS" ]]; then
        # Make replica setup script executable
        chmod +x "$SCRIPT_DIR/replica_setup.sh"
        
        # Setup each replica
        IFS=',' read -ra REPLICA_ARRAY <<< "$REPLICA_HOSTS"
        for replica_host in "${REPLICA_ARRAY[@]}"; do
            log_info "Setting up replica on $replica_host"
            
            # Run replica setup on remote host
            ssh "$replica_host" "bash -s" < "$SCRIPT_DIR/replica_setup.sh"
            
            if [[ $? -eq 0 ]]; then
                log_info "Replica setup completed on $replica_host"
            else
                log_error "Replica setup failed on $replica_host"
                return 1
            fi
        done
    else
        log_info "No replica hosts specified, skipping replica setup"
    fi
}

# Setup monitoring and alerting
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Make monitoring setup script executable
    chmod +x "$SCRIPT_DIR/monitoring/setup_monitoring.sh"
    
    # Run monitoring setup
    "$SCRIPT_DIR/monitoring/setup_monitoring.sh"
    
    if [[ $? -eq 0 ]]; then
        log_info "Monitoring and alerting setup completed successfully"
    else
        log_error "Monitoring and alerting setup failed"
        return 1
    fi
}

# Setup disaster recovery
setup_disaster_recovery() {
    log_info "Setting up disaster recovery..."
    
    # Make recovery scripts executable
    chmod +x "$SCRIPT_DIR/disaster_recovery/recovery_scripts.sh"
    
    # Copy disaster recovery files to system locations
    cp "$SCRIPT_DIR/disaster_recovery/recovery_scripts.sh" /usr/local/bin/mysql_recovery
    cp "$SCRIPT_DIR/disaster_recovery/recovery_config.conf" /etc/mysql/recovery.conf
    
    # Create disaster recovery cron jobs
    cat > /etc/cron.d/mysql-disaster-recovery << EOF
# MySQL Disaster Recovery Cron Jobs
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Weekly disaster recovery test
0 3 * * 0 root /usr/local/bin/mysql_recovery test-functionality >> /var/log/mysql-recovery-test.log 2>&1

# Daily backup verification
0 4 * * * root /usr/local/bin/mysql_recovery verify-integrity >> /var/log/mysql-recovery-test.log 2>&1
EOF

    log_info "Disaster recovery setup completed successfully"
}

# Update application configuration
update_application_config() {
    log_info "Updating application configuration..."
    
    # Update Django settings
    local django_settings_file="/opt/ecommerce/backend/ecommerce_project/settings/production.py"
    local generated_settings="$SCRIPT_DIR/generated/django-db-$ENVIRONMENT.py"
    
    if [[ -f "$generated_settings" ]]; then
        # Backup current settings
        cp "$django_settings_file" "$django_settings_file.backup"
        
        # Append database configuration
        cat "$generated_settings" >> "$django_settings_file"
        
        log_info "Django settings updated"
    fi
    
    # Update environment file
    local env_file="/opt/ecommerce/backend/.env"
    local env_template="$SCRIPT_DIR/environments/$ENVIRONMENT.env"
    
    if [[ -f "$env_template" ]]; then
        # Backup current env file
        cp "$env_file" "$env_file.backup"
        
        # Copy new environment configuration
        cp "$env_template" "$env_file"
        
        log_info "Environment configuration updated"
    fi
}

# Run database migrations
run_database_migrations() {
    log_info "Running database migrations..."
    
    # Change to application directory
    cd /opt/ecommerce/backend
    
    # Activate virtual environment if it exists
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    # Run Django migrations
    python manage.py migrate --settings=ecommerce_project.settings.production
    
    if [[ $? -eq 0 ]]; then
        log_info "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        return 1
    fi
    
    # Create superuser if it doesn't exist
    python manage.py shell --settings=ecommerce_project.settings.production << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ecommerce.com', '$ADMIN_PASSWORD')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

    log_info "Database setup completed"
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test database connectivity
    if mysql -h localhost -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
        log_info "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test application health
    cd /opt/ecommerce/backend
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    # Run Django check
    python manage.py check --settings=ecommerce_project.settings.production
    
    if [[ $? -eq 0 ]]; then
        log_info "Application health check passed"
    else
        log_error "Application health check failed"
        return 1
    fi
    
    # Test monitoring
    if systemctl is-active --quiet mysql-prometheus-exporter; then
        log_info "Monitoring service test passed"
    else
        log_warn "Monitoring service test failed"
    fi
    
    log_info "Deployment testing completed successfully"
}

# Restart services
restart_services() {
    log_info "Restarting application services..."
    
    # Restart MySQL
    systemctl restart mysql
    log_info "MySQL restarted"
    
    # Restart application services
    local services=("gunicorn" "celery" "nginx")
    
    for service in "${services[@]}"; do
        if systemctl is-enabled --quiet "$service"; then
            systemctl restart "$service"
            log_info "$service restarted"
        else
            log_debug "$service not enabled, skipping"
        fi
    done
    
    log_info "Services restart completed"
}

# Generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    local report_file="/var/log/mysql-deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
MySQL Production Deployment Report
==================================

Deployment Date: $(date '+%Y-%m-%d %H:%M:%S')
Environment: $ENVIRONMENT
Deployment Duration: $(($(date +%s) - $DEPLOYMENT_START_TIME)) seconds

Components Deployed:
- MySQL Server: $(mysql --version | head -1)
- Configuration Management: Completed
- Monitoring and Alerting: Completed
- Disaster Recovery: Completed
- Read Replicas: $(if [[ -n "$REPLICA_HOSTS" ]]; then echo "Completed"; else echo "Skipped"; fi)

Database Information:
- Database Name: $DB_NAME
- Database User: $DB_USER
- SSL Enabled: $(if [[ "$SECURITY_SSL_REQUIRED" == "true" ]]; then echo "Yes"; else echo "No"; fi)
- Backup Enabled: $(if [[ "$BACKUP_ENABLED" == "true" ]]; then echo "Yes"; else echo "No"; fi)

Service Status:
$(systemctl is-active mysql && echo "- MySQL: Active" || echo "- MySQL: Inactive")
$(systemctl is-active mysql-prometheus-exporter && echo "- Monitoring: Active" || echo "- Monitoring: Inactive")

Configuration Files:
- MySQL Config: /etc/mysql/mysql.conf.d/production.cnf
- Recovery Config: /etc/mysql/recovery.conf
- Monitoring Config: /opt/mysql-monitoring/config.json
- Backup Config: $SCRIPT_DIR/generated/backup-$ENVIRONMENT.json

Log Files:
- Deployment Log: $DEPLOYMENT_LOG
- MySQL Error Log: /var/log/mysql/error.log
- Monitoring Log: /var/log/mysql-monitoring.log
- Recovery Log: /var/log/mysql-recovery.log

Next Steps:
1. Verify application functionality
2. Run performance tests
3. Schedule regular backup tests
4. Review monitoring alerts
5. Update documentation

Backup Location: $(cat /tmp/deployment_backup_location 2>/dev/null || echo "Not available")

Report Generated: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    log_info "Deployment report generated: $report_file"
    
    # Display summary
    cat << EOF

${GREEN}=== MySQL Production Deployment Summary ===${NC}

✅ MySQL Server Setup: Completed
✅ Configuration Management: Completed  
✅ Monitoring and Alerting: Completed
✅ Disaster Recovery: Completed
$(if [[ -n "$REPLICA_HOSTS" ]]; then echo "✅ Read Replicas: Completed"; else echo "⏭️  Read Replicas: Skipped"; fi)
✅ Application Configuration: Completed
✅ Database Migrations: Completed
✅ Service Testing: Completed

${BLUE}Database Endpoint:${NC} $PRIMARY_HOST:$PRIMARY_PORT
${BLUE}Monitoring URL:${NC} http://localhost:9104/metrics
${BLUE}Deployment Report:${NC} $report_file

${YELLOW}Important:${NC}
- Update DNS records if needed
- Configure load balancer health checks
- Schedule regular disaster recovery tests
- Review and customize monitoring thresholds

${GREEN}Deployment completed successfully!${NC}

EOF
}

# Rollback deployment
rollback_deployment() {
    log_error "Rolling back deployment due to failure..."
    
    local backup_location=$(cat /tmp/deployment_backup_location 2>/dev/null)
    
    if [[ -n "$backup_location" && -d "$backup_location" ]]; then
        # Restore MySQL configuration
        if [[ -d "$backup_location/mysql" ]]; then
            rm -rf /etc/mysql
            cp -r "$backup_location/mysql" /etc/mysql
            log_info "MySQL configuration restored"
        fi
        
        # Restore database
        if [[ -f "$backup_location/current_database.sql" ]]; then
            mysql < "$backup_location/current_database.sql"
            log_info "Database restored"
        fi
        
        # Restore application configuration
        if [[ -f "$backup_location/.env" ]]; then
            cp "$backup_location/.env" /opt/ecommerce/backend/
            log_info "Application configuration restored"
        fi
        
        # Restart services
        systemctl restart mysql
        
        log_info "Rollback completed"
    else
        log_error "Backup location not found, manual rollback required"
    fi
}

# Main deployment function
main() {
    local DEPLOYMENT_START_TIME=$(date +%s)
    
    log_info "Starting MySQL production deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Set trap for cleanup on failure
    trap 'log_error "Deployment failed, initiating rollback..."; rollback_deployment; exit 1' ERR
    
    # Execute deployment steps
    check_prerequisites
    backup_current_state
    deploy_configuration
    setup_mysql_server
    setup_read_replicas
    setup_monitoring
    setup_disaster_recovery
    update_application_config
    run_database_migrations
    restart_services
    test_deployment
    generate_deployment_report
    
    # Remove error trap
    trap - ERR
    
    log_info "MySQL production deployment completed successfully!"
    
    # Clean up temporary files
    rm -f /tmp/deployment_backup_location
}

# Display usage information
usage() {
    cat << EOF
MySQL Production Deployment Script

Usage: $0 [options]

Options:
    --environment ENV    Deployment environment (default: production)
    --replica-hosts      Comma-separated list of replica hosts
    --help              Show this help message

Required Environment Variables:
    DB_PASSWORD         Database user password
    DB_ROOT_PASSWORD    Database root password
    BACKUP_ENCRYPTION_KEY   Backup encryption key
    SECRET_KEY          Django secret key
    ADMIN_PASSWORD      Admin user password

Optional Environment Variables:
    REPLICA_HOSTS       Comma-separated replica hosts
    MONITORING_EMAIL    Email for monitoring alerts
    SLACK_WEBHOOK       Slack webhook for notifications

Examples:
    # Basic production deployment
    export DB_PASSWORD="secure_password"
    export DB_ROOT_PASSWORD="root_password"
    export BACKUP_ENCRYPTION_KEY="encryption_key"
    export SECRET_KEY="django_secret"
    export ADMIN_PASSWORD="admin_password"
    $0

    # Deployment with replicas
    export REPLICA_HOSTS="replica1.db.com,replica2.db.com"
    $0 --replica-hosts "\$REPLICA_HOSTS"

    # Staging deployment
    $0 --environment staging

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --replica-hosts)
            REPLICA_HOSTS="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi