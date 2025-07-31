# Disaster Recovery Plan

## Overview

This comprehensive disaster recovery plan outlines procedures for recovering from various failure scenarios affecting the MySQL database infrastructure, ensuring minimal downtime and data loss.

## Recovery Time and Point Objectives

### Service Level Objectives
- **Recovery Time Objective (RTO)**: Maximum 4 hours for complete system recovery
- **Recovery Point Objective (RPO)**: Maximum 1 hour of data loss
- **Mean Time to Recovery (MTTR)**: Target 2 hours for most scenarios
- **Availability Target**: 99.9% uptime (8.76 hours downtime per year)

### Priority Classification
| Priority | Description | RTO | RPO |
|----------|-------------|-----|-----|
| P1 - Critical | Complete database failure | 2 hours | 15 minutes |
| P2 - High | Partial service degradation | 4 hours | 1 hour |
| P3 - Medium | Performance issues | 8 hours | 4 hours |
| P4 - Low | Non-critical component failure | 24 hours | 24 hours |

## Disaster Scenarios and Response Procedures

### 1. Complete Database Server Failure

#### Scenario: Primary MySQL server hardware failure
**Impact**: Complete service outage
**Priority**: P1 - Critical

#### Immediate Response (0-15 minutes)
```bash
# 1. Verify server status
ping mysql-primary.company.com
ssh mysql-primary.company.com  # If accessible

# 2. Check service status
systemctl status mysql
systemctl status mysqld

# 3. Attempt service restart
sudo systemctl restart mysql

# 4. If hardware failure confirmed, initiate failover
/usr/local/bin/initiate_failover.sh
```

#### Failover Procedure (15-30 minutes)
```bash
#!/bin/bash
# /usr/local/bin/initiate_failover.sh

LOG_FILE="/var/log/mysql/disaster_recovery.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Initiating disaster recovery failover" | tee -a $LOG_FILE

# 1. Promote read replica to primary
echo "[$TIMESTAMP] Promoting read replica to primary" | tee -a $LOG_FILE
ssh mysql-replica-1.company.com "
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e 'STOP SLAVE;'
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e 'RESET SLAVE ALL;'
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e 'SET GLOBAL read_only = OFF;'
"

# 2. Update DNS to point to new primary
echo "[$TIMESTAMP] Updating DNS records" | tee -a $LOG_FILE
/usr/local/bin/update_dns.sh mysql-primary.company.com mysql-replica-1.company.com

# 3. Update application configuration
echo "[$TIMESTAMP] Updating application configuration" | tee -a $LOG_FILE
sed -i 's/mysql-primary.company.com/mysql-replica-1.company.com/g' /etc/mysql/app_config.conf

# 4. Restart application services
echo "[$TIMESTAMP] Restarting application services" | tee -a $LOG_FILE
systemctl restart gunicorn
systemctl restart celery
systemctl restart nginx

# 5. Verify connectivity
echo "[$TIMESTAMP] Verifying database connectivity" | tee -a $LOG_FILE
mysql -h mysql-replica-1.company.com -u app_user -p${APP_PASSWORD} -e "SELECT 1;"

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] Failover completed successfully" | tee -a $LOG_FILE
    # Send success notification
    echo "MySQL failover completed successfully. New primary: mysql-replica-1.company.com" | \
        mail -s "DR: Failover Successful" admin@company.com
else
    echo "[$TIMESTAMP] Failover failed - manual intervention required" | tee -a $LOG_FILE
    # Send failure alert
    echo "MySQL failover failed. Manual intervention required immediately." | \
        mail -s "CRITICAL: DR Failover Failed" admin@company.com
fi
```

#### Recovery Procedure (30 minutes - 4 hours)
```bash
# 1. Assess primary server damage
# 2. If repairable, fix and restore as replica
# 3. If replacement needed, provision new hardware
# 4. Restore from backup and sync with current primary

# Restore primary server as replica
#!/bin/bash
# /usr/local/bin/restore_primary_as_replica.sh

NEW_PRIMARY="mysql-replica-1.company.com"
OLD_PRIMARY="mysql-primary.company.com"

# 1. Install MySQL on repaired/new server
sudo apt-get update
sudo apt-get install mysql-server-8.0

# 2. Restore from latest backup
LATEST_BACKUP=$(ls -t /backups/mysql/*.sql.gz | head -1)
gunzip -c $LATEST_BACKUP | mysql -u root -p

# 3. Configure as replica
mysql -u root -p -e "
CHANGE MASTER TO
    MASTER_HOST='$NEW_PRIMARY',
    MASTER_USER='replication_user',
    MASTER_PASSWORD='${REPLICATION_PASSWORD}',
    MASTER_AUTO_POSITION=1;
START SLAVE;
"

# 4. Verify replication
mysql -u root -p -e "SHOW SLAVE STATUS\G"
```

