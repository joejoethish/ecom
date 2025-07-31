# Zero-Downtime Migration System Guide

## Overview

The Zero-Downtime Migration System provides a comprehensive solution for migrating from SQLite to MySQL with minimal service interruption. The system implements a staged migration process with validation checkpoints, real-time monitoring, and automated rollback capabilities.

## Features

### Core Features
- **Staged Migration Process**: 8-stage migration with validation at each step
- **Real-time Monitoring**: Live progress tracking with web dashboard
- **Automated Rollback**: Automatic rollback on failure conditions
- **Validation Checkpoints**: Data integrity verification at each stage
- **Progress Tracking**: Detailed metrics and ETA calculations
- **Web Dashboard**: Real-time monitoring interface
- **Command Line Interface**: Full CLI control and monitoring

### Safety Features
- **Rollback Points**: Automatic backup creation before each stage
- **Error Thresholds**: Configurable error limits trigger rollback
- **Time Limits**: Maximum migration time prevents runaway processes
- **Graceful Shutdown**: Signal handling for clean termination
- **Data Validation**: Comprehensive integrity checks

## Architecture

### Migration Stages

1. **Preparation**: Database connections, table discovery, resource validation
2. **Schema Sync**: MySQL table creation with optimized schema
3. **Initial Data Sync**: Bulk data migration with batch processing
4. **Validation**: Data integrity verification and consistency checks
5. **Cutover Preparation**: Final synchronization and readiness checks
6. **Cutover**: Database switch with minimal downtime
7. **Post-Cutover Validation**: Verify new system functionality
8. **Cleanup**: Resource cleanup and log archival

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                Zero-Downtime Migration System               │
├─────────────────────────────────────────────────────────────┤
│  ZeroDowntimeMigrationService                              │
│  ├── Migration Stages (8 stages)                           │
│  ├── Checkpoint System                                     │
│  ├── Progress Tracking                                     │
│  ├── Rollback Management                                   │
│  └── Monitoring Callbacks                                  │
├─────────────────────────────────────────────────────────────┤
│  Management Command (zero_downtime_migrate)                │
│  ├── CLI Interface                                         │
│  ├── Progress Display                                      │
│  ├── Configuration Options                                 │
│  └── Status Reporting                                      │
├─────────────────────────────────────────────────────────────┤
│  Web Monitoring Interface                                  │
│  ├── Real-time Dashboard                                   │
│  ├── REST API                                              │
│  ├── Migration History                                     │
│  └── Control Operations                                    │
├─────────────────────────────────────────────────────────────┤
│  Database Migration Service (Core)                         │
│  ├── Schema Conversion                                     │
│  ├── Data Transfer                                         │
│  ├── Validation                                            │
│  └── Rollback Operations                                   │
└─────────────────────────────────────────────────────────────┘
```

## Installation and Setup

### Prerequisites

1. **Python Environment**: Python 3.8+ with Django
2. **Database Access**: MySQL server with appropriate permissions
3. **System Resources**: Sufficient disk space and memory
4. **Network Connectivity**: Stable connection between databases

### Configuration

1. **Django Settings**: Configure MySQL database settings
2. **Migration Settings**: Set rollback triggers and timeouts
3. **Monitoring Setup**: Enable web monitoring if needed
4. **Logging Configuration**: Configure detailed logging

### Required Permissions

#### MySQL User Permissions
```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER 
ON database_name.* TO 'migration_user'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'migration_user'@'%';
```

#### File System Permissions
- Read access to SQLite database file
- Write access to migration logs directory
- Temporary file creation permissions

## Usage

### Command Line Interface

#### Basic Migration
```bash
python manage.py zero_downtime_migrate \
    --mysql-user myuser \
    --mysql-password mypassword \
    --mysql-database mydatabase
