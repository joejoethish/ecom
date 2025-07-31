# MySQL Production Deployment Procedures

This directory contains all the scripts and configurations needed for deploying MySQL database integration in production environments.

## Overview

The deployment system provides:
- Automated MySQL server setup and configuration
- Environment-specific configuration management
- Read replica setup and management
- Comprehensive monitoring and alerting
- Disaster recovery and business continuity
- Zero-downtime deployment procedures

## Directory Structure

```
deployment/
├── README.md                           # This file
├── deploy_production.sh                # Main deployment orchestrator
├── mysql_setup.sh                      # MySQL server setup script
├── replica_setup.sh                    # Read replica setup script
├── config_manager.py                   # Configuration management tool
├── environments/                       # Environment-specific configurations
│   ├── production.env                  # Production environment config
│   └── staging.env                     # Staging environment config
├── monitoring/                         # Monitoring and alerting setup
│   └── setup_monitoring.sh             # Monitoring setup script
├── disaster_recovery/                  # Disaster recovery procedures
│   ├── disaster_recovery_plan.md       # Comprehensive DR plan
│   ├── recovery_scripts.sh             # Recovery automation scripts
│   └── recovery_config.conf            # Recovery configuration
└── generated/                          # Generated configuration files
    ├── mysql-{env}.cnf                 # Generated MySQL configs
    ├── django-db-{env}.py              # Generated Django settings
    ├── monitoring-{env}.json           # Generated monitoring configs
    └── backup-{env}.json               # Generated backup configs
```

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or later
- Minimum 4GB RAM, 8GB recommended
- Minimum 50GB disk space
- Root access
- Internet connectivity

### Required Software
- MySQL 8.0
- Python 3.8+
- pip3
- curl
- systemctl

### Required Environment Variables
```bash
export DB_PASSWORD="your_secure_database_password"
export DB_ROOT_PASSWORD="your_secure_root_password"
export BACKUP_ENCRYPTION_KEY="your_backup_encryption_key"
export SECRET_KEY="your_django_secret_key"
export ADMIN_PASSWORD="your_admin_password"
```

### Optional Environment Variables
```bash
export REPLICA_HOSTS="replica1.db.com,replica2.db.com"
export MONITORING_EMAIL="admin@yourcompany.com"
export SLACK_WEBHOOK="https://hooks.slack.com/services/..."
```

## Quick Start

### 1. Basic Production Deployment

```bash
# Set required environment variables
export DB_PASSWORD="secure_password_123"
export DB_ROOT_PASSWORD="root_password_123"
export BACKUP_ENCRYPTION_KEY="encryption_key_123"
export SECRET_KEY="django_secret_key_123"
export ADMIN_PASSWORD="admin_password_123"

# Make scripts executable (Linux/Mac)
chmod +x backend/deployment/*.sh
chmod +x backend/deployment/monitoring/*.sh
chmod +x backend/deployment/disaster_recovery/*.sh

# Run deployment
sudo ./backend/deployment/deploy_production.sh
```

### 2. Staging Deployment

```bash
# Set environment variables for staging
export DB_PASSWORD="staging_password"
export DB_ROOT_PASSWORD="staging_root_password"
export BACKUP_ENCRYPTION_KEY="staging_encryption_key"
export SECRET_KEY="staging_secret_key"
export ADMIN_PASSWORD="staging_admin_password"

# Deploy to staging
sudo ./backend/deployment/deploy_production.sh --environment staging
```

### 3. Deployment with Read Replicas

```bash
# Set replica hosts
export REPLICA_HOSTS="replica1.internal,replica2.internal"

# Run deployment with replicas
sudo ./backend/deployment/deploy_production.sh --replica-hosts "$REPLICA_HOSTS"
```

## Individual Component Setup

### MySQL Server Setup Only
```bash
sudo ./backend/deployment/mysql_setup.sh
```

### Read Replica Setup Only
```bash
export MASTER_HOST="primary.db.com"
export MASTER_PASSWORD="replication_password"
export REPLICA_ID="2"
sudo ./backend/deployment/replica_setup.sh
```

### Monitoring Setup Only
```bash
export MONITORING_USER="monitor"
export MONITORING_PASSWORD="monitor_password"
export ALERT_EMAIL="admin@company.com"
sudo ./backend/deployment/monitoring/setup_monitoring.sh
```

### Configuration Management
```bash
# Deploy configuration for specific environment
python3 backend/deployment/config_manager.py deploy --environment production

# List available environments
python3 backend/deployment/config_manager.py list

# Compare environments
python3 backend/deployment/config_manager.py compare --environment production --compare-with staging

# Validate configuration
python3 backend/deployment/config_manager.py validate --environment production
```

## Disaster Recovery

### Recovery Scripts Usage
```bash
# Promote replica to primary
sudo /usr/local/bin/mysql_recovery promote-replica replica.db.com 3306

# Enable maintenance mode
sudo /usr/local/bin/mysql_recovery enable-maintenance

# Restore from backup
sudo /usr/local/bin/mysql_recovery restore-backup /backups/mysql_backup.sql.gz

# Apply binary logs for point-in-time recovery
sudo /usr/local/bin/mysql_recovery apply-binlogs "2024-01-01 10:00:00" "2024-01-01 12:00:00"

# Run complete recovery orchestration
sudo /usr/local/bin/mysql_recovery orchestrate primary_failure
```

### Available Recovery Scenarios
- `primary_failure` - Primary database server failure
- `data_corruption` - Data corruption recovery
- `datacenter_outage` - Complete datacenter outage

## Monitoring and Alerting

### Monitoring Endpoints
- **Prometheus Metrics**: http://localhost:9104/metrics
- **Health Check**: http://localhost:8000/health/
- **Monitoring Logs**: /var/log/mysql-monitoring.log
- **Metrics Data**: /var/log/mysql-metrics-*.json