### 2. Data Corruption

#### Scenario: Database corruption detected
**Impact**: Data integrity compromised
**Priority**: P1 - Critical

#### Detection and Assessment
```sql
-- Check for table corruption
CHECK TABLE auth_user, products_product, orders_order, reviews_review;

-- Check InnoDB status for corruption indicators
SHOW ENGINE INNODB STATUS;

-- Verify data consistency
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'ecommerce_db';
```

#### Recovery Procedure
```bash
#!/bin/bash
# /usr/local/bin/recover_from_corruption.sh

CORRUPTION_LOG="/var/log/mysql/corruption_recovery.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting corruption recovery" | tee -a $CORRUPTION_LOG

# 1. Stop MySQL service
echo "[$TIMESTAMP] Stopping MySQL service" | tee -a $CORRUPTION_LOG
systemctl stop mysql

# 2. Backup current data directory
echo "[$TIMESTAMP] Backing up corrupted data" | tee -a $CORRUPTION_LOG
cp -r /var/lib/mysql /var/lib/mysql_corrupted_$(date +%Y%m%d_%H%M%S)

# 3. Attempt InnoDB recovery
echo "[$TIMESTAMP] Attempting InnoDB recovery" | tee -a $CORRUPTION_LOG
echo "innodb_force_recovery = 1" >> /etc/mysql/mysql.conf.d/mysqld.cnf
systemctl start mysql

# 4. Export recoverable data
echo "[$TIMESTAMP] Exporting recoverable data" | tee -a $CORRUPTION_LOG
mysqldump -u root -p --single-transaction --routines --triggers ecommerce_db > /tmp/recovery_export.sql

# 5. Restore from clean backup
echo "[$TIMESTAMP] Restoring from backup" | tee -a $CORRUPTION_LOG
systemctl stop mysql
rm -rf /var/lib/mysql/*
mysql_install_db --user=mysql --datadir=/var/lib/mysql

# Remove recovery mode
sed -i '/innodb_force_recovery/d' /etc/mysql/mysql.conf.d/mysqld.cnf
systemctl start mysql

# 6. Restore database
mysql -u root -p < /backups/mysql/latest_clean_backup.sql

# 7. Apply recovered data where possible
mysql -u root -p ecommerce_db < /tmp/recovery_export.sql

echo "[$TIMESTAMP] Corruption recovery completed" | tee -a $CORRUPTION_LOG
```

### 3. Accidental Data Deletion

#### Scenario: Critical data accidentally deleted
**Impact**: Data loss affecting business operations
**Priority**: P1 - Critical