```

#### Advanced Options
```bash
python manage.py zero_downtime_migrate \
    --sqlite-path /path/to/database.db \
    --mysql-host mysql.example.com \
    --mysql-port 3306 \
    --mysql-user myuser \
    --mysql-password mypassword \
    --mysql-database mydatabase \
    --log-file /path/to/migration.log \
    --web-monitoring \
    --max-errors 3 \
    --max-time-hours 12
```

#### Dry Run
```bash
python manage.py zero_downtime_migrate \
    --mysql-user myuser \
    --mysql-password mypassword \
    --mysql-database mydatabase \
    --dry-run
```

#### Status and Control
```bash
# Check migration status
python manage.py zero_downtime_migrate --status

# Stop running migration
python manage.py zero_downtime_migrate --stop

# Trigger rollback
python manage.py zero_downtime_migrate --rollback
```

### Programmatic Usage

#### Basic Migration
```python
from core.zero_downtime_migration import ZeroDowntimeMigrationService

# Create migration service
migration = ZeroDowntimeMigrationService(
    sqlite_path='/path/to/database.db',
    mysql_config={
        'host': 'localhost',
        'port': 3306,
        'user': 'myuser',
        'password': 'mypassword',
        'database': 'mydatabase'
    }
)

# Execute migration
success = migration.execute_migration()
```

#### With Monitoring
```python
from core.zero_downtime_migration import (
    ZeroDowntimeMigrationService,
    MigrationMonitor
)

# Create migration service
migration = ZeroDowntimeMigrationService()

# Add monitoring callbacks
migration.add_progress_callback(MigrationMonitor.console_progress_callback)
migration.add_progress_callback(
    MigrationMonitor.file_progress_callback('migration.log')
)

# Configure rollback triggers
migration.rollback_triggers.update({
    'max_errors': 3,
    'max_migration_time_hours': 8
})

# Execute migration
success = migration.execute_migration()

# Get final status
status = migration.get_migration_status()
print(f"Migration completed: {status['current_stage']}")
```

### Web Dashboard

Access the web dashboard at: `http://your-domain/migration/dashboard/`

#### Features
- Real-time progress tracking
- Migration history
- Performance statistics
- Error monitoring
- ETA calculations

#### API Endpoints
- `GET /api/migration/monitor/` - List active migrations
- `GET /api/migration/monitor/{id}/` - Get specific migration status
- `GET /api/migration/history/` - Get migration history and statistics
- `POST /api/migration/control/{id}/{action}/` - Control migration

## Configuration Options

### Migration Service Configuration

```python
# Rollback trigger configuration
rollback_triggers = {
    'max_errors': 5,                    # Maximum errors before rollback
    'max_validation_failures': 3,      # Maximum validation failures
    'max_sync_lag_seconds': 300,       # Maximum sync lag (5 minutes)
    'max_migration_time_hours': 24     # Maximum total migration time
}

# Batch processing configuration
batch_size = 1000                      # Records per batch
monitor_interval = 5                   # Progress update interval (seconds)
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sqlite-path` | SQLite database path | From Django settings |
| `--mysql-host` | MySQL host | localhost |
| `--mysql-port` | MySQL port | 3306 |
| `--mysql-user` | MySQL username | Required |
| `--mysql-password` | MySQL password | Required |
| `--mysql-database` | MySQL database | Required |
| `--dry-run` | Perform dry run | False |
| `--monitor-interval` | Progress update interval | 5 seconds |
| `--log-file` | Log file path | None |
| `--web-monitoring` | Enable web monitoring | False |
| `--max-errors` | Maximum errors | 5 |
| `--max-time-hours` | Maximum time | 24 hours |
| `--force` | Skip validation warnings | False |

## Monitoring and Logging

### Progress Monitoring

The system provides multiple monitoring options:

1. **Console Output**: Real-time progress bar and status updates
2. **File Logging**: Detailed progress logs to file
3. **Web Dashboard**: Browser-based real-time monitoring
4. **Cache-based**: Progress stored in Django cache for API access