### Alert Thresholds (Production)
- CPU Usage: 80%
- Memory Usage: 85%
- Disk Usage: 90%
- Connection Usage: 80%
- Slow Query Threshold: 5 seconds
- Replication Lag: 300 seconds

### Log Files
- **Deployment**: /var/log/mysql-deployment.log
- **Monitoring**: /var/log/mysql-monitoring.log
- **Recovery**: /var/log/mysql-recovery.log
- **MySQL Error**: /var/log/mysql/error.log
- **MySQL Slow Query**: /var/log/mysql/slow.log

## Configuration Files

### Generated Configuration Files
After deployment, configuration files are generated in `backend/deployment/generated/`:

- `mysql-production.cnf` - MySQL server configuration
- `django-db-production.py` - Django database settings
- `monitoring-production.json` - Monitoring configuration
- `backup-production.json` - Backup configuration

### Environment Configuration
Environment-specific settings are stored in:
- `backend/deployment/environments/production.env`
- `backend/deployment/environments/staging.env`

## Security Considerations

### SSL/TLS Configuration
- All database connections use SSL encryption
- SSL certificates are automatically generated during setup
- Certificate location: `/etc/mysql/ssl/`

### Access Control
- Role-based database users with minimal privileges
- Separate users for application, replication, and monitoring
- Failed login attempt monitoring and lockout

### Data Encryption
- Backup files are encrypted using AES-256
- Sensitive data fields can be encrypted at rest
- SSL required for all client connections

## Backup and Recovery

### Backup Schedule
- **Full Backups**: Daily at 2:00 AM
- **Incremental Backups**: Every 4 hours
- **Binary Log Backups**: Continuous
- **Retention**: 30 days local, 90 days remote

### Backup Locations
- **Primary**: Local SAN storage (`/var/backups/mysql`)
- **Secondary**: AWS S3 (encrypted, versioned)
- **Tertiary**: Tape backup (weekly, offsite)

### Recovery Objectives
- **RPO (Recovery Point Objective)**: 15 minutes
- **RTO (Recovery Time Objective)**: 30 minutes

## Performance Tuning

### MySQL Configuration Optimizations
- InnoDB buffer pool sizing
- Connection pooling and limits
- Query cache configuration
- Binary logging optimization
- Index optimization strategies

### Application-Level Optimizations
- Database connection pooling
- Read/write splitting
- Query optimization
- Caching strategies

## Troubleshooting

### Common Issues

#### Deployment Fails
```bash
# Check deployment logs
tail -f /var/log/mysql-deployment.log

# Check MySQL service status
systemctl status mysql

# Check disk space
df -h

# Check memory usage
free -h
```

#### Database Connection Issues
```bash
# Test database connectivity
mysql -h localhost -u ecommerce_prod_user -p

# Check MySQL error log
tail -f /var/log/mysql/error.log

# Check connection limits
mysql -e "SHOW VARIABLES LIKE 'max_connections'"
mysql -e "SHOW STATUS LIKE 'Threads_connected'"
```

#### Replication Issues
```bash
# Check slave status
mysql -e "SHOW SLAVE STATUS\G"

# Check master status
mysql -e "SHOW MASTER STATUS\G"

# Check replication lag
/usr/local/bin/mysql_recovery verify-integrity
```

#### Performance Issues
```bash
# Check slow query log
tail -f /var/log/mysql/slow.log

# Check system resources
top
iostat -x 1

# Check MySQL process list
mysql -e "SHOW PROCESSLIST"
```

### Recovery Procedures

#### If Deployment Fails
The deployment script includes automatic rollback functionality. If deployment fails:

1. Check the deployment log: `/var/log/mysql-deployment.log`
2. The system will automatically attempt rollback
3. Manual rollback location is stored in `/tmp/deployment_backup_location`

#### If MySQL Won't Start
```bash
# Check MySQL error log
tail -f /var/log/mysql/error.log

# Check configuration syntax
mysqld --help --verbose

# Start in safe mode
mysqld_safe --skip-grant-tables --skip-networking
```

## Maintenance

### Regular Maintenance Tasks
- **Daily**: Backup verification, log rotation
- **Weekly**: Performance analysis, slow query review
- **Monthly**: Disaster recovery testing, capacity planning
- **Quarterly**: Security audit, configuration review

### Automated Maintenance
The deployment sets up automated cron jobs for:
- Database monitoring (every 5 minutes)
- Daily health reports (8:00 AM)
- Weekly disaster recovery tests (Sunday 3:00 AM)
- Daily backup verification (4:00 AM)

### Manual Maintenance Commands
```bash
# Optimize tables
mysqlcheck --optimize --all-databases

# Analyze tables
mysqlcheck --analyze --all-databases

# Check table integrity
mysqlcheck --check --all-databases

# Update table statistics
mysql -e "ANALYZE TABLE table_name"
```

## Support and Documentation

### Additional Resources
- [MySQL 8.0 Documentation](https://dev.mysql.com/doc/refman/8.0/en/)
- [Django Database Documentation](https://docs.djangoproject.com/en/stable/ref/databases/)
- [Disaster Recovery Plan](disaster_recovery/disaster_recovery_plan.md)

### Getting Help
1. Check the troubleshooting section above
2. Review log files for error messages
3. Consult the disaster recovery plan for emergency procedures
4. Contact the database team for assistance

### Emergency Contacts
- **Database Team Lead**: +1-555-0101
- **Infrastructure Manager**: +1-555-0102
- **On-Call Engineer**: +1-555-0103

---

**Last Updated**: $(date '+%Y-%m-%d')
**Version**: 1.0
**Maintained By**: Database Team