#### Point-in-Time Recovery
```bash
#!/bin/bash
# /usr/local/bin/point_in_time_recovery.sh

RECOVERY_TIME="$1"  # Format: YYYY-MM-DD HH:MM:SS
RECOVERY_LOG="/var/log/mysql/pit_recovery.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if [ -z "$RECOVERY_TIME" ]; then
    echo "Usage: $0 'YYYY-MM-DD HH:MM:SS'"
    exit 1
fi

echo "[$TIMESTAMP] Starting point-in-time recovery to $RECOVERY_TIME" | tee -a $RECOVERY_LOG

# 1. Create recovery database
mysql -u root -p -e "CREATE DATABASE ecommerce_db_recovery;"

# 2. Find appropriate backup
BACKUP_DATE=$(date -d "$RECOVERY_TIME" +%Y%m%d)
BACKUP_FILE="/backups/mysql/full_backup_${BACKUP_DATE}.sql.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    # Find the most recent backup before recovery time
    BACKUP_FILE=$(find /backups/mysql -name "full_backup_*.sql.gz" -newermt "$RECOVERY_TIME" | sort | head -1)
fi

echo "[$TIMESTAMP] Using backup file: $BACKUP_FILE" | tee -a $RECOVERY_LOG

# 3. Restore from backup
gunzip -c $BACKUP_FILE | mysql -u root -p ecommerce_db_recovery

# 4. Apply binary logs up to recovery point
BINLOG_FILES=$(mysql -u root -p -e "SHOW BINARY LOGS;" | awk 'NR>1 {print $1}')

for binlog in $BINLOG_FILES; do
    echo "[$TIMESTAMP] Processing binary log: $binlog" | tee -a $RECOVERY_LOG
    mysqlbinlog --stop-datetime="$RECOVERY_TIME" /var/log/mysql/$binlog | \
        mysql -u root -p ecommerce_db_recovery
done

# 5. Verify recovered data
RECOVERED_COUNT=$(mysql -u root -p -e "SELECT COUNT(*) FROM ecommerce_db_recovery.auth_user;" | tail -1)
CURRENT_COUNT=$(mysql -u root -p -e "SELECT COUNT(*) FROM ecommerce_db.auth_user;" | tail -1)

echo "[$TIMESTAMP] Recovery verification:" | tee -a $RECOVERY_LOG
echo "[$TIMESTAMP] Current database records: $CURRENT_COUNT" | tee -a $RECOVERY_LOG
echo "[$TIMESTAMP] Recovered database records: $RECOVERED_COUNT" | tee -a $RECOVERY_LOG

# 6. Manual verification step
echo "[$TIMESTAMP] Recovery database created: ecommerce_db_recovery" | tee -a $RECOVERY_LOG
echo "[$TIMESTAMP] Please verify data before switching databases" | tee -a $RECOVERY_LOG

# Send notification
echo "Point-in-time recovery completed. Recovery database: ecommerce_db_recovery. Please verify before switching." | \
    mail -s "PIT Recovery Completed - Verification Required" admin@company.com
```

### 4. Network Partition/Split-Brain

#### Scenario: Network partition causing split-brain
**Impact**: Data consistency issues
**Priority**: P1 - Critical

#### Detection and Resolution
```bash
#!/bin/bash
# /usr/local/bin/resolve_split_brain.sh

SPLIT_BRAIN_LOG="/var/log/mysql/split_brain_recovery.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Detecting split-brain scenario" | tee -a $SPLIT_BRAIN_LOG

# 1. Check replication status on all nodes
PRIMARY_STATUS=$(mysql -h mysql-primary.company.com -u monitor -p${MONITOR_PASSWORD} -e "SHOW MASTER STATUS;" 2>/dev/null)
REPLICA1_STATUS=$(mysql -h mysql-replica-1.company.com -u monitor -p${MONITOR_PASSWORD} -e "SHOW SLAVE STATUS\G" 2>/dev/null)
REPLICA2_STATUS=$(mysql -h mysql-replica-2.company.com -u monitor -p${MONITOR_PASSWORD} -e "SHOW SLAVE STATUS\G" 2>/dev/null)

# 2. Determine which node has the most recent data
PRIMARY_GTID=$(mysql -h mysql-primary.company.com -u monitor -p${MONITOR_PASSWORD} -e "SELECT @@GLOBAL.gtid_executed;" 2>/dev/null | tail -1)
REPLICA1_GTID=$(mysql -h mysql-replica-1.company.com -u monitor -p${MONITOR_PASSWORD} -e "SELECT @@GLOBAL.gtid_executed;" 2>/dev/null | tail -1)
REPLICA2_GTID=$(mysql -h mysql-replica-2.company.com -u monitor -p${MONITOR_PASSWORD} -e "SELECT @@GLOBAL.gtid_executed;" 2>/dev/null | tail -1)

echo "[$TIMESTAMP] GTID positions:" | tee -a $SPLIT_BRAIN_LOG
echo "[$TIMESTAMP] Primary: $PRIMARY_GTID" | tee -a $SPLIT_BRAIN_LOG
echo "[$TIMESTAMP] Replica1: $REPLICA1_GTID" | tee -a $SPLIT_BRAIN_LOG
echo "[$TIMESTAMP] Replica2: $REPLICA2_GTID" | tee -a $SPLIT_BRAIN_LOG

# 3. Stop all writes to prevent further divergence
echo "[$TIMESTAMP] Enabling read-only mode on all nodes" | tee -a $SPLIT_BRAIN_LOG
mysql -h mysql-primary.company.com -u root -p${MYSQL_ROOT_PASSWORD} -e "SET GLOBAL read_only = ON;" 2>/dev/null
mysql -h mysql-replica-1.company.com -u root -p${MYSQL_ROOT_PASSWORD} -e "SET GLOBAL read_only = ON;" 2>/dev/null
mysql -h mysql-replica-2.company.com -u root -p${MYSQL_ROOT_PASSWORD} -e "SET GLOBAL read_only = ON;" 2>/dev/null

# 4. Manual intervention required
echo "[$TIMESTAMP] Split-brain detected. Manual intervention required." | tee -a $SPLIT_BRAIN_LOG
echo "[$TIMESTAMP] All nodes set to read-only. Please analyze data divergence manually." | tee -a $SPLIT_BRAIN_LOG

# Send critical alert
echo "Split-brain scenario detected in MySQL cluster. All nodes set to read-only. Immediate manual intervention required." | \
    mail -s "CRITICAL: MySQL Split-Brain Detected" admin@company.com
```