### Log Files

Migration logs are stored in `migration_logs/` directory:

- `migration_log_{timestamp}.json` - Detailed migration log
- `migration_report_{migration_id}.json` - Final migration report
- `checkpoint_{stage}_{timestamp}.json` - Individual checkpoint data

### Metrics Tracked

- **Progress**: Percentage completion and ETA
- **Performance**: Records per second, elapsed time
- **Errors**: Error count and types
- **Stages**: Current stage and checkpoint status
- **Resources**: Memory usage and connection status

## Error Handling and Rollback

### Automatic Rollback Triggers

1. **Error Count**: Too many errors during migration
2. **Time Limit**: Migration exceeds maximum time
3. **Validation Failures**: Data integrity checks fail
4. **Resource Issues**: Insufficient disk space or memory
5. **Connection Failures**: Database connectivity problems

### Manual Rollback

```bash
# Trigger immediate rollback
python manage.py zero_downtime_migrate --rollback

# Or programmatically
migration.trigger_rollback("Manual intervention required")
```

### Rollback Process

1. **Stop Migration**: Halt current operations
2. **Restore Data**: Restore from rollback points
3. **Verify Restoration**: Validate rollback success
4. **Clean Up**: Remove temporary data
5. **Report Status**: Log rollback completion

## Performance Optimization

### Batch Size Tuning

```python
# Small datasets (< 10K records)
batch_size = 100

# Medium datasets (10K - 1M records)
batch_size = 1000

# Large datasets (> 1M records)
batch_size = 5000
```

### Connection Optimization

```python
mysql_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'myuser',
    'password': 'mypassword',
    'database': 'mydatabase',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False,
    'connect_timeout': 60,
    'read_timeout': 300,
    'write_timeout': 300
}
```

### Resource Management

- **Memory**: Monitor memory usage during large data transfers
- **Disk Space**: Ensure sufficient space for rollback points
- **Network**: Use stable, high-bandwidth connections
- **CPU**: Consider migration during low-usage periods

## Testing

### Unit Tests

```bash
# Run zero-downtime migration tests
python backend/tests/test_zero_downtime_migration.py

# Run with Django test runner
python manage.py test tests.test_zero_downtime_migration
```

### Integration Tests

```bash
# Run comprehensive migration tests
python backend/run_migration_tests.py --suite all

# Run specific test suite
python backend/run_migration_tests.py --suite integration
```

### Test Coverage

The test suite covers:
- ✅ Migration service initialization
- ✅ Callback registration and notification
- ✅ Checkpoint creation and storage
- ✅ Metrics calculation and updates
- ✅ Rollback trigger conditions
- ✅ Individual migration stages
- ✅ Error handling and recovery
- ✅ Monitoring utilities
- ✅ Integration workflows

## Troubleshooting

### Common Issues

#### Connection Errors
```
Error: Failed to connect to MySQL
Solution: Check MySQL credentials, host, and port
```

#### Permission Errors
```
Error: Access denied for user
Solution: Grant appropriate MySQL permissions
```

#### Disk Space Issues
```
Error: No space left on device
Solution: Free up disk space or use different location
```

#### Memory Issues
```
Error: Out of memory during migration
Solution: Reduce batch size or increase system memory
```

### Debug Mode

Enable debug logging:
```bash
export DJANGO_LOG_LEVEL=DEBUG
export MIGRATION_DEBUG=1
python manage.py zero_downtime_migrate --mysql-user ... --mysql-password ...
```

### Recovery Procedures

#### Failed Migration Recovery
1. Check migration logs for error details
2. Verify database connectivity
3. Check available disk space
4. Review rollback points
5. Restart migration with fixes

#### Partial Migration Recovery
1. Identify completed stages from checkpoints
2. Resume from last successful checkpoint
3. Validate data integrity
4. Continue with remaining stages

## Best Practices

### Pre-Migration