## Backup and Recovery Procedures

### 1. Backup Verification
```bash
#!/bin/bash
# /usr/local/bin/verify_backup_integrity.sh

BACKUP_DIR="/backups/mysql"
VERIFY_LOG="/var/log/mysql/backup_verification.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting backup verification" | tee -a $VERIFY_LOG

# 1. Check latest backup file
LATEST_BACKUP=$(ls -t $BACKUP_DIR/full_backup_*.sql.gz | head -1)
echo "[$TIMESTAMP] Verifying backup: $LATEST_BACKUP" | tee -a $VERIFY_LOG

# 2. Test backup file integrity
if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
    echo "[$TIMESTAMP] ✓ Backup file compression is valid" | tee -a $VERIFY_LOG
else
    echo "[$TIMESTAMP] ✗ Backup file compression is corrupted" | tee -a $VERIFY_LOG
    exit 1
fi

# 3. Test backup content
TEST_DB="backup_verification_$(date +%s)"
mysql -u root -p -e "CREATE DATABASE $TEST_DB;"

if gunzip -c "$LATEST_BACKUP" | mysql -u root -p $TEST_DB; then
    echo "[$TIMESTAMP] ✓ Backup content is valid" | tee -a $VERIFY_LOG
    
    # Verify table counts
    ORIGINAL_TABLES=$(mysql -u root -p -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ecommerce_db';" | tail -1)
    RESTORED_TABLES=$(mysql -u root -p -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$TEST_DB';" | tail -1)
    
    if [ "$ORIGINAL_TABLES" -eq "$RESTORED_TABLES" ]; then
        echo "[$TIMESTAMP] ✓ Table count matches ($ORIGINAL_TABLES tables)" | tee -a $VERIFY_LOG
    else
        echo "[$TIMESTAMP] ⚠ Table count mismatch: Original=$ORIGINAL_TABLES, Restored=$RESTORED_TABLES" | tee -a $VERIFY_LOG
    fi
else
    echo "[$TIMESTAMP] ✗ Backup content is corrupted" | tee -a $VERIFY_LOG
fi

# 4. Cleanup test database
mysql -u root -p -e "DROP DATABASE $TEST_DB;"

echo "[$TIMESTAMP] Backup verification completed" | tee -a $VERIFY_LOG
```

### 2. Automated Recovery Testing
```bash
#!/bin/bash
# /usr/local/bin/automated_recovery_test.sh

RECOVERY_TEST_LOG="/var/log/mysql/recovery_test.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting automated recovery test" | tee -a $RECOVERY_TEST_LOG

# 1. Create test environment
TEST_CONTAINER="mysql_recovery_test_$(date +%s)"
docker run -d --name $TEST_CONTAINER \
    -e MYSQL_ROOT_PASSWORD=test_password \
    -v /backups/mysql:/backups \
    mysql:8.0

# Wait for MySQL to start
sleep 30

# 2. Restore latest backup
LATEST_BACKUP=$(ls -t /backups/mysql/full_backup_*.sql.gz | head -1)
echo "[$TIMESTAMP] Testing recovery with backup: $LATEST_BACKUP" | tee -a $RECOVERY_TEST_LOG

docker exec $TEST_CONTAINER bash -c "
    mysql -u root -ptest_password -e 'CREATE DATABASE recovery_test;'
    gunzip -c /backups/$(basename $LATEST_BACKUP) | mysql -u root -ptest_password recovery_test
"

# 3. Verify recovery
RECOVERY_STATUS=$?
if [ $RECOVERY_STATUS -eq 0 ]; then
    echo "[$TIMESTAMP] ✓ Recovery test successful" | tee -a $RECOVERY_TEST_LOG
    
    # Test data integrity
    TABLE_COUNT=$(docker exec $TEST_CONTAINER mysql -u root -ptest_password -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='recovery_test';" | tail -1)
    echo "[$TIMESTAMP] Recovered $TABLE_COUNT tables" | tee -a $RECOVERY_TEST_LOG
else
    echo "[$TIMESTAMP] ✗ Recovery test failed" | tee -a $RECOVERY_TEST_LOG
fi

# 4. Cleanup
docker stop $TEST_CONTAINER
docker rm $TEST_CONTAINER

echo "[$TIMESTAMP] Recovery test completed" | tee -a $RECOVERY_TEST_LOG

# Send test results
if [ $RECOVERY_STATUS -eq 0 ]; then
    echo "Automated recovery test passed successfully. $TABLE_COUNT tables recovered." | \
        mail -s "Recovery Test: PASSED" admin@company.com
else
    echo "Automated recovery test FAILED. Please investigate backup integrity." | \
        mail -s "Recovery Test: FAILED" admin@company.com
fi
```

## Communication and Escalation

### 1. Incident Communication Plan

#### Notification Matrix
| Incident Level | Notification Method | Recipients | Timeline |
|----------------|-------------------|------------|----------|
| P1 - Critical | Phone + Email + SMS | DBA Team, CTO, On-call Engineer | Immediate |
| P2 - High | Email + Slack | DBA Team, Dev Team Lead | 15 minutes |
| P3 - Medium | Email | DBA Team | 1 hour |
| P4 - Low | Email | DBA Team | 4 hours |

#### Communication Templates
```bash
# Critical incident notification
CRITICAL_TEMPLATE="
CRITICAL DATABASE INCIDENT

Incident ID: DR-$(date +%Y%m%d-%H%M%S)
Severity: P1 - Critical
Start Time: $(date)
Affected Systems: MySQL Primary Database
Impact: Complete service outage
Estimated Users Affected: All users

Current Status: [STATUS]
Actions Taken: [ACTIONS]
Next Steps: [NEXT_STEPS]
ETA for Resolution: [ETA]

Incident Commander: [NAME]
Contact: [PHONE] / [EMAIL]
"

# Send critical notification
send_critical_alert() {
    local status="$1"
    local actions="$2"
    local next_steps="$3"
    local eta="$4"
    local commander="$5"
    local contact="$6"
    
    MESSAGE=$(echo "$CRITICAL_TEMPLATE" | \
        sed "s/\[STATUS\]/$status/g" | \
        sed "s/\[ACTIONS\]/$actions/g" | \
        sed "s/\[NEXT_STEPS\]/$next_steps/g" | \
        sed "s/\[ETA\]/$eta/g" | \
        sed "s/\[NAME\]/$commander/g" | \
        sed "s/\[CONTACT\]/$contact/g")
    
    echo "$MESSAGE" | mail -s "CRITICAL: Database Incident" admin@company.com
    # Also send to Slack, PagerDuty, etc.
}
```

### 2. Escalation Procedures

#### Escalation Timeline
- **0-15 minutes**: On-call DBA responds
- **15-30 minutes**: Escalate to Senior DBA if no progress
- **30-60 minutes**: Escalate to Database Team Lead
- **60-120 minutes**: Escalate to CTO and Infrastructure Director
- **120+ minutes**: Escalate to CEO and activate external support

#### External Support Contacts
- **MySQL Enterprise Support**: +1-800-MYSQL-1
- **Cloud Provider Support**: [Provider-specific contact]
- **Hardware Vendor Support**: [Vendor-specific contact]
- **Network Provider Support**: [Provider-specific contact]

## Testing and Validation

### 1. Disaster Recovery Drills