1. **Backup**: Create full database backup
2. **Testing**: Test migration on staging environment
3. **Resources**: Ensure adequate system resources
4. **Timing**: Schedule during low-usage periods
5. **Monitoring**: Set up monitoring and alerting

### During Migration

1. **Monitor**: Watch progress and error rates
2. **Resources**: Monitor system resource usage
3. **Logs**: Review logs for warnings or issues
4. **Network**: Ensure stable network connectivity
5. **Standby**: Have rollback plan ready

### Post-Migration

1. **Validation**: Verify all data migrated correctly
2. **Performance**: Check application performance
3. **Monitoring**: Continue monitoring for issues
4. **Cleanup**: Clean up temporary files and logs
5. **Documentation**: Document any issues or lessons learned

## Security Considerations

### Database Security

1. **Credentials**: Use secure credential storage
2. **Connections**: Use SSL/TLS for database connections
3. **Permissions**: Grant minimal required permissions
4. **Audit**: Enable database audit logging

### Application Security

1. **Access Control**: Restrict migration command access
2. **Logging**: Secure migration logs
3. **Monitoring**: Secure web dashboard access
4. **Cleanup**: Securely delete temporary files

## Support and Maintenance

### Regular Maintenance

1. **Log Rotation**: Rotate and archive migration logs
2. **Performance Review**: Review migration performance metrics
3. **Update Testing**: Test migrations with new data
4. **Documentation**: Keep documentation updated

### Monitoring Setup

1. **Alerts**: Set up alerts for migration failures
2. **Dashboards**: Create monitoring dashboards
3. **Reports**: Generate regular migration reports
4. **Metrics**: Track migration success rates

### Troubleshooting Resources

1. **Logs**: Check detailed migration logs
2. **Metrics**: Review performance metrics
3. **Tests**: Run diagnostic tests
4. **Documentation**: Consult troubleshooting guide

---

## Appendix

### Migration Stage Details

#### Stage 1: Preparation
- Database connection validation
- Table discovery and analysis
- Resource availability checks
- Migration plan creation

#### Stage 2: Schema Sync
- MySQL table creation
- Index optimization
- Constraint setup
- Schema validation

#### Stage 3: Initial Data Sync
- Bulk data transfer
- Batch processing
- Progress tracking
- Error handling

#### Stage 4: Validation
- Record count verification
- Data integrity checks
- Consistency validation
- Error reporting

#### Stage 5: Cutover Preparation
- Final synchronization
- Readiness verification
- Rollback point creation
- System preparation

#### Stage 6: Cutover
- Application shutdown
- Final data sync
- Database switch
- Application restart

#### Stage 7: Post-Cutover Validation
- System functionality verification
- Performance validation
- Error detection
- Success confirmation

#### Stage 8: Cleanup
- Temporary file cleanup
- Log archival
- Resource cleanup
- Final reporting

### Error Codes

| Code | Description | Action |
|------|-------------|--------|
| CONN_001 | Database connection failed | Check credentials and connectivity |
| PERM_001 | Insufficient permissions | Grant required database permissions |
| DISK_001 | Insufficient disk space | Free up disk space |
| MEM_001 | Out of memory | Reduce batch size or increase memory |
| TIME_001 | Migration timeout | Increase time limit or optimize |
| DATA_001 | Data validation failed | Check data integrity |
| ROLL_001 | Rollback failed | Manual intervention required |

### Performance Benchmarks

| Dataset Size | Expected Duration | Memory Usage | Disk Space |
|--------------|-------------------|--------------|------------|
| < 10K records | 1-5 minutes | < 100MB | < 50MB |
| 10K-100K records | 5-30 minutes | 100-500MB | 50-500MB |
| 100K-1M records | 30-180 minutes | 500MB-2GB | 500MB-5GB |
| > 1M records | 3+ hours | 2GB+ | 5GB+ |

*Note: Performance varies based on hardware, network, and data complexity*