#### Monthly DR Drill Schedule
```bash
#!/bin/bash
# /usr/local/bin/monthly_dr_drill.sh

DR_DRILL_LOG="/var/log/mysql/dr_drill_$(date +%Y%m).log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting monthly DR drill" | tee -a $DR_DRILL_LOG

# Scenario rotation (different scenario each month)
MONTH=$(date +%m)
case $MONTH in
    01|04|07|10) SCENARIO="primary_failure" ;;
    02|05|08|11) SCENARIO="data_corruption" ;;
    03|06|09|12) SCENARIO="network_partition" ;;
esac

echo "[$TIMESTAMP] DR Drill Scenario: $SCENARIO" | tee -a $DR_DRILL_LOG

# Execute scenario-specific drill
case $SCENARIO in
    "primary_failure")
        /usr/local/bin/drill_primary_failure.sh
        ;;
    "data_corruption")
        /usr/local/bin/drill_data_corruption.sh
        ;;
    "network_partition")
        /usr/local/bin/drill_network_partition.sh
        ;;
esac

echo "[$TIMESTAMP] Monthly DR drill completed" | tee -a $DR_DRILL_LOG

# Generate drill report
/usr/local/bin/generate_drill_report.sh $SCENARIO
```

### 2. Recovery Time Testing
```bash
#!/bin/bash
# /usr/local/bin/test_recovery_times.sh

RTO_TEST_LOG="/var/log/mysql/rto_test.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting RTO testing" | tee -a $RTO_TEST_LOG

# Test 1: Backup restoration time
START_TIME=$(date +%s)
/usr/local/bin/test_backup_restore.sh
END_TIME=$(date +%s)
BACKUP_RESTORE_TIME=$((END_TIME - START_TIME))

echo "[$TIMESTAMP] Backup restore time: ${BACKUP_RESTORE_TIME} seconds" | tee -a $RTO_TEST_LOG

# Test 2: Failover time
START_TIME=$(date +%s)
/usr/local/bin/test_failover.sh
END_TIME=$(date +%s)
FAILOVER_TIME=$((END_TIME - START_TIME))

echo "[$TIMESTAMP] Failover time: ${FAILOVER_TIME} seconds" | tee -a $RTO_TEST_LOG

# Test 3: Point-in-time recovery time
START_TIME=$(date +%s)
/usr/local/bin/test_pit_recovery.sh
END_TIME=$(date +%s)
PIT_RECOVERY_TIME=$((END_TIME - START_TIME))

echo "[$TIMESTAMP] PIT recovery time: ${PIT_RECOVERY_TIME} seconds" | tee -a $RTO_TEST_LOG

# Generate RTO report
echo "RTO Test Results - $(date)" > /tmp/rto_report.txt
echo "Backup Restore: ${BACKUP_RESTORE_TIME}s (Target: <7200s)" >> /tmp/rto_report.txt
echo "Failover: ${FAILOVER_TIME}s (Target: <1800s)" >> /tmp/rto_report.txt
echo "PIT Recovery: ${PIT_RECOVERY_TIME}s (Target: <14400s)" >> /tmp/rto_report.txt

# Check if targets are met
if [ $BACKUP_RESTORE_TIME -gt 7200 ] || [ $FAILOVER_TIME -gt 1800 ] || [ $PIT_RECOVERY_TIME -gt 14400 ]; then
    echo "⚠ Some RTO targets not met. Review and optimize procedures." >> /tmp/rto_report.txt
    mail -s "RTO Test: Targets Not Met" admin@company.com < /tmp/rto_report.txt
else
    echo "✓ All RTO targets met successfully." >> /tmp/rto_report.txt
    mail -s "RTO Test: All Targets Met" admin@company.com < /tmp/rto_report.txt
fi
```

## Documentation Maintenance

### 1. Plan Updates
- Review and update disaster recovery plan quarterly
- Update contact information monthly
- Test all procedures semi-annually
- Validate backup and recovery procedures monthly

### 2. Training Requirements
- All DBA team members must complete DR training annually
- New team members must complete DR training within 30 days
- Conduct DR simulation exercises quarterly
- Maintain DR runbook with step-by-step procedures

This comprehensive disaster recovery plan ensures rapid response and recovery from various failure scenarios while maintaining data integrity and minimizing business impact.